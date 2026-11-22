# LightGBM variants: revisions

Every implementation choice the plan (`PLAN.md`, tag `lgbm-variants-plan`) does not name, and every change after a script has run on the backtest. Newest last.

## V5's data, before any fetch (20 November 2026)

1. **New data go in new files; nothing frozen changes.** INDO for March to December 2022 goes to `data/indo_2022.csv`, not into `data/indo.csv`, whose hash is in `data/fetch_manifest.json`. ERA5's half-hourly series for 15 March 2022 to 14 March 2023 goes to its own file, beside the frozen one. `lgbm_variants/v5_data_manifest.json` records both hashes.
2. **Each new file is checked where it meets the frozen data.** INDO's December 2022, held by both files, must agree to the megawatt. The ERA5 series is rebuilt by the backtest's own functions for six days past the join, and must agree with the frozen file to its four decimals. If either check fails, nothing is used.
3. **Gaps are counted, not filled.** The manifest lists every incomplete training day from 15 March to 30 November 2022. V5 drops incomplete days from training, as every forecaster here does.
4. **The ERA5 download reuses `era5_download.py` unchanged,** with its first month moved back to March 2022 at run time. The request, the files, the log and the single-instance lock are the same as the hourly task's.

## `lightgbm_variants.py`, before it ran on the backtest (20 November 2026)

The script lives in `gb-weather-private/weather/`, as `PLAN.md` §9 says, and changes neither `lightgbm_weather.py` nor `regression_weather.py`. Its outputs go to this folder.

5. **The training window is a parameter, and is checked at 365 days.** S1's feature build and the weather regression are rewritten with the window as an argument. At 365 days they must reproduce S1's features and `RegressionW`'s forecasts exactly (check 2), and the script's S1 must reproduce checkpoint 0's saved S1 forecasts exactly on the 20 sample days (check 6, added). So V1–V4 differ from S1 only in the change each names.
6. **V1** fits LightGBM, with S1's settings and its L1 objective, to the regression's in-sample residuals on S1's training rows. Rows in a slot the regression does not fit (fewer than 20 rows) are dropped. The forecast is the regression's forecast plus the residual forecast.
7. **V2 and V2c** standardise every non-categorical feature, the holiday and Christmas flags included, by its mean and standard deviation over the fit's rows. The target-day rows use the same values. A feature with zero spread is centred only.
8. **V3** fits each slot's model on that slot's rows of S1's training matrix, without the slot feature.
9. **V4's temperature mean** for a slot is taken over that slot's training rows. Those are the same rows the regression fits for the slot, because both require demand, both lags and all three weather values to be present.
10. **V5's data** join the frozen data at their start. Where both hold a half-hour, the frozen value is kept; the manifest's checks show they agree.
11. **Check tolerances.** Features must match exactly. V2's scaling and V4's terms must match to 1e-9. The in-sample regression fits must match the normal equations to 0.1 MW, the tolerance the weather study's gate check 8 used for the same comparison.
12. **Check 3's tolerance was set after a development run on synthetic data.** The plan asks V1 to recover a known heating curve "to a stated tolerance" without giving one. On 10 days of quiet synthetic demand (a quadratic heating curve, little noise), V1's error was 1.07 times the regression's (139 against 129 MW). The tolerance is therefore V1 at most 1.10 times the regression's error, and at most a quarter of the heating term's mean absolute size. No backtest day was involved.
13. **Coverage is checked at the end of the run** (check 7, added): the run refuses to write forecasts if any variant misses a half-hour the regression forecast. Running every variant on every day inside the checks would double the run time.
14. **The run is long.** On the development machine V3, with 48 separate fits a day, took about 45 seconds a day, and the other variants about 4 seconds each. The full run should take 12 to 15 hours.

## `score.py`, before it ran (21 November 2026)

`score.py` was written and committed before any variant forecast existed. Its synthetic check passed, and it failed, or stopped with an error, when each of four rules was broken in turn: ties sent to the later variant, V2c allowed as the best variant, overlapping intervals read as "supported", and winter cut to December–February.

15. **When H3 and H4 read "unclear".** The plan offers "supported, not supported, or unclear" and says H3 and H4 compare point estimates while stating whether the intervals overlap. It does not say when "unclear" applies. The rule, fixed before scoring: not supported if a point estimate does not point the hypothesis's way; supported if every one does and no pair of intervals overlaps; unclear if every one does but some intervals overlap. H2 is a choice on point estimates, so it is supported or not supported only.
16. **S1 is checkpoint 0's saved forecast.** `lightgbm_variants.py` check 6 showed the script's own S1 equal to it on the 20 sample days, so the variants run does not repeat S1.
17. **Scoring reuses checkpoint 0's code unchanged.** `load`, `daily`, `boot_idx`, `ratio`, `table_vs` and `reading` are imported from `checkpoint0/score.py`. Only the seed differs (20261119, as `PLAN.md` §5 sets). A day is scored only if every forecaster in the table has every half-hour, as in checkpoint 0.
18. **Winter is November to March,** as `PLAN.md` §5 says, not checkpoint 0's December–February.
19. **The headline's numbers have three decimals,** as the ratios in checkpoint 0's headlines.

## After scoring (22 November 2026)

20. **The run took 1 hour 47 minutes on Andy's machine,** not the 12 to 15 hours item 14 estimated from the development machine. The cost check (`cost.json`) gives V3 at 2.7 seconds a day and every other forecaster under 1.2.
21. **Two exploratory additions, written after the scored results were seen,** at a review's request. `explore.py`, committed before it ran, reads the same files as `score.py` and changes no scored result, reading or headline:
    - **H3, compared directly.** Item 15's rule read H3 from point estimates and overlapping intervals, and overlap alone does not show whether two ratios differ. `explore.py` gives each variant's winter ratio minus S1's, with an interval on paired bootstrap draws, and the same for all days and for T1.
    - **V2's errors.** V2's mean daily error (3,089 MW) is dominated by a few days of extreme raw output, as low as −9.3 million MW. `explore.py` reports the distribution of its daily errors and its five worst days. V2 is unstable as specified, so it did not provide a reliable test of H4, whatever the fixed rule reads. Regularising its linear leaves (`linear_lambda`, default 0) is one setting a future plan could test; changing it now would change the model after seeing the result.
22. **`explore.py`'s first run stopped before computing anything.** Both scoring scripts are named `score.py`; importing the variants one as `score` made it find itself, not checkpoint 0's, when it imported `score` in turn. It now loads the variants' `score.py` under its own name. Nothing was written by the failed run, and no logic changed.
