"""Render the English report from aggregate viewing-strength evidence."""

import json
from pathlib import Path


def render(out):
    load = lambda p: json.loads(p.read_text())
    selection = load(out / "selection.json")
    summaries = {s: load(out / s / "comparison.json") for s in ["main", "auxiliary"]}
    diagnostics = {s: load(out / s / "retrieval_diagnostics.json") for s in summaries}
    lines = [
        "# Viewing-strength counts and remaining errors (executed)",
        "",
        "**Decision: retain submitted v5 (T50). Neither bonus improves either split; no new prediction CSV or combined-window refit was generated. Neither variant is recommended for manual benchmark submission.**",
        "",
        "Exactly two new scores were tested: L05 uses the integer score `2*N50 + N80` (lambda 0.5); L10 uses `N50 + N80` (lambda 1.0). N80 airings are a subset of N50 and intentionally receive an additional bonus. Reference v5 uses N50 alone. Tie keys and fallback remain the original >=0.80 distinct training viewers, total qualified user-airings and ascending raw string programme ID. Interval unions, full original airing denominators, canonical deduplication, causal cleaning/clipping, candidates and repeats are unchanged.",
        "",
        "Main: fit [2020-03-09,2020-05-18), validate [2020-05-18,2020-07-27), 4,625 users and 6,384 candidates. Auxiliary: fit [2020-03-09,2020-06-01), validate [2020-06-01,2020-07-27), 4,589 users and 5,742 candidates. Source wall-clock parsing is unchanged. Truth remains the existing >=0.80 targets; original >=0.80 history-slice membership remains fixed. No completed opportunity/week/threshold experiment was rerun. Existing segment databases and cached truths were reused; v5 predictions were reconciled exactly to saved references on both splits.",
        "",
        "## Local comparison",
        "",
        "| Split | Method | MAP@5 | Delta from v5 | Conditional paired bootstrap 95% interval | Improved / worsened / unchanged users |",
        "| --- | --- | ---: | ---: | --- | --- |",
    ]
    for split, d in summaries.items():
        for v in ["v5", "L05", "L10"]:
            r = d["results"][v]
            ci = r.get("paired_user_bootstrap_95pct_interval")
            interval = f"[{ci[0]:+.9f}, {ci[1]:+.9f}]" if ci else "reference"
            outcomes = (
                " / ".join(
                    str(r[k])
                    for k in ["users_improved", "users_worsened", "users_unchanged_ap"]
                )
                if ci
                else "reference"
            )
            lines.append(
                f'| {split} | {v} | {r["map_at_5"]:.12f} | {r.get("delta_from_v5",0):+.12f} | {interval} | {outcomes} |'
            )
    lines += [
        "",
        "The bootstrap uses 2,000 paired-user resamples, seed 42, shared indices for both variants within a split. These intervals are **conditional on the reused cohorts**, not adjusted for repeated hold-out use or selection. The main/auxiliary splits overlap and are not independent tests. All four intervals are below zero, although the main L10 upper endpoint is close to zero. This evidence supports retention of v5 in this bounded round, not a general claim that viewing strength can never help.",
        "",
        "## Personal-history retrieval diagnostics",
        "",
        "The personal-history set consists of available programmes with at least one N50 training airing. Relevant items are distinct items in the unchanged validation targets. Macro recall averages h / |relevant| by user; micro coverage sums h over summed relevant-item counts. Ranking below is the **full v5 personal ranking before fallback**, not the completed system list.",
        "",
        "| Split | Macro recall | Micro covered / relevant | Micro coverage | Personal-history-only oracle MAP@5 |",
        "| --- | ---: | --- | ---: | ---: |",
    ]
    for split, r in diagnostics.items():
        lines.append(
            f'| {split} | {r["macro_personal_history_recall"]:.9f} | {r["micro_relevant_covered"]:,} / {r["micro_relevant_total"]:,} | {r["micro_relevant_coverage"]:.4%} | {r["personal_history_only_oracle_map_at_5"]:.9f} |'
        )
    lines += [
        "",
        "Per-user oracle AP@5 is `min(5,h) / min(5,|relevant|)`. This is a **diagnostic upper bound for personal-history-only retrieval**, not an attainable model score or an upper bound for the full system with fallback. The macro recall and oracle happen to coincide here because the established targets contain at most five relevant programmes per user. Do not interpret the difference between this oracle and full-system MAP as guaranteed recoverable improvement.",
        "",
        "| Split | Rank 1–5 | Rank 6–20 | Rank 21–50 | Beyond 50 | Absent | Absent: other users have N50 | Absent: no N50 interactions |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for split, r in diagnostics.items():
        b = r["relevant_rank_buckets"]
        lines.append(
            f"| {split} | "
            + " | ".join(
                f"{b[k]:,}" for k in ["1–5", "6–20", "21–50", "beyond_50", "absent"]
            )
            + f' | {r["absent_with_other_users_n50"]:,} | {r["absent_without_any_n50"]:,} |'
        )
    lines += [
        "",
        "Each absent item is available but has no N50 training airing for that user. The first absent category therefore identifies interactions from other users; the second identifies programmes with no N50 interactions from any training user.",
        "",
        "**Bottleneck: a mixture, with coverage the larger component of personal-prefix misses.** Main has 8,968 absent relevant items versus 3,932 present but below rank five; auxiliary has 8,720 versus 3,964. Coverage accounts for about 69.5% / 68.7% of these personal-prefix misses. Ranking still matters: 3,507 / 3,468 relevant items sit at ranks 6–20. These counts describe the personal ranker before fallback, not final-system missed-item attribution.",
        "",
        "Of absent items, 7,647 / 8,968 (85.3%) main and 7,349 / 8,720 (84.3%) auxiliary already have N50 interactions from other users. The diagnostics support a later controlled investigation of retrieving previously unseen programmes from other-user signals, with a separate cold-item strategy for the remainder. This is evidence of opportunity, not proof that collaborative retrieval will work. No item-item collaborative filtering was implemented in this round. The two bonuses leave the personal candidate set unchanged and do not address this coverage limitation.",
        "",
        "## Fixed history-size slices",
        "",
        "Slice counts use original >=0.80 distinct training programmes before availability filtering; weights do not change membership.",
        "",
        "| Split | History size | Users | v5 MAP@5 | L05 MAP@5 | L10 MAP@5 |",
        "| --- | --- | ---: | ---: | ---: | ---: |",
    ]
    for split, d in summaries.items():
        for sl in ["0", "1–5", "6–20", "21+"]:
            r = d["results"]
            lines.append(
                f'| {split} | {sl} | {r["v5"]["history_slices"][sl]["users"]} | '
                + " | ".join(
                    f'{r[v]["history_slices"][sl]["map_at_5"]:.9f}'
                    for v in ["v5", "L05", "L10"]
                )
                + " |"
            )
    lines += [
        "",
        "## Ordering and membership changes",
        "",
        "| Split | Variant | Changed lists | Changed rank slots | Membership-change users | Order-only users | Common items / all slots | New membership slots |",
        "| --- | --- | ---: | ---: | ---: | ---: | --- | ---: |",
    ]
    for split, d in summaries.items():
        for v in ["L05", "L10"]:
            c = d["results"][v]["prediction_changes"]
            lines.append(
                f'| {split} | {v} | {c["users_changed"]} | {c["rank_position_slots_changed"]} | {c["users_with_membership_change"]} | {c["users_with_order_change_only"]} | {c["top5_items_in_common"]} / {c["recommendation_slots"]} ({c["top5_set_overlap_fraction"]:.4%}) | {c["new_item_slots_ignoring_order"]} |'
            )
    lines += [
        "",
        "## Reproducibility, preservation and tests",
        "",
        "The frozen selection rule requires strictly positive within-split MAP differences on both splits. If both qualify, higher main MAP wins; exact selection ties retain v5. Neither qualifies. No new final-window prediction file was generated and no final refit was run.",
        "",
        "All 48 tests pass. Existing exact 0.50/0.80 inclusion, duplicate/overlap, longest-block/full-duration and pre-cutoff leakage regressions were reused. New focused checks verify the N80 bonus, exact integer scores, deterministic global/raw-string ties, unchanged truth/global keys/fallback/slices, and a hand-computable oracle example covering all five rank buckets and both absent categories. Runtime anchor hashes also match those recorded in the completed v5 experiment on each split.",
        "",
        f'Frozen protocol SHA-256: `{selection["frozen_definition_sha256"]}`. Total diagnostics/evaluation/selection: {selection["total_experiment_seconds"]:.3f} seconds. Peak process RSS: {selection["environment"]["peak_process_rss_bytes"]:,} bytes (process-lifetime high-water mark). Input/source hashes, base commit, environment and timings appear in the JSON evidence; dependencies match the established pinned environment.',
        "",
        "```bash",
        "OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 /private/tmp/sweettv-model-venv/bin/python -m src.experiment_viewing_strength --data-dir /Users/chenfengru/LLM4Rec-Course-codex/data/sweettv/raw --output-dir results/viewing_strength_20261030_v6 --private-dir artifacts/viewing_strength_20261030_v6",
        "/private/tmp/sweettv-model-venv/bin/python -m unittest discover -s tests",
        "/private/tmp/sweettv-model-venv/bin/python -m src.report_viewing_strength",
        "```",
        "",
        "Preserved best submitted artifact:",
        "",
        "- File: `candidate_personal_threshold_050_20261030_v5.csv`.",
        "- Absolute path: `/Users/chenfengru/sweettv-recommender-exam/submissions/candidate_personal_threshold_050_20261030_v5.csv`.",
        "- SHA-256: `593b1134b6625771abfe107e17d074499cedf6efb4ef9306e06289e9566876e5`.",
        "- Private **0.40210**, Public **0.41789**: user-supplied screenshot values transcribed in the attached request. Screenshot binary was not supplied to this run; no independent Kaggle lookup. Submission ID and submission timestamp are unknown and not invented. The evidence recording time is not a submission timestamp.",
        "",
        "All previous prediction files and checksums are preserved. No Kaggle workflow, upload, Submit action, or submission API was used. The native session transcript remains unmodified; native exports are not committed. Student verification is pending until personally performed. Stop for user review; any later upload is manual-only.",
    ]
    (out / "comparison_report.md").write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    render(Path("results/viewing_strength_20261030_v6"))
