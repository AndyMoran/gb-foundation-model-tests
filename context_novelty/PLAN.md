# Context novelty: do the foundation models fail when tomorrow is colder than their context?

Andy Moran (Heaviside Analytics) · 20 November 2026 · **Status: version 2. Andy freezes it at tag `context-novelty-plan-v2` before any script runs on the backtest.** Version 1 is at tag `context-novelty-plan` (9e1002b). Two reviews changed it before any script ran on real data; the changes are listed at the end.

For: a forecaster who wants to know whether a foundation model's bad days can be seen coming the day before.

**The question.** Is Chronos-2 worse on cold days that are colder than anything in the eight weeks of history it was given? The comparison is with cold days, equally cold and in the same part of winter, that are not.

This is a case study on real data. It does not offer a general theory of covariate novelty.

## 1. Why

**The tails study points here.** On the coldest tenth of days, Chronos-2 under-forecast the daily peak by 511 MW (90% interval 195 to 837 MW), and its error relative to the regression did not clearly shift (`tails/RESULTS.md`). The same study found that LightGBM never had to forecast a temperature outside its training range.

**A foundation model learns from its context, not from a training year.** It infers how demand responds to weather from the history it receives with each forecast: here 2,688 half-hours, or eight weeks (`weather_study/PLAN.md`). An early cold spell can be colder than anything in those eight weeks yet well within a year's range. So extrapolation, ruled out for LightGBM, may still matter for the foundation models, measured against their context.

**Prior work studies the same setting on simulated data.**
- **WhatIf-Bench** (Ashok et al., arXiv 2610.26582) "measures how well a forecaster can learn covariate–target relationships in-context and extrapolate them to the future". Its tasks come from simulators of data centres, power grids, road traffic and water networks. Every model forecast well when future covariates repeated values seen in the history, and lost much of its skill when they did not. Its simple regression baselines lost the most. Those baselines are not TimesFM 2.5's in-context regression, so the result says nothing directly about TimesFM here.
- **CovNovBench** names the setting "covariate novelty": future covariates that "fall outside the range seen in the history". It has 88,476 series, generated or filtered from four simulated and real datasets. Only its abstract was found, with no preprint; nothing beyond the abstract is cited.
- **On German day-ahead prices**, a blog series reports that Chronos-2 and TimesFM-3 "missed the price spikes on days when the demand left for conventional power plants rose above anything in their 30-day history" (AI Horizon Forecast, Part 0's recap of Part 2).

**What is new here is narrow:** real GB demand; three foundation models given the same weather and context; the regression as reference; and novel days compared with cold days matched on temperature and month.

## 2. What this study does not show

- **Live performance.** The foundation models may have seen the backtest in training.
- **Cause.** It compares matched days; it changes nothing, so it cannot prove novelty causes a failure.
- **Why models differ.** Comparisons between models are exploratory (§7).
- **Covariates other than temperature,** except as description (§5).
- **Other targets or settings:** prices, other series, or contexts of other lengths.

## 3. What was known before this plan

**Every forecaster's errors on the 960 backtest days had been seen,** by season, by block and on the tails study's sets T1 to T4. That includes Chronos-2's peak error on T1. No error had been computed on days chosen by novelty, and no real day had been tested for novelty.

**So the plan is not blind to the tails study.** The hypothesis (§7), the 250 MW threshold (§6) and the matching rule (§5) were set after seeing Chronos-2's T1 peak error and the German price result. They were set before any error on novel days was computed.

## 4. Forecasters and inputs

**The forecasts are the tails study's,** with the same hashes and the same outturn (`tails/PLAN.md` §4).
- **Primary:** Chronos-2 (`chronos2_A`).
- **Exploratory:** TimesFM 2.5, one day per call (`timesfm25_weather_single_day`).
- **Descriptive only:** Timestral (`timestral_A`; covariate defect `mistralai/timestral#9`) and LightGBM S1.
- **Reference for every comparison:** the weather regression.

**All three foundation models received the same covariates:** adjusted national temperature, wind and solar, for the 2,688 context half-hours and the horizon (`weather_study/PLAN.md`, decision 13).

**Every temperature was available before the forecast was issued.** The weather study's frozen plan (`weather-plan`) sets the sources:
- **The target day, D:** ECMWF's 00:00 UTC open-data run of D−1. It counts only if ECMWF published it before 09:30 UK time on D−1, the issue time. Otherwise D−2's run is used, and the day is flagged as a fallback.
- **The context from D−10 to D−1:** each UTC day from the first 24 hours of its own ECMWF run.
- **The context before D−10:** ERA5, up to UTC day D−11.
- **The adjustment (decision 13):** the context's ERA5 days are shifted onto ECMWF's scale. The shift is estimated from D−70 to D−11, so nothing from D−10 onwards enters it. The weather study's look-ahead check enforces this.

**The adjustment makes context and target comparable.** In the cool months ERA5 runs about 0.2 °C warmer than ECMWF (`weather_study/PLAN.md`, Q3). Unadjusted, that gap alone could make a day look novel.

## 5. Day sets and matched pairs, fixed now

**Every set is chosen from the covariates the models received the day before, never from outturn.** Choosing by outcome can make a good forecaster look poor: the forecaster's dilemma (`tails/PLAN.md` §5).

| Set | Definition | Role |
|---|---|---|
| **N** | Days whose coldest target half-hour is colder than the coldest context half-hour | Counts and description |
| **N∩T1** | Days in both N and the tails study's T1, the coldest tenth by mean forecast temperature | **Novel days** |
| **T1∖N** | Days in T1 but not in N | **Pool of controls** |
| **Nw** | Days whose target wind exceeds the context's highest, or whose target solar falls below the context's lowest | Description |

**Definitions.**
- **The covariates** are the `t2m_c` column of the weather study's frozen backtest inputs: the adjusted temperature, as fed to the models. Rows marked `context` are the context; rows marked `horizon` are the horizon. The script checks the file's SHA-256 against `build.json`.
- **A target half-hour** is one of D's own settlement periods: the last rows of the horizon.
- **"Colder"** is strict. A target equal to the context's coldest is not novel.
- **The margin** of an N day is the context's minimum minus the target's minimum, in °C. `days.csv` records it.

**Each novel day is paired with one control, using covariates only,** before any error on these days is computed.
1. **Coldness** is measured as T1 measures it: mean forecast temperature over D's half-hours (`t_mean` in the tails study's `day_inputs.csv`, checked against `tails/days.json`).
2. **An eligible control** is a T1∖N day whose `t_mean` is within 1.0 °C of the novel day's, and whose calendar month is within one month. December and January are one month apart.
3. **Novel days are matched in date order,** earliest first. Each takes the eligible control nearest in temperature. A tie goes to the nearer month, then to the earlier date.
4. **No control is used twice.** A novel day left with no eligible control is unmatched, and listed.

**`pairs.csv` lists every pair.** `days.json` reports how many novel days were eligible, how many pairs were made and which days went unmatched. It also reports the balance: the mean and largest differences in `t_mean`, in the daily minimum (`t_min`) and in month.

**Pairs are grouped by cold spell.** Novel days fewer than three days apart belong to the same cold spell, and each pair takes its novel day's spell. Intervals resample whole spells (§6), so days from one spell are not treated as independent.

**Counts are reported in full:** each set's size, by winter and by month, and N's overlap with T1 and T4. **With fewer than 10 pairs, H5 is not assessed,** and the pairs are reported one by one, with no average or interval.

## 6. What is measured

**The primary outcome is Chronos-2's excess peak error.**
- **A day's peak error** is its highest outturn half-hour minus the forecaster's highest forecast half-hour, wherever each falls (`tails/PLAN.md` §6). Positive means the forecast peak was too low.
- **Excess peak error** is Chronos-2's peak error minus the regression's, in MW. Subtracting the regression's error allows for days that are hard for everyone. The regression trains on a year of days, not an eight-week context, so novelty as defined here should not affect it.

**The primary comparison is Δ:** the mean, over all pairs, of the novel day's excess peak error minus its control's, in MW.

**Its interval** is a 90% percentile interval from 2,000 cluster-bootstrap draws, seed 20261120. Each draw resamples cold spells with replacement and keeps every pair in each spell drawn.

**The practical threshold is 250 MW, chosen for this study.** It is not a NESO standard. It is about half the 511 MW peak miss that prompted the study, and was set knowing that result. Readings at 100 MW and 500 MW are reported beside it.

**Secondary results are reported in full:**
- **Δ for the other forecasters:** TimesFM 2.5 (exploratory), Timestral and LightGBM S1 (descriptive);
- **the unmatched comparison:** every novel day against every T1∖N day (descriptive);
- **the tails study's metrics on N,** against its broad and narrow complements: mean daily error and its ratio to the regression, bias, peak error, the worst day and the 95th percentile of absolute errors. Their intervals use the tails study's 7-day moving-block bootstrap: 2,000 draws, seed 20261120, with dropped draws counted.

**Every ratio divides by the regression's mean daily error over the same set.** A day's error is the mean absolute error across its half-hours; the set's figure is the mean over its days. On the backtest it is about 1,000 MW. A set where it falls below 100 MW gets no ratios.

## 7. Hypotheses, written before any novelty or error on these sets is computed

**H5 (Chronos-2, primary):** Chronos-2's excess peak error is larger on novel days than on their controls, so Δ > 0. The interval of Δ decides the reading:

| Interval of Δ | Reading |
|---|---|
| Lower bound above 250 MW | **Meaningful penalty supported** |
| Lower bound above 0 MW, but not above 250 MW | **Positive penalty supported; meaningful size not shown** |
| Contains 0 | **Unclear** |
| Upper bound below 0 MW | **Smaller on novel days** |

**An estimate above 250 MW is not enough on its own;** the lower bound must clear the threshold. With fewer than 10 pairs, H5 is "not assessed", and the note says so.

**TimesFM 2.5 is exploratory.** Its Δ is reported with an interval but no reading. The reason to look: TimesFM 2.5 handles covariates by fitting a linear regression in context (`timesfm`'s `xreg` mode), which extends a straight line beyond the context's range. Chronos-2 reads covariates through learned attention instead. A difference between the two would not show that this mechanism caused it.

**LightGBM S1 is descriptive.** It learns from a year of training days, not a context, so novelty should not matter to it. Its Δ is shown, and nothing about coldness or novelty is inferred from it.

## 8. Headline, fixed now

**The note and any post lead with one sentence,** which the script picks by rule:

| H5 reading | Sentence |
|---|---|
| Meaningful penalty supported | "In a backtest it may have seen in training, Chronos-2 under-forecast the daily peak, relative to a weather regression, by D MW more on cold days colder than its eight-week context than on matched cold days that were not (90% interval L–U, above the 250 MW threshold set in advance)." |
| Positive penalty; meaningful size not shown | "In a backtest it may have seen in training, Chronos-2 under-forecast the daily peak, relative to a weather regression, by D MW more on cold days colder than its eight-week context than on matched cold days that were not (90% interval L–U). A penalty of 250 MW, the threshold set in advance, was not shown." |
| Unclear | "In a backtest it may have seen in training, Chronos-2's peak error relative to a weather regression did not clearly differ between cold days colder than its eight-week context and matched cold days that were not (difference D MW, 90% interval L–U)." |
| Smaller on novel days | "In a backtest it may have seen in training, Chronos-2 under-forecast the daily peak, relative to a weather regression, by D MW less on cold days colder than its eight-week context than on matched cold days that were not (90% interval L–U)." |
| Not assessed | "Too few cold days colder than Chronos-2's eight-week context could be matched for a comparison (n pairs from m novel days)." |

**The next sentence gives the number of pairs,** how many fall in each winter, and the number of cold spells. TimesFM 2.5 and the descriptive forecasters follow.

## 9. Work

1. **`context_novelty/build_days.py` builds the sets and the pairs.** It writes `days.csv`, `day_inputs.csv`, `pairs.csv` and `days.json`. It reads the covariates and the tails study's committed `days.csv` and `day_inputs.csv`, and no outturn or forecast. It checks every file's hash and records the commits. It refuses to run with uncommitted changes, or if this plan differs from tag `context-novelty-plan-v2`. Its `--synthetic` mode checks the set rules, the matching and the cold spells on invented covariates. It is committed before it runs; its outputs are committed after.
2. **`context_novelty/score.py` computes §6** and picks the H5 reading and the headline by rule. It imports the tails study's scoring functions where they apply, unchanged. It checks every hash. Before the real run, its `--synthetic` mode must recover a known Δ and pick the right reading and sentence, for every threshold case. It is committed before it runs; its outputs are committed after.
3. **`context_novelty/RESULTS.md` reports the result.** It opens with what the study does not show, then the headline, copied unchanged. The pairs and their balance, the tables, H5, the exploratory and descriptive results and the limits follow. It follows `WRITING.md`.

**Any change after a script runs on the backtest is a deviation,** logged in `context_novelty/REVISIONS.md`. Both scripts run on Andy's machine, which holds the inputs.

## 10. Timing

| Step | Target |
|---|---|
| Version 2 tagged `context-novelty-plan-v2` | 21 November 2026 |
| Sets and pairs built and committed; synthetic checks passed | 28 November 2026 |
| Scored; note published | 4 December 2026 |

## Changes from version 1

Two reviews on 20 November led to these changes, before any script ran on real data. `build_days.py` had been committed (deec625) but not run on the backtest.

1. **Weather provenance is stated** (§4): where each temperature came from, when it was available, and why context and target are comparable.
2. **Matching replaces "equally cold"** (§5). Version 1 compared every novel day with every other T1 day, which could mistake coldness or season for novelty. Version 2 pairs each novel day with a control matched on T1's temperature measure and month, by a fixed rule, and reports the balance.
3. **There is one primary outcome** (§6): Δ, the matched difference in Chronos-2's peak error relative to the regression. It is read against a 250 MW threshold in three ways (§7). Version 1 read H5 from the interval alone.
4. **Intervals resample cold spells** (§6), so pairs from one spell are not treated as independent. A reviewer suggested re-matching within block-bootstrap draws of the 960 days. The matching uses covariates only and is fixed before errors are seen, and re-matching on a resample with repeated days is not well defined. So whole cold spells are resampled instead.
5. **TimesFM 2.5 and LightGBM are no longer tested** (§7). TimesFM 2.5's hypothesis, H6, is now an exploratory comparison with no reading. LightGBM's control no longer supports any conclusion about coldness against novelty.
6. **The references are fixed** (§1). WhatIf-Bench's arXiv record and result are added, with its limit for TimesFM. CovNovBench is marked abstract only.

## Sources

- Ashok, A., Parmar, M., Goyal, P., Dalvi Mishra, B., Li, C.-L., Rish, I., Drouin, A., Yoon, J. and Pfister, T. (2026). [WhatIf-Bench: benchmarking intervention-aware time series forecasting](https://arxiv.org/abs/2610.26582). arXiv 2610.26582; [NeurIPS 2026](https://neurips.cc/virtual/2026/175046).
- [CovNovBench: a benchmark for evaluating time series foundation models under covariate novelty](https://neurips.cc/virtual/2026/175022). NeurIPS 2026. Abstract only; no preprint located.
- AI Horizon Forecast, "Timestral and t0-gamma: do the leaderboard leaders win on real prices?" (Substack, 2026). Its recap states Part 2's finding. It was read from text Andy supplied, because the site could not be fetched; Part 2's figures are not cited.
- `tails/PLAN.md`, `tails/RESULTS.md` and `weather_study/PLAN.md`, for every earlier rule and figure.
