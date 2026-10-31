# Fixed historical LightGBM reranker

The frozen design is in [lightgbm_reranker_protocol.md](lightgbm_reranker_protocol.md). The experiment uses the existing audited interaction pipeline; it does not rerun the audit or train on main/auxiliary validation labels.

Install `requirements-reranker.txt` in the established Python environment. The measured runtime used Python 3.10.11, LightGBM 4.6.0, scikit-learn 1.7.2 and the existing NumPy/SciPy pins. On this macOS ARM64 host, the LightGBM wheel required OpenMP; Homebrew libomp 23.1.3 was installed with `HOMEBREW_NO_AUTO_UPDATE=1 brew install libomp`. Other hosts need their platform's working OpenMP runtime. No credentials or raw data belong in Git.

```bash
python -m pip install -r requirements-reranker.txt
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 python -m src.experiment_lightgbm_reranker --data-dir "$HOME/LLM4Rec-Course-codex/data/sweettv/raw"
python -m unittest discover -s tests
python -m src.report_lightgbm_reranker
```

LightGBM explicitly uses four threads; the environment variables limit unrelated numerical-library pools. The classifier is fit exactly once on all candidate rows at the two earlier origins. There is no early stopping, negative sampling, tuning or reweighting. Final application, if qualified, reuses those exact classifier weights and recomputes only causal features/retrieval. Use a new versioned run/output directory to preserve existing evidence; the default existing artifact must not be overwritten. The code refuses to overwrite a candidate CSV.

Private features, labels, user/item row metadata, model weights and predictions remain under ignored `artifacts/`. Public output contains aggregate evidence only. Candidate CSVs are validated for manual review; this module contains no Kaggle upload workflow.

## Reference and independent implementation

The user supplied [3_final_model.ipynb](https://github.com/ndmel/2nd_place_recsys_cinema_challenge_2020/blob/main/3_final_model.ipynb) and [utils.py](https://github.com/ndmel/2nd_place_recsys_cinema_challenge_2020/blob/main/utils.py). Inspected Git blob SHAs are `5626149f36a62ed8de9abd3e6ea882c946882fca` and `a96378556c471e6119d2ac8744ef3a8ce7785af9`, respectively. The inspiration is supervised binary boosting of frequency/rank/collaborative features. The reference's threshold helper defaults to five rows per user and is invoked from feature enrichment without overriding that default; our feature extractor retains all threshold counts. We did not copy its preprocessing, validation split, LightFM/content/schedule-change features, hyperparameters or early-stopping procedure.
