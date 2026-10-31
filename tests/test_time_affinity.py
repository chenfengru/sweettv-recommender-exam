import sqlite3
import tempfile
import unittest
from pathlib import Path
import numpy as np
from src.real_matching_audit import stamp
from src.time_affinity import (
    histogram,
    normalized_histogram,
    merge_intervals,
    user_profiles,
    schedule_profiles,
    append_time_features,
    TIME_FEATURES,
)


class TimeAffinityTests(unittest.TestCase):
    def test_hour_day_week_boundaries_and_fractional_mass(self):
        start = stamp("2020-03-15 23:30:00")
        end = stamp("2020-03-16 00:30:00")
        d, w, total = histogram([(start, end)])
        self.assertEqual(total, 3600)
        self.assertEqual(d[23], 1800)
        self.assertEqual(d[0], 1800)
        self.assertEqual(w[167], 1800)
        self.assertEqual(w[0], 1800)
        d, w, total = histogram([(3599.5, 3600.25)])
        self.assertEqual(total, 0.75)
        self.assertEqual(d[0], 0.5)
        self.assertEqual(d[1], 0.25)
        self.assertEqual(d.sum(), total)
        self.assertEqual(w.sum(), total)
        nd, nw, _ = normalized_histogram([(start, end)])
        self.assertEqual(nd.sum(), 1)
        self.assertEqual(nw.sum(), 1)

    def cache(self, tmp, rows):
        p = Path(tmp) / "views.sqlite"
        with sqlite3.connect(p) as db:
            db.execute("CREATE TABLE views(u TEXT,c TEXT,s REAL,e REAL)")
            db.executemany("INSERT INTO views VALUES(?,?,?,?)", rows)
        return p

    def test_cross_channel_union_unattributed_and_post_cutoff_invariance(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = self.cache(
                tmp,
                [("u", "A", 0, 60), ("u", "UNATTRIBUTED", 30, 90), ("u", "B", 80, 200)],
            )
            first = user_profiles(p, 0, 100)
            self.assertEqual(first["u"][0][2], 100)
            self.assertEqual(
                merge_intervals([(0, 60), (30, 90), (80, 200)], 0, 100), [(0, 100)]
            )
            with sqlite3.connect(p) as db:
                db.execute('UPDATE views SET e=500 WHERE c="B"')
                db.execute(
                    "INSERT INTO views VALUES(?,?,?,?)", ("future", "A", 100, 200)
                )
            second = user_profiles(p, 0, 100)
            self.assertNotIn("future", second)
            for k in range(2):
                np.testing.assert_array_equal(first["u"][k][0], second["u"][k][0])
                np.testing.assert_array_equal(first["u"][k][1], second["u"][k][1])
                self.assertEqual(first["u"][k][2], second["u"][k][2])

    def test_schedule_midnight_carryover_dedup_clipping_add_across_channels(self):
        start = stamp("2020-03-16")
        end = start + 3600
        catalog = [
            ("c", start - 1800, start + 1800, "i"),
            ("c", start - 1800, start + 1800, "i"),
            ("other", start, start + 3600, "i"),
            ("c", end, end + 100, "future"),
            ("c", start - 100, start, "past"),
            ("c", start, end, "0"),
        ]
        profiles = schedule_profiles(catalog, start, end)
        self.assertEqual(set(profiles), {"i"})
        self.assertEqual(profiles["i"][2], 5400)
        self.assertEqual(profiles["i"][0][0], 1.0)
        self.assertEqual(profiles["i"][1][0], 1.0)

    def test_known_dot_products_and_no_second_exposure_division(self):
        start = stamp("2020-03-16")
        user = normalized_histogram([(start, start + 3600)])
        programme = normalized_histogram([(start, start + 7200)])
        base = np.arange(52, dtype=np.float32).reshape(1, 52)
        x, extra = append_time_features(
            base, ["u"], [["i"]], {"u": [user, user]}, {"i": programme}
        )
        np.testing.assert_array_equal(
            extra, np.array([[0.5, 0.5, 0.5, 0.5, 0, 0]], dtype=np.float32)
        )
        np.testing.assert_array_equal(x[:, :52], base)
        self.assertEqual(x.shape, (1, 58))
        self.assertEqual(len(TIME_FEATURES), 6)
        scaled = normalized_histogram([(start, start + 7200), (start, start + 7200)])
        _, twice = append_time_features(
            base, ["u"], [["i"]], {"u": [user, user]}, {"i": scaled}
        )
        np.testing.assert_array_equal(twice, extra)

    def test_zero_histories_trailing_window_and_missing_programme_fail(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = self.cache(tmp, [("u", "A", 0, 3600)])
            users = user_profiles(p, 0, 30 * 86400)
            self.assertEqual(users["u"][0][2], 3600)
            self.assertEqual(users["u"][1][2], 0)
            programme = normalized_histogram([(0, 3600)])
            _, extra = append_time_features(
                np.zeros((2, 52), dtype=np.float32),
                ["u", "cold"],
                [["i"], ["i"]],
                users,
                {"i": programme},
            )
            self.assertEqual(extra[0].tolist(), [1, 1, 0, 0, 0, 1])
            self.assertEqual(extra[1].tolist(), [0, 0, 0, 0, 1, 1])
            self.assertEqual(programme[0].sum(), 1)
            with self.assertRaises(ValueError):
                append_time_features(
                    np.zeros((1, 52)), ["u"], [["missing"]], users, {"i": programme}
                )
