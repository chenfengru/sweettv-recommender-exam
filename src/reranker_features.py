"""Causal complete behavioural features and label-independent candidate unions."""

import math
import sqlite3
from collections import defaultdict
from pathlib import Path
import numpy as np
from .intervals import segment_durations
from .item_item import score_user
from .personal_ties import personal_order
from .improvement_helpers import complete

FEATURES = [
    "n30",
    "n50",
    "n80",
    "log1p_n30",
    "log1p_n50",
    "log1p_n80",
    "personal_n50_rank",
    "personal_rank_missing",
    "item_item_score",
    "item_item_score_missing",
    "item_item_rank",
    "item_item_rank_missing",
    "global_viewers80",
    "global_airings80",
    "user_history30",
    "user_history50",
    "user_history80",
    "user_airings30",
    "user_airings50",
    "user_airings80",
    "days_since_last_n50_view",
    "last_n50_view_missing",
    "n50_last7days",
    "n50_last28days",
    "source_personal200",
    "source_unseen50",
    "source_global5",
]


def causal_history(database, start, cutoff):
    counts = {t: defaultdict(lambda: defaultdict(int)) for t in [0.3, 0.5, 0.8]}
    latest = defaultdict(dict)
    rolling = {days: defaultdict(lambda: defaultdict(int)) for days in [7, 28]}
    key = None
    segments = []

    def consume():
        if key is None or not segments:
            return
        u, airing, item, duration = key
        fraction = segment_durations(segments)["longest_block_seconds"] / duration
        for t in counts:
            if fraction >= t:
                counts[t][u][item] += 1
        if fraction >= 0.5:
            end = max(e for _, e in segments)
            assert end <= cutoff
            latest[u][item] = max(latest[u].get(item, float("-inf")), end)
        for days in rolling:
            clipped = [
                (max(s, cutoff - days * 86400), e)
                for s, e in segments
                if e > cutoff - days * 86400
            ]
            if (
                clipped
                and segment_durations(clipped)["longest_block_seconds"] / duration
                >= 0.5
            ):
                rolling[days][u][item] += 1

    with sqlite3.connect(
        "file:" + str(Path(database).resolve()) + "?mode=ro", uri=True
    ) as db:
        known_users = {
            row[0]
            for row in db.execute(
                "SELECT DISTINCT u FROM views WHERE s < ? AND e > ?", (cutoff, start)
            )
        }
        for u, a, it, s, e, d in db.execute(
            "SELECT u,a,item,s,e,d FROM segments ORDER BY u,a,s,e"
        ):
            next_key = (u, a, it, d)
            if next_key != key:
                consume()
                key, segments = next_key, []
            s, e = max(s, start), min(e, cutoff)
            if e > s and d > 0:
                segments.append((s, e))
        consume()
    return {
        "counts": {
            t: {u: dict(c) for u, c in users.items()} for t, users in counts.items()
        },
        "latest": dict(latest),
        "rolling": {
            days: {u: dict(c) for u, c in users.items()}
            for days, users in rolling.items()
        },
        "known_users": known_users,
        "cutoff": cutoff,
    }


def candidate_union(personal, unseen, fallback, pool):
    sources = [
        set([it for it in ranking if it in pool][:limit])
        for ranking, limit in [(personal, 200), (unseen, 50), (fallback, 5)]
    ]
    return sorted(set.union(*sources)), sources


def user_features(u, history, neighbours, pool, viewers, total, fallback):
    counts = history["counts"]
    n50 = counts[0.5].get(u, {})
    personal = personal_order(
        n50, pool, variant="popularity", viewers=viewers, total=total
    )
    direct, unseen, scores = score_user(n50, neighbours, pool, return_scores=True)
    items, sources = candidate_union(personal, unseen, fallback, pool)
    p_rank = {it: r for r, it in enumerate(personal, 1)}
    i_rank = {it: r for r, it in enumerate(direct, 1)}
    user_sizes = [len(counts[t].get(u, {})) for t in [0.3, 0.5, 0.8]]
    user_totals = [sum(counts[t].get(u, {}).values()) for t in [0.3, 0.5, 0.8]]
    rows = []
    for item in items:
        ns = [counts[t].get(u, {}).get(item, 0) for t in [0.3, 0.5, 0.8]]
        last = history["latest"].get(u, {}).get(item)
        days = (history["cutoff"] - last) / 86400 if last is not None else 0
        assert days >= 0
        row = (
            ns
            + [math.log1p(n) for n in ns]
            + [
                p_rank.get(item, 0),
                int(item not in p_rank),
                scores.get(item, 0),
                int(item not in scores),
                i_rank.get(item, 0),
                int(item not in i_rank),
                viewers.get(item, 0),
                total.get(item, 0),
            ]
            + user_sizes
            + user_totals
            + [
                days,
                int(last is None),
                history["rolling"][7].get(u, {}).get(item, 0),
                history["rolling"][28].get(u, {}).get(item, 0),
            ]
            + [int(item in source) for source in sources]
        )
        rows.append(row)
    matrix = np.asarray(rows, dtype=np.float32).reshape(len(items), len(FEATURES))
    check_schema(matrix, FEATURES)
    return items, matrix


def check_schema(matrix, names):
    if list(names) != FEATURES or matrix.ndim != 2 or matrix.shape[1] != len(FEATURES):
        raise ValueError("Training/inference feature schema mismatch")
    if not np.isfinite(matrix).all():
        raise ValueError("Non-finite feature value")


def build_rows(users, history, neighbours, pool, viewers, total, fallback):
    chunks = []
    items = []
    offsets = [0]
    for u in users:
        candidate, x = user_features(
            u, history, neighbours, pool, viewers, total, fallback
        )
        assert (
            len(candidate) == len(set(candidate)) >= 5
            and set(candidate) <= pool
            and "0" not in candidate
        )
        items.append(candidate)
        chunks.append(x)
        offsets.append(offsets[-1] + len(candidate))
    matrix = np.concatenate(chunks, axis=0)
    check_schema(matrix, FEATURES)
    missing = {
        name: {
            "rows": int(np.sum(matrix[:, j] > 0)),
            "fraction": float(np.mean(matrix[:, j] > 0)),
        }
        for j, name in enumerate(FEATURES)
        if name.endswith("_missing")
    }
    return (
        matrix,
        items,
        offsets,
        {
            "rows": len(matrix),
            "features": len(FEATURES),
            "dtype": str(matrix.dtype),
            "matrix_bytes": matrix.nbytes,
            "all_finite": True,
            "actual_nan_or_inf": 0,
            "encoded_missing": missing,
            "zero_fraction": {
                name: float(np.mean(matrix[:, j] == 0))
                for j, name in enumerate(FEATURES)
            },
        },
    )


def candidate_labels(users, items, truth):
    return np.asarray(
        [int(it in truth.get(u, [])) for u, row in zip(users, items) for it in row],
        dtype=np.uint8,
    )


def candidate_coverage(users, items, truth):
    eligible = [
        (u, set(truth.get(u, [])), set(row))
        for u, row in zip(users, items)
        if truth.get(u)
    ]
    covered = sum(len(target & candidate) for u, target, candidate in eligible)
    den = sum(len(t) for _, t, _ in eligible)
    return {
        "users_in_feature_universe": len(users),
        "users_with_targets": len(eligible),
        "users_without_targets": len(users) - len(eligible),
        "all_label_users": len(truth),
        "label_users_outside_feature_universe": len(set(truth) - set(users)),
        "covered_relevant_pairs": covered,
        "all_relevant_pairs_in_universe": den,
        "micro_recall": covered / den if den else None,
        "macro_recall_target_users": (
            math.fsum(len(t & c) / len(t) for _, t, c in eligible) / len(eligible)
            if eligible
            else None
        ),
        "oracle_map_at_5_target_users": (
            math.fsum(min(5, len(t & c)) / min(5, len(t)) for _, t, c in eligible)
            / len(eligible)
            if eligible
            else None
        ),
    }


def ranked_candidates(items, probabilities, counts, viewers, total, pool, fallback):
    if len(items) != len(probabilities) or not np.isfinite(probabilities).all():
        raise ValueError("Invalid prediction vector")
    if any(p < 0 or p > 1 for p in probabilities):
        raise ValueError("Invalid binary probabilities")
    scores = dict(zip(items, probabilities))
    order = sorted(
        items,
        key=lambda it: (
            -scores[it],
            -counts.get(it, 0),
            -viewers.get(it, 0),
            -total.get(it, 0),
            it,
        ),
    )
    return complete(order, fallback, pool)
