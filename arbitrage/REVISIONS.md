# Arbitrage signal: revisions

Choices made while writing `score.py`, after the plan was tagged `arbitrage-plan` and before any real run. None changes a forecaster, a set, a measure's purpose, a label rule or the headline.

1. **The sign of the bias correction.** PLAN.md §6 says each forecast is scored "after subtracting its own recent bias: its mean error, *y* minus forecast". Subtracting *y* − *F* from *F* would double the bias, not remove it. The script does what the plan intends: it adds the recent mean of *y* − *F* to the forecast, so a forecast that ran 100 MW high is lowered by 100 MW. NESO's forecast is corrected the same way.
2. **Recent bias.** The mean of the 28 daily mean errors from D − 29 to D − 2, each day weighted equally, as elsewhere in the project. A window with any day missing gives no correction, and that day drops from the bias-corrected measure.
3. **Pooled shares.** The capture share and the hit rate are totals over the days in a set (total captured over total perfect; total hits over total half-hours of disagreement), not means of daily shares, so a day with few disagreements does not count as much as one with many. Their intervals are the same ratios on each bootstrap draw.
4. **Ties.** A half-hour where outturn equals NESO's forecast counts as not moving the forecaster's way. In part A, outturn's own four highest and four lowest use the same tie rule as the forecasts: the earlier start wins.
5. **Day-to-day direction.** A day on which outturn's daily mean or peak does not change counts as a wrong call. "Weekday pairs" are pairs whose later day is Tuesday to Friday; bank holidays are not removed.
6. **The headline's numbers.** Missed spreads are rounded to whole MW and gains to one decimal place. A gain is signed, so "moved clearly away from Chronos-2, by −40.0 MW" can appear: the label gives the direction and the number its size and sign, as the plan defines the gain.
7. **Check 1** compares each forecaster's mean daily error with `asymmetric/results.json`, whose hash the script records, to 0.01 MW.
8. **Check 3 on real data.** The script adds 1,024 MW to Chronos-2's forecast and confirms part A is unchanged on every day, a perfect forecast misses nothing and scores 8 hits, and NESO scored against itself gains 0 on every half-hour.
9. **The synthetic noise check** draws its noise from a fixed seed, so it is repeatable.
10. **Development runs.** The synthetic check was run while writing the script, and the report was rendered from invented data. Nothing has been computed on real forecasts or outturn.
