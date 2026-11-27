# Quantile forecasts from the strongest of three foundation models tested on GB day-ahead demand: do they beat a band you can build in a spreadsheet?

Andy Moran (Heaviside Analytics) · 27 November 2026 · **Status: draft, to be frozen at tag `quantiles-plan` before any backtest quantile is made.** An exploratory study in two stages (§5), built on the imbalance study's data and code.

**No quantile has been compared with outturn or prices, in the backtest or live, before this plan is tagged** (§4).

For: a GB electricity supplier or trader deciding how much to commit day-ahead, when a shortfall costs *k* times a surplus.

**The question.** Chronos-2 is the most accurate of the three foundation models this benchmark tested: its median forecasts averaged 916 MW of daily error, against 1,089–1,103 MW for Timestral (its two configurations¹) and 1,620 MW for TimesFM 2.5 (checkpoint 0). Every forecast scored so far is its median. But a supplier whose shortfall costs *k* times a surplus should position at the *k*/(1 + *k*) quantile, not the median (`asymmetric/RESULTS.md`). Chronos-2 gives those quantiles directly. They can also be built cheaply, by adding the quantiles of a forecast's recent errors to the forecast (dressing) — a band anyone can make in a spreadsheet.

So the question is whether positions set from Chronos-2's own quantiles cost less than positions set from two such bands: its own median dressed this way, which isolates what its quantiles add; and NESO's free forecast dressed the same way, the alternative a supplier actually has. Calibration, and whether the band widens before a miss, explain the answer.

¹ Checkpoint 0 does not rank Timestral, because of a defect in its calendar input (`mistralai/timestral#9`). It is less accurate than Chronos-2 in both of its configurations.

## 1. Why

**What a quantile is.** A 0.9 quantile of 31 GW says: "there is a 90% chance demand will be at or below 31 GW." If the forecaster is honest, outturn falls below its 0.9 quantile 90% of the time. Chronos-2 gives 21 levels: 0.01, 0.05, every 0.05 from 0.10 to 0.90, 0.95 and 0.99 (`calendar_quantiles.py`, `GRID`).

**The score is a decision cost.** If a shortfall costs *k* times a surplus, the cost of positioning at *q* in a half-hour is exactly (1 + *k*) times the pinball loss (§7) at level *k*/(1 + *k*). So each level's pinball loss is, up to that factor, the cost of one supplier's decision (Laio and Tamea 2007). The primary score is the equal-weight average of the pinball loss over the 17 levels from 0.10 to 0.90: the decisions of suppliers whose cost ratios run from 1:9 to 9:1. It is not an average over cost ratios, because equal steps in level are unequal steps in ratio (0.10 to 0.15 spans *k* from 0.11 to 0.18; 0.85 to 0.90 spans 5.7 to 9), and each level's loss is its cost divided by 1 + *k*. It is a standard summary. Four named ratios give single decisions (§7 A). No real supplier's ratio was measured.

**The cheap band.** Dressing is an old baseline (Roulston and Smith 2003). A dressed band has roughly constant width. If Chronos-2's quantiles do no better, they add nothing a supplier could not build in a spreadsheet.

**Why they might fail.** Chronos-2 receives ECMWF's weather forecast for the target day as a known input (`weather_study/PLAN.md` §2–4). Nothing tells it the weather forecast can be wrong. Its bands may therefore be too narrow, most of all when the weather forecast misses. Its worst days are calendar days (`imbalance_cost/worst_days_results.md`), which its bands may not foresee.

**What is not new.** The pinball loss is a proper score for a quantile (Gneiting and Raftery 2007); its mean over levels scored the load track of the 2014 Global Energy Forecasting Competition (Ziel and Liu 2016). Calibration and sharpness are judged together (Gneiting, Balabdaoui and Raftery 2007). Sorting crossed quantiles cannot move them further from the truth (Chernozhukov, Fernández-Val and Galichon 2010). What this adds is the test for a zero-shot foundation model on GB day-ahead demand, with a day-ahead weather forecast as input, against dressed point forecasts, with a live replication.

**Related work.** Chronos-2's bands have mostly been found honest. Its developers report the best calibration on 23 of 24 metric-interval pairs across three general benchmarks (Ansari et al. 2026). On 200 German low-voltage feeders, its 90% intervals covered 89.75% of outturns, and it had the lowest pinball loss of nine models (Kaas et al. 2026). On Polish national load, its 80% intervals came within 0.04 of nominal coverage (Michael et al. 2026). But pooled coverage can hide errors in opposite directions: across 55 general datasets, its calibration error was larger step by step through the horizon than pooled (Decker and Tresp 2026). None of these studies gave the model a day-ahead weather forecast; the feeder study used weather one to three hours ahead. `LITERATURE.md` records how each source was checked.

## 2. What this study shows

- **Whether Chronos-2's quantiles make a cost-aware position cheaper** than its own dressed median and than dressed NESO: on the equal-weight average over levels 0.10 to 0.90, and at four named cost ratios.
- **Why:** how honest its bands are, and whether they widen before its median misses.
- **Where:** on cold days, winter days, evenings and calendar days.

## 3. What this study does not show

- **Whether the bands are worth buying.** A supplier's alternatives are NESO's forecast with a band of its own making, or a commercial probabilistic forecast. This study tests the first, built one fixed way, and cannot test the second.
- **Foundation models in general.** It tests the strongest of the three tested, zero-shot and untuned. TimesFM 2.5's quantiles, tabular foundation models such as TabPFN-TS, and models trained to give quantiles are not tested.
- **NESO's view of its own uncertainty.** NESO publishes a point forecast; its band here is this study's construction.
- **Money.** Costs are in MW of pinball loss, not pounds. Two uses of the quantiles at real prices are left for a later exploratory note, planned and committed before any quantile is joined with a price: whether Chronos-2's confident disagreements with NESO point the right way, and whether its 0.10 and 0.90 quantiles pick a battery's hours better than its median.
- **Live performance from the backtest.** See §5.

## 4. What is known before this plan

Every earlier result, including the mean daily errors of the medians: Chronos-2 916 MW, NESO 700, the weather regression 1,014 (checkpoint 0).

About the quantiles, only what `calendar_quantiles.py` reports as it writes each live day: the 0.5 quantile equals the issued median (largest difference 0.0 MW on every day so far), and some half-hours have crossing quantiles (on the nine days so far, at most 4 a day, by at most 66 MW). **No quantile has been compared with outturn or prices.** No backtest quantile exists; the backtest's forecasts are medians only (`code/models.py`, `quantile_levels=[0.5]`).

The predictions (§9) are written before any of this is computed.

## 5. Two stages

**Stage 1: backtest pilot.** The 960 backtest days, 16 March 2024 to 31 October 2026. After the tag, a new script (§11) reruns the configuration scored as `chronos2_A` (Chronos-2 with calendar and weather; the weather study's check E5) with the same code, inputs, pinned weights and settings, asking for 21 levels instead of one. Chronos-2's disclosed pretraining data contain no GB national demand and nothing from the backtest period (`ASSUMPTIONS.md` A16), but undisclosed overlap cannot be ruled out, so stage 1 is a pilot.

**Stage 2: live replication.** Target days 20 November 2026 to 31 March 2027, scored after the window with the same code. `calendar_quantiles.py` writes each day's quantiles beside its median (`imbalance_cost/REVISIONS.md` 19). Days from 28 November are **issued**: pushed before 00:00 UK time on the target day, by GitHub's server-side record. Days 20 to 27 November, and any day whose push is missed, are **reconstructed** from inputs archived in advance. The note reports issued days alone as well as all days. About 130 days, mostly winter, give wide intervals.

## 6. Forecasters

All forecast INDO outturn, in MW, for each half-hour of the target day. Forecasts and outturn are matched by settlement period. Clock-change days have 46 or 50 half-hours and are scored on all of them, as in every earlier study; check 4 confirms the counts match.

- **Chronos-2's quantiles** (`chronos2_A`, 21 levels).
- **Chronos-2's median, dressed** (primary comparison).
- **NESO's day-ahead forecast, dressed** (primary comparison).
- **The weather regression, dressed** (`regression_weather`; descriptive). In stage 2 it is the weather study's prospective arm, made after the window from archived inputs.

**Dressing.** For target day *D*, take the forecaster's errors (outturn minus forecast) on the latest 56 days that end on or before *D* − 2 and have a forecast and full outturn. Group them by the UK start time of the half-hour into four blocks: 00:00–05:30, 06:00–11:30, 12:00–17:30 and 18:00–23:30. A half-hour's dressed *q*-quantile is the forecast plus the *q*-quantile of its block's errors (about 670 errors; NumPy's default interpolation). *D* − 1 is excluded because its outturn is incomplete at issue time. A day with fewer than 28 qualifying days is dropped from every comparison and listed; in stage 1 this drops about the first month. In stage 2 the window reaches back into the backtest where live forecasts do not yet exist; Chronos-2 has none for 1 to 19 November 2026. The window and blocks are fixed and never tuned; §7 A reports how much they matter.

**Crossing.** Quantiles can cross: a lower level above a higher one in the same half-hour. They are stored as made. For scoring, each half-hour's 21 values are sorted into increasing order, which changes nothing where they do not cross. The note reports how many half-hours were sorted and by how much, every primary result on the raw values too, and any half-hour where sorting moved the 0.5 quantile.

## 7. Measures

*y* is outturn and *q*τ the forecast at level τ. The **pinball loss** at τ is τ(*y* − *q*τ) if *y* ≥ *q*τ, and (1 − τ)(*q*τ − *y*) otherwise, in MW; at τ = 0.5 it is half the absolute error. The **score** of a half-hour is the mean pinball loss over the 17 levels from 0.10 to 0.90. The four tail levels are left out because the dressed tails rest on few errors: about 7 of 670 lie below the 0.01 quantile. The **full score**, over all 21 levels, is reported beside it; it roughly approximates half the CRPS (`LITERATURE.md` 2) but is not called that. Lower is better. A day's score is the mean over its half-hours; the study's figure is the mean over days.

**A. Decision cost (primary).** Two ratios, each with its 90% interval: Chronos-2's score to its dressed median's (what the model's quantiles add), and to dressed NESO's (the supplier's alternative). Each is **clearly lower** if its interval lies wholly below 1, **clearly higher** if wholly above, otherwise **not clearly different**. With so many half-hours, a trivial difference can be clear, so each ratio also carries a practical label: **practically lower** if the point ratio is below 0.95, **practically higher** if above 1.05, otherwise **practically equal**. The 5% margin is a convention, fixed now, half of rule 7.5's 10% bar for switching; it is not a measured cost of switching. Only a ratio that is both clearly and practically lower is read as a gain. Also reported:
- **At named cost ratios** (primary): the same two ratios, with both labels, at *k* = 1, 3, 4 and 9, levels 0.50, 0.75, 0.80 and 0.90. A supplier who knows its ratio can read its row. With the two averages these make ten unadjusted comparisons, so one clear result is weak evidence alone; the note counts the clear results in each direction.
- **By level:** the ratios at each of the 21 levels, to show whether any gain lies in the centre or the tails.
- **Robustness to the dressing:** both primary ratios with windows of 28, 56 and 90 days (four blocks), and with 2, 4 and 8 blocks (56 days), on the same days. Two blocks split the day at 00:00 and 12:00; eight are 3-hour blocks from 00:00. The result is **robust to the dressing** if all five variants carry the same labels.
- **Descriptive:** the ratio to the dressed regression, and whether any ratio is credibly below 0.9, in the manner of rule 7.5.

**B. Calibration.** For each forecaster: the share of outturns at or below each level, beside the level; the coverage of the 80% interval (0.10 to 0.90) and the 98% interval (0.01 to 0.99), with 90% intervals; and each interval's mean width in MW, because a band can be honest and useless. A coverage whose interval lies wholly below nominal is **too narrow**, wholly above **too wide**, otherwise **consistent with its level**. With some 44,000 half-hours these strict labels will flag small gaps, so a practical label sits beside each: **practically consistent** within 3 percentage points of nominal for the 80% interval and 1 point for the 98% interval, otherwise **practically too narrow** or **practically too wide**. These tolerances are conventions, fixed now so they cannot be chosen after the result. The study measures no reserve or operating impact, so neither label says what a gap would cost. The dressed 98% intervals rest on about 7 errors at each end of each block, so their coverage is reported but not interpreted, and no gap between Chronos-2 and a dressed band at 98% is read as a difference in band quality. Coverage is also reported for each of the four dressing blocks, with the largest gap from nominal, because pooled coverage can hide errors in opposite directions (Decker and Tresp 2026).

**C. Does the band widen before a miss?** For each day, Chronos-2's mean 80% interval width and its median's mean absolute error. Days are ranked by width **within each calendar month**, then pooled into four equal groups, so that the season, which widens bands and errors alike, cannot drive the result. Reported: the median's mean daily error in each group; the ratio of the widest group's to the narrowest's, with its interval; and the Spearman correlation of width with error within each month with at least 20 scored days, summarised by the median over months and the number of months in which it is positive. The same for the dressed median, as the reference. The ranking and the correlation over the whole year are shown too, but not interpreted.

**D. Hard days (descriptive).** A and B on the coldest tenth of days (T1, `tails/days.csv`; stage 1 only), winter days (December to February), the evening window (16:00 to 19:30 UK time), the calendar days of the worst-days analysis (bank holidays, Easter, 24 December to 1 January, clock changes), and, in stage 1, **stage 2's season**: every backtest day dated 20 November to 31 March, the same span of the year as stage 2.

**Intervals and labels.** The tails study's 7-day moving-block bootstrap over days: 2,000 draws, the same for every forecaster, seed 20261129 for stage 1 and 20270405 for stage 2. Ratios are of totals over the resampled days. Labels are unadjusted and descriptive; they are not tests.

## 8. Checks before each real run

1. **The quantiles belong to the medians.** Stage 1 writes every backtest day, recording the largest difference between its raw 0.5 quantile and the scored `chronos2_A` forecast. A day is **exact** (every half-hour within 0.001 MW), **close** (within 0.01 MW) or **mismatched**. Chronos-2 gives its quantiles directly, without sampling, so there is no seed to fix; the only expected difference is floating-point order when days are batched differently (`calendar_study.py`). `calendar_live.py`'s reproduction check found differences of 0.002 to 0.004 MW on six backtest days run singly (`imbalance_cost/calendar_live/check.json`). So **close** allows a little over twice the largest difference rounding has produced, and nothing more; anything larger points to something other than rounding. Primary results use exact and close days. Any mismatched day stops the scoring until the cause is found and recorded in `REVISIONS.md`, because mismatched days may be the hard ones. Then every primary result is reported on exact days, on exact and close days, and on all days, with any change of label stated. If more than 5% of days are mismatched and the cause cannot be fixed, stage 1 is abandoned and stage 2 proceeds alone. In stage 2, every day's file must carry a passed median check and match its manifest hash.
2. **Reproduction.** The medians' mean daily errors match checkpoint 0's to 0.01 MW (stage 1) or the weather study's prospective figures (stage 2).
3. **No look-ahead.** Every dressing window ends on or before *D* − 2; changing outturn on *D* − 1 or later leaves *D*'s dressed quantiles unchanged.
4. **Arithmetic.** Every scored day has as many forecast half-hours as outturn half-hours, including the 46- and 50-half-hour clock-change days. A forecast equal to outturn at every level scores 0. The 0.5-level score is half the mean daily error. Sorting leaves an uncrossed half-hour unchanged.
5. **Synthetic.** On invented data with known answers:
   - outturns drawn from the forecast's own distribution are labelled "consistent with its level";
   - bands half as wide as the truth are "too narrow", twice as wide "too wide";
   - a forecaster equal to its dressed version scores exactly 1 under every dressing variant;
   - 78% coverage on an 80% interval is "practically consistent", 76% "practically too narrow"; a ratio of 0.96 with a tight interval is "clearly lower" and "practically equal";
   - bands whose width tracks the error give a widest-to-narrowest ratio above 1; constant bands give about 1; bands and errors that share only the season give about 1 within months;
   - every label, including "undefined", and the headline come out right.
6. **Hashes.** Every file read matches its recorded SHA-256.

## 9. Predictions, written before any quantile is compared with outturn

- **A.** In stage 1, Chronos-2's score is practically equal to its dressed median's, and clearly and practically higher than dressed NESO's, because NESO's median errs about 30% less. Any gain over the dressed median lies in the centre, not the tails. The result is robust to the dressing. At every named cost ratio, dressed NESO is clearly and practically better.
- **B.** Chronos-2's 80% and 98% intervals are too narrow and practically too narrow, in stage 1 and on winter days, because it treats the weather forecast as known and does not foresee calendar days. The closest published evidence points the other way (Kaas et al. 2026; Michael et al. 2026), but neither study gave it a day-ahead weather forecast. Coverage is furthest from nominal in the evening block. The dressed 80% bands are consistent with their level on all days and too narrow on T1.
- **C.** Within months, Chronos-2's widest quarter of days has a higher median error than its narrowest (ratio above 1), but width and error correlate weakly (median monthly correlation below 0.3). The ratio is smaller within months than over the whole year.
- **D.** Coverage is worst on calendar days.
- **Stage 2.** The same directions, none clearly different, because the window is short. Its smallest detectable difference cannot be computed before any quantile is scored. So stage 1's `score.py` estimates it: it resamples 130-day windows from stage 1's days in stage 2's season (§7 D) with the same bootstrap, and reports the smallest true difference in each primary ratio that would be labelled clearly different in at least half of them. The figure is reported before stage 2 is scored and quoted in its note.

## 10. Headlines, fixed now

Written by the script, by rule (§7).

Stage 1: "In a backtest the foundation model may have seen in training, a day-ahead position on GB demand set from Chronos-2's quantile forecasts, averaged with equal weight over quantile levels 0.10 to 0.90 (cost ratios from 1:9 to 9:1), cost [**clearly less than** / **clearly more than** / **not clearly different from**] one set from its own median with a band built from its recent errors (score [X] against [Y] MW, ratio [R], 90% interval [l] to [u]; [**practically lower** / **practically higher** / **practically equal**]), and [**clearly less than** / **clearly more than** / **not clearly different from**] one set from NESO's forecast with a band built the same way (ratio [S], 90% interval [m] to [v]; [**practically lower** / **practically higher** / **practically equal**]). Chronos-2's 80% intervals contained outturn [c]% of the time ([**too narrow** / **too wide** / **consistent with their level**]; [**practically consistent** / **practically too narrow** / **practically too wide**])."

Stage 2: the same, opening "On [n] days no model could have seen," in place of "In a backtest the foundation model may have seen in training,". When stage 2 is reported, its sentences lead and stage 1's follow as the pilot, computed on stage 2's season (§7 D), so that the time of year cannot explain a difference between them. The all-year stage 1 figures follow.

## 11. Work

1. **`quantiles/LITERATURE.md`** (before the tag): eleven sources, each opened before it is cited.
2. **`gb-weather-private/weather/calendar_quantiles_backtest.py`:** reruns `chronos2_A` on the 960 backtest days with the 21-level grid, using `calendar_study.py`'s and `calendar_quantiles.py`'s functions unchanged; writes every day with its check 1 category and largest difference, to `quantiles/backtest_quantiles.csv` with a manifest of hashes. Committed before it runs; outputs after.
3. **`quantiles/score.py`:** loads through the imbalance study's loader, imported unchanged; builds the dressed bands; runs §8; computes §7; writes the headline by rule. Committed before it runs, with its synthetic check; outputs after.
4. **`quantiles/RESULTS_stage1.md`:** a pilot note, led by its headline.
5. **After 31 March 2027:** stage 2 with the same scripts; any change recorded in `quantiles/REVISIONS.md` before it runs.

## 12. Timing

Stage 1: two or three days after the tag, mostly the backtest run. Stage 2: April 2027, with the imbalance and disagreement studies' stage 2.

## Sources

- `checkpoint0/RESULTS.md`: mean daily errors of every forecaster, and why Timestral is unranked.
- `asymmetric/RESULTS.md`: under cost ratio *k*, the best point forecast is the *k*/(1 + *k*) quantile.
- `weather_study/PLAN.md` §2–4: ECMWF forecasts as future inputs; issue timing.
- `imbalance_cost/REVISIONS.md` 19, `imbalance_cost/worst_days_results.md` and `imbalance_cost/calendar_live/check.json`.
- `ASSUMPTIONS.md` A16: Chronos-2's disclosed pretraining data.
- `quantiles/LITERATURE.md`: how each paper below was checked.
- Adler, C., Chang, Y., Draxler, F., Abdi, S. and Smyth, P. (2026). Beyond accuracy: are time series foundation models well-calibrated? Proceedings of ICLR 2026. [arXiv:2510.16060](https://arxiv.org/abs/2510.16060).
- Ansari, A. F., Shchur, O., Küken, J. et al. (2026). Chronos-2: a foundation model for multivariate time series forecasting. [arXiv:2610.41956](https://arxiv.org/abs/2610.41956).
- Chernozhukov, V., Fernández-Val, I. and Galichon, A. (2010). Quantile and probability curves without crossing. *Econometrica* 78(3), 1093–1125. [arXiv:0704.3649](https://arxiv.org/abs/0704.3649).
- Decker, T. and Tresp, V. (2026). Evaluating uncertainty calibration in probabilistic time series foundation models. NeurIPS 2026. [arXiv:2611.03592](https://arxiv.org/abs/2611.03592).
- Gneiting, T., Balabdaoui, F. and Raftery, A. E. (2007). Probabilistic forecasts, calibration and sharpness. *Journal of the Royal Statistical Society B* 69(2), 243–268. [Open copy](https://sites.stat.washington.edu/people/raftery/Research/PDF/Gneiting2007jrssb.pdf).
- Gneiting, T. and Raftery, A. E. (2007). Strictly proper scoring rules, prediction, and estimation. *Journal of the American Statistical Association* 102(477), 359–378. [Technical report version](https://apps.dtic.mil/sti/pdfs/ADA454828.pdf).
- Kaas, B., Treutlein, M., Gerber, H. B., Neumann, O., Phatthanakhuha, C., Resch, O., Mikut, R. and Hagenmeyer, V. (2026). Probabilistic low-voltage peak load forecasting with time series foundation models evaluated on application-oriented metrics. [arXiv:2607.01966](https://arxiv.org/abs/2607.01966).
- Laio, F. and Tamea, S. (2007). Verification tools for probabilistic forecasts of continuous hydrological variables. *Hydrology and Earth System Sciences* 11(4), 1267–1277. [doi:10.5194/hess-11-1267-2007](https://doi.org/10.5194/hess-11-1267-2007).
- Michael, P., Symeonides, M. and Trihinas, D. (2026). Evaluating accuracy and probabilistic reliability of zero-shot time series foundation models. [arXiv:2609.25788](https://arxiv.org/abs/2609.25788).
- Roulston, M. S. and Smith, L. A. (2003). Combining dynamical and statistical ensembles. *Tellus* 55A, 16–30. [doi:10.1034/j.1600-0870.2003.201378.x](https://doi.org/10.1034/j.1600-0870.2003.201378.x).
- Ziel, F. and Liu, B. (2016). Lasso estimation for GEFCom2014 probabilistic electric load forecasting. [arXiv:1603.01376](https://arxiv.org/abs/1603.01376).
