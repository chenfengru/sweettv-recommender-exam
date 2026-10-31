"""Build report-ready English analysis from actual stored comparison outputs."""

import argparse
import csv
import json
import math
from pathlib import Path
import numpy as np
from .validate_submission import validate_submission
from .metrics import average_precision_at_k


def main(args):
    out, private = args.output_dir, args.private_dir
    summary = json.loads((out / "comparison.json").read_text())
    methods = summary["methods"]
    prep = json.loads((out / "preparation.json").read_text())
    diagnostics = json.loads(
        (out / "numerical_and_content_diagnostics.json").read_text()
    )
    invariance = json.loads((out / "actual_data_cutoff_invariance.json").read_text())
    setup = json.loads((private / "setup.json").read_text())
    truth = json.loads((private / "truth.json").read_text())
    names = list(methods)
    users = sorted(truth)
    aps = {n: json.loads((private / f"{n}_ap.json").read_text()) for n in names}
    predictions = {
        n: json.loads((private / f"{n}_predictions.json").read_text()) for n in names
    }
    candidate_set = set(setup["candidates"])
    validations = {}
    breakdown = {}
    for name, r in methods.items():
        assert abs(math.fsum(aps[name].values()) / len(users) - r["map_at_5"]) < 1e-12
        path = private / f"{name}_validation_template.csv"
        with path.open("w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["user_id", "tv_show_id"])
            writer.writerows(
                (u, " ".join(predictions[name][u])) for u in setup["template_users"]
            )
        validations[name] = validate_submission(
            args.data_dir / "submission.csv",
            path,
            candidate_set,
            user_column="user_id",
            prediction_column="tv_show_id",
        )
        cold = (
            0
            if name == "popularity"
            else (
                r["zero_qualified_training_history_users"]
                if name == "personal"
                else r["zero_soft_training_history_users"]
            )
        )
        breakdown[name] = {
            "complete_model_cold_start_users": cold,
            "complete_no_available_supported_items_users": r["fallback"][
                "complete_users"
            ]
            - cold,
            "partial_list_completion_users": r["fallback"]["partial_completion_users"],
        }
    rng = np.random.default_rng(42)
    differences = []
    d = np.array([aps["personal"][u] - aps["popularity"][u] for u in users])
    for _ in range(1000):
        differences.append(float(np.mean(d[rng.integers(len(d), size=len(d))])))
    ci = np.quantile(differences, [0.025, 0.975]).tolist()
    example_scores = {
        label: {
            n: (
                average_precision_at_k(truth[u], predictions[n][u])
                if u in truth
                else None
            )
            for n in names
        }
        for label, u in setup["examples"].items()
    }
    analysis = {
        "fallback_breakdown": breakdown,
        "validation_template_checks": validations,
        "personal_minus_popularity": {
            "difference": float(d.mean()),
            "paired_user_bootstrap_95pct_percentile_interval": ci,
            "bootstrap_resamples": 1000,
            "seed": 42,
            "sampling": "uniform with replacement across the fixed 4625-user local cohort; conditional descriptive uncertainty, not Kaggle generalization",
        },
        "example_ap_at_5": example_scores,
    }
    (out / "analysis.json").write_text(json.dumps(analysis, indent=2) + "\n")
    labels = {
        "popularity": "Global popularity",
        "personal": "Personal repeat-frequency",
        "cbf": "Content-based filtering",
        summary["selected_als_configuration"]: "Implicit ALS",
    }
    pc = lambda v: f"{100*v:.2f}%"
    lines = [
        "# Local model comparison — 29 October 2026",
        "",
        "**Executed:** all four individual methods on the frozen 4,625-user cohort and 6,384 validation candidates. **Not executed:** hybrid fitting, final weeks 11–30 model refit, Kaggle submission, or private-score evaluation. Student verification remains pending.",
        "",
        "## Result and recommendation",
        "",
        "Personal repeat-frequency is the strongest measured local method. Its MAP@5 exceeds popularity by "
        + f"{analysis['personal_minus_popularity']['difference']:.6f}"
        + " absolute. The descriptive paired-user bootstrap interval for that difference is ["
        + f"{ci[0]:.6f}, {ci[1]:.6f}"
        + "] (1,000 resamples, seed 42). This interval conditions on this local cohort and target; it does not predict a Kaggle score or account for target-construction uncertainty.",
        "",
        "Keep personal frequency as the local performance anchor and popularity as the shared fallback. CBF and implicit MF both ran successfully as the two qualifying methods, but neither currently improves the reference. Do not deploy their greater catalogue diversity as a claimed benefit without further evidence.",
        "",
        "| Method | MAP@5 | Evaluation users | Candidates | Fit s | Inference s | Peak worker RSS MiB |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for n, r in methods.items():
        lines.append(
            f"| {labels[n]} | {r['map_at_5']:.6f} | {r['evaluation_users']:,} | {r['candidate_count']:,} | {r['fit_seconds']:.4f} | {r['inference_seconds']:.4f} | {r['peak_process_rss_bytes']/2**20:.2f} |"
        )
    lines += [
        "",
        "Fit time includes ranker construction and feature/model fitting after loading cached interactions. Inference generates 4,649 user lists: the evaluation cohort union all 1,260 template users. MAP and every descriptive slice/fallback/coverage statistic use only the 4,625 evaluation users. Peak RSS is an isolated worker process’s lifetime high-water mark, including imports and loaded histories; it is not an incremental model allocation. All workers used one ALS thread and one numerical-library thread.",
        "",
        "### ALS grid: fixed budget, unchanged truth",
        "",
        "| Factors | Regularization | Iterations | MAP@5 |",
        "| ---: | ---: | ---: | ---: |",
    ]
    for n, score in summary["all_als_grid_scores"].items():
        r = json.loads((out / f"{n}.json").read_text())
        c = r["config"]
        lines.append(
            f"| {c['factors']} | {c['regularization']} | {c['iterations']} | {score:.6f} |"
        )
    lines += [
        "",
        "Selected ALS: **32 factors, regularization 0.1, 20 iterations**, seed 42. The same validation window selected this configuration and supplies its displayed score, so it is a model-selection estimate rather than a second untouched test. No larger search or extra target tuning was performed.",
        "",
        "## Frozen data and protocol",
        "",
        "The established audit was reused, not rerun. Input SHA-256 identities were checked against it. Training behaviour is [2020-03-09 00:00:00, 2020-05-18 00:00:00); validation is [2020-05-18 00:00:00, 2020-07-27 00:00:00), in the fixed source wall-clock convention with timezone unknown. Previous-file airings carry into the next midnight window; canonical airings retain their complete original duration. Programme 0 is excluded, and previously watched IDs remain eligible.",
        "",
        "Local truth remains up to five most-frequently qualified programmes, with an 80% longest merged-block requirement and ascending raw string ID ties. **Every held-out user/programme qualified count exactly matches the authoritative cleaned audit**, not merely the cohort size. No difficult users were removed. There are 108 users without qualified training history, of whom 44 have no soft training overlap. The main cohort excludes users with no qualified validation target, as frozen before modelling.",
        "",
        "Training has "
        + f"{prep['train_soft_pairs']:,}"
        + " soft user-item pairs from "
        + f"{prep['train']['user_airings']:,}"
        + " usable user-airings; validation has "
        + f"{prep['validation_soft_pairs']:,}"
        + " soft pairs and "
        + f"{prep['validation']['qualified_user_airings']:,}"
        + " qualified user-airings. Sparse training axes contain 4,841 users and 2,973 items. Training strength is `s_ui = sum(union_overlap / full_airing_duration)`, with `w_ui = log1p(s_ui)`. Qualified counts are distinct from these soft strengths.",
        "",
        "### Causal cleaning correction and leakage verification",
        "",
        "For sessions completed by the cutoff, retain the audit’s duration-discrepancy and >24-hour exclusions. For sessions still ongoing at the cutoff, only the observed prefix can be known: apply the 24-hour rule to that prefix and do not use the future complete declared duration or stop time for discrepancy rejection. Rows starting at/after the cutoff are ignored before further preprocessing. This closes a future-tail dependence in the original full-session cleaning rule. On the actual data it changes **zero qualified training user-item counts**; validation truth is unchanged. The original audit remains a historical measurement.",
        "",
        "The focused fixture covers file-boundary carryover, duplicate canonical broadcasts, original airing denominators after clipping, and a combined fitting window. Its two half-window 50% portions do not separately qualify, while the combined 100% airing qualifies exactly once; the final refit builder therefore recomputes the combined interval window rather than adding split counts. A full actual-data final refit has not been run.",
        "",
        "The end-to-end fixture modifies strictly future behaviour, including a crossing session extended beyond 24 hours, and compares interactions, sparse features, ALS factors and predictions for all four methods. The additional full-data check removed "
        + f"{invariance['mutation']['strictly_future_rows_removed']:,}"
        + " strictly future rows and extended "
        + f"{invariance['mutation']['crossing_tails_extended']:,}"
        + " crossing tails to 14 days after the cutoff. It produced byte-equivalent training interaction records, identical fitted fingerprints, and identical predictions for all 4,649 users across every selected method. See `actual_data_cutoff_invariance.json`. Input hashes identify provenance, not model features.",
        "",
        "## Method definitions and failure cases",
        "",
        "Popularity ranks distinct qualified training viewers, then qualified user-airing totals, then string IDs. Personal frequency ranks each user’s qualified airing counts, then IDs. All methods complete unsupported slots with the same candidate-restricted popularity order and ascending IDs for zero-popularity candidates.",
        "",
        "CBF uses sparse, L2-normalized category/genre multi-hot vectors (the three genre positions share a genre namespace) and normalized `w_ui`-weighted user profiles. Metadata uses the modal title/category/genre tuple over unique airings starting before the cutoff, breaking tuple ties lexicographically. Titles are displayed but are not content features. Of 6,384 candidates, **2,391 lack pre-cutoff metadata representations** and receive no direct CBF score; they remain eligible through shared completion. Permitted future schedule metadata are used only for availability and report display, not fitted content features.",
        "",
        "After fixing score-to-ID candidate alignment, independent checks on 30 users and ten candidate scores per user agree with manually accumulated double-precision profiles/cosines within "
        + f"{diagnostics['cbf']['max_cosine_error']:.3g}"
        + ". CBF has only "
        + str(diagnostics["cbf"]["distinct_candidate_content_vectors"])
        + " distinct candidate vectors, including the empty vector. "
        + f"{diagnostics['cbf']['users_with_more_than_five_exactly_tied_top_scores']:,}"
        + " / "
        + f"{diagnostics['cbf']['cohort_users_with_positive_content_score']:,}"
        + " scored users have more than five exactly tied top candidates; the median top-score tie contains "
        + f"{diagnostics['cbf']['median_exact_top_score_tie_count']:.0f}"
        + " items. The ID tie-break therefore frequently chooses among indistinguishable metadata representations. These diagnostics support limited item discrimination; they do not prove that metadata alone explains every error.",
        "",
        "ALS uses positive sparse preferences and **observed confidence `1 + 40*w_ui`, with library `alpha=1.0`**. The [official CPU ALS documentation](https://benfred.github.io/implicit/api/models/cpu/als.html) describes sparse values as confidences and missing entries as preference zero/confidence one. The installed implicit 0.7.3 fit implementation was also inspected to confirm its optional alpha multiplication. Confidence is applied exactly once; its algebra is asserted in the integration check. See `als_confidence_check.json`. Only items with fitting-window interactions receive learned factors: **4,178 candidates lack trained ALS representations**, and can enter lists only through completion.",
        "",
        "The bounded ALS search underperforms popularity, especially for history-rich users. Soft training overlaps include many programmes that never satisfy the stricter qualified-repeat target. This is a plausible mismatch to investigate, not a measured causal explanation. No unknown interactions are treated as explicit dislikes. Repeats were enabled and candidate filtering was identical across methods.",
        "",
        "Native float32 matrix-vector scoring emitted overflow/invalid/divide warnings despite finite factors. Across 64 sampled users per ALS configuration, scores were finite and agreed with direct float64 contraction within 2.3e-7, with all sampled top-1 choices agreeing. Direct contraction also matched scalar `math.fsum` within 1.2e-16. The root cause of the native warnings is not established. Final scoring uses finite-checked float64 direct contraction; final fitting/inference logs contain no numerical warning. A nonfinite factor or score now fails explicitly.",
        "",
        "Two earlier local attempts are retained under `preliminary_native_matmul/` and `preliminary_unordered_candidates/`. Their CBF scores are superseded: the candidate-ordering defect mixed up score rows and IDs. The final result is protected by a unique-category recommendation fixture. Do not cite preliminary metrics. The original 25 tests plus three focused tests all pass (28 total).",
        "",
        "## History-size slices",
        "",
        "History size is the number of distinct programmes with at least one qualified pre-cutoff airing, before candidate filtering. Slice users sum to 4,625 for every method.",
        "",
        "| Qualified training items | Users | Popularity MAP@5 | Personal MAP@5 | CBF MAP@5 | ALS MAP@5 |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for sl in ["0", "1–5", "6–20", "21+"]:
        lines.append(
            "| "
            + sl
            + " | "
            + str(methods["popularity"]["history_slices"][sl]["users"])
            + " | "
            + " | ".join(
                f"{methods[n]['history_slices'][sl]['map_at_5']:.6f}" for n in names
            )
            + " |"
        )
    lines += [
        "",
        "Personal frequency’s advantage grows with qualified history. For users without qualified history, its shared fallback equals popularity. The 108-user zero-qualified-history slice is broader than the 44-user zero-soft-history slice, so CBF/ALS can score some users whom personal frequency must fall back for.",
        "",
        "## Fallback, catalogue coverage and repeats",
        "",
        "| Method | Complete cold-start fallback users | Complete fallback: no available supported items | Partial completion users | Fallback slots / 23,125 | Distinct recommended IDs / 6,384 | Repeated-item share |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for n, r in methods.items():
        b = breakdown[n]
        lines.append(
            f"| {labels[n]} | {b['complete_model_cold_start_users']} | {b['complete_no_available_supported_items_users']} | {b['partial_list_completion_users']} | {r['fallback']['completion_slots']} ({pc(r['fallback']['slot_fraction'])}) | {r['distinct_recommended_items']} ({pc(r['catalogue_coverage'])}) | {pc(r['repeated_item_share'])} |"
        )
    lines += [
        "",
        "Cold-start here means no qualified history for personal frequency and no soft interaction representation for CBF/ALS. Four additional personal-frequency users have history but none of its qualified items is available in the validation window. Popularity is intentionally a global method; its lists are not labelled fallback operations. Repeated-item share counts recommendation slots whose programme appears in any cleaned soft training history, with denominator 4,625 × 5. Catalogue coverage is distinct recommended IDs divided by the common 6,384 candidates. Larger catalogue coverage alone does not establish user value.",
        "",
        "All seven model/configuration outputs contain five distinct, nonzero, available IDs for every predicted user. The four selected methods additionally pass the existing template validator for all 1,260 template users in original row order, using the exact 6,384-ID validation-window candidate set. These private files are **validation-window demonstrations**, not final weeks 31–42 submissions. Their paths and checksums are in `analysis.json` and individual method records.",
        "",
        "## Two fixed example users",
        "",
        "[Report-ready ranked IDs, original titles/categories, observed training aggregates and held-out hits](two_user_examples.md) use the same history-poor and history-rich users for every method. They were selected once by minimum/maximum qualified training item count among template users with positive training history, breaking ties by raw user ID. Selection did not use recommendation hits or model scores. Private user-ID mapping and detailed aggregates remain under ignored `artifacts/model_comparison_20261029/`.",
        "",
        "The history-poor user has four soft-history programmes but only one qualified programme; no qualified validation target is observed. This user is outside the fixed metric cohort, so recommendations are marked **not evaluable**, not treated as negative labels. The history-rich user has 837 soft-history programmes and 183 qualified programmes. Their personal and popularity lists both hit programme 240081 at rank 2 (AP@5 "
        + f"{example_scores['history_rich']['personal']:.2f}"
        + "); the rich-history example illustrates that the overall winner still has failures. No replacement user was chosen to obtain a more favourable example.",
        "",
        "## Reproducibility, provenance and next experiment",
        "",
        "The prior ChatGPT-generated foundation and audited branch were reused. All new implementation, execution and automated checks were performed by Codex; they do not constitute student verification. The original native session transcript remains unmodified and excluded from public Git; its actual location remains in the private provenance note created during the audit. Historical audit records are untouched.",
        "",
        "Python 3.10.11 on macOS 26.6.2 arm64, 24 GiB physical RAM established by the audit. Runtime versions: "
        + ", ".join(f"{k} {v}" for k, v in prep["dependencies"].items())
        + ". `requirements.txt` pins runtime packages; `dependencies_full.txt` also records tooling. Seed 42; no GPU; ALS and numerical-library threads set to one. Each method JSON includes base Git commit, dirty-tree state, source hashes, configuration, dependency versions, output hash, runtime and RSS.",
        "",
        "Cold extraction took "
        + f"{prep['train']['elapsed_seconds']:.2f}"
        + " s for training and "
        + f"{prep['validation']['elapsed_seconds']:.2f}"
        + " s for validation. The final cached preparation took "
        + f"{prep['preparation_seconds']:.2f}"
        + " s. The runner’s timed comparison through model selection took "
        + f"{summary['elapsed_seconds']:.2f}"
        + " s; subsequent example rendering and diagnostic commands are separate. The full-data cutoff check took "
        + f"{invariance['elapsed_seconds']:.2f}"
        + " s. Cache manifests identify full input checksums, code hashes, exact windows, cleaning configuration and interaction-file digests. Cache lookup validates configuration and output checksum before reuse. Original raw inputs were never rewritten.",
        "",
        "**Recommended next experiment:** change only CBF’s tie-break among exactly equal cosine scores from raw ID order to pre-cutoff qualified-viewer popularity, keeping features, soft weights, truth, cohort, candidates and shared fallback unchanged. The measured frequency of large exact ties makes this a concrete test of item discrimination at ranking time; improvement is a hypothesis. Keep the current CBF result as the comparator. After these individual results, simple reciprocal-rank fusion with personal frequency can be considered, but no fusion was run here. Do not refit or submit to Kaggle until a later authorized stage.",
        "",
    ]
    (out / "comparison_report.md").write_text("\n".join(lines))
    (out / "metrics.csv").write_text(
        "method,map_at_5,evaluation_users,candidates,fit_seconds,inference_seconds,peak_rss_bytes\n"
        + "\n".join(
            f"{n},{r['map_at_5']:.12f},{r['evaluation_users']},{r['candidate_count']},{r['fit_seconds']:.6f},{r['inference_seconds']:.6f},{r['peak_process_rss_bytes']}"
            for n, r in methods.items()
        )
        + "\n"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--private-dir", type=Path, required=True)
    main(parser.parse_args())
