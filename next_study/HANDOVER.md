# Where things stand (17 November 2026)

Read this first in a new session. Then read `PROJECT.md`, `BENCHMARK_RULES.md`, `ASSUMPTIONS.md`, `next_study/CORRECTIONS.md`, both `LESSONS.md` files, `checkpoint0/RESULTS.md` and `tails/PLAN.md`. Code and documents follow `PIPELINE_RULES.md` and `WRITING.md`.

## The project

A standing, preregistered benchmark. Zero-shot foundation models are tested against trained baselines for GB day-ahead demand (INDO), on equal weather and calendar inputs, on live days no model can have seen, with cost measured. It commits to a minimum of three checkpoints, reviewed at the third. Rules: `BENCHMARK_RULES.md` (complete; Andy to tag `benchmark-rules-v1`). Why and how: `PROJECT.md`.

## Done

**Weather study** (`weather_study/`):
- Published 12 November 2026.
- Corrected on 16 November as version 2, DOI 10.5281/zenodo.24284719. Version 1 (10.5281/zenodo.24161799) stays available.
- **Correction 1:** TimesFM 2.5 with covariates fits one regression across every series in a call. The scored backtest batched 64 days, so each forecast drew on later days. Forecast one day per call, weather did not improve TimesFM (1.034, p = 0.947, against the published 0.941). The confirmed improvements are three: the regression, Chronos-2 and Timestral. Record: `weather_study/CORRECTIONS.md`; outputs: `weather_study/correction1/`.
- Reported upstream as google-research/timesfm#577, with a minimal reproduction (`gb-weather-private/weather/timesfm_batch_repro.py`).
- Andy's LinkedIn post on the weather results was corrected in place, with comments.

**Benchmark design** (`next_study/`, `PROJECT.md`, `BENCHMARK_RULES.md`):
- **Windows.** Confirmatory claims in summer only. Checkpoint 1 runs from 1 April 2027 (first 180 days); checkpoint 2, winter 2027–28, is descriptive; checkpoint 3, summer 2028, is confirmatory, with the review.
- **Power.** Summer 180 days gives 93.7% at the backtest's summer edge over the regression (10.8%, c = 0.47), and 72.2% at the low end of its interval. No winter window, single or two pooled, reaches 80% at a 10% edge.
- **c correction.** The power-check specification called c = 0.7 pessimistic; it is optimistic (`next_study/CORRECTIONS.md`).
- **D-1.** The user is a forecasting team. There is no £ valuation; each checkpoint reports a break-even price (rule 5.6).
- **Draft rule 4.8** (from the weather correction): every model forecasts one day per call, with a call-mode check before entry.

**Checkpoint 0** (`checkpoint0/`): LightGBM added on the weather study's 960 backtest days, exploratory.
- **Process.** Plan frozen at tag `checkpoint0-plan` before any run. All checks passed first time, and scoring used the committed `score.py`.
- **Mean daily error:** Chronos-2 (calendar and weather) 916 MW, regression 1,014, LightGBM defaults 1,134, S1 1,061, S2 1,094, TimesFM 2.5 (corrected) 1,620.
- **Findings:**
  - LightGBM matches the regression in summer and is 29% worse in winter (two winters).
  - Chronos-2 shows no leakage signature (0.807 before release, 0.808 after).
- **Cost:** the regression 0.22 s a day, Chronos-2 1.85, TimesFM one day per call 10.63.
- **Outputs:** the note is `checkpoint0/RESULTS.md`; every change is in `checkpoint0/REVISIONS.md`. Andy posted it on LinkedIn on 16 November.

**17 November:**
- **Rules completed.** Brackets settled (3.3 budget, 9.7 per-dispute reviewer, 10.2 GitHub-hosted runners); launch clause (3.6); API entrants descriptive only (3.7); issue time defined by inputs (2.1). Two reviews; see the `PROJECT.md` decision log.
- **Gates respecified.** G2 names both confirmatory pairs and fixes a missing row (`CORRECTIONS.md` 3); G3 is per-test, one-sided, 5,000 simulations, threshold 0.032, with a fixed calibration fallback; G4 re-tags the plan if the window moves.
- **`PIPELINE_RULES.md` and `WRITING.md`** added, adapted from the battery project.
- **Tails study planned** (`tails/PLAN.md`): errors on the backtest's coldest days, with tail days chosen only from forecasts and the calendar (forecaster's dilemma), narrow same-month complements, hypothesis H1 on LightGBM's extrapolation. Three reviews; ready to tag `tails-plan`. Tails 2 deferred with a trigger (step 3).
- **Scope.** Andy judged the full standing benchmark a lot for a solo researcher. Direction agreed: finish bounded pieces (tails study, the weather study's live report), put new effort into the battery work, and treat outreach as the main deliverable. Whether checkpoint 1 runs at all is open.

## Next steps, in order

1. **19 November, after 10:30:** check the weather study's first live push, with `tail -8 ~/gb-weather-data/push.log`. The live window starts on 20 November.
2. **Tag the rules:** the brackets were settled on 17 November (`PROJECT.md` decision log). Andy reads `BENCHMARK_RULES.md` once more, then tags `benchmark-rules-v1`. Before or just after: run `.github/workflows/runner_check.yml` once from the Actions tab and record the result as A13.
3. **Tails study (`tails/PLAN.md`), by 5 December:** tag the plan (`tails-plan`), then build the day sets, run the synthetic check, have the scripts reviewed, score, and write the note. Both scripts run on Andy's machine.
   - Tails 2 (deferred): uncertainty on the hardest days. Two parts: (1) spread–skill of a heterogeneous pool (regression, LightGBM, foundation models): measured over all days, leaving out the forecaster whose error is predicted, with the target error stated; prior work on ensemble spread–skill and on forecaster disagreement finds the signal often weak, and no novelty is claimed; (2) interval coverage on tail days, which needs new quantile forecasts (arXiv 2602.10848 already reports Chronos-2 coverage on outcome-selected extremes). Comes back if tails 1 finds any cold-day effect: on T1 or T4, a tail shift whose interval excludes 1, or any forecaster's bias or peak error whose interval excludes 0. If none does, tails 2 is not pursued; that means no effect large enough for tails 1 to detect, not that the question is settled.
4. **Gates G2 and G3 (January):** short scripts, committed before they run, using public data.
   - **Before G2:** backtest per-slot LightGBM under its own committed script if it is to count for the LightGBM comparator (`PROJECT.md` §4, confirmatory pairs).
   - **G2:** power for every family the fallback table can produce, each pair at c − 0.05, c and c + 0.05, at the central edge and the interval's low end, at the family's own alpha. Where LightGBM S1 is the comparator, use S1's summer edge, not the defaults' (checkpoint 0, `results.md` tables 2 and 6): it is smaller, so power will be lower than 93.7%. Show the number.
   - **G3:** the per-test false-positive rate, one-sided at alpha 0.025, from 5,000 simulations at a true edge of zero; threshold 0.032 (`PROJECT.md`, G3).
5. **Checkpoint 1's plan, frozen by 25 March 2027,** citing rules by number. Its first backtest analyses, before any tuning:
   - a pre-specified per-slot LightGBM, which tests the structure hypothesis;
   - each forecaster's error on the highest-demand days (top 10% by outturn), which tests the extrapolation hypothesis.

   It must also settle:
   - Timestral's calendar encoding (the categorical route; `mistralai/timestral#9`);
   - LightGBM tuning, on the past only, with a fixed budget;
   - the compute price for rule 5.5: the larger-runner rate (check GitHub's pricing page) and the dollar-to-pound rate, each with its date;
   - the expected total of all entrants' weights against the 10 GB Actions cache;
   - the input table and its gate check;
   - the 10% rationale;
   - whether to add one pre-specified combination, such as the average of Chronos-2 and the regression.
6. **Move the daily pipeline off Andy's laptop by 1 March 2027,** onto GitHub Actions (rule 10.2). It must then run unattended for at least 28 days before 1 April (gate G4). The workflow needs:
   - scheduled attempts after 09:30 UK (cron is UTC: for example 09:47, 13:47 and 17:47 UTC), off the hour;
   - a concurrency group keyed to the forecast day, without cancelling runs in progress, so attempts never overlap;
   - `workflow_dispatch` for manual retries;
   - per-entrant retries: later attempts forecast only entrants still missing;
   - weights fetched by pinned revision and hash-checked, with the cache as a speed-up only;
   - a weekly job archiving run IDs, times and logs (GitHub keeps logs at most 90 days).

## Watch

- **The weather study's live window** runs from 20 November 2026 to 31 March 2027 and reports in April 2027. Read TimesFM's live result against its corrected backtest.
- **Upstream replies:** record them in the relevant corrections file or note.
  - Mistral on `mistralai/timestral#9`.
  - Google on `google-research/timesfm#577`.

## Standing constraints

- Commits are authored "Andy Moran" <andrewgmoran@gmail.com>, with no AI co-author or session trailers.
- The Copernicus CDS key lives only in `~/.cdsapirc` and is never written to any file, script or commit.
- Model weights and data folders are never committed.
- Any script that produces a result is committed before it runs; its outputs are committed after.
- Committed files are never edited to fix errors; the fix goes in a `CORRECTIONS.md` or `REVISIONS.md`.
- Every source is opened before it is cited, including sources a reviewer supplies (lesson 23).
- Headlines fixed by a plan lead every note and post that reports the result. Context follows; it does not replace them (lesson 24).
- Tags cannot be pushed from Claude's workspace. Andy creates and pushes them.
