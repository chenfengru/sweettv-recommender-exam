# Versioned prediction artifacts

## Submitted baseline

`first_personal_original_20261029_v1.csv` is the exact first benchmark artifact, generated after a single combined weeks 11–30 refit. Its SHA-256 remains `53cb8ae4b59b26ab6ee00b5e99ad91044876180e662732a755d3e99a297e64bc`.

The user confirms manual submission and screenshot scores: Private **0.38937**, Public **0.39131**. These are user-confirmed values; see [score provenance and corrected CLI evidence](../results/improvement_20261029_v2/baseline_score_evidence.json). The original file must remain byte-for-byte unchanged.

## Exploratory review candidate — not submitted

`candidate_rrf_als_lb80_w0p1_20261029_v2.csv` has SHA-256 `905971a8a9c47bcf4a88e14cd10d2514feaaea43900d6f513b2eecc4986f19f5`. It fuses original personal frequency with 80%-filtered implicit ALS, using weights 1.0/0.1, k=60 and direct top-50 ranks only. Both internal and CLI validation pass for 1,260 users and 6,649 final-window candidates.

The nominal local MAP@5 gain is only 0.000197 and its conditional bootstrap interval includes zero. **Recommendation: retain the baseline rather than submit this candidate on current evidence.** Review [all results, limitations and changed-user/slot counts](../results/improvement_20261029_v2/improvement_report.md).

All files preserve the original template header/order with five distinct nonzero available IDs. Caches, raw histories, credentials and original session records remain excluded from Git. Uploads will be performed manually by the user. Approval of experimental results never authorizes an automated upload or submission.
