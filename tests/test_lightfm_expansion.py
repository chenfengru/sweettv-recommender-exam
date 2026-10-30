import json
import tempfile
import unittest
from pathlib import Path
import numpy as np
from src.lightfm_expansion import expand_candidates, restore_lightfm, lightfm_ranking
from src.lightfm_features import (
    fit_lightfm,
    pair_features,
    predictive_hash,
    append_features,
)
from src.reranker_features import user_features, FEATURES, candidate_labels
from src.schedule_features import augment


class LightFMExpansionTests(unittest.TestCase):
    def test_unseen_top50_is_selected_before_union_not_fifty_unique_additions(self):
        original = [f"OLD{i:02}" for i in range(50)]
        ranked = ["SEEN"] + original + ["NEW_AFTER_50"]
        expanded, selected = expand_candidates(original, ranked, {"SEEN": 1}, True)
        self.assertEqual(selected, original)
        self.assertEqual(set(expanded), set(original))
        self.assertNotIn("NEW_AFTER_50", expanded)

    def test_dedup_unsupported_users_and_no_label_injection(self):
        original = ["A", "A", "B"]
        ranking = ["SEEN", "A", "C", "D"]
        expanded, selected = expand_candidates(original, ranking, {"SEEN": 1}, True)
        self.assertEqual(expanded, ["A", "B", "C", "D"])
        self.assertEqual(selected, ["A", "C", "D"])
        unchanged, empty = expand_candidates(original, ranking, {}, False)
        self.assertEqual(unchanged, ["A", "B"])
        self.assertEqual(empty, [])
        labels = candidate_labels(["u"], [expanded], {"u": ["FUTURE_ONLY"]})
        self.assertEqual(labels.tolist(), [0] * 4)
        self.assertNotIn("FUTURE_ONLY", expanded)

    def test_cached_predictive_state_restoration_is_exact(self):
        bundle = fit_lightfm(
            {"u": {"A": 1, "B": 1}, "v": {"B": 1, "C": 1}, "w": {"A": 1, "C": 1}}
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            (path / "mappings.json").write_text(json.dumps(bundle["mappings"]))
            np.savez(
                path / "lightfm_predictive_arrays.npz",
                **{
                    k: getattr(bundle["model"], k)
                    for k in [
                        "user_embeddings",
                        "item_embeddings",
                        "user_biases",
                        "item_biases",
                    ]
                },
            )
            restored = restore_lightfm(path, predictive_hash(bundle["model"]))
            before, _ = pair_features(bundle, ["u"], [["A", "B", "C"]], {"A", "B", "C"})
            after, _ = pair_features(
                restored, ["u"], [["A", "B", "C"]], {"A", "B", "C"}
            )
            self.assertTrue(np.array_equal(before, after))
            self.assertEqual(
                lightfm_ranking(bundle, "u", {"A", "B", "C"}),
                lightfm_ranking(restored, "u", {"A", "B", "C"}),
            )
            self.assertEqual(lightfm_ranking(restored, "unknown", {"A", "B", "C"}), [])

    def test_original_rows_equal_and_new_rows_have_complete_same40_features(self):
        history = {
            "counts": {
                0.3: {"u": {"A": 2, "X": 3}},
                0.5: {"u": {"A": 1}},
                0.8: {"u": {"A": 1}},
            },
            "latest": {"u": {"A": 900}},
            "rolling": {7: {"u": {"A": 1}}, 28: {"u": {"A": 1}}},
            "cutoff": 1000,
            "known_users": {"u"},
        }
        pool = set("ABCDEXY")
        fallback = list("ABCDE")
        neighbours = {"A": [("Y", 0.4)]}
        old_items, old27 = user_features(
            "u", history, neighbours, pool, {"X": 2}, {"X": 2}, fallback
        )
        expanded_items = sorted(set(old_items) | {"X"})
        items, new27 = user_features(
            "u",
            history,
            neighbours,
            pool,
            {"X": 2},
            {"X": 2},
            fallback,
            candidate_items=expanded_items,
        )
        schedule = {it: [0, 1, 0, 100, 1, 2, 1] for it in pool}
        old34, _ = augment(old27, [old_items], schedule)
        new34, _ = augment(new27, [items], schedule)
        bundle = fit_lightfm(
            {"u": {"A": 1}, "v": {"X": 1, "B": 1}, "w": {"Y": 1, "C": 1}}
        )
        old6, _ = pair_features(bundle, ["u"], [old_items], pool)
        new6, _ = pair_features(bundle, ["u"], [items], pool)
        old40 = append_features(old34, old6)
        new40 = append_features(new34, new6)
        self.assertEqual(new40.shape[1], 40)
        for i, it in enumerate(old_items):
            self.assertTrue(np.array_equal(old40[i], new40[items.index(it)]))
        row = dict(zip(FEATURES, new40[items.index("X"), :27]))
        self.assertEqual(row["n30"], 3)
        self.assertEqual(row["n50"], 0)
        self.assertEqual(row["n80"], 0)
        self.assertEqual(row["personal_rank_missing"], 1)
        self.assertEqual(row["last_n50_view_missing"], 1)
        self.assertEqual(
            [
                row[k]
                for k in ["source_personal200", "source_unseen50", "source_global5"]
            ],
            [0, 0, 0],
        )
        self.assertTrue(np.isfinite(new40).all())
