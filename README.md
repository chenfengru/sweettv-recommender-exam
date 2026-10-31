# LLM4Rec Midterm Exam

SWEET.TV programme recommendation: five ranked programmes per user, evaluated with MAP@5. The selected **four-seed ensemble (v20)** averages historical LightGBM reranking scores with personal-frequency and item-item retrieval features, schedule exposure, support-aware LightFM features, and user-channel affinity (52 features). Four classifiers (seeds 42–45) use the same two earlier historical origins, 52 features and fixed settings; their prediction scores are averaged equally. No best-seed or weight selection is used.

| Evidence | Result | Provenance |
| --- | ---: | --- |
| Main validation MAP@5 | **0.369630450** | Measured locally; 4,625 users |
| Auxiliary validation MAP@5 | **0.359208736** | Measured locally; 4,589 users |
| Kaggle Private | **0.44124** | User-screenshot-reported |
| Kaggle Public | **0.44911** | User-screenshot-reported |

Kaggle scores were supplied by the user; submission ID/time are unknown. No Kaggle access or upload is performed by repository tools.

The later item-affinity extension returned user-screenshot-reported Private 0.43970 / Public 0.44687 and is not selected. Main ensemble improvement is small and its conditional bootstrap interval includes zero; no generalization guarantee is claimed.

## Review the evidence

- [Selected four-seed ensemble experiment](results/seed_ensemble_20261031_v20/comparison_report.md): fixed equal mean, diversity checks, both-split comparisons and limitations.

- [Required individual-method comparison](results/model_comparison_20261029/comparison_report.md): popularity, personal frequency, CBF and implicit ALS, under the shared temporal protocol.
- [Single-model channel-affinity experiment](results/channel_affinity_20261030_v18/comparison_report.md): configuration, paired comparisons, channel coverage, slices and limitations. This historical report predates the user's submission; [later score provenance](results/time_affinity_20261030_v19/submitted_score_evidence.json) records the confirmed scores above.
- [Completed examples for the same light and heavy users](results/final_report_examples/ensemble_two_user_examples.md): main-window recommendations, original titles/categories and hits. The light user has no qualified targets, so AP@5 is **not evaluable**; the missing cached list was recovered with saved-model inference. User identities remain private.
- [Reproduction order and limitations](docs/reproducing_selected_model.md): original five inputs, environment, cache producers, historical command order and fresh-clone restrictions.
- [Exact final CSV](submissions/candidate_channel_affinity_seed_mean_20261031_v20.csv) ; its two-validator results and exact checksum are recorded in the [ensemble report](results/seed_ensemble_20261031_v20/comparison_report.md).

Final CSV SHA-256:

```text
5c052205c156f48a7f72b38efc680323a34152496bc2e2df7a1964f93961a861
```

Automated checks validate all 1,260 template users, original header/order, and five distinct nonzero available IDs per row. The regression suite has 108 passing tests; [example-recovery checks](results/final_report_examples/v18_light_user_recovery_checks.json) verify all 52 reconstructed features against a saved heavy-user control. These are automated checks, **not independent student verification**. The student personally identified the example's matching programme and rank change, and reviewed AP@5 in an AI-guided walkthrough. This is guided case review, not independent verification of the full pipeline. Original native session records remain private and are not uploaded to GitHub.

The evaluation cohorts overlap, repeated model selection introduces uncertainty, and historical training horizons differ from evaluation/final horizons. Channel mapping coverage and cross-origin LightFM score shifts are additional limitations. Raw data, user mappings, caches, weights and native session exports are excluded from Git. Historical experiment reports remain execution records rather than current status announcements.
