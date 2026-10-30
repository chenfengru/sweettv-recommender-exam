# V17: fixed LightGBM LambdaRank on original v14 tables

**Retain submitted v14.** The one frozen ranker reduces MAP@5 on both splits. No final prediction CSV or new submission description was generated; no additional ranking configuration was tested. Student verification remains pending. No Kaggle workflow/command/API/upload was used.

V14 user-screenshot-reported Private **0.43416** / Public **0.44157** remain the best confirmed scores. Submission ID/time are unknown. Its CSV SHA-256 `108b159c4e2c687b45f4c4d3e6e9519bace4abc73d5ba888f927a0efbb30ce90` and all earlier artifacts/checksums remain unchanged.

## Frozen question and formulation

Does learning within-user rankings improve MAP@5 versus binary row-wise v14? [Frozen protocol](../../docs/lambdarank_protocol.md) and [pre-evaluation source hashes/settings](frozen_experiment.json). Restore exactly the original historical tables: Apr6 features with [Apr6,Apr20) labels and Apr20 features with [Apr20,May4) labels, histories from Mar9. No v15 candidate expansion or v16 longer targets. No raw IDs as features. All original ordered 40 features, rows, labels, negatives and uniform queries remain. No new data audit or behavioural/retrieval model fit.

LambdaRank learns an **NDCG-oriented pairwise surrogate, not MAP@5 directly**. With `label_gain=[0,1]`, binary relevant items have unit gain; truncation level8 and query normalization are fixed. Query normalization differs from binary row-wise training, so this changes the training formulation rather than isolating a numerical loss substitution. The same user at different origins remains separate (origin,user) queries, with no query weights.

## Primary and secondary evaluation

| Split | v14 MAP@5 | LambdaRank MAP@5 | Paired difference | Bootstrap 95% interval | Improved / worsened / unchanged |
|---|---:|---:|---:|---|---|
| main | 0.363412552553 | 0.360976216216 | -0.002436336336 | [-0.004438226727, -0.000469560060] | 834 / 878 / 2913 |
| auxiliary | 0.351762790247 | 0.351570179899 | -0.000192610348 | [-0.002028048655, +0.001742622757] | 803 / 799 / 2987 |

Bootstrap: 2,000 paired-user resamples, seed42, percentile95% intervals. Conditional on reused cohorts, excluding configuration-selection uncertainty and accumulated validation-informed development. Main/auxiliary cohorts and windows overlap, so these are not independent replications.

| Split | v14 NDCG@5 | LambdaRank NDCG@5 | Difference |
|---|---:|---:|---:|
| main | 0.479870450390 | 0.477962908970 | -0.001907541419 |
| auxiliary | 0.467160151971 | 0.467668300567 | +0.000508148596 |

NDCG@5 is secondary only. Per user DCG=sum(binary_hit/log2(rank+1)) at ranks1–5, divided by ideal DCG for min(5,|R|) relevant items from full unchanged truth; missing-candidate targets remain in the ideal denominator. Average over the exact fixed cohort. Empty truth would score zero, but both evaluation cohorts have nonempty truth. MAP@5 alone controls selection.

## Queries and table equality

| Origin | Queries | Candidate rows | Positives | Informative queries | Uniform negative / positive | Size min / median / mean / p90 / p95 / max |
|---|---:|---:|---:|---:|---|---|
| origin_20200406 | 4836 | 291,619 | 13020 | 3857 | 979 / 0 | 5 / 61 / 60.302 / 74 / 78 / 236 |
| origin_20200420 | 4859 | 313,316 | 12365 | 3782 | 1077 / 0 | 5 / 64 / 64.482 / 81 / 86 / 250 |

Total: **9695** queries, **604,935** rows, 25,385 positive labels; group-size sum exactly 604,935. **7639** queries contain positive-negative pairs; **2056** uniform-label queries supply no pairwise ranking signal but remain in the fit. Overall query sizes: `{"min": 5, "median": 63.0, "mean": 62.39659618359979, "p90": 78.0, "p95": 83.0, "max": 250, "sum": 604935, "queries": 9695}`.

Each original table already has contiguous user blocks and ascending raw-string item IDs within each query. We use the identity row permutation and concatenate origins; origin/user keys are globally unique. Reverse-permutation feature and label arrays equal originals exactly. No label/feature mismatch, positive injection, negative sampling, origin merging or query dropping. Exact file hashes and original two-week label manifests are in training.json, frozen_experiment.json and verification.json. Weights are omitted entirely.

## Fixed API and model

Installed LightGBM **4.6.0** supports the sklearn `LGBMRanker.fit(..., group=...)` API. The full installed signature, requested/get_params/effective Booster parameters and dependency versions are recorded in [training.json](training.json). Exactly one fit used all rows and exact query sizes, with no eval_set, early stopping, alternative seeds or tuning. Exactly 300 trees were fitted. The implicit default `eval_at=[1,2,3,4,5]` is recorded, but no evaluation set was supplied; it does not select iterations.

Requested settings: objective lambdarank; metric ndcg; gains[0,1]; truncation8; normalizationTrue; learning_rate.05; num_leaves15; max_depth−1; min_child_samples100; reg_lambda1; n_estimators300; random_state42; n_jobs4; deterministicTrue; force_col_wiseTrue. Effective parameters retain these values (thread/iteration aliases become num_threads4/num_iterations300). Other library defaults are recorded rather than silently tuned.

Raw ranking scores are sorted directly, including negative and >1 values; they are not probabilities or sigmoid transformed. Exact-score ties use v14 N50 count, global80 distinct viewers, global80 airing count, then raw-string ID. Shared fallback is unchanged. No E2, protected positions, cold overrides, blending or candidate expansion. All40 columns remain in the inference schema; LightGBM reported39 used training features, reflecting its handling of uninformative columns, not a schema change.

## Main error analysis

Exact v14 table: 4625 users / 380,403 rows / 6384 available programmes. All40 feature values and candidate rows/order are directly reused with verified hashes. Unchanged coverage: 15999/21466 relevant pairs; micro recall 0.745318178, macro recall 0.728601802, oracle MAP@5 0.728601802.

Changed ordered lists 3686; changed rank-position slots 9061; membership-change users 2102; order-only changes 1584; top-five set overlap 0.902443243. Relevant-hit gains/losses 341 / 381 (net -40). Fallback completion remains zero users/slots because all unions already contain global5. The classifier/ranker can select global-source items, distinct from fallback completion.

Seen relevant hits 8948 → 8907; unseen relevant hits 365 → 366. Seen AP contribution change -0.002640660661; unseen +0.000204324324. Contributions attribute each hit's rank precision to seen/unseen under the original AP denominator. Legacy `fused_` JSON fields mean current ranker predictions; no fusion occurred.

| Fixed H80 slice | Users | v14 MAP | Ranker MAP | Delta | Improved / worsened / unchanged | Hit gains / losses | Changed lists / positions / memberships |
|---|---:|---:|---:|---:|---|---|---|
| 0 | 108 | 0.178433642 | 0.174369856 | -0.004063786 | 18 / 20 / 70 | 0 / 2 | 105 / 369 / 21 |
| 1–5 | 462 | 0.215341510 | 0.216945647 | +0.001604137 | 65 / 57 / 340 | 19 / 18 | 384 / 985 / 219 |
| 6–20 | 2087 | 0.335706091 | 0.334404515 | -0.001301576 | 379 / 382 / 1326 | 164 / 156 | 1695 / 4181 / 958 |
| 21+ | 1968 | 0.437706216 | 0.433207289 | -0.004498927 | 372 / 419 / 1177 | 158 / 205 | 1502 / 3526 / 904 |

Slices retain original H80 distinct programme histories before availability filtering. Complete slice-specific seen/unseen effects are in comparison.json.

| Cold group | Users | v14 MAP | Ranker MAP | Improved / worsened / unchanged |
|---|---:|---:|---:|---|
| no_n50_training_history | 74 | 0.178265766 | 0.175788288 | 16 / 14 / 44 |
| no_available_n50_history | 76 | 0.184100877 | 0.180372807 | 16 / 15 / 45 |

Inference/evaluation: 1.271s; process-lifetime peak RSS 726,564,864 bytes.

## Auxiliary error analysis

Exact v14 table: 4589 users / 397,757 rows / 5742 available programmes. All40 feature values and candidate rows/order are directly reused with verified hashes. Unchanged coverage: 15639/21080 relevant pairs; micro recall 0.741888046, macro recall 0.724358974, oracle MAP@5 0.724358974.

Changed ordered lists 3560; changed rank-position slots 8642; membership-change users 2008; order-only changes 1552; top-five set overlap 0.905731096. Relevant-hit gains/losses 364 / 330 (net +34). Fallback completion remains zero users/slots because all unions already contain global5. The classifier/ranker can select global-source items, distinct from fallback completion.

Seen relevant hits 8651 → 8658; unseen relevant hits 293 → 320. Seen AP contribution change -0.000670625409; unseen +0.000478015060. Contributions attribute each hit's rank precision to seen/unseen under the original AP denominator. Legacy `fused_` JSON fields mean current ranker predictions; no fusion occurred.

| Fixed H80 slice | Users | v14 MAP | Ranker MAP | Delta | Improved / worsened / unchanged | Hit gains / losses | Changed lists / positions / memberships |
|---|---:|---:|---:|---:|---|---|---|
| 0 | 87 | 0.177279693 | 0.178850575 | +0.001570881 | 10 / 11 / 66 | 4 / 0 | 84 / 193 / 16 |
| 1–5 | 401 | 0.216854392 | 0.216451926 | -0.000402466 | 51 / 48 / 302 | 19 / 10 | 340 / 908 / 195 |
| 6–20 | 1874 | 0.322244160 | 0.321209386 | -0.001034774 | 313 / 313 / 1248 | 122 / 129 | 1493 / 3646 / 901 |
| 21+ | 2227 | 0.407710797 | 0.408195754 | +0.000484957 | 429 / 427 / 1371 | 219 / 191 | 1643 / 3895 / 896 |

Slices retain original H80 distinct programme histories before availability filtering. Complete slice-specific seen/unseen effects are in comparison.json.

| Cold group | Users | v14 MAP | Ranker MAP | Improved / worsened / unchanged |
|---|---:|---:|---:|---|
| no_n50_training_history | 60 | 0.175666667 | 0.174583333 | 5 / 6 / 49 |
| no_available_n50_history | 63 | 0.183439153 | 0.179894180 | 5 / 9 / 49 |

Inference/evaluation: 1.318s; process-lifetime peak RSS 726,564,864 bytes.

## Reproducibility, final equality and limitations

Fit runtime 5.234s; training-process peak RSS 726,564,864 bytes, measured with resource.ru_maxrss (process-lifetime high-water mark, not a per-phase allocation). Frozen ranker SHA-256 `94a3c9c35fcca7a2e6230e9687c01ee96c3f6c4ea31ab9217ff946ada6cb9762`. [Feature importance](feature_importance.json) gives gain/split counts; top5 by gain: n30, lightfm_rank, n50, personal_n50_rank, n80. These are descriptive model-use diagnostics, not causal explanations.

Final input equality was verified despite failed qualification: 1260 original template users, 152,442 unchanged rows, 6649 available programmes including carryovers. Original feature/index hashes match v14. The ranker was not applied to final rows and no CSV/validator run was needed because selection failed.

All **95 tests pass**. Focused tests cover origin/user key separation, contiguous groups, exact group-size sums, row/label alignment, retention of uniform negative/positive queries, binary labels, deterministic raw-score ordering with v14 tie keys and unchanged40-feature inference schema. Existing cutoff, half-open-window, restored model, candidate, schedule and submission checks are reused. Original two-week manifests and all frozen source artifact/model/CSV hashes pass post-run verification. Model weights/private rows stay ignored; native session records are untouched. Student verification is pending.

The reused overlapping cohorts and accumulated model-selection history limit generalization claims; bootstrap intervals exclude selection uncertainty and training variability. Original training forecast windows remain two weeks, unlike main ten/auxiliary eight/final twelve weeks. Historical feature histories last four/six weeks, versus ten/twelve/twenty weeks at evaluation/final origins. Separately fitted LightFM models can shift scores/bias scales across origins. This bounded result rejects the specified configuration, not all pairwise learning-to-rank approaches. No further variants were tested.

## Decision

Retain submitted v14. Main degrades with a conditional interval below zero; auxiliary has a small negative point estimate with an interval spanning zero. Neither passes the strict gain requirement. No new CSV exists. Manual upload remains solely the user’s action.
