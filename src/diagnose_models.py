"""Bounded numerical checks and full-cohort CBF tie diagnostics for an executed run."""

import argparse
import json
import math
import warnings
from collections import Counter
from pathlib import Path
import numpy as np
from threadpoolctl import threadpool_limits
from .models import Ranker


def main(private, output):
    setup = json.loads((private / "setup.json").read_text())
    records = json.loads((private / "train/interactions.json").read_text())
    truth = json.loads((private / "truth.json").read_text())
    cbf = Ranker(records, set(setup["candidates"]), setup["metadata"], "cbf")
    patterns = Counter(
        tuple(
            cbf.candidate_content.indices[
                cbf.candidate_content.indptr[i] : cbf.candidate_content.indptr[i + 1]
            ]
        )
        for i in range(len(cbf.candidates))
    )
    ties = []
    for user in truth:
        if user not in cbf.user_index:
            continue
        scores = (
            (cbf.candidate_content @ cbf.profiles[cbf.user_index[user]].T)
            .toarray()
            .ravel()
        )
        if scores.max() > 0:
            ties.append(int(np.sum(scores == scores.max())))
    rng = np.random.default_rng(42)
    users = sorted(set(truth) & set(cbf.users))
    sampled = [
        users[i]
        for i in rng.choice(len(users), size=min(30, len(users)), replace=False)
    ]
    profile_error = score_error = 0.0
    for user in sampled:
        # Independently sum sparse item vectors in double precision, using original strengths.
        terms = []
        for item, strength in cbf.history[user].items():
            terms.append(
                math.log1p(strength)
                * cbf.content[cbf.content_index[item]]
                .toarray()
                .ravel()
                .astype(np.float64)
            )
        profile = np.array(
            [math.fsum(t[j] for t in terms) for j in range(cbf.content.shape[1])]
        )
        length = math.sqrt(math.fsum(float(v * v) for v in profile))
        if length:
            profile /= length
        observed = cbf.profiles[cbf.user_index[user]].toarray().ravel()
        profile_error = max(profile_error, float(np.max(np.abs(observed - profile))))
        for i in rng.choice(len(cbf.candidates), size=10, replace=False):
            item = cbf.candidate_content[i].toarray().ravel()
            expected = math.fsum(float(x * y) for x, y in zip(item, profile))
            actual = float(
                (
                    cbf.candidate_content[i] @ cbf.profiles[cbf.user_index[user]].T
                ).toarray()[0, 0]
            )
            score_error = max(score_error, abs(expected - actual))
    assert profile_error < 1e-5 and score_error < 1e-5
    numerical = {}
    for path in sorted(private.glob("als_*_model.npz")):
        saved = np.load(path)
        X, Y = saved["user_factors"], saved["item_factors"]
        assert np.all(np.isfinite(X)) and np.all(np.isfinite(Y))
        indices = rng.choice(len(X), size=64, replace=False)
        max_error = scalar_error = 0.0
        warning_count = nonfinite = 0
        argmax_agree = 0
        for i in indices:
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter("always")
                native = Y @ X[i]
            warning_count += len(caught)
            nonfinite += int(np.sum(~np.isfinite(native)))
            reference = np.einsum(
                "ij,j->i", Y.astype(np.float64), X[i].astype(np.float64), optimize=False
            )
            assert np.all(np.isfinite(reference))
            max_error = max(max_error, float(np.max(np.abs(native - reference))))
            argmax_agree += int(native.argmax() == reference.argmax())
            j = int(rng.integers(len(Y)))
            scalar = math.fsum(float(a) * float(b) for a, b in zip(Y[j], X[i]))
            scalar_error = max(scalar_error, abs(float(reference[j]) - scalar))
        assert scalar_error < 1e-12 and nonfinite == 0 and max_error < 1e-5
        numerical[path.stem] = {
            "sampled_users": 64,
            "sampling": "uniform without replacement; NumPy Generator seed 42 stream after CBF diagnostic sampling",
            "all_factors_finite": True,
            "sampled_native_scores_nonfinite": nonfinite,
            "native_warning_count": warning_count,
            "max_native_float32_vs_direct_float64_score_error": max_error,
            "max_direct_float64_vs_scalar_fsum_error": scalar_error,
            "sampled_top1_argmax_agreements": argmax_agree,
        }
    result = {
        "seed": 42,
        "cbf": {
            "sampled_users_independent_profile_check": len(sampled),
            "candidate_cosines_checked_per_sampled_user": 10,
            "max_profile_coordinate_error": profile_error,
            "max_cosine_error": score_error,
            "candidate_items": len(cbf.candidates),
            "distinct_candidate_content_vectors": len(patterns),
            "largest_identical_vector_group": max(patterns.values()),
            "cohort_users_with_positive_content_score": len(ties),
            "users_with_more_than_five_exactly_tied_top_scores": sum(
                n > 5 for n in ties
            ),
            "median_exact_top_score_tie_count": float(np.median(ties)),
            "max_exact_top_score_tie_count": max(ties),
        },
        "als": numerical,
        "interpretation": "Native matmul emitted warnings despite finite factors and closely agreeing finite scores in this environment. Root cause is not established. Final scoring uses finite-checked float64 direct contraction, not native matmul; no warnings are suppressed in final fitting or inference.",
    }
    (output / "numerical_and_content_diagnostics.json").write_text(
        json.dumps(result, indent=2) + "\n"
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--private-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    with threadpool_limits(limits=1):
        main(args.private_dir, args.output_dir)
