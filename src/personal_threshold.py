"""Integer personal airing counts; global anchors are supplied separately."""

import sqlite3
from collections import defaultdict
from .intervals import segment_durations
from .personal_ties import personal_order
from .improvement_helpers import complete


def personal_counts(
    db, start, cutoff, thresholds=(0.5, 0.65, 0.8), *, airing_observer=None
):
    counts = {t: defaultdict(lambda: defaultdict(int)) for t in thresholds}
    current = None
    segments = []

    def finish():
        if current is None or not segments:
            return
        u, a, item, duration = current
        durations = segment_durations(segments)
        fraction = durations["longest_block_seconds"] / duration
        if airing_observer is not None:
            airing_observer(u, item, duration, durations)
        for threshold in thresholds:
            if fraction >= threshold:
                counts[threshold][u][item] += 1

    with sqlite3.connect(db) as connection:
        for u, a, item, s, e, d in connection.execute(
            "SELECT u,a,item,s,e,d FROM segments ORDER BY u,a,s,e"
        ):
            key = (u, a, item, d)
            if key != current:
                finish()
                current, segments = key, []
            s, e = max(s, start), min(e, cutoff)
            if e > s and d > 0:
                segments.append((s, e))
        finish()
    return {t: {u: dict(c) for u, c in users.items()} for t, users in counts.items()}


def predict(counts, candidates, viewers, total, fallback, users):
    predictions, sizes = {}, {}
    for u in users:
        order = personal_order(
            counts.get(u, {}),
            candidates,
            variant="popularity",
            viewers=viewers,
            total=total,
        )
        predictions[u], sizes[u] = complete(order, fallback, candidates)
    return predictions, sizes
