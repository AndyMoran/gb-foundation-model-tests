# Assumptions

Every claim the benchmark's design rests on, labelled GROUNDED (with its source) or PROVISIONAL (with the check that would settle it). A PROVISIONAL row moves to GROUNDED only when its check is done and cited. See `PROJECT.md` §3.1.

| ID | Claim | Status | Source, or the check that settles it |
|---|---|---|---|
| A1 | Chronos-2's edge over the weather regression in summer is about 10.8% (90% interval 7.7–15.0%) | GROUNDED (backtest) | `next_study/summer_edge.json` |
| A2 | The error correlation c between Chronos-2 and the regression is 0.47 in summer, 0.54 in winter | GROUNDED (backtest) | `summer_edge.json`; `power_check.json` |
| A3 | The live edge is similar to the backtest's | PROVISIONAL | Only checkpoint 1 settles it; backtest days may have been seen in training (R2) |
| A4 | c for Chronos-2 against LightGBM is similar to c against the regression | PROVISIONAL | G2: measure on LightGBM's backtest (R1) |
| A5 | The 7-day moving-block bootstrap holds each one-sided test's false-positive rate near 0.025 (per test, rule 7.2) | PROVISIONAL | G3: 5,000 simulations at a true edge of zero (R12) |
| A6 | No feasible winter window reaches 80% power at a 10% edge | GROUNDED (backtest) | `power_check.md`; `pooled_winter.md` |
| A7 | The regression in E5 had the calendar, so E5's inputs were matched | GROUNDED | `weather_study/RESULTS.md`, E5; `AndyMoran/gb-weather-private`, `weather/calendar_study.py` |
| A8 | Timestral's covariate asymmetry comes from per-row scaling treating {0, −1} rows differently from 0/1 rows, and the categorical route avoids it | PROVISIONAL (mechanism reported upstream) | `mistralai/timestral#9`; confirm with the maintainers' reply or a minimal reproduction |
| A9 | ECMWF open data, NESO data and each model's licence allow publishing derived daily forecasts and scores | PROVISIONAL | Read each licence before the rules are tagged |
| A10 | The daily pipeline can run unattended off the laptop with ≤ 1 missed day in 28 | PROVISIONAL | G4 |
| A11 | Each entrant's release date and training-data cutoff can be established from public sources | PROVISIONAL | Check model cards for Chronos-2, TimesFM 2.5 and Timestral before G5 |
| A12 | INDO outturn as first published is retrievable and archived for each day | PROVISIONAL | Confirm the source and record the download time daily from the start of G4 |
| A13 | A GitHub-hosted runner for a public repository (4 CPUs, 16 GB RAM) has enough free disk for the environment and every entrant's weights | PROVISIONAL | Run `.github/workflows/runner_check.yml` once by hand; record free disk and CPU here |
| A14 | Every entrant runs within rule 3.3's budget on that runner | PROVISIONAL | Time each entrant on the runner during G4 |
