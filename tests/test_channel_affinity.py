import json
import math
import sqlite3
import tempfile
import unittest
from pathlib import Path
import numpy as np
from src.channel_affinity import (
    union_seconds,
    channel_statistics,
    programme_weights,
    pair_affinity,
    append_affinity,
    AFFINITY_FEATURES,
)


class ChannelAffinityTests(unittest.TestCase):
    def database(self, root, views, segments):
        p = Path(root) / "cache.sqlite"
        with sqlite3.connect(p) as db:
            db.execute("CREATE TABLE views(u TEXT,c TEXT,s REAL,e REAL)")
            db.execute(
                "CREATE TABLE segments(u TEXT,a TEXT,item TEXT,s REAL,e REAL,d REAL)"
            )
            db.executemany("INSERT INTO views VALUES(?,?,?,?)", views)
            db.executemany("INSERT INTO segments VALUES(?,?,?,?,?,?)", segments)
        return p

    def test_channel_unions_unattributed_denominators_and_simultaneous_channels(self):
        with tempfile.TemporaryDirectory() as tmp:
            a = json.dumps(["A", 0, 100, "i"])
            p = self.database(
                tmp,
                [("u", "A", 0, 20), ("u", "A", 10, 30), ("u", "UNATTRIBUTED", 0, 20)],
                [("u", a, "i", 0, 60, 100), ("u", a, "i", 20, 60, 100)],
            )
            stats = channel_statistics(p, 0, 100)
            self.assertEqual(stats["seconds"][0]["u"]["A"], 30)
            self.assertEqual(stats["totals"][0][0]["u"], 50)
            self.assertEqual(stats["counts"][0]["u"]["A"], 1)
            row = pair_affinity(stats, "u", {"A": 1.0})
            self.assertAlmostEqual(row[0], math.log1p(30))
            self.assertEqual(row[1], 0.6)
            self.assertEqual(row[3], 1.0)
            self.assertEqual(row[8:], [0, 0, 0, 0])

    def test_trailing_clipped_qualification_longest_block_full_denominator(self):
        with tempfile.TemporaryDirectory() as tmp:
            day = 86400
            cutoff = 30 * day
            a = json.dumps(["A", day, day + 100, "old"])
            b = json.dumps(["A", cutoff - 100, cutoff, "new"])
            c = json.dumps(["A", cutoff - 300, cutoff - 200, "gaps"])
            p = self.database(
                tmp,
                [("u", "A", day, day + 60), ("u", "A", cutoff - 100, cutoff + 100)],
                [
                    ("u", a, "old", day, day + 60, 100),
                    ("u", b, "new", cutoff - 100, cutoff - 50, 100),
                    ("u", c, "gaps", cutoff - 300, cutoff - 270, 100),
                    ("u", c, "gaps", cutoff - 260, cutoff - 230, 100),
                ],
            )
            stats = channel_statistics(p, 0, cutoff)
            self.assertEqual(stats["counts"][0]["u"]["A"], 2)
            self.assertEqual(stats["counts"][1]["u"]["A"], 1)
            self.assertEqual(stats["seconds"][1]["u"]["A"], 100)
            self.assertEqual(
                union_seconds([(-1, 0), (0, 5), (4, 10), (10, 15), (20, 30)], 0, 10), 10
            )

    def test_schedule_multichannel_clipped_weights_dedup_and_exact_ids(self):
        catalog = [
            ("01", -10, 10, "i"),
            ("B", 0, 30, "i"),
            ("01", -10, 10, "i"),
            ("END", 40, 50, "x"),
        ]
        weights = programme_weights(catalog, 0, 40)
        self.assertEqual(weights["i"], {"01": 0.25, "B": 0.75})
        self.assertNotIn("x", weights)
        with tempfile.TemporaryDirectory() as tmp:
            p = self.database(tmp, [("u", "1", 0, 20), ("u", "B", 0, 10)], [])
            stats = channel_statistics(p, 0, 40)
            row = pair_affinity(stats, "u", weights["i"])
            self.assertAlmostEqual(row[0], math.log1p(0.75 * 10))
            self.assertEqual(row[1], 7.5 / 30)
            self.assertEqual(row[3], 0)
            self.assertEqual(row[8:], [0, 1, 0, 1])

    def test_no_history_indicators_and_original40_preservation(self):
        with tempfile.TemporaryDirectory() as tmp:
            stats = channel_statistics(self.database(tmp, [], []), 0, 100)
            row = pair_affinity(stats, "cold", {"missing": 1.0})
            self.assertEqual(row, [0.0] * 8 + [1, 1, 1, 1])
            base = np.arange(80, dtype=np.float32).reshape(2, 40)
            x, extra = append_affinity(
                base,
                ["cold"],
                [["i", "j"]],
                stats,
                {"i": {"missing": 1.0}, "j": {"missing": 1.0}},
            )
            np.testing.assert_array_equal(x[:, :40], base)
            self.assertEqual(x.shape, (2, 52))
            self.assertEqual(len(AFFINITY_FEATURES), 12)
            self.assertTrue(np.isfinite(x).all())

    def test_post_cutoff_behavior_invariance(self):
        with tempfile.TemporaryDirectory() as tmp:
            a = json.dumps(["A", 0, 100, "i"])
            p = self.database(tmp, [("u", "A", 0, 200)], [("u", a, "i", 0, 200, 100)])
            before = channel_statistics(p, 0, 60)
            with sqlite3.connect(p) as db:
                db.execute("UPDATE views SET e=300")
                db.execute("UPDATE segments SET e=300")
                db.execute("INSERT INTO views VALUES(?,?,?,?)", ("new", "A", 60, 100))
                db.execute(
                    "INSERT INTO segments VALUES(?,?,?,?,?,?)",
                    (
                        "new",
                        json.dumps(["A", 60, 100, "future"]),
                        "future",
                        60,
                        100,
                        40,
                    ),
                )
            after = channel_statistics(p, 0, 60)
            self.assertEqual(
                pair_affinity(before, "u", {"A": 1.0}),
                pair_affinity(after, "u", {"A": 1.0}),
            )
            self.assertEqual(before["totals"], after["totals"])
