# Checkpoint 0: a backtest first look with LightGBM

Andy Moran (Heaviside Analytics) · 15 November 2026 · **Status: frozen at tag `checkpoint0-plan`**

**The question:** on the weather study's backtest, with equal weather and calendar inputs, how does a trained LightGBM model compare with the foundation models and with the weather regression?

## 1. What this is, and is not

This is a new, exploratory study on backtest days. It is not part of the weather study, whose last analysis was E5. It is not a live benchmark either: the standing benchmark's first live checkpoint opens on 1 April 2027 (`BENCHMARK_RULES.md`, rule 6.1). It is called checkpoint 0 because it builds the LightGBM forecaster that the benchmark uses, and its results feed gate G2 (`PROJECT.md` §4). Every result is descriptive.

## 2. Non-claims

Checkpoint 0 does not establish:
- live performance: the foundation models may have seen these days in training;
- the best a trained model can do: LightGBM is untuned;
- a ranking of model families: it compares five specific forecasters on one series;
- anything for other series, horizons or countries: one series (GB national demand, INDO), day ahead;
- commercial value: cost is measured, not priced.

The note states these before any result.

## 3. What has been seen before this plan

Every foundation-model and regression forecast and error in the backtest is published: `weather_study/RESULTS.md`, E1–E5 and `results/`. No LightGBM model has been fitted, tuned or run on these data, and no LightGBM error has been computed. No forecaster's compute time has been measured (`weather_study/LESSONS.md`, lesson 6).

## 4. Forecasters compared

The existing forecasts are used as saved, unchanged, and checked against these hashes:
- `weather_study/results/forecasts.csv`: b5f16561dcf1a26f8d7910bcca95cd137f677760c6f80153349034d4a85f7328
- `weather_study/results/calendar_forecasts.csv`: 976e27ef28d0eef1ddf351c6557af9f771c308b94f389fe0f06b84ec86c8e2fe

| Forecaster | Column | Weather | Calendar | Ranked |
|---|---|---|---|---|
| Chronos-2 | `chronos2_A` (E5) | Yes | Yes | Yes |
| TimesFM 2.5 | `timesfm25_weather` | Yes | No (8-week context; weather study, E5) | Yes |
| Weather regression | `regression_weather` | Yes | Yes | Yes |
| **LightGBM**, defaults | new | Yes | Yes | Yes |
| **LightGBM**, S1 and S2 settings | new | Yes | Yes | Sensitivity only (§5) |
| Timestral | `timestral_A` (E5) | Yes | Yes, affected by a defect | No |
| Timestral | `timestral_weather` | Yes | No | No |

Timestral's calendar input is affected by a covariate defect (`mistralai/timestral#9`), so it is shown both ways and is not ranked. Any ranking compares Chronos-2, TimesFM 2.5, LightGBM (defaults) and the regression.

## 5. LightGBM, fixed before any run

**Information:** exactly the regression's (`gb-weather-private`, `weather/regression_weather.py`):
- **Clock slot:** the local half-hour, 0–47.
- **Calendar:** day of week as a category; bank holiday (England and Wales); 24 December to 2 January.
- **Lags:** demand at D−2 (falling back to D−9) and at D−7 (falling back to D−14), same slot.
- **Weather:** temperature, wind and solar for the half-hour, unadjusted, by the regression's splice rule (`weather_for`).

Trees need no centred or interaction terms, so the regression's Tc, Tc² and Tc × wind are not built.

**Training:** one model across all slots. It is re-fitted for each target day D on every half-hour of the complete days D−366 to D−2 whose target, lags and weather are finite. That is the regression's window and retraining frequency. The script asserts that no training day is later than D−2.

**Primary settings: LightGBM's defaults** (100 trees, learning rate 0.1, 31 leaves, at least 20 rows per leaf), with three exceptions:
- `objective = 'l1'`, because the score is mean absolute error;
- `seed = 20261115` with `deterministic = True`, so runs repeat exactly;
- day of week declared categorical.

**Sensitivity settings, fixed now.** Defaults are not neutral. In load forecasting, Nguyen et al. (Engineering, Technology & Applied Science Research, 2024) find that "using default hyperparameter values may result in large errors in load forecasting". On 58 time series, randomly generated configurations cut mean squared error by up to 17.45% against the default (Barros, Cerqueira and Soares, PRICAI 2021). That paper's proposed alternative defaults were not accessible before the freeze. Two configurations published for electricity load forecasting are used instead, each run in full as a sensitivity:

| Run | Source | Settings |
|---|---|---|
| S1 | Misiurek, Olkuski and Zyśk, *Energies* 19(13), 3211 (2026), doi:10.3390/en19133211: national load (Poland) against the TSO's forecast, rolling-window training | 500 trees, learning rate 0.05, 31 leaves, maximum depth 8, at least 20 rows per leaf, row sampling 0.8 (every iteration), column sampling 0.8 |
| S2 | Uzzaman et al., *Electricity* 7(4), 143 (2026), doi:10.3390/electricity7040143: distribution feeders (Bangladesh) | 500 trees, learning rate 0.03, 31 leaves; other settings at their defaults |

These are configurations other researchers chose for other load series, not settings tuned for this one. They test one direction (more trees, slower learning, and in S1 sampling and a depth limit) rather than bracketing every plausible setting. Three departures from the sources are made, and the same in every run:
- objective L1, as in the primary run;
- no early stopping (S1's source used it), because this plan forbids it;
- `bagging_freq = 1` with the seed fixed, because LightGBM ignores row sampling unless a frequency is set.

All three runs use the same features, window and seed. None is tuned or searched.

**Clock-change days:** forecasts are made per local slot and mapped to the target day's settlement periods by the regression's rules (`C.target_starts`, `C.clock`).

**Revisions before the freeze:** every change to the LightGBM script before the scored run, including each check that failed and the fix, is logged in `checkpoint0/REVISIONS.md` with its date, the commit and the reason. The record shows the path, not only the endpoint. Any change after the scored run is a deviation, logged the same way.

## 6. Work packages

### WP1: checks before scoring

These run on the full backtest period (lesson 9). Only check 5 touches outturn, and only with corrupted inputs.

1. **Coverage.** All three LightGBM runs produce a finite forecast for every half-hour of every backtest day that the regression covers, or each missing one is listed with the reason.
2. **Leakage.** The training-window assertion holds on every day. A deliberately leaked feature (the target day's own demand, given as a lag) is shown to make the assertion or the coverage check fail.
3. **Determinism.** Two runs on the WP2 sample days are identical to the last digit.
4. **Feature build.** A second, independent build of the feature matrix for 10 days, written with plain loops, matches the first exactly.
5. **Corruption.**
   - **Corruption:** complete days of the demand series are permuted with seed 20261115 before any feature is built. Targets and lags then come from unrelated days, while weather and calendar keep their true dates, so no input carries information about the target.
   - **Comparator:** for each target day D and clock slot, the median of the corrupted training targets for that slot over D−366 to D−2. That is the same window and data LightGBM sees. The median is used because, with no information in the inputs, it is the best forecast under the L1 objective.
   - **Pass:** primary-settings LightGBM's mean daily error on the WP2 sample days, against true outturn, is at least 0.9 times the comparator's.
   - **Rationale:** a model with no information can beat the no-information forecast only by chance or through leaked information. The 10% margin allows for chance over 20 days.

### WP2: cost

- **Days:** 20 backtest days, 5 in each meteorological season, drawn at random within each season with seed 20261115. The list is committed before any timing.
- **Forecasters:** Chronos-2 (E5 arm A configuration), TimesFM 2.5, Timestral (both configurations), the regression, and LightGBM (all three settings).
- **Machine:** all on the same machine, in one session, on CPU only, with the same fixed thread count for every forecaster (PyTorch and LightGBM thread settings), and no other heavy work running. CPU model, cores, RAM, operating system and library versions are recorded.
- **Timed:**
  - wall-clock time per forecast day, from loading that day's inputs to writing its forecasts, including fitting where a forecaster fits (LightGBM and the regression re-fit daily);
  - model loading time once per forecaster, reported separately;
  - peak resident memory per forecaster.

  One untimed warm-up day precedes each forecaster's timed days. The report gives the median and range over the 20 days.
- **Check:** each foundation model's forecasts from the timing run must match its saved backtest forecasts to within 1 MW on every half-hour. That confirms the timed configuration is the one scored. Any mismatch is reported.
- **Scope:** cost is reported in time and memory only. No £ figure is computed in checkpoint 0.

### WP3: scoring

Scoring follows the weather study:
- daily mean absolute error over each day's half-hours;
- ratios of mean daily error;
- moving-block bootstrap of days (blocks of 7, 2,000 draws, seed 20261115), with 90% intervals.

Every result is given in MW and as a ratio.

**Tables:**
1. Each forecaster's mean daily error, and its ratio to LightGBM (defaults), over all 960 days.
2. LightGBM (defaults) against the regression: the ratio and the MW difference.
3. Tables 1 and 2 repeated for LightGBM with S1 and with S2.
4. Tables 1 and 2 by meteorological season, pooled across years.
5. Chronos-2 against LightGBM, before and after Chronos-2's release (20 October 2025), read as in the weather study's leakage check.
6. The error correlation c between Chronos-2 and LightGBM (defaults), and Chronos-2's edge over it, on the summer 180-day windows and the winter 120-day windows, by the method of `next_study/summer_edge.py`. These feed gate G2 (`PROJECT.md` §4), whose power rerun is a separate script, committed before it runs.
7. Cost (WP2).

**Reading rule:** no p-values are reported, and nothing is called significant. A difference between two forecasters is described only where the 90% interval of their ratio excludes 1. Separate intervals for each forecaster are not compared, because the comparison is paired. Otherwise they are described as about equally accurate.

## 7. Headlines, fixed now

The note and any post lead with two sentences of equal weight. The first covers Chronos-2 against LightGBM (table 1); the second covers LightGBM against the regression (table 2). Each takes the form that matches its interval:

**Chronos-2 against LightGBM** (ratio = Chronos-2's error ÷ LightGBM's):

| Result | Sentence |
|---|---|
| Interval wholly below 1 | "In a backtest the foundation models may have seen in training, Chronos-2 forecast GB demand Z% more accurately than a LightGBM model with library defaults, on equal inputs." |
| Interval wholly above 1 | "In a backtest the foundation models may have seen in training, a LightGBM model with library defaults forecast GB demand Z% more accurately than Chronos-2, on equal inputs." |
| Interval includes 1 | "In a backtest the foundation models may have seen in training, Chronos-2 and a LightGBM model with library defaults forecast GB demand about equally well, on equal inputs (ratio R, 90% interval L–U)." |

**LightGBM against the regression** (ratio = LightGBM's error ÷ the regression's):

| Result | Sentence |
|---|---|
| Interval wholly below 1 | "The LightGBM model was Z% more accurate than a weather regression given the same information." |
| Interval wholly above 1 | "The LightGBM model was Z% less accurate than a weather regression given the same information: with library defaults, the trained tree model did not beat the linear one." |
| Interval includes 1 | "The LightGBM model and a weather regression given the same information were about equally accurate (ratio R, 90% interval L–U)." |

A third sentence follows if S1 or S2 changes either reading (from one row of a table to another): "With the settings of [source], [the changed reading]." If both change it, both are named. A change of reading is itself a finding, and it is reported rather than resolved.

Every lead ends: "A live, preregistered test starts on 1 April 2027."

## 8. Analysis budget

These tables are the whole analysis. Further cuts, models or settings wait for checkpoint 1's plan (`next_study/LESSONS.md`, R11).

## 9. Order of work

1. Commit, and tag `checkpoint0-plan`.
2. Commit the WP2 day list.
3. Write the LightGBM script in `gb-weather-private`, where the weather inputs are. Run WP1 on Andy's machine, logging every revision (§5).
4. Commit the script; record its hash in `REVISIONS.md`.
5. Run WP2 and the scored LightGBM runs.
6. Commit the forecasts. Commit `checkpoint0/score.py` before it runs, and its outputs after.
7. Write a two-page note, `checkpoint0/RESULTS.md`, and a post, each checked line by line against the results (lesson 11).
