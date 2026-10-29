# Modelling specification v1

Status: fixed local assumptions after the 29 October 2026 real-data audit; no model trained or Kaggle submission made. [Measured evidence](../results/local_audit_20261029/audit_review.md) and machine-readable run records distinguish observations from choices. Earlier foundation code was generated with ChatGPT; local execution and the added diagnostics were performed by Codex, not independently by the student. The historical implementation's target construction is accepted project context; it was not reviewed again.

## Clock and temporal split

Both sources contain timezone-free civil timestamps. Parse views with `wall-iso` (`YYYY-MM-DD HH:MM:SS`) and schedules with `wall-dmy` (`DD.MM.YYYY HH:MM:SS`). Represent them as seconds since a naive 1970-01-01 reference solely for arithmetic. These numbers are not verified UTC instants; do not apply the Mac's timezone. A common source clock with zero offset between sources is an explicit local assumption supported by matching coverage and checked actual examples. The 117 one-hour duration discrepancies occur across 29 March; a clock change is plausible, but neither the timezone name nor DST handling is proven.

| Phase | Fitting behaviour, half-open source wall time | Prediction window |
| --- | --- | --- |
| Comparison | [2020-03-09 00:00:00, 2020-05-18 00:00:00) | [2020-05-18 00:00:00, 2020-07-27 00:00:00) |
| Selected-model refit | [2020-03-09 00:00:00, 2020-07-27 00:00:00) | [2020-07-27 00:00:00, 2020-10-19 00:00:00) |

The 70/70/84-day windows follow the measured calendar ranges and retained week design. Midnight is the chosen reproducible cutoff, not a claim that every channel's schedule file begins then. Schedule files contain channel-specific broadcast-day tails extending to noon on the following Monday. Include all known airings intersecting the relevant window, carrying preceding-file airings across midnight. Clip viewing segments to the window; preserve the airing's original full duration as the watch-fraction denominator. Do not use rows lying wholly beyond the prediction window. For the final refit, partition and deduplicate the combined known schedules by canonical broadcast key.

## Cleaning and matching

1. Preserve raw inputs and string identifiers. Map source `duraton` to `declared_view_seconds`; use endpoint differences for interval arithmetic.
2. Exclude nonpositive intervals. Exclude viewing rows with `abs(declared_view_seconds - wall_elapsed_seconds) > 1` or `wall_elapsed_seconds > 86400` from both fitted interactions and local truth. The observed union of these suspect classes is recorded in the cleaned audit. This is a conservative quality assumption, not proof that long sessions are false.
3. Merge overlapping or touching intervals per user and channel. This removes duplicate log contributions without discarding legitimate repeated airings. Concurrent different-channel records remain separate exposures; do not interpret their summed time as unique human attention.
4. Exclude schedules with duration <= 0. Deduplicate broadcasts on `(channel_id, start, end, tv_show_id)` while retaining metadata conflicts for inspection. No source row is rewritten.
5. Use the existing same-channel half-open interval matcher; allocate actual overlap to every intersecting broadcast. Union segments per user-airing before measuring time. ID `0` supplies coverage diagnostics only.
6. Where different nonzero IDs overlap on one channel, exclude both entire conflicting broadcasts from training/label attribution as a conservative rule. None occur in the two behavioural periods; four conflicting pairs occur in the future schedule. Their IDs remain permitted candidates because availability is still observed.

## Validation truth, separate from training confidence

For each cleaned user-airing pair, merge touching/overlapping viewing segments on that channel. Let `L_ua` be the longest merged block and `D_a` the original airing duration. A qualified airing satisfies `L_ua / D_a >= 0.8`. Count qualified airings by user/programme. Local truth is the first up to five distinct available programme IDs sorted by descending qualified-airing count, then ascending raw string programme ID. Do not count a source duplicate as another airing.

The 80% threshold retains thousands of evaluable users; measured 50/80/90% sensitivity is in the audit. Summing disconnected blocks yields more positives, so the longest-block choice deliberately requires stronger session evidence. This remains an observed-session proxy, not confirmed uninterrupted attention. Top-five frequency follows the established historical implementation as a local hypothesis; the hidden evaluator is unknown. Freeze this target before model comparisons and never choose the target definition by whichever gives a better score. An all-qualified-ID target may be reported only as a separately labelled sensitivity analysis.

Main cohort: all observed users with at least one qualified held-out target, including users without qualified training history. Report excluded users, template overlap, and cold-start counts. Use the identical user set and truth for all four methods. Empty-truth AP is defined as zero by the metric utility but those users are outside the main local cohort; report an all-observed-user diagnostic separately if used.

## Training interactions and methods

For every cleaned user-airing pair with positive overlap, define `q_ua = union_overlap_seconds / D_a`, capped at 1. Aggregate `s_ui = sum(q_ua)` across pre-cutoff airings of programme i. Use `w_ui = log(1 + s_ui)` for the initial CBF profile and MF strength. There is no minimum watch-fraction threshold for this softer training signal and no recency term initially. Programme normalization avoids making duration alone dominate; unioning prevents duplicate sessions from increasing confidence. These are initial modelling choices, not measured optimal weights.

| Method | Initial specification |
| --- | --- |
| Global popularity | Number of distinct qualified training viewers; break ties by qualified training user-airing count, then ascending string ID |
| Personal repeat-frequency | Qualified training airing counts per user; same deterministic ID tie-break; complete using shared popularity |
| Content-based filtering | Sparse category/genre multi-hot vectors, L2 normalized; user profile is the normalized weighted sum using `w_ui`; cosine score |
| Implicit MF | Sparse implicit ALS; preference `p_ui = 1[s_ui > 0]`, confidence `c_ui = 1 + 40*w_ui` for observed interactions and 1 for unobserved pairs; seed 42 |

The MF confidence multiplier 40 is an initial assumption. Freeze a small search budget before running: factors {32, 64}, regularization {0.01, 0.1}, 20 iterations; select on the unchanged hold-out. Verify the chosen library's confidence convention before implementation. CBF starts with category/genre only. Build metadata representations from airings starting before the fit cutoff; use the modal tuple per item, breaking tuple ties lexicographically. Do not fit text vocabulary, feature weights, or profiles on held-out behaviour. Future schedule channel/time/availability are allowed; future behaviour is forbidden. Conflicting titles/categories are not a reason to merge programme IDs.

## Shared candidates, repeats, and fallback

A candidate is a distinct nonzero ID with a positive-duration airing intersecting the prediction window, including known preceding-file carryovers. Use exactly the same candidates across methods. Previously watched programmes remain eligible. Complete every list using the qualified-viewer popularity order restricted to candidates, excluding IDs already selected. Candidate IDs with no training popularity follow in ascending raw string ID. This guarantees a deterministic five-ID fallback if at least five candidates exist. Users without model representations use this same ordering. Keep final template row order and headers `user_id,tv_show_id`; serialize five distinct IDs with single spaces.

## Concrete next task

Implement a reusable, disk-backed interaction builder following this specification, then run popularity, personal-frequency, CBF, and implicit MF on the fixed hold-out. Check that changing post-cutoff behaviour cannot change fitting features, parameters, or predictions. Confirm candidates and truth are contained in the documented windows and final predictions cover all 1,260 template users. Record MAP@5, cohort counts, history-size slices, fallback share, catalogue/repeat coverage, environment, runtime and peak RSS. Select the same history-rich and history-poor users from pre-cutoff history for all methods; preserve their user-level evidence privately and use IDs/titles/categories in the later report. No training or submission belongs to this audit round.

After comparison, refit the selected configuration on weeks 11–30 and validate the exact final CSV. A later designated Kaggle submission must be recorded with its returned private score and screenshot; the daily limit is five. The course submission remains exactly the report PDF and the original unmodified AI-session export. Keep raw data, credentials and session exports out of public Git. Student verification remains pending until personally performed.
