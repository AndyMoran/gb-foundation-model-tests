# Checkpoint 0: a backtest first look with LightGBM

Andy Moran (Heaviside Analytics) · 15 November 2026 · **Status: draft plan, not yet tagged**

**The question:** on the weather study's backtest, with equal weather and calendar inputs, how does a trained LightGBM model compare with the foundation models and with the weather regression?

This is a new, exploratory study. It is not part of the weather study, whose last analysis was E5, and it is not a confirmatory test of the benchmark (`BENCHMARK_RULES.md` rule 7). Every result is descriptive. The benchmark's confirmatory test is checkpoint 1, on live days from 1 April 2027.

It also does work the benchmark needs anyway. LightGBM's backtest forecasts feed gate G2 (`PROJECT.md` §4): the power check for the Chronos-2–LightGBM pair.

## 1. What has been seen before this plan

Every foundation-model and regression forecast and error in the backtest is published: `weather_study/RESULTS.md`, E1–E5 and `results/`. No LightGBM model has been fitted, tuned or run on these data, and no LightGBM error has been computed. The only new forecaster is LightGBM, so the only new information this study produces is how LightGBM does.

## 2. Forecasters compared

The existing forecasts are used as saved, unchanged, and checked against these hashes:
- `weather_study/results/forecasts.csv`: b5f16561dcf1a26f8d7910bcca95cd137f677760c6f80153349034d4a85f7328
- `weather_study/results/calendar_forecasts.csv`: 976e27ef28d0eef1ddf351c6557af9f771c308b94f389fe0f06b84ec86c8e2fe

| Forecaster | Column | Weather | Calendar |
|---|---|---|---|
| Chronos-2 | `chronos2_A` (E5) | Yes | Yes |
| Timestral | `timestral_A` (E5) | Yes | Yes, but see the caveat below |
| Timestral | `timestral_weather` | Yes | No |
| TimesFM 2.5 | `timesfm25_weather` | Yes | No (8-week context; see the weather study, E5) |
| Weather regression | `regression_weather` | Yes | Yes |
| **LightGBM** | new | Yes | Yes |

Timestral is shown both ways because its calendar input is affected by a covariate defect (`mistralai/timestral#9`): with the calendar it did worse in E5 (calendar gain 1.013). Both rows are reported, and neither is chosen as "Timestral's result".

## 3. LightGBM, fixed before any run

**Information:** exactly the regression's (`gb-weather-private`, `weather/regression_weather.py`):
- **Clock slot:** the local half-hour, 0–47.
- **Calendar:** day of week as a category; bank holiday (England and Wales); 24 December to 2 January.
- **Lags:** demand at D−2 (falling back to D−9 if missing) and at D−7 (falling back to D−14), same slot.
- **Weather:** temperature, wind and solar for the half-hour, unadjusted, by the regression's splice rule (`weather_for`): D's built inputs where they cover the half-hour, otherwise ERA5.

Trees need no centred or interaction terms, so the regression's Tc, Tc², Tc × wind are not built.

**Training:** one model across all slots. It is re-fitted for each target day D on every half-hour of the complete days D−366 to D−2 whose target, lags and weather are finite. That is the regression's training window and retraining frequency. The script asserts that no training day is later than D−2.

**Settings:** LightGBM's defaults (100 trees, learning rate 0.1, 31 leaves, at least 20 rows per leaf), with three exceptions:
- `objective = 'l1'`, because the score is mean absolute error;
- `seed = 20261115` with `deterministic = True`, so runs repeat exactly;
- day of week declared categorical.

There is no tuning, no early stopping and no search. The LightGBM version is pinned and recorded. Any change to this section after the first scored run is a deviation, logged with its date and reason.

**Clock-change days:** forecasts are made per local slot and mapped to the target day's settlement periods by the regression's rules (`C.target_starts`, `C.clock`).

**Cost:** the run records wall-clock time and peak memory per forecast day, and the hardware.

## 4. Checks before scoring

These run on the full backtest period (lesson 9). None of them computes an error against outturn.

1. **Coverage.** A finite forecast for every half-hour of every backtest day that the regression covers, or each missing one listed with the reason.
2. **Leakage.** The training-window assertion holds on every day. A deliberately leaked feature (the target day's own demand, given as a lag) is shown to make the assertion or the coverage check fail.
3. **Determinism.** Two runs on 20 days, spread across the period, are identical to the last digit.
4. **Feature build.** A second, independent build of the feature matrix for 10 days, written with plain loops, matches the first exactly.
5. **Corruption.** With demand shuffled across days, LightGBM's error on 20 days rises by more than half. This is the one check that touches outturn, and it uses only corrupted inputs.

The LightGBM script is committed, with its hash recorded here, after these checks pass and before the scored run: [hash].

## 5. Scoring, fixed now

Scoring follows the weather study:
- daily mean absolute error over each day's half-hours;
- ratios of mean daily error;
- moving-block bootstrap of days (blocks of 7, 2,000 draws, seed 20261115), with 90% intervals.

Every result is given in MW and as a ratio.

**Tables:**
1. Each forecaster's mean daily error, and its ratio to LightGBM, over all 960 days.
2. LightGBM's ratio to the regression.
3. Tables 1 and 2 by meteorological season, pooled across years.
4. Chronos-2 against LightGBM, before and after Chronos-2's release date, read as in the weather study's leakage check.
5. The error correlation c between Chronos-2 and LightGBM, on winter and summer days, by the method in `next_study/power_check.py`. This feeds gate G2. The G2 power rerun is a separate script, committed before it runs.
6. LightGBM's cost (§3).

No p-values are reported, and nothing is called significant.

## 6. Headlines, fixed now

The note and any post lead with the sentence that matches table 1's Chronos-2 row (the ratio is Chronos-2's error over LightGBM's):

| Result | Headline |
|---|---|
| Interval wholly below 1 | "In a backtest with equal inputs, Chronos-2 forecast GB demand Z% more accurately than a LightGBM model with library defaults. The models may have seen these days in training; a live test starts on 1 April 2027." |
| Interval wholly above 1 | "In a backtest with equal inputs, a LightGBM model with library defaults forecast GB demand Z% more accurately than Chronos-2. A live test starts on 1 April 2027." |
| Interval includes 1 | "In a backtest with equal inputs, Chronos-2 and a LightGBM model with library defaults forecast GB demand about equally well (ratio R, 90% interval L–U). A live test starts on 1 April 2027." |

The second sentence follows from table 2, in the same three forms: "LightGBM was [Z% better than / Z% worse than / about as accurate as] the weather regression."

"With library defaults" stays in every headline. An untuned LightGBM shows what a trained model does with little effort, not the best a trained model can do.

## 7. Limits, stated in the note before any result

- Backtest days fall in a period the foundation models may have seen in training.
- LightGBM is untuned. A tuned model may do better.
- Timestral's calendar input is affected by a known defect.
- One series (GB national demand, INDO), one horizon (day ahead), one country.

## 8. Analysis budget

This plan's tables are the whole analysis. Further cuts, models or settings wait for checkpoint 1's plan (`next_study/LESSONS.md`, R11).

## 9. Order of work

1. This plan is committed and tagged `checkpoint0-plan`.
2. The LightGBM script is written in `gb-weather-private`, where the weather inputs are. It is run on Andy's machine, and the §4 checks are passed.
3. The script is committed, and its hash is recorded in §4 by an amendment commit.
4. The scored run.
5. Forecasts and results are committed. `checkpoint0/score.py` is committed before it runs, and its outputs after.
6. A two-page note, `checkpoint0/RESULTS.md`, and a post, each checked line by line against the results (lesson 11).
