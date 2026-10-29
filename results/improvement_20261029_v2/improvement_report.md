# Bounded improvement review — 29 October 2026

**Recommendation: retain the submitted original personal-frequency baseline.** The strongest new local configuration has only a marginal gain, with uncertainty spanning a loss. An exploratory, validated candidate is available for review because it meets the nominal positive-local-score criterion; it is not recommended as an evidence-backed replacement yet. **No Kaggle page, upload workflow or submission API was used in this stage.** Stop for the user’s review.

## Baseline evidence and validator correction

The user confirms that `first_personal_original_20261029_v1.csv` was manually submitted and that a Kaggle screenshot returned **Private Score 0.38937** and **Public Score 0.39131**. These are user-confirmed screenshot values, not scores independently retrieved during this run. The original screenshot binary/submission reference is not available in this tool run; none was manufactured. `baseline_score_evidence.json` records this provenance.

Submitted CSV SHA-256 remains `53cb8ae4b59b26ab6ee00b5e99ad91044876180e662732a755d3e99a297e64bc`. The baseline file has not been regenerated or modified.

The historical `results/first_submission_20261029/validator_cli.json` actually records an autodetection failure for the one-column candidate export. The internal validation in `first_artifact.json` succeeded, but the previous report incorrectly described the CLI attempt as successful too. The failed file is preserved unchanged. Rerunning the CLI with **`--delimiter ,`** succeeds; `baseline_validator_cli_success.json` separately records 1,260 users, K=5, 6,649 candidates and the unchanged CSV hash. The first-artifact report now explicitly corrects the earlier claim.

## Fixed protocol and bounded results

All local comparisons keep the same **4,625 users, 6,384 candidates**, 80% longest-block validation truth, causal preprocessing, canonical-airing deduplication, interval unions, repeat eligibility and unweighted shared popularity fallback. Fitting is [2020-03-09, 2020-05-18); validation is [2020-05-18, 2020-07-27), in source wall time. No target or cohort was retuned. Earlier recency experiments were not repeated.

| Configuration | Local MAP@5 | Difference from personal baseline | Status |
| --- | ---: | ---: | --- |
| personal_original | 0.317490 | +0.000000 | existing reference, score/ranks reconciled |
| als_original | 0.087237 | -0.230253 | existing reference, score/ranks reconciled |
| cbf_original | 0.024851 | -0.292639 | existing reference, score/ranks reconciled |
| als_lb50 | 0.133973 | -0.183516 | new bounded experiment |
| als_lb80 | 0.152084 | -0.165405 | new bounded experiment |
| cbf_pop_tie | 0.028687 | -0.288802 | new bounded experiment |
| rrf_als_lb80_w0p05 | 0.317258 | -0.000232 | new bounded experiment |
| rrf_als_lb80_w0p1 | 0.317687 | +0.000197 | new bounded experiment |
| rrf_als_lb80_w0p2 | 0.316788 | -0.000702 | new bounded experiment |

The two new ALS fits fix **32 factors, regularization 0.1, 20 iterations, seed 42, one CPU thread**, with observed confidence `1 + 40*log1p(s_ui)` and library `alpha=1`. Only the per-airing inclusion gate changes: retain an airing if its longest merged block/full original airing duration is at least 0.5 or 0.8. Its contribution remains `q=min(1, union_overlap/full_airing_duration)`; contributions are aggregated by user/item before log scaling. Qualified counts used for shared fallback are exactly unchanged. The original ALS factors are loaded for direct top-50 ranks; the original all-positive-overlap model is not refitted for validation.

| ALS signal | Retained user-airings | User-item pairs | Fitting users | Fitting items |
| --- | ---: | ---: | ---: | ---: |
| als_lb50 | 475,291 | 179,742 | 4,784 | 2,682 |
| als_lb80 | 289,762 | 102,689 | 4,726 | 2,432 |

Cleaner ALS signals improve the local score from 0.087237 to 0.133973/0.152084, while reducing item support. This is consistent with incidental overlaps weakening target alignment, but does not isolate a universal causal explanation: filtering also changes sparsity, retained users/items and confidence totals. Both variants remain substantially below personal frequency.

CBF uses the identical fitted category/genre vectors, weighted profiles and cosine scores. Only **exactly equal** positive cosine scores are ordered by descending distinct qualified training viewers, then raw programme ID. No tolerance or rounding is used, and the old CBF fitted fingerprint and original-score replay match the established baseline. The gain from 0.024851 to 0.028687 is small and does not rescue the method.

## Supported candidates, fallback and runtime

| Method | Supported candidate IDs / 6,384 | Full fallback users | Partial completion users | Fallback slots / 23,125 | Fit or load s | Direct top-50 inference s | Peak worker MiB |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| als_original | 2,206 (34.56%) | 44 | 0 | 220 | 0.1186 | 2.0275 | 434.33 |
| als_lb50 | 2,004 (31.39%) | 74 | 0 | 370 | 0.5081 | 1.7961 | 163.12 |
| als_lb80 | 1,831 (28.68%) | 108 | 0 | 540 | 0.3200 | 1.6318 | 126.88 |
| cbf_pop_tie | 3,993 (62.55%) | 44 | 0 | 220 | 0.5332 | 13.3850 | 503.75 |

Support means a trained item factor for ALS or nonempty pre-cutoff content vector for CBF. Unsupported IDs remain in the common global pool and can enter through the unchanged shared fallback. Fit/load timing excludes JSON loading; the original ALS row is a load, not a new fit. Inference covers 4,649 users (evaluation cohort union template users), while all scores and fallback counts use the fixed 4,625-user cohort. RSS is each isolated worker’s lifetime high-water, including imports/data. New ALS filtering changes model-history availability, but not the cohort or its history-size slice definitions.

## Fusion construction and budget

The strongest individual alternative is **als_lb80** (local MAP@5 0.152084). Only that alternative is fused with personal frequency. Each component supplies at most its top 50 **directly scored, supported** IDs, before any popularity completion. A missing component supplies zero evidence. The score is `1/(60+personal_rank) + w/(60+alternative_rank)`, with absent terms zero, personal weight 1.0 and only `w in {0.05,0.1,0.2}` tested. Raw IDs break fused-score ties; shared fallback is applied only after fusion.

| Fusion weight | MAP@5 | Complete fallback | Partial completion | Ranking replay s | Completion replay s |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 0.05 | 0.317258 | 108 | 0 | 0.0454 | 0.0042 |
| 0.1 | 0.317687 | 108 | 0 | 0.0434 | 0.0031 |
| 0.2 | 0.316788 | 108 | 0 | 0.0441 | 0.0035 |

Fusion timing is a separately measured deterministic replay of rank construction/completion from cached direct component lists, excluding component fitting/inference. Every replay exactly reproduces the original predictions. All local experiments, preparation, process startup, inference and assessment together took 40.86 seconds before the final artifact refit. No further configurations were searched.

## History-size slices

Slices use the original number of distinct programmes with qualified pre-cutoff history, identically across every configuration.

| Qualified training items | Users | Personal | Original ALS | ALS ≥50% | ALS ≥80% | Original CBF | CBF popularity ties | Best fusion |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0 | 108 | 0.163050 | 0.109046 | 0.150844 | 0.163050 | 0.087377 | 0.089846 | 0.163050 |
| 1–5 | 462 | 0.171129 | 0.156975 | 0.171853 | 0.170764 | 0.051039 | 0.057347 | 0.165586 |
| 6–20 | 2087 | 0.285914 | 0.126655 | 0.200222 | 0.220758 | 0.034262 | 0.038281 | 0.287998 |
| 21+ | 1968 | 0.393810 | 0.027867 | 0.053900 | 0.074271 | 0.005292 | 0.008429 | 0.393364 |

Every JSON method record includes all slice counts/scores, including the two other fusion weights. The best fusion improves the 6–20-item slice but worsens the 1–5 and 21+ slices. No slice-specific selection or switch was fitted after inspecting these results.

## Credibility and prediction overlap

Best new configuration: **rrf_als_lb80_w0p1**. Local MAP@5 **0.317686607**, an absolute gain of **+0.000196877** over the unrounded personal-frequency reference. AP@5 improves for **297 users**, worsens for **242**, and is unchanged for **4086**.

The paired-user bootstrap 95% percentile interval for the mean difference is **[-0.000928218, +0.001405351]**, using 2,000 resamples of the fixed cohort with replacement, seed 42. It includes zero. This is conditional on this validation set, not a test of Kaggle improvement, and does not correct for choosing models/weights on the same hold-out or earlier experiment reuse. The small nominal gain is therefore not convincing evidence to replace the scored baseline.

Local predictions change for **1637 / 4,625 users**, with **3371 / 23,125 rank-position slots** changed. Top-five set overlap is **94.7286%**. AP can remain unchanged despite a list changing, and slot changes include reordering. The baseline’s 0.38937 private Kaggle score uses different data; no private score or predicted private-score increment is assigned to this candidate.

## Exact candidate for user review

A new candidate was generated because the best new configuration exceeded the frozen local baseline and produced nonduplicate combined-window predictions. This is an **exploratory review artifact**, not a claim of a statistically supported improvement or a recommendation to upload now.

Filename: `candidate_rrf_als_lb80_w0p1_20261029_v2.csv`

Absolute path: `/Users/chenfengru/sweettv-recommender-exam/submissions/candidate_rrf_als_lb80_w0p1_20261029_v2.csv`

[Open candidate CSV](../../submissions/candidate_rrf_als_lb80_w0p1_20261029_v2.csv)

SHA-256: `905971a8a9c47bcf4a88e14cd10d2514feaaea43900d6f513b2eecc4986f19f5`

Final fitting uses the existing canonical, unioned **combined [2020-03-09, 2020-07-27)** cache, not added split qualifications. The selected ≥80% filter is applied to those combined per-airing segments; ALS is refitted with the same fixed settings, then fused with combined-window personal frequency using weight 0.1 and k=60. Prediction is **[2020-07-27, 2020-10-19)**, with known schedule carryovers and the original airing denominators. Only pre-cutoff behaviour is fitted.

Internal and explicit-comma CLI validation both return **valid**: **1260 users, five distinct nonzero available IDs per user, 6649 candidates**, original template header and exact user order. There are 258 distinct recommended IDs. See `candidate_validator_cli.json` and `candidate_artifact.json` for full provenance and checksums.

Against the exact submitted baseline file, **705 / 1260 users** have a different ordered list; **1674 / 6300 recommendation slots** change. Top-five set overlap is 92.5397% (5830 common item placements when order is ignored). These counts describe final-window predictions, separately from the local validation overlap. The submitted baseline bytes and checksum remain unchanged.

## Reproducibility and review boundary

The existing interval matcher, causal cleaning, interaction cache, sparse rankers, verified ALS confidence convention and validator were reused. Three focused tests cover longest-block gating versus union contribution, strict exact-score tie ordering, and direct-only top-50 fusion/completion. **All 33 tests pass**. Existing audit, recency results, failed validator evidence and native session transcript remain preserved; student verification is still pending. Dependencies remain the pinned NumPy 2.2.6, SciPy 1.15.3, implicit 0.7.3 and threadpoolctl 3.7.0 environment on the 24 GiB Mac. Per-method records contain seed, configuration, runtime, worker RSS and source hashes. Private ranks/predictions, filtered interactions and user-level AP remain ignored under `artifacts/improvement_20261029_v2/`.

**Manual submission recommendation: no, not on this evidence.** Keep the already scored original-frequency baseline. The candidate is available if the user chooses an exploratory manual benchmark, but the mean local gain is tiny, uncertainty spans a loss, and 705 final-user lists change. A later independent temporal check would be more informative than claiming this hold-out-selected winner will beat private MAP@5 0.38937. No further experiment or Kaggle action is scheduled. Stop and wait for review.
