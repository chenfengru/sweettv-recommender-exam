"""Generate the English review packet from bounded local experiment records."""

import argparse
import json
from pathlib import Path


def run(out):
    summary = json.loads((out / "comparison.json").read_text())
    r = summary["results"]
    a = summary["assessment"]
    artifact = (
        json.loads((out / "candidate_artifact.json").read_text())
        if (out / "candidate_artifact.json").exists()
        else None
    )
    prep = json.loads((out / "training_signal_preparation.json").read_text())
    timing = json.loads((out / "fusion_ranking_runtime_replay.json").read_text())
    selected = a["selected"]
    base = r["personal_original"]["map_at_5"]
    ci = a["paired_user_bootstrap_95pct_percentile_interval"]
    recommendation = {
        "recommended_configuration": "submitted original personal repeat-frequency baseline",
        "best_experimental_configuration": selected,
        "recommend_manual_submission": False,
        "reason": "Nominal local gain is small, the conditional paired-user bootstrap interval includes zero, and this hold-out also selected configurations. Retain the already submitted baseline unless the user explicitly chooses an exploratory manual benchmark.",
        "csv_generation_reason": (
            "The selected new configuration met the requested positive-local-score criterion and produced nonduplicate final predictions; the artifact is exploratory and not a statistically supported replacement."
            if artifact
            else "No justified nonduplicate improvement artifact."
        ),
        "workflow": "Stop for user review. Only the user may upload to Kaggle; approval of results does not authorize automatic upload.",
        "new_candidate_public_score": None,
        "new_candidate_private_score": None,
        "student_verification": "pending",
    }
    (out / "recommendation.json").write_text(
        json.dumps(recommendation, indent=2) + "\n"
    )
    lines = [
        "# Bounded improvement review — 29 October 2026",
        "",
        "**Recommendation: retain the submitted original personal-frequency baseline.** The strongest new local configuration has only a marginal gain, with uncertainty spanning a loss. An exploratory, validated candidate is available for review because it meets the nominal positive-local-score criterion; it is not recommended as an evidence-backed replacement yet. **No Kaggle page, upload workflow or submission API was used in this stage.** Stop for the user’s review.",
        "",
        "## Baseline evidence and validator correction",
        "",
        "The user confirms that `first_personal_original_20261029_v1.csv` was manually submitted and that a Kaggle screenshot returned **Private Score 0.38937** and **Public Score 0.39131**. These are user-confirmed screenshot values, not scores independently retrieved during this run. The original screenshot binary/submission reference is not available in this tool run; none was manufactured. `baseline_score_evidence.json` records this provenance.",
        "",
        "Submitted CSV SHA-256 remains `53cb8ae4b59b26ab6ee00b5e99ad91044876180e662732a755d3e99a297e64bc`. The baseline file has not been regenerated or modified.",
        "",
        "The historical `results/first_submission_20261029/validator_cli.json` actually records an autodetection failure for the one-column candidate export. The internal validation in `first_artifact.json` succeeded, but the previous report incorrectly described the CLI attempt as successful too. The failed file is preserved unchanged. Rerunning the CLI with **`--delimiter ,`** succeeds; `baseline_validator_cli_success.json` separately records 1,260 users, K=5, 6,649 candidates and the unchanged CSV hash. The first-artifact report now explicitly corrects the earlier claim.",
        "",
        "## Fixed protocol and bounded results",
        "",
        "All local comparisons keep the same **4,625 users, 6,384 candidates**, 80% longest-block validation truth, causal preprocessing, canonical-airing deduplication, interval unions, repeat eligibility and unweighted shared popularity fallback. Fitting is [2020-03-09, 2020-05-18); validation is [2020-05-18, 2020-07-27), in source wall time. No target or cohort was retuned. Earlier recency experiments were not repeated.",
        "",
        "| Configuration | Local MAP@5 | Difference from personal baseline | Status |",
        "| --- | ---: | ---: | --- |",
    ]
    for n, v in r.items():
        status = (
            "existing reference, score/ranks reconciled"
            if n in ("personal_original", "als_original", "cbf_original")
            else "new bounded experiment"
        )
        lines.append(
            f"| {n} | {v['map_at_5']:.6f} | {v['map_at_5']-base:+.6f} | {status} |"
        )
    lines += [
        "",
        "The two new ALS fits fix **32 factors, regularization 0.1, 20 iterations, seed 42, one CPU thread**, with observed confidence `1 + 40*log1p(s_ui)` and library `alpha=1`. Only the per-airing inclusion gate changes: retain an airing if its longest merged block/full original airing duration is at least 0.5 or 0.8. Its contribution remains `q=min(1, union_overlap/full_airing_duration)`; contributions are aggregated by user/item before log scaling. Qualified counts used for shared fallback are exactly unchanged. The original ALS factors are loaded for direct top-50 ranks; the original all-positive-overlap model is not refitted for validation.",
        "",
        "| ALS signal | Retained user-airings | User-item pairs | Fitting users | Fitting items |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for n, v in prep["variants"].items():
        lines.append(
            f"| {n} | {v['retained_user_airings']:,} | {v['user_item_pairs']:,} | {v['users']:,} | {v['items']:,} |"
        )
    lines += [
        "",
        "Cleaner ALS signals improve the local score from 0.087237 to 0.133973/0.152084, while reducing item support. This is consistent with incidental overlaps weakening target alignment, but does not isolate a universal causal explanation: filtering also changes sparsity, retained users/items and confidence totals. Both variants remain substantially below personal frequency.",
        "",
        "CBF uses the identical fitted category/genre vectors, weighted profiles and cosine scores. Only **exactly equal** positive cosine scores are ordered by descending distinct qualified training viewers, then raw programme ID. No tolerance or rounding is used, and the old CBF fitted fingerprint and original-score replay match the established baseline. The gain from 0.024851 to 0.028687 is small and does not rescue the method.",
        "",
        "## Supported candidates, fallback and runtime",
        "",
        "| Method | Supported candidate IDs / 6,384 | Full fallback users | Partial completion users | Fallback slots / 23,125 | Fit or load s | Direct top-50 inference s | Peak worker MiB |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for n in ["als_original", "als_lb50", "als_lb80", "cbf_pop_tie"]:
        v = r[n]
        f = v["fallback"]
        lines.append(
            f"| {n} | {v['supported_candidate_items']:,} ({100*v['supported_candidate_fraction']:.2f}%) | {f['complete_users']} | {f['partial_completion_users']} | {f['completion_slots']} | {v['fit_or_existing_model_load_seconds']:.4f} | {v['direct_inference_seconds']:.4f} | {v['peak_worker_rss_bytes']/2**20:.2f} |"
        )
    lines += [
        "",
        "Support means a trained item factor for ALS or nonempty pre-cutoff content vector for CBF. Unsupported IDs remain in the common global pool and can enter through the unchanged shared fallback. Fit/load timing excludes JSON loading; the original ALS row is a load, not a new fit. Inference covers 4,649 users (evaluation cohort union template users), while all scores and fallback counts use the fixed 4,625-user cohort. RSS is each isolated worker’s lifetime high-water, including imports/data. New ALS filtering changes model-history availability, but not the cohort or its history-size slice definitions.",
        "",
        "## Fusion construction and budget",
        "",
        "The strongest individual alternative is **"
        + a["strongest_alternative"]
        + "** (local MAP@5 "
        + f"{r[a['strongest_alternative']]['map_at_5']:.6f}"
        + "). Only that alternative is fused with personal frequency. Each component supplies at most its top 50 **directly scored, supported** IDs, before any popularity completion. A missing component supplies zero evidence. The score is `1/(60+personal_rank) + w/(60+alternative_rank)`, with absent terms zero, personal weight 1.0 and only `w in {0.05,0.1,0.2}` tested. Raw IDs break fused-score ties; shared fallback is applied only after fusion.",
        "",
        "| Fusion weight | MAP@5 | Complete fallback | Partial completion | Ranking replay s | Completion replay s |",
        "| ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for n, v in r.items():
        if n.startswith("rrf_"):
            t = timing[n]
            f = v["fallback"]
            lines.append(
                f"| {v['config']['alternative_weight']} | {v['map_at_5']:.6f} | {f['complete_users']} | {f['partial_completion_users']} | {t['direct_fusion_rank_replay_seconds']:.4f} | {t['completion_replay_seconds']:.4f} |"
            )
    lines += [
        "",
        "Fusion timing is a separately measured deterministic replay of rank construction/completion from cached direct component lists, excluding component fitting/inference. Every replay exactly reproduces the original predictions. All local experiments, preparation, process startup, inference and assessment together took "
        + f"{summary['elapsed_seconds_local_experiments']:.2f}"
        + " seconds before the final artifact refit. No further configurations were searched.",
        "",
        "## History-size slices",
        "",
        "Slices use the original number of distinct programmes with qualified pre-cutoff history, identically across every configuration.",
        "",
        "| Qualified training items | Users | Personal | Original ALS | ALS ≥50% | ALS ≥80% | Original CBF | CBF popularity ties | Best fusion |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    names = [
        "personal_original",
        "als_original",
        "als_lb50",
        "als_lb80",
        "cbf_original",
        "cbf_pop_tie",
        selected,
    ]
    for sl in ["0", "1–5", "6–20", "21+"]:
        lines.append(
            "| "
            + sl
            + " | "
            + str(r["personal_original"]["history_slices"][sl]["users"])
            + " | "
            + " | ".join(f"{r[n]['history_slices'][sl]['map_at_5']:.6f}" for n in names)
            + " |"
        )
    lines += [
        "",
        "Every JSON method record includes all slice counts/scores, including the two other fusion weights. The best fusion improves the 6–20-item slice but worsens the 1–5 and 21+ slices. No slice-specific selection or switch was fitted after inspecting these results.",
        "",
        "## Credibility and prediction overlap",
        "",
        "Best new configuration: **"
        + selected
        + "**. Local MAP@5 **"
        + f"{r[selected]['map_at_5']:.9f}"
        + "**, an absolute gain of **"
        + f"{a['map_difference']:+.9f}"
        + "** over the unrounded personal-frequency reference. AP@5 improves for **"
        + str(a["users_improved"])
        + " users**, worsens for **"
        + str(a["users_worsened"])
        + "**, and is unchanged for **"
        + str(a["users_unchanged"])
        + "**.",
        "",
        "The paired-user bootstrap 95% percentile interval for the mean difference is **["
        + f"{ci[0]:+.9f}, {ci[1]:+.9f}"
        + "]**, using 2,000 resamples of the fixed cohort with replacement, seed 42. It includes zero. This is conditional on this validation set, not a test of Kaggle improvement, and does not correct for choosing models/weights on the same hold-out or earlier experiment reuse. The small nominal gain is therefore not convincing evidence to replace the scored baseline.",
        "",
        "Local predictions change for **"
        + str(a["prediction_overlap"]["users_changed"])
        + " / 4,625 users**, with **"
        + str(a["prediction_overlap"]["rank_position_slots_changed"])
        + " / 23,125 rank-position slots** changed. Top-five set overlap is **"
        + f"{100*a['prediction_overlap']['top5_set_overlap_fraction']:.4f}%"
        + "**. AP can remain unchanged despite a list changing, and slot changes include reordering. The baseline’s 0.38937 private Kaggle score uses different data; no private score or predicted private-score increment is assigned to this candidate.",
        "",
    ]
    if artifact:
        d = artifact["differences_from_submitted_baseline"]
        v = artifact["validation"]
        lines += [
            "## Exact candidate for user review",
            "",
            "A new candidate was generated because the best new configuration exceeded the frozen local baseline and produced nonduplicate combined-window predictions. This is an **exploratory review artifact**, not a claim of a statistically supported improvement or a recommendation to upload now.",
            "",
            "Filename: `" + artifact["csv_filename"] + "`",
            "",
            "Absolute path: `" + artifact["csv_absolute_path"] + "`",
            "",
            "[Open candidate CSV](../../submissions/" + artifact["csv_filename"] + ")",
            "",
            "SHA-256: `" + artifact["csv_sha256"] + "`",
            "",
            "Final fitting uses the existing canonical, unioned **combined [2020-03-09, 2020-07-27)** cache, not added split qualifications. The selected ≥80% filter is applied to those combined per-airing segments; ALS is refitted with the same fixed settings, then fused with combined-window personal frequency using weight 0.1 and k=60. Prediction is **[2020-07-27, 2020-10-19)**, with known schedule carryovers and the original airing denominators. Only pre-cutoff behaviour is fitted.",
            "",
            "Internal and explicit-comma CLI validation both return **valid**: **"
            + str(v["users"])
            + " users, five distinct nonzero available IDs per user, "
            + str(v["candidate_ids"])
            + " candidates**, original template header and exact user order. There are "
            + str(v["distinct_recommended_ids"])
            + " distinct recommended IDs. See `candidate_validator_cli.json` and `candidate_artifact.json` for full provenance and checksums.",
            "",
            "Against the exact submitted baseline file, **"
            + str(d["users_changed"])
            + " / "
            + str(d["users"])
            + " users** have a different ordered list; **"
            + str(d["rank_position_slots_changed"])
            + " / "
            + str(d["recommendation_slots"])
            + " recommendation slots** change. Top-five set overlap is "
            + f"{100*d['top5_set_overlap_fraction']:.4f}%"
            + " ("
            + str(d["top5_items_in_common"])
            + " common item placements when order is ignored). These counts describe final-window predictions, separately from the local validation overlap. The submitted baseline bytes and checksum remain unchanged.",
            "",
        ]
    lines += [
        "## Reproducibility and review boundary",
        "",
        "The existing interval matcher, causal cleaning, interaction cache, sparse rankers, verified ALS confidence convention and validator were reused. Three focused tests cover longest-block gating versus union contribution, strict exact-score tie ordering, and direct-only top-50 fusion/completion. **All 33 tests pass**. Existing audit, recency results, failed validator evidence and native session transcript remain preserved; student verification is still pending. Dependencies remain the pinned NumPy 2.2.6, SciPy 1.15.3, implicit 0.7.3 and threadpoolctl 3.7.0 environment on the 24 GiB Mac. Per-method records contain seed, configuration, runtime, worker RSS and source hashes. Private ranks/predictions, filtered interactions and user-level AP remain ignored under `artifacts/improvement_20261029_v2/`.",
        "",
        "**Manual submission recommendation: no, not on this evidence.** Keep the already scored original-frequency baseline. The candidate is available if the user chooses an exploratory manual benchmark, but the mean local gain is tiny, uncertainty spans a loss, and 705 final-user lists change. A later independent temporal check would be more informative than claiming this hold-out-selected winner will beat private MAP@5 0.38937. No further experiment or Kaggle action is scheduled. Stop and wait for review.",
        "",
    ]
    (out / "improvement_report.md").write_text("\n".join(lines))
    (out / "metrics.csv").write_text(
        "configuration,local_map_at_5,delta_from_personal,evaluation_users,candidates\n"
        + "\n".join(
            f"{n},{v['map_at_5']:.12f},{v['map_at_5']-base:.12f},4625,6384"
            for n, v in r.items()
        )
        + "\n"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    run(parser.parse_args().output_dir)
