import math
import sqlite3
import tempfile
import unittest
from pathlib import Path
from src.item_item import fit_item_item, score_user, retrieval_metrics
from src.personal_threshold import personal_counts


class ItemItemTests(unittest.TestCase):
    def test_binary_coview_normalization_shrinkage_and_support_gate(self):
        counts = {
            "u1": {"A": 9, "B": 1, "C": 1},
            "u2": {"A": 1, "B": 1, "C": 1},
            "u3": {"A": 1, "B": 1},
            "u4": {"B": 1, "D": 1},
            "u5": {"D": 1},
        }
        model, support, stats = fit_item_item(counts)
        self.assertEqual(support, {"A": 3, "B": 4, "C": 2, "D": 2})
        self.assertEqual(stats["binary_pairs"], 11)
        self.assertAlmostEqual(model["A"][0][1], 3 / math.sqrt(3 * 4) * 3 / 23)
        self.assertEqual([i for i, s in model["A"]], ["B"])
        self.assertEqual(model["C"], [])
        self.assertTrue(all(i != j for i, row in model.items() for j, s in row))

    def test_raw_string_pruning_and_block_invariance(self):
        counts = {str(u): {"S": 1, "10": 1, "2": 1} for u in range(3)}
        model, _, _ = fit_item_item(counts, top_k=1, block_items=1)
        other, _, _ = fit_item_item(
            dict(reversed(list(counts.items()))), top_k=1, block_items=128
        )
        self.assertEqual(model, other)
        self.assertEqual(model["S"][0][0], "10")
        self.assertTrue(all(len(row) <= 1 for row in model.values()))

    def test_log_weighting_availability_watched_eligibility_and_unseen(self):
        model = {"A": [("X", 0.5)], "B": [("Y", 0.8), ("Z", 0.9)]}
        direct, unseen = score_user({"A": 3, "B": 1, "X": 1}, model, {"X", "Y"})
        self.assertEqual(direct, ["X", "Y"])
        self.assertEqual(unseen, ["Y"])
        self.assertEqual(score_user({}, model, {"X", "Y"}), ([], []))

    def test_recall_denominators_and_incremental_union(self):
        truth = {"u": ["A", "B", "C"], "v": ["D"], "w": ["E"]}
        history = {"u": {"A": 1}, "w": {"E": 1}}
        direct = {"u": ["A", "B", "C"], "v": [], "w": ["E"]}
        unseen = {"u": ["B", "C"], "v": [], "w": []}
        r = retrieval_metrics(truth, history, direct, unseen)["20"]
        self.assertEqual(r["all_ranking_all_targets"]["hits"], 4)
        self.assertAlmostEqual(r["all_ranking_all_targets"]["micro"], 4 / 5)
        absent = r["unseen_ranking_absent_targets"]
        self.assertEqual(
            (
                absent["users_with_targets"],
                absent["users_without_targets"],
                absent["target_items"],
            ),
            (2, 1, 3),
        )
        self.assertAlmostEqual(absent["macro_conditional"], 0.5)
        self.assertAlmostEqual(absent["macro_cohort_zero_for_no_targets"], 1 / 3)
        self.assertAlmostEqual(absent["micro"], 2 / 3)
        self.assertEqual(
            r["union_with_personal_history"]["additional_relevant_items"], 2
        )
        self.assertEqual(r["union_with_personal_history"]["union_hits"], 4)
        self.assertEqual(r["union_with_personal_history"]["base_hits"], 2)

    def test_post_cutoff_segments_cannot_change_model_or_profile(self):
        with tempfile.TemporaryDirectory() as directory:
            db = Path(directory) / "segments.sqlite"
            with sqlite3.connect(db) as connection:
                connection.execute("CREATE TABLE segments(u,a,item,s,e,d)")
                connection.executemany(
                    "INSERT INTO segments VALUES (?,?,?,?,?,?)",
                    [(str(u), a, a, 0, 50, 100) for u in range(3) for a in ["A", "B"]],
                )
            before = personal_counts(db, 0, 50, thresholds=(0.5,))[0.5]
            with sqlite3.connect(db) as connection:
                connection.execute("UPDATE segments SET e=500")
                connection.execute(
                    "INSERT INTO segments VALUES ('future','C','C',51,151,100)"
                )
            after = personal_counts(db, 0, 50, thresholds=(0.5,))[0.5]
            self.assertEqual(before, after)
            self.assertEqual(fit_item_item(before)[:2], fit_item_item(after)[:2])
