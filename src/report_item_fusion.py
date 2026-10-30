"""Render the controlled v5/v7 fusion report from aggregate evidence."""

import json
from pathlib import Path


def render(out):
    load = lambda p: json.loads(p.read_text())
    data = {s: load(out / s / "comparison.json") for s in ["main", "auxiliary"]}
    selection = load(out / "selection.json")
    lines = [
        "# Controlled v5 + v7 weighted reciprocal-rank fusion (executed)",
        "",
        "**Retain submitted v5. All three frozen weights lower MAP@5 on both splits. No weight qualifies; no combined-window refit or final prediction CSV was generated. None is recommended for manual submission.**",
        "",
        "## Definition and reconciliation",
        "",
        "For each source, use direct top-50 distinct available items before fallback. V5 ranks by N50 personal airing count, then original >=0.80 global distinct viewers, qualified user-airings, and raw string programme ID. V7 uses its saved all-supported direct ranking, including seen and unseen programmes; its top50/shrink20/min-co-view3 model was neither refit on these splits nor retuned. Cache checksums were verified against v7 provenance. No audit or prior experiment was repeated.",
        "",
        "Fusion is `1/(60+rank_v5) + w/(60+rank_item_item)` for exactly w=0.05,0.10,0.20. Ranks start at one; absent ranks contribute zero. Duplicate items are removed before source truncation. Scores are exact rational numbers, so mathematical ties use the unchanged global viewer count, global airing count and ascending raw string ID. Shared v5 popularity fills only insufficient fused lists; no fallback items enter either source list.",
        "",
        "Main remains 4,625 users / 6,384 candidates, fit [2020-03-09,2020-05-18), validate [2020-05-18,2020-07-27). Auxiliary remains 4,589 / 5,742, fit [2020-03-09,2020-06-01), validate [2020-06-01,2020-07-27). Original >=0.80 validation truth and history slices, candidate availability, repeat eligibility and global fallback are unchanged. Both frozen anchor hashes match v7, and completed v5 top-five predictions exactly reconcile to the saved v5 references.",
        "",
        "## Local results and conditional uncertainty",
        "",
        "| Split | Weight | MAP@5 | Difference from v5 | Paired bootstrap 95% interval | Improved / worsened / unchanged AP users |",
        "| --- | ---: | ---: | ---: | --- | --- |",
    ]
    for split, d in data.items():
        lines.append(
            f'| {split} | v5 | {d["results"]["v5"]["map_at_5"]:.12f} | reference | reference | reference |'
        )
        for w in ["0.05", "0.1", "0.2"]:
            r = d["results"][w]
            ci = r["paired_bootstrap_95pct"]
            lines.append(
                f'| {split} | {w} | {r["map_at_5"]:.12f} | {r["delta_from_v5"]:+.12f} | [{ci[0]:+.9f}, {ci[1]:+.9f}] | {r["users_improved"]} / {r["users_worsened"]} / {r["users_unchanged"]} |'
            )
    lines += [
        "",
        "Each interval uses 2,000 paired-user resamples with seed 42; the same resampled users are used for all three weights within a split. Intervals are **conditional on the reused cohorts and exclude configuration-selection uncertainty**. The temporal windows and users overlap, so the two splits are not independent untouched tests. All six intervals are below zero. This supports the bounded decision to retain v5, not a claim that every future integration method must fail.",
        "",
        "Eligibility requires a strictly positive within-split gain on both splits. Among eligible weights, maximize the minimum absolute MAP gain across main and auxiliary, breaking ties toward smaller weight. No eligible weight exists; the max-min rule therefore selects no candidate. No configuration was added after inspecting results.",
        "",
        "## Ordered lists, positions and membership",
        "",
        "| Split | Weight | Changed lists | Changed rank slots | Membership-change users | Order-only users | Common top-five items / slots | New membership slots |",
        "| --- | ---: | ---: | ---: | ---: | ---: | --- | ---: |",
    ]
    for split, d in data.items():
        for w in ["0.05", "0.1", "0.2"]:
            c = d["results"][w]["prediction_changes"]
            lines.append(
                f'| {split} | {w} | {c["users_changed"]} | {c["rank_position_slots_changed"]} | {c["users_with_membership_change"]} | {c["users_with_order_change_only"]} | {c["top5_items_in_common"]} / {c["recommendation_slots"]} ({c["top5_set_overlap_fraction"]:.4%}) | {c["new_item_slots_ignoring_order"]} |'
            )
    lines += [
        "",
        "## Seen and unseen effects",
        "",
        "Seen means a programme in that user’s pre-cutoff N50 history; all recommended programmes are available. Unseen means absent from that history. Baseline unseen recommendations supplied by fallback remain classified as unseen. An entering item is in fused top five but not baseline top five; leaving is the reverse. Counts are user-item recommendation occurrences, not globally unique programme IDs. Relevant hits use the same >=0.80 target set.",
        "",
        "| Split | Weight | Users with entering unseen | Entering unseen recommendations / relevant hits | Leaving unseen recommendations / relevant hits | Total unseen slots baseline -> fused | Unseen relevant hits baseline -> fused |",
        "| --- | ---: | ---: | --- | --- | --- | --- |",
    ]
    for split, d in data.items():
        for w in ["0.05", "0.1", "0.2"]:
            e = d["results"][w]["seen_unseen_effects"]
            get = lambda k: e.get(k, 0)
            lines.append(
                f'| {split} | {w} | {get("users_with_entering_unseen")} | {get("entering_unseen_items")} / {get("entering_unseen_relevant_hits")} | {get("leaving_unseen_items")} / {get("leaving_unseen_relevant_hits")} | {get("baseline_unseen_recommendations")} -> {get("fused_unseen_recommendations")} | {get("baseline_unseen_relevant_hits")} -> {get("fused_unseen_relevant_hits")} |'
            )
    lines += [
        "",
        "| Split | Weight | Entering seen recommendations / relevant hits | Leaving seen recommendations / relevant hits | Net seen hits | Net unseen hits | Seen AP contribution difference | Unseen AP contribution difference |",
        "| --- | ---: | --- | --- | ---: | ---: | ---: | ---: |",
    ]
    for split, d in data.items():
        for w in ["0.05", "0.1", "0.2"]:
            e = d["results"][w]["seen_unseen_effects"]
            get = lambda k: e.get(k, 0)
            lines.append(
                f'| {split} | {w} | {get("entering_seen_items")} / {get("entering_seen_relevant_hits")} | {get("leaving_seen_items")} / {get("leaving_seen_relevant_hits")} | {get("fused_seen_relevant_hits")-get("baseline_seen_relevant_hits"):+d} | {get("fused_unseen_relevant_hits")-get("baseline_unseen_relevant_hits"):+d} | {e["delta_seen_map_contribution"]:+.9f} | {e["delta_unseen_map_contribution"]:+.9f} |'
            )
    lines += [
        "",
        "Seen/unseen AP contributions assign each relevant-hit precision term to the hit item’s type, dividing by the original AP denominator; precision still includes all earlier hits. The two contribution means add to MAP, and their differences add to the reported MAP difference. They reflect positions and preceding hits as well as membership and are descriptive attribution, not independent or causal component scores.",
        "",
        "At w=0.05, main gains 12 entering unseen relevant hits but loses 10 unseen hits, a net +2. Seen hits decline by 41. Auxiliary gains 5 unseen hits but loses 11 (net -6), while seen hits decline by 42. Larger weights increase seen-hit losses to 170/232 main and 195/295 auxiliary without increasing unseen hits. New hits therefore do not offset displaced personal-history hits; the MAP decline also includes reordering of retained hits.",
        "",
        "## Why the larger v7 candidate coverage does not transfer here",
        "",
        "For these weights an item missing from v5’s direct top50 has maximum RRF score `0.20/61 = 0.00327869`. Any retained v5 item has personal contribution at least `1/110 = 0.00909091`, before any collaborative bonus. Thus every retained personal item outranks every collaborative-only item. In particular, users with at least five available personal items cannot receive an unseen top-five item through this rule. The weights mainly rerank known programmes; unseen replacements occur in short-history/fallback cases and are identical across the three weights. A focused regression verifies this fixed-weight barrier.",
        "",
        "This explains why v7’s useful unseen candidate retrieval is not evidence for improved ranking under this specific RRF. It does not justify trying unregistered weights in this round. If integration is revisited later, it should be a separately controlled design that can admit useful unseen items while protecting the strong personal ranking; no such change was implemented here.",
        "",
        "## Existing history-size slices",
        "",
        "Slice membership remains based on original >=0.80 distinct training programmes before availability filtering. The JSON evidence includes slice user outcomes, position/membership changes, full seen/unseen attribution and fallback usage in addition to the table below.",
        "",
        "| Split | History size | Users | Weight | v5 MAP@5 | Fused MAP@5 | Difference | Net seen / unseen relevant hits |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for split, d in data.items():
        for sl in ["0", "1–5", "6–20", "21+"]:
            for w in ["0.05", "0.1", "0.2"]:
                r = d["results"][w]["history_slices"][sl]
                e = r["seen_unseen_effects"]
                delta = lambda kind: e.get(f"fused_{kind}_relevant_hits", 0) - e.get(
                    f"baseline_{kind}_relevant_hits", 0
                )
                lines.append(
                    f'| {split} | {sl} | {r["users"]} | {w} | {r["v5_map_at_5"]:.9f} | {r["map_at_5"]:.9f} | {r["delta_from_v5"]:+.9f} | {delta("seen"):+d} / {delta("unseen"):+d} |'
                )
    lines += [
        "",
        "## Reproducibility, checks and preservation",
        "",
        "All 58 tests pass. New focused tests cover exact fusion arithmetic, zero contribution for missing ranks, duplicate suppression and top50 truncation, a hand-constructed mathematical tie resolved by global viewer/airing keys and raw ID, empty-source fallback, seen/unseen hit/AP attribution, and the fixed-weight unseen-item barrier. No new timestamp feature was introduced: the established canonical-count and item-item cutoff invariance/leakage tests are reused. Checksummed v7 caches, frozen anchors and unchanged truth files constrain the fusion inputs.",
        "",
        f'Frozen protocol SHA-256: `{selection["frozen_protocol_sha256"]}`. Split comparisons, bootstrap and selection took {selection["elapsed_comparison_seconds"]:.3f} seconds. Peak process RSS at selection: {selection["environment"]["peak_process_rss_bytes"]:,} bytes (process-lifetime high-water, including cached interactions and rankings). Per-weight/split timings, input/source hashes, dependency versions, base commit and environment are in comparison.json and selection.json. No split item-item model was refit.',
        "",
        "No new submission description, path, checksum or validator result is claimed because no new prediction artifact was generated. The implemented conditional final-fit path was not executed. All previous CSVs remain byte-identical. Best submitted v5 remains `submissions/candidate_personal_threshold_050_20261030_v5.csv`, SHA-256 `593b1134b6625771abfe107e17d074499cedf6efb4ef9306e06289e9566876e5`; user-reported Private 0.40210 / Public 0.41789. No submission ID or timestamp is known or invented.",
        "",
        "Native session records remain unmodified, and student verification remains pending. No Kaggle workflow, submission command, upload or submission API was used. Stop for user review.",
        "",
        "```bash",
        "OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 /private/tmp/sweettv-model-venv/bin/python -m src.experiment_item_fusion --data-dir /Users/chenfengru/LLM4Rec-Course-codex/data/sweettv/raw",
        "/private/tmp/sweettv-model-venv/bin/python -m unittest discover -s tests",
        "/private/tmp/sweettv-model-venv/bin/python -m src.report_item_fusion",
        "```",
    ]
    (out / "comparison_report.md").write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    render(Path("results/item_fusion_20261030_v8"))
