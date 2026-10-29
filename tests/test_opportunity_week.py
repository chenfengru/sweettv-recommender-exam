import csv
import sqlite3
import tempfile
import unittest
from pathlib import Path
from src.opportunity_week import (
    prediction_airing_counts,
    qualified_viewing_weeks,
    controlled_order,
    monday_week,
)
from src.interactions import extract_interactions
from src.personal_ties import global_qualified_statistics
from src.models import Ranker
from src.improvement_helpers import complete
from src.real_matching_audit import stamp


class OpportunityWeekTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def csv(self, name, headers, rows):
        path = self.root / name
        with path.open("w", newline="") as f:
            w = csv.writer(f)
            w.writerow(headers)
            w.writerows(rows)
        return path

    def test_canonical_airings_duplicates_channels_carryovers_and_half_open_edges(self):
        h = ["channel_id", "start_time", "duration", "tv_show_id"]
        carry = ["3", "17.05.2020 23:30:00", 7200, "A"]
        a = self.csv(
            "a.csv",
            h,
            [
                carry,
                ["3", "17.05.2020 23:00:00", 3600, "touch"],
                ["3", "18.05.2020 01:00:00", 60, "0"],
            ],
        )
        b = self.csv(
            "b.csv",
            h,
            [
                carry,
                ["4", "17.05.2020 23:30:00", 7200, "A"],
                ["3", "19.05.2020 00:00:00", 60, "end"],
                ["3", "18.05.2020 02:00:00", 0, "zero"],
                ["3", "18.05.2020 03:00:00", 60, "B"],
            ],
        )
        counts, stats = prediction_airing_counts(
            [a, b], stamp("2020-05-18"), stamp("2020-05-19")
        )
        self.assertEqual(counts, {"A": 2, "B": 1})
        self.assertEqual(stats["canonical_intersecting_airings"], 3)
        self.assertEqual(stats["duplicate_canonical_rows_beyond_first"], 1)

    def database(self, name, rows):
        path = self.root / name
        db = sqlite3.connect(path)
        db.execute(
            "CREATE TABLE segments(u TEXT,a TEXT,item TEXT,s REAL,e REAL,d REAL)"
        )
        db.executemany("INSERT INTO segments VALUES(?,?,?,?,?,?)", rows)
        db.commit()
        db.close()
        return path

    def test_week_deduplication_first_observation_and_monday_boundary(self):
        rows = []
        for aid, start in [
            ("tue", "2020-05-12 12:00:00"),
            ("fri", "2020-05-15 12:00:00"),
            ("mon", "2020-05-18 12:00:00"),
        ]:
            s = stamp(start)
            rows.append(("u", aid, "A", s, s + 100, 100))
        # Qualified longest block is Monday, but first observed 4-second segment is Sunday.
        s = stamp("2020-05-17 23:59:55")
        m = stamp("2020-05-18 00:00:00")
        rows += [
            ("u", "cross", "A", s, s + 4, 100),
            ("u", "cross", "A", m, m + 90, 100),
        ]
        p = self.database("weeks.sqlite", rows)
        q, w, _ = qualified_viewing_weeks(p, stamp("2020-05-11"), stamp("2020-05-25"))
        self.assertEqual(q, {"u": {"A": 4}})
        self.assertEqual(w, {"u": {"A": 2}})
        self.assertEqual(monday_week(stamp("2020-05-17 23:59:59")), "2020-05-11")
        self.assertEqual(monday_week(m), "2020-05-18")
        # Isolate the crossing airing to show assignment is its first segment's week.
        p2 = self.database("cross.sqlite", rows[-2:])
        _, _, stats = qualified_viewing_weeks(
            p2, stamp("2020-05-11"), stamp("2020-05-25")
        )
        self.assertEqual(stats["first_observed_start_min"], s)
        p3 = self.database("same-week.sqlite", [rows[0]] + rows[-2:])
        q3, w3, _ = qualified_viewing_weeks(
            p3, stamp("2020-05-11"), stamp("2020-05-25")
        )
        self.assertEqual(q3, {"u": {"A": 2}})
        self.assertEqual(w3, {"u": {"A": 1}})

    def test_primary_count_precedence_and_v3_keys_after_new_feature_ties(self):
        counts = {"H": 7, "A": 6, "B": 6, "C": 6, "L": 5}
        viewers = {"A": 10, "B": 8, "C": 100, "L": 999}
        total = {"A": 11, "B": 12, "C": 999, "L": 9999}
        self.assertEqual(
            controlled_order(
                counts,
                set(counts),
                viewers,
                total,
                "C",
                airings={"H": 1, "A": 3, "B": 3, "C": 4, "L": 999},
            ),
            ["H", "C", "A", "B", "L"],
        )
        self.assertEqual(
            controlled_order(
                counts,
                set(counts),
                viewers,
                total,
                "D",
                weeks={"H": 1, "A": 2, "B": 2, "C": 3, "L": 5},
            ),
            ["H", "C", "A", "B", "L"],
        )
        self.assertEqual(
            controlled_order(
                {"A": 2, "B": 2}, {"A", "B"}, {}, {}, "C", airings={"A": 1, "B": 1}
            ),
            ["A", "B"],
        )

    def test_week_cutoff_clipping_and_future_only_rows_do_not_change_features(self):
        before = self.database(
            "before.sqlite", [("u", "opaque-future-broadcast", "A", 0, 80, 100)]
        )
        after = self.database(
            "after.sqlite",
            [
                ("u", "opaque-future-broadcast", "A", 0, 180, 100),
                ("u", "future", "A", 81, 181, 100),
                ("future-user", "future", "B", 90, 190, 100),
            ],
        )
        a = qualified_viewing_weeks(before, 0, 80)
        b = qualified_viewing_weeks(after, 0, 80)
        self.assertEqual(a, b)
        self.assertEqual(a[0], {"u": {"A": 1}})

    def test_end_to_end_both_variants_ignore_future_viewing(self):
        start, cutoff, end = map(stamp, ["2020-05-11", "2020-05-18", "2020-05-25"])
        h = ["channel_id", "start_time", "duration", "tv_show_id"]
        schedule = [
            ["3", "17.05.2020 23:00:00", 4200, "A"],
            ["3", "17.05.2020 14:00:00", 3600, "B"],
        ]
        schedule += [
            ["3", f"18.05.2020 {14+i:02d}:00:00", 3600, it]
            for i, it in enumerate(["B", "C", "D", "E", "F"])
        ]
        path = self.csv("schedule.csv", h, schedule)
        vh = ["user_id", "vsetv_id", "start_time", "stop_time", "duraton"]
        common = [["u", "3", "2020-05-17 14:00:00", "2020-05-17 15:00:00", 3600]]
        before = self.csv(
            "views_before.csv",
            vh,
            common + [["u", "3", "2020-05-17 23:00:00", "2020-05-18 00:10:00", 4200]],
        )
        changed_end = stamp("2020-05-20 00:10:00")
        after = self.csv(
            "views_after.csv",
            vh,
            common
            + [
                [
                    "u",
                    "3",
                    "2020-05-17 23:00:00",
                    "2020-05-20 00:10:00",
                    int(changed_end - stamp("2020-05-17 23:00:00")),
                ],
                [
                    "future-user",
                    "3",
                    "2020-05-18 14:00:00",
                    "2020-05-18 15:00:00",
                    3600,
                ],
            ],
        )
        ra, _ = extract_interactions(before, [path], start, cutoff, self.root / "fit_a")
        rb, _ = extract_interactions(after, [path], start, cutoff, self.root / "fit_b")
        self.assertEqual(ra, rb)
        qa, wa, _ = qualified_viewing_weeks(
            self.root / "fit_a/segments.sqlite", start, cutoff
        )
        qb, wb, _ = qualified_viewing_weeks(
            self.root / "fit_b/segments.sqlite", start, cutoff
        )
        self.assertEqual((qa, wa), (qb, wb))
        opportunities, _ = prediction_airing_counts([path], cutoff, end)
        candidates = set(opportunities)
        viewers, total = global_qualified_statistics(ra)
        fallback = Ranker(ra, candidates, {}, "personal").fallback
        for v in ["v3", "C", "D"]:
            a = controlled_order(
                qa["u"],
                candidates,
                viewers,
                total,
                v,
                airings=opportunities,
                weeks=wa["u"],
            )
            b = controlled_order(
                qb["u"],
                candidates,
                viewers,
                total,
                v,
                airings=opportunities,
                weeks=wb["u"],
            )
            self.assertEqual(
                complete(a, fallback, candidates), complete(b, fallback, candidates)
            )


if __name__ == "__main__":
    unittest.main()
