"""Real-data interval diagnostics; private disk-backed histories, aggregate outputs."""
import argparse, csv, json, sqlite3, time, random, resource, platform, sys
from pathlib import Path
from datetime import datetime
from collections import Counter, defaultdict
from src.intervals import View, Airing, IntervalMatcher, segment_durations, match_reference
from src.audit_data import NumericSummary, _environment
EPOCH = datetime(1970, 1, 1)

def stamp(s, dmy=False):
    d = datetime.strptime(s, '%d.%m.%Y %H:%M:%S') if dmy else datetime.fromisoformat(s)
    return (d - EPOCH).total_seconds()

def wall(t):
    return datetime.fromtimestamp(t, __import__('datetime').timezone.utc).strftime('%Y-%m-%d %H:%M:%S')

def rows(p):
    with p.open(encoding='utf-8-sig', newline='') as f:
        yield from csv.DictReader(f)

def main():
    a = argparse.ArgumentParser()
    a.add_argument('--data-dir', type=Path, required=True)
    a.add_argument('--output-dir', type=Path, required=True)
    a.add_argument('--private-dir', type=Path, required=True)
    a.add_argument('--exclude-suspect-views', action='store_true')
    args = a.parse_args()
    start = time.perf_counter()
    args.private_dir.mkdir(exist_ok=True, parents=True)
    args.output_dir.mkdir(exist_ok=True, parents=True)
    db = sqlite3.connect(args.private_dir / 'matching.sqlite')
    db.execute('PRAGMA journal_mode=OFF')
    db.execute('PRAGMA synchronous=OFF')
    db.execute('PRAGMA cache_size=-32768')
    db.execute('PRAGMA temp_store=FILE')
    db.execute('DROP TABLE IF EXISTS views')
    db.execute('CREATE TABLE views(u TEXT,c TEXT,s REAL,e REAL)')
    rng = random.Random(42)
    sample = []
    n = 0
    invalid = 0
    excluded = Counter()
    channels = Counter()
    ranges = [float('inf'), -float('inf')]
    for (i, r) in enumerate(rows(args.data_dir / 'dataset11-30.csv'), 2):
        (s, e) = (stamp(r['start_time']), stamp(r['stop_time']))
        n += 1
        channels[r['vsetv_id']] += 1
        ranges = [min(ranges[0], s), max(ranges[1], e)]
        if e <= s:
            invalid += 1
            continue
        mismatch = abs(float(r['duraton']) - (e - s)) > 1
        long = e - s > 86400
        excluded['duration_discrepancy_rows'] += mismatch
        excluded['above_24h_rows'] += long
        suspect = mismatch or long
        excluded['suspect_rows_union'] += suspect
        if not (args.exclude_suspect_views and suspect):
            db.execute('INSERT INTO views VALUES(?,?,?,?)', (r['user_id'], r['vsetv_id'], s, e))
        v = View(str(i), r['user_id'], r['vsetv_id'], s, e)
        if len(sample) < 10000:
            sample.append(v)
        else:
            j = rng.randrange(n - invalid)
            if j < 10000:
                sample[j] = v
        if n % 100000 == 0:
            db.commit()
    db.commit()
    db.execute('CREATE INDEX views_order ON views(u,c,s,e)')
    db.commit()
    templates = {r['user_id'] for r in rows(args.data_dir / 'submission.csv')}
    report = {'clock': 'naive source wall time; seconds since a naive 1970 epoch, NOT verified UTC', 'sampling': {'method': 'Algorithm R uniform reservoir over positive-length view rows in source order', 'size': len(sample), 'seed': 42}, 'view_rows': n, 'invalid_view_intervals': invalid, 'exclude_suspect_views': args.exclude_suspect_views, 'suspect_view_counts': dict(excluded), 'view_channel_row_counts': dict(channels), 'view_wall_range': list(map(wall, ranges)), 'periods': {}}
    private_examples = []
    prior_items = set()
    carry_airings = []
    periods = [('11-20', '2020-03-09', '2020-05-18'), ('21-30', '2020-05-18', '2020-07-27'), ('31-42', '2020-07-27', '2020-10-19')]
    for (period, lo, hi) in periods:
        began = time.perf_counter()
        (lo, hi) = (stamp(lo), stamp(hi))
        catalog = set()
        attrs = set()
        unique = {}
        dups = 0
        min_s = float('inf')
        max_e = -float('inf')
        dur = NumericSummary(10000, 42)
        gaps = NumericSummary(10000, 42)
        for (i, r) in enumerate(rows(args.data_dir / f'export_arh_{period}-final.csv'), 2):
            s = stamp(r['start_time'], True)
            d = float(r['duration'])
            e = s + d
            c = r['channel_id']
            item = r['tv_show_id']
            min_s = min(min_s, s)
            max_e = max(max_e, e)
            if item != '0':
                if s < hi and e > lo and (d > 0):
                    catalog.add(item)
                    if any((r.get(f) for f in ['tv_show_category', 'tv_show_genre_1', 'tv_show_genre_2', 'tv_show_genre_3'])):
                        attrs.add(item)
                dur.add(str(d))
            if d <= 0:
                continue
            key = (c, s, e, item)
            if key in unique:
                dups += 1
            else:
                unique[key] = Airing(period + ':' + str(i), c, item, s, e)
        carry_count = 0
        for x in carry_airings:
            if x.end > lo and x.start < hi:
                key = (x.channel_id, x.start, x.end, x.item_id)
                if key not in unique:
                    unique[key] = x
                    carry_count += 1
                if x.item_id != '0':
                    catalog.add(x.item_id)
                    attrs.add(x.item_id)
        airings = list(unique.values())
        del unique
        carry_airings = [x for x in airings if x.end > hi]
        by_channel = defaultdict(list)
        for x in airings:
            by_channel[x.channel_id].append(x)
        bad = set()
        conflict_pairs = 0
        adjacent = 0
        endpoints = Counter()
        for (c, aa) in by_channel.items():
            aa.sort(key=lambda x: (x.start, x.end, x.item_id))
            active = []
            for (j, x) in enumerate(aa):
                if j:
                    gap = x.start - aa[j - 1].end
                    gaps.add(str(gap))
                    adjacent += gap == 0
                active = [y for y in active if y.end > x.start]
                for y in active:
                    if x.item_id != '0' and y.item_id != '0' and (x.item_id != y.item_id):
                        bad.update([x.row_id, y.row_id])
                        conflict_pairs += 1
                active.append(x)
        result = {'window_wall': [wall(lo), wall(hi)], 'schedule_wall_extent': [wall(min_s), wall(max_e)], 'canonical_duplicate_airing_rows_beyond_first': dups, 'canonical_airings': len(airings), 'carryover_airings_from_previous_file': carry_count, 'distinct_candidate_ids': len(catalog), 'candidates_without_structured_attributes': len(catalog - attrs), 'labelled_duration_seconds': dur.report(), 'adjacent_schedule_gap_seconds': gaps.report(), 'exactly_touching_adjacent_rows': adjacent, 'conflicting_nonzero_overlap_pairs': conflict_pairs, 'conflicted_airings_excluded_from_usable_labels': len(bad), 'schedule_channels': len(by_channel), 'view_channels_missing_from_schedule': sorted(set(channels) - set(by_channel))}
        if period == '31-42':
            result['candidate_ids_without_pre_cutoff_usable_interactions'] = len(catalog - prior_items)
            report['periods'][period] = result
            break
        matcher = IntervalMatcher(airings, include_unlabelled=True)
        checks = 0
        for v in sample[:30]:
            if not (v.start < hi and v.end > lo):
                continue
            clipped = View(v.row_id, v.user_id, v.channel_id, max(lo, v.start), min(hi, v.end))
            local = [x for x in by_channel.get(v.channel_id, []) if x.start < clipped.end and x.end > clipped.start]
            assert sorted(((x.airing_id, x.start, x.end) for x in matcher.match([clipped]))) == sorted(((x.airing_id, x.start, x.end) for x in match_reference([clipped], local, include_unlabelled=True)))
            checks += 1
        sample_counts = Counter()
        sample_seconds = Counter()
        for v in sample:
            if v.start >= hi or v.end <= lo:
                continue
            v = View(v.row_id, v.user_id, v.channel_id, max(lo, v.start), min(hi, v.end))
            mm = list(matcher.match([v]))
            lab = [m for m in mm if m.item_id != '0']
            sample_counts['rows'] += 1
            sample_counts['rows_any_schedule'] += bool(mm)
            sample_counts['rows_nonzero_programme'] += bool(lab)
            sample_seconds['logged'] += v.end - v.start
            sample_seconds['labelled_union'] += segment_durations([(m.start, m.end) for m in lab])['union_seconds']
        result['sampled_raw_row_matching'] = dict(sample_counts)
        result['sampled_session_seconds'] = dict(sample_seconds)
        result['actual_reference_views_checked'] = checks
        db.execute('DROP TABLE IF EXISTS segments')
        db.execute('CREATE TABLE segments(u TEXT,a TEXT,item TEXT,s REAL,e REAL,d REAL)')
        totals = Counter()
        merged_count = 0

        def merged_views():
            previous = None
            left = right = None
            for (u, c, s, e) in db.execute('SELECT u,c,s,e FROM views WHERE s<? AND e>? ORDER BY u,c,s,e', (hi, lo)):
                (s, e) = (max(s, lo), min(e, hi))
                totals['raw_clipped_session_seconds'] += e - s
                totals['raw_clipped_rows'] += 1
                if previous == (u, c) and s <= right:
                    right = max(right, e)
                else:
                    if previous is not None:
                        yield View('merged', *previous, left, right)
                    previous = (u, c)
                    (left, right) = (s, e)
            if previous is not None:
                yield View('merged', *previous, left, right)
        for v in merged_views():
            merged_count += 1
            totals['user_channel_union_seconds'] += v.end - v.start
            mm = list(matcher.match([v]))
            lab = [m for m in mm if m.item_id != '0']
            usable = [m for m in lab if m.airing_id not in bad]
            for (name, ms) in [('any_schedule', mm), ('nonzero_schedule', lab), ('unambiguous_nonzero_schedule', usable)]:
                totals[name + '_union_seconds'] += segment_durations([(m.start, m.end) for m in ms])['union_seconds']
            for m in usable:
                db.execute('INSERT INTO segments VALUES(?,?,?,?,?,?)', (m.user_id, m.airing_id, m.item_id, m.start, m.end, m.programme_seconds))
        db.commit()
        db.execute('CREATE INDEX segment_order ON segments(u,a,s,e)')
        db.commit()
        qualified = {t: Counter() for t in (0.5, 0.8, 0.9)}
        union_q = Counter()
        ratios = NumericSummary(10000, 42)
        usable_users = set()
        interaction_items = set()
        example = None

        def consume(key, segments, d, item):
            nonlocal example
            if key is None:
                return
            sd = segment_durations(segments)
            ratio = sd['longest_block_seconds'] / d
            ratios.add(str(ratio))
            usable_users.add(key[0])
            interaction_items.add(item)
            for t in qualified:
                if ratio >= t:
                    qualified[t][key[0], item] += 1
                if sd['union_seconds'] / d >= t:
                    union_q[str(t)] += 1
            if example is None and ratio >= 0.8 and (len(segments) == 1):
                x = next((x for x in by_channel.get(next((a.channel_id for a in airings if a.row_id == key[1])), []) if x.row_id == key[1]))
                example = {'period': period, 'user_id': key[0], 'schedule_source_period': x.row_id.split(':')[0], 'schedule_csv_record': int(x.row_id.split(':')[1]), 'channel_id': x.channel_id, 'tv_show_id': item, 'airing_wall': [wall(x.start), wall(x.end)], 'merged_view_segment_wall': [wall(segments[0][0]), wall(segments[0][1])], 'overlap_seconds': sd['union_seconds'], 'airing_seconds': d, 'longest_block_fraction': ratio}
        key = None
        segments = []
        d = 0
        item = ''
        for (u, aid, it, s, e, seconds) in db.execute('SELECT u,a,item,s,e,d FROM segments ORDER BY u,a,s,e'):
            if (u, aid) != key:
                consume(key, segments, d, item)
                key = (u, aid)
                segments = []
                d = seconds
                item = it
            segments.append((s, e))
        consume(key, segments, d, item)
        result.update({'full_cleaned_matching': dict(totals), 'merged_user_channel_intervals': merged_count, 'usable_user_airing_longest_block_fraction': ratios.report(), 'users_with_any_usable_overlap': len(usable_users), 'template_users_with_any_usable_overlap': len(templates & usable_users), 'candidate_ids_without_usable_interactions': len(catalog - interaction_items), 'positive_threshold_sensitivity': {}, 'qualified_airings_by_union_threshold': dict(union_q)})
        for (t, q) in qualified.items():
            users = {u for (u, it) in q}
            items = {it for (u, it) in q}
            result['positive_threshold_sensitivity'][str(t)] = {'qualified_user_airings': sum(q.values()), 'user_item_pairs': len(q), 'users': len(users), 'items': len(items), 'template_users': len(templates & users)}
        (args.private_dir / f'qualified_{period}.json').write_text(json.dumps([[u, it, count] for ((u, it), count) in qualified[0.8].items()]))
        prior_items.update(interaction_items)
        if example:
            private_examples.append(example)
        result['elapsed_seconds'] = time.perf_counter() - began
        report['periods'][period] = result
        (args.output_dir / 'matching_audit.json').write_text(json.dumps(report, indent=2))
        print(period, 'completed', result['elapsed_seconds'], flush=True)
        del matcher, airings, by_channel, qualified
    (args.private_dir / 'real_examples.json').write_text(json.dumps(private_examples, indent=2))
    train = json.loads((args.private_dir / 'qualified_11-20.json').read_text())
    valid = json.loads((args.private_dir / 'qualified_21-30.json').read_text())
    tu = {x[0] for x in train}
    vu = {x[0] for x in valid}
    report['cohort'] = {'retained_view_users': db.execute('SELECT COUNT(DISTINCT u) FROM views').fetchone()[0], 'template_users': len(templates), 'validation_users_with_80pct_positive': len(vu), 'validation_users_without_80pct_training_positive': len(vu - tu), 'validation_users_in_template': len(vu & templates), 'template_users_with_80pct_training_positive': len(tu & templates), 'template_users_with_80pct_refit_positive': len((tu | vu) & templates)}
    report['elapsed_seconds'] = time.perf_counter() - start
    report['environment'] = _environment()
    (args.output_dir / 'matching_audit.json').write_text(json.dumps(report, indent=2))
    db.close()
if __name__ == '__main__':
    main()
