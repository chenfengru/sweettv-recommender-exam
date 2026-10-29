"""Validate an actual template and prediction CSV, without contacting Kaggle."""

import argparse
import json
from pathlib import Path
from .csv_io import checked_rows, is_zero_id, open_csv, require_columns, sha256_file


def candidate_ids(schedule_paths, *, encoding=None, delimiter=None):
    allowed = set()
    for path in schedule_paths:
        with open_csv(path, encoding=encoding, delimiter=delimiter) as (header, reader, _):
            require_columns(header, {"tv_show_id"}, Path(path).name)
            for number, row in checked_rows(reader, header, Path(path).name):
                item = row["tv_show_id"]
                if not item.strip() or is_zero_id(item):
                    continue
                if item != item.strip() or any(char.isspace() for char in item):
                    raise ValueError(f"{Path(path).name}: record {number} has whitespace in programme ID")
                allowed.add(item)
    if len(allowed) < 5:
        raise ValueError("prediction-window schedules contain fewer than five valid candidate IDs")
    return allowed


def validate_submission(template_path, prediction_path, candidates, *, user_column,
                        prediction_column, encoding=None, delimiter=None):
    if user_column == prediction_column:
        raise ValueError("user and prediction columns must differ")
    if len(candidates) < 5 or any(not isinstance(item, str) or not item or
                                 any(c.isspace() for c in item) or is_zero_id(item) for item in candidates):
        raise ValueError("candidate set must contain at least five valid nonzero string IDs")
    users = []
    with open_csv(template_path, encoding=encoding, delimiter=delimiter) as (header, reader, _):
        template_header = header
        if len(header) != 2 or set(header) != {user_column, prediction_column}:
            raise ValueError("template must have exactly the two explicitly named columns; inspect its actual schema")
        for number, row in checked_rows(reader, header, Path(template_path).name):
            user = row[user_column]
            if not user or user != user.strip():
                raise ValueError(f"template record {number}: empty user ID or surrounding whitespace")
            users.append(user)
    if not users or len(set(users)) != len(users):
        raise ValueError("template must have nonempty, unique user IDs")
    seen_items, rows = set(), 0
    with open_csv(prediction_path, encoding=encoding, delimiter=delimiter) as (header, reader, _):
        if header != template_header:
            raise ValueError("prediction header/order differs from the template")
        for number, row in checked_rows(reader, header, Path(prediction_path).name):
            if rows >= len(users) or row[user_column] != users[rows]:
                raise ValueError(f"prediction record {number}: user/order differs from the template")
            text = row[prediction_column]
            items = text.split(" ")
            if len(items) != 5 or any(not item or any(char.isspace() for char in item) for item in items):
                raise ValueError(f"prediction record {number}: expected exactly five IDs separated by single spaces")
            if len(set(items)) != 5:
                raise ValueError(f"prediction record {number}: duplicate programme IDs")
            if any(is_zero_id(item) or item not in candidates for item in items):
                raise ValueError(f"prediction record {number}: zero or unavailable programme ID")
            seen_items.update(items)
            rows += 1
    if rows != len(users):
        raise ValueError(f"prediction has {rows} users; template has {len(users)}")
    return {"status": "valid", "users": rows, "k": 5, "candidate_ids": len(candidates),
            "distinct_recommended_ids": len(seen_items),
            "template_sha256": sha256_file(Path(template_path)),
            "prediction_sha256": sha256_file(Path(prediction_path))}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--template", type=Path, required=True)
    parser.add_argument("--predictions", type=Path, required=True)
    parser.add_argument("--schedule", type=Path, nargs="+", required=True,
                        help="Only the schedule files for the prediction window")
    parser.add_argument("--user-column", required=True)
    parser.add_argument("--prediction-column", required=True)
    parser.add_argument("--encoding")
    parser.add_argument("--delimiter")
    args = parser.parse_args(argv)
    try:
        options = {"encoding": args.encoding, "delimiter": args.delimiter}
        result = validate_submission(args.template, args.predictions,
                                    candidate_ids(args.schedule, **options),
                                    user_column=args.user_column,
                                    prediction_column=args.prediction_column, **options)
    except (ValueError, OSError) as exc:
        print(json.dumps({"status": "invalid", "error": str(exc)}, ensure_ascii=False))
        return 2
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
