"""Frozen viewing-strength comparisons on main and overlapping auxiliary temporal splits.

This module has no Kaggle network, browser, upload or submission functionality.
"""

import argparse
import csv
import json
import math
import subprocess
import sys
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
from .audit_data import _environment
from .compare_models import history_slice, versions
from .csv_io import sha256_file
from .experiment_personal_ties import list_difference
from .first_submission import verify_interaction_cache
from .interactions import extract_interactions, csv_rows
from .metrics import average_precision_at_k
from .models import Ranker
from .personal_threshold import personal_counts, predict
from .viewing_strength import strength_counts, retrieval_diagnostics
from .interactions import schedule_catalog
from .personal_ties import global_qualified_statistics
from .real_matching_audit import stamp
from .validate_submission import validate_submission

START, MAIN_CUTOFF, AUX_CUTOFF, END, FUTURE_END = map(
    stamp, ["2020-03-09", "2020-05-18", "2020-06-01", "2020-07-27", "2020-10-19"]
)
ORIGINAL = Path("artifacts/model_comparison_20261029")
BASELINE = Path("submissions/candidate_personal_threshold_050_20261030_v5.csv")
BASELINE_HASH = "593b1134b6625771abfe107e17d074499cedf6efb4ef9306e06289e9566876e5"
DEFINITION = Path("docs/viewing_strength_protocol.md")


def prediction_airing_counts(paths, start, end):
    airings, conflicts, metadata = schedule_catalog(paths, start, end, start)
    return {a.item_id: 1 for a in airings}, {
        "candidate_count": len({a.item_id for a in airings}),
        "conflicts": len(conflicts),
    }


def rank_all(
    qualified, features, airings, candidates, viewers, total, fallback, users, variant
):
    scores = strength_counts(features[0.5], features[0.8], variant)
    return predict(scores, candidates, viewers, total, fallback, users)


def evaluate_split(
    name,
    fit_records,
    fit_cache,
    fit_end,
    truth,
    opportunities,
    schedule_stats,
    template_users,
    out,
    private,
    manifests,
):
    began = time.perf_counter()
    out.mkdir(parents=True, exist_ok=True)
    private.mkdir(parents=True, exist_ok=True)
    candidates = set(opportunities)
    users = sorted(truth)
    prediction_users = sorted(set(users) | set(template_users))
    assert users and len(candidates) >= 5
    model = Ranker(fit_records, candidates, {}, "personal")
    viewers, total = global_qualified_statistics(fit_records)
    assert (
        sorted(candidates, key=lambda it: (-viewers[it], -total[it], it))
        == model.fallback
    )
    count_features = personal_counts(
        fit_cache / "segments.sqlite", START, fit_end, thresholds=(0.5, 0.8)
    )
    qualified = count_features[0.8]
    assert qualified == dict(model.qualified), "Reference personal counts changed"
    count_statistics = {
        "qualified_user_airings": sum(sum(c.values()) for c in qualified.values())
    }
    anchors = {
        "truth": truth,
        "viewers": dict(viewers),
        "total": dict(total),
        "fallback": model.fallback,
        "slices": {u: history_slice(len(qualified.get(u, {}))) for u in users},
        "candidates": sorted(candidates),
    }
    import hashlib

    digest = lambda: hashlib.sha256(
        json.dumps(anchors, sort_keys=True).encode()
    ).hexdigest()
    anchor_hash = digest()
    diagnostics = retrieval_diagnostics(
        truth, count_features[0.5], candidates, viewers, total
    )
    (out / "retrieval_diagnostics.json").write_text(
        json.dumps(diagnostics, indent=2) + "\n"
    )
    (out / "frozen_anchors.json").write_text(
        json.dumps(
            {
                "sha256": anchor_hash,
                "components": "truth, >=80% global viewer/airing counts, fallback, original history slices, candidates",
            },
            indent=2,
        )
        + "\n"
    )
    result = {}
    predictions = {}
    ap = {}
    for variant in ["v5", "L05", "L10"]:
        start = time.perf_counter()
        pred, sizes = rank_all(
            qualified,
            count_features,
            opportunities,
            candidates,
            viewers,
            total,
            model.fallback,
            prediction_users,
            variant,
        )
        runtime = time.perf_counter() - start
        values = {u: average_precision_at_k(truth[u], pred[u]) for u in users}
        slices = defaultdict(list)
        for u, value in values.items():
            slices[history_slice(len(qualified.get(u, {})))].append(value)
        result[variant] = {
            "map_at_5": math.fsum(values.values()) / len(users),
            "evaluation_users": len(users),
            "candidates": len(candidates),
            "inference_users": len(prediction_users),
            "history_slices": {
                s: {"users": len(v), "map_at_5": math.fsum(v) / len(v)}
                for s, v in sorted(slices.items())
            },
            "fallback": {
                "complete_users": sum(sizes[u] == 0 for u in users),
                "partial_completion_users": sum(0 < sizes[u] < 5 for u in users),
                "completion_slots": sum(5 - sizes[u] for u in users),
            },
            "ranking_and_completion_seconds": runtime,
            "all_predictions_valid": True,
            "scaled_integer_score_ranking": True,
        }
        predictions[variant] = pred
        ap[variant] = values
        (private / f"{variant}_predictions.json").write_text(
            json.dumps(pred, separators=(",", ":")) + "\n"
        )
        (private / f"{variant}_ap.json").write_text(
            json.dumps(values, separators=(",", ":")) + "\n"
        )
    if name == "main":
        assert len(users) == 4625 and len(candidates) == 6384
        assert abs(result["v5"]["map_at_5"] - 0.33471117117117116) < 1e-12
        assert predictions["v5"] == json.loads(
            Path(
                "artifacts/personal_threshold_20261030_v5/main/T50_predictions.json"
            ).read_text()
        )
    reference_path = (
        Path("artifacts/personal_threshold_20261030_v5/auxiliary/T50_predictions.json")
        if name == "auxiliary"
        else Path("artifacts/personal_threshold_20261030_v5/main/T50_predictions.json")
    )
    assert predictions["v5"] == json.loads(reference_path.read_text())
    rng = np.random.default_rng(42)
    diff = {
        v: np.array([ap[v][u] - ap["v5"][u] for u in users]) for v in ["L05", "L10"]
    }
    samples = {v: [] for v in diff}
    for _ in range(2000):
        indices = rng.integers(len(users), size=len(users))
        for v in diff:
            samples[v].append(float(diff[v][indices].mean()))
    for v, d in diff.items():
        result[v].update(
            {
                "delta_from_v5": float(d.mean()),
                "users_improved": int(np.sum(d > 0)),
                "users_worsened": int(np.sum(d < 0)),
                "users_unchanged_ap": int(np.sum(d == 0)),
                "prediction_changes": list_difference(
                    {u: predictions[v][u] for u in users},
                    {u: predictions["v5"][u] for u in users},
                ),
                "paired_user_bootstrap_95pct_interval": np.quantile(
                    samples[v], [0.025, 0.975]
                ).tolist(),
                "bootstrap_resamples": 2000,
                "seed": 42,
                "uncertainty": "Conditional on this split cohort; not adjusted for model selection or repeated overlapping experiments.",
            }
        )
        assert digest() == anchor_hash

    summary = {
        "split": name,
        "fit_window_seconds": [START, fit_end],
        "validation_window_seconds": [fit_end, END],
        "results": result,
        "truth_policy": "unchanged 80% longest-block, top-five frequency, raw string ID target ties; all users with positive targets",
        "auxiliary_is_independent_test": False,
        "qualified_user_airings": count_statistics["qualified_user_airings"],
        "source_cache_manifests": manifests,
        "elapsed_evaluation_seconds": time.perf_counter() - began,
        "dependencies": versions(),
        "environment": _environment(),
    }
    (out / "comparison.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(
        json.dumps(
            {
                "split": name,
                "users": len(users),
                "candidates": len(candidates),
                "scores": {v: r["map_at_5"] for v, r in result.items()},
                "deltas": {v: result[v]["delta_from_v5"] for v in ["L05", "L10"]},
            }
        ),
        flush=True,
    )
    return summary


def run(args):
    start = time.perf_counter()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    args.private_dir.mkdir(parents=True, exist_ok=True)
    frozen = json.loads((args.output_dir / "frozen_experiment.json").read_text())
    assert sha256_file(DEFINITION) == frozen["definition_sha256"]
    assert sha256_file(BASELINE) == BASELINE_HASH
    # Preserve all previous prediction artifacts, not merely the current baseline.
    old_hashes = {
        str(p): sha256_file(p) for p in sorted(Path("submissions").glob("*.csv"))
    }
    (args.output_dir / "baseline_score_evidence.json").write_text(
        json.dumps(
            {
                "recorded_at_utc": datetime.now(timezone.utc).isoformat(),
                "file": str(BASELINE),
                "csv_sha256": BASELINE_HASH,
                "local_map_at_5": 0.33471117117117116,
                "private_score": 0.40210,
                "public_score": 0.41789,
                "source": "User-confirmed screenshot values in the request; no independent Kaggle lookup. Screenshot binary not supplied to this tool run.",
                "submission_id": None,
                "submission_timestamp": None,
                "best_submitted_baseline": "v5 T50 personal count then original >=80% global qualified popularity",
                "previous_artifacts_sha256": old_hashes,
            },
            indent=2,
        )
        + "\n"
    )
    manifest = verify_interaction_cache(ORIGINAL / "train")
    inputs = {
        name: sha256_file(args.data_dir / name) for name in manifest["config"]["inputs"]
    }
    assert inputs == manifest["config"]["inputs"]
    paths = [
        args.data_dir / "export_arh_11-20-final.csv",
        args.data_dir / "export_arh_21-30-final.csv",
    ]
    template_users = [r["user_id"] for r in csv_rows(args.data_dir / "submission.csv")]
    records = json.loads((ORIGINAL / "train/interactions.json").read_text())
    truth = json.loads((ORIGINAL / "truth.json").read_text())
    opportunities, stats = prediction_airing_counts(paths, MAIN_CUTOFF, END)
    main = evaluate_split(
        "main",
        records,
        ORIGINAL / "train",
        MAIN_CUTOFF,
        truth,
        opportunities,
        stats,
        template_users,
        args.output_dir / "main",
        args.private_dir / "main",
        {"fit": manifest, "validation_truth": "existing frozen main truth cache"},
    )
    del records, truth, opportunities
    aux_cache = Path("artifacts/opportunity_week_20261030_v4/auxiliary")
    args_fit_manifest = verify_interaction_cache(aux_cache / "train")
    args_val_manifest = verify_interaction_cache(aux_cache / "validation")
    aux_fit = json.loads((aux_cache / "train/interactions.json").read_text())
    aux_truth = json.loads((aux_cache / "truth.json").read_text())
    aux_opportunities, aux_stats = prediction_airing_counts(paths, AUX_CUTOFF, END)
    auxiliary = evaluate_split(
        "auxiliary",
        aux_fit,
        aux_cache / "train",
        AUX_CUTOFF,
        aux_truth,
        aux_opportunities,
        aux_stats,
        template_users,
        args.output_dir / "auxiliary",
        args.private_dir / "auxiliary",
        {"fit": args_fit_manifest, "validation": args_val_manifest},
    )
    eligible = [
        v
        for v in ["L05", "L10"]
        if main["results"][v]["delta_from_v5"] > 0
        and auxiliary["results"][v]["delta_from_v5"] > 0
    ]
    selected = "v5"
    if len(eligible) == 1:
        selected = eligible[0]
    elif (
        len(eligible) == 2
        and main["results"]["L05"]["map_at_5"] != main["results"]["L10"]["map_at_5"]
    ):
        selected = max(eligible, key=lambda v: main["results"][v]["map_at_5"])
    selection = {
        "selected": selected,
        "eligible_variants": eligible,
        "rule": "strict improvement relative to within-split v5 on BOTH splits; highest main MAP if both; exact selection tie retains v5",
        "main_deltas": {v: main["results"][v]["delta_from_v5"] for v in ["L05", "L10"]},
        "auxiliary_deltas": {
            v: auxiliary["results"][v]["delta_from_v5"] for v in ["L05", "L10"]
        },
        "auxiliary_limitation": "overlapping robustness check, not an independent untouched test",
        "frozen_definition_sha256": sha256_file(DEFINITION),
        "total_experiment_seconds": time.perf_counter() - start,
        "input_sha256": inputs,
        "preserved_previous_artifact_sha256": old_hashes,
        "environment": _environment(),
    }
    (args.output_dir / "selection.json").write_text(
        json.dumps(selection, indent=2) + "\n"
    )
    print(
        json.dumps(
            {
                "selection": selection["selected"],
                "eligible": eligible,
                "main_deltas": selection["main_deltas"],
                "auxiliary_deltas": selection["auxiliary_deltas"],
            }
        ),
        flush=True,
    )
    if selected != "v5":
        make_candidate(args, selection, paths, template_users)
    else:
        (args.output_dir / "candidate_decision.json").write_text(
            json.dumps(
                {
                    "decision": "Neither variant uniquely satisfies improvement on both splits; retain submitted v5 and generate no new prediction CSV.",
                    "selection": selection["selected"],
                },
                indent=2,
            )
            + "\n"
        )
    assert sha256_file(DEFINITION) == frozen["definition_sha256"]
    for path, digest in old_hashes.items():
        assert sha256_file(Path(path)) == digest


def make_candidate(args, selection, fit_paths, users):
    start = time.perf_counter()
    cache = Path("artifacts/first_submission_20261029/combined_fit")
    records, manifest = extract_interactions(
        args.data_dir / "dataset11-30.csv",
        fit_paths,
        START,
        END,
        cache,
        input_hashes=selection["input_sha256"],
    )
    count_features = personal_counts(
        cache / "segments.sqlite", START, END, thresholds=(0.5, 0.8)
    )
    qualified = count_features[0.8]
    count_statistics = {
        "personal_threshold": 0.5,
        "strength_variant": selection["selected"],
        "lambda": {"L05": 0.5, "L10": 1.0}[selection["selected"]],
        "combined_window_recomputed": True,
    }
    expected = {(u, it): n for u, it, _, n in records if n}
    assert {(u, it): n for u, c in qualified.items() for it, n in c.items()} == expected
    opportunities, schedule_stats = prediction_airing_counts(
        [
            args.data_dir / "export_arh_21-30-final.csv",
            args.data_dir / "export_arh_31-42-final.csv",
        ],
        END,
        FUTURE_END,
    )
    candidates = set(opportunities)
    assert len(candidates) == 6649
    model = Ranker(records, candidates, {}, "personal")
    viewers, total = global_qualified_statistics(records)
    pred, sizes = rank_all(
        qualified,
        count_features,
        opportunities,
        candidates,
        viewers,
        total,
        model.fallback,
        users,
        selection["selected"],
    )
    baseline = {r["user_id"]: r["tv_show_id"].split(" ") for r in csv_rows(BASELINE)}
    reference, _ = rank_all(
        qualified,
        count_features,
        opportunities,
        candidates,
        viewers,
        total,
        model.fallback,
        users,
        "v5",
    )
    assert reference == baseline
    changes = list_difference(pred, baseline)
    if changes["users_changed"] == 0:
        (args.output_dir / "candidate_decision.json").write_text(
            json.dumps(
                {
                    "decision": "Selected configuration duplicates submitted v5 on final predictions; no duplicate CSV generated.",
                    "changes": changes,
                },
                indent=2,
            )
            + "\n"
        )
        return
    suffix = (
        "strength_lambda_05" if selection["selected"] == "L05" else "strength_lambda_10"
    )
    path = (
        args.candidate_path
        or Path("submissions") / f"candidate_personal_{suffix}_20261030_v6.csv"
    )
    assert not path.exists(), "Refusing to overwrite a versioned CSV"
    with (args.data_dir / "submission.csv").open(newline="") as f:
        header = next(csv.reader(f))
    with path.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows((u, " ".join(pred[u])) for u in users)
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
    artifact = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "validated for manual user review; no Kaggle action performed",
        "selected_variant": selection["selected"],
        "csv_filename": path.name,
        "csv_absolute_path": str(path.resolve()),
        "csv_sha256": sha256_file(path),
        "validation": validation,
        "differences_from_submitted_v5": changes,
        "combined_fit_manifest": manifest,
        "combined_count_statistics": count_statistics,
        "prediction_airing_statistics": schedule_stats,
        "fit_window_wall": ["2020-03-09 00:00:00", "2020-07-27 00:00:00"],
        "prediction_window_wall": ["2020-07-27 00:00:00", "2020-10-19 00:00:00"],
        "selection_rule": selection["rule"],
        "refit_and_validation_seconds": time.perf_counter() - start,
        "environment": _environment(),
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
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--data-dir", type=Path, required=True)
    p.add_argument("--output-dir", type=Path, required=True)
    p.add_argument("--private-dir", type=Path, required=True)
    p.add_argument("--candidate-path", type=Path)
    run(p.parse_args())
