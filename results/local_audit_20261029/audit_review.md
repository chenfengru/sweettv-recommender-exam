# Real-data audit review — 29 October 2026

Status: **audit and modelling specification completed by Codex on the supplied local files; student verification pending**. No models trained, validation model scores measured, or Kaggle submissions made. This review resolves the generic warnings in the profiler; a warning exit code is not an execution failure. Raw inputs are unchanged.

## Evidence and provenance

The existing ChatGPT-generated implementation at base commit `e0c6bf1cdab49f06c7d6defdace29d3a4ede2f86` was reused. The original 24-test suite passed locally before edits (0.131 s), and again after parser support (0.120 s). A source-format regression was added; final results are in `tests_final.txt`. Synthetic checks are regression evidence, not a real-data audit or student-performed verification. Original `results/data_audit.*` and `results/phase1_checks.json` remain historical records.

Current evidence: `data_audit.json` (exact per-file profiles and SHA-256), `anomaly_audit.json` (full-data anomaly follow-up), and **`cleaned/matching_audit.json` (authoritative final matching results)**. The root `matching_audit.json` is the initial unfiltered/file-isolated run; `cleaned_before_carryover/` records the first filtering experiment. Those intermediate matching results are superseded by the cleaned run with channel-specific schedule carryovers. Do not mix their denominators. Commands are recorded in `commands.txt`.

The native current Codex JSONL session was located and retained in place without modification. Its actual private path is in ignored `artifacts/session_provenance.txt`; the native export must be retained after the session ends, outside public Git. Nothing here reconstructs a transcript.

## Files, schema, and exact counts

All five files parsed fully as strict UTF-8, comma-delimited CSVs. All records have their expected field counts. Viewing fields are `user_id,vsetv_id,start_time,stop_time,duraton`; submission fields are `user_id,tv_show_id`. Schedule fields are:

`channel_id,channel_title,start_time,duration,tv_show_title,tv_show_id,tv_show_category,tv_show_genre_1,tv_show_genre_2,tv_show_genre_3,year_of_production,director,actors`

Identifiers are integer-looking **strings**, preserved without float conversion; duration fields are numeric seconds; time fields are naive civil strings; programme metadata are text. The template contains 1,260 unique users in its original order and five-zero placeholder lists, not targets.

| File | Data rows | Exact duplicate rows beyond first | Channels | Users / distinct nonzero programmes | Zero-ID rows | Nonzero-ID rows (% of all rows) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| dataset11-30.csv | 5,821,987 | 17 | 202 | 4,914 | — | — |
| export_arh_11-20-final.csv | 1,074,235 | 0 | 400 | 5,847 | 958,622 | 115,613 (10.7624%) |
| export_arh_21-30-final.csv | 1,074,394 | 0 | 403 | 6,363 | 952,889 | 121,505 (11.3092%) |
| export_arh_31-42-final.csv | 1,295,378 | 0 | 404 | 6,636 | 1,150,604 | 144,774 (11.1762%) |
| submission.csv | 1,260 | 0 | — | 1,260 | — | — |

These are measured counts, independently reproducing the supplied inventory. Zero-ID fractions use the same per-file row denominator: 11-20: 89.2376%, 21-30: 88.6908%, 31-42: 88.8238%. They are neither watch-time nor user fractions. Cardinalities and exact parsed-row duplicates use disk-backed SQLite keys. No within-file canonical schedule duplicates were found either. No exact parsed-row or canonical-airing duplicates were found across the adjacent file boundaries; the cross-file check restricts to date ranges that could overlap.

### Missingness

Blank/whitespace missingness uses every schema-valid row in that file as its denominator. All viewing/template cells and the schedule fields `channel_id,channel_title,start_time,duration,tv_show_title,tv_show_id,tv_show_category` have **zero missing cells**. Empty metadata counts follow; JSON retains every field, identifier representation and whitespace count. No unsupported timestamps, invalid numeric durations, or malformed rows occurred.

| Field | Weeks 11–20 / 1,074,235 | Weeks 21–30 / 1,074,394 | Weeks 31–42 / 1,295,378 |
| --- | ---: | ---: | ---: |
| tv_show_genre_1 | 620,089 | 616,370 | 737,871 |
| tv_show_genre_2 | 928,009 | 924,020 | 1,113,598 |
| tv_show_genre_3 | 1,054,059 | 1,050,668 | 1,266,621 |
| year_of_production | 959,500 | 954,382 | 1,151,706 |
| director | 974,050 | 969,487 | 1,170,189 |
| actors | 973,861 | 968,834 | 1,169,519 |

Missing metadata do not indicate dislike. Category is complete, while deeper genres and production/person fields are sparse. IDs with multiple distinct `(title, category, genre1, genre2, genre3)` tuples in the in-window schedule are 1,698 for 11-20, 2,526 for 21-30, 1,715 for 31-42. This counts any tuple difference, not necessarily a semantic contradiction. Use deterministic pre-cutoff metadata selection; do not collapse IDs because titles resemble each other.

## Timestamp and duration evidence

Views use `YYYY-MM-DD HH:MM:SS`; schedules use `DD.MM.YYYY HH:MM:SS`. Neither has an offset or zone. View starts range from 2020-03-09 00:00:02 to 2020-07-26 23:58:42; final stop is 2020-07-26 23:59:58. Schedule extents including ends are 2020-03-08 23:00 through 2020-05-18 12:00, 2020-05-18 00:00 through 2020-07-27 12:00, and 2020-07-27 00:00 through 2020-10-19 12:00.

The source `duraton` equals the wall-clock endpoint difference for **5,821,870 / 5,821,987 rows**. The remaining 117 are exactly 3,600 seconds smaller, all spanning the 29 March interval (115 start and stop on that date, two span adjacent dates). This is consistent with a clock transition but does not establish a named timezone. Do not assign UTC, Moscow, or Kyiv as a measured fact. The local matching convention assumes a shared source wall clock and no offset between sources; excluding the discrepant rows avoids treating their ambiguous elapsed time as label evidence.

Schedule durations are supported as seconds by 1,074,234 valid intervals in 11-20, 1,074,394 valid intervals in 21-30, 1,295,378 valid intervals in 31-42. More directly, **1,073,436 / 1,073,834**, **1,073,986 / 1,073,991**, and **1,294,962 / 1,294,974** adjacent same-channel pairs touch exactly when `end = start + duration seconds`. The independent real example has duration 8,100 seconds = 135 minutes. Multiplying these values by 60 would introduce major overlaps; interpreting them as milliseconds would introduce gaps. This is empirical consistency evidence, not external source-zone confirmation.

Full-column viewing duration min/max are 61 / 342,145 seconds; sampled p50/p90/p99 are 397 / 3,921 / 13,171.66 seconds. Labelled-airing sampled medians are 2,700 seconds in all periods, p90 7,200 seconds; their full maxima are 32,700 / 30,900 / 31,200 seconds. All quantiles use uniform reservoirs of 10,000 valid numeric values, seed 42 (duration residuals seed 43), with linear interpolation; counts, means, minima and maxima use full columns.

## Data-quality policy and boundary handling

There are no nonpositive viewing intervals. The first schedule has one zero-duration row; later schedules have none, and no negative schedule duration occurs. There are 52 viewing intervals longer than 24 hours. Filtering duration discrepancies and >24-hour intervals excludes **168 distinct rows** (the classes overlap); retained source rows are 5,821,819. The 24-hour limit is a conservative modelling assumption; these observations are not proven invalid. Raw and cleaned runs are both retained. Exact duplicate viewing rows are removed implicitly by interval union, not counted as repeated interest.

The all-ID schedules have 2 / 2 / 8 overlap pairs. The behavioural periods have no overlapping different nonzero programmes; the future period has four such pairs involving eight broadcasts. Exclude those broadcasts from label/interaction attribution, retain their availability, and union coverage intervals. Full overlap locations are in `anomaly_audit.json`. No arbitrary winner is selected.

File boundaries are channel-specific: channel 3 ends/begins at 2020-05-18 06:30, channel 6 at 02:00, and channel 1521 at 07:00. Therefore midnight windows need preceding-file carryovers. The corrected run includes 2,679 prior-file airings for validation and 2,689 for final availability. There are 2,431, 2,429, 2,399 schedule rows starting at/after the respective window end; exclude them from that window. File-level catalogue sizes are not the window candidate sizes.

Use half-open source wall-time windows **[9 March, 18 May)** for fitting, **[18 May, 27 July)** for validation, and **[27 July, 19 October)** for final prediction, all in 2020 at 00:00:00. Midnight is the fixed local protocol choice supported by calendar ranges, rather than a universal source-file boundary. Clip views at cutoffs and retain full airing duration as the fraction denominator.

## Channel alignment and matching coverage

197 / 202 viewing channel IDs occur in the union of the two behavioural schedules. The five absent throughout are `1174,149,1508,1509,1510`. Per-period missing-channel sets and exact channel row counts are in JSON; other channels also lack period-specific coverage. Use exact `vsetv_id == channel_id`, with no invented remapping. Strong temporal coverage and real source examples support this local alignment, but cannot prove semantic identity for every row.

The following exact full-data measures use cleaned **user-channel union seconds**: overlap and duplicate sessions on the same channel are merged first; simultaneous different-channel exposures remain separate. Broadcast overlaps are unioned again per query, preventing double-counted coverage. They are not unique user-attention seconds.

| Period | Retained clipped source rows | User-channel union seconds | Any-schedule matched seconds (%) | Nonzero-programme matched seconds (%) |
| --- | ---: | ---: | ---: | ---: |
| 11-20 | 3,945,050 | 4,846,464,205 | 4,401,022,804 (90.8089%) | 2,399,690,897 (49.5143%) |
| 21-30 | 1,877,776 | 3,649,665,920 | 3,589,022,466 (98.3384%) | 2,094,338,214 (57.3844%) |

Cross-cutoff rows contribute a clipped part to each window, so period row counts may sum above the retained file count. Logged endpoints, not declared duration, supply these second denominators. Unlabelled schedule coverage is not a positive recommendation signal.

Raw-row matching was separately **sampled**, using one Algorithm R reservoir of 10,000 positive-length original view rows, seed 42; period subsets contain 6,701 and 3,301 clipped rows (two cross both windows). These are sampled diagnostics, not full-data matched-row counts. With corrected schedule carryovers:

| Period | Sampled rows | Any schedule | Nonzero programme |
| --- | ---: | ---: | ---: |
| 11-20 | 6701 | 6074 (90.6432%) | 3177 (47.4108%) |
| 21-30 | 3301 | 3226 (97.7280%) | 1890 (57.2554%) |

The indexed matcher agreed with the independent brute-force reference on 30 actual reservoir views (18 training, 12 validation), using bounded channel-specific source airings. This tests real conversion/alignment/intersections, while the regression suite covers synthetic edge cases. For unfiltered logs, the across-all-channel user-time union is 7,872,586,950 seconds; 694,730 source rows overlap an earlier same-user interval on any channel. See `user_time_union.json` for its exact SQL ordering and merge method. This denominator is deliberately separate from channel exposure time.

## Label sensitivity and modelling decision

| Period | Longest-block threshold | Qualified user-airings | Distinct user-item pairs | Users | Template users |
| --- | ---: | ---: | ---: | ---: | ---: |
| 11-20 | 50% | 475,291 | 179,742 | 4,784 | 1,245 |
| 11-20 | 80% | 289,762 | 102,689 | 4,726 | 1,241 |
| 11-20 | 90% | 244,204 | 84,640 | 4,693 | 1,237 |
| 21-30 | 50% | 403,195 | 199,056 | 4,721 | 1,244 |
| 21-30 | 80% | 282,950 | 134,151 | 4,625 | 1,236 |
| 21-30 | 90% | 251,268 | 116,796 | 4,561 | 1,226 |

At 80%, using disconnected-segment union instead would yield 316,270 and 294,465 qualified user-airings. The stricter longest-block rule avoids upgrading disconnected visits solely by adding their time. Choose **80% longest merged same-channel block**, then at most five most-frequently qualified programmes, tied by ascending string ID. This retains a substantial cohort and follows the historical target hypothesis without claiming the hidden evaluator uses it. No model score was used to select the target definition.

Final local cohort: 4,625 evaluable users out of 4,914 observed; 289 have no qualified validation target. 108 evaluable users lack a qualified training positive. 1,236 evaluable users are in the template. Of all 1,260 template users, 1,241 have qualified initial training history and 1,255 have qualified weeks 11–30 history. Users with any usable overlap (a softer history definition) are separately recorded in JSON.

Window candidates including carryovers: 11-20: 5,842, 21-30: 6,384, 31-42: 6,649. Future candidates without any cleaned pre-cutoff overlap: 3,527; this is absence of observed interactions, not absence of scheduled metadata. Every candidate has at least a category in the supplied schedule; metadata access for CBF remains restricted as specified in the protocol.

For training confidence, use all positive cleaned overlaps: `q_ua = min(1, union_seconds / full_airing_seconds)`, `s_ui = sum(q_ua)`, and `w_ui = log1p(s_ui)`. CBF profiles use `w_ui`; initial implicit MF confidence is `1 + 40*w_ui` for observed pairs. The multiplier 40, the 24-hour exclusion, and exact fallback/tie rules are fixed initial assumptions, not empirically optimal settings. Qualified counts define popularity/personal frequency separately from soft weights. See the [complete modelling specification](../../docs/experiment_protocol.md).

## Execution cost, checksums, and next stage

Host: macOS 26.6.2 arm64, Python 3.10.11, 24 GiB measured physical RAM. The foundation documentation recommended 3.11+, but this actual environment is 3.10.11; its full suite and audit ran successfully. No third-party dependency was installed. `host_measurements.json` contains raw memory and OS measurements: free pages 4,465 × 16,384 bytes = 73,154,560 bytes at that snapshot; free + inactive + speculative pages are a reclaimable-memory proxy, not a guaranteed available-memory value. System applications and memory compression affect these snapshots.

Per-file profiling including hashing: 170.33 s; peak process RSS 71.39 MiB. Initial matching: 103.67 s; final cleaned/carryover matching: 102.64 s, peak RSS 928.62 MiB. Anomaly follow-up: 26.02 s. Runs partially overlapped in wall time; do not sum them as elapsed session duration. RSS is each process’s lifetime high-water mark, not the whole Mac’s consumption. SQLite scratch data remain ignored/private and may be regenerated.

| Input | Bytes | SHA-256 |
| --- | ---: | --- |
| dataset11-30.csv | 396,216,555 | `8c9e5f058157041e5c33f13e64dc1625a5177cc6d5e434ba18cd8a69afafb53b` |
| export_arh_11-20-final.csv | 153,322,643 | `7888aa00c20db3db23f95000c721eccf2878e5f58bf5383bb25b99f078b1033c` |
| export_arh_21-30-final.csv | 154,366,907 | `bdc9fa9850239aaed608bece9cdb200011e690300470fe85b980457d8c0cb2d4` |
| export_arh_31-42-final.csv | 185,952,991 | `5cc01f4619bd94886d83744f00bbc15cc5fa23384d297244a7dc2207450c4088` |
| submission.csv | 38,348 | `d8c209dce3c7c9d815d8e2a6226e1be63052ee7afa7e8ba8b75dc2f703967a02` |

Necessary implementation changes: explicit source wall-clock parsers and real-source conversion regression; reuse of the existing interval matcher in disk-backed full-data diagnostics; union-based coverage and per-airing label sensitivity; anomaly and cross-file boundary checks; carryover-aware candidates and matching. Original inputs and historical execution records are preserved.

Next task: implement reusable cleaned interaction extraction, then compare global popularity, personal repeat-frequency, CBF and implicit MF under the frozen cohort/candidates/repeat/fallback policy. Record actual MAP@5 and costs before selection. Add the end-to-end cutoff-invariance check with those fitted components. No training or Kaggle submission has been performed in this audit round. Student verification remains pending; the private, source-record-indexed example is in `artifacts/local_audit_20261029/checkable_example.json`.
