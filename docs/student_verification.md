# Student verification checklist

**Status: not yet performed by the student.** Automated synthetic checks were executed by Codex. They do not count as the student's independent check. Fill in a date, your own working, and what you observed only after personally doing the check. Preserve the original AI-session export separately.

## 1. Programme overlap

A viewer watches channel X from 19:50 to 20:30. Programme A runs 19:30-20:00, and B runs 20:00-21:00 on X.

- [ ] Draw the intervals or calculate their intersections yourself.
- [ ] Verify A receives 10 minutes = 600 seconds and B receives 30 minutes = 1,800 seconds.
- [ ] Verify that a view ending exactly at 20:00 contributes zero seconds to B.
- [ ] Explain why a simultaneous broadcast on another channel is not a match.

Student's date, working and conclusion: **pending**.

## 2. AP@5 calculation

Relevant programmes are `{A, B, C}`; predictions are `[A, B, D, C, E]`.

- [ ] Write out relevant hits at ranks 1, 2 and 4.
- [ ] Verify the precisions at those ranks are 1, 1 and 3/4.
- [ ] Divide their sum by `min(5, 3)`: `(1 + 1 + 3/4) / 3 = 11/12`.
- [ ] Compare `[D, A, E, B, C]`: `(1/2 + 2/4 + 3/5) / 3 = 8/15`.
- [ ] Explain why the two lists have the same number of hits but different AP.

Student's date, working and conclusion: **pending**.

## 3. Re-run and inspect

- [ ] Personally run `python -m unittest discover -s tests -v`.
- [ ] Read one test and the corresponding function; explain which error it would catch.
- [ ] After real data is available, inspect a few source intervals locally, verify their units, and reproduce at least one match by hand. Do not publish user histories in this public repository.
- [ ] Record the command, environment, actual output, and any discrepancy you investigated.

Student's observations: **pending**.
