"""Two frozen exploratory stages; cached split predictions, manual review only."""

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
from .adaptive_threshold import (
    h80_from_records,
    adaptation_eligible,
    select_counts,
    adaptive_predictions,
)
from .audit_data import _environment
from .compare_models import history_slice, versions
from .csv_io import sha256_file
from .experiment_personal_ties import list_difference
from .experiment_lower_threshold import (
    START,
    MAIN_CUTOFF,
    AUX_CUTOFF,
    END,
    FUTURE_END,
    ORIGINAL,
    BASELINE,
    BASELINE_HASH,
    V9,
    V9_HASH,
    prediction_airing_counts,
)
from .fifth_replacement import fifth_replacement
from .first_submission import verify_interaction_cache
from .interactions import extract_interactions, csv_rows
from .item_item import fit_item_item, score_user
from .metrics import average_precision_at_k
from .models import Ranker
from .personal_threshold import personal_counts, predict
from .personal_ties import global_qualified_statistics
from .improvement_helpers import complete

DEFINITION = Path("docs/adaptive_threshold_protocol.md")
SLICE_ORDER = ["0", "1–5", "6–20", "21+"]
CONFIGS = {"S30": 0.3, "S40": 0.4}


def fallback_sum(per_slice):
    return {
        k: sum(r[k] for r in per_slice.values())
        for k in ["complete_users", "partial_users", "completion_slots"]
    }


def compare(truth, pred, reference, slices, method_fallback, reference_fallback):
    users = sorted(truth)
    ap = {u: average_precision_at_k(truth[u], pred[u]) for u in users}
    base = {u: average_precision_at_k(truth[u], reference[u]) for u in users}

    def summarize(group):
        diff = [ap[u] - base[u] for u in group]
        gains = sum(
            len((set(pred[u]) - set(reference[u])) & set(truth[u])) for u in group
        )
        losses = sum(
            len((set(reference[u]) - set(pred[u])) & set(truth[u])) for u in group
        )
        return {
            "users": len(group),
            "map_at_5": math.fsum(ap[u] for u in group) / len(group),
            "reference_map_at_5": math.fsum(base[u] for u in group) / len(group),
            "delta": math.fsum(diff) / len(group),
            "users_improved": sum(v > 0 for v in diff),
            "users_worsened": sum(v < 0 for v in diff),
            "users_unchanged": sum(v == 0 for v in diff),
            "relevant_hit_gains": gains,
            "relevant_hit_losses": losses,
            "net_relevant_hits": gains - losses,
            "prediction_changes": list_difference(
                {u: pred[u] for u in group}, {u: reference[u] for u in group}
            ),
        }

    result = summarize(users)
    result["fallback"] = fallback_sum(method_fallback)
    result["reference_fallback"] = fallback_sum(reference_fallback)
    result["history_slices"] = {
        sl: summarize([u for u in users if slices[u] == sl]) for sl in SLICE_ORDER
    }
    for sl in SLICE_ORDER:
        result["history_slices"][sl]["fallback"] = method_fallback[sl]
        result["history_slices"][sl]["reference_fallback"] = reference_fallback[sl]
    differences = np.array([ap[u] - base[u] for u in users])
    rng = np.random.default_rng(42)
    samples = [
        float(differences[rng.integers(len(users), size=len(users))].mean())
        for _ in range(2000)
    ]
    result["paired_bootstrap_95pct"] = np.quantile(samples, [0.025, 0.975]).tolist()
    return result


def load_split(name, cache, truth_path, candidates, frozen):
    manifest = verify_interaction_cache(cache)
    truth_hash = sha256_file(truth_path)
    truth = json.loads(truth_path.read_text())
    users = sorted(truth)
    assert (len(users), len(candidates)) == (
        (4625, 6384) if name == "main" else (4589, 5742)
    )
    records = json.loads((cache / "interactions.json").read_text())
    h80 = h80_from_records(records)
    anchor = Ranker(records, candidates, {}, "personal")
    assert h80 == {u: len(c) for u, c in anchor.qualified.items()}
    viewers, total = global_qualified_statistics(records)
    slices = {u: history_slice(h80.get(u, 0)) for u in users}
    anchors = {
        "truth": truth,
        "viewers": dict(viewers),
        "total": dict(total),
        "fallback": anchor.fallback,
        "slices": slices,
        "candidates": sorted(candidates),
    }
    digest = hashlib.sha256(json.dumps(anchors, sort_keys=True).encode()).hexdigest()
    old = json.loads(
        Path(f"results/lower_threshold_20261030_v10/{name}/comparison.json").read_text()
    )
    assert digest == old["anchor_sha256"]

    def cached(path):
        assert sha256_file(path) == frozen["cached_input_sha256"][str(path)]
        raw = json.loads(path.read_text())
        return {u: raw[u] for u in users}

    n50path = Path(f"artifacts/item_item_20261030_v7/{name}/n50.json")
    assert sha256_file(n50path) == frozen["cached_input_sha256"][str(n50path)]
    n50 = json.loads(n50path.read_text())
    unseen = cached(
        Path(f"artifacts/item_item_20261030_v7/{name}/unseen_rankings.json")
    )
    thresholds = {
        t: cached(
            Path(f"artifacts/lower_threshold_20261030_v10/{name}/t{t}_predictions.json")
        )
        for t in [0.3, 0.4, 0.5]
    }
    v9 = cached(
        Path(f"artifacts/fifth_replacement_20261030_v9/{name}/E2_predictions.json")
    )
    reference, _ = predict(n50, candidates, viewers, total, anchor.fallback, users)
    assert thresholds[0.5] == reference
    for t, pred in thresholds.items():
        for sl in SLICE_ORDER:
            group = [u for u in users if slices[u] == sl]
            assert (
                abs(
                    math.fsum(average_precision_at_k(truth[u], pred[u]) for u in group)
                    / len(group)
                    - old["results"][str(t)]["history_slices"][sl]["map_at_5"]
                )
                < 1e-12
            )
    v9score = math.fsum(average_precision_at_k(truth[u], v9[u]) for u in users) / len(
        users
    )
    assert abs(v9score - old["v9_e2_existing_local_score_context_only"]) < 1e-12
    assert all(
        len(r) == len(set(r))
        and set(r) <= candidates
        and not (set(r) & set(n50.get(u, {})))
        for u, r in unseen.items()
    )
    for rankings in [*thresholds.values(), v9]:
        assert all(
            len(row) == len(set(row)) == 5 and set(row) <= candidates and "0" not in row
            for row in rankings.values()
        )
    fallback = {
        t: {
            sl: old["results"][str(t)]["history_slices"][sl]["fallback"]
            for sl in SLICE_ORDER
        }
        for t in [0.3, 0.4, 0.5]
    }
    return {
        "truth": truth,
        "users": users,
        "h80": h80,
        "slices": slices,
        "candidates": candidates,
        "n50": n50,
        "unseen": unseen,
        "thresholds": thresholds,
        "v9": v9,
        "fallback": fallback,
        "anchor_sha256": digest,
        "truth_sha256": truth_hash,
        "manifest": manifest,
        "truth_path": truth_path,
    }


def stage1(split, args, name):
    truth = split["truth"]
    base = split["thresholds"][0.5]
    slices = split["slices"]
    v9 = split["v9"]
    methods = {}
    predictions = {}
    fallbacks = {}
    eligible = {
        u for u in split["users"] if adaptation_eligible(split["h80"].get(u, 0))
    }
    assert eligible == {u for u in split["users"] if slices[u] == "1–5"}
    for config, t in CONFIGS.items():
        pred = adaptive_predictions(base, split["thresholds"][t], split["h80"])
        assert all(pred[u] == base[u] for u in split["users"] if u not in eligible)
        fallback = {
            sl: split["fallback"][t if sl == "1–5" else 0.5][sl] for sl in SLICE_ORDER
        }
        predictions[config] = pred
        fallbacks[config] = fallback
        methods[config] = {
            "threshold": t,
            "adaptation_eligible_users": len(eligible),
            "changed_adaptive_group_users": sum(pred[u] != base[u] for u in eligible),
            "outside_group_exact_v5": True,
            "e2_enabled": False,
            "comparisons": {
                "v5": compare(
                    truth, pred, base, slices, fallback, split["fallback"][0.5]
                ),
                "v9": compare(
                    truth, pred, v9, slices, fallback, split["fallback"][0.5]
                ),
            },
        }
        private = args.private_dir / name
        private.mkdir(parents=True, exist_ok=True)
        (private / f"{config}_predictions.json").write_text(
            json.dumps(pred, separators=(",", ":")) + "\n"
        )
    report = {
        "stage": 1,
        "split": name,
        "methods": methods,
        "anchor_sha256": split["anchor_sha256"],
        "truth_sha256": split["truth_sha256"],
        "fallback_provenance": "Exact composition of frozen v10 slice fallback counts: lower threshold only for original1–5 slice, N50 for other slices.",
        "environment": _environment(),
    }
    out = args.output_dir / "stage1" / name
    out.mkdir(parents=True, exist_ok=True)
    (out / "comparison.json").write_text(json.dumps(report, indent=2) + "\n")
    print(
        json.dumps(
            {
                "stage": 1,
                "split": name,
                "map": {
                    m: r["comparisons"]["v5"]["map_at_5"] for m, r in methods.items()
                },
                "deltas_v5": {
                    m: r["comparisons"]["v5"]["delta"] for m, r in methods.items()
                },
            }
        ),
        flush=True,
    )
    return methods, predictions, fallbacks


def stage2(split, args, name, parent_name, parent, fallback):
    truth = split["truth"]
    n50 = split["n50"]
    pool = split["candidates"]
    pred = {}
    flags = {}
    for u in split["users"]:
        pred[u], flags[u] = fifth_replacement(
            parent[u], n50.get(u, {}), split["unseen"][u], pool, "E2"
        )
    changed = [u for u in pred if flags[u]["replaced"]]
    for u in pred:
        assert pred[u][:4] == parent[u][:4]
        expected = (
            n50.get(u, {}).get(parent[u][3], 0)
            == n50.get(u, {}).get(parent[u][4], 0)
            == 1
        )
        assert flags[u]["eligible"] == expected
        if flags[u]["replaced"]:
            expected_item = next(
                it
                for it in split["unseen"][u][:50]
                if it in pool and it not in parent[u] and n50.get(u, {}).get(it, 0) == 0
            )
            assert pred[u][4] == expected_item
        if not adaptation_eligible(split["h80"].get(u, 0)):
            assert pred[u] == split["v9"][u]

    def replacements(group):
        active = [u for u in group if flags[u]["replaced"]]
        return {
            "users": len(group),
            "eligible_users": sum(flags[u]["eligible"] for u in group),
            "actual_replacements": len(active),
            "inserted_relevant": sum(pred[u][4] in truth[u] for u in active),
            "removed_relevant": sum(parent[u][4] in truth[u] for u in active),
        }

    comparisons = {
        "parent": compare(truth, pred, parent, split["slices"], fallback, fallback),
        "v5": compare(
            truth,
            pred,
            split["thresholds"][0.5],
            split["slices"],
            fallback,
            split["fallback"][0.5],
        ),
        "v9": compare(
            truth, pred, split["v9"], split["slices"], fallback, split["fallback"][0.5]
        ),
    }
    report = {
        "stage": 2,
        "split": name,
        "method": parent_name + "+E2",
        "parent": parent_name,
        "comparisons": comparisons,
        "replacement_counts": replacements(split["users"]),
        "replacement_slices": {
            sl: replacements([u for u in pred if split["slices"][u] == sl])
            for sl in SLICE_ORDER
        },
        "invariants": {
            "first_four_identical_to_adaptive_parent": True,
            "original_n50_eligibility": True,
            "original_n50_unseen_order_and_entire_parent_top5_exclusion": True,
            "outside_adaptive_group_exact_v9": True,
        },
        "fallback_provenance": "Inherited unchanged from parent: E2 requires positive N50 at fifth, hence cannot replace a parent global-fallback slot.",
        "environment": _environment(),
    }
    private = args.private_dir / name
    (private / f"{parent_name}_E2_predictions.json").write_text(
        json.dumps(pred, separators=(",", ":")) + "\n"
    )
    out = args.output_dir / "stage2" / name
    out.mkdir(parents=True, exist_ok=True)
    (out / "comparison.json").write_text(json.dumps(report, indent=2) + "\n")
    print(
        json.dumps(
            {
                "stage": 2,
                "split": name,
                "method": parent_name + "+E2",
                "deltas": {ref: r["delta"] for ref, r in comparisons.items()},
                "replacements": len(changed),
            }
        ),
        flush=True,
    )
    return report


def make_candidate(args, threshold, use_e2, inputs):
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
    h80 = h80_from_records(records)
    assert h80 == {u: len(c) for u, c in counts[0.8].items()}
    available, _ = prediction_airing_counts(
        [
            args.data_dir / "export_arh_21-30-final.csv",
            args.data_dir / "export_arh_31-42-final.csv",
        ],
        END,
        FUTURE_END,
    )
    pool = set(available)
    assert len(pool) == 6649
    anchor = Ranker(records, pool, {}, "personal")
    viewers, total = global_qualified_statistics(records)
    users = [r["user_id"] for r in csv_rows(args.data_dir / "submission.csv")]
    adapted = {u: select_counts(u, counts[0.5], counts[threshold], h80) for u in users}
    parent, parent_sizes = predict(
        adapted, pool, viewers, total, anchor.fallback, users
    )
    base5 = {r["user_id"]: r["tv_show_id"].split() for r in csv_rows(BASELINE)}
    base9 = {r["user_id"]: r["tv_show_id"].split() for r in csv_rows(V9)}
    base, _ = predict(counts[0.5], pool, viewers, total, anchor.fallback, users)
    assert base == base5
    assert all(
        parent[u] == base5[u] for u in users if not adaptation_eligible(h80.get(u, 0))
    )
    pred = parent
    stats = None
    flags = {}
    if use_e2:
        neighbours, support, stats = fit_item_item(counts[0.5])
        unseen = {
            u: score_user(counts[0.5].get(u, {}), neighbours, pool)[1] for u in users
        }
        assert {
            u: fifth_replacement(
                base5[u], counts[0.5].get(u, {}), unseen[u], pool, "E2"
            )[0]
            for u in users
        } == base9
        pred = {}
        for u in users:
            pred[u], flags[u] = fifth_replacement(
                parent[u], counts[0.5].get(u, {}), unseen[u], pool, "E2"
            )
        assert all(pred[u][:4] == parent[u][:4] for u in users)
    suffix = "e2" if use_e2 else "only"
    config = f"S{int(threshold*100)}" + ("+E2" if use_e2 else "")
    path = (
        Path("submissions")
        / f"candidate_adaptive_s{int(threshold*100)}_{suffix}_20261030_v11.csv"
    )
    assert not path.exists()
    with (args.data_dir / "submission.csv").open(newline="") as f:
        header = next(csv.reader(f))
    with path.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows((u, " ".join(pred[u])) for u in users)
    from .validate_submission import validate_submission

    validation = validate_submission(
        args.data_dir / "submission.csv",
        path,
        pool,
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
    description = (
        f"Exploratory {config}: personal threshold {threshold:.2f} only for users with1–5 distinct >=80%-qualified training programmes before availability filtering; N50 otherwise. Original >=80% global popularity ties/fallback. "
        + (
            "Then apply original E2 to completed adaptive list using N50=1 at positions4/5 and fixed N50 unseen-only top50 retrieval outside entire original adaptive top5; preserve adaptive first4. "
            if use_e2
            else "E2 disabled. "
        )
        + "Canonical combined weeks11–30 fit; predict weeks31–42 including carryovers. Grouping was motivated by reused validation slices; local gains are exploratory. Validated for manual review, no Kaggle result."
    )
    artifact = {
        "filename": path.name,
        "absolute_path": str(path.resolve()),
        "sha256": sha256_file(path),
        "validation": validation,
        "configuration": config,
        "personal_adaptive_threshold": threshold,
        "e2_enabled": use_e2,
        "final_template_adaptation_eligible_users": sum(
            adaptation_eligible(h80.get(u, 0)) for u in users
        ),
        "final_e2_eligible_users": sum(v["eligible"] for v in flags.values()),
        "final_e2_replacements": sum(v["replaced"] for v in flags.values()),
        "differences_from_submitted_v9": list_difference(pred, base9),
        "differences_from_submitted_v5": list_difference(pred, base5),
        "changes_from_adaptive_parent": list_difference(pred, parent),
        "item_item_model": stats,
        "combined_fit_manifest": manifest,
        "elapsed_seconds": time.perf_counter() - began,
        "environment": _environment(),
        "submission_description": description,
    }
    (args.output_dir / "candidate_artifact.json").write_text(
        json.dumps(artifact, indent=2) + "\n"
    )
    (args.output_dir / "submission_description.txt").write_text(description + "\n")
    print(
        json.dumps(
            {
                "candidate": str(path.resolve()),
                "sha256": artifact["sha256"],
                "adaptive_users": artifact["final_template_adaptation_eligible_users"],
                "e2_replacements": artifact["final_e2_replacements"],
            }
        ),
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
    assert {p: sha256_file(args.data_dir / p) for p in inputs} == inputs
    splits = {}
    results = {}
    preds = {}
    fallbacks = {}
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
        splits[name] = load_split(name, cache, truth, set(available), frozen)
        results[name], preds[name], fallbacks[name] = stage1(splits[name], args, name)
    eligible = [
        m
        for m in CONFIGS
        if all(results[s][m]["comparisons"]["v5"]["delta"] > 0 for s in splits)
    ]
    parent = (
        max(
            eligible,
            key=lambda m: (
                min(results[s][m]["comparisons"]["v5"]["delta"] for s in splits),
                m == "S40",
            ),
        )
        if eligible
        else None
    )
    combo = {}
    final = None
    qualified = []
    if parent:
        for name, split in splits.items():
            combo[name] = stage2(
                split, args, name, parent, preds[name][parent], fallbacks[name][parent]
            )
        if all(results[s][parent]["comparisons"]["v9"]["delta"] > 0 for s in splits):
            qualified.append(parent)
        if all(combo[s]["comparisons"]["v9"]["delta"] > 0 for s in splits):
            qualified.append(parent + "+E2")

        def worst_gain(model):
            return min(
                (
                    results[s][parent]["comparisons"]["v9"]
                    if model == parent
                    else combo[s]["comparisons"]["v9"]
                )["delta"]
                for s in splits
            )

        final = (
            max(qualified, key=lambda model: (worst_gain(model), model == parent))
            if qualified
            else None
        )
    evidence = {
        "stage1_selected": parent,
        "stage1_eligible": eligible,
        "final_qualified": qualified,
        "final_selected": final,
        "frozen_protocol_sha256": frozen["definition_sha256"],
        "grouping_provenance": "Exploratory hypothesis derived from v10 hold-out slices; not pre-validation independent.",
        "uncertainty": "Intervals conditional on reused overlapping cohorts; exclude grouping/configuration-selection uncertainty.",
        "preserved_csv_sha256": previous,
        "input_sha256": inputs,
        "elapsed_stages_seconds": time.perf_counter() - began,
        "environment": _environment(),
        "dependencies": versions(),
        "incumbent_v9": {
            "sha256": V9_HASH,
            "private": 0.40261,
            "public": 0.41871,
            "source": "User-screenshot-reported; no independent Kaggle lookup.",
            "submission_id": None,
            "submission_timestamp": None,
        },
    }
    (args.output_dir / "selection.json").write_text(
        json.dumps(evidence, indent=2) + "\n"
    )
    print(
        json.dumps(
            {
                "stage1_selected": parent,
                "final_qualified": qualified,
                "final_selected": final,
            }
        ),
        flush=True,
    )
    if final:
        make_candidate(args, CONFIGS[parent], final.endswith("+E2"), inputs)
    else:
        (args.output_dir / "candidate_decision.json").write_text(
            json.dumps(
                {
                    "decision": "Retain submitted v9; no eligible final candidate. No final fit or CSV."
                },
                indent=2,
            )
            + "\n"
        )
    assert all(sha256_file(Path(p)) == h for p, h in previous.items())
    assert all(
        sha256_file(Path(p)) == h for p, h in frozen["cached_input_sha256"].items()
    )
    assert all(
        sha256_file(s["truth_path"]) == s["truth_sha256"] for s in splits.values()
    )
    assert sha256_file(DEFINITION) == frozen["definition_sha256"]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("results/adaptive_threshold_20261030_v11"),
    )
    parser.add_argument(
        "--private-dir",
        type=Path,
        default=Path("artifacts/adaptive_threshold_20261030_v11"),
    )
    run(parser.parse_args())
