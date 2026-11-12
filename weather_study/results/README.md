# Weather study: backtest results

The one scored run of the backtest (`backtest_attempt1`, 11 November 2026), which passed every gate check. The plan
allows no second run once one passes.

| File | Contents |
| --- | --- |
| `results.json` | Gates, Q1 to Q4 and the plan's descriptive results, as `run_weather.py score` wrote them |
| `forecasts.csv` | Every half-hour of the 960 days: outturn, and each forecaster's forecast with and without weather |
| `daily_mae.csv` | Each forecaster's mean absolute error for each day, with and without weather |
| `descriptive_blocks.csv`, `descriptive_seasons.csv`, `descriptive_tables.md` | Errors by four-hour block and by season (written after the freeze, `descriptive_tables.py`) |
| `exploratory.json`, `exploratory.md`, `exploratory_e3_daily.csv` | The exploratory checks added after review (`exploratory.py`) |

**Backtest inputs.** The national weather inputs for every backtest day are not stored here. Their hashes are in
`../WEATHER_LOCK.json`, and they can be rebuilt from public ECMWF open data and ERA5 with
`weather/backtest_inputs.py` in [gb-weather-private](https://github.com/AndyMoran/gb-weather-private) at the tag
`weather-plan`; the rebuilt files must match the locked hashes.
