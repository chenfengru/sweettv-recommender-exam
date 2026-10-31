# Fixed LambdaRank reproduction

Use the established modelling environment (LightGBM4.6.0) and original verified v12/v14 private caches. No v15 expanded rows or v16 longer targets are used. Historical rows are already contiguous by user; queries remain separate across origins.

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 python -m src.experiment_lambdarank --data-dir /absolute/path/to/raw
python -m unittest discover -s tests -v
```

The protocol and source hashes are frozen in `docs/lambdarank_protocol.md` and `results/lambdarank_20261030_v17/frozen_experiment.json`. The run refuses to overwrite a saved ranker. If evaluation is interrupted after fitting, `--resume-frozen-ranker` verifies and loads the saved weights without fitting again. The measured run completed with one fit and no resume.

All original feature and label files are preserved byte-for-byte; group sizes sum exactly to row count. No query weights, sampling, tuning or early stopping are used. Effective parameters, installed API signature, dependency versions, per-origin query statistics, feature importance, runtime and process-lifetime peak RSS are recorded in the result folder. Scores remain raw ranking scores, with v14 tie/fallback rules; binary probability validation is not applied to them. Main/auxiliary/final inputs reuse original v14 files with exact hash verification.

A candidate can be generated only if MAP@5 strictly improves on both splits; NDCG@5 is diagnostic only. This run fails and creates no CSV. Private rows/query keys/model weights and native session exports remain outside Git. Kaggle uploads remain manual-only.
