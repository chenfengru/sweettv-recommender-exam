"""Execute the frozen four-method local comparison; no Kaggle or final refit."""

import argparse
import csv
import hashlib
import importlib.metadata
import inspect
import json
import os
import platform
import resource
import subprocess
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
from threadpoolctl import threadpool_limits
from .audit_data import _environment
from .csv_io import sha256_file
from .interactions import extract_interactions, schedule_catalog, targets, csv_rows
from .metrics import average_precision_at_k
from .models import Ranker
from .real_matching_audit import stamp

DATA_NAMES = [
    "dataset11-30.csv",
    "export_arh_11-20-final.csv",
    "export_arh_21-30-final.csv",
    "export_arh_31-42-final.csv",
    "submission.csv",
]
START, CUTOFF, END = map(stamp, ["2020-03-09", "2020-05-18", "2020-07-27"])


def rss():
    value = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return value if sys.platform == "darwin" else value * 1024


def versions():
    return {
        name: importlib.metadata.version(name)
        for name in ["numpy", "scipy", "implicit", "threadpoolctl", "tqdm"]
    }


def history_slice(count):
    return (
        "0" if count == 0 else "1–5" if count <= 5 else "6–20" if count <= 20 else "21+"
    )


def worker(args):
    setup = json.loads((args.private_dir / "setup.json").read_text())
    records = json.loads((args.private_dir / "train/interactions.json").read_text())
    truth = json.loads((args.private_dir / "truth.json").read_text())
    metadata = {it: tuple(values) for it, values in setup["metadata"].items()}
    config = json.loads(args.worker)
    with threadpool_limits(limits=1):
        model = Ranker(records, set(setup["candidates"]), metadata, **config)
        train_peak = rss()
        began = time.perf_counter()
        predictions, primary_sizes = {}, {}
        for user in setup["prediction_users"]:
            predictions[user], primary_sizes[user] = model.recommend(user)
        infer = time.perf_counter() - began
    ap = {
        u: average_precision_at_k(actual, predictions[u]) for u, actual in truth.items()
    }
    slices = defaultdict(list)
    for u, score in ap.items():
        slices[history_slice(len(model.qualified.get(u, {})))].append(score)
    predicted_items = {it for u in truth for it in predictions[u]}
    cold = sum(primary_sizes[u] == 0 for u in truth)
    partial = sum(0 < primary_sizes[u] < 5 for u in truth)
    slots = sum(5 - primary_sizes[u] for u in truth)
    repeats = sum(
        it in model.history.get(u, {}) for u in truth for it in predictions[u]
    )
    if model.method == "cbf":
        unsupported = int(np.sum(np.diff(model.candidate_content.indptr) == 0))
    elif model.method == "als":
        unsupported = len(setup["candidates"]) - len(model.supported_candidates)
    else:
        unsupported = 0
    result = {
        "config": model.config,
        "map_at_5": sum(ap.values()) / len(ap),
        "evaluation_users": len(truth),
        "prediction_users": len(predictions),
        "template_users_predicted": len(setup["template_users"]),
        "candidate_count": len(setup["candidates"]),
        "history_slices": {
            k: {"users": len(v), "map_at_5": sum(v) / len(v)}
            for k, v in sorted(slices.items())
        },
        "fallback": {
            "complete_users": cold,
            "partial_completion_users": partial,
            "completion_slots": slots,
            "slot_fraction": slots / (5 * len(truth)),
            "complete_user_fraction": cold / len(truth),
            "partial_user_fraction": partial / len(truth),
        },
        "zero_qualified_training_history_users": sum(
            not model.qualified.get(u) for u in truth
        ),
        "zero_soft_training_history_users": sum(
            not model.history.get(u) for u in truth
        ),
        "distinct_recommended_items": len(predicted_items),
        "catalogue_coverage": len(predicted_items) / len(setup["candidates"]),
        "repeated_item_share": repeats / (5 * len(truth)),
        "candidates_without_method_representation": unsupported,
        "fit_seconds": model.fit_seconds,
        "inference_seconds": infer,
        "peak_rss_after_fit_bytes": train_peak,
        "peak_process_rss_bytes": rss(),
        "memory_method": "resource.ru_maxrss isolated worker lifetime high-water; includes loaded records and imports",
        "all_lists_valid": all(
            len(v) == 5
            and len(set(v)) == 5
            and "0" not in v
            and set(v) <= set(setup["candidates"])
            for v in predictions.values()
        ),
        "dependencies": versions(),
        "environment": _environment(),
        "model_fingerprint": model.fingerprint(),
    }
    assert result["all_lists_valid"] and result["evaluation_users"] == 4625
    name = args.name
    prediction_path = args.private_dir / f"{name}_predictions.json"
    prediction_path.write_text(json.dumps(predictions, separators=(",", ":")) + "\n")
    (args.private_dir / f"{name}_ap.json").write_text(
        json.dumps(ap, separators=(",", ":")) + "\n"
    )
    result["private_predictions_path"] = str(prediction_path)
    result["prediction_sha256"] = sha256_file(prediction_path)
    if model.method == "als":
        model.als.save(args.private_dir / f"{name}_model.npz")
    (args.output_dir / f"{name}.json").write_text(json.dumps(result, indent=2) + "\n")
    print(
        json.dumps(
            {
                "method": name,
                "MAP@5": result["map_at_5"],
                "fit_seconds": result["fit_seconds"],
                "inference_seconds": infer,
            }
        ),
        flush=True,
    )


def main(args):
    args.output_dir.mkdir(parents=True, exist_ok=True)
    args.private_dir.mkdir(parents=True, exist_ok=True)
    began = time.perf_counter()
    # Check identity, not re-audit the established dataset.
    measured = {name: sha256_file(args.data_dir / name) for name in DATA_NAMES}
    established = json.loads(
        Path("results/local_audit_20261029/data_audit.json").read_text()
    )
    assert measured == {f["filename"]: f["sha256"] for f in established["files"]}
    schedule_paths = [args.data_dir / name for name in DATA_NAMES[1:3]]
    train, train_manifest = extract_interactions(
        args.data_dir / DATA_NAMES[0],
        schedule_paths,
        START,
        CUTOFF,
        args.private_dir / "train",
        input_hashes=measured,
    )
    valid, valid_manifest = extract_interactions(
        args.data_dir / DATA_NAMES[0],
        schedule_paths,
        CUTOFF,
        END,
        args.private_dir / "validation",
        input_hashes=measured,
    )
    airings, _, metadata = schedule_catalog(schedule_paths, CUTOFF, END, CUTOFF)
    candidates = {a.item_id for a in airings}
    truth = targets(valid, candidates)
    assert (
        len(truth) == 4625
    ), f"Frozen cohort mismatch: {len(truth)} != 4625; stop before comparisons"
    assert (
        len(candidates) == 6384
    ), f"Frozen candidates mismatch: {len(candidates)} != 6384"
    # Exact reconciliation against authoritative audit counts, not just equal cohort size.
    reference = json.loads(
        Path("results/model_comparison_20261029/audit_reference.json").read_text()
    )

    def qualified_digest(records):
        values = sorted(
            [[u, it, count] for u, it, _, count in records if count],
            key=lambda r: (r[0], r[1]),
        )
        return hashlib.sha256(
            json.dumps(values, separators=(",", ":")).encode()
        ).hexdigest()

    assert (
        qualified_digest(valid) == reference["validation_qualified_counts_sha256"]
    ), "Held-out qualified counts differ from authoritative audit"
    # The causal prefix correction changes no actual qualified training counts.
    assert (
        qualified_digest(train) == reference["training_qualified_counts_sha256"]
    ), "Training qualified counts require investigation"
    changed = []
    template = [r["user_id"] for r in csv_rows(args.data_dir / "submission.csv")]
    counts = Counter()
    soft = Counter()
    for u, it, strength, count in train:
        soft[u] += 1
        if count:
            counts[u] += 1
    eligible = [u for u in template if counts[u] > 0]
    examples = {
        "history_poor": min(eligible, key=lambda u: (counts[u], u)),
        "history_rich": min(eligible, key=lambda u: (-counts[u], u)),
    }
    setup = {
        "candidates": sorted(candidates),
        "metadata": metadata,
        "template_users": template,
        "prediction_users": sorted(set(truth) | set(template) | set(examples.values())),
        "examples": examples,
        "selection_rule": "Among template users with qualified training history: min/max distinct qualified programme count; ties ascending raw user ID. No held-out hits or scores used.",
    }
    (args.private_dir / "setup.json").write_text(json.dumps(setup, ensure_ascii=False))
    (args.private_dir / "truth.json").write_text(
        json.dumps(truth, separators=(",", ":"))
    )
    (args.private_dir / "causal_cleaning_changes.json").write_text(json.dumps(changed))
    # Publish aggregate cache provenance only. Histories and predictions remain private.
    prep = {
        "train": train_manifest,
        "validation": valid_manifest,
        "input_checksums": measured,
        "cohort": len(truth),
        "candidates": len(candidates),
        "validation_qualified_counts_match_audit": True,
        "training_qualified_pairs_changed_by_causal_prefix_cleaning": len(changed),
        "train_soft_pairs": len(train),
        "validation_soft_pairs": len(valid),
        "metadata_candidate_ids_missing_pre_cutoff_representation": len(
            candidates - set(metadata)
        ),
        "examples_selection_rule": setup["selection_rule"],
        "preparation_seconds": time.perf_counter() - began,
        "dependencies": versions(),
        "environment": _environment(),
    }
    (args.output_dir / "preparation.json").write_text(json.dumps(prep, indent=2) + "\n")
    print(
        json.dumps(
            {
                "prepared": True,
                "cohort": len(truth),
                "candidates": len(candidates),
                "training_pairs_changed_causal": len(changed),
            }
        ),
        flush=True,
    )
    configs = [
        ("popularity", {"method": "popularity"}),
        ("personal", {"method": "personal"}),
        ("cbf", {"method": "cbf"}),
    ]
    configs += [
        (f"als_f{f}_r{r}", {"method": "als", "factors": f, "regularization": r})
        for f in (32, 64)
        for r in (0.01, 0.1)
    ]
    for name, config in configs:
        command = [
            sys.executable,
            "-m",
            "src.compare_models",
            "--output-dir",
            str(args.output_dir),
            "--private-dir",
            str(args.private_dir),
            "--worker",
            json.dumps(config),
            "--name",
            name,
        ]
        subprocess.run(
            command,
            check=True,
            env={
                **os.environ,
                "OPENBLAS_NUM_THREADS": "1",
                "OMP_NUM_THREADS": "1",
                "VECLIB_MAXIMUM_THREADS": "1",
            },
        )
    results = {
        name: json.loads((args.output_dir / f"{name}.json").read_text())
        for name, _ in configs
    }
    best = min(
        (name for name in results if name.startswith("als_")),
        key=lambda n: (-results[n]["map_at_5"], n),
    )
    summary = {
        "methods": {
            name: results[name] for name in ["popularity", "personal", "cbf", best]
        },
        "selected_als_configuration": best,
        "all_als_grid_scores": {
            name: r["map_at_5"]
            for name, r in results.items()
            if name.startswith("als_")
        },
        "elapsed_seconds": time.perf_counter() - began,
        "no_kaggle_submission": True,
    }
    (args.output_dir / "comparison.json").write_text(
        json.dumps(summary, indent=2) + "\n"
    )
    write_examples(args, setup, train, truth, summary, metadata)


def write_examples(args, setup, train, truth, summary, metadata):
    history = defaultdict(list)
    for u, it, strength, count in train:
        if u in setup["examples"].values():
            history[u].append((it, strength, count))
    # Display-only held-out metadata; never enters fitted CBF features or item scoring.
    paths = [args.data_dir / n for n in DATA_NAMES[1:3]]
    _, _, display = schedule_catalog(paths, START, END, END)
    lines = [
        "# Two-user comparison",
        "",
        "Users are anonymized here; the private setup file preserves the source-ID mapping. Selection used training history only: "
        + setup["selection_rule"],
        "",
    ]
    private = {}
    for label, u in setup["examples"].items():
        h = history[u]
        qual = [x for x in h if x[2]]
        private[label] = {
            "user_id": u,
            "training_history": h,
            "truth": truth.get(u, []),
        }
        lines += [
            f'## {label.replace("_"," ").title()}',
            "",
            f"{len(h)} distinct programmes with soft training overlap; {len(qual)} with qualified training airings. Held-out target IDs: "
            + (
                ", ".join(truth[u])
                if u in truth
                else "none observed; outside the fixed evaluation cohort"
            )
            + ".",
            "",
            "| Observed training programme | Title | Category | Qualified airings | Soft airing sum |",
            "| --- | --- | --- | ---: | ---: |",
        ]
        for it, strength, count in sorted(h, key=lambda x: (-x[2], -x[1], x[0]))[:5]:
            md = metadata.get(it, display.get(it, ("", "", "", "", "")))
            lines.append(
                f'| {it} | {md[0].replace("|","/")} | {md[1]} | {count} | {strength:.4f} |'
            )
        lines += [
            "",
            "| Method | Rank | Programme ID | Title | Category | Held-out hit | Seen in training |",
            "| --- | ---: | --- | --- | --- | --- | --- |",
        ]
        seen = {x[0] for x in h}
        for name in summary["methods"]:
            pred = json.loads(
                (args.private_dir / f"{name}_predictions.json").read_text()
            )[u]
            for rank, it in enumerate(pred, 1):
                md = display.get(
                    it, metadata.get(it, ("unknown", "unknown", "", "", ""))
                )
                lines.append(
                    f'| {name} | {rank} | {it} | {md[0].replace("|","/")} | {md[1]} | {"yes" if it in truth.get(u,[]) else ("no" if u in truth else "not evaluable")} | {"yes" if it in seen else "no"} |'
                )
        lines += [""]
    (args.private_dir / "example_histories.json").write_text(
        json.dumps(private, ensure_ascii=False, indent=2)
    )
    (args.output_dir / "two_user_examples.md").write_text("\n".join(lines).rstrip() + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--private-dir", type=Path, required=True)
    parser.add_argument("--worker")
    parser.add_argument("--name")
    args = parser.parse_args()
    worker(args) if args.worker else main(args)
