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
