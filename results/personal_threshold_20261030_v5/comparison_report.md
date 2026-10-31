# Personal training-threshold experiment (executed)

Question: does counting shorter but substantial observed viewing improve personal frequency while all global and evaluation qualifications remain at 0.80?

Exactly two new variants were evaluated: T50 (>=0.50) and T65 (>=0.65). Each passing canonical user-airing adds one integer personal count. Ranking is descending personal count, original >=0.80 distinct qualified viewers, original >=0.80 total qualified user-airings, then ascending raw string programme ID. Full original airing durations, causal cleaning, interval unions, canonical deduplication, candidates and repeat eligibility are unchanged. The shared fallback ordering remains anchored to >=0.80; its usage can fall when personal coverage grows.

The opportunity/week experiments were accepted as established and were not repeated. Existing cleaned segment databases and >=0.80 validation truth were reused. Original >=0.80 personal counts exactly matched the interaction caches; v3 predictions exactly matched both saved split references. Truth, global keys, fallback, candidates and original history-slice membership were hashed together and checked unchanged across variants. No validation threshold was relaxed.

## Within-split results

| Split | Method | MAP@5 | Delta from v3 | Conditional paired bootstrap 95% interval | Improved / worsened / unchanged users |
| --- | --- | ---: | ---: | --- | --- |
| main | v3 | 0.326853993994 | +0.000000000000 | reference | reference |
| main | T50 | 0.334711171171 | +0.007857177177 | [+0.005385303, +0.010662553] | 1204 / 1000 / 2421 |
| main | T65 | 0.333174294294 | +0.006320300300 | [+0.004308710, +0.008411287] | 939 / 744 / 2942 |
| auxiliary | v3 | 0.324108919881 | +0.000000000000 | reference | reference |
| auxiliary | T50 | 0.331395910511 | +0.007286990630 | [+0.004674903, +0.009914147] | 1116 / 960 / 2513 |
| auxiliary | T65 | 0.328717101281 | +0.004608181400 | [+0.002576018, +0.006623514] | 836 / 765 / 2988 |

The main split retains 4,625 users / 6,384 candidates (fit March 9–May 18, validation May 18–July 27). Auxiliary retains 4,589 / 5,742 (fit March 9–June 1, validation June 1–July 27), using the same half-open wall-clock convention. These are different tasks: compare differences within each split, not their absolute MAP values across splits.

Bootstrap: 2,000 paired-user resamples, seed 42, shared draws for the two variants within each split. Intervals are conditional on the reused cohorts. The auxiliary windows and users overlap the main split; this is a robustness check, not an independent untouched test. Reusing hold-outs and selecting the stronger of two variants introduces selection uncertainty not represented by these intervals. Local gains do not guarantee Kaggle gains.

## Original history-size slices

Slices use distinct >=0.80 training programmes before candidate filtering and remain fixed even when lower thresholds add history.

| Split | Original history size | Users | v3 MAP@5 | T50 MAP@5 | T65 MAP@5 |
| --- | --- | ---: | ---: | ---: | ---: |
| main | 0 | 108 | 0.163050412 | 0.162896091 | 0.157757202 |
| main | 1–5 | 462 | 0.176880712 | 0.193964646 | 0.179733045 |
| main | 6–20 | 2087 | 0.299143374 | 0.307892110 | 0.305282037 |
| main | 21+ | 1968 | 0.400436568 | 0.405621895 | 0.408400943 |
| auxiliary | 0 | 87 | 0.172905492 | 0.170593870 | 0.164463602 |
| auxiliary | 1–5 | 401 | 0.178942920 | 0.197744528 | 0.184497091 |
| auxiliary | 6–20 | 1874 | 0.292018113 | 0.300831406 | 0.296715433 |
| auxiliary | 21+ | 2227 | 0.383158958 | 0.387463204 | 0.388031607 |

## Personal coverage expansion

| Split | Variant | Additional training pairs (all / available) | Additional available cohort pairs | Users gaining usable history (all / cohort) | Personal user-airings |
| --- | --- | --- | ---: | --- | ---: |
| main | T50 | 77053 / 63892 | 62726 | 60 / 36 | 475291 |
| main | T65 | 33153 / 27707 | 27233 | 39 / 24 | 370959 |
| auxiliary | T50 | 88489 / 68836 | 67432 | 59 / 29 | 564320 |
| auxiliary | T65 | 38369 / 30060 | 29480 | 34 / 16 | 445515 |

A pair is a distinct user/programme with a positive personal count. Usable history requires at least one programme in that split’s unchanged candidate pool. All-user figures concern training users; cohort figures concern the frozen evaluation users.

## Ordering and membership

| Split | Variant | Changed lists | Changed rank slots | Membership-change users | Order-only users | Common items / total slots | New membership slots |
| --- | --- | ---: | ---: | ---: | ---: | --- | ---: |
| main | T50 | 4102 | 12142 | 3267 | 835 | 18441 / 23125 (79.74%) | 4684 |
| main | T65 | 3451 | 9173 | 2413 | 1038 | 20110 / 23125 (86.96%) | 3015 |
| auxiliary | T50 | 4046 | 11813 | 3241 | 805 | 18277 / 22945 (79.66%) | 4668 |
| auxiliary | T65 | 3417 | 8981 | 2428 | 989 | 19909 / 22945 (86.77%) | 3036 |

## Selection and manual-review artifact

Both variants strictly improve both splits. T50 has the higher main MAP and is selected under the frozen rule. Recommend one manual submission of T50 as a locally supported candidate; retain v3 as the best confirmed submitted model until the user obtains a new result. T50’s zero-history main slice is slightly worse; aggregate improvements are not universal.

The selected configuration was refit by recomputing integer personal qualifications from the single combined weeks 11–30 cleaned segment database. Counts were not added across split qualifications. Global keys/fallback still use the combined-window >=0.80 statistics. Predictions cover weeks 31–42; the 6,649-ID availability pool includes schedule carryovers. Combined-window v3 predictions were reproduced and matched the exact submitted CSV before comparing the candidate.

- Filename: `candidate_personal_threshold_050_20261030_v5.csv`
- Absolute path: `/Users/chenfengru/sweettv-recommender-exam/submissions/candidate_personal_threshold_050_20261030_v5.csv`
- SHA-256: `593b1134b6625771abfe107e17d074499cedf6efb4ef9306e06289e9566876e5`
- Internal and separate CLI validators: **valid**; original header and all 1,260 template users in exact order; five distinct available nonzero IDs per row; 6,649 eligible IDs; 229 distinct IDs recommended.
- Versus submitted v3: 1,112 changed ordered lists; 3,086 / 6,300 changed rank slots; 829 users with changed membership and 283 order-only changes; 148 unchanged lists. Set overlap is 5,224 / 6,300 (82.9206%); 1,076 new membership slots.

## Provenance and checks

All 45 tests passed, including three focused regressions for exact threshold boundaries, canonical duplicate/interval behavior, full-duration denominators and cutoff clipping, plus changed personal predictions with fixed truth/global keys/fallback/slices. Existing interaction, matching, MAP and submission tests were reused. No unrelated model experiments were rerun.

Frozen protocol SHA-256: `b104ef9b0d493a44b613de2081f7d09ea4af5e9e6e847c85be51bdc0cdf3f3b7`. Source hashes, input hashes, base commit, dependency versions, timings and process RSS are recorded in the JSON evidence. Split evaluation and selection took 17.801 seconds; combined refit/validation took 11.407 seconds. Peak process RSS at final artifact recording: 1,204,699,136 bytes (process-lifetime high-water mark).

Execution (single-thread numeric libraries):

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 /private/tmp/sweettv-model-venv/bin/python -m src.experiment_personal_threshold --data-dir /Users/chenfengru/LLM4Rec-Course-codex/data/sweettv/raw --output-dir results/personal_threshold_20261030_v5 --private-dir artifacts/personal_threshold_20261030_v5
/private/tmp/sweettv-model-venv/bin/python -m unittest discover -s tests
```

The previous CSVs and their recorded hashes are preserved. Best submitted v3 SHA-256: `39aac2794395209b2299ccee2e2bb1b4b9afde22f3e06ccb5b04f3d706c9522f`. Its Private 0.39697 / Public 0.40288 scores are user-reported from screenshots; no submission ID or submission timestamp is known or invented. See `baseline_score_evidence.json` for all previous artifact hashes. The new file has no Kaggle score.

No Kaggle workflow, upload or submission API was used. Stop for user review and manual upload. Native session records were left unmodified; original session exports are not committed. Student verification remains pending until personally performed.
