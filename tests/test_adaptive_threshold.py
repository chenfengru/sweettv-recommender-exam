import unittest
import sqlite3
import tempfile
from pathlib import Path
from src.personal_threshold import personal_counts
from src.adaptive_threshold import (
    adaptation_eligible,
    h80_from_records,
    select_counts,
    adaptive_predictions,
)
from src.fifth_replacement import fifth_replacement


class AdaptiveThresholdTests(unittest.TestCase):
    def test_existing_h80_boundaries_distinct_items_before_availability(self):
        self.assertEqual(
            [adaptation_eligible(n) for n in [0, 1, 5, 6]], [False, True, True, False]
        )
        records = [("u", str(i), 1, 1) for i in range(6)] + [
            ("u", "0", 2, 2),
            ("u", "soft_only", 1, 0),
        ]
        h80 = h80_from_records(records)
        self.assertEqual(h80["u"], 6)
        self.assertFalse(adaptation_eligible(h80["u"]))
        # Only one item might be available; group assignment has no availability input.
        self.assertTrue(adaptation_eligible(len({"0"})))

    def test_training_assignment_selects_counts_and_preserves_outside_predictions(self):
        h80 = {"cold": 0, "low": 1, "edge": 5, "dense": 6}
        n50 = {u: {"A": 1} for u in h80}
        lower = {u: {"A": 1, "B": 1} for u in h80}
        for u in ["cold", "dense"]:
            self.assertEqual(select_counts(u, n50, lower, h80), n50[u])
        for u in ["low", "edge"]:
            self.assertEqual(select_counts(u, n50, lower, h80), lower[u])
        base = {u: ["A", "C", "D", "E", "F"] for u in h80}
        new = {u: ["B", "C", "D", "E", "F"] for u in h80}
        pred = adaptive_predictions(base, new, h80)
        self.assertEqual(pred["cold"], base["cold"])
        self.assertEqual(pred["dense"], base["dense"])
        self.assertEqual(pred["low"], new["low"])
        self.assertEqual(pred["edge"], new["edge"])
        # Validation targets never enter assignment, count choice or list selection.

    def test_h80_training_group_is_unchanged_by_future_qualified_views(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "segments.sqlite"
            with sqlite3.connect(path) as connection:
                connection.execute("CREATE TABLE segments(u,a,item,s,e,d)")
                connection.execute("INSERT INTO segments VALUES ('u','A','A',0,80,100)")

            def assignment():
                counts = personal_counts(path, 0, 100, thresholds=(0.8,))[0.8]
                records = [
                    (u, item, 0, n)
                    for u, row in counts.items()
                    for item, n in row.items()
                ]
                return h80_from_records(records)

            before = assignment()
            with sqlite3.connect(path) as connection:
                connection.executemany(
                    "INSERT INTO segments VALUES (?,?,?,?,?,?)",
                    [("u", str(i), str(i), 101, 201, 100) for i in range(6)],
                )
            self.assertEqual(before, assignment())
            self.assertTrue(adaptation_eligible(assignment()["u"]))

    def test_original_n50_e2_eligibility_and_unseen_are_not_lower_threshold_counts(
        self,
    ):
        parent = ["A", "B", "C", "D", "E"]
        pool = set(parent) | {"X", "Y"}
        n50 = {"D": 1, "E": 1}
        lower = {"D": 2, "E": 3, "X": 1}
        pred, flags = fifth_replacement(parent, n50, ["A", "E", "X", "Y"], pool, "E2")
        self.assertTrue(flags["replaced"])
        self.assertEqual(pred, parent[:4] + ["X"])
        self.assertFalse(
            fifth_replacement(parent, lower, ["X", "Y"], pool, "E2")[1]["eligible"]
        )
        # A lower-qualified fifth without N50 history must not trigger E2.
        n50.pop("E")
        self.assertFalse(
            fifth_replacement(parent, n50, ["Y"], pool, "E2")[1]["eligible"]
        )
