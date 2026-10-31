import copy
import unittest
import numpy as np
from src.seed_ensemble import predictive_tree_hash, vector_diversity, equal_score_mean


class SeedEnsembleTests(unittest.TestCase):
    def test_predictive_hash_ignores_seeds_counts_and_gains_not_leaf_values(self):
        class Model:
            def __init__(self, d):
                self.d = d

            def dump_model(self):
                return self.d

        tree = {
            "split_feature": 0,
            "threshold": 0.5,
            "decision_type": "<=",
            "default_left": True,
            "missing_type": "None",
            "split_gain": 3.0,
            "left_child": {"leaf_value": -0.2, "leaf_count": 8},
            "right_child": {"leaf_value": 0.4, "leaf_count": 5},
        }
        d = {
            "feature_names": ["x"],
            "num_tree_per_iteration": 1,
            "objective": "binary",
            "seed": 42,
            "tree_info": [{"tree_structure": tree}],
        }
        different = copy.deepcopy(d)
        different["seed"] = 43
        different["tree_info"][0]["tree_structure"]["split_gain"] = 5
        self.assertEqual(
            predictive_tree_hash(Model(d)), predictive_tree_hash(Model(different))
        )
        different["tree_info"][0]["tree_structure"]["right_child"]["leaf_value"] = 0.41
        self.assertNotEqual(
            predictive_tree_hash(Model(d)), predictive_tree_hash(Model(different))
        )

    def test_diversity_gate_uses_scores_not_model_metadata(self):
        a = np.array([0.1, 0.2, 0.3])
        same = vector_diversity(a, a.copy())
        self.assertTrue(same["bitwise_identical"])
        b = a.copy()
        b[1] = np.nextafter(b[1], 1.0)
        self.assertFalse(vector_diversity(b, a)["bitwise_identical"])
        self.assertEqual(vector_diversity(b, a)["different_scores"], 1)

    def test_exactly_four_equal_weights_and_alignment(self):
        arrays = [np.array([i, i + 1.0]) for i in range(4)]
        np.testing.assert_array_equal(equal_score_mean(arrays), [1.5, 2.5])
        with self.assertRaises(ValueError):
            equal_score_mean(arrays[:3])
        with self.assertRaises(ValueError):
            equal_score_mean(arrays[:3] + [np.array([1.0])])
