# Running the local model comparison

The authoritative English report is [comparison_report.md](../results/model_comparison_20261029/comparison_report.md). The audited source data remain at `/Users/chenfengru/LLM4Rec-Course-codex/data/sweettv/raw`. No Kaggle submission or final model refit is performed by these commands.

From the exam repository root:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python -m src.compare_models --data-dir /Users/chenfengru/LLM4Rec-Course-codex/data/sweettv/raw --output-dir results/reproduced_comparison --private-dir artifacts/reproduced_comparison
.venv/bin/python -m src.diagnose_models --private-dir artifacts/reproduced_comparison --output-dir results/reproduced_comparison
.venv/bin/python -m src.check_cutoff_invariance --data-dir /Users/chenfengru/LLM4Rec-Course-codex/data/sweettv/raw --private-dir artifacts/reproduced_comparison --output-dir results/reproduced_comparison
.venv/bin/python -m src.report_comparison --data-dir /Users/chenfengru/LLM4Rec-Course-codex/data/sweettv/raw --output-dir results/reproduced_comparison --private-dir artifacts/reproduced_comparison
```

Use a fresh output/private directory to retain prior run records. The comparison checks the unchanged original input identities and the published aggregate audit-reference hashes before fitting. Its frozen guards require 4,625 users and 6,384 candidates. Public qualified-count hashes permit exact reconciliation without publishing or depending on private audit histories. No repeated data audit is needed.

The interaction cache validates input hashes, relevant source hashes, configuration, temporal bounds and output checksum. It stores sparse long-format user/item strengths and qualified counts in ignored JSON plus SQLite scratch records. The model stage uses sparse matrices; it never creates a dense user-by-programme table. Per-user score vectors are bounded by the candidate catalogue. All raw histories, fitted factors, private user mappings, predictions and the intentionally perturbed leakage-check CSV stay under ignored `artifacts/`.

`interactions.extract_interactions` accepts arbitrary explicit half-open fitting windows. For a future final weeks 11–30 refit, call it on the combined [2020-03-09, 2020-07-27) window and union/deduplicate canonical airings before computing fractions. Do not add the two comparison-window qualified counts. This combined-window behaviour is implemented and tested; no final actual-data model refit was run in this stage.

Per-method records contain fit/inference time, process peak RSS, dependency versions, source hashes, seed/configuration and prediction hashes. Timing excludes private JSON loading from the fit interval; process RSS includes imports and loaded records. Report metrics use 4,625 users; inference additionally covers every original template user, for 4,649 unique predicted users. Validation-template CSVs are explicitly local validation-window demonstrations and remain private; they are not final competition submissions.

The examples use the same two users chosen solely by pre-cutoff qualified-history size. The history-poor example has no qualified held-out target and is marked not evaluable rather than counted as a miss. Detailed identities remain private. Student verification is still pending. Preserve the original native AI-session record separately; do not commit it.
