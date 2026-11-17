# Tails: who fails on the hardest days?

Andy Moran (Heaviside Analytics) · 17 November 2026 · **Status: draft, to be frozen at tag `tails-plan` before any script runs**

For: a reader who wants to know whether average error hides how forecasters behave on the days that matter most.

**The question:** on the backtest's coldest days, does each forecaster hold the position against the weather regression that it holds on other days of the same months?

## 1. What this is, and is not

This is a new, descriptive study on the backtest's saved forecasts: 960 days, 16 March 2024 to 31 October 2026. It makes no new forecasts. It is not part of the weather study, whose last analysis was E5, and not part of the live benchmark. Checkpoint 0's note proposed it as the second test for checkpoint 1 (`checkpoint0/RESULTS.md`, "What checkpoint 1 should test first"), and this study runs it on the backtest first.

The reason to look: the cost of a demand forecast's error concentrates on the most extreme days, when prices spike and margins are tight. Average error can hide that. A model may be close on ordinary days and fail on cold ones.

**Related work.** A zero-shot benchmark on ERCOT demand found that all the foundation models it tested struggle with extreme events, and that Chronos-2 had the best accuracy on them (arXiv 2602.10848, §4.3.3 and Figure 9). That study defined extremes by observed load (above the 95th or below the 5th percentile), gave the models no weather, and included no gradient-boosting or regression baseline. This study differs in three ways: every forecaster gets the same weather and calendar inputs, trained baselines are compared alongside, and tail days are chosen only from information known the day before (§5).

## 2. Non-claims

This study does not establish:
- live performance: the foundation models may have seen these days in training;
- a cold-day effect separate from a winter effect, unless the narrow tail shift (§6) shows one;
- who is best in the tails: about 96 tail days, clustered in two winters, cannot settle a ranking;
- anything about prices or profit: it scores demand forecasts, which are one input to price;
- anything for other series, horizons or countries: one series (GB national demand, INDO), day ahead.

The day sets are built from public data that are not committed to the repository: NESO's publications, ERA5, and ECMWF's 00 UTC runs from its open-data copies on Google Cloud, Azure and AWS (no MARS account is needed). Their files are named and hashed (§9). Anyone can download them again and check the hashes, for as long as those copies keep their archive.

The note states these before any result.

## 3. What has been seen before this plan

Every forecaster's error over all 960 days, by season and by block, is published: `weather_study/RESULTS.md` and `results/`, and `checkpoint0/results.md`. In particular, winter results are known. In December to February, LightGBM with defaults had 1.286 times the regression's error (90% interval 1.192–1.398; `checkpoint0/results.md`, table 4), and the extrapolation hypothesis came from that.

No forecaster's error has been computed on days selected by temperature, by NESO's forecast peak, or by position outside a model's training range. No peak half-hour error or signed error (bias) has been computed for any forecaster.

So the coldest-days result is not blind. The winter tables make a direction likely for LightGBM. What is new is the size of the effect on the coldest days alone, the bias, and the mechanism test (§5, T4).

## 4. Forecasters

The saved forecasts are used unchanged, checked against these hashes:
- `weather_study/results/forecasts.csv`: b5f16561dcf1a26f8d7910bcca95cd137f677760c6f80153349034d4a85f7328
- `weather_study/results/calendar_forecasts.csv`: 976e27ef28d0eef1ddf351c6557af9f771c308b94f389fe0f06b84ec86c8e2fe
- `checkpoint0/lightgbm_forecasts.csv`: 812ffb251e7c4428ec1bb9f1e7467c51bc4f8ae55caf5b78b3fd0c840b6250cd
- `weather_study/correction1/timesfm25_single_day_forecasts.csv`: 479ec318925cc59cd1e4f56a29ef9bc10d297fe3f8fa012482e1ce130dccd821

| Forecaster | Column | Role |
|---|---|---|
| Weather regression | `regression_weather` | Reference for every ratio |
| Chronos-2 | `chronos2_A` | Compared |
| TimesFM 2.5 | `timesfm25_weather_single_day` (corrected, one day per call) | Compared |
| LightGBM, S1 settings | `lightgbm_s1` | Compared |
| LightGBM, defaults and S2 | `lightgbm_default`, `lightgbm_s2` | Sensitivity |
| Timestral | `timestral_A` | Shown, not compared: covariate defect (`mistralai/timestral#9`) |
| NESO day-ahead | as scored by `code/run.py` (`inputs.neso_forecast`) | Shown for reference: different information |

LightGBM S1 is the compared configuration because it had the lowest error of the three in checkpoint 0. That follows the comparator rule in `PROJECT.md` §4: the hardest trained opponent, chosen on error.

## 5. Tail sets, fixed now

Every set is chosen only from information known before the forecasts were issued, never from outturn. Selecting days by what happened is the "forecaster's dilemma": it can make a skilful forecast look poor and reward one that always predicts extremes (Lerch et al., 2017). Lerch et al. find conditioning on outcomes "problematic", and conditioning on forecasts "unproblematic from a decision theoretic perspective". Each set below conditions on a forecast or on the calendar.

Each set is a list of target days, written to `tails/days.csv` with the reason each day is in it, before any error is computed. The script that builds it reads no outturn and no forecast being scored.

| Set | Definition | Role |
|---|---|---|
| **T1** | The coldest 10% of backtest days by mean forecast temperature over D's half-hours | **Primary** |
| T2 | The top 10% of backtest days by NESO's day-ahead forecast of D's peak half-hourly demand | Secondary |
| T3 | Bank holidays (England and Wales) and 24 December to 2 January | Secondary |
| T4 | Days with any half-hour whose forecast temperature is below the lowest in LightGBM's training window for that day (D−366 to D−2) | Mechanism |

**Forecast temperature** is the population-weighted national 2 m temperature that the regression received for D (`gb-weather-private`, `weather/regression_weather.py`, `weather_for`), from the weather study's frozen backtest inputs. The script records the inputs file's SHA-256 and checks it against `build.json`. T4 compares it with the temperatures in LightGBM's training rows for D, exactly as `lightgbm_weather.py` builds them. Those rows hold ERA5 reanalysis, not past forecasts (`weather_for` fills every training day from ERA5). The comparison is still the right one for the mechanism: a tree's splits are set by the values in its training rows, whatever their source, and it cannot place a predict-time value below the lowest of them anywhere but its lowest leaf. Checkpoint 0 re-fitted LightGBM for each target day on the complete days D−366 to D−2 (`checkpoint0/PLAN.md` §5), so each day has its own window.

**NESO's forecast** is the day-ahead publication the weather study used for D (`code/inputs.py`, `neso_forecast`). NESO is not one of the forecasters compared, so selecting by its forecast favours none of them. NESO had more information than the compared forecasters, which is a reason T2 is secondary. Days with no NESO forecast are left out of T2's ranking, and the count is stated. NESO's own T2 figures are selected by its own forecast and are read as descriptive only.

**Why T1 is primary.** Forecast temperature is known the day before, it drives winter demand, and it is the input a tree cannot extrapolate. Its limit: a day's mean can be mild while one half-hour is very cold. T4 catches some of those days, not all, and a sensitivity set, **T1b**, takes the coldest 10% of days by their coldest forecast half-hour. T1b is descriptive only.

**Ties** at a 10% boundary are broken by date, earliest first. "10%" means the floor of 0.1 times the number of days ranked.

**Overlap.** The sets are independent: a day may be in several, and each set's metrics include every day that qualifies for it. A cold Christmas day, for example, is in T1 and in T3.

**Counts.** `days.csv` states each set's size, how many of its days fall in each winter, and the overlap of every pair of sets (in particular T4 with T1, and T1 with T3). If T1's days come mostly from one winter, the note says the result is largely that winter's.

**Small sets.** If T4 has fewer than 10 days, it is reported day by day, with no averages or intervals. T3's size is stated whatever it is.

**T3 is a calendar set, not a weather set.** Its results are reported separately and kept out of the cold-day reading.

**Not used.** Days selected by outturn: the highest-demand days, or days whose demand exceeded a model's training range. Both were in an earlier draft. They were dropped for the reason above.

## 6. Metrics

Error is outturn minus forecast, in MW, so a positive mean means a forecaster under-forecast. Outturn is the `outturn` column of `weather_study/results/forecasts.csv`, the first hashed file in §4.

Each set has two complements:
- **broad:** every other scored day;
- **narrow:** every other scored day in a calendar month (of a given year) that contains at least one of the set's days. For T1 that is the other days of the same winter months.

The broad complement answers "cold days against all others", but cold days are winter days, so it mixes a cold-day effect with a winter effect. Checkpoint 0 already showed LightGBM worse in winter (§3). The narrow complement compares cold days with other days of the same months, which isolates the cold-day effect.

For each forecaster and each set, and for each complement:

1. **Mean daily error:** mean absolute error over each day's half-hours, averaged over the set's days.
2. **Ratio to the regression:** each forecaster's mean daily error over the regression's, on the set and on its complement.
3. **Tail shift:** the ratio on the set divided by the ratio on its complement, broad and narrow. Above 1, the forecaster loses ground to the regression on those days; below 1, it gains ground.
4. **Bias:** the mean signed error over the set's half-hours.
5. **Peak error:** each day's highest outturn half-hour minus the forecaster's highest forecast half-hour, averaged over the set. It compares the two daily peaks, wherever each falls. Taking the error at the half-hour of highest outturn instead would select by outcome within the day (§5).
6. **Worst day:** the forecaster's largest daily mean absolute error in the set, with its date. If several forecasters' worst days share a date or a cold spell, the note says so.
7. **95th percentile** of absolute half-hourly errors in the set.

Intervals: moving-block bootstrap of the 960 days in calendar order (blocks of 7, 2,000 draws, seed 20261117). Seven-day blocks keep each week's cycle and short runs of similar weather together, as in the weather study and checkpoint 0; other block lengths are not tried. Each draw recomputes every metric on the resampled days that fall in the set and its complements. A draw with no days in a set or complement is dropped for that metric, and the number dropped is reported. 90% intervals are reported for metrics 1–5. Metrics 6 and 7 are given without intervals.

**Reading rule:** as in checkpoint 0. No p-values, and nothing is called significant. A forecaster is said to lose or gain ground only where the 90% interval of its tail shift excludes 1. Otherwise it did not clearly lose or gain ground, which is not evidence that it performed the same. Likewise, a forecaster is said to under- or over-forecast only where the 90% interval of its bias or peak error excludes 0.

**What the study can detect.** A rough guide from published figures only: checkpoint 0's winter ratio for LightGBM had a 90% interval of about ±8% on 180 days. A tail shift divides two ratios, on about 96 days and their complement, so its interval will be roughly twice as wide. Tail shifts smaller than about 15–20% will probably not be distinguishable from none. The intervals in the results give the actual figure.

**Many comparisons.** Up to 56 tail shifts are reported (seven forecasters against the regression × four sets × two complements). At the 90% level, roughly one in ten would exclude 1 by chance alone. Only the two headline comparisons and H1 are fixed in advance; every other result is descriptive.

## 7. Hypothesis, written before any tail error is computed

H1's direction is already implied by the known winter result (§3). What is new is its size on the coldest days against other days of the same months, the sign of the bias, and the mechanism test on T4.

- **H1 (LightGBM):** on T1, LightGBM S1's narrow tail shift is above 1, and its bias and peak error are positive (it under-forecasts). On T4 its bias is larger than on T1. Reason: a tree predicts only values it has seen, so it cannot follow demand beyond its training range (`checkpoint0/RESULTS.md`, "Extrapolation").
- **No prediction** is made for Chronos-2 or TimesFM 2.5. The ERCOT benchmark found Chronos-2 best on extreme load (§1), but without weather, against no trained baseline, and on days chosen by outcome. Its result does not carry over to this design in a known direction.

The note reports H1 as supported, not supported, or unclear, by the reading rule:
- **supported** only if, on T1, the narrow and broad tail shifts both have intervals wholly above 1, and the bias and peak error both have intervals wholly above 0;
- **a winter effect, not a cold-day effect** (H1 unclear) if only the broad shift's interval excludes 1;
- **a cold-day effect not seen against all other days** (H1 unclear) if only the narrow shift's interval excludes 1;
- **not supported** if neither interval excludes 1 above, or either lies wholly below 1;
- **unclear** in any other case.

**The T4 clause** is assessed only if T4 has at least 10 days. Then it holds if LightGBM's bias on T4 exceeds its bias on T1 and the interval of the difference lies wholly above 0. If T4 is smaller, H1 is assessed on the T1 conditions alone, and the note says the T4 clause was not assessed and why.

## 8. Headlines, fixed now

The note and any post lead with two sentences of equal weight: Chronos-2 against the regression on T1, then LightGBM S1 against the regression on T1. Both read the **narrow** tail shift, so neither reports a winter effect as a cold-day one. "Z%" is the tail shift minus 1, as a percentage.

**Chronos-2** (a foundation model, so the backtest caveat applies):

| Result | Sentence |
|---|---|
| Interval wholly above 1 | "In a backtest Chronos-2 may have seen in training, it lost ground to a weather regression on the coldest tenth of days: relative to the regression, its error was Z% higher than on other days of the same months." |
| Interval wholly below 1 | "In a backtest Chronos-2 may have seen in training, it gained ground on a weather regression on the coldest tenth of days: relative to the regression, its error was Z% lower than on other days of the same months." |
| Interval includes 1 | "In a backtest Chronos-2 may have seen in training, it did not clearly lose or gain ground against a weather regression on the coldest tenth of days, compared with other days of the same months (tail shift S, 90% interval L–U)." |

**LightGBM S1** (trained only on days before each forecast, so no leakage caveat):

| Result | Sentence |
|---|---|
| Interval wholly above 1 | "On the coldest tenth of days in a 960-day backtest, LightGBM lost ground to a weather regression: relative to the regression, its error was Z% higher than on other days of the same months." |
| Interval wholly below 1 | "On the coldest tenth of days in a 960-day backtest, LightGBM gained ground on a weather regression: relative to the regression, its error was Z% lower than on other days of the same months." |
| Interval includes 1 | "On the coldest tenth of days in a 960-day backtest, LightGBM did not clearly lose or gain ground against a weather regression, compared with other days of the same months (tail shift S, 90% interval L–U)." |

The third sentence of the note states H1's outcome. TimesFM 2.5 has a row in every main table beside Chronos-2 and LightGBM, and one sentence in the body; it is not in the headline. Every other result follows.

## 9. Work

1. **`tails/build_days.py`** builds `tails/days.csv`: every set's days, the reason for each, and the counts in §5. It reads forecast temperature, LightGBM's training temperatures, NESO's forecast and the calendar only: no outturn and no forecast being scored. It records the SHA-256 of every file it reads (the weather study's backtest inputs, `data/neso_dayahead_publications.csv`, `data/bank_holidays_ew.json`) and the commit of `code/` it imported. It is committed before it runs; its output is committed after.
2. **`tails/score_tails.py`** checks the four hashes and `days.csv`'s hash, then computes §6 for every forecaster and set. It also picks each headline template (§8) and H1's outcome (§7) by rule, and writes the filled sentences into `results.md`. It is committed before it runs. Its outputs, `tails/results.json` and `tails/results.md`, are committed after.
3. **Before the real run, `score_tails.py --synthetic`** scores invented forecasts with a known tail shift, bias and peak error built in, on the real calendar and day sets. It must recover each to within its interval, and pick the right template for each case. The result is committed. A second reader also reviews both scripts before the real run.
4. **`tails/RESULTS.md`** is the note: non-claims first, then the headline sentences copied unchanged from `results.md`, the tables, H1, and the limits. It follows `WRITING.md`.

Any change to a script after it has run on the backtest is a deviation, logged in `tails/REVISIONS.md` with its date, commit and reason.

Both scripts run on Andy's machine, where the demand history and the weather study's backtest inputs are held. Neither is in the repository (`data/` and `~/gb-weather-data/` are not committed).

## 10. Timing

| Step | Target |
|---|---|
| Plan reviewed and tagged `tails-plan` | 21 November 2026 |
| Scripts committed; synthetic check passed; scripts reviewed | 26 November 2026 |
| Real run; outputs committed | 28 November 2026 |
| Note published | 5 December 2026 |

The study comes before gates G2 and G3 (`PROJECT.md` §4). It does not change the comparator rule, which chooses on error. If H1 holds, it informs how a checkpoint 1 result against LightGBM should be read in a cold spring.

**Revision before the freeze, 17 November 2026:** a literature check found that the draft's outturn-selected sets (top 10% by peak outturn, and days above LightGBM's demand range) fall foul of the forecaster's dilemma. They were dropped; T2 now selects by NESO's forecast. Peak error now compares the two daily peaks rather than taking the error at the observed peak half-hour. The related-work paragraph was added. No data had been read.

**Revision before the freeze, 17 November 2026, after review:** narrow (same-month) complements added, because cold days are winter days and checkpoint 0 already showed LightGBM worse in winter; headlines read the narrow shift, with separate templates for Chronos-2 and LightGBM; H1's reading spelled out, including the T4 size condition; winter and T1–T4 overlap counts; dropped bootstrap draws reported; file hashes and the code commit recorded; multiple-comparison note; "held its position" replaced. No data had been read.

**Revision before the freeze, 17 November 2026, second review:** H1's bias and peak-error conditions now need intervals clear of 0; every combination of the two tail shifts is classified; T4's size rule and its effect on H1 stated; set overlap stated; T4's training temperatures identified as ERA5, with the reason the comparison holds; T1b sensitivity; heading "Prediction" changed to "Hypothesis"; TimesFM's place in the note; a synthetic check and a script review before the real run; headline sentences filled by the script; a rough detectable-size guide. The reviewer's point that ECMWF's archive needs MARS access was checked and is wrong: the runs come from ECMWF's open-data copies (`gb-weather-private`, `weather/archive.py`). No data had been read.

## Sources

- Lerch, S., Thorarinsdottir, T. L., Ravazzolo, F. and Gneiting, T. (2017). [Forecaster's dilemma: extreme events and forecast evaluation](https://projecteuclid.org/euclid.ss/1491465630). *Statistical Science* 32(1), 106–127. doi:10.1214/16-STS588.
- [Time series foundation models for energy load forecasting on consumer hardware: a multi-dimensional zero-shot benchmark](https://arxiv.org/abs/2602.10848). arXiv 2602.10848 (February 2026).
