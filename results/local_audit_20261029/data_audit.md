# Data audit

Status: **profiled_review_required**

This report contains aggregate file diagnostics only. Instructor counts are separately labelled in JSON.

| File | Status | Measured data records | Duplicates beyond first |
| --- | --- | ---: | ---: |
| dataset11-30.csv | profiled | 5821987 | 17 |
| export_arh_11-20-final.csv | profiled | 1074235 | 0 |
| export_arh_21-30-final.csv | profiled | 1074394 | 0 |
| export_arh_31-42-final.csv | profiled | 1295378 | 0 |
| submission.csv | profiled | 1260 | 0 |

See JSON for actual headers, denominators, unit overrides, parsing issues, samples and timing.

- `dataset11-30.csv`: issues require review; no rows were silently repaired or removed.
- `export_arh_11-20-final.csv`: issues require review; no rows were silently repaired or removed.

Unresolved before modelling:

- Match real view and schedule timestamps/channels; prove units from source and diagnostics.
- Confirm template column roles and exact calendar cutoffs.
- Confirm continuous watching and most-frequent-five target semantics; historical code is not the evaluator.
- Measure matched view rows, union viewing seconds, usable template-user history and candidate cold start.
- Choose positive thresholds and interaction weights only after real duration/coverage diagnostics.

Synthetic checks are recorded separately; they do not verify the competition data or constitute student verification.
