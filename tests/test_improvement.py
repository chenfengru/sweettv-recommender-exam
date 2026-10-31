import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
import numpy as np
from src.improvement_helpers import (
    filtered_airing_interactions,
    exact_score_order,
    rrf_rank,
    complete,
)


class ImprovementTests(unittest.TestCase):
    def test_filter_uses_longest_block_but_keeps_union_contribution(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "segments.sqlite"
            db = sqlite3.connect(p)
            db.execute(
                "CREATE TABLE segments(u TEXT,a TEXT,item TEXT,s REAL,e REAL,d REAL)"
            )
            for item, segments in [("A", [(0, 50), (70, 100)]), ("B", [(200, 280)])]:
                key = json.dumps(
                    ["c", 0 if item == "A" else 200, 100 if item == "A" else 300, item]
                )
                for s, e in segments:
                    db.execute(
                        "INSERT INTO segments VALUES(?,?,?,?,?,?)",
                        ("u", key, item, s, e, 100),
                    )
            db.commit()
            db.close()
            records, counts = filtered_airing_interactions(p)
            self.assertEqual(records[0.5], [["u", "A", 0.8, 0], ["u", "B", 0.8, 1]])
            self.assertEqual(records[0.8], [["u", "B", 0.8, 1]])
            self.assertEqual(counts, {"0.5": 2, "0.8": 1})

    def test_popularity_breaks_only_exact_cosine_ties(self):
        ids = ["A", "B", "C"]
        scores = np.array([0.5, 0.5, np.nextafter(0.5, 1.0)])
        self.assertEqual(
            exact_score_order(ids, scores, {"A": 1, "B": 100, "C": 0}), ["C", "B", "A"]
        )
        self.assertEqual(exact_score_order(ids, scores), ["C", "A", "B"])

    def test_fusion_has_no_completion_evidence_or_ranks_beyond_50(self):
        self.assertEqual(rrf_rank([], [], 0.1), [])
        a = [str(i) for i in range(60)]
        self.assertNotIn("59", rrf_rank(a, [], 0.1))
        direct = rrf_rank(["A"], ["B"], 0.1)
        self.assertEqual(direct, ["A", "B"])
        prediction, n = complete(
            direct, ["X", "Y", "Z", "A", "B"], {"A", "B", "X", "Y", "Z"}
        )
        self.assertEqual(n, 2)
        self.assertEqual(prediction, ["A", "B", "X", "Y", "Z"])


if __name__ == "__main__":
    unittest.main()
