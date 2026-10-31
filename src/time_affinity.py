"""Source-naive histogram affinity; cross-channel union before user binning."""

import math
import sqlite3
from pathlib import Path
from collections import defaultdict
import numpy as np

TIME_FEATURES = [
    "time_full_hour_day_affinity",
    "time_full_hour_week_affinity",
    "time_trailing28_hour_day_affinity",
    "time_trailing28_hour_week_affinity",
    "time_full_no_viewing",
    "time_trailing28_no_viewing",
]


def merge_intervals(intervals, start, end):
    merged = []
    for s, e in sorted(
        (max(s, start), min(e, end)) for s, e in intervals if s < end and e > start
    ):
        if merged and s <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], e))
        else:
            merged.append((s, e))
    return merged


def histogram(intervals):
    """Bin additive durations; caller determines whether intervals should be unioned.

    Seconds are naive calendar offsets. The naive 1970-01-01 epoch is Thursday,
    hence +72h aligns week bin zero to Monday. No timezone conversion occurs.
    """
    day = np.zeros(24, dtype=np.float64)
    week = np.zeros(168, dtype=np.float64)
    total = 0.0
    for start, end in intervals:
        if not math.isfinite(start) or not math.isfinite(end) or end < start:
            raise ValueError("Invalid interval.")
        s = start
        while s < end:
            hour = math.floor(s / 3600)
            right = min(end, (hour + 1) * 3600)
            seconds = right - s
            day[hour % 24] += seconds
            week[(hour + 72) % 168] += seconds
            total += seconds
            s = right
    assert math.isclose(float(day.sum()), total, rel_tol=1e-12, abs_tol=1e-8)
    assert math.isclose(float(week.sum()), total, rel_tol=1e-12, abs_tol=1e-8)
    return day, week, total


def normalized_histogram(intervals):
    day, week, total = histogram(intervals)
    if total:
        day /= total
        week /= total
    assert np.isfinite(day).all() and np.isfinite(week).all()
    assert (
        abs(float(day.sum()) - bool(total)) < 1e-10
        and abs(float(week.sum()) - bool(total)) < 1e-10
    )
    return day, week, total


def user_profiles(database, start, cutoff):
    windows = [(start, cutoff), (max(start, cutoff - 28 * 86400), cutoff)]
    profiles = {}
    user = None
    intervals = []

    def emit():
        if user is None:
            return
        # Union independently of channel before either window's histogram.
        union = merge_intervals(intervals, start, cutoff)
        profiles[user] = [
            normalized_histogram(merge_intervals(union, a, b)) for a, b in windows
        ]

    with sqlite3.connect(
        "file:" + str(Path(database).resolve()) + "?mode=ro", uri=True
    ) as db:
        for u, s, e in db.execute(
            "SELECT u,s,e FROM views WHERE s < ? AND e > ? ORDER BY u,s,e",
            (cutoff, start),
        ):
            if u != user:
                emit()
                user = u
                intervals = []
            intervals.append((s, e))
        emit()
    return profiles


def schedule_profiles(catalog, cutoff, end):
    intervals = defaultdict(list)
    for channel, s, e, item in set(catalog):
        if item != "0" and s < end and e > cutoff and e > s:
            intervals[item].append((max(s, cutoff), min(e, end)))
    profiles = {it: normalized_histogram(rows) for it, rows in intervals.items()}
    if not profiles or any(p[2] <= 0 for p in profiles.values()):
        raise ValueError("Available programme profile has no mass.")
    return profiles


def append_time_features(base, users, items, user_hist, programme_hist):
    if base.shape[1] != 52 or len(base) != sum(map(len, items)):
        raise ValueError("Original52 row alignment required.")
    chunks = []
    zero = (np.zeros(24), np.zeros(168), 0.0)
    for u, row in zip(users, items):
        if any(it not in programme_hist or programme_hist[it][2] <= 0 for it in row):
            raise ValueError("Required available programme lacks schedule mass.")
        day = np.asarray([programme_hist[it][0] for it in row])
        week = np.asarray([programme_hist[it][1] for it in row])
        full, trailing = user_hist.get(u, [zero, zero])
        # Elementwise sums avoid platform BLAS floating-status warnings.
        # Full-origin replay verified identical float32 features to matrix dots.
        chunks.append(
            np.column_stack(
                [
                    np.sum(day * full[0], axis=1),
                    np.sum(week * full[1], axis=1),
                    np.sum(day * trailing[0], axis=1),
                    np.sum(week * trailing[1], axis=1),
                    np.full(len(row), full[2] == 0),
                    np.full(len(row), trailing[2] == 0),
                ]
            )
        )
    extra = np.concatenate(chunks).astype(np.float32)
    x = np.concatenate([base, extra], axis=1)
    assert (
        x.shape == (len(base), 58)
        and np.array_equal(x[:, :52], base)
        and np.isfinite(x).all()
    )
    assert np.all(extra[:, :4] >= 0) and np.all(extra[:, :4] <= 1 + 1e-6)
    return x, extra
