import csv
import tempfile
import unittest
from pathlib import Path

import numpy as np
from threadpoolctl import threadpool_limits
from src.interactions import extract_interactions, schedule_catalog, targets
from src.models import Ranker
from src.real_matching_audit import stamp


class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.start = stamp("2020-05-17 00:00:00")
        self.cutoff = stamp("2020-05-18 00:00:00")
        self.end = stamp("2020-05-19 00:00:00")
        self.header = [
            "channel_id",
            "start_time",
            "duration",
            "tv_show_id",
            "tv_show_title",
            "tv_show_category",
            "tv_show_genre_1",
            "tv_show_genre_2",
            "tv_show_genre_3",
        ]
        crossing = [
            "3",
            "17.05.2020 23:00:00",
            7200,
            "A",
            "Programme A",
            "Drama",
            "",
            "",
            "",
        ]
        self.first = self.write("first.csv", self.header, [crossing])
        # Deliberate duplicate across files: must be a single canonical broadcast.
        self.second = self.write(
            "second.csv",
            self.header,
            [crossing]
            + [
                [
                    "3",
                    "18.05.2020 01:00:00",
                    3600,
                    "B",
                    "Programme B",
                    "News",
                    "",
                    "",
                    "",
                ]
            ],
        )
        self.views_header = [
            "user_id",
            "vsetv_id",
            "start_time",
            "stop_time",
            "duraton",
        ]

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, name, header, rows):
        path = self.root / name
        with path.open("w", newline="") as f:
            w = csv.writer(f)
            w.writerow(header)
            w.writerows(rows)
        return path

    def test_carryover_full_denominator_and_combined_refit(self):
        views = self.write(
            "views.csv",
            self.views_header,
            [["u", "3", "2020-05-17 23:00:00", "2020-05-18 01:00:00", 7200]],
        )
        paths = [self.first, self.second]
        pre, _ = extract_interactions(
            views, paths, self.start, self.cutoff, self.root / "pre"
        )
        post, _ = extract_interactions(
            views, paths, self.cutoff, self.end, self.root / "post"
        )
        combined, _ = extract_interactions(
            views, paths, self.start, self.end, self.root / "combined"
        )
        self.assertEqual(pre, [["u", "A", 0.5, 0]])
        self.assertEqual(post, [["u", "A", 0.5, 0]])
        self.assertEqual(combined, [["u", "A", 1.0, 1]])
        self.assertEqual(targets(combined, {"A"}), {"u": ["A"]})
        airings, _, _ = schedule_catalog(paths, self.cutoff, self.end, self.cutoff)
        self.assertEqual(len([a for a in airings if a.item_id == "A"]), 1)
        self.assertEqual(
            next(a for a in airings if a.item_id == "A").end
            - next(a for a in airings if a.item_id == "A").start,
            7200,
        )

    def test_cbf_score_to_programme_alignment(self):
        items = [str(i) for i in range(101, 121)]
        records = [["user_" + it, it, 1.0, 1] for it in items]
        metadata = {
            it: ("Title " + it, "Unique category " + it, "", "", "") for it in items
        }
        model = Ranker(records, set(items), metadata, "cbf")
        for it in items:
            self.assertEqual(model.primary("user_" + it), [it])
        self.assertEqual(model.recommend("cold")[1], 0)

    def test_end_to_end_post_cutoff_invariance_including_cleaning(self):
        schedules = self.write(
            "fitting.csv",
            self.header,
            [
                ["3", "17.05.2020 12:00:00", 3600, "B", "B", "News", "", "", ""],
                ["3", "17.05.2020 13:00:00", 3600, "C", "C", "Drama", "", "", ""],
                ["3", "17.05.2020 14:00:00", 3600, "D", "D", "News", "", "", ""],
                ["3", "17.05.2020 15:00:00", 3600, "E", "E", "Drama", "", "", ""],
                ["3", "17.05.2020 16:00:00", 3600, "F", "F", "News", "", "", ""],
            ],
        )
        common = [
            ["u", "3", "2020-05-17 12:00:00", "2020-05-17 13:00:00", 3600],
            ["v", "3", "2020-05-17 13:00:00", "2020-05-17 14:00:00", 3600],
        ]
        original = common + [
            ["u", "3", "2020-05-17 23:00:00", "2020-05-18 01:00:00", 7200]
        ]
        # Extending only the unobserved tail beyond 24h used to alter cleaning.
        changed = common + [
            ["u", "3", "2020-05-17 23:00:00", "2020-05-19 02:00:00", 97200],
            [
                "future_only_user",
                "3",
                "2020-05-18 10:00:00",
                "2020-05-18 11:00:00",
                3600,
            ],
        ]
        paths = [self.first, self.second, schedules]
        before, _ = extract_interactions(
            self.write("before.csv", self.views_header, original),
            paths,
            self.start,
            self.cutoff,
            self.root / "before",
        )
        after, _ = extract_interactions(
            self.write("after.csv", self.views_header, changed),
            paths,
            self.start,
            self.cutoff,
            self.root / "after",
        )
        self.assertEqual(before, after)
        _, _, metadata = schedule_catalog(paths, self.start, self.end, self.cutoff)
        candidates = {"A", "B", "C", "D", "E", "F"}
        with threadpool_limits(limits=1):
            for method in ["popularity", "personal", "cbf", "als"]:
                a = Ranker(
                    before, candidates, metadata, method, factors=4, iterations=3
                )
                b = Ranker(after, candidates, metadata, method, factors=4, iterations=3)
                self.assertEqual(a.fingerprint(), b.fingerprint(), method)
                for u in ["u", "v", "cold"]:
                    self.assertEqual(a.recommend(u), b.recommend(u), method)
                if method == "als":
                    np.testing.assert_array_equal(
                        a.confidence.data, 1 + 40 * a.weights.data
                    )
                    self.assertEqual(a.als.alpha, 1.0)


if __name__ == "__main__":
    unittest.main()
