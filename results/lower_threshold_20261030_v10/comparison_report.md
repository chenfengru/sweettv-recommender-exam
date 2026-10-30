# Lower personal-viewing thresholds, without E2 (executed)

**Retain submitted v9 E2. Neither threshold qualifies against the 0.50 threshold-only control on both splits. No final fit or new prediction CSV was generated. No threshold/E2 combination was tested.**

## Frozen question and control

Exactly t=0.30 and 0.40 were tested against 0.50. N_t counts canonical pre-cutoff user-airings whose longest merged observed viewing block covers at least t of the full original airing duration. Ranking is descending N_t, then unchanged original >=0.80 distinct global training viewers, total qualified user-airings and ascending raw string programme ID. Shared fallback remains original >=0.80 popularity. E2 and collaborative retrieval are disabled for every threshold, including 0.50.

Reuse original interval unions, canonical deduplication, full airing denominators, causal cleaning and observed-end clipping. Main remains 4,625 users/6,384 candidates, fit[2020-03-09,2020-05-18), validate[2020-05-18,2020-07-27); auxiliary remains 4,589/5,742, fit[2020-03-09,2020-06-01), validate[2020-06-01,2020-07-27). Truth stays >=0.80. Original >=0.80 history-size membership, candidates, global tie keys and fallback order are fixed. No audit or previously completed experiment was repeated.

N50 was extracted alongside the new thresholds and exactly matched its saved checksummed v7 count cache; completed 0.50 lists exactly matched saved v5 predictions. Original frozen anchor hashes and truth-file hashes reconcile. An optional observer on the established count extractor records duration statistics without changing qualification or ranking.

## Threshold-only MAP@5 comparison

| Split | Personal threshold, E2 off | MAP@5 | Paired difference from0.50 | Paired bootstrap95% interval | Improved / worsened / unchanged AP users |
| --- | ---: | ---: | ---: | --- | --- |
| main | 0.5 | 0.334711171171 | +0.000000000000 | reference | reference |
| main | 0.3 | 0.333379819820 | -0.001331351351 | [-0.003389613, +0.001000140] | 839 / 992 / 2794 |
| main | 0.4 | 0.334991411411 | +0.000280240240 | [-0.001412619, +0.002152598] | 612 / 715 / 3298 |
| auxiliary | 0.5 | 0.331395910511 | +0.000000000000 | reference | reference |
| auxiliary | 0.3 | 0.329341662429 | -0.002054248081 | [-0.004216211, +0.000136454] | 778 / 949 / 2862 |
| auxiliary | 0.4 | 0.331264194572 | -0.000131715939 | [-0.001735535, +0.001585874] | 556 / 660 / 3373 |

Bootstrap: 2,000 paired-user resamples, seed 42, shared user draws across the two thresholds within each split. Intervals are **conditional on reused cohorts and exclude configuration-selection uncertainty**. The splits overlap in time and users and are not independent untouched tests. All four intervals include zero. The point estimates fail the frozen two-split eligibility rule; they do not establish a general statistically certain disadvantage of every lower threshold.

## Submitted v9: separate context, not the control

| Split | Previously measured v9 E2 MAP@5 |0.30 minus v9|0.40 minus v9|
| --- | ---: | ---: | ---: |
| main | 0.335652432432 | -0.002272612613 | -0.000661021021 |
| auxiliary | 0.332178216024 | -0.002836553594 | -0.000914021452 |

These v9 scores are read from completed E2 evidence, not rerun. Both new threshold-only models are below v9 on both splits. Even a threshold beating v5 alone would not establish superiority to v9; E2 is a different controlled factor. Any combination remains a separate future experiment.

## Qualifying counts, personal candidates and coverage

Counts below are canonical user-airing occurrences, not unique broadcast airings. User-item pairs are distinct positive-count user/programme pairs. “Cohort candidate pairs” restricts users to the frozen cohort and programmes to the fixed available pool. Macro coverage averages |relevant intersect personal history|/|relevant| by user; micro sums covered relevant pairs over all relevant pairs. All targets are available and distinct. Enlarged candidate coverage alone is not ranking evidence.

| Split | Threshold | Qualified user-airings (change)| Training user-item pairs (change)| Available training pairs | Cohort candidate pairs (change)| Mean available history | Users gaining usable history |
| --- | ---: | --- | --- | ---: | --- | ---: | ---: |
| main | 0.5 | 475,291 (+0) | 179,742 (+0) | 155,482 | 153,024 (+0) | 33.086 | 0 |
| main | 0.3 | 676,026 (+200,735) | 267,802 (+88,060) | 227,114 | 223,358 (+70,334) | 48.294 | 14 |
| main | 0.4 | 564,084 (+88,793) | 217,844 (+38,102) | 186,594 | 183,594 (+30,570) | 39.696 | 11 |
| auxiliary | 0.5 | 564,320 (+0) | 215,794 (+0) | 174,455 | 171,504 (+0) | 37.373 | 0 |
| auxiliary | 0.3 | 791,357 (+227,037) | 315,338 (+99,544) | 250,510 | 246,012 (+74,508) | 53.609 | 10 |
| auxiliary | 0.4 | 665,268 (+100,948) | 259,354 (+43,560) | 207,906 | 204,292 (+32,788) | 44.518 | 9 |

| Split | Threshold | Relevant pairs covered / all relevant | Micro coverage | Macro coverage | Newly covered relevant pairs | Full / partial fallback users | Fallback slots |
| --- | ---: | --- | ---: | ---: | ---: | --- | ---: |
| main | 0.5 | 12,498 / 21,466 | 58.2223% | 56.5978% | 0 | 76 / 151 | 718 |
| main | 0.3 | 13,182 / 21,466 | 61.4087% | 59.7733% | 684 | 62 / 79 | 506 |
| main | 0.4 | 12,842 / 21,466 | 59.8248% | 58.2137% | 344 | 65 / 110 | 604 |
| auxiliary | 0.5 | 12,360 / 21,080 | 58.6338% | 56.8443% | 0 | 63 / 124 | 598 |
| auxiliary | 0.3 | 13,015 / 21,080 | 61.7410% | 59.9887% | 655 | 53 / 64 | 426 |
| auxiliary | 0.4 | 12,685 / 21,080 | 60.1755% | 58.4510% | 325 | 54 / 90 | 500 |

Global fallback ordering is frozen, but usage may fall as more personal programmes qualify. Coverage expands monotonically; this does not imply better ordered predictions.

## Top-five changes and relevant hits

| Split | Threshold | Changed lists | Changed rank slots | Membership-change users | Order-only users | Top-five common items / slots |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| main | 0.3 | 3834 | 10381 | 2783 | 1051 | 19537/23125 (84.4843%) |
| main | 0.4 | 3000 | 7357 | 1957 | 1043 | 20900/23125 (90.3784%) |
| auxiliary | 0.3 | 3761 | 10116 | 2702 | 1059 | 19491/22945 (84.9466%) |
| auxiliary | 0.4 | 2964 | 7173 | 1915 | 1049 | 20740/22945 (90.3901%) |

| Split | Threshold | Entering relevant top-five hits | Leaving relevant top-five hits | Net hits | Entering relevant hits from newly covered personal history |
| --- | ---: | ---: | ---: | ---: | ---: |
| main | 0.3 | 488 | 482 | +6 | 83 |
| main | 0.4 | 309 | 301 | +8 | 49 |
| auxiliary | 0.3 | 429 | 459 | -30 | 68 |
| auxiliary | 0.4 | 288 | 288 | +0 | 41 |

Entering/leaving relevant hits compare membership with the exact0.50 top five; counts are per-user occurrences. Newly covered relevant histories count retrieval availability, while entering relevant hits require a new top-five recommendation. Reordering retained hits also changes AP. For example 0.30 adds 684/655 relevant candidate pairs but nets only+6/-30 top-five hits and lowers MAP on both splits. At 0.40 auxiliary net hits are zero but MAP is slightly lower, showing the role of positions.

## Fixed original history-size slices

The slices remain based on >=0.80 distinct training programmes before availability filtering. Lower thresholds do not move users between slices. Complete slice coverage/fallback/user-outcome/membership/hit statistics are in comparison.json.

| Split | History size | Users |0.50 MAP|0.30 MAP (difference)|0.40 MAP (difference)|
| --- | --- | ---: | ---: | --- | --- |
| main | 0 | 108 | 0.162896091 | 0.162911523 (+0.000015432) | 0.160434671 (-0.002461420) |
| main | 1–5 | 462 | 0.193964646 | 0.197646705 (+0.003682059) | 0.197683983 (+0.003719336) |
| main | 6–20 | 2087 | 0.307892110 | 0.308155513 (+0.000263403) | 0.309936911 (+0.002044801) |
| main | 21+ | 1968 | 0.405621895 | 0.401348521 (-0.004273374) | 0.403373984 (-0.002247911) |
| auxiliary | 0 | 87 | 0.170593870 | 0.172787356 (+0.002193487) | 0.167567050 (-0.003026820) |
| auxiliary | 1–5 | 401 | 0.197744528 | 0.207330285 (+0.009585758) | 0.203086728 (+0.005342200) |
| auxiliary | 6–20 | 1874 | 0.300831406 | 0.297712558 (-0.003118849) | 0.300124956 (-0.000706451) |
| auxiliary | 21+ | 2227 | 0.387463204 | 0.384042933 (-0.003420271) | 0.386942573 (-0.000520631) |

## Newly included duration summaries and possible short-viewing noise

For each threshold, newly included means t<=longest-block fraction<0.50. The 0.40 group is contained in the0.30 group; **do not add their counts**. Statistics are weighted by canonical user-airing occurrences, not unique programmes/broadcasts. Viewing duration is reported both as the longest merged observed block (qualification quantity) and the total observed interval union. The latter may exceed the longest block when viewing is disconnected. All times are seconds; fractions are unitless. These are full-data descriptive quantiles with linear interpolation, rounded below; full precision is in new_airing_durations.json.

| Split | Threshold | Measure, all training newly included | Count | Mean | Min | P10 | Median | P90 | P95 | Max |
| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| main | 0.3 | full airing seconds | 200,735 | 5076.739 | 180.000 | 1500.000 | 5100.000 | 8400.000 | 10500.000 | 32700.000 |
| main | 0.3 | longest observed block seconds | 200,735 | 1981.562 | 54.000 | 541.000 | 1916.000 | 3436.000 | 4128.300 | 14856.000 |
| main | 0.3 | total observed union seconds | 200,735 | 2269.673 | 54.000 | 555.000 | 2045.000 | 4291.000 | 5351.000 | 28387.000 |
| main | 0.3 | longest block fraction | 200,735 | 0.392 | 0.300 | 0.316 | 0.388 | 0.476 | 0.487 | 0.500 |
| main | 0.4 | full airing seconds | 88,793 | 4914.295 | 180.000 | 1320.000 | 4800.000 | 8400.000 | 9900.000 | 30300.000 |
| main | 0.4 | longest observed block seconds | 88,793 | 2201.190 | 72.000 | 596.000 | 2142.000 | 3753.000 | 4531.000 | 14856.000 |
| main | 0.4 | total observed union seconds | 88,793 | 2482.855 | 72.000 | 616.000 | 2305.000 | 4634.000 | 5748.800 | 28387.000 |
| main | 0.4 | longest block fraction | 88,793 | 0.448 | 0.400 | 0.409 | 0.448 | 0.489 | 0.494 | 0.500 |
| auxiliary | 0.3 | full airing seconds | 227,037 | 5121.775 | 180.000 | 1500.000 | 5400.000 | 8400.000 | 10500.000 | 32700.000 |
| auxiliary | 0.3 | longest observed block seconds | 227,037 | 2001.428 | 54.000 | 545.000 | 1950.000 | 3448.000 | 4135.000 | 14856.000 |
| auxiliary | 0.3 | total observed union seconds | 227,037 | 2282.310 | 54.000 | 559.000 | 2074.000 | 4278.000 | 5335.200 | 28387.000 |
| auxiliary | 0.3 | longest block fraction | 227,037 | 0.392 | 0.300 | 0.316 | 0.389 | 0.476 | 0.488 | 0.500 |
| auxiliary | 0.4 | full airing seconds | 100,948 | 4976.120 | 180.000 | 1380.000 | 4800.000 | 8400.000 | 9900.000 | 30300.000 |
| auxiliary | 0.4 | longest observed block seconds | 100,948 | 2228.946 | 72.000 | 603.000 | 2207.000 | 3772.000 | 4537.000 | 14856.000 |
| auxiliary | 0.4 | total observed union seconds | 100,948 | 2504.059 | 72.000 | 623.000 | 2365.000 | 4622.000 | 5733.000 | 28387.000 |
| auxiliary | 0.4 | longest block fraction | 100,948 | 0.448 | 0.400 | 0.409 | 0.448 | 0.489 | 0.494 | 0.500 |

The same summaries restricted to available programme/user pairs in the frozen cohort are also in the JSON; their medians are shown below.

| Split | Threshold | Newly included available cohort user-airings | Median full airing seconds | Median longest observed block seconds | Median total observed union seconds | Median fraction |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| main | 0.3 | 178,044 | 4500.000 | 1780.000 | 1912.000 | 0.389 |
| main | 0.4 | 79,052 | 4500.000 | 1936.000 | 2102.500 | 0.448 |
| auxiliary | 0.3 | 194,355 | 4500.000 | 1781.000 | 1911.000 | 0.389 |
| auxiliary | 0.4 | 86,762 | 4500.000 | 1952.000 | 2122.000 | 0.448 |

The newly admitted 0.30 group includes observed blocks as short as 54 seconds, but its median is about 32 minutes on both splits. The 0.40 group starts at 72 seconds and has medians about36–37 minutes. Thus these are not uniformly brief visits. Lower relative thresholds can admit more weak or incidental evidence, especially for short airings, but these summaries do not identify user intent or prove that noise caused the observed MAP changes. Longer partial views can also be useful. No extra duration gate or threshold was tested.

## Decision, reproducibility and score provenance

Eligibility requires strictly positive MAP gain over the 0.50 control on both splits. Among eligible thresholds maximize the minimum absolute gain, exact tie toward0.40. No threshold qualifies: 0.30 is negative on both; 0.40 has mixed signs. Retain submitted v9. No final threshold-only fit, candidate CSV, validator run for a new candidate or E2 combination was generated. This round does not support submitting either threshold-only configuration.

All 64 tests pass. New checks verify exact 0.30/0.40/0.50 boundaries, monotonic qualified-airing inclusion, canonical duplicate and disconnected-union behavior, unchanged 0.50 counts with an observer, cutoff-clipped observer values and full denominators. Existing temporal, ranking and submission regressions are reused. Runtime checks reconcile cached 0.50 counts/predictions, fixed anchors/truth, monotonic counts and equality of added counts with duration-summary sample counts.

Frozen protocol SHA-256: `24cef66b1573e81cddd1b98c83fdb70f75eb298f99b45e8105eecaa1edcf1155`. Full comparisons, duration summaries, bootstrap and selection took 19.819 seconds. Peak process RSS: 798,588,928 bytes (process-lifetime high-water, including cached interactions and diagnostic arrays). Exact inputs/source hashes, base commit, dependency versions, cache manifests and timings appear in the JSON evidence.

Best confirmed submitted v9 file: `submissions/candidate_personal_fifth_e2_20261030_v9.csv`; SHA-256 `f1378b0d6fed62793e14ebb4c1b64cf8b2163485485c15c861aae7e67e556375`. Private **0.40261** / Public **0.41871** are **user-screenshot-reported** in the current request; no independent Kaggle lookup. Screenshot binary was not supplied for this run. Submission ID and submission timestamp remain unknown and are not invented; evidence recording time is not a submission timestamp. V5’s exact file/checksum and every other previous artifact are also preserved.

No Kaggle workflow, submission command, upload or API was used. Native session records are unmodified; student verification remains pending until personally performed. Stop for user review. Any future E2 combination requires a separately controlled experiment.

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 /private/tmp/sweettv-model-venv/bin/python -m src.experiment_lower_threshold --data-dir /Users/chenfengru/LLM4Rec-Course-codex/data/sweettv/raw
/private/tmp/sweettv-model-venv/bin/python -m unittest discover -s tests
/private/tmp/sweettv-model-venv/bin/python -m src.report_lower_threshold
```
