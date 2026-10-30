# Controlled v5 + v7 weighted reciprocal-rank fusion (executed)

**Retain submitted v5. All three frozen weights lower MAP@5 on both splits. No weight qualifies; no combined-window refit or final prediction CSV was generated. None is recommended for manual submission.**

## Definition and reconciliation

For each source, use direct top-50 distinct available items before fallback. V5 ranks by N50 personal airing count, then original >=0.80 global distinct viewers, qualified user-airings, and raw string programme ID. V7 uses its saved all-supported direct ranking, including seen and unseen programmes; its top50/shrink20/min-co-view3 model was neither refit on these splits nor retuned. Cache checksums were verified against v7 provenance. No audit or prior experiment was repeated.

Fusion is `1/(60+rank_v5) + w/(60+rank_item_item)` for exactly w=0.05,0.10,0.20. Ranks start at one; absent ranks contribute zero. Duplicate items are removed before source truncation. Scores are exact rational numbers, so mathematical ties use the unchanged global viewer count, global airing count and ascending raw string ID. Shared v5 popularity fills only insufficient fused lists; no fallback items enter either source list.

Main remains 4,625 users / 6,384 candidates, fit [2020-03-09,2020-05-18), validate [2020-05-18,2020-07-27). Auxiliary remains 4,589 / 5,742, fit [2020-03-09,2020-06-01), validate [2020-06-01,2020-07-27). Original >=0.80 validation truth and history slices, candidate availability, repeat eligibility and global fallback are unchanged. Both frozen anchor hashes match v7, and completed v5 top-five predictions exactly reconcile to the saved v5 references.

## Local results and conditional uncertainty

| Split | Weight | MAP@5 | Difference from v5 | Paired bootstrap 95% interval | Improved / worsened / unchanged AP users |
| --- | ---: | ---: | ---: | --- | --- |
| main | v5 | 0.334711171171 | reference | reference | reference |
| main | 0.05 | 0.331631231231 | -0.003079939940 | [-0.004525794, -0.001641587] | 442 / 520 / 3663 |
| main | 0.1 | 0.327558138138 | -0.007153033033 | [-0.009456541, -0.004846321] | 799 / 822 / 3004 |
| main | 0.2 | 0.322913993994 | -0.011797177177 | [-0.014829677, -0.008779140] | 1102 / 1182 / 2341 |
| auxiliary | v5 | 0.331395910511 | reference | reference | reference |
| auxiliary | 0.05 | 0.327938790828 | -0.003457119682 | [-0.004926896, -0.002076218] | 480 / 531 / 3578 |
| auxiliary | 0.1 | 0.322938609235 | -0.008457301276 | [-0.010758688, -0.006254920] | 788 / 843 / 2958 |
| auxiliary | 0.2 | 0.316684583908 | -0.014711326602 | [-0.017832598, -0.011547169] | 1057 / 1190 / 2342 |

Each interval uses 2,000 paired-user resamples with seed 42; the same resampled users are used for all three weights within a split. Intervals are **conditional on the reused cohorts and exclude configuration-selection uncertainty**. The temporal windows and users overlap, so the two splits are not independent untouched tests. All six intervals are below zero. This supports the bounded decision to retain v5, not a claim that every future integration method must fail.

Eligibility requires a strictly positive within-split gain on both splits. Among eligible weights, maximize the minimum absolute MAP gain across main and auxiliary, breaking ties toward smaller weight. No eligible weight exists; the max-min rule therefore selects no candidate. No configuration was added after inspecting results.

## Ordered lists, positions and membership

| Split | Weight | Changed lists | Changed rank slots | Membership-change users | Order-only users | Common top-five items / slots | New membership slots |
| --- | ---: | ---: | ---: | ---: | ---: | --- | ---: |
| main | 0.05 | 1983 | 4777 | 1023 | 960 | 22029 / 23125 (95.2605%) | 1096 |
| main | 0.1 | 3126 | 8127 | 1855 | 1271 | 20967 / 23125 (90.6681%) | 2158 |
| main | 0.2 | 3864 | 11588 | 2626 | 1238 | 19830 / 23125 (85.7514%) | 3295 |
| auxiliary | 0.05 | 2062 | 5145 | 1087 | 975 | 21791 / 22945 (94.9706%) | 1154 |
| auxiliary | 0.1 | 3206 | 8477 | 1951 | 1255 | 20652 / 22945 (90.0065%) | 2293 |
| auxiliary | 0.2 | 3894 | 11701 | 2731 | 1163 | 19417 / 22945 (84.6241%) | 3528 |

## Seen and unseen effects

Seen means a programme in that user’s pre-cutoff N50 history; all recommended programmes are available. Unseen means absent from that history. Baseline unseen recommendations supplied by fallback remain classified as unseen. An entering item is in fused top five but not baseline top five; leaving is the reverse. Counts are user-item recommendation occurrences, not globally unique programme IDs. Relevant hits use the same >=0.80 target set.

| Split | Weight | Users with entering unseen | Entering unseen recommendations / relevant hits | Leaving unseen recommendations / relevant hits | Total unseen slots baseline -> fused | Unseen relevant hits baseline -> fused |
| --- | ---: | ---: | --- | --- | --- | --- |
| main | 0.05 | 65 | 102 / 12 | 102 / 10 | 718 -> 718 | 107 -> 109 |
| main | 0.1 | 65 | 102 / 12 | 102 / 10 | 718 -> 718 | 107 -> 109 |
| main | 0.2 | 65 | 102 / 12 | 102 / 10 | 718 -> 718 | 107 -> 109 |
| auxiliary | 0.05 | 52 | 88 / 5 | 88 / 11 | 598 -> 598 | 94 -> 88 |
| auxiliary | 0.1 | 52 | 88 / 5 | 88 / 11 | 598 -> 598 | 94 -> 88 |
| auxiliary | 0.2 | 52 | 88 / 5 | 88 / 11 | 598 -> 598 | 94 -> 88 |

| Split | Weight | Entering seen recommendations / relevant hits | Leaving seen recommendations / relevant hits | Net seen hits | Net unseen hits | Seen AP contribution difference | Unseen AP contribution difference |
| --- | ---: | --- | --- | ---: | ---: | ---: | ---: |
| main | 0.05 | 994 / 153 | 994 / 194 | -41 | +2 | -0.003105465 | +0.000025526 |
| main | 0.1 | 2056 / 326 | 2056 / 496 | -170 | +2 | -0.007178559 | +0.000025526 |
| main | 0.2 | 3193 / 541 | 3193 / 773 | -232 | +2 | -0.011822703 | +0.000025526 |
| auxiliary | 0.05 | 1066 / 177 | 1066 / 219 | -42 | -6 | -0.003201617 | -0.000255502 |
| auxiliary | 0.1 | 2205 / 336 | 2205 / 531 | -195 | -6 | -0.008201799 | -0.000255502 |
| auxiliary | 0.2 | 3440 / 549 | 3440 / 844 | -295 | -6 | -0.014455824 | -0.000255502 |

Seen/unseen AP contributions assign each relevant-hit precision term to the hit item’s type, dividing by the original AP denominator; precision still includes all earlier hits. The two contribution means add to MAP, and their differences add to the reported MAP difference. They reflect positions and preceding hits as well as membership and are descriptive attribution, not independent or causal component scores.

At w=0.05, main gains 12 entering unseen relevant hits but loses 10 unseen hits, a net +2. Seen hits decline by 41. Auxiliary gains 5 unseen hits but loses 11 (net -6), while seen hits decline by 42. Larger weights increase seen-hit losses to 170/232 main and 195/295 auxiliary without increasing unseen hits. New hits therefore do not offset displaced personal-history hits; the MAP decline also includes reordering of retained hits.

## Why the larger v7 candidate coverage does not transfer here

For these weights an item missing from v5’s direct top50 has maximum RRF score `0.20/61 = 0.00327869`. Any retained v5 item has personal contribution at least `1/110 = 0.00909091`, before any collaborative bonus. Thus every retained personal item outranks every collaborative-only item. In particular, users with at least five available personal items cannot receive an unseen top-five item through this rule. The weights mainly rerank known programmes; unseen replacements occur in short-history/fallback cases and are identical across the three weights. A focused regression verifies this fixed-weight barrier.

This explains why v7’s useful unseen candidate retrieval is not evidence for improved ranking under this specific RRF. It does not justify trying unregistered weights in this round. If integration is revisited later, it should be a separately controlled design that can admit useful unseen items while protecting the strong personal ranking; no such change was implemented here.

## Existing history-size slices

Slice membership remains based on original >=0.80 distinct training programmes before availability filtering. The JSON evidence includes slice user outcomes, position/membership changes, full seen/unseen attribution and fallback usage in addition to the table below.

| Split | History size | Users | Weight | v5 MAP@5 | Fused MAP@5 | Difference | Net seen / unseen relevant hits |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| main | 0 | 108 | 0.05 | 0.162896091 | 0.162276235 | -0.000619856 | +0 / +2 |
| main | 0 | 108 | 0.1 | 0.162896091 | 0.162276235 | -0.000619856 | +0 / +2 |
| main | 0 | 108 | 0.2 | 0.162896091 | 0.162276235 | -0.000619856 | +0 / +2 |
| main | 1–5 | 462 | 0.05 | 0.193964646 | 0.190141895 | -0.003822751 | +1 / +0 |
| main | 1–5 | 462 | 0.1 | 0.193964646 | 0.185107023 | -0.008857624 | -2 / +0 |
| main | 1–5 | 462 | 0.2 | 0.193964646 | 0.179448052 | -0.014516595 | -4 / +0 |
| main | 6–20 | 2087 | 0.05 | 0.307892110 | 0.305125646 | -0.002766464 | -23 / +0 |
| main | 6–20 | 2087 | 0.1 | 0.307892110 | 0.302584917 | -0.005307193 | -55 / +0 |
| main | 6–20 | 2087 | 0.2 | 0.307892110 | 0.298353697 | -0.009538412 | -66 / +0 |
| main | 21+ | 1968 | 0.05 | 0.405621895 | 0.402248899 | -0.003372996 | -19 / +0 |
| main | 21+ | 1968 | 0.1 | 0.405621895 | 0.396553043 | -0.009068852 | -113 / +0 |
| main | 21+ | 1968 | 0.2 | 0.405621895 | 0.391454381 | -0.014167514 | -162 / +0 |
| auxiliary | 0 | 87 | 0.05 | 0.170593870 | 0.156283525 | -0.014310345 | +0 / -7 |
| auxiliary | 0 | 87 | 0.1 | 0.170593870 | 0.156283525 | -0.014310345 | +0 / -7 |
| auxiliary | 0 | 87 | 0.2 | 0.170593870 | 0.156283525 | -0.014310345 | +0 / -7 |
| auxiliary | 1–5 | 401 | 0.05 | 0.197744528 | 0.195414935 | -0.002329593 | +1 / +1 |
| auxiliary | 1–5 | 401 | 0.1 | 0.197744528 | 0.190834026 | -0.006910502 | -1 / +1 |
| auxiliary | 1–5 | 401 | 0.2 | 0.197744528 | 0.182032419 | -0.015712109 | +0 / +1 |
| auxiliary | 6–20 | 1874 | 0.05 | 0.300831406 | 0.298584430 | -0.002246976 | -10 / +0 |
| auxiliary | 6–20 | 1874 | 0.1 | 0.300831406 | 0.295888622 | -0.004942784 | -51 / +0 |
| auxiliary | 6–20 | 1874 | 0.2 | 0.300831406 | 0.290643010 | -0.010188397 | -73 / +0 |
| auxiliary | 21+ | 2227 | 0.05 | 0.387463204 | 0.383208726 | -0.004254478 | -33 / +0 |
| auxiliary | 21+ | 2227 | 0.1 | 0.387463204 | 0.375998603 | -0.011464601 | -143 / +0 |
| auxiliary | 21+ | 2227 | 0.2 | 0.387463204 | 0.369110413 | -0.018352791 | -222 / +0 |

## Reproducibility, checks and preservation

All 58 tests pass. New focused tests cover exact fusion arithmetic, zero contribution for missing ranks, duplicate suppression and top50 truncation, a hand-constructed mathematical tie resolved by global viewer/airing keys and raw ID, empty-source fallback, seen/unseen hit/AP attribution, and the fixed-weight unseen-item barrier. No new timestamp feature was introduced: the established canonical-count and item-item cutoff invariance/leakage tests are reused. Checksummed v7 caches, frozen anchors and unchanged truth files constrain the fusion inputs.

Frozen protocol SHA-256: `f1b3682ea9a23e0666c1e98cd0a077718719076aa90dac9499196836d4451dd2`. Split comparisons, bootstrap and selection took 17.458 seconds. Peak process RSS at selection: 778,534,912 bytes (process-lifetime high-water, including cached interactions and rankings). Per-weight/split timings, input/source hashes, dependency versions, base commit and environment are in comparison.json and selection.json. No split item-item model was refit.

No new submission description, path, checksum or validator result is claimed because no new prediction artifact was generated. The implemented conditional final-fit path was not executed. All previous CSVs remain byte-identical. Best submitted v5 remains `submissions/candidate_personal_threshold_050_20261030_v5.csv`, SHA-256 `593b1134b6625771abfe107e17d074499cedf6efb4ef9306e06289e9566876e5`; user-reported Private 0.40210 / Public 0.41789. No submission ID or timestamp is known or invented.

Native session records remain unmodified, and student verification remains pending. No Kaggle workflow, submission command, upload or submission API was used. Stop for user review.

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 /private/tmp/sweettv-model-venv/bin/python -m src.experiment_item_fusion --data-dir /Users/chenfengru/LLM4Rec-Course-codex/data/sweettv/raw
/private/tmp/sweettv-model-venv/bin/python -m unittest discover -s tests
/private/tmp/sweettv-model-venv/bin/python -m src.report_item_fusion
```
