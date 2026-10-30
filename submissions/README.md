# Preserved prediction artifacts

| File | User-confirmed Private / Public Score | SHA-256 |
| --- | --- | --- |
| `first_personal_original_20261029_v1.csv` | 0.38937 / 0.39131 | `53cb8ae4b59b26ab6ee00b5e99ad91044876180e662732a755d3e99a297e64bc` |
| `candidate_rrf_als_lb80_w0p1_20261029_v2.csv` | 0.38663 / 0.38852 | `905971a8a9c47bcf4a88e14cd10d2514feaaea43900d6f513b2eecc4986f19f5` |
| `candidate_personal_tie_popularity_20261030_v3.csv` | **0.39697 / 0.40288** | `39aac2794395209b2299ccee2e2bb1b4b9afde22f3e06ccb5b04f3d706c9522f` |

The user confirms these scores from Kaggle screenshots. They are not independently fetched in this experiment, and no unknown submission identifiers/timestamps are invented. The filenames retain their original candidate names after the user’s manual submissions. Every file remains byte-for-byte unchanged; v3 is the best submitted baseline.

## Latest C/D round: no new candidate

[The frozen scheduled-opportunity / qualified-week experiment](../results/opportunity_week_20261030_v4/comparison_report.md) tested exactly C and D against v3 on the main and one overlapping auxiliary split. C has mixed signs; D is negative on both. Neither improves both windows, so v3 is retained and **no additional prediction CSV or final refit was generated**. The main split uses 4,625 users/6,384 candidates; the auxiliary has 4,589 users/5,742 candidates. Their raw MAP values describe different tasks and must not be treated as interchangeable.

V3 already preserves the original template header/order, five distinct nonzero available IDs for all 1,260 users, and the exact 6,649-ID final-window pool. Its recorded validation remains associated with the unchanged checksum. Caches, credentials, raw histories and original native session exports remain outside Git. Uploads are manual-only by the user; approval of results never authorizes an automated upload or submission workflow.

## Personal-threshold round: manual-review candidate

Selected T50 improves both frozen splits. `candidate_personal_threshold_050_20261030_v5.csv` has SHA-256 `593b1134b6625771abfe107e17d074499cedf6efb4ef9306e06289e9566876e5`; both validators pass for all 1,260 template users. It has **not been submitted** and has no Kaggle score. [Results, limitations and exact path](../results/personal_threshold_20261030_v5/comparison_report.md). The earlier C/D result above remains historical evidence and was not rerun.
