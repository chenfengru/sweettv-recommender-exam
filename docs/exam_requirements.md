# Exam requirements

Status: instructor-requirement summary, prepared 29 October 2026. Source: the user-provided **Final Exam Quiz (FKN): TV Program Recommendation on sweet.tv** (`exam_quiz_FKN.md`), with the existing homework guidelines. These originals remain authoritative.

## Mandatory requirements

| Requirement | Evidence to produce |
| --- | --- |
| Individual submission by 1 Nov 2026, 19:00 MSK | Final course submission |
| Five ranked programme IDs for each test user | CSV using the original template |
| At least two of CBF, association rules, implicit matrix factorization, personalized PageRank | Separate implementations and hold-out results |
| Popularity baseline | Result row under the same protocol; does not count as a required method |
| Same temporal hold-out, candidates, repeat policy, fallback, and evaluation protocol | Versioned experiment configuration |
| Explain channel/time matching and the watched threshold | Method description and checked examples |
| Explain treatment of ID 0 | Counts and policy |
| Handle users with no usable history | Explicit shared fallback |
| Document parameters, seeds, runtime, and environment | Run records |
| Same two example users for every method | Ordered ID/title/category lists compared with actual observed histories |
| Choose a platform strategy using evidence | Validation, computation, examples, and supported limitations |
| No future viewing behaviour | Documented feature cutoff and leakage checks |

A hybrid is optional. Evaluate each component separately before combining it. Hybrid scores are not automatically probabilities; document fusion, switching, or reranking.

The test-period schedule is permitted to identify which programme airs on which channel at which time. It cannot provide future viewer behaviour.

## Grading

| Cohort private-score band | Ranking points |
| --- | ---: |
| Top 20% | 50 |
| Next 20% | 40 |
| Next 20% | 30 |
| Next 20% | 20 |
| Bottom 20% | 10 |

Coursework-style evaluation contributes another 50 points. The exam does not specify a new subscore breakdown. Gate 0 causes automatic exam failure.

There is no fixed MAP@5 score that guarantees top-20% membership. Historical scores are not current-cohort percentiles.

## Submission destinations

- Course channel: exactly the report PDF and original, unmodified AI-session export.
- PDF: repository link, screenshot of the designated submission's returned **private** score, comparison, validation, and business/algorithmic analysis.
- GitHub: implementation and the exact final prediction file associated with that score. Reproduction instructions are optional in the exam and recommended for this project.
- No new report language or page limit is added by this exam. The underlying homework guidelines apply; their conflicting page-limit statements should not be silently resolved by inventing an exam rule.

## Instructor-reported data inventory, not yet locally measured

| Filename | Reported rows | Role |
| --- | ---: | --- |
| dataset11-30.csv | 5,821,987 | Viewing logs |
| export_arh_11-20-final.csv | 1,074,235 | Earlier training schedule |
| export_arh_21-30-final.csv | 1,074,394 | Later training schedule |
| export_arh_31-42-final.csv | 1,295,378 | Future schedule |
| submission.csv | 1,260 users | Submission template |

The source reports approximately 890 MB extracted. Its reading-time and peak-memory measurements are environment-specific and do not measure the cost of our matching or modeling pipeline.

Viewing-log fields: user_id, vsetv_id, start_time, stop_time, duraton. The source says duraton is viewing-interval length in seconds, not programme length.

Schedule fields include channel_id, channel_title, start_time, duration, tv_show_title, tv_show_id, tv_show_category, three genre fields, year_of_production, director, and actors.

For weeks 11-20 the source reports 115,613 nonzero-ID rows out of 1,074,235: approximately 10.8%. This is a **row fraction**, not a measured fraction of airtime, viewing time, users, or recoverable interactions. Verify the other periods separately.

## Additional user constraint

The user reports five Kaggle submissions per day. This limit is not stated in the uploaded exam file. Preserve a record of attempts and follow the account's quota/reset display without assuming local midnight.
