# Tails: who fails on the hardest days?

Andy Moran (Heaviside Analytics) · 17 November 2026 · **Status: draft, to be frozen at tag `tails-plan` before any script runs**

For: a reader who wants to know whether average error hides how forecasters behave on the days that matter most.

**The question:** on the backtest's coldest days, does each forecaster hold the position against the weather regression that it holds on other days?

## 1. What this is, and is not

This is a new, descriptive study on the backtest's saved forecasts. It makes no new forecasts. It is not part of the weather study, whose last analysis was E5, and not part of the live benchmark. Checkpoint 0's note proposed it as the second test for checkpoint 1 (`checkpoint0/RESULTS.md`, "What checkpoint 1 should test first"), and this study runs it on the backtest first.

The reason to look: the cost of a demand forecast's error concentrates on the most extreme days, when prices spike and margins are tight. Average error can hide that. A model may be close on ordinary days and fail on cold ones.

## 2. Non-claims

This study does not establish:
- live performance: the foundation models may have seen these days in training;
- who is best in the tails: about 96 tail days, clustered in two winters, cannot settle a ranking;
- anything about prices or profit: it scores demand forecasts, which are one input to price;
- anything for other series, horizons or countries: one series (GB national demand, INDO), day ahead.

The note states these before any result.

## 3. What has been seen before this plan

Every forecaster's error over all 960 days, by season and by block, is published: `weather_study/RESULTS.md` and `results/`, and `checkpoint0/results.md`. In particular, winter results are known. In December to February, LightGBM with defaults had 1.286 times the regression's error (90% interval 1.192–1.398; `checkpoint0/results.md`, table 4), and the extrapolation hypothesis came from that.

No forecaster's error has been computed on days selected by temperature, by peak demand, or by position outside a model's training range. No peak half-hour error or signed error (bias) has been computed for any forecaster.

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

Each set is a list of target days, written to `tails/days.csv` with the reason each day is in it, before any error is computed.

| Set | Definition | Known in advance? | Role |
|---|---|---|---|
| **T1** | The coldest 10% of backtest days by mean forecast temperature over D's half-hours | Yes | **Primary** |
| T2 | The top 10% of backtest days by peak half-hourly outturn | No | Secondary |
| T3 | Bank holidays (England and Wales) and 24 December to 2 January | Yes | Secondary |
| T4a | Days whose peak outturn exceeds the highest half-hourly demand in LightGBM's training window for that day (D−366 to D−2) | No | Mechanism |
| T4b | Days with any half-hour whose forecast temperature is below the lowest in LightGBM's training window for that day | Yes | Mechanism |

**Forecast temperature** is the population-weighted national 2 m temperature that the regression received for D (`gb-weather-private`, `weather/regression_weather.py`, `weather_for`), from the weather study's frozen backtest inputs. The script records the inputs file's SHA-256 and checks it against `build.json`.

**Why T1 is primary.** A forecaster knows the next day's forecast temperature in advance and can act on it. T2 selects days by what happened, which favours whichever model happened to forecast high. T2 is shown because peak days are where the cost falls, with that caveat stated beside it.

**Ties** at a 10% boundary are broken by date, earliest first. "10%" means the floor of 0.1 times the number of scored days.

**Small sets.** If T4a or T4b has fewer than 10 days, it is reported day by day, with no averages or intervals. T3's size is stated whatever it is.

## 6. Metrics

Error is outturn minus forecast, in MW, so a positive mean means a forecaster under-forecast. For each forecaster and each set, and for the complement of each set (all other scored days):

1. **Mean daily error:** mean absolute error over each day's half-hours, averaged over the set's days.
2. **Ratio to the regression:** each forecaster's mean daily error over the regression's, on the set and on its complement.
3. **Tail shift:** the ratio on the set divided by the ratio on its complement. Above 1, the forecaster loses ground to the regression on those days; below 1, it gains ground.
4. **Bias:** the mean signed error over the set's half-hours.
5. **Peak error:** the signed error at each day's half-hour of highest outturn, averaged over the set.
6. **Worst day:** the forecaster's largest daily mean absolute error in the set, with its date.
7. **95th percentile** of absolute half-hourly errors in the set.

Intervals: moving-block bootstrap of the 960 days in calendar order (blocks of 7, 2,000 draws, seed 20261117). Each draw recomputes every metric on the resampled days that fall in the set. 90% intervals are reported for metrics 1–5. Metrics 6 and 7 are given without intervals.

**Reading rule:** as in checkpoint 0. No p-values, and nothing is called significant. A forecaster is said to lose or gain ground only where the 90% interval of its tail shift excludes 1. Otherwise it held its position.

## 7. Prediction, written before any tail error is computed

- **H1 (LightGBM):** on T1, LightGBM S1's tail shift is above 1, and its bias and peak error are positive (it under-forecasts). On T4a and T4b it under-forecasts more than on T1. Reason: a tree predicts only values it has seen, so it cannot follow demand beyond its training range (`checkpoint0/RESULTS.md`, "Extrapolation").
- **No prediction** is made for Chronos-2 or TimesFM 2.5. They take temperature as a covariate, but how they use it is not documented in a way that implies a direction.

The note reports H1 as supported, not supported, or unclear, by the reading rule.

## 8. Headlines, fixed now

The note and any post lead with two sentences of equal weight: Chronos-2 against the regression on T1, then LightGBM S1 against the regression on T1. Each takes the form that matches its tail-shift interval. "X" is the forecaster and "Z%" the tail shift minus 1, as a percentage.

| Result | Sentence |
|---|---|
| Interval wholly above 1 | "In a backtest the foundation models may have seen in training, X lost ground to a weather regression on the coldest tenth of days: relative to the regression, its error was Z% higher than on other days." |
| Interval wholly below 1 | "In a backtest the foundation models may have seen in training, X gained ground on a weather regression on the coldest tenth of days: relative to the regression, its error was Z% lower than on other days." |
| Interval includes 1 | "In a backtest the foundation models may have seen in training, X held its position against a weather regression on the coldest tenth of days (tail shift S, 90% interval L–U)." |

The third sentence of the note states H1's outcome. Every other result follows.

## 9. Work

1. **`tails/build_days.py`** builds `tails/days.csv`: every set's days and the reason for each. It reads outturn and forecast temperature only, never a forecast. It is committed before it runs; its output is committed after.
2. **`tails/score_tails.py`** checks the four hashes and `days.csv`'s hash, then computes §6 for every forecaster and set. It is committed before it runs. Its outputs, `tails/results.json` and `tails/results.md`, are committed after.
3. **`tails/RESULTS.md`** is the note: non-claims first, then the headline (§8), the tables, H1, and the limits. It follows `WRITING.md`.

Any change to a script after it has run on the backtest is a deviation, logged in `tails/REVISIONS.md` with its date, commit and reason.

Both scripts run on Andy's machine, where the demand history and the weather study's backtest inputs are held. Neither is in the repository (`data/` and `~/gb-weather-data/` are not committed).

## 10. Timing

| Step | Target |
|---|---|
| Plan reviewed and tagged `tails-plan` | 21 November 2026 |
| `build_days.py` and `score_tails.py` committed, run, outputs committed | 28 November 2026 |
| Note published | 5 December 2026 |

The study comes before gates G2 and G3 (`PROJECT.md` §4). If H1 holds, it bears on G2: it would support keeping the regression as the main trained bar.
