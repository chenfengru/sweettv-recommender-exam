import sqlite3
import tempfile
import unittest
from pathlib import Path
from src.personal_ties import latest_qualified_viewing, personal_order, tie_diagnostics


class PersonalTieTests(unittest.TestCase):
    def test_latest_changes_only_equal_count_order_and_preserves_higher_counts(self):
        c = {"H": 5, "A": 3, "B": 3, "L": 2}
        items = set(c)
        self.assertEqual(
            personal_order(c, items, "latest", {"H": 1, "A": 20, "B": 30, "L": 1000}),
            ["H", "B", "A", "L"],
        )
        self.assertEqual(personal_order(c, items, "original"), ["H", "A", "B", "L"])
        self.assertEqual(
            personal_order(c, items, "latest", dict.fromkeys(c, 10)),
            ["H", "A", "B", "L"],
        )

    def test_popularity_uses_both_global_keys_then_id_only_inside_count_ties(self):
        c = {"H": 5, "A": 3, "B": 3, "C": 3, "D": 3, "L": 2}
        order = personal_order(
            c,
            set(c),
            "popularity",
            viewers={"A": 2, "B": 2, "C": 1, "D": 2, "L": 999},
            total={"A": 10, "B": 11, "C": 999, "D": 11, "L": 9999},
        )
        self.assertEqual(order, ["H", "B", "D", "A", "C", "L"])

    def test_latest_uses_clipped_observed_ends_not_broadcast_or_future_segments(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "segments.sqlite"
            db = sqlite3.connect(p)
            db.execute(
                "CREATE TABLE segments(u TEXT,a TEXT,item TEXT,s REAL,e REAL,d REAL)"
            )
            # An opaque airing ID: latest extraction has no need to parse a future airing end.
            db.execute(
                "INSERT INTO segments VALUES(?,?,?,?,?,?)",
                ("u", "airing-A-end-is-future", "A", 0, 80, 100),
            )
            db.commit()
            before = latest_qualified_viewing(p, 80)
            db.execute("UPDATE segments SET e=150")
            db.execute(
                "INSERT INTO segments VALUES(?,?,?,?,?,?)",
                ("u", "future", "A", 81, 200, 100),
            )
            db.execute(
                "INSERT INTO segments VALUES(?,?,?,?,?,?)",
                ("future-user", "future", "B", 90, 190, 100),
            )
            db.commit()
            after = latest_qualified_viewing(p, 80)
            db.close()
            self.assertEqual(before, after)
            self.assertEqual(after, ({"u": {"A": 1}}, {"u": {"A": 80.0}}))
            self.assertEqual(
                personal_order(
                    {"A": 1, "B": 1},
                    {"A", "B"},
                    "latest",
                    {"A": after[1]["u"]["A"], "B": 79},
                ),
                ["A", "B"],
            )

    def test_boundary_group_sizes_are_distinct_from_internal_order_ties(self):
        q = {
            "u": {"A": 8, "B": 7, "C": 6, "D": 2, "E": 2, "F": 2},
            "v": {"A": 5, "B": 4, "C": 3, "D": 2, "E": 1, "F": 1},
        }
        r = tie_diagnostics(q, {"A", "B", "C", "D", "E", "F"}, ["u", "v"])
        self.assertEqual(r["users_with_equal_counts_within_selected_direct_top5"], 1)
        self.assertEqual(r["users_with_count_tie_crossing_fifth_position"], 2)
        self.assertEqual(r["boundary_full_group_size_histogram"], {"2": 1, "3": 1})
        self.assertEqual(
            r["boundary_group_joint_histogram"][1],
            {
                "full_group_size": 3,
                "inside_original_top5": 2,
                "outside_original_top5": 1,
                "users": 1,
            },
        )


if __name__ == "__main__":
    unittest.main()
