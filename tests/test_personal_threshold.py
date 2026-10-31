import sqlite3
import tempfile
import unittest
from pathlib import Path
from src.personal_threshold import personal_counts, predict
from src.personal_ties import global_qualified_statistics


class PersonalThresholdTests(unittest.TestCase):
    def database(self, rows):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        path = Path(temporary.name) / "segments.sqlite"
        with sqlite3.connect(path) as db:
            db.execute("CREATE TABLE segments(u,a,item,s,e,d)")
            db.executemany("INSERT INTO segments VALUES (?,?,?,?,?,?)", rows)
        return path

    def test_integer_counts_longest_block_and_deduplication(self):
        rows = [
            ("u", "a", "A", 0, 50, 100),
            ("u", "a", "A", 70, 100, 100),
            ("u", "b", "B", 0, 65, 100),
            ("u", "c", "C", 0, 80, 100),
            ("u", "c", "C", 0, 80, 100),
        ]
        result = personal_counts(self.database(rows), 0, 100)
        self.assertEqual(result[0.5], {"u": {"A": 1, "B": 1, "C": 1}})
        self.assertEqual(result[0.65], {"u": {"B": 1, "C": 1}})
        self.assertEqual(result[0.8], {"u": {"C": 1}})

    def test_cutoff_preserves_full_denominator(self):
        first = personal_counts(self.database([("u", "a", "A", 0, 65, 100)]), 0, 65)
        future = personal_counts(
            self.database(
                [("u", "a", "A", 0, 180, 100), ("u", "b", "B", 70, 170, 100)]
            ),
            0,
            65,
        )
        self.assertEqual(first, future)
        self.assertEqual(first[0.8], {})

    def test_fixed_truth_globals_fallback_and_slices(self):
        records = [
            ("u", "A", 1, 1),
            ("u", "B", 0.5, 0),
            ("v", "B", 1, 1),
            ("w", "B", 1, 1),
        ]
        viewers, total = global_qualified_statistics(records)
        fallback = ["B", "A", "C", "D", "E"]
        truth = {"u": ["A"]}
        slices = {"u": "1–5"}
        original = (
            dict(viewers),
            dict(total),
            list(fallback),
            dict(truth),
            dict(slices),
        )
        base, _ = predict(
            {"u": {"A": 1}}, set(fallback), viewers, total, fallback, ["u"]
        )
        lower, _ = predict(
            {"u": {"A": 1, "B": 1}}, set(fallback), viewers, total, fallback, ["u"]
        )
        self.assertEqual(base["u"][0], "A")
        self.assertEqual(lower["u"][0], "B")
        self.assertEqual(
            original, (dict(viewers), dict(total), fallback, truth, slices)
        )
