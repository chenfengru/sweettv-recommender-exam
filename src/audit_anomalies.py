import csv, json, sqlite3, time, argparse
from pathlib import Path
from collections import Counter
from datetime import datetime, timedelta
parser = argparse.ArgumentParser(description='Exact anomaly follow-up; first examples stay private.')
parser.add_argument('--data-dir', type=Path, required=True)
parser.add_argument('--output-dir', type=Path, required=True)
parser.add_argument('--private-dir', type=Path, required=True)
args = parser.parse_args()
(data, out, priv) = (args.data_dir, args.output_dir, args.private_dir)
out.mkdir(exist_ok=True, parents=True)
priv.mkdir(exist_ok=True, parents=True)
started = time.perf_counter()
res = Counter()
dates = Counter()
longdates = Counter()
examples = []
longs = []
rawlong = 0
with (data / 'dataset11-30.csv').open() as f:
    for (n, r) in enumerate(csv.DictReader(f), 2):
        (s, e) = (datetime.fromisoformat(r['start_time']), datetime.fromisoformat(r['stop_time']))
        d = float(r['duraton'])
        delta = d - (e - s).total_seconds()
        res[str(delta)] += 1
        if delta:
            dates[s.date().isoformat(), e.date().isoformat()] += 1
            if len(examples) < 5:
                examples.append({'csv_record': n, **r, 'elapsed_wall_seconds': (e - s).total_seconds(), 'residual_seconds': delta})
        if (e - s).total_seconds() > 86400:
            rawlong += 1
            if len(longs) < 3:
                longs.append({'csv_record': n, **r})
schedules = {}
overlaps = {}
boundary = {}
candidates = {}
examples_schedule = []
meta = {}
cross_keys = {}
head_keys = {}
tail_rows = {}
head_rows = {}
for (period, lo, hi) in [('11-20', '2020-03-09', '2020-05-18'), ('21-30', '2020-05-18', '2020-07-27'), ('31-42', '2020-07-27', '2020-10-19')]:
    (lo, hi) = (datetime.fromisoformat(lo), datetime.fromisoformat(hi))
    channels = {}
    active = []
    ov = []
    outside = 0
    avail = set()
    metadata = {}
    seam = set()
    wall_gap_dates = Counter()
    head = set()
    tail_full = set()
    head_full = set()
    with (data / f'export_arh_{period}-final.csv').open() as f:
        for (n, r) in enumerate(csv.DictReader(f), 2):
            s = datetime.strptime(r['start_time'], '%d.%m.%Y %H:%M:%S')
            d = float(r['duration'])
            e = s + timedelta(seconds=d)
            channels.setdefault(r['channel_id'], []).append((s, e, r['tv_show_id'], n))
            if d > 0 and s < hi and (e > lo) and (r['tv_show_id'] != '0'):
                avail.add(r['tv_show_id'])
                metadata.setdefault(r['tv_show_id'], set()).add((r['tv_show_title'], r['tv_show_category'], r['tv_show_genre_1'], r['tv_show_genre_2'], r['tv_show_genre_3']))
            if s >= hi:
                outside += 1
            if s < lo + timedelta(days=1):
                head.add((r['channel_id'], s.isoformat(), e.isoformat(), r['tv_show_id']))
                head_full.add(tuple(r.values()))
            if s < hi and e > hi or s >= hi:
                tail_full.add(tuple(r.values()))
            if s < hi and e > hi or s >= hi:
                seam.add((r['channel_id'], s.isoformat(), e.isoformat(), r['tv_show_id']))
            if period == '11-20' and n == 1025:
                examples_schedule.append({'csv_record': n, **r})
    for (c, aa) in channels.items():
        aa.sort()
        active = []
        for x in aa:
            active = [y for y in active if y[1] > x[0]]
            for y in active:
                ov.append({'channel_id': c, 'records': [y[3], x[3]], 'intervals': [[str(y[0]), str(y[1]), y[2]], [str(x[0]), str(x[1]), x[2]]]})
            active.append(x)
    overlaps[period] = ov
    candidates[period] = {'ids_intersecting_window': len(avail), 'rows_starting_at_or_after_window_end': outside, 'metadata_conflicting_item_ids': sum((len(v) > 1 for v in metadata.values()))}
    cross_keys[period] = seam
    head_keys[period] = head
    tail_rows[period] = tail_full
    head_rows[period] = head_full
    ordered = [(c, aa) for (c, aa) in channels.items()]
    boundary[period] = {'first_day': str(lo), 'next_period_start': str(hi)}
report = {'residual_seconds_counts': dict(res), 'discrepancy_start_stop_dates': {' / '.join(k): v for (k, v) in dates.items()}, 'view_intervals_above_24h_by_endpoints': rawlong, 'schedule_overlaps': overlaps, 'window_candidates': candidates, 'cross_file_boundary_duplicates': {f'{x} / {y}': {'canonical_airing_keys': len(cross_keys[x] & head_keys[y]), 'exact_parsed_rows': len(tail_rows[x] & head_rows[y])} for (x, y) in [('11-20', '21-30'), ('21-30', '31-42')]}, 'elapsed_seconds': time.perf_counter() - started}
(out / 'anomaly_audit.json').write_text(json.dumps(report, indent=2))
(priv / 'anomaly_examples.json').write_text(json.dumps({'duration_discrepancies': examples, 'long_sessions': longs, 'schedule_example': examples_schedule}, indent=2))
print(json.dumps({'status': 'completed', 'report': str(out / 'anomaly_audit.json')}))
