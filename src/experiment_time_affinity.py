"""One six-feature viewing-time affinity extension of submitted v18."""

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
from types import SimpleNamespace
import numpy as np
from lightgbm import LGBMClassifier, Booster
from .audit_data import _environment
from .compare_models import history_slice
from .csv_io import sha256_file
from .experiment_adaptive_threshold import compare, SLICE_ORDER
from .experiment_lightfm_expansion import META, dump
from .experiment_lightfm_extension import ORIGINS, train_cache
from .experiment_long_horizon import immutable_origin
from .experiment_channel_affinity import FULL_FEATURES as ORIGINAL_FEATURES
from .experiment_lower_threshold import START
from .experiment_personal_ties import list_difference
from .first_submission import verify_interaction_cache
from .interactions import csv_rows
from .item_fusion import seen_unseen_effects
from .metrics import average_precision_at_k
from .reranker_features import FEATURES, candidate_coverage, ranked_candidates
from .schedule_features import canonical_schedule, distribution
from .validate_submission import validate_submission
from .time_affinity import (
    TIME_FEATURES,
    user_profiles,
    schedule_profiles,
    append_time_features,
)

OLD = Path("artifacts/channel_affinity_20261030_v18")
PRIOR = Path("results/channel_affinity_20261030_v18")
V18 = Path("submissions/candidate_lightgbm_channel_affinity_20261030_v18.csv")
FULL_FEATURES = ORIGINAL_FEATURES + TIME_FEATURES
DEFINITION = Path("docs/time_affinity_protocol.md")


def infer(prepared, model, filename):
    assert model.booster_.feature_name() == FULL_FEATURES
    assert prepared["x"].shape[1] == 58 and np.isfinite(prepared["x"]).all()
    prob = model.booster_.predict(prepared["x"], num_threads=4)
    assert np.isfinite(prob).all()
    predictions = {}
    slices = {}
    counts = {}
    cold = {"no_n50_training_history": [], "no_available_n50_history": []}
    for index, (u, items) in enumerate(zip(prepared["users"], prepared["items"])):
        begin, end = prepared["offsets"][index : index + 2]
        x = prepared["x"][begin:end]
        values = lambda col: {
            it: float(x[j, FEATURES.index(col)]) for j, it in enumerate(items)
        }
        n50 = values("n50")
        viewers = values("global_viewers80")
        airings = values("global_airings80")
        fallback = [
            it
            for j, it in enumerate(items)
            if x[j, FEATURES.index("source_global5")] == 1
        ]
        fallback.sort(key=lambda it: (-viewers[it], -airings[it], it))
        assert len(fallback) == 5
        predictions[u], size = ranked_candidates(
            items, prob[begin:end], n50, viewers, airings, prepared["pool"], fallback
        )
        assert size == 5
        counts[u] = {it: int(n) for it, n in n50.items() if n > 0}
        slices[u] = history_slice(int(x[0, FEATURES.index("user_history80")]))
        if x[0, FEATURES.index("user_history50")] == 0:
            cold["no_n50_training_history"].append(u)
        if not np.any(x[:, FEATURES.index("source_personal200")] > 0):
            cold["no_available_n50_history"].append(u)
    (prepared["private"] / filename).write_text(
        json.dumps(predictions, separators=(",", ":")) + "\n"
    )
    return predictions, slices, counts, cold


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
        abs(result["reference_map_at_5"] - prior["comparison_v14"]["map_at_5"]) < 1e-12
    )
    coverage = candidate_coverage(prepared["users"], prepared["items"], truth)
    assert coverage == prior["candidate_coverage_unchanged_v14"]
    result["seen_unseen_effects"] = seen_unseen_effects(truth, pred, reference, counts)
    for sl, r in result["history_slices"].items():
        assert r["users"] == prior["comparison_v14"]["history_slices"][sl]["users"]
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
            "v18_map": math.fsum(a) / len(a),
            "new_map": math.fsum(b) / len(b),
            "improved": sum(y > x for x, y in zip(a, b)),
            "worsened": sum(y < x for x, y in zip(a, b)),
            "unchanged": sum(y == x for x, y in zip(a, b)),
        }
    dump(
        args.output_dir / name / "comparison.json",
        {
            "comparison_v18": result,
            "cold_users": cold_report,
            "candidate_coverage_unchanged_v18": coverage,
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
    reference = {r["user_id"]: r["tv_show_id"].split() for r in csv_rows(V18)}
    assert reference == json.loads((OLD / "final/predictions.json").read_text())
    template = args.data_dir / "submission.csv"
    path = Path("submissions/candidate_lightgbm_time_affinity_20261030_v19.csv")
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
    description = "Fixed binary LightGBM reranker appending six viewing-time affinity features to unchanged v18 candidates and 52 features. Full-history and trailing28-day user profiles union cleaned observed intervals across channels, including unattributed viewing; source-naive half-open durations split exactly into 24 hour-of-day and 168 Monday-first hour-of-week bins. Canonical clipped forecast schedule airings give normalized programme profiles; four dot-product affinities and two no-viewing indicators, no smoothing or timezone conversion. Original two-week historical labels/settings/300trees/seed42, one fit with all negatives. Same frozen classifier applied at final cutoff; no candidate expansion, longer horizons, LambdaRank, tuning, blend, E2 or cold override. Validated for manual review; no Kaggle result."
    dump(
        args.output_dir / "candidate_artifact.json",
        {
            "filename": path.name,
            "absolute_path": str(path.resolve()),
            "sha256": sha256_file(path),
            "validation": validation,
            "differences_from_submitted_v18": list_difference(pred, reference),
            "classifier_sha256": model_hash,
            "submission_description": description,
        },
    )
    (args.output_dir / "submission_description.txt").write_text(description + "\n")


def cached_v18(args, name, catalog, frozen):
    prepared = immutable_origin(args, name, catalog, frozen)
    path = OLD / name / "extended_features.npy"
    assert sha256_file(path) == frozen["source_artifact_sha256"][str(path)]
    x = np.load(path, mmap_mode="r")
    assert x.shape == (prepared["offsets"][-1], 52) and np.isfinite(x).all()
    assert np.array_equal(x[:, :40], prepared["x"])
    prepared["x"] = x
    dump(
        args.output_dir / name / "input_equality.json",
        {
            "origin": name,
            "candidate_equality_v18": True,
            "feature52_equality_v18": True,
            "mechanism": "Direct original v18 array and original unchanged row index, no reconstruction.",
            "feature_sha256": sha256_file(path),
            "row_index_sha256": sha256_file(META / name / "row_index.json"),
            "rows": len(x),
            "users": len(prepared["users"]),
            "pool": len(prepared["pool"]),
        },
    )
    return prepared


def augmented(args, name, catalog, frozen, prepared=None):
    began = time.perf_counter()
    print(
        json.dumps({"origin": name, "phase": "causal cross-channel time profiles"}),
        flush=True,
    )
    prepared = prepared or cached_v18(args, name, catalog, frozen)
    cutoff, end = ORIGINS[name]
    cache = train_cache(name)
    manifest = verify_interaction_cache(cache)
    assert manifest["config"]["start"] == START and manifest["config"]["end"] == cutoff
    profiles = user_profiles(cache / "segments.sqlite", START, cutoff)
    programmes = schedule_profiles(catalog, cutoff, end)
    if set(programmes) != prepared["pool"]:
        raise ValueError(
            "Schedule profile universe differs from original availability."
        )
    x, extra = append_time_features(
        prepared["x"], prepared["users"], prepared["items"], profiles, programmes
    )
    assert np.array_equal(
        x[:, :52], np.load(OLD / name / "extended_features.npy", mmap_mode="r")
    )
    np.save(prepared["private"] / "time_features.npy", extra, allow_pickle=False)
    np.save(prepared["private"] / "extended_features.npy", x, allow_pickle=False)
    zero_rates = {}
    normalization = {}
    for k, w in enumerate(["full", "trailing28"]):
        positive = [hist[k] for hist in profiles.values() if hist[k][2] > 0]
        flags = sum(
            u not in profiles or profiles[u][k][2] == 0 for u in prepared["users"]
        )
        zero_rates[w] = {
            "query_users": len(prepared["users"]),
            "zero_users": flags,
            "zero_fraction": flags / len(prepared["users"]),
        }
        normalization[w] = {
            "positive_profile_users": len(positive),
            "total_union_seconds_all_cleaned_users": math.fsum(h[2] for h in positive),
            "max_day_mass_error": max(abs(float(h[0].sum()) - 1) for h in positive),
            "max_week_mass_error": max(abs(float(h[1].sum()) - 1) for h in positive),
        }
    report = {
        "origin": name,
        "feature_window": [START, cutoff],
        "trailing_window": [max(START, cutoff - 28 * 86400), cutoff],
        "forecast_window": [cutoff, end],
        "clock": "source-naive wall seconds; no timezone conversion",
        "rows": len(x),
        "users": len(prepared["users"]),
        "schema": FULL_FEATURES,
        "original52_exactly_equal_v18": True,
        "candidates_exactly_equal_v18": True,
        "all_finite": bool(np.isfinite(x).all()),
        "matrix_bytes": x.nbytes,
        "feature_sha256": sha256_file(prepared["private"] / "time_features.npy"),
        "user_zero_profiles": zero_rates,
        "user_normalization": normalization,
        "schedule_profiles": len(programmes),
        "schedule_min_positive_broadcast_seconds": min(
            h[2] for h in programmes.values()
        ),
        "schedule_total_broadcast_seconds": math.fsum(
            h[2] for h in programmes.values()
        ),
        "schedule_max_day_mass_error": max(
            abs(float(h[0].sum()) - 1) for h in programmes.values()
        ),
        "schedule_max_week_mass_error": max(
            abs(float(h[1].sum()) - 1) for h in programmes.values()
        ),
        "feature_distributions": distribution(extra, TIME_FEATURES),
        "elapsed_origin_seconds": time.perf_counter() - began,
        "environment": _environment(),
    }
    dump(args.output_dir / name / "time_diagnostics.json", report)
    prepared["x"] = x
    return prepared


def run(args):
    began = time.perf_counter()
    args.private_dir.mkdir(parents=True, exist_ok=True)
    frozen = json.loads((args.output_dir / "frozen_experiment.json").read_text())
    assert sha256_file(DEFINITION) == frozen["definition_sha256"]
    assert all(
        sha256_file(Path(p)) == h for p, h in frozen["source_artifact_sha256"].items()
    )
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
        xs = []
        ys = []
        origins = []
        for name in ["origin_20200406", "origin_20200420"]:
            prep = augmented(args, name, catalog, frozen)
            manifest = verify_interaction_cache(META / name / "labels")
            assert (manifest["config"]["start"], manifest["config"]["end"]) == ORIGINS[
                name
            ]
            path = META / name / "labels.npy"
            y = np.load(path)
            assert sha256_file(path) == frozen["source_artifact_sha256"][str(path)]
            assert len(y) == len(prep["x"]) and np.isin(y, [0, 1]).all()
            origins.append(
                {
                    "name": name,
                    "rows": len(y),
                    "positives": int(y.sum()),
                    "labels_exactly_equal_v18": True,
                    "label_sha256": sha256_file(path),
                    "label_window": list(ORIGINS[name]),
                    "all_negative_queries": sum(
                        not y[a:b].any()
                        for a, b in zip(prep["offsets"][:-1], prep["offsets"][1:])
                    ),
                }
            )
            xs.append(prep["x"])
            ys.append(y)
        x = np.concatenate(xs)
        y = np.concatenate(ys)
        del xs, ys, prep
        start = time.perf_counter()
        model = LGBMClassifier(**frozen["parameters"])
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
                "origins": origins,
                "rows": len(y),
                "positive_rows": int(y.sum()),
                "schema": FULL_FEATURES,
                "classifier_fit_calls": 1,
                "trees": 300,
                "fit_seconds": fit_seconds,
                "classifier_sha256": model_hash,
                "requested_parameters": frozen["parameters"],
                "effective_booster_parameters": model.booster_.params,
                "versions": {
                    n: importlib.metadata.version(n)
                    for n in ["lightgbm", "lightfm", "numpy", "scipy", "scikit-learn"]
                },
                "environment": _environment(),
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
    final = cached_v18(args, "final", catalog, frozen)
    results = {
        n: evaluate(args, augmented(args, n, catalog, frozen), model)
        for n in ["main", "auxiliary"]
    }
    qualifies = all(r["delta"] > 0 for r in results.values())
    dump(
        args.output_dir / "selection.json",
        {
            "qualifies": qualifies,
            "decision": (
                "Generate one candidate." if qualifies else "Retain v18; no CSV."
            ),
            "deltas_v18": {n: r["delta"] for n, r in results.items()},
            "classifier_sha256": model_hash,
            "classifier_fit_calls": 1,
            "v18_user_screenshot_scores": {
                "private": 0.43798,
                "public": 0.44758,
                "submission_id": None,
                "timestamp": None,
            },
            "elapsed_before_optional_final_seconds": time.perf_counter() - began,
            "environment": _environment(),
        },
    )
    if qualifies:
        make_candidate(
            args, augmented(args, "final", catalog, frozen, final), model, model_hash
        )
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
        "--output-dir", type=Path, default=Path("results/time_affinity_20261030_v19")
    )
    parser.add_argument(
        "--private-dir", type=Path, default=Path("artifacts/time_affinity_20261030_v19")
    )
    parser.add_argument("--resume-frozen-classifier", action="store_true")
    run(parser.parse_args())
