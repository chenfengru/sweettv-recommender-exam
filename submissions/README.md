# Versioned prediction artifacts

## Submitted files — preserved unchanged

| File | User-confirmed Private / Public Score | SHA-256 |
| --- | --- | --- |
| `first_personal_original_20261029_v1.csv` | **0.38937 / 0.39131** | `53cb8ae4b59b26ab6ee00b5e99ad91044876180e662732a755d3e99a297e64bc` |
| `candidate_rrf_als_lb80_w0p1_20261029_v2.csv` | 0.38663 / 0.38852 | `905971a8a9c47bcf4a88e14cd10d2514feaaea43900d6f513b2eecc4986f19f5` |

The original personal-frequency model remains the best submitted baseline. The user supplied these results from Kaggle screenshots; no submission IDs or timestamps are invented. [Score provenance](../results/personal_ties_20261030_v3/submitted_score_evidence.json) distinguishes these user reports from local validation and direct tool measurements. The v2 filename retains its original candidate name even though the user now confirms it was submitted.

## New review candidate — not submitted

`candidate_personal_tie_popularity_20261030_v3.csv` keeps personal qualified-airing counts primary, then uses global qualified viewers, total qualified user-airings, and raw programme ID. SHA-256: `39aac2794395209b2299ccee2e2bb1b4b9afde22f3e06ccb5b04f3d706c9522f`.

Local MAP@5 is **0.326854**, +0.009364 over the original 0.317490. The conditional paired-user bootstrap interval is positive; selection on the reused hold-out and the earlier fusion’s lower returned scores remain limitations. See the [English review report](../results/personal_ties_20261030_v3/tie_break_report.md). Both validators pass for all 1,260 users, K=5 and 6,649 final-window candidates, preserving exact header/order. The file changes 739 users’ ordered lists and 1,620/6,300 rank-position slots versus the exact submitted personal baseline.

Recommendation: worth one manual benchmark after user review; no Kaggle score is assigned to this new file. All uploads are performed manually by the user. Approval of experiment results never authorizes automated upload or submission. Existing files are never overwritten; caches, credentials, raw histories and native session records remain outside Git.
