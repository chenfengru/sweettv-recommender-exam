# Reproducing the selected v18 pipeline

This guide records the actual implemented dependency order, not a claim that a clean clone can run the final experiment in one command. **No training was rerun during instructor-review preparation.** The saved final CSV and all historical reports remain unchanged.

## Inputs and environment

Obtain the original five files from the coursework source (not from Git):

- `dataset11-30.csv`: viewing records; preserve the source `duraton` spelling.
- `export_arh_11-20-final.csv`, `export_arh_21-30-final.csv`: historical schedules.
- `export_arh_31-42-final.csv`: final forecast schedule, including boundary carryovers.
- `submission.csv`: original template header and user order.

Use the files whose checksums are recorded in `results/lightgbm_reranker_20261030_v12/selection.json` (`input_sha256`). Put them outside Git; the measured location is `/Users/chenfengru/LLM4Rec-Course-codex/data/sweettv/raw`. The source clock is naive wall time; no timezone conversion is justified.

The measured environment is Python 3.10.11, NumPy 2.2.6, SciPy 1.15.3, implicit 0.7.3, LightGBM 4.6.0, scikit-learn 1.7.2 and LightFM 1.17. Existing requirements files are nested; install the final one:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-lightfm.txt
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1
SWEETTV_DATA_DIR="/absolute/path/to/the/five/original/files"
.venv/bin/python -m unittest discover -s tests -v
```

LightGBM requires a working OpenMP runtime. The measured macOS ARM64 setup used Homebrew libomp 23.1.3; LightFM used its single-thread backend, matching the fixed one-thread fit. Source compilation may need a platform compiler. These dependency/platform constraints matter for numerical replay and frozen hashes.

## Actual producer order

The following are existing CLI entry points, listed in the original dependency order with the paths used by downstream scripts. **This is a historical replay recipe, not an in-place rerun instruction.** Run only in an isolated working copy after resolving the guard restrictions below; published results and submission files already exist in this checkout and must not be overwritten. These commands were inspected, not executed for this review.

```bash
# 1. Original main interactions, targets, metadata/mapping, individual models.
.venv/bin/python -m src.compare_models --data-dir "$SWEETTV_DATA_DIR" --output-dir results/model_comparison_20261029 --private-dir artifacts/model_comparison_20261029

# 2. Combined-window interaction cache and final available-programme export.
.venv/bin/python -m src.first_submission --data-dir "$SWEETTV_DATA_DIR" --output-dir results/first_submission_20261029 --private-dir artifacts/first_submission_20261029

# 3. Legacy personal baselines and auxiliary-cache producer.
.venv/bin/python -m src.experiment_personal_ties --data-dir "$SWEETTV_DATA_DIR" --output-dir results/personal_ties_20261030_v3 --private-dir artifacts/personal_ties_20261030_v3
.venv/bin/python -m src.experiment_opportunity_week --data-dir "$SWEETTV_DATA_DIR" --output-dir results/opportunity_week_20261030_v4 --private-dir artifacts/opportunity_week_20261030_v4
.venv/bin/python -m src.experiment_personal_threshold --data-dir "$SWEETTV_DATA_DIR" --output-dir results/personal_threshold_20261030_v5 --private-dir artifacts/personal_threshold_20261030_v5

# 4. Original item-item neighbours and frozen evaluation-cohort controls.
.venv/bin/python -m src.experiment_item_item --data-dir "$SWEETTV_DATA_DIR"
.venv/bin/python -m src.experiment_fifth_replacement --data-dir "$SWEETTV_DATA_DIR"

# 5. Original historical candidate tables, labels and 27 behavioural features.
.venv/bin/python -m src.experiment_lightgbm_reranker --data-dir "$SWEETTV_DATA_DIR"

# 6. Seven schedule-exposure features, six LightFM features, twelve channel features.
.venv/bin/python -m src.experiment_schedule_reranker --data-dir "$SWEETTV_DATA_DIR"
.venv/bin/python -m src.experiment_lightfm_extension --data-dir "$SWEETTV_DATA_DIR"
.venv/bin/python -m src.experiment_channel_affinity --data-dir "$SWEETTV_DATA_DIR"
```

The auxiliary opportunity/week experiment and fifth-replacement stage appear here because the original experiment scripts use their generated caches/control predictions and frozen cohorts. Their alternative ranking formulas are **not** components of v18. V15 candidate expansion, v16 longer labels, v17 LambdaRank and v19 time affinities are not part of the selected pipeline.

| Generated private intermediate | Producer / purpose |
| --- | --- |
| `artifacts/model_comparison_20261029/` | `compare_models`: main cleaned SQLite views/segments, interactions, targets, original metadata and private example-user mapping; not a supplied dataset |
| `artifacts/first_submission_20261029/combined_fit/` | `first_submission`: recomputed [Mar9,Jul27) qualification, never a sum of separately qualified windows |
| `artifacts/opportunity_week_20261030_v4/auxiliary/` | `experiment_opportunity_week`: [Mar9,Jun1) history and [Jun1,Jul27) targets |
| `artifacts/item_item_20261030_v7/` | `experiment_item_item`: fixed N50 neighbours and support statistics |
| `artifacts/fifth_replacement_20261030_v9/` | Legacy evaluation-cohort/control predictions read by v12; no E2 in v18 |
| `artifacts/lightgbm_reranker_20261030_v12/` | `experiment_lightgbm_reranker`: original Apr6/Apr20 rows/labels, main/auxiliary/final row indexes and 27 features |
| `artifacts/schedule_reranker_20261030_v13/` | `experiment_schedule_reranker`: 34-feature arrays and classifier |
| `artifacts/lightfm_extension_20261030_v14/` | `experiment_lightfm_extension`: origin-specific positive-support mappings, WARP predictive arrays, 40 features and classifier |
| `artifacts/channel_affinity_20261030_v18/` | `experiment_channel_affinity`: 52 features, one frozen selected classifier and predictions |

Every private cache is a **generated intermediate**, deliberately excluded from Git. The five original CSVs are the external data inputs. Public results are aggregate evidence/frozen run manifests; private cache files are not downloadable prerequisites disguised as source data.

### Current fresh-clone replay restrictions

1. Several historical runners have fixed downstream paths, frozen `source_artifact_sha256` dictionaries and explicit refusal to overwrite existing versioned CSVs/models. Merely passing a new `--private-dir` does not relocate every dependency. Existing tracked CSVs are controls for later stages, while their producing stages refuse to replace them.
2. Before full replay, an isolated replay driver must explicitly separate output copies from published controls and populate/verify freshly generated source-artifact hashes for that replay. No such all-in-one driver currently exists. Do not delete published files or bypass guards in this review checkout. Do not present the sequence above as a verified clean-clone bootstrap.
3. The main/auxiliary/final origin tables for v18 are derived by the preceding producers. The v18 command alone cannot regenerate missing v12/v13/v14 artifacts. The exact paths and producers are listed above so the dependency is explicit.
4. Independently regenerated models may fail the original exact-hash guards on a different numerical backend. Preserve the original evidence and record new-run hashes instead of claiming bitwise identity without verification.

These are remaining reproducibility-packaging limitations, not missing competition files on the measured machine. Local cached artifacts needed for instructor-review checks and the completed example recovery are present. Training was not rerun to work around these restrictions.

## Checks that do not fit models

Validate the exact final CSV from the original template and the recorded final availability export:

```bash
.venv/bin/python -m src.validate_submission --template "$SWEETTV_DATA_DIR/submission.csv" --predictions submissions/candidate_lightgbm_channel_affinity_20261030_v18.csv --schedule results/first_submission_20261029/final_window_candidate_ids.csv --user-column user_id --prediction-column tv_show_id --delimiter ,
shasum -a 256 submissions/candidate_lightgbm_channel_affinity_20261030_v18.csv
```

Expected SHA-256: `a62d1afb1a0c015cb70fd60c1e89bb670b731f872b3433dc438526a5ae703c45`. The availability export is generated by `first_submission`; it contains programme IDs, not user histories.

The original two-user identities remain only in the generated private setup mapping. With the verified caches available, the inference-only recovery implementation is:

```bash
.venv/bin/python -m src.recover_v18_examples --data-dir "$SWEETTV_DATA_DIR" --private-dir artifacts/final_report_examples/new_v18_main_recovery
```

Choose a new ignored output folder. This reads the existing original mapping, reconstructs 52 main-window features, verifies them bit-for-bit against the heavy control, and applies the saved classifier without fitting. It updates only the anonymized report/check evidence; it does not change original model outputs or add the light user to the scored cohort. The light user's AP@5 remains not evaluable. Recovery code was included from the executed recovery, and its CLI/syntax checked during review preparation; no model inference was repeated during that preparation.

The selected model was trained only on [Apr6,Apr20) and [Apr20,May4) labels. Main and auxiliary use their own targets; final inference uses [Jul27,Oct19) schedule availability. The light-user example is never scored using final-window submission predictions. Student verification and original native session records remain separate personal coursework deliverables; automated checks do not establish independent student review.
