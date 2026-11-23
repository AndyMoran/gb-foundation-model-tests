# Imbalance exposure: revisions

Choices made after the plan was tagged `imbalance-cost-plan` (f0678fa). None changes a forecaster, a measure, a set, a label rule or a headline.

1. **How a live calendar forecast proves its inputs** (`gb-weather-private/weather/calendar_live.py`, PLAN.md §6). Demand: the INDO series is cut at 08:30 UK time on D−1 from the prospective run's cache, whose values are never overwritten, and its SHA-256 must equal the `input_sha256` the prospective run recorded for D when it forecast D. A day whose hash differs is refused, not forecast. Weather: the committed, unchanged `weather_study/inputs/<D>.csv` pushed for D. Calendar: E5's function and the hashed bank-holiday file. Each day's record lists every hash and the commit of the weather file.
2. **Order of the daily runs.** The calendar forecast for D needs the prospective record for D (made at 09:45) and the weather inputs for D (pushed from 10:00), so it runs after both: suggested at 10:30, 16:00 and 21:30 UK time. A run that finds either missing stops and leaves the day to the next run.
3. **The reproduction check** reruns E5's arm A on six backtest days (every 160th of the 960) and requires every half-hour within 1 MW of `weather_study/results/calendar_forecasts.csv`. It is run once, committed, and required by every later run of the same script. It confirms the code path; nothing is tuned on it.
4. **Weights.** Chronos-2's weights are checked against the prospective lock, the same pinned revision the no-weather live run uses.
5. **One day per call,** for every live and reconstructed day, although Chronos-2 runs with `cross_learning = False` and batching would not change its forecasts.
