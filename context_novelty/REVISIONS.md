# Context novelty: revisions

Every implementation choice the plan (`PLAN.md`, tag `context-novelty-plan`) does not name, and every change after a script has run on the backtest. Newest last.

## Before any script ran (20 November 2026)

`build_days.py` was written and committed before it ran. Its synthetic check passed, and it failed as it should when each of three rules was deliberately broken: "below" made non-strict, the pre-D half-hours counted as target, and T1∖N built without removing N.

1. **Target half-hours are D's own.** The horizon the models received runs from the input cut-off (08:30 on D−1) to the end of D. The plan's "target half-hour" is read as D's settlement periods only (46, 48 or 50, from `code/common.target_starts`), the last rows of the horizon. The earlier horizon rows are not used for any set. Their coldest value is recorded in `day_inputs.csv` (`t_gap_min`) so a reader can see whether it would have mattered.
2. **"Below" is strict.** A target temperature equal to the context's coldest is not novel. The same holds for Nw's "above" and "below".
3. **The inputs file is read directly.** `run_weather.load_inputs` renames `t2m_c`, `wind_ms` and `solar_wm2` and changes nothing else. The script reads the same columns from the same hash-checked file, so it needs nothing from `gb-weather-private`. It checks the layout the models received for every day: 2,688 context half-hours ending at the cut-off, a horizon of the length `code/common.horizon` gives, and target half-hours equal to D's settlement periods.
4. **T1 and T4 come from `tails/days.csv`.** The file is checked against the SHA-256 in `tails/days.json`.
5. **Nw's solar arm will almost never fire.** The context's lowest solar value is a night-time zero, and a target value cannot fall below zero. The arm is kept as the plan defines it. `days.json` reports each arm's count separately, so an empty solar arm is visible, not hidden.
6. **Fallback days are flagged.** On a fallback day the horizon came from D−2's run. That is still what the models received, so these days stay in the sets. `days.json` lists any that fall in N.
7. **The plan tag is checked.** The real build refuses to run if `PLAN.md` differs from tag `context-novelty-plan`, or if the script, `code/` or the tails study's day files have uncommitted changes.

## Plan version 2, before any script ran on the backtest (20 November 2026)

Two reviews of plan version 1 led to version 2 (`PLAN.md`, "Changes from version 1"). `build_days.py` (deec625) had not run on the backtest, so it was revised to match rather than run against the old plan.

8. **The plan tag is now `context-novelty-plan-v2`.** The real build refuses to run if `PLAN.md` differs from it. Item 7 above stands with the new tag.
9. **Matched pairs and cold-spell clusters are built here,** from covariates only, as `PLAN.md` §5 sets out, and written to `pairs.csv`. T1's measure, `t_mean`, and the daily minimum, `t_min`, come from `tails/day_inputs.csv`, checked against `tails/days.json`.
10. **Temperature differences are rounded to 0.000001 °C before matching.** That is `tails/day_inputs.csv`'s precision, so ties are exact rather than decided by floating-point noise, and the plan's tie rule applies as written.
11. **The synthetic check covers the matching.** It checks the caliper, the month rule across December and January, nearest-first choice, both tie rules, no reuse of controls, unmatched days, and the cluster boundary at two and three days apart. It failed, as it should, when each of five rules was broken in turn: reuse allowed, ties to the later date, a wider caliper, months not wrapping at the year end, and the cluster boundary moved by one day.
