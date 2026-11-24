# Where things stand (24 November 2026, evening)

Read this first in a new session. Then read `PROJECT.md`, `BENCHMARK_RULES.md`, `ASSUMPTIONS.md`, `next_study/CORRECTIONS.md`, both `LESSONS.md` files, `checkpoint0/RESULTS.md`, `tails/PLAN.md`, `tails/RESULTS.md`, `context_novelty/RESULTS.md`, `lgbm_variants/RESULTS.md`, `asymmetric/RESULTS.md`, `arbitrage/RESULTS.md`, `imbalance_cost/RESULTS_stage1.md` and `disagreement/RESULTS_stage1.md`. Code and documents follow `PIPELINE_RULES.md` and `WRITING.md`.

## The project

A standing, preregistered benchmark. Zero-shot foundation models are tested against trained baselines for GB day-ahead demand (INDO), on equal weather and calendar inputs, on live days no model can have seen, with cost measured. It commits to a minimum of three checkpoints, reviewed at the third. Rules: `BENCHMARK_RULES.md`, in force at tag `benchmark-rules-v2`. Why and how: `PROJECT.md`.

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
- **Note.** `context_novelty/RESULTS.md`, published 20 November (d000ae0); REVISIONS 23 (21c9f8c) explains how to read Δ.
- **Longer-context check** (`context_check.py`, 1107ff8): a 24-week context changes no pair; about 49 weeks clears the six November pairs. This led to `context_novelty_2/PLAN.md`, drafted and parked (06e5605), not tagged.

**LightGBM variants** (`lgbm_variants/`), published 22 November (96f8ba6):
- **Process.** Plan tagged `lgbm-variants-plan`. V5's data fetched and checked (`fetch_v5.py`, ERA5 overlap passed). Forecasts made by `gb-weather-private/weather/lightgbm_variants.py` (sha256 69968508…) after its synthetic and real checks passed; scored by `score.py`; exploratory additions in `explore.py`, committed before it ran. Every choice is in `REVISIONS.md` (items 1–22).
- **Headline.** The best of five pre-specified variants, V1 (LightGBM on the regression's residual), beat the regression: 0.984 times its error (0.973–0.994). Chronos-2 had 0.918 times V1's error (0.887–0.948). V1 was chosen on the same days, so its figure is optimistic.
- **Findings.** V1 closed LightGBM's winter gap (0.992 in winter, 0.976 on the coldest tenth, against S1's 1.125 and 1.218). V2 (linear leaves) produced extreme forecasts on a few days and did not test linear leaves reliably. The TNEI description was checked against the report, p. 18.
- **Consequence.** V1 is the LightGBM comparator if checkpoint 1 runs.

**Asymmetric cost** (`asymmetric/`), 22 November:
- **Process.** Plan after three reviews and a literature check, tagged `asymmetric-plan` (dc78a88). `score.py` committed before it ran (15a479a); synthetic output a3ff952; results 77fe107; note 53e340d; figure `figures/cost_ratio_chart.png` (cccfd60). Implementation choices in `REVISIONS.md` (items 1–11).
- **Headline.** Over all half-hours, Chronos-2 had clearly less cost-weighted error than the regression at every cost ratio from 0.5 to 10; there is no break-even (96% of draws). On the daily peak of the coldest tenth of days it was not clearly different from 0.5 to 1.5 and clearly worse from 2 to 10; break-even 0.69 (conditional interval 0.38–1.53).
- **Findings.** Chronos-2 sets the cold-day peak too low by 776 MW on average (regression 395). The fixed 50:50 average of Chronos-2 and the regression beat both over all half-hours (833 MW, 9% below Chronos-2) and beat Chronos-2 at cold peaks for every ratio from 1. Chronos-2's bias is not linear in temperature (slope +1.2 MW/°C): short in the coldest tenth, clearly long in the next two. Most predictions on direction failed; the note scores each.
- **Limit worth repeating.** Only Chronos-2's median was saved; its quantiles might serve a shortfall-averse user better.

**Arbitrage signal** (`arbitrage/`), 23 November:
- **Process.** Plan tagged `arbitrage-plan` (468ccdc). `score.py` committed before it ran (000879c); synthetic output 6d2ddc7; results fe866ce; note 468b3fe; figures `figures/timing_chart.png` and `figures/combination_chart.png` (cccfd60). `REVISIONS.md` item 1 corrects the plan's sign slip in the bias correction (the code adds the recent mean of outturn minus forecast).
- **Headline.** Choosing a two-hour battery's hours, Chronos-2 missed clearly less of each day's demand spread than the regression (219 against 409 MW a day; NESO 255). Where it disagreed with NESO, outturn moved clearly towards it (272 MW), but so it did for every forecaster, the regression included (262).
- **The gain test is easy to pass:** any forecast whose errors differ from NESO's tends to be right when NESO is wrong (lesson 25). The stricter test is the combination: averaging with NESO cut NESO's error only for Chronos-2 (3%, 679 against 700 MW) and the 50:50 average (8%). The regression added nothing.
- **Day-to-day direction.** NESO called the change in daily mean most often (87%); Chronos-2 less often than the regression (81% against 84%).
- **Consequence.** Both demand-side preconditions for a trading edge appeared, so the parked price study was reopened (below).

**Imbalance exposure** (`imbalance_cost/`), 23–24 November. Stage 1 (backtest pilot) done; stage 2 (live) after 31 March 2027:
- **Plan.** The parked price plan, redrafted after one review and tagged `imbalance-cost-plan` (f0678fa). Two stages with one frozen code path: a backtest pilot with no money claim, then the live window. Open prices only: the System Price against Elexon's Market Index Price (a near-real-time traded price; the day-ahead auction carries zero weight in it). Main measure: net imbalance exposure, (A − F) × (SP − MIP) × 0.5 h, in £ per GWh of demand, with losses and gains separate. Secondary: a demand-proxy dispatch ranking, explicitly not battery earnings. No net-demand forecast.
- **Prices.** `fetch_prices.py` (cda8165); manifest ceeacf0. System Price complete; Market Index Price missing in 20 half-hours. A provider reporting zero volume is left out of the index, never averaged in as a price of 0 (N2EX reported zero volume in almost every half-hour). Seven days dropped for a missing index price.
- **Stage 1 headline.** In a backtest the foundation models may have seen in training, a supplier using Chronos-2 would have had net imbalance exposure not clearly different from one using the regression (75 against 86 £ per GWh). Note `RESULTS_stage1.md` (ecfd1e0); `score.py` fa794fa; results 058f043.
- **Findings.** A MWh of miss was worth about £2 net. NESO's misses cost the most per MWh (£3.00), so its average exposure is no lower although its errors are smallest; interpretation, not tested: market positions follow NESO's forecast, so its misses line up with the system's. Shortfall cost is concentrated in cold evenings.
- **Frequency and tail** (`explore.py`, added after the results following a review; 2c4c748, results b5dd652). Misses were on the costly side about 47% of half-hours, earning 45%. Each forecaster's worst 10% of half-hours carried about two-thirds of gross losses. 8 January 2025 (Electricity Margin Notice) was the worst day for every forecaster; the regression under-forecast by 1.6 GW that day. On the mean of the worst 5% of days, NESO and the 50:50 average were clearly better than the regression; Chronos-2 was not clearly different. Worst days cluster on clock changes and Easter, from genuine forecast error.
- **Revisions 1–16,** including the plan's open questions settled after tagging, a code review of `explore.py` that changed no figure (15), and a superseded sentence in the note (16). Revision 15 lists fixes to make before stage 2 reuses the scripts.
- **Weather study correction 3** (f0678fa): the live window's scoring would batch TimesFM 2.5 with weather; it is to run one day per call before any live day is scored.

**Disagreement value** (`disagreement/`), 24 November. Stage 1 (backtest pilot) done; stage 2 (live) after 31 March 2027, with the imbalance study's:
- **Question.** Andy asked whether the foundation models are "more directionally right" than NESO: NESO is judged on average error, a trader on being right when it pays. What would switching from NESO's day-ahead forecast to each forecaster have earned at real prices? Value per half-hour v = (F − NESO) × (SP − MIP) × 0.5 h, which is exactly NESO's imbalance exposure minus F's.
- **Framing.** By rule 7.5's 10% bar, Chronos-2 has no accuracy case against NESO (about 31% worse), so settlement value is its only case, about a penny per MWh at the point estimate. The plan expected a calibrated near-null and said it was worth publishing.
- **Plan.** Measures: A value per GWh; B value per MWh of disagreement by size of disagreement; C by price stress; D direction alone (hit rate, sign payoff), with a **sign-flip null** (each day's half-hours keep their sizes but take one random sign; also by 7-day block); E tail days; F accuracy ratio to NESO beside every value. Year-by-year split in stage 1. Frozen at **tag `disagreement-plan-3a260a2`**: the tag `disagreement-plan` points to ddb2798 in error and cannot be deleted (REVISIONS 1).
- **Literature** (`LITERATURE.md`): seven papers opened. Lipiecki and Weron (statistical dominance need not mean economic dominance), Tahavori and Shaker, Hornek et al., Bui et al., Wu et al., TS-Arena and Upadhyay (source of the sign-flip null) are cited. Bui et al.'s abstract says Chronos-2's imbalance-price error is 10% higher; its tables give +4.3% to −0.3%, so the recomputed figures are cited.
- **Stage 1 headline.** In a backtest the foundation models may have seen in training, Chronos-2's forecast had 1.31 times NESO's daily error (1.26 to 1.36), and a supplier that bought it instead of NESO's would have neither clearly gained nor lost (9 £ per GWh, −11 to 28); the regression −1 (−20 to 18). Largest quarter of disagreements: 0.07 £ per MWh (−0.80 to 0.90), against −0.45 (−0.91 to 0.07) in the smallest.
- **Findings.** Chronos-2 was within chance on every sign-flip measure: hit rate 50.0%, and 25% of coin-flipped copies earned as much. Value did not grow with disagreement or concentrate in stressed prices. The test detects about ±£20 per GWh. It found LightGBM S1 clearly losing (−50) and worse than chance on all three measures, and TimesFM's hit rate worse than chance, so it is not blind; no forecaster was reliably good. Year by year: +15, −1, +16, no trend. For a supplier: no reason to switch from NESO to Chronos-2 on this evidence.
- **Files.** `score.py` a402043; synthetic ff4eda6 (13 of 13); results aa1021c; note `RESULTS_stage1.md` aaf12c6. Revisions 1–8: 6 reports shares of value only where the total is clearly non-zero; 7 leaves the 8 January prediction unscored (days were not ranked) and lapses it; 8 fixes the stage 2 replication rule.

**Live calendar forecasts for stage 2** (`gb-weather-private/weather/calendar_live.py`, e0704d5). Chronos-2 with calendar and weather (the backtest's `chronos2_A`), issued daily for the live window. Each day's demand input must hash to the prospective run's recorded `input_sha256`, and its weather input is the committed file pushed for that day. Reproduction check: six backtest days within 0.0043 MW of E5 (ce6b3e6). 20–23 November reconstructed and labelled; 24 November onward issued. Outputs in `imbalance_cost/calendar_live/`, with a manifest. Task `Calendar live`, in `gbwx`; log `~/gb-weather-data/calendar_live.log`.

**Daily schedule changed, 24 November.** The 10:00 push failed on 23 and 24 November ("DROPPED under the rules: ERA5 missing values" at 9 November 00:00–04:00 UTC) and succeeded later each day, once the hourly ERA5 download had refreshed the November file. First triggers moved: `Weather push` 11:15, 15:45, 21:00; `Calendar live` 11:45, 16:00, 21:30. The 09:45 prospective forecast is unchanged. Neither task catches up a missed start.

**A pattern to watch.** The pre-specified 50:50 average of Chronos-2 and the regression has now done well in four places: weighted error, battery timing, combination with NESO, and the tail of imbalance exposure. It is descriptive each time, on days the foundation model may have seen. In the disagreement study it showed no settlement edge over NESO (4 £ per GWh, −12 to 19, within chance), though it was the closest to NESO on accuracy (1.19 times its error). Checkpoint 1's plan already lists "one pre-specified combination" as a question to settle.

**Posts.** LinkedIn drafts for the asymmetric and arbitrage notes exist (23 November), each led by its fixed headline; not yet posted as far as this record knows. In the arbitrage post, "best of every forecaster" should read "less than every other forecaster, NESO included, on the point figures": Chronos-2 and NESO were not compared directly.

**Scope.** Andy judged the full standing benchmark a lot for a solo researcher. Direction agreed: finish bounded pieces, put new effort into the battery work, and treat outreach as the main deliverable. Whether checkpoint 1 runs at all is decided on 8 January 2027.

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
- **Parked plans**, each committed and in this claude.ai project, none tagged (the price plan was unparked and tagged on 23 November):
  - `weather_value/PLAN.md` (what perfect weather is worth) and `weather_inputs/PLAN.md` (urban heat, terrain, downscaling; waits on `weather_value`), b1a4394.
  - `context_novelty_2/PLAN.md` (Chronos-2 hourly, 8 weeks against about 49 weeks of context), 06e5605. Its unparking condition, the variants note, is met.

## Next steps, in order

1. **Daily, as needed:** `tail -8 ~/gb-weather-data/push.log` should end `=== end …: ok`, and `tail -2 ~/gb-weather-data/calendar_live.log` should show the next day issued or already made. A missed calendar day is filled with `--reconstruct` and labelled. If the 11:15 push says DROPPED for missing ERA5, the later runs usually succeed; if it recurs, move the first trigger later again.
2. **Tails 2** (triggered, not urgent): uncertainty on the hardest days. Two parts: (1) spread–skill of a heterogeneous pool, measured over all days, leaving out the forecaster whose error is predicted; prior work finds the signal often weak, and no novelty is claimed; (2) interval coverage on tail days, which needs new quantile forecasts (arXiv 2602.10848 already reports Chronos-2 coverage on outcome-selected extremes). Tails 1 found no T4 days, so a design cannot rely on out-of-range temperatures.
3. **Post the asymmetric and arbitrage notes** (Andy), and optionally the stage 1 pilots of the imbalance and disagreement studies. Asymmetric first. Each post leads with its fixed headline (lesson 24); the arbitrage post keeps the paragraph on why the gain test is easy to pass straight after it. A stage 1 post must say it is a pilot. The imbalance pilot's strongest content is the tail (8 January 2025; mean against worst days); the disagreement pilot's is the coin-flip table and what the test can detect (about ±£20 per GWh; S1 caught, nothing reliably good).
4. **Stage 2 of the imbalance and disagreement studies (April 2027).** The disagreement study reuses the imbalance study's data and loader, so they run in this order:
   1. After 31 March: fetch the live window's prices with `fetch_prices.py --first 2026-11-05 --last 2027-03-31`, and commit the manifest.
   2. Make the weather arm's forecasts (TimesFM one day per call, weather study correction 3).
   3. **Imbalance:** add the stage 2 loader to `imbalance_cost/score.py` and make its revision 15 fixes, each recorded in `imbalance_cost/REVISIONS.md` before stage 2 runs; synthetic check; score; note.
   4. **Disagreement:** in `disagreement/score.py`, before it runs on stage 2, and each recorded in `disagreement/REVISIONS.md` first: load stage 2 through the imbalance loader; seeds 20270402 (bootstrap), 20270403 (null) and 20270404 (null by 7-day block); add each forecaster's five best and five worst days with dates (REVISIONS 7); report shares of value only where the total is clearly non-zero (REVISIONS 6); no year-by-year split; LightGBM V1 and S1 are stage 1 only (PLAN.md §6). Commit, run the synthetic check, commit its output, then score.
   5. **Disagreement verdict:** apply REVISIONS 8 to Chronos-2 and to the average: replicated, contradicted, or neither. Say how large an edge the wider stage 2 intervals still rule out.
   6. **Both notes:** report the primary results on issued days alone as well as on all days. Stage 2's headline opens "On [n] days no model could have seen," and leads; stage 1 follows as the pilot.
5. **Housekeeping:** Zenodo DOIs for the notes published since the weather study's correction (tails, context novelty, LightGBM variants, asymmetric, arbitrage, imbalance stage 1, disagreement stage 1), or one DOI for the repository at a tagged release.

**Decision point, 8 January 2027: does checkpoint 1 run?** Andy decides, with the variants result in hand. Everything below this line is conditional on a yes; nothing in 2027 is committed except the weather study's live window (it ends in March and reports in April) and its daily push.
- **If yes:** steps 6 to 8 as written.
- **If no:** publish `BENCHMARK_RULES.md` as a proposal, not a commitment; offer it to the TS-Arena team and the author of the German demand repository (`PROJECT.md` §1); record the decision in the `PROJECT.md` log; the body of work is the weather study, checkpoint 0, the tails study, context novelty, the variants, the asymmetric, arbitrage, imbalance and disagreement studies, plus the weather study's live result and both stage 2s in April.
- **Why the date:** Andy's concern (20 November) is a commitment running far into 2027, not the December workload. Checkpoint 1 means gates in January, the pipeline move by 1 March, a live window from April to September and a report in autumn 2027.

6. **Gates G2 and G3 (January, only if checkpoint 1 runs):** short scripts, committed before they run, using public data.
   - **Before G2:** the LightGBM comparator is V1 from the variants study; per-slot LightGBM (V3) was one of the five variants and lost to V1.
   - **G2:** power for every family the fallback table can produce, each pair at c − 0.05, c and c + 0.05, at the central edge and the interval's low end, at the family's own alpha. Use the comparator's own summer edge (V1's), not the defaults': it is smaller, so power will be lower than 93.7%. Show the number.
   - **G3:** the per-test false-positive rate, one-sided at alpha 0.025, from 5,000 simulations at a true edge of zero; threshold 0.032 (`PROJECT.md`, G3).
7. **Checkpoint 1's plan (only if it runs), frozen by 25 March 2027,** citing rules by number. Its first backtest analyses, before any tuning:
   - each forecaster's error on the highest-demand days (top 10% by outturn), which tests the extrapolation hypothesis.

   It must also settle:
   - Timestral's calendar encoding (the categorical route; `mistralai/timestral#9`);
   - LightGBM tuning, on the past only, with a fixed budget;
   - the compute price for rule 5.5: the larger-runner rate (check GitHub's pricing page) and the dollar-to-pound rate, each with its date;
   - the expected total of all entrants' weights against the 10 GB Actions cache;
   - the input table and its gate check;
   - the 10% rationale;
   - whether to add one pre-specified combination, such as the average of Chronos-2 and the regression, which did well descriptively in the asymmetric and arbitrage studies.
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
- Tags cannot be pushed from Claude's workspace. Andy creates and pushes them, after Claude has pushed the commit to be tagged; tag by commit hash. The repository's rules forbid deleting a tag, so a wrong tag stays and a corrected one is added.
- A paper's tables are checked, not only its abstract, before a figure from it is cited.
