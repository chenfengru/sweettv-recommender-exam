# Run the fixed v15 expansion

Use the existing pinned modelling environment and private verified v12/v14 origin caches. Do not rebuild the audit or refit LightFM. Model weights and private row arrays remain ignored.

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 python -m src.experiment_lightfm_expansion --data-dir /absolute/path/to/raw
```

The runner refuses to overwrite a saved classifier. After an interrupted evaluation, add `--resume-frozen-classifier`: this loads and verifies the already fitted classifier and performs no further fit. The frozen protocol and source hashes are checked before execution; original features/labels and old artifact hashes are checked during/after execution. Do not overwrite completed evidence to try new configurations.

The measured run used Python 3.10.11, LightFM 1.17, LightGBM 4.6.0, NumPy 2.2.6, SciPy 1.15.3 and scikit-learn 1.7.2. LightFM uses the installed single-thread build, matching the original configuration. The first execution fit exactly one classifier; evaluation resumed after correcting a missing reporting import. See the report for separate runtime/memory records.

No final artifact is produced when either split fails the fixed qualification rule. The diagnostic cannot qualify or produce a CSV. All uploads are performed manually by the user.
