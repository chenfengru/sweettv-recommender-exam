# V18 final-model examples: the original two users

The light (History Poor) and heavy (History Rich) users are exactly those in [the original comparison](../model_comparison_20261029/two_user_examples.md). Their identities were recovered from the existing private setup mapping and cross-checked against the private example-history mapping; no users were reselected. Source user IDs are deliberately omitted. The original selection used training history only.

All recommendations and hits below refer to the **main validation window [2020-05-18, 2020-07-27)**, with training history [2020-03-09, 2020-05-18), in the established source-naive clock. No final Kaggle submission predictions are compared with main targets. No model was retrained, tuned or refitted. The light user’s missing main-window predictions were recovered by applying the saved v18 classifier to reconstructed main-window features; the original heavy user was reconstructed only as a control.

**Why the previous output was missing:** the v18 main prediction/feature tables inherit the fixed 4,625-user evaluation cohort, which contains only users with nonempty qualified held-out targets. The original light user has no such targets, so the user had no saved main prediction or feature rows. The previous export reported that cache gap rather than generating new inference. This recovery preserves the original user and reconstructs the unchanged main-window pipeline, then applies the saved v18 classifier without training. The final-window list is never substituted.

Original baseline and heavy-user titles/categories remain copied verbatim from the published examples. Recovered light-user v18 titles/categories come from the original schedule files using the same display-only canonical metadata convention (modal canonical-airing attributes, deterministic ties, observed schedule starts before the main-window end); original-language strings are retained. They do not enter this export as new model features. AP@5 is reported only for users with qualified held-out targets: sum of precision at relevant ranks divided by min(5, number of targets). An empty target set is **not evaluable**, not AP@5 = 0.

## Light user (original History Poor)

One programme with >=80%-qualified training airings (four programmes with soft overlap). No qualified main-window held-out targets; outside the fixed evaluation cohort. **Not evaluable for every method.**

| Method | Rank | Programme ID | Title | Category | Main held-out hit |
| --- | ---: | --- | --- | --- | --- |
| Popularity | 1 | 2400480 | ТСН. | Инфо | not evaluable |
| Popularity | 2 | 240081 | Факты. | Инфо | not evaluable |
| Popularity | 3 | 2400467 | 'Викна-Новости'. | Инфо | not evaluable |
| Popularity | 4 | 200344 | 'Чистоnews'. | Развлечения | not evaluable |
| Popularity | 5 | 2400508 | Сегодня. | Инфо | not evaluable |
| Original personal frequency | 1 | 90066849 | Х/ф 'Гангстер'. | Фильмы | not evaluable |
| Original personal frequency | 2 | 2400480 | ТСН. | Инфо | not evaluable |
| Original personal frequency | 3 | 240081 | Факты. | Инфо | not evaluable |
| Original personal frequency | 4 | 2400467 | 'Викна-Новости'. | Инфо | not evaluable |
| Original personal frequency | 5 | 200344 | 'Чистоnews'. | Развлечения | not evaluable |
| CBF | 1 | 10002484 | Т/с 'Демоны', 1-4 с. | Сериалы | not evaluable |
| CBF | 2 | 10002525 | Т/с 'Расплата', 1 и 2 с. | Сериалы | not evaluable |
| CBF | 3 | 10002578 | Т/с 'Особо опасен', 3 сезон, 11 и 12 с. | Сериалы | not evaluable |
| CBF | 4 | 10002674 | Т/с 'Станица', 1 с. | Сериалы | not evaluable |
| CBF | 5 | 10003051 | Т/с 'Шулер', 6 с. | Сериалы | not evaluable |
| ALS (32 factors, regularization 0.1) | 1 | 90070560 | Х/ф '2012'. | Фильмы | not evaluable |
| ALS (32 factors, regularization 0.1) | 2 | 10001072 | Т/с 'Побег', 3 сезон, 5 с. 'Помехи'. | Сериалы | not evaluable |
| ALS (32 factors, regularization 0.1) | 3 | 10001085 | Т/с 'Как я встретил вашу маму', 5 сезон, 18 с. 'Улыбочку'. | Сериалы | not evaluable |
| ALS (32 factors, regularization 0.1) | 4 | 90066849 | Х/ф 'Гангстер'. | Фильмы | not evaluable |
| ALS (32 factors, regularization 0.1) | 5 | 10001711 | Т/с 'Город хищниц', 6 сезон, 6 с. 'Не то, что стоит делать'. | Сериалы | not evaluable |
| V18 final model | 1 | 12001682 | М/с 'Губка Боб Квадратные Штаны'. | Детям | not evaluable |
| V18 final model | 2 | 2400480 | ТСН. | Инфо | not evaluable |
| V18 final model | 3 | 240081 | Факты. | Инфо | not evaluable |
| V18 final model | 4 | 10001261 | Т/с 'Мыслить как преступник'. | Сериалы | not evaluable |
| V18 final model | 5 | 12002856 | М/с 'Элвиннн!!! и бурундуки'. | Детям | not evaluable |

| Method | Relevant hits in top five | AP@5 |
| --- | ---: | ---: |
| Popularity | not evaluable | not evaluable |
| Original personal frequency | not evaluable | not evaluable |
| CBF | not evaluable | not evaluable |
| ALS (32 factors, regularization 0.1) | not evaluable | not evaluable |
| V18 final model (recovered main inference) | not evaluable | not evaluable |

The original personal model retains the sole qualified training programme at rank one, while popularity offers mainly news, CBF offers series, and ALS mixes films and series. Without held-out targets, none of these lists supports a measured accuracy claim for this user. The recovered v18 list mixes two children’s programmes, two news programmes and one crime series, and omits the sole >=80%-qualified training film. This describes the actual outputs, without identifying which features caused the ranking. It is reported above for descriptive comparison only; its hit indicators and AP@5 remain not evaluable because the main target set is empty. It must not be scored as zero or used to claim an accuracy gain.

## Heavy user (original History Rich)

183 programmes with >=80%-qualified training airings (837 with soft overlap). Main-window top-five target IDs: 240081, 12001734, 200352, 90049236, 90071741.

| Method | Rank | Programme ID | Title | Category | Main held-out hit |
| --- | ---: | --- | --- | --- | --- |
| Popularity | 1 | 2400480 | ТСН. | Инфо | no |
| Popularity | 2 | 240081 | Факты. | Инфо | yes |
| Popularity | 3 | 2400467 | 'Викна-Новости'. | Инфо | no |
| Popularity | 4 | 200344 | 'Чистоnews'. | Развлечения | no |
| Popularity | 5 | 2400508 | Сегодня. | Инфо | no |
| Original personal frequency | 1 | 2400480 | ТСН. | Инфо | no |
| Original personal frequency | 2 | 240081 | Факты. | Инфо | yes |
| Original personal frequency | 3 | 12001682 | М/с 'Губка Боб Квадратные Штаны'. | Детям | no |
| Original personal frequency | 4 | 20088 | 'Завтрак с 1+1'. Информационно-развлекательная программа. | Развлечения | no |
| Original personal frequency | 5 | 2400508 | Сегодня. | Инфо | no |
| CBF | 1 | 90034099 | Х/ф 'Шанхайский полдень'. | Фильмы | no |
| CBF | 2 | 90041065 | Х/ф 'Доспехи Бога 2'. | Фильмы | no |
| CBF | 3 | 90042900 | Х/ф 'Гудзонский ястреб'. | Фильмы | no |
| CBF | 4 | 90044252 | Х/ф 'Ангелы Чарли'. | Фильмы | no |
| CBF | 5 | 90046928 | Х/ф 'Доспехи Бога'. | Фильмы | no |
| ALS (32 factors, regularization 0.1) | 1 | 90047611 | Х/ф 'Лучше не бывает'. | Фильмы | no |
| ALS (32 factors, regularization 0.1) | 2 | 90081973 | Х/ф 'Эволюция'. | Фильмы | no |
| ALS (32 factors, regularization 0.1) | 3 | 90012900 | Х/ф 'Шоссе в никуда'. | Фильмы | no |
| ALS (32 factors, regularization 0.1) | 4 | 90063383 | Х/ф 'Ночной рейс'. | Фильмы | no |
| ALS (32 factors, regularization 0.1) | 5 | 90079986 | Х/ф 'Лев'. | Фильмы | no |
| V18 final model | 1 | 240081 | Факты. | Инфо | yes |
| V18 final model | 2 | 2400480 | ТСН. | Инфо | no |
| V18 final model | 3 | 2400508 | Сегодня. | Инфо | no |
| V18 final model | 4 | 20088 | 'Завтрак с 1+1'. Информационно-развлекательная программа. | Развлечения | no |
| V18 final model | 5 | 12001682 | М/с 'Губка Боб Квадратные Штаны'. | Детям | no |

| Method | Relevant hits in top five | AP@5 |
| --- | ---: | ---: |
| Popularity | 1 | 0.1000 |
| Original personal frequency | 1 | 0.1000 |
| CBF | 0 | 0.0000 |
| ALS (32 factors, regularization 0.1) | 0 | 0.0000 |
| V18 final model | 1 | 0.2000 |

V18 places **Факты. (240081)** first, improving AP@5 from **0.1000** for popularity and original personal frequency to **0.2000**. All three have exactly one relevant hit: the gain comes from moving that hit from rank two to rank one, not from retrieving additional relevant programmes. V18’s top-five membership is identical to the original personal list; only ordering changes. CBF and ALS recommend films here and hit none of the five targets (AP@5 = 0.0000). This is evidence about this selected user, not a population-level comparison or proof that any individual v18 feature caused the improvement.

## Provenance and limits

- Existing anonymized examples: `results/model_comparison_20261029/two_user_examples.md`; same private identity mapping, retained privately.
- V18 predictions: `artifacts/channel_affinity_20261030_v18/main/predictions.json`.
- Main targets: `artifacts/model_comparison_20261029/truth.json`; original top-five >=80%-qualified targets, unchanged.
- Main candidate/feature-row index: `artifacts/lightgbm_reranker_20261030_v12/main/row_index.json`; v18 preserves these rows.
- Original baseline predictions: the saved popularity, personal, CBF and selected ALS main-window prediction files under `artifacts/model_comparison_20261029/`; IDs and hit indicators were checked against the published original examples.
- The light user’s originally missing main list was caused by evaluation-cohort filtering. It has now been recovered by inference only; the evaluation cohort and metrics remain unchanged. No replacement user or final-window list was used.
- Native session records were not modified. Student verification remains pending. No Kaggle access occurred.

Checksums of the read-only export sources (for reproducibility; no source user identities are published):

| Source | SHA-256 |
| --- | --- |
| `results/model_comparison_20261029/two_user_examples.md` | `7f680fac36f55056ac845c01945d57edcf3ca72577381961e3c272770cb12ac8` |
| `artifacts/channel_affinity_20261030_v18/main/predictions.json` | `42aa502209880f545b2d0f989df13676bf939471ac6559024b7b63400dc9c72b` |
| `artifacts/model_comparison_20261029/truth.json` | `831ad286f8e910342549453567cd240bc2375f3bac49c39d31487d5b77a3d2a6` |
| `artifacts/lightgbm_reranker_20261030_v12/main/row_index.json` | `3970749dd964154ec269fb8cb6c6bdf202eb87fea42a4a892a55da7e0abb00a8` |
| `artifacts/model_comparison_20261029/popularity_predictions.json` | `35616f464c34d50d4d4cad971727d7d2591e210cd404958c0d5fc965ec53166d` |
| `artifacts/model_comparison_20261029/personal_predictions.json` | `20f4b9f6f696a4f8300d2299771725eea5abd69a576dae9adbba6888e7a9947e` |
| `artifacts/model_comparison_20261029/cbf_predictions.json` | `f042231034935d340b0d37ff71bfec5e608c19ceb8e36d13b1a16c9a5d8a78ab` |
| `artifacts/model_comparison_20261029/als_f32_r0.1_predictions.json` | `670489acf7846d57706b4071db769cbf824abac7dba00e1dcd54daa2540fb663` |

## Recovery checks

Reconstructed the original light user and the same original heavy control from the main pre-cutoff interaction cache. The heavy control’s complete candidate rows and all 52 feature values match saved v18 main arrays **bit-for-bit**, and its prediction reproduces the saved list exactly. The original light-user identity mapping is unchanged and remains private.

The recovered light user has 52 original-rule candidate rows from the unchanged 6,384-programme main pool. Feature order exactly matches the saved 52-column classifier schema; all values and predictions are finite. Cleaned viewing and matched segments were checked to stay within [Mar9,May18), and the forecast schedule is clipped to [May18,Jul27), including carryovers. The saved classifier hash and 300-tree count were verified; zero fits occurred. Ranking uses descending score, N50 count, global80 distinct viewers, global80 user-airing count, then ascending raw string programme ID. An independent direct sort reproduces all five predictions; all are distinct, nonzero and available. No held-out viewing enters any feature.

[Anonymous recovery verification](v18_light_user_recovery_checks.json) records schema, checks and classifier hash. Candidate rows, features, scores and the private mapping are kept only in a new ignored recovery folder; original model, caches, predictions and CSVs remain unchanged. AP@5 remains **not evaluable**. Student verification remains pending.
