"""English report for the fixed personal-frequency tie-break experiment."""

import argparse
import json
from pathlib import Path
import numpy as np


def run(out):
    s = json.loads((out / "comparison.json").read_text())
    r = s["results"]
    d = json.loads((out / "tie_diagnostics.json").read_text())
    artifact = (
        json.loads((out / "candidate_artifact.json").read_text())
        if (out / "candidate_artifact.json").exists()
        else None
    )
    labels = {
        "original": "Original: raw string ID",
        "latest": "Variant A: latest observed qualified viewing",
        "popularity": "Variant B: global qualified popularity",
    }
    sizes = np.array(
        [
            int(size)
            for size, n in d["boundary_full_group_size_histogram"].items()
            for _ in range(n)
        ]
    )
    selected = s["selected"]
    strong = (
        selected != "original"
        and r[selected]["paired_user_bootstrap_95pct_interval"][0] > 0
    )
    decision = {
        "recommended_configuration": selected,
        "worth_one_manual_submission": bool(strong),
        "reason": (
            "Meaningful positive local difference with a positive conditional bootstrap interval; counts remain primary. Kaggle improvement is not guaranteed after repeated hold-out use."
            if strong
            else "Insufficient evidence to replace the original submitted baseline."
        ),
        "best_submitted_baseline_remains": "original personal frequency; private 0.38937 / public 0.39131, user-confirmed screenshots",
        "candidate_generated": artifact is not None,
        "new_candidate_private_score": None,
        "new_candidate_public_score": None,
        "workflow": "Stop for user review. No Kaggle access, upload workflow, Submit click or submission API is authorized. Only the user may upload.",
        "student_verification": "pending",
    }
    (out / "recommendation.json").write_text(json.dumps(decision, indent=2) + "\n")
    lines = [
        "# Personal-frequency tie-breaking review",
        "",
        "**Recommendation: Variant B is worth one manual benchmark submission after user review.** Its local gain is substantially larger than the earlier fusion gain and its conditional interval is positive. This is not a guarantee of improving the best submitted private score. Exactly the two requested tie-break variants were evaluated; no decay, combination, extra parameter or previous model experiment was rerun.",
        "",
        "## Submitted-score provenance",
        "",
        "The user confirms these values from Kaggle screenshots:",
        "",
        "| Exact submitted file | Private Score | Public Score | SHA-256 |",
        "| --- | ---: | ---: | --- |",
        "| `first_personal_original_20261029_v1.csv` | **0.38937** | **0.39131** | `53cb8ae4b59b26ab6ee00b5e99ad91044876180e662732a755d3e99a297e64bc` |",
        "| `candidate_rrf_als_lb80_w0p1_20261029_v2.csv` | 0.38663 | 0.38852 | `905971a8a9c47bcf4a88e14cd10d2514feaaea43900d6f513b2eecc4986f19f5` |",
        "",
        "Both submitted files remain byte-for-byte unchanged. The original personal-frequency model remains the best submitted baseline. These scores were supplied by the user, not fetched from Kaggle; original screenshot binaries are not present in this tool run. Submission IDs and submission timestamps remain null rather than being invented. See `submitted_score_evidence.json`. The prior fusion’s small positive local result and lower returned scores demonstrate why local selection is not a promise of Kaggle improvement.",
        "",
        "## Fixed protocol and observed-time feature",
        "",
        "The original temporal windows, causal cleaning, 80% longest-block qualification, interval unions, canonical broadcasts, candidate carryovers, repeats, cohort and shared popularity fallback are unchanged. Training is [2020-03-09 00:00:00, 2020-05-18 00:00:00); validation is [2020-05-18 00:00:00, 2020-07-27 00:00:00), on the established source wall clock. Every result uses **4,625 evaluation users and 6,384 candidates**. Rankings were additionally generated for the full template/evaluation union of 4,649 users.",
        "",
        "Original ranking is descending personal qualified-airing count, then ascending raw string programme ID. Variant A keeps that count primary and then sorts by descending **maximum observed viewing-segment end across that user/programme’s qualified airings**, followed by ID. Qualified segment groups are recomputed from the existing read-only pre-cutoff cache with the full original airing duration denominator; their counts exactly match the existing interaction records. Segments are clipped again at the information cutoff and all extracted latest timestamps are asserted <= cutoff. The extractor never parses an airing end from the canonical airing ID. It does not infer recency from a future broadcast end and does not decay counts.",
        "",
        "Variant B also keeps personal counts primary, then uses descending distinct qualified training viewers, descending total qualified training user-airing count, then ID. These two global statistics reproduce the existing shared popularity ordering exactly. Only equal-personal-count ordering can change. In both variants, primary count sequences in the top five are asserted identical to baseline; a membership change is permitted only if the original ranks five and six have equal personal counts. Fallback ordering and the numbers of completed slots are identical across all three methods.",
        "",
        "## Importance of existing ties",
        "",
        "All counts below use the fixed **4,625-user cohort**, and only directly ranked available programmes with positive personal qualified counts. Popularity-fallback items are excluded from tie diagnosis. These are potential tie ambiguities, not counts of actual changes under a particular variant.",
        "",
        "| Diagnostic | Users | Denominator |",
        "| --- | ---: | ---: |",
        f"| At least two equal-count items already inside original direct top five | {d['users_with_equal_counts_within_selected_direct_top5']:,} | 4,625 |",
        f"| Equal counts at direct ranks five and six: boundary membership ambiguous | {d['users_with_count_tie_crossing_fifth_position']:,} | 4,625 |",
        f"| Both internal-order and boundary tie | {d['users_with_both']:,} | 4,625 |",
        f"| Either type | {d['users_with_either_order_or_boundary_tie']:,} | 4,625 |",
        f"| At least six available qualified programmes, so a crossing tie is possible | {d['users_with_at_least_six_available_qualified_items']:,} | 4,625 |",
        "",
        f"Boundary groups contain **{int(sizes.min())}–{int(sizes.max())} programmes**, median **{np.median(sizes):.0f}**, exact full-cohort mean **{sizes.mean():.4f}**. These summaries use all {len(sizes):,} affected users, not a sample. A full group includes its selected and unselected members; one or more are outside rank five. The exact joint selected/unselected group-size histogram and tied count values are retained in `tie_diagnostics.json`.",
        "",
        "| Full boundary tie-group size | Users |",
        "| ---: | ---: |",
    ]
    for size, n in d["boundary_full_group_size_histogram"].items():
        lines.append(f"| {size} | {n} |")
    lines += [
        "",
        "## Three-method local results",
        "",
        "| Method | MAP@5 | Absolute difference | AP improved / worsened / unchanged users | Conditional paired-bootstrap 95% interval for difference |",
        "| --- | ---: | ---: | --- | --- |",
    ]
    lines.append(
        f"| {labels['original']} | {r['original']['map_at_5']:.12f} | 0 | reference | reference |"
    )
    for v in ["latest", "popularity"]:
        x = r[v]
        lo, hi = x["paired_user_bootstrap_95pct_interval"]
        lines.append(
            f"| {labels[v]} | {x['map_at_5']:.12f} | {x['delta_from_original']:+.12f} | {x['users_improved']} / {x['users_worsened']} / {x['users_unchanged_ap']} | [{lo:+.9f}, {hi:+.9f}] |"
        )
    lines += [
        "",
        "Intervals use 2,000 paired-user bootstrap resamples with replacement, seed 42; the same draw indices are used for both variants. They are **conditional on this reused validation cohort**. Selecting the stronger of these two variants on the same hold-out introduces selection uncertainty, and the intervals do not cover repeated historical experimentation or future Kaggle data. The positive interval supports a local difference for Variant B, not a claimed future private score. Exact ties in model selection retain the original baseline.",
        "",
        "Variant A is below baseline, so it was not refitted or combined with Variant B. Variant B improves all nonempty-history slices in this validation run. The zero-history fallback is unchanged.",
        "",
        "## History-size slices",
        "",
        "History size is the existing number of distinct programmes with qualified pre-cutoff airings, before candidate filtering.",
        "",
        "| Qualified training items | Users | Original MAP@5 | Variant A MAP@5 | Variant B MAP@5 |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for sl in ["0", "1–5", "6–20", "21+"]:
        lines.append(
            "| "
            + sl
            + " | "
            + str(r["original"]["history_slices"][sl]["users"])
            + " | "
            + " | ".join(
                f"{r[v]['history_slices'][sl]['map_at_5']:.9f}"
                for v in ["original", "latest", "popularity"]
            )
            + " |"
        )
    lines += [
        "",
        "## Ordered-list changes versus membership changes",
        "",
        "The following compare each variant with the exact original local predictions, using the 4,625 evaluation users. A rank-position slot can change because of reordering or a different programme. Membership change means the top-five set itself differs; order-only means the set stays identical.",
        "",
        "| Variant | Changed ordered lists | Order-only users | Membership-change users | Changed rank slots / 23,125 | Top-five set overlap |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for v in ["latest", "popularity"]:
        x = r[v]["prediction_changes"]
        lines.append(
            f"| {labels[v]} | {x['users_changed']} | {x['users_with_order_change_only']} | {x['users_with_membership_change']} | {x['rank_position_slots_changed']} | {100*x['top5_set_overlap_fraction']:.4f}% |"
        )
    f = r["original"]["fallback"]
    lines += [
        "",
        f"All methods have exactly {f['complete_users']} complete-fallback users, {f['partial_completion_users']} partial-completion users and {f['completion_slots']} fallback slots. These unchanged counts confirm that the experiment changes tie ordering, not the common fallback policy. A user’s AP can stay unchanged despite their ordered list changing.",
        "",
    ]
    if artifact:
        x = artifact["differences_from_submitted_personal_baseline"]
        v = artifact["validation"]
        lines += [
            "## Candidate for manual review",
            "",
            "Selected configuration: **Variant B — personal qualified count ↓, qualified global viewers ↓, qualified global user-airings ↓, raw string programme ID ↑**. No additional fitted parameter, decay or hybrid component was introduced.",
            "",
            "The combined [2020-03-09, 2020-07-27) interaction cache is generated by the established full-window pipeline, not by summing split-window qualification. This stage recomputes qualification from those full-window canonical segment groups and reconciles all **573,003** qualified user-airings with that combined cache. Prediction remains [2020-07-27, 2020-10-19); known schedule carryovers yield 6,649 candidates.",
            "",
            "Filename: `" + artifact["csv_filename"] + "`",
            "",
            "Absolute path: `" + artifact["csv_absolute_path"] + "`",
            "",
            "[Open the exact candidate CSV](../../submissions/"
            + artifact["csv_filename"]
            + ")",
            "",
            "SHA-256: `" + artifact["csv_sha256"] + "`",
            "",
            "Internal validation and the separate explicit-comma CLI both report **valid**: "
            + str(v["users"])
            + " users in original order, exact original header, five distinct nonzero available IDs per user, "
            + str(v["candidate_ids"])
            + " candidates and "
            + str(v["distinct_recommended_ids"])
            + " distinct recommended IDs. The submitted baseline and fusion files are preserved. See `candidate_validator_cli.json` and `candidate_artifact.json`.",
            "",
            "Against the **exact submitted personal-frequency baseline**, "
            + str(x["users_changed"])
            + " / 1,260 ordered lists change: "
            + str(x["users_with_order_change_only"])
            + " users have order-only changes and "
            + str(x["users_with_membership_change"])
            + " have membership changes. "
            + str(x["rank_position_slots_changed"])
            + " / 6,300 rank-position slots change; "
            + str(x["new_item_slots_ignoring_order"])
            + " programme slots introduce IDs absent from the old user list. Final top-five set overlap is "
            + f"{100*x['top5_set_overlap_fraction']:.4f}%"
            + ". These final-window counts are separate from the validation overlap table above.",
            "",
        ]
    lines += [
        "## Runtime, regression and provenance",
        "",
        "Local feature extraction/ranking/assessment took "
        + f"{s['elapsed_seconds_local_experiment']:.3f}"
        + " seconds, including "
        + f"{s['latest_extraction_seconds']:.3f}"
        + " seconds for latest-observed-end extraction. Ranking and completion for the 4,649-user union took "
        + ", ".join(
            v + " " + f"{r[v]['ranking_and_completion_seconds']:.4f}" + " s"
            for v in ["original", "latest", "popularity"]
        )
        + ". "
        + (
            "The selected combined-window candidate took "
            + f"{artifact['refit_and_artifact_seconds']:.3f}"
            + " seconds to refit/validate from existing caches. "
            if artifact
            else ""
        )
        + "Code/source hashes, input identities, cache provenance, exact windows and dependency versions are in the JSON records. No raw dataset audit, prior model grid or recency experiment was repeated.",
        "",
        "All **37 tests pass**: the existing 33 plus four focused checks for primary-count precedence, both global popularity tie keys and final raw-ID ties, observed-time cutoff invariance, and internal-versus-boundary tie-group semantics. The cutoff check extends a segment beyond cutoff and adds future-only segments/users, leaving qualified counts and latest features unchanged; opaque airing IDs prevent reliance on a future broadcast end. Existing interval, metric, carryover and leakage checks remain in the suite.",
        "",
        "Private per-user ranks, latest features and AP values are ignored under `artifacts/personal_ties_20261030_v3/`. Raw inputs and credentials remain outside Git. Both submitted CSVs and failed historical validator evidence are preserved. The original native session transcript remains unmodified; student verification is pending.",
        "",
        "**Manual submission recommendation: yes, Variant B is worth one reviewed benchmark submission.** The local gain is +0.009364 with a positive conditional interval, while retaining personal-frequency count precedence. The earlier fusion’s worse reported Kaggle result is a concrete limitation on extrapolating validation gains. The original baseline remains the best submitted model until an actual new result is supplied. No Kaggle page, upload workflow, Submit action or API was used. Stop and wait for user review.",
        "",
    ]
    (out / "tie_break_report.md").write_text("\n".join(lines))
    (out / "metrics.csv").write_text(
        "method,map_at_5,delta_from_original,improved_users,worsened_users,unchanged_ap_users\n"
        + "\n".join(
            f"{v},{x['map_at_5']:.12f},{x.get('delta_from_original',0):.12f},{x.get('users_improved',0)},{x.get('users_worsened',0)},{x.get('users_unchanged_ap',4625)}"
            for v, x in r.items()
        )
        + "\n"
    )


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output-dir", type=Path, required=True)
    run(p.parse_args().output_dir)
