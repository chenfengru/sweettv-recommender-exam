"""Two-stage unweighted item-affinity extension, original 52 features frozen."""

import argparse
import csv
import hashlib
import json
import math
import subprocess
import sys
import time
from pathlib import Path
from types import SimpleNamespace
import numpy as np
from lightgbm import Booster, LGBMClassifier
from .audit_data import _environment
from .csv_io import sha256_file
from .experiment_seed_ensemble import load_origin, ScoreVector, native_params, dump
from .experiment_channel_affinity import FULL_FEATURES as ORIGINAL_FEATURES, infer
from .experiment_lightfm_extension import ORIGINS, train_cache
from .experiment_lower_threshold import START
from .experiment_adaptive_threshold import compare, SLICE_ORDER
from .experiment_personal_ties import list_difference
from .first_submission import verify_interaction_cache
from .personal_threshold import personal_counts
from .item_item import fit_item_item, score_user
from .item_affinity import FEATURES, append_affinities, scalar_reference
from .item_fusion import seen_unseen_effects
from .reranker_features import candidate_coverage
from .schedule_features import canonical_schedule, distribution
from .seed_ensemble import equal_score_mean
from .interactions import csv_rows
from .validate_submission import validate_submission

BASE = Path("artifacts/channel_affinity_20261030_v18")
META = Path("artifacts/lightgbm_reranker_20261030_v12")
SEEDS = Path("artifacts/seed_ensemble_20261031_v20")
INCUMBENT = Path("submissions/candidate_channel_affinity_seed_mean_20261031_v20.csv")
FULL_FEATURES = ORIGINAL_FEATURES + FEATURES
DEFINITION = Path("docs/item_affinity_protocol.md")


def augmented(args, name, catalog):
    began = time.perf_counter()
    print(
        json.dumps(
            {"origin": name, "phase": "pre-cutoff directed other-history affinity"}
        ),
        flush=True,
    )
    prep = load_origin(name, catalog)
    prep["base"] = prep["x"]
    cutoff, end = ORIGINS[name]
    cache = train_cache(name)
    manifest = verify_interaction_cache(cache)
    assert manifest["config"]["start"] == START and manifest["config"]["end"] == cutoff
    n50 = personal_counts(cache / "segments.sqlite", START, cutoff, thresholds=(0.5,))[
        0.5
    ]
    assert n50 == json.loads(
        (
            Path("artifacts/lightfm_extension_20261030_v14") / name / "n50.json"
        ).read_text()
    )
    if name in ["main", "auxiliary"]:
        graph_path = Path("artifacts/item_item_20261030_v7") / name / "neighbours.json"
        expected = json.loads(
            Path("results/item_item_20261030_v7/preservation_checks.json").read_text()
        )["private_model_sha256"][str(graph_path)]
        assert sha256_file(graph_path) == expected
        neighbours = json.loads(graph_path.read_text())
        graph_stats = {"verified_saved_graph": str(graph_path), "sha256": expected}
    else:
        neighbours, _, graph_stats = fit_item_item(n50)
    x, extra = append_affinities(
        prep["base"], prep["users"], prep["items"], n50, neighbours
    )
    # Verify the original graph orientation/weights/ranks against every frozen row.
    for j, (u, row) in enumerate(zip(prep["users"], prep["items"])):
        a, b = prep["offsets"][j : j + 2]
        direct, _, score = score_user(
            n50.get(u, {}), neighbours, prep["pool"], return_scores=True
        )
        rank = {it: r for r, it in enumerate(direct, 1)}
        assert np.array_equal(
            np.asarray([score.get(it, 0) for it in row], dtype=np.float32),
            prep["base"][a:b, 8],
        )
        assert np.array_equal(
            np.asarray([rank.get(it, 0) for it in row], dtype=np.float32),
            prep["base"][a:b, 10],
        )
    # Independent candidate-centric scalar lookup on predeclared random real rows.
    indices = np.random.default_rng(42).choice(
        len(x), size=min(64, len(x)), replace=False
    )
    max_error = 0.0
    for index in indices:
        j = int(np.searchsorted(prep["offsets"], index, side="right") - 1)
        u = prep["users"][j]
        it = prep["items"][j][index - prep["offsets"][j]]
        expected = scalar_reference(
            [i for i, c in n50.get(u, {}).items() if c > 0], it, neighbours
        )
        max_error = max(max_error, float(np.max(abs(expected - extra[index]))))
        np.testing.assert_allclose(expected, extra[index], rtol=1e-7, atol=1e-7)
    private = args.private_dir / name
    private.mkdir(parents=True, exist_ok=True)
    np.save(private / "affinity_features.npy", extra, allow_pickle=False)
    np.save(private / "extended55.npy", x, allow_pickle=False)
    if name not in ["main", "auxiliary"]:
        dump(private / "neighbours.json", neighbours)
    dump(
        args.output_dir / name / "feature_diagnostics.json",
        {
            "origin": name,
            "history_window": [START, cutoff],
            "forecast_window": [cutoff, end],
            "rows": len(x),
            "users": len(prep["users"]),
            "candidates": len(prep["pool"]),
            "schema": FULL_FEATURES,
            "original52_exactly_equal": bool(np.array_equal(x[:, :52], prep["base"])),
            "original_candidates_exactly_equal": True,
            "all_original_weighted_item_scores_and_ranks_exact": True,
            "original_n50_cache_exact": True,
            "graph": graph_stats,
            "scalar_sample_rows": len(indices),
            "scalar_max_abs_difference_float32": max_error,
            "nan_or_infinite_values": int(np.sum(~np.isfinite(extra))),
            "all_three_zero_rows": int(np.sum(np.all(extra == 0, axis=1))),
            "all_three_zero_fraction": float(np.mean(np.all(extra == 0, axis=1))),
            "distributions": distribution(extra, FEATURES),
            "matrix_bytes": x.nbytes,
            "elapsed_origin_seconds": time.perf_counter() - began,
            "environment": _environment(),
        },
    )
    prep.update(x=x, n50=n50)
    return prep


def fit_one(args, seed, x, y, frozen):
    path = args.private_dir / f"extended_seed{seed}.txt"
    assert not path.exists(), "Refusing to overwrite or refit."
    began = time.perf_counter()
    model = LGBMClassifier(**dict(frozen["parameters42"], random_state=seed))
    model.fit(x, y, feature_name=FULL_FEATURES)
    assert (
        model.booster_.feature_name() == FULL_FEATURES
        and model.booster_.current_iteration() == 300
    )
    assert {k: v for k, v in model.booster_.params.items() if k != "random_state"} == {
        k: v for k, v in frozen["effective_parameters42"].items() if k != "random_state"
    }
    path.write_text(model.booster_.model_to_string())
    dump(
        args.output_dir / f"seed{seed}_fit.json",
        {
            "seed": seed,
            "rows": len(y),
            "positive_rows": int(y.sum()),
            "fit_seconds": time.perf_counter() - began,
            "effective_parameters": model.booster_.params,
            "model_sha256": sha256_file(path),
            "environment": _environment(),
        },
    )
    return model.booster_


def ranking(args, prep, scores, method):
    path = args.private_dir / prep["name"] / method
    path.mkdir(parents=True, exist_ok=True)
    return infer(
        dict(prep, x=prep["base"], private=path),
        SimpleNamespace(booster_=ScoreVector(scores)),
        "predictions.json",
    )


def evaluate(args, prep, scores, reference, method):
    pred, slices, _, _ = ranking(args, prep, scores, method)
    truth_path = (
        Path("artifacts/model_comparison_20261029/truth.json")
        if prep["name"] == "main"
        else Path("artifacts/opportunity_week_20261030_v4/auxiliary/truth.json")
    )
    truth = json.loads(truth_path.read_text())
    assert set(truth) == set(pred) == set(reference)
    zero = {
        sl: {"complete_users": 0, "partial_users": 0, "completion_slots": 0}
        for sl in SLICE_ORDER
    }
    result = compare(truth, pred, reference, slices, zero, zero)
    result["seen_unseen"] = seen_unseen_effects(truth, pred, reference, prep["n50"])
    result["candidate_coverage"] = candidate_coverage(
        prep["users"], prep["items"], truth
    )
    expected = json.loads(
        (
            Path("results/channel_affinity_20261030_v18")
            / prep["name"]
            / "comparison.json"
        ).read_text()
    )["candidate_coverage_unchanged_v14"]
    assert result["candidate_coverage"] == expected
    for sl, row in result["history_slices"].items():
        row["seen_unseen"] = seen_unseen_effects(
            {u: t for u, t in truth.items() if slices[u] == sl},
            pred,
            reference,
            prep["n50"],
        )
    dump(args.output_dir / prep["name"] / (method + ".json"), result)
    print(
        json.dumps(
            {
                "split": prep["name"],
                "method": method,
                "map": result["map_at_5"],
                "delta": result["delta"],
                "ci": result["paired_bootstrap_95pct"],
            }
        ),
        flush=True,
    )
    return result


def candidate(args, models, prep):
    scores = equal_score_mean([m.predict(prep["x"], num_threads=4) for m in models])
    pred, _, _, _ = ranking(args, prep, scores, "extended_ensemble")
    template = args.data_dir / "submission.csv"
    rows = list(csv_rows(template))
    assert len(rows) == 1260 and prep["users"] == [r["user_id"] for r in rows]
    reference = {r["user_id"]: r["tv_show_id"].split() for r in csv_rows(INCUMBENT)}
    assert reference == json.loads(
        (SEEDS / "final/ensemble/predictions.json").read_text()
    )
    path = Path("submissions/candidate_item_other_history_affinity_20261031_v21.csv")
    assert not path.exists()
    with template.open(newline="") as f:
        header = next(csv.reader(f))
    with path.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows((u, " ".join(pred[u])) for u in prep["users"])
    validation = validate_submission(
        template,
        path,
        prep["pool"],
        user_column="user_id",
        prediction_column="tv_show_id",
        delimiter=",",
    )
    with (args.output_dir / "candidate_validator_cli.json").open("w") as f:
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
            stdout=f,
            check=True,
        )
    description = "Equal mean of four historical channel-affinity LightGBM classifiers, seeds42–45, with three unweighted item-item features from other distinct N50-history programmes: maximum positive similarity, sum of five largest positives and log1p contributor count. Original outgoing top50 shrunk-cosine graph, self-exclusion, candidates, 52 existing features, labels and fixed settings preserved. Same frozen classifiers applied to final55-feature rows without evaluation-label refit, tuning or incumbent blending. Validated manual-submission candidate; no Kaggle result."
    dump(
        args.output_dir / "candidate_artifact.json",
        {
            "filename": path.name,
            "absolute_path": str(path.resolve()),
            "sha256": sha256_file(path),
            "validation": validation,
            "differences_vs_incumbent": list_difference(pred, reference),
            "submission_description": description,
        },
    )
    (args.output_dir / "submission_description.txt").write_text(description + "\n")


def run(args):
    began = time.perf_counter()
    args.private_dir.mkdir(parents=True, exist_ok=True)
    frozen = json.loads((args.output_dir / "frozen_experiment.json").read_text())
    assert sha256_file(DEFINITION) == frozen["definition_sha256"]
    assert all(sha256_file(Path(p)) == h for p, h in frozen["source_sha256"].items())
    catalog, _ = canonical_schedule(
        [
            args.data_dir / f"export_arh_{s}-final.csv"
            for s in ["11-20", "21-30", "31-42"]
        ]
    )
    training = [
        augmented(args, n, catalog) for n in ["origin_20200406", "origin_20200420"]
    ]
    x = np.concatenate([d["x"] for d in training])
    ys = []
    for prep in training:
        path = META / prep["name"] / "labels.npy"
        y = np.load(path)
        assert (
            len(y) == len(prep["x"])
            and sha256_file(path) == frozen["source_sha256"][str(path)]
        )
        ys.append(y)
        manifest = verify_interaction_cache(META / prep["name"] / "labels")
        assert (manifest["config"]["start"], manifest["config"]["end"]) == ORIGINS[
            prep["name"]
        ]
    y = np.concatenate(ys)
    del training, ys
    models = {42: fit_one(args, 42, x, y, frozen)}
    original = {42: Booster(model_file=str(BASE / "frozen_model.txt"))}
    original.update(
        {s: Booster(model_file=str(SEEDS / f"seed{s}.txt")) for s in [43, 44, 45]}
    )
    evaluations = {n: augmented(args, n, catalog) for n in ["main", "auxiliary"]}
    stage1 = {}
    incumbents = {}
    for name, prep in evaluations.items():
        scores = models[42].predict(prep["x"], num_threads=4)
        seed42 = json.loads((BASE / name / "predictions.json").read_text())
        old42, _, _, _ = ranking(
            args,
            prep,
            original[42].predict(prep["base"], num_threads=4),
            "replayed_original42",
        )
        assert old42 == seed42
        old_mean = equal_score_mean(
            [original[s].predict(prep["base"], num_threads=4) for s in [42, 43, 44, 45]]
        )
        old, _, _, _ = ranking(args, prep, old_mean, "replayed_incumbent")
        assert old == json.loads(
            (SEEDS / name / "ensemble/predictions.json").read_text()
        )
        incumbents[name] = old
        stage1[name] = evaluate(args, prep, scores, seed42, "stage1_vs_seed42")
        evaluate(args, prep, scores, old, "stage1_vs_incumbent_context_only")
    proceed = all(r["delta"] > 0 for r in stage1.values())
    dump(
        args.output_dir / "stage1_gate.json",
        {
            "passes": proceed,
            "deltas_vs_original_seed42": {n: r["delta"] for n, r in stage1.items()},
            "stage1_fit_count": 1,
        },
    )
    stage2 = {}
    if proceed:
        for seed in [43, 44, 45]:
            models[seed] = fit_one(args, seed, x, y, frozen)
        for name, prep in evaluations.items():
            scores = [
                models[s].predict(prep["x"], num_threads=4) for s in [42, 43, 44, 45]
            ]
            for seed, values in zip([42, 43, 44, 45], scores):
                evaluate(
                    args,
                    prep,
                    values,
                    incumbents[name],
                    f"stage2_seed{seed}_diagnostic",
                )
            stage2[name] = evaluate(
                args,
                prep,
                equal_score_mean(scores),
                incumbents[name],
                "extended_ensemble_vs_incumbent",
            )
    qualifies = proceed and all(r["delta"] > 0 for r in stage2.values())
    dump(
        args.output_dir / "selection.json",
        {
            "stage1_passes": proceed,
            "stage2_run": proceed,
            "qualifies": bool(qualifies),
            "new_classifier_fits": len(models),
            "decision": (
                "Generate one extended ensemble candidate."
                if qualifies
                else "Retain submitted four-seed incumbent; no CSV."
            ),
            "stage2_deltas_vs_incumbent": {n: r["delta"] for n, r in stage2.items()},
            "elapsed_before_optional_final_seconds": time.perf_counter() - began,
            "environment": _environment(),
            "user_screenshot_reported_incumbent_scores": {
                "private": 0.44124,
                "public": 0.44911,
                "submission_id": None,
                "submission_timestamp": None,
            },
        },
    )
    if qualifies:
        candidate(
            args,
            [models[s] for s in [42, 43, 44, 45]],
            augmented(args, "final", catalog),
        )
    importance = {
        s: [
            {"feature": f, "gain": float(g)}
            for f, g in zip(FULL_FEATURES, m.feature_importance("gain"))
        ]
        for s, m in models.items()
    }
    dump(args.output_dir / "feature_importance.json", importance)
    assert all(sha256_file(Path(p)) == h for p, h in frozen["source_sha256"].items())
    assert sha256_file(DEFINITION) == frozen["definition_sha256"]
    print(
        json.dumps(
            {
                "stage1_passes": proceed,
                "qualifies": bool(qualifies),
                "fits": len(models),
            }
        ),
        flush=True,
    )


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--data-dir", type=Path, required=True)
    p.add_argument(
        "--output-dir", type=Path, default=Path("results/item_affinity_20261031_v21")
    )
    p.add_argument(
        "--private-dir", type=Path, default=Path("artifacts/item_affinity_20261031_v21")
    )
    run(p.parse_args())
