import unittest
from src.fifth_replacement import fifth_replacement


class FifthReplacementTests(unittest.TestCase):
    def setUp(self):
        self.base = ["A", "B", "C", "D", "E"]
        self.pool = set(self.base) | {"X", "Y", "SEEN"}

    def test_exact_count_eligibility_for_e1_and_e2(self):
        counts = {"A": 3, "B": 2, "C": 2, "D": 2, "E": 1}
        pred, info = fifth_replacement(self.base, counts, ["X"], self.pool, "E1")
        self.assertTrue(info["replaced"])
        self.assertEqual(pred, self.base[:4] + ["X"])
        self.assertFalse(
            fifth_replacement(self.base, counts, ["X"], self.pool, "E2")[1]["eligible"]
        )
        counts["D"] = 1
        self.assertTrue(
            fifth_replacement(self.base, counts, ["X"], self.pool, "E2")[1]["eligible"]
        )
        counts["E"] = 2
        self.assertFalse(
            fifth_replacement(self.base, counts, ["X"], self.pool, "E1")[1]["eligible"]
        )
        counts.pop("E")
        self.assertFalse(
            fifth_replacement(self.base, counts, ["X"], self.pool, "E1")[1]["eligible"]
        )

    def test_e3_available_history_and_fallback_provenance(self):
        counts = {"A": 2, "B": 1, "C": 1, "D": 1, "OFF_SCHEDULE": 8}
        pred, info = fifth_replacement(self.base, counts, ["X"], self.pool, "E3")
        self.assertTrue(info["fifth_from_fallback"])
        self.assertTrue(info["replaced"])
        self.assertEqual(pred[:4], self.base[:4])
        counts["E"] = 1
        self.assertFalse(
            fifth_replacement(self.base, counts, ["X"], self.pool, "E3")[1]["eligible"]
        )

    def test_original_entire_top5_exclusion_and_deterministic_choice(self):
        counts = {"E": 1, "SEEN": 3}
        ranking = ["A", "E", "OFF_SCHEDULE", "SEEN", "Y", "X"]
        pred, info = fifth_replacement(self.base, counts, ranking, self.pool, "E1")
        self.assertEqual(pred, self.base[:4] + ["Y"])
        self.assertTrue(info["replaced"])
        self.assertEqual(
            fifth_replacement(self.base, counts, ranking, self.pool, "E1")[0], pred
        )

    def test_missing_or_beyond_top50_candidate_preserves_full_list(self):
        counts = {"E": 1}
        for ranking in [[], self.base, ["A"] * 50 + ["X"]]:
            pred, info = fifth_replacement(self.base, counts, ranking, self.pool, "E1")
            self.assertEqual(pred, self.base)
            self.assertFalse(info["replaced"])
            self.assertTrue(info["eligible"])
        pred, info = fifth_replacement(self.base, {"E": 2}, ["X"], self.pool, "E1")
        self.assertEqual(pred, self.base)
        self.assertTrue(info["has_available_replacement"])
        self.assertFalse(info["eligible"])
