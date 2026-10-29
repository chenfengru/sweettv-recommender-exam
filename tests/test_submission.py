import csv
import tempfile
import unittest
from pathlib import Path
from src.validate_submission import candidate_ids, validate_submission


class SubmissionTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.template = self.root / "template.csv"
        self.prediction = self.root / "prediction.csv"
        self.header = ["viewer", "recommendations"]
        self.write(self.template, self.header, [["001", "0 0 0 0 0"], ["1", "0 0 0 0 0"]])
        self.allowed = {"A", "B", "C", "D", "E", "F"}

    def tearDown(self):
        self.temporary.cleanup()

    def write(self, path, header, rows):
        with path.open("w", newline="", encoding="utf-8") as output:
            writer = csv.writer(output)
            writer.writerow(header)
            writer.writerows(rows)

    def validate(self):
        return validate_submission(self.template, self.prediction, self.allowed,
                                   user_column="viewer", prediction_column="recommendations", delimiter=",")

    def test_valid_actual_template_order_and_text_ids(self):
        self.write(self.prediction, self.header, [["001", "A B C D E"], ["1", "F E D C B"]])
        result = self.validate()
        self.assertEqual(result["users"], 2)
        self.assertEqual(result["distinct_recommended_ids"], 6)
        self.assertEqual(len(result["prediction_sha256"]), 64)

    def test_bad_recommendation_lists(self):
        for text in ("A B C D", "A B C D E F", "A A B C D", "A B C D X", "A B C D 0",
                     "A  B C D E", " A B C D E", "A B C D E ", "A\tB C D E"):
            with self.subTest(text=text):
                self.write(self.prediction, self.header, [["001", text], ["1", "A B C D E"]])
                with self.assertRaises(ValueError):
                    self.validate()

    def test_missing_extra_reordered_or_coerced_users(self):
        for users in (["001"], ["001", "1", "extra"], ["1", "001"], ["1", "1"], ["001", "001"]):
            with self.subTest(users=users):
                self.write(self.prediction, self.header, [[user, "A B C D E"] for user in users])
                with self.assertRaises(ValueError):
                    self.validate()

    def test_wrong_header_or_malformed_row(self):
        self.write(self.prediction, list(reversed(self.header)), [["A B C D E", "001"]])
        with self.assertRaises(ValueError):
            self.validate()
        self.write(self.prediction, self.header, [["001", "A B C D E", "extra"]])
        with self.assertRaises(ValueError):
            self.validate()

    def test_duplicate_template_and_invalid_candidates(self):
        self.write(self.prediction, self.header, [["001", "A B C D E"], ["1", "F E D C B"]])
        self.write(self.template, self.header, [["001", "0"], ["001", "0"]])
        with self.assertRaises(ValueError):
            self.validate()
        self.allowed = {"A", "B", "C"}
        with self.assertRaises(ValueError):
            self.validate()

    def test_candidates_use_only_explicit_schedule_and_exclude_zero(self):
        schedule = self.root / "future.csv"
        self.write(schedule, ["tv_show_id", "channel_id"], [[item, "ch"] for item in ["0", "0.0", "", "001", "1", "A", "B", "C"]])
        self.assertEqual(candidate_ids([schedule], delimiter=","), {"001", "1", "A", "B", "C"})


if __name__ == "__main__":
    unittest.main()
