# Frozen exploratory history-adaptive thresholds

Motivation is validation-informed v10 slice behaviour. This is exploratory evidence; reused cohorts overlap and intervals exclude grouping/configuration-selection uncertainty. No audit or earlier experiment rerun.

H80(u) is number of DISTINCT programmes with positive >=0.80 qualified pre-cutoff training user-airing count, BEFORE availability filtering, exactly existing history slices. Adapt only1<=H80<=5. Stage1: S30 uses N30 for that group and N50 otherwise; S40 uses N40 for group and N50 otherwise. E2 disabled for both and v5control. Same original >=0.80 global viewer/airing tie keys, raw string IDs, availability and shared fallback. No new group/threshold or label-based per-user choice.

Main4625/6384 and auxiliary4589/5742 with established training/validation windows, >=0.80 truth and original slices fixed. Reuse v10 cached completed threshold predictions, reconcile v5/control and v9/reference and source metrics; use training H80 only to mix lists. Record source hashes before evaluation. Whole/slice fallback provenance can be composed exactly from frozen v10 per-slice fallback aggregates because adaptation group is exactly the existing1–5 slice. No split fitting required.

Stage1 qualify positive MAP difference vs v5 on BOTH splits; maximize min absolute gain, exact tie S40. If none stop/noCSV/retainv9.

Stage2 evaluate ONLY selected parent+originalE2. Build completed adaptive list first; both its original fourth/fifth programmes must have ORIGINAL N50=1. Use unchanged N50-based v7 unseen-only direct top50 in original order, exclude ENTIRE pre-replacement adaptive top5, keep first4. Unseen meansN50=0, never N30/N40. Reuse original fifth_replacement helper. E2 can only remove a direct personal fifth (positiveN50 implies positive adapted history); source global-fallback slots therefore unchanged. Compare combo vsparent, v5 ANDv9. No unselected E2 combination.

Final candidates only selected parent and singlecombo. Qualify strictly above existingv9 MAP on BOTH splits; max min absolute gain vs v9, exact tie adaptive-only. If none noCSV/retainv9. No search expansion after inspection.

Report both stages MAP, paired deltas and2000 paired-user bootstrap95% intervals seed42; shared draws across evaluated methods/reference comparisons within split. Conditional on reused cohorts, excluding selection uncertainty. Whole/slice AP outcomes, relevant membership hit gains/losses, top5 set/position changes, fallback usage, adaptation and E2 eligibility/replacement counts. Assert Stage1 outsidegroup exactlyv5; Stage2 first4 unchanged, originalN50eligibility, N50unseen/order/exclusion maintained; outsidegroup combo exactlyv9.

If finalqualifies, recompute selectedlower,N50,N80 and H80 in combined[2020-03-09,2020-07-27) canonical single-window pipeline, not split-count sums. Predict[2020-07-27,2020-10-19) inclcarryovers. Use same >=0.80 globals/fallback; fit unchanged N50 item-item model once if E2 required. Reconcile finalv5 and, when E2 fit, finalv9. Generate exactlyoneversionedCSV, validate1260originalusers/header/order and5distinctavailablenonzeroIDs. Report path/hash/v9diff/finaladaptivegroup size/Englishdescription. Preserve alloldCSVchecksums/native transcript; studentverification pending. No Kaggleworkflow/commands/upload/API. English evidence to draftPR1 and stop for manualreview.
