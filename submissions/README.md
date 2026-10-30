# Preserved prediction artifacts

| File | User-confirmed Private / Public Score | SHA-256 |
| --- | --- | --- |
| `first_personal_original_20261029_v1.csv` | 0.38937 / 0.39131 | `53cb8ae4b59b26ab6ee00b5e99ad91044876180e662732a755d3e99a297e64bc` |
| `candidate_rrf_als_lb80_w0p1_20261029_v2.csv` | 0.38663 / 0.38852 | `905971a8a9c47bcf4a88e14cd10d2514feaaea43900d6f513b2eecc4986f19f5` |
| `candidate_personal_tie_popularity_20261030_v3.csv` | **0.39697 / 0.40288** | `39aac2794395209b2299ccee2e2bb1b4b9afde22f3e06ccb5b04f3d706c9522f` |
| `candidate_personal_threshold_050_20261030_v5.csv` | **0.40210 / 0.41789** | `593b1134b6625771abfe107e17d074499cedf6efb4ef9306e06289e9566876e5` |
| `candidate_personal_fifth_e2_20261030_v9.csv` | **0.40261 / 0.41871** | `f1378b0d6fed62793e14ebb4c1b64cf8b2163485485c15c861aae7e67e556375` |

The user confirms these scores from Kaggle screenshots. They are not independently fetched in this experiment, and no unknown submission identifiers/timestamps are invented. The filenames retain their original candidate names after the user’s manual submissions. Every file remains byte-for-byte unchanged; v9 E2 is now the best confirmed submitted model; older scores remain historical evidence.

## Latest C/D round: no new candidate

[The frozen scheduled-opportunity / qualified-week experiment](../results/opportunity_week_20261030_v4/comparison_report.md) tested exactly C and D against v3 on the main and one overlapping auxiliary split. C has mixed signs; D is negative on both. Neither improves both windows, so v3 is retained and **no additional prediction CSV or final refit was generated**. The main split uses 4,625 users/6,384 candidates; the auxiliary has 4,589 users/5,742 candidates. Their raw MAP values describe different tasks and must not be treated as interchangeable.

V3 already preserves the original template header/order, five distinct nonzero available IDs for all 1,260 users, and the exact 6,649-ID final-window pool. Its recorded validation remains associated with the unchanged checksum. Caches, credentials, raw histories and original native session exports remain outside Git. Uploads are manual-only by the user; approval of results never authorizes an automated upload or submission workflow.

## Personal-threshold round: manual-review candidate

Selected T50 improves both frozen splits. `candidate_personal_threshold_050_20261030_v5.csv` has SHA-256 `593b1134b6625771abfe107e17d074499cedf6efb4ef9306e06289e9566876e5`; both validators pass for all 1,260 template users. It was initially prepared for manual review; the user now confirms manual-submission screenshot scores Private **0.40210**, Public **0.41789**. Submission ID and timestamp remain unknown. [Results, limitations and exact path](../results/personal_threshold_20261030_v5/comparison_report.md). The earlier C/D result above remains historical evidence and was not rerun.

## Viewing-strength round: retain v5

Exactly lambda 0.5 and 1.0 bonuses were tested against v5, with >=0.80 global anchors and validation truth unchanged. Both reduce MAP on both reused splits. No new CSV or combined-window refit was generated. [English diagnostics and experiment report](../results/viewing_strength_20261030_v6/comparison_report.md). Other-user retrieval is supported as a later investigation by the coverage diagnostics; no collaborative retrieval was implemented. Uploads remain manual-only.

## Fixed item-item retrieval round: no submission artifact

One fixed model per existing temporal split recovers useful unseen targets, but standalone MAP@5 is worse than submitted v5 on both splits. Retain v5; no fusion, combined refit or prediction CSV was generated. [English retrieval and standalone comparison](../results/item_item_20261030_v7/comparison_report.md). All previous CSVs/checksums remain unchanged.

## Controlled v5/v7 RRF round: retain submitted v5

All three predeclared weights (0.05, 0.10, 0.20) reduce MAP@5 on both frozen splits. No configuration satisfies the two-split eligibility rule; no final refit or prediction CSV was generated. [Full English report and paired uncertainty](../results/item_fusion_20261030_v8/comparison_report.md). Every previous artifact remains byte-identical; no Kaggle action was taken.

## Fifth-position round: E2 manual-review candidate

`candidate_personal_fifth_e2_20261030_v9.csv` has SHA-256 `f1378b0d6fed62793e14ebb4c1b64cf8b2163485485c15c861aae7e67e556375`. E2 improves both reused splits and wins the predeclared max-min rule. Both validators pass for all1,260 template users. Exactly58 fifth-position replacements; all first four positions remain identical to submitted v5. Initially prepared for manual review; the user now reports screenshot scores **Private 0.40261 / Public 0.41871**. Submission ID/time remain unknown. [English evidence and exact path](../results/fifth_replacement_20261030_v9/comparison_report.md); [manual submission description](../results/fifth_replacement_20261030_v9/submission_description.txt). V9 is now the best confirmed submitted artifact, and all prior CSVs/checksums are preserved.

## Lower-threshold round: no new artifact

Exactly 0.30 and 0.40 were evaluated against 0.50 with E2 disabled throughout. Neither improves both splits. Retain submitted v9 and preserve its exact checksum; no combined final fit or prediction CSV was generated. [English report, paired intervals and newly included viewing-duration summaries](../results/lower_threshold_20261030_v10/comparison_report.md). No E2 combination or Kaggle action was performed.

## Exploratory adaptive round: S40+E2 candidate

`candidate_adaptive_s40_e2_20261030_v11.csv` has SHA-256 `ccac509f8efeeddb9187f1ff2e5300db08f82ae0f9acd1f4ba7d8220f9dd26fb`. It qualifies under the frozen two-stage point-estimate rules, but gains against v9 are small and both conditional intervals include zero. The grouping was derived from v10 validation slices, so evidence is exploratory. Both validators pass for all 1,260 users; 27 users adapt, and 17 lists / 44 rank slots change versus submitted v9. **Not uploaded; no Kaggle result.** [English report and path](../results/adaptive_threshold_20261030_v11/comparison_report.md); [English submission description](../results/adaptive_threshold_20261030_v11/submission_description.txt). V9 remains the best confirmed submitted model.
