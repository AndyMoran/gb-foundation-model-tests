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
| A9 | ECMWF open data, NESO data and each model's licence allow publishing derived daily forecasts and scores | GROUNDED | Checked 18 November 2026; `ATTRIBUTION.md`. ECMWF open data and ERA5 are CC BY 4.0; Elexon treats its data as open; NESO's licence is based on OGL v3.0; Chronos-2 and TimesFM 2.5 are Apache 2.0; Timestral's "Modified MIT" bars use by anyone whose company or employer has monthly revenue above $20 million, but places no condition on publishing outputs. Conditions: every publication carries the four data attributions in `ATTRIBUTION.md`; `benchmark/ENTRANTS.md` records Timestral's condition; Elexon's wording is confirmed (A15) |
| A10 | The daily pipeline can run unattended off the laptop with ≤ 1 missed day in 28 | PROVISIONAL | G4 |
| A11 | Each entrant's release date and training-data cutoff can be established from public sources | PROVISIONAL | Check model cards for Chronos-2, TimesFM 2.5 and Timestral before G5 |
| A12 | INDO outturn as first published is retrievable and archived for each day | PROVISIONAL | Confirm the source and record the download time daily from the start of G4 |
| A13 | A GitHub-hosted runner for a public repository (4 CPUs, 16 GB RAM) has enough free disk for the environment and every entrant's weights | GROUNDED | `runner_check.yml`, run 44297069899, 18 November 2026, at commit ae35b13: `ubuntu-latest` gave 4 CPUs (Intel Xeon 6975P-C, 2 threads per core), 15 GiB memory with 14 GiB available, no swap, and 91 GB free in the workspace. Rule 3.3's 12 GB memory and 5 GB weights limits fit. Runner images change, so A14's timings during G4 are the binding check |
| A14 | Every entrant runs within rule 3.3's budget on that runner | PROVISIONAL | Time each entrant on the runner during G4 |
| A15 | The attribution line this repository uses for Elexon data ("Contains BMRS data © Elexon Limited copyright and database right") is the one the BMRS Data Licence Terms require | PROVISIONAL | Open the BMRS Data Licence Terms from the BMRS website and compare; the developer portal's link to them is a placeholder |
