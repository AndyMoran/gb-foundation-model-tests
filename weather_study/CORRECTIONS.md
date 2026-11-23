# Corrections to the weather study

The published note (`RESULTS.md`, DOI 10.5281/zenodo.24161799) is not edited. Errors found after publication are recorded here, with the evidence, the correction and its effect. A corrected release follows under a new version DOI.

## 1. TimesFM 2.5's forecasts with weather depended on the other days in each batch (found 15 November 2026)

**The error.** TimesFM 2.5 with covariates fits one linear in-context regression across every input in a call. In timesfm 3.0.2, `utils/xreg_lib.py`, `BatchedInContextXRegLinear.fit` flattens the targets of all inputs into one vector and solves one set of coefficients. The scored backtest called it with up to 64 consecutive days at a time (`run_weather.model_forecasts`, `RUN_BATCH = 64`). Two consequences follow:
- each day's TimesFM forecast depended on which other days shared its call;
- the regression used to forecast day D was fitted partly on the contexts of later days in the batch. Those contexts contain demand after D's issue time, including D's own outturn. That is look-ahead.

**How it was found.** Checkpoint 0's cost check (`checkpoint0/REVISIONS.md`) requires each timed forecaster to reproduce its scored forecasts. Run one day per call, TimesFM differed from its scored forecasts by up to 5,643 MW on a half-hour. Run inside its scored batches, it matched exactly.

**What is not affected.** Chronos-2 runs with `cross_learning = False`, and Timestral treats each input separately. Both reproduce their scored forecasts one day per call, to within 0.01 MW. Rung 1's TimesFM had no covariates. The regression is fitted day by day. E5 did not include TimesFM.

**The correction.** `gb-weather-private`, `weather/timesfm_correction.py`, committed as ae06cb1 before it ran. It does three things:
- reruns TimesFM 2.5 with weather one day per call on all 960 days;
- reruns the study's evaluation, unchanged, with TimesFM's corrected forecasts;
- reports TimesFM's Q1–Q4 and descriptive readings beside the published ones.

TimesFM's figures from batched sensitivity runs and from the exploratory checks E1–E4 are withdrawn, not rerun. So are its rows in the descriptive block and season tables.

**Checks.** Both passed before the rerun. The evaluation, rerun on the scored forecasts, reproduced the published Q1–Q3 for every forecaster. TimesFM, rerun in its scored batches, reproduced its scored forecasts exactly (maximum difference 0.0000 MW).

**Effect.** Run 15 November 2026, 20:59–23:49, on Andy's machine. Outputs are in `correction1/`.

| Measure | Published (batched) | Corrected (one day per call) |
|---|---|---|
| Mean daily error with weather (MW) | 1,474 | 1,620 |
| Q1: with weather ÷ without | 0.941 (0.913–0.968), p < 0.0005 | 1.034 (0.999–1.068), p = 0.947 |
| Q2: gap to NESO closed | 93 MW, 11% | −53 MW, −6% |
| Q3: with weather ÷ regression with weather | 1.453 (1.394–1.510) | 1.597 (1.530–1.662) |
| Q1 without fallback days | 0.943 (0.913–0.974) | 1.043 (1.004–1.080) |
| Q1 on winter days | 0.875 (0.827–0.926) | 0.985 (0.924–1.050) |

The two sets of forecasts differ by up to 6,801 MW on a half-hour. The median, over days, of each day's largest difference is 927 MW. Every other forecaster's results are unchanged.

**What changes in the published note:**
- **Q1 for TimesFM 2.5 is no longer rejected.** The note's summary, "all four forecasters forecast GB electricity demand better, each confirmed", is wrong for TimesFM 2.5. Forecast one day at a time, weather did not reduce its error (ratio 1.034; p = 0.947). The confirmed improvements are three: the regression, Chronos-2 and Timestral.
- **Q2 for TimesFM 2.5 is reversed.** Weather widened its gap to NESO slightly, by 53 MW, rather than closing it by 11%.
- **Q3 for TimesFM 2.5 is larger.** Its error is 1.60 times the regression's, not 1.45.
- **TimesFM 2.5's other-mode figure (0.952), its block, season and holiday figures, and its rows in E1–E4 are withdrawn.**
- **The other forecasters' results stand,** including everything about Chronos-2, Timestral, the regression and E5.

**What this does not settle.** The batched forecasts combined two things: pooling the weather regression across 64 days, which gives it more data, and look-ahead within each batch. The correction removes both. It does not measure how much of the published gain came from each. A pooled regression using only past days would answer that, but it would be a new analysis, not a correction.

**Reported upstream.** [google-research/timesfm#577](https://github.com/google-research/timesfm/issues/577), with a minimal reproduction (`gb-weather-private`, `weather/timesfm_batch_repro.py`). Batched with one other series, a synthetic series' forecast moved by up to 1.23, on a level of about 10 and a covariate effect of about ±2.

**Release.** Version 2 of `RESULTS.md`, with this correction, was released on 16 November 2026 as tag `weather-results-backtest-v2`, DOI [10.5281/zenodo.24284719](https://doi.org/10.5281/zenodo.24284719). Version 1 stays available at [10.5281/zenodo.24161799](https://doi.org/10.5281/zenodo.24161799).

## 2. An empty day from Google's ERA5 copy can be cached and reused (found 18 November 2026)

**The defect.** `gb-weather-private`, `weather/sources.py`, `_arco_day` fetches a day of ERA5 from Google's copy when the CDS files lack it, and caches the result. It checks that the day has 24 hours, not that the hours hold values. Google's copy can return a day whose every value is missing: on 18 November, the cached files for 4 and 9 November held nothing else. Once cached, an empty day is reused on every later build.

**How it was found.** A dry run of the live push on 18 November stopped with "ERA5 missing values" from 4 November. The CDS download, `era5_download.py`, had not run since 10 November, so November came from Google's copy, and two of its days were empty.

**Effect: none on any published result.** `national.era5_national` stops on any missing value, so an empty day can stop a build but never enter one. The published backtest and every live push so far built without it: the first live push, for 20 November, took all 61 ERA5 days from CDS.

**The correction.** The code is frozen under `WEATHER_LOCK.json` and is not changed. Instead:
- the two empty files were moved out of the cache (`~/gb-weather-data/era5_arco/_to_delete/`);
- `era5_download.py` now runs hourly from Task Scheduler, so the CDS files keep ahead of the builds and Google's copy is needed only for hours CDS lacks.

If an empty day is cached again, the build stops with the same message, and the fix is the same: move the file aside and fetch the day from CDS.

## 3. The live window's scoring would batch TimesFM 2.5 (found 23 November 2026, before any live day was scored)

**The defect.** `gb-weather-private`, `weather/run_weather.py`, makes each model's forecasts in batches of days that share a horizon, up to rung 1's batch of 64 (`model_forecasts`). That is how the backtest was scored, and it is the cause of correction 1: TimesFM 2.5 with weather fits one in-context regression across every day in a call, so a day's forecast depends on the other days in its batch. The prospective window's scoring (§6.3) would use the same code, and this record did not say otherwise. It was found while checking the live forecasts for the imbalance study (`imbalance_cost/PLAN.md` §6).

**Effect: none yet.** No live day has been scored. Chronos-2 (`cross_learning = False`) and Timestral treat each day separately, and the regression is fitted day by day, so batching does not affect them (correction 1).

**The correction, fixed now.** Before the live window is scored, TimesFM 2.5 with weather is run one day per call, as in correction 1. Batched TimesFM results are not part of the live comparison. Each forecast is archived with its target day and the inputs pushed before that day. The script that does this is committed before it runs; the frozen scoring code under `WEATHER_LOCK.json` is not changed.
