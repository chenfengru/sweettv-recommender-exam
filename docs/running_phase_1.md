# Running Phase 1

## Current evidence

The foundation code has been exercised only with small synthetic fixtures. The original competition CSVs are absent. `results/data_audit.json` records this actual blocker and keeps instructor-reported row counts in a separate field; it contains no measured competition-data statistics. `results/phase1_checks.json` records executed synthetic checks, source hashes, environment, and timing.

No model, feature pipeline, target construction, full-data interval join, prediction CSV, or Kaggle submission exists yet. Performance on synthetic tests is not a full-data performance benchmark.

## Environment and first commands

Python 3.11+; only the standard library is used. On systems without IANA timezone data, named-zone parsing requires installing that database before using `--naive-timezone`. Numeric Unix times and ISO strings with explicit offsets do not require a named zone.

Keep the data in the existing local course workspace. On the user's Mac, create the dedicated directory and extract the five CSVs there:

```bash
SWEETTV_DATA_DIR="$HOME/LLM4Rec-Course-codex/data/sweettv/raw"
mkdir -p "$SWEETTV_DATA_DIR"
```

From the exam repository root, use that external data location:

```bash
SWEETTV_DATA_DIR="$HOME/LLM4Rec-Course-codex/data/sweettv/raw"
python -m unittest discover -s tests -v
python -m src.audit_data --data-dir "$SWEETTV_DATA_DIR" --output-dir results
```

Put the five original files from [the competition](https://www.kaggle.com/competitions/sweettv-tv-program-recommender/data) directly in that `raw/` directory; see [the file list and local ignore instructions](../data/README.md). Keep raw files and credentials out of Git. The audit does not download data or submit anything. No code change or duplicate copy into this exam repository is needed: `--data-dir` already accepts an external directory.

The committed missing-input report used `data/raw` in the assistant workspace before this location preference was recorded. Preserve it as historical execution evidence. The user's Mac directory has not been inspected or created from this environment; rerun the command locally to obtain an actual data audit.

The audit writes `data_audit.json` and `data_audit.md`. Exit code 2 means missing inputs, parsing failures, or flagged data issues needing review. Exit code 0 means profiling completed without those flags; it does **not** prove the units or modelling protocol are correct. Existing reports in the output directory are replaced; choose another `--output-dir` to preserve a previous run.

## Inspect before converting

The first run discovers headers, delimiters, and timestamp representations. Encoding defaults to UTF-8 with BOM handling or BOM-marked UTF-16; other encodings require an explicit `--encoding`. `--delimiter` accepts a single character. Detection errors fail clearly instead of silently changing parsing rules.

Check the JSON's actual headers, raw time ranges, raw duration diagnostics, and ID representation counts. IDs remain strings: `001` and `1` are distinct. Empty/whitespace values and malformed records are counted; no rows are silently repaired.

Do not copy unit choices from a synthetic example. Once source evidence and actual values support them, rerun with the appropriate options:

- `--view-time-format unix-s`, `unix-ms`, or `iso`
- `--schedule-time-format unix-s`, `unix-ms`, or `iso`
- `--view-duration-unit seconds`, `minutes`, or `milliseconds`
- `--schedule-duration-unit seconds`, `minutes`, or `milliseconds`
- `--naive-timezone` only for ISO strings without an offset, using the verified source zone
- `--template-user-column` using the real template's header

Specifying a unit is a hypothesis, not independent verification. Check the residual between declared view duration and `stop_time - start_time`, schedule overlaps/gaps, and source examples before accepting it. The original `duraton` spelling is retained at input; it refers to viewing-interval duration, not programme duration. Naive DST gaps/ambiguous times fail rather than selecting a fold silently.

## Measurement details and costs

- Counts, missingness, per-file parsed-row duplicates, and per-field raw-string cardinalities use all successfully parsed records. Duplicate counts include copies beyond the first. Cross-file duplicates are not measured.
- Missingness uses schema-valid records as its denominator. Malformed records remain separately visible.
- Duration min/max/counts use the full column. Quantiles use a uniform reservoir (default 10,000 values, seed 42); the report explicitly says when they are sampled. Numeric summaries use floating-point arithmetic; identifiers do not.
- SQLite indexes keep duplicate/cardinality keys on disk with an 8 MiB page cache. Allow temporary disk space comparable to the CSVs, possibly larger due to index overhead. `--scratch-dir` can select an existing directory with sufficient free space. The actual full-data cost is not yet measured.
- Normalized schedule airtime uses a per-channel interval union, so duplicate/overlapping schedule rows do not double-count time. This is schedule airtime, **not matched viewing-time coverage**.
- Channel overlap uses exact raw ID equality; it does not establish the channel mapping or time alignment.
- Reports contain aggregate diagnostics, no original rows or user-ID lists. User histories, if later inspected, must stay in ignored storage.
- Source hashes identify the code used even when the recorded base commit has uncommitted changes. Peak RSS is a process-lifetime high-water mark, not a per-model allocation measurement.

## Interval matching and metric contracts

`src/intervals.py` accepts already normalized, common-unit finite endpoints. Intervals are half-open. It matches multiple airings on the same channel, excludes missing/zero programme IDs by default, and clips views at a supplied cutoff. Duplicate source rows are retained. The indexed matcher streams one view's matches at a time without a global channel-only Cartesian product. Its schedule index still scales with the number of airings.

`segment_durations` separates union time, longest merged block, and longest original segment. Touching intervals merge for the union/block diagnostic; this does not establish uninterrupted watching without a channel switch. The target continuity rule remains unresolved.

`src/metrics.py` uses distinct truth IDs. Repeated predictions earn no extra hits. Empty truth gives AP=0. MAP requires exactly the same nonempty user-key set on both sides; it never silently drops users. The modelling pipeline must explicitly construct the agreed evaluation cohort first.

## Prediction validation after model implementation

Use the actual template and only the schedule files for the prediction window. Replace the two column-name placeholders after inspecting the template:

```bash
SWEETTV_DATA_DIR="$HOME/LLM4Rec-Course-codex/data/sweettv/raw"
python -m src.validate_submission \
  --template "$SWEETTV_DATA_DIR/submission.csv" \
  --predictions submissions/final.csv \
  --schedule "$SWEETTV_DATA_DIR/export_arh_31-42-final.csv" \
  --user-column ACTUAL_USER_COLUMN \
  --prediction-column ACTUAL_PREDICTION_COLUMN
```

`submissions/final.csv` does not exist yet; the command is an example for the later stage. Validation checks the two-column header and order against the template, preserves all template users, requires five distinct nonzero available IDs separated by single spaces, and returns input/output hashes. Extra or missing users, unknown IDs, duplicates, malformed rows, and leading/trailing whitespace fail. It does not verify model quality or submit to Kaggle.

## Next decision

Run the first audit command on the real inputs. Then verify units/channel mapping, quantify actual matching coverage, settle target semantics and exact temporal boundaries, and record a data-based threshold/weight recommendation. Only then start the shared-protocol popularity, personal-frequency, CBF, and implicit-MF comparisons.
