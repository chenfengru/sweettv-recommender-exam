# SWEET.TV Recommender Exam

Individual TV-programme recommendation project for LLM4Rec (FKN).

**Current status: Phase 1 foundations implemented and checked on synthetic fixtures.** The original five CSV files are still missing. No real-data statistics or model scores have been measured, no models have been trained, and no Kaggle prediction has been submitted. See [the data audit status](results/data_audit.md) and [executed checks](results/phase1_checks.json).

本仓库先固定任务与评估口径，再按阶段完成数据审查、推荐模型、比较实验和报告。

## Start here

1. [Exam requirements](docs/exam_requirements.md): mandatory deliverables and scoring.
2. [Experiment protocol](docs/experiment_protocol.md): proposed design, assumptions, and unresolved decisions.
3. [First Codex task](docs/phase_1_codex_task.md): data audit and small-scale verification.
4. [Data location](data/README.md): obtain and store the five original files locally.
5. [Run Phase 1](docs/running_phase_1.md): audit, tests, limitations, and the next command.
6. [Student verification](docs/student_verification.md): small examples to check personally; not yet completed by the student.

## Run the implemented tools

Use Python 3.11 or newer. Phase 1 has no third-party Python dependencies.

```bash
python -m unittest discover -s tests -v
python -m src.audit_data --data-dir data/raw --output-dir results
```

The second command currently writes a missing-input report and exits with code 2. After the five original CSVs are available, the same command profiles their schemas and raw values. Timestamp units, duration units, timezone, and template column roles are deliberately not guessed. Follow [the run guide](docs/running_phase_1.md) before converting intervals or training a model.

## Task and deadline

- Recommend exactly five distinct, nonzero programme IDs per test user, in preference order.
- Metric: MAP@5.
- Deadline: **1 November 2026, 19:00 Europe/Moscow (UTC+3)**.
- Individual submission. The cohort's top 20% by returned Kaggle private score receives 50 ranking points; coursework evaluation contributes the other 50 points.
- The old Kaggle leaderboard is frozen. It does not show the current exam cohort's ranking.
- The user reports a limit of five submissions per day.
- [Kaggle competition](https://www.kaggle.com/competitions/sweettv-tv-program-recommender)

## Planned methods

| Method | Role |
| --- | --- |
| Global popularity | Required reference baseline |
| Personal repeat-frequency | Extra diagnostic baseline; not counted as one of the two required methods |
| Content-based filtering | Required method 1 |
| Implicit-feedback matrix factorization | Required method 2 |
| Rank fusion or temporal reranking | Optional, after separate method evaluation |

Model choice and performance are not established by this plan.

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
