# Frozen fifth-position replacement experiment

Question: can one conditional unseen replacement at position five improve submitted v5 without changing its first four positions?

Exactly E1,E2,E3, fixed before evaluation. E1: original position5 programme has N50 exactly1. E2: original positions4 and5 both have N50 exactly1. E3: fewer than5 distinct available positive-N50 programmes AND original fifth position supplied by v5 global fallback. Determine fallback provenance by reconciling the exact completed v5 list with direct personal ordering and completion; a fallback fifth item has no positive available N50 history. Counts are pre-cutoff >=0.50 canonical user-airings.

Start from exact completed v5. Inspect only v7 unseen-only direct top50, before fallback. Select first available nonzero candidate with N50=0 absent from the ENTIRE original top5. If ineligible or no candidate, preserve all5. Otherwise replace position5 once; positions1–4 remain identical. No retrieval fitting or tuning on either validation split, no extra rules or thresholds, no RRF sweep extension.

Reuse checksummed v7 N50/unseen rankings and saved v5 predictions. Reconcile original >=0.80 globals, fallback, truth, slices and candidates. Main4625/6384 and auxiliary4589/5742, original half-open cutoffs and >=0.80 truth unchanged. Whole cohort and replaced-user AP outcomes, inserted/removed/both/neither relevant cases, net hits, slices, list and slot changes. Available-replacement users are reported both over whole cohort and among eligible users; eligible-with-candidate equals actual replacements.

Paired bootstrap2000 user resamples, seed42, same draws across rules per split. Conditional on reused overlapping cohorts, excludes configuration-selection uncertainty. Qualification strictly positive MAP improvement on BOTH splits. Select largest minimum absolute gain, ties fewer main replacements then E1,E2,E3. If none qualifies no finalfit/CSV. No expansion after inspection.

If selected, recompute combined [2020-03-09,2020-07-27) N50/N80 with original canonical pipeline (not adding independently qualified counts), fit unchanged v7 item-item once (binary N50; cosine*c/(c+20), mincoview3, top50), predict [2020-07-27,2020-10-19) using carryovers and >=0.80 global keys/fallback. Reproduce exact submitted v5 before applying selected rule. Generate exactly1 versioned CSV and run both validators for1260 users/order/header, five distinct available nonzero IDs; report path/hash/config/differences/accurate English description.

Preserve prior artifacts/checksums and native transcript. English evidence to draftPR1. Student verification pending. No Kaggle workflow/upload/submit command/API. Stop for manual user review.
