"""Exactly two personal count-tie experiments; review-only candidate preparation."""

import argparse
import csv
import json
import math
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from collections import defaultdict
import numpy as np
from .audit_data import _environment
from .compare_models import history_slice, versions
from .csv_io import sha256_file
from .first_submission import verify_interaction_cache
from .improve_recommender import difference_stats
from .improvement_helpers import complete
from .interactions import extract_interactions, schedule_catalog, csv_rows
from .metrics import average_precision_at_k
from .models import Ranker
from .personal_ties import (
    latest_qualified_viewing,
    global_qualified_statistics,
    personal_order,
    tie_diagnostics,
)
from .real_matching_audit import stamp
from .validate_submission import validate_submission

ORIGINAL = Path("artifacts/model_comparison_20261029")
BASELINE = Path("submissions/first_personal_original_20261029_v1.csv")
RRF = Path("submissions/candidate_rrf_als_lb80_w0p1_20261029_v2.csv")
HASHES = {
    BASELINE: "53cb8ae4b59b26ab6ee00b5e99ad91044876180e662732a755d3e99a297e64bc",
    RRF: "905971a8a9c47bcf4a88e14cd10d2514feaaea43900d6f513b2eecc4986f19f5",
}
START, CUTOFF, END, FUTURE_END = map(
    stamp, ["2020-03-09", "2020-05-18", "2020-07-27", "2020-10-19"]
)
BASE_MAP = 0.3174897297297298


def list_difference(prediction, baseline):
    result = difference_stats(prediction, baseline)
    result["users_with_membership_change"] = sum(
        set(prediction[u]) != set(baseline[u]) for u in baseline
    )
    result["users_with_order_change_only"] = sum(
        prediction[u] != baseline[u] and set(prediction[u]) == set(baseline[u])
        for u in baseline
    )
    result["new_item_slots_ignoring_order"] = sum(
        len(set(prediction[u]) - set(baseline[u])) for u in baseline
    )
    return result


def predict(qualified, latest, viewers, total, users, candidates, fallback, variant):
    result = {}
    sizes = {}
    for u in users:
        counts = qualified.get(u, {})
        order = personal_order(
            counts,
            candidates,
            variant,
            latest=latest.get(u, {}),
            viewers=viewers,
            total=total,
        )
        original = personal_order(counts, candidates)
        assert [counts[it] for it in order[:5]] == [
            counts[it] for it in original[:5]
        ], "Count precedence changed"
        result[u], sizes[u] = complete(order, fallback, candidates)
        original_prediction, _ = complete(original, fallback, candidates)
        if set(result[u]) != set(original_prediction):
            assert (
                len(original) > 5 and counts[original[4]] == counts[original[5]]
            ), "Membership changed without a fifth-boundary count tie"
    return result, sizes


def run(args):
    began = time.perf_counter()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    args.private_dir.mkdir(parents=True, exist_ok=True)
    for path, expected in HASHES.items():
        assert sha256_file(path) == expected
    evidence = {
        "recorded_at_utc": datetime.now(timezone.utc).isoformat(),
        "source": "User-confirmed values from Kaggle screenshots in this request. No independent Kaggle lookup; original screenshot binaries are not supplied to this tool run.",
        "submissions": [
            {
                "file": str(BASELINE),
                "sha256": HASHES[BASELINE],
                "private_score": 0.38937,
                "public_score": 0.39131,
                "submission_id": None,
                "submission_timestamp": None,
            },
            {
                "file": str(RRF),
                "sha256": HASHES[RRF],
                "private_score": 0.38663,
                "public_score": 0.38852,
                "submission_id": None,
                "submission_timestamp": None,
            },
        ],
        "best_submitted_baseline": "original personal frequency",
        "no_kaggle_access_performed": True,
    }
    (args.output_dir / "submitted_score_evidence.json").write_text(
        json.dumps(evidence, indent=2) + "\n"
    )
    manifest = verify_interaction_cache(ORIGINAL / "train")
    assert (manifest["config"]["start"], manifest["config"]["end"]) == (START, CUTOFF)
    input_checks = {
        name: sha256_file(args.data_dir / name) == value
        for name, value in manifest["config"]["inputs"].items()
    }
    assert all(input_checks.values())
    records = json.loads((ORIGINAL / "train/interactions.json").read_text())
    setup = json.loads((ORIGINAL / "setup.json").read_text())
    truth = json.loads((ORIGINAL / "truth.json").read_text())
    assert len(truth) == 4625 and len(setup["candidates"]) == 6384
    model = Ranker(records, set(setup["candidates"]), {}, "personal")
    extraction_started = time.perf_counter()
    qualified, latest = latest_qualified_viewing(
        ORIGINAL / "train/segments.sqlite", CUTOFF
    )
    latest_seconds = time.perf_counter() - extraction_started
    assert qualified == dict(
        model.qualified
    ), "Qualified counts changed while extracting latest observed ends"
    assert all(t <= CUTOFF for values in latest.values() for t in values.values())
    viewers, total = global_qualified_statistics(records)
    assert (
        sorted(setup["candidates"], key=lambda it: (-viewers[it], -total[it], it))
        == model.fallback
    )
    diagnostics = tie_diagnostics(qualified, set(setup["candidates"]), sorted(truth))
    (args.output_dir / "tie_diagnostics.json").write_text(
        json.dumps(diagnostics, indent=2) + "\n"
    )
    (args.private_dir / "latest_observed_ends.json").write_text(
        json.dumps(latest, separators=(",", ":")) + "\n"
    )
    results = {}
    predictions = {}
    ap = {}
    for variant in ["original", "latest", "popularity"]:
        start = time.perf_counter()
        pred, size = predict(
            qualified,
            latest,
            viewers,
            total,
            setup["prediction_users"],
            set(setup["candidates"]),
            model.fallback,
            variant,
        )
        elapsed = time.perf_counter() - start
        values = {
            u: average_precision_at_k(actual, pred[u]) for u, actual in truth.items()
        }
        slices = defaultdict(list)
        for u, value in values.items():
            slices[history_slice(len(qualified.get(u, {})))].append(value)
        results[variant] = {
            "map_at_5": math.fsum(values.values()) / len(values),
            "evaluation_users": len(truth),
            "candidates": len(setup["candidates"]),
            "inference_users": len(pred),
            "ranking_and_completion_seconds": elapsed,
            "history_slices": {
                s: {"users": len(v), "map_at_5": math.fsum(v) / len(v)}
                for s, v in sorted(slices.items())
            },
            "fallback": {
                "complete_users": sum(size[u] == 0 for u in truth),
                "partial_completion_users": sum(0 < size[u] < 5 for u in truth),
                "completion_slots": sum(5 - size[u] for u in truth),
            },
            "all_qualified_counts_unchanged": True,
            "all_lists_valid": True,
        }
        predictions[variant] = pred
        ap[variant] = values
        (args.private_dir / f"{variant}_predictions.json").write_text(
            json.dumps(pred, separators=(",", ":")) + "\n"
        )
        (args.private_dir / f"{variant}_ap.json").write_text(
            json.dumps(values, separators=(",", ":")) + "\n"
        )
    assert abs(results["original"]["map_at_5"] - BASE_MAP) < 1e-12
    original_predictions = json.loads(
        (ORIGINAL / "personal_predictions.json").read_text()
    )
    assert (
        predictions["original"] == original_predictions
    ), "Original prediction lists failed exact baseline reconciliation"
    users = sorted(truth)
    rng = np.random.default_rng(42)
    diffs = {
        v: np.array([ap[v][u] - ap["original"][u] for u in users])
        for v in ["latest", "popularity"]
    }
    bootstrap = {v: [] for v in diffs}
    for _ in range(2000):
        indices = rng.integers(len(users), size=len(users))
        for v in diffs:
            bootstrap[v].append(float(diffs[v][indices].mean()))
    for v, d in diffs.items():
        changes = list_difference(
            {u: predictions[v][u] for u in users},
            {u: predictions["original"][u] for u in users},
        )
        results[v].update(
            {
                "delta_from_original": float(d.mean()),
                "users_improved": int(np.sum(d > 0)),
                "users_worsened": int(np.sum(d < 0)),
                "users_unchanged_ap": int(np.sum(d == 0)),
                "prediction_changes": changes,
                "paired_user_bootstrap_95pct_interval": np.quantile(
                    bootstrap[v], [0.025, 0.975]
                ).tolist(),
                "bootstrap_resamples": 2000,
                "bootstrap_seed": 42,
                "bootstrap_scope": "Conditional on this reused fixed cohort; no allowance for hold-out selection or Kaggle generalization.",
            }
        )
        assert results[v]["fallback"] == results["original"]["fallback"]
    score_a, score_b = results["latest"]["map_at_5"], results["popularity"]["map_at_5"]
    selected = "latest" if score_a > score_b else "popularity"
    if max(score_a, score_b) <= results["original"]["map_at_5"] or score_a == score_b:
        selected = "original"
    summary = {
        "results": results,
        "selected": selected,
        "tie_policy": "Unique stronger new score must strictly exceed original; exact score ties retain original baseline.",
        "qualified_airings": sum(n for c in qualified.values() for n in c.values()),
        "latest_extraction_seconds": latest_seconds,
        "latest_feature": "maximum observed clipped segment end across qualified airings of that user/programme; no broadcast-end recency",
        "latest_observed_end_max": max(t for c in latest.values() for t in c.values()),
        "fitting_cutoff": CUTOFF,
        "input_identities_unchanged": input_checks,
        "source_cache_manifest": manifest,
        "elapsed_seconds_local_experiment": time.perf_counter() - began,
        "dependencies": versions(),
        "environment": _environment(),
        "workflow": "Stop for user review. All Kaggle uploads and submissions are manual-only by the user.",
    }
    (args.output_dir / "comparison.json").write_text(
        json.dumps(summary, indent=2) + "\n"
    )
    print(
        json.dumps(
            {
                "scores": {v: r["map_at_5"] for v, r in results.items()},
                "selected": selected,
                "ties": diagnostics,
            }
        ),
        flush=True,
    )
    if selected != "original":
        make_candidate(args, summary)
    else:
        (args.output_dir / "candidate_decision.json").write_text(
            json.dumps(
                {
                    "decision": "Neither variant uniquely improves local validation; retain original and generate no new CSV."
                },
                indent=2,
            )
            + "\n"
        )


def make_candidate(args, summary):
    began = time.perf_counter()
    selected = summary["selected"]
    original_artifact = json.loads(
        Path("results/first_submission_20261029/first_artifact.json").read_text()
    )
    paths = [
        args.data_dir / "export_arh_11-20-final.csv",
        args.data_dir / "export_arh_21-30-final.csv",
    ]
    cache = Path("artifacts/first_submission_20261029/combined_fit")
    records, manifest = extract_interactions(
        args.data_dir / "dataset11-30.csv",
        paths,
        START,
        END,
        cache,
        input_hashes=original_artifact["input_sha256"],
    )
    qualified, latest = latest_qualified_viewing(cache / "segments.sqlite", END)
    expected = {(u, it): n for u, it, _, n in records if n}
    assert {(u, it): n for u, c in qualified.items() for it, n in c.items()} == expected
    assert sum(n for c in qualified.values() for n in c.values()) == 573003
    airings, _, _ = schedule_catalog(
        [
            args.data_dir / "export_arh_21-30-final.csv",
            args.data_dir / "export_arh_31-42-final.csv",
        ],
        END,
        FUTURE_END,
        END,
    )
    candidates = {a.item_id for a in airings}
    assert len(candidates) == 6649
    model = Ranker(records, candidates, {}, "personal")
    viewers, total = global_qualified_statistics(records)
    with (args.data_dir / "submission.csv").open(newline="") as f:
        reader = csv.DictReader(f)
        header = reader.fieldnames
        template = list(reader)
    users = [row["user_id"] for row in template]
    pred, sizes = predict(
        qualified, latest, viewers, total, users, candidates, model.fallback, selected
    )
    original = {
        row["user_id"]: row["tv_show_id"].split(" ") for row in csv_rows(BASELINE)
    }
    changes = list_difference(pred, original)
    if changes["users_changed"] == 0:
        (args.output_dir / "candidate_decision.json").write_text(
            json.dumps(
                {
                    "decision": "Local improvement but final predictions duplicate submitted baseline; no duplicate CSV generated.",
                    "differences": changes,
                },
                indent=2,
            )
            + "\n"
        )
        return
    path = (
        args.candidate_path
        or Path("submissions") / f"candidate_personal_tie_{selected}_20261030_v3.csv"
    )
    assert not path.exists(), "Refusing to overwrite an existing versioned artifact"
    with path.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(
            (row["user_id"], " ".join(pred[row["user_id"]])) for row in template
        )
    validation = validate_submission(
        args.data_dir / "submission.csv",
        path,
        candidates,
        user_column="user_id",
        prediction_column="tv_show_id",
        delimiter=",",
    )
    subprocess.run(
        [
            sys.executable,
            "-m",
            "src.validate_submission",
            "--template",
            str(args.data_dir / "submission.csv"),
            "--predictions",
            str(path),
            "--schedule",
            "results/first_submission_20261029/final_window_candidate_ids.csv",
            "--user-column",
            "user_id",
            "--prediction-column",
            "tv_show_id",
            "--delimiter",
            ",",
        ],
        check=True,
        stdout=(args.output_dir / "candidate_validator_cli.json").open("w"),
    )
    for old, digest in HASHES.items():
        assert sha256_file(old) == digest
    artifact = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "validated_candidate_awaiting_user_review; never uploaded by agent",
        "selected_variant": selected,
        "local_map_at_5": summary["results"][selected]["map_at_5"],
        "local_assessment": summary["results"][selected],
        "csv_filename": path.name,
        "csv_absolute_path": str(path.resolve()),
        "csv_sha256": sha256_file(path),
        "validation": validation,
        "differences_from_submitted_personal_baseline": changes,
        "prior_submitted_csv_checksums_preserved": {
            str(p): v for p, v in HASHES.items()
        },
        "combined_fit_manifest": manifest,
        "combined_qualification_recomputed_user_airings": 573003,
        "fitting_window_wall": ["2020-03-09 00:00:00", "2020-07-27 00:00:00"],
        "prediction_window_wall": ["2020-07-27 00:00:00", "2020-10-19 00:00:00"],
        "observed_latest_end_max": max(t for c in latest.values() for t in c.values()),
        "cutoff": END,
        "refit_and_artifact_seconds": time.perf_counter() - began,
        "environment": _environment(),
        "kaggle_submission_performed": False,
    }
    (args.output_dir / "candidate_artifact.json").write_text(
        json.dumps(artifact, indent=2) + "\n"
    )
    print(
        json.dumps(
            {
                "candidate": str(path.resolve()),
                "sha256": artifact["csv_sha256"],
                "changes": changes,
            }
        ),
        flush=True,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--private-dir", type=Path, required=True)
    parser.add_argument("--candidate-path", type=Path)
    run(parser.parse_args())
