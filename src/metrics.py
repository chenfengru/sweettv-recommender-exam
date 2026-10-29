"""Ranking metrics for an explicit, shared evaluation cohort."""

from collections.abc import Iterable, Mapping
from math import fsum


def average_precision_at_k(actual: Iterable, predicted: Iterable, k: int = 5) -> float:
    if not isinstance(k, int) or isinstance(k, bool) or k <= 0:
        raise ValueError("k must be a positive integer")
    relevant = set(actual)
    if not relevant:
        return 0.0
    seen, hits, terms = set(), 0, []
    for rank, item in enumerate(predicted, 1):
        if rank > k:
            break
        if item in relevant and item not in seen:
            hits += 1
            terms.append(hits / rank)
        seen.add(item)
    return fsum(terms) / min(k, len(relevant))


def mean_average_precision_at_k(actual: Mapping, predicted: Mapping, k: int = 5) -> float:
    """Include exactly the supplied users; empty truth gives AP=0, no silent drop."""
    if not actual:
        raise ValueError("evaluation cohort is empty")
    if actual.keys() != predicted.keys():
        raise ValueError("truth and predictions must contain exactly the same user keys")
    return fsum(average_precision_at_k(truth, predicted[user], k) for user, truth in actual.items()) / len(actual)
