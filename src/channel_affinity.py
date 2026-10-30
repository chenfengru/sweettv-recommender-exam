"""Exact-channel exposure and qualified-airing affinities; no future viewing."""

import json
import math
import sqlite3
from collections import defaultdict
from pathlib import Path
import numpy as np
from .intervals import segment_durations

AFFINITY_FEATURES = [
    f"{w}_{s}"
    for w in ["full", "trailing28"]
    for s in [
        "log1p_weighted_view_seconds",
        "weighted_view_share",
        "log1p_weighted_n50_airings",
        "weighted_n50_share",
    ]
] + ["full_no_viewing", "full_no_n50", "trailing28_no_viewing", "trailing28_no_n50"]


def union_seconds(intervals, start, end):
    clipped = sorted(
        (max(s, start), min(e, end)) for s, e in intervals if s < end and e > start
    )
    total = 0.0
    left = right = None
    for s, e in clipped:
        if left is None:
            left, right = s, e
        elif s <= right:
            right = max(right, e)
        else:
            total += right - left
            left, right = s, e
    return total + (right - left if left is not None else 0.0)


def channel_statistics(database, start, cutoff):
    windows = [(start, cutoff), (max(start, cutoff - 28 * 86400), cutoff)]
    seconds = [defaultdict(dict), defaultdict(dict)]
    counts = [
        defaultdict(lambda: defaultdict(int)),
        defaultdict(lambda: defaultdict(int)),
    ]
    channels = set()
    key = None
    intervals = []

    def emit_views():
        if key is None:
            return
        u, c = key
        for k, (a, b) in enumerate(windows):
            value = union_seconds(intervals, a, b)
            if value:
                seconds[k][u][c] = value
                channels.add(c)

    with sqlite3.connect(
        "file:" + str(Path(database).resolve()) + "?mode=ro", uri=True
    ) as db:
        for u, c, s, e in db.execute(
            "SELECT u,c,s,e FROM views WHERE s < ? AND e > ? ORDER BY u,c,s,e",
            (cutoff, start),
        ):
            if (u, c) != key:
                emit_views()
                key = (u, c)
                intervals = []
            intervals.append((s, e))
        emit_views()
        key = None
        intervals = []
        duration = None
        channel = None

        def emit_airing():
            if key is None:
                return
            u, _ = key
            for k, (a, b) in enumerate(windows):
                clipped = [
                    (max(s, a), min(e, b)) for s, e in intervals if s < b and e > a
                ]
                if (
                    clipped
                    and segment_durations(clipped)["longest_block_seconds"] / duration
                    >= 0.5
                ):
                    counts[k][u][channel] += 1

        for u, airing, s, e, d in db.execute(
            "SELECT u,a,s,e,d FROM segments ORDER BY u,a,s,e"
        ):
            if (u, airing) != key:
                emit_airing()
                key = (u, airing)
                intervals = []
                duration = d
                channel = json.loads(airing)[0]
                assert duration > 0
            intervals.append((s, e))
        emit_airing()
    totals = [
        (
            {u: math.fsum(c.values()) for u, c in sec.items()},
            {u: sum(c.values()) for u, c in count.items()},
        )
        for sec, count in zip(seconds, counts)
    ]
    return {
        "seconds": seconds,
        "counts": counts,
        "totals": totals,
        "channels": channels,
        "windows": windows,
    }


def programme_weights(catalog, cutoff, end):
    durations = defaultdict(lambda: defaultdict(float))
    for channel, s, e, item in set(catalog):
        overlap = min(e, end) - max(s, cutoff)
        if overlap > 0:
            durations[item][channel] += overlap
    weights = {
        it: {c: v / math.fsum(cs.values()) for c, v in cs.items()}
        for it, cs in durations.items()
    }
    assert all(abs(math.fsum(cs.values()) - 1) < 1e-12 for cs in weights.values())
    return weights


def pair_affinity(stats, user, weights):
    row = []
    indicators = []
    for k in range(2):
        seconds = stats["seconds"][k].get(user, {})
        counts = stats["counts"][k].get(user, {})
        sec_total, n_total = stats["totals"][k][0].get(user, 0), stats["totals"][k][
            1
        ].get(user, 0)
        sec = math.fsum(w * seconds.get(c, 0) for c, w in weights.items())
        n = math.fsum(w * counts.get(c, 0) for c, w in weights.items())
        row.extend(
            [
                math.log1p(sec),
                sec / sec_total if sec_total else 0.0,
                math.log1p(n),
                n / n_total if n_total else 0.0,
            ]
        )
        indicators.extend([int(sec_total == 0), int(n_total == 0)])
    return row + indicators


def append_affinity(base, users, items, stats, weights):
    extra = np.asarray(
        [
            pair_affinity(stats, u, weights[it])
            for u, row in zip(users, items)
            for it in row
        ],
        dtype=np.float32,
    )
    if len(base) != len(extra) or base.shape[1] != 40:
        raise ValueError("Original40 row alignment required.")
    x = np.concatenate([base, extra], axis=1)
    assert (
        x.shape == (len(base), 52)
        and np.array_equal(x[:, :40], base)
        and np.isfinite(x).all()
    )
    return x, extra
