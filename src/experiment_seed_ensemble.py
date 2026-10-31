"""Conditional seed-only experiment; original v18 inputs and frozen settings."""

import argparse
import csv
import hashlib
import importlib.metadata
import json
import re
import subprocess
import sys
import time
from pathlib import Path
from types import SimpleNamespace
import numpy as np
from lightgbm import Booster, LGBMClassifier
from .audit_data import _environment
from .csv_io import sha256_file
from .experiment_channel_affinity import FULL_FEATURES, infer
from .experiment_lightfm_extension import ORIGINS
from .experiment_adaptive_threshold import compare, SLICE_ORDER
from .experiment_personal_ties import list_difference
from .schedule_features import canonical_schedule, schedule_origin
from .interactions import csv_rows
from .validate_submission import validate_submission
from .seed_ensemble import predictive_tree_hash, vector_diversity, equal_score_mean

OLD = Path("artifacts/channel_affinity_20261030_v18")
META = Path("artifacts/lightgbm_reranker_20261030_v12")
INCUMBENT = Path("submissions/candidate_lightgbm_channel_affinity_20261030_v18.csv")
DEFINITION = Path("docs/seed_ensemble_protocol.md")


def dump(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2) + "\n")


def native_params(model):
    return dict(re.findall(r"^\[([^:]+): (.*)\]$", model.model_to_string(), re.M))


class ScoreVector:
    def __init__(self, scores):
        self.scores = scores

    def feature_name(self):
        return FULL_FEATURES

    def predict(self, x, **kwargs):
        assert x.shape == (len(self.scores), 52)
        return self.scores


def load_origin(name, catalog):
    meta = json.loads((META / name / "row_index.json").read_text())
    x = np.load(OLD / name / "extended_features.npy", mmap_mode="r")
    schedule, coverage = schedule_origin(catalog, *ORIGINS[name])
    pool = {it for it, row in schedule.items() if row[1] > 0}
    assert (
        x.shape == (meta["offsets"][-1], 52)
        and np.isfinite(x).all()
        and all(set(row) <= pool for row in meta["items"])
    )
    return dict(meta, x=x, pool=pool, name=name, coverage=coverage)


def evaluate(args, prepared, scores, reference_scores, method):
    began = time.perf_counter()
    name = prepared["name"]
    prepared = dict(prepared, private=args.private_dir / name / method)
    prepared["private"].mkdir(parents=True, exist_ok=True)
    pred, slices, counts, cold = infer(
        prepared, SimpleNamespace(booster_=ScoreVector(scores)), "predictions.json"
    )
    reference = json.loads((OLD / name / "predictions.json").read_text())
    if method == "seed42":
        assert pred == reference
    truth_path = (
        Path("artifacts/model_comparison_20261029/truth.json")
        if name == "main"
        else Path("artifacts/opportunity_week_20261030_v4/auxiliary/truth.json")
    )
    truth = json.loads(truth_path.read_text())
    assert set(truth) == set(pred) == set(reference)
    zero = {
        sl: {"complete_users": 0, "partial_users": 0, "completion_slots": 0}
        for sl in SLICE_ORDER
    }
    result = compare(truth, pred, reference, slices, zero, zero)
    # Full candidate orders compared with the original score convention/ties.
    changed_order = 0
    for row, a, b in zip(
        prepared["items"], prepared["offsets"][:-1], prepared["offsets"][1:]
    ):
        x = prepared["x"][a:b]

        def order(values):
            return sorted(
                range(len(row)),
                key=lambda j: (-values[j], -x[j, 1], -x[j, 12], -x[j, 13], row[j]),
            )

        changed_order += order(scores[a:b]) != order(reference_scores[a:b])
    result["score_diversity_vs42"] = vector_diversity(scores, reference_scores)
    result["users_with_full_candidate_order_change"] = changed_order
    result["elapsed_evaluation_seconds"] = time.perf_counter() - began
    dump(args.output_dir / name / (method + ".json"), result)
    print(
        json.dumps(
            {
                "split": name,
                "method": method,
                "map": result["map_at_5"],
                "delta": result["delta"],
                "score_rows_different": result["score_diversity_vs42"][
                    "different_scores"
                ],
            }
        ),
        flush=True,
    )
    return result


def fit_one(args, seed, x, y, frozen, reference_params):
    path = args.private_dir / f"seed{seed}.txt"
    assert not path.exists(), "Refusing to refit/overwrite a saved seed."
    params = dict(frozen["parameters42"], random_state=seed)
    began = time.perf_counter()
    model = LGBMClassifier(**params)
    model.fit(x, y, feature_name=FULL_FEATURES)
    assert (
        model.booster_.current_iteration() == 300
        and model.booster_.feature_name() == FULL_FEATURES
    )
    effective = model.booster_.params
    assert {k: v for k, v in effective.items() if k != "random_state"} == {
        k: v
        for k, v in frozen["incumbent_effective_parameters"].items()
        if k != "random_state"
    }
    current = native_params(model.booster_)
    native_changes = {
        k: {"seed42": reference_params[k], "new": v}
        for k, v in current.items()
        if k in reference_params and v != reference_params[k]
    }
    assert all("seed" in k for k in native_changes), native_changes
    path.write_text(model.booster_.model_to_string())
    dump(
        args.output_dir / f"seed{seed}_fit.json",
        {
            "seed": seed,
            "fit_seconds": time.perf_counter() - began,
            "rows": len(y),
            "positive_rows": int(y.sum()),
            "effective_parameters": effective,
            "native_seed_changes_only": native_changes,
            "predictive_tree_sha256": predictive_tree_hash(model.booster_),
            "saved_model_sha256": sha256_file(path),
            "environment": _environment(),
        },
    )
    return model.booster_


def candidate(args, models, prepared):
    scores = equal_score_mean([m.predict(prepared["x"], num_threads=4) for m in models])
    prep = dict(prepared, private=args.private_dir / "final/ensemble")
    prep["private"].mkdir(parents=True, exist_ok=True)
    pred, _, _, _ = infer(
        prep, SimpleNamespace(booster_=ScoreVector(scores)), "predictions.json"
    )
    reference = {r["user_id"]: r["tv_show_id"].split() for r in csv_rows(INCUMBENT)}
    assert reference == json.loads((OLD / "final/predictions.json").read_text())
    template = args.data_dir / "submission.csv"
    rows = list(csv_rows(template))
    assert prepared["users"] == [r["user_id"] for r in rows] and len(rows) == 1260
    path = Path("submissions/candidate_channel_affinity_seed_mean_20261031_v20.csv")
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
    description = "Equal arithmetic mean of four original 52-feature channel-affinity LightGBM ranking-score vectors, seeds42/43/44/45. Saved seed42 reused; three historical classifiers differ only in global seed with unchanged original bin-construction sampling, full row/feature usage and300trees. Same original two-week training labels and frozen classifiers applied to unchanged final candidate features; no evaluation-label refit, sampling changes, weight tuning, best-seed selection, blending with other methods, E2 or cold override. Scores are ranking signals, not calibrated probabilities. Validated for manual review; no Kaggle result."
    dump(
        args.output_dir / "candidate_artifact.json",
        {
            "absolute_path": str(path.resolve()),
            "filename": path.name,
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
    incumbent = Booster(model_file=str(OLD / "frozen_model.txt"))
    assert incumbent.feature_name() == FULL_FEATURES
    params = native_params(incumbent)
    x = np.concatenate(
        [
            np.load(OLD / n / "extended_features.npy")
            for n in ["origin_20200406", "origin_20200420"]
        ]
    )
    y = np.concatenate(
        [
            np.load(META / n / "labels.npy")
            for n in ["origin_20200406", "origin_20200420"]
        ]
    )
    assert x.shape == (604935, 52) and len(y) == len(x) and np.isfinite(x).all()
    seed43 = fit_one(args, 43, x, y, frozen, params)
    catalog, _ = canonical_schedule(
        [
            args.data_dir / f"export_arh_{p}-final.csv"
            for p in ["11-20", "21-30", "31-42"]
        ]
    )
    prepared = {n: load_origin(n, catalog) for n in ["main", "auxiliary"]}
    models = {42: incumbent, 43: seed43}
    scores = {}
    raw = {}
    results = {}
    diverse = False
    for name, prep in prepared.items():
        scores[name] = {
            s: m.predict(prep["x"], num_threads=4) for s, m in models.items()
        }
        raw[name] = {
            s: m.predict(prep["x"], num_threads=4, raw_score=True)
            for s, m in models.items()
        }
        results[name] = {}
        for seed in [42, 43]:
            results[name][str(seed)] = evaluate(
                args, prep, scores[name][seed], scores[name][42], f"seed{seed}"
            )
        diverse |= not np.array_equal(scores[name][42], scores[name][43])
    tree42 = predictive_tree_hash(incumbent)
    tree43 = predictive_tree_hash(seed43)
    dump(
        args.output_dir / "stage1_gate.json",
        {
            "prediction_diversity": diverse,
            "tree42": tree42,
            "tree43": tree43,
            "predictive_trees_equal": tree42 == tree43,
            "raw_margin_diversity": {
                n: vector_diversity(raw[n][43], raw[n][42]) for n in raw
            },
            "response_score_diversity": {
                n: vector_diversity(scores[n][43], scores[n][42]) for n in scores
            },
            "stage2_permitted": diverse,
        },
    )
    if diverse:
        for seed in [44, 45]:
            models[seed] = fit_one(args, seed, x, y, frozen, params)
            for name, prep in prepared.items():
                scores[name][seed] = models[seed].predict(prep["x"], num_threads=4)
                raw[name][seed] = models[seed].predict(
                    prep["x"], num_threads=4, raw_score=True
                )
                results[name][str(seed)] = evaluate(
                    args, prep, scores[name][seed], scores[name][42], f"seed{seed}"
                )
        for name, prep in prepared.items():
            mean = equal_score_mean([scores[name][s] for s in [42, 43, 44, 45]])
            results[name]["ensemble"] = evaluate(
                args, prep, mean, scores[name][42], "ensemble"
            )
    qualifies = diverse and all(results[n]["ensemble"]["delta"] > 0 for n in results)
    dump(
        args.output_dir / "selection.json",
        {
            "stage2_run": diverse,
            "qualifies": bool(qualifies),
            "new_classifier_fit_count": len(models) - 1,
            "seed42_fit_count": 0,
            "decision": (
                "Generate one equal-mean candidate."
                if qualifies
                else "Retain submitted v18; no CSV."
            ),
            "sole_candidate": "Equal mean of42/43/44/45; no best seed or weight selection.",
            "ensemble_deltas": (
                {n: results[n]["ensemble"]["delta"] for n in results}
                if diverse
                else None
            ),
            "elapsed_before_optional_final_seconds": time.perf_counter() - began,
            "environment": _environment(),
            "versions": {
                n: importlib.metadata.version(n)
                for n in ["lightgbm", "numpy", "scipy", "scikit-learn"]
            },
        },
    )
    dump(
        args.output_dir / "all_seed_diversity.json",
        {
            "predictive_tree_hashes": {
                s: predictive_tree_hash(m) for s, m in models.items()
            },
            "raw_margins_vs42": {
                n: {s: vector_diversity(v, raw[n][42]) for s, v in vals.items()}
                for n, vals in raw.items()
            },
        },
    )
    if qualifies:
        candidate(
            args, [models[s] for s in [42, 43, 44, 45]], load_origin("final", catalog)
        )
    assert all(sha256_file(Path(p)) == h for p, h in frozen["source_sha256"].items())
    assert sha256_file(DEFINITION) == frozen["definition_sha256"]
    print(
        json.dumps(
            {
                "diverse": diverse,
                "qualifies": bool(qualifies),
                "new_fits": len(models) - 1,
            }
        ),
        flush=True,
    )


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--data-dir", type=Path, required=True)
    p.add_argument(
        "--output-dir", type=Path, default=Path("results/seed_ensemble_20261031_v20")
    )
    p.add_argument(
        "--private-dir", type=Path, default=Path("artifacts/seed_ensemble_20261031_v20")
    )
    run(p.parse_args())
