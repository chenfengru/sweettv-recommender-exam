import json
import math
import sqlite3
import tempfile
import unittest
from pathlib import Path
from src.first_submission import recency_weight, qualified_recency_counts


class RecencyTests(unittest.TestCase):
    def test_end_based_half_life_and_crossing_clamp(self):
        cutoff = 100 * 86400
        self.assertEqual(recency_weight(cutoff - 28 * 86400, cutoff, 28), 0.5)
        self.assertAlmostEqual(
            recency_weight(cutoff - 28 * 86400, cutoff, 56), math.sqrt(0.5)
        )
        self.assertEqual(recency_weight(cutoff + 3600, cutoff, 28), 1)
        with self.assertRaises(ValueError):
            recency_weight(cutoff, cutoff, 0)

    def test_union_qualification_keeps_full_airing_denominator(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "segments.sqlite"
            db = sqlite3.connect(p)
            db.execute(
                "CREATE TABLE segments(u TEXT,a TEXT,item TEXT,s REAL,e REAL,d REAL)"
            )
            cutoff = 100 * 86400
            # Old full 100-second airing qualifies once, even with duplicate segments.
            old_end = cutoff - 28 * 86400
            old = json.dumps(["3", old_end - 100, old_end, "A"])
            # Crossing airing has only 50% observed before cutoff, so must not qualify.
            crossing = json.dumps(["3", cutoff - 50, cutoff + 50, "B"])
            for s, e in [(old_end - 100, old_end - 20), (old_end - 80, old_end - 20)]:
                db.execute(
                    "INSERT INTO segments VALUES(?,?,?,?,?,?)",
                    ("u", old, "A", s, e, 100),
                )
            db.execute(
                "INSERT INTO segments VALUES(?,?,?,?,?,?)",
                ("u", crossing, "B", cutoff - 50, cutoff, 100),
            )
            db.commit()
            db.close()
            scores, counts, n = qualified_recency_counts(p, cutoff)
            self.assertEqual(n, 1)
            self.assertEqual(dict(counts), {"u": {"A": 1}})
            self.assertEqual(scores[28]["u"], {"A": 0.5})
            self.assertAlmostEqual(scores[56]["u"]["A"], math.sqrt(0.5))


if __name__ == "__main__":
    unittest.main()
