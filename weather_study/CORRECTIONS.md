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

**Release.** Version 2 of `RESULTS.md`, with this correction, was released on 16 November 2026 as tag `weather-results-backtest-v2`, DOI [10.5281/zenodo.24284719](https://doi.org/10.5281/zenodo.24284719). Version 1 stays available at [10.5281/zenodo.24161799](https://doi.org/10.5281/zenodo.24161799).
