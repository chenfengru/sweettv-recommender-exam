# Exploratory history-adaptive thresholds and one E2 combination (executed)

**S40+E2 qualifies under the frozen point-estimate rule and is prepared for manual review. The evidence against incumbent v9 is weak: gains are small, both paired intervals include zero, and the grouping hypothesis was derived from the same reused validation slices. Retain v9 as the best confirmed submitted model until a manual benchmark result is available.**

## Exploratory scope and fixed definitions

V10’s existing 1–5 history slice improved under both lower thresholds on both splits. That validation-informed observation motivated this experiment; the grouping is not an independently prespecified hypothesis. Both stages and selection rules were frozen before this run. Paired intervals are conditional on the reused cohorts, exclude grouping/configuration-selection uncertainty, and do not make the overlapping main/auxiliary windows independent tests.

H80 is the number of distinct programmes with positive >=0.80-qualified pre-cutoff training user-airing counts, **before candidate-availability filtering**, exactly the original slice definition. Only users with 1<=H80<=5 adapt. S30 uses N30 for those users, S40 uses N40; all others use N50. V5 N50 is the Stage 1 control, with E2 disabled in all three lists. Original >=0.80 global viewer/airing popularity ties, raw string IDs and shared fallback remain unchanged.

Stage 1 reuses v10 completed threshold lists and selects per user solely through training H80. Frozen cache hashes and source-slice scores reconcile; no audit, split count extraction, retrieval fitting or prior experiment was repeated. Main retains 4,625 users / 6,384 candidates, fit [2020-03-09,2020-05-18), validate [2020-05-18,2020-07-27). Auxiliary retains 4,589 / 5,742, fit [2020-03-09,2020-06-01), validate [2020-06-01,2020-07-27). Truth, original history slices, candidates and anchors stay fixed.

## Stage 1: both adaptive-only configurations

| Split | Model | Reference | MAP@5 | Paired difference | Conditional paired bootstrap 95% interval | Improved / worsened / unchanged AP users |
| --- | --- | --- | ---: | ---: | --- | --- |
| main | S30 | v5 | 0.335078978979 | +0.000367807808 | [-0.000521545, +0.001357731] | 68 / 81 / 4476 |
| main | S30 | v9 | 0.335078978979 | -0.000573453453 | [-0.001493153, +0.000454468] | 88 / 149 / 4388 |
| main | S40 | v5 | 0.335082702703 | +0.000371531532 | [-0.000414767, +0.001282236] | 41 / 57 / 4527 |
| main | S40 | v9 | 0.335082702703 | -0.000569729730 | [-0.001415929, +0.000366123] | 62 / 125 / 4438 |
| auxiliary | S30 | v5 | 0.332233541561 | +0.000837631050 | [-0.000123475, +0.001965882] | 60 / 61 / 4468 |
| auxiliary | S30 | v9 | 0.332233541561 | +0.000055325537 | [-0.000950481, +0.001123941] | 76 / 113 / 4400 |
| auxiliary | S40 | v5 | 0.331862727295 | +0.000466816784 | [-0.000314930, +0.001319744] | 37 / 49 / 4503 |
| auxiliary | S40 | v9 | 0.331862727295 | -0.000315488729 | [-0.001139591, +0.000564234] | 53 / 101 / 4435 |

Each paired interval uses 2,000 user resamples, seed 42. Identical seeded user-index draws are reused for every evaluated comparison within a split. Whole-cohort intervals include unchanged users. These intervals are not adjusted for either stage of selection or for discovering the H80 grouping from v10.

Both S30 and S40 strictly improve v5 on both splits. Their smaller split gains are +0.000367807808 and +0.000371531532 respectively. S40 wins the frozen max-min rule by only 0.000003723724; this is not convincing evidence that S40 is intrinsically better than S30. No exact tie-break was needed. Only S40 was subsequently combined with E2.

S40 adaptive-only is below v9 on both splits and therefore cannot be the final candidate. S30 was not considered at the final stage after S40 selection; no S30+E2 model was evaluated.

## Stage 2: the single predefined combination

Build the completed S40 list, then use the unchanged original E2 helper. Eligibility requires ORIGINAL N50=1 for both its fourth and fifth programmes. Retrieval remains v7’s N50-based unseen-only direct top50 in its original order. Select the first available item absent from the **entire pre-replacement adaptive top five**. Unseen remains N50=0, even when an item has lower-threshold history. The adaptive first four positions are preserved. N30/N40 never replace N50 in E2 eligibility or unseen filtering.

| Split | Model | Reference | MAP@5 | Paired difference | Conditional paired bootstrap 95% interval | Improved / worsened / unchanged AP users |
| --- | --- | --- | ---: | ---: | --- | --- |
| main | S40+E2 | parent | 0.335705405405 | +0.000622702703 | [+0.000248577, +0.001047225] | 72 / 31 / 4522 |
| main | S40+E2 | v5 | 0.335705405405 | +0.000994234234 | [+0.000126836, +0.001991743] | 107 / 75 / 4443 |
| main | S40+E2 | v9 | 0.335705405405 | +0.000052972973 | [-0.000727096, +0.000949833] | 38 / 58 / 4529 |
| auxiliary | S40+E2 | parent | 0.332503389748 | +0.000640662454 | [+0.000246931, +0.001020702] | 60 / 23 / 4506 |
| auxiliary | S40+E2 | v5 | 0.332503389748 | +0.001107479238 | [+0.000240984, +0.002082203] | 89 / 62 / 4438 |
| auxiliary | S40+E2 | v9 | 0.332503389748 | +0.000325173725 | [-0.000431473, +0.001139555] | 35 / 48 / 4506 |

Existing v5 MAP@5 is 0.334711171171 main / 0.331395910511 auxiliary; existing v9 is 0.335652432432 / 0.332178216024. The combination improves its parent and v5 with positive conditional intervals, but its intervals against v9 include zero. In particular, main gain versus v9 is only +0.000052972973. This is an exploratory candidate, not established superiority over v9.

## Adaptation, replacement and fallback usage

| Split | Model | Adaptation-eligible users | E2-eligible users | Actual E2 replacements | Full / partial fallback users | Global fallback slots |
| --- | --- | ---: | ---: | ---: | --- | ---: |
| main | S30 | 462 | 0 | 0 | 76 / 73 | 570 |
| main | S40 | 462 | 0 | 0 | 76 / 103 | 635 |
| main | S40+E2 | 462 | 593 | 593 | 76 / 103 | 635 |
| auxiliary | S30 | 401 | 0 | 0 | 63 / 59 | 473 |
| auxiliary | S40 | 401 | 0 | 0 | 63 / 83 | 523 |
| auxiliary | S40+E2 | 401 | 524 | 524 | 63 / 83 | 523 |

V5/v9 global-fallback slots are 718 main and 598 auxiliary. Stage 1 fallback counts compose exactly from frozen v10 per-slice counts: the lower-threshold 1–5 slice plus N50 elsewhere. Stage 2 inherits those global-fallback counts unchanged: positive N50 at the fifth position implies a direct personal item under either threshold, so E2 never removes a global-fallback slot. Collaborative E2 insertions are direct retrieved items, not global fallback. All first-four and original-N50 E2 invariants are asserted per user.

## Whole-cohort hit, membership and position changes

| Stage | Split | Model | Reference | Relevant hit gains / losses | Net relevant hits | Changed lists / rank slots | Membership-change / order-only users | Top-five common items / all slots |
| --- | --- | --- | --- | --- | ---: | --- | --- | --- |
| 1 | main | S30 | v5 | 43 / 38 | +5 | 420 / 1423 | 379 / 41 | 22492 / 23125 (97.2627%) |
| 1 | main | S30 | v9 | 67 / 117 | -50 | 853 / 1862 | 818 / 35 | 22073 / 23125 (95.4508%) |
| 1 | main | S40 | v5 | 27 / 25 | +2 | 317 / 943 | 269 / 48 | 22759 / 23125 (98.4173%) |
| 1 | main | S40 | v9 | 50 / 103 | -53 | 807 / 1442 | 772 / 35 | 22270 / 23125 (96.3027%) |
| 1 | auxiliary | S30 | v5 | 35 / 22 | +13 | 370 / 1264 | 332 / 38 | 22378 / 22945 (97.5289%) |
| 1 | auxiliary | S30 | v9 | 57 / 87 | -30 | 752 / 1650 | 722 / 30 | 22004 / 22945 (95.8989%) |
| 1 | auxiliary | S40 | v5 | 20 / 16 | +4 | 288 / 873 | 241 / 47 | 22597 / 22945 (98.4833%) |
| 1 | auxiliary | S40 | v9 | 41 / 80 | -39 | 719 / 1323 | 689 / 30 | 22157 / 22945 (96.5657%) |
| 2 | main | S40+E2 | parent | 79 / 38 | +41 | 593 / 593 | 593 / 0 | 22532 / 23125 (97.4357%) |
| 2 | main | S40+E2 | v5 | 102 / 59 | +43 | 808 / 1440 | 782 / 26 | 22177 / 23125 (95.9005%) |
| 2 | main | S40+E2 | v9 | 21 / 33 | -12 | 316 / 862 | 276 / 40 | 22765 / 23125 (98.4432%) |
| 2 | auxiliary | S40+E2 | parent | 65 / 28 | +37 | 524 / 524 | 524 / 0 | 22421 / 22945 (97.7163%) |
| 2 | auxiliary | S40+E2 | v5 | 81 / 40 | +41 | 723 / 1324 | 701 / 22 | 22081 / 22945 (96.2345%) |
| 2 | auxiliary | S40+E2 | v9 | 16 / 18 | -2 | 284 / 809 | 240 / 44 | 22606 / 22945 (98.5226%) |

Relevant gains/losses count entering/leaving target items per user; retained hits can also move. Versus v9 the final combination has **12 fewer relevant top-five hits on main and 2 fewer on auxiliary**, despite slightly higher MAP. Thus the gain is due to the precision/order distribution, not greater net top-five hit count. More users worsen than improve against v9 on both splits. No conclusion of universal per-user benefit is supported.

## Fixed-slice outcomes

Original H80 membership is held fixed. Stage 1 comparisons below use v5; Stage 2 shows both its adaptive parent and incumbent v9. Slice comparisons against every other reported reference, including Stage 1 versus v9 and Stage 2 versus v5, are in the JSON evidence.

| Stage | Split | Model | Reference | Slice | Users | MAP difference | Improved / worsened / unchanged | Relevant gains / losses | Changed lists / positions | Fallback slots |
| --- | --- | --- | --- | --- | ---: | ---: | --- | --- | --- | ---: |
| 1 | main | S30 | v5 | 0 | 108 | +0.000000000 | 0 / 0 / 108 | 0 / 0 | 0 / 0 | 473 |
| 1 | main | S30 | v5 | 1–5 | 462 | +0.003682059 | 68 / 81 / 313 | 43 / 38 | 420 / 1423 | 97 |
| 1 | main | S30 | v5 | 6–20 | 2087 | +0.000000000 | 0 / 0 / 2087 | 0 / 0 | 0 / 0 | 0 |
| 1 | main | S30 | v5 | 21+ | 1968 | +0.000000000 | 0 / 0 / 1968 | 0 / 0 | 0 / 0 | 0 |
| 1 | main | S40 | v5 | 0 | 108 | +0.000000000 | 0 / 0 / 108 | 0 / 0 | 0 / 0 | 473 |
| 1 | main | S40 | v5 | 1–5 | 462 | +0.003719336 | 41 / 57 / 364 | 27 / 25 | 317 / 943 | 162 |
| 1 | main | S40 | v5 | 6–20 | 2087 | +0.000000000 | 0 / 0 / 2087 | 0 / 0 | 0 / 0 | 0 |
| 1 | main | S40 | v5 | 21+ | 1968 | +0.000000000 | 0 / 0 / 1968 | 0 / 0 | 0 / 0 | 0 |
| 1 | auxiliary | S30 | v5 | 0 | 87 | +0.000000000 | 0 / 0 / 87 | 0 / 0 | 0 / 0 | 388 |
| 1 | auxiliary | S30 | v5 | 1–5 | 401 | +0.009585758 | 60 / 61 / 280 | 35 / 22 | 370 / 1264 | 85 |
| 1 | auxiliary | S30 | v5 | 6–20 | 1874 | +0.000000000 | 0 / 0 / 1874 | 0 / 0 | 0 / 0 | 0 |
| 1 | auxiliary | S30 | v5 | 21+ | 2227 | +0.000000000 | 0 / 0 / 2227 | 0 / 0 | 0 / 0 | 0 |
| 1 | auxiliary | S40 | v5 | 0 | 87 | +0.000000000 | 0 / 0 / 87 | 0 / 0 | 0 / 0 | 388 |
| 1 | auxiliary | S40 | v5 | 1–5 | 401 | +0.005342200 | 37 / 49 / 315 | 20 / 16 | 288 / 873 | 135 |
| 1 | auxiliary | S40 | v5 | 6–20 | 1874 | +0.000000000 | 0 / 0 / 1874 | 0 / 0 | 0 / 0 | 0 |
| 1 | auxiliary | S40 | v5 | 21+ | 2227 | +0.000000000 | 0 / 0 / 2227 | 0 / 0 | 0 / 0 | 0 |
| 2 | main | S40+E2 | parent | 0 | 108 | +0.000000000 | 0 / 0 / 108 | 0 / 0 | 3 / 3 | 473 |
| 2 | main | S40+E2 | parent | 1–5 | 462 | +0.000714286 | 19 / 9 / 434 | 20 / 10 | 178 / 178 | 162 |
| 2 | main | S40+E2 | parent | 6–20 | 2087 | +0.001202683 | 50 / 21 / 2016 | 56 / 27 | 397 / 397 | 0 |
| 2 | main | S40+E2 | parent | 21+ | 1968 | +0.000020325 | 3 / 1 / 1964 | 3 / 1 | 15 / 15 | 0 |
| 2 | main | S40+E2 | v9 | 0 | 108 | +0.000000000 | 0 / 0 / 108 | 0 / 0 | 0 / 0 | 473 |
| 2 | main | S40+E2 | v9 | 1–5 | 462 | +0.000530303 | 38 / 58 / 366 | 21 / 33 | 316 / 862 | 162 |
| 2 | main | S40+E2 | v9 | 6–20 | 2087 | +0.000000000 | 0 / 0 / 2087 | 0 / 0 | 0 / 0 | 0 |
| 2 | main | S40+E2 | v9 | 21+ | 1968 | +0.000000000 | 0 / 0 / 1968 | 0 / 0 | 0 / 0 | 0 |
| 2 | auxiliary | S40+E2 | parent | 0 | 87 | +0.000766284 | 1 / 0 / 86 | 1 / 0 | 2 / 2 | 388 |
| 2 | auxiliary | S40+E2 | parent | 1–5 | 401 | +0.001047382 | 16 / 7 / 378 | 16 / 7 | 149 / 149 | 135 |
| 2 | auxiliary | S40+E2 | parent | 6–20 | 1874 | +0.001223764 | 42 / 16 / 1816 | 47 / 21 | 361 / 361 | 0 |
| 2 | auxiliary | S40+E2 | parent | 21+ | 2227 | +0.000071846 | 1 / 0 / 2226 | 1 / 0 | 12 / 12 | 0 |
| 2 | auxiliary | S40+E2 | v9 | 0 | 87 | +0.000000000 | 0 / 0 / 87 | 0 / 0 | 0 / 0 | 388 |
| 2 | auxiliary | S40+E2 | v9 | 1–5 | 401 | +0.003721252 | 35 / 48 / 318 | 16 / 18 | 284 / 809 | 135 |
| 2 | auxiliary | S40+E2 | v9 | 6–20 | 1874 | +0.000000000 | 0 / 0 / 1874 | 0 / 0 | 0 / 0 | 0 |
| 2 | auxiliary | S40+E2 | v9 | 21+ | 2227 | +0.000000000 | 0 / 0 / 2227 | 0 / 0 | 0 / 0 | 0 |

Stage 1 predictions outside H80=1–5 exactly equal v5, including order. Stage 2 predictions outside that group exactly equal v9. All incremental changes against incumbent v9 therefore occur in the validation-informed adaptation slice.

| Split | Original slice | E2 eligible / replacements | Inserted relevant / removed relevant versus parent |
| --- | --- | --- | --- |
| main | 0 | 3 / 3 | 0 / 0 |
| main | 1–5 | 178 / 178 | 20 / 10 |
| main | 6–20 | 397 / 397 | 56 / 27 |
| main | 21+ | 15 / 15 | 3 / 1 |
| auxiliary | 0 | 2 / 2 | 1 / 0 |
| auxiliary | 1–5 | 149 / 149 | 16 / 7 |
| auxiliary | 6–20 | 361 / 361 | 47 / 21 |
| auxiliary | 21+ | 12 / 12 | 1 / 0 |

## Frozen final selection and manual-review artifact

Only selected S40 adaptive-only and its single S40+E2 combination were considered. A final candidate must strictly beat v9 on both splits, maximizing the smaller absolute gain and preferring adaptive-only on exact ties. Adaptive-only fails; S40+E2 qualifies. No tie-break was needed and no unselected E2 combination or extra grouping was tested.

- Filename: `candidate_adaptive_s40_e2_20261030_v11.csv`.
- Absolute path: `/Users/chenfengru/sweettv-recommender-exam/submissions/candidate_adaptive_s40_e2_20261030_v11.csv`.
- SHA-256: `ccac509f8efeeddb9187f1ff2e5300db08f82ae0f9acd1f4ba7d8220f9dd26fb`.
- Internal and separate CLI validation: **valid**; all 1,260 template users in original order/header, five distinct available nonzero IDs per row, 6,649 carryover-aware candidates.
- Final-template adaptation group: **27** users. Final E2 eligibility/replacements: **50/50**.
- Versus submitted v9: **17** changed lists, **44** changed rank slots, 14 users with changed membership and 3 order-only changes. 1243 lists identical; set overlap 6285/6300 (99.7619%).

Counts and H80 were recomputed over the single canonical combined weeks11–30 fitting window, preserving full denominators and observed clipping. Split qualifications were not added. Selected lower counts, N50 and N80 were recomputed; the fixed N50 item-item model was fit once for E2. Final v5 and v9 were reproduced exactly before comparing the candidate. Predictions use weeks31–42 availability with carryovers. The first four are preserved relative to the **adaptive parent**, not necessarily relative to v9.

Only 27 final-template users adapt, compared with 462/401 validation users. All changes from v9 are confined to that group. Different final training length and template population limit transfer of the small exploratory gains. The file is a valid candidate under the frozen rule; evidence does not establish reliable Kaggle improvement. Retain v9 as incumbent until manual benchmarking provides a new result.

English manual submission description is saved in submission_description.txt:

> Exploratory S40+E2: personal threshold 0.40 only for users with1–5 distinct >=80%-qualified training programmes before availability filtering; N50 otherwise. Original >=80% global popularity ties/fallback. Then apply original E2 to completed adaptive list using N50=1 at positions4/5 and fixed N50 unseen-only top50 retrieval outside entire original adaptive top5; preserve adaptive first4. Canonical combined weeks11–30 fit; predict weeks31–42 including carryovers. Grouping was motivated by reused validation slices; local gains are exploratory. Validated for manual review, no Kaggle result.

## Verification and provenance

All **68 tests pass**. New checks cover H80 boundaries0/1/5/6, distinct qualified programmes before availability filtering, per-user lower/N50 count and cached-list choice, identical outside-group Stage 1 predictions, training-only H80 invariance under post-cutoff qualified rows, and original-N50 E2 eligibility/unseen behaviour even when lower-threshold counts disagree. Existing cutoff, interval, ranking, retrieval, replacement and submission checks are reused.

Runtime checks verify frozen cache hashes, source slice scores, original anchors, exact v5/v9 references, per-user Stage 1 outside-group equality, Stage 2 adaptive-prefix preservation, original N50 eligibility, highest candidate in original retrieval order and exclusion of the entire adaptive top five. Private user-level predictions stay outside Git. Original truth files and all previous CSVs/checksums are preserved.

Frozen protocol SHA-256: `5590ae5dfc48a15bf96663d69e155c752d4b1a65df84e2d2bfe6d99045e399a2`. Stage execution/selection took 11.027 seconds. Exact inputs/source hashes, cache fingerprints, base commit, dependencies, timings and process-lifetime RSS are recorded in the JSON evidence.

Submitted v9 SHA-256 remains `f1378b0d6fed62793e14ebb4c1b64cf8b2163485485c15c861aae7e67e556375`. Private0.40261/Public0.41871 are user-screenshot-reported; no independent Kaggle lookup, submission ID or timestamp is invented. The new file has no Kaggle result.

No Kaggle workflow, submission command, upload or submission API was used. Native session records remain unmodified; student verification is pending until personally performed. Stop for user review and manual upload.

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 /private/tmp/sweettv-model-venv/bin/python -m src.experiment_adaptive_threshold --data-dir /Users/chenfengru/LLM4Rec-Course-codex/data/sweettv/raw
/private/tmp/sweettv-model-venv/bin/python -m unittest discover -s tests
/private/tmp/sweettv-model-venv/bin/python -m src.report_adaptive_threshold
```
