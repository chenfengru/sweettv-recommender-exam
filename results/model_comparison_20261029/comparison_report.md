# Local model comparison — 29 October 2026

**Executed:** all four individual methods on the frozen 4,625-user cohort and 6,384 validation candidates. **Not executed:** hybrid fitting, final weeks 11–30 model refit, Kaggle submission, or private-score evaluation. Student verification remains pending.

## Result and recommendation

Personal repeat-frequency is the strongest measured local method. Its MAP@5 exceeds popularity by 0.083083 absolute. The descriptive paired-user bootstrap interval for that difference is [0.076079, 0.089902] (1,000 resamples, seed 42). This interval conditions on this local cohort and target; it does not predict a Kaggle score or account for target-construction uncertainty.

Keep personal frequency as the local performance anchor and popularity as the shared fallback. CBF and implicit MF both ran successfully as the two qualifying methods, but neither currently improves the reference. Do not deploy their greater catalogue diversity as a claimed benefit without further evidence.

| Method | MAP@5 | Evaluation users | Candidates | Fit s | Inference s | Peak worker RSS MiB |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Global popularity | 0.234407 | 4,625 | 6,384 | 0.1059 | 0.0024 | 426.03 |
| Personal repeat-frequency | 0.317490 | 4,625 | 6,384 | 0.1053 | 0.0178 | 427.72 |
| Content-based filtering | 0.024851 | 4,625 | 6,384 | 0.5169 | 0.9741 | 502.83 |
| Implicit ALS | 0.087237 | 4,625 | 6,384 | 1.9498 | 0.5302 | 514.12 |

Fit time includes ranker construction and feature/model fitting after loading cached interactions. Inference generates 4,649 user lists: the evaluation cohort union all 1,260 template users. MAP and every descriptive slice/fallback/coverage statistic use only the 4,625 evaluation users. Peak RSS is an isolated worker process’s lifetime high-water mark, including imports and loaded histories; it is not an incremental model allocation. All workers used one ALS thread and one numerical-library thread.

### ALS grid: fixed budget, unchanged truth

| Factors | Regularization | Iterations | MAP@5 |
| ---: | ---: | ---: | ---: |
| 32 | 0.01 | 20 | 0.085502 |
| 32 | 0.1 | 20 | 0.087237 |
| 64 | 0.01 | 20 | 0.068295 |
| 64 | 0.1 | 20 | 0.069699 |

Selected ALS: **32 factors, regularization 0.1, 20 iterations**, seed 42. The same validation window selected this configuration and supplies its displayed score, so it is a model-selection estimate rather than a second untouched test. No larger search or extra target tuning was performed.

## Frozen data and protocol

The established audit was reused, not rerun. Input SHA-256 identities were checked against it. Training behaviour is [2020-03-09 00:00:00, 2020-05-18 00:00:00); validation is [2020-05-18 00:00:00, 2020-07-27 00:00:00), in the fixed source wall-clock convention with timezone unknown. Previous-file airings carry into the next midnight window; canonical airings retain their complete original duration. Programme 0 is excluded, and previously watched IDs remain eligible.

Local truth remains up to five most-frequently qualified programmes, with an 80% longest merged-block requirement and ascending raw string ID ties. **Every held-out user/programme qualified count exactly matches the authoritative cleaned audit**, not merely the cohort size. No difficult users were removed. There are 108 users without qualified training history, of whom 44 have no soft training overlap. The main cohort excludes users with no qualified validation target, as frozen before modelling.

Training has 856,858 soft user-item pairs from 1,823,678 usable user-airings; validation has 659,721 soft pairs and 282,950 qualified user-airings. Sparse training axes contain 4,841 users and 2,973 items. Training strength is `s_ui = sum(union_overlap / full_airing_duration)`, with `w_ui = log1p(s_ui)`. Qualified counts are distinct from these soft strengths.

### Causal cleaning correction and leakage verification

For sessions completed by the cutoff, retain the audit’s duration-discrepancy and >24-hour exclusions. For sessions still ongoing at the cutoff, only the observed prefix can be known: apply the 24-hour rule to that prefix and do not use the future complete declared duration or stop time for discrepancy rejection. Rows starting at/after the cutoff are ignored before further preprocessing. This closes a future-tail dependence in the original full-session cleaning rule. On the actual data it changes **zero qualified training user-item counts**; validation truth is unchanged. The original audit remains a historical measurement.

The focused fixture covers file-boundary carryover, duplicate canonical broadcasts, original airing denominators after clipping, and a combined fitting window. Its two half-window 50% portions do not separately qualify, while the combined 100% airing qualifies exactly once; the final refit builder therefore recomputes the combined interval window rather than adding split counts. A full actual-data final refit has not been run.

The end-to-end fixture modifies strictly future behaviour, including a crossing session extended beyond 24 hours, and compares interactions, sparse features, ALS factors and predictions for all four methods. The additional full-data check removed 1,876,814 strictly future rows and extended 1,007 crossing tails to 14 days after the cutoff. It produced byte-equivalent training interaction records, identical fitted fingerprints, and identical predictions for all 4,649 users across every selected method. See `actual_data_cutoff_invariance.json`. Input hashes identify provenance, not model features.

## Method definitions and failure cases

Popularity ranks distinct qualified training viewers, then qualified user-airing totals, then string IDs. Personal frequency ranks each user’s qualified airing counts, then IDs. All methods complete unsupported slots with the same candidate-restricted popularity order and ascending IDs for zero-popularity candidates.

CBF uses sparse, L2-normalized category/genre multi-hot vectors (the three genre positions share a genre namespace) and normalized `w_ui`-weighted user profiles. Metadata uses the modal title/category/genre tuple over unique airings starting before the cutoff, breaking tuple ties lexicographically. Titles are displayed but are not content features. Of 6,384 candidates, **2,391 lack pre-cutoff metadata representations** and receive no direct CBF score; they remain eligible through shared completion. Permitted future schedule metadata are used only for availability and report display, not fitted content features.

After fixing score-to-ID candidate alignment, independent checks on 30 users and ten candidate scores per user agree with manually accumulated double-precision profiles/cosines within 1.31e-07. CBF has only 444 distinct candidate vectors, including the empty vector. 2,936 / 4,581 scored users have more than five exactly tied top candidates; the median top-score tie contains 22 items. The ID tie-break therefore frequently chooses among indistinguishable metadata representations. These diagnostics support limited item discrimination; they do not prove that metadata alone explains every error.

ALS uses positive sparse preferences and **observed confidence `1 + 40*w_ui`, with library `alpha=1.0`**. The [official CPU ALS documentation](https://benfred.github.io/implicit/api/models/cpu/als.html) describes sparse values as confidences and missing entries as preference zero/confidence one. The installed implicit 0.7.3 fit implementation was also inspected to confirm its optional alpha multiplication. Confidence is applied exactly once; its algebra is asserted in the integration check. See `als_confidence_check.json`. Only items with fitting-window interactions receive learned factors: **4,178 candidates lack trained ALS representations**, and can enter lists only through completion.

The bounded ALS search underperforms popularity, especially for history-rich users. Soft training overlaps include many programmes that never satisfy the stricter qualified-repeat target. This is a plausible mismatch to investigate, not a measured causal explanation. No unknown interactions are treated as explicit dislikes. Repeats were enabled and candidate filtering was identical across methods.

Native float32 matrix-vector scoring emitted overflow/invalid/divide warnings despite finite factors. Across 64 sampled users per ALS configuration, scores were finite and agreed with direct float64 contraction within 2.3e-7, with all sampled top-1 choices agreeing. Direct contraction also matched scalar `math.fsum` within 1.2e-16. The root cause of the native warnings is not established. Final scoring uses finite-checked float64 direct contraction; final fitting/inference logs contain no numerical warning. A nonfinite factor or score now fails explicitly.

Two earlier local attempts are retained under `preliminary_native_matmul/` and `preliminary_unordered_candidates/`. Their CBF scores are superseded: the candidate-ordering defect mixed up score rows and IDs. The final result is protected by a unique-category recommendation fixture. Do not cite preliminary metrics. The original 25 tests plus three focused tests all pass (28 total).

## History-size slices

History size is the number of distinct programmes with at least one qualified pre-cutoff airing, before candidate filtering. Slice users sum to 4,625 for every method.

| Qualified training items | Users | Popularity MAP@5 | Personal MAP@5 | CBF MAP@5 | ALS MAP@5 |
| --- | ---: | ---: | ---: | ---: | ---: |
| 0 | 108 | 0.163050 | 0.163050 | 0.087377 | 0.109046 |
| 1–5 | 462 | 0.155368 | 0.171129 | 0.051039 | 0.156975 |
| 6–20 | 2087 | 0.221042 | 0.285914 | 0.034262 | 0.126655 |
| 21+ | 1968 | 0.271052 | 0.393810 | 0.005292 | 0.027867 |

Personal frequency’s advantage grows with qualified history. For users without qualified history, its shared fallback equals popularity. The 108-user zero-qualified-history slice is broader than the 44-user zero-soft-history slice, so CBF/ALS can score some users whom personal frequency must fall back for.

## Fallback, catalogue coverage and repeats

| Method | Complete cold-start fallback users | Complete fallback: no available supported items | Partial completion users | Fallback slots / 23,125 | Distinct recommended IDs / 6,384 | Repeated-item share |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Global popularity | 0 | 0 | 0 | 0 (0.00%) | 5 (0.08%) | 81.91% |
| Personal repeat-frequency | 108 | 4 | 376 | 1446 (6.25%) | 707 (11.07%) | 95.99% |
| Content-based filtering | 44 | 0 | 0 | 220 (0.95%) | 449 (7.03%) | 14.12% |
| Implicit ALS | 44 | 0 | 0 | 220 (0.95%) | 806 (12.63%) | 67.10% |

Cold-start here means no qualified history for personal frequency and no soft interaction representation for CBF/ALS. Four additional personal-frequency users have history but none of its qualified items is available in the validation window. Popularity is intentionally a global method; its lists are not labelled fallback operations. Repeated-item share counts recommendation slots whose programme appears in any cleaned soft training history, with denominator 4,625 × 5. Catalogue coverage is distinct recommended IDs divided by the common 6,384 candidates. Larger catalogue coverage alone does not establish user value.

All seven model/configuration outputs contain five distinct, nonzero, available IDs for every predicted user. The four selected methods additionally pass the existing template validator for all 1,260 template users in original row order, using the exact 6,384-ID validation-window candidate set. These private files are **validation-window demonstrations**, not final weeks 31–42 submissions. Their paths and checksums are in `analysis.json` and individual method records.

## Two fixed example users

[Report-ready ranked IDs, original titles/categories, observed training aggregates and held-out hits](two_user_examples.md) use the same history-poor and history-rich users for every method. They were selected once by minimum/maximum qualified training item count among template users with positive training history, breaking ties by raw user ID. Selection did not use recommendation hits or model scores. Private user-ID mapping and detailed aggregates remain under ignored `artifacts/model_comparison_20261029/`.

The history-poor user has four soft-history programmes but only one qualified programme; no qualified validation target is observed. This user is outside the fixed metric cohort, so recommendations are marked **not evaluable**, not treated as negative labels. The history-rich user has 837 soft-history programmes and 183 qualified programmes. Their personal and popularity lists both hit programme 240081 at rank 2 (AP@5 0.10); the rich-history example illustrates that the overall winner still has failures. No replacement user was chosen to obtain a more favourable example.

## Reproducibility, provenance and next experiment

The prior ChatGPT-generated foundation and audited branch were reused. All new implementation, execution and automated checks were performed by Codex; they do not constitute student verification. The original native session transcript remains unmodified and excluded from public Git; its actual location remains in the private provenance note created during the audit. Historical audit records are untouched.

Python 3.10.11 on macOS 26.6.2 arm64, 24 GiB physical RAM established by the audit. Runtime versions: numpy 2.2.6, scipy 1.15.3, implicit 0.7.3, threadpoolctl 3.7.0, tqdm 4.70.1. `requirements.txt` pins runtime packages; `dependencies_full.txt` also records tooling. Seed 42; no GPU; ALS and numerical-library threads set to one. Each method JSON includes base Git commit, dirty-tree state, source hashes, configuration, dependency versions, output hash, runtime and RSS.

Cold extraction took 33.36 s for training and 24.26 s for validation. The final cached preparation took 5.33 s. The runner’s timed comparison through model selection took 28.66 s; subsequent example rendering and diagnostic commands are separate. The full-data cutoff check took 52.47 s. Cache manifests identify full input checksums, code hashes, exact windows, cleaning configuration and interaction-file digests. Cache lookup validates configuration and output checksum before reuse. Original raw inputs were never rewritten.

**Recommended next experiment:** change only CBF’s tie-break among exactly equal cosine scores from raw ID order to pre-cutoff qualified-viewer popularity, keeping features, soft weights, truth, cohort, candidates and shared fallback unchanged. The measured frequency of large exact ties makes this a concrete test of item discrimination at ranking time; improvement is a hypothesis. Keep the current CBF result as the comparator. After these individual results, simple reciprocal-rank fusion with personal frequency can be considered, but no fusion was run here. Do not refit or submit to Kaggle until a later authorized stage.
