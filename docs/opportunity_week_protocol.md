# Frozen C/D opportunity-and-week experiment

This definition is recorded before execution. Reuse existing audited preprocessing, private caches, source wall-clock convention and 80% longest-block qualification. Do not combine C/D, decay counts, tune weights, change truth or expand the search. No Kaggle browser/upload/submission workflow is permitted.

## Exact ranking keys

Baseline v3: descending personal qualified-airing count, descending distinct qualified training viewers, descending total qualified training user-airings, ascending raw string programme ID.

C inserts descending prediction-window canonical airing count immediately after personal count. Only `tv_show_id`, `channel_id`, `start_time`, and `duration` may supply this feature. A positive-duration, nonzero-ID canonical broadcast `(channel,start,end,item)` counts once if `start < window_end and end > window_start`. Deduplicate across source files before counting; carryovers count once without changing full airing endpoints. Distinct channels remain distinct broadcasts; counts aggregate across channels. Scheduled opportunities are not verified user exposures. No future behaviour or future content attributes are used.

D inserts descending distinct qualified viewing-week count immediately after personal count. For every qualified user-airing, take the minimum observed overlapping segment start after clipping to the fitting window. Assign that airing once to the source-calendar Monday date containing that start, even if the airing or a later segment crosses Monday. Several qualified airings for one user/programme in the same Monday-start week contribute one week. Preserve the full original airing duration when computing the 80% longest-block qualification. Never infer a week from a future broadcast end. Week sets are computed only from pre-cutoff observed viewing.

Personal counts remain primary. Global popularity keys and the shared fallback/completion remain unchanged. Previously watched items remain eligible.

## Frozen splits

| Split | Fitting wall-clock interval | Prediction/validation wall-clock interval |
| --- | --- | --- |
| Main | [2020-03-09 00:00:00, 2020-05-18 00:00:00) | [2020-05-18 00:00:00, 2020-07-27 00:00:00) |
| Auxiliary | [2020-03-09 00:00:00, 2020-06-01 00:00:00) | [2020-06-01 00:00:00, 2020-07-27 00:00:00) |

Main uses the frozen 4,625 users, 6,384 candidates and original truth. Rebuild auxiliary fit/validation interactions, permitted preprocessing metadata, global statistics, candidates and truth using the established pipeline and its fixed raw-ID target tie-break. The auxiliary cohort is all users with a qualifying target under the same policy; do not force main counts. Compute schedule opportunities for each prediction window separately and weeks from its fitting window only. The auxiliary split overlaps the main one and is not an independent untouched test. Compare deltas from v3 within each split; do not interpret raw MAP across splits as equivalent tasks.

## Diagnostics and uncertainty

For each feature report users with any available equal-personal-count group distinguished by the new feature, users with such a group intersecting the v3 top five, users whose already-selected top-five tie can be distinguished, and users whose fifth-boundary tie has differing feature values. These are potential distinctions; actual ordering-only and membership changes are reported separately. Denominator is that split’s evaluation cohort; fallback items do not count as personal evidence.

Report MAP@5, differences from that split’s v3, AP improved/worsened/unchanged users, fixed qualified-history slices, ordered-list/slot changes, order-only/membership changes, set overlap and paired-user bootstrap 95% percentile intervals (2,000 resamples, seed 42). Uncertainty conditions on each reused cohort and excludes selection/multiple-experiment uncertainty.

## Predeclared selection and artifact

A variant is eligible only if its unrounded MAP strictly improves v3 in BOTH splits. If both are eligible, choose higher main MAP; exact main-score ties retain v3 as a conservative tie rule. If neither is eligible, retain v3 and do not generate another CSV. Report disagreement or weak evidence rather than calling it robust.

For a selected variant, use the canonical combined [2020-03-09, 2020-07-27) fit and recompute qualification/weekly statistics from its full-window segments. Do not add split counts. C computes opportunities separately from [2020-07-27, 2020-10-19) schedules including known carryovers. Preserve all submitted files, generate at most one new versioned file, validate all 1,260 users and the exact header/order/five valid IDs, and compare against the submitted v3 CSV. The user alone may upload after review. Native transcript remains unmodified; student verification stays pending.
