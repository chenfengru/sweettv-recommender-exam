"""One unseen-top50 expansion; retrained classifier selection, frozen-v14 diagnostic."""

import argparse
import hashlib
import json
import math
import time
import csv
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace
import numpy as np
from lightgbm import LGBMClassifier, Booster
from .audit_data import _environment
from .compare_models import history_slice
from .metrics import average_precision_at_k
from .csv_io import sha256_file
from .experiment_adaptive_threshold import compare, SLICE_ORDER
from .experiment_lightfm_extension import ORIGINS, train_cache
from .experiment_lower_threshold import START
from .experiment_personal_ties import list_difference
from .first_submission import verify_interaction_cache
from .interactions import targets, csv_rows
from .item_item import fit_item_item
from .item_fusion import seen_unseen_effects
from .lightfm_expansion import restore_lightfm, lightfm_ranking, expand_candidates
from .lightfm_features import FULL_FEATURES, pair_features, predictive_hash
from .personal_ties import global_qualified_statistics
from .reranker_features import (
    FEATURES,
    causal_history,
    user_features,
    candidate_labels,
    candidate_coverage,
    ranked_candidates,
)
from .schedule_features import canonical_schedule, schedule_origin
from .validate_submission import validate_submission

DEFINITION = Path("docs/lightfm_expansion_protocol.md")
OLD = Path("artifacts/lightfm_extension_20261030_v14")
META = Path("artifacts/lightgbm_reranker_20261030_v12")
PRIOR = Path("results/lightfm_extension_20261030_v14")
V14 = Path("submissions/candidate_lightgbm_lightfm_warp_20261030_v14.csv")
V14_HASH = "108b159c4e2c687b45f4c4d3e6e9519bace4abc73d5ba888f927a0efbb30ce90"


def dump(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n")


def summary(values):
    array = np.asarray(values, dtype=float)
    return {
        "users": len(values),
        "sum": int(array.sum()),
        "min": int(array.min()),
        "mean": float(array.mean()),
        "median": float(np.median(array)),
        "p90": float(np.quantile(array, 0.9)),
        "p95": float(np.quantile(array, 0.95)),
        "max": int(array.max()),
        "zero_users": int(np.sum(array == 0)),
    }


def build_origin(args, name, catalog, frozen):
    began = time.perf_counter()
    print(
        json.dumps(
            {"origin": name, "phase": "restore cached LightFM; expand before labels"}
        ),
        flush=True,
    )
    cutoff, pred_end = ORIGINS[name]
    cache = train_cache(name)
    manifest = verify_interaction_cache(cache)
    assert manifest["config"]["start"] == START and manifest["config"]["end"] == cutoff
    history = causal_history(cache / "segments.sqlite", START, cutoff)
    n50 = history["counts"][0.5]
    assert n50 == json.loads((OLD / name / "n50.json").read_text())
    source_report = json.loads((PRIOR / name / "feature_diagnostics.json").read_text())
    assert source_report["feature_cutoff"] == cutoff
    bundle = restore_lightfm(
        OLD / name, source_report["lightfm"]["predictive_state_sha256"]
    )
    schedule, coverage = schedule_origin(catalog, cutoff, pred_end)
    pool = {it for it, row in schedule.items() if row[1] > 0}
    assert len(pool) == source_report["support_and_features"]["available_programmes"]
    records = (
        (u, it, 0, n) for u, c in history["counts"][0.8].items() for it, n in c.items()
    )
    viewers, total = global_qualified_statistics(records)
    fallback = sorted(pool, key=lambda it: (-viewers[it], -total[it], it))
    item_began = time.perf_counter()
    if name in ["main", "auxiliary"]:
        path = Path(f"artifacts/item_item_20261030_v7/{name}/neighbours.json")
        sha = json.loads(
            Path("results/item_item_20261030_v7/preservation_checks.json").read_text()
        )["private_model_sha256"][str(path)]
        assert sha256_file(path) == sha
        neighbours = json.loads(path.read_text())
        item_source = {"verified_cache": str(path), "sha256": sha}
    else:
        neighbours, _, item_source = fit_item_item(n50)
    item_seconds = time.perf_counter() - item_began
    metadata = json.loads((META / name / "row_index.json").read_text())
    users = metadata["users"]
    original = metadata["items"]
    old_offsets = metadata["offsets"]
    old40 = np.load(OLD / name / "extended_features.npy", mmap_mode="r")
    assert old_offsets[-1] == len(old40)
    chunks = []
    expanded = []
    selected = []
    offsets = [0]
    old_to_new = []
    added_counts = []
    old_sizes = []
    overlap = {
        k: 0
        for k in [
            "lightfm_selected_pairs",
            "selected_overlap_v14",
            "selected_overlap_personal200",
            "selected_overlap_itemitem50",
            "selected_overlap_global5",
        ]
    }
    expansion_began = time.perf_counter()
    for index, (u, old_items) in enumerate(zip(users, original)):
        ranking = lightfm_ranking(bundle, u, pool)
        items, chosen = expand_candidates(
            old_items, ranking, n50.get(u, {}), u in bundle["user_index"]
        )
        assert (
            set(old_items) <= set(items)
            and len(items) == len(set(items)) <= len(old_items) + 50
        )
        if u not in bundle["user_index"]:
            assert items == sorted(old_items)
        _, x27 = user_features(
            u,
            history,
            neighbours,
            pool,
            viewers,
            total,
            fallback,
            candidate_items=items,
        )
        x7 = np.asarray([schedule[it] for it in items], dtype=np.float32)
        chunks.append(np.concatenate([x27, x7], axis=1))
        expanded.append(items)
        selected.append(chosen)
        local = {it: j for j, it in enumerate(items)}
        old_to_new.extend(offsets[-1] + local[it] for it in old_items)
        offsets.append(offsets[-1] + len(items))
        added_counts.append(len(items) - len(old_items))
        old_sizes.append(len(old_items))
        overlap["lightfm_selected_pairs"] += len(chosen)
        overlap["selected_overlap_v14"] += len(set(chosen) & set(old_items))
        ob, oe = old_offsets[index : index + 2]
        old_lookup = {it: j for j, it in enumerate(old_items)}
        for feature, key in [
            ("source_personal200", "selected_overlap_personal200"),
            ("source_unseen50", "selected_overlap_itemitem50"),
            ("source_global5", "selected_overlap_global5"),
        ]:
            overlap[key] += sum(
                old40[ob + old_lookup[it], FEATURES.index(feature)] == 1
                for it in set(chosen) & set(old_items)
            )
    x34 = np.concatenate(chunks)
    del chunks
    extra, support = pair_features(bundle, users, expanded, pool)
    x = np.concatenate([x34, extra], axis=1)
    del x34
    old_to_new = np.asarray(old_to_new, dtype=np.int64)
    if not np.array_equal(x[old_to_new], old40):
        bad = np.where(np.any(x[old_to_new] != old40, axis=0))[0]
        raise ValueError(
            "Original feature mismatch: " + str([FULL_FEATURES[j] for j in bad])
        )
    is_new = np.ones(len(x), dtype=bool)
    is_new[old_to_new] = False
    assert np.isfinite(x).all() and x.shape[1] == 40
    assert np.all(x[is_new, FEATURES.index("n50")] == 0)
    assert np.all(
        x[is_new][
            :,
            [
                FEATURES.index(k)
                for k in ["source_personal200", "source_unseen50", "source_global5"]
            ],
        ]
        == 0
    )
    assert (
        predictive_hash(bundle["model"])
        == source_report["lightfm"]["predictive_state_sha256"]
    )
    private = args.private_dir / name
    private.mkdir(parents=True, exist_ok=True)
    np.save(private / "expanded_features.npy", x, allow_pickle=False)
    np.save(private / "old_to_new.npy", old_to_new, allow_pickle=False)
    (private / "row_index.json").write_text(
        json.dumps(
            {"users": users, "items": expanded, "offsets": offsets},
            separators=(",", ":"),
        )
        + "\n"
    )
    (private / "selected_lightfm_unseen50.json").write_text(
        json.dumps(dict(zip(users, selected)), separators=(",", ":")) + "\n"
    )
    report = {
        "origin": name,
        "feature_cutoff": cutoff,
        "prediction_end": pred_end,
        "original_rows": len(old40),
        "expanded_rows": len(x),
        "additional_rows": int(is_new.sum()),
        "original_candidate_counts": summary(old_sizes),
        "expanded_candidate_counts": summary([len(r) for r in expanded]),
        "additional_candidates": summary(added_counts),
        "users_receiving_additions": sum(n > 0 for n in added_counts),
        "supported_users": sum(u in bundle["user_index"] for u in users),
        "unsupported_users_no_expansion": sum(
            u not in bundle["user_index"] for u in users
        ),
        "source_overlap": {k: int(v) for k, v in overlap.items()},
        "source_flags_for_new_only_rows_all_zero": True,
        "original40_features_exactly_equal": True,
        "schema": FULL_FEATURES,
        "all_finite": True,
        "support_and_features": support,
        "restored_lightfm_predictive_state_sha256": source_report["lightfm"][
            "predictive_state_sha256"
        ],
        "lightfm_fit_calls": 0,
        "item_item_feature_source": item_source,
        "item_item_seconds": item_seconds,
        "expansion_feature_seconds": time.perf_counter() - expansion_began,
        "elapsed_origin_seconds": time.perf_counter() - began,
        "matrix_bytes": x.nbytes,
        "environment": _environment(),
    }
    dump(args.output_dir / name / "candidate_features.json", report)
    return {
        "name": name,
        "x": x,
        "base": x,
        "users": users,
        "items": expanded,
        "offsets": offsets,
        "pool": pool,
        "private": private,
        "original": original,
        "old_to_new": old_to_new,
        "added_counts": added_counts,
        "history": history,
        "report": report,
    }


def infer(prepared, model, filename):
    assert model.booster_.feature_name() == FULL_FEATURES
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


def retrieval_diagnostics(prepared, truth, predictions):
    before = candidate_coverage(prepared["users"], prepared["original"], truth)
    after = candidate_coverage(prepared["users"], prepared["items"], truth)
    new_relevant = selected_new_relevant = selected_new = users_new = 0
    for u, old, new in zip(prepared["users"], prepared["original"], prepared["items"]):
        additions = set(new) - set(old)
        relevant = set(truth[u])
        new_relevant += len(additions & relevant)
        chosen = set(predictions[u]) & additions
        selected_new += len(chosen)
        selected_new_relevant += len(chosen & relevant)
        users_new += bool(chosen)
    return {
        "before": before,
        "after": after,
        "newly_retrieved_relevant_pairs": new_relevant,
        "new_only_recommendations": selected_new,
        "users_with_new_only_recommendations": users_new,
        "new_only_relevant_top5_hits": selected_new_relevant,
        "newly_retrieved_relevant_entering_top5": selected_new_relevant,
    }


def evaluate(args, prepared, model, diagnostic):
    name = prepared["name"]
    pred, slices, counts, cold = infer(prepared, model, "predictions.json")
    diag, _, _, _ = infer(
        prepared, diagnostic, "diagnostic_frozen_v14_predictions.json"
    )
    truth_path = (
        Path("artifacts/model_comparison_20261029/truth.json")
        if name == "main"
        else Path("artifacts/opportunity_week_20261030_v4/auxiliary/truth.json")
    )
    truth_hash = sha256_file(truth_path)
    truth = json.loads(truth_path.read_text())
    reference = json.loads((OLD / name / "predictions.json").read_text())
    assert set(truth) == set(pred) == set(reference)
    assert all(
        diag[u] == reference[u]
        for u, n in zip(prepared["users"], prepared["added_counts"])
        if n == 0
    )
    zero = {
        sl: {"complete_users": 0, "partial_users": 0, "completion_slots": 0}
        for sl in SLICE_ORDER
    }
    result = compare(truth, pred, reference, slices, zero, zero)
    diagnostic_result = compare(truth, diag, reference, slices, zero, zero)
    previous = json.loads((PRIOR / name / "comparison.json").read_text())
    assert (
        abs(result["reference_map_at_5"] - previous["comparison_v13"]["map_at_5"])
        < 1e-12
    )
    assert {k: r["users"] for k, r in result["history_slices"].items()} == {
        k: r["users"] for k, r in previous["comparison_v13"]["history_slices"].items()
    }
    result["seen_unseen_effects"] = seen_unseen_effects(truth, pred, reference, counts)
    diagnostic_result["seen_unseen_effects"] = seen_unseen_effects(
        truth, diag, reference, counts
    )
    for sl, r in result["history_slices"].items():
        r["seen_unseen_effects"] = seen_unseen_effects(
            {u: t for u, t in truth.items() if slices[u] == sl}, pred, reference, counts
        )
    retrieval = retrieval_diagnostics(prepared, truth, pred)
    assert retrieval["before"] == previous["candidate_coverage_exactly_equal_v13"]
    cold_report = {}
    for label, group in cold.items():
        assert len(group) == previous["cold_users"][label]["users"]
        d = [
            average_precision_at_k(truth[u], pred[u])
            - average_precision_at_k(truth[u], reference[u])
            for u in group
        ]
        cold_report[label] = {
            "users": len(group),
            "v14_map": math.fsum(
                average_precision_at_k(truth[u], reference[u]) for u in group
            )
            / len(group),
            "new_map": math.fsum(
                average_precision_at_k(truth[u], pred[u]) for u in group
            )
            / len(group),
            "diagnostic_map": math.fsum(
                average_precision_at_k(truth[u], diag[u]) for u in group
            )
            / len(group),
            "improved": sum(v > 0 for v in d),
            "worsened": sum(v < 0 for v in d),
            "unchanged": sum(v == 0 for v in d),
        }
    dump(
        args.output_dir / name / "comparison.json",
        {
            "origin": name,
            "retrained_comparison_v14": result,
            "diagnostic_only_frozen_v14_expanded": diagnostic_result,
            "diagnostic_excluded_from_selection": True,
            "retrieval": retrieval,
            "diagnostic_retrieval": retrieval_diagnostics(prepared, truth, diag),
            "cold_users": cold_report,
            "diagnostic_no_additions_exact_v14": True,
            "truth_sha256": truth_hash,
            "environment": _environment(),
        },
    )
    assert sha256_file(truth_path) == truth_hash
    print(
        json.dumps(
            {
                "split": name,
                "new_map": result["map_at_5"],
                "new_delta_v14": result["delta"],
                "new_ci": result["paired_bootstrap_95pct"],
                "diagnostic_map": diagnostic_result["map_at_5"],
                "new_relevant_candidates": retrieval["newly_retrieved_relevant_pairs"],
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
    path = Path("submissions/candidate_lightgbm_lightfm_expanded50_20261030_v15.csv")
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
    description = "Fixed historical LightGBM reranker retrained once on the same two historical origins with the v14 union expanded by LightFM-supported available N50-unseen top50, selected before union/dedup. Saved origin-specific WARP models reused without fitting; unsupported users unchanged. Same40 feature definitions, full-universe ranks and original source flags; all negatives retained, no tuning, blend, E2 or cold override. Frozen new classifier applied at final cutoff; candidate validated for manual review, no Kaggle score."
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
    args.output_dir.mkdir(parents=True, exist_ok=True)
    args.private_dir.mkdir(parents=True, exist_ok=True)
    frozen = json.loads((args.output_dir / "frozen_experiment.json").read_text())
    assert sha256_file(DEFINITION) == frozen["definition_sha256"]
    previous = {
        str(p): sha256_file(p) for p in sorted(Path("submissions").glob("*.csv"))
    }
    assert sha256_file(V14) == V14_HASH
    assert all(
        sha256_file(Path(p)) == h for p, h in frozen["source_artifact_sha256"].items()
    )
    inputs = json.loads(
        Path("results/lightgbm_reranker_20261030_v12/selection.json").read_text()
    )["input_sha256"]
    assert all(sha256_file(args.data_dir / name) == h for name, h in inputs.items())
    catalog, _ = canonical_schedule(
        [
            args.data_dir / f"export_arh_{period}-final.csv"
            for period in ["11-20", "21-30", "31-42"]
        ]
    )
    if args.resume_frozen_classifier:
        training = json.loads((args.output_dir / "training.json").read_text())
        model_hash = training["classifier_sha256"]
        assert sha256_file(args.private_dir / "frozen_model.txt") == model_hash
        model = SimpleNamespace(booster_=Booster(model_file=str(args.private_dir / "frozen_model.txt")))
        assert model.booster_.current_iteration() == 300
    else:
        assert not (args.private_dir / "frozen_model.txt").exists(), "Use --resume-frozen-classifier; a classifier already exists."
        train = []
        labels = []
        origin_rows = []
        for name in ["origin_20200406", "origin_20200420"]:
            prepared = build_origin(args, name, catalog, frozen)
            label_cache = META / name / "labels"
            label_manifest = verify_interaction_cache(label_cache)
            assert (
                label_manifest["config"]["start"] == ORIGINS[name][0]
                and label_manifest["config"]["end"] == ORIGINS[name][1]
            )
            truth = targets(
                json.loads((label_cache / "interactions.json").read_text()),
                prepared["pool"],
            )
            y = candidate_labels(prepared["users"], prepared["items"], truth)
            old_y = np.load(META / name / "labels.npy")
            assert np.array_equal(y[prepared["old_to_new"]], old_y)
            coverage_before = candidate_coverage(
                prepared["users"], prepared["original"], truth
            )
            coverage_after = candidate_coverage(prepared["users"], prepared["items"], truth)
            report = {
                "origin": name,
                "old_rows": len(old_y),
                "expanded_rows": len(y),
                "old_positive_rows": int(old_y.sum()),
                "expanded_positive_rows": int(y.sum()),
                "positive_rate": float(y.mean()),
                "original_labels_exactly_equal": True,
                "candidate_coverage_before": coverage_before,
                "candidate_coverage_after": coverage_after,
                "all_negative_candidate_queries_before": sum(
                    not old_y[a:b].any()
                    for a, b in zip(
                        json.loads((META / name / "row_index.json").read_text())["offsets"][
                            :-1
                        ],
                        json.loads((META / name / "row_index.json").read_text())["offsets"][
                            1:
                        ],
                    )
                ),
                "all_negative_candidate_queries_after": sum(
                    not y[a:b].any()
                    for a, b in zip(prepared["offsets"][:-1], prepared["offsets"][1:])
                ),
                "no_label_based_user_or_candidate_selection": True,
            }
            dump(args.output_dir / name / "training_origin.json", report)
            origin_rows.append(report)
            np.save(prepared["private"] / "labels.npy", y, allow_pickle=False)
            train.append(prepared["x"])
            labels.append(y)
            del prepared, truth
        x = np.concatenate(train)
        y = np.concatenate(labels)
        del train, labels
        began_fit = time.perf_counter()
        model = LGBMClassifier(**frozen["lightgbm_parameters"])
        model.fit(x, y, feature_name=FULL_FEATURES)
        fit_seconds = time.perf_counter() - began_fit
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
                "origins": origin_rows,
                "rows": len(y),
                "positive_rows": int(y.sum()),
                "positive_rate": float(y.mean()),
                "classifier_fit_calls": 1,
                "LightFM_fit_calls": 0,
                "trained_iterations": 300,
                "schema": FULL_FEATURES,
                "parameters": frozen["lightgbm_parameters"],
                "classifier_sha256": model_hash,
                "fit_seconds": fit_seconds,
                "environment": _environment(),
            },
        )
        del x, y
    diagnostic = SimpleNamespace(
        booster_=Booster(model_file=str(OLD / "frozen_model.txt"))
    )
    assert diagnostic.booster_.feature_name() == FULL_FEATURES
    results = {}
    for name in ["main", "auxiliary"]:
        prepared = build_origin(args, name, catalog, frozen)
        results[name] = evaluate(args, prepared, model, diagnostic)
        del prepared
    qualifies = all(r["delta"] > 0 for r in results.values())
    dump(
        args.output_dir / "selection.json",
        {
            "qualifies": qualifies,
            "decision": (
                "Generate exactly one new-model candidate."
                if qualifies
                else "Retain v14; no CSV or extra variants."
            ),
            "new_model_deltas_v14": {s: r["delta"] for s, r in results.items()},
            "diagnostic_excluded_from_selection": True,
            "classifier_fit_calls": 1,
            "LightFM_fit_calls": 0,
            "classifier_sha256": model_hash,
            "frozen_protocol_sha256": frozen["definition_sha256"],
            "preserved_csv_sha256": previous,
            "original_v14_artifact_sha256": frozen["source_artifact_sha256"],
            "elapsed_before_optional_final_seconds": time.perf_counter() - began,
            "environment": _environment(),
            "v14_kaggle": {
                "private": 0.43416,
                "public": 0.44157,
                "source": "User-screenshot-reported; no independent lookup.",
                "submission_id": None,
                "submission_timestamp": None,
            },
        },
    )
    print(
        json.dumps(
            {
                "qualifies": qualifies,
                "new_deltas_v14": {s: r["delta"] for s, r in results.items()},
            }
        ),
        flush=True,
    )
    if qualifies:
        final = build_origin(args, "final", catalog, frozen)
        make_candidate(args, final, model, model_hash)
    else:
        dump(
            args.output_dir / "candidate_decision.json",
            {
                "decision": "Retain v14. New model fails strict gain on both splits; diagnostic is not selectable. No final expansion/CSV or further variants."
            },
        )
    assert all(sha256_file(Path(p)) == h for p, h in previous.items()) and all(
        sha256_file(Path(p)) == h for p, h in frozen["source_artifact_sha256"].items()
    )
    assert (
        sha256_file(DEFINITION) == frozen["definition_sha256"]
        and hashlib.sha256(model.booster_.model_to_string().encode()).hexdigest()
        == model_hash
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("results/lightfm_expansion_20261030_v15"),
    )
    parser.add_argument(
        "--private-dir",
        type=Path,
        default=Path("artifacts/lightfm_expansion_20261030_v15"),
    )
    parser.add_argument("--resume-frozen-classifier", action="store_true")
    run(parser.parse_args())
