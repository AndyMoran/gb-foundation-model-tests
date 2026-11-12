# Lessons from the weather study

Andy Moran (Heaviside Analytics) · 12 November 2026

What the weather study taught, written down before the next study is designed. Each lesson says what happened and
what the next study does about it. The last section lists the practices that worked and stay.

## Lessons

**1. Check that every forecaster gets the same inputs, before the freeze.**
The regression had a calendar (day of week, bank holidays, Christmas); the models had none. Nobody noticed until the
day after the results were published, when exploratory check E4 showed the asymmetry explained part of Q3.
*Next study:* the plan holds an input table, one row per forecaster and one column per input, and a gate check
confirms that the code feeds each forecaster exactly what the table says.

**2. Leakage decides which data can be confirmatory.**
Timestral was released on 15 October 2026, so no backtest exists that it cannot have seen.
*Next study:* the live window is the confirmatory test, sized by power at realistic effects. Any backtest serves
development and description only.

**3. Compare like with like across seasons.**
The power addendum found that a winter-only live window, read against an all-year backtest interval, often reads as
a "larger gain" when nothing has changed.
*Next study:* every comparison between periods is matched by season, by rule.

**4. Fix the analysis budget and the stopping rule in advance.**
E4 followed one look at the results, and E5 followed E4. Each step was reasonable; a chain of them invites the
garden of forking paths.
*Next study:* the plan names its exploratory checks and states that nothing beyond them is done without a new study.

**5. Name the measure for every hypothesis.**
Q4 was set in percentage cuts of error; in megawatts it reads differently, and a reviewer had to ask what "points"
meant.
*Next study:* each hypothesis names its measure, and results are given in both MW and percentage.

**6. Measure cost, because cost is part of the answer.**
Compute time was estimated afterwards from log timestamps.
*Next study:* the scoring run records wall time and peak memory for each forecaster.

**7. Check facts against data before writing them down.**
The design brief gave ECMWF's release-time change as November 2025; the records showed 2 October 2025.
*Next study:* every date or figure in a frozen document is computed by the code or cited to its source file.

**8. Pin the environments early.**
A missing package (cfgrib) surfaced in a late dry run, and library warnings buried the logs.
*Next study:* the environments are built and locked on the first day, and known warnings are silenced from the start.

**9. Test on full-size data.**
The bugs that mattered appeared only at full size: a partial build that sorted ahead of the full one, one lock key
with two meanings, an index error on a subset of days.
*Next study:* the dry gates run on the full period early, and files are chosen by exact name, never by sort order.

**10. Keep one canonical copy of the results note.**
The working draft and the repository copy drifted apart, and a reviewer read a stale version.
*Next study:* once the note is exported, only the repository copy is edited.

**11. Check public posts against the note, line by line.**
Small slips reached LinkedIn: "the models train on ERA5", "last week" for the day before.
*Next study:* every number and claim in a post is checked against the published note before posting.

**12. Tune trained models only on the past.**
A new risk for the next study: tuning a gradient-boosted model on the test period would leak.
*Next study:* each model is tuned only on data before each forecast day, within a search budget fixed and frozen
before scoring, and the budget is the same for every trained model.

## What worked, and stays

- Every gate check shown to fail on deliberately corrupted input before real data are scored.
- A second, independent implementation of each trained model, required to agree with the first.
- Result sentences written into the plan before the results exist.
- A freeze script that tests, hashes and tags, and a lock that scoring checks before it runs.
- Honest timing of every input: data count only if they were public by the issue time.
- A written rule for each foreseeable change (late runs, model-cycle changes) rather than a decision made later.
- Independent review rounds on the plan and on the draft results.
- Code published with the results.
