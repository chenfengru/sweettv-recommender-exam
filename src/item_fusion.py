"""Fixed weighted RRF with exact score ties and seen/unseen attribution."""

from collections import defaultdict
from fractions import Fraction
from math import fsum


def fusion_scores(personal, collaborative, weight, candidates):
    weight = Fraction(str(weight))
    if weight not in {Fraction(1, 20), Fraction(1, 10), Fraction(1, 5)}:
        raise ValueError("Weight outside the frozen experiment")
    scores = defaultdict(Fraction)
    for ranking, coefficient in [(personal, Fraction(1)), (collaborative, weight)]:
        direct = [it for it in dict.fromkeys(ranking) if it in candidates][:50]
        for rank, it in enumerate(direct, 1):
            scores[it] += coefficient / Fraction(60 + rank)
    return dict(scores)


def fusion_order(personal, collaborative, weight, candidates, viewers, total):
    scores = fusion_scores(personal, collaborative, weight, candidates)
    return sorted(
        scores, key=lambda it: (-scores[it], -viewers.get(it, 0), -total.get(it, 0), it)
    )


def seen_unseen_effects(truth, predictions, baseline, histories):
    """Count per-user item occurrences; attribute AP terms, not causal effects."""
    stats = defaultdict(int)
    contributions = {
        "baseline_seen": [],
        "baseline_unseen": [],
        "fused_seen": [],
        "fused_unseen": [],
    }
    for u, target in truth.items():
        relevant, history = set(target), set(histories.get(u, {}))
        base, fused = set(baseline[u]), set(predictions[u])
        entering = fused - base
        leaving = base - fused
        stats["users_with_entering_unseen"] += bool(entering - history)
        for group, items in [("entering", entering), ("leaving", leaving)]:
            for kind, subset in [
                ("seen", items & history),
                ("unseen", items - history),
            ]:
                stats[f"{group}_{kind}_items"] += len(subset)
                stats[f"{group}_{kind}_relevant_hits"] += len(subset & relevant)
        for method, ranking in [("baseline", baseline[u]), ("fused", predictions[u])]:
            hits, terms = 0, {"seen": [], "unseen": []}
            for rank, it in enumerate(ranking[:5], 1):
                kind = "seen" if it in history else "unseen"
                stats[f"{method}_{kind}_recommendations"] += 1
                if it in relevant:
                    hits += 1
                    stats[f"{method}_{kind}_relevant_hits"] += 1
                    terms[kind].append(hits / rank / min(5, len(relevant)))
            for kind in terms:
                contributions[f"{method}_{kind}"].append(fsum(terms[kind]))
    result = dict(stats)
    for name, values in contributions.items():
        result[f"{name}_map_contribution"] = fsum(values) / len(truth)
    for kind in ["seen", "unseen"]:
        result[f"delta_{kind}_map_contribution"] = (
            result[f"fused_{kind}_map_contribution"]
            - result[f"baseline_{kind}_map_contribution"]
        )
    return result
