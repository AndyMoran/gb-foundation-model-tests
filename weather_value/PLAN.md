# What would a perfect weather forecast be worth for GB demand?

Andy Moran (Heaviside Analytics) · 17 November 2026 · **Status: parked until the current studies are published (decision, 20 November 2026). Idea draft, second version (prior work added); not reviewed; nothing frozen, no data read**

For: a reader who wants to know how much of a day-ahead demand forecast's error comes from the weather forecast, and from which variable.

**The question:** if the weather regression had known the target day's actual weather, how much would its error on GB national demand fall, and does the gain come from temperature, solar radiation or wind?

## 1. Prior work, and what this adds

**National Grid has measured this before.** A National Grid review of Met Office forecast accuracy, published by Ofgem, made demand forecasts with the weather forecast received around 9am for 1, 2 and 7 days ahead. It then recomputed them with observed weather from Met Office stations, which isolated the error due to the weather forecast. At day ahead it attributed about 350 MW of mean absolute error to consumer response (temperature, wind and light), 548 MW to embedded solar and 406 MW to embedded wind. It concluded that a very large irreducible error remains from weather forecasts. The document is undated; its date is still to find (§9).

So the question is not new. This study is an open update of that analysis:
- **Recent:** 2024–2026, with far more embedded solar installed than when National Grid's review was written.
- **Open:** the model, code, inputs and outputs are published, and every step is hashed.
- **Measured against NESO's own forecast,** as a share of the gap that weather could close.
- **Two forecaster types:** a trained regression and a zero-shot foundation model, Chronos-2.

The wider literature agrees that the share varies widely. Fay and Ringwood (2010) note that weather forecast errors have been held responsible for between 17% and 60% of load forecast errors in different studies. They also note that load models are usually trained on actual weather, not past forecasts, as the regression here is (§4). Comparing a model's error with actual and with forecast weather is a standard check, so the method is not new either.

**Expected direction.** National Grid's split puts most of the day-ahead weather error in embedded solar and wind. This study expects the same ordering, with solar larger than in National Grid's review because more solar is installed. It does not make that a hypothesis: the regression represents embedded generation only through national solar radiation and wind terms, not as generation, so its split may differ.

## 2. Why

The weather study showed that honest weather forecasts cut the regression's mean daily error by 34% (`weather_study/RESULTS.md`). This study asks the next question: how much is left to gain from a better weather forecast, and in which variable?

Three uses:
- **A ceiling.** The gain from perfect weather is the most that any better weather forecast could give this forecaster, on this weather representation.
- **A pointer.** If most of the gain is in solar radiation or wind, the weather that matters for transmission demand is embedded generation, not heating. That would motivate a bottom-up study of demand, embedded solar and embedded wind (Project 2). If it is in temperature, the parked weather-inputs study (`weather_inputs/PLAN.md`) comes back with a stronger case.
- **A gap decomposition.** NESO's forecast had less error than the regression throughout the weather study. This study measures how much of that gap weather could close.

## 3. Non-claims

This study does not establish:
- **The value of better weather representation.** "Perfect" here means ERA5 on the same 0.25° grid, weighted the same way. Urban heat, cold pools and detail finer than the grid are outside it; the weather-inputs study tests those.
- **The value for other forecasters,** except Chronos-2, run as a secondary arm.
- **Truth.** ERA5 is a reanalysis, not observed weather. It is the right reference here because the regression already trains on it (§4).
- **The value of perfect solar.** ERA5's solar radiation is the weakest of its three variables here. One evaluation found its errors larger at coasts and in mountains, and that it overestimates radiation under cloud and slightly underestimates it under clear skies (Urraca et al., 2018). So arm O-S, and arm O, understate what a truly perfect solar forecast would be worth. If solar carries the largest gain, the true value is larger still.
- **Commercial value.** The study scores demand error, not money.
- **Live performance:** it is a backtest.

## 4. Design

**Days and target.** The weather study's 960 backtest days, 16 March 2024 to 31 October 2026, scored against INDO, as before. NESO's day-ahead forecast is scored on the same days against the same outturn; it is complete on every backtest day.

**One change per arm.** Every arm is the weather regression exactly as in the weather study (`gb-weather-private`, `weather/regression_weather.py`), refitted for each target day on D−366 to D−2. Its training rows are unchanged in every arm. Only the weather for the target day D changes: the ECMWF forecast it was given is replaced by ERA5 for D's half-hours.

This is a clean swap. The regression's training weather before D−10 is already ERA5 (`weather_for`'s splice rule), so the oracle arms give the target day the same kind of weather the model learned from. Forecast error is the only thing removed.

| Arm | Target-day weather | Role |
|---|---|---|
| **F** | The ECMWF forecast, as published | Reference: the weather study's regression |
| **O** | ERA5 for temperature, wind and solar | Perfect weather |
| **O-T** | ERA5 temperature; forecast wind and solar | Temperature only |
| **O-S** | ERA5 solar; forecast temperature and wind | Solar only |
| **O-W** | ERA5 wind; forecast temperature and solar | Wind only |

Arm F must reproduce the published regression forecasts exactly, or the run stops (`PIPELINE_RULES.md` rule 1).

**The single-variable arms do not add up.** The regression has a temperature-and-wind interaction (wind chill), so the three single gains need not sum to O's gain. The note reports each, and the remainder, without forcing a split.

**Secondary arm: Chronos-2.** The same F and O swap for Chronos-2, with calendar and weather, one day per call (draft rule 4.8). It runs on a CPU in about 2 seconds a day (checkpoint 0). It shows whether the value of perfect weather depends on the forecaster. It is descriptive.

## 5. Metrics

- **Mean daily error:** mean absolute error over each day's half-hours, averaged over days.
- **Ratio to F:** each arm's mean daily error over F's.
- **Gap to NESO closed:** (F's mean daily error − the arm's) ÷ (F's − NESO's), as in the weather study's Q2. NESO had more information than any arm, so a gap that perfect weather cannot close is not weather.
- **Breakdowns, descriptive:** by meteorological season, by four-hour block of the day, and on the tails study's cold days (T1, `tails/days.csv`).

Intervals: moving-block bootstrap over days (blocks of 7, 2,000 draws), 90%, as in the earlier studies. No p-values. A gain is described only where the ratio's interval lies wholly below 1.

## 6. Headline and decision rule, fixed before any run

**Headline:** the share of F's gap to NESO that perfect weather (O) closes, with its interval, then the single variable whose arm closes the largest share.

**Decision rule for the next study.** Proposed thresholds, to be settled at review:
- **Temperature matters:** O-T closes at least 10% of the gap to NESO, with its interval wholly above 0. Then the weather-inputs study is reconsidered, R1 first.
- **Solar or wind matters more:** O-S or O-W closes a larger share than O-T, and at least 10% of the gap. Then Project 2, the bottom-up decomposition, is planned.
- **Weather matters little:** O closes under 10% of the gap. Then the gap lies elsewhere, probably in fresher demand data or embedded generation. That also points to Project 2, and the weather-inputs study stays parked.

## 7. Data still to obtain

| Need | Source | Status |
|---|---|---|
| ERA5 on every target-day half-hour | ERA5, built by `national.era5_halfhourly` with the weather study's weights | The weather study's `era5_halfhourly` file ends ten days before the last target day, because the regression needed ERA5 only before D−10. ERA5 for October 2026 may still be the preliminary release (ERA5T). Both to check |
| Everything else | The weather study's frozen backtest inputs, forecasts and NESO publications | Held, hashed |

## 8. What has been seen

The regression's backtest errors with forecast weather are published (`weather_study/results/`), by season and block. No forecaster has been run with ERA5 for the target day.

## 9. Work and timing

1. Build ERA5 for every target-day half-hour, with the weather study's code and weights; hash it.
2. Write the script; check that arm F reproduces the published forecasts exactly; run a synthetic check, as in the tails study.
3. Freeze the plan at a tag, with the decision thresholds settled.
4. Run, then write a short note. It cites National Grid's review first and presents this study as an update of it.

Literature still to check before the freeze:
- **The date of National Grid's review,** because its figures reflect the solar fleet of that time.
- **Newer NESO publications** on demand forecast error by cause, which may update National Grid's split.

This is a few days' work, and fits around the battery project.

## Sources

- `weather_study/RESULTS.md`, `checkpoint0/RESULTS.md`, `tails/RESULTS.md` (this repository).
- National Grid. [Review of Met Office weather forecast accuracy](https://www.ofgem.gov.uk/ofgem-publications/111122). Published by Ofgem; undated.
- Fay, D. and Ringwood, J. V. (2010). [On the influence of weather forecast errors in short-term load forecasting models](https://mural.maynoothuniversity.ie/3618/1/JR_On_the_influence.pdf). *IEEE Transactions on Power Systems* 25(3), 1751–1758.
- Urraca, R. et al. (2018). [Evaluation of global horizontal irradiance estimates from ERA5 and COSMO-REA6 reanalyses using ground and satellite-based data](https://publications.jrc.ec.europa.eu/repository/handle/JRC108636). *Solar Energy*.
- Hersbach, H. et al. (2020). The ERA5 global reanalysis. *Quarterly Journal of the Royal Meteorological Society* 146, 1999–2049. doi:10.1002/qj.3803.
