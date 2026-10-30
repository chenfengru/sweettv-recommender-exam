import json
import unittest
from src.personal_threshold import predict
from src.personal_ties import global_qualified_statistics, personal_order
from src.viewing_strength import strength_counts, retrieval_diagnostics


class ViewingStrengthTests(unittest.TestCase):
    def test_additional_n80_contribution_and_scaled_integer_ranking(self):
        n50 = {"u": {"A": 2, "B": 1, "10": 1, "2": 1}}
        n80 = {"u": {"B": 1}}
        viewers = {"B": 2}
        total = {"B": 2}
        scores05 = strength_counts(n50, n80, "L05")
        scores10 = strength_counts(n50, n80, "L10")
        self.assertEqual(scores05["u"], {"A": 4, "B": 3, "10": 2, "2": 2})
        self.assertEqual(scores10["u"], {"A": 2, "B": 2, "10": 1, "2": 1})
        self.assertTrue(
            all(type(x) is int for c in scores05.values() for x in c.values())
        )
        rank = lambda scores: personal_order(
            scores["u"],
            set(n50["u"]),
            variant="popularity",
            viewers=viewers,
            total=total,
        )
        self.assertEqual(rank(scores05), ["A", "B", "10", "2"])
        self.assertEqual(rank(scores10), ["B", "A", "10", "2"])
        self.assertEqual(strength_counts(n50, n80, "v5"), n50)

    def test_weighting_preserves_truth_globals_fallback_slices_and_membership(self):
        records = [("u", "A", 1, 1), ("v", "A", 1, 1), ("u", "B", 0.5, 0)]
        viewers, total = global_qualified_statistics(records)
        fallback = ["A", "B", "C", "D", "E"]
        truth = {"u": ["A"]}
        slices = {"u": "1–5"}
        n50 = {"u": {"A": 1, "B": 2}}
        n80 = {"u": {"A": 1}}
        snapshot = json.dumps(
            [truth, viewers, total, fallback, slices, n50, n80], sort_keys=True
        )
        base, _ = predict(n50, set(fallback), viewers, total, fallback, ["u"])
        weighted, _ = predict(
            strength_counts(n50, n80, "L10"),
            set(fallback),
            viewers,
            total,
            fallback,
            ["u"],
        )
        self.assertEqual(base["u"][:2], ["B", "A"])
        self.assertEqual(weighted["u"][:2], ["A", "B"])
        self.assertEqual(set(base["u"]), set(weighted["u"]))
        self.assertEqual(
            snapshot,
            json.dumps(
                [truth, viewers, total, fallback, slices, n50, n80], sort_keys=True
            ),
        )

    def test_hand_computable_oracle_and_all_rank_buckets(self):
        n50 = {"u": {str(i): 61 - i for i in range(1, 61)}, "v": {"X": 1}}
        candidates = set(n50["u"]) | {"X", "Y"}
        truth = {"u": ["1", "7", "23", "51", "X", "Y"], "v": ["X"]}
        r = retrieval_diagnostics(truth, n50, candidates, {}, {})
        self.assertAlmostEqual(r["macro_personal_history_recall"], (4 / 6 + 1) / 2)
        self.assertAlmostEqual(r["micro_relevant_coverage"], 5 / 7)
        self.assertEqual(
            (r["micro_relevant_covered"], r["micro_relevant_total"]), (5, 7)
        )
        self.assertAlmostEqual(r["personal_history_only_oracle_map_at_5"], 0.9)
        self.assertEqual(
            r["relevant_rank_buckets"],
            {"1–5": 2, "6–20": 1, "21–50": 1, "beyond_50": 1, "absent": 2},
        )
        self.assertEqual(r["absent_with_other_users_n50"], 1)
        self.assertEqual(r["absent_without_any_n50"], 1)
