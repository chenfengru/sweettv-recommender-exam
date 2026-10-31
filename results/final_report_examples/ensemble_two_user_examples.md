# Selected four-seed ensemble: the original two users

Selected submission: **v20**, equal arithmetic mean of the original 52-feature channel-affinity LightGBM models, seeds 42/43/44/45. Exact same light (History Poor) and heavy (History Rich) identities as [the completed v18 examples](v18_two_user_examples.md) and [the original individual-method comparison](../model_comparison_20261029/two_user_examples.md); original private mappings were cross-checked, not replaced. Source user IDs remain private.

## Confirmed score provenance

| Model | User-screenshot-reported Private | User-screenshot-reported Public | Selection |
|---|---:|---:|---|
| v20 four-seed channel-affinity ensemble | 0.44124 | 0.44911 | Selected submission |
| v21 item-item affinity extension | 0.43970 | 0.44687 | Not selected |

These are user-supplied screenshot-reported results, not independently fetched. Submission IDs and timestamps are unknown and are not inferred. V21 is not used in this export; only the four original 52-feature v20 classifiers are applied.

## Window and inference checks

History **[2020-03-09, 2020-05-18)**; forecast and targets **[2020-05-18, 2020-07-27)**, source-naive wall time. No final-window list is compared with main targets. The original light user is outside the fixed target-bearing evaluation cohort, so saved main evaluation outputs omit that user. The previously recovered, verified main 52-feature rows are reused, with the same original identity, candidate construction and cutoff conventions. The heavy user’s entire recovered feature/candidate table is bitwise identical to the original main cache.

Four saved model checksums, 300-tree counts and exact 52-feature order were verified. Replayed seed 42 scores equal the saved private recovery scores bit-for-bit, and its ranked lists match the single-model examples. The four original-convention prediction-score vectors are averaged equally, before descending score/N50/global80-viewer/global80-airing/raw-string-ID tie-breaking and unchanged fallback. No calibrated probability interpretation is claimed. The heavy ensemble list exactly reproduces the saved v20 main prediction. All five recommendations per user are distinct, nonzero and in the unchanged 6,384-ID main universe. No retraining, tuning or future viewing.

Source titles/categories below come from the original schedule files using the same display-only canonical metadata convention as the prior examples; original-language strings are preserved. They do not enter a new model fit.

AP@5 uses the unchanged main top-five >=80%-qualified target set. The light user has no targets and remains **not evaluable**, including hit indicators, for every method; AP is not set to zero. Individual-method and v18 lists are preserved saved outputs, not retrained controls.

## Light user (original History Poor)

No qualified main-window targets; AP@5 and hit indicators are **not evaluable**.

| Rank | Programme ID | Source title | Source category | Main-target hit |
|---:|---|---|---|---|
| 1 | 12001682 | М/с 'Губка Боб Квадратные Штаны'. | Детям | not evaluable |
| 2 | 2400480 | ТСН. | Инфо | not evaluable |
| 3 | 240081 | Факты. | Инфо | not evaluable |
| 4 | 10001261 | Т/с 'Мыслить как преступник'. | Сериалы | not evaluable |
| 5 | 12002856 | М/с 'Элвиннн!!! и бурундуки'. | Детям | not evaluable |

| Method | Ranked programme IDs (1→5) | Relevant hits | AP@5 |
|---|---|---:|---:|
| Popularity | 2400480 → 240081 → 2400467 → 200344 → 2400508 | not evaluable | not evaluable |
| Original personal frequency | 90066849 → 2400480 → 240081 → 2400467 → 200344 | not evaluable | not evaluable |
| CBF | 10002484 → 10002525 → 10002578 → 10002674 → 10003051 | not evaluable | not evaluable |
| ALS (32 factors, regularization 0.1) | 90070560 → 10001072 → 10001085 → 90066849 → 10001711 | not evaluable | not evaluable |
| V18 single seed 42 | 12001682 → 2400480 → 240081 → 10001261 → 12002856 | not evaluable | not evaluable |
| Selected V20 equal mean 42–45 | 12001682 → 2400480 → 240081 → 10001261 → 12002856 | not evaluable | not evaluable |

The ensemble list is descriptive only; absent qualified main targets prevent an accuracy comparison. It exactly matches the single seed 42 v18 list, so neither membership nor ordering changes in this example. The comparison does not establish improved relevance for this user.

## Heavy user (original History Rich)

Main targets: 240081, 12001734, 200352, 90049236, 90071741.

| Rank | Programme ID | Source title | Source category | Main-target hit |
|---:|---|---|---|---|
| 1 | 240081 | Факты. | Инфо | yes |
| 2 | 2400480 | ТСН. | Инфо | no |
| 3 | 2400508 | Сегодня. | Инфо | no |
| 4 | 20088 | 'Завтрак с 1+1'. Информационно-развлекательная программа. | Развлечения | no |
| 5 | 12001682 | М/с 'Губка Боб Квадратные Штаны'. | Детям | no |

| Method | Ranked programme IDs (1→5) | Relevant hits | AP@5 |
|---|---|---:|---:|
| Popularity | 2400480 → 240081 → 2400467 → 200344 → 2400508 | 1 | 0.1000 |
| Original personal frequency | 2400480 → 240081 → 12001682 → 20088 → 2400508 | 1 | 0.1000 |
| CBF | 90034099 → 90041065 → 90042900 → 90044252 → 90046928 | 0 | 0.0000 |
| ALS (32 factors, regularization 0.1) | 90047611 → 90081973 → 90012900 → 90063383 → 90079986 | 0 | 0.0000 |
| V18 single seed 42 | 240081 → 2400480 → 2400508 → 20088 → 12001682 | 1 | 0.2000 |
| Selected V20 equal mean 42–45 | 240081 → 2400480 → 2400508 → 20088 → 12001682 | 1 | 0.2000 |

Selected v20 AP@5 is **0.2000**, compared with **0.2000** for v18, **0.1000** for popularity, **0.1000** for original personal frequency, and **0.0000/0.0000** for CBF/ALS. The ensemble exactly matches the v18 single-model ranking; it therefore adds no example-level AP gain over v18. This fixed illustrative case cannot establish population-level superiority or explain the Kaggle score difference.

## Provenance and limits

The two users were originally selected by training-history size, not hits. No replacement user, seed selection, weighting choice, v21 features or final-window predictions enter this export. User mappings, candidate rows, feature arrays and per-seed scores remain only in ignored private storage. Existing report/model/cache/CSV hashes are preserved. Native session records are unmodified; no independent student verification is claimed. No Kaggle access occurred.

The main evaluation cohorts have been reused across experiments; these two examples illustrate actual rankings rather than independent validation. Selected submission status is supplied by the user’s screenshot-reported results.

[Anonymous export verification and score provenance](ensemble_two_user_examples_checks.json) records model hashes, feature checks, empty-target handling and unknown submission identifiers without publishing source user IDs.
