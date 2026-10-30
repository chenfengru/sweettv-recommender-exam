# V18: fixed user-channel affinity extension

Question: does pre-cutoff channel affinity add ranking information, including for N50-unseen programmes?

**One candidate qualifies for manual review** under the frozen strict-MAP-gain-on-both-splits rule. Exactly one fixed binary classifier was fitted; no additional variants. Student verification remains pending. No Kaggle workflow, command, API or upload was used.

V14 user-screenshot-reported Private **0.43416** / Public **0.44157** remain confirmed baseline scores. No submission ID/time is known or invented. Original CSV SHA-256 `108b159c4e2c687b45f4c4d3e6e9519bace4abc73d5ba888f927a0efbb30ce90` and previous artifacts/models remain unchanged.

## Frozen controlled design

[Protocol](../../docs/channel_affinity_protocol.md) and [pre-evaluation settings/source hashes](frozen_experiment.json). Original v14 candidate tables, original [Apr6,Apr20) and [Apr20,May4) historical labels and first40 feature values remain exact. No v15 candidate expansion, v16 longer windows or v17 LambdaRank. Append exactly twelve features and train one fixed v14 binary classifier for300trees/seed42, no tuning, eval_set, early stopping, weights, negative sampling, blend, E2 or cold override. Main/auxiliary labels never enter fitting. The same frozen weights apply on both evaluations and any final application.

For full history from Mar9 and trailing28days: union cleaned observed intervals within each user/channel, clipped to the window; retain viewing without programme attribution in denominators. Sum channel seconds for user exposure totals, so simultaneous channels contribute separately. These are **channel exposure seconds, not unique human attention**. Separately count distinct canonical N50 user-airings on each channel: longest merged block >=50% of full airing duration, qualified independently after window clipping. Full and trailing user totals exactly match existing N50/rolling28 pipeline counts. Raw channel viewing and programme-qualified airing counts are distinct signals.

Programme weights use canonical positive-duration scheduled airings with positive forecast-window overlap, summing clipped broadcast seconds by channel and dividing by programme total. Raw string vsetv_id=channel_id is the established exact mapping; no numeric coercion or guessed mapping. A missing behavioural channel contributes zero numerator, with full denominators and original schedule weights retained. No renormalization to matched channels. Future schedule channel/time information is permitted; future viewing is excluded.

For each window append log1p(weighted viewing seconds), weighted viewing share, log1p(weighted N50 airings), weighted N50 share. Log is applied after weighting. Add four per-user indicators: full_no_viewing, full_no_n50, trailing28_no_viewing, trailing28_no_n50. Zero denominators produce zero shares and indicator1. Total schema52; no raw channel, content, new source flag or extra aggregation.

## Local comparison

| Split | v14 MAP@5 | Extended MAP@5 | Paired delta | Bootstrap95% interval | Improved / worsened / unchanged |
|---|---:|---:|---:|---|---|
| main | 0.363412552553 | 0.369249609610 | +0.005837057057 | [+0.003627061562, +0.007884054054] | 1016 / 839 / 2770 |
| auxiliary | 0.351762790247 | 0.357738856202 | +0.005976065955 | [+0.003751004818, +0.008194595772] | 1032 / 844 / 2713 |

Paired-user bootstrap: 2,000 resamples, seed42, percentile95% intervals. Conditional on reused cohorts; excludes accumulated configuration-selection uncertainty and training variability. Evaluation cohorts/windows overlap and are not independent replications. Both-split point-estimate qualification is not a claim of Kaggle superiority.

## Exact table and training checks

Training retains 604,935 rows and 25,385 positive labels. Every original40 row value is exactly equal to v14 after concatenation; original candidate metadata is read directly and hash verified. Labels are loaded unchanged and verified against frozen hashes/original two-week manifests. All negatives and all-negative queries survive.

- origin_20200406: 291,619 rows, 13020 positives, 979 all-negative queries; labels unchanged.
- origin_20200420: 313,316 rows, 12365 positives, 1077 all-negative queries; labels unchanged.

## Mapping, denominator and feature diagnostics

Mapping coverage is relative to channels with any cleaned positive pre-cutoff exposure at that origin. The user-specific absence of history on an otherwise mapped channel also gives zero numerator; it does not alter weights. Programme-weight averages weight each programme equally; candidate-row averages weight each user-programme row equally. The broadcast-second fraction uses actual clipped scheduled seconds. These denominators are different and are reported separately.

| Origin | Observed channels | Forecast channels | Exact matches / unmatched | Unmatched broadcast seconds fraction | Mean unmatched programme weight | Mean unmatched candidate-row weight | Rows with any unmatched weight |
|---|---:|---:|---|---:|---:|---:|---:|
| origin_20200406 | 191 | 167 | 74 / 93 | 0.548520422 | 0.528405487 | 0.134734486 | 78627 |
| origin_20200420 | 196 | 167 | 75 / 92 | 0.547950238 | 0.546705326 | 0.152966804 | 88315 |
| main | 199 | 188 | 87 / 101 | 0.508025316 | 0.545377726 | 0.194520994 | 144122 |
| auxiliary | 199 | 188 | 87 / 101 | 0.507986285 | 0.543441305 | 0.201505007 | 157060 |
| final | 202 | 191 | 87 / 104 | 0.509361181 | 0.543836010 | 0.225865027 | 71799 |

| Origin / window | Users | No raw viewing (count / fraction) | No N50 (count / fraction) | Total raw channel seconds | Total qualified user-airings |
|---|---:|---|---|---:|---:|
| origin_20200406 / full | 4836 | 9 / 0.001861 | 206 / 0.042597 | 2000507570 | 189847 |
| origin_20200406 / trailing28 | 4836 | 9 / 0.001861 | 206 / 0.042597 | 2000507570 | 189847 |
| origin_20200420 / full | 4859 | 5 / 0.001029 | 152 / 0.031282 | 2946587106 | 279018 |
| origin_20200420 / trailing28 | 4859 | 46 / 0.009467 | 251 / 0.051657 | 1969831573 | 188908 |
| main / full | 4625 | 31 / 0.006703 | 74 / 0.016000 | 4846464205 | 475291 |
| main / trailing28 | 4625 | 92 / 0.019892 | 171 / 0.036973 | 1899877099 | 196213 |
| auxiliary / full | 4589 | 27 / 0.005884 | 60 / 0.013075 | 5623196884 | 564320 |
| auxiliary / trailing28 | 4589 | 95 / 0.020702 | 225 / 0.049030 | 1774741789 | 199720 |
| final / full | 1260 | 0 / 0.000000 | 4 / 0.003175 | 8496130125 | 878586 |
| final / trailing28 | 1260 | 20 / 0.015873 | 32 / 0.025397 | 1847969548 | 201586 |

Each origin’s affinity_diagnostics.json contains all twelve distributions (min/mean/median/p90/max/zero fraction), exact feature windows, finite52/schema checks, cache-backed N50-total equality, runtime and process-lifetime peak memory. Every first40 value remains exact; new columns are float32 and finite. Existing original40 distributions remain unchanged.

## Main error analysis

Fixed input: 4625 users, 380,403 candidate rows, 6384 available programmes. Recall/oracle unchanged: covered relevant pairs 15999/21466, micro recall 0.745318178, macro recall 0.728601802, oracle MAP@5 0.728601802.

Changed ordered lists 3844; changed position slots 9768; membership-change users 2525; order-only changes 1319; top-five set overlap 0.870789189. Relevant-hit gains/losses 533 / 390 (net +143). Shared fallback completion remains zero users/slots because candidate unions contain global5; model selection of global-source items is separate from completion.

Seen relevant hits 8948 → 9048; unseen hits 365 → 408. Seen AP contribution delta +0.004171951952; unseen +0.001665105105. Each hit's rank precision is attributed to its seen/unseen category under the unchanged AP denominator. Legacy JSON `fused_` denotes current predictions; no fusion occurred.

| Fixed H80 slice | Users | v14 MAP | New MAP | Delta | Improved / worsened / unchanged | Hit gains / losses | Changed lists / positions / memberships |
|---|---:|---:|---:|---:|---|---|---|
| 0 | 108 | 0.178433642 | 0.181574074 | +0.003140432 | 13 / 12 / 83 | 2 / 2 | 104 / 264 / 29 |
| 1–5 | 462 | 0.215341510 | 0.223737975 | +0.008396465 | 87 / 63 / 312 | 35 / 29 | 437 / 1296 / 336 |
| 6–20 | 2087 | 0.335706091 | 0.341924080 | +0.006217990 | 489 / 386 / 1212 | 268 / 177 | 1806 / 4679 / 1247 |
| 21+ | 1968 | 0.437706216 | 0.442686456 | +0.004980239 | 427 / 378 / 1163 | 228 / 182 | 1497 / 3529 / 913 |

Slices retain original >=80% history membership before candidate availability filtering. Full slice-specific seen/unseen diagnostics are in comparison.json.

| Cold group | Users | v14 MAP | New MAP | Improved / worsened / unchanged |
|---|---:|---:|---:|---|
| no_n50_training_history | 74 | 0.178265766 | 0.182094595 | 10 / 5 / 59 |
| no_available_n50_history | 76 | 0.184100877 | 0.185197368 | 10 / 6 / 60 |

Inference/evaluation: 1.245s; process-lifetime peak RSS 1,050,624,000 bytes.

## Auxiliary error analysis

Fixed input: 4589 users, 397,757 candidate rows, 5742 available programmes. Recall/oracle unchanged: covered relevant pairs 15639/21080, micro recall 0.741888046, macro recall 0.724358974, oracle MAP@5 0.724358974.

Changed ordered lists 3881; changed position slots 10048; membership-change users 2555; order-only changes 1326; top-five set overlap 0.868773153. Relevant-hit gains/losses 514 / 387 (net +127). Shared fallback completion remains zero users/slots because candidate unions contain global5; model selection of global-source items is separate from completion.

Seen relevant hits 8651 → 8755; unseen hits 293 → 316. Seen AP contribution delta +0.005452349822; unseen +0.000523716133. Each hit's rank precision is attributed to its seen/unseen category under the unchanged AP denominator. Legacy JSON `fused_` denotes current predictions; no fusion occurred.

| Fixed H80 slice | Users | v14 MAP | New MAP | Delta | Improved / worsened / unchanged | Hit gains / losses | Changed lists / positions / memberships |
|---|---:|---:|---:|---:|---|---|---|
| 0 | 87 | 0.177279693 | 0.178212005 | +0.000932312 | 12 / 13 / 62 | 4 / 3 | 82 / 221 / 19 |
| 1–5 | 401 | 0.216854392 | 0.226622333 | +0.009767941 | 69 / 48 / 284 | 33 / 16 | 368 / 1107 / 294 |
| 6–20 | 1874 | 0.322244160 | 0.328296128 | +0.006051968 | 424 / 342 / 1108 | 211 / 152 | 1634 / 4351 / 1138 |
| 21+ | 2227 | 0.407710797 | 0.413137255 | +0.005426458 | 527 / 441 / 1259 | 266 / 216 | 1797 / 4369 / 1104 |

Slices retain original >=80% history membership before candidate availability filtering. Full slice-specific seen/unseen diagnostics are in comparison.json.

| Cold group | Users | v14 MAP | New MAP | Improved / worsened / unchanged |
|---|---:|---:|---:|---|
| no_n50_training_history | 60 | 0.175666667 | 0.188777778 | 9 / 7 / 44 |
| no_available_n50_history | 63 | 0.183439153 | 0.190899471 | 10 / 9 / 44 |

Inference/evaluation: 1.278s; process-lifetime peak RSS 1,139,179,520 bytes.

## Runtime, importance and limitations

One fit, exactly300trees: 5.751s; training-process peak RSS 878,231,552 bytes (resource.ru_maxrss lifetime high-water mark, not per-phase allocation). Fixed classifier SHA-256 `a1e667ad3a87ba6372ff147ef7b1b54d553955c81c6dc7f5d73fba0dd8309226`. Requested/effective settings and versions are in training.json. [Feature importance](feature_importance.json) is descriptive split/gain usage, not causal evidence.

Top appended features by gain: trailing28_log1p_weighted_view_seconds (19761.501), trailing28_weighted_n50_share (7410.478), full_log1p_weighted_view_seconds (6912.001), full_weighted_view_share (5058.064), full_weighted_n50_share (4315.212).

| Origin | Feature construction seconds | Full52 matrix bytes | Process-lifetime peak RSS bytes |
|---|---:|---:|---:|
| origin_20200406 | 7.687 | 60,656,752 | 630,751,232 |
| origin_20200420 | 10.085 | 65,169,728 | 827,539,456 |
| main | 15.160 | 79,123,824 | 1,050,624,000 |
| auxiliary | 16.638 | 82,733,456 | 1,139,179,520 |
| final | 21.225 | 31,707,936 | 1,139,179,520 |

All **100 tests pass**. New checks cover interval clipping/union, raw unattributed viewing in denominators, simultaneous channels, deduplicated canonical N50 counts, full denominators and independently clipped trailing qualification, zero histories, multi-channel schedule weights, exact ID mismatch without coercion, first40 preservation and post-cutoff invariance. Existing temporal/ranking/schema/submission checks are reused. Old CSV/source/model hashes are checked after execution; native session records remain untouched, private histories/weights are ignored. Student verification remains pending.

Reused overlapping evaluation cohorts, accumulated validation-informed selection and training variation are not fully captured by conditional bootstrap intervals. Historical forecasts remain two weeks; main/auxiliary/final forecasts are ten/eight/twelve weeks and feature histories four/six versus ten/twelve/twenty weeks. Channel shares can shift across these windows. Separately fitted LightFM score/bias scales also shift across origins. Raw viewing exposure can include sessions without programme attribution and simultaneous channels, whereas N50 counts require qualified canonical programme airings; neither should be equated with unique attention. Coverage gains alone cannot establish ranking gains.

## Manual-review candidate

Filename: `candidate_lightgbm_channel_affinity_20261030_v18.csv`. Absolute path: `/Users/chenfengru/sweettv-recommender-exam/submissions/candidate_lightgbm_channel_affinity_20261030_v18.csv`. SHA-256: `a62d1afb1a0c015cb70fd60c1e89bb670b731f872b3433dc438526a5ae703c45`.

Existing in-process validator: `{"status": "valid", "users": 1260, "k": 5, "candidate_ids": 6649, "distinct_recommended_ids": 128, "template_sha256": "d8c209dce3c7c9d815d8e2a6226e1be63052ee7afa7e8ba8b75dc2f703967a02", "prediction_sha256": "a62d1afb1a0c015cb70fd60c1e89bb670b731f872b3433dc438526a5ae703c45"}`. Existing independent CLI validator also passes. Comparison with submitted v14: `{"users": 1260, "users_changed": 1053, "users_identical": 207, "recommendation_slots": 6300, "rank_position_slots_changed": 2707, "top5_items_in_common": 5524, "top5_set_overlap_fraction": 0.8768253968253968, "users_with_membership_change": 667, "users_with_order_change_only": 386, "new_item_slots_ignoring_order": 776}`. All1260templateusers/header/order/five distinct nonzero available IDs are validated, including carryover availability. Exactly one CSV generated.

Fixed binary LightGBM reranker with twelve exact user-channel affinity features appended to the original v14 candidate rows and 40 features. Full-history and trailing28-day cleaned per-channel viewing unions include unattributed viewing in exposure denominators; separate N50 counts use canonical airings, clipped-window longest blocks and full-airing denominators. Programme channel weights use clipped forecast schedule seconds, with no mapping invention or missing-weight renormalization. Original two-week historical labels/settings/300trees/seed42, one fit, all negatives retained. Same frozen classifier applied at final cutoff; no candidate expansion, longer targets, LambdaRank, tuning, blend, E2 or cold override. Validated candidate for manual review; no Kaggle result.

This passes the frozen point-estimate rule; conditional intervals and exploratory selection limitations still apply. Any upload remains solely the user’s manual action.

Recommendation: **worth manually submitting** as the one controlled candidate. Gains are positive on both splits and both conditional intervals exclude zero; seen and unseen hit/AP contributions improve. This is still exploratory evidence from overlapping reused cohorts. A material limitation is unmatched channel coverage: at final origin, unmatched schedule channels account for about 50.94% of all clipped programme broadcast seconds and 22.59% of mean candidate-row programme weight. These weights stay in the normalization, with zero numerators as specified. V14 remains the best confirmed submission until the user obtains a result.
