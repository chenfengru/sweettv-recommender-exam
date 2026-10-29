"""Half-open interval matching on already verified, common-unit timestamps.

No CSV timestamps are converted here. Duplicate source rows are preserved;
their treatment is a data decision, not an implicit cleaning operation.
"""

from dataclasses import dataclass
from math import isfinite
from .csv_io import is_zero_id


def _check_interval(start, end):
    if not isfinite(start) or not isfinite(end) or end <= start:
        raise ValueError("interval endpoints must be finite with end > start")


@dataclass(frozen=True, slots=True)
class View:
    row_id: str
    user_id: str
    channel_id: str
    start: float
    end: float

    def __post_init__(self):
        _check_interval(self.start, self.end)


@dataclass(frozen=True, slots=True)
class Airing:
    row_id: str
    channel_id: str
    item_id: str
    start: float
    end: float

    def __post_init__(self):
        _check_interval(self.start, self.end)


@dataclass(frozen=True, slots=True)
class Match:
    view_id: str
    airing_id: str
    user_id: str
    item_id: str
    start: float
    end: float
    programme_seconds: float

    @property
    def overlap_seconds(self):
        return self.end - self.start


def _eligible(airing, include_unlabelled):
    return include_unlabelled or (bool(airing.item_id.strip()) and not is_zero_id(airing.item_id))


def match_reference(views, airings, *, cutoff=None, include_unlabelled=False):
    """Independent brute-force oracle for small, bounded synthetic or real examples."""
    if cutoff is not None and not isfinite(cutoff):
        raise ValueError("cutoff must be finite")
    airings = list(airings)
    for view in views:
        view_end = min(view.end, cutoff) if cutoff is not None else view.end
        if view_end <= view.start:
            continue
        for airing in airings:
            if view.channel_id != airing.channel_id or not _eligible(airing, include_unlabelled):
                continue
            start = max(view.start, airing.start)
            end = min(view_end, airing.end)
            if end > start:
                yield Match(view.row_id, airing.row_id, view.user_id, airing.item_id,
                            start, end, airing.end - airing.start)


class _Node:
    """Balanced centered interval tree; query visits only relevant branches."""
    __slots__ = ("center", "by_start", "by_end", "left", "right")

    def __init__(self, airings):
        starts = sorted(a.start for a in airings)
        self.center = starts[len(starts) // 2]
        left, right, crossing = [], [], []
        for airing in airings:
            if airing.end <= self.center:
                left.append(airing)
            elif airing.start > self.center:
                right.append(airing)
            else:
                crossing.append(airing)
        self.by_start = sorted(crossing, key=lambda a: a.start)
        self.by_end = sorted(crossing, key=lambda a: a.end, reverse=True)
        self.left = _Node(left) if left else None
        self.right = _Node(right) if right else None

    def query(self, start, end):
        if end <= self.center:
            for airing in self.by_start:
                if airing.start >= end:
                    break
                yield airing
            if self.left:
                yield from self.left.query(start, end)
        elif start >= self.center:
            for airing in self.by_end:
                if airing.end <= start:
                    break
                yield airing
            if self.right:
                yield from self.right.query(start, end)
        else:
            yield from self.by_start
            if self.left:
                yield from self.left.query(start, end)
            if self.right:
                yield from self.right.query(start, end)


class IntervalMatcher:
    """Index O(number of airings) storage; stream views and individual matches.

    Tree construction sorts at each level (O(n log^2 n) worst case). A query
    takes O(log n + matches) per channel. Full-data memory is not benchmarked.
    """

    def __init__(self, airings, *, include_unlabelled=False):
        channels = {}
        for airing in airings:
            if _eligible(airing, include_unlabelled):
                channels.setdefault(airing.channel_id, []).append(airing)
        self.channels = {channel: _Node(rows) for channel, rows in channels.items()}

    def match(self, views, *, cutoff=None):
        if cutoff is not None and not isfinite(cutoff):
            raise ValueError("cutoff must be finite")
        for view in views:
            end = min(view.end, cutoff) if cutoff is not None else view.end
            root = self.channels.get(view.channel_id)
            if root is None or end <= view.start:
                continue
            for airing in root.query(view.start, end):
                yield Match(view.row_id, airing.row_id, view.user_id, airing.item_id,
                            max(view.start, airing.start), min(end, airing.end),
                            airing.end - airing.start)


def segment_durations(segments):
    """Return union seconds, longest merged block, and longest single segment.

    Touching segments are merged. This is a duration diagnostic; merging does
    not establish continuous watching without a channel switch.
    """
    segments = sorted(segments)
    if not segments:
        return {"union_seconds": 0.0, "longest_block_seconds": 0.0, "longest_single_seconds": 0.0}
    for start, end in segments:
        _check_interval(start, end)
    start, end = segments[0]
    lengths = []
    for next_start, next_end in segments[1:]:
        if next_start <= end:
            end = max(end, next_end)
        else:
            lengths.append(end - start)
            start, end = next_start, next_end
    lengths.append(end - start)
    return {"union_seconds": sum(lengths), "longest_block_seconds": max(lengths),
            "longest_single_seconds": max(b - a for a, b in segments)}
