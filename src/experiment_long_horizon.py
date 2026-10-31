"""One longer historical-horizon fit; immutable v14 evaluation and final inputs."""

import argparse
import csv
import subprocess
import sys
from .validate_submission import validate_submission
from .experiment_personal_ties import list_difference
import hashlib
import importlib.metadata
import json
import math
import sqlite3
import time
from pathlib import Path
from types import SimpleNamespace
import numpy as np
from lightgbm import Booster, LGBMClassifier
from .audit_data import _environment
from .csv_io import sha256_file
from .experiment_adaptive_threshold import compare, SLICE_ORDER
from .experiment_lightfm_extension import ORIGINS, train_cache
from .experiment_lightfm_expansion import (
    dump,
    infer,
    OLD,
    META,
    PRIOR,
    V14,
)
from .experiment_lower_threshold import START, MAIN_CUTOFF
from .first_submission import verify_interaction_cache
from .interactions import extract_interactions, targets, csv_rows
from .item_item import fit_item_item
from .item_fusion import seen_unseen_effects
from .lightfm_expansion import restore_lightfm
from .lightfm_features import FULL_FEATURES, pair_features
from .metrics import average_precision_at_k
from .personal_ties import global_qualified_statistics
from .reranker_features import (
    FEATURES,
    causal_history,
    user_features,
    candidate_labels,
    candidate_coverage,
)
from .schedule_features import canonical_schedule, schedule_origin, distribution

DEFINITION = Path("docs/long_horizon_protocol.md")
NAMES = ["origin_20200406", "origin_20200420"]


def assert_label_window(start, end):
    if not START <= start < end <= MAIN_CUTOFF:
        raise ValueError("Historical labels must end no later than the main cutoff.")


def immutable_origin(args, name, catalog, frozen):
    """No reconstruction: use the same files/rows/float values as v14."""
    path = OLD / name / "extended_features.npy"
    meta_path = META / name / "row_index.json"
    assert sha256_file(path) == frozen["source_artifact_sha256"][str(path)]
    assert sha256_file(meta_path) == frozen["source_artifact_sha256"][str(meta_path)]
    meta = json.loads(meta_path.read_text())
    x = np.load(path, mmap_mode="r")
    schedule, coverage = schedule_origin(catalog, *ORIGINS[name])
    pool = {it for it, row in schedule.items() if row[1] > 0}
    assert x.shape == (meta["offsets"][-1], 40) and np.isfinite(x).all()
    assert all(set(row) <= pool for row in meta["items"])
    private = args.private_dir / name
    private.mkdir(parents=True, exist_ok=True)
    report = {
        "origin": name,
        "candidate_equality_v14": True,
        "feature_equality_v14": True,
        "mechanism": "Read original v14 feature array and original row index directly; no feature/candidate transformation.",
        "feature_sha256": sha256_file(path),
        "row_index_sha256": sha256_file(meta_path),
        "users": len(meta["users"]),
        "rows": len(x),
        "pool": len(pool),
        "coverage": coverage,
    }
    dump(args.output_dir / name / "input_equality.json", report)
    return dict(meta, x=x, pool=pool, private=private, name=name)


def historical_origin(args, name, catalog, inputs):
    began = time.perf_counter()
    cutoff, old_end = ORIGINS[name]
    assert_label_window(cutoff, MAIN_CUTOFF)
    print(
        json.dumps(
            {
                "origin": name,
                "phase": "long-window causal candidate/features before labels",
            }
        ),
        flush=True,
    )
    cache = train_cache(name)
    manifest = verify_interaction_cache(cache)
    assert manifest["config"]["start"] == START and manifest["config"]["end"] == cutoff
    history = causal_history(cache / "segments.sqlite", START, cutoff)
    assert history["counts"][0.5] == json.loads((OLD / name / "n50.json").read_text())
    original = json.loads((META / name / "row_index.json").read_text())
    template = {r["user_id"] for r in csv_rows(args.data_dir / "submission.csv")}
    users = sorted(history["known_users"] | template)
    assert users == original["users"]
    schedule, coverage = schedule_origin(catalog, cutoff, MAIN_CUTOFF)
    old_schedule, _ = schedule_origin(catalog, cutoff, old_end)
    pool = {it for it, row in schedule.items() if row[1] > 0}
    old_pool = {it for it, row in old_schedule.items() if row[1] > 0}
    assert old_pool <= pool
    records = (
        (u, it, 0, n) for u, c in history["counts"][0.8].items() for it, n in c.items()
    )
    viewers, total = global_qualified_statistics(records)
    fallback = sorted(pool, key=lambda it: (-viewers[it], -total[it], it))
    neighbours, _, item_stats = fit_item_item(history["counts"][0.5])
    source = json.loads((PRIOR / name / "feature_diagnostics.json").read_text())
    bundle = restore_lightfm(OLD / name, source["lightfm"]["predictive_state_sha256"])
    items = []
    offsets = [0]
    chunks = []
    # Features and candidates are fully constructed before any target loading.
    for u in users:
        row, base = user_features(
            u, history, neighbours, pool, viewers, total, fallback
        )
        assert len(row) >= 5 and len(row) == len(set(row))
        items.append(row)
        offsets.append(offsets[-1] + len(row))
        chunks.append(
            np.concatenate(
                [base, np.asarray([schedule[it] for it in row], dtype=np.float32)],
                axis=1,
            )
        )
    extra, support = pair_features(bundle, users, items, pool)
    x = np.concatenate([np.concatenate(chunks), extra], axis=1)
    assert x.shape == (offsets[-1], 40) and np.isfinite(x).all()
    private = args.private_dir / name
    private.mkdir(parents=True, exist_ok=True)
    np.save(private / "features.npy", x, allow_pickle=False)
    dump(
        private / "row_index.json", {"users": users, "items": items, "offsets": offsets}
    )
    old_x = np.load(OLD / name / "extended_features.npy", mmap_mode="r")
    common = []
    old_common = []
    new_pairs = removed_pairs = changed_queries = 0
    for j, (old, new) in enumerate(zip(original["items"], items)):
        om = {it: original["offsets"][j] + k for k, it in enumerate(old)}
        nm = {it: offsets[j] + k for k, it in enumerate(new)}
        shared = sorted(set(om) & set(nm))
        common.extend(nm[it] for it in shared)
        old_common.extend(om[it] for it in shared)
        new_pairs += len(set(new) - set(old))
        removed_pairs += len(set(old) - set(new))
        changed_queries += old != new
    common = np.asarray(common)
    old_common = np.asarray(old_common)
    # Count/source/rank changes from availability must be described, not assumed absent.
    feature_change = {
        f: int(np.sum(x[common, k] != old_x[old_common, k]))
        for k, f in enumerate(FULL_FEATURES)
    }
    schedule_only_changed = int(
        np.sum(np.any(x[common, 27:34] != old_x[old_common, 27:34], axis=1))
    )
    # Reconstruct old-window 27 features with the SAME origin-specific inputs to verify retrieval reuse.
    old_fallback = sorted(old_pool, key=lambda it: (-viewers[it], -total[it], it))
    for j, u in enumerate(users):
        old_items, base = user_features(
            u, history, neighbours, old_pool, viewers, total, old_fallback
        )
        a, b = original["offsets"][j : j + 2]
        assert old_items == original["items"][j] and np.array_equal(
            base, old_x[a:b, :27]
        )
    feature_seconds = time.perf_counter() - began
    # Only now construct new targets over the longer half-open window.
    label_cache = private / "labels"
    label_records, label_manifest = extract_interactions(
        args.data_dir / "dataset11-30.csv",
        [
            args.data_dir / "export_arh_11-20-final.csv",
            args.data_dir / "export_arh_21-30-final.csv",
        ],
        cutoff,
        MAIN_CUTOFF,
        label_cache,
        input_hashes=inputs,
    )
    assert (
        label_manifest["config"]["start"] == cutoff
        and label_manifest["config"]["end"] == MAIN_CUTOFF
    )
    with sqlite3.connect(
        "file:" + str((label_cache / "segments.sqlite").resolve()) + "?mode=ro",
        uri=True,
    ) as db:
        bad = db.execute(
            "SELECT COUNT(*) FROM segments WHERE s < ? OR e > ? OR s >= ?",
            (cutoff, MAIN_CUTOFF, MAIN_CUTOFF),
        ).fetchone()[0]
        observed = db.execute("SELECT MIN(s),MAX(e) FROM segments").fetchone()
    assert bad == 0
    truth = targets(label_records, pool)
    old_records = json.loads((META / name / "labels/interactions.json").read_text())
    old_truth = targets(old_records, old_pool)
    old_y = np.load(META / name / "labels.npy")
    assert np.array_equal(candidate_labels(users, original["items"], old_truth), old_y)
    y = candidate_labels(users, items, truth)
    np.save(private / "labels.npy", y, allow_pickle=False)
    # A label-only descriptive comparison on fixed OLD candidate rows, not another fit.
    new_truth_old_pool = targets(label_records, old_pool)
    changed_target_users = sum(
        set(old_truth.get(u, [])) != set(new_truth_old_pool.get(u, [])) for u in users
    )
    target_only_y = candidate_labels(users, original["items"], new_truth_old_pool)
    negatives = lambda labels, offs: sum(
        not labels[a:b].any() for a, b in zip(offs[:-1], offs[1:])
    )
    report = {
        "origin": name,
        "feature_window": [START, cutoff],
        "label_window": [cutoff, MAIN_CUTOFF],
        "old_label_end": old_end,
        "label_weeks": (MAIN_CUTOFF - cutoff) / 604800,
        "users": len(users),
        "users_equal_pre_cutoff_union_template": True,
        "old_rows": len(old_y),
        "rows": len(y),
        "old_positive_rows": int(old_y.sum()),
        "positive_rows": int(y.sum()),
        "positive_rate": float(y.mean()),
        "old_positive_rate": float(old_y.mean()),
        "all_negative_queries_old": negatives(old_y, original["offsets"]),
        "all_negative_queries_new": negatives(y, offsets),
        "old_pool": len(old_pool),
        "new_pool": len(pool),
        "new_available_programmes": len(pool - old_pool),
        "candidate_pairs_added": new_pairs,
        "candidate_pairs_removed": removed_pairs,
        "changed_candidate_queries": changed_queries,
        "common_candidate_pairs": len(common),
        "common_row_feature_change_counts": feature_change,
        "common_rows_with_schedule_change": schedule_only_changed,
        "target_only_changed_users_fixed_old_pool": changed_target_users,
        "target_only_positive_rows_fixed_old_candidates": int(target_only_y.sum()),
        "old_coverage": candidate_coverage(users, original["items"], old_truth),
        "long_truth_old_candidates_coverage": candidate_coverage(
            users, original["items"], truth
        ),
        "new_coverage": candidate_coverage(users, items, truth),
        "schedule_coverage": coverage,
        "old_retrieval_and_behavior_reconstruction_exact_v14": True,
        "label_boundary_violating_segments": bad,
        "observed_segment_min_start_max_end": observed,
        "label_manifest": label_manifest,
        "no_label_injection": True,
        "all_negatives_and_queries_retained": True,
        "lightfm_fit_calls": 0,
        "item_item_fixed_configuration": item_stats,
        "lightfm_support": support,
        "feature_distributions": distribution(x, FULL_FEATURES),
        "feature_generation_seconds": feature_seconds,
        "elapsed_seconds": time.perf_counter() - began,
        "environment": _environment(),
    }
    dump(args.output_dir / name / "historical.json", report)
    print(
        json.dumps({"origin": name, "rows": len(y), "positives": int(y.sum())}),
        flush=True,
    )
    return x, y, report


def evaluate(args, prepared, model):
    began = time.perf_counter()
    name = prepared["name"]
    pred, slices, counts, cold = infer(prepared, model, "predictions.json")
    path = (
        Path("artifacts/model_comparison_20261029/truth.json")
        if name == "main"
        else Path("artifacts/opportunity_week_20261030_v4/auxiliary/truth.json")
    )
    truth = json.loads(path.read_text())
    reference = json.loads((OLD / name / "predictions.json").read_text())
    assert set(truth) == set(pred) == set(reference)
    zero = {
        sl: {"complete_users": 0, "partial_users": 0, "completion_slots": 0}
        for sl in SLICE_ORDER
    }
    result = compare(truth, pred, reference, slices, zero, zero)
    prior = json.loads((PRIOR / name / "comparison.json").read_text())
    assert (
        abs(result["reference_map_at_5"] - prior["comparison_v13"]["map_at_5"]) < 1e-12
    )
    coverage = candidate_coverage(prepared["users"], prepared["items"], truth)
    assert coverage == prior["candidate_coverage_exactly_equal_v13"]
    result["seen_unseen_effects"] = seen_unseen_effects(truth, pred, reference, counts)
    for sl, r in result["history_slices"].items():
        assert r["users"] == prior["comparison_v13"]["history_slices"][sl]["users"]
        r["seen_unseen_effects"] = seen_unseen_effects(
            {u: t for u, t in truth.items() if slices[u] == sl}, pred, reference, counts
        )
    cold_report = {}
    for group, users in cold.items():
        assert len(users) == prior["cold_users"][group]["users"]
        a = [average_precision_at_k(truth[u], reference[u]) for u in users]
        b = [average_precision_at_k(truth[u], pred[u]) for u in users]
        cold_report[group] = {
            "users": len(users),
            "v14_map": math.fsum(a) / len(a),
            "new_map": math.fsum(b) / len(b),
            "improved": sum(y > x for x, y in zip(a, b)),
            "worsened": sum(y < x for x, y in zip(a, b)),
            "unchanged": sum(y == x for x, y in zip(a, b)),
        }
    dump(
        args.output_dir / name / "comparison.json",
        {
            "comparison_v14": result,
            "cold_users": cold_report,
            "candidate_coverage_unchanged_v14": coverage,
            "inference_evaluation_seconds": time.perf_counter() - began,
            "environment": _environment(),
        },
    )
    print(
        json.dumps(
            {
                "split": name,
                "map": result["map_at_5"],
                "delta": result["delta"],
                "ci": result["paired_bootstrap_95pct"],
            }
        ),
        flush=True,
    )
    return result


def make_candidate(args, prepared, model, model_hash):
    pred, _, _, _ = infer(prepared, model, "predictions.json")
    reference = {r["user_id"]: r["tv_show_id"].split() for r in csv_rows(V14)}
    assert reference == json.loads((OLD / "final/predictions.json").read_text())
    template = args.data_dir / "submission.csv"
    path = Path("submissions/candidate_lightgbm_long_horizon_20261030_v16.csv")
    assert not path.exists()
    with template.open(newline="") as f:
        header = next(csv.reader(f))
    with path.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows((u, " ".join(pred[u])) for u in prepared["users"])
    validation = validate_submission(
        template,
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
                str(template),
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
    description = "Fixed 40-feature LightGBM reranker trained once on two longer historical target windows: Apr6-May18 (six weeks) and Apr20-May18 (four weeks), half-open, with pre-cutoff histories from Mar9. Original v14 personal200/item-item unseen50/global5 candidate rule; historical availability and schedule exposure recomputed for those horizons. Saved origin-specific LightFM models reused. Same seed/settings and 300 trees; all negatives and overlapping-origin examples retained equally. No tuning, candidate expansion, blend, E2 or cold override. Frozen new classifier applied to exact unchanged v14 final candidate rows and feature values; validated for manual review, no Kaggle result."
    dump(
        args.output_dir / "candidate_artifact.json",
        {
            "filename": path.name,
            "absolute_path": str(path.resolve()),
            "sha256": sha256_file(path),
            "validation": validation,
            "differences_from_submitted_v14": list_difference(pred, reference),
            "classifier_sha256": model_hash,
            "submission_description": description,
        },
    )
    (args.output_dir / "submission_description.txt").write_text(description + "\n")


def run(args):
    began = time.perf_counter()
    args.private_dir.mkdir(parents=True, exist_ok=True)
    frozen = json.loads((args.output_dir / "frozen_experiment.json").read_text())
    assert sha256_file(DEFINITION) == frozen["definition_sha256"]
    assert all(
        sha256_file(Path(p)) == h for p, h in frozen["source_artifact_sha256"].items()
    )
    inputs = json.loads(
        Path("results/lightgbm_reranker_20261030_v12/selection.json").read_text()
    )["input_sha256"]
    assert all(sha256_file(args.data_dir / name) == h for name, h in inputs.items())
    catalog, _ = canonical_schedule(
        [
            args.data_dir / f"export_arh_{p}-final.csv"
            for p in ["11-20", "21-30", "31-42"]
        ]
    )
    if args.resume_frozen_classifier:
        training = json.loads((args.output_dir / "training.json").read_text())
        model_hash = training["classifier_sha256"]
        assert sha256_file(args.private_dir / "frozen_model.txt") == model_hash
        model = SimpleNamespace(
            booster_=Booster(model_file=str(args.private_dir / "frozen_model.txt"))
        )
    else:
        assert not (
            args.private_dir / "frozen_model.txt"
        ).exists(), "Classifier exists: resume without refitting."
        data = [historical_origin(args, n, catalog, inputs) for n in NAMES]
        x = np.concatenate([d[0] for d in data])
        y = np.concatenate([d[1] for d in data])
        del data
        start = time.perf_counter()
        model = LGBMClassifier(**frozen["lightgbm_parameters"])
        model.fit(x, y, feature_name=FULL_FEATURES)
        fit_seconds = time.perf_counter() - start
        assert (
            model.booster_.current_iteration() == 300
            and model.booster_.feature_name() == FULL_FEATURES
        )
        text = model.booster_.model_to_string()
        model_hash = hashlib.sha256(text.encode()).hexdigest()
        (args.private_dir / "frozen_model.txt").write_text(text)
        dump(
            args.output_dir / "training.json",
            {
                "rows": len(y),
                "positives": int(y.sum()),
                "positive_rate": float(y.mean()),
                "classifier_fit_calls": 1,
                "lightfm_fit_calls": 0,
                "trees": 300,
                "parameters": frozen["lightgbm_parameters"],
                "classifier_sha256": model_hash,
                "fit_seconds": fit_seconds,
                "environment": _environment(),
                "versions": {
                    n: importlib.metadata.version(n)
                    for n in ["lightfm", "lightgbm", "numpy", "scipy", "scikit-learn"]
                },
            },
        )
        del x, y
    importance = [
        {"feature": f, "gain": float(g), "splits": int(s)}
        for f, g, s in zip(
            FULL_FEATURES,
            model.booster_.feature_importance("gain"),
            model.booster_.feature_importance("split"),
        )
    ]
    dump(
        args.output_dir / "feature_importance.json",
        sorted(importance, key=lambda r: -r["gain"]),
    )
    # Verify final equality regardless of qualification; no final refit/reconstruction.
    final = immutable_origin(args, "final", catalog, frozen)
    results = {
        n: evaluate(args, immutable_origin(args, n, catalog, frozen), model)
        for n in ["main", "auxiliary"]
    }
    qualifies = all(r["delta"] > 0 for r in results.values())
    dump(
        args.output_dir / "selection.json",
        {
            "qualifies": qualifies,
            "decision": (
                "Generate one candidate." if qualifies else "Retain v14; no CSV."
            ),
            "deltas_v14": {n: r["delta"] for n, r in results.items()},
            "classifier_sha256": model_hash,
            "classifier_fit_calls": 1,
            "lightfm_fit_calls": 0,
            "frozen_protocol_sha256": sha256_file(DEFINITION),
            "historical_label_overlap": ["2020-04-20", "2020-05-18"],
            "equal_row_weights": True,
            "v14_user_screenshot_scores": {
                "private": 0.43416,
                "public": 0.44157,
                "submission_id": None,
                "timestamp": None,
            },
            "elapsed_seconds": time.perf_counter() - began,
            "environment": _environment(),
        },
    )
    if qualifies:
        make_candidate(args, final, model, model_hash)
    assert all(
        sha256_file(Path(p)) == h for p, h in frozen["source_artifact_sha256"].items()
    )
    assert sha256_file(DEFINITION) == frozen["definition_sha256"]
    assert (
        hashlib.sha256(model.booster_.model_to_string().encode()).hexdigest()
        == model_hash
    )
    print(json.dumps({"qualifies": qualifies}), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument(
        "--output-dir", type=Path, default=Path("results/long_horizon_20261030_v16")
    )
    parser.add_argument(
        "--private-dir", type=Path, default=Path("artifacts/long_horizon_20261030_v16")
    )
    parser.add_argument("--resume-frozen-classifier", action="store_true")
    run(parser.parse_args())
