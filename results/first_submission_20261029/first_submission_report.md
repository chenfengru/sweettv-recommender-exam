# First benchmark artifact and manual submission handoff

Status: **final prediction artifact generated and validated; the user requested manual upload**. No automated Kaggle submission was sent. This is a first benchmark, not completion of the coursework.

## Bounded local comparison

The established audit and model comparison were reused. No new audit, ALS/CBF fit, hybrid or larger search was run. The three personal-frequency configurations used exactly the frozen 4,625 users, 6,384 candidates, 80% longest-block truth, causal cleaning, repeat eligibility and shared unweighted popularity fallback.

| Configuration | Local MAP@5 |
| --- | ---: |
| personal_original | 0.317490 |
| personal_half_life_28d | 0.311193 |
| personal_half_life_56d | 0.316090 |

Selected **personal_original**. Neither requested recency variant improved the baseline. The experiment took 3.87 seconds, below the 20-minute limit. Exact values and source provenance are in `recency_experiment.json`.

For each qualified canonical airing, the added weights are `2 ** (-max(0, (cutoff - airing_end)/86400) / half_life_days)`, with half-life 28 or 56 days. Age uses the complete airing end, not the viewing segment end; airings ending after cutoff have age zero. Qualification uses the observed pre-cutoff segment and original full airing duration. Weighted counts are aggregated by user/programme; string-ID ties and the original shared popularity fallback are unchanged. Two focused checks cover the half-life endpoints, crossing-cutoff clamp, duplicate-segment union and original duration denominator. All **30 tests pass**.

## Combined-window refit and exact CSV

The final selected original-frequency model was rebuilt over **[2020-03-09 00:00:00, 2020-07-27 00:00:00)** in source wall time, for **[2020-07-27 00:00:00, 2020-10-19 00:00:00)** predictions. A single extraction unions viewing intervals and deduplicates canonical broadcasts before qualification. It does not add separately qualified comparison-window counts. The combined fit contains **573,003 qualified user-airings**; the sum of the earlier separately clipped counts would be 572,712 and was not used.

The prediction-window schedule includes known preceding-file carryovers, yielding **6,649** valid nonzero candidate IDs. All **1,260** original template users are retained in the exact header and row order, with five distinct single-space-separated IDs each. There are 277 distinct recommended IDs, six users requiring full shared fallback and 19 requiring partial completion.

Final file: [`first_personal_original_20261029_v1.csv`](../../submissions/first_personal_original_20261029_v1.csv)

Absolute path: `/Users/chenfengru/sweettv-recommender-exam/submissions/first_personal_original_20261029_v1.csv`

SHA-256: `53cb8ae4b59b26ab6ee00b5e99ad91044876180e662732a755d3e99a297e64bc`

The original template and exact final-window candidate export both pass the existing validator; see `validator_cli.json`. `final_window_candidate_ids.csv` is a derived availability export from the timestamp-filtered schedules, not a replacement raw input. Complete input hashes, source hashes, configuration, combined-fit cache provenance, fit/prediction windows and creation timestamp are in `first_artifact.json`. All original inputs remain unchanged. The complete experiment/refit/artifact generation took 57.19 seconds.

## Kaggle handoff

The authenticated account’s late-submission form displayed **100 submissions remaining today**, resetting “in 4 hours,” before the upload-helper attempt. This display differs from the earlier user-reported five-per-day constraint; the agent was authorized to send only one submission and sent **zero**. No current remaining quota is inferred after any manual user activity.

The browser file chooser helper failed because the Chrome extension did not permit local-file URL access. The user then explicitly requested the file and chose to upload it personally. Automatic upload/submission work stopped immediately. **No submission reference, success status, public score or private score has been verified.** No score screenshot is available yet. Local MAP@5 is not a Kaggle score.

Manual step: open the competition’s Late Submission form, select the exact CSV linked above, optionally enter the description `First benchmark: original personal qualified-airing frequency; combined weeks 11–30 fit; local MAP@5 0.317490`, and submit it once. Preserve the returned submission reference, status and actual scores; retain a screenshot showing the private score when returned. Do not describe an unsubmitted or pending file as scored. `submission_record.json` records the current handoff state.

Raw inputs, credentials, intermediate histories, caches, fitted weights and native AI-session records remain outside Git. The exact final prediction CSV is included as explicitly requested. The native session transcript remains unmodified. Student verification is pending.
