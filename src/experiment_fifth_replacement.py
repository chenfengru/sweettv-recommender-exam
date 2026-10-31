"""Controlled fifth-position replacement; manual review only."""

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
from .improvement_helpers import complete
from .interactions import extract_interactions, csv_rows
from .fifth_replacement import fifth_replacement, RULES
from .item_item import fit_item_item, score_user
from .metrics import average_precision_at_k
from .models import Ranker
from .personal_threshold import personal_counts
from .personal_ties import global_qualified_statistics, personal_order
from .validate_submission import validate_submission

DEFINITION = Path("docs/fifth_replacement_protocol.md")


def predict_all(baseline, counts, unseen, candidates, rule, users):
    predictions, flags = {}, {}
    for u in users:
        predictions[u], flags[u] = fifth_replacement(
            baseline[u], counts.get(u, {}), unseen[u], candidates, rule
        )
    return predictions, flags


def evaluate(name, cache, truth_path, candidates, out, private):
    started = time.perf_counter()
    out.mkdir(parents=True, exist_ok=True)
    private.mkdir(parents=True, exist_ok=True)
    manifest = verify_interaction_cache(cache)
    truth_hash = sha256_file(truth_path)
    truth = json.loads(truth_path.read_text())
    users = sorted(truth)
    expected = (4625, 6384) if name == "main" else (4589, 5742)
    assert (len(users), len(candidates)) == expected
    records = json.loads((cache / "interactions.json").read_text())
    anchor = Ranker(records, candidates, {}, "personal")
    viewers, total = global_qualified_statistics(records)
    cached = Path(f"artifacts/item_item_20261030_v7/{name}")
    provenance = json.loads(
        Path("results/item_item_20261030_v7/preservation_checks.json").read_text()
    )["private_model_sha256"]
    hashes = {
        str(cached / f): sha256_file(cached / f)
        for f in ["n50.json", "unseen_rankings.json"]
    }
    assert all(provenance[p] == h for p, h in hashes.items())
    n50 = json.loads((cached / "n50.json").read_text())
    alternative = json.loads((cached / "unseen_rankings.json").read_text())
    personal = {
        u: personal_order(
            n50.get(u, {}),
            candidates,
            variant="popularity",
            viewers=viewers,
            total=total,
        )
        for u in users
    }
    assert set(alternative) == set(users)
    assert all(not (set(row) & set(n50.get(u, {}))) for u, row in alternative.items())
    assert all(
        len(r) == len(set(r)) and set(r) <= candidates for r in alternative.values()
    )
    baseline = {u: complete(personal[u], anchor.fallback, candidates)[0] for u in users}
    reference = json.loads(
        Path(
            f"artifacts/personal_threshold_20261030_v5/{name}/T50_predictions.json"
        ).read_text()
    )
    assert baseline == {u: reference[u] for u in users}
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
    base_ap = {u: average_precision_at_k(truth[u], baseline[u]) for u in users}
    results = {"v5": {"map_at_5": math.fsum(base_ap.values()) / len(users)}}
    differences = {}
    for rule in RULES:
        began = time.perf_counter()
        pred, flags = predict_all(baseline, n50, alternative, candidates, rule, users)
        values = {u: average_precision_at_k(truth[u], pred[u]) for u in users}

        def summarize(group):
            replaced = [u for u in group if flags[u]["replaced"]]
            outcomes = lambda subset: {
                "users": len(subset),
                "improved": sum(values[u] > base_ap[u] for u in subset),
                "worsened": sum(values[u] < base_ap[u] for u in subset),
                "unchanged": sum(values[u] == base_ap[u] for u in subset),
            }
            inserted = sum(pred[u][4] in truth[u] for u in replaced)
            removed = sum(baseline[u][4] in truth[u] for u in replaced)
            both = sum(
                pred[u][4] in truth[u] and baseline[u][4] in truth[u] for u in replaced
            )
            neither = sum(
                pred[u][4] not in truth[u] and baseline[u][4] not in truth[u]
                for u in replaced
            )
            assert outcomes(replaced)["improved"] == inserted - both
            assert outcomes(replaced)["worsened"] == removed - both
            assert outcomes(replaced)["unchanged"] == both + neither
            return {
                "users": len(group),
                "map_at_5": math.fsum(values[u] for u in group) / len(group),
                "v5_map_at_5": math.fsum(base_ap[u] for u in group) / len(group),
                "delta_from_v5": math.fsum(values[u] - base_ap[u] for u in group)
                / len(group),
                "eligible_users": sum(flags[u]["eligible"] for u in group),
                "available_replacement_users_whole_cohort": sum(
                    flags[u]["has_available_replacement"] for u in group
                ),
                "eligible_with_available_replacement": sum(
                    flags[u]["eligible"] and flags[u]["has_available_replacement"]
                    for u in group
                ),
                "actual_replacements": len(replaced),
                "inserted_relevant": inserted,
                "removed_relevant": removed,
                "both_relevant": both,
                "neither_relevant": neither,
                "inserted_only_relevant": inserted - both,
                "removed_only_relevant": removed - both,
                "net_relevant_hit_change": inserted - removed,
                "whole_cohort_ap_outcomes": outcomes(group),
                "replaced_users_ap_outcomes": outcomes(replaced),
                "prediction_changes": list_difference(
                    {u: pred[u] for u in group}, {u: baseline[u] for u in group}
                ),
                "invariants": {
                    "first_four_identical": all(
                        pred[u][:4] == baseline[u][:4] for u in group
                    ),
                    "all_actual_replacements_unseen_available_distinct_and_outside_original_top5": all(
                        pred[u][4] not in baseline[u]
                        and pred[u][4] in candidates
                        and n50.get(u, {}).get(pred[u][4], 0) == 0
                        and len(set(pred[u])) == 5
                        for u in replaced
                    ),
                },
            }

        result = summarize(users)
        result["history_slices"] = {
            sl: summarize([u for u in users if slices[u] == sl])
            for sl in ["0", "1–5", "6–20", "21+"]
        }
        result["evaluation_seconds"] = time.perf_counter() - began
        assert (
            result["actual_replacements"]
            == result["prediction_changes"]["users_changed"]
            == result["prediction_changes"]["rank_position_slots_changed"]
        )
        results[rule] = result
        differences[rule] = np.array([values[u] - base_ap[u] for u in users])
        (private / f"{rule}_predictions.json").write_text(
            json.dumps(pred, separators=(",", ":")) + "\n"
        )
    rng = np.random.default_rng(42)
    samples = {w: [] for w in RULES}
    for _ in range(2000):
        indices = rng.integers(len(users), size=len(users))
        for w in RULES:
            samples[w].append(float(differences[w][indices].mean()))
    for w in RULES:
        results[w]["paired_bootstrap_95pct"] = np.quantile(
            samples[w], [0.025, 0.975]
        ).tolist()
    summary = {
        "split": name,
        "evaluation_users": len(users),
        "candidates": len(candidates),
        "results": results,
        "anchor_sha256": anchor_hash,
        "truth_sha256": truth_hash,
        "cached_input_sha256": hashes,
        "source_cache_manifest": manifest,
        "elapsed_seconds": time.perf_counter() - started,
        "bootstrap": {
            "resamples": 2000,
            "seed": 42,
            "scope": "Conditional on reused overlapping cohorts; excludes configuration-selection uncertainty.",
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
                "scores": {k: v["map_at_5"] for k, v in results.items()},
                "deltas": {w: results[w]["delta_from_v5"] for w in RULES},
            }
        ),
        flush=True,
    )
    return summary


def make_candidate(args, rule, inputs):
    began = time.perf_counter()
    paths = [
        args.data_dir / "export_arh_11-20-final.csv",
        args.data_dir / "export_arh_21-30-final.csv",
    ]
    cache = Path("artifacts/first_submission_20261029/combined_fit")
    records, manifest = extract_interactions(
        args.data_dir / "dataset11-30.csv",
        paths,
        START,
        END,
        cache,
        input_hashes=inputs,
    )
    counts = personal_counts(
        cache / "segments.sqlite", START, END, thresholds=(0.5, 0.8)
    )
    assert {(u, it): n for u, c in counts[0.8].items() for it, n in c.items()} == {
        (u, it): n for u, it, _, n in records if n
    }
    neighbours, support, stats = fit_item_item(counts[0.5])
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
    personal = {
        u: personal_order(
            counts[0.5].get(u, {}),
            candidates,
            variant="popularity",
            viewers=viewers,
            total=total,
        )
        for u in users
    }
    alternative = {
        u: score_user(counts[0.5].get(u, {}), neighbours, candidates)[1] for u in users
    }
    baseline = {r["user_id"]: r["tv_show_id"].split(" ") for r in csv_rows(BASELINE)}
    assert {
        u: complete(personal[u], anchor.fallback, candidates)[0] for u in users
    } == baseline
    predictions, flags = predict_all(
        baseline, counts[0.5], alternative, candidates, rule, users
    )
    path = (
        Path("submissions") / f"candidate_personal_fifth_{rule.lower()}_20261030_v9.csv"
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
        "differences_from_submitted_v5": list_difference(predictions, baseline),
        "configuration": {
            "rule": rule,
            "unseen_direct_limit": 50,
            "first_four_preserved": all(
                predictions[u][:4] == baseline[u][:4] for u in users
            ),
            "actual_replacements": sum(flags[u]["replaced"] for u in users),
            "item_item": stats,
        },
        "combined_fit_manifest": manifest,
        "elapsed_seconds": time.perf_counter() - began,
        "environment": _environment(),
        "submission_description": f"V5 N50 personal frequency with controlled fifth-position unseen replacement, rule {rule}. Preserve positions1–4; highest eligible v7 unseen direct top50 candidate outside original top5. Fit weeks11–30 with unchanged canonical cleaning and fixed item-item model; predict31–42 including carryovers. Original >=80% global keys/fallback. Validated for manual review; no Kaggle result.",
    }
    (args.output_dir / "candidate_artifact.json").write_text(
        json.dumps(artifact, indent=2) + "\n"
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
    assert sha256_file(BASELINE) == BASELINE_HASH
    manifest = verify_interaction_cache(ORIGINAL / "train")
    inputs = {p: sha256_file(args.data_dir / p) for p in manifest["config"]["inputs"]}
    assert inputs == manifest["config"]["inputs"]
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
            set(available),
            args.output_dir / name,
            args.private_dir / name,
        )
    eligible = [
        rule
        for rule in RULES
        if all(
            summaries[split]["results"][rule]["delta_from_v5"] > 0
            for split in summaries
        )
    ]
    selected = (
        max(
            eligible,
            key=lambda rule: (
                min(
                    summaries[split]["results"][rule]["delta_from_v5"]
                    for split in summaries
                ),
                -summaries["main"]["results"][rule]["actual_replacements"],
                -RULES.index(rule),
            ),
        )
        if eligible
        else None
    )
    evidence = {
        "selected_rule": selected,
        "eligible_rules": eligible,
        "selection_rule": frozen["selection"],
        "frozen_protocol_sha256": frozen["definition_sha256"],
        "preserved_csv_sha256": previous,
        "input_sha256": inputs,
        "elapsed_comparison_seconds": time.perf_counter() - began,
        "environment": _environment(),
        "best_submitted_baseline": {
            "file": str(BASELINE),
            "sha256": BASELINE_HASH,
            "private": 0.40210,
            "public": 0.41789,
            "source": "User-reported screenshot values; no independent Kaggle lookup.",
            "submission_id": None,
            "submission_timestamp": None,
        },
    }
    (args.output_dir / "selection.json").write_text(
        json.dumps(evidence, indent=2) + "\n"
    )
    print(json.dumps({"selected_rule": selected, "eligible": eligible}), flush=True)
    if selected is not None:
        make_candidate(args, selected, inputs)
    else:
        (args.output_dir / "candidate_decision.json").write_text(
            json.dumps(
                {
                    "decision": "Retain submitted v5; no rule improves both splits. No final fit or CSV generated."
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
        "--output-dir", type=Path, default=Path("results/fifth_replacement_20261030_v9")
    )
    parser.add_argument(
        "--private-dir",
        type=Path,
        default=Path("artifacts/fifth_replacement_20261030_v9"),
    )
    run(parser.parse_args())
