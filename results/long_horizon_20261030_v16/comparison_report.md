# V16: longer-horizon historical reranker training

Question: does one fixed longer-horizon historical training construction transfer better to unchanged v14 evaluation/final inputs?

Decision: **retain submitted v14; no new CSV** under strict positive MAP@5 gain on both splits. No additional horizons/configurations were tested. No Kaggle workflow or upload was opened. Student verification remains pending.

V14 confirmed scores are user-screenshot-reported: Private **0.43416**, Public **0.44157**. Submission ID/time are unknown. Original CSV SHA-256 `108b159c4e2c687b45f4c4d3e6e9519bace4abc73d5ba888f927a0efbb30ce90` and all prior artifacts are unchanged.

## Protocol and interpretation

[Frozen protocol](../../docs/long_horizon_protocol.md), [pre-evaluation hashes/settings](frozen_experiment.json). Feature cutoffs Apr6 and Apr20; histories start Mar9. New labels are [Apr6,May18) and [Apr20,May18), respectively six/four weeks. All observed label segments are clipped at May18; airing denominators are full durations, canonical unions and >=80% qualification/top-five targets unchanged. Both origins retain their original equal-row treatment, including legitimate overlapping examples. The historical label overlap [Apr20,May18) creates dependence and is not independent data. No reweighting/deduplication across origins.

Use exactly v14 personal N50 top200 / fixed item-item unseen top50 / global80 first5 union rules. **No v15 LightFM candidate expansion.** Saved origin-specific LightFM predictive arrays are restored only for inference; zero fits. Fixed item-item configurations are rebuilt from identical pre-cutoff N50 counts and checked by exact reconstruction of all original 27 behavioural/retrieval features and candidates under the original window. New availability and full-universe ranks are computed per longer forecast. Future exposure uses full six/four-week normalization with unchanged 28-day past exposure. Candidate users equal pre-cutoff cleaned users union template; labels never choose users/candidates. All negatives and all-negative queries survive.

One new binary 300-tree LightGBM fit uses the fixed v14 parameters/seed, no early stopping, sampling, class weighting, tuning, blend, E2 or cold override. Main/auxiliary labels never enter classifier training. Main/auxiliary/final inputs are direct reads of original v14 feature arrays and row indexes with hash checks, rather than recomputed approximations. The same new classifier applies everywhere.

## Local ranking comparison

| Split | Users | v14 MAP@5 | New MAP@5 | Paired delta | Bootstrap 95% interval | Improved / worsened / unchanged |
|---|---:|---:|---:|---:|---|---|
| main | 4625 | 0.363412552553 | 0.363376456456 | -0.000036096096 | [-0.001961385886, +0.001836003003] | 871 / 838 / 2916 |
| auxiliary | 4589 | 0.351762790247 | 0.348558327886 | -0.003204462362 | [-0.005098405608, -0.001187611983] | 764 / 890 / 2935 |

Intervals use 2,000 paired-user bootstrap resamples, seed42. They condition on reused cohorts, exclude selection uncertainty and do not account for the accumulated validation-informed model development. Main and auxiliary cohorts/windows overlap, so they are not independent replication. Historical training labels also overlap. A qualifying point estimate would not by itself establish generalization or Kaggle superiority.

## Historical reconstruction and descriptive changes

This experiment changes target horizons, available universes/candidate rows and future schedule features together. It **does not isolate label length alone**. The descriptive label-only columns below use longer-window targets restricted to the original available pool on fixed original candidate rows; no extra classifier was fitted.

| Origin | Original / new target weeks | Users | Rows old → new | Positives old → new | Positive rate old → new | All-negative queries old → new |
|---|---|---:|---|---|---|---|
| origin_20200406 | 2 / 6 | 4836 | 291,619 → 298,479 | 13020 → 16083 | 0.044647 → 0.053883 | 979 → 506 |
| origin_20200420 | 2 / 4 | 4859 | 313,316 → 320,070 | 12365 → 14967 | 0.039465 → 0.046762 | 1077 → 650 |

### origin_20200406

Availability: 2143 → 4795 programmes (2652 added). Candidate pairs added/removed 12170 / 5310; changed queries 4621; common rows 286309. Keeping old candidates but switching to new truth yields 16153 covered relevant pairs; the reconstructed new candidate universe yields 16083. Target universes can differ when availability changes, so this is descriptive, not a causal decomposition.

On the fixed old pool/candidate rows, 4059 users change target membership; label-only positive rows become 16786 (original 13020). Candidate rows were constructed before target loading, with no positive injection.

Original truth coverage: macro 0.788516805, micro 0.816761809, oracle 0.788516805, covered/total pairs 13020/15941, target users 4106. New truth/new candidates: macro 0.751136945, micro 0.765674839, oracle 0.751136945, pairs 16083/21005, target users 4559. Empty-target users 277 are excluded only from coverage denominators, not training. Label users outside the fixed feature universe: 32; they are not added.

Schedule exposure changes on 282819 common candidate rows. Per-feature changed-value counts (including universe-dependent ranks/source flags): `{"personal_n50_rank": 17248, "item_item_rank": 232208, "future_airings_per_day": 260612, "future_broadcast_seconds_per_day": 282812, "log_airings_rate_change": 260612, "log_broadcast_rate_change": 282812, "lightfm_rank": 213490}`. Complete feature distributions/support/coverage are in [origin_20200406/historical.json](origin_20200406/historical.json). Unlisted features have zero changed common-row values.

Boundary check: 0 segments start outside [cutoff,May18) or end after May18. Observed segment min/max in source-naive seconds: [1586131200.0, 1589760000.0]. Manifest records exact half-open window, >=80% rule and input/output checksums. Preparation including label reconstruction 34.016s; feature construction 8.444s; process-lifetime peak RSS 1,023,541,248 bytes.

### origin_20200420

Availability: 2515 → 4035 programmes (1520 added). Candidate pairs added/removed 11545 / 4791; changed queries 4686; common rows 308525. Keeping old candidates but switching to new truth yields 14997 covered relevant pairs; the reconstructed new candidate universe yields 14967. Target universes can differ when availability changes, so this is descriptive, not a causal decomposition.

On the fixed old pool/candidate rows, 3463 users change target membership; label-only positive rows become 15227 (original 12365). Candidate rows were constructed before target loading, with no positive injection.

Original truth coverage: macro 0.751322816, micro 0.781062472, oracle 0.751322816, covered/total pairs 12365/15831, target users 4120. New truth/new candidates: macro 0.741232581, micro 0.759245168, oracle 0.741232581, pairs 14967/19713, target users 4473. Empty-target users 386 are excluded only from coverage denominators, not training. Label users outside the fixed feature universe: 16; they are not added.

Schedule exposure changes on 303107 common candidate rows. Per-feature changed-value counts (including universe-dependent ranks/source flags): `{"personal_n50_rank": 22752, "item_item_rank": 234692, "future_airings_per_day": 285157, "future_broadcast_seconds_per_day": 303104, "log_airings_rate_change": 285157, "log_broadcast_rate_change": 303104, "lightfm_rank": 207244}`. Complete feature distributions/support/coverage are in [origin_20200420/historical.json](origin_20200420/historical.json). Unlisted features have zero changed common-row values.

Boundary check: 0 segments start outside [cutoff,May18) or end after May18. Observed segment min/max in source-naive seconds: [1587340800.0, 1589760000.0]. Manifest records exact half-open window, >=80% rule and input/output checksums. Preparation including label reconstruction 30.968s; feature construction 10.129s; process-lifetime peak RSS 1,032,814,592 bytes.

Coverage definitions: macro recall averages |R∩C|/|R| over fixed-universe users with nonempty truth. Micro recall is summed covered pairs divided by summed relevant pairs. Oracle MAP@5 is the mean min(5,|R∩C|)/min(5,|R|). With top-five targets this equals macro recall. Users with no targets remain in training with all-zero labels. Increased coverage is not evidence of improved final ranking.

## Fixed evaluation slices and error analysis

### Main

Exact v14 input equality: 4625 users, 380403 candidate rows, 6384 available programmes; original array/index hashes verified. Candidate recall/oracle unchanged. Changed ordered lists 3667; changed rank-position slots 8699; changed membership users 2158; order-only changes 1509; top-five set overlap 0.898637838.

Relevant-hit gains/losses 410 / 355 (net +55). Seen relevant hits 8948 → 8991; unseen 365 → 377. Seen AP contribution delta -0.000259579580; unseen +0.000223483483. Contributions attribute each hit's rank precision to seen/unseen with the same AP denominator. Legacy JSON `fused_` means current predictions; no fusion occurs. Fallback completion is zero because all candidate unions contain global5; the classifier can still select global-source items.

| Fixed H80 slice | Users | v14 MAP | New MAP | Delta | Improved / worsened / unchanged | Hit gains / losses | Changed lists / positions / membership users |
|---|---:|---:|---:|---:|---|---|---|
| 0 | 108 | 0.178433642 | 0.178598251 | +0.000164609 | 9 / 5 / 94 | 0 / 0 | 99 / 208 / 24 |
| 1–5 | 462 | 0.215341510 | 0.214607985 | -0.000733526 | 62 / 62 / 338 | 18 / 21 | 378 / 955 / 244 |
| 6–20 | 2087 | 0.335706091 | 0.336069185 | +0.000363094 | 398 / 362 / 1327 | 177 / 135 | 1669 / 3972 / 970 |
| 21+ | 1968 | 0.437706216 | 0.437399503 | -0.000306713 | 402 / 409 / 1157 | 215 / 199 | 1521 / 3564 / 920 |

H80 slice membership retains original >=80% distinct history before candidate filtering. Slice-specific seen/unseen effects remain in comparison.json.

| Cold group | Users | v14 MAP | New MAP | Improved / worsened / unchanged |
|---|---:|---:|---:|---|
| no_n50_training_history | 74 | 0.178265766 | 0.180968468 | 8 / 3 / 63 |
| no_available_n50_history | 76 | 0.184100877 | 0.185855263 | 8 / 4 / 64 |

Inference/evaluation 1.472s; process-lifetime peak RSS 1,119,371,264 bytes.
### Auxiliary

Exact v14 input equality: 4589 users, 397757 candidate rows, 5742 available programmes; original array/index hashes verified. Candidate recall/oracle unchanged. Changed ordered lists 3586; changed rank-position slots 8649; changed membership users 2185; order-only changes 1401; top-five set overlap 0.896491610.

Relevant-hit gains/losses 372 / 411 (net -39). Seen relevant hits 8651 → 8612; unseen 293 → 293. Seen AP contribution delta -0.002606171763; unseen -0.000598290598. Contributions attribute each hit's rank precision to seen/unseen with the same AP denominator. Legacy JSON `fused_` means current predictions; no fusion occurs. Fallback completion is zero because all candidate unions contain global5; the classifier can still select global-source items.

| Fixed H80 slice | Users | v14 MAP | New MAP | Delta | Improved / worsened / unchanged | Hit gains / losses | Changed lists / positions / membership users |
|---|---:|---:|---:|---:|---|---|---|
| 0 | 87 | 0.177279693 | 0.175785441 | -0.001494253 | 2 / 2 / 83 | 1 / 0 | 21 / 52 / 17 |
| 1–5 | 401 | 0.216854392 | 0.214359933 | -0.002494458 | 41 / 45 / 315 | 16 / 17 | 339 / 828 / 198 |
| 6–20 | 1874 | 0.322244160 | 0.319857702 | -0.002386458 | 308 / 335 / 1231 | 129 / 140 | 1483 / 3612 / 890 |
| 21+ | 2227 | 0.407710797 | 0.403623335 | -0.004087462 | 413 / 508 / 1306 | 226 / 254 | 1743 / 4157 / 1080 |

H80 slice membership retains original >=80% distinct history before candidate filtering. Slice-specific seen/unseen effects remain in comparison.json.

| Cold group | Users | v14 MAP | New MAP | Improved / worsened / unchanged |
|---|---:|---:|---:|---|
| no_n50_training_history | 60 | 0.175666667 | 0.175666667 | 0 / 0 / 60 |
| no_available_n50_history | 63 | 0.183439153 | 0.183439153 | 0 / 0 / 63 |

Inference/evaluation 1.547s; process-lifetime peak RSS 1,120,452,608 bytes.

## Reproducibility and limitations

Exactly one fit on 618,549 historical rows / 31,050 positives (fraction 0.050198125), 300 trees; fit 4.824s; process-lifetime peak RSS 1,032,830,976 bytes. Dependencies/settings are in [training.json](training.json). Classifier SHA-256 `943ea8db791b0499d2a8873f5876812d73b50b9d6bc6bee2cd67da4ae283469e`. [Feature importance](feature_importance.json) is descriptive gain/split usage, not causal evidence.

Final equality was verified regardless of qualification: original 1260 users, 152442 rows, 6649 available programmes including schedule carryovers; all 40 values and candidate ordering read directly from v14 cache. No final behavioural/model refit is required: only apply the frozen classifier if qualified.

All 90 tests pass. New tests cover exact half-open Apr6/May18 handling, no influence from May18-and-later behaviour, full denominators on crossing airings, rejection of training windows beyond the main cutoff, origin-specific available universes/full future normalization, no positive injection and direct unchanged evaluation-table loading. Existing schema, causal history, restored-model, ranking and submission checks are reused. All old CSV/model/source artifact hashes are rechecked at completion. Native records are untouched; weights/private histories stay ignored. Student verification is pending.

Remaining differences: historical feature histories last four/six weeks and forecasts six/four weeks; main history ten weeks/forecast ten weeks, auxiliary history twelve/forecast eight, final history twenty/forecast twelve. Longer historical labels reduce but do not remove horizon/history-length shift. Separately fitted origin LightFM scores/biases can also shift in scale. Both historical-label and evaluation-window overlap create dependence. Conditional intervals do not quantify all training/selection uncertainty. No claim of Kaggle improvement is warranted without a user-performed submission.

## Decision

Retain v14. The fixed rule requires positive MAP@5 gains on both splits and is not met. No final CSV, final prediction run or submission validator was invoked for a nonexistent candidate. No additional horizon was tested.

Evaluation and final feature distributions are unchanged by construction; refer to the preserved v14 `support_and_features.distributions` records for LightFM scalars, v13 schedule diagnostics for schedule features and v12 feature diagnostics for the original behavioural columns. The equality records contain the exact array/index hashes tying those distributions to this experiment. Historical distributions of all 40 reconstructed columns are included in each historical.json.
