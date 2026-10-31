# LLM4Rec Midterm Exam

SWEET.TV programme recommendation: five ranked programmes per user, evaluated with MAP@5. The selected **v18** model is historical LightGBM reranking with personal-frequency and item-item retrieval features, schedule exposure, support-aware LightFM features, and user-channel affinity (52 features). One binary classifier is trained on two earlier historical origins and applied unchanged at evaluation and final inference.

| Evidence | Result | Provenance |
| --- | ---: | --- |
| Main validation MAP@5 | **0.369249610** | Measured locally; 4,625 users |
| Auxiliary validation MAP@5 | **0.357738856** | Measured locally; 4,589 users |
| Kaggle Private | **0.43798** | User-screenshot-reported |
| Kaggle Public | **0.44758** | User-screenshot-reported |

Kaggle scores were supplied by the user; submission ID/time are unknown. No Kaggle access or upload is performed by repository tools.

## Review the evidence

- [Required individual-method comparison](results/model_comparison_20261029/comparison_report.md): popularity, personal frequency, CBF and implicit ALS, under the shared temporal protocol.
- [Selected v18 experiment](results/channel_affinity_20261030_v18/comparison_report.md): configuration, paired comparisons, channel coverage, slices and limitations. This historical report predates the user's submission; [later score provenance](results/time_affinity_20261030_v19/submitted_score_evidence.json) records the confirmed scores above.
- [Completed examples for the same light and heavy users](results/final_report_examples/v18_two_user_examples.md): main-window recommendations, original titles/categories and hits. The light user has no qualified targets, so AP@5 is **not evaluable**; the missing cached list was recovered with saved-model inference. User identities remain private.
- [Reproduction order and limitations](docs/reproducing_selected_model.md): original five inputs, environment, cache producers, historical command order and fresh-clone restrictions.
- [Exact final CSV](submissions/candidate_lightgbm_channel_affinity_20261030_v18.csv) and [validator evidence](results/channel_affinity_20261030_v18/candidate_validator_cli.json).

Final CSV SHA-256:

```text
a62d1afb1a0c015cb70fd60c1e89bb670b731f872b3433dc438526a5ae703c45
```

Automated checks validate all 1,260 template users, original header/order, and five distinct nonzero available IDs per row. The regression suite has 105 passing tests; [example-recovery checks](results/final_report_examples/v18_light_user_recovery_checks.json) verify all 52 reconstructed features against a saved heavy-user control. These are automated checks, **not independent student verification**. The student personally identified the example's matching programme and rank change, and reviewed AP@5 in an AI-guided walkthrough. This is guided case review, not independent verification of the full pipeline. Original native session records remain private and are not uploaded to GitHub.

The evaluation cohorts overlap, repeated model selection introduces uncertainty, and historical training horizons differ from evaluation/final horizons. Channel mapping coverage and cross-origin LightFM score shifts are additional limitations. Raw data, user mappings, caches, weights and native session exports are excluded from Git. Historical experiment reports remain execution records rather than current status announcements.
