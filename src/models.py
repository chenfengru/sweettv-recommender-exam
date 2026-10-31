"""Four deterministic rankers with a shared completion policy and sparse features."""

import hashlib
import time
from collections import Counter, defaultdict

import numpy as np
from scipy import sparse
from implicit.cpu.als import AlternatingLeastSquares


def normalized(matrix):
    lengths = np.sqrt(np.asarray(matrix.multiply(matrix).sum(axis=1)).ravel())
    inverse = np.divide(1.0, lengths, out=np.zeros_like(lengths), where=lengths > 0)
    return sparse.diags(inverse).dot(matrix).tocsr()


class Ranker:
    def __init__(
        self,
        records,
        candidates,
        metadata,
        method,
        *,
        factors=32,
        regularization=0.01,
        iterations=20,
        seed=42
    ):
        began = time.perf_counter()
        self.method = method
        self.candidates = sorted(candidates)
        self.candidate_set = set(candidates)
        self.history = defaultdict(dict)
        self.qualified = defaultdict(dict)
        counts, viewers = Counter(), Counter()
        for u, it, strength, count in records:
            self.history[u][it] = strength
            if count:
                self.qualified[u][it] = count
                counts[it] += count
                viewers[it] += 1
        self.fallback = sorted(
            candidates, key=lambda it: (-viewers[it], -counts[it], it)
        )
        self.users = sorted(self.history)
        self.user_index = {u: i for i, u in enumerate(self.users)}
        self.items = sorted({it for values in self.history.values() for it in values})
        self.item_index = {it: i for i, it in enumerate(self.items)}
        self.config = {"method": method, "seed": seed}
        if method in ("cbf", "als"):
            rr, cc, vv = [], [], []
            for u in self.users:
                for it, value in sorted(self.history[u].items()):
                    rr.append(self.user_index[u])
                    cc.append(self.item_index[it])
                    vv.append(np.log1p(value))
            self.weights = sparse.csr_matrix(
                (np.asarray(vv, dtype=np.float32), (rr, cc)),
                shape=(len(self.users), len(self.items)),
            )
        if method == "cbf":
            # Metadata tuple is title/category/genre1/genre2/genre3. Title is display-only.
            def tokens(values):
                return ({("category", values[1])} if values[1] else set()) | {
                    ("genre", value) for value in values[2:] if value
                }

            vocabulary = sorted(
                {token for values in metadata.values() for token in tokens(values)}
            )
            self.vocabulary = vocabulary
            features = {token: i for i, token in enumerate(vocabulary)}
            self.content_items = sorted(set(self.items) | set(self.candidates))
            self.content_index = {it: i for i, it in enumerate(self.content_items)}
            rr, cc = [], []
            for it in self.content_items:
                for token in sorted(tokens(metadata.get(it, ("", "", "", "", "")))):
                    if token in features:
                        rr.append(self.content_index[it])
                        cc.append(features[token])
            self.content = normalized(
                sparse.csr_matrix(
                    (np.ones(len(rr), dtype=np.float32), (rr, cc)),
                    shape=(len(self.content_items), len(features)),
                )
            )
            training_content = self.content[
                [self.content_index[it] for it in self.items]
            ]
            self.profiles = normalized(self.weights @ training_content)
            self.candidate_content = self.content[
                [self.content_index[it] for it in self.candidates]
            ]
            self.config.update(
                {
                    "features": "category/genre multi-hot L2; genre slots pooled",
                    "user_profile": "L2 normalized log1p-strength weighted item sum",
                }
            )
        elif method == "als":
            # Official API accepts C_ui itself. alpha=1 prevents applying 40 twice.
            self.confidence = self.weights.copy()
            self.confidence.data = 1.0 + 40.0 * self.confidence.data
            self.als = AlternatingLeastSquares(
                factors=factors,
                regularization=regularization,
                iterations=iterations,
                random_state=seed,
                alpha=1.0,
                num_threads=1,
                dtype=np.float32,
                use_cg=True,
            )
            self.als.fit(self.confidence, show_progress=False)
            if not (
                np.all(np.isfinite(self.als.user_factors))
                and np.all(np.isfinite(self.als.item_factors))
            ):
                raise FloatingPointError("ALS produced non-finite fitted factors")
            self.supported_candidates = [
                it for it in self.candidates if it in self.item_index
            ]
            self.candidate_factors = self.als.item_factors[
                [self.item_index[it] for it in self.supported_candidates]
            ]
            self.config.update(
                {
                    "factors": factors,
                    "regularization": regularization,
                    "iterations": iterations,
                    "library_alpha": 1.0,
                    "confidence_multiplier": 40,
                    "num_threads": 1,
                    "use_cg": True,
                }
            )
        elif method not in ("popularity", "personal"):
            raise ValueError(method)
        self.fit_seconds = time.perf_counter() - began

    def primary(self, user):
        if self.method == "popularity":
            # The global model is the baseline itself, rather than a per-user fallback.
            return self.fallback[:5]
        if self.method == "personal":
            values = self.qualified.get(user, {})
            return sorted(
                (it for it in values if it in self.candidate_set),
                key=lambda it: (-values[it], it),
            )[:5]
        index = self.user_index.get(user)
        if index is None:
            return []
        if self.method == "cbf":
            scores = (self.candidate_content @ self.profiles[index].T).toarray().ravel()
            valid = np.flatnonzero(scores > 0)
            order = valid[np.argsort(-scores[valid], kind="stable")][:5]
            return [self.candidates[i] for i in order]
        scores = np.einsum(
            "ij,j->i",
            self.candidate_factors.astype(np.float64),
            self.als.user_factors[index].astype(np.float64),
            optimize=False,
        )
        if not np.all(np.isfinite(scores)):
            raise FloatingPointError("ALS produced non-finite candidate scores")
        valid = np.flatnonzero(np.isfinite(scores))
        order = valid[np.argsort(-scores[valid], kind="stable")][:5]
        return [self.supported_candidates[i] for i in order]

    def recommend(self, user):
        primary = self.primary(user)
        selected = primary.copy()
        for it in self.fallback:
            if len(selected) == 5:
                break
            if it not in selected:
                selected.append(it)
        assert len(selected) == 5 and len(set(selected)) == 5 and "0" not in selected
        assert set(selected) <= self.candidate_set
        return selected, len(primary)

    def fingerprint(self):
        """Deterministic fitted-feature/parameter signature for leakage regression."""
        digest = hashlib.sha256()
        for name in ("weights", "confidence", "content", "profiles"):
            if hasattr(self, name):
                value = getattr(self, name)
                digest.update(value.data.tobytes())
                digest.update(value.indices.tobytes())
                digest.update(value.indptr.tobytes())
        if hasattr(self, "als"):
            digest.update(self.als.user_factors.tobytes())
            digest.update(self.als.item_factors.tobytes())
        import json

        digest.update(
            json.dumps(
                [
                    self.users,
                    self.items,
                    self.fallback,
                    dict(self.history),
                    dict(self.qualified),
                    self.config,
                ],
                sort_keys=True,
            ).encode()
        )
        return digest.hexdigest()
