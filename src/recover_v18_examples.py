"""Inference-only recovery for original private example identities; no fitting."""

import argparse
import json, sqlite3, hashlib, time
from pathlib import Path
import numpy as np
from lightgbm import Booster
from src.csv_io import sha256_file
from src.first_submission import verify_interaction_cache
from src.experiment_lightfm_extension import ORIGINS, train_cache
from src.experiment_lower_threshold import START
from src.reranker_features import causal_history, user_features, ranked_candidates
from src.personal_ties import global_qualified_statistics
from src.schedule_features import canonical_schedule, schedule_origin, augment
from src.lightfm_expansion import restore_lightfm
from src.lightfm_features import pair_features, append_features
from src.channel_affinity import channel_statistics, programme_weights, append_affinity
from src.experiment_channel_affinity import FULL_FEATURES
from src.interactions import schedule_catalog


def run(args):
    # Recovery identities/caches must remain under the ignored artifact root.
    args.private_dir.resolve().relative_to(Path("artifacts").resolve())
    if args.private_dir.exists():
        raise FileExistsError("Choose a new ignored private recovery folder.")
    began = time.perf_counter()
    data = args.data_dir
    old = Path("artifacts/channel_affinity_20261030_v18")
    meta = Path("artifacts/lightgbm_reranker_20261030_v12/main")
    base = Path("artifacts/model_comparison_20261029")
    setup = json.loads((base / "setup.json").read_text())
    examples = setup["examples"]
    users = [examples[k] for k in ["history_poor", "history_rich"]]
    assert all(
        json.loads((base / "example_histories.json").read_text())[k]["user_id"] == v
        for k, v in examples.items()
    )
    preserved = [
        base / "setup.json",
        base / "example_histories.json",
        base / "truth.json",
        old / "frozen_model.txt",
        old / "main/extended_features.npy",
        old / "main/predictions.json",
        meta / "row_index.json",
    ]
    preserved += list(Path("submissions").glob("*.csv"))
    original_hash = {str(p): sha256_file(p) for p in preserved}
    cutoff, end = ORIGINS["main"]
    cache = train_cache("main")
    manifest = verify_interaction_cache(cache)
    assert manifest["config"]["start"] == START and manifest["config"]["end"] == cutoff
    with sqlite3.connect(
        "file:" + str((cache / "segments.sqlite").resolve()) + "?mode=ro", uri=True
    ) as db:
        assert (
            db.execute(
                "SELECT COUNT(*) FROM views WHERE s < ? OR e > ? OR s >= ?",
                (START, cutoff, cutoff),
            ).fetchone()[0]
            == 0
        )
        assert (
            db.execute(
                "SELECT COUNT(*) FROM segments WHERE s < ? OR e > ? OR s >= ?",
                (START, cutoff, cutoff),
            ).fetchone()[0]
            == 0
        )
    history = causal_history(cache / "segments.sqlite", START, cutoff)
    assert history["counts"][0.5] == json.loads(
        Path("artifacts/lightfm_extension_20261030_v14/main/n50.json").read_text()
    )
    paths = [data / f"export_arh_{s}-final.csv" for s in ["11-20", "21-30", "31-42"]]
    catalog, _ = canonical_schedule(paths)
    schedule, coverage = schedule_origin(catalog, cutoff, end)
    pool = {it for it, row in schedule.items() if row[1] > 0}
    assert len(pool) == 6384 and pool == set(setup["candidates"])
    viewers, total = global_qualified_statistics(
        (u, it, 0, n) for u, c in history["counts"][0.8].items() for it, n in c.items()
    )
    fallback = sorted(pool, key=lambda it: (-viewers[it], -total[it], it))
    neighpath = Path("artifacts/item_item_20261030_v7/main/neighbours.json")
    assert (
        sha256_file(neighpath)
        == json.loads(
            Path("results/item_item_20261030_v7/preservation_checks.json").read_text()
        )["private_model_sha256"][str(neighpath)]
    )
    neighbours = json.loads(neighpath.read_text())
    items = []
    matrices = []
    offsets = [0]
    for u in users:
        row, x = user_features(u, history, neighbours, pool, viewers, total, fallback)
        assert row == sorted(set(row)) and set(row) <= pool
        items.append(row)
        matrices.append(x)
        offsets.append(offsets[-1] + len(row))
    x27 = np.concatenate(matrices)
    x34, _ = augment(x27, items, schedule)
    lightfm = restore_lightfm(
        Path("artifacts/lightfm_extension_20261030_v14/main"),
        json.loads(
            Path(
                "results/lightfm_extension_20261030_v14/main/feature_diagnostics.json"
            ).read_text()
        )["lightfm"]["predictive_state_sha256"],
    )
    extra, _ = pair_features(lightfm, users, items, pool)
    x40 = append_features(x34, extra)
    channel = channel_statistics(cache / "segments.sqlite", START, cutoff)
    weights = programme_weights(catalog, cutoff, end)
    x52, _ = append_affinity(x40, users, items, channel, weights)
    model = Booster(model_file=str(old / "frozen_model.txt"))
    assert (
        sha256_file(old / "frozen_model.txt")
        == json.loads(
            Path("results/channel_affinity_20261030_v18/training.json").read_text()
        )["classifier_sha256"]
    )
    assert (
        model.feature_name() == FULL_FEATURES
        and x52.shape[1] == 52
        and np.isfinite(x52).all()
        and model.current_iteration() == 300
    )
    saved_meta = json.loads((meta / "row_index.json").read_text())
    saved_x = np.load(old / "main/extended_features.npy", mmap_mode="r")
    saved_pred = json.loads((old / "main/predictions.json").read_text())
    truth = json.loads((base / "truth.json").read_text())
    assert (
        users[0] not in truth
        and users[0] not in saved_meta["users"]
        and users[0] not in saved_pred
    )
    j = saved_meta["users"].index(users[1])
    a, b = saved_meta["offsets"][j : j + 2]
    assert items[1] == saved_meta["items"][j] and np.array_equal(
        x52[offsets[1] : offsets[2]], saved_x[a:b]
    )
    scores = model.predict(x52, num_threads=4)
    assert np.isfinite(scores).all() and np.all((scores >= 0) & (scores <= 1))
    pred = {}
    for u, row, a, b in zip(users, items, offsets[:-1], offsets[1:]):
        order, size = ranked_candidates(
            row,
            scores[a:b],
            history["counts"][0.5].get(u, {}),
            viewers,
            total,
            pool,
            fallback,
        )
        assert (
            size == 5
            and len(order) == len(set(order)) == 5
            and set(order) <= pool
            and "0" not in order
        )
        independent = sorted(
            zip(row, scores[a:b]),
            key=lambda z: (
                -z[1],
                -history["counts"][0.5].get(u, {}).get(z[0], 0),
                -viewers[z[0]],
                -total[z[0]],
                z[0],
            ),
        )
        assert order == [it for it, score in independent[:5]]
        pred[u] = order
    assert pred[users[1]] == saved_pred[users[1]]
    # Display-only source metadata, same convention as original comparison examples.
    _, _, display = schedule_catalog(paths[:2], START, end, end)
    report_path = args.report_path
    report = report_path.read_text()
    report = report.split("\n## Recovery checks\n", 1)[0].rstrip() + "\n"
    light_rows = []
    for rank, it in enumerate(pred[users[0]], 1):
        assert it in display and display[it][0] and display[it][1]
        title, category = display[it][:2]
        light_rows.append(
            f"| V18 final model | {rank} | {it} | {title.replace('|','/')} | {category.replace('|','/')} | not evaluable |"
        )
    report = report.replace(
        "No model was retrained, tuned or refitted; no new predictions were generated.",
        "No model was retrained, tuned or refitted. The light user’s missing main-window predictions were recovered by applying the saved v18 classifier to reconstructed main-window features; the original heavy user was reconstructed only as a control.",
    )
    report = report.replace(
        "**Saved-output gap:** the light user is absent from both the saved v18 main predictions and the saved main candidate/feature-row index. Therefore a v18 main top-five list cannot be exported for this user from those artifacts. The final-window list is not substituted. The heavy user’s v18 main list is available.",
        "**Why the previous output was missing:** the v18 main prediction/feature tables inherit the fixed 4,625-user evaluation cohort, which contains only users with nonempty qualified held-out targets. The original light user has no such targets, so the user had no saved main prediction or feature rows. The previous export reported that cache gap rather than generating new inference. This recovery preserves the original user and reconstructs the unchanged main-window pipeline, then applies the saved v18 classifier without training. The final-window list is never substituted.",
    )
    report = report.replace(
        "Programme titles and categories are copied verbatim from the already published original example tables, which document display-only schedule metadata; their original-language strings are retained.",
        "Original baseline and heavy-user titles/categories remain copied verbatim from the published examples. Recovered light-user v18 titles/categories come from the original schedule files using the same display-only canonical metadata convention (modal canonical-airing attributes, deterministic ties, observed schedule starts before the main-window end); original-language strings are retained.",
    )
    import re

    light, rest = report.split("\n## Heavy user", 1)
    light = re.sub(r"^\| V18 final model \|.*$", "", light, flags=re.MULTILINE)
    marker = "\n| Method | Relevant hits in top five | AP@5 |"
    light = light.replace(marker, "\n" + "\n".join(light_rows) + "\n" + marker, 1)
    report = light + "\n## Heavy user" + rest
    report = report.replace(
        "V18 final model (saved prediction unavailable)",
        "V18 final model (recovered main inference)",
    )
    old_interpret = "V18 behaviour cannot be described because the required main-window prediction and feature rows are missing."
    new_interpret = "The recovered v18 list is reported above for descriptive comparison only; its hit indicators and AP@5 remain not evaluable because the main target set is empty. It must not be scored as zero or used to claim an accuracy gain."
    report = report.replace(old_interpret, new_interpret)
    report = report.replace(
        "- The light user’s missing main list is an export-coverage limitation, not a zero AP score. No replacement user or final-window list was used.",
        "- The light user’s originally missing main list was caused by evaluation-cohort filtering. It has now been recovered by inference only; the evaluation cohort and metrics remain unchanged. No replacement user or final-window list was used.",
    )
    checks = {
        "history_window": [START, cutoff],
        "forecast_window": [cutoff, end],
        "clock": "source-naive wall seconds; no timezone conversion",
        "feature_schema": FULL_FEATURES,
        "feature_count": 52,
        "finite_features": True,
        "candidate_universe": len(pool),
        "recovered_light_candidate_rows": len(items[0]),
        "heavy_control_candidate_rows": len(items[1]),
        "heavy_control_all52_values_bitwise_equal_saved_main": True,
        "heavy_control_prediction_equal_saved_main": True,
        "model_sha256": sha256_file(old / "frozen_model.txt"),
        "model_iterations": 300,
        "model_fits": 0,
        "all_interaction_segments_and_cleaned_views_within_history_boundaries": True,
        "tie_order": "descending binary score, N50, global80 viewers, global80 user-airings; ascending raw string programme ID",
        "five_distinct_nonzero_available_predictions": True,
        "light_ap_at_5": "not evaluable",
        "light_main_target_count": 0,
        "raw_user_ids_published": False,
        "elapsed_seconds": time.perf_counter() - began,
        "native_records": "unmodified",
        "student_verification": "pending",
    }
    report += "\n## Recovery checks\n\nReconstructed the original light user and the same original heavy control from the main pre-cutoff interaction cache. The heavy control’s complete candidate rows and all 52 feature values match saved v18 main arrays **bit-for-bit**, and its prediction reproduces the saved list exactly. The original light-user identity mapping is unchanged and remains private.\n\n"
    report += f"The recovered light user has {len(items[0])} original-rule candidate rows from the unchanged 6,384-programme main pool. Feature order exactly matches the saved 52-column classifier schema; all values and predictions are finite. Cleaned viewing and matched segments were checked to stay within [Mar9,May18), and the forecast schedule is clipped to [May18,Jul27), including carryovers. The saved classifier hash and 300-tree count were verified; zero fits occurred. Ranking uses descending score, N50 count, global80 distinct viewers, global80 user-airing count, then ascending raw string programme ID. An independent direct sort reproduces all five predictions; all are distinct, nonzero and available. No held-out viewing enters any feature.\n\n"
    report += "[Anonymous recovery verification](v18_light_user_recovery_checks.json) records schema, checks and classifier hash. Candidate rows, features, scores and the private mapping are kept only in a new ignored recovery folder; original model, caches, predictions and CSVs remain unchanged. AP@5 remains **not evaluable**. Student verification remains pending.\n"
    for u in users:
        assert u not in report
    assert (
        "saved prediction unavailable" not in report
        and "No saved main-window list" not in report
    )
    private = args.private_dir
    assert not private.exists(), "Choose a new ignored private output folder."
    private.mkdir(parents=True)
    (private / "source_user_mapping.json").write_text(
        json.dumps({k: examples[k] for k in ["history_poor", "history_rich"]}, indent=2)
        + "\n"
    )
    (private / "row_index.json").write_text(
        json.dumps({"users": users, "items": items, "offsets": offsets}) + "\n"
    )
    np.save(private / "features52.npy", x52)
    np.save(private / "scores.npy", scores)
    (private / "predictions.json").write_text(json.dumps(pred) + "\n")
    assert all(sha256_file(Path(p)) == h for p, h in original_hash.items())
    report_path.write_text(report)
    check_path = report_path.parent / "v18_light_user_recovery_checks.json"
    check_path.write_text(json.dumps(checks, indent=2) + "\n")
    print(
        json.dumps(
            {
                "status": "recovered",
                "light_top5": pred[users[0]],
                "light_ap_at_5": "not evaluable",
                "heavy_control_exact": True,
                "original_artifacts_preserved": True,
            }
        ),
        flush=True,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--private-dir", type=Path, required=True)
    parser.add_argument(
        "--report-path",
        type=Path,
        default=Path("results/final_report_examples/v18_two_user_examples.md"),
    )
    run(parser.parse_args())
