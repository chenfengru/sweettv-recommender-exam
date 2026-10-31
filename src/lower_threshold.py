"""Newly included user-airing diagnostics; reuse the canonical count extractor."""

import math
from collections import defaultdict
import numpy as np
from .personal_threshold import personal_counts


def duration_summary(values):
    if not values:
        return {"count": 0}
    array = np.asarray(values, dtype=np.float64)
    return {
        "count": len(values),
        "mean": math.fsum(values) / len(values),
        "min": float(array.min()),
        "p10": float(np.quantile(array, 0.1)),
        "median": float(np.median(array)),
        "p90": float(np.quantile(array, 0.9)),
        "p95": float(np.quantile(array, 0.95)),
        "max": float(array.max()),
    }


def lower_counts(db, start, cutoff, cohort, candidates):
    noise = {
        t: {scope: defaultdict(list) for scope in ["all_training", "available_cohort"]}
        for t in [0.3, 0.4]
    }

    def observe(u, item, duration, values):
        fraction = values["longest_block_seconds"] / duration
        if fraction >= 0.5:
            return
        for threshold in noise:
            if fraction < threshold:
                continue
            scopes = ["all_training"] + (
                ["available_cohort"] if u in cohort and item in candidates else []
            )
            for scope in scopes:
                target = noise[threshold][scope]
                target["full_airing_seconds"].append(duration)
                target["longest_observed_block_seconds"].append(
                    values["longest_block_seconds"]
                )
                target["total_observed_union_seconds"].append(values["union_seconds"])
                target["longest_block_fraction"].append(fraction)

    counts = personal_counts(
        db, start, cutoff, thresholds=(0.3, 0.4, 0.5), airing_observer=observe
    )
    for low, high in [(0.3, 0.4), (0.4, 0.5)]:
        assert all(
            counts[low].get(u, {}).get(it, 0) >= n
            for u, c in counts[high].items()
            for it, n in c.items()
        )
    summary = {
        str(t): {
            scope: {name: duration_summary(values) for name, values in groups.items()}
            for scope, groups in scopes.items()
        }
        for t, scopes in noise.items()
    }
    base = sum(sum(c.values()) for c in counts[0.5].values())
    for t in [0.3, 0.4]:
        assert sum(sum(c.values()) for c in counts[t].values()) - base == summary[
            str(t)
        ]["all_training"].get("full_airing_seconds", {}).get("count", 0)
    return counts, summary
