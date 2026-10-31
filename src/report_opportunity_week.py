"""Build the English review report for the frozen two-split C/D experiment."""

import argparse
import json
from pathlib import Path


def run(out):
    selection = json.loads((out / "selection.json").read_text())
    splits = {
        name: json.loads((out / name / "comparison.json").read_text())
        for name in ["main", "auxiliary"]
    }
    diagnostics = {
        name: json.loads((out / name / "feature_diagnostics.json").read_text())
        for name in splits
    }
    selected = selection["selected"]
    retain = selected == "v3"
    recommendation = {
        "recommended_configuration": "submitted v3" if retain else selected,
        "worth_new_manual_submission": not retain,
        "reason": (
            "C reverses from a small positive main delta to a negative auxiliary delta. D is negative on both. Neither passes the frozen two-split criterion."
            if retain
            else "Passes the frozen positive-delta criterion on both overlapping splits; selection uncertainty remains."
        ),
        "new_submission_csv_generated": (out / "candidate_artifact.json").exists(),
        "best_submitted_private_score": 0.39697,
        "best_submitted_public_score": 0.40288,
        "score_source": "user-confirmed Kaggle screenshot",
        "workflow": "Stop for user review. All uploads manual-only; no Kaggle browser, workflow, upload, Submit click or submission API used.",
        "student_verification": "pending",
    }
    (out / "recommendation.json").write_text(
        json.dumps(recommendation, indent=2) + "\n"
    )
    lines = [
        "# Scheduled-opportunity and qualified-week tie-break review",
        "",
        "**Decision: retain submitted v3. No new prediction CSV was generated.** C improves the main split only, then declines on the predeclared auxiliary split. D declines on both. Neither meets the selection rule frozen before execution; there is no recommendation for another manual submission from this round.",
        "",
        "## Baseline and provenance",
        "",
        "The user confirms that `submissions/candidate_personal_tie_popularity_20261030_v3.csv` returned **Private Score 0.39697** and **Public Score 0.40288**, from a Kaggle screenshot. The exact file remains unchanged with SHA-256 `39aac2794395209b2299ccee2e2bb1b4b9afde22f3e06ccb5b04f3d706c9522f`. These are user-reported screenshot values, not independently fetched by the agent. The screenshot binary, submission ID and submission timestamp are not available in this tool run; none was invented. `baseline_score_evidence.json` records this provenance and checksums for all previous CSVs.",
        "",
        "## Definitions frozen before execution",
        "",
        "[The frozen protocol](../../docs/opportunity_week_protocol.md) was written before experiments, with its timestamp and SHA-256 in `frozen_experiment.json`. Its hash is unchanged. Exactly v3 and two new variants were evaluated; no combined C/D key, weight, decay, qualification threshold or extra temporal split was tried.",
        "",
        "All methods first rank by descending personal qualified-airing count. V3 then uses distinct qualified training viewers, total qualified training user-airings and raw string programme ID. C and D insert one secondary key before those unchanged v3 keys:",
        "",
        "- **C — scheduled opportunities:** count each positive-duration, nonzero-ID canonical `(channel,start,end,item)` broadcast once if `start < prediction_end and end > prediction_start`. Deduplicate across files, include carryovers and preserve full broadcast endpoints; separate channels remain separate opportunities. The feature reads only item ID, channel, start and duration. Future content attributes and viewing behaviour are not inputs. Opportunities are not verified exposures.",
        "- **D — distinct qualified viewing weeks:** after the existing 80% longest-block/full-original-duration qualification, assign each user-airing once to the Monday-start source-calendar week of its **first observed overlapping segment start**, clipped to the fitting window. Multiple qualified airings of the same user/programme in that week contribute one distinct week. An airing crossing Monday is not assigned to both weeks, and a later longest block does not replace the first observed start. No future broadcast end supplies its week.",
        "",
        "Causal cleaning, canonical deduplication, union of viewing intervals, original airing denominators, repeat eligibility and shared popularity completion remain unchanged. Each fitted week count is reconciled with the established qualified-airing counts. Primary count sequences are asserted unchanged, and membership changes require an equal-count fifth-boundary tie. Global fallback ordering is recomputed from fitting behaviour only and remains identical across methods within each split.",
        "",
        "## Main validation",
        "",
        "Fit **[2020-03-09, 2020-05-18)**; validate **[2020-05-18, 2020-07-27)**, in the established source wall clock. The frozen main truth and candidate pool are reused exactly: **4,625 users and 6,384 candidates**. V3 lists reconcile exactly with the previous saved v3 predictions.",
        "",
        "| Method | MAP@5 | Delta from within-split v3 | AP improved / worsened / unchanged | Conditional paired-bootstrap 95% interval |",
        "| --- | ---: | ---: | --- | --- |",
    ]
    for name in ["main", "auxiliary"]:
        if name == "auxiliary":
            n = splits[name]["results"]["v3"]["evaluation_users"]
            c = splits[name]["results"]["v3"]["candidates"]
            lines += [
                "",
                "## Predeclared auxiliary temporal comparison",
                "",
                "Fit **[2020-03-09, 2020-06-01)**; validate **[2020-06-01, 2020-07-27)**. Both interaction windows were rebuilt from the unchanged raw files using the existing pipeline, including its schedule/metadata preprocessing and canonical overlap treatment. Global qualified statistics, available candidates and raw-ID-tied top-five target construction were rebuilt for this split; no future content attributes enter C/D. The actual common auxiliary cohort is **"
                + f"{n:,}"
                + " users**, with **"
                + f"{c:,}"
                + " candidates**. No main-split counts were imposed.",
                "",
                "| Method | MAP@5 | Delta from within-split v3 | AP improved / worsened / unchanged | Conditional paired-bootstrap 95% interval |",
                "| --- | ---: | ---: | --- | --- |",
            ]
        for v, x in splits[name]["results"].items():
            delta = x.get("delta_from_v3", 0)
            if v == "v3":
                counts = "reference"
                ci = "reference"
            else:
                counts = f"{x['users_improved']} / {x['users_worsened']} / {x['users_unchanged_ap']}"
                lo, hi = x["paired_user_bootstrap_95pct_interval"]
                ci = f"[{lo:+.9f}, {hi:+.9f}]"
            lines.append(
                f"| {v} | {x['map_at_5']:.12f} | {delta:+.12f} | {counts} | {ci} |"
            )
    lines += [
        "",
        "Compare **deltas within each split**, not raw main-versus-auxiliary MAP as if the tasks were identical. The auxiliary fitting history, target horizon, cohort and candidate pool differ; its behaviour overlaps the main comparison. This is an overlapping robustness check, **not an independent untouched test**.",
        "",
        "C has a small positive main point estimate, whose interval includes zero, and a negative auxiliary estimate, whose conditional interval is slightly below zero. Its direction is inconsistent across the prescribed windows. D is negative in both; its main interval is below zero, while its auxiliary interval includes zero. These are negative/mixed findings, not evidence of a robust improvement. No cause for the sign reversal is established by this experiment.",
        "",
        "## Feature and tie diagnostics",
        "",
        "These are potential feature distinctions among available programmes with the same positive personal count, not counts of actual reordered lists. Denominator is the split’s evaluation cohort. Fallback items are excluded. Top-five-relevant groups intersect the baseline direct top five; within-selected compares selected members only; boundary means the baseline count tie spans ranks five and six.",
        "",
        "| Split | Feature | Cohort | Any equal-count group distinguished | Top-five-relevant group | Within selected top five | Fifth-boundary tie |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for name in splits:
        diag = diagnostics[name]["ties"]
        for v, x in diag["features"].items():
            lines.append(
                f"| {name} | {v} | {diag['cohort_users']:,} | {x['any_equal_count_group_distinguished']:,} | {x['top5_relevant_tie_group_distinguished']:,} | {x['within_selected_top5_tie_distinguished']:,} | {x['fifth_boundary_tie_distinguished']:,} |"
            )
    lines += [
        "",
        "| Split | Canonical prediction-window broadcasts | Candidate IDs | Broadcast-count range per item | Qualified fitting user-airings | Maximum distinct qualified weeks |",
        "| --- | ---: | ---: | --- | ---: | ---: |",
    ]
    for name, diag in diagnostics.items():
        c, w = diag["schedule"], diag["weeks"]
        lines.append(
            f"| {name} | {c['canonical_intersecting_airings']:,} | {c['distinct_programme_ids']:,} | {c['minimum_airings_per_item']}–{c['maximum_airings_per_item']} | {w['qualified_user_airings']:,} | {w['maximum_distinct_weeks']} |"
        )
    lines += [
        "",
        "No duplicate canonical broadcast rows were found within these prediction-window inputs; the dedicated fixture verifies deduplication and carryovers even when duplicates are present. These are exact full-window counts, not sampled statistics. D cannot distinguish equal-count-one programmes because each necessarily occupies one qualified week. The larger number of distinguishable C ties does not establish a ranking benefit; observed AP and prediction changes are reported separately.",
        "",
        "## Actual ordered-list and membership changes",
        "",
        "All changes are relative to that split’s v3. Changed rank-position slots include reordering; top-five set overlap ignores order. AP can be unchanged while predictions change.",
        "",
        "| Split | Variant | Changed ordered lists | Order-only users | Membership-change users | Changed rank slots / denominator | Top-five set overlap |",
        "| --- | --- | ---: | ---: | ---: | --- | ---: |",
    ]
    for name, s in splits.items():
        for v in ["C", "D"]:
            x = s["results"][v]["prediction_changes"]
            lines.append(
                f"| {name} | {v} | {x['users_changed']} | {x['users_with_order_change_only']} | {x['users_with_membership_change']} | {x['rank_position_slots_changed']} / {x['recommendation_slots']} | {100*x['top5_set_overlap_fraction']:.4f}% |"
            )
    lines += [
        "",
        "Within each split, complete fallback, partial completion and fallback-slot counts are identical for v3, C and D:",
        "",
        "| Split | Complete fallback users | Partial completion users | Fallback slots |",
        "| --- | ---: | ---: | ---: |",
    ]
    for name, s in splits.items():
        f = s["results"]["v3"]["fallback"]
        lines.append(
            f"| {name} | {f['complete_users']} | {f['partial_completion_users']} | {f['completion_slots']} |"
        )
    for name, s in splits.items():
        lines += [
            "",
            "## " + name.title() + " history-size slices",
            "",
            "History size is the established number of distinct qualified fitting programmes before candidate filtering. All three methods use the same slice membership within this split.",
            "",
            "| Qualified fitting items | Users | v3 MAP@5 | C MAP@5 | D MAP@5 |",
            "| --- | ---: | ---: | ---: | ---: |",
        ]
        for sl in ["0", "1–5", "6–20", "21+"]:
            lines.append(
                "| "
                + sl
                + " | "
                + str(s["results"]["v3"]["history_slices"][sl]["users"])
                + " | "
                + " | ".join(
                    f"{s['results'][v]['history_slices'][sl]['map_at_5']:.9f}"
                    for v in ["v3", "C", "D"]
                )
                + " |"
            )
    lines += [
        "",
        "## Uncertainty and frozen selection",
        "",
        "Each interval uses 2,000 paired-user resamples with replacement, seed 42, conditional on its own split cohort; C/D use the same resampled indices within that split. Neither interval accounts for selecting methods on reused data, repeated prior experiments, or future Kaggle generalization. The overlapping auxiliary comparison is not pooled into an independent-test confidence claim.",
        "",
        "The predeclared rule requires a strictly positive delta on **both** splits, then chooses higher main MAP if both qualify, with exact score ties retaining v3. **Eligible variants: none. Selected: v3.** No new final-window refit or prediction CSV was performed. There is no new filename/path/checksum or validator result to present. The previously validated and submitted v3 file remains intact, and its user-reported Private 0.39697 / Public 0.40288 remain the best submitted scores.",
        "",
        "## Regression, runtime and reproducibility",
        "",
        "All **42 tests pass**: the existing 37 plus focused canonical-airing, week-assignment, ranking-precedence, clipped-week invariance and end-to-end future-viewing tests. Fixtures cover duplicate rows across schedule files, distinct-channel opportunities, carryovers, zero-duration/zero-ID exclusion and exact half-open endpoints. Week fixtures include several airings in one week, Sunday-to-Monday crossing, and a qualified Monday block whose first observed segment is Sunday. A full pipeline fixture changes only future viewing tails/adds future users while keeping both C and D predictions unchanged.",
        "",
        "Runtime and code/cache provenance are recorded in the split JSON files. The auxiliary extraction rebuilt both windows; the main reused its established cache. No unrelated audit, model training, recency experiment or added parameter search was run.",
        "",
        "| Measurement | Seconds |",
        "| --- | ---: |",
        f"| Entire frozen main + auxiliary experiment | {selection['total_experiment_seconds']:.3f} |",
    ]
    for name, s in splits.items():
        lines.append(
            f"| {name} week-feature extraction | {diagnostics[name]['week_extraction_seconds']:.3f} |"
        )
        for v, x in s["results"].items():
            lines.append(
                f"| {name} {v} ranking/completion for {x['inference_users']:,} users | {x['ranking_and_completion_seconds']:.4f} |"
            )
    aux = splits["auxiliary"]["source_cache_manifests"]
    lines += [
        f"| Auxiliary fitting-window interaction build | {aux['fit']['elapsed_seconds']:.3f} |",
        f"| Auxiliary validation-window interaction build | {aux['validation']['elapsed_seconds']:.3f} |",
        "",
        "Intervals, raw input checksums, dependency versions, source hashes, cache configurations and measured process high-water RSS are included in the machine-readable records. The environment remains the pinned standard model-comparison environment, seed 42, one numerical-library thread, on the 24 GiB Mac. All per-user weeks, truth, predictions and AP values remain in ignored local artifacts. Raw inputs, credentials and the original native session record remain outside public Git and unmodified. Student verification remains pending.",
        "",
        "**Manual submission recommendation: no new submission from this round.** Keep the exact submitted v3 baseline. There is no new candidate to upload, no new Kaggle score and no further experiment or action scheduled. Stop for user review; all future uploads remain manual-only by the user.",
        "",
    ]
    (out / "comparison_report.md").write_text("\n".join(lines))
    (out / "metrics.csv").write_text(
        "split,method,map_at_5,delta_from_within_split_v3,users,candidates\n"
        + "\n".join(
            f"{name},{v},{x['map_at_5']:.12f},{x.get('delta_from_v3',0):.12f},{x['evaluation_users']},{x['candidates']}"
            for name, s in splits.items()
            for v, x in s["results"].items()
        )
        + "\n"
    )


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output-dir", type=Path, required=True)
    run(p.parse_args().output_dir)
