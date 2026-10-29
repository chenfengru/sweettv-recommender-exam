import csv
import json
import tempfile
import unittest
from pathlib import Path
from src.audit_data import INPUTS, NumericSummary, build_report, make_parser, parse_timestamp, write_report
from src.csv_io import open_csv


class AuditTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)

    def tearDown(self):
        self.temporary.cleanup()

    def args(self, *extra):
        return make_parser().parse_args(["--data-dir", str(self.root), "--delimiter", ",", *extra])

    def write(self, name, header, rows):
        with (self.root / name).open("w", newline="", encoding="utf-8-sig") as output:
            writer = csv.writer(output)
            writer.writerow(header)
            writer.writerows(rows)

    def test_missing_inputs_report_contains_no_measurements(self):
        report = build_report(self.args())
        self.assertEqual(report["status"], "blocked_missing_inputs")
        self.assertEqual(set(report["missing_inputs"]), set(INPUTS))
        self.assertEqual(report["files"], [])
        write_report(report, self.root / "output")
        saved = json.loads((self.root / "output/data_audit.json").read_text())
        self.assertEqual(saved["files"], [])

    def test_synthetic_known_counts_duplicates_units_and_overlap(self):
        self.write("dataset11-30.csv", ["user_id", "vsetv_id", "start_time", "stop_time", "duraton"],
                   [["001", "7", "100", "160", "60"], ["001", "7", "100", "160", "60"],
                    ["1", "7", "150", "240", "90"], ["002", "8", "300", "300", "0"],
                    ["003", "7", "bad", "350", "NaN"], ["malformed"]])
        for name in list(INPUTS)[1:4]:
            self.write(name, ["channel_id", "start_time", "duration", "tv_show_id", "tv_show_title"],
                       [["7", "100", "1", "A", "Сериал"], ["7", "100", "1", "A", "Сериал"],
                        ["7", "160", "2", "0", "unknown"], ["8", "300", "1", "B", "B"],
                        ["7", "120", "1", "C", "C"]])
        self.write("submission.csv", ["viewer", "items"], [["001", "0"], ["1", "0"]])
        report = build_report(self.args("--view-time-format", "unix-s", "--schedule-time-format", "unix-s",
                                        "--view-duration-unit", "seconds", "--schedule-duration-unit", "minutes",
                                        "--template-user-column", "viewer"))
        self.assertEqual(report["status"], "profiled_review_required")
        views, schedule = report["files"][:2]
        self.assertEqual(views["counts"]["data_records"], 6)
        self.assertEqual(views["counts"]["duplicate_records_beyond_first"], 1)
        self.assertEqual(views["counts"]["malformed_records"], 1)
        self.assertEqual(views["distinct_nonempty_raw_ids"]["user_id"], 4)
        self.assertEqual(views["issues"]["nonpositive_view_interval"], 1)
        self.assertEqual(views["issues"]["start_time_conversion_failed"], 1)
        self.assertEqual(views["duration_raw_units"]["invalid_count"], 1)
        self.assertEqual(schedule["nonzero_schedule_row_fraction"]["fraction"], 4 / 5)
        self.assertEqual(schedule["schedule_airtime"]["all"]["union_seconds_summed_over_channels"], 240)
        self.assertEqual(schedule["schedule_airtime"]["labelled"]["union_seconds_summed_over_channels"], 140)
        self.assertEqual(schedule["schedule_airtime"]["all"]["rows_overlapping_any_earlier_interval"], 3)
        self.assertEqual(report["files"][-1]["distinct_nonempty_raw_ids"]["viewer"], 2)

    def test_units_and_template_roles_are_not_guessed(self):
        self.write("dataset11-30.csv", ["user_id", "vsetv_id", "start_time", "stop_time", "duraton"],
                   [["001", "7", "1600000000000", "1600000060000", "60"]])
        self.write("submission.csv", ["viewer", "items"], [["001", "0"]])
        report = build_report(self.args())
        view, template = report["files"]
        self.assertIsNone(view["timestamp_conversion"])
        self.assertEqual(view["normalized_timestamp_ranges_seconds"], {})
        self.assertEqual(template["template_schema_status"], "header_observed_column_roles_unresolved")

    def test_explicit_time_units_and_timezone(self):
        self.assertEqual(parse_timestamp("1600000000000", "unix-ms"), 1600000000)
        self.assertEqual(parse_timestamp("2020-01-01T03:00:00+03:00", "iso"), 1577836800)
        self.assertEqual(parse_timestamp("2020-01-01T03:00:00", "iso", "Europe/Moscow"), 1577836800)
        for value, fmt, zone in [("2020-01-01T03:00:00", "iso", None), ("bad", "unix-s", None),
                                  ("2020-11-01T01:30:00", "iso", "America/New_York"),
                                  ("2020-03-08T02:30:00", "iso", "America/New_York")]:
            with self.assertRaises(ValueError):
                parse_timestamp(value, fmt, zone)

    def test_reservoir_sample_label_and_reproducibility(self):
        first, second = NumericSummary(10, 42), NumericSummary(10, 42)
        for value in range(100):
            first.add(str(value))
            second.add(str(value))
        self.assertEqual(first.report(), second.report())
        self.assertTrue(first.report()["quantiles_sampled"])
        self.assertEqual(first.report()["quantile_sample_size"], 10)
        self.assertEqual(first.report()["minimum"], 0)
        self.assertEqual(first.report()["maximum"], 99)

    def test_delimiter_encoding_and_bad_schema(self):
        path = self.root / "semicolon.csv"
        path.write_text("channel_id;title\n007;Новости\n", encoding="utf-16")
        with open_csv(path) as (header, reader, meta):
            self.assertEqual(header, ["channel_id", "title"])
            self.assertEqual(next(reader), ["007", "Новости"])
            self.assertEqual(meta["delimiter"], ";")
        self.write("dataset11-30.csv", ["wrong", "columns"], [["1", "2"]])
        report = build_report(self.args())
        self.assertEqual(report["status"], "input_errors")
        self.assertIn("missing columns", report["files"][0]["error"])


if __name__ == "__main__":
    unittest.main()
