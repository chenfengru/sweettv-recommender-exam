import sqlite3
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
import numpy as np
from src.lightfm_features import (
    binary_interactions,
    fit_lightfm,
    predictive_hash,
    pair_features,
    append_features,
    FULL_FEATURES,
)
from src.personal_threshold import personal_counts


class LightFMFeatureTests(unittest.TestCase):
    def test_deterministic_positive_only_mappings_binary_and_training_replay(self):
        counts = {
            "2": {"20": 8, "10": 1, "empty": 0},
            "10": {"2": 1, "20": 1},
            "0": {},
            "30": {"10": 1, "2": 1},
        }
        matrix, users, items, _, _ = binary_interactions(counts)
        self.assertEqual(users, ["10", "2", "30"])
        self.assertEqual(items, ["10", "2", "20"])
        self.assertTrue(np.all(matrix.data == 1))
        self.assertEqual(matrix.nnz, 6)
        first = fit_lightfm(counts)
        second = fit_lightfm(dict(reversed(list(counts.items()))))
        self.assertEqual(first["mappings"], second["mappings"])
        self.assertEqual(
            predictive_hash(first["model"]), predictive_hash(second["model"])
        )
        self.assertEqual(first["report"]["epochs"], 15)
        self.assertEqual(first["report"]["num_threads"], 1)

    def fake(self):
        class Model:
            def predict(self, u, items, num_threads):
                self_test.assertEqual(num_threads, 1)
                return np.asarray([5, 5, 1], dtype=np.float32)[items]

        self_test = self
        return {
            "model": Model(),
            "user_index": {"known": 0},
            "item_index": {"10": 0, "2": 1, "C": 2},
            "user_biases": np.asarray([0.7]),
            "item_biases": np.asarray([0.1, 0.2, 0.3]),
        }

    def test_support_aware_biases_score_rank_and_all_available_raw_ties(self):
        bundle = self.fake()
        available = {"10", "2", "C", "NEW"}
        x, r = pair_features(
            bundle, ["known", "cold"], [["C", "NEW"], ["2", "NEW"]], available
        )
        self.assertEqual(
            x[0, 1], 3
        )  # Rank among all supported available items, not two candidate rows.
        self.assertEqual(x[1, :2].tolist(), [0, 0])
        self.assertAlmostEqual(x[1, 2], 0.7, places=6)
        self.assertEqual(x[1, 3], 0)
        self.assertEqual(x[1, 4:].tolist(), [0, 1])
        self.assertEqual(x[2, :3].tolist(), [0, 0, 0])
        self.assertAlmostEqual(x[2, 3], 0.2, places=6)
        self.assertEqual(x[3].tolist(), [0, 0, 0, 0, 1, 1])
        ties, _ = pair_features(bundle, ["known"], [["2", "10"]], available)
        self.assertEqual(ties[:, 1].tolist(), [2, 1])

    def test_append_exactly_six_aligned_columns(self):
        base = np.arange(68, dtype=np.float32).reshape(2, 34)
        extra = np.arange(12, dtype=np.float32).reshape(2, 6)
        x = append_features(base, extra)
        self.assertEqual(x.shape, (2, 40))
        self.assertEqual(len(FULL_FEATURES), 40)
        self.assertTrue(np.array_equal(x[:, :34], base))
        self.assertTrue(np.array_equal(x[:, 34:], extra))
        with self.assertRaises(ValueError):
            append_features(base, extra[:1])

    def test_post_cutoff_behaviour_cannot_change_binary_support_or_mapping(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "segments.sqlite"
            with sqlite3.connect(path) as db:
                db.execute("CREATE TABLE segments(u,a,item,s,e,d)")
                db.execute("INSERT INTO segments VALUES ('u','a','A',0,50,100)")
            before = personal_counts(path, 0, 50, thresholds=(0.5,))[0.5]
            with sqlite3.connect(path) as db:
                db.execute("UPDATE segments SET e=1000")
                db.execute("INSERT INTO segments VALUES ('future','b','B',51,151,100)")
            after = personal_counts(path, 0, 50, thresholds=(0.5,))[0.5]
            self.assertEqual(before, after)
            b, u, i, _, _ = binary_interactions(before)
            a, uu, ii, _, _ = binary_interactions(after)
            self.assertEqual((u, i), (uu, ii))
            self.assertEqual((b != a).nnz, 0)
