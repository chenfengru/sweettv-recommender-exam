"""Perturb only future behaviour in actual local data; check all four fitted methods."""

import argparse
import csv
import hashlib
import json
import time
from pathlib import Path
from threadpoolctl import threadpool_limits
from .compare_models import START, CUTOFF, END
from .interactions import csv_rows, extract_interactions, schedule_catalog
from .models import Ranker
from .real_matching_audit import stamp, wall
from .audit_data import _environment


def main(args):
    began = time.perf_counter()
    setup = json.loads((args.private_dir / "setup.json").read_text())
    source = args.data_dir / "dataset11-30.csv"
    perturbed = args.private_dir / "future_perturbed_views.csv"
    counts = {
        "strictly_future_rows_removed": 0,
        "crossing_tails_extended": 0,
        "pre_cutoff_rows_retained": 0,
    }
    with source.open(newline="") as f, perturbed.open("w", newline="") as dest:
        reader = csv.DictReader(f)
        writer = csv.DictWriter(dest, reader.fieldnames)
        writer.writeheader()
        for row in reader:
            s = stamp(row["start_time"])
            if s >= CUTOFF:
                counts["strictly_future_rows_removed"] += 1
                continue
            e = stamp(row["stop_time"])
            if e > CUTOFF:
                row["stop_time"] = wall(CUTOFF + 14 * 86400)
                row["duraton"] = str(int(CUTOFF + 14 * 86400 - s))
                counts["crossing_tails_extended"] += 1
            counts["pre_cutoff_rows_retained"] += 1
            writer.writerow(row)
    paths = [
        args.data_dir / "export_arh_11-20-final.csv",
        args.data_dir / "export_arh_21-30-final.csv",
    ]
    original = json.loads((args.private_dir / "train/interactions.json").read_text())
    changed, manifest = extract_interactions(
        perturbed, paths, START, CUTOFF, args.private_dir / "cutoff_invariance_cache"
    )
    assert original == changed, "Pre-cutoff interaction dependence on future behaviour"
    _, _, metadata = schedule_catalog(paths, CUTOFF, END, CUTOFF)
    comparison = json.loads((args.output_dir / "comparison.json").read_text())
    checks = {}
    for name, result in comparison["methods"].items():
        c = result["config"]
        kwargs = {
            k: c[k]
            for k in ("method", "factors", "regularization", "iterations", "seed")
            if k in c
        }
        model = Ranker(changed, set(setup["candidates"]), metadata, **kwargs)
        fingerprint = model.fingerprint()
        assert (
            fingerprint == result["model_fingerprint"]
        ), f"{name}: fitted features or parameters changed"
        preds = {u: model.recommend(u)[0] for u in setup["prediction_users"]}
        original_predictions = json.loads(
            (args.private_dir / f"{name}_predictions.json").read_text()
        )
        assert preds == original_predictions, f"{name}: predictions changed"
        checks[name] = {
            "fitted_features_and_parameters_unchanged": True,
            "fitted_fingerprint": fingerprint,
            "predictions_unchanged": True,
            "prediction_users": len(preds),
        }
    result = {
        "data_scope": "actual full local viewing file; no audit repeated",
        "mutation": counts,
        "schedule": "identical permitted schedule files; no schedule modification",
        "training_interactions_exactly_equal": True,
        "training_interaction_pairs": len(original),
        "perturbed_cache_output_sha256": manifest["output_sha256"],
        "methods": checks,
        "elapsed_seconds": time.perf_counter() - began,
        "environment": _environment(),
    }
    (args.output_dir / "actual_data_cutoff_invariance.json").write_text(
        json.dumps(result, indent=2) + "\n"
    )
    print(json.dumps({k: v for k, v in result.items() if k != "environment"}, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--private-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    with threadpool_limits(limits=1):
        main(args)
