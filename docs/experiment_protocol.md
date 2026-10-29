# Experiment protocol - draft v0.2

**Status:** source-based analysis with implemented Phase 1 utilities checked on synthetic fixtures. No original CSV has been inspected or model run. Choices marked unresolved must be settled from data and task evidence before comparative experiments.

## Implementation evidence, 29 October 2026

- Implemented: streaming CSV audit, exact disk-backed per-file duplicate/cardinality counts, sampled duration quantiles, explicit timestamp/unit conversion, per-channel interval index with independent brute-force reference, segment-union diagnostics, AP/MAP, and template-based prediction validation.
- Executed: synthetic unit tests and a real input-availability audit. See [check results](../results/phase1_checks.json) and [audit status](../results/data_audit.md).
- Missing: all five original CSVs. No actual channel mapping, timestamp/duration unit, cutoff, coverage, label threshold, interaction weight, target, or template schema has been verified.
- The cutoff invariance check covers the interval matcher only. An end-to-end feature/model leakage check must be added with those components.
- The matcher preserves duplicate source rows. It exposes a union-duration helper but does not silently select a deduplication or continuity rule.
- Full-data runtime and memory remain unmeasured. The audit uses disposable on-disk SQLite indexes; the matcher keeps a schedule index in memory and streams view queries.

This implementation does not freeze the proposed target construction or replace any unresolved protocol decision below.

## 1. Main hypothesis

Repeated viewing is likely useful for this task. Compare it explicitly with global popularity, content similarity, and implicit collaborative preferences. A more complex method is retained only if measured validation benefit justifies its cost.

The public historical implementation is a reference, not a baseline already reproduced here. See [the original utils.py](https://github.com/ndmel/2nd_place_recsys_cinema_challenge_2020/blob/main/utils.py).

## 2. Temporal design

| Phase | Behaviour available for fitting | Prediction/evaluation window |
| --- | --- | --- |
| Initial method comparison | Weeks 11-20 | Weeks 21-30 |
| Final refit after selection | Weeks 11-30 | Weeks 31-42 |

Use actual timestamps to implement these boundaries after inspecting the files. Do not assume the week labels are ISO week numbers or invent calendar dates. Record the source timezone, timestamp unit, and exact boundary instants.

The 10-week validation horizon is reasonably close to the 12-week target horizon, but shorter training history and possible seasonal change limit comparability. This is a rationale, not evidence that local and Kaggle scores will correlate.

Clip crossing view intervals at the information cutoff; a training feature must never contain post-cutoff watch time. Auditing the held-out log is allowed, but its behavioural aggregates must not enter fitted features.

Optional reranking must use training examples generated from earlier temporal cutoffs inside the fitting period. The main hold-out remains unused for fitting. Do not train base models on an example's target period before generating its scores.

## 3. Matching viewing intervals to broadcasts

1. Map vsetv_id to channel_id and verify the mapping in the data.
2. Parse both sides' timestamps and verify schedule duration units independently.
3. Use half-open intervals [start, end) on the same channel.
4. Compute overlap_seconds = max(0, min(view_end, airing_end) - max(view_start, airing_start)).
5. A view may match multiple consecutive airings. Allocate actual overlap to each; do not assign the whole view using only its start time.
6. Exclude tv_show_id=0 from recommendable items; retain aggregate diagnostics about this airtime.
7. Detect duplicate logs, duplicated/overlapping schedule rows, impossible durations, and very long view intervals. Quantify anomalies before deciding how to repair or exclude them.

Use per-channel sorting plus an interval sweep, indexed lookup, or an equivalent bounded interval-join algorithm. Do not materialize all same-channel view/schedule pairs. Allow for genuine schedule overlaps and test multiple-match cases.

For repeated segments within one airing, distinguish:
- longest continuous viewing overlap; and
- union of viewing segments, without double counting overlapping intervals.

**Unresolved:** which continuity definition best matches the task's positives. Historical documentation mentions continuous watching; summing disconnected sessions may create a different target.

## 4. Positive labels and interaction weights

The log does not contain programme-normalized watch percentages. Derive them only after programme duration has been verified.

A source-code review found that the historical get_target:
- keeps rows with user_watch_perc >= 0.8;
- counts them by user and programme;
- keeps up to five most frequent programmes for each user.

This is evidence about that author's implementation, **not confirmation of Kaggle's hidden evaluator**. Before freezing local truth, determine whether the competition target is the user's five most-frequent qualified programmes or all qualified programmes. These produce different MAP@5 denominators and targets.

**Provisional candidate:** use an 80% continuous-overlap threshold and at most five most-frequent programmes for local truth if task evidence supports that construction. Freeze a deterministic tie-break and record its limitations. Otherwise document the supported alternative before comparing models.

Keep target construction separate from training confidence weights. Training may use lower-threshold counts, overlap duration, log-scaled frequency, and recency, without redefining validation truth per method.

Threshold choice must be justified with observed duration distributions and coverage. Do not tune the definition of success to make a model's score look better.

## 5. Candidates, repeats, and shared fallback

- For a given prediction window, use one candidate set of distinct nonzero IDs with labelled airings in that window's permitted schedule.
- Keep previously watched programmes eligible for every method.
- Use only pre-cutoff behavioural data for popularity, user profiles, and learned models.
- Initially build CBF attributes from permitted training-period metadata. Record item metadata conflicts and missing attributes; do not silently assume unrestricted use of every test-schedule field.
- For users with no usable history, return the same global-popularity list restricted to valid candidates.
- Proposed popularity: distinct qualified training viewers per programme; break ties by qualified airing count, then a deterministic ID order.
- Where a method has fewer than five supported scores, append unseen-in-the-list valid candidates using that same popularity order.
- Every output contains exactly five distinct, nonzero, valid IDs. If the candidate set itself has fewer than five IDs, report a data/protocol error instead of inventing IDs.

## 6. Methods to compare

| Method | Proposed definition | Main diagnostic |
| --- | --- | --- |
| Popularity | Global training viewer counts | How much is explained by common items? |
| Personal frequency | User's qualified programme counts, optionally recency-weighted | How much is repeat behaviour? |
| CBF | Category/genre and other documented attributes; normalized item vectors; user profile from training history | Can content help sparse histories? |
| Implicit MF | Sparse user-item interactions; confidence-weighted factorization | Does collaborative structure add value? |

Start CBF with structured category/genre features; add richer attributes only after auditing availability and consistency. Do not begin with LLM generation.

For MF, unobserved interactions are not known negative ratings. Use an implicit-feedback objective. Evaluate small configurations and record the actual package/API used rather than copying old code blindly.

A shared candidate pool does not require all models to have a trained representation for every candidate. Missing representations must use the documented shared completion policy and appear in diagnostics.

## 7. Metrics and cohort definition

Let R_u be the distinct held-out relevant IDs for user u. For K=5:

- P_u(r) = number of distinct relevant hits in the first r positions / r.
- AP_u@5 = sum over ranks 1..5 of P_u(r) times the relevant-hit indicator, divided by min(5, |R_u|).
- MAP@5 is the unweighted mean across the fixed evaluation cohort.
- A duplicate prediction earns no additional hit. The submission validator rejects duplicates.

**Proposed main validation cohort:** users with at least one qualifying held-out target, including those with no usable training history. Report the count excluded for having no evaluable target; do not imply unlabelled viewing proves disinterest. Freeze this policy identically across methods and reconcile it with any available official evaluator convention. The metric utility should separately define empty-ground-truth behaviour (return 0) for explicit use cases.

Generate final predictions for every template user, including cold-start users. Report validation overlap with the test-user list; if useful, add a clearly labelled test-user-overlap diagnostic without replacing the main cohort opportunistically.

Report:
- MAP@5 overall and by training-history size;
- user count in every slice;
- fraction of predictions using fallback;
- catalogue coverage and repeated-item share as descriptive measures;
- training/inference runtime, environment, and measured peak memory where available.

No fabricated online lift, engagement, satisfaction, or revenue claims.

## 8. Required coverage audit

Measure and name denominators separately:
1. nonzero-ID schedule-row fraction by period;
2. view-row fraction with any valid programme match;
3. fraction of logged viewing seconds matched to valid labelled airings;
4. template users with at least one usable training interaction;
5. candidate IDs lacking training interactions or usable content attributes.

For watch-time coverage, avoid double counting overlap across duplicate/overlapping schedule rows; describe whether concurrent viewing logs are counted per session or per user-time.

Do not convert the instructor's 10.8% schedule-row statistic into any of these other quantities.

## 9. Verification examples

Use synthetic examples to check code without claiming student verification:

- View 19:50-20:30; same-channel airings 19:30-20:00 and 20:00-21:00: overlaps 600 and 1800 seconds.
- Touching endpoints yield zero overlap; a different channel yields no match.
- Relevant {A,B,C}; prediction [A,B,D,C,E]: AP@5 = 11/12.
- Relevant {A,B,C}; prediction [D,A,E,B,C]: AP@5 = 8/15.
- Check duplicate predictions, empty truth, fewer-than-five truth IDs, and unknown IDs.
- Compare an optimized matcher against a simple brute-force reference on a small controlled sample.
- Verify that modifying post-cutoff viewer behaviour cannot change training features or predictions.

Provide a short separate checklist of examples the student can personally verify. Only record completion after the student actually performs it.

## 10. Experiment and submission discipline

Every result should record input hashes, code commit, protocol version, exact temporal cutoffs, method/configuration, seed, metric cohort size, scores, timing, and output location.

First implement and evaluate the four baseline/method rows. Try simple rank fusion next; use a learned reranker only if time and temporal training design permit. Freeze a small search budget before tuning.

With the user-reported daily quota of five, reserve an attempt for final correction. Submit meaningful candidates selected with local evidence; do not tune hundreds of decisions directly against the returned private score.

Private MAP@5 around 0.43 is an external historical reference and an aspirational target, not a verified full-mark cutoff. The actual ranking award depends on current-cohort results.

## 11. Two-user analysis

Choose users using pre-cutoff characteristics, such as one history-rich and one history-poor viewer. Use the same users for every method and show ID, title, category, past history, and held-out hits. Selection should not depend solely on obtaining flattering examples.

Explain failure cases supported by the actual outputs: missing item IDs, unavailable programmes, cold-start, concentrated popularity, sparse metadata, or unsuccessful generalization. An unfamiliar recommendation is not automatically valuable discovery.
