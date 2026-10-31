# Scheduled-opportunity and qualified-week tie-break review

**Decision: retain submitted v3. No new prediction CSV was generated.** C improves the main split only, then declines on the predeclared auxiliary split. D declines on both. Neither meets the selection rule frozen before execution; there is no recommendation for another manual submission from this round.

## Baseline and provenance

The user confirms that `submissions/candidate_personal_tie_popularity_20261030_v3.csv` returned **Private Score 0.39697** and **Public Score 0.40288**, from a Kaggle screenshot. The exact file remains unchanged with SHA-256 `39aac2794395209b2299ccee2e2bb1b4b9afde22f3e06ccb5b04f3d706c9522f`. These are user-reported screenshot values, not independently fetched by the agent. The screenshot binary, submission ID and submission timestamp are not available in this tool run; none was invented. `baseline_score_evidence.json` records this provenance and checksums for all previous CSVs.

## Definitions frozen before execution

[The frozen protocol](../../docs/opportunity_week_protocol.md) was written before experiments, with its timestamp and SHA-256 in `frozen_experiment.json`. Its hash is unchanged. Exactly v3 and two new variants were evaluated; no combined C/D key, weight, decay, qualification threshold or extra temporal split was tried.

All methods first rank by descending personal qualified-airing count. V3 then uses distinct qualified training viewers, total qualified training user-airings and raw string programme ID. C and D insert one secondary key before those unchanged v3 keys:

- **C — scheduled opportunities:** count each positive-duration, nonzero-ID canonical `(channel,start,end,item)` broadcast once if `start < prediction_end and end > prediction_start`. Deduplicate across files, include carryovers and preserve full broadcast endpoints; separate channels remain separate opportunities. The feature reads only item ID, channel, start and duration. Future content attributes and viewing behaviour are not inputs. Opportunities are not verified exposures.
- **D — distinct qualified viewing weeks:** after the existing 80% longest-block/full-original-duration qualification, assign each user-airing once to the Monday-start source-calendar week of its **first observed overlapping segment start**, clipped to the fitting window. Multiple qualified airings of the same user/programme in that week contribute one distinct week. An airing crossing Monday is not assigned to both weeks, and a later longest block does not replace the first observed start. No future broadcast end supplies its week.

Causal cleaning, canonical deduplication, union of viewing intervals, original airing denominators, repeat eligibility and shared popularity completion remain unchanged. Each fitted week count is reconciled with the established qualified-airing counts. Primary count sequences are asserted unchanged, and membership changes require an equal-count fifth-boundary tie. Global fallback ordering is recomputed from fitting behaviour only and remains identical across methods within each split.

## Main validation

Fit **[2020-03-09, 2020-05-18)**; validate **[2020-05-18, 2020-07-27)**, in the established source wall clock. The frozen main truth and candidate pool are reused exactly: **4,625 users and 6,384 candidates**. V3 lists reconcile exactly with the previous saved v3 predictions.

| Method | MAP@5 | Delta from within-split v3 | AP improved / worsened / unchanged | Conditional paired-bootstrap 95% interval |
| --- | ---: | ---: | --- | --- |
| v3 | 0.326853993994 | +0.000000000000 | reference | reference |
| C | 0.328006966967 | +0.001152972973 | 476 / 446 / 3703 | [-0.000106384, +0.002346784] |
| D | 0.325717537538 | -0.001136456456 | 142 / 208 / 4275 | [-0.001814668, -0.000430107] |

## Predeclared auxiliary temporal comparison

Fit **[2020-03-09, 2020-06-01)**; validate **[2020-06-01, 2020-07-27)**. Both interaction windows were rebuilt from the unchanged raw files using the existing pipeline, including its schedule/metadata preprocessing and canonical overlap treatment. Global qualified statistics, available candidates and raw-ID-tied top-five target construction were rebuilt for this split; no future content attributes enter C/D. The actual common auxiliary cohort is **4,589 users**, with **5,742 candidates**. No main-split counts were imposed.

| Method | MAP@5 | Delta from within-split v3 | AP improved / worsened / unchanged | Conditional paired-bootstrap 95% interval |
| --- | ---: | ---: | --- | --- |
| v3 | 0.324108919881 | +0.000000000000 | reference | reference |
| C | 0.322843393622 | -0.001265526258 | 355 / 438 / 3796 | [-0.002506867, -0.000046562] |
| D | 0.323493438416 | -0.000615481465 | 171 / 197 / 4221 | [-0.001352320, +0.000146009] |

Compare **deltas within each split**, not raw main-versus-auxiliary MAP as if the tasks were identical. The auxiliary fitting history, target horizon, cohort and candidate pool differ; its behaviour overlaps the main comparison. This is an overlapping robustness check, **not an independent untouched test**.

C has a small positive main point estimate, whose interval includes zero, and a negative auxiliary estimate, whose conditional interval is slightly below zero. Its direction is inconsistent across the prescribed windows. D is negative in both; its main interval is below zero, while its auxiliary interval includes zero. These are negative/mixed findings, not evidence of a robust improvement. No cause for the sign reversal is established by this experiment.

## Feature and tie diagnostics

These are potential feature distinctions among available programmes with the same positive personal count, not counts of actual reordered lists. Denominator is the split’s evaluation cohort. Fallback items are excluded. Top-five-relevant groups intersect the baseline direct top five; within-selected compares selected members only; boundary means the baseline count tie spans ranks five and six.

| Split | Feature | Cohort | Any equal-count group distinguished | Top-five-relevant group | Within selected top five | Fifth-boundary tie |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| main | C | 4,625 | 4,375 | 3,794 | 3,297 | 2,482 |
| main | D | 4,625 | 2,515 | 1,961 | 1,488 | 899 |
| auxiliary | C | 4,589 | 4,365 | 3,710 | 3,179 | 2,404 |
| auxiliary | D | 4,589 | 2,639 | 1,957 | 1,476 | 898 |

| Split | Canonical prediction-window broadcasts | Candidate IDs | Broadcast-count range per item | Qualified fitting user-airings | Maximum distinct qualified weeks |
| --- | ---: | ---: | --- | ---: | ---: |
| main | 121,587 | 6,384 | 1–6138 | 289,762 | 10 |
| auxiliary | 98,071 | 5,742 | 1–4884 | 352,391 | 12 |

No duplicate canonical broadcast rows were found within these prediction-window inputs; the dedicated fixture verifies deduplication and carryovers even when duplicates are present. These are exact full-window counts, not sampled statistics. D cannot distinguish equal-count-one programmes because each necessarily occupies one qualified week. The larger number of distinguishable C ties does not establish a ranking benefit; observed AP and prediction changes are reported separately.

## Actual ordered-list and membership changes

All changes are relative to that split’s v3. Changed rank-position slots include reordering; top-five set overlap ignores order. AP can be unchanged while predictions change.

| Split | Variant | Changed ordered lists | Order-only users | Membership-change users | Changed rank slots / denominator | Top-five set overlap |
| --- | --- | ---: | ---: | ---: | --- | ---: |
| main | C | 2555 | 963 | 1592 | 5382 / 23125 | 92.2638% |
| main | D | 853 | 522 | 331 | 1633 / 23125 | 98.4951% |
| auxiliary | C | 2292 | 909 | 1383 | 4718 / 22945 | 93.3144% |
| auxiliary | D | 896 | 530 | 366 | 1716 / 22945 | 98.3613% |

Within each split, complete fallback, partial completion and fallback-slot counts are identical for v3, C and D:

| Split | Complete fallback users | Partial completion users | Fallback slots |
| --- | ---: | ---: | ---: |
| main | 112 | 376 | 1446 |
| auxiliary | 92 | 368 | 1314 |

## Main history-size slices

History size is the established number of distinct qualified fitting programmes before candidate filtering. All three methods use the same slice membership within this split.

| Qualified fitting items | Users | v3 MAP@5 | C MAP@5 | D MAP@5 |
| --- | ---: | ---: | ---: | ---: |
| 0 | 108 | 0.163050412 | 0.163050412 | 0.163050412 |
| 1–5 | 462 | 0.176880712 | 0.177942520 | 0.177295575 |
| 6–20 | 2087 | 0.299143374 | 0.299491695 | 0.298378587 |
| 21+ | 1968 | 0.400436568 | 0.402527524 | 0.398479421 |

## Auxiliary history-size slices

History size is the established number of distinct qualified fitting programmes before candidate filtering. All three methods use the same slice membership within this split.

| Qualified fitting items | Users | v3 MAP@5 | C MAP@5 | D MAP@5 |
| --- | ---: | ---: | ---: | ---: |
| 0 | 87 | 0.172905492 | 0.172905492 | 0.172905492 |
| 1–5 | 401 | 0.178942920 | 0.178915212 | 0.179109172 |
| 6–20 | 1874 | 0.292018113 | 0.289881566 | 0.291289577 |
| 21+ | 2227 | 0.383158958 | 0.382354064 | 0.382473806 |

## Uncertainty and frozen selection

Each interval uses 2,000 paired-user resamples with replacement, seed 42, conditional on its own split cohort; C/D use the same resampled indices within that split. Neither interval accounts for selecting methods on reused data, repeated prior experiments, or future Kaggle generalization. The overlapping auxiliary comparison is not pooled into an independent-test confidence claim.

The predeclared rule requires a strictly positive delta on **both** splits, then chooses higher main MAP if both qualify, with exact score ties retaining v3. **Eligible variants: none. Selected: v3.** No new final-window refit or prediction CSV was performed. There is no new filename/path/checksum or validator result to present. The previously validated and submitted v3 file remains intact, and its user-reported Private 0.39697 / Public 0.40288 remain the best submitted scores.

## Regression, runtime and reproducibility

All **42 tests pass**: the existing 37 plus focused canonical-airing, week-assignment, ranking-precedence, clipped-week invariance and end-to-end future-viewing tests. Fixtures cover duplicate rows across schedule files, distinct-channel opportunities, carryovers, zero-duration/zero-ID exclusion and exact half-open endpoints. Week fixtures include several airings in one week, Sunday-to-Monday crossing, and a qualified Monday block whose first observed segment is Sunday. A full pipeline fixture changes only future viewing tails/adds future users while keeping both C and D predictions unchanged.

Runtime and code/cache provenance are recorded in the split JSON files. The auxiliary extraction rebuilt both windows; the main reused its established cache. No unrelated audit, model training, recency experiment or added parameter search was run.

| Measurement | Seconds |
| --- | ---: |
| Entire frozen main + auxiliary experiment | 76.735 |
| main week-feature extraction | 3.663 |
| main v3 ranking/completion for 4,649 users | 0.0453 |
| main C ranking/completion for 4,649 users | 0.0536 |
| main D ranking/completion for 4,649 users | 0.0521 |
| auxiliary week-feature extraction | 4.265 |
| auxiliary v3 ranking/completion for 4,617 users | 0.0543 |
| auxiliary C ranking/completion for 4,617 users | 0.0640 |
| auxiliary D ranking/completion for 4,617 users | 0.0613 |
| Auxiliary fitting-window interaction build | 35.958 |
| Auxiliary validation-window interaction build | 21.731 |

Intervals, raw input checksums, dependency versions, source hashes, cache configurations and measured process high-water RSS are included in the machine-readable records. The environment remains the pinned standard model-comparison environment, seed 42, one numerical-library thread, on the 24 GiB Mac. All per-user weeks, truth, predictions and AP values remain in ignored local artifacts. Raw inputs, credentials and the original native session record remain outside public Git and unmodified. Student verification remains pending.

**Manual submission recommendation: no new submission from this round.** Keep the exact submitted v3 baseline. There is no new candidate to upload, no new Kaggle score and no further experiment or action scheduled. Stop for user review; all future uploads remain manual-only by the user.
