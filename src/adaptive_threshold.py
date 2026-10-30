"""Training-only H80 assignment and fixed adaptive count/list selection."""

from collections import defaultdict


def h80_from_records(records):
    items = defaultdict(set)
    for u, it, _, n80 in records:
        if n80 > 0:
            items[u].add(it)
    return {u: len(programmes) for u, programmes in items.items()}


def adaptation_eligible(h80):
    return 1 <= h80 <= 5


def select_counts(u, n50, lower, h80):
    return (lower if adaptation_eligible(h80.get(u, 0)) else n50).get(u, {})


def adaptive_predictions(baseline, lower, h80):
    return {
        u: list(lower[u] if adaptation_eligible(h80.get(u, 0)) else ranking)
        for u, ranking in baseline.items()
    }
