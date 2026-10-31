"""Causal, disk-backed viewing-to-programme interactions; original inputs stay read-only."""

import csv
import hashlib
import json
import sqlite3
import time
from collections import Counter, defaultdict
from pathlib import Path

from .audit_data import _environment
from .csv_io import sha256_file
from .intervals import Airing, IntervalMatcher, View, segment_durations
from .real_matching_audit import stamp

METADATA = (
    "tv_show_title",
    "tv_show_category",
    "tv_show_genre_1",
    "tv_show_genre_2",
    "tv_show_genre_3",
)
PIPELINE_VERSION = "causal-interactions-v1"


def csv_rows(path):
    with Path(path).open(encoding="utf-8-sig", newline="") as source:
        yield from csv.DictReader(source)


def schedule_catalog(paths, start, end, metadata_cutoff):
    """Union files by canonical airing, preserving complete airing denominators.

    Include prior-file carryovers by their timestamps, not by the source filename.
    Metadata selection counts distinct canonical broadcasts, never duplicate rows.
    """
    unique = {}
    metadata_counts = defaultdict(Counter)
    seen_metadata = set()
    for path in paths:
        for row in csv_rows(path):
            item = row["tv_show_id"]
            if item == "0" or not item.strip():
                continue
            s = stamp(row["start_time"], True)
            duration = float(row["duration"])
            if duration <= 0:
                continue
            e = s + duration
            key = (row["channel_id"], s, e, item)
            if s < metadata_cutoff and key not in seen_metadata:
                metadata_counts[item][tuple(row.get(f, "") for f in METADATA)] += 1
                seen_metadata.add(key)
            if s < end and e > start:
                unique.setdefault(
                    key, Airing(json.dumps(key), row["channel_id"], item, s, e)
                )
    metadata = {
        item: min(counts, key=lambda value: (-counts[value], value))
        for item, counts in metadata_counts.items()
    }
    airings = sorted(
        unique.values(), key=lambda a: (a.channel_id, a.start, a.end, a.item_id)
    )
    active, channel, bad = [], None, set()
    for airing in airings:
        if airing.channel_id != channel:
            active, channel = [], airing.channel_id
        active = [a for a in active if a.end > airing.start]
        for earlier in active:
            if earlier.item_id != airing.item_id:
                bad.update((earlier.row_id, airing.row_id))
        active.append(airing)
    return airings, bad, metadata


def clipped_clean_view(row, start, end):
    """Observe only the prefix known at end; future tails cannot affect cleaning.

    Completed sessions use the audited discrepancy and 24h rules. For ongoing
    sessions, declared complete duration is unknowable at cutoff: clean the
    observed prefix on length only. Clip to the window only AFTER that check.
    """
    s = stamp(row["start_time"])
    if s >= end:
        return None
    e = stamp(row["stop_time"])
    if e <= start or e <= s:
        return None
    observed_end = min(e, end)
    elapsed = observed_end - s
    if elapsed > 86400 or elapsed <= 0:
        return None
    if e <= end and abs(float(row["duraton"]) - (e - s)) > 1:
        return None
    return row["user_id"], row["vsetv_id"], max(s, start), observed_end


def extract_interactions(
    views_path, schedule_paths, start, end, cache_dir, *, input_hashes=None, force=False
):
    """Return sorted [user,item,soft_airing_sum,qualified_airing_count] records.

    The same function handles a combined 11–30 fitting window; never add the
    separately clipped comparison-window counts for a final refit.
    """
    cache_dir = Path(cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)
    paths = [Path(views_path), *map(Path, schedule_paths)]
    inputs = input_hashes or {p.name: sha256_file(p) for p in paths}
    sources = {
        name: sha256_file(Path(__file__).with_name(name))
        for name in ("interactions.py", "intervals.py", "real_matching_audit.py")
    }
    config = {
        "version": PIPELINE_VERSION,
        "start": start,
        "end": end,
        "clock": "source-naive-wall-seconds",
        "qualified_fraction": 0.8,
        "max_session_seconds": 86400,
        "inputs": inputs,
        "sources": sources,
    }
    config_digest = hashlib.sha256(
        json.dumps(config, sort_keys=True).encode()
    ).hexdigest()
    manifest_path = cache_dir / "manifest.json"
    result_path = cache_dir / "interactions.json"
    if not force and manifest_path.exists() and result_path.exists():
        old = json.loads(manifest_path.read_text())
        if old["config_digest"] == config_digest and old[
            "output_sha256"
        ] == sha256_file(result_path):
            return json.loads(result_path.read_text()), old
    began = time.perf_counter()
    airings, bad, _ = schedule_catalog(schedule_paths, start, end, end)
    matcher = IntervalMatcher(a for a in airings if a.row_id not in bad)
    db = sqlite3.connect(cache_dir / "segments.sqlite")
    db.executescript(
        "PRAGMA journal_mode=OFF; PRAGMA synchronous=OFF; "
        "PRAGMA cache_size=-32768; PRAGMA temp_store=FILE; "
        "DROP TABLE IF EXISTS views; DROP TABLE IF EXISTS segments; "
        "CREATE TABLE views(u TEXT,c TEXT,s REAL,e REAL); "
        "CREATE TABLE segments(u TEXT,a TEXT,item TEXT,s REAL,e REAL,d REAL);"
    )
    retained = crossing = 0
    for i, row in enumerate(csv_rows(views_path)):
        value = clipped_clean_view(row, start, end)
        if value is not None:
            retained += 1
            crossing += stamp(row["stop_time"]) > end
            db.execute("INSERT INTO views VALUES(?,?,?,?)", value)
        if i % 100000 == 0:
            db.commit()
    db.commit()
    db.execute("CREATE INDEX view_order ON views(u,c,s,e)")
    previous, left, right = None, None, None

    def emit(user_channel, a, b):
        if user_channel is None:
            return
        v = View("merged", *user_channel, a, b)
        for m in matcher.match([v]):
            db.execute(
                "INSERT INTO segments VALUES(?,?,?,?,?,?)",
                (
                    m.user_id,
                    m.airing_id,
                    m.item_id,
                    m.start,
                    m.end,
                    m.programme_seconds,
                ),
            )

    for u, c, s, e in db.execute("SELECT u,c,s,e FROM views ORDER BY u,c,s,e"):
        if previous == (u, c) and s <= right:
            right = max(right, e)
        else:
            emit(previous, left, right)
            previous, left, right = (u, c), s, e
    emit(previous, left, right)
    db.commit()
    db.execute("CREATE INDEX segment_order ON segments(u,a,s,e)")
    interactions = defaultdict(lambda: [0.0, 0])
    key, segments, duration, item = None, [], 0, None
    user_airings = 0

    def consume():
        nonlocal user_airings
        if key is None:
            return
        user_airings += 1
        values = segment_durations(segments)
        pair = interactions[(key[0], item)]
        pair[0] += min(1.0, values["union_seconds"] / duration)
        pair[1] += values["longest_block_seconds"] / duration >= 0.8

    for u, a, it, s, e, d in db.execute(
        "SELECT u,a,item,s,e,d FROM segments ORDER BY u,a,s,e"
    ):
        if key != (u, a):
            consume()
            key, segments, duration, item = (u, a), [], d, it
        segments.append((s, e))
    consume()
    result = [
        [u, it, value[0], value[1]] for (u, it), value in sorted(interactions.items())
    ]
    result_path.write_text(json.dumps(result, separators=(",", ":")) + "\n")
    db.close()
    manifest = {
        "config": config,
        "config_digest": config_digest,
        "output_sha256": sha256_file(result_path),
        "retained_clipped_source_rows": retained,
        "ongoing_sessions_at_cutoff": crossing,
        "user_airings": user_airings,
        "user_item_pairs": len(result),
        "qualified_user_airings": sum(r[3] for r in result),
        "qualified_users": len({r[0] for r in result if r[3]}),
        "conflicted_airings_excluded": len(bad),
        "elapsed_seconds": time.perf_counter() - began,
        "environment": _environment(),
    }
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    return result, manifest


def targets(records, candidates):
    by_user = defaultdict(list)
    for user, item, _, qualified in records:
        if qualified and item in candidates:
            by_user[user].append((item, qualified))
    return {
        u: [item for item, _ in sorted(values, key=lambda v: (-v[1], v[0]))[:5]]
        for u, values in sorted(by_user.items())
    }
