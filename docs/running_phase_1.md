# Reproducing the real-data audit

The audit was completed locally on 29 October 2026 using Python 3.10.11 and only the standard library. [Results](../results/local_audit_20261029/audit_review.md) and [exact executed commands](../results/local_audit_20261029/commands.txt) are recorded separately from historical missing-input/synthetic runs. No model or Kaggle submission exists yet.

Run from the exam repository root, using a fresh result directory if preserving a previous run:

```bash
python3 -m unittest discover -s tests -v
python3 -m src.audit_data --data-dir /Users/chenfengru/LLM4Rec-Course-codex/data/sweettv/raw --output-dir results/reproduced_audit --view-time-format wall-iso --schedule-time-format wall-dmy --view-duration-unit seconds --schedule-duration-unit seconds --template-user-column user_id
python3 -m src.audit_anomalies --data-dir /Users/chenfengru/LLM4Rec-Course-codex/data/sweettv/raw --output-dir results/reproduced_audit --private-dir artifacts/reproduced_audit
python3 -m src.real_matching_audit --data-dir /Users/chenfengru/LLM4Rec-Course-codex/data/sweettv/raw --output-dir results/reproduced_audit/cleaned --private-dir artifacts/reproduced_audit/cleaned --exclude-suspect-views
```

The profiler returns 2 because measured anomalies require review; it still writes complete profiles. Do not chain it with `&&` when intending to run follow-up diagnostics. See the review for dispositions. Wall-clock conversion does not assign UTC or any named timezone. The matching audit carries previous-file broadcasts into the next midnight window, unions duplicate/overlapping user-channel logs, and uses full-airing durations. Its raw-row sample remains an explicitly labelled sample of original rows, including rows excluded from cleaned interactions.

Exact counts/cardinalities/duplicates and schedule unions use all records. Quantiles use reservoirs of 10,000 values, seed 42 (residuals 43). The matching raw-row reservoir uses Algorithm R, seed 42. Code hashes, input SHA-256, runtime and peak RSS accompany the results. Allow several GiB of disk space for ignored SQLite scratch files. Aggregate results may be versioned; private histories, examples and native transcripts must stay outside public Git.

For later submission-file checking, use the actual columns `--user-column user_id --prediction-column tv_show_id`, the original template, and the final-window schedule **including known preceding-file carryovers**. The current validator can accept multiple `--schedule` inputs but reads full-file candidate IDs; the next-stage implementation must supply a window-filtered schedule/candidate export so outside-window tail IDs cannot pass accidentally. Preserve all 1,260 template rows in source order, with five distinct nonzero IDs separated by single spaces. No prediction file is fabricated in this audit.

The [modelling specification](experiment_protocol.md) fixes labels, confidence weights, cutoffs, shared fallback, cohort and the four-method comparison. Implement the interaction builder and end-to-end leakage check before training. Student verification remains pending; inspect the private source-indexed real example before recording personal verification.
