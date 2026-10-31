import sqlite3
import tempfile
import unittest
from pathlib import Path
from src.lower_threshold import lower_counts
from src.personal_threshold import personal_counts


class LowerThresholdTests(unittest.TestCase):
    def test_exact_boundaries_monotonic_airings_and_disconnected_unions(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "segments.sqlite"
            with sqlite3.connect(path) as db:
                db.execute("CREATE TABLE segments(u,a,item,s,e,d)")
                db.executemany(
                    "INSERT INTO segments VALUES (?,?,?,?,?,?)",
                    [
                        ("u", "a", "A", 0, 30, 100),
                        ("u", "a", "A", 0, 30, 100),
                        ("u", "a", "A", 70, 100, 100),
                        ("u", "b", "B", 0, 40, 100),
                        ("u", "c", "C", 0, 50, 100),
                        ("u", "d", "D", 0, 29.999, 100),
                    ],
                )
            counts, noise = lower_counts(path, 0, 100, {"u"}, {"A", "B", "C", "D"})
            self.assertEqual(counts[0.3], {"u": {"A": 1, "B": 1, "C": 1}})
            self.assertEqual(counts[0.4], {"u": {"B": 1, "C": 1}})
            self.assertEqual(counts[0.5], {"u": {"C": 1}})
            self.assertTrue(
                set(counts[0.5]["u"]) <= set(counts[0.4]["u"]) <= set(counts[0.3]["u"])
            )
            self.assertEqual(
                noise["0.3"]["all_training"]["full_airing_seconds"]["count"], 2
            )
            self.assertEqual(
                noise["0.4"]["all_training"]["longest_observed_block_seconds"]["mean"],
                40,
            )
            self.assertEqual(
                noise["0.3"]["all_training"]["total_observed_union_seconds"]["max"], 60
            )
            self.assertEqual(
                counts[0.5], personal_counts(path, 0, 100, thresholds=(0.5,))[0.5]
            )

    def test_observer_uses_clipped_end_and_full_denominator(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "segments.sqlite"
            with sqlite3.connect(path) as db:
                db.execute("CREATE TABLE segments(u,a,item,s,e,d)")
                db.executemany(
                    "INSERT INTO segments VALUES (?,?,?,?,?,?)",
                    [("u", "a", "A", 0, 1000, 100), ("u", "b", "B", 50, 150, 100)],
                )
            counts, noise = lower_counts(path, 0, 40, {"u"}, {"A", "B"})
            self.assertEqual(counts[0.4], {"u": {"A": 1}})
            self.assertEqual(counts[0.5], {})
            self.assertEqual(
                noise["0.4"]["all_training"]["longest_block_fraction"]["mean"], 0.4
            )
            self.assertEqual(
                noise["0.4"]["available_cohort"]["full_airing_seconds"]["mean"], 100
            )
