"""Single fixed classifier trained only on two earlier historical origins."""

import argparse
import csv
import hashlib
import importlib.metadata
import json
import math
import sqlite3
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
from lightgbm import LGBMClassifier
from .audit_data import _environment
from .adaptive_threshold import h80_from_records
from .compare_models import history_slice
from .csv_io import sha256_file
from .experiment_adaptive_threshold import compare, SLICE_ORDER
from .experiment_lower_threshold import (
    START,
    MAIN_CUTOFF,
    AUX_CUTOFF,
    END,
    FUTURE_END,
    ORIGINAL,
    BASELINE,
    BASELINE_HASH,
    V9,
    V9_HASH,
    prediction_airing_counts,
)
from .experiment_personal_ties import list_difference
from .first_submission import verify_interaction_cache
from .interactions import extract_interactions, targets, csv_rows
from .item_item import fit_item_item
from .item_fusion import seen_unseen_effects
from .models import Ranker
from .personal_threshold import predict
from .personal_ties import global_qualified_statistics
from .real_matching_audit import stamp
from .reranker_features import (
    FEATURES,
    causal_history,
    build_rows,
    candidate_labels,
    candidate_coverage,
    check_schema,
    ranked_candidates,
)
from .validate_submission import validate_submission

DEFINITION = Path("docs/lightgbm_reranker_protocol.md")


def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n")


def prepare_origin(args, name, cutoff, pred_end, inputs, cache=None, users=None):
    began = time.perf_counter()
    private = args.private_dir / name
    private.mkdir(parents=True, exist_ok=True)
    print(
        json.dumps(
            {
                "origin": name,
                "phase": "pre-cutoff interactions and features",
                "cutoff": cutoff,
            }
        ),
        flush=True,
    )
    paths = [
        args.data_dir / "export_arh_11-20-final.csv",
        args.data_dir / "export_arh_21-30-final.csv",
    ]
    if cache is None:
        cache = private / "train"
        records, manifest = extract_interactions(
            args.data_dir / "dataset11-30.csv",
            paths,
            START,
            cutoff,
            cache,
            input_hashes=inputs,
        )
    else:
        manifest = verify_interaction_cache(cache)
        records = json.loads((cache / "interactions.json").read_text())
    history = causal_history(cache / "segments.sqlite", START, cutoff)
    assert {
        (u, it): n for u, c in history["counts"][0.8].items() for it, n in c.items()
    } == {(u, it): n for u, it, _, n in records if n}
    if name in ["main", "auxiliary"]:
        expected = json.loads(
            Path(f"artifacts/item_item_20261030_v7/{name}/n50.json").read_text()
        )
        assert history["counts"][0.5] == expected
    if users is None:
        template = {r["user_id"] for r in csv_rows(args.data_dir / "submission.csv")}
        users = sorted(history["known_users"] | template)
    paths_for_availability = (
        paths
        if pred_end <= END
        else [
            args.data_dir / "export_arh_21-30-final.csv",
            args.data_dir / "export_arh_31-42-final.csv",
        ]
    )
    available, schedule_stats = prediction_airing_counts(
        paths_for_availability, cutoff, pred_end
    )
    pool = set(available)
    assert len(pool) >= 5 and "0" not in pool
    anchor = Ranker(records, pool, {}, "personal")
    viewers, total = global_qualified_statistics(records)
    assert dict(anchor.qualified) == history["counts"][0.8]
    retrieval_began = time.perf_counter()
    neighbours, support, model_stats = fit_item_item(history["counts"][0.5])
    retrieval_seconds = time.perf_counter() - retrieval_began
    table_began = time.perf_counter()
    x, items, offsets, feature_stats = build_rows(
        users, history, neighbours, pool, viewers, total, anchor.fallback
    )
    table_seconds = time.perf_counter() - table_began
    np.save(private / "features.npy", x, allow_pickle=False)
    (private / "row_index.json").write_text(
        json.dumps(
            {"users": users, "items": items, "offsets": offsets}, separators=(",", ":")
        )
        + "\n"
    )
    report = {
        "origin": name,
        "feature_window": [START, cutoff],
        "prediction_window": [cutoff, pred_end],
        "feature_user_universe": len(users),
        "pre_cutoff_cleaned_view_users": len(history["known_users"]),
        "candidate_pool": len(pool),
        "interaction_manifest": manifest,
        "retrieval": model_stats,
        "retrieval_seconds": retrieval_seconds,
        "feature_table_seconds": table_seconds,
        "features": feature_stats,
        "schema": FEATURES,
        "schema_sha256": hashlib.sha256(json.dumps(FEATURES).encode()).hexdigest(),
        "feature_and_retrieval_elapsed_seconds": time.perf_counter() - began,
        "environment": _environment(),
    }
    return {
        "name": name,
        "history": history,
        "records": records,
        "anchor": anchor,
        "viewers": viewers,
        "total": total,
        "pool": pool,
        "users": users,
        "items": items,
        "offsets": offsets,
        "x": x,
        "report": report,
        "private": private,
    }


def infer(prepared, model):
    began = time.perf_counter()
    x = prepared["x"]
    check_schema(x, model.booster_.feature_name())
    probabilities = model.booster_.predict(x, num_threads=4)
    assert np.isfinite(probabilities).all()
    predictions = {}
    sizes = {}
    global5 = set(prepared["anchor"].fallback[:5])
    selected_global = 0
    for index, (u, items) in enumerate(zip(prepared["users"], prepared["items"])):
        begin, end = prepared["offsets"][index : index + 2]
        predictions[u], sizes[u] = ranked_candidates(
            items,
            probabilities[begin:end],
            prepared["history"]["counts"][0.5].get(u, {}),
            prepared["viewers"],
            prepared["total"],
            prepared["pool"],
            prepared["anchor"].fallback,
        )
        selected_global += len(set(predictions[u]) & global5)
    np.save(
        prepared["private"] / "probabilities.npy", probabilities, allow_pickle=False
    )
    (prepared["private"] / "predictions.json").write_text(
        json.dumps(predictions, separators=(",", ":")) + "\n"
    )
    return (
        predictions,
        sizes,
        {
            "prediction_seconds": time.perf_counter() - began,
            "all_probabilities_finite": True,
            "selected_items_also_in_global5_candidate_source": selected_global,
        },
    )


def fallback_by_slice(sizes, slices):
    return {
        sl: {
            "complete_users": sum(sizes[u] == 0 for u in sizes if slices[u] == sl),
            "partial_users": sum(0 < sizes[u] < 5 for u in sizes if slices[u] == sl),
            "completion_slots": sum(5 - sizes[u] for u in sizes if slices[u] == sl),
        }
        for sl in SLICE_ORDER
    }


def evaluate(args, prepared, model, truth_path):
    name = prepared["name"]
    pred, sizes, inference = infer(prepared, model)
    # Evaluation labels are opened only AFTER features and probabilities are fixed.
    truth_hash = sha256_file(truth_path)
    truth = json.loads(truth_path.read_text())
    users = prepared["users"]
    assert set(users) == set(truth)
    assert (len(users), len(prepared["pool"])) == (
        (4625, 6384) if name == "main" else (4589, 5742)
    )
    h80 = h80_from_records(prepared["records"])
    slices = {u: history_slice(h80.get(u, 0)) for u in users}
    counts = prepared["history"]["counts"][0.5]
    base, base_sizes = predict(
        counts,
        prepared["pool"],
        prepared["viewers"],
        prepared["total"],
        prepared["anchor"].fallback,
        users,
    )
    oldbase = json.loads(
        Path(
            f"artifacts/personal_threshold_20261030_v5/{name}/T50_predictions.json"
        ).read_text()
    )
    assert base == {u: oldbase[u] for u in users}
    v9 = json.loads(
        Path(
            f"artifacts/fifth_replacement_20261030_v9/{name}/E2_predictions.json"
        ).read_text()
    )
    method_fallback = fallback_by_slice(sizes, slices)
    base_fallback = fallback_by_slice(base_sizes, slices)
    results = {}
    for ref, reference in [("v5", base), ("v9", v9)]:
        r = compare(truth, pred, reference, slices, method_fallback, base_fallback)
        r["seen_unseen_effects"] = seen_unseen_effects(truth, pred, reference, counts)
        for sl in SLICE_ORDER:
            actual = {u: truth[u] for u in users if slices[u] == sl}
            r["history_slices"][sl]["seen_unseen_effects"] = seen_unseen_effects(
                actual, pred, reference, counts
            )
        results[ref] = r
    coverage = candidate_coverage(users, prepared["items"], truth)
    cold = {}
    for label, group in [
        ("no_n50_training_history", [u for u in users if not counts.get(u)]),
        (
            "no_available_n50_history",
            [u for u in users if not (set(counts.get(u, {})) & prepared["pool"])],
        ),
    ]:
        if group:
            actual = {u: truth[u] for u in group}
            slice_all = {u: "cold" for u in group}
            from .metrics import average_precision_at_k

            cold[label] = {
                "users": len(group),
                "reranker_map": math.fsum(
                    average_precision_at_k(truth[u], pred[u]) for u in group
                )
                / len(group),
                "v5_map": math.fsum(
                    average_precision_at_k(truth[u], base[u]) for u in group
                )
                / len(group),
                "v9_map": math.fsum(
                    average_precision_at_k(truth[u], v9[u]) for u in group
                )
                / len(group),
            }
        else:
            cold[label] = {"users": 0}
    anchors = {
        "truth": truth,
        "viewers": dict(prepared["viewers"]),
        "total": dict(prepared["total"]),
        "fallback": prepared["anchor"].fallback,
        "slices": slices,
        "candidates": sorted(prepared["pool"]),
    }
    anchor_hash = hashlib.sha256(
        json.dumps(anchors, sort_keys=True).encode()
    ).hexdigest()
    assert (
        anchor_hash
        == json.loads(
            Path(
                f"results/lower_threshold_20261030_v10/{name}/comparison.json"
            ).read_text()
        )["anchor_sha256"]
    )
    report = {
        **prepared["report"],
        "comparisons": results,
        "candidate_coverage": coverage,
        "cold_users": cold,
        "inference": inference,
        "candidate_coverage_slices": {
            sl: candidate_coverage(
                [u for u in users if slices[u] == sl],
                [row for u, row in zip(users, prepared["items"]) if slices[u] == sl],
                truth,
            )
            for sl in SLICE_ORDER
        },
        "anchor_sha256": anchor_hash,
        "truth_sha256": truth_hash,
        "environment_after_evaluation": _environment(),
    }
    assert sha256_file(truth_path) == truth_hash
    dump(args.output_dir / name / "comparison.json", report)
    print(
        json.dumps(
            {
                "split": name,
                "map": results["v9"]["map_at_5"],
                "delta_v5": results["v5"]["delta"],
                "delta_v9": results["v9"]["delta"],
                "oracle": coverage["oracle_map_at_5_target_users"],
            }
        ),
        flush=True,
    )
    return report


def make_candidate(args, model, inputs, model_hash):
    prepared = prepare_origin(
        args,
        "final",
        END,
        FUTURE_END,
        inputs,
        Path("artifacts/first_submission_20261029/combined_fit"),
        [r["user_id"] for r in csv_rows(args.data_dir / "submission.csv")],
    )
    pred, sizes, inference = infer(prepared, model)
    assert (
        hashlib.sha256(model.booster_.model_to_string().encode()).hexdigest()
        == model_hash
    )
    baseline = {r["user_id"]: r["tv_show_id"].split() for r in csv_rows(V9)}
    path = Path("submissions/candidate_lightgbm_historical_fixed_20261030_v12.csv")
    assert not path.exists()
    with (args.data_dir / "submission.csv").open(newline="") as f:
        header = next(csv.reader(f))
    with path.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows((u, " ".join(pred[u])) for u in prepared["users"])
    validation = validate_submission(
        args.data_dir / "submission.csv",
        path,
        prepared["pool"],
        user_column="user_id",
        prediction_column="tv_show_id",
        delimiter=",",
    )
    with (args.output_dir / "candidate_validator_cli.json").open("w") as output:
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
            stdout=output,
            check=True,
        )
    description = "Fixed LightGBM binary reranker trained only on Apr6 and Apr20 historical origins with two-week >=80% top-five labels. Candidate union: personal N50 top200, fixed item-item N50-unseen top50, global-popularity first5. Complete causal N30/N50/N80, ranks/scores, recency, rolling counts and source features; no raw IDs, E2 or blending. Same frozen classifier applied to recomputed weeks11–30 features/retrieval; weeks31–42 carryover-aware candidates. Validated for manual review; no Kaggle score."
    dump(
        args.output_dir / "candidate_artifact.json",
        {
            "filename": path.name,
            "absolute_path": str(path.resolve()),
            "sha256": sha256_file(path),
            "validation": validation,
            "differences_from_submitted_v9": list_difference(pred, baseline),
            "frozen_classifier_sha256": model_hash,
            "final_origin": prepared["report"],
            "inference": inference,
            "submission_description": description,
        },
    )
    (args.output_dir / "submission_description.txt").write_text(description + "\n")


def run(args):
    began = time.perf_counter()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    args.private_dir.mkdir(parents=True, exist_ok=True)
    frozen = json.loads((args.output_dir / "frozen_experiment.json").read_text())
    assert sha256_file(DEFINITION) == frozen["definition_sha256"]
    previous = {
        str(p): sha256_file(p) for p in sorted(Path("submissions").glob("*.csv"))
    }
    assert sha256_file(BASELINE) == BASELINE_HASH and sha256_file(V9) == V9_HASH
    inputs = verify_interaction_cache(ORIGINAL / "train")["config"]["inputs"]
    assert {p: sha256_file(args.data_dir / p) for p in inputs} == inputs
    train_x = []
    train_y = []
    origin_reports = []
    paths = [
        args.data_dir / "export_arh_11-20-final.csv",
        args.data_dir / "export_arh_21-30-final.csv",
    ]
    for cutoff_text, end_text in frozen["training_origins"]:
        cutoff, label_end = stamp(cutoff_text), stamp(end_text)
        name = "origin_" + cutoff_text.replace("-", "")
        prepared = prepare_origin(args, name, cutoff, label_end, inputs)
        print(
            json.dumps({"origin": name, "phase": "earlier label window only"}),
            flush=True,
        )
        label_records, label_manifest = extract_interactions(
            args.data_dir / "dataset11-30.csv",
            paths,
            cutoff,
            label_end,
            args.private_dir / name / "labels",
            input_hashes=inputs,
        )
        truth = targets(label_records, prepared["pool"])
        y = candidate_labels(prepared["users"], prepared["items"], truth)
        coverage = candidate_coverage(prepared["users"], prepared["items"], truth)
        assert (
            len(y) == len(prepared["x"])
            and int(y.sum()) == coverage["covered_relevant_pairs"]
        )
        np.save(prepared["private"] / "labels.npy", y, allow_pickle=False)
        report = {
            **prepared["report"],
            "label_window": [cutoff, label_end],
            "label_manifest": label_manifest,
            "candidate_coverage": coverage,
            "positive_rows": int(y.sum()),
            "positive_rate": float(y.mean()),
            "all_rows_retained": True,
        }
        dump(args.output_dir / name / "origin.json", report)
        origin_reports.append(report)
        train_x.append(prepared["x"])
        train_y.append(y)
        del prepared, label_records, truth
    x = np.concatenate(train_x)
    y = np.concatenate(train_y)
    del train_x, train_y
    check_schema(x, FEATURES)
    assert set(np.unique(y)) == {0, 1}
    fit_started = time.perf_counter()
    model = LGBMClassifier(**frozen["parameters"])
    model.fit(x, y, feature_name=FEATURES)
    fit_seconds = time.perf_counter() - fit_started
    assert (
        model.booster_.current_iteration() == 300
        and model.booster_.feature_name() == FEATURES
    )
    model_text = model.booster_.model_to_string()
    model_hash = hashlib.sha256(model_text.encode()).hexdigest()
    (args.private_dir / "frozen_model.txt").write_text(model_text)
    importance = [
        {"feature": name, "gain": float(gain), "split_count": int(splits)}
        for name, gain, splits in zip(
            FEATURES,
            model.booster_.feature_importance(importance_type="gain"),
            model.booster_.feature_importance(importance_type="split"),
        )
    ]
    dump(
        args.output_dir / "feature_importance.json",
        sorted(importance, key=lambda r: (-r["gain"], r["feature"])),
    )
    dump(
        args.output_dir / "training.json",
        {
            "origin_rows": [
                {
                    "origin": r["origin"],
                    "rows": r["features"]["rows"],
                    "positive_rows": r["positive_rows"],
                    "positive_rate": r["positive_rate"],
                }
                for r in origin_reports
            ],
            "total_rows": len(y),
            "positive_rows": int(y.sum()),
            "positive_rate": float(y.mean()),
            "fit_seconds": fit_seconds,
            "classifier_fit_calls": 1,
            "parameters": frozen["parameters"],
            "actual_parameters": model.get_params(),
            "trained_iterations": model.booster_.current_iteration(),
            "schema": FEATURES,
            "all_features_finite": True,
            "model_sha256": model_hash,
            "model_file_private": str(args.private_dir / "frozen_model.txt"),
            "environment": _environment(),
        },
    )
    del x, y
    reports = {}
    for name, cache, truth, cutoff in [
        ("main", ORIGINAL / "train", ORIGINAL / "truth.json", MAIN_CUTOFF),
        (
            "auxiliary",
            Path("artifacts/opportunity_week_20261030_v4/auxiliary/train"),
            Path("artifacts/opportunity_week_20261030_v4/auxiliary/truth.json"),
            AUX_CUTOFF,
        ),
    ]:
        # User IDs are the already-frozen forecast cohort, not newly selected by labels.
        users = sorted(
            json.loads(
                Path(
                    f"artifacts/fifth_replacement_20261030_v9/{name}/E2_predictions.json"
                ).read_text()
            )
        )
        prepared = prepare_origin(args, name, cutoff, END, inputs, cache, users)
        reports[name] = evaluate(args, prepared, model, truth)
        del prepared
    qualifies = all(reports[s]["comparisons"]["v9"]["delta"] > 0 for s in reports)
    assert (
        hashlib.sha256(model.booster_.model_to_string().encode()).hexdigest()
        == model_hash
    )
    evidence = {
        "qualifies": qualifies,
        "decision": (
            "Generate one manual-review candidate with unchanged historical classifier."
            if qualifies
            else "Retain submitted v9; no final prediction CSV."
        ),
        "comparison_deltas_v9": {
            s: r["comparisons"]["v9"]["delta"] for s, r in reports.items()
        },
        "frozen_protocol_sha256": frozen["definition_sha256"],
        "model_sha256": model_hash,
        "classifier_fit_calls": 1,
        "preserved_csv_sha256": previous,
        "input_sha256": inputs,
        "elapsed_before_optional_final_seconds": time.perf_counter() - began,
        "versions": {
            name: importlib.metadata.version(name)
            for name in [
                "numpy",
                "scipy",
                "lightgbm",
                "scikit-learn",
                "joblib",
                "cloudpickle",
            ]
        },
        "environment": _environment(),
        "score_provenance": {
            "v9": {"private": 0.40261, "public": 0.41871},
            "v11": {"private": 0.40257, "public": 0.41846},
            "source": "User-screenshot-reported in current request; no independent Kaggle lookup.",
            "submission_id": None,
            "submission_timestamp": None,
        },
    }
    dump(args.output_dir / "selection.json", evidence)
    print(
        json.dumps(
            {"qualifies": qualifies, "deltas_v9": evidence["comparison_deltas_v9"]}
        ),
        flush=True,
    )
    if qualifies:
        make_candidate(args, model, inputs, model_hash)
    else:
        dump(
            args.output_dir / "candidate_decision.json",
            {
                "decision": "Retain v9; fixed reranker does not strictly improve both splits. No final fit/CSV and no tuning."
            },
        )
    assert all(sha256_file(Path(p)) == h for p, h in previous.items())
    assert sha256_file(DEFINITION) == frozen["definition_sha256"]
    assert (
        hashlib.sha256(model.booster_.model_to_string().encode()).hexdigest()
        == model_hash
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("results/lightgbm_reranker_20261030_v12"),
    )
    parser.add_argument(
        "--private-dir",
        type=Path,
        default=Path("artifacts/lightgbm_reranker_20261030_v12"),
    )
    run(parser.parse_args())
