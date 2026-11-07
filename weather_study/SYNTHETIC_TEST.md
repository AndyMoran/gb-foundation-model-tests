# Weather study: synthetic end-to-end test

*6 November 2026 · Andy Moran (Heaviside Analytics)*

The weather study asks whether day-ahead weather forecasts improve three forecasting foundation models' forecasts of GB electricity demand. Its plan and code are frozen before any model sees real weather-forecast inputs. Before that freeze, the weather pipeline ran once from end to end on synthetic data, as the study's brief requires. This note records the result. No real demand entered the test.

The weather-processing code is private until the study's results note, when it will be published on the same day. Until then, the SHA-256 hashes below fix the exact code that ran, so anyone can check it at publication.

## What ran

| | |
| --- | --- |
| Pipeline code (`weather/national.py`) | SHA-256 `33e289045731fada12496dfee59176017db61230b547831411561ae0275014b3` |
| Test code (`weather/synth_test.py`) | SHA-256 `a27a28d518c29ca8886caa95a0e7c46739d9ab6c09d9a43df31ea58a56c0192d` |
| Spatial weights (`weights.nc`) | SHA-256 `c3af7721b673386ef31285ff55deab71617bff774b7cb5c13e448dee543102be` |
| Private commit | `923192f69c179b1f59ec4f7397608311b3e11c8f`, pushed before the run; the test refuses to run otherwise |
| Run | 6 November 2026, 20:44 to 21:29 UTC |

The test builds gridded weather over Great Britain in the formats of the study's real sources: ERA5, with each hour's own solar total, and ECMWF's 00:00 UTC runs, with solar radiation accumulated from the start of the run. It then passes everything through the pipeline: weighting to national values, the ten-day splice between the two sources, and interpolation to the demand study's half-hours.

## Part 1: the pipeline

| Check | Result |
| --- | --- |
| ERA5 history equals the true national weather, and its solar means | Pass |
| ECMWF history equals the truth at its own times; solar accumulations are differenced correctly | Pass |
| A run whose solar accumulation is deliberately left undifferenced is caught | Pass |
| The horizon comes from the run of D−1; with that run marked late, from the run of D−2 | Pass |
| Every half-hour of context and horizon is filled, across the October clock change (79- and 81-step horizons) | Pass |

Reading 3-hourly and hourly sources at half-hour midpoints costs, on average, 0.19 °C, 0.27 m/s and 14 W/m² against the truth over the eight-week context. The real study bears the same cost.

## Part 2: TimesFM's weather mode

TimesFM 2.5 takes weather through a linear regression fitted within each forecast. The regression can be fitted before the model (regression first) or to the model's errors afterwards (TimesFM first). The brief fixed the test and the threshold before it ran: TimesFM first would replace regression first only if, in every scenario, its mean daily error were at least 5% lower and its 95th-percentile daily error no higher.

Each scenario uses 20 synthetic series (seeds 20261106 to 20261125), each forecast on 30 days. Demand responds to the weather with a heating threshold at 15.5 °C, wind chill below it, and behind-the-meter solar. Forecast error is added to the target day's weather only.

Mean daily error in MW (95th percentile in brackets), 600 forecasts each:

| Scenario | Regression first | TimesFM first | No weather |
| --- | --- | --- | --- |
| Winter, with forecast error | **1,127** (2,437) | 1,409 (3,156) | 1,534 (3,315) |
| Shoulder season, with forecast error | **1,294** (2,704) | 1,357 (2,844) | 1,414 (3,169) |
| Winter, perfect weather | **1,098** (2,408) | 1,407 (3,153) | 1,534 (3,315) |

**TimesFM first was worse in every scenario, so the study uses regression first.** TimesFM's fit to its own history absorbs the weather's slow swings, which leaves the regression fitted afterwards little to learn.

These errors show how each mode uses the weather. They do not predict how much weather will help on real demand: the synthetic response is simple, and its noise known.
