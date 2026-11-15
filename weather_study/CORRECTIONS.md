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

TimesFM's figures from batched sensitivity runs and from the exploratory checks E1–E3 are withdrawn, not rerun.

**Effect.** [Pending the run.]
