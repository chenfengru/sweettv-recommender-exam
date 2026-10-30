# Viewing-strength counts and remaining errors (executed)

**Decision: retain submitted v5 (T50). Neither bonus improves either split; no new prediction CSV or combined-window refit was generated. Neither variant is recommended for manual benchmark submission.**

Exactly two new scores were tested: L05 uses the integer score `2*N50 + N80` (lambda 0.5); L10 uses `N50 + N80` (lambda 1.0). N80 airings are a subset of N50 and intentionally receive an additional bonus. Reference v5 uses N50 alone. Tie keys and fallback remain the original >=0.80 distinct training viewers, total qualified user-airings and ascending raw string programme ID. Interval unions, full original airing denominators, canonical deduplication, causal cleaning/clipping, candidates and repeats are unchanged.

Main: fit [2020-03-09,2020-05-18), validate [2020-05-18,2020-07-27), 4,625 users and 6,384 candidates. Auxiliary: fit [2020-03-09,2020-06-01), validate [2020-06-01,2020-07-27), 4,589 users and 5,742 candidates. Source wall-clock parsing is unchanged. Truth remains the existing >=0.80 targets; original >=0.80 history-slice membership remains fixed. No completed opportunity/week/threshold experiment was rerun. Existing segment databases and cached truths were reused; v5 predictions were reconciled exactly to saved references on both splits.

## Local comparison

| Split | Method | MAP@5 | Delta from v5 | Conditional paired bootstrap 95% interval | Improved / worsened / unchanged users |
| --- | --- | ---: | ---: | --- | --- |
| main | v5 | 0.334711171171 | +0.000000000000 | reference | reference |
| main | L05 | 0.332385105105 | -0.002326066066 | [-0.003693426, -0.000944647] | 445 / 561 / 3619 |
| main | L10 | 0.333026966967 | -0.001684204204 | [-0.003333833, -0.000056947] | 620 / 706 / 3299 |
| auxiliary | v5 | 0.331395910511 | +0.000000000000 | reference | reference |
| auxiliary | L05 | 0.328680782548 | -0.002715127963 | [-0.003991037, -0.001399654] | 410 / 516 / 3663 |
| auxiliary | L10 | 0.329095663543 | -0.002300246967 | [-0.003869194, -0.000729837] | 598 / 658 / 3333 |

The bootstrap uses 2,000 paired-user resamples, seed 42, shared indices for both variants within a split. These intervals are **conditional on the reused cohorts**, not adjusted for repeated hold-out use or selection. The main/auxiliary splits overlap and are not independent tests. All four intervals are below zero, although the main L10 upper endpoint is close to zero. This evidence supports retention of v5 in this bounded round, not a general claim that viewing strength can never help.

## Personal-history retrieval diagnostics

The personal-history set consists of available programmes with at least one N50 training airing. Relevant items are distinct items in the unchanged validation targets. Macro recall averages h / |relevant| by user; micro coverage sums h over summed relevant-item counts. Ranking below is the **full v5 personal ranking before fallback**, not the completed system list.

| Split | Macro recall | Micro covered / relevant | Micro coverage | Personal-history-only oracle MAP@5 |
| --- | ---: | --- | ---: | ---: |
| main | 0.565978378 | 12,498 / 21,466 | 58.2223% | 0.565978378 |
| auxiliary | 0.568442653 | 12,360 / 21,080 | 58.6338% | 0.568442653 |

Per-user oracle AP@5 is `min(5,h) / min(5,|relevant|)`. This is a **diagnostic upper bound for personal-history-only retrieval**, not an attainable model score or an upper bound for the full system with fallback. The macro recall and oracle happen to coincide here because the established targets contain at most five relevant programmes per user. Do not interpret the difference between this oracle and full-system MAP as guaranteed recoverable improvement.

| Split | Rank 1–5 | Rank 6–20 | Rank 21–50 | Beyond 50 | Absent | Absent: other users have N50 | Absent: no N50 interactions |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| main | 8,566 | 3,507 | 416 | 9 | 8,968 | 7,647 | 1,321 |
| auxiliary | 8,396 | 3,468 | 478 | 18 | 8,720 | 7,349 | 1,371 |

Each absent item is available but has no N50 training airing for that user. The first absent category therefore identifies interactions from other users; the second identifies programmes with no N50 interactions from any training user.

**Bottleneck: a mixture, with coverage the larger component of personal-prefix misses.** Main has 8,968 absent relevant items versus 3,932 present but below rank five; auxiliary has 8,720 versus 3,964. Coverage accounts for about 69.5% / 68.7% of these personal-prefix misses. Ranking still matters: 3,507 / 3,468 relevant items sit at ranks 6–20. These counts describe the personal ranker before fallback, not final-system missed-item attribution.

Of absent items, 7,647 / 8,968 (85.3%) main and 7,349 / 8,720 (84.3%) auxiliary already have N50 interactions from other users. The diagnostics support a later controlled investigation of retrieving previously unseen programmes from other-user signals, with a separate cold-item strategy for the remainder. This is evidence of opportunity, not proof that collaborative retrieval will work. No item-item collaborative filtering was implemented in this round. The two bonuses leave the personal candidate set unchanged and do not address this coverage limitation.

## Fixed history-size slices

Slice counts use original >=0.80 distinct training programmes before availability filtering; weights do not change membership.

| Split | History size | Users | v5 MAP@5 | L05 MAP@5 | L10 MAP@5 |
| --- | --- | ---: | ---: | ---: | ---: |
| main | 0 | 108 | 0.162896091 | 0.162896091 | 0.162896091 |
| main | 1–5 | 462 | 0.193964646 | 0.181336580 | 0.179878547 |
| main | 6–20 | 2087 | 0.307892110 | 0.305038466 | 0.305429245 |
| main | 21+ | 1968 | 0.405621895 | 0.406146116 | 0.407582430 |
| auxiliary | 0 | 87 | 0.170593870 | 0.170593870 | 0.170593870 |
| auxiliary | 1–5 | 401 | 0.197744528 | 0.184003186 | 0.183175395 |
| auxiliary | 6–20 | 1874 | 0.300831406 | 0.297484584 | 0.297736719 |
| auxiliary | 21+ | 2227 | 0.387463204 | 0.387158983 | 0.387950781 |

## Ordering and membership changes

| Split | Variant | Changed lists | Changed rank slots | Membership-change users | Order-only users | Common items / all slots | New membership slots |
| --- | --- | ---: | ---: | ---: | ---: | --- | ---: |
| main | L05 | 2606 | 5793 | 1470 | 1136 | 21400 / 23125 (92.5405%) | 1725 |
| main | L10 | 3106 | 7391 | 1893 | 1213 | 20909 / 23125 (90.4173%) | 2216 |
| auxiliary | L05 | 2537 | 5672 | 1436 | 1101 | 21250 / 22945 (92.6128%) | 1695 |
| auxiliary | L10 | 3068 | 7294 | 1876 | 1192 | 20732 / 22945 (90.3552%) | 2213 |

## Reproducibility, preservation and tests

The frozen selection rule requires strictly positive within-split MAP differences on both splits. If both qualify, higher main MAP wins; exact selection ties retain v5. Neither qualifies. No new final-window prediction file was generated and no final refit was run.

All 48 tests pass. Existing exact 0.50/0.80 inclusion, duplicate/overlap, longest-block/full-duration and pre-cutoff leakage regressions were reused. New focused checks verify the N80 bonus, exact integer scores, deterministic global/raw-string ties, unchanged truth/global keys/fallback/slices, and a hand-computable oracle example covering all five rank buckets and both absent categories. Runtime anchor hashes also match those recorded in the completed v5 experiment on each split.

Frozen protocol SHA-256: `0719affae203031ccfdc939a0a2055b9bef7aed27833a9ba08c53fa96f9b3dfe`. Total diagnostics/evaluation/selection: 20.032 seconds. Peak process RSS: 526,794,752 bytes (process-lifetime high-water mark). Input/source hashes, base commit, environment and timings appear in the JSON evidence; dependencies match the established pinned environment.

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 /private/tmp/sweettv-model-venv/bin/python -m src.experiment_viewing_strength --data-dir /Users/chenfengru/LLM4Rec-Course-codex/data/sweettv/raw --output-dir results/viewing_strength_20261030_v6 --private-dir artifacts/viewing_strength_20261030_v6
/private/tmp/sweettv-model-venv/bin/python -m unittest discover -s tests
/private/tmp/sweettv-model-venv/bin/python -m src.report_viewing_strength
```

Preserved best submitted artifact:

- File: `candidate_personal_threshold_050_20261030_v5.csv`.
- Absolute path: `/Users/chenfengru/sweettv-recommender-exam/submissions/candidate_personal_threshold_050_20261030_v5.csv`.
- SHA-256: `593b1134b6625771abfe107e17d074499cedf6efb4ef9306e06289e9566876e5`.
- Private **0.40210**, Public **0.41789**: user-supplied screenshot values transcribed in the attached request. Screenshot binary was not supplied to this run; no independent Kaggle lookup. Submission ID and submission timestamp are unknown and not invented. The evidence recording time is not a submission timestamp.

All previous prediction files and checksums are preserved. No Kaggle workflow, upload, Submit action, or submission API was used. The native session transcript remains unmodified; native exports are not committed. Student verification is pending until personally performed. Stop for user review; any later upload is manual-only.
