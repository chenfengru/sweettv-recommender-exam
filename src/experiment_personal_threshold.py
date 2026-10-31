"""Frozen personal training-threshold comparisons on main and overlapping auxiliary temporal splits.

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
from .personal_threshold import personal_counts, predict
from .interactions import schedule_catalog
from .personal_ties import global_qualified_statistics
from .real_matching_audit import stamp
from .validate_submission import validate_submission

START, MAIN_CUTOFF, AUX_CUTOFF, END, FUTURE_END = map(
    stamp, ["2020-03-09", "2020-05-18", "2020-06-01", "2020-07-27", "2020-10-19"]
)
ORIGINAL = Path("artifacts/model_comparison_20261029")
V3 = Path("submissions/candidate_personal_tie_popularity_20261030_v3.csv")
V3_HASH = "39aac2794395209b2299ccee2e2bb1b4b9afde22f3e06ccb5b04f3d706c9522f"
DEFINITION = Path("docs/personal_threshold_protocol.md")


def prediction_airing_counts(paths, start, end):
    airings, conflicts, metadata = schedule_catalog(paths, start, end, start)
    return {a.item_id: 1 for a in airings}, {
        "candidate_count": len({a.item_id for a in airings}),
        "conflicts": len(conflicts),
    }


def rank_all(
    qualified, features, airings, candidates, viewers, total, fallback, users, variant
):
    threshold = {"v3": 0.8, "T50": 0.5, "T65": 0.65}[variant]
    return predict(features[threshold], candidates, viewers, total, fallback, users)


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
    weeks = personal_counts(fit_cache / "segments.sqlite", START, fit_end)
    qualified = weeks[0.8]
    assert qualified == dict(model.qualified), "Reference personal counts changed"
    week_stats = {
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
    expansion = {}
    for variant, threshold in [("T50", 0.5), ("T65", 0.65)]:
        lower = weeks[threshold]
        assert all(
            lower.get(u, {}).get(it, 0) >= n
            for u, c in qualified.items()
            for it, n in c.items()
        )
        pairs = lambda data, available: {
            (u, it)
            for u, c in data.items()
            for it in c
            if not available or it in candidates
        }
        usable = lambda data, u: bool(set(data.get(u, {})) & candidates)
        expansion[variant] = {
            "additional_training_user_item_pairs": len(
                pairs(lower, False) - pairs(qualified, False)
            ),
            "additional_available_training_user_item_pairs": len(
                pairs(lower, True) - pairs(qualified, True)
            ),
            "cohort_additional_available_pairs": sum(
                u in truth for u, it in pairs(lower, True) - pairs(qualified, True)
            ),
            "cohort_users_gaining_usable_history": sum(
                not usable(qualified, u) and usable(lower, u) for u in users
            ),
            "all_users_gaining_usable_history": sum(
                not usable(qualified, u) and usable(lower, u) for u in lower
            ),
            "personal_user_airings": sum(sum(c.values()) for c in lower.values()),
        }
    (out / "feature_diagnostics.json").write_text(
        json.dumps(
            {"expansion": expansion, "frozen_anchor_sha256": anchor_hash}, indent=2
        )
        + "\n"
    )
    result = {}
    predictions = {}
    ap = {}
    for variant in ["v3", "T50", "T65"]:
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
    reference_path = (
        Path("artifacts/opportunity_week_20261030_v4/auxiliary/v3_predictions.json")
        if name == "auxiliary"
        else Path("artifacts/personal_ties_20261030_v3/popularity_predictions.json")
    )
    assert predictions["v3"] == json.loads(reference_path.read_text())
    rng = np.random.default_rng(42)
    diff = {
        v: np.array([ap[v][u] - ap["v3"][u] for u in users]) for v in ["T50", "T65"]
    }
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
        assert digest() == anchor_hash
        result[v]["history_expansion"] = expansion[v]
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
                "deltas": {v: result[v]["delta_from_v3"] for v in ["T50", "T65"]},
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
        for v in ["T50", "T65"]
        if main["results"][v]["delta_from_v3"] > 0
        and auxiliary["results"][v]["delta_from_v3"] > 0
    ]
    selected = (
        max(eligible, key=lambda v: (main["results"][v]["map_at_5"], v == "T65"))
        if eligible
        else "v3"
    )
    selection = {
        "selected": selected,
        "eligible_variants": eligible,
        "rule": "strict improvement relative to within-split v3 on BOTH splits; highest main MAP if both; exact new-variant tie prefers T65",
        "main_deltas": {v: main["results"][v]["delta_from_v3"] for v in ["T50", "T65"]},
        "auxiliary_deltas": {
            v: auxiliary["results"][v]["delta_from_v3"] for v in ["T50", "T65"]
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
    weeks = personal_counts(cache / "segments.sqlite", START, END)
    qualified = weeks[0.8]
    week_stats = {
        "personal_threshold": selection["selected"],
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
    reference, _ = rank_all(
        qualified,
        weeks,
        opportunities,
        candidates,
        viewers,
        total,
        model.fallback,
        users,
        "v3",
    )
    assert reference == baseline
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
    suffix = "threshold_050" if selection["selected"] == "T50" else "threshold_065"
    path = (
        args.candidate_path
        or Path("submissions") / f"candidate_personal_{suffix}_20261030_v5.csv"
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
