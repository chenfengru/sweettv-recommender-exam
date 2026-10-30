"""Frozen single-slot replacement; neither eligibility nor choice sees truth."""

RULES = ["E1", "E2", "E3"]


def fifth_replacement(baseline, counts, unseen_ranking, candidates, rule):
    if rule not in RULES:
        raise ValueError("Unknown frozen rule")
    assert len(baseline) == len(set(baseline)) == 5 and set(baseline) <= candidates
    available_history = {it for it, n in counts.items() if n > 0 and it in candidates}
    fifth_fallback = len(available_history) < 5 and baseline[4] not in available_history
    eligibility = {
        "E1": counts.get(baseline[4], 0) == 1,
        "E2": counts.get(baseline[3], 0) == counts.get(baseline[4], 0) == 1,
        "E3": len(available_history) < 5 and fifth_fallback,
    }
    original = set(baseline)
    replacement = next(
        (
            it
            for it in unseen_ranking[:50]
            if it in candidates
            and it != "0"
            and counts.get(it, 0) == 0
            and it not in original
        ),
        None,
    )
    predicted = list(baseline)
    changed = eligibility[rule] and replacement is not None
    if changed:
        predicted[4] = replacement
    assert (
        predicted[:4] == baseline[:4]
        and len(set(predicted)) == 5
        and set(predicted) <= candidates
    )
    if changed:
        assert predicted[4] not in original and counts.get(predicted[4], 0) == 0
    return predicted, {
        "eligible": eligibility[rule],
        "has_available_replacement": replacement is not None,
        "replaced": changed,
        "fifth_from_fallback": fifth_fallback,
    }
