import math
import sqlite3
import tempfile
import unittest
from pathlib import Path
import numpy as np
from src.item_affinity import (
    affinity_rows,
    append_affinities,
    scalar_reference,
    FEATURES,
)
from src.item_item import fit_item_item
from src.personal_threshold import personal_counts


class ItemAffinityTests(unittest.TestCase):
    def test_self_exclusion_distinct_sources_and_unweighted_top_five(self):
        graph = {str(i): [("candidate", i / 10)] for i in range(1, 7)}
        graph["candidate"] = [("candidate", 999.0)]
        history = ["1", "2", "3", "4", "5", "6", "1", "candidate"]
        actual = affinity_rows(history, ["candidate", "unsupported"], graph)
        np.testing.assert_allclose(actual[0], [0.6, 2.0, math.log1p(6)], rtol=1e-7)
        np.testing.assert_array_equal(actual[1], [0, 0, 0])
        np.testing.assert_allclose(
            actual[0], scalar_reference(history, "candidate", graph), rtol=1e-7
        )

    def test_directed_history_to_candidate_not_reverse(self):
        graph = {"A": [("B", 0.3)], "B": [("C", 0.7)]}
        np.testing.assert_allclose(
            affinity_rows(["A"], ["B"], graph)[0], [0.3, 0.3, math.log(2)], rtol=1e-7
        )
        np.testing.assert_array_equal(affinity_rows(["B"], ["A"], graph), [[0, 0, 0]])
        np.testing.assert_array_equal(
            affinity_rows(["B"], ["B"], {"B": [("B", 1.0)]}), [[0, 0, 0]]
        )
        np.testing.assert_array_equal(affinity_rows([], ["A"], graph), [[0, 0, 0]])

    def test_original52_alignment_and_no_frequency_weighting(self):
        base = np.arange(104, dtype=np.float32).reshape(2, 52)
        users = ["u"]
        items = [["B", "C"]]
        graph = {"A": [("B", 0.4), ("C", 0.2)]}
        x, extra = append_affinities(base, users, items, {"u": {"A": 1}}, graph)
        x2, extra2 = append_affinities(base, users, items, {"u": {"A": 100}}, graph)
        np.testing.assert_array_equal(extra, extra2)
        np.testing.assert_array_equal(x[:, :52], base)
        self.assertEqual(x.shape, (2, 55))
        self.assertEqual(len(FEATURES), 3)
        self.assertTrue(np.isfinite(x).all())
        with self.assertRaises(ValueError):
            append_affinities(base[:, :51], users, items, {"u": {"A": 1}}, graph)

    def test_post_cutoff_counts_and_graph_invariance(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "segments.sqlite"
            with sqlite3.connect(path) as db:
                db.execute(
                    "CREATE TABLE segments(u TEXT,a TEXT,item TEXT,s REAL,e REAL,d REAL)"
                )
                db.executemany(
                    "INSERT INTO segments VALUES(?,?,?,?,?,?)",
                    [
                        (u, it, it, 0, 100, 100)
                        for u in ["u", "v", "w"]
                        for it in ["A", "B"]
                    ],
                )
            before = personal_counts(path, 0, 100, thresholds=(0.5,))[0.5]
            g1, _, _ = fit_item_item(before)
            with sqlite3.connect(path) as db:
                db.execute("UPDATE segments SET e=200")
                db.executemany(
                    "INSERT INTO segments VALUES(?,?,?,?,?,?)",
                    [(u, "future", "F", 100, 200, 100) for u in ["u", "v", "w"]],
                )
            after = personal_counts(path, 0, 100, thresholds=(0.5,))[0.5]
            g2, _, _ = fit_item_item(after)
            self.assertEqual(before, after)
            self.assertEqual(g1, g2)
            np.testing.assert_array_equal(
                affinity_rows(before["u"], ["A", "B", "F"], g1),
                affinity_rows(after["u"], ["A", "B", "F"], g2),
            )
