"""Independent full-origin numeric verification; no model fitting."""

import json
import time
from pathlib import Path
import numpy as np
from src.experiment_lightfm_extension import ORIGINS, train_cache
from src.experiment_lower_threshold import START
from src.schedule_features import canonical_schedule
from src.time_affinity import user_profiles, schedule_profiles
from src.csv_io import sha256_file
import argparse


def run(args):
    p = Path("results/time_affinity_20261030_v19")
    private = Path("artifacts/time_affinity_20261030_v19")
    began = time.perf_counter()
    catalog, _ = canonical_schedule(
        [
            args.data_dir / f"export_arh_{s}-final.csv"
            for s in ["11-20", "21-30", "31-42"]
        ]
    )
    out = {}
    for name in ["origin_20200406", "origin_20200420", "main", "auxiliary"]:
        cutoff, end = ORIGINS[name]
        profiles = user_profiles(train_cache(name) / "segments.sqlite", START, cutoff)
        programmes = schedule_profiles(catalog, cutoff, end)
        meta = json.loads(
            (
                Path("artifacts/lightgbm_reranker_20261030_v12")
                / name
                / "row_index.json"
            ).read_text()
        )
        chunks = []
        zero = (np.zeros(24), np.zeros(168), 0.0)
        for u, row in zip(meta["users"], meta["items"]):
            day = np.asarray([programmes[it][0] for it in row])
            week = np.asarray([programmes[it][1] for it in row])
            full, trailing = profiles.get(u, [zero, zero])
            # Independent sum of elementwise products: no matrix multiplication / BLAS.
            chunks.append(
                np.column_stack(
                    [
                        np.sum(day * full[0], axis=1),
                        np.sum(week * full[1], axis=1),
                        np.sum(day * trailing[0], axis=1),
                        np.sum(week * trailing[1], axis=1),
                        np.full(len(row), full[2] == 0),
                        np.full(len(row), trailing[2] == 0),
                    ]
                )
            )
        check = np.concatenate(chunks).astype(np.float32)
        old = np.load(private / name / "time_features.npy")
        assert np.array_equal(check, old), (
            name,
            float(np.max(abs(check - old))),
            int(np.sum(check != old)),
        )
        out[name] = {
            "rows": len(old),
            "independent_elementwise_sum_all_six_columns_bitwise_equal": True,
            "max_abs_difference": 0.0,
            "saved_feature_sha256": sha256_file(private / name / "time_features.npy"),
        }
        print(name, "bitwise equal", flush=True)
    (p / "numeric_verification.json").write_text(
        json.dumps(
            {
                "method": "Recompute normalized profiles, elementwise multiply then np.sum over bins; no matmul or BLAS. Compare all float32 feature values against actual fit/evaluation saved arrays.",
                "origins": out,
                "elapsed_seconds": time.perf_counter() - began,
                "model_fits_during_verification": 0,
            },
            indent=2,
        )
        + "\n"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Verify all saved time affinities using elementwise products, without fitting."
    )
    parser.add_argument("--data-dir", type=Path, required=True)
    run(parser.parse_args())
