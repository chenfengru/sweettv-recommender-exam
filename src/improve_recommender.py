"""Bounded local ALS/CBF/RRF experiments; manual-review artifacts only. No Kaggle I/O."""

import argparse
import csv
import hashlib
import json
import math
import os
import subprocess
import sys
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
from implicit.cpu.als import AlternatingLeastSquares
from threadpoolctl import threadpool_limits
from .audit_data import _environment
from .compare_models import history_slice, rss, versions
from .csv_io import sha256_file
from .first_submission import verify_interaction_cache
from .improvement_helpers import (
    filtered_airing_interactions,
    direct_ranking,
    complete,
    rrf_rank,
    popularity_viewers,
)
from .interactions import extract_interactions, schedule_catalog, csv_rows
from .metrics import average_precision_at_k
from .models import Ranker
from .real_matching_audit import stamp
from .validate_submission import validate_submission

START, CUTOFF, END, FUTURE_END = map(
    stamp, ["2020-03-09", "2020-05-18", "2020-07-27", "2020-10-19"]
)
ORIGINAL = Path("artifacts/model_comparison_20261029")
BASELINE = Path("submissions/first_personal_original_20261029_v1.csv")
BASELINE_SHA = "53cb8ae4b59b26ab6ee00b5e99ad91044876180e662732a755d3e99a297e64bc"


def evaluate(name, direct, setup, truth, out, private, *, extra=None):
    began = time.perf_counter()
    candidates = set(setup["candidates"])
    fallback = setup["fallback"]
    predictions = {}
    sizes = {}
    for u in setup["prediction_users"]:
        predictions[u], sizes[u] = complete(direct.get(u, []), fallback, candidates)
    ap = {
        u: average_precision_at_k(actual, predictions[u]) for u, actual in truth.items()
    }
    slices = defaultdict(list)
    for u, value in ap.items():
        slices[history_slice(setup["qualified_history_sizes"].get(u, 0))].append(value)
    summary = {
        "name": name,
        "map_at_5": math.fsum(ap.values()) / len(ap),
        "evaluation_users": len(ap),
        "candidate_count": len(candidates),
        "history_slices": {
            s: {"users": len(v), "map_at_5": math.fsum(v) / len(v)}
            for s, v in sorted(slices.items())
        },
        "fallback": {
            "complete_users": sum(sizes[u] == 0 for u in truth),
            "partial_completion_users": sum(0 < sizes[u] < 5 for u in truth),
            "completion_slots": sum(5 - sizes[u] for u in truth),
        },
        "direct_ranking_limit": 50,
        "all_lists_valid": True,
        "evaluation_and_completion_seconds": time.perf_counter() - began,
    }
    summary.update(extra or {})
    (private / f"{name}_direct_top50.json").write_text(
        json.dumps(direct, separators=(",", ":")) + "\n"
    )
    (private / f"{name}_predictions.json").write_text(
        json.dumps(predictions, separators=(",", ":")) + "\n"
    )
    (private / f"{name}_ap.json").write_text(
        json.dumps(ap, separators=(",", ":")) + "\n"
    )
    summary["prediction_sha256"] = sha256_file(private / f"{name}_predictions.json")
    (out / f"{name}.json").write_text(json.dumps(summary, indent=2) + "\n")
    return summary, predictions, ap


def get_model(name, records, candidates, metadata):
    if name.startswith("als_lb"):
        return Ranker(
            records,
            candidates,
            {},
            "als",
            factors=32,
            regularization=0.1,
            iterations=20,
            seed=42,
        )
    if name in ("cbf_pop_tie", "cbf_original"):
        return Ranker(records, candidates, metadata, "cbf")
    if name == "als_original":
        model = Ranker(records, candidates, {}, "personal")
        model.method = "als"
        model.als = AlternatingLeastSquares.load(ORIGINAL / "als_f32_r0.1_model.npz")
        model.supported_candidates = [
            it for it in model.candidates if it in model.item_index
        ]
        model.candidate_factors = model.als.item_factors[
            [model.item_index[it] for it in model.supported_candidates]
        ]
        return model
    return Ranker(records, candidates, {}, "personal")


def worker(args):
    setup = json.loads((args.private_dir / "setup.json").read_text())
    truth = json.loads((ORIGINAL / "truth.json").read_text())
    path = (
        args.private_dir / f"{args.worker}_training.json"
        if args.worker.startswith("als_lb")
        else ORIGINAL / "train/interactions.json"
    )
    records = json.loads(path.read_text())
    candidates = set(setup["candidates"])
    began = time.perf_counter()
    with threadpool_limits(limits=1):
        model = get_model(args.worker, records, candidates, setup["metadata"])
        fit_elapsed = time.perf_counter() - began
        assert model.fallback == setup["fallback"], "Shared popularity fallback changed"
        began = time.perf_counter()
        pop = (
            {it: n for it, n in setup["popularity_viewers"].items()}
            if args.worker == "cbf_pop_tie"
            else None
        )
        direct = {
            u: direct_ranking(model, u, cbf_popularity=pop)
            for u in setup["prediction_users"]
        }
        inference = time.perf_counter() - began
        supported = (
            int(np.sum(np.diff(model.candidate_content.indptr) > 0))
            if model.method == "cbf"
            else len(model.supported_candidates)
        )
        result, _, _ = evaluate(
            args.worker,
            direct,
            setup,
            truth,
            args.output_dir,
            args.private_dir,
            extra={
                "config": {
                    "method": model.method,
                    "longest_block_training_threshold": (
                        0.5
                        if args.worker == "als_lb50"
                        else 0.8 if args.worker == "als_lb80" else None
                    ),
                    "als_factors": 32 if model.method == "als" else None,
                    "regularization": 0.1 if model.method == "als" else None,
                    "iterations": 20 if model.method == "als" else None,
                    "confidence": "1 + 40*log1p(s_ui); library alpha=1",
                    "cbf_tie_break": (
                        "exact cosine; qualified-viewer count descending; raw ID"
                        if pop
                        else "raw ID"
                    ),
                    "seed": 42,
                },
                "supported_candidate_items": supported,
                "supported_candidate_fraction": supported / len(candidates),
                "fitting_users": len(model.users),
                "fitting_items": len(model.items),
                "fitting_user_item_pairs": len(records),
                "fit_or_existing_model_load_seconds": fit_elapsed,
                "direct_inference_seconds": inference,
                "peak_worker_rss_bytes": rss(),
                "dependencies": versions(),
                "environment": _environment(),
                "training_fingerprint": model.fingerprint(),
                "original_training_reused": args.worker == "als_original",
            },
        )
        if args.worker == "cbf_pop_tie":
            old_direct = {
                u: direct_ranking(model, u) for u in setup["prediction_users"]
            }
            old, _, _ = evaluate(
                "cbf_original",
                old_direct,
                setup,
                truth,
                args.output_dir,
                args.private_dir,
                extra={
                    "result_kind": "existing baseline replay; same fitted features/profiles, only ID tie-break"
                },
            )
            expected = json.loads(
                Path("results/model_comparison_20261029/cbf.json").read_text()
            )
            assert abs(old["map_at_5"] - expected["map_at_5"]) < 1e-12
            assert (
                model.fingerprint() == expected["model_fingerprint"]
            ), "CBF fitted features changed"
    print(
        json.dumps(
            {
                "name": args.worker,
                "map_at_5": result["map_at_5"],
                "supported_items": supported,
            }
        ),
        flush=True,
    )


def difference_stats(predictions, baseline, truth=None):
    users = sorted(baseline)
    unchanged = sum(predictions[u] == baseline[u] for u in users)
    slots = sum(a != b for u in users for a, b in zip(predictions[u], baseline[u]))
    intersections = sum(len(set(predictions[u]) & set(baseline[u])) for u in users)
    return {
        "users": len(users),
        "users_changed": len(users) - unchanged,
        "users_identical": unchanged,
        "recommendation_slots": len(users) * 5,
        "rank_position_slots_changed": slots,
        "top5_items_in_common": intersections,
        "top5_set_overlap_fraction": intersections / (len(users) * 5),
    }


def run(args):
    started = time.perf_counter()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    args.private_dir.mkdir(parents=True, exist_ok=True)
    assert sha256_file(BASELINE) == BASELINE_SHA
    manifest = verify_interaction_cache(ORIGINAL / "train")
    for name, expected in manifest["config"]["inputs"].items():
        assert sha256_file(args.data_dir / name) == expected, (
            "Input identity changed: " + name
        )
    records = json.loads((ORIGINAL / "train/interactions.json").read_text())
    truth = json.loads((ORIGINAL / "truth.json").read_text())
    setup = json.loads((ORIGINAL / "setup.json").read_text())
    assert len(truth) == 4625 and len(setup["candidates"]) == 6384
    personal = Ranker(records, set(setup["candidates"]), {}, "personal")
    setup.update(
        {
            "fallback": personal.fallback,
            "qualified_history_sizes": {
                u: len(v) for u, v in personal.qualified.items()
            },
            "popularity_viewers": dict(popularity_viewers(records)),
        }
    )
    (args.private_dir / "setup.json").write_text(json.dumps(setup, ensure_ascii=False))
    began = time.perf_counter()
    filtered, counts = filtered_airing_interactions(ORIGINAL / "train/segments.sqlite")
    original_qualified = {(u, it): n for u, it, _, n in records if n}
    filter_report = {}
    for t, name in [(0.5, "als_lb50"), (0.8, "als_lb80")]:
        r = filtered[t]
        assert {(u, it): n for u, it, _, n in r if n} == original_qualified
        (args.private_dir / f"{name}_training.json").write_text(
            json.dumps(r, separators=(",", ":")) + "\n"
        )
        filter_report[name] = {
            "retained_user_airings": counts[str(t)],
            "user_item_pairs": len(r),
            "users": len({x[0] for x in r}),
            "items": len({x[1] for x in r}),
            "qualified_counts_unchanged": True,
        }
    (args.output_dir / "training_signal_preparation.json").write_text(
        json.dumps(
            {
                "variants": filter_report,
                "elapsed_seconds": time.perf_counter() - began,
                "source_cache_manifest": manifest,
                "environment": _environment(),
            },
            indent=2,
        )
        + "\n"
    )
    direct = {u: direct_ranking(personal, u) for u in setup["prediction_users"]}
    base, base_preds, base_ap = evaluate(
        "personal_original",
        direct,
        setup,
        truth,
        args.output_dir,
        args.private_dir,
        extra={
            "result_kind": "existing submitted-baseline configuration replay",
            "external_private_score": 0.38937,
            "external_public_score": 0.39131,
            "external_scores_provenance": "user-confirmed screenshot values",
        },
    )
    assert abs(base["map_at_5"] - 0.3174897297297298) < 1e-12
    for name in ["als_lb50", "als_lb80", "cbf_pop_tie", "als_original"]:
        subprocess.run(
            [
                sys.executable,
                "-m",
                "src.improve_recommender",
                "--output-dir",
                str(args.output_dir),
                "--private-dir",
                str(args.private_dir),
                "--worker",
                name,
            ],
            check=True,
        )
    old_als = json.loads((args.output_dir / "als_original.json").read_text())
    assert abs(old_als["map_at_5"] - 0.08723681681681694) < 1e-12
    names = ["als_original", "cbf_original", "als_lb50", "als_lb80", "cbf_pop_tie"]
    alternatives = {
        n: json.loads((args.output_dir / f"{n}.json").read_text()) for n in names
    }
    alternative = max(names, key=lambda n: alternatives[n]["map_at_5"])
    anchor = json.loads(
        (args.private_dir / "personal_original_direct_top50.json").read_text()
    )
    other = json.loads(
        (args.private_dir / f"{alternative}_direct_top50.json").read_text()
    )
    results = {"personal_original": base, **alternatives}
    for weight in [0.05, 0.1, 0.2]:
        name = f'rrf_{alternative}_w{str(weight).replace(".","p")}'
        direct = {
            u: rrf_rank(anchor[u], other[u], weight) for u in setup["prediction_users"]
        }
        result, _, _ = evaluate(
            name,
            direct,
            setup,
            truth,
            args.output_dir,
            args.private_dir,
            extra={
                "config": {
                    "personal_weight": 1.0,
                    "alternative": alternative,
                    "alternative_weight": weight,
                    "rank_constant": 60,
                    "direct_top_n": 50,
                    "fallback_in_component_ranks": False,
                    "seed": 42,
                }
            },
        )
        results[name] = result
    selected = max(results, key=lambda n: results[n]["map_at_5"])
    # The original baseline wins any exact score tie.
    if results[selected]["map_at_5"] <= base["map_at_5"]:
        selected = "personal_original"
    predictions = json.loads(
        (args.private_dir / f"{selected}_predictions.json").read_text()
    )
    ap = json.loads((args.private_dir / f"{selected}_ap.json").read_text())
    users = sorted(truth)
    diff = np.array([ap[u] - base_ap[u] for u in users])
    rng = np.random.default_rng(42)
    bootstrap = [
        float(np.mean(diff[rng.integers(len(diff), size=len(diff))]))
        for _ in range(2000)
    ]
    assessment = {
        "selected": selected,
        "strongest_alternative": alternative,
        "map_difference": float(diff.mean()),
        "users_improved": int(np.sum(diff > 0)),
        "users_worsened": int(np.sum(diff < 0)),
        "users_unchanged": int(np.sum(diff == 0)),
        "paired_user_bootstrap_95pct_percentile_interval": np.quantile(
            bootstrap, [0.025, 0.975]
        ).tolist(),
        "bootstrap_resamples": 2000,
        "seed": 42,
        "bootstrap_scope": "conditional on this fixed validation set; does not cover configuration selection or Kaggle generalization",
        "prediction_overlap": difference_stats(
            {u: predictions[u] for u in users}, {u: base_preds[u] for u in users}
        ),
    }
    summary = {
        "results": results,
        "assessment": assessment,
        "cohort": 4625,
        "candidates": 6384,
        "elapsed_seconds_local_experiments": time.perf_counter() - started,
        "configuration_budget": "two ALS filters; one exact CBF tie-break; three fixed RRF weights; no other tuning",
        "submission_workflow": "manual review only; no Kaggle access or upload permitted",
        "environment": _environment(),
    }
    (args.output_dir / "comparison.json").write_text(
        json.dumps(summary, indent=2) + "\n"
    )
    print(
        json.dumps(
            {
                "selected": selected,
                "assessment": assessment,
                "scores": {n: r["map_at_5"] for n, r in results.items()},
            }
        ),
        flush=True,
    )
    if selected != "personal_original":
        make_candidate(args, summary, setup)
    else:
        (args.output_dir / "candidate_decision.json").write_text(
            json.dumps(
                {
                    "decision": "retain submitted baseline; no improved or duplicate prediction CSV generated"
                },
                indent=2,
            )
            + "\n"
        )


def make_candidate(args, summary, validation_setup):
    selected = summary["assessment"]["selected"]
    original_artifact = json.loads(
        Path("results/first_submission_20261029/first_artifact.json").read_text()
    )
    paths = [
        args.data_dir / "export_arh_11-20-final.csv",
        args.data_dir / "export_arh_21-30-final.csv",
    ]
    records, manifest = extract_interactions(
        args.data_dir / "dataset11-30.csv",
        paths,
        START,
        END,
        Path("artifacts/first_submission_20261029/combined_fit"),
        input_hashes=original_artifact["input_sha256"],
    )
    assert manifest["config"]["start"] == START and manifest["config"]["end"] == END
    # This existing cache was computed over the combined window before qualification.
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
    personal = Ranker(records, candidates, {}, "personal")
    kind = (
        summary["assessment"]["strongest_alternative"]
        if selected.startswith("rrf_")
        else selected
    )
    signal_records = records
    if kind in ("als_lb50", "als_lb80"):
        filtered, counts = filtered_airing_interactions(
            "artifacts/first_submission_20261029/combined_fit/segments.sqlite"
        )
        signal_records = filtered[0.5 if kind == "als_lb50" else 0.8]
    metadata = {}
    if kind.startswith("cbf"):
        _, _, metadata = schedule_catalog(paths, START, END, END)
    with threadpool_limits(limits=1):
        if kind == "als_original":
            model = Ranker(
                records,
                candidates,
                {},
                "als",
                factors=32,
                regularization=0.1,
                iterations=20,
                seed=42,
            )
        else:
            model = get_model(kind, signal_records, candidates, metadata)
        assert model.fallback == personal.fallback
        pop = popularity_viewers(records) if kind == "cbf_pop_tie" else None
        prediction = {}
        template = list(csv_rows(args.data_dir / "submission.csv"))
        for row in template:
            u = row["user_id"]
            other = direct_ranking(model, u, cbf_popularity=pop)
            direct = (
                rrf_rank(
                    direct_ranking(personal, u),
                    other,
                    summary["results"][selected]["config"]["alternative_weight"],
                )
                if selected.startswith("rrf_")
                else other
            )
            prediction[u] = complete(direct, personal.fallback, candidates)[0]
    baseline = {r["user_id"]: r["tv_show_id"].split(" ") for r in csv_rows(BASELINE)}
    differences = difference_stats(prediction, baseline)
    if differences["users_changed"] == 0:
        (args.output_dir / "candidate_decision.json").write_text(
            json.dumps(
                {
                    "decision": "local improvement but combined-window predictions duplicate submitted baseline; no duplicate CSV generated",
                    "differences": differences,
                },
                indent=2,
            )
            + "\n"
        )
        return
    path = args.candidate_path or (
        Path("submissions") / f"candidate_{selected}_20261029_v2.csv"
    )
    assert not path.exists(), "Refusing to overwrite versioned candidate"
    with path.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["user_id", "tv_show_id"])
        writer.writerows(
            (r["user_id"], " ".join(prediction[r["user_id"]])) for r in template
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
    assert sha256_file(BASELINE) == BASELINE_SHA
    artifact = {
        "status": "validated_candidate_awaiting_user_review; no upload authorized",
        "method": selected,
        "config": summary["results"][selected].get("config"),
        "alternative": kind,
        "local_map_at_5": summary["results"][selected]["map_at_5"],
        "local_assessment": summary["assessment"],
        "csv_filename": path.name,
        "csv_absolute_path": str(path.resolve()),
        "csv_sha256": sha256_file(path),
        "baseline_sha256_unchanged": BASELINE_SHA,
        "validation": validation,
        "differences_from_submitted_baseline": differences,
        "combined_fit_manifest": manifest,
        "fit_window_wall": ["2020-03-09 00:00:00", "2020-07-27 00:00:00"],
        "prediction_window_wall": ["2020-07-27 00:00:00", "2020-10-19 00:00:00"],
        "kaggle_upload_performed": False,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
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
                "differences": differences,
            }
        ),
        flush=True,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--private-dir", type=Path, required=True)
    parser.add_argument("--worker")
    parser.add_argument(
        "--candidate-path",
        type=Path,
        help="Fresh versioned output path for a reproducibility rerun; existing artifacts are never overwritten",
    )
    args = parser.parse_args()
    worker(args) if args.worker else run(args)
