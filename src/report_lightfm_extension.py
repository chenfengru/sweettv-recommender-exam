"""English report for the fixed six-feature identity WARP extension."""

import json
from pathlib import Path
from .lightfm_features import LIGHTFM_FEATURES


def render(out):
    load = lambda p: json.loads(p.read_text())
    selection = load(out / "selection.json")
    training = load(out / "training.json")
    api = load(out / "installed_api.json")
    names = ["origin_20200406", "origin_20200420", "main", "auxiliary"] + (
        ["final"] if (out / "final/feature_diagnostics.json").exists() else []
    )
    origins = {name: load(out / name / "feature_diagnostics.json") for name in names}
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
        "# Fixed identity-only LightFM WARP feature extension (executed)",
        "",
        "**The extension qualifies under the frozen two-split point-estimate rule and one validated candidate is prepared for manual review. Main improves with a positive conditional interval; auxiliary improvement is small and its interval includes zero. This is a reasonable exploratory benchmark candidate, not established superiority to submitted v13. Retain v13 as the confirmed incumbent until manual benchmarking supplies new evidence.**",
        "",
        "## Frozen scope and installed API",
        "",
        "Exactly six new columns are appended to unchanged v13 rows and all 34 original feature values: LightFM score, rank, user bias, item bias, unsupported-user flag, unsupported-item flag. No embedding coordinates, candidate expansion, content, model blending, E2, cold-user override, extra seed/configuration or post-result tuning is used. One extended LightGBM classifier is fit on the original 604,935 historical candidate rows and 25,385 positive labels, with exactly v13’s fixed 300-tree settings.",
        "",
        f'LightFM **{api["lightfm_version"]}** installed successfully from source. Actual compiled backend is `{api["compiled_backend"]}`; it lacks OpenMP and executes single-threaded, matching the explicitly requested num_threads=1. No substitute algorithm was used. Constructor/fit/predict/representation signatures and all dependency versions are saved in installed_api.json. Main versions: NumPy2.2.6, SciPy1.15.3, scikit-learn1.7.2, LightGBM4.6.0. See docs/running_lightfm_extension.md for reproduction.',
        "",
        "Requested LightFM settings: loss=warp, no_components=10, learning_rate=0.05, item_alpha=user_alpha=0, max_sampled=10, random_state=42; fit epochs=15 and num_threads=1. Installed defaults retained and recorded by actual get_params: learning_schedule=adagrad, k=5,n=10,rho=0.95,epsilon=1e-6. Fitted RandomState descriptors include the initial seed and resulting state hash. All origin reports retain actual parameters, counts, mappings/state fingerprints and timings.",
        "",
        "## Pre-cutoff support, mappings and ranking",
        "",
        "At each origin, extract N50 from its own audited canonical pre-cutoff segment cache with observed clipping and full airing denominators. Binary user-item matrices contain one positive per distinct N50 pair regardless of airing frequency. Only users/items with positive support enter mappings. Raw string IDs are sorted ascending for stable dense indices and explicitly saved privately as ordered ID lists plus ID/index dictionaries. Each origin fits a fresh identity-only model; no later-origin weights are borrowed. Historical cutoffs are April6/April20; evaluation cutoffs are May18/June1. Histories start March9. Final July27 LightFM is fitted only after qualification.",
        "",
        "Score/rank require both supports; otherwise both are zero. User bias requires only user support; item bias requires only item support. Unsupported values are zero with the explicit flags, and unsupported identities are never passed to predict with random untrained embeddings. Supported user/item biases come from the installed identity representation APIs.",
        "",
        "Ranks are one-based among **ALL available origin-supported programmes**, with repeats allowed, descending LightFM score and ascending raw string ID for exact ties. They are not ranks within a user’s candidate union. Only the six scalar features reach LightGBM; private predictive arrays are saved for reproducibility, not used as embedding-coordinate columns.",
        "",
        "## Origin support coverage",
        "",
        "| Origin | Supported training users / items | Binary N50 pairs | Supported query users / queries | Supported available programmes / all available | Supported candidate pairs / all rows | Unsupported user / item rows |",
        "| --- | --- | ---: | --- | --- | --- | --- |",
    ]
    for name, d in origins.items():
        m = d["lightfm"]
        s = d["support_and_features"]
        lines.append(
            f'| {name} | {m["supported_training_users"]} / {m["supported_training_items"]} | {m["binary_n50_pairs"]:,} | {s["supported_query_users"]} / {s["query_users"]} | {s["supported_available_programmes"]} / {s["available_programmes"]} ({s["available_item_support_fraction"]:.4%}) | {s["supported_pairs"]:,} / {s["candidate_rows"]:,} | {s["unsupported_user_rows"]} / {s["unsupported_item_rows"]} |'
        )
    lines += [
        "",
        "All candidate programmes happen to have item support in every origin because the unchanged generator uses N50 personal/related items and >=0.80 popularity. Many available programmes outside those candidate rows lack support; no candidate expansion is performed. The unsupported-item flag is therefore constant zero in this run, but retained exactly as frozen. Unsupported-user rows still retain supported item biases. True numeric missingness is zero after explicit support encoding.",
        "",
        "## MAP@5 against saved v13",
        "",
        "Main retains 4,625 users / 6,384 candidates and >=0.80 truth from [2020-05-18,2020-07-27); auxiliary retains 4,589 / 5,742 and truth from [2020-06-01,2020-07-27). Original cohorts, availability, repeat rules and H80 history slices remain fixed. The extended classifier trains only on April6->[April6,April20) and April20->[April20,May4) labels; main/auxiliary labels are opened after feature tables and probabilities are fixed.",
        "",
        "| Split | Saved v13 MAP@5 | Extended MAP@5 | Paired difference | Conditional paired bootstrap 95% interval | Improved / worsened / unchanged AP users |",
        "| --- | ---: | ---: | ---: | --- | --- |",
    ]
    for name, d in results.items():
        r = d["comparison_v13"]
        ci = r["paired_bootstrap_95pct"]
        lines.append(
            f'| {name} | {r["reference_map_at_5"]:.12f} | {r["map_at_5"]:.12f} | {r["delta"]:+.12f} | [{ci[0]:+.9f}, {ci[1]:+.9f}] | {r["users_improved"]} / {r["users_worsened"]} / {r["users_unchanged"]} |'
        )
    lines += [
        "",
        "Intervals use 2,000 paired-user resamples, seed42, conditional on the reused cohorts and trained models. Main and auxiliary overlap in time/users; intervals exclude model-selection uncertainty and do not make them independent tests. The auxiliary interval crosses zero, so the small positive point estimate is uncertain. Qualification follows the predeclared strict point-estimate rule, not an additional significance rule. No variants were added to strengthen it.",
        "",
        "## Candidate, label and original-feature equality",
        "",
        "All historical labels, original v13 matrices and row_index metadata are hashed before/after. Corresponding original34 columns are exactly equal; only six new columns are appended. Classifier rows remain in the same two-origin order, and the original settings/tie-breaking are unchanged. Candidate recall/oracle dictionaries exactly equal v13.",
        "",
        "| Split | Covered relevant pairs / all targets | Micro candidate recall | Macro candidate recall | Oracle MAP@5 |",
        "| --- | --- | ---: | ---: | ---: |",
    ]
    for name, d in results.items():
        c = d["candidate_coverage_exactly_equal_v13"]
        lines.append(
            f'| {name} | {c["covered_relevant_pairs"]:,}/{c["all_relevant_pairs_in_universe"]:,} | {c["micro_recall"]:.4%} | {c["macro_recall_target_users"]:.9f} | {c["oracle_map_at_5_target_users"]:.9f} |'
        )
    lines += [
        "",
        "Candidate recall is |relevant intersect candidate|/|relevant|, macro averaged over target users or micro summed over target occurrences. Oracle AP=min(5,covered)/min(5,relevant), averaged by user; it equals macro recall for the fixed at-most-five targets. This is a candidate-union diagnostic ceiling, not achieved model performance. Any gain here is a ranking change, not more retrieval coverage.",
        "",
        "## Fixed history slices and N50-cold groups",
        "",
        "| Split | Original H80 slice | Users | v13 MAP | Extended MAP | Difference | Improved / worsened / unchanged |",
        "| --- | --- | ---: | ---: | ---: | ---: | --- |",
    ]
    for name, d in results.items():
        for sl, r in d["comparison_v13"]["history_slices"].items():
            lines.append(
                f'| {name} | {sl} | {r["users"]} | {r["reference_map_at_5"]:.9f} | {r["map_at_5"]:.9f} | {r["delta"]:+.9f} | {r["users_improved"]} / {r["users_worsened"]} / {r["users_unchanged"]} |'
            )
    lines += [
        "",
        "| Split | Cold definition | Users | v13 MAP | Extended MAP | Improved / worsened / unchanged |",
        "| --- | --- | ---: | ---: | ---: | --- |",
    ]
    for name, d in results.items():
        for label, r in d["cold_users"].items():
            lines.append(
                f'| {name} | {label} | {r["users"]} | {r["v13_map"]:.9f} | {r["extended_map"]:.9f} | {r["users_improved"]} / {r["users_worsened"]} / {r["users_unchanged"]} |'
            )
    lines += [
        "",
        "H80 is the original >=0.80 distinct programme history before availability filtering. Full N50-cold users are unsupported by LightFM; availability-cold users may still have supported historical identities. Cold behaviour is mixed and no override is introduced. Post-score fallback completion remains zero because original candidate unions already include five global fallback items.",
        "",
        "## Seen/unseen hit attribution and prediction changes",
        "",
        "Seen means positive pre-cutoff N50. Relevant gains/losses count entering/leaving target occurrences per user. AP terms are assigned by hit type with all preceding hits retained; this descriptive decomposition is not causal. The reused helper’s legacy `fused_` prefix denotes current unblended classifier predictions.",
        "",
        "| Split | Seen target hits v13 -> extended | Unseen target hits v13 -> extended | Seen / unseen MAP contribution difference | Entering unseen items / target hits | Leaving unseen items / target hits |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for name, d in results.items():
        e = d["comparison_v13"]["seen_unseen_effects"]
        g = lambda k: e.get(k, 0)
        lines.append(
            f'| {name} | {g("baseline_seen_relevant_hits")} -> {g("fused_seen_relevant_hits")} | {g("baseline_unseen_relevant_hits")} -> {g("fused_unseen_relevant_hits")} | {e["delta_seen_map_contribution"]:+.9f} / {e["delta_unseen_map_contribution"]:+.9f} | {g("entering_unseen_items")} / {g("entering_unseen_relevant_hits")} | {g("leaving_unseen_items")} / {g("leaving_unseen_relevant_hits")} |'
        )
    lines += [
        "",
        "| Split | Changed lists | Changed rank slots | Membership-change / order-only users | Common top-five items / all slots | Relevant hit gains / losses |",
        "| --- | ---: | ---: | --- | --- | --- |",
    ]
    for name, d in results.items():
        r = d["comparison_v13"]
        c = r["prediction_changes"]
        lines.append(
            f'| {name} | {c["users_changed"]} | {c["rank_position_slots_changed"]} | {c["users_with_membership_change"]} / {c["users_with_order_change_only"]} | {c["top5_items_in_common"]}/{c["recommendation_slots"]} ({c["top5_set_overlap_fraction"]:.4%}) | {r["relevant_hit_gains"]} / {r["relevant_hit_losses"]} |'
        )
    lines += [
        "",
        "Main nets31 relevant hits; auxiliary nets-8 despite its small MAP increase, reflecting precision/order changes. The extension does not improve every user or all hit-count measures. Detailed slice attribution and list changes remain in comparison.json.",
        "",
        "## Feature distributions, missingness and cross-origin shift",
        "",
        "| Origin | Feature | Min | Mean | Median | P90 | Max | Zero fraction |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for name, d in origins.items():
        for feature, r in d["support_and_features"]["distributions"].items():
            lines.append(
                f'| {name} | {feature} | {r["min"]:.5f} | {r["mean"]:.5f} | {r["median"]:.5f} | {r["p90"]:.5f} | {r["max"]:.5f} | {r["zero_fraction"]:.4%} |'
            )
    lines += [
        "",
        "All 40-column tables are finite and original34 values unchanged. Zero score/rank for unsupported pairs is enforced; a supported bias is retained even when the other identity is unsupported. Observed zero values are not automatically interpreted as unsupported.",
        "",
        "Scores are uncalibrated WARP margins from separately fitted models, and user/item biases are not necessarily comparable across origins. Mean candidate score changes from about+0.51 at the two historical origins to-0.04/-0.30 at main/auxiliary and-1.32 at final. Mean user bias shifts from-1.35/-1.56 to-2.20/-2.45 and-3.40; the supported available universe grows from583/760 to2004/2086 and2964, changing rank distributions. Identical seeds do not align latent axes or guarantee score/bias calibration across these different training problems. No coordinate features, cross-origin normalization or recalibration variant was added.",
        "",
        "## Deterministic replay, importance and resources",
        "",
        "The predeclared April6 full-data replay uses the same binary matrix, sorted mappings, seed42,15 epochs and one thread. Mappings, predictive embedding/bias arrays and all six candidate feature columns are **bitwise identical**. This is a reproducibility verification, not a configuration search or independent statistical replication. Primary weights are retained; no selection between replays occurs. Unit tests separately verify the same properties on small fixtures.",
        "",
        "| Feature | Gain importance | Split count |",
        "| --- | ---: | ---: |",
    ]
    show = {r["feature"] for r in importance[:10]} | set(LIGHTFM_FEATURES)
    for r in importance:
        if r["feature"] in show:
            lines.append(f'| {r["feature"]} | {r["gain"]:.3f} | {r["splits"]} |')
    lines += [
        "",
        "LightFM rank has the largest training gain importance among the six additions. Importance is descriptive, not causal, and correlated original/collaborative features make isolated attribution unreliable. Unsupported flags have zero split importance in this fit but are preserved; neither feature selection nor alternative models were tested.",
        "",
        "| Origin | N50 extraction/fit/feature/save elapsed seconds | LightFM fit seconds | Six-feature generation seconds | Binary sparse bytes | Extended matrix bytes | Peak process RSS bytes |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for name, d in origins.items():
        m = d["lightfm"]
        lines.append(
            f'| {name} | {d["elapsed_origin_seconds_including_optional_replay"]:.3f} | {m["fit_seconds"]:.3f} | {d["feature_generation_seconds"]:.3f} | {m["binary_matrix_bytes"]:,} | {d["matrix_bytes"]:,} | {d["environment"]["peak_process_rss_bytes"]:,} |'
        )
    lines += [
        "",
        f'Extended LightGBM fit: {training["fit_seconds"]:.3f} seconds; run through both evaluations: {selection["elapsed_before_optional_final_seconds"]:.3f} seconds before conditional final fitting. First-origin elapsed includes the one replay. RSS is process-lifetime high-water, not isolated model memory. Scoring is one user against all supported available items at a time; no dense full user-item score matrix is materialized. Original candidate tables remain bounded by255 rows/user.',
        "",
        "Limitations remain: two-week historical label horizons versus ten/eight-week validation and twelve-week final predictions; four/six-week historical behaviour versus longer validation/final histories; repeated overlapping cohorts; uncalibrated cross-origin LightFM scores/biases and shifting rank universes; stochastic-model uncertainty beyond this one fixed seed. Deterministic replay verifies implementation repeatability, not generalization. Auxiliary evidence is especially weak because its interval includes zero.",
        "",
        "## Frozen decision and final candidate",
        "",
        "The decision requires strictly positive MAP differences against v13 on both splits. Both point estimates are positive, so the extension qualifies without adding a significance threshold or further variants. The final LightFM model is then fit only on N50 observations before July27. Its six features are appended to unchanged v13 final rows/34 features; the same extended LightGBM weights are used, with no evaluation-label retraining.",
        "",
    ]
    if artifact:
        c = artifact["differences_from_submitted_v13"]
        v = artifact["validation"]
        lines += [
            f'- Filename: `{artifact["filename"]}`.',
            f'- Absolute path: `{artifact["absolute_path"]}`.',
            f'- SHA-256: `{artifact["sha256"]}`.',
            f'- Both internal and separate CLI validators: **{v["status"]}**, all {v["users"]:,} original template users/header/order, five distinct available nonzero IDs, {v["candidate_ids"]:,} carryover-aware candidates.',
            f'- Versus exact submitted v13: {c["users_changed"]} changed lists, {c["rank_position_slots_changed"]} changed rank slots, {c["users_with_membership_change"]} membership-change and {c["users_with_order_change_only"]} order-only users. {c["users_identical"]} lists identical; set overlap {c["top5_items_in_common"]}/{c["recommendation_slots"]} ({c["top5_set_overlap_fraction"]:.4%}).',
            f'- Frozen extended classifier SHA-256: `{artifact["classifier_sha256"]}`.',
            "",
            "Accurate English manual submission description is saved in submission_description.txt:",
            "",
            "> " + artifact["submission_description"],
            "",
        ]
    lines += [
        "## Verification and preserved evidence",
        "",
        "All **83 tests pass**. New focused tests cover positive-only deterministic mappings/binary interactions, seeded training replay, support-aware score/rank/bias zeros, rank ties over the entire available supported universe, exact six-column alignment and post-cutoff behaviour invariance. Existing temporal, candidate, schema, ranking and submission checks are reused. Runtime checks confirm every origin’s N50 matches original per-user counts/context in candidate rows, original34/candidate/label equality, unchanged recall/oracle, finite support semantics, saved mappings/state hashes, replay and one frozen extended classifier.",
        "",
        f'Frozen protocol SHA-256: `{selection["frozen_protocol_sha256"]}`. Actual installed APIs/default parameters, dependency versions, source/cache fingerprints, mapping/model/feature hashes, timings and environment are retained in JSON evidence. Private mappings, N50 histories, latent predictive arrays, model weights and user-level rows remain ignored.',
        "",
        "Best confirmed submitted v13: user-screenshot-reported Private **0.43400** / Public **0.43774**, CSV SHA-256 `1fd147770b6be8ebcd64c89244af60cb8510440607358ec84c9adc6ffe7ec359`. No independent Kaggle lookup or invented submission ID/time. The new candidate has no Kaggle result; previous CSVs/checksums and models/caches are unchanged.",
        "",
        "No Kaggle workflow, submission command, upload or API was used. Native session records remain unmodified; student verification is pending until personally performed. Stop for user review and manual upload.",
        "",
        "```bash",
        "OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 /private/tmp/sweettv-model-venv/bin/python -m src.experiment_lightfm_extension --data-dir /Users/chenfengru/LLM4Rec-Course-codex/data/sweettv/raw",
        "/private/tmp/sweettv-model-venv/bin/python -m unittest discover -s tests",
        "/private/tmp/sweettv-model-venv/bin/python -m src.report_lightfm_extension",
        "```",
    ]
    (out / "comparison_report.md").write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    render(Path("results/lightfm_extension_20261030_v14"))
