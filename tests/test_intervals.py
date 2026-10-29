import math
import random
import unittest
from src.intervals import Airing, IntervalMatcher, View, match_reference, segment_durations


def canonical(matches):
    return sorted((m.view_id, m.airing_id, m.user_id, m.item_id, m.start, m.end, m.programme_seconds)
                  for m in matches)


class IntervalTests(unittest.TestCase):
    def test_hand_calculated_cross_programme_view(self):
        view = View("v", "synthetic-user", "ch", 19 * 3600 + 50 * 60, 20 * 3600 + 30 * 60)
        airings = [Airing("a", "ch", "A", 19 * 3600 + 30 * 60, 20 * 3600),
                   Airing("b", "ch", "B", 20 * 3600, 21 * 3600)]
        self.assertEqual({m.item_id: m.overlap_seconds for m in IntervalMatcher(airings).match([view])},
                         {"A": 600, "B": 1800})

    def test_touching_channels_unlabelled_and_duplicate_rows(self):
        airings = [Airing("left", "ch", "L", 0, 10), Airing("right", "ch", "R", 20, 30),
                   Airing("other", "other", "X", 10, 20), Airing("zero", "ch", "0", 10, 20),
                   Airing("a", "ch", "A", 10, 20), Airing("duplicate-a", "ch", "A", 10, 20)]
        views = [View("v", "u", "ch", 10, 20)]
        matches = list(IntervalMatcher(airings).match(views))
        self.assertEqual({m.airing_id for m in matches}, {"a", "duplicate-a"})
        self.assertEqual(len(list(IntervalMatcher(airings, include_unlabelled=True).match(views))), 3)
        self.assertEqual(segment_durations([(m.start, m.end) for m in matches])["union_seconds"], 10)

    def test_cutoff_clips_crossing_and_excludes_future_changes(self):
        airings = [Airing("a", "ch", "A", 0, 40)]
        before = [View("crossing", "u", "ch", 8, 12), View("future", "u", "ch", 10, 20)]
        changed = [View("crossing", "u", "ch", 8, 35), View("future", "u", "ch", 11, 32)]
        matcher = IntervalMatcher(airings)
        self.assertEqual(canonical(matcher.match(before, cutoff=10)), canonical(matcher.match(changed, cutoff=10)))
        self.assertEqual([m.overlap_seconds for m in matcher.match(before, cutoff=10)], [2])
        self.assertEqual(list(matcher.match(before, cutoff=8)), [])

    def test_random_overlap_tree_matches_independent_reference(self):
        rng = random.Random(20261029)
        airings, views = [], []
        for index in range(140):
            start = rng.randrange(1000)
            airings.append(Airing(str(index), str(rng.randrange(4)), str(rng.randrange(12)), start,
                                  start + rng.randrange(1, 400)))
        for index in range(90):
            start = rng.randrange(1100)
            views.append(View(str(index), "u", str(rng.randrange(5)), start, start + rng.randrange(1, 300)))
        for cutoff in (None, 0, 100, 600, 2000):
            for include in (False, True):
                with self.subTest(cutoff=cutoff, include=include):
                    got = IntervalMatcher(airings, include_unlabelled=include).match(views, cutoff=cutoff)
                    expected = match_reference(views, airings, cutoff=cutoff, include_unlabelled=include)
                    self.assertEqual(canonical(got), canonical(expected))

    def test_nested_intervals_and_adjacent_floats_terminate(self):
        after_one = math.nextafter(1.0, 2.0)
        airings = [Airing("tiny", "ch", "A", 1.0, after_one),
                   Airing("wide", "ch", "B", 0, 1000), Airing("nested", "ch", "C", 300, 400)]
        views = [View("v", "u", "ch", 1.0, after_one), View("v2", "u", "ch", 350, 450)]
        self.assertEqual(canonical(IntervalMatcher(airings).match(views)), canonical(match_reference(views, airings)))

    def test_union_and_continuity_are_different(self):
        self.assertEqual(segment_durations([(0, 10), (0, 10), (8, 15), (15, 20), (25, 30)]),
                         {"union_seconds": 25, "longest_block_seconds": 20, "longest_single_seconds": 10})
        self.assertEqual(segment_durations([])["union_seconds"], 0)

    def test_invalid_intervals_and_cutoffs_fail(self):
        for start, end in ((1, 1), (2, 1), (0, math.inf), (math.nan, 1)):
            with self.assertRaises(ValueError):
                View("v", "u", "ch", start, end)
        with self.assertRaises(ValueError):
            list(IntervalMatcher([]).match([], cutoff=math.nan))


if __name__ == "__main__":
    unittest.main()
