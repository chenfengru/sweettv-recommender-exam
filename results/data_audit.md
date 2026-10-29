# Data audit

Status: **blocked_missing_inputs**

This report contains aggregate file diagnostics only. Instructor counts are separately labelled in JSON.

Missing original inputs:

- `dataset11-30.csv`
- `export_arh_11-20-final.csv`
- `export_arh_21-30-final.csv`
- `export_arh_31-42-final.csv`
- `submission.csv`

**No real-data statistics were measured.** No model was trained or submitted.

Unresolved before modelling:

- Match real view and schedule timestamps/channels; prove units from source and diagnostics.
- Confirm template column roles and exact calendar cutoffs.
- Confirm continuous watching and most-frequent-five target semantics; historical code is not the evaluator.
- Measure matched view rows, union viewing seconds, usable template-user history and candidate cold start.
- Choose positive thresholds and interaction weights only after real duration/coverage diagnostics.

Synthetic checks are recorded separately; they do not verify the competition data or constitute student verification.
