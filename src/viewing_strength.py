"""Exact viewing-strength scores and personal-only retrieval diagnostics."""

import math
from collections import Counter
from .personal_ties import personal_order


def strength_counts(n50, n80, variant):
    if variant not in {"v5", "L05", "L10"}:
        raise ValueError("Unknown frozen strength variant")
    scale, bonus = {"v5": (1, 0), "L05": (2, 1), "L10": (1, 1)}[variant]
    assert all(
        n50.get(u, {}).get(it, 0) >= n for u, c in n80.items() for it, n in c.items()
    )
    return {
        u: {it: scale * n + bonus * n80.get(u, {}).get(it, 0) for it, n in c.items()}
        for u, c in n50.items()
    }


def retrieval_diagnostics(truth, n50, candidates, viewers, total):
    global_items = {it for c in n50.values() for it in c}
    buckets = Counter({k: 0 for k in ["1–5", "6–20", "21–50", "beyond_50", "absent"]})
    covered, relevant_total, macro, oracle = 0, 0, [], []
    absent_other, absent_none = 0, 0
    for u, target in truth.items():
        relevant = set(target)
        assert relevant
        order = personal_order(
            n50.get(u, {}),
            candidates,
            variant="popularity",
            viewers=viewers,
            total=total,
        )
        ranks = {it: rank for rank, it in enumerate(order, 1)}
        h = len(relevant & ranks.keys())
        covered += h
        relevant_total += len(relevant)
        macro.append(h / len(relevant))
        oracle.append(min(5, h) / min(5, len(relevant)))
        for it in relevant:
            rank = ranks.get(it)
            if rank is None:
                buckets["absent"] += 1
                # Truth is available; absence means this user has no N50 airing.
                assert it in candidates and it not in n50.get(u, {})
                if it in global_items:
                    absent_other += 1
                else:
                    absent_none += 1
            else:
                key = (
                    "1–5"
                    if rank <= 5
                    else (
                        "6–20" if rank <= 20 else "21–50" if rank <= 50 else "beyond_50"
                    )
                )
                buckets[key] += 1
    assert sum(buckets.values()) == relevant_total
    assert absent_other + absent_none == buckets["absent"]
    return {
        "evaluation_users": len(truth),
        "macro_personal_history_recall": math.fsum(macro) / len(macro),
        "micro_relevant_covered": covered,
        "micro_relevant_total": relevant_total,
        "micro_relevant_coverage": covered / relevant_total,
        "relevant_rank_buckets": dict(buckets),
        "personal_history_only_oracle_map_at_5": math.fsum(oracle) / len(oracle),
        "absent_with_other_users_n50": absent_other,
        "absent_without_any_n50": absent_none,
        "oracle_scope": "Diagnostic upper bound for personal-history-only retrieval; not attainable model performance or a bound for full system with fallback.",
    }
