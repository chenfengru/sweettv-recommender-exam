import unittest
from src.metrics import average_precision_at_k as ap, mean_average_precision_at_k as mapk


class MetricTests(unittest.TestCase):
    def test_documented_ranking_examples(self):
        self.assertAlmostEqual(ap("ABC", "ABDCE"), 11 / 12)
        self.assertAlmostEqual(ap("ABC", "DAEBC"), 8 / 15)

    def test_duplicate_predictions_never_add_hits(self):
        self.assertAlmostEqual(ap(["A", "B"], ["A", "A", "B"]), (1 + 2 / 3) / 2)
        self.assertEqual(ap(["A", "A"], ["A", "A"]), 1)

    def test_empty_truth_short_truth_and_cutoff(self):
        self.assertEqual(ap([], ["A"]), 0)
        self.assertEqual(ap(["A"], ["X", "A"]), 0.5)
        self.assertEqual(ap(["A"], ["B", "C", "D", "E", "F", "A"]), 0)
        self.assertEqual(ap("ABCDEFG", "ABCDE"), 1)

    def test_fixed_cohort_includes_empty_truth(self):
        self.assertEqual(mapk({"a": ["A"], "b": []}, {"b": ["B"], "a": ["A"]}), 0.5)
        with self.assertRaises(ValueError):
            mapk({"a": ["A"]}, {"other": ["A"]})
        with self.assertRaises(ValueError):
            mapk({}, {})

    def test_invalid_k(self):
        for k in (0, -1, 1.5, True):
            with self.assertRaises(ValueError):
                ap("A", "A", k)


if __name__ == "__main__":
    unittest.main()
