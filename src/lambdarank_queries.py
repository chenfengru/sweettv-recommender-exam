"""Explicit origin/user queries and raw-score ranking with v14 tie/fallback keys."""

import math
import numpy as np
from .improvement_helpers import complete


def query_layout(origin, metadata, labels):
    users, items, offsets = metadata["users"], metadata["items"], metadata["offsets"]
    if (
        len(users) != len(set(users))
        or len(items) != len(users)
        or len(offsets) != len(users) + 1
    ):
        raise ValueError("Invalid per-origin query metadata.")
    if offsets[0] != 0 or offsets[-1] != len(labels):
        raise ValueError("Offsets must cover every label exactly.")
    if not np.isin(labels, [0, 1]).all():
        raise ValueError("Binary relevance labels required.")
    groups = np.diff(offsets)
    if any(g <= 0 for g in groups) or any(
        g != len(row) for g, row in zip(groups, items)
    ):
        raise ValueError("Invalid group sizes.")
    keys = [(origin, u) for u in users]
    informative = all_negative = all_positive = 0
    for a, b in zip(offsets[:-1], offsets[1:]):
        positive = int(np.sum(labels[a:b]))
        all_negative += positive == 0
        all_positive += positive == b - a
        informative += 0 < positive < b - a
    return (
        keys,
        groups.astype(np.int32),
        {
            "queries": len(keys),
            "informative_queries": informative,
            "all_negative_queries": all_negative,
            "all_positive_queries": all_positive,
            "uniform_label_queries": all_negative + all_positive,
        },
    )


def rank_raw_candidates(items, scores, counts, viewers, total, pool, fallback):
    if (
        len(items) != len(scores)
        or len(items) != len(set(items))
        or not np.isfinite(scores).all()
    ):
        raise ValueError("Invalid raw-score vector.")
    order = sorted(
        range(len(items)),
        key=lambda j: (
            -scores[j],
            -counts.get(items[j], 0),
            -viewers.get(items[j], 0),
            -total.get(items[j], 0),
            items[j],
        ),
    )
    return complete([items[j] for j in order], fallback, pool)


def ndcg_at_five(truth, predictions):
    relevant = set(truth)
    if not relevant:
        return 0.0
    dcg = math.fsum(
        1 / math.log2(j + 2) for j, it in enumerate(predictions[:5]) if it in relevant
    )
    ideal = math.fsum(1 / math.log2(j + 2) for j in range(min(5, len(relevant))))
    return dcg / ideal
