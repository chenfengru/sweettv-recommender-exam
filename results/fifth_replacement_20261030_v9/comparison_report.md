# Controlled fifth-position unseen replacement (executed)

**E2 qualifies and is selected for manual review.** E1 and E2 improve both fixed splits; E3 has mixed signs. E2 maximizes the smaller absolute MAP improvement across the splits. Recommend one manual benchmark submission as a locally supported, small change; submitted v5 remains the incumbent until a new user-reported result is obtained.

## Frozen rules and inputs

- E1: original fifth programme has exactly one pre-cutoff >=0.50 qualified personal airing (N50=1).
- E2: both original fourth and fifth programmes have N50=1.
- E3: fewer than five distinct available positive-N50 programmes and original fifth position supplied by global-popularity fallback.

Each rule starts from the exact completed v5 list, preserves positions one through four, and inspects only v7’s unseen-only direct top50 before fallback. Choose the first available nonzero programme with N50=0 that is absent from the entire original top five. At most one replacement is made; otherwise preserve all five. Source ordering is unchanged and deterministic. Fallback provenance is established by reproducing the exact v5 direct ordering and completion; a fifth fallback programme is outside available positive-N50 history.

V7 N50 counts and unseen rankings were reused with verified hashes. No split item-item model was refit or retuned, no RRF weight sweep was repeated or extended, and no new rule/threshold was added after inspecting results. Existing canonical deduplication, interval unions, full original airing denominators, causal clipping/cleaning and availability filtering remain unchanged.

Main: 4,625 users / 6,384 candidates; fit [2020-03-09,2020-05-18), validate [2020-05-18,2020-07-27). Auxiliary: 4,589 / 5,742; fit [2020-03-09,2020-06-01), validate [2020-06-01,2020-07-27). Original >=0.80 truth, original >=0.80 history-slice membership, global tie statistics/fallback and candidates are unchanged. Frozen anchor hashes match v7 and recomputed v5 predictions match saved references exactly.

## MAP@5 and paired uncertainty

| Split | Rule | MAP@5 | Difference from v5 | Paired bootstrap 95% interval |
| --- | --- | ---: | ---: | --- |
| main | v5 | 0.334711171171 | reference | reference |
| main | E1 | 0.335201261261 | +0.000490090090 | [-0.000032523, +0.001011928] |
| main | E2 | 0.335652432432 | +0.000941261261 | [+0.000541135, +0.001368667] |
| main | E3 | 0.334755855856 | +0.000044684685 | [-0.000151351, +0.000229946] |
| auxiliary | v5 | 0.331395910511 | reference | reference |
| auxiliary | E1 | 0.332008970727 | +0.000613060216 | [+0.000102310, +0.001132454] |
| auxiliary | E2 | 0.332178216024 | +0.000782305513 | [+0.000401649, +0.001178271] |
| auxiliary | E3 | 0.331273153192 | -0.000122757318 | [-0.000320349, +0.000040677] |

Bootstrap: 2,000 paired-user resamples, seed42, shared user draws across the three rules within each split. Intervals are **conditional on the reused cohorts, exclude configuration-selection uncertainty, and are not independent evidence across splits**. Windows and users overlap. E2’s intervals are above zero on both splits, but repeated hold-out use and selecting the best of three add uncertainty beyond these intervals. These small local gains do not guarantee Kaggle improvement.

## Eligibility and execution

“Available candidate, whole cohort” counts every user having an acceptable candidate within the fixed unseen top50, regardless of rule eligibility. “Eligible with candidate” intersects that count with rule eligibility and equals actual replacements. A user may therefore have a candidate but remain ineligible. This avoids treating lack of eligibility as lack of retrieval support.

| Split | Rule | Eligible users | Available candidate, whole cohort | Eligible with candidate | Actual replacements |
| --- | --- | ---: | ---: | ---: | ---: |
| main | E1 | 962 | 4551 | 962 | 962 |
| main | E2 | 705 | 4551 | 705 | 705 |
| main | E3 | 227 | 4551 | 153 | 153 |
| auxiliary | E1 | 873 | 4529 | 873 | 873 |
| auxiliary | E2 | 635 | 4529 | 635 | 635 |
| auxiliary | E3 | 187 | 4529 | 127 | 127 |

## Relevant-hit changes

Inserted/removed relevant counts include both-relevant cases. Both-relevant and neither-relevant are disjoint replacement outcomes; insert-only and remove-only counts are also reported. A hit is a per-user recommendation occurrence, not a globally unique programme. Because only position five changes, both/neither cases leave AP unchanged; insert-only improves AP and remove-only worsens it.

| Split | Rule | Inserted relevant | Removed relevant | Both relevant | Neither relevant | Insert-only / remove-only | Net relevant hits |
| --- | --- | ---: | ---: | ---: | ---: | --- | ---: |
| main | E1 | 119 | 91 | 14 | 766 | 105 / 77 | +28 |
| main | E2 | 92 | 37 | 8 | 584 | 84 / 29 | +55 |
| main | E3 | 20 | 14 | 4 | 123 | 16 / 10 | +6 |
| auxiliary | E1 | 100 | 72 | 13 | 714 | 87 / 59 | +28 |
| auxiliary | E2 | 71 | 28 | 6 | 542 | 65 / 22 | +43 |
| auxiliary | E3 | 11 | 12 | 3 | 107 | 8 / 9 | -1 |

E2 inserts 92 relevant items and removes 37 on main (net+55), and inserts 71/removes 28 auxiliary (net+43). These are measured top-five hit and MAP improvements, rather than an inference from candidate coverage. E1 changes more users but yields smaller gains. E3’s auxiliary loss disqualifies it.

## AP outcomes, whole cohort and replaced users

| Split | Rule | Whole cohort improved / worsened / unchanged | Replaced users | Replaced improved / worsened / unchanged |
| --- | --- | --- | ---: | --- |
| main | E1 | 105 / 77 / 4443 | 962 | 105 / 77 / 780 |
| main | E2 | 84 / 29 / 4512 | 705 | 84 / 29 / 592 |
| main | E3 | 16 / 10 / 4599 | 153 | 16 / 10 / 127 |
| auxiliary | E1 | 87 / 59 / 4443 | 873 | 87 / 59 / 727 |
| auxiliary | E2 | 65 / 22 / 4502 | 635 | 65 / 22 / 548 |
| auxiliary | E3 | 8 / 9 / 4572 | 127 | 8 / 9 / 110 |

## Existing personal-history slices

Slice membership uses original >=0.80 distinct training programmes before availability filtering, not N50 profile size. Full slice eligibility, AP outcomes, hit categories, invariants and list changes are retained in comparison.json.

| Split | History size | Users | Rule | v5 MAP@5 | Rule MAP@5 | Difference | Eligible / replaced | Net relevant hits |
| --- | --- | ---: | --- | ---: | ---: | ---: | --- | ---: |
| main | 0 | 108 | E1 | 0.162896091 | 0.162896091 | +0.000000000 | 3 / 3 | +0 |
| main | 0 | 108 | E2 | 0.162896091 | 0.162896091 | +0.000000000 | 3 / 3 | +0 |
| main | 0 | 108 | E3 | 0.162896091 | 0.165087449 | +0.002191358 | 105 / 31 | +2 |
| main | 1–5 | 462 | E1 | 0.193964646 | 0.197348485 | +0.003383838 | 323 / 323 | +22 |
| main | 1–5 | 462 | E2 | 0.193964646 | 0.197867965 | +0.003903319 | 290 / 290 | +24 |
| main | 1–5 | 462 | E3 | 0.193964646 | 0.193899711 | -0.000064935 | 122 / 122 | +4 |
| main | 6–20 | 2087 | E1 | 0.307892110 | 0.308305782 | +0.000413672 | 604 / 604 | +8 |
| main | 6–20 | 2087 | E2 | 0.307892110 | 0.309094793 | +0.001202683 | 397 / 397 | +29 |
| main | 6–20 | 2087 | E3 | 0.307892110 | 0.307892110 | +0.000000000 | 0 / 0 | +0 |
| main | 21+ | 1968 | E1 | 0.405621895 | 0.405540594 | -0.000081301 | 32 / 32 | -2 |
| main | 21+ | 1968 | E2 | 0.405621895 | 0.405642220 | +0.000020325 | 15 / 15 | +2 |
| main | 21+ | 1968 | E3 | 0.405621895 | 0.405621895 | +0.000000000 | 0 / 0 | +0 |
| auxiliary | 0 | 87 | E1 | 0.170593870 | 0.171360153 | +0.000766284 | 2 / 2 | +1 |
| auxiliary | 0 | 87 | E2 | 0.170593870 | 0.171360153 | +0.000766284 | 2 / 2 | +1 |
| auxiliary | 0 | 87 | E3 | 0.170593870 | 0.166915709 | -0.003678161 | 85 / 25 | -3 |
| auxiliary | 1–5 | 401 | E1 | 0.197744528 | 0.199814353 | +0.002069825 | 290 / 290 | +13 |
| auxiliary | 1–5 | 401 | E2 | 0.197744528 | 0.200412857 | +0.002668329 | 260 / 260 | +15 |
| auxiliary | 1–5 | 401 | E3 | 0.197744528 | 0.197137711 | -0.000606816 | 102 / 102 | +2 |
| auxiliary | 6–20 | 1874 | E1 | 0.300831406 | 0.301811485 | +0.000980078 | 553 / 553 | +14 |
| auxiliary | 6–20 | 1874 | E2 | 0.300831406 | 0.302055170 | +0.001223764 | 361 / 361 | +26 |
| auxiliary | 6–20 | 1874 | E3 | 0.300831406 | 0.300831406 | +0.000000000 | 0 / 0 | +0 |
| auxiliary | 21+ | 2227 | E1 | 0.387463204 | 0.387499127 | +0.000035923 | 28 / 28 | +0 |
| auxiliary | 21+ | 2227 | E2 | 0.387463204 | 0.387535050 | +0.000071846 | 12 / 12 | +1 |
| auxiliary | 21+ | 2227 | E3 | 0.387463204 | 0.387463204 | +0.000000000 | 0 / 0 | +0 |

## Selection and final-window candidate

Selection was frozen before evaluation: qualify only with strictly positive MAP gain on both splits; maximize the minimum absolute gain, then prefer fewer main replacements and finally rule order E1,E2,E3. E1’s smaller gain is +0.000490090090; E2’s is +0.000782305513. E2 wins without invoking tie-breaks. No extra variant was added.

The selected inputs were recomputed on the single combined [2020-03-09,2020-07-27) fitting window using canonical user-airing unions and full denominators. Independently qualified split counts were not added. Fixed v7 item-item configuration was fit once on combined N50 binary interactions; original combined >=0.80 global keys/fallback were retained. Predictions cover [2020-07-27,2020-10-19), with carryovers from the prior schedule. Reconstructed final v5 exactly matches the submitted CSV before applying E2.

- Filename: `candidate_personal_fifth_e2_20261030_v9.csv`.
- Absolute path: `/Users/chenfengru/sweettv-recommender-exam/submissions/candidate_personal_fifth_e2_20261030_v9.csv`.
- SHA-256: `f1378b0d6fed62793e14ebb4c1b64cf8b2163485485c15c861aae7e67e556375`.
- Both internal and independent CLI validators: **valid** for all 1,260 template users in exact original order/header, five distinct available nonzero programme IDs per row, and the 6,649-ID final candidate pool.
- Compared with exact submitted v5: **58** changed lists and rank-position slots; all changes are position five. Positions1–4 are identical for every user; 1202 lists remain identical. Set overlap is 6242/6300 (99.0794%).
- Every actual replacement is unseen (N50=0), available, distinct and absent from the entire original v5 top five. Selection and insertion satisfy E2; runtime assertions and CSV comparison checks verify this.

The final fit produces only 58 replacements, versus 705/635 in validation. Eligibility depends on each window’s count distribution and template population; this smaller affected population limits how directly the local effect transfers. Retain v5 as the best confirmed submitted model until manual benchmarking provides evidence.

Accurate English description for manual submission:

> V5 N50 personal-frequency baseline with E2 fifth-position replacement. Preserve the original first four recommendations. Replace the fifth only when both original fourth and fifth programmes have exactly one >=50%-qualified training airing. Insert the highest-ranked available programme from fixed v7 unseen-only direct top50, excluding the entire original top five. Fit on weeks11–30 with canonical interval unions; predict weeks31–42 including schedule carryovers. Item-item model: binary N50, shrunk cosine c/(c+20), minimum co-view3, top50 neighbours and log1p profile weights. Original >=80% global popularity ties/fallback retained. Validated for manual review; no Kaggle score exists for this candidate.

## Verification and provenance

All 62 tests pass. New checks cover exact E1/E2 eligibility, E3 available-history and fallback requirements, exclusion of the entire original top five, deterministic first acceptable candidate, unavailable/seen candidates, no candidate and no search beyond top50, and exact first-four preservation. Existing causal cutoff, canonical interval, item-item and submission regressions were reused. No new timestamp feature was introduced.

For every rule/split, runtime checks assert identical first four positions, at most one membership change, and unseen/available/distinct/new fifth items for actual replacements. Actual replacements equal changed lists and changed rank-position slots. Truth/anchor hashes remain unchanged. Previous submitted CSVs remain byte-identical; private user-level predictions stay ignored.

Frozen protocol SHA-256: `f3c8de17cfeab44b663c7e4cfdada4240e7e8fe05e44c32f06b989973d189ac9`. Comparison/bootstrap/selection elapsed 10.997 seconds. Final combined fitting/generation/validation elapsed 14.952 seconds.

Source/input hashes, base commit, environment, dependency versions, cache manifests, process-lifetime peak RSS and timings appear in the JSON evidence. The recorded time is an experiment time, not a submission timestamp.

Submitted v5 SHA-256 remains `593b1134b6625771abfe107e17d074499cedf6efb4ef9306e06289e9566876e5`. Its Private0.40210/Public0.41789 scores are user-reported screenshot values; submission ID and time are unknown and not invented. The new candidate has not been uploaded and has no Kaggle score.

No Kaggle workflow, upload, submission command or API was used. Native session records remain unmodified; student verification is pending until personally performed. Stop for user review and manual upload.

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 /private/tmp/sweettv-model-venv/bin/python -m src.experiment_fifth_replacement --data-dir /Users/chenfengru/LLM4Rec-Course-codex/data/sweettv/raw
/private/tmp/sweettv-model-venv/bin/python -m unittest discover -s tests
/private/tmp/sweettv-model-venv/bin/python -m src.report_fifth_replacement
```
