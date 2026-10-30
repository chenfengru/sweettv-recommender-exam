# Fixed identity-only LightFM WARP feature extension (executed)

**The extension qualifies under the frozen two-split point-estimate rule and one validated candidate is prepared for manual review. Main improves with a positive conditional interval; auxiliary improvement is small and its interval includes zero. This is a reasonable exploratory benchmark candidate, not established superiority to submitted v13. Retain v13 as the confirmed incumbent until manual benchmarking supplies new evidence.**

## Frozen scope and installed API

Exactly six new columns are appended to unchanged v13 rows and all 34 original feature values: LightFM score, rank, user bias, item bias, unsupported-user flag, unsupported-item flag. No embedding coordinates, candidate expansion, content, model blending, E2, cold-user override, extra seed/configuration or post-result tuning is used. One extended LightGBM classifier is fit on the original 604,935 historical candidate rows and 25,385 positive labels, with exactly v13’s fixed 300-tree settings.

LightFM **1.17** installed successfully from source. Actual compiled backend is `lightfm._lightfm_fast_no_openmp`; it lacks OpenMP and executes single-threaded, matching the explicitly requested num_threads=1. No substitute algorithm was used. Constructor/fit/predict/representation signatures and all dependency versions are saved in installed_api.json. Main versions: NumPy2.2.6, SciPy1.15.3, scikit-learn1.7.2, LightGBM4.6.0. See docs/running_lightfm_extension.md for reproduction.

Requested LightFM settings: loss=warp, no_components=10, learning_rate=0.05, item_alpha=user_alpha=0, max_sampled=10, random_state=42; fit epochs=15 and num_threads=1. Installed defaults retained and recorded by actual get_params: learning_schedule=adagrad, k=5,n=10,rho=0.95,epsilon=1e-6. Fitted RandomState descriptors include the initial seed and resulting state hash. All origin reports retain actual parameters, counts, mappings/state fingerprints and timings.

## Pre-cutoff support, mappings and ranking

At each origin, extract N50 from its own audited canonical pre-cutoff segment cache with observed clipping and full airing denominators. Binary user-item matrices contain one positive per distinct N50 pair regardless of airing frequency. Only users/items with positive support enter mappings. Raw string IDs are sorted ascending for stable dense indices and explicitly saved privately as ordered ID lists plus ID/index dictionaries. Each origin fits a fresh identity-only model; no later-origin weights are borrowed. Historical cutoffs are April6/April20; evaluation cutoffs are May18/June1. Histories start March9. Final July27 LightFM is fitted only after qualification.

Score/rank require both supports; otherwise both are zero. User bias requires only user support; item bias requires only item support. Unsupported values are zero with the explicit flags, and unsupported identities are never passed to predict with random untrained embeddings. Supported user/item biases come from the installed identity representation APIs.

Ranks are one-based among **ALL available origin-supported programmes**, with repeats allowed, descending LightFM score and ascending raw string ID for exact ties. They are not ranks within a user’s candidate union. Only the six scalar features reach LightGBM; private predictive arrays are saved for reproducibility, not used as embedding-coordinate columns.

## Origin support coverage

| Origin | Supported training users / items | Binary N50 pairs | Supported query users / queries | Supported available programmes / all available | Supported candidate pairs / all rows | Unsupported user / item rows |
| --- | --- | ---: | --- | --- | --- | --- |
| origin_20200406 | 4630 / 1275 | 77,144 | 4630 / 4836 | 583 / 2143 (27.2049%) | 290,589 / 291,619 | 1030 / 0 |
| origin_20200420 | 4707 / 1755 | 104,958 | 4707 / 4859 | 760 / 2515 (30.2187%) | 312,556 / 313,316 | 760 / 0 |
| main | 4784 / 2682 | 179,742 | 4551 / 4625 | 2004 / 6384 (31.3910%) | 380,033 / 380,403 | 370 / 0 |
| auxiliary | 4801 / 3031 | 215,794 | 4529 / 4589 | 2086 / 5742 (36.3288%) | 397,457 / 397,757 | 300 / 0 |
| final | 4867 / 4053 | 339,985 | 1256 / 1260 | 2964 / 6649 (44.5781%) | 152,422 / 152,442 | 20 / 0 |

All candidate programmes happen to have item support in every origin because the unchanged generator uses N50 personal/related items and >=0.80 popularity. Many available programmes outside those candidate rows lack support; no candidate expansion is performed. The unsupported-item flag is therefore constant zero in this run, but retained exactly as frozen. Unsupported-user rows still retain supported item biases. True numeric missingness is zero after explicit support encoding.

## MAP@5 against saved v13

Main retains 4,625 users / 6,384 candidates and >=0.80 truth from [2020-05-18,2020-07-27); auxiliary retains 4,589 / 5,742 and truth from [2020-06-01,2020-07-27). Original cohorts, availability, repeat rules and H80 history slices remain fixed. The extended classifier trains only on April6->[April6,April20) and April20->[April20,May4) labels; main/auxiliary labels are opened after feature tables and probabilities are fixed.

| Split | Saved v13 MAP@5 | Extended MAP@5 | Paired difference | Conditional paired bootstrap 95% interval | Improved / worsened / unchanged AP users |
| --- | ---: | ---: | ---: | --- | --- |
| main | 0.361626846847 | 0.363412552553 | +0.001785705706 | [+0.000259940, +0.003352375] | 646 / 564 / 3415 |
| auxiliary | 0.351481501659 | 0.351762790247 | +0.000281288589 | [-0.001502037, +0.002014387] | 669 / 631 / 3289 |

Intervals use 2,000 paired-user resamples, seed42, conditional on the reused cohorts and trained models. Main and auxiliary overlap in time/users; intervals exclude model-selection uncertainty and do not make them independent tests. The auxiliary interval crosses zero, so the small positive point estimate is uncertain. Qualification follows the predeclared strict point-estimate rule, not an additional significance rule. No variants were added to strengthen it.

## Candidate, label and original-feature equality

All historical labels, original v13 matrices and row_index metadata are hashed before/after. Corresponding original34 columns are exactly equal; only six new columns are appended. Classifier rows remain in the same two-origin order, and the original settings/tie-breaking are unchanged. Candidate recall/oracle dictionaries exactly equal v13.

| Split | Covered relevant pairs / all targets | Micro candidate recall | Macro candidate recall | Oracle MAP@5 |
| --- | --- | ---: | ---: | ---: |
| main | 15,999/21,466 | 74.5318% | 0.728601802 | 0.728601802 |
| auxiliary | 15,639/21,080 | 74.1888% | 0.724358974 | 0.724358974 |

Candidate recall is |relevant intersect candidate|/|relevant|, macro averaged over target users or micro summed over target occurrences. Oracle AP=min(5,covered)/min(5,relevant), averaged by user; it equals macro recall for the fixed at-most-five targets. This is a candidate-union diagnostic ceiling, not achieved model performance. Any gain here is a ranking change, not more retrieval coverage.

## Fixed history slices and N50-cold groups

| Split | Original H80 slice | Users | v13 MAP | Extended MAP | Difference | Improved / worsened / unchanged |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| main | 0 | 108 | 0.182615741 | 0.178433642 | -0.004182099 | 5 / 11 / 92 |
| main | 1–5 | 462 | 0.215712482 | 0.215341510 | -0.000370972 | 57 / 49 / 356 |
| main | 6–20 | 2087 | 0.332253101 | 0.335706091 | +0.003452989 | 290 / 238 / 1559 |
| main | 21+ | 1968 | 0.436854816 | 0.437706216 | +0.000851400 | 294 / 266 / 1408 |
| auxiliary | 0 | 87 | 0.175134100 | 0.177279693 | +0.002145594 | 9 / 7 / 71 |
| auxiliary | 1–5 | 401 | 0.214287891 | 0.216854392 | +0.002566500 | 44 / 35 / 322 |
| auxiliary | 6–20 | 1874 | 0.320295269 | 0.322244160 | +0.001948891 | 275 / 240 / 1359 |
| auxiliary | 21+ | 2227 | 0.409317093 | 0.407710797 | -0.001606296 | 341 / 349 / 1537 |

| Split | Cold definition | Users | v13 MAP | Extended MAP | Improved / worsened / unchanged |
| --- | --- | ---: | ---: | ---: | --- |
| main | no_n50_training_history | 74 | 0.180518018 | 0.178265766 | 3 / 7 / 64 |
| main | no_available_n50_history | 76 | 0.183662281 | 0.184100877 | 4 / 7 / 65 |
| auxiliary | no_n50_training_history | 60 | 0.174583333 | 0.175666667 | 6 / 5 / 49 |
| auxiliary | no_available_n50_history | 63 | 0.181746032 | 0.183439153 | 7 / 5 / 51 |

H80 is the original >=0.80 distinct programme history before availability filtering. Full N50-cold users are unsupported by LightFM; availability-cold users may still have supported historical identities. Cold behaviour is mixed and no override is introduced. Post-score fallback completion remains zero because original candidate unions already include five global fallback items.

## Seen/unseen hit attribution and prediction changes

Seen means positive pre-cutoff N50. Relevant gains/losses count entering/leaving target occurrences per user. AP terms are assigned by hit type with all preceding hits retained; this descriptive decomposition is not causal. The reused helper’s legacy `fused_` prefix denotes current unblended classifier predictions.

| Split | Seen target hits v13 -> extended | Unseen target hits v13 -> extended | Seen / unseen MAP contribution difference | Entering unseen items / target hits | Leaving unseen items / target hits |
| --- | --- | --- | --- | --- | --- |
| main | 8924 -> 8948 | 358 -> 365 | +0.001660240 / +0.000125465 | 501 / 36 | 474 / 29 |
| auxiliary | 8656 -> 8651 | 296 -> 293 | +0.000039345 / +0.000241943 | 536 / 31 | 490 / 34 |

| Split | Changed lists | Changed rank slots | Membership-change / order-only users | Common top-five items / all slots | Relevant hit gains / losses |
| --- | ---: | ---: | --- | --- | --- |
| main | 3033 | 6721 | 1613 / 1420 | 21379/23125 (92.4497%) | 260 / 229 |
| auxiliary | 3157 | 7098 | 1674 / 1483 | 21119/22945 (92.0418%) | 264 / 272 |

Main nets31 relevant hits; auxiliary nets-8 despite its small MAP increase, reflecting precision/order changes. The extension does not improve every user or all hit-count measures. Detailed slice attribution and list changes remain in comparison.json.

## Feature distributions, missingness and cross-origin shift

| Origin | Feature | Min | Mean | Median | P90 | Max | Zero fraction |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| origin_20200406 | lightfm_score | -7.80756 | 0.51404 | 0.53020 | 1.83186 | 4.78911 | 0.3532% |
| origin_20200406 | lightfm_rank | 0.00000 | 47.37358 | 34.00000 | 100.00000 | 583.00000 | 0.3532% |
| origin_20200406 | lightfm_user_bias | -5.34377 | -1.34856 | -1.33243 | -0.75025 | 0.00000 | 0.5250% |
| origin_20200406 | lightfm_item_bias | -1.14661 | 1.31539 | 1.25230 | 2.14020 | 3.20710 | 0.0000% |
| origin_20200406 | lightfm_unsupported_user | 0.00000 | 0.00353 | 0.00000 | 0.00000 | 1.00000 | 99.6468% |
| origin_20200406 | lightfm_unsupported_item | 0.00000 | 0.00000 | 0.00000 | 0.00000 | 0.00000 | 100.0000% |
| origin_20200420 | lightfm_score | -8.37385 | 0.51121 | 0.55116 | 1.88370 | 5.08343 | 0.2426% |
| origin_20200420 | lightfm_rank | 0.00000 | 52.39286 | 36.00000 | 109.00000 | 760.00000 | 0.2426% |
| origin_20200420 | lightfm_user_bias | -6.73222 | -1.56385 | -1.53698 | -0.86704 | 0.00000 | 0.2895% |
| origin_20200420 | lightfm_item_bias | -1.11326 | 1.40579 | 1.35138 | 2.23289 | 3.12250 | 0.0000% |
| origin_20200420 | lightfm_unsupported_user | 0.00000 | 0.00243 | 0.00000 | 0.00000 | 1.00000 | 99.7574% |
| origin_20200420 | lightfm_unsupported_item | 0.00000 | 0.00000 | 0.00000 | 0.00000 | 0.00000 | 100.0000% |
| main | lightfm_score | -9.53812 | -0.03760 | 0.12246 | 1.64690 | 5.13976 | 0.0973% |
| main | lightfm_rank | 0.00000 | 115.96753 | 46.00000 | 301.00000 | 1997.00000 | 0.0973% |
| main | lightfm_user_bias | -7.49225 | -2.19634 | -2.13286 | -1.24728 | 0.00000 | 0.1236% |
| main | lightfm_item_bias | -1.13148 | 1.27820 | 1.44067 | 2.15589 | 2.93823 | 0.0000% |
| main | lightfm_unsupported_user | 0.00000 | 0.00097 | 0.00000 | 0.00000 | 1.00000 | 99.9027% |
| main | lightfm_unsupported_item | 0.00000 | 0.00000 | 0.00000 | 0.00000 | 0.00000 | 100.0000% |
| auxiliary | lightfm_score | -10.24971 | -0.29982 | -0.08731 | 1.51060 | 5.09095 | 0.0754% |
| auxiliary | lightfm_rank | 0.00000 | 130.00955 | 50.00000 | 346.00000 | 2083.00000 | 0.0754% |
| auxiliary | lightfm_user_bias | -7.57064 | -2.45306 | -2.34486 | -1.34732 | 0.00000 | 0.0754% |
| auxiliary | lightfm_item_bias | -1.12335 | 1.30099 | 1.47808 | 2.11750 | 3.11056 | 0.0000% |
| auxiliary | lightfm_unsupported_user | 0.00000 | 0.00075 | 0.00000 | 0.00000 | 1.00000 | 99.9246% |
| auxiliary | lightfm_unsupported_item | 0.00000 | 0.00000 | 0.00000 | 0.00000 | 0.00000 | 100.0000% |
| final | lightfm_score | -7.98837 | -1.32008 | -1.12750 | 0.92584 | 4.84293 | 0.0131% |
| final | lightfm_rank | 0.00000 | 234.79784 | 76.00000 | 688.00000 | 2957.00000 | 0.0131% |
| final | lightfm_user_bias | -7.03102 | -3.39663 | -3.24237 | -1.94938 | 0.00000 | 0.0131% |
| final | lightfm_item_bias | -1.11763 | 1.20502 | 1.28017 | 2.15187 | 3.08019 | 0.0000% |
| final | lightfm_unsupported_user | 0.00000 | 0.00013 | 0.00000 | 0.00000 | 1.00000 | 99.9869% |
| final | lightfm_unsupported_item | 0.00000 | 0.00000 | 0.00000 | 0.00000 | 0.00000 | 100.0000% |

All 40-column tables are finite and original34 values unchanged. Zero score/rank for unsupported pairs is enforced; a supported bias is retained even when the other identity is unsupported. Observed zero values are not automatically interpreted as unsupported.

Scores are uncalibrated WARP margins from separately fitted models, and user/item biases are not necessarily comparable across origins. Mean candidate score changes from about+0.51 at the two historical origins to-0.04/-0.30 at main/auxiliary and-1.32 at final. Mean user bias shifts from-1.35/-1.56 to-2.20/-2.45 and-3.40; the supported available universe grows from583/760 to2004/2086 and2964, changing rank distributions. Identical seeds do not align latent axes or guarantee score/bias calibration across these different training problems. No coordinate features, cross-origin normalization or recalibration variant was added.

## Deterministic replay, importance and resources

The predeclared April6 full-data replay uses the same binary matrix, sorted mappings, seed42,15 epochs and one thread. Mappings, predictive embedding/bias arrays and all six candidate feature columns are **bitwise identical**. This is a reproducibility verification, not a configuration search or independent statistical replication. Primary weights are retained; no selection between replays occurs. Unit tests separately verify the same properties on small fixtures.

| Feature | Gain importance | Split count |
| --- | ---: | ---: |
| n30 | 335461.881 | 243 |
| n50_last28days | 195702.238 | 127 |
| n50 | 90767.939 | 44 |
| lightfm_rank | 62425.581 | 215 |
| future_airings_per_day | 29852.299 | 311 |
| n80 | 26905.534 | 116 |
| personal_n50_rank | 22353.364 | 109 |
| global_airings80 | 21161.098 | 153 |
| log_airings_rate_change | 12691.229 | 285 |
| log_broadcast_rate_change | 9435.484 | 257 |
| lightfm_item_bias | 2700.511 | 148 |
| lightfm_score | 2528.508 | 151 |
| lightfm_user_bias | 1916.488 | 144 |
| lightfm_unsupported_item | 0.000 | 0 |
| lightfm_unsupported_user | 0.000 | 0 |

LightFM rank has the largest training gain importance among the six additions. Importance is descriptive, not causal, and correlated original/collaborative features make isolated attribution unreliable. Unsupported flags have zero split importance in this fit but are preserved; neither feature selection nor alternative models were tested.

| Origin | N50 extraction/fit/feature/save elapsed seconds | LightFM fit seconds | Six-feature generation seconds | Binary sparse bytes | Extended matrix bytes | Peak process RSS bytes |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| origin_20200406 | 7.307 | 0.215 | 0.738 | 635,676 | 46,659,040 | 355,696,640 |
| origin_20200420 | 7.428 | 0.294 | 0.910 | 858,496 | 50,130,560 | 522,256,384 |
| main | 10.244 | 0.540 | 1.813 | 1,457,076 | 60,864,480 | 733,675,520 |
| auxiliary | 11.094 | 0.677 | 1.939 | 1,745,560 | 63,641,120 | 775,241,728 |
| final | 12.695 | 1.149 | 0.767 | 2,739,352 | 24,390,720 | 781,877,248 |

Extended LightGBM fit: 4.546 seconds; run through both evaluations: 44.474 seconds before conditional final fitting. First-origin elapsed includes the one replay. RSS is process-lifetime high-water, not isolated model memory. Scoring is one user against all supported available items at a time; no dense full user-item score matrix is materialized. Original candidate tables remain bounded by255 rows/user.

Limitations remain: two-week historical label horizons versus ten/eight-week validation and twelve-week final predictions; four/six-week historical behaviour versus longer validation/final histories; repeated overlapping cohorts; uncalibrated cross-origin LightFM scores/biases and shifting rank universes; stochastic-model uncertainty beyond this one fixed seed. Deterministic replay verifies implementation repeatability, not generalization. Auxiliary evidence is especially weak because its interval includes zero.

## Frozen decision and final candidate

The decision requires strictly positive MAP differences against v13 on both splits. Both point estimates are positive, so the extension qualifies without adding a significance threshold or further variants. The final LightFM model is then fit only on N50 observations before July27. Its six features are appended to unchanged v13 final rows/34 features; the same extended LightGBM weights are used, with no evaluation-label retraining.

- Filename: `candidate_lightgbm_lightfm_warp_20261030_v14.csv`.
- Absolute path: `/Users/chenfengru/sweettv-recommender-exam/submissions/candidate_lightgbm_lightfm_warp_20261030_v14.csv`.
- SHA-256: `108b159c4e2c687b45f4c4d3e6e9519bace4abc73d5ba888f927a0efbb30ce90`.
- Both internal and separate CLI validators: **valid**, all 1,260 original template users/header/order, five distinct available nonzero IDs, 6,649 carryover-aware candidates.
- Versus exact submitted v13: 811 changed lists, 1818 changed rank slots, 453 membership-change and 358 order-only users. 449 lists identical; set overlap 5811/6300 (92.2381%).
- Frozen extended classifier SHA-256: `e4612c15829ffc34eb30d5423b438deb3d9a20ae66c79fd738bb0486ff01f094`.

Accurate English manual submission description is saved in submission_description.txt:

> Historical LightGBM reranker with all34 v13 features/candidate rows unchanged, plus identity-only LightFM WARP score, full-available supported-item rank, user/item biases and unsupported-user/item indicators. Separate pre-cutoff binary N50 LightFM models:10 components, seed42,15 epochs,1 thread, fixedWARP settings. No latent coordinates, new candidates, blend, E2 or cold override. Same frozen extended classifier at validation and final weeks11–30 cutoff for weeks31–42 predictions. Validated for manual review; no Kaggle result.

## Verification and preserved evidence

All **83 tests pass**. New focused tests cover positive-only deterministic mappings/binary interactions, seeded training replay, support-aware score/rank/bias zeros, rank ties over the entire available supported universe, exact six-column alignment and post-cutoff behaviour invariance. Existing temporal, candidate, schema, ranking and submission checks are reused. Runtime checks confirm every origin’s N50 matches original per-user counts/context in candidate rows, original34/candidate/label equality, unchanged recall/oracle, finite support semantics, saved mappings/state hashes, replay and one frozen extended classifier.

Frozen protocol SHA-256: `a9b7305c9268a15053a2d4fecf2221127bf14c75cd2cdf4d45b36b4bda714d96`. Actual installed APIs/default parameters, dependency versions, source/cache fingerprints, mapping/model/feature hashes, timings and environment are retained in JSON evidence. Private mappings, N50 histories, latent predictive arrays, model weights and user-level rows remain ignored.

Best confirmed submitted v13: user-screenshot-reported Private **0.43400** / Public **0.43774**, CSV SHA-256 `1fd147770b6be8ebcd64c89244af60cb8510440607358ec84c9adc6ffe7ec359`. No independent Kaggle lookup or invented submission ID/time. The new candidate has no Kaggle result; previous CSVs/checksums and models/caches are unchanged.

No Kaggle workflow, submission command, upload or API was used. Native session records remain unmodified; student verification is pending until personally performed. Stop for user review and manual upload.

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 /private/tmp/sweettv-model-venv/bin/python -m src.experiment_lightfm_extension --data-dir /Users/chenfengru/LLM4Rec-Course-codex/data/sweettv/raw
/private/tmp/sweettv-model-venv/bin/python -m unittest discover -s tests
/private/tmp/sweettv-model-venv/bin/python -m src.report_lightfm_extension
```
