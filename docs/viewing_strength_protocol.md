# Frozen viewing-strength experiment

Question: do bonuses for >=0.80 airings improve T50 ranking, and are remaining errors due to personal-history coverage or ranking?

Exactly two new scores: L05 = 2*N50 + N80 and L10 = N50 + N80 (scaled integers). Reference v5 is N50. Canonical counts use longest contiguous unioned block / full original airing duration. Counts, cleaning, clipping, intervals, deduplication, repeats and candidates use the established pipeline. Global tie keys and fallback always use original >=0.80 qualifications. Truth and original history slices remain >=0.80 and unchanged.

Reuse main [2020-03-09,2020-05-18) fit / [2020-05-18,2020-07-27) validation, 4625 users and 6384 candidates; auxiliary [2020-03-09,2020-06-01) fit / [2020-06-01,2020-07-27) validation, 4589 users and 5742 candidates. Reconcile v5 to saved predictions. Use 2000 paired-user bootstrap draws, seed 42, common indices per split; uncertainty is conditional on reused overlapping cohorts and not selection-adjusted.

Diagnostics use each user's available >=0.50 personal history before fallback and full v5 ranking. Deduplicate relevant validation items. Macro recall is mean h/|relevant|; micro coverage is sum(h)/sum(|relevant|). Bucket relevant items by ranks 1–5,6–20,21–50,>50,absent. Oracle AP@5=min(5,h)/min(5,|relevant|); mean is a diagnostic upper bound for personal-history-only retrieval, not an attainable model score or a bound for the full fallback system. Absent items are partitioned by whether any other user has >=0.50 pre-cutoff airings. Do not implement collaborative filtering.

Select only if strictly positive MAP delta against v5 on both splits. If both qualify choose higher main MAP; exact main selection tie retains v5. Otherwise no new CSV. A selected candidate uses a single combined weeks11–30 fit, recomputing per-airing counts, predicting weeks31–42 with carryovers, >=0.80 globals/fallback. Reproduce exact submitted v5 before comparison. At most one new versioned CSV; never overwrite old files.

Record English evidence and tests. No Kaggle workflow, upload, API or browser action. Push to existing draft PR for manual review. Native transcript stays unmodified. Student verification remains pending.
