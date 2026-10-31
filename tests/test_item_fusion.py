import unittest
from fractions import Fraction
from src.item_fusion import fusion_scores, fusion_order, seen_unseen_effects
from src.improvement_helpers import complete


class ItemFusionTests(unittest.TestCase):
    def test_arithmetic_missing_ranks_deduplication_and_direct_limit(self):
        personal = ["A", "A", "B"] + [f"P{i}" for i in range(49)]
        scores = fusion_scores(personal, ["B", "B", "C"], 0.1, set(personal) | {"C"})
        self.assertEqual(scores["A"], Fraction(1, 61))
        self.assertEqual(scores["B"], Fraction(1, 62) + Fraction(1, 610))
        self.assertEqual(scores["C"], Fraction(1, 620))
        self.assertNotIn("P48", scores)
        self.assertEqual(fusion_scores([], [], 0.05, {"A"}), {})
        extended = fusion_scores(
            personal + ["future_ignored"],
            ["B", "C"],
            0.1,
            set(personal) | {"C", "future_ignored"},
        )
        self.assertEqual(scores, extended)

    def test_exact_mathematical_ties_use_global_keys_then_raw_string(self):
        personal = ["P1", "A", "B"]
        alternative = [f"I{i}" for i in range(1, 34)]
        alternative[2] = "B"
        alternative[32] = "A"
        candidates = set(personal) | set(alternative)
        scores = fusion_scores(personal, alternative, 0.05, candidates)
        self.assertEqual(scores["A"], scores["B"])
        rank = fusion_order(
            personal, alternative, 0.05, candidates, {"B": 2, "A": 1}, {}
        )
        self.assertLess(rank.index("B"), rank.index("A"))
        rank = fusion_order(
            personal, alternative, 0.05, candidates, {}, {"A": 2, "B": 1}
        )
        self.assertLess(rank.index("A"), rank.index("B"))
        rank = fusion_order(personal, alternative, 0.05, candidates, {}, {})
        self.assertLess(rank.index("A"), rank.index("B"))

    def test_fixed_weights_cannot_promote_alternative_only_above_personal_top50(self):
        personal = [f"P{i}" for i in range(50)]
        candidates = set(personal) | {"NEW"}
        for weight in [0.05, 0.10, 0.20]:
            order = fusion_order(personal, ["NEW"], weight, candidates, {}, {})
            self.assertEqual(order[-1], "NEW")
            self.assertEqual(set(order[:5]), set(personal[:5]))

    def test_empty_sources_use_existing_fallback_completion(self):
        fallback = ["2", "10", "A", "B", "C"]
        order = fusion_order([], [], 0.2, set(fallback), {}, {})
        prediction, size = complete(order, fallback, set(fallback))
        self.assertEqual(prediction, fallback)
        self.assertEqual(size, 0)

    def test_seen_unseen_hits_and_ap_attribution(self):
        truth = {"u": ["A", "X"]}
        history = {"u": {"A": 1, "B": 1}}
        baseline = {"u": ["A", "B", "C", "D", "E"]}
        fused = {"u": ["X", "A", "B", "C", "D"]}
        r = seen_unseen_effects(truth, fused, baseline, history)
        self.assertEqual(r["entering_unseen_items"], 1)
        self.assertEqual(r["entering_unseen_relevant_hits"], 1)
        self.assertEqual(r["leaving_unseen_items"], 1)
        self.assertEqual(r["baseline_seen_map_contribution"], 0.5)
        self.assertEqual(r["fused_seen_map_contribution"], 0.5)
        self.assertEqual(r["fused_unseen_map_contribution"], 0.5)
