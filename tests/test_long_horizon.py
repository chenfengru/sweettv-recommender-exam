import csv
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
import numpy as np
from src.experiment_long_horizon import assert_label_window, immutable_origin
from src.interactions import extract_interactions, targets
from src.real_matching_audit import stamp
from src.schedule_features import schedule_origin
from src.reranker_features import candidate_union, candidate_labels
from src.csv_io import sha256_file
from unittest.mock import patch


class LongHorizonTests(unittest.TestCase):
    def test_half_open_labels_no_may18_or_later_behavior_and_full_denominator(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)

            def write(name, header, rows):
                p = root / name
                with p.open("w", newline="") as f:
                    w = csv.writer(f)
                    w.writerow(header)
                    w.writerows(rows)
                return p

            schedule = write(
                "schedule.csv",
                ["channel_id", "start_time", "duration", "tv_show_id"],
                [
                    ["c", "06.04.2020 00:00:00", 3600, "START"],
                    ["c", "17.05.2020 23:00:00", 3600, "END"],
                    ["c", "18.05.2020 00:00:00", 3600, "FUTURE"],
                    ["other", "17.05.2020 23:00:00", 7200, "CROSS"],
                ],
            )
            header = ["user_id", "vsetv_id", "start_time", "stop_time", "duraton"]
            rows = [
                ["u", "c", "2020-04-06 00:00:00", "2020-04-06 01:00:00", 3600],
                ["u", "c", "2020-05-17 23:00:00", "2020-05-18 00:00:00", 3600],
                ["u", "other", "2020-05-17 23:00:00", "2020-05-18 01:00:00", 7200],
            ]
            start, end = stamp("2020-04-06"), stamp("2020-05-18")
            before, _ = extract_interactions(
                write("a.csv", header, rows), [schedule], start, end, root / "a"
            )
            after, _ = extract_interactions(
                write(
                    "b.csv",
                    header,
                    rows
                    + [
                        ["u", "c", "2020-05-18 00:00:00", "2020-05-18 01:00:00", 3600],
                        [
                            "new",
                            "c",
                            "2020-05-19 00:00:00",
                            "2020-05-19 01:00:00",
                            3600,
                        ],
                    ],
                ),
                [schedule],
                start,
                end,
                root / "b",
            )
            self.assertEqual(before, after)
            truth = targets(before, {"START", "END", "CROSS", "FUTURE"})
            self.assertEqual(set(truth["u"]), {"START", "END"})
            assert_label_window(start, end)
            with self.assertRaises(ValueError):
                assert_label_window(start, end + 1)

    def test_origin_availability_and_full_future_rate_windows(self):
        day = 86400
        cutoff = stamp("2020-04-06")
        end = stamp("2020-05-18")
        catalog = [
            ("bg", cutoff - 28 * day, end, "BG"),
            ("c", cutoff + 20 * day, cutoff + 20 * day + 3600, "LATER"),
        ]
        short, _ = schedule_origin(catalog, cutoff, cutoff + 14 * day)
        long, coverage = schedule_origin(catalog, cutoff, end)
        self.assertNotIn("LATER", short)
        self.assertAlmostEqual(long["LATER"][1], 1 / 42)
        self.assertEqual(coverage["past"]["full_window_days"], 28)
        self.assertEqual(coverage["future"]["full_window_days"], 42)
        items, _ = candidate_union(["BG"], [], ["BG"], {"BG"})
        labels = candidate_labels(["u"], [items], {"u": ["LATER"]})
        self.assertNotIn("LATER", items)
        self.assertEqual(labels.tolist(), [0])

    def test_evaluation_reads_exact_original_features_and_row_index(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            old = root / "old"
            meta = root / "meta"
            for p in [old / "main", meta / "main"]:
                p.mkdir(parents=True)
            x = np.arange(200, dtype=np.float32).reshape(5, 40)
            np.save(old / "main/extended_features.npy", x)
            row = {
                "users": ["u"],
                "items": [["1", "2", "3", "4", "5"]],
                "offsets": [0, 5],
            }
            (meta / "main/row_index.json").write_text(json.dumps(row))
            files = [old / "main/extended_features.npy", meta / "main/row_index.json"]
            frozen = {"source_artifact_sha256": {str(p): sha256_file(p) for p in files}}
            args = SimpleNamespace(
                private_dir=root / "private", output_dir=root / "results"
            )
            schedule = {i: [0, 1, 0, 0, 0, 0, 0] for i in row["items"][0]}
            with patch("src.experiment_long_horizon.OLD", old), patch(
                "src.experiment_long_horizon.META", meta
            ), patch(
                "src.experiment_long_horizon.schedule_origin",
                return_value=(schedule, {}),
            ):
                prepared = immutable_origin(args, "main", [], frozen)
            self.assertTrue(np.array_equal(prepared["x"], x))
            self.assertEqual(prepared["items"], row["items"])
