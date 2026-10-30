# V16 frozen longer-horizon historical training

Question: does one fixed longer-horizon historical training construction transfer better to the unchanged v14 evaluation and final tables?

Histories start 2020-03-09. Origins: feature cutoff Apr6, labels [Apr6,May18), six weeks; feature cutoff Apr20, labels [Apr20,May18), four weeks. All timestamps use the established source-naive clock. Clip observed segments to each half-open window; full airing denominators, canonical unions, >=80% qualification and original top-five targets are unchanged. No behaviour at/after May18 enters labels. Overlapping historical labels retain both origins as equally weighted rows; no deduplication across origins.

Reuse verified pre-cutoff counts and origin-specific saved LightFM predictive models. Reconstruct the unchanged v14 candidate RULE: available N50 personal top200, fixed item-item unseen top50, global80 first5. No LightFM candidate expansion. Determine users from pre-cutoff cleaned history union template only, verify against original universe. Recompute availability over each longer forecast window, full-universe ranks and seven schedule features (28-day past; future rates normalized by the entire new forecast window). No labels in construction. New labels are built afterward with the existing interaction pipeline. Retain all negatives and all-negative queries.

Exactly 40 original ordered feature definitions and fixed v14 binary LightGBM parameters, seed42, 300 trees, one classifier fit. No early stopping, tuning, weighting, sampling, additional horizons, blending, E2 or cold overrides. Main/auxiliary/final candidate rows and all feature values are read directly from immutable v14 caches with hash verification. Same classifier weights for both evaluations and optional final prediction.

Compare to saved v14 predictions using fixed cohorts/truth/H80 slices. Paired user bootstrap: 2000 resamples seed42, 95% percentile intervals, conditional on reused overlapping cohorts, excluding selection uncertainty. Report overlap of historical labels and horizon/history differences. Describe target-window, candidate/availability, and schedule changes separately without attributing gains to label duration alone.

Only strict MAP@5 gains on BOTH splits qualify. If qualified, apply frozen classifier to unchanged v14 final inputs and create exactly one versioned CSV, validate original1260users/header/order/five distinct nonzero availableIDs including carryovers; report path/SHA/v14 comparison/English description. Otherwise retain v14 and create no CSV. No further configurations after results.

V14 user-screenshot-reported Private0.43416/Public0.44157; no submission ID or timestamp invented. Preserve prior CSV/checksums/models/native records; student verification pending. English report/code/results to existing draft PR1. No Kaggle workflow/commands/APIs/uploads; manual user review.
