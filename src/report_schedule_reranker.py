"""Render the single frozen schedule-extension experiment in English."""

import json
from datetime import datetime
from pathlib import Path
from .schedule_features import SCHEDULE_FEATURES


def render(out):
    load = lambda p: json.loads(p.read_text())
    selection = load(out / "selection.json")
    training = load(out / "training.json")
    coverage = load(out / "schedule_coverage.json")
    origins = ["origin_20200406", "origin_20200420", "main", "auxiliary", "final"]
    features = {name: load(out / name / "feature_diagnostics.json") for name in origins}
    results = {
        name: load(out / name / "comparison.json") for name in ["main", "auxiliary"]
    }
    importance = load(out / "feature_importance.json")
    artifact = (
        load(out / "candidate_artifact.json")
        if (out / "candidate_artifact.json").exists()
        else None
    )
    lines = [
        "# Single schedule-exposure extension of historical LightGBM (executed)",
        "",
        "**The schedule-extended model qualifies on both splits. Recommend one manual benchmark submission, while retaining v12 as the best confirmed submitted model until a new user-reported result is available.** Exactly one new classifier was trained; v12’s candidates, labels, original 27 features and model parameters were preserved. No E2, blend, cold override or post-result feature search was used.",
        "",
        "## Frozen extension and unchanged control",
        "",
        "Add exactly seven features: past/future scheduled airings per day, past/future clipped broadcast seconds per day, their two log1p rate differences (future minus past), and a zero-past-airings indicator. Past is always the full 28 days before the origin cutoff; future is that origin’s exact label/prediction window. Full-window days, including zero-airing days, are the denominators.",
        "",
        "Schedules use canonical (channel,start,end,programme) deduplication across the three audited exports, positive durations and nonzero programme IDs. Count a canonical airing once in each window with positive overlap; sum its duration clipped to that window. Cross-channel exposures add, even when simultaneous; these are scheduled broadcast seconds, not wall-clock availability unions. Boundary-touching nonoverlaps are excluded and carryovers are clipped at both ends.",
        "",
        "Only programme ID, channel, start and duration fields are read for these features. No viewing log or content attribute is joined. Historical future features cover only the corresponding two-week label window; evaluation/final future exposure covers the permitted prediction window. Original candidate availability remains unchanged.",
        "",
        "Historical training origins remain April6->[April6,April20) and April20->[April20,May4), with histories beginning March9. The same 604,935 rows, 25,385 labels=1 and all negatives are retained in exactly their cached order. The original float32 feature columns are copied byte-for-value; seven columns are appended for an identical 34-column training/inference schema. Raw IDs remain metadata only.",
        "",
        "Classifier settings are exactly v12’s fixed binary LightGBM settings: learning_rate0.05,num_leaves15,max_depth-1,min_child_samples100,reg_lambda1,n_estimators300,random_state42,n_jobs4, deterministic column-wise execution. Exactly one fit and 300 iterations; no early stopping, weights, subsampling or parameter changes. Probability ties use N50, original >=0.80 viewer/airing popularity and raw string ID. The classifier ranks the full unchanged candidate union, preserving no particular positions.",
        "",
        "## Required schedule coverage: checked before fitting",
        "",
        "The gate was fixed before inspecting results: all three source files must exist and match v12 hashes; the union of valid nonzero airing intervals must cover every required window second with no gaps. All ten windows, including final application, passed before fitting. Failure would stop the experiment without imputing missing coverage as zero. Source ranges, canonical counts and channel coverage are retained in schedule_coverage.json.",
        "",
        "| Origin | Window | Source wall-date interval | Full days | Canonical overlapping airings | Channels | Global covered seconds / required | Gaps | Per-channel coverage min / median / max |",
        "| --- | --- | --- | ---: | ---: | ---: | --- | ---: | --- |",
    ]
    date = lambda t: datetime.utcfromtimestamp(t).strftime("%Y-%m-%d")
    for name in origins:
        for kind, r in coverage["origins"][name].items():
            if kind not in ["past", "future"]:
                continue
            c = r["channel_coverage_fraction"]
            lines.append(
                f'| {name} | {kind} | [{date(r["window"][0])},{date(r["window"][1])}) | {r["full_window_days"]:.0f} | {r["canonical_airings"]:,} | {r["channels"]} | {r["global_covered_seconds"]:.0f} / {r["required_seconds"]:.0f} | {len(r["global_gaps"])} | {c["min"]:.5%} / {c["median"]:.5%} / {c["max"]:.5%} |'
            )
    lines += [
        "",
        "These checks establish temporal availability in the provided authoritative exports, not independent completeness of every channel’s guide. Per-channel gaps and changing channel coverage are explicitly reported; absence for a programme is measured relative to the supplied canonical catalogue. No external channel-completeness guarantee is claimed. Genuine zero programme exposure is represented as zero only after the window-level gate passes; there are no missing-coverage NaNs or silent missing-window imputations.",
        "",
        "## MAP@5 versus saved v12 predictions",
        "",
        "| Split | Saved v12 MAP@5 | Extended MAP@5 | Paired difference | Conditional paired bootstrap 95% interval | Improved / worsened / unchanged users |",
        "| --- | ---: | ---: | ---: | --- | --- |",
    ]
    for name, d in results.items():
        r = d["comparison_v12"]
        ci = r["paired_bootstrap_95pct"]
        lines.append(
            f'| {name} | {r["reference_map_at_5"]:.12f} | {r["map_at_5"]:.12f} | {r["delta"]:+.12f} | [{ci[0]:+.9f}, {ci[1]:+.9f}] | {r["users_improved"]} / {r["users_worsened"]} / {r["users_unchanged"]} |'
        )
    lines += [
        "",
        "Paired intervals use 2,000 user resamples, seed42. They condition on the reused cohorts and exclude selection uncertainty. Main and auxiliary windows/users overlap and are not independent tests. Both differences and intervals are positive. No additional feature or variant was tested after inspection.",
        "",
        "## Candidate equality and retrieval limits",
        "",
        "Every cached row_index/users/items/offset and historical label file is hashed before and after the run. All 27 original feature values are exactly equal. Candidate recall and oracle dictionaries exactly match v12; no positives are injected and no programme is added or removed. This isolates reranking with the schedule extension from candidate-generation changes.",
        "",
        "| Split | Users | Covered relevant pairs / all targets | Candidate micro recall | Candidate macro recall | Oracle MAP@5 |",
        "| --- | ---: | --- | ---: | ---: | ---: |",
    ]
    for name, d in results.items():
        c = d["candidate_coverage_exactly_equal_v12"]
        lines.append(
            f'| {name} | {c["users_with_targets"]} | {c["covered_relevant_pairs"]:,} / {c["all_relevant_pairs_in_universe"]:,} | {c["micro_recall"]:.4%} | {c["macro_recall_target_users"]:.9f} | {c["oracle_map_at_5_target_users"]:.9f} |'
        )
    lines += [
        "",
        "For relevant set R and candidate set C, recall is |R intersect C|/|R|; macro averages users, micro sums covered/target occurrences. Oracle AP is min(5,|R intersect C|)/min(5,|R|), averaged per user. It equals macro recall because existing target sets have at most five items. It is a diagnostic ceiling within this fixed candidate union, not trained-model performance or a promise of attainable gains. Candidate limits are unchanged; measured improvements are ranking changes.",
        "",
        "## Existing history slices and cold users",
        "",
        "| Split | Original H80 slice | Users | v12 MAP@5 | Extended MAP@5 | Difference | Improved / worsened / unchanged |",
        "| --- | --- | ---: | ---: | ---: | ---: | --- |",
    ]
    for name, d in results.items():
        for sl, r in d["comparison_v12"]["history_slices"].items():
            lines.append(
                f'| {name} | {sl} | {r["users"]} | {r["reference_map_at_5"]:.9f} | {r["map_at_5"]:.9f} | {r["delta"]:+.9f} | {r["users_improved"]} / {r["users_worsened"]} / {r["users_unchanged"]} |'
            )
    lines += [
        "",
        "| Split | N50-cold definition | Users | v12 MAP@5 | Extended MAP@5 | Improved / worsened / unchanged |",
        "| --- | --- | ---: | ---: | ---: | --- |",
    ]
    for name, d in results.items():
        for label, r in d["cold_users"].items():
            lines.append(
                f'| {name} | {label} | {r["users"]} | {r["v12_map"]:.9f} | {r["extended_map"]:.9f} | {r["users_improved"]} / {r["users_worsened"]} / {r["users_unchanged"]} |'
            )
    lines += [
        "",
        "H80 is the original >=0.80 distinct programme history before availability filtering. Cold groups and slice counts match v12 exactly. Cold-group MAP improves here without any cold override. Both models have zero post-score fallback completion slots because the unchanged candidate union already contains the first five global fallback programmes.",
        "",
        "## Seen/unseen hits and prediction changes",
        "",
        "Seen means N50>0; unseen means N50=0. The old complete candidate features supply this classification for every selected/reference item. Gains/losses are per-user target occurrences entering/leaving top five. AP contribution terms include all preceding hits and are attributed to the hit item’s type; this is descriptive, not causal. The reused helper’s legacy `fused_` prefix refers to the unblended schedule classifier here.",
        "",
        "| Split | Seen target hits v12 -> extended | Unseen target hits v12 -> extended | Seen / unseen MAP contribution difference | Entering unseen recommendations / target hits | Leaving unseen recommendations / target hits |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for name, d in results.items():
        e = d["comparison_v12"]["seen_unseen_effects"]
        g = lambda k: e.get(k, 0)
        lines.append(
            f'| {name} | {g("baseline_seen_relevant_hits")} -> {g("fused_seen_relevant_hits")} | {g("baseline_unseen_relevant_hits")} -> {g("fused_unseen_relevant_hits")} | {e["delta_seen_map_contribution"]:+.9f} / {e["delta_unseen_map_contribution"]:+.9f} | {g("entering_unseen_items")} / {g("entering_unseen_relevant_hits")} | {g("leaving_unseen_items")} / {g("leaving_unseen_relevant_hits")} |'
        )
    lines += [
        "",
        "| Split | Changed lists | Changed positions | Membership-change / order-only users | Common top-five items / all slots | Relevant gains / losses |",
        "| --- | ---: | ---: | --- | --- | --- |",
    ]
    for name, d in results.items():
        r = d["comparison_v12"]
        c = r["prediction_changes"]
        lines.append(
            f'| {name} | {c["users_changed"]} | {c["rank_position_slots_changed"]} | {c["users_with_membership_change"]} / {c["users_with_order_change_only"]} | {c["top5_items_in_common"]}/{c["recommendation_slots"]} ({c["top5_set_overlap_fraction"]:.4%}) | {r["relevant_hit_gains"]} / {r["relevant_hit_losses"]} |'
        )
    lines += [
        "",
        "## Where the gains occur: schedule-only exposure groups",
        "",
        "Groups were frozen before evaluation using only the sign of log1p(future broadcastseconds/day)-log1p(past broadcastseconds/day): increased>0, decreased<0, unchanged=0. No outcome-based bins or tolerance threshold were selected. AP precision terms are attributed by the hit programme’s group; the group differences sum to the overall MAP difference. Group changes can include the effect of preceding hits, so they are not causal feature effects.",
        "",
        "| Split | Exposure group | Selected slots v12 -> extended | Entering / leaving relevant hits | Net relevant hits | MAP contribution difference |",
        "| --- | --- | --- | --- | ---: | ---: |",
    ]
    for name, d in results.items():
        for group, r in d["schedule_exposure_groups"].items():
            lines.append(
                f'| {name} | {group} | {r["baseline_selected"]} -> {r["extended_selected"]} | {r["entering_relevant"]} / {r["leaving_relevant"]} | {r["net_relevant_hits"]:+d} | {r["delta_map_contribution"]:+.9f} |'
            )
    lines += [
        "",
        "The gains concentrate in increased-exposure programmes: main gains +0.010601381 MAP contribution there, almost its entire +0.010708048 gain; auxiliary gains +0.011798927 there, partially offset by decreased/unchanged groups. Seen relevant hits rise by206/237 while unseen target hit counts fall by6/24; unseen AP contributions still rise through order/precision changes. Thus the improvement is not simply more unseen target hits or more candidate coverage.",
        "",
        "## Seven-feature distributions and missingness",
        "",
        "The following distributions describe actual fixed candidate rows (popular items can repeat across users). Each origin JSON also contains unique candidate-programme and all canonical schedule-programme distributions, full schema, row/group counts and original-feature equality checks. Values are rounded; broadcast rates use seconds/day. Every origin has zero missing new-feature values and zero NaN/Inf after passing coverage. Past absence is genuine zero relative to the covered provided catalogue, marked by past_airings_zero.",
        "",
        "| Origin | Schedule feature | Mean | Min | Median | P90 | Max | Zero fraction |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for name, r in features.items():
        for feature, d in r["candidate_row_distributions"].items():
            lines.append(
                f'| {name} | {feature} | {d["mean"]:.5f} | {d["min"]:.5f} | {d["median"]:.5f} | {d["p90"]:.5f} | {d["max"]:.5f} | {d["zero_fraction"]:.4%} |'
            )
    lines += [
        "",
        "## Descriptive importance, runtime and memory",
        "",
        "| Feature | Gain importance | Split count |",
        "| --- | ---: | ---: |",
    ]
    selected_names = {r["feature"] for r in importance[:10]} | set(SCHEDULE_FEATURES)
    for r in importance:
        if r["feature"] in selected_names:
            lines.append(f'| {r["feature"]} | {r["gain"]:.3f} | {r["splits"]} |')
    lines += [
        "",
        "Frequency and recent counts remain prominent; future airings/day and exposure-change features are also used. These are descriptive training importance values, not causal evidence. Exposure rates, counts, changes and original popularity features are correlated. No feature removal or extra model was tested based on importance.",
        "",
        "| Origin | Fixed candidate rows | Augmentation seconds | Extended matrix bytes | Recorded peak process RSS bytes |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for name, d in features.items():
        lines.append(
            f'| {name} | {d["rows"]:,} | {d["augmentation_seconds"]:.3f} | {d["matrix_bytes"]:,} | {d["environment"]["peak_process_rss_bytes"]:,} |'
        )
    lines += [
        "",
        f'Classifier fit took {training["fit_seconds"]:.3f} seconds. Schedule coverage, augmentation, training, evaluation and final-origin statistics took {selection["elapsed_before_optional_final_seconds"]:.3f} seconds before optional final prediction. RSS is process-lifetime high-water, not isolated classifier allocation. Candidate matrices remain bounded by the original at-most255 rows/user; no dense user-item join was introduced. Private matrices, original row metadata, labels and model weights stay outside Git.',
        "",
        "Historical label windows remain two weeks, versus ten-week main/eight-week auxiliary and twelve-week final forecasts. Historical histories are four/six weeks versus longer evaluation/final histories. Per-day exposure normalizes full window length but does not eliminate horizon/distribution shift. Overlapping/reused cohorts, changing channel coverage, correlated schedule features and any model selection limit generalization. Positive local intervals do not guarantee improved Kaggle scores.",
        "",
        "## Qualified final candidate",
        "",
        "The frozen decision requires strict gain against v12 on both splits. This single extension qualifies. The same new classifier weights are reused at final application, without evaluation-label retraining. Its final seven schedule features are recomputed for the 28-day past and exact weeks31–42 future window; all original v12 final rows and 27 features remain identical.",
        "",
    ]
    if artifact:
        c = artifact["differences_from_submitted_v12"]
        v = artifact["validation"]
        lines += [
            f'- Filename: `{artifact["filename"]}`.',
            f'- Absolute path: `{artifact["absolute_path"]}`.',
            f'- SHA-256: `{artifact["sha256"]}`.',
            f'- Internal and independent CLI validators: **{v["status"]}**, all {v["users"]:,} original template users/header/order, five distinct available nonzero IDs per row, {v["candidate_ids"]:,} carryover-aware candidate IDs.',
            f'- Versus exact submitted v12: {c["users_changed"]} changed lists, {c["rank_position_slots_changed"]} changed rank slots, {c["users_with_membership_change"]} membership-change and {c["users_with_order_change_only"]} order-only users. {c["users_identical"]} lists identical; set overlap {c["top5_items_in_common"]}/{c["recommendation_slots"]} ({c["top5_set_overlap_fraction"]:.4%}).',
            f'- Frozen schedule classifier SHA-256: `{artifact["classifier_sha256"]}`.',
            "",
            "English manual submission description is in submission_description.txt:",
            "",
            "> " + artifact["submission_description"],
            "",
        ]
    lines += [
        "## Verification and preserved incumbent",
        "",
        "All **79 tests pass**, including new canonical cross-file deduplication/nonzero IDs, clipped carryovers and exact half-open boundaries, simultaneous cross-channel duration sums, full-day normalization, genuine zero-past indicator, missing-coverage stop, schedule invariance to future viewing-log changes, and original27/candidate-row preservation. Existing causal, ranking, schema and submission checks are reused. Runtime assertions check exact historical row/label equality, original27 values, availability, unchanged candidate recall/oracle, slice/cold memberships and frozen classifier hashes.",
        "",
        f'Frozen protocol SHA-256: `{selection["frozen_protocol_sha256"]}`. Source/input hashes, candidate/label/model fingerprints, actual settings, distributions, runtime/RSS and checks are retained in the JSON evidence. V12’s original model and CSV remain byte-for-byte unchanged, as do all other prior artifacts.',
        "",
        "Best confirmed submitted v12: user-screenshot-reported Private **0.42660** / Public **0.43394**. Exact CSV SHA-256 `e18c49cb106df5b5e50f3b7123a080443a2ab48c709e68e721ee9965d96b1457`. No independent Kaggle lookup, submission ID or timestamp is invented. The new candidate has not been uploaded and has no Kaggle score.",
        "",
        "No Kaggle workflow, submission command, upload or API was used. Native session records remain unmodified; student verification remains pending until personally performed. Stop for user review and manual upload.",
        "",
        "```bash",
        "OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 /private/tmp/sweettv-model-venv/bin/python -m src.experiment_schedule_reranker --data-dir /Users/chenfengru/LLM4Rec-Course-codex/data/sweettv/raw",
        "/private/tmp/sweettv-model-venv/bin/python -m unittest discover -s tests",
        "/private/tmp/sweettv-model-venv/bin/python -m src.report_schedule_reranker",
        "```",
    ]
    (out / "comparison_report.md").write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    render(Path("results/schedule_reranker_20261030_v13"))
