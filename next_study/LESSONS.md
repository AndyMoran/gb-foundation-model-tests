# Lessons from designing the benchmark

Andy Moran (Heaviside Analytics) · 15 November 2026, updated 16 November 2026

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

**22. A model's forecast depended on what else was in the call.**
TimesFM 2.5 with covariates fits one regression across every series in a call. The weather study batched 64 consecutive days for speed, so each day's forecast drew on later days' demand. That was look-ahead, and it reversed a published confirmatory result (weather study correction 1). It was caught only because checkpoint 0's cost check required every timed forecaster to reproduce its scored forecasts.
*Fix:* forecast one issue day per call. Before a model enters, run it on at least 20 days both one day per call and batched; if the two differ, batching is barred (draft rule 4.8). Any reproduction check is worth running even when it seems redundant.

**23. Reviewers supplied sources that did not hold up.**
In two days of review, outside feedback supplied five citations or quotations that failed on checking:
- a paper whose DOI could not be found;
- a configuration attributed to the wrong journal;
- a quotation that appears nowhere;
- a system operator's "own methodology" that was a consultant's report, and was misdescribed even there;
- a study that "beat the system operator" only because it forecast an hour ahead.

Two more were real but said less than claimed. The pattern matches lesson 15: confident, specific and plausible.
*Fix:* open every source before citing it, whoever supplies it. Check that it says what the citation claims, at the stated scale and horizon. If only the abstract is accessible, say so in the citation. Cite a relayed claim as relayed ("März and Rasul, citing Godahewa et al.").

**24. Pressure to reframe a fixed headline after the result.**
Once checkpoint 0's result was known, three separate suggestions would have led with something other than the plan's fixed headline: the regression comparison, LightGBM's credentials, a "confirmation, not discovery" framing. Each was reasonable as context, and each would have made the opening a choice made after seeing the result.
*Fix:* the fixed headline leads, quoted if need be, and context follows straight after. Quoting it with a link to the tagged plan turned the constraint into a credibility point.

**25. A prediction rested on a measure nobody had worked through.**
The arbitrage plan predicted that where a forecaster disagreed with NESO, outturn would side with NESO, because NESO is more accurate. Every forecaster gained instead, even TimesFM 2.5. The direction of a disagreement depends on both forecasters' errors, so any forecast whose errors differ from NESO's tends to be right when NESO is wrong. The synthetic check tested a forecaster equal to NESO plus noise, which scores zero, but not one equal to outturn plus independent noise, which scores well.
*Fix:* before predicting from a new measure, work out what it gives for an uninformative forecaster and for an independent one, and put both in the synthetic check. A measure that almost anything passes is a precondition, not a result.

**26. A sign slipped in a frozen plan.**
The arbitrage plan said to correct each forecast by "subtracting its own recent bias: its mean error, *y* minus forecast", which would double the bias. Review did not catch it; writing the code did, and the synthetic check would have failed with the wrong sign.
*Fix:* write every correction as a formula with its sign, as well as in words, before tagging. Record a slip found after tagging in `REVISIONS.md`, and do not edit the tagged plan.

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

**R12. The block bootstrap may undercover.** The credit project found that block-bootstrap intervals undercover. If they do here, the confirmatory false-positive rate exceeds 0.025.
*Now:* simulate at a true edge of zero before freezing checkpoint 1's plan (`PROJECT.md`, gate G3).
*Note, 17 November:* the rate here is per test, one-sided, at alpha 0.025 (rule 7.2); a reviewer read it as family-wise.

## Part 3: what worked, and stays

- Committing each analysis script before running it, and its outputs after. Three power scripts this way gave four hashes of evidence in one morning.
- Recording errors in `CORRECTIONS.md` rather than editing committed files.
- Putting alternatives into a specification before running it. The summer window was in the power check's specification, so choosing it later was not a rescue.
- Measuring an assumption rather than arguing about it: the summer edge took one short script.
- Fixing the outcome headlines before any result.
- Checking each review's claims against the files before adopting them.
- Filing upstream issues with a minimal reproduction (`mistralai/timestral#9`, `google-research/timesfm#577`).
- Requiring every timed forecaster to reproduce its scored forecasts: the check that caught lesson 22.
- Correcting a published result openly: a notice in the note, a new version DOI, the original left available, and the public post edited with a comment.
