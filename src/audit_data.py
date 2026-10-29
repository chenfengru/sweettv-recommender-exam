"""Stream the five inputs into aggregate diagnostics; never infer time units.

The SQLite scratch index makes cardinalities and duplicate counts exact without
retaining all rows in RAM. It can require disk space comparable to the inputs.
Unit choices are explicit hypotheses until checked against source evidence.
"""

import argparse
import json
import math
import platform
import random
import sqlite3
import subprocess
import sys
import tempfile
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo
from .csv_io import is_zero_id, open_csv, require_columns, sha256_file


INPUTS = {
    "dataset11-30.csv": ("views", 5821987),
    "export_arh_11-20-final.csv": ("schedule", 1074235),
    "export_arh_21-30-final.csv": ("schedule", 1074394),
    "export_arh_31-42-final.csv": ("schedule", 1295378),
    "submission.csv": ("template", 1260),
}
REQUIRED = {
    "views": {"user_id", "vsetv_id", "start_time", "stop_time", "duraton"},
    "schedule": {"channel_id", "start_time", "duration", "tv_show_id"},
}
UNIT_SECONDS = {"seconds": 1, "minutes": 60, "milliseconds": 0.001}


def number(value):
    result = float(value)
    if not math.isfinite(result):
        raise ValueError("non-finite numeric value")
    return result


def parse_timestamp(value, representation, naive_timezone=None):
    """Explicit conversion only; numeric timestamps have no guessed unit."""
    if representation == "unix-s":
        return number(value)
    if representation == "unix-ms":
        return number(value) / 1000
    if representation != "iso":
        raise ValueError("timestamp representation must be explicitly selected")
    instant = datetime.fromisoformat(value)
    if instant.tzinfo is None:
        if naive_timezone is None:
            raise ValueError("naive ISO timestamps require an explicit source timezone")
        zone = ZoneInfo(naive_timezone)
        first, second = instant.replace(tzinfo=zone, fold=0), instant.replace(tzinfo=zone, fold=1)
        if first.utcoffset() != second.utcoffset():
            raise ValueError("ambiguous or nonexistent local time requires source-specific resolution")
        instant = first
    result = instant.timestamp()
    if not math.isfinite(result):
        raise ValueError("non-finite timestamp")
    return result


class NumericSummary:
    def __init__(self, sample_size, seed):
        self.capacity = sample_size
        self.rng = random.Random(seed)
        self.sample = []
        self.count = self.missing = self.invalid = self.zero = self.negative = 0
        self.minimum = self.maximum = None
        self.mean = 0.0

    def add(self, value):
        if not value.strip():
            self.missing += 1
            return None
        try:
            parsed = number(value)
        except (ValueError, OverflowError):
            self.invalid += 1
            return None
        self.count += 1
        self.minimum = parsed if self.minimum is None else min(self.minimum, parsed)
        self.maximum = parsed if self.maximum is None else max(self.maximum, parsed)
        self.mean = self.mean * ((self.count - 1) / self.count) + parsed / self.count
        self.zero += parsed == 0
        self.negative += parsed < 0
        if len(self.sample) < self.capacity:
            self.sample.append(parsed)
        else:
            index = self.rng.randrange(self.count)
            if index < self.capacity:
                self.sample[index] = parsed
        return parsed

    def report(self):
        ordered = sorted(self.sample)
        quantiles = {}
        for q in (0.5, 0.9, 0.99):
            position = (len(ordered) - 1) * q
            low = math.floor(position)
            quantiles[str(q)] = (ordered[low] + (ordered[min(low + 1, len(ordered) - 1)] - ordered[low]) *
                                 (position - low)) if ordered else None
        return {"numeric_count": self.count, "missing_count": self.missing,
                "invalid_count": self.invalid, "zero_count": self.zero, "negative_count": self.negative,
                "minimum": self.minimum, "maximum": self.maximum,
                "mean": self.mean if self.count else None,
                "quantiles": quantiles, "quantile_sample_size": len(ordered),
                "quantile_method": "uniform reservoir, linear interpolation; approximate if sampled",
                "quantiles_sampled": self.count > self.capacity}


class TimeSummary:
    def __init__(self):
        self.kinds = Counter()
        self.ranges = {}

    def add(self, value):
        if not value.strip():
            self.kinds["missing"] += 1
            return
        try:
            parsed = number(value)
            kind = "numeric_unit_unresolved"
        except (ValueError, OverflowError):
            try:
                parsed_date = datetime.fromisoformat(value)
                if parsed_date.tzinfo is None:
                    kind, parsed = "iso_naive_timezone_unresolved", parsed_date.isoformat()
                else:
                    kind, parsed = "iso_offset", parsed_date.astimezone(timezone.utc).isoformat()
            except ValueError:
                self.kinds["invalid_or_unsupported"] += 1
                return
        self.kinds[kind] += 1
        if kind not in self.ranges:
            self.ranges[kind] = {"minimum": parsed, "maximum": parsed}
        else:
            self.ranges[kind]["minimum"] = min(self.ranges[kind]["minimum"], parsed)
            self.ranges[kind]["maximum"] = max(self.ranges[kind]["maximum"], parsed)

    def report(self):
        return {"representations": dict(self.kinds), "ranges_by_representation": self.ranges}


def _union_airtime(connection, labelled=False):
    condition = "WHERE labelled = 1" if labelled else ""
    query = f"SELECT channel, start, end FROM intervals {condition} ORDER BY channel, start, end"
    previous_channel = None
    start = end = total = 0.0
    overlaps = count = 0
    for channel, next_start, next_end in connection.execute(query):
        count += 1
        if channel != previous_channel:
            total += end - start
            start, end, previous_channel = next_start, next_end, channel
        elif next_start <= end:
            overlaps += next_start < end
            end = max(end, next_end)
        else:
            total += end - start
            start, end = next_start, next_end
    return {"union_seconds_summed_over_channels": total + end - start,
            "interval_rows": count, "rows_overlapping_any_earlier_interval": overlaps}


def profile_file(path, role, args):
    started = time.perf_counter()
    sha256 = sha256_file(path)
    time_format = args.view_time_format if role == "views" else args.schedule_time_format
    duration_unit = args.view_duration_unit if role == "views" else args.schedule_duration_unit
    duration_field = "duraton" if role == "views" else "duration"
    normalized = bool(time_format) and bool(duration_unit)
    channels, programmes = set(), set()  # Small channel/catalogue sets; never user histories.
    counts, issues, id_types, whitespace = Counter(), Counter(), {}, Counter()
    timestamps, normalized_ranges = {}, {}
    duration = NumericSummary(args.sample_size, args.seed)
    residual = NumericSummary(args.sample_size, args.seed + 1)
    nulls = Counter()
    with tempfile.TemporaryDirectory(prefix="sweettv-audit-", dir=args.scratch_dir) as tmp:
        connection = sqlite3.connect(str(Path(tmp) / "index.sqlite"))
        try:
            connection.execute("PRAGMA cache_size = -8192")
            connection.execute("PRAGMA temp_store = FILE")
            connection.execute("PRAGMA journal_mode = OFF")
            connection.execute("CREATE TABLE seen_rows (payload TEXT PRIMARY KEY) WITHOUT ROWID")
            connection.execute("CREATE TABLE ids (field TEXT, value TEXT, PRIMARY KEY(field, value)) WITHOUT ROWID")
            connection.execute("CREATE TABLE intervals (channel TEXT, start REAL, end REAL, labelled INTEGER)")
            with open_csv(path, encoding=args.encoding, delimiter=args.delimiter) as (header, reader, csv_format):
                if role in REQUIRED:
                    require_columns(header, REQUIRED[role], path.name)
                if role == "template":
                    if len(header) != 2:
                        raise ValueError(f"{path.name}: expected a two-column template; inspect the schema")
                    if args.template_user_column:
                        require_columns(header, {args.template_user_column}, path.name)
                    id_fields = [args.template_user_column] if args.template_user_column else []
                else:
                    id_fields = sorted(set(header) & {"user_id", "vsetv_id", "channel_id", "tv_show_id"})
                id_types = {field: Counter() for field in id_fields}
                timestamps = {field: TimeSummary() for field in header if field in {"start_time", "stop_time"}}
                for record_number, values in enumerate(reader, 2):
                    counts["data_records"] += 1
                    inserted = connection.execute("INSERT OR IGNORE INTO seen_rows VALUES (?)",
                                                  (json.dumps(values, ensure_ascii=False),)).rowcount
                    counts["duplicate_records_beyond_first"] += 1 - inserted
                    if len(values) != len(header):
                        counts["malformed_records"] += 1
                        continue
                    counts["schema_valid_records"] += 1
                    row = dict(zip(header, values))
                    for field, value in row.items():
                        nulls[field] += not value.strip()
                        whitespace[field] += value != value.strip()
                    for field in id_fields:
                        value = row[field]
                        if not value.strip():
                            id_types[field]["missing"] += 1
                            continue
                        connection.execute("INSERT OR IGNORE INTO ids VALUES (?, ?)", (field, value))
                        id_types[field]["integer_text" if value.isdecimal() else "other_text"] += 1
                    for field, stats in timestamps.items():
                        stats.add(row[field])
                    if role == "template":
                        continue
                    channel = row["vsetv_id" if role == "views" else "channel_id"]
                    if channel.strip():
                        channels.add(channel)
                    labelled = False
                    if role == "schedule":
                        item = row["tv_show_id"]
                        if not item.strip():
                            counts["missing_programme_id_records"] += 1
                        elif is_zero_id(item):
                            counts["zero_programme_id_records"] += 1
                        else:
                            counts["nonzero_programme_id_records"] += 1
                            programmes.add(item)
                            labelled = True
                    raw_duration = duration.add(row[duration_field])
                    if raw_duration is not None and raw_duration <= 0:
                        issues["nonpositive_duration"] += 1
                    converted = {}
                    if time_format:
                        for field in timestamps:
                            try:
                                converted[field] = parse_timestamp(row[field], time_format, args.naive_timezone)
                                current = normalized_ranges.setdefault(field, [converted[field], converted[field]])
                                current[0], current[1] = min(current[0], converted[field]), max(current[1], converted[field])
                            except (ValueError, OverflowError, OSError):
                                issues[f"{field}_conversion_failed"] += 1
                    if duration_unit and raw_duration is not None:
                        seconds = raw_duration * UNIT_SECONDS[duration_unit]
                        issues["duration_above_24h_review_required"] += seconds > 86400
                    if role == "views" and len(converted) == 2:
                        elapsed = converted["stop_time"] - converted["start_time"]
                        if elapsed <= 0:
                            issues["nonpositive_view_interval"] += 1
                        if duration_unit and raw_duration is not None:
                            difference = raw_duration * UNIT_SECONDS[duration_unit] - elapsed
                            residual.add(str(difference))
                            issues["duration_disagrees_with_interval_over_1s"] += abs(difference) > 1
                    elif (role == "schedule" and normalized and "start_time" in converted and
                          raw_duration is not None and raw_duration > 0 and channel.strip()):
                        start = converted["start_time"]
                        end = start + raw_duration * UNIT_SECONDS[duration_unit]
                        if not math.isfinite(end) or end <= start:
                            issues["invalid_schedule_end"] += 1
                        else:
                            connection.execute("INSERT INTO intervals VALUES (?, ?, ?, ?)",
                                               (channel, start, end, int(labelled)))
                    if counts["data_records"] % 50000 == 0:
                        connection.commit()
                connection.commit()
            distinct = {field: value for field, value in connection.execute("SELECT field, COUNT(*) FROM ids GROUP BY field")}
            result = {
                "filename": path.name, "role": role, "status": "profiled",
                "sha256": sha256, "bytes": path.stat().st_size, "csv_format": csv_format,
                "header": header, "counts": dict(counts),
                "missing_fields": {field: nulls[field] for field in header},
                "missingness_denominator": counts["schema_valid_records"],
                "surrounding_whitespace_counts": dict(whitespace),
                "identifier_representation_counts": {field: dict(value) for field, value in id_types.items()},
                "distinct_nonempty_raw_ids": {field: distinct.get(field, 0) for field in id_fields},
                "cardinality_and_duplicate_method": "exact SQLite keys; parsed field strings preserved; per file",
                "timestamps": {field: value.report() for field, value in timestamps.items()},
                "timestamp_conversion": time_format, "duration_unit_override": duration_unit,
                "normalized_timestamp_ranges_seconds": normalized_ranges,
                "issues": dict(issues),
            }
            if counts["malformed_records"]:
                result["issues"]["malformed_csv_records"] = counts["malformed_records"]
            if not counts["schema_valid_records"]:
                result["issues"]["no_schema_valid_data_records"] = 1
            for field in REQUIRED.get(role, set()):
                if nulls[field]:
                    result["issues"][f"missing_required_field_{field}"] = nulls[field]
            for field, stats in timestamps.items():
                invalid = stats.kinds["invalid_or_unsupported"]
                if invalid:
                    result["issues"][f"{field}_invalid_or_unsupported"] = invalid
            if role != "template":
                result["duration_field"] = duration_field
                result["duration_raw_units"] = duration.report()
                if duration.invalid:
                    result["issues"]["invalid_numeric_duration"] = duration.invalid
                if role == "views" and normalized:
                    result["duration_minus_interval_seconds"] = residual.report()
            else:
                result["template_user_column"] = args.template_user_column
                result["template_schema_status"] = "explicit_user_column" if id_fields else "header_observed_column_roles_unresolved"
                if id_fields:
                    result["issues"]["duplicate_or_empty_template_users"] = counts["schema_valid_records"] - distinct.get(id_fields[0], 0)
            if role == "schedule":
                denominator = counts["schema_valid_records"]
                result["nonzero_schedule_row_fraction"] = {
                    "numerator": counts["nonzero_programme_id_records"], "denominator": denominator,
                    "fraction": counts["nonzero_programme_id_records"] / denominator if denominator else None,
                }
                if normalized:
                    result["schedule_airtime"] = {"all": _union_airtime(connection),
                                                  "labelled": _union_airtime(connection, True),
                                                  "unit_status": "based on explicit overrides, not independently verified"}
            result["elapsed_seconds_including_hashing"] = time.perf_counter() - started
            return result, {"channels": channels, "programmes": programmes}
        finally:
            connection.close()


def _environment():
    try:
        import resource
        peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        peak_bytes = peak if sys.platform == "darwin" else peak * 1024
    except (ImportError, AttributeError):
        peak_bytes = None
    root = Path(__file__).resolve().parents[1]
    try:
        commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True, stderr=subprocess.DEVNULL).strip()
        dirty = bool(subprocess.check_output(["git", "status", "--porcelain"], cwd=root, text=True))
    except (OSError, subprocess.CalledProcessError):
        commit, dirty = None, None
    return {"python": sys.version, "platform": platform.platform(),
            "code_base_commit": commit, "working_tree_dirty": dirty,
            "source_sha256": {str(path.relative_to(root)): sha256_file(path) for path in sorted((root / "src").glob("*.py"))},
            "peak_process_rss_bytes": peak_bytes,
            "memory_method": "resource.ru_maxrss process-lifetime high-water mark; unavailable on unsupported platforms"}


def build_report(args):
    started = time.perf_counter()
    missing = [name for name in INPUTS if not (args.data_dir / name).is_file()]
    report = {
        "audit_version": "0.1", "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "blocked_missing_inputs" if missing else "profiled",
        "data_source": "original competition files only; no synthetic replacement",
        "configuration": {key: str(value) if isinstance(value, Path) else value for key, value in vars(args).items()},
        "instructor_reported_row_counts_not_measurements": {name: value[1] for name, value in INPUTS.items()},
        "missing_inputs": missing, "files": [],
        "unresolved": [
            "Match real view and schedule timestamps/channels; prove units from source and diagnostics.",
            "Confirm template column roles and exact calendar cutoffs.",
            "Confirm continuous watching and most-frequent-five target semantics; historical code is not the evaluator.",
            "Measure matched view rows, union viewing seconds, usable template-user history and candidate cold start.",
            "Choose positive thresholds and interaction weights only after real duration/coverage diagnostics.",
        ],
    }
    internal = {}
    for name, (role, _) in INPUTS.items():
        path = args.data_dir / name
        if not path.is_file():
            continue
        try:
            result, internal[name] = profile_file(path, role, args)
            report["files"].append(result)
        except (ValueError, OSError, sqlite3.Error) as exc:
            report["files"].append({"filename": name, "status": "error", "error": str(exc)})
    view = internal.get("dataset11-30.csv")
    train_schedules = [internal[name] for name in ("export_arh_11-20-final.csv", "export_arh_21-30-final.csv") if name in internal]
    if view is not None and len(train_schedules) == 2:
        schedule_channels = set.union(*(item["channels"] for item in train_schedules))
        report["channel_id_diagnostic"] = {
            "view_channel_ids": len(view["channels"]),
            "view_channel_ids_found_in_training_schedules": len(view["channels"] & schedule_channels),
            "interpretation": "raw string equality only; not proof of channel mapping or time-matched coverage",
        }
    if any(item["status"] == "error" for item in report["files"]):
        report["status"] = "input_errors"
    elif not missing:
        report["status"] = "profiled_review_required"
    report["elapsed_seconds"] = time.perf_counter() - started
    report["environment"] = _environment()
    return report


def write_report(report, output_dir):
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "data_audit.json").write_text(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    lines = ["# Data audit", "", f"Status: **{report['status']}**", "",
             "This report contains aggregate file diagnostics only. Instructor counts are separately labelled in JSON.", ""]
    if report["missing_inputs"]:
        lines += ["Missing original inputs:", ""] + [f"- `{name}`" for name in report["missing_inputs"]] + [""]
    if report["files"]:
        lines += ["| File | Status | Measured data records | Duplicates beyond first |", "| --- | --- | ---: | ---: |"]
        for item in report["files"]:
            counts = item.get("counts", {})
            lines.append(f"| {item['filename']} | {item['status']} | {counts.get('data_records', 'not measured')} | {counts.get('duplicate_records_beyond_first', 'not measured')} |")
        lines += ["", "See JSON for actual headers, denominators, unit overrides, parsing issues, samples and timing.", ""]
        for item in report["files"]:
            if item.get("error"):
                lines.append(f"- `{item['filename']}`: {item['error']}")
            if any(item.get("issues", {}).values()):
                lines.append(f"- `{item['filename']}`: issues require review; no rows were silently repaired or removed.")
        lines.append("")
    else:
        lines += ["**No real-data statistics were measured.** No model was trained or submitted.", ""]
    lines += ["Unresolved before modelling:", ""] + [f"- {item}" for item in report["unresolved"]]
    lines += ["", "Synthetic checks are recorded separately; they do not verify the competition data or constitute student verification.", ""]
    (output_dir / "data_audit.md").write_text("\n".join(lines), encoding="utf-8")


def make_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, default=Path("results"))
    parser.add_argument("--scratch-dir", type=Path, help="Existing local directory for disposable SQLite indexes")
    parser.add_argument("--encoding", help="Explicit legacy encoding if strict UTF-8/BOM detection fails")
    parser.add_argument("--delimiter", help="One-character override after inspecting the source")
    parser.add_argument("--template-user-column", help="Actual header name; never guessed")
    parser.add_argument("--view-time-format", choices=("unix-s", "unix-ms", "iso"))
    parser.add_argument("--schedule-time-format", choices=("unix-s", "unix-ms", "iso"))
    parser.add_argument("--view-duration-unit", choices=tuple(UNIT_SECONDS))
    parser.add_argument("--schedule-duration-unit", choices=tuple(UNIT_SECONDS))
    parser.add_argument("--naive-timezone", help="Verified source timezone for naive ISO timestamps, not your computer timezone")
    parser.add_argument("--sample-size", type=int, default=10000)
    parser.add_argument("--seed", type=int, default=42)
    return parser


def main(argv=None):
    parser = make_parser()
    args = parser.parse_args(argv)
    if args.sample_size < 1:
        parser.error("--sample-size must be positive")
    if args.naive_timezone:
        try:
            ZoneInfo(args.naive_timezone)
        except (KeyError, ValueError):
            parser.error("--naive-timezone must be a valid IANA timezone")
    report = build_report(args)
    write_report(report, args.output_dir)
    print(json.dumps({"status": report["status"], "files_profiled": len(report["files"]),
                      "missing_inputs": report["missing_inputs"], "report": str(args.output_dir / "data_audit.json")}, indent=2))
    has_issues = any(any(item.get("issues", {}).values()) for item in report["files"])
    return 2 if report["missing_inputs"] or report["status"] == "input_errors" or has_issues else 0


if __name__ == "__main__":
    raise SystemExit(main())
