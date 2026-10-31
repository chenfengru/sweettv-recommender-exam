# Local competition inputs

The user chose to keep the competition data in the existing LLM4Rec course folder. The dedicated location on the user's Mac is:

```text
$HOME/LLM4Rec-Course-codex/data/sweettv/raw/
```

This is an external data directory relative to the exam repository. Its actual contents have not been inspected from the assistant workspace. Create it locally, then download the original archive from [the competition data page](https://www.kaggle.com/competitions/sweettv-tv-program-recommender/data) using your own Kaggle account after accepting the competition rules. Extract the five original CSVs directly into this directory, without another nested archive folder.

```bash
SWEETTV_DATA_DIR="$HOME/LLM4Rec-Course-codex/data/sweettv/raw"
mkdir -p "$SWEETTV_DATA_DIR"
```

Expected files, according to the instructor's exam document:

- dataset11-30.csv
- export_arh_11-20-final.csv
- export_arh_21-30-final.csv
- export_arh_31-42-final.csv
- submission.csv

These inputs are not bundled with this repository. The supplied files were audited in the recorded experiment; their checksums are preserved in results/local_audit_20261029/data_audit.json. Verify any newly supplied copy against those identities rather than silently renaming a different dataset. See docs/reproducing_selected_model.md for the selected pipeline and generated-cache dependencies.

Before adding files in the existing course checkout, exclude `/data/sweettv/` in that checkout's `.gitignore` or local Git exclude file. The exam repository's `.gitignore` cannot protect data inside a different Git checkout. Do not commit raw competition data or Kaggle credentials to either repository.

From the exam repository root, pass the external location explicitly:

```bash
SWEETTV_DATA_DIR="$HOME/LLM4Rec-Course-codex/data/sweettv/raw"
python -m src.audit_data --data-dir "$SWEETTV_DATA_DIR" --output-dir results
```

`SWEETTV_DATA_DIR` is a shell convenience used in the documented commands; the Python script reads the explicit `--data-dir` argument. The historical report under `results/` is not proof that this Mac directory has been checked.
