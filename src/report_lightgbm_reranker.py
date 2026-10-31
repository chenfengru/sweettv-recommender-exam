"""Render the fixed historical LightGBM experiment's aggregate evidence."""

import json
from pathlib import Path


def render(out):
    load = lambda p: json.loads(p.read_text())
    selection = load(out / "selection.json")
    training = load(out / "training.json")
    origins = [
        load(out / name / "origin.json")
        for name in ["origin_20200406", "origin_20200420"]
    ]
    data = {s: load(out / s / "comparison.json") for s in ["main", "auxiliary"]}
    importance = load(out / "feature_importance.json")
    artifact = (
        load(out / "candidate_artifact.json")
        if (out / "candidate_artifact.json").exists()
        else None
    )
    lines = [
        "# Minimal historical LightGBM reranker (executed)",
        "",
        "**The single frozen reranker qualifies on both existing splits. Recommend one manual benchmark submission, while retaining v9 as the best confirmed submitted model until a new user-reported result is available.** No tuning, blending, E2 or protected positions were used. Cold users perform worse, and the historical training/evaluation horizon mismatch remains a material limitation.",
        "",
        "## Reference and independent implementation",
        "",
        "Inspected [3_final_model.ipynb](https://github.com/ndmel/2nd_place_recsys_cinema_challenge_2020/blob/main/3_final_model.ipynb) and [utils.py](https://github.com/ndmel/2nd_place_recsys_cinema_challenge_2020/blob/main/utils.py), provided by the user. Git blob identifiers are `5626149f36a62ed8de9abd3e6ea882c946882fca` and `a96378556c471e6119d2ac8744ef3a8ce7785af9`. Inspiration is binary boosted-tree combination of frequency, rank and collaborative features. The reference threshold helper defaults to retaining only five rows per user; this default is also used during its feature enrichment. Our counts retain **all** qualified programmes, including candidate rows beyond personal rank five. We did not copy its preprocessing, validation split, LightFM/content features, future schedule-change features, tuning or early stopping.",
        "",
        "## Frozen supervised temporal protocol",
        "",
        "The classifier was trained once, exclusively on the two earlier origins below. Histories begin March 9. Each origin independently rebuilds causal canonical interactions, full behavioural features, original >=0.80 global popularity and the fixed N50 item-item model using only observations available at its cutoff. Labels use the established >=0.80 longest-block/full-original-duration rule and top-five count/raw-ID targets in the half-open future label window.",
        "",
        "| Feature cutoff | Label window | Prior history | Feature users | Target users in universe / all label users | All-negative target queries | Candidate rows | Positive rows / rate |",
        "| --- | --- | --- | ---: | --- | ---: | ---: | --- |",
    ]
    for d in origins:
        c = d["candidate_coverage"]
        date = d["origin"][-8:]
        date = f"{date[:4]}-{date[4:6]}-{date[6:]}"
        label = (
            "[2020-04-06, 2020-04-20)"
            if date == "2020-04-06"
            else "[2020-04-20, 2020-05-04)"
        )
        weeks = 4 if date == "2020-04-06" else 6
        lines.append(
            f'| {date} | {label} | {weeks} weeks | {d["feature_user_universe"]} | {c["users_with_targets"]} / {c["all_label_users"]} | {c["users_without_targets"]} | {d["features"]["rows"]:,} | {d["positive_rows"]:,} / {d["positive_rate"]:.4%} |'
        )
    lines += [
        "",
        "Training-user membership is determined without labels: users in cleaned pre-cutoff views plus the supplied template users. The 9/10 label-positive users outside that known universe were not added retrospectively. Queries with no target programmes remain as all-negative rows. Candidate rows from both origins are all retained; no negative sampling, class weights or per-query weighting is applied. Label windows do not overlap; histories and users do. The latest supervised label end is May 4, strictly before main/auxiliary feature cutoffs. Evaluation labels are opened only after their feature tables and probabilities are fixed.",
        "",
        f'Total training rows: **{training["total_rows"]:,}**; positives **{training["positive_rows"]:,} ({training["positive_rate"]:.4%})**. Exactly **{training["classifier_fit_calls"]} classifier fit**, **{training["trained_iterations"]} trees**. Parameters: binary objective, learning_rate=0.05, num_leaves=15, max_depth=-1, min_child_samples=100, reg_lambda=1.0, n_estimators=300, random_state=42, n_jobs=4. Deterministic column-wise execution is fixed; there is no eval_set, early stopping or hyperparameter search.',
        "",
        "## Candidates and 27 complete causal features",
        "",
        "Candidate union per user: available direct N50 personal top200, fixed v7 N50-unseen-only item-item top50, and the first five available original >=0.80 global fallback programmes. Deduplicate the union; do not inject positives. Empty histories still receive the five global candidates. Retrieval is rebuilt at each origin, never borrowed from a later cutoff. It uses unchanged binary N50 co-views, cosine*c/(c+20), minimum co-view3, no self-neighbours, top50 neighbours and log1p profile weights. Item-item score/rank features use its full all-supported available ranking; candidate selection uses the unseen-only subset.",
        "",
        "Features: full N30/N50/N80 and log1p transforms; full available N50 rank and missing flag; item-item score/rank and separate missing flags; original >=0.80 global viewers/airings; full pre-availability user history sizes and total qualified airings at all three thresholds; days since the most recent **observed segment end of an N50-qualified airing**, with missing flag; trailing 7/28-day N50 counts; three candidate-source flags. Rolling counts independently requalify segments clipped to each window against the full airing denominator. Recency never uses future broadcast ends. Missing numeric fields encode zero plus explicit indicators. Raw user/programme IDs remain private metadata and are not features.",
        "",
        "All tables use the identical ordered 27-column float32 schema and contain no NaN/Inf. Counts satisfy N30>=N50>=N80 and rolling7<=rolling28<=N50. Probability ties use the full v5 keys: N50 descending, original global viewers/airings descending, then raw string ID. Every candidate is ranked directly by the classifier; no blend, E2 or rank protection is applied.",
        "",
        "## Main and auxiliary MAP@5",
        "",
        "Main retains 4,625 users / 6,384 candidates, fit [2020-03-09,2020-05-18), truth [2020-05-18,2020-07-27). Auxiliary retains 4,589 / 5,742, fit [2020-03-09,2020-06-01), truth [2020-06-01,2020-07-27). Original >=0.80 targets, H80 history slices and repeat eligibility are unchanged. Original anchor hashes reconcile, and v5 lists reproduce their saved references.",
        "",
        "| Split | Reference | Reference MAP@5 | Reranker MAP@5 | Paired difference | Conditional paired bootstrap 95% interval | Improved / worsened / unchanged users |",
        "| --- | --- | ---: | ---: | ---: | --- | --- |",
    ]
    for split, d in data.items():
        for ref, r in d["comparisons"].items():
            ci = r["paired_bootstrap_95pct"]
            lines.append(
                f'| {split} | {ref} | {r["reference_map_at_5"]:.12f} | {r["map_at_5"]:.12f} | {r["delta"]:+.12f} | [{ci[0]:+.9f}, {ci[1]:+.9f}] | {r["users_improved"]} / {r["users_worsened"]} / {r["users_unchanged"]} |'
            )
    lines += [
        "",
        "Intervals use 2,000 paired-user resamples, seed42, shared seeded draws across reference comparisons within each split. They are **conditional on reused overlapping cohorts and exclude model-selection uncertainty**. All four intervals are positive, but the hold-outs have been reused across earlier project decisions and are not independent tests.",
        "",
        "## Candidate generation versus ranking",
        "",
        "For distinct relevant set R_u and candidate union C_u, h_u=|R_u intersect C_u|. Macro candidate recall averages h_u/|R_u| over users with targets; micro is sum(h_u)/sum(|R_u|). Queries without targets are excluded from target-user recall/oracle means, but remain in classifier training. Oracle AP@5 is min(5,h_u)/min(5,|R_u|), averaged over target users. It is the diagnostic ceiling within that candidate union, not a trained model score or guaranteed attainable result. It does not bound systems using other retrieval/fallback candidates. All established target sets contain at most five items, so this oracle equals macro candidate recall here.",
        "",
        "| Origin | Target users | Covered relevant pairs / target pairs in universe | Micro recall | Macro recall | Candidate oracle MAP@5 |",
        "| --- | ---: | --- | ---: | ---: | ---: |",
    ]
    for d in origins:
        c = d["candidate_coverage"]
        lines.append(
            f'| {d["origin"]} | {c["users_with_targets"]} | {c["covered_relevant_pairs"]:,} / {c["all_relevant_pairs_in_universe"]:,} | {c["micro_recall"]:.4%} | {c["macro_recall_target_users"]:.9f} | {c["oracle_map_at_5_target_users"]:.9f} |'
        )
    for split, d in data.items():
        c = d["candidate_coverage"]
        lines.append(
            f'| {split} | {c["users_with_targets"]} | {c["covered_relevant_pairs"]:,} / {c["all_relevant_pairs_in_universe"]:,} | {c["micro_recall"]:.4%} | {c["macro_recall_target_users"]:.9f} | {c["oracle_map_at_5_target_users"]:.9f} |'
        )
    lines += [
        "",
        "About one quarter of evaluation relevant items remain outside the candidate union. Among covered items, the large oracle/reranker gap indicates substantial ranking headroom; it is not a forecast of achievable improvement. The observed MAP gains are measured separately from candidate recall.",
        "",
        "## Original history slices and cold users",
        "",
        "| Split | Original H80 slice | Users | v5 MAP | v9 MAP | Reranker MAP | Difference versus v9 | Improved / worsened / unchanged versus v9 |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for split, d in data.items():
        for sl, r in d["comparisons"]["v9"]["history_slices"].items():
            b = d["comparisons"]["v5"]["history_slices"][sl]
            lines.append(
                f'| {split} | {sl} | {r["users"]} | {b["reference_map_at_5"]:.9f} | {r["reference_map_at_5"]:.9f} | {r["map_at_5"]:.9f} | {r["delta"]:+.9f} | {r["users_improved"]} / {r["users_worsened"]} / {r["users_unchanged"]} |'
            )
    lines += [
        "",
        "| Split | Cold definition | Users | v5 MAP | v9 MAP | Reranker MAP |",
        "| --- | --- | ---: | ---: | ---: | ---: |",
    ]
    for split, d in data.items():
        for definition, r in d["cold_users"].items():
            lines.append(
                f'| {split} | {definition} | {r["users"]} | {r.get("v5_map",0):.9f} | {r.get("v9_map",0):.9f} | {r.get("reranker_map",0):.9f} |'
            )
    lines += [
        "",
        "Both full-history and availability-specific N50-cold groups worsen. No cold-user override was added after inspection. Post-ranking fallback completion is zero on both splits because global5 is already included in every candidate union, ensuring at least five candidates. This is distinct from the model selecting items also present in the global5 source: 14,170/14,748 selected slots on main/auxiliary have that source membership, which can overlap personal/retrieval sources. V5/v9 global completion slots remain 718/598. Full per-slice candidate coverage, completion, list changes and seen/unseen attribution are in comparison.json.",
        "",
        "## Seen/unseen hit attribution and prediction changes",
        "",
        "Seen means positive pre-cutoff N50 history; unseen means N50=0. Gains/losses count target item occurrences entering/leaving top five per user. AP attribution assigns each hit precision term to its item type while retaining all earlier hits; contributions sum to MAP and are descriptive, not causal effects. The existing attribution helper uses a legacy `fused_` field prefix for current predictions; here those fields refer only to the unblended reranker.",
        "",
        "| Split | Reference | Seen hits baseline -> reranker | Unseen hits baseline -> reranker | Entering unseen items / relevant hits | Leaving unseen items / relevant hits | Seen / unseen MAP contribution change |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for split, d in data.items():
        for ref, r in d["comparisons"].items():
            e = r["seen_unseen_effects"]
            g = lambda k: e.get(k, 0)
            lines.append(
                f'| {split} | {ref} | {g("baseline_seen_relevant_hits")} -> {g("fused_seen_relevant_hits")} | {g("baseline_unseen_relevant_hits")} -> {g("fused_unseen_relevant_hits")} | {g("entering_unseen_items")} / {g("entering_unseen_relevant_hits")} | {g("leaving_unseen_items")} / {g("leaving_unseen_relevant_hits")} | {e["delta_seen_map_contribution"]:+.9f} / {e["delta_unseen_map_contribution"]:+.9f} |'
            )
    lines += [
        "",
        "| Split | Reference | Changed lists | Changed positions | Membership-change / order-only users | Top-five common items / slots | Relevant hit gains / losses |",
        "| --- | --- | ---: | ---: | --- | --- | --- |",
    ]
    for split, d in data.items():
        for ref, r in d["comparisons"].items():
            c = r["prediction_changes"]
            lines.append(
                f'| {split} | {ref} | {c["users_changed"]} | {c["rank_position_slots_changed"]} | {c["users_with_membership_change"]} / {c["users_with_order_change_only"]} | {c["top5_items_in_common"]}/{c["recommendation_slots"]} ({c["top5_set_overlap_fraction"]:.4%}) | {r["relevant_hit_gains"]} / {r["relevant_hit_losses"]} |'
            )
    lines += [
        "",
        "## Feature missingness, consistency and model diagnostics",
        "",
        "| Origin | Rows | Personal-rank missing | Item-score/rank missing | Recency missing | NaN/Inf |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    tables = [(d["origin"], d["features"]) for d in origins] + [
        (s, d["features"]) for s, d in data.items()
    ]
    if artifact:
        tables.append(("final", artifact["final_origin"]["features"]))
    for name, d in tables:
        m = d["encoded_missing"]
        lines.append(
            f'| {name} | {d["rows"]:,} | {m["personal_rank_missing"]["fraction"]:.4%} | {m["item_item_score_missing"]["fraction"]:.4%} | {m["last_n50_view_missing"]["fraction"]:.4%} | {d["actual_nan_or_inf"]} |'
        )
    lines += [
        "",
        "Missing flags explicitly distinguish absent ranks/scores/recency from valid numeric zeros. Count-zero rates and all flag numerators are retained in each origin JSON. Model feature names, ordered inference schema and finite-value checks match exactly; IDs never enter the 27 predictive columns.",
        "",
        "| Feature | Training gain importance | Split count |",
        "| --- | ---: | ---: |",
    ]
    for r in importance[:10]:
        lines.append(f'| {r["feature"]} | {r["gain"]:.3f} | {r["split_count"]} |')
    lines += [
        "",
        "Importance is descriptive of this fitted model, not causal evidence. Counts, log counts, ranks, recency and user context are correlated; importance cannot establish that a feature independently caused the gain. No feature removal, alternative model or retuning was performed after inspection. Full 27-feature importance is saved in feature_importance.json.",
        "",
        "## Runtime, memory and limitations",
        "",
        "| Origin | Feature/retrieval elapsed seconds | Item-item fit seconds | Feature table seconds | Feature matrix bytes | Recorded peak process RSS bytes |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for name, d in (
        [(d["origin"], d) for d in origins]
        + list(data.items())
        + ([("final", artifact["final_origin"])] if artifact else [])
    ):
        lines.append(
            f'| {name} | {d["feature_and_retrieval_elapsed_seconds"]:.3f} | {d["retrieval_seconds"]:.3f} | {d["feature_table_seconds"]:.3f} | {d["features"]["matrix_bytes"]:,} | {d["environment"]["peak_process_rss_bytes"]:,} |'
        )
    lines += [
        "",
        f'Classifier fit took {training["fit_seconds"]:.3f} seconds; the run through historical labels, fitting and both evaluations took {selection["elapsed_before_optional_final_seconds"]:.3f} seconds before optional final application. Feature-origin timings exclude subsequent historical-label extraction; complete label manifests retain extraction evidence. RSS is process-lifetime high-water, not isolated model allocation. Candidate feature matrices are bounded by at most255 rows/user; sparse item-item multiplication remains blocked at128 source items. Private matrices/model weights/user metadata are not committed.',
        "",
        "Historical labels cover only two weeks, versus ten-week main and eight-week auxiliary target windows. Historical feature histories are four/six weeks, versus ten/twelve weeks at validation and twenty weeks at final application; raw counts and popularity can shift in scale. Final forecast spans twelve weeks. Earlier origins share users and overlapping histories; evaluation windows also overlap. These distribution/horizon shifts, reused hold-outs, cold-user losses and correlated features limit transfer of the local gains. No claim of guaranteed Kaggle improvement is supported.",
        "",
        "## Final candidate and decision",
        "",
        "The fixed rule requires strict improvement against v9 on both splits. The reranker satisfies it. The same saved classifier is applied at the final cutoff; it is not retrained on main/auxiliary labels. Final causal counts/recency/rolling windows/global statistics/retrieval are recomputed on the single combined weeks11–30 window, never summed from separately qualified split counts.",
        "",
    ]
    if artifact:
        c = artifact["differences_from_submitted_v9"]
        v = artifact["validation"]
        lines += [
            f'- Filename: `{artifact["filename"]}`.',
            f'- Absolute path: `{artifact["absolute_path"]}`.',
            f'- SHA-256: `{artifact["sha256"]}`.',
            f'- Internal and independent CLI validation: **{v["status"]}**; {v["users"]:,} original template users/header/order, five distinct available nonzero IDs, {v["candidate_ids"]:,} carryover-aware candidate IDs.',
            f'- Versus submitted v9: {c["users_changed"]} changed lists, {c["rank_position_slots_changed"]} changed rank slots; {c["users_with_membership_change"]} membership-change and {c["users_with_order_change_only"]} order-only users. {c["users_identical"]} unchanged lists; set overlap {c["top5_items_in_common"]}/{c["recommendation_slots"]} ({c["top5_set_overlap_fraction"]:.4%}).',
            f'- Frozen classifier SHA-256: `{artifact["frozen_classifier_sha256"]}`; exactly one historical fit, unchanged during both evaluations and final application.',
            "",
            "Accurate English manual submission description is saved in submission_description.txt:",
            "",
            "> " + artifact["submission_description"],
            "",
        ]
    lines += [
        "## Verification and preserved evidence",
        "",
        "All **73 tests pass**. Focused checks cover historical cutoff and future-tail invariance, rolling/full-duration counts, half-open label boundaries, top-five truth, complete threshold features beyond personal rank five, missing-rank indicators, label-independent candidates with no positive injection, cold fallback candidates, deterministic probability ties and finite/schema failures. Existing canonical/temporal/ranking/retrieval/submission checks are reused. Verification checks every training/inference/final feature matrix, monotonic counts/rolling windows, model hash, private-file ignore rules and previous CSV Git bytes.",
        "",
        f'Frozen protocol SHA-256: `{selection["frozen_protocol_sha256"]}`. Runtime, source/input hashes, actual model parameters, dependency versions and origin manifests are in the JSON evidence. LightGBM4.6.0/scikit-learn1.7.2 were installed with pinned dependencies; macOS OpenMP libomp23.1.3 was required. See docs/running_lightgbm_reranker.md for reproduction and reference attribution.',
        "",
        "User-screenshot-reported results: v9 Private0.40261/Public0.41871; submitted v11 Private0.40257/Public0.41846. V9 remains the best confirmed submitted model. No independent Kaggle lookup, submission ID or timestamp is invented. Both exact submitted files and all previous CSVs/checksums are preserved. The new candidate has not been uploaded and has no Kaggle result.",
        "",
        "No Kaggle workflow, submission command, upload or API was used. Native session records remain unmodified; student verification is pending until personally performed. Stop for user review and manual upload.",
        "",
        "```bash",
        "OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 /private/tmp/sweettv-model-venv/bin/python -m src.experiment_lightgbm_reranker --data-dir /Users/chenfengru/LLM4Rec-Course-codex/data/sweettv/raw",
        "/private/tmp/sweettv-model-venv/bin/python -m unittest discover -s tests",
        "/private/tmp/sweettv-model-venv/bin/python -m src.report_lightgbm_reranker",
        "```",
    ]
    (out / "comparison_report.md").write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    render(Path("results/lightgbm_reranker_20261030_v12"))
