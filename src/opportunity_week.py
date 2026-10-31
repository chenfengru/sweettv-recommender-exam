"""Permitted schedule opportunities and observed qualified viewing-week features."""

import math
import sqlite3
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from .csv_io import is_zero_id
from .interactions import csv_rows
from .intervals import segment_durations
from .real_matching_audit import stamp

EPOCH = datetime(1970, 1, 1)


def monday_week(source_wall_seconds):
    day = (EPOCH + timedelta(seconds=source_wall_seconds)).date()
    return (day - timedelta(days=day.weekday())).isoformat()


def prediction_airing_counts(schedule_paths, start, end):
    """Read only item/channel/start/duration; count canonical intersecting broadcasts."""
    canonical = set()
    counts = Counter()
    source_rows = 0
    duplicates = 0
    for path in schedule_paths:
        for row in csv_rows(path):
            item = row["tv_show_id"]
            if not item.strip() or is_zero_id(item):
                continue
            duration = float(row["duration"])
            if not math.isfinite(duration):
                raise ValueError("Nonfinite schedule duration")
            if duration <= 0:
                continue
            s = stamp(row["start_time"], True)
            e = s + duration
            if not (s < end and e > start):
                continue
            source_rows += 1
            key = (row["channel_id"], s, e, item)
            if key in canonical:
                duplicates += 1
                continue
            canonical.add(key)
            counts[item] += 1
    return dict(counts), {
        "intersecting_source_rows": source_rows,
        "duplicate_canonical_rows_beyond_first": duplicates,
        "canonical_intersecting_airings": len(canonical),
        "distinct_programme_ids": len(counts),
        "minimum_airings_per_item": min(counts.values()) if counts else None,
        "maximum_airings_per_item": max(counts.values()) if counts else None,
        "feature_fields": ["tv_show_id", "channel_id", "start_time", "duration"],
        "interval_rule": "half-open intersection; canonical full endpoints preserved; distinct channels counted separately",
    }


def qualified_viewing_weeks(database, fit_start, cutoff):
    """Assign a qualified user-airing once to its first observed clipped start week."""
    db = sqlite3.connect("file:" + str(Path(database).resolve()) + "?mode=ro", uri=True)
    qualified = defaultdict(dict)
    weeks = defaultdict(lambda: defaultdict(set))
    key = None
    segments = []
    duration = 0
    item = None
    first_min = first_max = None
    airings = 0

    def consume():
        nonlocal first_min, first_max, airings
        if key is None or not segments:
            return
        if segment_durations(segments)["longest_block_seconds"] / duration < 0.8:
            return
        first = min(s for s, _ in segments)
        assert fit_start <= first < cutoff
        first_min = first if first_min is None else min(first_min, first)
        first_max = first if first_max is None else max(first_max, first)
        user = key[0]
        qualified[user][item] = qualified[user].get(item, 0) + 1
        weeks[user][item].add(monday_week(first))
        airings += 1

    for u, a, it, s, e, d in db.execute(
        "SELECT u,a,item,s,e,d FROM segments ORDER BY u,a,s,e"
    ):
        if s >= cutoff or e <= fit_start or e <= s:
            continue
        s, e = max(s, fit_start), min(e, cutoff)
        if e <= s:
            continue
        if key != (u, a):
            consume()
            key, segments, duration, item = (u, a), [], d, it
        segments.append((s, e))
    consume()
    db.close()
    feature = {
        u: {it: len(w) for it, w in values.items()} for u, values in weeks.items()
    }
    assert all(
        1 <= n <= qualified[u][it]
        for u, values in feature.items()
        for it, n in values.items()
    )
    return (
        dict(qualified),
        feature,
        {
            "qualified_user_airings": airings,
            "first_observed_start_min": first_min,
            "first_observed_start_max": first_max,
            "fit_start": fit_start,
            "cutoff": cutoff,
            "maximum_distinct_weeks": max(
                (n for values in feature.values() for n in values.values()), default=0
            ),
            "week_rule": "source-wall-calendar Monday; qualified airing assigned once by first observed clipped segment start",
        },
    )


def controlled_order(
    counts, candidates, viewers, total, variant="v3", airings=None, weeks=None
):
    items = [it for it in counts if it in candidates]
    if variant == "v3":
        return sorted(
            items,
            key=lambda it: (-counts[it], -viewers.get(it, 0), -total.get(it, 0), it),
        )
    if variant == "C":
        if airings is None or any(it not in airings for it in items):
            raise ValueError("Candidate opportunity feature missing")
        feature = airings
    elif variant == "D":
        if weeks is None or any(it not in weeks for it in items):
            raise ValueError("Qualified week feature missing")
        feature = weeks
    else:
        raise ValueError(variant)
    return sorted(
        items,
        key=lambda it: (
            -counts[it],
            -feature[it],
            -viewers.get(it, 0),
            -total.get(it, 0),
            it,
        ),
    )


def distinction_diagnostics(
    qualified, candidates, viewers, total, users, airings, weeks
):
    counters = {v: Counter() for v in ["C", "D"]}
    for user in users:
        counts = qualified.get(user, {})
        order = controlled_order(counts, candidates, viewers, total)
        top = set(order[:5])
        groups = defaultdict(list)
        for it in order:
            groups[counts[it]].append(it)
        boundary = (
            counts[order[4]]
            if len(order) > 5 and counts[order[4]] == counts[order[5]]
            else None
        )
        for variant in ["C", "D"]:
            feature = airings if variant == "C" else weeks.get(user, {})
            any_tie = relevant = internal = crossing = False
            for count, items in groups.items():
                if len(items) < 2:
                    continue
                if len({feature[it] for it in items}) > 1:
                    any_tie = True
                    relevant |= bool(set(items) & top)
                    crossing |= count == boundary
                selected = [it for it in items if it in top]
                internal |= (
                    len(selected) > 1 and len({feature[it] for it in selected}) > 1
                )
            for name, value in [
                ("any_equal_count_group_distinguished", any_tie),
                ("top5_relevant_tie_group_distinguished", relevant),
                ("within_selected_top5_tie_distinguished", internal),
                ("fifth_boundary_tie_distinguished", crossing),
            ]:
                counters[variant][name] += value
    return {
        "cohort_users": len(users),
        "features": {v: dict(n) for v, n in counters.items()},
        "definitions": "Potential distinctions within positive-count available items. Relevant groups intersect baseline direct top5; within-selected compares selected members only; boundary uses baseline count at ranks5/6. Fallback excluded. Counts need not equal actual changes.",
    }
