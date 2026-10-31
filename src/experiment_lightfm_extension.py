"""One identity-only WARP feature extension of immutable v13 reranker data."""

import argparse
import csv
import hashlib
import importlib.metadata
import json
import math
import subprocess
import sys
import time
from pathlib import Path
import numpy as np
from lightgbm import LGBMClassifier
from .audit_data import _environment
from .compare_models import history_slice
from .csv_io import sha256_file
from .experiment_adaptive_threshold import compare, SLICE_ORDER
from .experiment_lower_threshold import (
    START,
    MAIN_CUTOFF,
    AUX_CUTOFF,
    END,
    FUTURE_END,
    prediction_airing_counts,
)
from .experiment_personal_ties import list_difference
from .first_submission import verify_interaction_cache
from .item_fusion import seen_unseen_effects
from .metrics import average_precision_at_k
from .interactions import csv_rows
from .personal_threshold import personal_counts
from .real_matching_audit import stamp
from .reranker_features import FEATURES, candidate_coverage, ranked_candidates
from .lightfm_features import (
    FULL_FEATURES,
    LIGHTFM_FEATURES,
    fit_lightfm,
    pair_features,
    append_features,
    predictive_hash,
)
from .validate_submission import validate_submission

DEFINITION = Path("docs/lightfm_extension_protocol.md")
V13 = Path("submissions/candidate_lightgbm_schedule_exposure_20261030_v13.csv")
V13_HASH = "1fd147770b6be8ebcd64c89244af60cb8510440607358ec84c9adc6ffe7ec359"
OLD = Path("artifacts/schedule_reranker_20261030_v13")
PRIOR = Path("results/schedule_reranker_20261030_v13")
META = Path("artifacts/lightgbm_reranker_20261030_v12")
ORIGINS = {
    "origin_20200406": (stamp("2020-04-06"), stamp("2020-04-20")),
    "origin_20200420": (stamp("2020-04-20"), stamp("2020-05-04")),
    "main": (MAIN_CUTOFF, END),
    "auxiliary": (AUX_CUTOFF, END),
    "final": (END, FUTURE_END),
}


def dump(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n")


def train_cache(name):
    if name.startswith("origin_"):
        return META / name / "train"
    if name == "main":
        return Path("artifacts/model_comparison_20261029/train")
    if name == "auxiliary":
        return Path("artifacts/opportunity_week_20261030_v4/auxiliary/train")
    return Path("artifacts/first_submission_20261029/combined_fit")


def load_augmented(args, name, frozen):
    began = time.perf_counter()
    print(
        json.dumps({"origin": name, "phase": "pre-cutoff N50 identity WARP fit"}),
        flush=True,
    )
    cutoff, pred_end = ORIGINS[name]
    cache = train_cache(name)
    manifest = verify_interaction_cache(cache)
    assert manifest["config"]["start"] == START and manifest["config"]["end"] == cutoff
    n50 = personal_counts(cache / "segments.sqlite", START, cutoff, thresholds=(0.5,))[
        0.5
    ]
    base_path = OLD / name / "augmented_features.npy"
    meta_path = META / name / "row_index.json"
    assert sha256_file(base_path) == frozen["source_artifact_sha256"][str(base_path)]
    assert sha256_file(meta_path) == frozen["source_artifact_sha256"][str(meta_path)]
    base = np.load(base_path, mmap_mode="r")
    metadata = json.loads(meta_path.read_text())
    users, items, offsets = metadata["users"], metadata["items"], metadata["offsets"]
    assert offsets[-1] == len(base)
    for index, u in enumerate(users):
        start, end = offsets[index : index + 2]
        rows = base[start:end]
        counts = n50.get(u, {})
        assert int(rows[0, FEATURES.index("user_history50")]) == len(counts)
        assert int(rows[0, FEATURES.index("user_airings50")]) == sum(counts.values())
        assert all(
            int(rows[j, FEATURES.index("n50")]) == counts.get(it, 0)
            for j, it in enumerate(items[index])
        )
    paths = (
        [
            args.data_dir / "export_arh_11-20-final.csv",
            args.data_dir / "export_arh_21-30-final.csv",
        ]
        if pred_end <= END
        else [
            args.data_dir / "export_arh_21-30-final.csv",
            args.data_dir / "export_arh_31-42-final.csv",
        ]
    )
    availability, _ = prediction_airing_counts(paths, cutoff, pred_end)
    pool = set(availability)
    previous = json.loads((PRIOR / name / "feature_diagnostics.json").read_text())
    assert len(pool) == previous["coverage"]["future"]["programmes"]
    bundle = fit_lightfm(n50)
    feature_began = time.perf_counter()
    extra, support = pair_features(bundle, users, items, pool)
    feature_seconds = time.perf_counter() - feature_began
    replay = None
    if name == frozen["deterministic_replay_origin"]:
        replay_bundle = fit_lightfm(n50)
        replay_extra, replay_support = pair_features(replay_bundle, users, items, pool)
        assert bundle["mappings"] == replay_bundle["mappings"] and predictive_hash(
            bundle["model"]
        ) == predictive_hash(replay_bundle["model"])
        assert (
            np.array_equal(extra, replay_extra)
            and support["feature_sha256"] == replay_support["feature_sha256"]
        )
        replay = {
            "same_mapping": True,
            "same_binary_matrix": bundle["report"]["binary_sha256"]
            == replay_bundle["report"]["binary_sha256"],
            "same_predictive_arrays": True,
            "all_six_feature_columns_bitwise_equal": True,
            "same_hyperparameters_seed_epochs_threads": True,
            "replay_fit_seconds": replay_bundle["report"]["fit_seconds"],
            "configuration_search": False,
        }
        del replay_bundle, replay_extra
    x = append_features(base, extra)
    private = args.private_dir / name
    private.mkdir(parents=True, exist_ok=True)
    dump(private / "mappings.json", bundle["mappings"])
    np.savez(
        private / "lightfm_predictive_arrays.npz",
        **{
            key: getattr(bundle["model"], key)
            for key in [
                "user_embeddings",
                "item_embeddings",
                "user_biases",
                "item_biases",
            ]
        }
    )
    np.save(private / "lightfm_features.npy", extra, allow_pickle=False)
    np.save(private / "extended_features.npy", x, allow_pickle=False)
    dump(private / "n50.json", n50)
    report = {
        "origin": name,
        "feature_cutoff": cutoff,
        "prediction_end": pred_end,
        "source_cache_manifest": manifest,
        "lightfm": bundle["report"],
        "support_and_features": support,
        "deterministic_replay": replay,
        "candidate_and_original34_equality": True,
        "schema": FULL_FEATURES,
        "rows": len(x),
        "matrix_bytes": x.nbytes,
        "feature_generation_seconds": feature_seconds,
        "source_hashes": {
            "original34": frozen["source_artifact_sha256"][str(base_path)],
            "row_index": frozen["source_artifact_sha256"][str(meta_path)],
        },
        "elapsed_origin_seconds_including_optional_replay": time.perf_counter() - began,
        "environment": _environment(),
    }
    dump(args.output_dir / name / "feature_diagnostics.json", report)
    del bundle, n50
    return {
        "x": x,
        "base": base,
        "users": users,
        "items": items,
        "offsets": offsets,
        "pool": pool,
        "stats": report,
        "private": private,
    }


def infer(prepared, model):
    assert (
        model.booster_.feature_name() == FULL_FEATURES
        and prepared["x"].shape[1] == 40
        and np.isfinite(prepared["x"]).all()
    )
    began = time.perf_counter()
    prob = model.booster_.predict(prepared["x"], num_threads=4)
    assert np.isfinite(prob).all()
    predictions = {}
    sizes = {}
    counts = {}
    slices = {}
    cold_full = []
    cold_available = []
    for index, (u, items) in enumerate(zip(prepared["users"], prepared["items"])):
        begin, end = prepared["offsets"][index : index + 2]
        base = prepared["base"][begin:end]
        values = lambda name: {
            it: float(base[j, FEATURES.index(name)]) for j, it in enumerate(items)
        }
        n50 = values("n50")
        viewers = values("global_viewers80")
        total = values("global_airings80")
        fallback = [
            it
            for j, it in enumerate(items)
            if base[j, FEATURES.index("source_global5")] == 1
        ]
        fallback.sort(key=lambda it: (-viewers[it], -total[it], it))
        assert len(fallback) == 5
        predictions[u], sizes[u] = ranked_candidates(
            items, prob[begin:end], n50, viewers, total, prepared["pool"], fallback
        )
        counts[u] = {it: int(n) for it, n in n50.items() if n > 0}
        h80 = int(base[0, FEATURES.index("user_history80")])
        slices[u] = history_slice(h80)
        if base[0, FEATURES.index("user_history50")] == 0:
            cold_full.append(u)
        if not np.any(base[:, FEATURES.index("source_personal200")] > 0):
            cold_available.append(u)
    np.save(prepared["private"] / "probabilities.npy", prob, allow_pickle=False)
    (prepared["private"] / "predictions.json").write_text(
        json.dumps(predictions, separators=(",", ":")) + "\n"
    )
    return (
        predictions,
        sizes,
        counts,
        slices,
        {
            "no_n50_training_history": cold_full,
            "no_available_n50_history": cold_available,
        },
        time.perf_counter() - began,
    )


def evaluate(args, name, prepared, model):
    pred, sizes, counts, slices, cold, inference_seconds = infer(prepared, model)
    truth_path = (
        Path("artifacts/model_comparison_20261029/truth.json")
        if name == "main"
        else Path("artifacts/opportunity_week_20261030_v4/auxiliary/truth.json")
    )
    truth_hash = sha256_file(truth_path)
    truth = json.loads(truth_path.read_text())
    assert set(truth) == set(pred)
    reference = json.loads((OLD / name / "predictions.json").read_text())
    assert all(
        set(reference[u]) <= set(row)
        for u, row in zip(prepared["users"], prepared["items"])
    )
    zero_fallback = {
        sl: {"complete_users": 0, "partial_users": 0, "completion_slots": 0}
        for sl in SLICE_ORDER
    }
    result = compare(truth, pred, reference, slices, zero_fallback, zero_fallback)
    assert not any(n < 5 for n in sizes.values())
    prior = json.loads((PRIOR / name / "comparison.json").read_text())
    assert (
        abs(result["reference_map_at_5"] - prior["comparison_v12"]["map_at_5"]) < 1e-12
    )
    assert {sl: r["users"] for sl, r in result["history_slices"].items()} == {
        sl: r["users"] for sl, r in prior["comparison_v12"]["history_slices"].items()
    }
    coverage = candidate_coverage(prepared["users"], prepared["items"], truth)
    assert coverage == prior["candidate_coverage_exactly_equal_v12"]
    result["seen_unseen_effects"] = seen_unseen_effects(truth, pred, reference, counts)
    for sl, r in result["history_slices"].items():
        r["seen_unseen_effects"] = seen_unseen_effects(
            {u: t for u, t in truth.items() if slices[u] == sl}, pred, reference, counts
        )
    cold_report = {}
    for label, group in cold.items():
        assert len(group) == prior["cold_users"][label]["users"]
        if group:
            d = [
                average_precision_at_k(truth[u], pred[u])
                - average_precision_at_k(truth[u], reference[u])
                for u in group
            ]
            cold_report[label] = {
                "users": len(group),
                "v13_map": math.fsum(
                    average_precision_at_k(truth[u], reference[u]) for u in group
                )
                / len(group),
                "extended_map": math.fsum(
                    average_precision_at_k(truth[u], pred[u]) for u in group
                )
                / len(group),
                "users_improved": sum(v > 0 for v in d),
                "users_worsened": sum(v < 0 for v in d),
                "users_unchanged": sum(v == 0 for v in d),
            }
        else:
            cold_report[label] = {"users": 0}
    report = {
        "origin": name,
        "comparison_v13": result,
        "candidate_equality": True,
        "candidate_coverage_exactly_equal_v13": coverage,
        "cold_users": cold_report,
        "inference_seconds": inference_seconds,
        "truth_sha256": truth_hash,
        "environment": _environment(),
    }
    dump(args.output_dir / name / "comparison.json", report)
    assert sha256_file(truth_path) == truth_hash
    print(
        json.dumps(
            {
                "split": name,
                "map": result["map_at_5"],
                "delta_v13": result["delta"],
                "ci": result["paired_bootstrap_95pct"],
            }
        ),
        flush=True,
    )
    return report


def make_candidate(args, prepared, model, model_hash):
    pred, _, _, _, _, seconds = infer(prepared, model)
    assert (
        hashlib.sha256(model.booster_.model_to_string().encode()).hexdigest()
        == model_hash
    )
    reference = {r["user_id"]: r["tv_show_id"].split() for r in csv_rows(V13)}
    assert reference == json.loads((OLD / "final/predictions.json").read_text())
    template = args.data_dir / "submission.csv"
    path = Path("submissions/candidate_lightgbm_lightfm_warp_20261030_v14.csv")
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
            check=True,
            stdout=output,
        )
    description = "Historical LightGBM reranker with all34 v13 features/candidate rows unchanged, plus identity-only LightFM WARP score, full-available supported-item rank, user/item biases and unsupported-user/item indicators. Separate pre-cutoff binary N50 LightFM models:10 components, seed42,15 epochs,1 thread, fixedWARP settings. No latent coordinates, new candidates, blend, E2 or cold override. Same frozen extended classifier at validation and final weeks11–30 cutoff for weeks31–42 predictions. Validated for manual review; no Kaggle result."
    dump(
        args.output_dir / "candidate_artifact.json",
        {
            "filename": path.name,
            "absolute_path": str(path.resolve()),
            "sha256": sha256_file(path),
            "validation": validation,
            "differences_from_submitted_v13": list_difference(pred, reference),
            "classifier_sha256": model_hash,
            "inference_seconds": seconds,
            "submission_description": description,
        },
    )
    (args.output_dir / "submission_description.txt").write_text(description + "\n")
    print(
        json.dumps({"candidate": str(path.resolve()), "sha256": sha256_file(path)}),
        flush=True,
    )


def run(args):
    began = time.perf_counter()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    args.private_dir.mkdir(parents=True, exist_ok=True)
    frozen = json.loads((args.output_dir / "frozen_experiment.json").read_text())
    assert sha256_file(DEFINITION) == frozen["definition_sha256"]
    previous = {
        str(p): sha256_file(p) for p in sorted(Path("submissions").glob("*.csv"))
    }
    assert sha256_file(V13) == V13_HASH
    assert all(
        sha256_file(Path(p)) == h for p, h in frozen["source_artifact_sha256"].items()
    )
    inputs = json.loads((PRIOR / "selection.json").read_text())["preserved_csv_sha256"]
    source_inputs = json.loads(
        Path("results/lightgbm_reranker_20261030_v12/selection.json").read_text()
    )["input_sha256"]
    assert all(
        sha256_file(args.data_dir / name) == h for name, h in source_inputs.items()
    )
    train = []
    labels = []
    for name in ["origin_20200406", "origin_20200420"]:
        prepared = load_augmented(args, name, frozen)
        label_path = META / name / "labels.npy"
        assert (
            sha256_file(label_path) == frozen["source_artifact_sha256"][str(label_path)]
        )
        y = np.load(label_path)
        assert len(y) == len(prepared["x"])
        train.append(prepared["x"])
        labels.append(y)
    x = np.concatenate(train)
    y = np.concatenate(labels)
    del train, labels, prepared
    prior_training = json.loads((PRIOR / "training.json").read_text())
    assert (
        len(y) == prior_training["rows"]
        and int(y.sum()) == prior_training["positive_rows"]
    )
    fit_began = time.perf_counter()
    model = LGBMClassifier(**frozen["lightgbm_parameters"])
    model.fit(x, y, feature_name=FULL_FEATURES)
    fit_seconds = time.perf_counter() - fit_began
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
            "positive_rows": int(y.sum()),
            "positive_rate": float(y.mean()),
            "classifier_fit_calls": 1,
            "trained_iterations": 300,
            "parameters": frozen["lightgbm_parameters"],
            "schema": FULL_FEATURES,
            "original_v13_candidate_rows_and_labels_equal": True,
            "model_sha256": model_hash,
            "fit_seconds": fit_seconds,
            "environment": _environment(),
        },
    )
    dump(
        args.output_dir / "feature_importance.json",
        sorted(
            [
                {"feature": name, "gain": float(gain), "splits": int(splits)}
                for name, gain, splits in zip(
                    FULL_FEATURES,
                    model.booster_.feature_importance(importance_type="gain"),
                    model.booster_.feature_importance(importance_type="split"),
                )
            ],
            key=lambda r: (-r["gain"], r["feature"]),
        ),
    )
    del x, y
    reports = {}
    for name in ["main", "auxiliary"]:
        prepared = load_augmented(args, name, frozen)
        reports[name] = evaluate(args, name, prepared, model)
        del prepared
    qualifies = all(r["comparison_v13"]["delta"] > 0 for r in reports.values())
    assert (
        hashlib.sha256(model.booster_.model_to_string().encode()).hexdigest()
        == model_hash
    )
    dump(
        args.output_dir / "selection.json",
        {
            "qualifies": qualifies,
            "decision": (
                "Generate one manual-review candidate."
                if qualifies
                else "Retain v13; no CSV, no final LightFM fit and no further variants."
            ),
            "deltas_v13": {
                name: r["comparison_v13"]["delta"] for name, r in reports.items()
            },
            "frozen_protocol_sha256": frozen["definition_sha256"],
            "classifier_sha256": model_hash,
            "classifier_fit_calls": 1,
            "preserved_csv_sha256": previous,
            "original_v13_artifact_sha256": frozen["source_artifact_sha256"],
            "elapsed_before_optional_final_seconds": time.perf_counter() - began,
            "versions": {
                name: importlib.metadata.version(name)
                for name in ["lightfm", "lightgbm", "numpy", "scipy", "scikit-learn"]
            },
            "environment": _environment(),
            "v13_kaggle": {
                "private": 0.43400,
                "public": 0.43774,
                "source": "User-screenshot-reported in current request; no independent lookup.",
                "submission_id": None,
                "submission_timestamp": None,
            },
        },
    )
    print(
        json.dumps(
            {
                "qualifies": qualifies,
                "deltas_v13": {
                    name: r["comparison_v13"]["delta"] for name, r in reports.items()
                },
            }
        ),
        flush=True,
    )
    if qualifies:
        final = load_augmented(args, "final", frozen)
        make_candidate(args, final, model, model_hash)
    else:
        dump(
            args.output_dir / "candidate_decision.json",
            {
                "decision": "Retain v13; extension fails strict gain on both splits. No final LightFM fit or CSV; no further variants."
            },
        )
    assert all(sha256_file(Path(p)) == h for p, h in previous.items())
    assert all(
        sha256_file(Path(p)) == h for p, h in frozen["source_artifact_sha256"].items()
    )
    assert (
        hashlib.sha256(model.booster_.model_to_string().encode()).hexdigest()
        == model_hash
    )
    assert sha256_file(DEFINITION) == frozen["definition_sha256"]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("results/lightfm_extension_20261030_v14"),
    )
    parser.add_argument(
        "--private-dir",
        type=Path,
        default=Path("artifacts/lightfm_extension_20261030_v14"),
    )
    run(parser.parse_args())
