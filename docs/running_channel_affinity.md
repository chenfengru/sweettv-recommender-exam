# Fixed channel-affinity extension

Use the established modelling environment and verified original v14/private interaction caches. Read cleaned pre-cutoff SQLite views for raw channel exposure, including unmatched programme observations; read canonical matched segments for N50 user-airing counts. Direct exact raw string channel IDs are the established mapping. No raw data audit or behavioural model refit is required.

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 python -m src.experiment_channel_affinity --data-dir /absolute/path/to/raw
python -m unittest discover -s tests -v
```

The twelve features/settings are frozen in `docs/channel_affinity_protocol.md` and result-side JSON. Original 40-feature arrays, candidate row indexes and two-week labels are hash-verified and preserved. The runner refuses to overwrite a saved classifier; `--resume-frozen-classifier` can resume interrupted evaluation without refitting. The measured run completed in one fit with no resume.

Per-origin diagnostics report exact/full/trailing windows, feature distributions, denominator zeros, channel mapping and unmatched schedule-weight coverage, N50 consistency, finite52-column schema, runtime and process-lifetime peak RSS. Views are unioned within user/channel, with simultaneous channels summed in denominators. N50 counts remain separate qualified programme-airing observations. Missing schedule-channel mappings contribute zero without renormalization.

The final affinity features and exactly one candidate CSV are generated only after both MAP differences are positive. The same frozen classifier is applied without evaluation-label training. Both validators preserve original template order/header and five distinct nonzero available programme IDs including carryovers. Private histories, model weights and native session exports remain ignored. Kaggle upload is manual-only by the user.
