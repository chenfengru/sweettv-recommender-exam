"""Frozen v3/C/D comparisons on main and overlapping auxiliary temporal splits.

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
from .improvement_helpers import complete
from .interactions import extract_interactions, targets, csv_rows
from .metrics import average_precision_at_k
from .models import Ranker
from .opportunity_week import (
    prediction_airing_counts,
    qualified_viewing_weeks,
    controlled_order,
    distinction_diagnostics,
)
from .personal_ties import global_qualified_statistics
from .real_matching_audit import stamp
from .validate_submission import validate_submission

START, MAIN_CUTOFF, AUX_CUTOFF, END, FUTURE_END = map(
    stamp, ["2020-03-09", "2020-05-18", "2020-06-01", "2020-07-27", "2020-10-19"]
)
ORIGINAL = Path("artifacts/model_comparison_20261029")
V3 = Path("submissions/candidate_personal_tie_popularity_20261030_v3.csv")
V3_HASH = "39aac2794395209b2299ccee2e2bb1b4b9afde22f3e06ccb5b04f3d706c9522f"
DEFINITION = Path("docs/opportunity_week_protocol.md")


def rank_all(
    qualified,
    week_feature,
    airings,
    candidates,
    viewers,
    total,
    fallback,
    users,
    variant,
):
    predictions = {}
    sizes = {}
    for u in users:
        counts = qualified.get(u, {})
        order = controlled_order(
            counts,
            candidates,
            viewers,
            total,
            variant,
            airings=airings,
            weeks=week_feature.get(u, {}),
        )
        base = controlled_order(counts, candidates, viewers, total)
        assert [counts[it] for it in order[:5]] == [
            counts[it] for it in base[:5]
        ], "Personal-count precedence changed"
        predictions[u], sizes[u] = complete(order, fallback, candidates)
        base_pred, _ = complete(base, fallback, candidates)
        if set(predictions[u]) != set(base_pred):
            assert (
                len(base) > 5 and counts[base[4]] == counts[base[5]]
            ), "Membership changed without count-boundary tie"
    return predictions, sizes


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
    feature_start = time.perf_counter()
    qualified, weeks, week_stats = qualified_viewing_weeks(
        fit_cache / "segments.sqlite", START, fit_end
    )
    assert qualified == dict(
        model.qualified
    ), "Week extraction changed qualified counts"
    week_seconds = time.perf_counter() - feature_start
    diagnostics = distinction_diagnostics(
        qualified, candidates, viewers, total, users, opportunities, weeks
    )
    (out / "feature_diagnostics.json").write_text(
        json.dumps(
            {
                "ties": diagnostics,
                "schedule": schedule_stats,
                "weeks": week_stats,
                "week_extraction_seconds": week_seconds,
            },
            indent=2,
        )
        + "\n"
    )
    (private / "qualified_weeks.json").write_text(
        json.dumps(weeks, separators=(",", ":")) + "\n"
    )
    (private / "truth.json").write_text(json.dumps(truth, separators=(",", ":")) + "\n")
    result = {}
    predictions = {}
    ap = {}
    for variant in ["v3", "C", "D"]:
        start = time.perf_counter()
        pred, sizes = rank_all(
            qualified,
            weeks,
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
            "personal_count_precedence_preserved": True,
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
        assert abs(result["v3"]["map_at_5"] - 0.32685399399399395) < 1e-12
        assert predictions["v3"] == json.loads(
            Path(
                "artifacts/personal_ties_20261030_v3/popularity_predictions.json"
            ).read_text()
        )
    rng = np.random.default_rng(42)
    diff = {v: np.array([ap[v][u] - ap["v3"][u] for u in users]) for v in ["C", "D"]}
    samples = {v: [] for v in diff}
    for _ in range(2000):
        indices = rng.integers(len(users), size=len(users))
        for v in diff:
            samples[v].append(float(diff[v][indices].mean()))
    for v, d in diff.items():
        result[v].update(
            {
                "delta_from_v3": float(d.mean()),
                "users_improved": int(np.sum(d > 0)),
                "users_worsened": int(np.sum(d < 0)),
                "users_unchanged_ap": int(np.sum(d == 0)),
                "prediction_changes": list_difference(
                    {u: predictions[v][u] for u in users},
                    {u: predictions["v3"][u] for u in users},
                ),
                "paired_user_bootstrap_95pct_interval": np.quantile(
                    samples[v], [0.025, 0.975]
                ).tolist(),
                "bootstrap_resamples": 2000,
                "seed": 42,
                "uncertainty": "Conditional on this split cohort; not adjusted for model selection or repeated overlapping experiments.",
            }
        )
        assert result[v]["fallback"] == result["v3"]["fallback"]
    summary = {
        "split": name,
        "fit_window_seconds": [START, fit_end],
        "validation_window_seconds": [fit_end, END],
        "results": result,
        "truth_policy": "unchanged 80% longest-block, top-five frequency, raw string ID target ties; all users with positive targets",
        "auxiliary_is_independent_test": False,
        "qualified_user_airings": week_stats["qualified_user_airings"],
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
                "deltas": {v: result[v]["delta_from_v3"] for v in ["C", "D"]},
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
    assert sha256_file(V3) == V3_HASH
    # Preserve all previous prediction artifacts, not merely the current baseline.
    old_hashes = {
        str(p): sha256_file(p) for p in sorted(Path("submissions").glob("*.csv"))
    }
    (args.output_dir / "baseline_score_evidence.json").write_text(
        json.dumps(
            {
                "recorded_at_utc": datetime.now(timezone.utc).isoformat(),
                "file": str(V3),
                "csv_sha256": V3_HASH,
                "local_map_at_5": 0.32685399399399395,
                "private_score": 0.39697,
                "public_score": 0.40288,
                "source": "User-confirmed screenshot values in the request; no independent Kaggle lookup. Screenshot binary not supplied to this tool run.",
                "submission_id": None,
                "submission_timestamp": None,
                "best_submitted_baseline": "v3 personal count then global qualified popularity",
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
    # This is the one predeclared new temporal comparison, rebuilt from original inputs.
    aux_fit, args_fit_manifest = extract_interactions(
        args.data_dir / "dataset11-30.csv",
        paths,
        START,
        AUX_CUTOFF,
        args.private_dir / "auxiliary/train",
        input_hashes=inputs,
    )
    aux_val, args_val_manifest = extract_interactions(
        args.data_dir / "dataset11-30.csv",
        paths,
        AUX_CUTOFF,
        END,
        args.private_dir / "auxiliary/validation",
        input_hashes=inputs,
    )
    aux_opportunities, aux_stats = prediction_airing_counts(paths, AUX_CUTOFF, END)
    aux_truth = targets(aux_val, set(aux_opportunities))
    auxiliary = evaluate_split(
        "auxiliary",
        aux_fit,
        args.private_dir / "auxiliary/train",
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
        for v in ["C", "D"]
        if main["results"][v]["delta_from_v3"] > 0
        and auxiliary["results"][v]["delta_from_v3"] > 0
    ]
    selected = "v3"
    if len(eligible) == 1:
        selected = eligible[0]
    elif (
        len(eligible) == 2
        and main["results"]["C"]["map_at_5"] != main["results"]["D"]["map_at_5"]
    ):
        selected = max(eligible, key=lambda v: main["results"][v]["map_at_5"])
    selection = {
        "selected": selected,
        "eligible_variants": eligible,
        "rule": "strict improvement relative to within-split v3 on BOTH splits; highest main MAP if both; exact main tie retains v3",
        "main_deltas": {v: main["results"][v]["delta_from_v3"] for v in ["C", "D"]},
        "auxiliary_deltas": {
            v: auxiliary["results"][v]["delta_from_v3"] for v in ["C", "D"]
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
    if selected != "v3":
        make_candidate(args, selection, paths, template_users)
    else:
        (args.output_dir / "candidate_decision.json").write_text(
            json.dumps(
                {
                    "decision": "Neither variant uniquely satisfies improvement on both splits; retain submitted v3 and generate no new prediction CSV.",
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
    qualified, weeks, week_stats = qualified_viewing_weeks(
        cache / "segments.sqlite", START, END
    )
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
        weeks,
        opportunities,
        candidates,
        viewers,
        total,
        model.fallback,
        users,
        selection["selected"],
    )
    baseline = {r["user_id"]: r["tv_show_id"].split(" ") for r in csv_rows(V3)}
    changes = list_difference(pred, baseline)
    if changes["users_changed"] == 0:
        (args.output_dir / "candidate_decision.json").write_text(
            json.dumps(
                {
                    "decision": "Selected configuration duplicates submitted v3 on final predictions; no duplicate CSV generated.",
                    "changes": changes,
                },
                indent=2,
            )
            + "\n"
        )
        return
    suffix = "airing_count" if selection["selected"] == "C" else "qualified_weeks"
    path = (
        args.candidate_path
        or Path("submissions") / f"candidate_personal_{suffix}_20261030_v4.csv"
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
        "differences_from_submitted_v3": changes,
        "combined_fit_manifest": manifest,
        "combined_week_statistics": week_stats,
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
