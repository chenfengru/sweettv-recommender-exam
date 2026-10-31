# Minimal historical LightGBM reranker (executed)

**The single frozen reranker qualifies on both existing splits. Recommend one manual benchmark submission, while retaining v9 as the best confirmed submitted model until a new user-reported result is available.** No tuning, blending, E2 or protected positions were used. Cold users perform worse, and the historical training/evaluation horizon mismatch remains a material limitation.

## Reference and independent implementation

Inspected [3_final_model.ipynb](https://github.com/ndmel/2nd_place_recsys_cinema_challenge_2020/blob/main/3_final_model.ipynb) and [utils.py](https://github.com/ndmel/2nd_place_recsys_cinema_challenge_2020/blob/main/utils.py), provided by the user. Git blob identifiers are `5626149f36a62ed8de9abd3e6ea882c946882fca` and `a96378556c471e6119d2ac8744ef3a8ce7785af9`. Inspiration is binary boosted-tree combination of frequency, rank and collaborative features. The reference threshold helper defaults to retaining only five rows per user; this default is also used during its feature enrichment. Our counts retain **all** qualified programmes, including candidate rows beyond personal rank five. We did not copy its preprocessing, validation split, LightFM/content features, future schedule-change features, tuning or early stopping.

## Frozen supervised temporal protocol

The classifier was trained once, exclusively on the two earlier origins below. Histories begin March 9. Each origin independently rebuilds causal canonical interactions, full behavioural features, original >=0.80 global popularity and the fixed N50 item-item model using only observations available at its cutoff. Labels use the established >=0.80 longest-block/full-original-duration rule and top-five count/raw-ID targets in the half-open future label window.

| Feature cutoff | Label window | Prior history | Feature users | Target users in universe / all label users | All-negative target queries | Candidate rows | Positive rows / rate |
| --- | --- | --- | ---: | --- | ---: | ---: | --- |
| 2020-04-06 | [2020-04-06, 2020-04-20) | 4 weeks | 4836 | 4106 / 4115 | 730 | 291,619 | 13,020 / 4.4647% |
| 2020-04-20 | [2020-04-20, 2020-05-04) | 6 weeks | 4859 | 4120 / 4130 | 739 | 313,316 | 12,365 / 3.9465% |

Training-user membership is determined without labels: users in cleaned pre-cutoff views plus the supplied template users. The 9/10 label-positive users outside that known universe were not added retrospectively. Queries with no target programmes remain as all-negative rows. Candidate rows from both origins are all retained; no negative sampling, class weights or per-query weighting is applied. Label windows do not overlap; histories and users do. The latest supervised label end is May 4, strictly before main/auxiliary feature cutoffs. Evaluation labels are opened only after their feature tables and probabilities are fixed.

Total training rows: **604,935**; positives **25,385 (4.1963%)**. Exactly **1 classifier fit**, **300 trees**. Parameters: binary objective, learning_rate=0.05, num_leaves=15, max_depth=-1, min_child_samples=100, reg_lambda=1.0, n_estimators=300, random_state=42, n_jobs=4. Deterministic column-wise execution is fixed; there is no eval_set, early stopping or hyperparameter search.

## Candidates and 27 complete causal features

Candidate union per user: available direct N50 personal top200, fixed v7 N50-unseen-only item-item top50, and the first five available original >=0.80 global fallback programmes. Deduplicate the union; do not inject positives. Empty histories still receive the five global candidates. Retrieval is rebuilt at each origin, never borrowed from a later cutoff. It uses unchanged binary N50 co-views, cosine*c/(c+20), minimum co-view3, no self-neighbours, top50 neighbours and log1p profile weights. Item-item score/rank features use its full all-supported available ranking; candidate selection uses the unseen-only subset.

Features: full N30/N50/N80 and log1p transforms; full available N50 rank and missing flag; item-item score/rank and separate missing flags; original >=0.80 global viewers/airings; full pre-availability user history sizes and total qualified airings at all three thresholds; days since the most recent **observed segment end of an N50-qualified airing**, with missing flag; trailing 7/28-day N50 counts; three candidate-source flags. Rolling counts independently requalify segments clipped to each window against the full airing denominator. Recency never uses future broadcast ends. Missing numeric fields encode zero plus explicit indicators. Raw user/programme IDs remain private metadata and are not features.

All tables use the identical ordered 27-column float32 schema and contain no NaN/Inf. Counts satisfy N30>=N50>=N80 and rolling7<=rolling28<=N50. Probability ties use the full v5 keys: N50 descending, original global viewers/airings descending, then raw string ID. Every candidate is ranked directly by the classifier; no blend, E2 or rank protection is applied.

## Main and auxiliary MAP@5

Main retains 4,625 users / 6,384 candidates, fit [2020-03-09,2020-05-18), truth [2020-05-18,2020-07-27). Auxiliary retains 4,589 / 5,742, fit [2020-03-09,2020-06-01), truth [2020-06-01,2020-07-27). Original >=0.80 targets, H80 history slices and repeat eligibility are unchanged. Original anchor hashes reconcile, and v5 lists reproduce their saved references.

| Split | Reference | Reference MAP@5 | Reranker MAP@5 | Paired difference | Conditional paired bootstrap 95% interval | Improved / worsened / unchanged users |
| --- | --- | ---: | ---: | ---: | --- | --- |
| main | v5 | 0.334711171171 | 0.350918798799 | +0.016207627628 | [+0.013104299, +0.019631935] | 1555 / 1043 / 2027 |
| main | v9 | 0.335652432432 | 0.350918798799 | +0.015266366366 | [+0.012184692, +0.018535571] | 1547 / 1041 / 2037 |
| auxiliary | v5 | 0.331395910511 | 0.340264037190 | +0.008868126680 | [+0.005592859, +0.012079276] | 1396 / 1095 / 2098 |
| auxiliary | v9 | 0.332178216024 | 0.340264037190 | +0.008085821167 | [+0.004840282, +0.011190885] | 1391 / 1092 / 2106 |

Intervals use 2,000 paired-user resamples, seed42, shared seeded draws across reference comparisons within each split. They are **conditional on reused overlapping cohorts and exclude model-selection uncertainty**. All four intervals are positive, but the hold-outs have been reused across earlier project decisions and are not independent tests.

## Candidate generation versus ranking

For distinct relevant set R_u and candidate union C_u, h_u=|R_u intersect C_u|. Macro candidate recall averages h_u/|R_u| over users with targets; micro is sum(h_u)/sum(|R_u|). Queries without targets are excluded from target-user recall/oracle means, but remain in classifier training. Oracle AP@5 is min(5,h_u)/min(5,|R_u|), averaged over target users. It is the diagnostic ceiling within that candidate union, not a trained model score or guaranteed attainable result. It does not bound systems using other retrieval/fallback candidates. All established target sets contain at most five items, so this oracle equals macro candidate recall here.

| Origin | Target users | Covered relevant pairs / target pairs in universe | Micro recall | Macro recall | Candidate oracle MAP@5 |
| --- | ---: | --- | ---: | ---: | ---: |
| origin_20200406 | 4106 | 13,020 / 15,941 | 81.6762% | 0.788516805 | 0.788516805 |
| origin_20200420 | 4120 | 12,365 / 15,831 | 78.1062% | 0.751322816 | 0.751322816 |
| main | 4625 | 15,999 / 21,466 | 74.5318% | 0.728601802 | 0.728601802 |
| auxiliary | 4589 | 15,639 / 21,080 | 74.1888% | 0.724358974 | 0.724358974 |

About one quarter of evaluation relevant items remain outside the candidate union. Among covered items, the large oracle/reranker gap indicates substantial ranking headroom; it is not a forecast of achievable improvement. The observed MAP gains are measured separately from candidate recall.

## Original history slices and cold users

| Split | Original H80 slice | Users | v5 MAP | v9 MAP | Reranker MAP | Difference versus v9 | Improved / worsened / unchanged versus v9 |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| main | 0 | 108 | 0.162896091 | 0.162896091 | 0.133731996 | -0.029164095 | 19 / 30 / 59 |
| main | 1–5 | 462 | 0.193964646 | 0.197867965 | 0.211899952 | +0.014031987 | 108 / 80 / 274 |
| main | 6–20 | 2087 | 0.307892110 | 0.309094793 | 0.325122185 | +0.016027392 | 715 / 469 / 903 |
| main | 21+ | 1968 | 0.405621895 | 0.405642220 | 0.422829579 | +0.017187359 | 705 / 462 / 801 |
| auxiliary | 0 | 87 | 0.170593870 | 0.171360153 | 0.123722861 | -0.047637292 | 13 / 28 / 46 |
| auxiliary | 1–5 | 401 | 0.197744528 | 0.200412857 | 0.207507620 | +0.007094763 | 74 / 73 / 254 |
| auxiliary | 6–20 | 1874 | 0.300831406 | 0.302055170 | 0.308707607 | +0.006652437 | 563 / 440 / 871 |
| auxiliary | 21+ | 2227 | 0.387463204 | 0.387535050 | 0.399182383 | +0.011647333 | 741 / 551 / 935 |

| Split | Cold definition | Users | v5 MAP | v9 MAP | Reranker MAP |
| --- | --- | ---: | ---: | ---: | ---: |
| main | no_n50_training_history | 74 | 0.168693694 | 0.168693694 | 0.120983483 |
| main | no_available_n50_history | 76 | 0.175219298 | 0.175219298 | 0.128764620 |
| auxiliary | no_n50_training_history | 60 | 0.179583333 | 0.179583333 | 0.123935185 |
| auxiliary | no_available_n50_history | 63 | 0.188227513 | 0.188227513 | 0.132583774 |

Both full-history and availability-specific N50-cold groups worsen. No cold-user override was added after inspection. Post-ranking fallback completion is zero on both splits because global5 is already included in every candidate union, ensuring at least five candidates. This is distinct from the model selecting items also present in the global5 source: 14,170/14,748 selected slots on main/auxiliary have that source membership, which can overlap personal/retrieval sources. V5/v9 global completion slots remain 718/598. Full per-slice candidate coverage, completion, list changes and seen/unseen attribution are in comparison.json.

## Seen/unseen hit attribution and prediction changes

Seen means positive pre-cutoff N50 history; unseen means N50=0. Gains/losses count target item occurrences entering/leaving top five per user. AP attribution assigns each hit precision term to its item type while retaining all earlier hits; contributions sum to MAP and are descriptive, not causal effects. The existing attribution helper uses a legacy `fused_` field prefix for current predictions; here those fields refer only to the unblended reranker.

| Split | Reference | Seen hits baseline -> reranker | Unseen hits baseline -> reranker | Entering unseen items / relevant hits | Leaving unseen items / relevant hits | Seen / unseen MAP contribution change |
| --- | --- | --- | --- | --- | --- | --- |
| main | v5 | 8566 -> 8718 | 107 -> 364 | 2408 / 260 | 75 / 3 | +0.009678679 / +0.006528949 |
| main | v9 | 8529 -> 8718 | 199 -> 364 | 1822 / 183 | 194 / 18 | +0.010383544 / +0.004882823 |
| auxiliary | v5 | 8396 -> 8419 | 94 -> 320 | 2413 / 227 | 24 / 1 | +0.002785042 / +0.006083085 |
| auxiliary | v9 | 8368 -> 8419 | 165 -> 320 | 1888 / 170 | 134 / 15 | +0.003342171 / +0.004743650 |

| Split | Reference | Changed lists | Changed positions | Membership-change / order-only users | Top-five common items / slots | Relevant hit gains / losses |
| --- | --- | ---: | ---: | --- | --- | --- |
| main | v5 | 4433 | 14286 | 3707 / 726 | 17327/23125 (74.9276%) | 1080 / 671 |
| main | v9 | 4429 | 14186 | 3679 / 750 | 17781/23125 (76.8908%) | 1016 / 662 |
| auxiliary | v5 | 4380 | 14136 | 3664 / 716 | 17165/22945 (74.8093%) | 953 / 704 |
| auxiliary | v9 | 4379 | 14063 | 3650 / 729 | 17564/22945 (76.5483%) | 909 / 703 |

## Feature missingness, consistency and model diagnostics

| Origin | Rows | Personal-rank missing | Item-score/rank missing | Recency missing | NaN/Inf |
| --- | ---: | ---: | ---: | ---: | ---: |
| origin_20200406 | 291,619 | 79.3138% | 2.3232% | 79.3138% | 0 |
| origin_20200420 | 313,316 | 75.1273% | 3.0902% | 75.1273% | 0 |
| main | 380,403 | 59.8860% | 7.6445% | 59.8860% | 0 |
| auxiliary | 397,757 | 56.9818% | 8.1851% | 56.9818% | 0 |
| final | 152,442 | 41.2071% | 12.0964% | 41.2071% | 0 |

Missing flags explicitly distinguish absent ranks/scores/recency from valid numeric zeros. Count-zero rates and all flag numerators are retained in each origin JSON. Model feature names, ordered inference schema and finite-value checks match exactly; IDs never enter the 27 predictive columns.

| Feature | Training gain importance | Split count |
| --- | ---: | ---: |
| n30 | 337329.777 | 293 |
| n50_last28days | 195641.153 | 145 |
| n50 | 89819.993 | 61 |
| global_airings80 | 64583.473 | 811 |
| global_viewers80 | 52498.765 | 806 |
| n80 | 34396.307 | 128 |
| personal_n50_rank | 22062.871 | 144 |
| item_item_rank | 19243.684 | 386 |
| item_item_score | 9949.979 | 301 |
| days_since_last_n50_view | 9224.621 | 245 |

Importance is descriptive of this fitted model, not causal evidence. Counts, log counts, ranks, recency and user context are correlated; importance cannot establish that a feature independently caused the gain. No feature removal, alternative model or retuning was performed after inspection. Full 27-feature importance is saved in feature_importance.json.

## Runtime, memory and limitations

| Origin | Feature/retrieval elapsed seconds | Item-item fit seconds | Feature table seconds | Feature matrix bytes | Recorded peak process RSS bytes |
| --- | ---: | ---: | ---: | ---: | ---: |
| origin_20200406 | 27.026 | 0.098 | 1.216 | 31,494,852 | 537,821,184 |
| origin_20200420 | 34.607 | 0.180 | 1.497 | 33,838,128 | 673,988,608 |
| main | 13.642 | 0.552 | 2.631 | 41,083,524 | 860,258,304 |
| auxiliary | 13.993 | 0.807 | 2.453 | 42,957,756 | 951,631,872 |
| final | 16.788 | 1.985 | 1.069 | 16,463,736 | 1,141,309,440 |

Classifier fit took 3.357 seconds; the run through historical labels, fitting and both evaluations took 127.204 seconds before optional final application. Feature-origin timings exclude subsequent historical-label extraction; complete label manifests retain extraction evidence. RSS is process-lifetime high-water, not isolated model allocation. Candidate feature matrices are bounded by at most255 rows/user; sparse item-item multiplication remains blocked at128 source items. Private matrices/model weights/user metadata are not committed.

Historical labels cover only two weeks, versus ten-week main and eight-week auxiliary target windows. Historical feature histories are four/six weeks, versus ten/twelve weeks at validation and twenty weeks at final application; raw counts and popularity can shift in scale. Final forecast spans twelve weeks. Earlier origins share users and overlapping histories; evaluation windows also overlap. These distribution/horizon shifts, reused hold-outs, cold-user losses and correlated features limit transfer of the local gains. No claim of guaranteed Kaggle improvement is supported.

## Final candidate and decision

The fixed rule requires strict improvement against v9 on both splits. The reranker satisfies it. The same saved classifier is applied at the final cutoff; it is not retrained on main/auxiliary labels. Final causal counts/recency/rolling windows/global statistics/retrieval are recomputed on the single combined weeks11–30 window, never summed from separately qualified split counts.

- Filename: `candidate_lightgbm_historical_fixed_20261030_v12.csv`.
- Absolute path: `/Users/chenfengru/sweettv-recommender-exam/submissions/candidate_lightgbm_historical_fixed_20261030_v12.csv`.
- SHA-256: `e18c49cb106df5b5e50f3b7123a080443a2ab48c709e68e721ee9965d96b1457`.
- Internal and independent CLI validation: **valid**; 1,260 original template users/header/order, five distinct available nonzero IDs, 6,649 carryover-aware candidate IDs.
- Versus submitted v9: 1184 changed lists, 3685 changed rank slots; 924 membership-change and 260 order-only users. 76 unchanged lists; set overlap 5034/6300 (79.9048%).
- Frozen classifier SHA-256: `f9e3774164b611ee806c9c170047f955a0d4e505ddadccffd7e4f85cf6abc30b`; exactly one historical fit, unchanged during both evaluations and final application.

Accurate English manual submission description is saved in submission_description.txt:

> Fixed LightGBM binary reranker trained only on Apr6 and Apr20 historical origins with two-week >=80% top-five labels. Candidate union: personal N50 top200, fixed item-item N50-unseen top50, global-popularity first5. Complete causal N30/N50/N80, ranks/scores, recency, rolling counts and source features; no raw IDs, E2 or blending. Same frozen classifier applied to recomputed weeks11–30 features/retrieval; weeks31–42 carryover-aware candidates. Validated for manual review; no Kaggle score.

## Verification and preserved evidence

All **73 tests pass**. Focused checks cover historical cutoff and future-tail invariance, rolling/full-duration counts, half-open label boundaries, top-five truth, complete threshold features beyond personal rank five, missing-rank indicators, label-independent candidates with no positive injection, cold fallback candidates, deterministic probability ties and finite/schema failures. Existing canonical/temporal/ranking/retrieval/submission checks are reused. Verification checks every training/inference/final feature matrix, monotonic counts/rolling windows, model hash, private-file ignore rules and previous CSV Git bytes.

Frozen protocol SHA-256: `c91c1f6de627e51a64a907a68e15ec410177c20c329395df34ed9de9e7fd4d58`. Runtime, source/input hashes, actual model parameters, dependency versions and origin manifests are in the JSON evidence. LightGBM4.6.0/scikit-learn1.7.2 were installed with pinned dependencies; macOS OpenMP libomp23.1.3 was required. See docs/running_lightgbm_reranker.md for reproduction and reference attribution.

User-screenshot-reported results: v9 Private0.40261/Public0.41871; submitted v11 Private0.40257/Public0.41846. V9 remains the best confirmed submitted model. No independent Kaggle lookup, submission ID or timestamp is invented. Both exact submitted files and all previous CSVs/checksums are preserved. The new candidate has not been uploaded and has no Kaggle result.

No Kaggle workflow, submission command, upload or API was used. Native session records remain unmodified; student verification is pending until personally performed. Stop for user review and manual upload.

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 /private/tmp/sweettv-model-venv/bin/python -m src.experiment_lightgbm_reranker --data-dir /Users/chenfengru/LLM4Rec-Course-codex/data/sweettv/raw
/private/tmp/sweettv-model-venv/bin/python -m unittest discover -s tests
/private/tmp/sweettv-model-venv/bin/python -m src.report_lightgbm_reranker
```
