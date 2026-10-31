# V20: controlled seed-only ensemble

Question: does averaging independently seeded copies of the selected v18 channel-affinity classifier improve MAP@5?

Frozen decision: **the sole equal-mean ensemble qualifies for manual review**. Seed 42 is reused unchanged. Exactly 3 additional historical classifiers were fitted. No best-seed selection, weight tuning or other variants. The coursework README/report and all previous submitted artifacts remain unchanged pending a manual result. No Kaggle access or upload occurred. Student verification claims are not changed.

Incumbent main/auxiliary MAP@5: 0.369249609610 / 0.357738856202. User-reported Kaggle Private0.43798 / Public0.44758; no submission ID/time invented. [Pre-evaluation protocol](../../docs/seed_ensemble_protocol.md), [frozen inputs/settings](frozen_experiment.json). Branch codex/v18-seed-ensemble starts at merged main `0cae3390185f6f4e8feda29ac2aed4e686945df5`.

## Enabled stochastic operations

Installed LightGBM 4.6.0 was inspected before any fit, including its sklearn parameter processing and the saved model’s full native parameters. The incumbent has deterministic CPU/force_col_wise enabled; GBDT, row bagging fraction 1/frequency 0; feature fractions 1 per tree/node; extra_trees=0, no DART or GOSS. Thus row bagging, feature subsampling, randomized split thresholds and dropout do not supply diversity here. Merely comparing model file hashes would confuse seed metadata with predictive differences.

However, **subsample_for_bin / bin_construct_sample_cnt remains 200,000 for 604,935 training rows**. Histogram-bin construction therefore samples data. The global random_state derives data_random_seed unless explicitly overridden. Deterministic mode provides reproducibility for the same configuration; it does not make all global seeds equivalent. These are existing settings, not newly enabled randomness. [Official version 4.6 parameter definitions](https://lightgbm.readthedocs.io/en/v4.6.0/Parameters.html#data_random_seed). The inspected API/native fields are recorded in installed_behavior.json.

Each new fit uses the exact incumbent constructor settings/defaults except random_state. Assertions compare effective Booster parameters excluding that one value, and native saved parameters allow differences only in seed fields. Derived bagging/feature/extra/drop seed metadata also changes automatically, although those operations are inactive. No independent override of data_random_seed, sampling fractions or hyperparameters was introduced.

## Stage1 gate

Seed 43 was fitted exactly once before deciding whether to run Stage2. Predictive-tree hashes include feature order, objective and tree split/default/threshold/leaf values; seed metadata and nonpredictive gain/count annotations are excluded.

Seed 42 predictive hash: `5511ac71d27e975aa784a4bcb45eb5624797d2719eaf99b7a65be9e1ecdf459c`. Seed 43: `e6b2e268553ad68259c0caae934b49b080975f943948f342334ed1032a4481e3`. Predictive structures equal: **False**; score diversity found: **True**. The gate uses actual original-inference score differences on main/auxiliary, not seed/file metadata or MAP signs.

| Split | Candidate rows | Seed 43 differing ranking scores | Maximum difference | Mean absolute difference | Differing raw margins |
|---|---:|---:|---:|---:|---:|
| main | 380403 | 380403 | 0.150988910 | 0.002390075 | 380403 |
| auxiliary | 397757 | 397757 | 0.178691526 | 0.002267566 | 397757 |

Actual score diversity permits the frozen Stage2. Seeds 44 and 45 were then fitted once each; no other seed was tried. Individual scores are diagnostic only. The only selectable model is **(score42+score43+score44+score45)/4**, computed per identical candidate row with no weights or seed selection. The score convention is the original v18 `Booster.predict(raw_score=False)` output; raw margins are compared for diagnosis but are not averaged. Scores are ranking signals and are **not assumed calibrated probabilities**.

## Main/auxiliary comparisons

| Method | Main MAP@5 | Delta vs42 | Auxiliary MAP@5 | Delta vs42 |
|---|---:|---:|---:|---:|
| seed42 | 0.369249609610 | +0.000000000000 | 0.357738856202 | +0.000000000000 |
| seed43 | 0.368859399399 | -0.000390210210 | 0.358898452822 | +0.001159596620 |
| seed44 | 0.369593873874 | +0.000344264264 | 0.357677719668 | -0.000061136534 |
| seed45 | 0.369407147147 | +0.000157537538 | 0.359959141425 | +0.002220285223 |
| ensemble | 0.369630450450 | +0.000380840841 | 0.359208735866 | +0.001469879664 |

| Split/method | Paired 95% delta interval | Improved / worsened / unchanged users |
|---|---|---|
| main/seed42 | [+0.000000000000, +0.000000000000] | 0 / 0 / 4625 |
| main/seed43 | [-0.001601600601, +0.000870600601] | 469 / 485 / 3671 |
| main/seed44 | [-0.000885306306, +0.001675962462] | 496 / 478 / 3651 |
| main/seed45 | [-0.000914391892, +0.001326989489] | 396 / 369 / 3860 |
| main/ensemble | [-0.000553138138, +0.001354457958] | 309 / 294 / 4022 |
| auxiliary/seed42 | [+0.000000000000, +0.000000000000] | 0 / 0 / 4589 |
| auxiliary/seed43 | [-0.000043727755, +0.002449501828] | 535 / 462 / 3592 |
| auxiliary/seed44 | [-0.001343861226, +0.001204604610] | 478 / 474 / 3637 |
| auxiliary/seed45 | [+0.001095336675, +0.003368244716] | 486 / 393 / 3710 |
| auxiliary/ensemble | [+0.000506237742, +0.002413166449] | 360 / 279 / 3950 |

Paired user bootstrap: 2,000 resamples, seed 42, percentile 95% intervals. Conditional on the reused cohorts; excludes accumulated model/configuration selection uncertainty and new-training variation. Cohorts/windows overlap and are not independent replication. The ensemble is the only selection candidate even if a diagnostic seed has a larger metric.

## Score and ranking diversity

| Split/method | Differing scores / max abs delta | Score correlation vs42 | Changed full candidate orders | Changed top5 lists / positions / membership users | Top5 set overlap |
|---|---|---:|---:|---|---:|
| main/seed42 | 0 / 0.000000000 | 1.000000000 | 0 | 0 / 0 / 0 | 1.000000000 |
| main/seed43 | 380403 / 0.150988910 | 0.997554229 | 4556 | 2345 / 4777 / 980 | 0.956843243 |
| main/seed44 | 380403 / 0.191233981 | 0.997406627 | 4553 | 2288 / 4709 / 968 | 0.957189189 |
| main/seed45 | 380403 / 0.144054806 | 0.998315703 | 4554 | 1995 / 3901 / 816 | 0.964194595 |
| main/ensemble | 380403 / 0.095447141 | 0.999147042 | 4550 | 1565 / 2941 / 599 | 0.973794595 |
| auxiliary/seed42 | 0 / 0.000000000 | 1.000000000 | 0 | 0 / 0 / 0 | 1.000000000 |
| auxiliary/seed43 | 397757 / 0.178691526 | 0.996933747 | 4578 | 2594 / 5300 / 1131 | 0.949836566 |
| auxiliary/seed44 | 397757 / 0.229627417 | 0.997101411 | 4576 | 2495 / 5131 / 1039 | 0.953846154 |
| auxiliary/seed45 | 397757 / 0.142409373 | 0.997960571 | 4580 | 2247 / 4466 / 937 | 0.958727392 |
| auxiliary/ensemble | 397757 / 0.106172618 | 0.999000809 | 4578 | 1783 / 3395 / 661 | 0.970974068 |

Full-order comparisons apply the unchanged tie sequence: descending ranking score, personal N50 count, original>=80% global viewer count, global airing count, then ascending raw string programme ID. Original fallback completes any insufficient list. All original candidate unions already contain global5, so evaluation completion counts remain zero. Individual/ensemble history-slice outcomes, hit changes and full list-difference statistics remain in per-split JSON. Raw-margin comparisons and all predictive-tree hashes are recorded in all_seed_diversity.json; no seed metadata is used to infer equality.

## Training, preservation and runtime

Training arrays are direct reads of original v18 Apr6/Apr20 tables: 604,935 rows, 25,385 positive labels, 52 unchanged features. Original two-week labels, all negatives/queries, preprocessing, row order, candidate pools and main/auxiliary/final arrays are unchanged. Main/auxiliary labels are read only after fitting each relevant model and are never supplied to fit. Saved seed42 reproduces the exact incumbent rankings on both cohorts. Frozen source/report/CSV/model hashes are checked before and after execution.

| Seed | Training seconds | Process-lifetime peak RSS bytes | Data-bin seed | Predictive-tree hash |
|---|---:|---:|---:|---|
| 43 | 5.696 | 578,715,648 | 179 | `e6b2e268553ad68259c0caae934b49b080975f943948f342334ed1032a4481e3` |
| 44 | 5.803 | 833,388,544 | 182 | `de573d1a177b1b0bc0b3c21623ebd13ab5de6432d8b017b8ccfffb1ddc29071a` |
| 45 | 5.768 | 988,315,648 | 185 | `5dec6c4625ec66bab0402b57c87ed78bb9afba63dd6c8125ee2ca2d1a821b53f` |

Elapsed before optional final inference: 48.449s; process-lifetime peak RSS 988,315,648 bytes. Memory uses resource.ru_maxrss high-water mark rather than per-phase allocation. Exact effective parameters, native seed-only changes, dependency versions and model hashes are recorded in the seed fit JSONs. No incumbent retrain, bin-sampling change, feature/row sampling change, early stopping or evaluation-label fitting occurred.

Automated tests: 108 pass, including new checks that predictive hashes ignore seeds/gains/counts but detect leaf changes; bitwise score equality gates diversity; four fixed aligned vectors receive exactly equal weights. Private model files and predictions remain ignored. The experiment does not modify the coursework report, prior submitted CSVs, original caches or native session records.

Remaining limits: small gains on reused overlapping validation do not establish future/Kaggle performance. Accumulated selection uncertainty remains, as do original two-week historical labels versus longer evaluation/final horizons, different history lengths, incomplete channel mapping and cross-origin LightFM feature-scale shifts. The seed ensemble targets model variance through existing bin-sampling randomness, not new information.

## Candidate and recommendation

Filename: `candidate_channel_affinity_seed_mean_20261031_v20.csv`. Absolute path: `/Users/chenfengru/sweettv-recommender-exam/submissions/candidate_channel_affinity_seed_mean_20261031_v20.csv`. SHA-256: `5c052205c156f48a7f72b38efc680323a34152496bc2e2df7a1964f93961a861`.

Both existing validators pass: `{"status": "valid", "users": 1260, "k": 5, "candidate_ids": 6649, "distinct_recommended_ids": 124, "template_sha256": "d8c209dce3c7c9d815d8e2a6226e1be63052ee7afa7e8ba8b75dc2f703967a02", "prediction_sha256": "5c052205c156f48a7f72b38efc680323a34152496bc2e2df7a1964f93961a861"}`. Original header/order for all 1,260 users; five distinct nonzero available programmes from 6,649 carryover-aware IDs. Differences from incumbent: `{"users": 1260, "users_changed": 455, "users_identical": 805, "recommendation_slots": 6300, "rank_position_slots_changed": 890, "top5_items_in_common": 6121, "top5_set_overlap_fraction": 0.9715873015873016, "users_with_membership_change": 179, "users_with_order_change_only": 276, "new_item_slots_ignoring_order": 179}`. The same four historical models were applied to existing final 52 rows; no final refit or evaluation labels were used.

Equal-weight mean of v18 channel-affinity LightGBM ranking scores from seeds 42, 43, 44 and 45. All four 300-tree historical classifiers use the same 52 features, original training rows/labels and fixed settings; saved seed 42 is reused. Final predictions use unchanged candidate features and ranking rules, with no evaluation-label refit, weight tuning or sampling changes. Validated for manual submission; no Kaggle result.

Recommendation: the candidate is eligible for cautious manual submission under the frozen rule, but evidence is limited: main gain is small and its conditional interval spans zero, while auxiliary is positive with a positive interval. Retain v18 as confirmed incumbent until a user-provided manual result exists. Do not change the coursework report or claim Kaggle improvement now. No upload occurred.
