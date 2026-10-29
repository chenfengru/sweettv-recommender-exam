"""Equal-count personal-frequency tie diagnostics and two fixed tie-break rules."""

import sqlite3
from collections import Counter, defaultdict
from pathlib import Path
from .intervals import segment_durations


def latest_qualified_viewing(database, cutoff):
    """Return qualified counts and latest OBSERVED segment ends, never airing ends.

    The cache already contains cleaned, canonical per-airing intersections. Clip
    again at cutoff so even a supplied future tail cannot affect qualification
    or its latest observed end. The original full airing duration is preserved.
    """
    db = sqlite3.connect("file:" + str(Path(database).resolve()) + "?mode=ro", uri=True)
    counts = defaultdict(dict)
    latest = defaultdict(dict)
    key = None
    segments = []
    item = None
    duration = 0

    def consume():
        if key is None or not segments:
            return
        values = segment_durations(segments)
        if values["longest_block_seconds"] / duration < 0.8:
            return
        u = key[0]
        counts[u][item] = counts[u].get(item, 0) + 1
        observed_end = max(e for _, e in segments)
        assert observed_end <= cutoff
        latest[u][item] = max(latest[u].get(item, float("-inf")), observed_end)

    for u, a, it, s, e, d in db.execute(
        "SELECT u,a,item,s,e,d FROM segments ORDER BY u,a,s,e"
    ):
        if s >= cutoff or e <= s:
            continue
        e = min(e, cutoff)
        if e <= s:
            continue
        if key != (u, a):
            consume()
            key, segments, item, duration = (u, a), [], it, d
        segments.append((s, e))
    consume()
    db.close()
    return dict(counts), dict(latest)


def global_qualified_statistics(records):
    viewers = Counter()
    total = Counter()
    for _, item, _, qualified in records:
        if qualified:
            viewers[item] += 1
            total[item] += qualified
    return viewers, total


def personal_order(
    counts, candidates, variant="original", latest=None, viewers=None, total=None
):
    items = [it for it in counts if it in candidates]
    if variant == "latest":
        if latest is None or any(it not in latest for it in items):
            raise ValueError("Every qualified item requires an observed pre-cutoff end")
        return sorted(items, key=lambda it: (-counts[it], -latest[it], it))
    if variant == "popularity":
        viewers = viewers or {}
        total = total or {}
        return sorted(
            items,
            key=lambda it: (-counts[it], -viewers.get(it, 0), -total.get(it, 0), it),
        )
    if variant != "original":
        raise ValueError(variant)
    return sorted(items, key=lambda it: (-counts[it], it))


def tie_diagnostics(qualified, candidates, users):
    within = boundary = both = any_tie = at_least_six = 0
    full_sizes = Counter()
    inside_sizes = Counter()
    outside_sizes = Counter()
    joint = Counter()
    tied_counts = Counter()
    eligible_sizes = Counter()
    for user in users:
        counts = qualified.get(user, {})
        order = personal_order(counts, candidates)
        eligible_sizes[str(min(len(order), 6))] += 1
        top = order[:5]
        top_counts = Counter(counts[it] for it in top)
        internal = any(n >= 2 for n in top_counts.values())
        crossing = len(order) > 5 and counts[order[4]] == counts[order[5]]
        within += internal
        boundary += crossing
        both += internal and crossing
        any_tie += internal or crossing
        at_least_six += len(order) >= 6
        if crossing:
            count = counts[order[4]]
            full = sum(counts[it] == count for it in order)
            inside = sum(counts[it] == count for it in top)
            outside = full - inside
            full_sizes[str(full)] += 1
            inside_sizes[str(inside)] += 1
            outside_sizes[str(outside)] += 1
            joint[(full, inside, outside)] += 1
            tied_counts[str(count)] += 1
    return {
        "cohort_users": len(users),
        "users_with_equal_counts_within_selected_direct_top5": within,
        "users_with_count_tie_crossing_fifth_position": boundary,
        "users_with_both": both,
        "users_with_either_order_or_boundary_tie": any_tie,
        "users_with_at_least_six_available_qualified_items": at_least_six,
        "boundary_full_group_size_histogram": dict(
            sorted(full_sizes.items(), key=lambda x: int(x[0]))
        ),
        "boundary_inside_top5_size_histogram": dict(inside_sizes),
        "boundary_outside_top5_size_histogram": dict(outside_sizes),
        "boundary_group_joint_histogram": [
            {
                "full_group_size": f,
                "inside_original_top5": i,
                "outside_original_top5": o,
                "users": n,
            }
            for (f, i, o), n in sorted(joint.items())
        ],
        "boundary_qualified_count_histogram": dict(tied_counts),
        "available_qualified_item_count_0_to_5_or_6plus": dict(eligible_sizes),
        "definitions": "Within-top5 tie means at least two directly ranked selected items have the same positive qualified count. Boundary tie means direct ranks 5 and 6 have equal counts. Fallback items are excluded; ties can overlap these two categories.",
    }
