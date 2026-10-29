# Project instructions

## Task context

Read README.md, docs/exam_requirements.md, and docs/experiment_protocol.md before implementation. The current implementation brief is docs/phase_1_codex_task.md.

This is an individual LLM4Rec exam project. Prioritize understandable, reproducible code and verifiable evidence.

## Evidence and scope

- Mark status accurately: planned, implemented, executed, or verified. Never manufacture data statistics, experiment scores, benchmark claims, screenshots, references, or AI-session exports.
- Distinguish instructor-reported statistics from measurements made on the actual files.
- Do not describe an AI-performed check as a check personally performed by the student.
- Use the instructor's original instructions if this project summary disagrees with them.
- Completing Phase 1 does not require training recommendation models or submitting predictions to Kaggle.

## Data and evaluation

- The user keeps SWEET.TV data in the existing local course workspace: `$HOME/LLM4Rec-Course-codex/data/sweettv/raw/`. Pass this location explicitly to `--data-dir`; see data/README.md. Check the actual filesystem in the user's Codex environment before claiming the files exist or moving anything.
- Never commit raw competition data, credentials, or original AI-session exports.
- Because the data directory is inside the separate course checkout, ensure that checkout excludes `/data/sweettv/` locally. This exam repository's ignore rules do not cover another checkout.
- Use the real submission template for column names, user order, and prediction serialization; do not infer its schema from this plan.
- Keep K=5. Use identical temporal splits, candidate sets, repeat policies, fallback rules, and evaluation users across methods.
- Fit behavioural features and models on data before the prediction cutoff. Retain the designated hold-out for evaluation and model selection.
- A reranker requires earlier temporal training examples; never fit it on the same labels used to report hold-out performance.
- Programme ID 0 is not an item. Missing identifiers or missing observations are not evidence of dislike.
- Use the permitted future schedule for programme availability, channel, and time; never use future viewer behaviour.
- Prefer sparse or streaming operations. Do not materialize a channel-only many-to-many join or a dense user-by-programme table.
- Record deterministic seeds, input checksums, exact cutoffs, configurations, command lines, environment, runtime, and peak memory when available.

## Engineering

- Inspect actual headers and timestamp/duration units before writing conversion logic.
- Preserve the source spelling duraton at input and explicitly map it to a documented internal field.
- Use meaningful small tests for interval overlap, temporal boundaries, MAP@5, and submission validity.
- Keep an independently computed small-example reference for the optimized interval matcher.
- Update documentation when a previously unresolved protocol decision becomes fixed.
- Keep commits focused and do not overwrite unrelated user changes.
