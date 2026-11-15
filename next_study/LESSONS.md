# Lessons from designing the benchmark

Andy Moran (Heaviside Analytics) · 15 November 2026

This file continues `weather_study/LESSONS.md` (lessons 1–12). It covers the period from the weather study's results to the draft benchmark rules: the exploratory checks, the Timestral investigation, the power checks and the benchmark design. Part 1 lists mistakes made and how each was caught. Part 2 lists where the benchmark is most likely to go wrong next, and what to do now. Part 3 lists practices that worked.

## Part 1: mistakes made

**13. A sensitivity value was labelled the wrong way round.**
The power-check specification called c = 0.7 "pessimistic". Higher correlation between two forecasters' errors raises power, so 0.7, above the measured 0.54, was the optimistic case. The decision rule's branches were therefore in the wrong order. Both branches failed, so the decision did not change. The error was caught only after the run, and is recorded in `next_study/CORRECTIONS.md`.
*Fix:* for every sensitivity value in a specification, state which direction helps the claim and why. Run one quick cell at two values to confirm that direction before committing.

**14. A decision rule's fallback rested on an unstated premise.**
"This winter if powered, otherwise next winter" assumed next winter would be powered. It would not: winter variance, not the year, is the limit.
*Fix:* for every branch of a decision rule, write down what must be true for that branch to make sense, and include a branch for "none of these work".

**15. Claims outran the evidence.**
Sentences drafted with AI help said more than the analysis showed. Each was caught on review:
- "the Timestral quirk doesn't explain the result";
- "look-ahead traps mattered far more";
- "erases the advantage";
- "five seconds per forecast";
- "85–99%" (the result was 85–100%);
- "last week" (it was the day before);
- a wrong reason for TimesFM's exclusion from E5. It does take covariates; it was excluded because its 8-week context rarely contains a bank holiday.

*Fix:* before a sentence is published, check every comparative or causal word ("explains", "far more", "erases", "because") against a number in a results file. If no number supports it, cut or soften it. Treat AI-drafted prose as a draft, never as a check.

**16. Reviewers were wrong too.**
Independent reviews caught many errors, but they also introduced some. Twice a reviewer said E5's regression lacked the calendar; it always had it. One review said Mistral accepts pull requests; it does not. One proposed "six checkpoints a year" beside "three checkpoints over eighteen months".
*Fix:* check every factual claim in a review against the files before adopting it, and record which points were adopted, which rejected and why.

**17. A bug report was drafted before its mechanism was understood.**
The first account of Timestral's covariate behaviour was imprecise. Reviews corrected it: each row is scaled on its own; 0/1 rows are treated as indicators but negated {0, −1} rows are not; so the day-of-week rows are the asymmetric ones. The check script itself had three bugs: a covariate passed as a scalar, a gradient-tracking tensor and a mislabelled horizon.
*Fix:* reproduce the behaviour in the smallest possible script, have the script assert the mechanism, and only then write the report.

**18. Analysis code was wrong on subsets.**
E1 indexed bootstrap resamples on a subset of days incorrectly. It was caught before publication. This is lesson 9 (test on full-size data) in another form.
*Fix:* every bootstrap on a subset is checked against a brute-force computation on a few days.

**19. The instrument was chosen late.**
The question "one-off study or standing benchmark?" was asked after the power check, not before. The choice changes the design: a six-monthly checkpoint cadence alternates seasons, and winter checkpoints cannot be confirmatory. Changing the frame late cost one round of rework.
*Fix:* settle the purpose and form of a project (study, benchmark or tool; who uses it; how long it runs) before any power or design work.

**20. A secret was pasted into a chat.**
The Copernicus CDS key was shared in conversation and had to be regenerated.
*Fix:* secrets go only into their config file (`~/.cdsapirc`). Scripts read them from there, and they never appear in messages, files or commits.

**21. Project state lived in the conversation.**
Decisions, numbers and open items accumulated in a long chat until the context had to be summarised.
*Fix:* keep state in the repository: a handover file updated at each milestone, the rules, the corrections and the lessons. A new session starts from the files, not from memory.

## Part 2: where it is most likely to go wrong next

Each risk lists the warning sign and what to do now.

**R1. LightGBM's errors may correlate less with Chronos-2's than the regression's do.** The power check measured c only against the regression. If LightGBM's c is lower, power for that pair falls.
*Now:* once LightGBM's backtest forecasts exist, rerun the summer power cell for the LightGBM pair before freezing checkpoint 1's plan (rule 7.4).

**R2. The live edge may be smaller than the backtest's.** The backtest covers days the models may have seen in training. At the low end of the summer interval (7.7%), power is 72%.
*Now:* the plan cites 72% as the sensitivity, and outcome (c)'s wording handles an underpowered null (rule 7.6).

**R3. Each extra confirmatory test costs power.** Adding a model or a baseline to the family splits the 0.05 further.
*Now:* checkpoint 1's family is two tests. Any addition needs its own power figure at the smaller alpha.

**R4. Outcome (b) may be read as a failure.** It is the likeliest outcome (about 88%) if the backtest edge is real.
*Now:* the headline is fixed (rule 7.6). Check every public post against it, line by line (lesson 11).

**R5. The pipeline may miss days.** More than 10% of days missed turns the checkpoint descriptive (rule 5.3). A laptop that sleeps, a full disk or an API change would do it.
*Now:* move the daily runs off the laptop, add an alert for a missed day, and run the whole pipeline unattended for at least a month before 1 April 2027.

**R6. ECMWF may change its model or release time during the window.** Cycle changes and release-time shifts have happened before: 13 November 2024, 13 May 2026, and 2 October 2025 for release time.
*Now:* checkpoint 1's plan carries forward the weather study's written rules for cycle changes and late runs (decisions 13 and 14, and the fallback rule).

**R7. A model may release a new revision mid-window.** The temptation would be to switch.
*Now:* rule 3.5 keeps the pinned revision to the end of the window, and the new one enters descriptively.

**R8. Data sources may change.** NESO may change INDO's definition, publication or API. Bank holiday files may change.
*Now:* hash every input file as in the weather study's lock, and fail loudly on a change rather than continue silently.

**R9. Timestral's calendar encoding may be fixed upstream mid-window.** A fix to `mistralai/timestral#9` would change its scores.
*Now:* pin the revision. Apply any upstream fix forward only (rule 8.3), as a new entrant revision.

**R10. The project may outgrow the maintainer.** A standing benchmark runs for at least eighteen months beside other energy work.
*Now:* keep the minimum commitment (three checkpoints) and the published review at checkpoint 3. Automate everything that can be automated before the window opens.

**R11. The chain of exploratory checks may grow again.** Lesson 4 applied to E4 and E5. Each new reviewer suggestion invites another check.
*Now:* each checkpoint plan names its exploratory checks. Anything else waits for the next checkpoint's plan.

## Part 3: what worked, and stays

- Committing each analysis script before running it, and its outputs after. Three power scripts this way gave four hashes of evidence in one morning.
- Recording errors in `CORRECTIONS.md` rather than editing committed files.
- Putting alternatives into a specification before running it. The summer window was in the power check's specification, so choosing it later was not a rescue.
- Measuring an assumption rather than arguing about it: the summer edge took one short script.
- Fixing the outcome headlines before any result.
- Checking each review's claims against the files before adopting them.
- Filing upstream issues with a minimal reproduction (`mistralai/timestral#9`).
