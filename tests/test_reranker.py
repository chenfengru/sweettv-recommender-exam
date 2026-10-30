import sqlite3
import tempfile
import unittest
from pathlib import Path
import numpy as np
from src.reranker_features import (
    causal_history,
    FEATURES,
    user_features,
    candidate_union,
    candidate_labels,
    candidate_coverage,
    check_schema,
    ranked_candidates,
)
from src.interactions import clipped_clean_view, targets
from src.real_matching_audit import stamp


class RerankerTests(unittest.TestCase):
    def test_causal_full_counts_recency_rolling_and_future_tail_invariance(self):
        day = 86400
        cutoff = 40 * day
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "segments.sqlite"
            with sqlite3.connect(path) as db:
                db.execute("CREATE TABLE segments(u,a,item,s,e,d)")
                db.execute("CREATE TABLE views(u,c,s,e)")
                rows = [
                    ("u", "old", "A", day, day + 80, 100),
                    ("u", "recent", "A", 38 * day, 38 * day + 80, 100),
                    ("u", "cross", "B", cutoff - 40, cutoff + 1000, 100),
                ]
                db.executemany("INSERT INTO segments VALUES(?,?,?,?,?,?)", rows)
                db.execute("INSERT INTO views VALUES (?,?,?,?)", ("u", "c", 0, cutoff))
            before = causal_history(path, 0, cutoff)
            self.assertEqual(before["counts"][0.5], {"u": {"A": 2}})
            self.assertEqual(before["counts"][0.3], {"u": {"A": 2, "B": 1}})
            self.assertEqual(before["latest"]["u"]["A"], 38 * day + 80)
            self.assertEqual(before["rolling"][7]["u"]["A"], 1)
            self.assertEqual(before["rolling"][28]["u"]["A"], 1)
            with sqlite3.connect(path) as db:
                db.execute("UPDATE segments SET e=? WHERE a='cross'", (cutoff + 5000,))
                db.execute(
                    "INSERT INTO segments VALUES(?,?,?,?,?,?)",
                    ("future", "F", "F", cutoff + 1, cutoff + 101, 100),
                )
                db.execute(
                    "INSERT INTO views VALUES(?,?,?,?)",
                    ("future", "c", cutoff + 1, cutoff + 101),
                )
            self.assertEqual(before, causal_history(path, 0, cutoff))

    def test_historical_label_boundaries_and_original_top5_truth(self):
        start, end = stamp("2020-04-06"), stamp("2020-04-20")
        row = lambda s, e, d: {
            "user_id": "u",
            "vsetv_id": "c",
            "start_time": s,
            "stop_time": e,
            "duraton": str(d),
        }
        self.assertIsNone(
            clipped_clean_view(
                row("2020-04-05 23:59:00", "2020-04-06 00:00:00", 60), start, end
            )
        )
        self.assertIsNone(
            clipped_clean_view(
                row("2020-04-20 00:00:00", "2020-04-20 00:01:00", 60), start, end
            )
        )
        self.assertEqual(
            clipped_clean_view(
                row("2020-04-06 00:00:00", "2020-04-06 00:01:00", 60), start, end
            )[2],
            start,
        )
        truth = targets(
            [("u", str(i), 1, 1) for i in range(1, 8)], {str(i) for i in range(1, 8)}
        )
        self.assertEqual(len(truth["u"]), 5)

    def fixture(self):
        counts = {
            0.3: {"u": {x: 2 for x in "ABCDEF"}},
            0.5: {"u": {x: 1 for x in "ABCDEF"}},
            0.8: {"u": {"A": 1}},
        }
        return {
            "counts": counts,
            "latest": {"u": {x: 900 for x in "ABCDEF"}},
            "rolling": {7: {}, 28: {}},
            "cutoff": 1000,
            "known_users": {"u"},
        }

    def test_complete_counts_missing_ranks_and_fixed_source_schema(self):
        pool = set("ABCDEFX")
        fallback = list("ABCDE")
        history = self.fixture()
        items, matrix = user_features(
            "u", history, {"A": [("X", 0.5)]}, pool, {}, {}, fallback
        )
        row = lambda it: dict(zip(FEATURES, matrix[items.index(it)]))
        self.assertEqual(row("F")["personal_n50_rank"], 6)
        self.assertEqual(row("F")["n30"], 2)
        self.assertEqual(row("F")["n50"], 1)
        self.assertEqual(row("X")["personal_n50_rank"], 0)
        self.assertEqual(row("X")["personal_rank_missing"], 1)
        self.assertEqual(row("X")["last_n50_view_missing"], 1)
        self.assertEqual(row("X")["source_unseen50"], 1)
        self.assertEqual(row("X")["item_item_rank_missing"], 0)
        self.assertEqual(matrix.shape[1], 27)
        self.assertTrue(np.isfinite(matrix).all())

    def test_no_positive_injection_and_cold_fallback_candidates(self):
        pool = set("ABCDEX")
        fallback = list("ABCDE")
        items, sources = candidate_union([], [], fallback, pool)
        self.assertNotIn("X", items)
        self.assertEqual(
            candidate_labels(["u"], [items], {"u": ["X"]}).tolist(), [0] * 5
        )
        self.assertEqual(
            candidate_coverage(["u"], [items], {"u": ["X"]})["micro_recall"], 0
        )
        changed_labels = {"u": ["A", "X"]}
        self.assertEqual(candidate_union([], [], fallback, pool)[0], items)
        self.assertEqual(int(candidate_labels(["u"], [items], changed_labels).sum()), 1)

    def test_probability_ties_follow_full_v5_keys_and_schema_checks(self):
        items = ["2", "10", "A", "B", "C", "D"]
        pool = set(items)
        pred, size = ranked_candidates(
            items, np.full(6, 0.5), {"A": 2, "B": 1}, {"2": 3, "10": 3}, {}, pool, items
        )
        self.assertEqual(pred, ["A", "B", "10", "2", "C"])
        matrix = np.zeros((2, len(FEATURES)), dtype=np.float32)
        check_schema(matrix, FEATURES)
        with self.assertRaises(ValueError):
            check_schema(matrix, list(reversed(FEATURES)))
        matrix[0, 0] = np.nan
        with self.assertRaises(ValueError):
            check_schema(matrix, FEATURES)
        self.assertNotIn("user_id", FEATURES)
        self.assertNotIn("item_id", FEATURES)
