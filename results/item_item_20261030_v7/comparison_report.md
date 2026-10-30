# Fixed item-item collaborative retrieval (executed)

**Retain submitted v5. The fixed item-item model retrieves useful previously unseen relevant programmes on both splits, but its standalone MAP@5 is substantially worse. A subsequent controlled reranking/fusion experiment is warranted; no fusion, final refit or prediction CSV was produced here.**

## Frozen engineering configuration

One model was fit per established temporal split using only pre-cutoff >=0.50 canonical user-airings. B is a sparse binary user-item matrix: repeat airing counts do not increase co-view support. Item support is the number of training users, and co-view support is the number watching both items. Similarity is `c_ij / sqrt(n_i*n_j) * c_ij/(c_ij+20)`. Self-neighbours and pairs with c<3 are excluded. Each item retains at most 50 neighbours, ordered by descending similarity then ascending raw string programme ID. Pruning happens over all training items before prediction availability filtering. The resulting directed neighbourhood can be asymmetric because of per-source pruning.

User scores sum `log1p(N50_ui) * sim(i,j)` over history items. Source items are iterated in raw string order; final equal-score destinations use raw string ID. All N50 history may seed scoring, including items unavailable in the prediction window. Only available destinations receive scores. The standalone direct list keeps previously watched programmes eligible; the second list filters out every item in the user’s N50 history. No validation behaviour enters model fitting, profiles or filtering.

Full original airing denominators, cleaning, canonical deduplication, interval unions, clipped pre-cutoff viewing ends and repeats are unchanged. Shared v5 fallback uses original >=0.80 global qualifications and only completes standalone top five. No additional neighbourhood, support, shrinkage or weight choices were searched.

## Frozen evaluation and standalone ranking

Main: fit [2020-03-09,2020-05-18), validate [2020-05-18,2020-07-27), 4,625 users / 6,384 candidates. Auxiliary: fit [2020-03-09,2020-06-01), validate [2020-06-01,2020-07-27), 4,589 / 5,742. Existing >=0.80 truth, candidate pools and original history-size slices are unchanged. Both original anchor hashes match the preceding round, and recomputed v5 predictions exactly reconcile with saved references. Completed experiments were not rerun.

| Split | v5 MAP@5 | Standalone item-item MAP@5 | Difference | Improved / worsened / unchanged AP users |
| --- | ---: | ---: | ---: | --- |
| main | 0.334711171171 | 0.155453093093 | -0.179258078078 | 752 / 3107 / 766 |
| auxiliary | 0.331395910511 | 0.157389530520 | -0.174006379991 | 751 / 3047 / 791 |

MAP@5 uses the all-supported direct ranking plus the unchanged shared fallback. These descriptive results are conditional on reused overlapping hold-outs, not independent tests. They do not justify replacing v5 or making a benchmark submission.

## Retrieval recall definitions and denominators

All-target recall is |topK intersect R_u| / |R_u| for distinct frozen relevant targets R_u. Macro averages per user over the entire fixed cohort; micro sums hits over summed relevant targets. All users have targets. For absent targets use A_u = R_u minus available N50 personal history. Report both the all-supported ranking evaluated against those targets and the separately filtered unseen-only ranking. The latter permits unseen items to move up after watched candidates are removed.

Conditional absent-target macro averages only over users with |A_u|>0. Users without absent targets are excluded from that mean; an additional cohort macro assigns them zero. They add no absent items or hits to micro recall. Direct lists shorter than K stay short. **No fallback items are included in any Recall@K or coverage metric.** Thus retrieval recall is not standalone ranking quality.

| Split | All-target users | All relevant items | Users with absent targets | Users excluded from conditional macro | Absent relevant items |
| --- | ---: | ---: | ---: | ---: | ---: |
| main | 4625 | 21466 | 3714 | 911 | 8968 |
| auxiliary | 4589 | 21080 | 3666 | 923 | 8720 |

| Split | Direct ranking / targets | K | Hits / relevant items | Macro conditional | Macro, whole cohort with zero if no targets | Micro |
| --- | --- | ---: | --- | ---: | ---: | ---: |
| main | all / all | 20 | 10794 / 21466 | 49.0804% | 49.0804% | 50.2842% |
| main | all / all | 50 | 13865 / 21466 | 63.1553% | 63.1553% | 64.5905% |
| main | all / absent | 20 | 1651 / 8968 | 19.4081% | 15.5852% | 18.4099% |
| main | all / absent | 50 | 2827 / 8968 | 33.6416% | 27.0151% | 31.5232% |
| main | unseen / absent | 20 | 2067 / 8968 | 25.5044% | 20.4807% | 23.0486% |
| main | unseen / absent | 50 | 3435 / 8968 | 41.4970% | 33.3232% | 38.3029% |
| auxiliary | all / all | 20 | 10403 / 21080 | 48.1735% | 48.1735% | 49.3501% |
| auxiliary | all / all | 50 | 13417 / 21080 | 62.1980% | 62.1980% | 63.6480% |
| auxiliary | all / absent | 20 | 1503 / 8720 | 17.8914% | 14.2929% | 17.2362% |
| auxiliary | all / absent | 50 | 2570 / 8720 | 31.0147% | 24.7766% | 29.4725% |
| auxiliary | unseen / absent | 20 | 1876 / 8720 | 23.2547% | 18.5774% | 21.5138% |
| auxiliary | unseen / absent | 50 | 3224 / 8720 | 39.9541% | 31.9180% | 36.9725% |

## Incremental coverage of personal history plus unseen retrieval

The base set is every available programme with an N50 training airing for that user. Add topK unseen direct recommendations, then measure how many relevant targets the union contains. Extra hits equal unseen-list absent-target hits because the two candidate sources are disjoint. Macro coverage averages union hits/|R_u| over all cohort users; micro divides summed union hits by all relevant items.

| Split | Added unseen K | Base hits | Extra hits | Union hits / all relevant | Base -> union macro coverage | Macro gain | Base -> union micro coverage | Micro gain | Users with extra relevant items |
| --- | ---: | ---: | ---: | --- | --- | ---: | --- | ---: | ---: |
| main | 20 | 12498 | 2067 | 14565 / 21466 | 56.5978% -> 66.2793% | +9.6814 pp | 58.2223% -> 67.8515% | +9.6292 pp | 1592 |
| main | 50 | 12498 | 3435 | 15933 / 21466 | 56.5978% -> 72.4789% | +15.8811 pp | 58.2223% -> 74.2244% | +16.0020 pp | 2277 |
| auxiliary | 20 | 12360 | 1876 | 14236 / 21080 | 56.8443% -> 65.8840% | +9.0397 pp | 58.6338% -> 67.5332% | +8.8994 pp | 1471 |
| auxiliary | 50 | 12360 | 3224 | 15584 / 21080 | 56.8443% -> 72.1236% | +15.2793 pp | 58.6338% -> 73.9279% | +15.2941 pp | 2196 |

The candidate-union oracle AP@5 is min(5,h)/min(5,|R_u|). Its mean equals macro coverage here because each frozen target set has at most five items. These are diagnostic bounds for perfect ranking within that candidate union, not attainable scores, guaranteed improvements, or upper bounds for the full system with fallback. Increasing coverage does not establish improved MAP@5; the standalone MAP results demonstrate this distinction.

## Established history-size slices

Membership uses original >=0.80 distinct training programmes before availability filtering, not N50 profile size. All slice-specific recall numerators/denominators, both K values, conditional/cohort macro, micro, union coverage and support/fallback counts are retained in each split’s comparison.json.

| Split | History size | Users | v5 MAP | Item-item MAP | All-target macro R@20 / R@50 | Unseen absent macro R@20 / R@50 (conditional) | Users with absent targets | Extra relevant hits @20 / @50 |
| --- | --- | ---: | ---: | ---: | --- | --- | ---: | --- |
| main | 0 | 108 | 0.162896091 | 0.147330247 | 8.44% / 13.26% | 9.30% / 12.87% | 107 | 32 / 45 |
| main | 1–5 | 462 | 0.193964646 | 0.067028018 | 30.78% / 46.16% | 24.90% / 35.96% | 434 | 326 / 491 |
| main | 6–20 | 2087 | 0.307892110 | 0.121996220 | 48.05% / 61.04% | 25.70% / 41.46% | 1826 | 1090 / 1801 |
| main | 21+ | 1968 | 0.405621895 | 0.212137110 | 56.70% / 72.13% | 26.72% / 45.61% | 1347 | 619 / 1098 |
| auxiliary | 0 | 87 | 0.170593870 | 0.150996169 | 10.40% / 14.48% | 11.19% / 13.95% | 87 | 27 / 37 |
| auxiliary | 1–5 | 401 | 0.197744528 | 0.067649626 | 29.80% / 45.40% | 23.60% / 34.47% | 370 | 262 / 389 |
| auxiliary | 6–20 | 1874 | 0.300831406 | 0.122929859 | 46.92% / 59.88% | 24.99% / 40.73% | 1642 | 951 / 1572 |
| auxiliary | 21+ | 2227 | 0.387463204 | 0.202795614 | 54.02% / 69.04% | 22.02% / 41.88% | 1567 | 636 / 1226 |

## Support, completion and bounded resources

A supported candidate has a positive aggregated neighbour score; positive counts without surviving neighbours do not guarantee a direct list. Empty direct lists use full fallback; lists with 1–4 candidates receive partial completion. Per-user list sizes below refer to all cohort users, including zero-support users.

| Split | Training users / items | Binary pairs | Retained neighbours | Items without neighbours | Available items with N50 support / scored for any cohort user | Direct candidates mean / median / max | Unseen mean / median / max | Full / partial fallback users | Fallback slots |
| --- | --- | ---: | ---: | ---: | --- | --- | --- | --- | ---: |
| main | 4784 / 2682 | 179742 | 102575 | 292 | 2004 / 1363 | 189.04 / 177 / 824 | 162.17 / 154 / 461 | 74 / 1 | 373 |
| auxiliary | 4801 / 3031 | 215794 | 122326 | 279 | 2086 / 1511 | 205.92 / 191 / 836 | 175.59 / 167 / 507 | 60 / 0 | 300 |

| Split | Count extraction seconds | Fit seconds | Cohort scoring seconds | Total split seconds incl. I/O/metrics | B / transpose sparse bytes | Largest co-view block bytes / entries | Peak process RSS bytes |
| --- | ---: | ---: | ---: | ---: | --- | --- | ---: |
| main | 3.644 | 0.527 | 0.832 | 5.946 | 2176044 / 2167636 | 1996992 / 166373 | 588759040 |
| auxiliary | 3.999 | 0.803 | 0.985 | 6.811 | 2608736 / 2601656 | 2298096 / 191465 | 808894464 |

Binary and co-view arrays use int64 counts. Multiplication processes 128 source items at a time and discards each sparse block after pruning; no dense user-item or full co-view matrix is materialized. Sparse byte counts cover numeric CSR buffers only, not Python objects, allocator overhead or transient multiplication workspace. Process RSS is the lifetime high-water mark and includes loaded interactions, models, private ranking serialization and metrics; auxiliary RSS is not an isolated auxiliary-model measurement. Models and user-level histories/rankings remain in ignored private artifacts. These local runtimes are measurements, not deployment latency guarantees.

## Checks, provenance and recommendation

All 53 tests pass. New checks cover hand-computable binary supports/co-view similarity and shrinkage, c>=3 gating, self-exclusion, raw string top-K ties and block-size invariance, log1p weighting, availability and unseen filtering, macro/micro denominators and incremental coverage, and cutoff invariance when future tails/rows are added. Existing matching, denominator, canonical deduplication, qualification, leakage and submission checks were reused. Runtime assertions reconcile v5 and original frozen anchors, preserve truth-file hashes and prior CSVs, and ensure direct/unseen rankings are available, distinct and correctly filtered.

**Conclusion:** the model recovers useful unseen relevant items on both splits: unseen R@50 micro is 38.30% main and 36.97% auxiliary. This warrants a subsequent controlled candidate retrieval plus reranking/fusion experiment, while retaining v5’s strong personal ranking as the reference. It does not warrant submitting this standalone model. No comparative unseen-retrieval baseline was tested, so this does not establish superiority to other retrieval methods. Co-view scores can favor broadly watched programmes; rare/unseen items and users without supported histories remain limitations. Repeated overlapping validation and any subsequent selection introduce uncertainty beyond these descriptive measurements. A future learned reranker would require earlier training labels, not fitting to these reported hold-out labels.

No fusion or additional hyperparameter search was implemented. No final prediction CSV, combined-window refit, Kaggle workflow or upload was initiated. Native session records remain unmodified and student verification is pending.

Frozen protocol SHA-256: `c6c434db4b58e9d119071bd3ccf56b5691e5a36b775970a182a10675897370f6`. Full run time: 21.277 seconds. Exact inputs, source hashes, base commit, environment and artifact checksums appear in run_evidence.json and comparison.json.

Best submitted v5 remains `submissions/candidate_personal_threshold_050_20261030_v5.csv`, SHA-256 `593b1134b6625771abfe107e17d074499cedf6efb4ef9306e06289e9566876e5`. Private 0.40210 / Public 0.41789 are user-reported screenshot scores; submission ID and time remain unknown. Every previous CSV and checksum is preserved.

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 /private/tmp/sweettv-model-venv/bin/python -m src.experiment_item_item --data-dir /Users/chenfengru/LLM4Rec-Course-codex/data/sweettv/raw
/private/tmp/sweettv-model-venv/bin/python -m unittest discover -s tests
/private/tmp/sweettv-model-venv/bin/python -m src.report_item_item
```
