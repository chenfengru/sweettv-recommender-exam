# Fixed identity-only LightFM feature extension

The frozen experiment is [lightfm_extension_protocol.md](lightfm_extension_protocol.md). It preserves v13’s original candidate rows, historical labels and 34 features, and appends exactly six support-aware features. Do not rerun the audit or regenerate the control model.

```bash
python -m pip install -r requirements-lightfm.txt
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 python -m src.experiment_lightfm_extension --data-dir "$HOME/LLM4Rec-Course-codex/data/sweettv/raw"
python -m unittest discover -s tests
python -m src.report_lightfm_extension
```

The measured environment uses LightFM 1.17, NumPy 2.2.6, SciPy 1.15.3, scikit-learn 1.7.2 and LightGBM 4.6.0. LightFM installed successfully from source on this macOS ARM64 host, with the `lightfm._lightfm_fast_no_openmp` backend. Its single-thread execution matches the explicit requested `num_threads=1`; no substitute algorithm was used. Actual installed constructor/fit/predict/bias APIs and dependency versions are recorded in `results/lightfm_extension_20261030_v14/installed_api.json`.

Each origin derives pre-cutoff binary N50 interactions using the established canonical segment cache. Only positive-support identities enter the deterministic raw-string-sorted mappings. Those mappings, N50 counts, predictive embedding/bias arrays and feature matrices are saved privately under ignored `artifacts/lightfm_extension_20261030_v14/`. Latent coordinates are never passed as classifier features.

Unsupported users/items receive zero score/rank if either side lacks support. User bias and item bias each require only their own side’s support. Explicit unsupported-user/item indicators disambiguate missing numerics from valid zeros. Ranks cover all available supported programmes, including repeats, not merely the candidate union.

A predeclared first-origin training replay checks identical mappings, sparse input, predictive arrays and all six feature columns. It is a deterministic reproducibility check, not a hyperparameter/configuration search. Other origins are independently fitted once; final-origin LightFM is fitted only after strict two-split qualification. The LightGBM classifier is fitted exactly once and remains frozen for validation/final inference.

Use fresh versioned output/private directories for any later authorized run; preserve current evidence and candidate files. Candidate CSVs are validated for manual review. There is no Kaggle upload workflow. Student verification and the unmodified native session record remain separate coursework requirements.
