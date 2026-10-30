"""One seven-feature schedule extension; immutable v12 candidate/label caches."""

import argparse
import csv
import hashlib
import json
import math
import subprocess
import sys
import time
from collections import Counter
from pathlib import Path
import numpy as np
from lightgbm import LGBMClassifier
from .audit_data import _environment
from .compare_models import history_slice
from .csv_io import sha256_file
from .experiment_adaptive_threshold import compare, SLICE_ORDER
from .experiment_lower_threshold import START, MAIN_CUTOFF, AUX_CUTOFF, END, FUTURE_END
from .experiment_personal_ties import list_difference
from .item_fusion import seen_unseen_effects
from .metrics import average_precision_at_k
from .real_matching_audit import stamp
from .reranker_features import FEATURES, candidate_coverage, ranked_candidates
from .schedule_features import (
    canonical_schedule,
    schedule_origin,
    augment,
    distribution,
    exposure_group,
    SCHEDULE_FEATURES,
    EXTENDED_FEATURES,
)
from .validate_submission import validate_submission

DEFINITION = Path("docs/schedule_reranker_protocol.md")
V12 = Path("submissions/candidate_lightgbm_historical_fixed_20261030_v12.csv")
V12_HASH = "e18c49cb106df5b5e50f3b7123a080443a2ab48c709e68e721ee9965d96b1457"
OLD = Path("artifacts/lightgbm_reranker_20261030_v12")
PRIOR = Path("results/lightgbm_reranker_20261030_v12")
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


def load_augmented(args, name, schedule, coverage, frozen):
    began = time.perf_counter()
    source = OLD / name
    for file in ["features.npy", "row_index.json"]:
        assert (
            sha256_file(source / file)
            == frozen["source_artifact_sha256"][str(source / file)]
        )
    base = np.load(source / "features.npy", mmap_mode="r")
    metadata = json.loads((source / "row_index.json").read_text())
    users, items, offsets = metadata["users"], metadata["items"], metadata["offsets"]
    assert offsets[-1] == len(base)
    x, stats = augment(base, items, schedule)
    prior_path = (
        PRIOR
        / name
        / ("origin.json" if name.startswith("origin_") else "comparison.json")
    )
    if name == "final":
        previous = json.loads((PRIOR / "candidate_artifact.json").read_text())[
            "final_origin"
        ]
    else:
        previous = json.loads(prior_path.read_text())
    pool = {it for it, row in schedule.items() if row[1] > 0}
    assert len(pool) == previous["candidate_pool"]
    assert (
        len(x) == previous["features"]["rows"]
        and len(users) == previous["feature_user_universe"]
    )
    private = args.private_dir / name
    private.mkdir(parents=True, exist_ok=True)
    np.save(private / "augmented_features.npy", x, allow_pickle=False)
    stats.update(
        {
            "origin": name,
            "rows": len(x),
            "users": len(users),
            "schema": EXTENDED_FEATURES,
            "matrix_bytes": x.nbytes,
            "candidate_equality": "Exact cached row_index/users/items/offsets retained; no candidate construction or label injection.",
            "source_hashes": {
                file: frozen["source_artifact_sha256"][str(source / file)]
                for file in ["features.npy", "row_index.json"]
            },
            "coverage": coverage,
            "all_schedule_programme_distributions": distribution(
                np.asarray(list(schedule.values()), dtype=np.float64), SCHEDULE_FEATURES
            ),
            "candidate_rows_by_exposure_group": dict(
                Counter(exposure_group(schedule[it]) for row in items for it in row)
            ),
            "augmentation_seconds": time.perf_counter() - began,
            "environment": _environment(),
        }
    )
    dump(args.output_dir / name / "feature_diagnostics.json", stats)
    return {
        "x": x,
        "base": base,
        "users": users,
        "items": items,
        "offsets": offsets,
        "pool": pool,
        "schedule": schedule,
        "stats": stats,
        "private": private,
    }


def infer(prepared, model):
    assert (
        model.booster_.feature_name() == EXTENDED_FEATURES
        and prepared["x"].shape[1] == 34
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


def group_effects(truth, pred, reference, schedule):
    result = {
        g: {
            "candidate_group": "sign of schedule-only log_broadcast_rate_change",
            "entering_relevant": 0,
            "leaving_relevant": 0,
            "baseline_selected": 0,
            "extended_selected": 0,
            "baseline_relevant_hits": 0,
            "extended_relevant_hits": 0,
            "baseline_ap_terms": [],
            "extended_ap_terms": [],
        }
        for g in ["increased", "decreased", "unchanged"]
    }
    for u, target in truth.items():
        relevant = set(target)
        for item in (set(pred[u]) - set(reference[u])) & relevant:
            result[exposure_group(schedule[item])]["entering_relevant"] += 1
        for item in (set(reference[u]) - set(pred[u])) & relevant:
            result[exposure_group(schedule[item])]["leaving_relevant"] += 1
        for method, ranking in [("baseline", reference[u]), ("extended", pred[u])]:
            hits = 0
            for rank, item in enumerate(ranking, 1):
                group = exposure_group(schedule[item])
                r = result[group]
                r[method + "_selected"] += 1
                if item in relevant:
                    hits += 1
                    r[method + "_relevant_hits"] += 1
                    r[method + "_ap_terms"].append(hits / rank / min(5, len(relevant)))
    for r in result.values():
        r["baseline_map_contribution"] = math.fsum(r.pop("baseline_ap_terms")) / len(
            truth
        )
        r["extended_map_contribution"] = math.fsum(r.pop("extended_ap_terms")) / len(
            truth
        )
        r["delta_map_contribution"] = (
            r["extended_map_contribution"] - r["baseline_map_contribution"]
        )
        r["net_relevant_hits"] = r["entering_relevant"] - r["leaving_relevant"]
    return result


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
        abs(result["reference_map_at_5"] - prior["comparisons"]["v9"]["map_at_5"])
        < 1e-12
    )
    assert {sl: r["users"] for sl, r in result["history_slices"].items()} == {
        sl: r["users"] for sl, r in prior["comparisons"]["v9"]["history_slices"].items()
    }
    coverage = candidate_coverage(prepared["users"], prepared["items"], truth)
    assert coverage == prior["candidate_coverage"]
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
                "v12_map": math.fsum(
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
    groups = group_effects(truth, pred, reference, prepared["schedule"])
    assert (
        abs(
            math.fsum(g["delta_map_contribution"] for g in groups.values())
            - result["delta"]
        )
        < 1e-12
    )
    report = {
        "origin": name,
        "comparison_v12": result,
        "candidate_equality": True,
        "candidate_coverage_exactly_equal_v12": coverage,
        "cold_users": cold_report,
        "schedule_exposure_groups": groups,
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
                "delta_v12": result["delta"],
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
    reference = {
        r["user_id"]: r["tv_show_id"].split()
        for r in __import__("src.interactions", fromlist=["csv_rows"]).csv_rows(V12)
    }
    assert reference == json.loads((OLD / "final/predictions.json").read_text())
    template = args.data_dir / "submission.csv"
    path = Path("submissions/candidate_lightgbm_schedule_exposure_20261030_v13.csv")
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
    description = "Fixed historical LightGBM reranker with v12 candidate union and 27 unchanged causal features, plus seven canonical schedule-exposure features: past28-day and exact future-window airings/day, clipped broadcastseconds/day, their log1p rate changes and zero-past indicator. Same two early training origins/labels and fixed300-tree settings; no future viewing/content features, E2, blend or cold override. Same frozen classifier applied at weeks11–30 cutoff for weeks31–42 carryover-aware candidates. Validated for manual review; no Kaggle score."
    dump(
        args.output_dir / "candidate_artifact.json",
        {
            "filename": path.name,
            "absolute_path": str(path.resolve()),
            "sha256": sha256_file(path),
            "validation": validation,
            "differences_from_submitted_v12": list_difference(pred, reference),
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
    assert sha256_file(V12) == V12_HASH
    assert all(
        sha256_file(Path(p)) == h for p, h in frozen["source_artifact_sha256"].items()
    )
    inputs = json.loads((PRIOR / "selection.json").read_text())["input_sha256"]
    paths = [
        args.data_dir / f"export_arh_{period}-final.csv"
        for period in ["11-20", "21-30", "31-42"]
    ]
    assert all(sha256_file(p) == inputs[p.name] for p in paths)
    catalog, sources = canonical_schedule(paths)
    schedules = {}
    coverage = {}
    for name, (cutoff, end) in ORIGINS.items():
        schedules[name], coverage[name] = schedule_origin(
            catalog, cutoff, end, require_coverage=False
        )
    dump(
        args.output_dir / "schedule_coverage.json",
        {"sources": sources, "origins": coverage},
    )
    if not all(
        r[w]["coverage_gate_passed"]
        for r in coverage.values()
        for w in ["past", "future"]
    ):
        dump(
            args.output_dir / "candidate_decision.json",
            {
                "decision": "Required schedule coverage unavailable; stopped before fitting. No zero imputation, model or CSV."
            },
        )
        raise RuntimeError("Schedule coverage gate failed; stop experiment")
    del catalog
    train = []
    labels = []
    for name in ["origin_20200406", "origin_20200420"]:
        prepared = load_augmented(args, name, schedules[name], coverage[name], frozen)
        label_path = OLD / name / "labels.npy"
        assert (
            sha256_file(label_path) == frozen["source_artifact_sha256"][str(label_path)]
        )
        y = np.load(label_path)
        assert len(y) == len(prepared["x"])
        train.append(prepared["x"])
        labels.append(y)
    x = np.concatenate(train)
    y = np.concatenate(labels)
    del train, labels
    old_training = json.loads((PRIOR / "training.json").read_text())
    assert (
        len(y) == old_training["total_rows"]
        and int(y.sum()) == old_training["positive_rows"]
    )
    model = LGBMClassifier(**frozen["parameters"])
    fit_started = time.perf_counter()
    model.fit(x, y, feature_name=EXTENDED_FEATURES)
    fit_seconds = time.perf_counter() - fit_started
    assert (
        model.booster_.current_iteration() == 300
        and model.booster_.feature_name() == EXTENDED_FEATURES
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
            "parameters": frozen["parameters"],
            "schema": EXTENDED_FEATURES,
            "original_v12_candidate_rows_and_labels_equal": True,
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
                    EXTENDED_FEATURES,
                    model.booster_.feature_importance(importance_type="gain"),
                    model.booster_.feature_importance(importance_type="split"),
                )
            ],
            key=lambda r: (-r["gain"], r["feature"]),
        ),
    )
    del x, y, prepared
    reports = {}
    for name in ["main", "auxiliary"]:
        prepared = load_augmented(args, name, schedules[name], coverage[name], frozen)
        reports[name] = evaluate(args, name, prepared, model)
        del prepared
    qualifies = all(r["comparison_v12"]["delta"] > 0 for r in reports.values())
    final = load_augmented(args, "final", schedules["final"], coverage["final"], frozen)
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
                else "Retain v12; no CSV and no further variants."
            ),
            "deltas_v12": {s: r["comparison_v12"]["delta"] for s, r in reports.items()},
            "frozen_protocol_sha256": frozen["definition_sha256"],
            "classifier_sha256": model_hash,
            "classifier_fit_calls": 1,
            "preserved_csv_sha256": previous,
            "original_v12_artifact_sha256": frozen["source_artifact_sha256"],
            "elapsed_before_optional_final_seconds": time.perf_counter() - began,
            "environment": _environment(),
            "v12_kaggle": {
                "private": 0.42660,
                "public": 0.43394,
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
                "deltas_v12": {
                    s: r["comparison_v12"]["delta"] for s, r in reports.items()
                },
            }
        ),
        flush=True,
    )
    if qualifies:
        make_candidate(args, final, model, model_hash)
    else:
        dump(
            args.output_dir / "candidate_decision.json",
            {
                "decision": "Retain submitted v12; schedule extension fails strict improvement on both splits. No prediction CSV or further variants."
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
        default=Path("results/schedule_reranker_20261030_v13"),
    )
    parser.add_argument(
        "--private-dir",
        type=Path,
        default=Path("artifacts/schedule_reranker_20261030_v13"),
    )
    run(parser.parse_args())
