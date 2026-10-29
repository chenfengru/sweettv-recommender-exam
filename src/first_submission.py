"""Bounded recency comparison, combined-window refit and validated first artifact.

This module never sends anything to Kaggle. Submission is a separate, single
user-authorized browser action after the exact CSV is validated.
"""

import argparse
import csv
import hashlib
import json
import math
import sqlite3
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from .audit_data import _environment
from .csv_io import sha256_file
from .interactions import extract_interactions, schedule_catalog, csv_rows
from .intervals import segment_durations
from .metrics import mean_average_precision_at_k
from .models import Ranker
from .real_matching_audit import stamp
from .validate_submission import validate_submission

HALF_LIVES = (28, 56)
START, VALIDATION_CUTOFF, FINAL_CUTOFF, PREDICTION_END = map(
    stamp, ["2020-03-09", "2020-05-18", "2020-07-27", "2020-10-19"]
)


def recency_weight(airing_end, cutoff, half_life_days):
    if half_life_days <= 0:
        raise ValueError("half-life must be positive")
    age_days = max(0.0, (cutoff - airing_end) / 86400.0)
    return 2.0 ** (-age_days / half_life_days)


def qualified_recency_counts(database, cutoff):
    """Reuse canonical per-airing segments, retaining original duration denominator."""
    db = sqlite3.connect("file:" + str(Path(database).resolve()) + "?mode=ro", uri=True)
    scores = {h: defaultdict(dict) for h in HALF_LIVES}
    counts = defaultdict(dict)
    airing_weights = {}
    key, segments, duration, item = None, [], 0, None
    qualified = 0

    def consume():
        nonlocal qualified
        if key is None:
            return
        values = segment_durations(segments)
        if values["longest_block_seconds"] / duration < 0.8:
            return
        qualified += 1
        user, airing = key
        # row ID is the canonical [channel,start,end,item] key from the existing extractor.
        if airing not in airing_weights:
            end = json.loads(airing)[2]
            airing_weights[airing] = {
                h: recency_weight(end, cutoff, h) for h in HALF_LIVES
            }
        counts[user][item] = counts[user].get(item, 0) + 1
        for h in HALF_LIVES:
            scores[h][user][item] = (
                scores[h][user].get(item, 0.0) + airing_weights[airing][h]
            )

    for user, airing, it, s, e, d in db.execute(
        "SELECT u,a,item,s,e,d FROM segments ORDER BY u,a,s,e"
    ):
        if key != (user, airing):
            consume()
            key, segments, duration, item = (user, airing), [], d, it
        segments.append((s, e))
    consume()
    db.close()
    return scores, counts, qualified


def rank_weighted(user, scores, candidates, fallback):
    values = scores.get(user, {})
    selected = sorted(
        (it for it in values if it in candidates), key=lambda it: (-values[it], it)
    )[:5]
    primary_count = len(selected)
    for it in fallback:
        if len(selected) == 5:
            break
        if it not in selected:
            selected.append(it)
    assert (
        len(selected) == len(set(selected)) == 5
        and "0" not in selected
        and set(selected) <= candidates
    )
    return selected, primary_count


def verify_interaction_cache(path):
    manifest = json.loads((path / "manifest.json").read_text())
    assert sha256_file(path / "interactions.json") == manifest["output_sha256"]
    return manifest


def run(args):
    began = time.perf_counter()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    args.private_dir.mkdir(parents=True, exist_ok=True)
    recorded_at = datetime.now(timezone.utc).isoformat()
    original = Path("artifacts/model_comparison_20261029")
    setup = json.loads((original / "setup.json").read_text())
    truth = json.loads((original / "truth.json").read_text())
    assert len(truth) == 4625 and len(setup["candidates"]) == 6384
    train_manifest = verify_interaction_cache(original / "train")
    assert (train_manifest["config"]["start"], train_manifest["config"]["end"]) == (
        START,
        VALIDATION_CUTOFF,
    )
    train = json.loads((original / "train/interactions.json").read_text())
    candidates = set(setup["candidates"])
    baseline = Ranker(train, candidates, {}, "personal")
    base_predictions = {u: baseline.recommend(u)[0] for u in truth}
    base_score = mean_average_precision_at_k(truth, base_predictions)
    established = json.loads(
        Path("results/model_comparison_20261029/personal.json").read_text()
    )
    assert abs(base_score - established["map_at_5"]) < 1e-12
    scores, unweighted, qualified = qualified_recency_counts(
        original / "train/segments.sqlite", VALIDATION_CUTOFF
    )
    expected = {(u, it): n for u, it, _, n in train if n}
    assert {
        (u, it): n for u, v in unweighted.items() for it, n in v.items()
    } == expected
    results = {"personal_original": {"map_at_5": base_score, "half_life_days": None}}
    for half in HALF_LIVES:
        predictions = {
            u: rank_weighted(u, scores[half], candidates, baseline.fallback)[0]
            for u in truth
        }
        score = mean_average_precision_at_k(truth, predictions)
        results[f"personal_half_life_{half}d"] = {
            "map_at_5": score,
            "half_life_days": half,
        }
        (args.private_dir / f"validation_recency_{half}d_predictions.json").write_text(
            json.dumps(predictions, separators=(",", ":")) + "\n"
        )
    # Original wins an exact score tie. No alternative grid or target change.
    selected = min(
        results,
        key=lambda name: (
            -results[name]["map_at_5"],
            results[name]["half_life_days"] is not None,
            name,
        ),
    )
    experiment = {
        "started_at_utc": recorded_at,
        "methods": results,
        "selected": selected,
        "selection": "largest fixed-cohort MAP@5; original method wins score ties",
        "evaluation_users": len(truth),
        "candidate_count": len(candidates),
        "qualified_training_airings": qualified,
        "formula": "2 ** (-max(0, (airing_end_to_cutoff_seconds)/86400) / half_life_days)",
        "age_origin": "full canonical airing end; clamped to zero across cutoff",
        "unchanged": "qualified target, cleaning, candidates, repeats, string-ID tie-break and unweighted shared popularity fallback",
        "elapsed_seconds": time.perf_counter() - began,
        "environment": _environment(),
    }
    assert experiment["elapsed_seconds"] < 20 * 60, "Improvement time budget exceeded"
    (args.output_dir / "recency_experiment.json").write_text(
        json.dumps(experiment, indent=2) + "\n"
    )
    print(
        json.dumps(
            {
                "local_results": results,
                "selected": selected,
                "elapsed_seconds": experiment["elapsed_seconds"],
            }
        ),
        flush=True,
    )
    inputs = {
        name: sha256_file(args.data_dir / name)
        for name in [
            "dataset11-30.csv",
            "export_arh_11-20-final.csv",
            "export_arh_21-30-final.csv",
            "export_arh_31-42-final.csv",
            "submission.csv",
        ]
    }
    audit = json.loads(Path("results/local_audit_20261029/data_audit.json").read_text())
    assert inputs == {f["filename"]: f["sha256"] for f in audit["files"]}
    fit_paths = [
        args.data_dir / "export_arh_11-20-final.csv",
        args.data_dir / "export_arh_21-30-final.csv",
    ]
    final_records, manifest = extract_interactions(
        args.data_dir / "dataset11-30.csv",
        fit_paths,
        START,
        FINAL_CUTOFF,
        args.private_dir / "combined_fit",
        input_hashes=inputs,
    )
    # This is ONE extraction over the combined window, never an addition of split qualifications.
    prediction_paths = [
        args.data_dir / "export_arh_21-30-final.csv",
        args.data_dir / "export_arh_31-42-final.csv",
    ]
    airings, _, _ = schedule_catalog(
        prediction_paths, FINAL_CUTOFF, PREDICTION_END, FINAL_CUTOFF
    )
    final_candidates = {a.item_id for a in airings}
    assert len(final_candidates) == 6649
    final_baseline = Ranker(final_records, final_candidates, {}, "personal")
    half = results[selected]["half_life_days"]
    if half is not None:
        final_scores, final_counts, final_qualified = qualified_recency_counts(
            args.private_dir / "combined_fit/segments.sqlite", FINAL_CUTOFF
        )
        assert {(u, it): n for u, v in final_counts.items() for it, n in v.items()} == {
            (u, it): n for u, it, _, n in final_records if n
        }
    template = list(csv_rows(args.data_dir / "submission.csv"))
    predictions = {}
    primary = []
    for row in template:
        u = row["user_id"]
        pred, n = (
            final_baseline.recommend(u)
            if half is None
            else rank_weighted(
                u, final_scores[half], final_candidates, final_baseline.fallback
            )
        )
        predictions[u] = pred
        primary.append(n)
    suffix = "original" if half is None else f"hl{half}d"
    csv_path = Path("submissions") / f"first_personal_{suffix}_20261029_v1.csv"
    assert (
        not csv_path.exists()
    ), "Refusing to overwrite versioned first-submission artifact"
    with csv_path.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["user_id", "tv_show_id"])
        writer.writerows(
            (r["user_id"], " ".join(predictions[r["user_id"]])) for r in template
        )
    validation = validate_submission(
        args.data_dir / "submission.csv",
        csv_path,
        final_candidates,
        user_column="user_id",
        prediction_column="tv_show_id",
    )
    (args.private_dir / "final_candidate_ids.json").write_text(
        json.dumps(sorted(final_candidates))
    )
    # Publish a derived, window-filtered schedule for independent CLI validation. It has no user data.
    candidate_path = args.output_dir / "final_window_candidate_ids.csv"
    with candidate_path.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["tv_show_id"])
        writer.writerows((it,) for it in sorted(final_candidates))
    artifact = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "method": selected,
        "half_life_days": half,
        "local_validation_map_at_5": results[selected]["map_at_5"],
        "fit_window_wall": ["2020-03-09 00:00:00", "2020-07-27 00:00:00"],
        "prediction_window_wall": ["2020-07-27 00:00:00", "2020-10-19 00:00:00"],
        "csv_absolute_path": str(csv_path.resolve()),
        "csv_sha256": sha256_file(csv_path),
        "candidate_ids_sha256": sha256_file(candidate_path),
        "validation": validation,
        "combined_fit_manifest": manifest,
        "input_sha256": inputs,
        "complete_fallback_users": sum(n == 0 for n in primary),
        "partial_completion_users": sum(0 < n < 5 for n in primary),
        "elapsed_seconds_including_experiment_and_refit": time.perf_counter() - began,
        "submission_status": "validated_not_yet_submitted",
        "authorized_submission_count": 1,
        "environment": _environment(),
    }
    (args.output_dir / "first_artifact.json").write_text(
        json.dumps(artifact, indent=2) + "\n"
    )
    print(
        json.dumps(
            {
                "artifact": str(csv_path.resolve()),
                "sha256": artifact["csv_sha256"],
                "validation": validation,
            }
        ),
        flush=True,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--private-dir", type=Path, required=True)
    run(parser.parse_args())
