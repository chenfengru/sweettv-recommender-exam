"""English evidence for the frozen lower-threshold-only experiment."""

import json
from pathlib import Path


def render(out):
    load = lambda p: json.loads(p.read_text())
    data = {
        split: load(out / split / "comparison.json") for split in ["main", "auxiliary"]
    }
    noise = {split: load(out / split / "new_airing_durations.json") for split in data}
    selection = load(out / "selection.json")
    lines = [
        "# Lower personal-viewing thresholds, without E2 (executed)",
        "",
        "**Retain submitted v9 E2. Neither threshold qualifies against the 0.50 threshold-only control on both splits. No final fit or new prediction CSV was generated. No threshold/E2 combination was tested.**",
        "",
        "## Frozen question and control",
        "",
        "Exactly t=0.30 and 0.40 were tested against 0.50. N_t counts canonical pre-cutoff user-airings whose longest merged observed viewing block covers at least t of the full original airing duration. Ranking is descending N_t, then unchanged original >=0.80 distinct global training viewers, total qualified user-airings and ascending raw string programme ID. Shared fallback remains original >=0.80 popularity. E2 and collaborative retrieval are disabled for every threshold, including 0.50.",
        "",
        "Reuse original interval unions, canonical deduplication, full airing denominators, causal cleaning and observed-end clipping. Main remains 4,625 users/6,384 candidates, fit[2020-03-09,2020-05-18), validate[2020-05-18,2020-07-27); auxiliary remains 4,589/5,742, fit[2020-03-09,2020-06-01), validate[2020-06-01,2020-07-27). Truth stays >=0.80. Original >=0.80 history-size membership, candidates, global tie keys and fallback order are fixed. No audit or previously completed experiment was repeated.",
        "",
        "N50 was extracted alongside the new thresholds and exactly matched its saved checksummed v7 count cache; completed 0.50 lists exactly matched saved v5 predictions. Original frozen anchor hashes and truth-file hashes reconcile. An optional observer on the established count extractor records duration statistics without changing qualification or ranking.",
        "",
        "## Threshold-only MAP@5 comparison",
        "",
        "| Split | Personal threshold, E2 off | MAP@5 | Paired difference from0.50 | Paired bootstrap95% interval | Improved / worsened / unchanged AP users |",
        "| --- | ---: | ---: | ---: | --- | --- |",
    ]
    for split, d in data.items():
        for t in ["0.5", "0.3", "0.4"]:
            r = d["results"][t]
            ci = r.get("paired_bootstrap_95pct")
            interval = f"[{ci[0]:+.9f}, {ci[1]:+.9f}]" if ci else "reference"
            outcomes = (
                f'{r["users_improved"]} / {r["users_worsened"]} / {r["users_unchanged"]}'
                if ci
                else "reference"
            )
            lines.append(
                f'| {split} | {t} | {r["map_at_5"]:.12f} | {r.get("delta_from_050",0):+.12f} | {interval} | {outcomes} |'
            )
    lines += [
        "",
        "Bootstrap: 2,000 paired-user resamples, seed 42, shared user draws across the two thresholds within each split. Intervals are **conditional on reused cohorts and exclude configuration-selection uncertainty**. The splits overlap in time and users and are not independent untouched tests. All four intervals include zero. The point estimates fail the frozen two-split eligibility rule; they do not establish a general statistically certain disadvantage of every lower threshold.",
        "",
        "## Submitted v9: separate context, not the control",
        "",
        "| Split | Previously measured v9 E2 MAP@5 |0.30 minus v9|0.40 minus v9|",
        "| --- | ---: | ---: | ---: |",
    ]
    for split, d in data.items():
        lines.append(
            f'| {split} | {d["v9_e2_existing_local_score_context_only"]:.12f} | {d["results"]["0.3"]["difference_from_v9_context_only"]:+.12f} | {d["results"]["0.4"]["difference_from_v9_context_only"]:+.12f} |'
        )
    lines += [
        "",
        "These v9 scores are read from completed E2 evidence, not rerun. Both new threshold-only models are below v9 on both splits. Even a threshold beating v5 alone would not establish superiority to v9; E2 is a different controlled factor. Any combination remains a separate future experiment.",
        "",
        "## Qualifying counts, personal candidates and coverage",
        "",
        "Counts below are canonical user-airing occurrences, not unique broadcast airings. User-item pairs are distinct positive-count user/programme pairs. “Cohort candidate pairs” restricts users to the frozen cohort and programmes to the fixed available pool. Macro coverage averages |relevant intersect personal history|/|relevant| by user; micro sums covered relevant pairs over all relevant pairs. All targets are available and distinct. Enlarged candidate coverage alone is not ranking evidence.",
        "",
        "| Split | Threshold | Qualified user-airings (change)| Training user-item pairs (change)| Available training pairs | Cohort candidate pairs (change)| Mean available history | Users gaining usable history |",
        "| --- | ---: | --- | --- | ---: | --- | ---: | ---: |",
    ]
    for split, d in data.items():
        base = d["results"]["0.5"]["personal_history_coverage"]
        for t in ["0.5", "0.3", "0.4"]:
            r = d["results"][t]
            c = r["personal_history_coverage"]
            difference = lambda key: f"{c[key]:,} ({c[key]-base[key]:+,})"
            lines.append(
                f'| {split} | {t} | {difference("all_training_qualified_user_airings")} | {difference("all_training_user_item_pairs")} | {c["available_training_user_item_pairs"]:,} | {difference("available_personal_candidate_pairs")} | {c["mean_available_history_size"]:.3f} | {r.get("users_gaining_usable_history",0)} |'
            )
    lines += [
        "",
        "| Split | Threshold | Relevant pairs covered / all relevant | Micro coverage | Macro coverage | Newly covered relevant pairs | Full / partial fallback users | Fallback slots |",
        "| --- | ---: | --- | ---: | ---: | ---: | --- | ---: |",
    ]
    for split, d in data.items():
        for t in ["0.5", "0.3", "0.4"]:
            r = d["results"][t]
            c = r["personal_history_coverage"]
            f = r["fallback"]
            lines.append(
                f'| {split} | {t} | {c["relevant_pairs_covered"]:,} / {c["relevant_pairs_total"]:,} | {c["micro"]:.4%} | {c["macro"]:.4%} | {r.get("newly_covered_relevant_pairs",0)} | {f["complete_users"]} / {f["partial_users"]} | {f["completion_slots"]} |'
            )
    lines += [
        "",
        "Global fallback ordering is frozen, but usage may fall as more personal programmes qualify. Coverage expands monotonically; this does not imply better ordered predictions.",
        "",
        "## Top-five changes and relevant hits",
        "",
        "| Split | Threshold | Changed lists | Changed rank slots | Membership-change users | Order-only users | Top-five common items / slots |",
        "| --- | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for split, d in data.items():
        for t in ["0.3", "0.4"]:
            c = d["results"][t]["prediction_changes"]
            lines.append(
                f'| {split} | {t} | {c["users_changed"]} | {c["rank_position_slots_changed"]} | {c["users_with_membership_change"]} | {c["users_with_order_change_only"]} | {c["top5_items_in_common"]}/{c["recommendation_slots"]} ({c["top5_set_overlap_fraction"]:.4%}) |'
            )
    lines += [
        "",
        "| Split | Threshold | Entering relevant top-five hits | Leaving relevant top-five hits | Net hits | Entering relevant hits from newly covered personal history |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for split, d in data.items():
        for t in ["0.3", "0.4"]:
            r = d["results"][t]
            lines.append(
                f'| {split} | {t} | {r["top5_relevant_hit_gains"]} | {r["top5_relevant_hit_losses"]} | {r["net_top5_relevant_hit_change"]:+d} | {r["gained_top5_relevant_from_new_personal_history"]} |'
            )
    lines += [
        "",
        "Entering/leaving relevant hits compare membership with the exact0.50 top five; counts are per-user occurrences. Newly covered relevant histories count retrieval availability, while entering relevant hits require a new top-five recommendation. Reordering retained hits also changes AP. For example 0.30 adds 684/655 relevant candidate pairs but nets only+6/-30 top-five hits and lowers MAP on both splits. At 0.40 auxiliary net hits are zero but MAP is slightly lower, showing the role of positions.",
        "",
        "## Fixed original history-size slices",
        "",
        "The slices remain based on >=0.80 distinct training programmes before availability filtering. Lower thresholds do not move users between slices. Complete slice coverage/fallback/user-outcome/membership/hit statistics are in comparison.json.",
        "",
        "| Split | History size | Users |0.50 MAP|0.30 MAP (difference)|0.40 MAP (difference)|",
        "| --- | --- | ---: | ---: | --- | --- |",
    ]
    for split, d in data.items():
        for sl in ["0", "1–5", "6–20", "21+"]:
            b = d["results"]["0.5"]["history_slices"][sl]
            a = d["results"]["0.3"]["history_slices"][sl]
            c = d["results"]["0.4"]["history_slices"][sl]
            lines.append(
                f'| {split} | {sl} | {b["users"]} | {b["map_at_5"]:.9f} | {a["map_at_5"]:.9f} ({a["delta_from_050"]:+.9f}) | {c["map_at_5"]:.9f} ({c["delta_from_050"]:+.9f}) |'
            )
    lines += [
        "",
        "## Newly included duration summaries and possible short-viewing noise",
        "",
        "For each threshold, newly included means t<=longest-block fraction<0.50. The 0.40 group is contained in the0.30 group; **do not add their counts**. Statistics are weighted by canonical user-airing occurrences, not unique programmes/broadcasts. Viewing duration is reported both as the longest merged observed block (qualification quantity) and the total observed interval union. The latter may exceed the longest block when viewing is disconnected. All times are seconds; fractions are unitless. These are full-data descriptive quantiles with linear interpolation, rounded below; full precision is in new_airing_durations.json.",
        "",
        "| Split | Threshold | Measure, all training newly included | Count | Mean | Min | P10 | Median | P90 | P95 | Max |",
        "| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for split, groups in noise.items():
        for t in ["0.3", "0.4"]:
            for name, s in groups[t]["all_training"].items():
                label = name.replace("_", " ")
                lines.append(
                    f'| {split} | {t} | {label} | {s["count"]:,} | '
                    + " | ".join(
                        f"{s[k]:.3f}"
                        for k in ["mean", "min", "p10", "median", "p90", "p95", "max"]
                    )
                    + " |"
                )
    lines += [
        "",
        "The same summaries restricted to available programme/user pairs in the frozen cohort are also in the JSON; their medians are shown below.",
        "",
        "| Split | Threshold | Newly included available cohort user-airings | Median full airing seconds | Median longest observed block seconds | Median total observed union seconds | Median fraction |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for split, groups in noise.items():
        for t in ["0.3", "0.4"]:
            s = groups[t]["available_cohort"]
            lines.append(
                f'| {split} | {t} | {s["full_airing_seconds"]["count"]:,} | {s["full_airing_seconds"]["median"]:.3f} | {s["longest_observed_block_seconds"]["median"]:.3f} | {s["total_observed_union_seconds"]["median"]:.3f} | {s["longest_block_fraction"]["median"]:.3f} |'
            )
    lines += [
        "",
        "The newly admitted 0.30 group includes observed blocks as short as 54 seconds, but its median is about 32 minutes on both splits. The 0.40 group starts at 72 seconds and has medians about36–37 minutes. Thus these are not uniformly brief visits. Lower relative thresholds can admit more weak or incidental evidence, especially for short airings, but these summaries do not identify user intent or prove that noise caused the observed MAP changes. Longer partial views can also be useful. No extra duration gate or threshold was tested.",
        "",
        "## Decision, reproducibility and score provenance",
        "",
        "Eligibility requires strictly positive MAP gain over the 0.50 control on both splits. Among eligible thresholds maximize the minimum absolute gain, exact tie toward0.40. No threshold qualifies: 0.30 is negative on both; 0.40 has mixed signs. Retain submitted v9. No final threshold-only fit, candidate CSV, validator run for a new candidate or E2 combination was generated. This round does not support submitting either threshold-only configuration.",
        "",
        "All 64 tests pass. New checks verify exact 0.30/0.40/0.50 boundaries, monotonic qualified-airing inclusion, canonical duplicate and disconnected-union behavior, unchanged 0.50 counts with an observer, cutoff-clipped observer values and full denominators. Existing temporal, ranking and submission regressions are reused. Runtime checks reconcile cached 0.50 counts/predictions, fixed anchors/truth, monotonic counts and equality of added counts with duration-summary sample counts.",
        "",
        f'Frozen protocol SHA-256: `{selection["frozen_protocol_sha256"]}`. Full comparisons, duration summaries, bootstrap and selection took {selection["elapsed_comparison_seconds"]:.3f} seconds. Peak process RSS: {selection["environment"]["peak_process_rss_bytes"]:,} bytes (process-lifetime high-water, including cached interactions and diagnostic arrays). Exact inputs/source hashes, base commit, dependency versions, cache manifests and timings appear in the JSON evidence.',
        "",
        "Best confirmed submitted v9 file: `submissions/candidate_personal_fifth_e2_20261030_v9.csv`; SHA-256 `f1378b0d6fed62793e14ebb4c1b64cf8b2163485485c15c861aae7e67e556375`. Private **0.40261** / Public **0.41871** are **user-screenshot-reported** in the current request; no independent Kaggle lookup. Screenshot binary was not supplied for this run. Submission ID and submission timestamp remain unknown and are not invented; evidence recording time is not a submission timestamp. V5’s exact file/checksum and every other previous artifact are also preserved.",
        "",
        "No Kaggle workflow, submission command, upload or API was used. Native session records are unmodified; student verification remains pending until personally performed. Stop for user review. Any future E2 combination requires a separately controlled experiment.",
        "",
        "```bash",
        "OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 /private/tmp/sweettv-model-venv/bin/python -m src.experiment_lower_threshold --data-dir /Users/chenfengru/LLM4Rec-Course-codex/data/sweettv/raw",
        "/private/tmp/sweettv-model-venv/bin/python -m unittest discover -s tests",
        "/private/tmp/sweettv-model-venv/bin/python -m src.report_lower_threshold",
        "```",
    ]
    (out / "comparison_report.md").write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    render(Path("results/lower_threshold_20261030_v10"))
