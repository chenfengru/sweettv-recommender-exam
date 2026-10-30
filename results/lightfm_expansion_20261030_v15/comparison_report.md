# V15: fixed LightFM unseen-top-50 candidate expansion

The retrained model fails the frozen qualification rule. Retain submitted v14. No final expansion, prediction CSV or submission description was generated. No Kaggle workflow or upload was opened. Student verification remains pending.

V14 screenshot-reported scores supplied by the user: Private **0.43416**, Public **0.44157**. Submission ID and timestamp are unknown. Its original CSV and SHA-256 `108b159c4e2c687b45f4c4d3e6e9519bace4abc73d5ba888f927a0efbb30ce90` remain unchanged.

## Controlled design

[Pre-evaluation protocol](../../docs/lightfm_expansion_protocol.md) and [frozen hashes/settings](frozen_experiment.json). Restore saved origin-specific LightFM models for inference only; zero LightFM fits. Filter the full available supported ranking to N50-unseen, take 50, then union/deduplicate with every v14 candidate. Never scan beyond 50 to force additional unique rows. Unsupported users receive no expansion. Preserve original source-flag meanings and all ordered 40 features. Fit one new 300-tree classifier on the same two historical origins, retaining all negatives and all-negative queries. Main/auxiliary labels never enter fitting. The saved v14 classifier on expanded rows is diagnostic only and cannot qualify.

## Ranking quality

| Method | Main MAP@5 | Auxiliary MAP@5 |
|---|---:|---:|
| Saved v14 | 0.363412552553 | 0.351762790247 |
| Retrained expanded model | 0.361554414414 | 0.351893174499 |
| Frozen v14 + expanded rows (diagnostic) | 0.363333093093 | 0.351352388562 |

Paired user bootstrap: 2,000 resamples, seed 42, percentile 95% intervals. These condition on the reused cohorts and exclude configuration-selection uncertainty. The splits overlap and are not independent replication. Repeated earlier model selection also limits generalization claims.

| Split / method | Delta vs v14 | 95% interval | Improved / worsened / unchanged | Hit gains / losses | Changed lists / positions / memberships |
|---|---:|---|---|---|---|
| main retrained | -0.001858138138 | [-0.003089393393, -0.000592740240] | 455 / 546 / 3624 | 180 / 201 | 2453 / 5043 / 1127 |
| main diagnostic | -0.000079459459 | [-0.000185409910, +0.000006495495] | 3 / 8 / 4614 | 3 / 6 | 47 / 105 / 47 |
| auxiliary retrained | +0.000130384252 | [-0.001173521828, +0.001420802462] | 486 / 465 / 3638 | 214 / 175 | 2418 / 4964 / 1122 |
| auxiliary diagnostic | -0.000410401685 | [-0.000823727028, -0.000082425365] | 1 / 9 / 4579 | 1 / 3 | 88 / 202 / 88 |

## Main diagnostics

Candidates: 380,403 → 440,402; 59,999 actual additions for 4,551 users. Unsupported users: 74. Addition-count distribution: `{"users": 4625, "sum": 59999, "min": 0, "mean": 12.972756756756757, "median": 11.0, "p90": 23.0, "p95": 29.0, "max": 50, "zero_users": 74}`.

LightFM selected 227,550 user-item pairs; 167,551 already belonged to v14. Overlaps with original personal200 / item-item unseen50 / global5 sources: 0 / 167551 / 6877. Source overlaps may overlap each other; they are pair counts, not unique programme counts.

Target denominator: 4625 users, 21466 relevant user-item pairs. Covered pairs 15999 → 16410; micro recall 0.745318178 → 0.764464735; macro recall 0.728601802 → 0.748072072; oracle MAP@5 0.728601802 → 0.748072072.

Newly retrieved relevant pairs: 411. Retrained model selects 16 new-only items across 14 users, with **0 relevant hits**. Diagnostic new-only selections/hits: 69 / 3.

Seen relevant hits 8948 → 8923; unseen hits 365 → 369. Seen AP contribution delta -0.001882822823; unseen contribution delta +0.000024684685. AP contributions attribute each relevant rank's precision to its seen/unseen category, using the unchanged AP denominator. The legacy JSON `fused_` prefix denotes the current model; no fusion occurred.

Top-five set overlap: 0.949578378. Fallback completion: zero users/slots for both models; candidate unions already contain global5. Global-source rows can still be selected by the classifier, which is distinct from fallback completion.

| Fixed H80 slice | Users | v14 MAP | New MAP | Delta | Improved / worsened / unchanged | Hit gains / losses | Changed lists / positions / memberships |
|---|---:|---:|---:|---:|---|---|---|
| 0 | 108 | 0.178433642 | 0.170892490 | -0.007541152 | 7 / 21 / 80 | 0 / 0 | 92 / 198 / 22 |
| 1–5 | 462 | 0.215341510 | 0.216887326 | +0.001545815 | 35 / 34 / 393 | 9 / 7 | 267 / 560 / 142 |
| 6–20 | 2087 | 0.335706091 | 0.333752995 | -0.001953096 | 180 / 212 / 1695 | 75 / 79 | 1034 / 2126 / 474 |
| 21+ | 1968 | 0.437706216 | 0.435461551 | -0.002244665 | 233 / 279 / 1456 | 96 / 115 | 1060 / 2159 / 489 |

H80 slices retain original >=80% history membership before availability filtering. Full slice-specific seen/unseen attribution and diagnostic outcomes remain in comparison.json.

| Cold group | Users | v14 / new / diagnostic MAP | Improved / worsened / unchanged |
|---|---:|---|---|
| no_n50_training_history | 74 | 0.178265766 / 0.166929429 / 0.178265766 | 4 / 18 / 52 |
| no_available_n50_history | 76 | 0.184100877 / 0.172185673 / 0.184100877 | 4 / 19 / 53 |

Origin preparation: 13.169s; expanded float32 feature matrix 70,464,320 bytes; process-lifetime peak RSS 914,489,344 bytes. Feature distributions/support/missingness are in [main/candidate_features.json](main/candidate_features.json).

## Auxiliary diagnostics

Candidates: 397,757 → 460,766; 63,009 actual additions for 4,529 users. Unsupported users: 60. Addition-count distribution: `{"users": 4589, "sum": 63009, "min": 0, "mean": 13.730442362170407, "median": 12.0, "p90": 23.0, "p95": 28.0, "max": 49, "zero_users": 60}`.

LightFM selected 226,450 user-item pairs; 163,441 already belonged to v14. Overlaps with original personal200 / item-item unseen50 / global5 sources: 0 / 163441 / 6698. Source overlaps may overlap each other; they are pair counts, not unique programme counts.

Target denominator: 4589 users, 21080 relevant user-item pairs. Covered pairs 15639 → 16038; micro recall 0.741888046 → 0.760815939; macro recall 0.724358974 → 0.744141788; oracle MAP@5 0.724358974 → 0.744141788.

Newly retrieved relevant pairs: 399. Retrained model selects 22 new-only items across 19 users, with **0 relevant hits**. Diagnostic new-only selections/hits: 124 / 1.

Seen relevant hits 8651 → 8675; unseen hits 293 → 308. Seen AP contribution delta -0.000119549163; unseen contribution delta +0.000249933416. AP contributions attribute each relevant rank's precision to its seen/unseen category, using the unchanged AP denominator. The legacy JSON `fused_` prefix denotes the current model; no fusion occurred.

Top-five set overlap: 0.949618653. Fallback completion: zero users/slots for both models; candidate unions already contain global5. Global-source rows can still be selected by the classifier, which is distinct from fallback completion.

| Fixed H80 slice | Users | v14 MAP | New MAP | Delta | Improved / worsened / unchanged | Hit gains / losses | Changed lists / positions / memberships |
|---|---:|---:|---:|---:|---|---|---|
| 0 | 87 | 0.177279693 | 0.176628352 | -0.000651341 | 4 / 3 / 80 | 4 / 1 | 20 / 57 / 14 |
| 1–5 | 401 | 0.216854392 | 0.215601275 | -0.001253117 | 28 / 28 / 345 | 10 / 8 | 268 / 600 / 130 |
| 6–20 | 1874 | 0.322244160 | 0.322422774 | +0.000178614 | 192 / 171 / 1511 | 70 / 56 | 961 / 1931 / 430 |
| 21+ | 2227 | 0.407710797 | 0.408080252 | +0.000369456 | 262 / 263 / 1702 | 130 / 110 | 1169 / 2376 / 548 |

H80 slices retain original >=80% history membership before availability filtering. Full slice-specific seen/unseen attribution and diagnostic outcomes remain in comparison.json.

| Cold group | Users | v14 / new / diagnostic MAP | Improved / worsened / unchanged |
|---|---:|---|---|
| no_n50_training_history | 60 | 0.175666667 / 0.175666667 / 0.175666667 | 0 / 0 / 60 |
| no_available_n50_history | 63 | 0.183439153 / 0.183439153 / 0.175502646 | 0 / 0 / 63 |

Origin preparation: 14.310s; expanded float32 feature matrix 73,722,560 bytes; process-lifetime peak RSS 1,059,028,992 bytes. Feature distributions/support/missingness are in [auxiliary/candidate_features.json](auxiliary/candidate_features.json).

## Coverage definitions and interpretation

Micro recall is total covered relevant pairs divided by all relevant pairs. Macro recall averages |R∩C|/|R| over users with nonempty truth. Oracle AP@5 assumes every covered target is optimally ranked: min(5,|R∩C|)/min(5,|R|). Truth has at most five targets here, so macro recall equals oracle MAP. Both evaluation cohorts have no empty-target users. Historical reports explicitly exclude empty-truth users from recall denominators but retain every original query/negative row for training. No label-only users were added. Larger coverage does not establish ranking improvement: neither split yields a new-only relevant top-five hit from the retrained model.

## Training, integrity and reproducibility

- origin_20200406: rows 291,619 → 350,617; positives 13020 → 13315; all-negative queries 979 → 950. Original labels exactly equal.
- origin_20200420: rows 313,316 → 368,851; positives 12365 → 12552; all-negative queries 1077 → 1051. Original labels exactly equal.

One classifier fit: 719,468 rows, 25,867 positives, positive fraction 0.035952954; 300 trees, fit time 5.316s, training-process peak RSS 1,036,877,824 bytes. Fixed classifier SHA-256 `dc8c69ed77767ce04032c20bc6abb3d9422e367a79cdbde16db056848cc5ccfb`. Parameters and dependency/runtime evidence: [training.json](training.json).

Every original candidate survives. All original 40 feature values and historical labels are exactly equal after row alignment. New-only rows have N50=0, original source flags zero, finite complete features, support-aware missing indicators and full-universe ranks. Origin mappings and all four LightFM predictive arrays retain their verified hashes; no later-origin model is borrowed. All previous CSVs and source artifacts pass final hash checks. Private histories, per-user rows, model weights and native session exports remain outside Git.

The initial run completed its single classifier fit, then encountered a missing metric import during reporting. After fixing the import, evaluation resumed with `--resume-frozen-classifier`; the saved classifier hash and 300-tree count were verified. No second fit occurred. Runtime records separate original training from resumed preparation/evaluation and must not be summed as one uninterrupted process.

Regression suite: 87 tests pass. Focused checks cover unseen-filter-before-top50, union overlap without tail refill, unsupported users, deduplication, no label injection, exact restored native predictions, complete new-row features and original 40-feature equality. Existing temporal, ranking, schedule and submission checks remain unchanged. A rerun refuses to overwrite an existing classifier; resume uses its verified saved state.

Descriptive feature importance is saved in feature_importance.json; it is not causal evidence. No tuning or second configuration was selected. Independent origin-specific LightFM score/bias scales can shift. Historical training forecasts span 14 days while evaluation windows are longer; reused overlapping cohorts and prior validation-informed development limit claims.

## Decision

Retain v14. Main deteriorates with a conditional interval below zero; auxiliary has a small positive point estimate with an interval spanning zero. The frozen diagnostic declines on both splits and is ineligible regardless. No final features/refit, CSV or validator run was needed because qualification failed. No further variants were evaluated. All uploads remain manual-only.
