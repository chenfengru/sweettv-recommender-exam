# Fixed longer-horizon historical training

Use the established modelling environment and verified private v12/v14 origin caches. Histories and identity models are reused; only historical label windows, availability/candidate tables and future schedule features are rebuilt. Main/auxiliary/final arrays are read unchanged from v14.

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 python -m src.experiment_long_horizon --data-dir /absolute/path/to/raw
python -m unittest discover -s tests -v
```

The single configuration is frozen in `docs/long_horizon_protocol.md` and its result-side JSON hashes. The runner refuses to overwrite an existing classifier. If evaluation is interrupted after fitting, `--resume-frozen-classifier` loads and verifies its saved hash without fitting again. Do not overwrite completed evidence or test additional horizons. The measured run completed with one fit and no resume. Saved LightFM arrays are inference-only; item-item reconstruction is checked against original candidates/behavioural features before use.

The observed Python/dependency versions, fixed parameters, runtime, process-lifetime peak RSS, label manifests, feature distributions and importance are recorded in `results/long_horizon_20261030_v16/`. Private user tables, labels, models and original native session records stay outside Git. The same frozen classifier can produce a final CSV only if both evaluation differences are positive. This run failed and created no CSV. Kaggle uploads remain manual-only.
