"""Controlled training-signal filters, exact score ties and direct-ranking fusion."""

import json
import sqlite3
from collections import Counter, defaultdict
from pathlib import Path
import numpy as np
from .intervals import segment_durations


def filtered_airing_interactions(database, thresholds=(0.5, 0.8)):
    """Only the longest-block inclusion gate changes; q remains union/full-duration."""
    db = sqlite3.connect("file:" + str(Path(database).resolve()) + "?mode=ro", uri=True)
    output = {t: defaultdict(lambda: [0.0, 0]) for t in thresholds}
    counts = Counter()
    key = None
    segments = []
    item = None
    duration = 0

    def consume():
        if key is None:
            return
        stats = segment_durations(segments)
        fraction = stats["longest_block_seconds"] / duration
        q = min(1.0, stats["union_seconds"] / duration)
        for threshold in thresholds:
            if fraction >= threshold:
                value = output[threshold][(key[0], item)]
                value[0] += q
                value[1] += fraction >= 0.8
                counts[str(threshold)] += 1

    for u, a, it, s, e, d in db.execute(
        "SELECT u,a,item,s,e,d FROM segments ORDER BY u,a,s,e"
    ):
        if key != (u, a):
            consume()
            key, segments, item, duration = (u, a), [], it, d
        segments.append((s, e))
    consume()
    db.close()
    records = {
        t: [[u, it, v[0], v[1]] for (u, it), v in sorted(values.items())]
        for t, values in output.items()
    }
    return records, dict(counts)


def exact_score_order(ids, scores, popularity=None, limit=50):
    """No tolerance or rounding: primary scores always dominate secondary keys."""
    valid = [i for i, s in enumerate(scores) if np.isfinite(s) and s > 0]
    popularity = popularity or {}
    valid.sort(key=lambda i: (-float(scores[i]), -popularity.get(ids[i], 0), ids[i]))
    return [ids[i] for i in valid[:limit]]


def direct_ranking(model, user, limit=50, cbf_popularity=None):
    if model.method == "personal":
        values = model.qualified.get(user, {})
        return sorted(
            (it for it in values if it in model.candidate_set),
            key=lambda it: (-values[it], it),
        )[:limit]
    index = model.user_index.get(user)
    if index is None:
        return []
    if model.method == "cbf":
        scores = (model.candidate_content @ model.profiles[index].T).toarray().ravel()
        return exact_score_order(model.candidates, scores, cbf_popularity, limit)
    scores = np.einsum(
        "ij,j->i",
        model.candidate_factors.astype(np.float64),
        model.als.user_factors[index].astype(np.float64),
        optimize=False,
    )
    if not np.all(np.isfinite(scores)):
        raise FloatingPointError("nonfinite ALS scores")
    # Negative finite latent scores remain directly scored, as in the original ALS.
    order = sorted(
        range(len(scores)),
        key=lambda i: (-float(scores[i]), model.supported_candidates[i]),
    )[:limit]
    return [model.supported_candidates[i] for i in order]


def complete(direct, fallback, candidates, k=5):
    selected = list(direct[:k])
    for it in fallback:
        if len(selected) == k:
            break
        if it not in selected:
            selected.append(it)
    assert (
        len(selected) == len(set(selected)) == k
        and "0" not in selected
        and set(selected) <= candidates
    )
    return selected, min(len(direct), k)


def rrf_rank(personal, alternative, weight, k=60, limit=50):
    scores = defaultdict(float)
    for rank, it in enumerate(personal[:limit], 1):
        scores[it] += 1.0 / (k + rank)
    for rank, it in enumerate(alternative[:limit], 1):
        scores[it] += weight / (k + rank)
    return sorted(scores, key=lambda it: (-scores[it], it))


def popularity_viewers(records):
    return Counter(it for _, it, _, qualified in records if qualified)
