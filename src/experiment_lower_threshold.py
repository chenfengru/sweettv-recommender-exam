"""Two lower personal thresholds against N50; E2 and retrieval disabled."""

import argparse
import csv
import hashlib
import json
import math
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
from .audit_data import _environment
from .compare_models import history_slice, versions
from .csv_io import sha256_file
from .experiment_personal_ties import list_difference
from .experiment_viewing_strength import (
    START,
    MAIN_CUTOFF,
    AUX_CUTOFF,
    END,
    FUTURE_END,
    ORIGINAL,
    BASELINE,
    BASELINE_HASH,
    prediction_airing_counts,
)
from .first_submission import verify_interaction_cache
from .interactions import csv_rows, extract_interactions
from .lower_threshold import lower_counts
from .metrics import average_precision_at_k
from .models import Ranker
from .personal_threshold import personal_counts, predict
from .personal_ties import global_qualified_statistics
from .validate_submission import validate_submission

DEFINITION = Path("docs/lower_threshold_protocol.md")
THRESHOLDS = [0.3, 0.4]
V9 = Path("submissions/candidate_personal_fifth_e2_20261030_v9.csv")
V9_HASH = "f1378b0d6fed62793e14ebb4c1b64cf8b2163485485c15c861aae7e67e556375"


def coverage(counts, truth, candidates):
    hits = {u: len(set(target) & set(counts.get(u, {}))) for u, target in truth.items()}
    total = sum(len(set(t)) for t in truth.values())
    sizes = [len(set(counts.get(u, {})) & candidates) for u in truth]
    return {
        "users": len(truth),
        "relevant_pairs_covered": sum(hits.values()),
        "relevant_pairs_total": total,
        "micro": sum(hits.values()) / total,
        "macro": math.fsum(hits[u] / len(set(t)) for u, t in truth.items())
        / len(truth),
        "available_personal_candidate_pairs": sum(sizes),
        "users_without_usable_history": sum(n == 0 for n in sizes),
        "mean_available_history_size": math.fsum(sizes) / len(sizes),
        "all_training_user_item_pairs": sum(map(len, counts.values())),
        "all_training_qualified_user_airings": sum(
            sum(c.values()) for c in counts.values()
        ),
        "available_training_user_item_pairs": sum(
            it in candidates for c in counts.values() for it in c
        ),
    }


def evaluate(
    name, cache, truth_path, fit_end, candidates, template_users, out, private
):
    began = time.perf_counter()
    out.mkdir(parents=True, exist_ok=True)
    private.mkdir(parents=True, exist_ok=True)
    manifest = verify_interaction_cache(cache)
    truth_hash = sha256_file(truth_path)
    truth = json.loads(truth_path.read_text())
    users = sorted(truth)
    assert (len(users), len(candidates)) == (
        (4625, 6384) if name == "main" else (4589, 5742)
    )
    records = json.loads((cache / "interactions.json").read_text())
    anchor = Ranker(records, candidates, {}, "personal")
    viewers, total = global_qualified_statistics(records)
    slices = {u: history_slice(len(anchor.qualified.get(u, {}))) for u in users}
    anchors = {
        "truth": truth,
        "viewers": dict(viewers),
        "total": dict(total),
        "fallback": anchor.fallback,
        "slices": slices,
        "candidates": sorted(candidates),
    }
    digest = lambda: hashlib.sha256(
        json.dumps(anchors, sort_keys=True).encode()
    ).hexdigest()
    anchor_hash = digest()
    assert (
        anchor_hash
        == json.loads(
            Path(f"results/item_item_20261030_v7/{name}/comparison.json").read_text()
        )["frozen_anchor_sha256"]
    )
    extraction = time.perf_counter()
    counts, noise = lower_counts(
        cache / "segments.sqlite", START, fit_end, set(users), candidates
    )
    extraction_seconds = time.perf_counter() - extraction
    old_n50 = Path(f"artifacts/item_item_20261030_v7/{name}/n50.json")
    hashes = json.loads(
        Path("results/item_item_20261030_v7/preservation_checks.json").read_text()
    )["private_model_sha256"]
    assert sha256_file(old_n50) == hashes[str(old_n50)]
    assert counts[0.5] == json.loads(old_n50.read_text())
    (out / "new_airing_durations.json").write_text(json.dumps(noise, indent=2) + "\n")
    prediction_users = sorted(set(users) | set(template_users))
    predictions = {}
    ap = {}
    results = {}
    for threshold in [0.5, 0.3, 0.4]:
        ranking_began = time.perf_counter()
        pred, sizes = predict(
            counts[threshold],
            candidates,
            viewers,
            total,
            anchor.fallback,
            prediction_users,
        )
        values = {u: average_precision_at_k(truth[u], pred[u]) for u in users}

        def group_summary(group):
            actual = {u: truth[u] for u in group}
            r = {
                "users": len(group),
                "map_at_5": math.fsum(values[u] for u in group) / len(group),
                "personal_history_coverage": coverage(
                    counts[threshold], actual, candidates
                ),
                "fallback": {
                    "complete_users": sum(sizes[u] == 0 for u in group),
                    "partial_users": sum(0 < sizes[u] < 5 for u in group),
                    "completion_slots": sum(5 - sizes[u] for u in group),
                },
            }
            if threshold != 0.5:
                baseline = predictions[0.5]
                base_counts = counts[0.5]
                delta = [values[u] - ap[0.5][u] for u in group]
                new_relevant = sum(
                    len(
                        (
                            set(counts[threshold].get(u, {}))
                            - set(base_counts.get(u, {}))
                        )
                        & set(truth[u])
                    )
                    for u in group
                )
                gained = {
                    u: (set(pred[u]) - set(baseline[u])) & set(truth[u]) for u in group
                }
                lost = {
                    u: (set(baseline[u]) - set(pred[u])) & set(truth[u]) for u in group
                }
                r.update(
                    {
                        "delta_from_050": math.fsum(delta) / len(group),
                        "users_improved": sum(v > 0 for v in delta),
                        "users_worsened": sum(v < 0 for v in delta),
                        "users_unchanged": sum(v == 0 for v in delta),
                        "prediction_changes": list_difference(
                            {u: pred[u] for u in group}, {u: baseline[u] for u in group}
                        ),
                        "newly_covered_relevant_pairs": new_relevant,
                        "users_gaining_usable_history": sum(
                            not (set(base_counts.get(u, {})) & candidates)
                            and bool(set(counts[threshold].get(u, {})) & candidates)
                            for u in group
                        ),
                        "top5_relevant_hit_gains": sum(map(len, gained.values())),
                        "top5_relevant_hit_losses": sum(map(len, lost.values())),
                        "net_top5_relevant_hit_change": sum(map(len, gained.values()))
                        - sum(map(len, lost.values())),
                        "gained_top5_relevant_from_new_personal_history": sum(
                            len(
                                gained[u]
                                & (
                                    set(counts[threshold].get(u, {}))
                                    - set(base_counts.get(u, {}))
                                )
                            )
                            for u in group
                        ),
                    }
                )
            return r

        result = group_summary(users)
        result["history_slices"] = {
            sl: group_summary([u for u in users if slices[u] == sl])
            for sl in ["0", "1–5", "6–20", "21+"]
        }
        result["ranking_and_diagnostics_seconds"] = time.perf_counter() - ranking_began
        results[str(threshold)] = result
        predictions[threshold] = pred
        ap[threshold] = values
        (private / f"t{threshold}_predictions.json").write_text(
            json.dumps(pred, separators=(",", ":")) + "\n"
        )
    reference = json.loads(
        Path(
            f"artifacts/personal_threshold_20261030_v5/{name}/T50_predictions.json"
        ).read_text()
    )
    assert predictions[0.5] == reference
    v9score = json.loads(
        Path(
            f"results/fifth_replacement_20261030_v9/{name}/comparison.json"
        ).read_text()
    )["results"]["E2"]["map_at_5"]
    rng = np.random.default_rng(42)
    samples = {t: [] for t in THRESHOLDS}
    diffs = {t: np.array([ap[t][u] - ap[0.5][u] for u in users]) for t in THRESHOLDS}
    for _ in range(2000):
        indices = rng.integers(len(users), size=len(users))
        for t in THRESHOLDS:
            samples[t].append(float(diffs[t][indices].mean()))
    for t in THRESHOLDS:
        results[str(t)]["paired_bootstrap_95pct"] = np.quantile(
            samples[t], [0.025, 0.975]
        ).tolist()
        results[str(t)]["difference_from_v9_context_only"] = (
            results[str(t)]["map_at_5"] - v9score
        )
    summary = {
        "split": name,
        "e2_enabled": False,
        "results": results,
        "v9_e2_existing_local_score_context_only": v9score,
        "fit_window": [START, fit_end],
        "validation_window": [fit_end, END],
        "candidates": len(candidates),
        "anchor_sha256": anchor_hash,
        "truth_sha256": truth_hash,
        "n50_reference_sha256": hashes[str(old_n50)],
        "cache_manifest": manifest,
        "count_extraction_seconds": extraction_seconds,
        "elapsed_seconds": time.perf_counter() - began,
        "bootstrap": {
            "resamples": 2000,
            "seed": 42,
            "scope": "Conditional on reused overlapping cohorts; excludes selection uncertainty.",
        },
        "environment": _environment(),
        "dependencies": versions(),
    }
    assert digest() == anchor_hash and sha256_file(truth_path) == truth_hash
    (out / "comparison.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(
        json.dumps(
            {
                "split": name,
                "scores": {t: r["map_at_5"] for t, r in results.items()},
                "deltas": {
                    str(t): results[str(t)]["delta_from_050"] for t in THRESHOLDS
                },
                "v9_context": v9score,
            }
        ),
        flush=True,
    )
    return summary


def make_candidate(args, threshold, inputs):
    began = time.perf_counter()
    cache = Path("artifacts/first_submission_20261029/combined_fit")
    paths = [
        args.data_dir / "export_arh_11-20-final.csv",
        args.data_dir / "export_arh_21-30-final.csv",
    ]
    records, manifest = extract_interactions(
        args.data_dir / "dataset11-30.csv",
        paths,
        START,
        END,
        cache,
        input_hashes=inputs,
    )
    counts = personal_counts(
        cache / "segments.sqlite", START, END, thresholds=(threshold, 0.5, 0.8)
    )
    assert {(u, it): n for u, c in counts[0.8].items() for it, n in c.items()} == {
        (u, it): n for u, it, _, n in records if n
    }
    available, _ = prediction_airing_counts(
        [
            args.data_dir / "export_arh_21-30-final.csv",
            args.data_dir / "export_arh_31-42-final.csv",
        ],
        END,
        FUTURE_END,
    )
    candidates = set(available)
    assert len(candidates) == 6649
    anchor = Ranker(records, candidates, {}, "personal")
    viewers, total = global_qualified_statistics(records)
    users = [r["user_id"] for r in csv_rows(args.data_dir / "submission.csv")]
    baseline = {r["user_id"]: r["tv_show_id"].split() for r in csv_rows(BASELINE)}
    baseline9 = {r["user_id"]: r["tv_show_id"].split() for r in csv_rows(V9)}
    reference, _ = predict(
        counts[0.5], candidates, viewers, total, anchor.fallback, users
    )
    assert reference == baseline
    predictions, _ = predict(
        counts[threshold], candidates, viewers, total, anchor.fallback, users
    )
    path = (
        Path("submissions")
        / f"candidate_personal_threshold_{int(threshold*100):03d}_noe2_20261030_v10.csv"
    )
    assert not path.exists()
    with (args.data_dir / "submission.csv").open(newline="") as f:
        header = next(csv.reader(f))
    with path.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows((u, " ".join(predictions[u])) for u in users)
    validation = validate_submission(
        args.data_dir / "submission.csv",
        path,
        candidates,
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
            check=True,
            stdout=output,
        )
    artifact = {
        "filename": path.name,
        "absolute_path": str(path.resolve()),
        "sha256": sha256_file(path),
        "validation": validation,
        "configuration": {
            "personal_threshold": threshold,
            "e2_enabled": False,
            "collaborative_retrieval": False,
            "global_statistics_threshold": 0.8,
        },
        "differences_from_submitted_v5": list_difference(predictions, baseline),
        "differences_from_submitted_v9": list_difference(predictions, baseline9),
        "combined_fit_manifest": manifest,
        "elapsed_seconds": time.perf_counter() - began,
        "environment": _environment(),
        "submission_description": f"Personal-frequency threshold-only model with longest merged observed viewing block/full original airing duration >= {threshold:.2f}. Count canonical pre-cutoff user-airings, rank by personal count then unchanged >=80% global viewer/airing popularity and raw string ID; shared >=80% fallback. Combined weeks11–30 fitting, weeks31–42 carryover-aware candidates. E2 and collaborative retrieval disabled. Validated for manual review; no Kaggle result.",
    }
    (args.output_dir / "candidate_artifact.json").write_text(
        json.dumps(artifact, indent=2) + "\n"
    )
    (args.output_dir / "submission_description.txt").write_text(
        artifact["submission_description"] + "\n"
    )
    print(
        json.dumps({"candidate": str(path.resolve()), "sha256": artifact["sha256"]}),
        flush=True,
    )


def run(args):
    began = time.perf_counter()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    frozen = json.loads((args.output_dir / "frozen_experiment.json").read_text())
    assert sha256_file(DEFINITION) == frozen["definition_sha256"]
    previous = {
        str(p): sha256_file(p) for p in sorted(Path("submissions").glob("*.csv"))
    }
    assert sha256_file(BASELINE) == BASELINE_HASH and sha256_file(V9) == V9_HASH
    inputs = verify_interaction_cache(ORIGINAL / "train")["config"]["inputs"]
    assert {name: sha256_file(args.data_dir / name) for name in inputs} == inputs
    template_users = [r["user_id"] for r in csv_rows(args.data_dir / "submission.csv")]
    summaries = {}
    for name, cache, truth, cutoff in [
        ("main", ORIGINAL / "train", ORIGINAL / "truth.json", MAIN_CUTOFF),
        (
            "auxiliary",
            Path("artifacts/opportunity_week_20261030_v4/auxiliary/train"),
            Path("artifacts/opportunity_week_20261030_v4/auxiliary/truth.json"),
            AUX_CUTOFF,
        ),
    ]:
        available, _ = prediction_airing_counts(
            [
                args.data_dir / "export_arh_11-20-final.csv",
                args.data_dir / "export_arh_21-30-final.csv",
            ],
            cutoff,
            END,
        )
        summaries[name] = evaluate(
            name,
            cache,
            truth,
            cutoff,
            set(available),
            template_users,
            args.output_dir / name,
            args.private_dir / name,
        )
    eligible = [
        t
        for t in THRESHOLDS
        if all(summaries[s]["results"][str(t)]["delta_from_050"] > 0 for s in summaries)
    ]
    selected = (
        max(
            eligible,
            key=lambda t: (
                min(
                    summaries[s]["results"][str(t)]["delta_from_050"] for s in summaries
                ),
                t == 0.4,
            ),
        )
        if eligible
        else None
    )
    evidence = {
        "selected_threshold": selected,
        "eligible_thresholds": eligible,
        "selection_rule": frozen["selection"],
        "e2_enabled": False,
        "selected_exceeds_v9_on_both_splits": (
            all(
                summaries[s]["results"][str(selected)]["map_at_5"]
                > summaries[s]["v9_e2_existing_local_score_context_only"]
                for s in summaries
            )
            if selected is not None
            else None
        ),
        "frozen_protocol_sha256": frozen["definition_sha256"],
        "preserved_csv_sha256": previous,
        "input_sha256": inputs,
        "elapsed_comparison_seconds": time.perf_counter() - began,
        "environment": _environment(),
        "best_confirmed_submitted_v9": {
            "file": str(V9),
            "sha256": V9_HASH,
            "private": 0.40261,
            "public": 0.41871,
            "source": "User-screenshot-reported scores in current request; no independent Kaggle lookup.",
            "submission_id": None,
            "submission_timestamp": None,
            "recorded_at_utc": datetime.now(timezone.utc).isoformat(),
        },
    }
    (args.output_dir / "selection.json").write_text(
        json.dumps(evidence, indent=2) + "\n"
    )
    print(
        json.dumps(
            {
                "selected_threshold": selected,
                "eligible": eligible,
                "exceeds_v9_both": evidence["selected_exceeds_v9_on_both_splits"],
            }
        ),
        flush=True,
    )
    if selected is not None:
        make_candidate(args, selected, inputs)
    else:
        (args.output_dir / "candidate_decision.json").write_text(
            json.dumps(
                {
                    "decision": "Retain submitted v9; neither threshold improves both splits vs0.50. No final fit or CSV generated."
                },
                indent=2,
            )
            + "\n"
        )
    assert all(sha256_file(Path(p)) == h for p, h in previous.items())
    assert sha256_file(DEFINITION) == frozen["definition_sha256"]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument(
        "--output-dir", type=Path, default=Path("results/lower_threshold_20261030_v10")
    )
    parser.add_argument(
        "--private-dir",
        type=Path,
        default=Path("artifacts/lower_threshold_20261030_v10"),
    )
    run(parser.parse_args())
