"""Unweighted incoming-from-history affinity using original outgoing top50 graph."""

import math
from collections import defaultdict
import numpy as np

FEATURES = [
    "ii_other_max_similarity",
    "ii_other_top5_similarity_sum",
    "ii_other_log1p_positive_history_count",
]


def affinity_rows(history, candidates, neighbours):
    destinations = set(candidates)
    values = defaultdict(list)
    for source in sorted(set(history)):
        seen = set()
        for destination, similarity in neighbours.get(source, []):
            if destination in seen:
                raise ValueError("Duplicate destination in canonical source graph.")
            seen.add(destination)
            if destination != source and destination in destinations and similarity > 0:
                values[destination].append(float(similarity))
    rows = []
    for item in candidates:
        scores = sorted(values.get(item, []), reverse=True)
        rows.append(
            [
                scores[0] if scores else 0.0,
                math.fsum(scores[:5]),
                math.log1p(len(scores)),
            ]
        )
    result = np.asarray(rows, dtype=np.float32).reshape(len(candidates), 3)
    assert np.isfinite(result).all() and np.all(result >= 0)
    return result


def append_affinities(base, users, items, n50, neighbours):
    if base.shape != (sum(map(len, items)), 52):
        raise ValueError("Original52 alignment required.")
    extra = np.concatenate(
        [
            affinity_rows(
                [i for i, n in n50.get(u, {}).items() if n > 0], row, neighbours
            )
            for u, row in zip(users, items)
        ]
    )
    x = np.concatenate([base, extra], axis=1)
    assert (
        x.shape == (len(base), 55)
        and np.array_equal(x[:, :52], base)
        and np.isfinite(x).all()
    )
    return x, extra


def scalar_reference(history, candidate, neighbours):
    # Independent candidate-centric lookup; do not call the feature aggregator.
    positive = []
    for h in set(history):
        if h == candidate:
            continue
        for destination, s in neighbours.get(h, []):
            if destination == candidate and s > 0:
                positive.append(s)
    positive.sort(reverse=True)
    return np.asarray(
        [max(positive, default=0.0), sum(positive[:5]), math.log1p(len(positive))],
        dtype=np.float32,
    )
