"""Render exploratory two-stage adaptive-threshold evidence in English."""

import json
from pathlib import Path


def render(out):
    load = lambda p: json.loads(p.read_text())
    selection = load(out / "selection.json")
    first = {
        s: load(out / "stage1" / s / "comparison.json") for s in ["main", "auxiliary"]
    }
    second = (
        {s: load(out / "stage2" / s / "comparison.json") for s in first}
        if selection["stage1_selected"]
        else {}
    )
    artifact = (
        load(out / "candidate_artifact.json")
        if (out / "candidate_artifact.json").exists()
        else None
    )
    parent = selection["stage1_selected"]
    lines = [
        "# Exploratory history-adaptive thresholds and one E2 combination (executed)",
        "",
        "**S40+E2 qualifies under the frozen point-estimate rule and is prepared for manual review. The evidence against incumbent v9 is weak: gains are small, both paired intervals include zero, and the grouping hypothesis was derived from the same reused validation slices. Retain v9 as the best confirmed submitted model until a manual benchmark result is available.**",
        "",
        "## Exploratory scope and fixed definitions",
        "",
        "V10’s existing 1–5 history slice improved under both lower thresholds on both splits. That validation-informed observation motivated this experiment; the grouping is not an independently prespecified hypothesis. Both stages and selection rules were frozen before this run. Paired intervals are conditional on the reused cohorts, exclude grouping/configuration-selection uncertainty, and do not make the overlapping main/auxiliary windows independent tests.",
        "",
        "H80 is the number of distinct programmes with positive >=0.80-qualified pre-cutoff training user-airing counts, **before candidate-availability filtering**, exactly the original slice definition. Only users with 1<=H80<=5 adapt. S30 uses N30 for those users, S40 uses N40; all others use N50. V5 N50 is the Stage 1 control, with E2 disabled in all three lists. Original >=0.80 global viewer/airing popularity ties, raw string IDs and shared fallback remain unchanged.",
        "",
        "Stage 1 reuses v10 completed threshold lists and selects per user solely through training H80. Frozen cache hashes and source-slice scores reconcile; no audit, split count extraction, retrieval fitting or prior experiment was repeated. Main retains 4,625 users / 6,384 candidates, fit [2020-03-09,2020-05-18), validate [2020-05-18,2020-07-27). Auxiliary retains 4,589 / 5,742, fit [2020-03-09,2020-06-01), validate [2020-06-01,2020-07-27). Truth, original history slices, candidates and anchors stay fixed.",
        "",
        "## Stage 1: both adaptive-only configurations",
        "",
        "| Split | Model | Reference | MAP@5 | Paired difference | Conditional paired bootstrap 95% interval | Improved / worsened / unchanged AP users |",
        "| --- | --- | --- | ---: | ---: | --- | --- |",
    ]
    for split, d in first.items():
        for model, r in d["methods"].items():
            for ref, v in r["comparisons"].items():
                ci = v["paired_bootstrap_95pct"]
                lines.append(
                    f'| {split} | {model} | {ref} | {v["map_at_5"]:.12f} | {v["delta"]:+.12f} | [{ci[0]:+.9f}, {ci[1]:+.9f}] | {v["users_improved"]} / {v["users_worsened"]} / {v["users_unchanged"]} |'
                )
    lines += [
        "",
        "Each paired interval uses 2,000 user resamples, seed 42. Identical seeded user-index draws are reused for every evaluated comparison within a split. Whole-cohort intervals include unchanged users. These intervals are not adjusted for either stage of selection or for discovering the H80 grouping from v10.",
        "",
        "Both S30 and S40 strictly improve v5 on both splits. Their smaller split gains are +0.000367807808 and +0.000371531532 respectively. S40 wins the frozen max-min rule by only 0.000003723724; this is not convincing evidence that S40 is intrinsically better than S30. No exact tie-break was needed. Only S40 was subsequently combined with E2.",
        "",
        "S40 adaptive-only is below v9 on both splits and therefore cannot be the final candidate. S30 was not considered at the final stage after S40 selection; no S30+E2 model was evaluated.",
        "",
        "## Stage 2: the single predefined combination",
        "",
        "Build the completed S40 list, then use the unchanged original E2 helper. Eligibility requires ORIGINAL N50=1 for both its fourth and fifth programmes. Retrieval remains v7’s N50-based unseen-only direct top50 in its original order. Select the first available item absent from the **entire pre-replacement adaptive top five**. Unseen remains N50=0, even when an item has lower-threshold history. The adaptive first four positions are preserved. N30/N40 never replace N50 in E2 eligibility or unseen filtering.",
        "",
        "| Split | Model | Reference | MAP@5 | Paired difference | Conditional paired bootstrap 95% interval | Improved / worsened / unchanged AP users |",
        "| --- | --- | --- | ---: | ---: | --- | --- |",
    ]
    for split, d in second.items():
        for ref, v in d["comparisons"].items():
            ci = v["paired_bootstrap_95pct"]
            lines.append(
                f'| {split} | {d["method"]} | {ref} | {v["map_at_5"]:.12f} | {v["delta"]:+.12f} | [{ci[0]:+.9f}, {ci[1]:+.9f}] | {v["users_improved"]} / {v["users_worsened"]} / {v["users_unchanged"]} |'
            )
    lines += [
        "",
        "Existing v5 MAP@5 is 0.334711171171 main / 0.331395910511 auxiliary; existing v9 is 0.335652432432 / 0.332178216024. The combination improves its parent and v5 with positive conditional intervals, but its intervals against v9 include zero. In particular, main gain versus v9 is only +0.000052972973. This is an exploratory candidate, not established superiority over v9.",
        "",
        "## Adaptation, replacement and fallback usage",
        "",
        "| Split | Model | Adaptation-eligible users | E2-eligible users | Actual E2 replacements | Full / partial fallback users | Global fallback slots |",
        "| --- | --- | ---: | ---: | ---: | --- | ---: |",
    ]
    for split, d in first.items():
        for model, r in d["methods"].items():
            f = r["comparisons"]["v5"]["fallback"]
            lines.append(
                f'| {split} | {model} | {r["adaptation_eligible_users"]} | 0 | 0 | {f["complete_users"]} / {f["partial_users"]} | {f["completion_slots"]} |'
            )
        if split in second:
            r = second[split]
            f = r["comparisons"]["parent"]["fallback"]
            e = r["replacement_counts"]
            lines.append(
                f'| {split} | {r["method"]} | {d["methods"][parent]["adaptation_eligible_users"]} | {e["eligible_users"]} | {e["actual_replacements"]} | {f["complete_users"]} / {f["partial_users"]} | {f["completion_slots"]} |'
            )
    lines += [
        "",
        "V5/v9 global-fallback slots are 718 main and 598 auxiliary. Stage 1 fallback counts compose exactly from frozen v10 per-slice counts: the lower-threshold 1–5 slice plus N50 elsewhere. Stage 2 inherits those global-fallback counts unchanged: positive N50 at the fifth position implies a direct personal item under either threshold, so E2 never removes a global-fallback slot. Collaborative E2 insertions are direct retrieved items, not global fallback. All first-four and original-N50 E2 invariants are asserted per user.",
        "",
        "## Whole-cohort hit, membership and position changes",
        "",
        "| Stage | Split | Model | Reference | Relevant hit gains / losses | Net relevant hits | Changed lists / rank slots | Membership-change / order-only users | Top-five common items / all slots |",
        "| --- | --- | --- | --- | --- | ---: | --- | --- | --- |",
    ]

    def change_row(stage, split, model, ref, r):
        c = r["prediction_changes"]
        return f'| {stage} | {split} | {model} | {ref} | {r["relevant_hit_gains"]} / {r["relevant_hit_losses"]} | {r["net_relevant_hits"]:+d} | {c["users_changed"]} / {c["rank_position_slots_changed"]} | {c["users_with_membership_change"]} / {c["users_with_order_change_only"]} | {c["top5_items_in_common"]} / {c["recommendation_slots"]} ({c["top5_set_overlap_fraction"]:.4%}) |'

    for split, d in first.items():
        for model, r in d["methods"].items():
            for ref, v in r["comparisons"].items():
                lines.append(change_row(1, split, model, ref, v))
    for split, d in second.items():
        for ref, v in d["comparisons"].items():
            lines.append(change_row(2, split, d["method"], ref, v))
    lines += [
        "",
        "Relevant gains/losses count entering/leaving target items per user; retained hits can also move. Versus v9 the final combination has **12 fewer relevant top-five hits on main and 2 fewer on auxiliary**, despite slightly higher MAP. Thus the gain is due to the precision/order distribution, not greater net top-five hit count. More users worsen than improve against v9 on both splits. No conclusion of universal per-user benefit is supported.",
        "",
        "## Fixed-slice outcomes",
        "",
        "Original H80 membership is held fixed. Stage 1 comparisons below use v5; Stage 2 shows both its adaptive parent and incumbent v9. Slice comparisons against every other reported reference, including Stage 1 versus v9 and Stage 2 versus v5, are in the JSON evidence.",
        "",
        "| Stage | Split | Model | Reference | Slice | Users | MAP difference | Improved / worsened / unchanged | Relevant gains / losses | Changed lists / positions | Fallback slots |",
        "| --- | --- | --- | --- | --- | ---: | ---: | --- | --- | --- | ---: |",
    ]

    def slice_rows(stage, split, model, ref, result):
        for sl, r in result["history_slices"].items():
            c = r["prediction_changes"]
            lines.append(
                f'| {stage} | {split} | {model} | {ref} | {sl} | {r["users"]} | {r["delta"]:+.9f} | {r["users_improved"]} / {r["users_worsened"]} / {r["users_unchanged"]} | {r["relevant_hit_gains"]} / {r["relevant_hit_losses"]} | {c["users_changed"]} / {c["rank_position_slots_changed"]} | {r["fallback"]["completion_slots"]} |'
            )

    for split, d in first.items():
        for model, r in d["methods"].items():
            slice_rows(1, split, model, "v5", r["comparisons"]["v5"])
    for split, d in second.items():
        for ref in ["parent", "v9"]:
            slice_rows(2, split, d["method"], ref, d["comparisons"][ref])
    lines += [
        "",
        "Stage 1 predictions outside H80=1–5 exactly equal v5, including order. Stage 2 predictions outside that group exactly equal v9. All incremental changes against incumbent v9 therefore occur in the validation-informed adaptation slice.",
        "",
        "| Split | Original slice | E2 eligible / replacements | Inserted relevant / removed relevant versus parent |",
        "| --- | --- | --- | --- |",
    ]
    for split, d in second.items():
        for sl, r in d["replacement_slices"].items():
            lines.append(
                f'| {split} | {sl} | {r["eligible_users"]} / {r["actual_replacements"]} | {r["inserted_relevant"]} / {r["removed_relevant"]} |'
            )
    lines += [
        "",
        "## Frozen final selection and manual-review artifact",
        "",
        "Only selected S40 adaptive-only and its single S40+E2 combination were considered. A final candidate must strictly beat v9 on both splits, maximizing the smaller absolute gain and preferring adaptive-only on exact ties. Adaptive-only fails; S40+E2 qualifies. No tie-break was needed and no unselected E2 combination or extra grouping was tested.",
        "",
    ]
    if artifact:
        c = artifact["differences_from_submitted_v9"]
        v = artifact["validation"]
        lines += [
            f'- Filename: `{artifact["filename"]}`.',
            f'- Absolute path: `{artifact["absolute_path"]}`.',
            f'- SHA-256: `{artifact["sha256"]}`.',
            f'- Internal and separate CLI validation: **{v["status"]}**; all {v["users"]:,} template users in original order/header, five distinct available nonzero IDs per row, {v["candidate_ids"]:,} carryover-aware candidates.',
            f'- Final-template adaptation group: **{artifact["final_template_adaptation_eligible_users"]}** users. Final E2 eligibility/replacements: **{artifact["final_e2_eligible_users"]}/{artifact["final_e2_replacements"]}**.',
            f'- Versus submitted v9: **{c["users_changed"]}** changed lists, **{c["rank_position_slots_changed"]}** changed rank slots, {c["users_with_membership_change"]} users with changed membership and {c["users_with_order_change_only"]} order-only changes. {c["users_identical"]} lists identical; set overlap {c["top5_items_in_common"]}/{c["recommendation_slots"]} ({c["top5_set_overlap_fraction"]:.4%}).',
            "",
            "Counts and H80 were recomputed over the single canonical combined weeks11–30 fitting window, preserving full denominators and observed clipping. Split qualifications were not added. Selected lower counts, N50 and N80 were recomputed; the fixed N50 item-item model was fit once for E2. Final v5 and v9 were reproduced exactly before comparing the candidate. Predictions use weeks31–42 availability with carryovers. The first four are preserved relative to the **adaptive parent**, not necessarily relative to v9.",
            "",
            "Only 27 final-template users adapt, compared with 462/401 validation users. All changes from v9 are confined to that group. Different final training length and template population limit transfer of the small exploratory gains. The file is a valid candidate under the frozen rule; evidence does not establish reliable Kaggle improvement. Retain v9 as incumbent until manual benchmarking provides a new result.",
            "",
            "English manual submission description is saved in submission_description.txt:",
            "",
            "> " + artifact["submission_description"],
            "",
        ]
    lines += [
        "## Verification and provenance",
        "",
        "All **68 tests pass**. New checks cover H80 boundaries0/1/5/6, distinct qualified programmes before availability filtering, per-user lower/N50 count and cached-list choice, identical outside-group Stage 1 predictions, training-only H80 invariance under post-cutoff qualified rows, and original-N50 E2 eligibility/unseen behaviour even when lower-threshold counts disagree. Existing cutoff, interval, ranking, retrieval, replacement and submission checks are reused.",
        "",
        "Runtime checks verify frozen cache hashes, source slice scores, original anchors, exact v5/v9 references, per-user Stage 1 outside-group equality, Stage 2 adaptive-prefix preservation, original N50 eligibility, highest candidate in original retrieval order and exclusion of the entire adaptive top five. Private user-level predictions stay outside Git. Original truth files and all previous CSVs/checksums are preserved.",
        "",
        f'Frozen protocol SHA-256: `{selection["frozen_protocol_sha256"]}`. Stage execution/selection took {selection["elapsed_stages_seconds"]:.3f} seconds. Exact inputs/source hashes, cache fingerprints, base commit, dependencies, timings and process-lifetime RSS are recorded in the JSON evidence.',
        "",
        "Submitted v9 SHA-256 remains `f1378b0d6fed62793e14ebb4c1b64cf8b2163485485c15c861aae7e67e556375`. Private0.40261/Public0.41871 are user-screenshot-reported; no independent Kaggle lookup, submission ID or timestamp is invented. The new file has no Kaggle result.",
        "",
        "No Kaggle workflow, submission command, upload or submission API was used. Native session records remain unmodified; student verification is pending until personally performed. Stop for user review and manual upload.",
        "",
        "```bash",
        "OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 /private/tmp/sweettv-model-venv/bin/python -m src.experiment_adaptive_threshold --data-dir /Users/chenfengru/LLM4Rec-Course-codex/data/sweettv/raw",
        "/private/tmp/sweettv-model-venv/bin/python -m unittest discover -s tests",
        "/private/tmp/sweettv-model-venv/bin/python -m src.report_adaptive_threshold",
        "```",
    ]
    (out / "comparison_report.md").write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    render(Path("results/adaptive_threshold_20261030_v11"))
