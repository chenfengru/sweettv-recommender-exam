"""Seven schedule-only exposure features; no viewing or content inputs."""

import math
from collections import defaultdict
import numpy as np
from .interactions import csv_rows
from .real_matching_audit import stamp
from .reranker_features import FEATURES

SCHEDULE_FEATURES = [
    "past_airings_per_day",
    "future_airings_per_day",
    "past_broadcast_seconds_per_day",
    "future_broadcast_seconds_per_day",
    "log_airings_rate_change",
    "log_broadcast_rate_change",
    "past_airings_zero",
]
EXTENDED_FEATURES = FEATURES + SCHEDULE_FEATURES


def canonical_schedule(paths):
    unique = {}
    source = []
    for path in paths:
        rows = accepted = duplicates = 0
        first = last = None
        for row in csv_rows(path):
            rows += 1
            it = row["tv_show_id"]
            duration = float(row["duration"])
            if (
                it == "0"
                or not it.strip()
                or not math.isfinite(duration)
                or duration <= 0
            ):
                continue
            start = stamp(row["start_time"], True)
            end = start + duration
            key = (row["channel_id"], start, end, it)
            duplicates += key in unique
            unique.setdefault(key, key)
            accepted += 1
            first = start if first is None else min(first, start)
            last = end if last is None else max(last, end)
        source.append(
            {
                "file": str(path),
                "rows": rows,
                "valid_rows": accepted,
                "duplicates_against_previous_rows": duplicates,
                "min_start": first,
                "max_end": last,
            }
        )
    return list(unique.values()), source


def merged_coverage(intervals, start, end):
    intervals = sorted(
        (max(s, start), min(e, end)) for s, e in intervals if s < end and e > start
    )
    covered = 0
    cursor = start
    gaps = []
    for s, e in intervals:
        if s > cursor:
            gaps.append([cursor, s])
        if e > cursor:
            covered += e - max(cursor, s)
            cursor = e
    if cursor < end:
        gaps.append([cursor, end])
    return covered, gaps


def exposure_window(catalog, start, end):
    if end <= start:
        raise ValueError("Invalid exposure window")
    counts = defaultdict(int)
    seconds = defaultdict(float)
    channels = defaultdict(list)
    for channel, s, e, item in sorted(set(catalog)):
        if item == "0" or not item.strip() or e <= s:
            continue
        if s < end and e > start:
            counts[item] += 1
            seconds[item] += min(e, end) - max(s, start)
            channels[channel].append((s, e))
    covered, gaps = merged_coverage(
        [interval for values in channels.values() for interval in values], start, end
    )
    per_channel = [
        merged_coverage(values, start, end)[0] / (end - start)
        for values in channels.values()
    ]
    days = (end - start) / 86400
    report = {
        "window": [start, end],
        "full_window_days": days,
        "canonical_airings": sum(counts.values()),
        "programmes": len(counts),
        "channels": len(channels),
        "global_covered_seconds": covered,
        "required_seconds": end - start,
        "global_coverage_fraction": covered / (end - start),
        "global_gaps": gaps,
        "channel_coverage_fraction": {
            "min": min(per_channel) if per_channel else None,
            "median": float(np.median(per_channel)) if per_channel else None,
            "max": max(per_channel) if per_channel else None,
        },
        "coverage_gate_passed": not gaps and covered == end - start,
    }
    return dict(counts), dict(seconds), report


def schedule_origin(catalog, cutoff, prediction_end, *, require_coverage=True):
    past_count, past_seconds, past_report = exposure_window(
        catalog, cutoff - 28 * 86400, cutoff
    )
    future_count, future_seconds, future_report = exposure_window(
        catalog, cutoff, prediction_end
    )
    if require_coverage and not (
        past_report["coverage_gate_passed"] and future_report["coverage_gate_passed"]
    ):
        raise ValueError(
            "Required schedule coverage unavailable; do not encode missing coverage as zero"
        )
    past_days = 28
    future_days = (prediction_end - cutoff) / 86400
    features = {}
    for item in set(past_count) | set(future_count):
        pa = past_count.get(item, 0) / past_days
        fa = future_count.get(item, 0) / future_days
        ps = past_seconds.get(item, 0) / past_days
        fs = future_seconds.get(item, 0) / future_days
        features[item] = [
            pa,
            fa,
            ps,
            fs,
            math.log1p(fa) - math.log1p(pa),
            math.log1p(fs) - math.log1p(ps),
            int(past_count.get(item, 0) == 0),
        ]
    assert all(np.isfinite(row).all() for row in features.values())
    return features, {
        "past": past_report,
        "future": future_report,
        "new_features": SCHEDULE_FEATURES,
        "missing_schedule_coverage_imputed": False,
    }


def distribution(matrix, names):
    return {
        name: {
            "count": len(matrix),
            "min": float(matrix[:, j].min()),
            "mean": float(matrix[:, j].mean()),
            "median": float(np.median(matrix[:, j])),
            "p90": float(np.quantile(matrix[:, j], 0.9)),
            "max": float(matrix[:, j].max()),
            "zero_fraction": float(np.mean(matrix[:, j] == 0)),
        }
        for j, name in enumerate(names)
    }


def augment(base, items, schedule):
    additions = np.asarray(
        [schedule[it] for row in items for it in row], dtype=np.float32
    )
    if len(additions) != len(base):
        raise ValueError("Candidate row count mismatch")
    if np.any(additions[:, 1] <= 0):
        raise ValueError("Original candidate missing positive future schedule exposure")
    matrix = np.concatenate([base, additions], axis=1)
    if matrix.shape[1] != 34 or not np.isfinite(matrix).all():
        raise ValueError("Invalid extended feature schema")
    assert np.array_equal(matrix[:, :27], base)
    return matrix, {
        "schema": EXTENDED_FEATURES,
        "all_finite": True,
        "original_27_exactly_equal": True,
        "new_feature_missing_values": 0,
        "candidate_row_distributions": distribution(additions, SCHEDULE_FEATURES),
        "candidate_programme_distributions": distribution(
            np.asarray(
                [schedule[it] for it in sorted({it for row in items for it in row})],
                dtype=np.float64,
            ),
            SCHEDULE_FEATURES,
        ),
    }


def exposure_group(row):
    delta = row[5]
    return "increased" if delta > 0 else "decreased" if delta < 0 else "unchanged"
