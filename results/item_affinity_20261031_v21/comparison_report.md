# V21: controlled other-history item-item affinity features

Question: can unweighted similarity support from other distinct N50-history programmes improve the fixed four-seed channel-affinity ensemble?

Decision: **one extended four-seed candidate qualifies for manual review**. Stage1 passed the required both-split gain versus original seed42. Exactly 4 extended classifiers were fitted; no best-seed/weight selection or additional variants.

Incumbent: original 52-feature channel-affinity models seeds42–45, equal mean; main 0.369630450450/auxiliary 0.359208735866. User-screenshot-reported Kaggle Private 0.44124/Public 0.44911; submission ID/time unknown. Reports, prior predictions/CSV checksums/models/caches and native records are preserved. No Kaggle access/upload or merge. Coursework reports are unchanged.

## Frozen graph and feature definition

[Pre-evaluation protocol](../../docs/item_affinity_protocol.md), [source hashes/settings](frozen_experiment.json). Branch codex/item-item-affinity derives from codex/v18-seed-ensemble at b0fa8f287fd157fdbe9cba45126493f88476aed0. Original historical origins/labels, all candidate rows, evaluation users, first 52 values and training/ranking settings remain frozen. No candidate expansion or evaluation-label fitting.

N50 history uses original canonical user-airings: longest merged observed block >=50% of full airing duration, with original cleaning, causal clipping and unions. Histories begin Mar9 and stop at each origin’s cutoff (Apr6,Apr20,May18,Jun1,finalJul27), before candidate availability filtering. Distinct positive-count programmes are used once, regardless of frequency.

The original graph uses sparse binary user-item interactions. Item support n_i counts users; c_ij counts users with both programmes. Similarity = c_ij/sqrt(n_i*n_j) * c_ij/(c_ij+20). Exclude self-neighbours and c_ij<3; retain the top50 outgoing neighbours per SOURCE history item by descending similarity then ascending raw destination string ID. Pruning occurs before forecast availability. Source-block size128 bounds sparse multiplication. The truncated graph is **directed**, although unpruned cosine is symmetric.

For candidate i, use retained edges **h→i** from distinct history h≠i; never reverse or symmetrize the graph. Collect strictly positive similarities only, with no frequency weights, normalization or decay. Exactly three columns: maximum; sum of the five largest positives; log1p(number of distinct positive contributors). Empty/unsupported retained neighbourhoods produce three zeros. A zero means no retained other-history support, not proof of zero unpruned similarity. Existing sum(log1p(N50_h)*sim(h→i)) scores, ranks and candidate retrieval are preserved.

Verified saved main/auxiliary graphs are reused. Historical/final graphs, where no saved graph exists, are rebuilt only from the corresponding verified pre-cutoff N50 counts with original fixed defaults. Every original weighted item-item score and rank on the reconstructed origin rows is checked against the existing52-feature arrays. No future graph/behaviour is used.

## Stage1: extended seed42 versus original seed42

| Split | Original seed42 MAP | Extended seed42 MAP | Delta | Paired 95% interval | Improved / worsened / unchanged |
|---|---:|---:|---:|---|---|
| main | 0.369249609610 | 0.371257057057 | +0.002007447447 | [+0.000721166667, +0.003370001502] | 581 / 497 / 3547 |
| auxiliary | 0.357738856202 | 0.359161158325 | +0.001422302123 | [+0.000028080434, +0.002798567226] | 550 / 493 / 3546 |

Stage1 qualification uses only strict positive MAP differences against original seed42 on BOTH splits. Context-only comparisons against the submitted four-seed incumbent are saved separately and do not replace this gate.

## Stage2: extended ensemble versus submitted four-seed ensemble

Only after the Stage1 gate passed were seeds43/44/45 fitted, once each, with unchanged effective settings. The sole candidate is the equal mean of all four extended original-convention binary ranking-score vectors, not raw-margin averaging, a best seed or a blend with the incumbent. Scores are not claimed calibrated probabilities.

| Method | Main MAP | Main delta vs incumbent | Auxiliary MAP | Auxiliary delta vs incumbent |
|---|---:|---:|---:|---:|
| stage2_seed42_diagnostic | 0.371257057057 | +0.001626606607 | 0.359161158325 | -0.000047577540 |
| stage2_seed43_diagnostic | 0.370460780781 | +0.000830330330 | 0.359170843321 | -0.000037892545 |
| stage2_seed44_diagnostic | 0.370472612613 | +0.000842162162 | 0.359206919929 | -0.000001815937 |
| stage2_seed45_diagnostic | 0.370083423423 | +0.000452972973 | 0.359780937508 | +0.000572201642 |
| extended_ensemble_vs_incumbent | 0.370537657658 | +0.000907207207 | 0.359880208712 | +0.000671472846 |

Individual models are diagnostic only; none is selected separately. Their JSON records include paired intervals and user outcomes.

| Split, extended equal mean | Incumbent MAP | Extended MAP | Delta | Paired 95% interval | Improved / worsened / unchanged |
|---|---:|---:|---:|---|---|
| main | 0.369630450450 | 0.370537657658 | +0.000907207207 | [-0.000204274775, +0.002024930931] | 432 / 372 / 3821 |
| auxiliary | 0.359208735866 | 0.359880208712 | +0.000671472846 | [-0.000469359095, +0.001812543885] | 386 / 364 / 3839 |

All paired intervals use 2,000 user resamples, seed42, percentile 95%. They condition on reused evaluation cohorts, exclude accumulated selection uncertainty and training variation, and do not establish independent replication because cohorts/windows overlap. The Stage1 gate and later selection add uncertainty beyond these intervals.

## Prediction and seen/unseen diagnostics

Seen means programme N50>0 in full pre-cutoff history, before availability filtering. Unseen means N50=0; it can still have shorter/unqualified viewing. Relevant means inclusion in the unchanged top-five >=80%-qualified held-out target set. A relevant hit is a user-item occurrence in the recommended five. Seen/unseen AP contributions assign each relevant rank’s precision term to that category using the unchanged AP denominator; precision includes preceding hits of either kind. Contributions sum to MAP, and are descriptive rather than causal. Legacy JSON `fused_` means current predictions, not a blend.

### main: stage1_vs_seed42

Changed ordered lists 2637; changed rank-position slots 5400; membership-change users 1199; order-only changes 1438; top-five set overlap 0.946810811. Relevant-hit gains/losses 208 / 175 (net +33).

Seen relevant hits 9048 → 9062; unseen hits 408 → 427. Seen AP contribution delta +0.001139159159; unseen delta +0.000868288288. No causal explanation is inferred from these changes.

Unchanged candidate coverage: 15999/21466 relevant pairs; micro 0.745318178; macro/oracle MAP 0.728601802/0.728601802. Fixed history slices and category-specific outcomes appear in the per-split JSON. Fallback completion remains zero because original candidate unions contain global5.

### main: extended_ensemble_vs_incumbent

Changed ordered lists 2050; changed rank-position slots 4010; membership-change users 895; order-only changes 1155; top-five set overlap 0.960735135. Relevant-hit gains/losses 152 / 139 (net +13).

Seen relevant hits 9068 → 9070; unseen hits 408 → 419. Seen AP contribution delta +0.000445825826; unseen delta +0.000461381381. No causal explanation is inferred from these changes.

Unchanged candidate coverage: 15999/21466 relevant pairs; micro 0.745318178; macro/oracle MAP 0.728601802/0.728601802. Fixed history slices and category-specific outcomes appear in the per-split JSON. Fallback completion remains zero because original candidate unions contain global5.

### auxiliary: stage1_vs_seed42

Changed ordered lists 2674; changed rank-position slots 5544; membership-change users 1283; order-only changes 1391; top-five set overlap 0.942166049. Relevant-hit gains/losses 217 / 190 (net +27).

Seen relevant hits 8755 → 8778; unseen hits 316 → 320. Seen AP contribution delta +0.001013232125; unseen delta +0.000409069998. No causal explanation is inferred from these changes.

Unchanged candidate coverage: 15639/21080 relevant pairs; micro 0.741888046; macro/oracle MAP 0.724358974/0.724358974. Fixed history slices and category-specific outcomes appear in the per-split JSON. Fallback completion remains zero because original candidate unions contain global5.

### auxiliary: extended_ensemble_vs_incumbent

Changed ordered lists 2019; changed rank-position slots 4015; membership-change users 915; order-only changes 1104; top-five set overlap 0.959293964. Relevant-hit gains/losses 156 / 136 (net +20).

Seen relevant hits 8785 → 8795; unseen hits 319 → 329. Seen AP contribution delta +0.000325779037; unseen delta +0.000345693809. No causal explanation is inferred from these changes.

Unchanged candidate coverage: 15639/21080 relevant pairs; micro 0.741888046; macro/oracle MAP 0.724358974/0.724358974. Fixed history slices and category-specific outcomes appear in the per-split JSON. Fallback completion remains zero because original candidate unions contain global5.

## Exact preservation, independent checks and distributions

Training retains original Apr6->[Apr6,Apr20) and Apr20->[Apr20,May4) rows/labels:604,935 rows and25,385 positives, every negative/query retained. All original 52 values are bitwise equal after appending, metadata/user order is unchanged, labels are hash/manifest checked. Candidate/feature schema is exactly 55 ordered columns. The original seed42 and original four-seed mean reproduce their saved main/auxiliary rankings exactly. New model settings equal original effective values except each predeclared global seed; there is no tuning, weight/sampling change or validation-label training.

| Origin | Rows | All-three-zero rows / fraction | Independent scalar sample / max absolute float32 error | Finite errors | Feature seconds | Full 55 matrix bytes |
|---|---:|---|---|---:|---:|---:|
| origin_20200406 | 291619 | 6775 / 0.023232 | 64 / 0 | 0 | 3.524 | 64,156,180 |
| origin_20200420 | 313316 | 9682 / 0.030902 | 64 / 0 | 0 | 4.559 | 68,929,520 |
| main | 380403 | 29080 / 0.076445 | 64 / 0 | 0 | 6.763 | 83,688,660 |
| auxiliary | 397757 | 32557 / 0.081851 | 64 / 0 | 0 | 7.541 | 87,506,540 |
| final | 152442 | 18440 / 0.120964 | 64 / 0 | 0 | 10.547 | 33,537,240 |

Scalar samples are predeclared uniform 64-row samples per origin, RNG seed 42; the candidate-centric implementation independently scans each distinct history source and checks the stored vector. No private user/row IDs are published. Exact full original item-item score/rank checks additionally validate source orientation, graph reconstruction and retained history conventions across every original row. Missing/unsupported support is encoded 0, not NaN; no extra indicator was added.

| Origin / feature | Min | Mean | Median | P90 | Max | Zero fraction |
|---|---:|---:|---:|---:|---:|---:|
| origin_20200406/ii_other_max_similarity | 0.000000 | 0.345315 | 0.316152 | 0.592173 | 0.804237 | 0.023232 |
| origin_20200406/ii_other_top5_similarity_sum | 0.000000 | 1.204347 | 1.183109 | 2.150031 | 3.568933 | 0.023232 |
| origin_20200406/ii_other_log1p_positive_history_count | 0.000000 | 2.171944 | 2.197225 | 3.218876 | 5.796058 | 0.023232 |
| origin_20200420/ii_other_max_similarity | 0.000000 | 0.379193 | 0.361938 | 0.639329 | 0.842423 | 0.030902 |
| origin_20200420/ii_other_top5_similarity_sum | 0.000000 | 1.402081 | 1.440078 | 2.439443 | 3.778037 | 0.030902 |
| origin_20200420/ii_other_log1p_positive_history_count | 0.000000 | 2.320767 | 2.397895 | 3.433987 | 6.156979 | 0.030902 |
| main/ii_other_max_similarity | 0.000000 | 0.387879 | 0.417869 | 0.675656 | 0.876978 | 0.076445 |
| main/ii_other_top5_similarity_sum | 0.000000 | 1.526016 | 1.645643 | 2.732715 | 3.968168 | 0.076445 |
| main/ii_other_log1p_positive_history_count | 0.000000 | 2.422495 | 2.564949 | 3.871201 | 6.270988 | 0.076445 |
| auxiliary/ii_other_max_similarity | 0.000000 | 0.386871 | 0.422333 | 0.652811 | 0.885638 | 0.081851 |
| auxiliary/ii_other_top5_similarity_sum | 0.000000 | 1.535996 | 1.654797 | 2.731287 | 4.026399 | 0.081851 |
| auxiliary/ii_other_log1p_positive_history_count | 0.000000 | 2.442567 | 2.564949 | 3.970292 | 6.270988 | 0.081851 |
| final/ii_other_max_similarity | 0.000000 | 0.372653 | 0.399064 | 0.661276 | 0.903328 | 0.120964 |
| final/ii_other_top5_similarity_sum | 0.000000 | 1.546967 | 1.563552 | 3.005592 | 4.127005 | 0.120964 |
| final/ii_other_log1p_positive_history_count | 0.000000 | 2.504082 | 2.708050 | 4.343805 | 5.968708 | 0.120964 |

## Runtime and limitations

| Extended seed | Fit seconds | Process-lifetime peak RSS bytes |
|---|---:|---:|
| 42 | 5.763 | 868,777,984 |
| 43 | 5.792 | 1,395,949,568 |
| 44 | 5.848 | 1,494,876,160 |
| 45 | 5.883 | 1,600,520,192 |

Elapsed before optional final inference 79.130s; process-lifetime peak RSS 1,600,520,192 bytes. RSS is resource.ru_maxrss high-water mark, not a per-phase allocation. Feature generation memory/timing and exact effective parameters/model checksums are recorded in diagnostics/fit JSON. Feature importance is descriptive gain usage only; it does not identify a cause of metric changes.

All 112 tests pass. New hand-checkable fixtures verify directed orientation, self-exclusion before all aggregations, each history programme once, no frequency weighting, top-five positive sum, empty/unsupported histories, finite 55 schema and exact first 52 preservation. A future-segment perturbation leaves clipped N50 counts, fitted graph and all new features unchanged. Existing temporal, ranking and submission tests are reused. All prior reports/CSVs/models/caches in the frozen inventory remain unchanged; private graphs/features/weights/mappings are ignored and native session exports untouched.

Reused overlapping cohorts and accumulated selection are not fully represented by conditional intervals. Historical label horizons remain two weeks versus longer main/auxiliary/final forecasts; history lengths differ, original channel mapping is incomplete and origin-specific LightFM scores can shift. The three columns summarize a directed truncated graph rather than full similarities; no improvement or failure should receive a fabricated causal explanation. This bounded result does not justify further variants.

## Candidate and recommendation

File `candidate_item_other_history_affinity_20261031_v21.csv`; absolute path `/Users/chenfengru/sweettv-recommender-exam/submissions/candidate_item_other_history_affinity_20261031_v21.csv`; SHA-256 `256924b2fc729fea5bfa6859da87281d9c003c0863146caf9fddb716d02d2665`.

Both validators pass for original 1,260 users/header/order/five distinct nonzero available IDs and 6,649 carryover-aware candidates: `{"status": "valid", "users": 1260, "k": 5, "candidate_ids": 6649, "distinct_recommended_ids": 127, "template_sha256": "d8c209dce3c7c9d815d8e2a6226e1be63052ee7afa7e8ba8b75dc2f703967a02", "prediction_sha256": "256924b2fc729fea5bfa6859da87281d9c003c0863146caf9fddb716d02d2665"}`. Differences from submitted incumbent: `{"users": 1260, "users_changed": 551, "users_identical": 709, "recommendation_slots": 6300, "rank_position_slots_changed": 1060, "top5_items_in_common": 6060, "top5_set_overlap_fraction": 0.9619047619047619, "users_with_membership_change": 237, "users_with_order_change_only": 314, "new_item_slots_ignoring_order": 240}`. Exactly one CSV, same four historical classifiers on final 55 features; no evaluation-label refit.

Equal-weight ensemble of four historical 55-feature channel-affinity LightGBM classifiers, seeds 42–45. Three added features summarize unweighted positive item-item similarities from other distinct N50-history programmes: maximum, top-five sum and log1p contributor count. Original directed top-50 graphs, self-exclusion, candidates, 52 existing features and training settings are preserved. No evaluation-label refit, tuning or incumbent blending. Validated candidate for manual submission; no Kaggle result.

Recommendation: eligible for cautious manual submission under the frozen two-stage rule, with conditional/selection limitations above. The existing ensemble remains the confirmed submission until a manual result is supplied; no coursework report changes or upload.

Both final ensemble difference intervals include zero. The point-estimate rule qualifies the candidate, but evidence for generalization remains weak; a cautious manual submission is optional, not a confirmed improvement over the submitted model.
