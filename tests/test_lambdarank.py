import unittest
import numpy as np
from src.lambdarank_queries import query_layout, rank_raw_candidates, ndcg_at_five
from src.lightfm_features import FULL_FEATURES
from src.experiment_lambdarank import infer
from types import SimpleNamespace
from pathlib import Path
import tempfile


class LambdaRankTests(unittest.TestCase):
    def test_origin_user_separation_contiguity_and_alignment(self):
        meta = {
            "users": ["u", "v"],
            "items": [["A", "B"], ["A", "C", "D"]],
            "offsets": [0, 2, 5],
        }
        y = np.array([1, 0, 0, 0, 0])
        x = np.arange(200).reshape(5, 40)
        keys1, g1, s1 = query_layout("apr6", meta, y)
        keys2, g2, s2 = query_layout("apr20", meta, y)
        self.assertEqual(len(set(keys1 + keys2)), 4)
        self.assertEqual((keys1 + keys2)[2], ("apr20", "u"))
        self.assertEqual(np.concatenate([g1, g2]).tolist(), [2, 3, 2, 3])
        self.assertEqual(int(g1.sum() + g2.sum()), 10)
        self.assertEqual(s1["informative_queries"], 1)
        self.assertEqual(s1["all_negative_queries"], 1)
        self.assertEqual(s1["queries"], 2)
        for a, b in zip(meta["offsets"][:-1], meta["offsets"][1:]):
            np.testing.assert_array_equal(x[a:b, 0], np.arange(a, b) * 40)
            np.testing.assert_array_equal(y[a:b], y[np.arange(a, b)])
        with self.assertRaises(ValueError):
            query_layout("apr6", dict(meta, offsets=[0, 2, 6]), y)

    def test_uniform_queries_retained_and_binary_labels_required(self):
        meta = {
            "users": ["negative", "positive", "mixed"],
            "items": [["a", "b"]] * 3,
            "offsets": [0, 2, 4, 6],
        }
        _, g, s = query_layout("apr6", meta, np.array([0, 0, 1, 1, 1, 0]))
        self.assertEqual(g.tolist(), [2, 2, 2])
        self.assertEqual(s["uniform_label_queries"], 2)
        self.assertEqual(s["all_positive_queries"], 1)
        self.assertEqual(s["informative_queries"], 1)
        with self.assertRaises(ValueError):
            query_layout("apr6", meta, np.array([0, 0, 1, 2, 1, 0]))

    def test_raw_negative_and_greater_than_one_scores_deterministic_v14_ties(self):
        items = ["2", "10", "A", "B", "C"]
        scores = np.array([2.0, 2.0, -3.0, -3.0, -4.0])
        result, _ = rank_raw_candidates(items, scores, {}, {}, {}, set(items), items)
        self.assertEqual(result, ["10", "2", "A", "B", "C"])
        order = [4, 3, 2, 1, 0]
        replay, _ = rank_raw_candidates(
            [items[i] for i in order], scores[order], {}, {}, {}, set(items), items
        )
        self.assertEqual(replay, result)
        counts = {"2": 1}
        result, _ = rank_raw_candidates(
            items, scores, counts, {}, {}, set(items), items
        )
        self.assertEqual(result[0], "2")

    def test_inference_schema_and_raw_score_request(self):
        with tempfile.TemporaryDirectory() as tmp:

            class Fake:
                def feature_name(self):
                    return FULL_FEATURES

                def predict(self, x, **kwargs):
                    self.kwargs = kwargs
                    return np.array([3.0, 2.0, 1.0, 0.0, -1.0])

            booster = Fake()
            x = np.zeros((5, 40), dtype=np.float32)
            x[:, FULL_FEATURES.index("source_global5")] = 1
            prepared = {
                "users": ["u"],
                "items": [["A", "B", "C", "D", "E"]],
                "offsets": [0, 5],
                "x": x,
                "pool": set("ABCDE"),
                "private": Path(tmp),
            }
            pred, _, _, _ = infer(prepared, SimpleNamespace(booster_=booster), "p.json")
            self.assertTrue(booster.kwargs["raw_score"])
            self.assertEqual(pred["u"], list("ABCDE"))
            with self.assertRaises(AssertionError):
                infer(
                    dict(prepared, x=x[:, :39]),
                    SimpleNamespace(booster_=booster),
                    "bad.json",
                )

    def test_binary_ndcg_secondary_diagnostic(self):
        self.assertEqual(ndcg_at_five(["A", "B"], ["A", "B"]), 1.0)
        self.assertEqual(ndcg_at_five(["A"], ["B", "C"]), 0.0)
        self.assertAlmostEqual(ndcg_at_five(["A"], ["B", "A"]), 1 / np.log2(3))
