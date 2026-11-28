# Quantile study: revisions

Choices made after the plan was frozen at tag `quantiles-plan` (5885516). None changes a forecaster, a measure, a set, a label rule, a prediction or a headline.

1. **Readings of the plan that `score.py` fixes** (93d8ab2, committed before it ran).
   - *Scored days* are the days on which outturn, Chronos-2's quantiles and median, NESO and the regression are complete, and every dressed forecaster can be dressed under all five variants. Every variant requires at least 28 days in its window, so the five variants score the same days. In stage 1 that drops the first 29 backtest days, 16 March to 13 April 2024, and nothing else.
   - *Check 1* is recomputed from the merged data and must agree with `backtest_check.csv` day by day.
   - *The evening set* scores each day by the mean over its half-hours from 16:00 to 19:30 UK time.
   - *Coverage* counts outturn on an interval's edge as inside.
   - *The width test (§7 C)* breaks ties in width by date order. A month enters the monthly correlations only if it has at least 20 scored days.
   - *The stage 2 power estimate (§9)* draws 500 windows of 130 days from stage 1's days in stage 2's season, by the 7-day block bootstrap, from the generator seeded with (20261129, 1). Each window's ratio interval uses 2,000 draws. Candidate differences run from 0 to 0.5 in steps of 0.005. Scaling Chronos-2's daily scores by *k* scales a window's ratio and interval by *k*, so each window is bootstrapped once.
   - *The headline* gives scores to the nearest MW, ratios to three decimals and coverage to one. A headline with an undefined label is not written.
2. **Rounding in the generated tables.** `results_stage1.json` stores values rounded to four decimals, and `results_stage1.md`'s tables round those again to three. The headline is written from unrounded values. So the primary ratio against the dressed median, just below 0.9905 unrounded, shows as 0.990 in the headline and as 0.991 in the table, where the stored 0.9905 was rounded again. No label is affected, because every label is computed before any rounding. The headline and the JSON govern. Before stage 2 runs, `score.py` will write its tables from unrounded values, recorded here.
