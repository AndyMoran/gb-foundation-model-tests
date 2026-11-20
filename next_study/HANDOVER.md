# Where things stand (20 November 2026, evening)

Read this first in a new session. Then read `PROJECT.md`, `BENCHMARK_RULES.md`, `ASSUMPTIONS.md`, `next_study/CORRECTIONS.md`, both `LESSONS.md` files, `checkpoint0/RESULTS.md`, `tails/PLAN.md`, `tails/RESULTS.md`, `context_novelty/PLAN.md` and `lgbm_variants/PLAN.md`. Code and documents follow `PIPELINE_RULES.md` and `WRITING.md`.

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
- **Tails study planned** (`tails/PLAN.md`), tagged `tails-plan`, then run the same day (below).

**Tails study** (`tails/`), 17 November:
- **Process.** Plan frozen at `tails-plan`. `build_days.py` and `score_tails.py` were committed before they ran, and three reviews were done before scoring. Every implementation choice and review is in `tails/REVISIONS.md`. Scored at commit 0db9b84, script sha256 07b508de…, after its synthetic check passed on the real day sets.
- **Day sets.** T1 96, T1b 96, T2 96, T3 35, **T4 0**. On no backtest day was a forecast temperature below LightGBM's training range; the closest was 0.40 °C, on 6 January 2026. 59 of T1's 96 days come from winter 2024–25.
- **Headlines** (narrow tail shift, T1). Chronos-2 did not clearly lose or gain ground: 1.055 (0.915–1.213). LightGBM S1 did not clearly lose or gain ground: 1.102 (0.988–1.217).
- **H1 unclear: a winter effect, not a cold-day effect.** LightGBM S1 lost ground against all other days (1.187, 1.066–1.298), but was already 10.5% worse than the regression on same-month days. The T4 clause was not assessed (T4 empty).
- **Other results.** TimesFM 2.5 lost ground on cold days (1.302, 1.117–1.533). Chronos-2 under-forecast the cold-day peak by 511 MW (195 to 837).
- **Note.** `tails/RESULTS.md`, published 20 November (c3a0908), with the AI-use statement (af9637b) and figures in `tails/figures/`: the paired dot plot and the peak-error chart (b1a4394). Christmas Day 2025 is stated as a limit, with no exploratory table, by Andy's decision.
- **Posts.** Andy posted a plain version (led by the headline, then what average error hid) and replied to comments from Chinmay Joshi (seasonal relationships) and Muhammed Asker (regime-aware retrieval).
- **Tails 2's trigger fired** (Andy, 17 November): the trigger counts any tail shift, including the broad one. Tails 2 is back on the list, not urgent.
**Context novelty study** (`context_novelty/`), 20 November, plan to draft note in one day:
- **Process.** Version 1 tagged `context-novelty-plan` (9e1002b). Two reviews led to version 2 before any script ran on real data: weather provenance stated; novel cold days matched to non-novel cold days on T1's mean forecast temperature (within 1 °C) and month (within one); one primary outcome; a chosen 250 MW threshold read by the interval's lower bound; a cold-spell cluster bootstrap; TimesFM exploratory and LightGBM descriptive. Tagged `context-novelty-plan-v2` (21b9a29). `build_days.py` and `score.py` were each committed before they ran, with synthetic checks that also failed when their rules were broken. Every choice and deviation is in `context_novelty/REVISIONS.md` (items 1–21).
- **Sets.** N 30 days; 14 novel cold days (N∩T1); 10 matched pairs in 4 cold spells; 4 novel days unmatched, including the three coldest in T1. A post-build review scoped H5 to the 10 pairs and added spell results and the unmatched days as description (REVISIONS 12–16).
- **Headline.** H5: meaningful penalty supported. Chronos-2's excess peak error was 1,241 MW greater on novel days than on matched controls (90% interval 589–1,765); leaving out any one spell keeps it between 1,017 and 1,551 MW.
- **The caveat that matters.** LightGBM, which context novelty should not affect, also shows Δ 618 MW (147–1,184). So the result is an association, and the backtest cannot say how much is due to the eight-week context. TimesFM 2.5's Δ was the largest (2,723 MW), opposite to version 1's dropped H6.
- **Note.** `context_novelty/RESULTS.md`, committed as a draft (625e64c). Next study suggested in it: re-forecast the same pairs with a longer context and test whether Chronos-2 improves more on novel days than on controls.

**Plan drafted, 19 November** (not yet tagged):
- **LightGBM variants** (`lgbm_variants/PLAN.md`): five pre-specified changes aimed at the heating response (V1 residual on the regression, V2 linear leaves with control V2c, V3 per-slot, V4 the regression's terms, V5 two winters); best chosen on error, as the comparator rule requires. A literature check found none is new; the nearest study is a German demand repository (LightGBM and Chronos-2 level). V5 needs INDO for March–November 2022 and ERA5 for March 2022–March 2023, fetched and checked by 3 December, or it is dropped. LightGBM does not support the L1 objective with `linear_tree` (4.7.0 source), hence V2c.
- **Why these two.** The tails study ruled out temperatures outside LightGBM's training range and found its gap on ordinary winter days (so: variants), and found Chronos-2 under-forecasting cold-day peaks (so: context novelty, now done).

- **Scope.** Andy judged the full standing benchmark a lot for a solo researcher. Direction agreed: finish bounded pieces (tails study, the weather study's live report), put new effort into the battery work, and treat outreach as the main deliverable. Whether checkpoint 1 runs at all is open.

**18–19 November:**
- **Rules in force.** An external review was checked point by point; the rules were revised and tagged `benchmark-rules-v2` (d17b658). `benchmark-rules-v1` (9d1e357, 17 November) stays as the pre-review version (`PROJECT.md` decision log). G1 passed.
- **Assumptions.** A9 (licences), A13 (runner: 4 CPUs, 15 GiB, 91 GB free) and A15 (Elexon's attribution) grounded; `ATTRIBUTION.md` added.
- **The weather study's live pipeline was pre-tested on 18 November, and three faults were fixed before the first push:**
  - there was no push task: `Weather push` now runs `push_daily.py` daily at 10:00, 15:45 and 21:00;
  - the ERA5 download task had stray text in its command and a start-up-only trigger, so it had not run since 10 November: it now runs hourly from 10:00;
  - November ERA5 was missing, and two days cached from Google's copy were empty (`weather_study/CORRECTIONS.md` 2).
- **First live push, 19 November:** inputs for 20 November, commit 6b23228, no fallback, all ERA5 from CDS. It ran at 08:55, not 10:00: yesterday's missed 15:45 run caught up when the laptop woke. The 19 November run came from a public archive copy, on time. Because a catch-up before about 07:30 would lock in a fallback, the push task's "run as soon as possible after a missed start" is to be unticked.
- **An extra push run at 16:29 on 19 November** came from an old task, `weather inputs daily` (10:30, 16:30, 21:00), which also ran the push. Andy disabled it; `Weather push` is the only push task. Later runs report "already published; nothing to do".
- **Battery project.** It has its own handover and claude.ai project; its pre-registration is not yet locked.
- **Parked plans**, committed as parked (b1a4394) and in this claude.ai project: `weather_value/PLAN.md` (what perfect weather is worth; an update of National Grid's analysis) and `weather_inputs/PLAN.md` (urban heat, terrain, downscaling; waits on `weather_value`). Parked until the current studies are published.

## Next steps, in order

1. **Daily, as needed:** `tail -8 ~/gb-weather-data/push.log` should end `=== end …: ok`. Untick catch-up on the push task (above).
2. **Done 18 November:** rules tagged `benchmark-rules-v2`; A13 recorded.
3. **Done 20 November:** tails note published; figures committed.
   - Tails 2 (triggered, not urgent): uncertainty on the hardest days. Two parts: (1) spread–skill of a heterogeneous pool (regression, LightGBM, foundation models): measured over all days, leaving out the forecaster whose error is predicted, with the target error stated; prior work on ensemble spread–skill and on forecaster disagreement finds the signal often weak, and no novelty is claimed; (2) interval coverage on tail days, which needs new quantile forecasts (arXiv 2602.10848 already reports Chronos-2 coverage on outcome-selected extremes). Note that tails 1 found no T4 days, so a tails-2 design cannot rely on out-of-range temperatures.
4. **Publish the context novelty note, after a review, before 4 December:** send `context_novelty/RESULTS.md` through the reviewer's figure check, set the publication date, commit and publish. Any post leads with the two headline sentences unchanged (lesson 24), and must give LightGBM's 618 MW straight after them.
5. **LightGBM variants, by 17 December:** Andy tags `lgbm-variants-plan`; fetch and check V5's data by 3 December (Copernicus key from `~/.cdsapirc` only); `gb-weather-private/weather/lightgbm_variants.py` with the checks in its §8, committed before it runs; then `lgbm_variants/score.py` and the note. It must finish before G2, because its best variant becomes the LightGBM comparator if checkpoint 1 runs.
**Decision point, 8 January 2027: does checkpoint 1 run?** Andy decides, with the variants result in hand. Everything below this line is conditional on a yes; nothing in 2027 is committed except the weather study's live window (it ends in March and reports in April) and its daily push.
- **If yes:** steps 6 to 8 as written.
- **If no:** publish `BENCHMARK_RULES.md` as a proposal, not a commitment; offer it to the TS-Arena team and the author of the German demand repository (`PROJECT.md` §1); record the decision in the `PROJECT.md` log; the body of work is the weather study, checkpoint 0, the tails study, context novelty and the variants, plus the weather study's live result in April.
- **Why the date:** Andy's concern (20 November) is a commitment running far into 2027, not the December workload. Checkpoint 1 means gates in January, the pipeline move by 1 March, a live window from April to September and a report in autumn 2027.

6. **Gates G2 and G3 (January, only if checkpoint 1 runs):** short scripts, committed before they run, using public data.
   - **Before G2:** backtest per-slot LightGBM under its own committed script if it is to count for the LightGBM comparator (`PROJECT.md` §4, confirmatory pairs).
   - **G2:** power for every family the fallback table can produce, each pair at c − 0.05, c and c + 0.05, at the central edge and the interval's low end, at the family's own alpha. Where LightGBM S1 is the comparator, use S1's summer edge, not the defaults' (checkpoint 0, `results.md` tables 2 and 6): it is smaller, so power will be lower than 93.7%. Show the number.
   - **G3:** the per-test false-positive rate, one-sided at alpha 0.025, from 5,000 simulations at a true edge of zero; threshold 0.032 (`PROJECT.md`, G3).
7. **Checkpoint 1's plan (only if it runs), frozen by 25 March 2027,** citing rules by number. Its first backtest analyses, before any tuning:
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
8. **Move the daily pipeline off Andy's laptop by 1 March 2027 (only if checkpoint 1 runs),** onto GitHub Actions (rule 10.2). It must then run unattended for at least 28 days before 1 April (gate G4). The workflow needs:
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
