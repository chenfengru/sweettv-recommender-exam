# Fixed viewing-time affinity extension

Use the established modelling environment and original verified v18 caches. Histories come from cleaned pre-cutoff SQLite views, including unattributed observations; all original v18 rows/labels/52 features are read unchanged. No audit or behavioural-model refit is needed.

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 python -m src.experiment_time_affinity --data-dir /absolute/path/to/raw
python -m unittest discover -s tests -v
```

The single configuration is frozen in `docs/time_affinity_protocol.md` and result-side hashes. The runner refuses to overwrite a saved classifier. An interrupted evaluation can use `--resume-frozen-classifier` to load verified weights without another fit. The measured experiment completed with one fit and no resume.

Time bins use source-naive calendar seconds, no timezone conversion. User intervals are unioned across channels before clipping/binning; schedule intervals add across canonical airings/channels. Histogram duration and normalization assertions run for every profile. Available programme profiles must have positive mass. Preserve all old columns even where zero-profile flags are redundant.

The measured matrix-product code emitted platform floating-status warnings despite valid finite output. An independent elementwise-product/sum replay reproduced all six float32 columns bit-for-bit at both historical/evaluation origins, without fitting. Current feature construction uses the verified sums to avoid that warning path; input values and recorded model results are unchanged. Reproduce the full numeric check using:

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 python -m src.verify_time_affinity --data-dir /absolute/path/to/raw
```

Requested/effective parameters, versions, runtime, process-lifetime peak RSS, distributions, normalization errors and exact equality hashes are recorded in `results/time_affinity_20261030_v19/`. No candidate is produced unless both MAP differences are positive. This run fails and generates no CSV or final extension features. Private profiles/weights and native session records remain outside Git. Kaggle upload remains manual-only.
