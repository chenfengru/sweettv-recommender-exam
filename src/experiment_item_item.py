"""One fixed item-item fit per split; no fusion, final refit or submission CSV."""

import argparse
import hashlib
import json
import math
import time
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
from .audit_data import _environment
from .compare_models import history_slice, versions, rss
from .csv_io import sha256_file
from .experiment_viewing_strength import (
    START,
    MAIN_CUTOFF,
    AUX_CUTOFF,
    END,
    ORIGINAL,
    BASELINE,
    BASELINE_HASH,
    prediction_airing_counts,
)
from .first_submission import verify_interaction_cache
from .improvement_helpers import complete
from .item_item import fit_item_item, score_user, retrieval_metrics
from .metrics import average_precision_at_k
from .models import Ranker
from .personal_threshold import personal_counts, predict
from .personal_ties import global_qualified_statistics

DEFINITION = Path("docs/item_item_protocol.md")


def distribution(values):
    return {
        "min": min(values),
        "median": float(np.median(values)),
        "p95": float(np.quantile(values, 0.95)),
        "max": max(values),
        "sum": sum(values),
        "mean": math.fsum(values) / len(values),
    }


def evaluate_split(name, cache, truth_path, fit_end, candidates, out, private):
    started = time.perf_counter()
    out.mkdir(parents=True, exist_ok=True)
    private.mkdir(parents=True, exist_ok=True)
    manifest = verify_interaction_cache(cache)
    truth_hash = sha256_file(truth_path)
    truth = json.loads(truth_path.read_text())
    users = sorted(truth)
    expected_users, expected_candidates = (
        (4625, 6384) if name == "main" else (4589, 5742)
    )
    assert len(users) == expected_users and len(candidates) == expected_candidates
    records = json.loads((cache / "interactions.json").read_text())
    anchor = Ranker(records, candidates, {}, "personal")
    viewers, total = global_qualified_statistics(records)
    extraction_start = time.perf_counter()
    counts = personal_counts(
        cache / "segments.sqlite", START, fit_end, thresholds=(0.5, 0.8)
    )
    extraction_seconds = time.perf_counter() - extraction_start
    assert counts[0.8] == dict(anchor.qualified)
    n50 = counts[0.5]
    history_slices = {u: history_slice(len(counts[0.8].get(u, {}))) for u in users}
    anchors = {
        "truth": truth,
        "viewers": dict(viewers),
        "total": dict(total),
        "fallback": anchor.fallback,
        "slices": history_slices,
        "candidates": sorted(candidates),
    }
    digest = lambda: hashlib.sha256(
        json.dumps(anchors, sort_keys=True).encode()
    ).hexdigest()
    anchor_digest = digest()
    previous_anchor = json.loads(
        Path(
            f"results/viewing_strength_20261030_v6/{name}/frozen_anchors.json"
        ).read_text()
    )["sha256"]
    assert anchor_digest == previous_anchor
    reference = json.loads(
        Path(
            f"artifacts/personal_threshold_20261030_v5/{name}/T50_predictions.json"
        ).read_text()
    )
    baseline, _ = predict(n50, candidates, viewers, total, anchor.fallback, users)
    assert baseline == {u: reference[u] for u in users}
    fit_started = time.perf_counter()
    neighbours, support, model_stats = fit_item_item(n50)
    fit_seconds = time.perf_counter() - fit_started
    fit_rss = rss()
    (private / "neighbours.json").write_text(
        json.dumps(neighbours, separators=(",", ":")) + "\n"
    )
    (private / "n50.json").write_text(json.dumps(n50, separators=(",", ":")) + "\n")
    infer_started = time.perf_counter()
    direct, unseen, predictions, sizes = {}, {}, {}, {}
    for u in users:
        direct[u], unseen[u] = score_user(n50.get(u, {}), neighbours, candidates)
        assert len(direct[u]) == len(set(direct[u])) and set(direct[u]) <= candidates
        assert unseen[u] == [it for it in direct[u] if it not in n50.get(u, {})]
        predictions[u], sizes[u] = complete(direct[u], anchor.fallback, candidates)
    inference_seconds = time.perf_counter() - infer_started
    (private / "direct_rankings.json").write_text(
        json.dumps(direct, separators=(",", ":")) + "\n"
    )
    (private / "unseen_rankings.json").write_text(
        json.dumps(unseen, separators=(",", ":")) + "\n"
    )
    (private / "standalone_top5.json").write_text(
        json.dumps(predictions, separators=(",", ":")) + "\n"
    )
    ap = {u: average_precision_at_k(truth[u], predictions[u]) for u in users}
    base_ap = {u: average_precision_at_k(truth[u], baseline[u]) for u in users}

    def group_summary(group):
        delta = [ap[u] - base_ap[u] for u in group]
        relevant = {u: truth[u] for u in group}
        return {
            "users": len(group),
            "v5_map_at_5": math.fsum(base_ap[u] for u in group) / len(group),
            "item_item_map_at_5": math.fsum(ap[u] for u in group) / len(group),
            "delta_from_v5": math.fsum(delta) / len(group),
            "users_improved": sum(d > 0 for d in delta),
            "users_worsened": sum(d < 0 for d in delta),
            "users_unchanged": sum(d == 0 for d in delta),
            "retrieval": retrieval_metrics(relevant, n50, direct, unseen),
            "direct_supported_candidates": distribution(
                [len(direct[u]) for u in group]
            ),
            "unseen_supported_candidates": distribution(
                [len(unseen[u]) for u in group]
            ),
            "fallback": {
                "complete_users": sum(sizes[u] == 0 for u in group),
                "partial_users": sum(0 < sizes[u] < 5 for u in group),
                "completion_slots": sum(5 - sizes[u] for u in group),
            },
        }

    summary = group_summary(users)
    expected_score = 0.33471117117117116 if name == "main" else 0.3313959105106414
    assert abs(summary["v5_map_at_5"] - expected_score) < 1e-12
    summary["history_slices"] = {
        sl: group_summary([u for u in users if history_slices[u] == sl])
        for sl in ["0", "1–5", "6–20", "21+"]
    }
    summary.update(
        {
            "split": name,
            "candidates": len(candidates),
            "fit_window": [START, fit_end],
            "validation_window": [fit_end, END],
            "model": model_stats,
            "items_in_pool_with_n50_support": len(candidates & support.keys()),
            "items_in_pool_scored_for_any_cohort_user": len(
                {it for order in direct.values() for it in order}
            ),
            "items_in_pool_unseen_scored_for_any_cohort_user": len(
                {it for order in unseen.values() for it in order}
            ),
            "count_extraction_seconds": extraction_seconds,
            "fit_seconds": fit_seconds,
            "inference_seconds": inference_seconds,
            "evaluation_seconds_including_io": time.perf_counter() - started,
            "peak_process_rss_after_fit_bytes": fit_rss,
            "frozen_anchor_sha256": anchor_digest,
            "truth_file_sha256": truth_hash,
            "cache_manifest": manifest,
            "environment": _environment(),
            "dependencies": versions(),
            "uncertainty": "Descriptive results conditional on reused overlapping cohorts; not an independent test. No tuning or fusion performed.",
        }
    )
    assert sha256_file(truth_path) == truth_hash and digest() == anchor_digest
    assert (
        summary["retrieval"]["20"]["union_with_personal_history"]["base_hits"]
        == json.loads(
            Path(
                f"results/viewing_strength_20261030_v6/{name}/retrieval_diagnostics.json"
            ).read_text()
        )["micro_relevant_covered"]
    )
    (out / "comparison.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(
        json.dumps(
            {
                "split": name,
                "v5_map": summary["v5_map_at_5"],
                "item_item_map": summary["item_item_map_at_5"],
                "delta": summary["delta_from_v5"],
                "unseen_recall50": summary["retrieval"]["50"][
                    "unseen_ranking_absent_targets"
                ],
                "extra_covered50": summary["retrieval"]["50"][
                    "union_with_personal_history"
                ]["additional_relevant_items"],
                "fit_seconds": fit_seconds,
                "inference_seconds": inference_seconds,
            }
        ),
        flush=True,
    )
    return summary


def run(args):
    started = time.perf_counter()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    frozen = json.loads((args.output_dir / "frozen_experiment.json").read_text())
    assert sha256_file(DEFINITION) == frozen["definition_sha256"]
    previous = {
        str(p): sha256_file(p) for p in sorted(Path("submissions").glob("*.csv"))
    }
    assert sha256_file(BASELINE) == BASELINE_HASH
    manifest = verify_interaction_cache(ORIGINAL / "train")
    input_hashes = {
        name: sha256_file(args.data_dir / name) for name in manifest["config"]["inputs"]
    }
    assert input_hashes == manifest["config"]["inputs"]
    paths = [
        args.data_dir / "export_arh_11-20-final.csv",
        args.data_dir / "export_arh_21-30-final.csv",
    ]
    for name, cache, truth, cutoff in [
        ("main", ORIGINAL / "train", ORIGINAL / "truth.json", MAIN_CUTOFF),
        (
            "auxiliary",
            Path("artifacts/opportunity_week_20261030_v4/auxiliary/train"),
            Path("artifacts/opportunity_week_20261030_v4/auxiliary/truth.json"),
            AUX_CUTOFF,
        ),
    ]:
        available, _ = prediction_airing_counts(paths, cutoff, END)
        evaluate_split(
            name,
            cache,
            truth,
            cutoff,
            set(available),
            args.output_dir / name,
            args.private_dir / name,
        )
    assert set(previous) == {str(p) for p in Path("submissions").glob("*.csv")}
    assert all(sha256_file(Path(p)) == h for p, h in previous.items())
    assert sha256_file(DEFINITION) == frozen["definition_sha256"]
    (args.output_dir / "run_evidence.json").write_text(
        json.dumps(
            {
                "recorded_at_utc": datetime.now(timezone.utc).isoformat(),
                "protocol_sha256": frozen["definition_sha256"],
                "preserved_csv_sha256": previous,
                "input_sha256": input_hashes,
                "elapsed_seconds": time.perf_counter() - started,
                "environment": _environment(),
                "best_submitted_baseline": {
                    "file": str(BASELINE),
                    "sha256": BASELINE_HASH,
                    "private": 0.40210,
                    "public": 0.41789,
                    "source": "User-reported screenshot scores in request; no independent Kaggle lookup.",
                    "submission_id": None,
                    "submission_timestamp": None,
                },
                "submission_action": "None. No CSV, fusion, combined refit or Kaggle workflow.",
                "student_verification": "pending; native transcript unmodified",
            },
            indent=2,
        )
        + "\n"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument(
        "--output-dir", type=Path, default=Path("results/item_item_20261030_v7")
    )
    parser.add_argument(
        "--private-dir", type=Path, default=Path("artifacts/item_item_20261030_v7")
    )
    run(parser.parse_args())
