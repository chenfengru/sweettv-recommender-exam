# First Codex task: audit data and verify the evaluation foundations

This is a ready-to-use implementation brief. The scripts and outputs listed below are **requested deliverables, not files already implemented**.

## Objective

Read AGENTS.md and the three planning documents. Implement a bounded, reproducible audit of the SWEET.TV inputs and a small verification of interval matching and MAP@5. Do not start model training or Kaggle submission in this phase.

## Inputs

Expect the five original files listed in data/README.md under data/raw/. If they are absent, prepare the audit code and run only synthetic examples; clearly report that real-data analysis is blocked. Never replace missing competition data with invented data.

## Requested implementation

1. Add a command-line audit script with an explicit data-directory argument.
2. Discover actual encoding, delimiter, headers, template schema, identifier types, timestamp representations, and duration units. Preserve identifiers without lossy numeric coercion.
3. Stream or chunk large inputs. Compute row counts, missingness, ID-zero counts by schedule period, observed temporal ranges, channel/programme cardinalities, duplicates, and duration diagnostics.
4. Label sampled statistics as sampled and record sample size/selection/seed. Do not report approximate quantiles as exact.
5. Preserve user-ID samples and original viewing records locally in ignored storage. Publish only appropriate aggregate audit outputs and synthetic matching examples.
6. Implement a small exact overlap reference and a bounded optimized matcher. Test boundaries, multiple airings per view, same/different channels, duplicates, and the train cutoff.
7. Implement MAP@5 and a prediction-file validator with meaningful tests. Check the documented examples and all template users, valid IDs, uniqueness, header, order, and exactly five space-separated IDs.
8. Inspect the historical target-construction reference and available official task wording. Record whether the most-frequent-five target interpretation is established or still a hypothesis.
9. Produce a data-dependent recommendation for positive-label and interaction-weight construction. Do not freeze a threshold based on model scores.
10. Update experiment_protocol.md with verified facts and remaining unresolved decisions.

## Suggested output paths

- src/audit_data.py
- src/intervals.py
- src/metrics.py
- src/validate_submission.py
- tests/test_intervals.py
- tests/test_metrics.py
- tests/test_submission.py
- results/data_audit.json
- results/data_audit.md
- docs/student_verification.md
- a minimal dependency specification and documented execution commands

Adapt filenames if the eventual project structure justifies it. Do not add placeholder benchmark numbers.

## Acceptance criteria

- One documented command produces the audit from actual supplied files.
- Instructor-reported statistics and newly measured statistics are explicitly separated.
- No global channel-only Cartesian product or dense all-user/all-item matrix is constructed.
- Matching is checked against an independent small reference.
- AP@5 examples equal 11/12 and 8/15 within floating-point tolerance.
- Missing files, invalid timestamps, impossible durations, and malformed submissions have clear errors.
- The script records its actual environment, runtime, and measurement method.
- No credentials, raw data, user histories, or original AI-session exports are committed.
- No measured model score or successful Kaggle submission is claimed in this phase.

## Report back

Give the student:
- what was implemented and actually run;
- measured data facts and their denominators;
- unresolved decisions affecting the label/split/candidate definitions;
- one overlap example and one AP@5 calculation to verify personally;
- the exact next command justified by those results.
