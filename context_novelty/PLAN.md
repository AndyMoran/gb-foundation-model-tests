# Context novelty: do the foundation models fail when tomorrow is colder than their context?

Andy Moran (Heaviside Analytics) · 20 November 2026 · **Status: draft, to be frozen at tag `context-novelty-plan` before any script runs**

For: a forecaster deciding whether a foundation model's bad days can be seen coming the day before.

**The question:** is Chronos-2 worse on days when tomorrow's forecast temperature is colder than anything in the eight weeks of history it was given, than on equally cold days when it is not?

## 1. Why

The tails study found that Chronos-2 under-forecast the daily peak on the coldest tenth of days by 511 MW (90% interval 195 to 837), while its error relative to the regression did not clearly shift (`tails/RESULTS.md`). It also found that LightGBM never forecast outside its training range: no day was colder than its training year.

A foundation model does not learn the link between weather and demand from a training year. It infers it in context, from the history it is given with each forecast: here 2,688 half-hours, eight weeks (`weather_study/PLAN.md`). An early cold spell can be colder than anything in those eight weeks while still inside a year's range. So "extrapolation", ruled out for LightGBM, may still apply to the foundation models, measured against their context.

**Prior work.** Two NeurIPS 2026 benchmarks study this. WhatIf-Bench "measures how well a forecaster can learn covariate–target relationships in-context and extrapolate them to the future", with tasks whose future either replays seen covariate values or sets them to unseen ones. CovNovBench calls the setting "covariate novelty": future covariates that "fall outside the range seen in the history". Both use simulated data, or filtered real data. On real German day-ahead prices, a blog series reports that Chronos-2 and TimesFM-3 "missed the price spikes on days when the demand left for conventional power plants rose above anything in their 30-day history" (AI Horizon Forecast, Part 0 recap of Part 2). This study tests the same idea on GB demand with weather, on days chosen in advance.

**What is new here** is narrow: real GB demand, three foundation models with the same weather and context, the regression as reference, and a comparison among equally cold days, which separates novelty from coldness.

## 2. Non-claims

This study does not establish:
- live performance: the foundation models may have seen the backtest in training;
- that novelty causes any failure: it compares days, it does not intervene;
- anything about covariates other than temperature, except descriptively (§5);
- anything for prices, other series, or contexts of other lengths.

## 3. What has been seen before this plan

Every forecaster's error on all 960 days, by season and block, and on the tails study's sets (T1 to T4), including Chronos-2's peak error on T1. No error has been computed on days selected by context novelty, and whether a day is novel has not been computed for any day.

The prediction (§7) was formed after seeing Chronos-2's T1 peak error and the German price result. It is not blind to them.

## 4. Forecasters

The saved forecasts and hashes of the tails study (`tails/PLAN.md` §4), and the same outturn. Compared: Chronos-2 (`chronos2_A`), TimesFM 2.5 one day per call (`timesfm25_weather_single_day`). Reference for every ratio: the weather regression. Shown, not compared: Timestral (`timestral_A`, covariate defect `mistralai/timestral#9`) and LightGBM S1 (its training range is a year, not the context, so it is a control: novelty should not matter to it).

All three foundation models received the same covariates: the adjusted national temperature, wind and solar for the 2,688 context half-hours and the 48 target half-hours (`weather_study/PLAN.md`, decisions 13 and the covariate table).

## 5. Day sets, fixed now

Every set is chosen from the covariates the models were given, known the day before, never from outturn (the forecaster's dilemma, `tails/PLAN.md` §5).

| Set | Definition | Role |
|---|---|---|
| **N** | Days whose coldest target half-hour temperature is below the coldest context half-hour temperature, in the covariates the foundation models received for D | **Primary** |
| N∩T1 | N's days that are also in the tails study's T1 (coldest tenth by mean forecast temperature) | **Mechanism** |
| T1∖N | T1's days that are not in N | **Mechanism** |
| Nw | As N, for wind above the context's highest or solar below its lowest | Descriptive |

**The covariates** are the `t2m_c` column (adjusted, as fed to the models) of the weather study's frozen backtest inputs, rows `part = context` and `part = horizon` for each target day. The script records the inputs file's SHA-256 and checks it against `build.json`.

**The margin** for each N day, the context minimum minus the target minimum in °C, is recorded in `days.csv`.

**Counts.** `days.csv` states each set's size, by winter and by month, and N's overlap with T1 and T4. If N∩T1 or T1∖N has fewer than 10 days, the mechanism comparison is reported day by day, with no averages or intervals.

## 6. Metrics

As the tails study (`tails/PLAN.md` §6): mean daily error and its ratio to the regression, bias, peak error (actual daily peak minus forecast daily peak), worst day, the 95th percentile of absolute errors, intervals from the 7-day moving-block bootstrap of the 960 days (2,000 draws, seed 20261120), dropped draws counted, and the same reading rule. Every set has the tails study's broad and narrow (same calendar months) complements, and the novelty shift is the ratio on N divided by the ratio on its complement.

The **mechanism comparison** is new: for each forecaster, the difference in peak error between N∩T1 and T1∖N, and the ratio of its error-to-regression ratios on those two sets, with intervals. It asks whether, among equally cold days, novelty matters.

## 7. Hypotheses, written before any novelty or error on these sets is computed

- **H5 (Chronos-2):** on N∩T1, Chronos-2's peak error is larger than on T1∖N, and the interval of the difference lies wholly above 0.
- **H6 (TimesFM 2.5):** the same difference for TimesFM 2.5 is smaller than Chronos-2's. Reason: TimesFM 2.5 handles covariates with a linear regression fitted in context (`timesfm`'s `xreg` mode), which extends a straight line beyond the context's range. Chronos-2 reads covariates through learned attention, with no fixed functional form to extend.
- **Control (LightGBM S1):** no prediction of a difference; a clear one would point to coldness, not novelty, as the cause.

Each is reported as supported, not supported, or unclear, by the reading rule. If a mechanism set has fewer than 10 days, H5 and H6 are "not assessed", and the note says so.

## 8. Headline, fixed now

The note and any post lead with one sentence, picked by the script by rule:

| Result for H5 | Sentence |
|---|---|
| Supported | "In a backtest it may have seen in training, Chronos-2 under-forecast the daily peak by D MW more on cold days colder than its eight-week context than on equally cold days that were not (90% interval L–U)." |
| Interval includes 0 | "In a backtest it may have seen in training, Chronos-2's peak error on cold days did not clearly differ between days colder than its eight-week context and equally cold days that were not (difference D MW, 90% interval L–U)." |
| Interval wholly below 0 | "In a backtest it may have seen in training, Chronos-2 under-forecast the daily peak by D MW less on cold days colder than its eight-week context than on equally cold days that were not (90% interval L–U)." |
| Not assessed | "Too few cold days were colder than Chronos-2's eight-week context to compare (N∩T1: n days)." |

The second sentence states N's size and how many of its days fall in each winter. TimesFM 2.5 and the control follow.

## 9. Work

1. **`context_novelty/build_days.py`** builds `days.csv` and `days.json` from the covariates and the tails study's committed `days.csv`. It reads no outturn and no forecast. It hashes every file it reads, refuses to run with uncommitted changes, and records the commits. A `--synthetic` mode checks the set rules on invented covariates. Committed before it runs; outputs after.
2. **`context_novelty/score.py`** reuses the tails study's scoring functions where they apply, unchanged and imported, not copied. It checks every hash, computes §6, and picks the headline and hypothesis outcomes by rule. A `--synthetic` run with a known peak-error difference built in must recover it and pick the right sentence before the real run. Committed before it runs; outputs after.
3. **`context_novelty/RESULTS.md`**: non-claims first, then the headline copied unchanged, the tables, H5, H6, the control and the limits. It follows `WRITING.md`.

Changes after a script has run on the backtest are deviations, logged in `context_novelty/REVISIONS.md`. Both scripts run on Andy's machine, where the inputs are held.

## 10. Timing

| Step | Target |
|---|---|
| Plan reviewed and tagged `context-novelty-plan` | 25 November 2026 |
| Day sets built and committed; synthetic checks passed | 28 November 2026 |
| Scored; note published | 4 December 2026 |

## Sources

- Ashok, A. et al. [WhatIf-Bench: benchmarking intervention-aware time series forecasting](https://neurips.cc/virtual/2026/175046). NeurIPS 2026.
- [CovNovBench: a benchmark for evaluating time series foundation models under covariate novelty](https://neurips.cc/virtual/2026/175022). NeurIPS 2026.
- AI Horizon Forecast, "Timestral and t0-gamma: do the leaderboard leaders win on real prices?" (Substack, 2026), whose recap states Part 2's finding; read from text supplied by Andy, as the site could not be fetched. Part 2's figures are not cited.
- `tails/PLAN.md`, `tails/RESULTS.md` and `weather_study/PLAN.md` for every earlier rule and figure.
