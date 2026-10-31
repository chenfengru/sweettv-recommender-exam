# V17 frozen LambdaRank experiment

Question: does one fixed within-user ranking formulation improve MAP@5 versus submitted v14 binary classification? No v15 expanded candidates or v16 longer horizons.

Restore exact original v14 40-feature historical arrays, original v12 row indexes and labels: Apr6 cutoff with [Apr6,Apr20) labels; Apr20 cutoff with [Apr20,May4) labels; histories from Mar9. Each (origin,user) is a separate query. Preserve existing contiguous per-user rows and deterministic raw-ID within-query order. Concatenate origins without merging users; group sizes from offsets must sum to rows. Identity permutation is valid and reversed feature/label equality must be exact. Keep all queries/negatives, including uniform-label groups; no weights, IDs as features or positive injection.

Exactly one LGBMRanker fit with objective=lambdarank, metric=ndcg, label_gain=[0,1], lambdarank_truncation_level=8, lambdarank_norm=True, learning_rate=.05, num_leaves=15,max_depth=-1,min_child_samples=100,reg_lambda=1,n_estimators=300,random_state=42,n_jobs=4,deterministic=True,force_col_wise=True. Pass exact group sizes. No early stopping, eval_set, tuning, class weights, seeds or other variants. Record installed API and effective booster parameters. LambdaRank optimizes an NDCG-oriented surrogate, not MAP@5; query normalization differs from binary row-wise training, so this changes the training formulation.

Read main/auxiliary/final candidate rows and all40 feature values directly from immutable v14 caches with hashes. Predict raw ranking scores (not probabilities), exact v14 score/count/global/raw-ID ties and fallback. No blend/E2/protected positions/cold override/expansion. Main/auxiliary labels never enter fitting. Frozen same ranker for both evaluations and optional final.

MAP@5 is sole selection metric; add binary-gain NDCG@5 against full unchanged truth as secondary diagnostic. Compare saved v14 predictions, paired user-bootstrap2000 seed42 percentile95% intervals, outcomes/slices/cold/seen-unseen AP and hits/membership/positions/unchanged coverage. Intervals conditional on reused overlapping cohorts, exclude accumulated selection uncertainty. Preserve unequal historical forecast/history horizons and independent LightFM origin-scale limitations.

Qualify only strict MAP gain versus v14 on BOTHsplits. Otherwise retain v14/noCSV/noadditionalconfigs. If qualified generate exactly one versioned CSV using same frozen ranker and unchanged final inputs; run existing validators, report path/SHA/v14diff/Englishdescription.

V14 user-screenshot-reported Private.43416/Public.44157, no submissionID/time invented. Preserve all artifacts/models/checksums/native records; studentverification pending. Englishreport/code/results to existingdraftPR1. Never open Kaggle or submit/upload; manual userreview.
