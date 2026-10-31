# Single schedule-exposure extension of historical LightGBM (executed)

**The schedule-extended model qualifies on both splits. Recommend one manual benchmark submission, while retaining v12 as the best confirmed submitted model until a new user-reported result is available.** Exactly one new classifier was trained; v12’s candidates, labels, original 27 features and model parameters were preserved. No E2, blend, cold override or post-result feature search was used.

## Frozen extension and unchanged control

Add exactly seven features: past/future scheduled airings per day, past/future clipped broadcast seconds per day, their two log1p rate differences (future minus past), and a zero-past-airings indicator. Past is always the full 28 days before the origin cutoff; future is that origin’s exact label/prediction window. Full-window days, including zero-airing days, are the denominators.

Schedules use canonical (channel,start,end,programme) deduplication across the three audited exports, positive durations and nonzero programme IDs. Count a canonical airing once in each window with positive overlap; sum its duration clipped to that window. Cross-channel exposures add, even when simultaneous; these are scheduled broadcast seconds, not wall-clock availability unions. Boundary-touching nonoverlaps are excluded and carryovers are clipped at both ends.

Only programme ID, channel, start and duration fields are read for these features. No viewing log or content attribute is joined. Historical future features cover only the corresponding two-week label window; evaluation/final future exposure covers the permitted prediction window. Original candidate availability remains unchanged.

Historical training origins remain April6->[April6,April20) and April20->[April20,May4), with histories beginning March9. The same 604,935 rows, 25,385 labels=1 and all negatives are retained in exactly their cached order. The original float32 feature columns are copied byte-for-value; seven columns are appended for an identical 34-column training/inference schema. Raw IDs remain metadata only.

Classifier settings are exactly v12’s fixed binary LightGBM settings: learning_rate0.05,num_leaves15,max_depth-1,min_child_samples100,reg_lambda1,n_estimators300,random_state42,n_jobs4, deterministic column-wise execution. Exactly one fit and 300 iterations; no early stopping, weights, subsampling or parameter changes. Probability ties use N50, original >=0.80 viewer/airing popularity and raw string ID. The classifier ranks the full unchanged candidate union, preserving no particular positions.

## Required schedule coverage: checked before fitting

The gate was fixed before inspecting results: all three source files must exist and match v12 hashes; the union of valid nonzero airing intervals must cover every required window second with no gaps. All ten windows, including final application, passed before fitting. Failure would stop the experiment without imputing missing coverage as zero. Source ranges, canonical counts and channel coverage are retained in schedule_coverage.json.

| Origin | Window | Source wall-date interval | Full days | Canonical overlapping airings | Channels | Global covered seconds / required | Gaps | Per-channel coverage min / median / max |
| --- | --- | --- | ---: | ---: | ---: | --- | ---: | --- |
| origin_20200406 | past | [2020-03-09,2020-04-06) | 28 | 45,084 | 163 | 2419200 / 2419200 | 0 | 0.11161% / 32.51488% / 99.85119% |
| origin_20200406 | future | [2020-04-06,2020-04-20) | 14 | 23,362 | 167 | 1209600 / 1209600 | 0 | 0.39683% / 31.17560% / 100.00000% |
| origin_20200420 | past | [2020-03-23,2020-04-20) | 28 | 45,971 | 170 | 2419200 / 2419200 | 0 | 0.04960% / 30.26786% / 99.85119% |
| origin_20200420 | future | [2020-04-20,2020-05-04) | 14 | 23,350 | 167 | 1209600 / 1209600 | 0 | 0.19841% / 36.33433% / 100.00000% |
| main | past | [2020-04-20,2020-05-18) | 28 | 46,989 | 173 | 2419200 / 2419200 | 0 | 0.14881% / 36.25992% / 100.00000% |
| main | future | [2020-05-18,2020-07-27) | 70 | 121,587 | 188 | 6048000 / 6048000 | 0 | 0.17361% / 30.67956% / 100.00000% |
| auxiliary | past | [2020-05-04,2020-06-01) | 28 | 47,216 | 170 | 2419200 / 2419200 | 0 | 0.44643% / 36.84276% / 100.00000% |
| auxiliary | future | [2020-06-01,2020-07-27) | 56 | 98,071 | 188 | 4838400 / 4838400 | 0 | 0.16121% / 31.54142% / 100.00000% |
| final | past | [2020-06-29,2020-07-27) | 28 | 49,390 | 185 | 2419200 / 2419200 | 0 | 0.17361% / 31.68403% / 100.00000% |
| final | future | [2020-07-27,2020-10-19) | 84 | 144,842 | 191 | 7257600 / 7257600 | 0 | 0.05787% / 27.88112% / 100.00000% |

These checks establish temporal availability in the provided authoritative exports, not independent completeness of every channel’s guide. Per-channel gaps and changing channel coverage are explicitly reported; absence for a programme is measured relative to the supplied canonical catalogue. No external channel-completeness guarantee is claimed. Genuine zero programme exposure is represented as zero only after the window-level gate passes; there are no missing-coverage NaNs or silent missing-window imputations.

## MAP@5 versus saved v12 predictions

| Split | Saved v12 MAP@5 | Extended MAP@5 | Paired difference | Conditional paired bootstrap 95% interval | Improved / worsened / unchanged users |
| --- | ---: | ---: | ---: | --- | --- |
| main | 0.350918798799 | 0.361626846847 | +0.010708048048 | [+0.008481904, +0.013065141] | 1162 / 750 / 2713 |
| auxiliary | 0.340264037190 | 0.351481501659 | +0.011217464468 | [+0.008947574, +0.013649427] | 1092 / 680 / 2817 |

Paired intervals use 2,000 user resamples, seed42. They condition on the reused cohorts and exclude selection uncertainty. Main and auxiliary windows/users overlap and are not independent tests. Both differences and intervals are positive. No additional feature or variant was tested after inspection.

## Candidate equality and retrieval limits

Every cached row_index/users/items/offset and historical label file is hashed before and after the run. All 27 original feature values are exactly equal. Candidate recall and oracle dictionaries exactly match v12; no positives are injected and no programme is added or removed. This isolates reranking with the schedule extension from candidate-generation changes.

| Split | Users | Covered relevant pairs / all targets | Candidate micro recall | Candidate macro recall | Oracle MAP@5 |
| --- | ---: | --- | ---: | ---: | ---: |
| main | 4625 | 15,999 / 21,466 | 74.5318% | 0.728601802 | 0.728601802 |
| auxiliary | 4589 | 15,639 / 21,080 | 74.1888% | 0.724358974 | 0.724358974 |

For relevant set R and candidate set C, recall is |R intersect C|/|R|; macro averages users, micro sums covered/target occurrences. Oracle AP is min(5,|R intersect C|)/min(5,|R|), averaged per user. It equals macro recall because existing target sets have at most five items. It is a diagnostic ceiling within this fixed candidate union, not trained-model performance or a promise of attainable gains. Candidate limits are unchanged; measured improvements are ranking changes.

## Existing history slices and cold users

| Split | Original H80 slice | Users | v12 MAP@5 | Extended MAP@5 | Difference | Improved / worsened / unchanged |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| main | 0 | 108 | 0.133731996 | 0.182615741 | +0.048883745 | 34 / 11 / 63 |
| main | 1–5 | 462 | 0.211899952 | 0.215712482 | +0.003812530 | 91 / 62 / 309 |
| main | 6–20 | 2087 | 0.325122185 | 0.332253101 | +0.007130916 | 492 / 353 / 1242 |
| main | 21+ | 1968 | 0.422829579 | 0.436854816 | +0.014025237 | 545 / 324 / 1099 |
| auxiliary | 0 | 87 | 0.123722861 | 0.175134100 | +0.051411239 | 29 / 10 / 48 |
| auxiliary | 1–5 | 401 | 0.207507620 | 0.214287891 | +0.006780272 | 86 / 46 / 269 |
| auxiliary | 6–20 | 1874 | 0.308707607 | 0.320295269 | +0.011587662 | 433 / 270 / 1171 |
| auxiliary | 21+ | 2227 | 0.399182383 | 0.409317093 | +0.010134710 | 544 / 354 / 1329 |

| Split | N50-cold definition | Users | v12 MAP@5 | Extended MAP@5 | Improved / worsened / unchanged |
| --- | --- | ---: | ---: | ---: | --- |
| main | no_n50_training_history | 74 | 0.120983483 | 0.180518018 | 27 / 7 / 40 |
| main | no_available_n50_history | 76 | 0.128764620 | 0.183662281 | 27 / 8 / 41 |
| auxiliary | no_n50_training_history | 60 | 0.123935185 | 0.174583333 | 20 / 5 / 35 |
| auxiliary | no_available_n50_history | 63 | 0.132583774 | 0.181746032 | 22 / 6 / 35 |

H80 is the original >=0.80 distinct programme history before availability filtering. Cold groups and slice counts match v12 exactly. Cold-group MAP improves here without any cold override. Both models have zero post-score fallback completion slots because the unchanged candidate union already contains the first five global fallback programmes.

## Seen/unseen hits and prediction changes

Seen means N50>0; unseen means N50=0. The old complete candidate features supply this classification for every selected/reference item. Gains/losses are per-user target occurrences entering/leaving top five. AP contribution terms include all preceding hits and are attributed to the hit item’s type; this is descriptive, not causal. The reused helper’s legacy `fused_` prefix refers to the unblended schedule classifier here.

| Split | Seen target hits v12 -> extended | Unseen target hits v12 -> extended | Seen / unseen MAP contribution difference | Entering unseen recommendations / target hits | Leaving unseen recommendations / target hits |
| --- | --- | --- | --- | --- | --- |
| main | 8718 -> 8924 | 364 -> 358 | +0.009528408 / +0.001179640 | 610 / 55 | 695 / 61 |
| auxiliary | 8419 -> 8656 | 320 -> 296 | +0.010817474 / +0.000399990 | 525 / 47 | 869 / 71 |

| Split | Changed lists | Changed positions | Membership-change / order-only users | Common top-five items / all slots | Relevant gains / losses |
| --- | ---: | ---: | --- | --- | --- |
| main | 3977 | 10002 | 3009 / 968 | 19643/23125 (84.9427%) | 599 / 399 |
| auxiliary | 3782 | 9735 | 2691 / 1091 | 19782/22945 (86.2149%) | 580 / 367 |

## Where the gains occur: schedule-only exposure groups

Groups were frozen before evaluation using only the sign of log1p(future broadcastseconds/day)-log1p(past broadcastseconds/day): increased>0, decreased<0, unchanged=0. No outcome-based bins or tolerance threshold were selected. AP precision terms are attributed by the hit programme’s group; the group differences sum to the overall MAP difference. Group changes can include the effect of preceding hits, so they are not causal feature effects.

| Split | Exposure group | Selected slots v12 -> extended | Entering / leaving relevant hits | Net relevant hits | MAP contribution difference |
| --- | --- | --- | --- | ---: | ---: |
| main | increased | 12264 -> 13389 | 393 / 200 | +193 | +0.010601381 |
| main | decreased | 10856 -> 9731 | 206 / 199 | +7 | +0.000106667 |
| main | unchanged | 5 -> 5 | 0 / 0 | +0 | +0.000000000 |
| auxiliary | increased | 4726 -> 6222 | 412 / 99 | +313 | +0.011798927 |
| auxiliary | decreased | 18171 -> 16702 | 168 / 264 | -96 | -0.000402775 |
| auxiliary | unchanged | 48 -> 21 | 0 / 4 | -4 | -0.000178688 |

The gains concentrate in increased-exposure programmes: main gains +0.010601381 MAP contribution there, almost its entire +0.010708048 gain; auxiliary gains +0.011798927 there, partially offset by decreased/unchanged groups. Seen relevant hits rise by206/237 while unseen target hit counts fall by6/24; unseen AP contributions still rise through order/precision changes. Thus the improvement is not simply more unseen target hits or more candidate coverage.

## Seven-feature distributions and missingness

The following distributions describe actual fixed candidate rows (popular items can repeat across users). Each origin JSON also contains unique candidate-programme and all canonical schedule-programme distributions, full schema, row/group counts and original-feature equality checks. Values are rounded; broadcast rates use seconds/day. Every origin has zero missing new-feature values and zero NaN/Inf after passing coverage. Past absence is genuine zero relative to the covered provided catalogue, marked by past_airings_zero.

| Origin | Schedule feature | Mean | Min | Median | P90 | Max | Zero fraction |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| origin_20200406 | past_airings_per_day | 6.14499 | 0.03571 | 1.85714 | 18.00000 | 84.39286 | 0.0000% |
| origin_20200406 | future_airings_per_day | 6.32448 | 0.07143 | 2.00000 | 17.92857 | 88.92857 | 0.0000% |
| origin_20200406 | past_broadcast_seconds_per_day | 11496.52539 | 107.14286 | 7215.00000 | 21154.28516 | 100669.28906 | 0.0000% |
| origin_20200406 | future_broadcast_seconds_per_day | 11224.82422 | 64.28571 | 6342.85693 | 25071.42773 | 106675.71094 | 0.0000% |
| origin_20200406 | log_airings_rate_change | -0.01919 | -1.46283 | 0.00000 | 0.08519 | 1.36524 | 13.2258% |
| origin_20200406 | log_broadcast_rate_change | -0.08694 | -3.13511 | -0.01418 | 0.09918 | 2.76500 | 2.5540% |
| origin_20200406 | past_airings_zero | 0.00000 | 0.00000 | 0.00000 | 0.00000 | 0.00000 | 100.0000% |
| origin_20200420 | past_airings_per_day | 6.13031 | 0.00000 | 2.00000 | 18.17857 | 87.03571 | 0.3552% |
| origin_20200420 | future_airings_per_day | 5.95555 | 0.07143 | 1.71429 | 17.50000 | 91.78571 | 0.0000% |
| origin_20200420 | past_broadcast_seconds_per_day | 11678.65039 | 0.00000 | 7748.57129 | 26832.85742 | 104125.71094 | 0.3552% |
| origin_20200420 | future_broadcast_seconds_per_day | 11072.36523 | 42.85714 | 6364.28564 | 21540.00000 | 106088.57031 | 0.0000% |
| origin_20200420 | log_airings_rate_change | -0.04405 | -1.60944 | -0.03974 | 0.06252 | 1.55060 | 13.7851% |
| origin_20200420 | log_broadcast_rate_change | -0.04574 | -3.98144 | -0.05217 | 0.31010 | 9.58541 | 3.4384% |
| origin_20200420 | past_airings_zero | 0.00355 | 0.00000 | 0.00000 | 0.00000 | 1.00000 | 99.6448% |
| main | past_airings_per_day | 4.85794 | 0.00000 | 1.32143 | 12.25000 | 91.67857 | 4.3953% |
| main | future_airings_per_day | 4.63678 | 0.01429 | 0.95714 | 12.35714 | 87.68571 | 0.0000% |
| main | past_broadcast_seconds_per_day | 9111.36426 | 0.00000 | 4553.57129 | 20410.71484 | 106240.71094 | 4.3953% |
| main | future_broadcast_seconds_per_day | 9044.09277 | 12.85714 | 4375.71436 | 21440.57227 | 101867.14062 | 0.0000% |
| main | log_airings_rate_change | -0.02559 | -1.44336 | 0.01325 | 0.19319 | 2.20984 | 1.0381% |
| main | log_broadcast_rate_change | 0.17551 | -4.58685 | 0.03457 | 0.56749 | 10.00305 | 0.5891% |
| main | past_airings_zero | 0.04395 | 0.00000 | 0.00000 | 0.00000 | 1.00000 | 95.6047% |
| auxiliary | past_airings_per_day | 4.61786 | 0.00000 | 1.14286 | 12.85714 | 90.53571 | 4.9575% |
| auxiliary | future_airings_per_day | 4.48883 | 0.01786 | 0.89286 | 10.89286 | 87.21429 | 0.0000% |
| auxiliary | past_broadcast_seconds_per_day | 8854.89453 | 0.00000 | 4200.00000 | 17667.85742 | 104453.57031 | 4.9575% |
| auxiliary | future_broadcast_seconds_per_day | 8791.31543 | 10.71429 | 4542.85693 | 21416.78516 | 101705.35938 | 0.0000% |
| auxiliary | log_airings_rate_change | -0.03021 | -1.28785 | 0.00000 | 0.16624 | 2.41080 | 5.1584% |
| auxiliary | log_broadcast_rate_change | 0.19844 | -3.49989 | 0.00390 | 0.79979 | 10.22619 | 0.9611% |
| auxiliary | past_airings_zero | 0.04958 | 0.00000 | 0.00000 | 0.00000 | 1.00000 | 95.0425% |
| final | past_airings_per_day | 3.66957 | 0.00000 | 0.57143 | 9.03571 | 86.92857 | 10.3994% |
| final | future_airings_per_day | 3.44968 | 0.01190 | 0.59524 | 7.94048 | 79.66666 | 0.0000% |
| final | past_broadcast_seconds_per_day | 7609.15186 | 0.00000 | 2967.85718 | 16960.71484 | 101689.28906 | 10.3994% |
| final | future_broadcast_seconds_per_day | 6966.36621 | 3.57143 | 2842.85718 | 14742.85742 | 94850.00000 | 0.0000% |
| final | log_airings_rate_change | -0.03152 | -1.89223 | 0.00000 | 0.19023 | 1.93221 | 3.0556% |
| final | log_broadcast_rate_change | 0.50709 | -5.27172 | -0.00652 | 4.37666 | 9.67772 | 1.5612% |
| final | past_airings_zero | 0.10399 | 0.00000 | 0.00000 | 1.00000 | 1.00000 | 89.6006% |

## Descriptive importance, runtime and memory

| Feature | Gain importance | Split count |
| --- | ---: | ---: |
| n30 | 338895.779 | 304 |
| n50_last28days | 194896.247 | 131 |
| n50 | 90396.376 | 48 |
| global_viewers80 | 35490.275 | 266 |
| n80 | 32639.028 | 118 |
| future_airings_per_day | 32161.186 | 317 |
| personal_n50_rank | 25473.120 | 117 |
| global_airings80 | 24347.839 | 190 |
| item_item_rank | 20924.594 | 359 |
| log_airings_rate_change | 14904.500 | 334 |
| log_broadcast_rate_change | 9967.962 | 286 |
| past_broadcast_seconds_per_day | 4683.686 | 143 |
| future_broadcast_seconds_per_day | 3155.863 | 148 |
| past_airings_per_day | 2707.723 | 148 |
| past_airings_zero | 0.000 | 0 |

Frequency and recent counts remain prominent; future airings/day and exposure-change features are also used. These are descriptive training importance values, not causal evidence. Exposure rates, counts, changes and original popularity features are correlated. No feature removal or extra model was tested based on importance.

| Origin | Fixed candidate rows | Augmentation seconds | Extended matrix bytes | Recorded peak process RSS bytes |
| --- | ---: | ---: | ---: | ---: |
| origin_20200406 | 291,619 | 0.154 | 39,660,184 | 442,613,760 |
| origin_20200420 | 313,316 | 0.173 | 42,610,976 | 529,350,656 |
| main | 380,403 | 0.203 | 51,734,808 | 670,416,896 |
| auxiliary | 397,757 | 0.209 | 54,094,952 | 705,789,952 |
| final | 152,442 | 0.092 | 20,732,112 | 718,536,704 |

Classifier fit took 4.297 seconds. Schedule coverage, augmentation, training, evaluation and final-origin statistics took 18.066 seconds before optional final prediction. RSS is process-lifetime high-water, not isolated classifier allocation. Candidate matrices remain bounded by the original at-most255 rows/user; no dense user-item join was introduced. Private matrices, original row metadata, labels and model weights stay outside Git.

Historical label windows remain two weeks, versus ten-week main/eight-week auxiliary and twelve-week final forecasts. Historical histories are four/six weeks versus longer evaluation/final histories. Per-day exposure normalizes full window length but does not eliminate horizon/distribution shift. Overlapping/reused cohorts, changing channel coverage, correlated schedule features and any model selection limit generalization. Positive local intervals do not guarantee improved Kaggle scores.

## Qualified final candidate

The frozen decision requires strict gain against v12 on both splits. This single extension qualifies. The same new classifier weights are reused at final application, without evaluation-label retraining. Its final seven schedule features are recomputed for the 28-day past and exact weeks31–42 future window; all original v12 final rows and 27 features remain identical.

- Filename: `candidate_lightgbm_schedule_exposure_20261030_v13.csv`.
- Absolute path: `/Users/chenfengru/sweettv-recommender-exam/submissions/candidate_lightgbm_schedule_exposure_20261030_v13.csv`.
- SHA-256: `1fd147770b6be8ebcd64c89244af60cb8510440607358ec84c9adc6ffe7ec359`.
- Internal and independent CLI validators: **valid**, all 1,260 original template users/header/order, five distinct available nonzero IDs per row, 6,649 carryover-aware candidate IDs.
- Versus exact submitted v12: 1017 changed lists, 2542 changed rank slots, 654 membership-change and 363 order-only users. 243 lists identical; set overlap 5570/6300 (88.4127%).
- Frozen schedule classifier SHA-256: `51078bfa7e49b7137308fc96aa0f0f2942b2575edeb1f714b2499aec16c316a6`.

English manual submission description is in submission_description.txt:

> Fixed historical LightGBM reranker with v12 candidate union and 27 unchanged causal features, plus seven canonical schedule-exposure features: past28-day and exact future-window airings/day, clipped broadcastseconds/day, their log1p rate changes and zero-past indicator. Same two early training origins/labels and fixed300-tree settings; no future viewing/content features, E2, blend or cold override. Same frozen classifier applied at weeks11–30 cutoff for weeks31–42 carryover-aware candidates. Validated for manual review; no Kaggle score.

## Verification and preserved incumbent

All **79 tests pass**, including new canonical cross-file deduplication/nonzero IDs, clipped carryovers and exact half-open boundaries, simultaneous cross-channel duration sums, full-day normalization, genuine zero-past indicator, missing-coverage stop, schedule invariance to future viewing-log changes, and original27/candidate-row preservation. Existing causal, ranking, schema and submission checks are reused. Runtime assertions check exact historical row/label equality, original27 values, availability, unchanged candidate recall/oracle, slice/cold memberships and frozen classifier hashes.

Frozen protocol SHA-256: `d8e8e000acfebec3265e6a18b7d17dbb455c5db283ac48cbaeafed485fcb15c7`. Source/input hashes, candidate/label/model fingerprints, actual settings, distributions, runtime/RSS and checks are retained in the JSON evidence. V12’s original model and CSV remain byte-for-byte unchanged, as do all other prior artifacts.

Best confirmed submitted v12: user-screenshot-reported Private **0.42660** / Public **0.43394**. Exact CSV SHA-256 `e18c49cb106df5b5e50f3b7123a080443a2ab48c709e68e721ee9965d96b1457`. No independent Kaggle lookup, submission ID or timestamp is invented. The new candidate has not been uploaded and has no Kaggle score.

No Kaggle workflow, submission command, upload or API was used. Native session records remain unmodified; student verification remains pending until personally performed. Stop for user review and manual upload.

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 /private/tmp/sweettv-model-venv/bin/python -m src.experiment_schedule_reranker --data-dir /Users/chenfengru/LLM4Rec-Course-codex/data/sweettv/raw
/private/tmp/sweettv-model-venv/bin/python -m unittest discover -s tests
/private/tmp/sweettv-model-venv/bin/python -m src.report_schedule_reranker
```
