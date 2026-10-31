import csv
import math
import tempfile
import unittest
from pathlib import Path
import numpy as np
from src.schedule_features import (
    canonical_schedule,
    exposure_window,
    schedule_origin,
    augment,
    SCHEDULE_FEATURES,
)


class ScheduleFeatureTests(unittest.TestCase):
    def test_dedup_across_files_and_zero_programme(self):
        with tempfile.TemporaryDirectory() as directory:
            paths = [Path(directory) / f"{i}.csv" for i in range(2)]
            rows = [
                ["c", "A", "09.03.2020 00:00:00", "3600"],
                ["c", "0", "09.03.2020 00:00:00", "3600"],
            ]
            for path in paths:
                with path.open("w", newline="") as source:
                    writer = csv.writer(source)
                    writer.writerow(
                        ["channel_id", "tv_show_id", "start_time", "duration"]
                    )
                    writer.writerows(rows)
            catalog, source = canonical_schedule(paths)
            self.assertEqual(len(catalog), 1)
            self.assertEqual(catalog[0][3], "A")
            self.assertEqual(source[1]["duplicates_against_previous_rows"], 1)

    def test_window_boundaries_carryovers_and_cross_channel_seconds(self):
        catalog = [
            ("c", -10, 10, "A"),
            ("c", 10, 20, "A"),
            ("c", -20, 0, "B"),
            ("c", 20, 30, "C"),
            ("other", -10, 10, "A"),
        ]
        counts, seconds, report = exposure_window(catalog + [catalog[0]], 0, 20)
        self.assertEqual(counts, {"A": 3})
        self.assertEqual(seconds, {"A": 30})
        self.assertTrue(report["coverage_gate_passed"])
        self.assertEqual(report["global_covered_seconds"], 20)

    def test_full_window_normalization_and_genuine_zero_past(self):
        day = 86400
        cutoff = 28 * day
        catalog = [
            ("background", 0, 42 * day, "BG"),
            ("c", 29 * day, 29 * day + 3600, "A"),
        ]
        features, report = schedule_origin(catalog, cutoff, 42 * day)
        row = features["A"]
        self.assertEqual(row[0], 0)
        self.assertAlmostEqual(row[1], 1 / 14)
        self.assertEqual(row[2], 0)
        self.assertAlmostEqual(row[3], 3600 / 14)
        self.assertAlmostEqual(row[4], math.log1p(1 / 14))
        self.assertEqual(row[6], 1)
        self.assertEqual(report["past"]["full_window_days"], 28)
        self.assertEqual(report["future"]["full_window_days"], 14)

    def test_missing_coverage_stops_instead_of_imputing_zero(self):
        with self.assertRaises(ValueError):
            schedule_origin(
                [("c", 28 * 86400, 42 * 86400, "A")], 28 * 86400, 42 * 86400
            )

    def test_schedule_features_invariant_to_future_viewing_log_changes(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "schedule.csv"
            views = Path(directory) / "views.csv"
            with path.open("w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["channel_id", "tv_show_id", "start_time", "duration"])
                writer.writerow(["c", "A", "09.03.2020 00:00:00", 42 * 86400])
            from src.real_matching_audit import stamp

            views.write_text("user_id,programme_id\nu,A\n")
            first = schedule_origin(
                canonical_schedule([path])[0], stamp("2020-04-06"), stamp("2020-04-20")
            )[0]
            views.write_text(
                "future viewing,arbitrary changed programme\nnew-user,new-programme\n"
            )
            second = schedule_origin(
                canonical_schedule([path])[0], stamp("2020-04-06"), stamp("2020-04-20")
            )[0]
            self.assertEqual(first, second)

    def test_append_preserves_original_features_and_candidate_rows(self):
        base = np.arange(5 * 27, dtype=np.float32).reshape(5, 27)
        items = [list("ABCDE")]
        features = {it: [0, 1, 0, 100, math.log(2), math.log(101), 1] for it in "ABCDE"}
        extended, report = augment(base, items, features)
        self.assertEqual(extended.shape, (5, 34))
        self.assertTrue(np.array_equal(extended[:, :27], base))
        self.assertEqual(report["new_feature_missing_values"], 0)
        self.assertEqual(len(SCHEDULE_FEATURES), 7)
