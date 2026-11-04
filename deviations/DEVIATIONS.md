# Deviations from the preregistered plan

The plan was frozen at tag `demand-plan` (commit 9c72ca2, pushed 3 November 2026, 18:04 UTC). Its text is never edited after the freeze. Each deviation is logged here, and its fixes are locked by `code/freeze.py --amend N`, which writes `plan/LOCK_AMENDMENT_N.json` and tags `demand-plan-devN` before the next attempt runs.

## Deviation 1: attempt 1 failed gate checks 3 and 4

*Logged 4 November 2026 by Andy Moran.*

### What happened

Attempt 1 ran on 3 November 2026, after the tag, and finished at 23:29 UTC. It failed two of the plan's validity checks (Section 9):

- **Check 3, NESO reconstruction:** 91.2% of daytime and evening half-hours matched NESO's performance file; the plan requires 95%.
- **Check 4, Timestral repeatability:** a repeated Timestral forecast was not identical to the original.

Every other check passed. As the plan requires, attempt 1's outputs are kept unchanged in `results/attempt1/`.

**What has been seen.** The author, and the AI assistant used to write the code, read attempt 1's full results, including the primary ratios, before any change below was made. The changes must therefore be judged on the evidence that they cannot move those results; the last section sets out that evidence and a prediction that attempt 2 can confirm or refute.

### Diagnosis

`deviations/diagnose_attempt1.py` (output in `diagnose_attempt1.txt`) examined both failures without changing any locked file.

**Check 3 compared two different forecasts.** The check assumed NESO's performance file always records the forecast Elexon published at 08:45 UK time on D−1. That assumption rested on 18 matching cases in the feasibility check, and it is false on 94 of the 1,035 target days:

- On 78 days the file's values appear in no Elexon publication at all. On 16 days they first appear in a publication later on D−1, after the 09:30 issue time (eight half-hours only on D itself). None appears in a publication at or before 09:30.
- On 69 of the 94 days, every half-hour from SP17 to SP48 differs: the file holds a different forecast for the whole day, not scattered errors.
- The mismatches are spread evenly across settlement periods and months, and between clock-time seasons in proportion to their length, which rules out a time-zone or clock-change error.
- The file's `Publish_Datetime` cannot separate the cases. It reads 08:45 in winter and 10:45 in summer (UK time) in 2024, and 09:33 to 11:03 in 2026; 337 days labelled 10:45 match Elexon's 08:45 publication exactly. The feasibility check (finding F) had already found this column unreliable.
- In every sampled mismatch, the value used is exactly Elexon's 08:45 publication, which is the forecast the plan defines (Section 3).

So on those 94 days the file does not record the forecast that was public at the issue time, and it cannot validate a reconstruction of that forecast. As specified, check 3 could never pass with these data, however correct the reconstruction. **The threshold is not the problem, and it is not lowered; the comparison is replaced** (below).

One finding concerns NESO's published forecast itself. On 5 March 2025, Elexon's 08:45 publication has SP15 to SP26 falling to 13,625 MW, against outturn of 25,500 to 32,300 MW; NESO's performance file holds plausible values (25,050 MW at SP25). The plan scores the forecast that was public at 09:30, so this publication is used as it stands. It counts against NESO in the secondary comparison only, and the sensitivity checks below show its effect.

**Check 4 tested batch size, not repetition.** The plan asks for model outputs "identical on repetition". The check instead re-forecast three days as a batch of three and required bit-for-bit equality with forecasts made in a batch of 64. Batch size changes floating-point rounding. Measured directly:

| Timestral forecast | Maximum difference |
| --- | --- |
| The same batch of 64, run twice | 0 MW |
| The same batch of 64 now, against attempt 1's saved forecasts | 0 MW |
| A batch of 3, run twice | 0 MW |
| A batch of 3, against the batch of 64 | 0.006 MW |

Timestral is fully repeatable; the check was at fault. The self-test passed because it repeated the same batch.

**Other gaps found in the same review.** Checking `run.py` against the plan found three further omissions and one fragility:

1. The robustness check (Section 6: primary ratios rescored against NESO's ND series) was not computed.
2. Check 3's mismatches were not listed, as Section 9 requires.
3. The exploratory tables (Section 6: between models; by season, time of day, weekday and holiday) were not computed.
4. `neso_forecast` took the last publication for each half-hour and relied on its caller to sort the publications. The real run's loader sorts them, so attempt 1's NESO values were correct (the diagnostic found every sampled value in the 08:45 or 09:16 publication). The synthetic test data were unsorted, so the self-tests had exercised a wrong selection without detecting it. The new check 3 found this on its first run.

The root cause of the check-3 failure is the same as for gaps 1 and 2: the synthetic tests had no performance file or ND file, so that code never ran before the real attempt.

### Changes

| File | Change |
| --- | --- |
| `code/run.py` | **Check 3** replaced: every NESO value used must equal an independent selection from the raw Elexon publications (the non-blank publication with the latest `publishTime` at or before 09:30 on D−1), on every day and half-hour, exactly. Agreement with NESO's performance file is reported as information, with every mismatch listed in `neso_file_mismatches.csv` and classed by where the file's value first appears. **Check 4** repeats exactly the call that made the forecasts (the first batch, same days, same order); the batch-size effect is reported as information. Descriptive numbers move to `gate_info`, so only pass/fail checks decide the gate. Added: the ND robustness rescoring; NESO sensitivity checks (excluding the 94 days, and with the file's values on those days); the exploratory tables. Lock amendments are honoured |
| `code/inputs.py` | `NesoIndependent`, the second selection for check 3; `load_nd`, which keeps actual rows only and reads both of NESO's date formats, refusing any other; `neso_forecast` sorts its own input |
| `code/synth.py` | Synthetic performance file (with whole days carrying a different forecast) and ND file (both date formats, forecast rows to be dropped), so the pipeline test runs every gate check |
| `code/selftest.py` | Check H: the two NESO selections agree, a later cut-off is told apart, and the ND loader behaves |
| `code/freeze.py` | `--amend N`, which locks these fixes |

**Not changed:** the plan text, the data, the weights, every model setting, the regression, the windows, the statistics, the threshold, the six primary tests, the leakage check, and how any forecast is computed. Where this entry and the plan's Section 9 differ on check 3 or 4, this entry applies from attempt 2.

**Considered and rejected:** restricting check 3 to rows whose `Publish_Datetime` is at or before 09:30, as a reviewer suggested. That column is mislabelled (above), so the filter would rest on a timestamp known to be wrong.

### Why these changes cannot move the results, and a prediction

- **Check 3 concerns NESO only.** The six primary tests compare each model with the regression; NESO enters only the secondary comparisons.
- **Check 4 now does what the plan says.** It changes no forecast.
- **No forecast is computed differently.** The models, contexts, batches and settings are unchanged. The `neso_forecast` change only sorts input the real loader already sorts.
- **The additions are new outputs.** They add tables; they alter no existing number.

**Prediction, recorded before attempt 2:** every value in attempt 2's `forecasts.csv` equals attempt 1's exactly, so every number in `results.json` under `primary`, `primary_tests_holm`, `secondary`, `exploratory` (the entries attempt 1 had) and `L1` is identical to attempt 1's. If any differs, that is logged as deviation 2 before the results are interpreted.

Before attempt 2, the new code runs on the real data with the stand-in forecaster (`run.py pipeline-test`), so checks 2, 3 and 6, the file comparison, the ND rescoring and the sensitivity checks run on the real files without any foundation model.

### Lesson

Every gate check must run at least once, before the freeze, on synthetic data with the real files' structure. A check that has never run is not a check. (Added to `LESSONS_LEARNED.md` when the project closes.)
