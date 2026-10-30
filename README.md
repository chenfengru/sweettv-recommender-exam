# SWEET.TV Recommender Exam

Individual TV-programme recommendation project for LLM4Rec (FKN).

**Current status: retain submitted v5; fixed item-item retrieval merits a later controlled fusion/reranking experiment.** Standalone item-item MAP@5 is **0.155453093093 / 0.157389530520**, far below v5’s **0.334711171171 / 0.331395910511**. Top-50 unseen retrieval adds **3,435 / 3,224** relevant items to personal history, raising micro coverage to **74.22% / 73.93%**. This is a retrieval gain, not an improved final ranker. [Full English report, recall definitions, slices and resource evidence](results/item_item_20261030_v7/comparison_report.md). All **53 tests pass**. No fusion, final refit, CSV or Kaggle action was produced. Previous artifacts/checksums and native session records are preserved; student verification is pending.

## Start here

1. [Exam requirements](docs/exam_requirements.md): mandatory deliverables and scoring.
2. [Experiment protocol](docs/experiment_protocol.md): proposed design, assumptions, and unresolved decisions.
3. [First Codex task](docs/phase_1_codex_task.md): data audit and small-scale verification.
4. [Data location](data/README.md): obtain and store the five original files locally.
5. [Run Phase 1](docs/running_phase_1.md): audit, tests, limitations, and the next command.
6. [Model comparison](results/model_comparison_20261029/comparison_report.md): executed results and next experiment.
7. [Student verification](docs/student_verification.md): small examples to check personally; not yet completed by the student.

## Run the implemented tools

For model comparison and the full test suite, first install the pinned environment using [the model-stage run guide](docs/running_model_comparison.md). The standalone audit CLI remains standard-library-only.

Phase 1 has no third-party Python dependencies; Python 3.10.11 was used successfully for the measured local run. Python 3.11+ remains suitable.

```bash
SWEETTV_DATA_DIR="$HOME/LLM4Rec-Course-codex/data/sweettv/raw"
python -m unittest discover -s tests -v
python -m src.audit_data --data-dir "$SWEETTV_DATA_DIR" --output-dir results
```

The supplied files remain in the external course data folder, locally excluded from Git. Use a fresh output directory to preserve previous execution records. The source timezone is unknown; follow the explicit wall-clock parsing and carryover-aware matching commands in [the run guide](docs/running_phase_1.md).

## Task and deadline

- Recommend exactly five distinct, nonzero programme IDs per test user, in preference order.
- Metric: MAP@5.
- Deadline: **1 November 2026, 19:00 Europe/Moscow (UTC+3)**.
- Individual submission. The cohort's top 20% by returned Kaggle private score receives 50 ranking points; coursework evaluation contributes the other 50 points.
- The old Kaggle leaderboard is frozen. It does not show the current exam cohort's ranking.
- The user reports a limit of five submissions per day.
- [Kaggle competition](https://www.kaggle.com/competitions/sweettv-tv-program-recommender)

## Compared methods

| Method | Role |
| --- | --- |
| Global popularity | Required reference baseline |
| Personal repeat-frequency | Extra diagnostic baseline; not counted as one of the two required methods |
| Content-based filtering | Required method 1 |
| Implicit-feedback matrix factorization | Required method 2 |
| Rank fusion or temporal reranking | Optional, after separate method evaluation |

The four individual methods were executed; optional fusion has not been run. See the comparison report for exact configuration, limitations and selection evidence.

## Repository conventions

- Implemented audit/evaluation code lives in `src/`, synthetic checks in `tests/`, and status/check records in `results/`. Model configurations will be added when the protocol is ready.
- Raw data, caches, credentials, and original AI-session exports remain outside version control.
- The exact final prediction CSV belongs in `submissions/`; this directory is deliberately not ignored.
- Retain the tool-native, unmodified AI-session export for course submission. Git history does not replace it.
- Cite any external implementations actually used. Separate proposed experiments from executed experiments, and AI checks from student checks.

## Sources

The requirements summary is based on the instructor's user-provided `exam_quiz_FKN.md` and homework guidelines. It is a summary, not a replacement for those originals.

- [Instructor's exam slides](https://docs.google.com/presentation/d/1xf9tJ0nU0L9GeSGxLQVT_-GzZ160rDSXKRVH5TD6MSE)
- [Historical second-place implementation](https://github.com/ndmel/2nd_place_recsys_cinema_challenge_2020)
- [Author's historical solution account](https://medium.com/data-science/two-layered-recommender-system-methodology-a-prize-winning-solution-c4bdb815b156)

Historical results are external references, not results reproduced in this repository.
