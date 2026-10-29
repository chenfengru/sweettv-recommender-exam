# Personal-frequency tie-breaking review

**Recommendation: Variant B is worth one manual benchmark submission after user review.** Its local gain is substantially larger than the earlier fusion gain and its conditional interval is positive. This is not a guarantee of improving the best submitted private score. Exactly the two requested tie-break variants were evaluated; no decay, combination, extra parameter or previous model experiment was rerun.

## Submitted-score provenance

The user confirms these values from Kaggle screenshots:

| Exact submitted file | Private Score | Public Score | SHA-256 |
| --- | ---: | ---: | --- |
| `first_personal_original_20261029_v1.csv` | **0.38937** | **0.39131** | `53cb8ae4b59b26ab6ee00b5e99ad91044876180e662732a755d3e99a297e64bc` |
| `candidate_rrf_als_lb80_w0p1_20261029_v2.csv` | 0.38663 | 0.38852 | `905971a8a9c47bcf4a88e14cd10d2514feaaea43900d6f513b2eecc4986f19f5` |

Both submitted files remain byte-for-byte unchanged. The original personal-frequency model remains the best submitted baseline. These scores were supplied by the user, not fetched from Kaggle; original screenshot binaries are not present in this tool run. Submission IDs and submission timestamps remain null rather than being invented. See `submitted_score_evidence.json`. The prior fusion’s small positive local result and lower returned scores demonstrate why local selection is not a promise of Kaggle improvement.

## Fixed protocol and observed-time feature

The original temporal windows, causal cleaning, 80% longest-block qualification, interval unions, canonical broadcasts, candidate carryovers, repeats, cohort and shared popularity fallback are unchanged. Training is [2020-03-09 00:00:00, 2020-05-18 00:00:00); validation is [2020-05-18 00:00:00, 2020-07-27 00:00:00), on the established source wall clock. Every result uses **4,625 evaluation users and 6,384 candidates**. Rankings were additionally generated for the full template/evaluation union of 4,649 users.

Original ranking is descending personal qualified-airing count, then ascending raw string programme ID. Variant A keeps that count primary and then sorts by descending **maximum observed viewing-segment end across that user/programme’s qualified airings**, followed by ID. Qualified segment groups are recomputed from the existing read-only pre-cutoff cache with the full original airing duration denominator; their counts exactly match the existing interaction records. Segments are clipped again at the information cutoff and all extracted latest timestamps are asserted <= cutoff. The extractor never parses an airing end from the canonical airing ID. It does not infer recency from a future broadcast end and does not decay counts.

Variant B also keeps personal counts primary, then uses descending distinct qualified training viewers, descending total qualified training user-airing count, then ID. These two global statistics reproduce the existing shared popularity ordering exactly. Only equal-personal-count ordering can change. In both variants, primary count sequences in the top five are asserted identical to baseline; a membership change is permitted only if the original ranks five and six have equal personal counts. Fallback ordering and the numbers of completed slots are identical across all three methods.

## Importance of existing ties

All counts below use the fixed **4,625-user cohort**, and only directly ranked available programmes with positive personal qualified counts. Popularity-fallback items are excluded from tie diagnosis. These are potential tie ambiguities, not counts of actual changes under a particular variant.

| Diagnostic | Users | Denominator |
| --- | ---: | ---: |
| At least two equal-count items already inside original direct top five | 3,299 | 4,625 |
| Equal counts at direct ranks five and six: boundary membership ambiguous | 2,483 | 4,625 |
| Both internal-order and boundary tie | 1,986 | 4,625 |
| Either type | 3,796 | 4,625 |
| At least six available qualified programmes, so a crossing tie is possible | 4,001 | 4,625 |

Boundary groups contain **2–46 programmes**, median **5**, exact full-cohort mean **6.5695**. These summaries use all 2,483 affected users, not a sample. A full group includes its selected and unselected members; one or more are outside rank five. The exact joint selected/unselected group-size histogram and tied count values are retained in `tie_diagnostics.json`.

| Full boundary tie-group size | Users |
| ---: | ---: |
| 2 | 391 |
| 3 | 411 |
| 4 | 344 |
| 5 | 259 |
| 6 | 198 |
| 7 | 153 |
| 8 | 119 |
| 9 | 113 |
| 10 | 92 |
| 11 | 73 |
| 12 | 68 |
| 13 | 45 |
| 14 | 38 |
| 15 | 27 |
| 16 | 25 |
| 17 | 16 |
| 18 | 14 |
| 19 | 16 |
| 20 | 10 |
| 21 | 12 |
| 22 | 9 |
| 23 | 7 |
| 24 | 5 |
| 25 | 6 |
| 26 | 4 |
| 27 | 4 |
| 28 | 2 |
| 29 | 4 |
| 30 | 1 |
| 31 | 2 |
| 32 | 4 |
| 33 | 1 |
| 36 | 1 |
| 37 | 1 |
| 38 | 5 |
| 40 | 1 |
| 42 | 1 |
| 46 | 1 |

## Three-method local results

| Method | MAP@5 | Absolute difference | AP improved / worsened / unchanged users | Conditional paired-bootstrap 95% interval for difference |
| --- | ---: | ---: | --- | --- |
| Original: raw string ID | 0.317489729730 | 0 | reference | reference |
| Variant A: latest observed qualified viewing | 0.316052492492 | -0.001437237237 | 561 / 592 / 3472 | [-0.003009710, +0.000065417] |
| Variant B: global qualified popularity | 0.326853993994 | +0.009364264264 | 904 / 465 / 3256 | [+0.007631601, +0.011085536] |

Intervals use 2,000 paired-user bootstrap resamples with replacement, seed 42; the same draw indices are used for both variants. They are **conditional on this reused validation cohort**. Selecting the stronger of these two variants on the same hold-out introduces selection uncertainty, and the intervals do not cover repeated historical experimentation or future Kaggle data. The positive interval supports a local difference for Variant B, not a claimed future private score. Exact ties in model selection retain the original baseline.

Variant A is below baseline, so it was not refitted or combined with Variant B. Variant B improves all nonempty-history slices in this validation run. The zero-history fallback is unchanged.

## History-size slices

History size is the existing number of distinct programmes with qualified pre-cutoff airings, before candidate filtering.

| Qualified training items | Users | Original MAP@5 | Variant A MAP@5 | Variant B MAP@5 |
| --- | ---: | ---: | ---: | ---: |
| 0 | 108 | 0.163050412 | 0.163050412 | 0.163050412 |
| 1–5 | 462 | 0.171129149 | 0.168579245 | 0.176880712 |
| 6–20 | 2087 | 0.285913592 | 0.282614865 | 0.299143374 |
| 21+ | 1968 | 0.393809564 | 0.394528709 | 0.400436568 |

## Ordered-list changes versus membership changes

The following compare each variant with the exact original local predictions, using the 4,625 evaluation users. A rank-position slot can change because of reordering or a different programme. Membership change means the top-five set itself differs; order-only means the set stays identical.

| Variant | Changed ordered lists | Order-only users | Membership-change users | Changed rank slots / 23,125 | Top-five set overlap |
| --- | ---: | ---: | ---: | ---: | ---: |
| Variant A: latest observed qualified viewing | 3062 | 1039 | 2023 | 7455 | 87.4249% |
| Variant B: global qualified popularity | 3185 | 1237 | 1948 | 7632 | 89.3535% |

All methods have exactly 112 complete-fallback users, 376 partial-completion users and 1446 fallback slots. These unchanged counts confirm that the experiment changes tie ordering, not the common fallback policy. A user’s AP can stay unchanged despite their ordered list changing.

## Candidate for manual review

Selected configuration: **Variant B — personal qualified count ↓, qualified global viewers ↓, qualified global user-airings ↓, raw string programme ID ↑**. No additional fitted parameter, decay or hybrid component was introduced.

The combined [2020-03-09, 2020-07-27) interaction cache is generated by the established full-window pipeline, not by summing split-window qualification. This stage recomputes qualification from those full-window canonical segment groups and reconciles all **573,003** qualified user-airings with that combined cache. Prediction remains [2020-07-27, 2020-10-19); known schedule carryovers yield 6,649 candidates.

Filename: `candidate_personal_tie_popularity_20261030_v3.csv`

Absolute path: `/Users/chenfengru/sweettv-recommender-exam/submissions/candidate_personal_tie_popularity_20261030_v3.csv`

[Open the exact candidate CSV](../../submissions/candidate_personal_tie_popularity_20261030_v3.csv)

SHA-256: `39aac2794395209b2299ccee2e2bb1b4b9afde22f3e06ccb5b04f3d706c9522f`

Internal validation and the separate explicit-comma CLI both report **valid**: 1260 users in original order, exact original header, five distinct nonzero available IDs per user, 6649 candidates and 248 distinct recommended IDs. The submitted baseline and fusion files are preserved. See `candidate_validator_cli.json` and `candidate_artifact.json`.

Against the **exact submitted personal-frequency baseline**, 739 / 1,260 ordered lists change: 294 users have order-only changes and 445 have membership changes. 1620 / 6,300 rank-position slots change; 539 programme slots introduce IDs absent from the old user list. Final top-five set overlap is 91.4444%. These final-window counts are separate from the validation overlap table above.

## Runtime, regression and provenance

Local feature extraction/ranking/assessment took 4.496 seconds, including 3.283 seconds for latest-observed-end extraction. Ranking and completion for the 4,649-user union took original 0.0349 s, latest 0.0394 s, popularity 0.0424 s. The selected combined-window candidate took 10.807 seconds to refit/validate from existing caches. Code/source hashes, input identities, cache provenance, exact windows and dependency versions are in the JSON records. No raw dataset audit, prior model grid or recency experiment was repeated.

All **37 tests pass**: the existing 33 plus four focused checks for primary-count precedence, both global popularity tie keys and final raw-ID ties, observed-time cutoff invariance, and internal-versus-boundary tie-group semantics. The cutoff check extends a segment beyond cutoff and adds future-only segments/users, leaving qualified counts and latest features unchanged; opaque airing IDs prevent reliance on a future broadcast end. Existing interval, metric, carryover and leakage checks remain in the suite.

Private per-user ranks, latest features and AP values are ignored under `artifacts/personal_ties_20261030_v3/`. Raw inputs and credentials remain outside Git. Both submitted CSVs and failed historical validator evidence are preserved. The original native session transcript remains unmodified; student verification is pending.

**Manual submission recommendation: yes, Variant B is worth one reviewed benchmark submission.** The local gain is +0.009364 with a positive conditional interval, while retaining personal-frequency count precedence. The earlier fusion’s worse reported Kaggle result is a concrete limitation on extrapolating validation gains. The original baseline remains the best submitted model until an actual new result is supplied. No Kaggle page, upload workflow, Submit action or API was used. Stop and wait for user review.
