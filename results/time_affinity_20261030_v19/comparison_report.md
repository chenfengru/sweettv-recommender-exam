# V19: fixed viewing-time affinity extension

**Retain submitted v18.** The one fixed six-feature extension improves auxiliary MAP@5 but reduces main MAP@5, failing the frozen strict-improvement-on-both rule. No final features, prediction CSV or new submission description were generated. No additional variants were tested. Student verification remains pending. No Kaggle workflow, command, API or upload was used.

V18 is the confirmed incumbent: **Private 0.43798 / Public 0.44758**, user-screenshot-reported. Submission ID/time are unknown and not invented. Submitted CSV SHA-256 `a62d1afb1a0c015cb70fd60c1e89bb670b731f872b3433dc438526a5ae703c45` and all prior artifacts remain unchanged.

## Frozen definition and control

[Protocol](../../docs/time_affinity_protocol.md), [pre-evaluation settings and source hashes](frozen_experiment.json). Original two-week historical origins/labels, candidates and all 52 v18 columns remain exactly equal. Only six additions change. Exactly one fixed binary LightGBM classifier, 300 trees/seed 42, all negatives and all-negative queries, no eval_set/early stopping/tuning/sampling/weights/expansion/blend/E2/cold overrides. No failed v15/v16/v17 changes. No main/auxiliary labels enter fitting. The same frozen classifier is used on both evaluations and would be applied unchanged at final cutoff only if qualified.

### Time profiles

Source-naive wall-clock timestamps remain unchanged: naive calendar differences from the established epoch, no UTC/Moscow/other timezone assumption or conversion. The naive 1970-01-01 calendar date is Thursday, so hour-of-week indexing adds 72 hours modulo 168 to make Monday 00:00 first. This is calendar alignment, not a timezone shift. Half-open durations split exactly across hourly, midnight/day and week boundaries.

User profiles: cleaned cutoff-clipped viewing, including unattributed intervals, is unioned **across channels per user** before binning. Simultaneous channel sessions count once here. Compute full history from Mar9 and trailing 28 days independently; split union duration into 24 hour-of-day and 168 hour-of-week bins, normalize each histogram by observed duration. A zero-duration profile stays all zero and receives a no-viewing flag. This differs intentionally from v18 channel-exposure denominators; all existing v18 columns are nevertheless preserved. Profiles describe observed device/session viewing times, not verified human attention.

Programme profiles: canonical nonzero positive-duration schedule airings, deduplicated across files and clipped to the exact forecast window including carryovers. Sum across airings/channels, distribute to the same bins, normalize by total broadcast seconds. Every available programme must have strictly positive mass; the profile universe exactly matches unchanged availability. Existing schedule coverage checks remain. Future schedule information is allowed; future viewing is excluded.

Append exactly four dot products: full day/week and trailing28 day/week; then two cross-channel-union no-viewing indicators. There is no second exposure division, smoothing, alternate similarity/binning, raw time ID or channel-time interaction. **Affinity measures temporal distribution overlap, not a calibrated watching probability or actual viewing availability.**

## Paired local evaluation

| Split | v18 MAP@5 | New MAP@5 | Delta | Bootstrap 95% interval | Improved / worsened / unchanged |
|---|---:|---:|---:|---|---|
| main | 0.369249609610 | 0.368260300300 | -0.000989309309 | [-0.002293626126, +0.000355291291] | 500 / 524 / 3601 |
| auxiliary | 0.357738856202 | 0.359933899906 | +0.002195043704 | [+0.000771405353, +0.003552768093] | 570 / 456 / 3563 |

Paired-user bootstrap: 2,000 resamples, seed 42, percentile 95% intervals. Conditional on reused cohorts; excludes accumulated configuration-selection uncertainty and training variation. Evaluation cohorts/windows overlap and do not provide independent replication. A positive auxiliary interval does not override the predeclared main-and-auxiliary selection rule.

## Table equality, histogram mass and finite schema

Training retains 604,935 rows and 25,385 positive labels. Candidate row indexes are unchanged direct cache reads; all 52 original values are exactly equal after concatenation. Original labels are loaded unchanged, hash-verified and checked against the original two-week manifests. All negative rows/queries remain.

- origin_20200406: 291,619 rows, 13020 positives, 979 all-negative queries; label checksum and window unchanged.
- origin_20200420: 313,316 rows, 12365 positives, 1077 all-negative queries; label checksum and window unchanged.

| Origin / user window | Query users | Zero profiles / fraction | Positive profiles among all cleaned users | Total union seconds, all cleaned users | Max day/week normalization error |
|---|---:|---|---:|---:|---|
| origin_20200406 / full | 4836 | 9 / 0.001861 | 4827 | 1864064659 | 2.22e-16 / 2.22e-16 |
| origin_20200406 / trailing28 | 4836 | 9 / 0.001861 | 4827 | 1864064659 | 2.22e-16 / 2.22e-16 |
| origin_20200420 / full | 4859 | 5 / 0.001029 | 4854 | 2753305890 | 2.22e-16 / 2.22e-16 |
| origin_20200420 / trailing28 | 4859 | 46 / 0.009467 | 4813 | 1837545451 | 2.22e-16 / 2.22e-16 |
| main / full | 4625 | 31 / 0.006703 | 4876 | 4498791957 | 2.22e-16 / 2.22e-16 |
| main / trailing28 | 4625 | 92 / 0.019892 | 4764 | 1745486067 | 2.22e-16 / 2.22e-16 |
| auxiliary / full | 4589 | 27 / 0.005884 | 4880 | 5198511707 | 2.22e-16 / 2.22e-16 |
| auxiliary / trailing28 | 4589 | 95 / 0.020702 | 4724 | 1596906788 | 2.22e-16 / 3.33e-16 |

Query zero rates use the original feature-user universe. Profile totals/positive-profile counts include all cleaned pre-cutoff users; no future-label-only users are added to model tables. Zero profiles sum to0; every nonzero day/week profile sums to 1. Each unnormalized histogram is checked against exact accumulated interval mass (floating arithmetic tolerance 1e-12 relative/1e-8seconds absolute).

| Origin | Available positive schedule profiles | Minimum broadcast seconds | Total broadcast seconds | Max day/week normalization error |
|---|---:|---:|---:|---|
| origin_20200406 | 2143 | 900 | 73906200 | 2.22e-16 / 2.22e-16 |
| origin_20200420 | 2515 | 600 | 79052580 | 2.22e-16 / 2.22e-16 |
| main | 6384 | 900 | 410731500 | 2.22e-16 / 2.22e-16 |
| auxiliary | 5742 | 600 | 331021260 | 2.22e-16 / 2.22e-16 |

Complete six-feature distributions (min/mean/median/p90/max/zero fraction), exact windows, feature hashes, finite 58-column schema and original 52 equality are in each origin’s time_diagnostics.json. Required programme profiles with missing/nonpositive mass fail explicitly; no silent profile imputation. All previous 52 columns remain even where no-viewing indicators are redundant.

### Independent numerical verification

The initial native NumPy matrix products emitted divide-by-zero/overflow/invalid floating-status warnings, although every output was finite and within valid bounds. We independently recomputed all six features for **every row** at both training origins and both evaluation origins using elementwise products followed by np.sum, with no matrix multiplication/BLAS. Every float32 value is **bitwise identical** to the actual fitted/evaluated arrays, max difference 0. See [numeric_verification.json](numeric_verification.json). No model fit or prediction change occurred during this check. The implementation now uses those verified elementwise sums to avoid the platform warning path; it does not change the feature definition or measured inputs. The evidence supports treating the warnings as a numerical-status artifact for this run, without relying on that assumption. The repeatable verification command is documented in the run guide.

## Main error analysis

Exact v18 inputs: 4625 users / 380,403 rows / 6384 available programmes. Unchanged relevant candidate coverage 15999/21466 pairs, micro recall 0.745318178, macro recall 0.728601802, oracle MAP@5 0.728601802.

Changed ordered lists 2606; rank-position slots 5378; membership-change users 1347; order-only changes 1259; top-five set overlap 0.939200000. Relevant-hit gains/losses 226 / 223 (net +3). Shared fallback completion remains zero because original candidate unions contain global5; model selection of global-source items is distinct from list completion.

Seen relevant hits 9048 → 9057; unseen hits 408 → 402. Seen AP contribution delta -0.000575975976; unseen -0.000413333333. Contributions assign each hit's rank precision to its category under the same AP denominator. Legacy `fused_` JSON prefix means current classifier predictions; no fusion occurs.

| Fixed H80 slice | Users | v18 MAP | New MAP | Delta | Improved / worsened / unchanged | Hit gains / losses | Changed lists / positions / memberships |
|---|---:|---:|---:|---:|---|---|---|
| 0 | 108 | 0.181574074 | 0.170540123 | -0.011033951 | 9 / 17 / 82 | 0 / 1 | 79 / 186 / 18 |
| 1–5 | 462 | 0.223737975 | 0.225183381 | +0.001445406 | 44 / 33 / 385 | 16 / 12 | 332 / 736 / 210 |
| 6–20 | 2087 | 0.341924080 | 0.340515493 | -0.001408588 | 215 / 235 / 1637 | 108 / 109 | 1194 / 2428 / 652 |
| 21+ | 1968 | 0.442686456 | 0.442121443 | -0.000565012 | 232 / 239 / 1497 | 102 / 101 | 1001 / 2028 / 467 |

Slice membership is original H80 >=80%-qualified distinct programmes before candidate filtering. Full slice-level seen/unseen attribution remains in comparison.json.

| Cold group | Users | v18 MAP | New MAP | Improved / worsened / unchanged |
|---|---:|---:|---:|---|
| no_n50_training_history | 74 | 0.182094595 | 0.171509009 | 6 / 13 / 55 |
| no_available_n50_history | 76 | 0.185197368 | 0.175109649 | 7 / 14 / 55 |

Inference/evaluation 1.323s; process-lifetime peak RSS 1,085,227,008 bytes.

## Auxiliary error analysis

Exact v18 inputs: 4589 users / 397,757 rows / 5742 available programmes. Unchanged relevant candidate coverage 15639/21080 pairs, micro recall 0.741888046, macro recall 0.724358974, oracle MAP@5 0.724358974.

Changed ordered lists 2738; rank-position slots 5745; membership-change users 1396; order-only changes 1342; top-five set overlap 0.936500327. Relevant-hit gains/losses 246 / 175 (net +71). Shared fallback completion remains zero because original candidate unions contain global5; model selection of global-source items is distinct from list completion.

Seen relevant hits 8755 → 8820; unseen hits 316 → 322. Seen AP contribution delta +0.001959940437; unseen +0.000235103266. Contributions assign each hit's rank precision to its category under the same AP denominator. Legacy `fused_` JSON prefix means current classifier predictions; no fusion occurs.

| Fixed H80 slice | Users | v18 MAP | New MAP | Delta | Improved / worsened / unchanged | Hit gains / losses | Changed lists / positions / memberships |
|---|---:|---:|---:|---:|---|---|---|
| 0 | 87 | 0.178212005 | 0.176008940 | -0.002203065 | 8 / 9 / 70 | 3 / 4 | 48 / 148 / 17 |
| 1–5 | 401 | 0.226622333 | 0.226551676 | -0.000070657 | 29 / 29 / 343 | 13 / 10 | 292 / 654 / 180 |
| 6–20 | 1874 | 0.328296128 | 0.329803303 | +0.001507174 | 222 / 185 / 1467 | 88 / 73 | 1147 / 2374 / 607 |
| 21+ | 2227 | 0.413137255 | 0.416490920 | +0.003353665 | 311 / 233 / 1683 | 142 / 88 | 1251 / 2569 / 592 |

Slice membership is original H80 >=80%-qualified distinct programmes before candidate filtering. Full slice-level seen/unseen attribution remains in comparison.json.

| Cold group | Users | v18 MAP | New MAP | Improved / worsened / unchanged |
|---|---:|---:|---:|---|
| no_n50_training_history | 60 | 0.188777778 | 0.181277778 | 3 / 5 / 52 |
| no_available_n50_history | 63 | 0.190899471 | 0.184814815 | 4 / 6 / 53 |

Inference/evaluation 1.352s; process-lifetime peak RSS 1,219,575,808 bytes.

## Runtime, importance and limitations

Exactly one 300-tree fit: 5.198s; training-process peak RSS 865,730,560 bytes. Memory uses resource.ru_maxrss, a lifetime high-water mark rather than phase allocations. Fixed classifier SHA-256 `eec8dbc59ec14606b74b50379e83b913156eacdef43d97f618fae2684598e830`. Effective/requested parameters and versions are recorded in training.json. [Feature importance](feature_importance.json) is descriptive gain/split usage, not causal evidence. Added features by gain: time_full_hour_day_affinity (3107.263), time_trailing28_hour_day_affinity (2831.744), time_trailing28_hour_week_affinity (2183.649), time_full_hour_week_affinity (662.052), time_full_no_viewing (0.000), time_trailing28_no_viewing (0.000).

| Origin | Feature construction seconds | Full58 matrix bytes | Process-lifetime peak RSS bytes |
|---|---:|---:|---:|
| origin_20200406 | 3.927 | 67,655,608 | 537,935,872 |
| origin_20200420 | 4.920 | 72,689,312 | 721,485,824 |
| main | 6.777 | 88,253,496 | 1,085,227,008 |
| auxiliary | 7.122 | 92,279,624 | 1,219,575,808 |

Final original 52-input equality was verified regardless of qualification: 1260 users / 152,442 rows / 6649 available programmes including carryovers. No final six-feature computation or prediction was performed because selection failed.

All **105 tests pass**. Focused checks cover exact fractional hour splits, Sunday/Monday week transition, midnight carryovers, cross-channel/unattributed unions, exact histogram mass and normalization, zero/trailing-empty histories, known dot products with no second exposure division, first 52 preservation, missing schedule mass failure and post-cutoff invariance. Existing causal cleaning, temporal/schema/ranking and submission checks remain. All frozen source artifacts/CSV/model hashes are preserved; private histories/weights remain ignored. Native records are untouched and student verification is pending.

Historical forecasts remain two weeks, versus main ten/auxiliary eight/final twelve; historical feature histories four/six weeks differ from evaluation/final ten/twelve/twenty weeks. Viewing-time distributions can shift, and separately fitted LightFM scores/biases retain origin-scale differences. Reused overlapping cohorts and accumulated validation-informed model selection limit claims beyond this specific configuration. Time-distribution overlap is not actual availability or calibrated watch probability.

## Decision

Retain submitted v18. Main is negative with an interval spanning zero; auxiliary is positive with an interval above zero. The fixed rule requires both point estimates to improve and is not met. No new CSV or candidate validator was needed. No extra variants were tested and no Kaggle action occurred.
