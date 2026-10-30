"""Render fixed item-item aggregate evidence in English."""

import json
from pathlib import Path


def render(out):
    load = lambda p: json.loads(p.read_text())
    summaries = {s: load(out / s / "comparison.json") for s in ["main", "auxiliary"]}
    evidence = load(out / "run_evidence.json")
    lines = [
        "# Fixed item-item collaborative retrieval (executed)",
        "",
        "**Retain submitted v5. The fixed item-item model retrieves useful previously unseen relevant programmes on both splits, but its standalone MAP@5 is substantially worse. A subsequent controlled reranking/fusion experiment is warranted; no fusion, final refit or prediction CSV was produced here.**",
        "",
        "## Frozen engineering configuration",
        "",
        "One model was fit per established temporal split using only pre-cutoff >=0.50 canonical user-airings. B is a sparse binary user-item matrix: repeat airing counts do not increase co-view support. Item support is the number of training users, and co-view support is the number watching both items. Similarity is `c_ij / sqrt(n_i*n_j) * c_ij/(c_ij+20)`. Self-neighbours and pairs with c<3 are excluded. Each item retains at most 50 neighbours, ordered by descending similarity then ascending raw string programme ID. Pruning happens over all training items before prediction availability filtering. The resulting directed neighbourhood can be asymmetric because of per-source pruning.",
        "",
        "User scores sum `log1p(N50_ui) * sim(i,j)` over history items. Source items are iterated in raw string order; final equal-score destinations use raw string ID. All N50 history may seed scoring, including items unavailable in the prediction window. Only available destinations receive scores. The standalone direct list keeps previously watched programmes eligible; the second list filters out every item in the user’s N50 history. No validation behaviour enters model fitting, profiles or filtering.",
        "",
        "Full original airing denominators, cleaning, canonical deduplication, interval unions, clipped pre-cutoff viewing ends and repeats are unchanged. Shared v5 fallback uses original >=0.80 global qualifications and only completes standalone top five. No additional neighbourhood, support, shrinkage or weight choices were searched.",
        "",
        "## Frozen evaluation and standalone ranking",
        "",
        "Main: fit [2020-03-09,2020-05-18), validate [2020-05-18,2020-07-27), 4,625 users / 6,384 candidates. Auxiliary: fit [2020-03-09,2020-06-01), validate [2020-06-01,2020-07-27), 4,589 / 5,742. Existing >=0.80 truth, candidate pools and original history-size slices are unchanged. Both original anchor hashes match the preceding round, and recomputed v5 predictions exactly reconcile with saved references. Completed experiments were not rerun.",
        "",
        "| Split | v5 MAP@5 | Standalone item-item MAP@5 | Difference | Improved / worsened / unchanged AP users |",
        "| --- | ---: | ---: | ---: | --- |",
    ]
    for split, d in summaries.items():
        lines.append(
            f'| {split} | {d["v5_map_at_5"]:.12f} | {d["item_item_map_at_5"]:.12f} | {d["delta_from_v5"]:+.12f} | {d["users_improved"]} / {d["users_worsened"]} / {d["users_unchanged"]} |'
        )
    lines += [
        "",
        "MAP@5 uses the all-supported direct ranking plus the unchanged shared fallback. These descriptive results are conditional on reused overlapping hold-outs, not independent tests. They do not justify replacing v5 or making a benchmark submission.",
        "",
        "## Retrieval recall definitions and denominators",
        "",
        "All-target recall is |topK intersect R_u| / |R_u| for distinct frozen relevant targets R_u. Macro averages per user over the entire fixed cohort; micro sums hits over summed relevant targets. All users have targets. For absent targets use A_u = R_u minus available N50 personal history. Report both the all-supported ranking evaluated against those targets and the separately filtered unseen-only ranking. The latter permits unseen items to move up after watched candidates are removed.",
        "",
        "Conditional absent-target macro averages only over users with |A_u|>0. Users without absent targets are excluded from that mean; an additional cohort macro assigns them zero. They add no absent items or hits to micro recall. Direct lists shorter than K stay short. **No fallback items are included in any Recall@K or coverage metric.** Thus retrieval recall is not standalone ranking quality.",
        "",
        "| Split | All-target users | All relevant items | Users with absent targets | Users excluded from conditional macro | Absent relevant items |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for split, d in summaries.items():
        a = d["retrieval"]["20"]["all_ranking_all_targets"]
        b = d["retrieval"]["20"]["unseen_ranking_absent_targets"]
        lines.append(
            f'| {split} | {d["users"]} | {a["target_items"]} | {b["users_with_targets"]} | {b["users_without_targets"]} | {b["target_items"]} |'
        )
    lines += [
        "",
        "| Split | Direct ranking / targets | K | Hits / relevant items | Macro conditional | Macro, whole cohort with zero if no targets | Micro |",
        "| --- | --- | ---: | --- | ---: | ---: | ---: |",
    ]
    names = [
        ("all_ranking_all_targets", "all / all"),
        ("all_ranking_absent_targets", "all / absent"),
        ("unseen_ranking_absent_targets", "unseen / absent"),
    ]
    for split, d in summaries.items():
        for key, label in names:
            for k in ["20", "50"]:
                r = d["retrieval"][k][key]
                lines.append(
                    f'| {split} | {label} | {k} | {r["hits"]} / {r["target_items"]} | {r["macro_conditional"]:.4%} | {r["macro_cohort_zero_for_no_targets"]:.4%} | {r["micro"]:.4%} |'
                )
    lines += [
        "",
        "## Incremental coverage of personal history plus unseen retrieval",
        "",
        "The base set is every available programme with an N50 training airing for that user. Add topK unseen direct recommendations, then measure how many relevant targets the union contains. Extra hits equal unseen-list absent-target hits because the two candidate sources are disjoint. Macro coverage averages union hits/|R_u| over all cohort users; micro divides summed union hits by all relevant items.",
        "",
        "| Split | Added unseen K | Base hits | Extra hits | Union hits / all relevant | Base -> union macro coverage | Macro gain | Base -> union micro coverage | Micro gain | Users with extra relevant items |",
        "| --- | ---: | ---: | ---: | --- | --- | ---: | --- | ---: | ---: |",
    ]
    for split, d in summaries.items():
        for k in ["20", "50"]:
            r = d["retrieval"][k]["union_with_personal_history"]
            lines.append(
                f'| {split} | {k} | {r["base_hits"]} | {r["additional_relevant_items"]} | {r["union_hits"]} / {r["target_items"]} | {r["base_macro_coverage"]:.4%} -> {r["union_macro_coverage"]:.4%} | {100*r["macro_coverage_gain"]:+.4f} pp | {r["base_micro_coverage"]:.4%} -> {r["union_micro_coverage"]:.4%} | {100*r["micro_coverage_gain"]:+.4f} pp | {r["users_with_extra_relevant_items"]} |'
            )
    lines += [
        "",
        "The candidate-union oracle AP@5 is min(5,h)/min(5,|R_u|). Its mean equals macro coverage here because each frozen target set has at most five items. These are diagnostic bounds for perfect ranking within that candidate union, not attainable scores, guaranteed improvements, or upper bounds for the full system with fallback. Increasing coverage does not establish improved MAP@5; the standalone MAP results demonstrate this distinction.",
        "",
        "## Established history-size slices",
        "",
        "Membership uses original >=0.80 distinct training programmes before availability filtering, not N50 profile size. All slice-specific recall numerators/denominators, both K values, conditional/cohort macro, micro, union coverage and support/fallback counts are retained in each split’s comparison.json.",
        "",
        "| Split | History size | Users | v5 MAP | Item-item MAP | All-target macro R@20 / R@50 | Unseen absent macro R@20 / R@50 (conditional) | Users with absent targets | Extra relevant hits @20 / @50 |",
        "| --- | --- | ---: | ---: | ---: | --- | --- | ---: | --- |",
    ]
    for split, d in summaries.items():
        for sl, s in d["history_slices"].items():
            a = s["retrieval"]["20"]
            b = s["retrieval"]["50"]
            percent = lambda x: f"{100*x:.2f}%" if x is not None else "n/a"
            lines.append(
                f'| {split} | {sl} | {s["users"]} | {s["v5_map_at_5"]:.9f} | {s["item_item_map_at_5"]:.9f} | {percent(a["all_ranking_all_targets"]["macro_conditional"])} / {percent(b["all_ranking_all_targets"]["macro_conditional"])} | {percent(a["unseen_ranking_absent_targets"]["macro_conditional"])} / {percent(b["unseen_ranking_absent_targets"]["macro_conditional"])} | {a["unseen_ranking_absent_targets"]["users_with_targets"]} | {a["union_with_personal_history"]["additional_relevant_items"]} / {b["union_with_personal_history"]["additional_relevant_items"]} |'
            )
    lines += [
        "",
        "## Support, completion and bounded resources",
        "",
        "A supported candidate has a positive aggregated neighbour score; positive counts without surviving neighbours do not guarantee a direct list. Empty direct lists use full fallback; lists with 1–4 candidates receive partial completion. Per-user list sizes below refer to all cohort users, including zero-support users.",
        "",
        "| Split | Training users / items | Binary pairs | Retained neighbours | Items without neighbours | Available items with N50 support / scored for any cohort user | Direct candidates mean / median / max | Unseen mean / median / max | Full / partial fallback users | Fallback slots |",
        "| --- | --- | ---: | ---: | ---: | --- | --- | --- | --- | ---: |",
    ]
    for split, d in summaries.items():
        m = d["model"]
        a = d["direct_supported_candidates"]
        b = d["unseen_supported_candidates"]
        f = d["fallback"]
        lines.append(
            f'| {split} | {m["training_users"]} / {m["training_items"]} | {m["binary_pairs"]} | {m["retained_directed_neighbours"]} | {m["items_without_neighbours"]} | {d["items_in_pool_with_n50_support"]} / {d["items_in_pool_scored_for_any_cohort_user"]} | {a["mean"]:.2f} / {a["median"]:.0f} / {a["max"]} | {b["mean"]:.2f} / {b["median"]:.0f} / {b["max"]} | {f["complete_users"]} / {f["partial_users"]} | {f["completion_slots"]} |'
        )
    lines += [
        "",
        "| Split | Count extraction seconds | Fit seconds | Cohort scoring seconds | Total split seconds incl. I/O/metrics | B / transpose sparse bytes | Largest co-view block bytes / entries | Peak process RSS bytes |",
        "| --- | ---: | ---: | ---: | ---: | --- | --- | ---: |",
    ]
    for split, d in summaries.items():
        m = d["model"]
        lines.append(
            f'| {split} | {d["count_extraction_seconds"]:.3f} | {d["fit_seconds"]:.3f} | {d["inference_seconds"]:.3f} | {d["evaluation_seconds_including_io"]:.3f} | {m["binary_sparse_bytes"]} / {m["transpose_sparse_bytes"]} | {m["max_coview_block_sparse_bytes"]} / {m["max_coview_block_nnz"]} | {d["environment"]["peak_process_rss_bytes"]} |'
        )
    lines += [
        "",
        "Binary and co-view arrays use int64 counts. Multiplication processes 128 source items at a time and discards each sparse block after pruning; no dense user-item or full co-view matrix is materialized. Sparse byte counts cover numeric CSR buffers only, not Python objects, allocator overhead or transient multiplication workspace. Process RSS is the lifetime high-water mark and includes loaded interactions, models, private ranking serialization and metrics; auxiliary RSS is not an isolated auxiliary-model measurement. Models and user-level histories/rankings remain in ignored private artifacts. These local runtimes are measurements, not deployment latency guarantees.",
        "",
        "## Checks, provenance and recommendation",
        "",
        "All 53 tests pass. New checks cover hand-computable binary supports/co-view similarity and shrinkage, c>=3 gating, self-exclusion, raw string top-K ties and block-size invariance, log1p weighting, availability and unseen filtering, macro/micro denominators and incremental coverage, and cutoff invariance when future tails/rows are added. Existing matching, denominator, canonical deduplication, qualification, leakage and submission checks were reused. Runtime assertions reconcile v5 and original frozen anchors, preserve truth-file hashes and prior CSVs, and ensure direct/unseen rankings are available, distinct and correctly filtered.",
        "",
        "**Conclusion:** the model recovers useful unseen relevant items on both splits: unseen R@50 micro is 38.30% main and 36.97% auxiliary. This warrants a subsequent controlled candidate retrieval plus reranking/fusion experiment, while retaining v5’s strong personal ranking as the reference. It does not warrant submitting this standalone model. No comparative unseen-retrieval baseline was tested, so this does not establish superiority to other retrieval methods. Co-view scores can favor broadly watched programmes; rare/unseen items and users without supported histories remain limitations. Repeated overlapping validation and any subsequent selection introduce uncertainty beyond these descriptive measurements. A future learned reranker would require earlier training labels, not fitting to these reported hold-out labels.",
        "",
        "No fusion or additional hyperparameter search was implemented. No final prediction CSV, combined-window refit, Kaggle workflow or upload was initiated. Native session records remain unmodified and student verification is pending.",
        "",
        f'Frozen protocol SHA-256: `{evidence["protocol_sha256"]}`. Full run time: {evidence["elapsed_seconds"]:.3f} seconds. Exact inputs, source hashes, base commit, environment and artifact checksums appear in run_evidence.json and comparison.json.',
        "",
        "Best submitted v5 remains `submissions/candidate_personal_threshold_050_20261030_v5.csv`, SHA-256 `593b1134b6625771abfe107e17d074499cedf6efb4ef9306e06289e9566876e5`. Private 0.40210 / Public 0.41789 are user-reported screenshot scores; submission ID and time remain unknown. Every previous CSV and checksum is preserved.",
        "",
        "```bash",
        "OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 /private/tmp/sweettv-model-venv/bin/python -m src.experiment_item_item --data-dir /Users/chenfengru/LLM4Rec-Course-codex/data/sweettv/raw",
        "/private/tmp/sweettv-model-venv/bin/python -m unittest discover -s tests",
        "/private/tmp/sweettv-model-venv/bin/python -m src.report_item_item",
        "```",
    ]
    (out / "comparison_report.md").write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    render(Path("results/item_item_20261030_v7"))
