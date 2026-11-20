# Better-placed weather: do terrain, urban heat and downscaling improve a national demand forecast?

Andy Moran (Heaviside Analytics) · 17 November 2026 · **Status: parked until the current studies are published (decision, 20 November 2026). Idea draft, third version (gap to NESO, independent station check); not reviewed; nothing frozen, no data read**

For: a reader deciding whether GB demand forecasting needs better-placed weather inputs before it needs regional forecasts.

**Parked, 17 November 2026: waits on `weather_value/PLAN.md`.** That study measures how much a perfect forecast of the same 0.25° weather would cut the regression's error, and in which variable. It does not test finer representation, which is this study's question. It decides whether this study runs: only if temperature carries a meaningful share of the gain, as its decision rule defines.

**The question:** does adding information about calm, clear nights to the weather regression's temperature cut its error on GB national demand?

## 1. Why, and why this way

The weather study showed that information matters: giving the regression honest weather forecasts cut its mean daily error by 34% (`weather_study/RESULTS.md`). Checkpoint 0 showed that, on the same information, a weather regression beat LightGBM with defaults. The next question about information is whether the temperature input itself could be better placed.

Two effects make the national temperature wrong for where people live:
- **Urban heat islands.** Towns are warmer than the countryside around them, most of all at night.
- **Orography.** Valleys and low ground are colder than the smoothed terrain in a weather model, most of all when cold air pools on calm nights.

A third route is a learned downscaler: a small model on top of the global forecast that predicts the detail inside each grid cell. A Hugging Face demonstration over France took AIFS-ENS 2 m temperature from about 28 km to 5.5 km with a 2-million-parameter network trained in about an hour on one GPU. It cut station error over the first two days by 14% in RMSE and 21% in CRPS (Scharfmann et al., 2026). Its authors call it a demonstration, not a robust evaluation, and it did not compare against a lapse-rate height correction.

A follow-on idea proposed a regional study with terrain and urban-heat covariates. This study tests the cheaper question first, on the national target the project already has. If better-placed temperature does not move national error, the regional study loses much of its motivation. If it does, the regional study has a reason to exist.

## 2. One fact that shapes the design

**A fixed correction cannot help the regression.** The weather study's temperature is already weighted by population (UKCEH 1 km residential population, 2021, mapped to the 0.25° grid; `gb-weather-private`, `weather/make_weights.py`). A height correction with a fixed lapse rate, such as 0.65 °C per 100 m, adds the same amount to every half-hour. So does a fixed urban uplift. The regression centres temperature on its training mean in each half-hour slot, so a constant shift changes nothing.

This includes the simple baseline the downscaling demonstration left out. For the national series, a fixed lapse-rate correction is R0 (§4) exactly. So comparing a downscaler with R0 nationally is comparing it with the lapse-rate baseline.

Only the part that varies with the weather can carry new information. Both effects peak in the same conditions: calm, clear nights, when the air near the ground is stable. The Met Office's height correction improved forecasts in stable conditions, but its overall effect on RMS error was limited (Sheridan et al., 2010). This study therefore tests weather-dependent corrections, not fixed ones.

## 3. Non-claims

This study would not establish:
- anything about regional or local demand: the target is GB national demand (INDO);
- anything about live performance: it is a backtest;
- that urban heat or terrain is the cause of any improvement: the arms add weather-dependent terms, and the note would say which term moved the error, not why;
- anything for model classes other than the weather regression, unless an arm is added for them.

## 4. Arms

Every arm is the weather regression, refitted for each target day D on D−366 to D−2, exactly as in the weather study (`regression_weather.py`). Only its temperature terms change.

| Arm | Temperature information | Role |
|---|---|---|
| **R0** | As published: population-weighted temperature, its square, wind, wind chill, solar | Reference |
| **R1** | R0 plus a calm-clear-night term: temperature × a stability index built from forecast wind speed and cloud cover, at night | Data-driven |
| **R2** | R0 with temperature replaced by a physically adjusted temperature: an urban term minus a cold-pool term, each scaled by the stability index, with coefficients taken from published work and not fitted | Physics-based |
| **R3** | R0 with temperature replaced by population-weighted temperature from a learned downscaler at 5.5 km | Learned |

**The stability index** would be fixed before any run. A candidate is the night-time product of low wind and low cloud, in the form the urban-climate and downscaling literatures use. The exact form, and its source, must be opened and checked before the plan is frozen (lesson 23).

**R2's two terms:**
- **Urban:** the urban share of each cell's population, from a land-cover map, times a published urban-heat intensity that rises as wind and cloud fall.
- **Cold pool:** the population-weighted height difference between model terrain and real terrain, times a lapse rate that varies with wind and cloud, after Sheridan et al. (2010).

**R3, the downscaler,** follows Scharfmann et al. (2026), with three changes for GB:
- **Target:** CERRA 2 m temperature at 5.5 km. Coarse input: ERA5 at 0.25°. Statics: fine elevation, height difference from the coarse terrain, land fraction, distance to the sea, position, season and time of day.
- **Training ends 15 March 2024,** the day before the backtest, so the downscaler has seen nothing from the backtest.
- **Applied to the forecasts:** at each target day, the downscaler runs on the same ECMWF run that gave R0 its temperature, then the 5.5 km field is weighted by the same UKCEH population, regridded to CERRA's grid. One member: the ensemble part of the demonstration is not needed for a point forecast.

The demonstration trained on ERA5 and applied the downscaler to a forecast model. R3 does the same, so a mismatch between ERA5 and the ECMWF forecast is part of what it tests.

R1 asks whether the information helps at all. R2 asks whether a physical form of it helps without fitting. If R1 helps and R2 does not, the information is real but the physics needs work. If neither helps, the national forecast does not need it. R3 asks whether a learned downscaler adds anything that a fixed correction does not. A fixed correction is R0 itself, nationally. Unlike a fixed correction, a downscaler varies with time of day and season.

## 5. Data still to obtain

| Need | Source to check | Status |
|---|---|---|
| Cloud cover, history | ERA5 total cloud cover | Not downloaded; `era5_download.py` fetches temperature, wind and solar only |
| Cloud cover, forecasts | ECMWF open data `tcc` | The daily collector fetches it (`prospective/weather/ecmwf_daily.py`); the backtest archive did not (`sources.py` fetches 2t, ssrd, 10u, 10v). The backtest runs would be re-fetched |
| Model terrain height | ERA5 and IFS surface geopotential | To check which the open data provide |
| Real terrain height | A public digital elevation model at 1 km or finer | To choose |
| Urban share | UKCEH Land Cover Map, urban and suburban classes | To check licence and resolution |
| Fine target for R3 | CERRA 2 m temperature, 5.5 km, on a Lambert conformal grid, with orography and land-sea mask (Copernicus Climate Data Store, single levels) | The CDS lists September 1984 to present, updated monthly. Analyses are 3-hourly; forecasts are hourly for steps 1–6. To check: the exact years and fields to download, and whether to train on 3-hourly analyses or hourly short forecasts |
| Station temperatures for the gridded check | Met Office hourly land-surface observations (MIDAS Open, CEDA) | To check licence and coverage, and which stations CERRA assimilated (§6) |
| Compute for R3 | One GPU, a few hours | As in the demonstration |

Every file would be named and hashed, as in the weather study.

## 6. Days, metric and reading

- **Days:** the weather study's 960 backtest days, 16 March 2024 to 31 October 2026, so results compare directly with the weather study and checkpoint 0.
- **Same days, same target, NESO included.** Every arm and NESO's day-ahead forecast are scored on the same days against the same outturn: INDO, as in the weather study. NESO's forecast is complete on every backtest day, so no day is lost to it.
- **Metric:** mean daily error (mean absolute error over each day's half-hours, averaged over days); each arm's ratio to R0.
- **Gap to NESO closed.** Each arm is also reported as the share of R0's error gap to NESO that it closes: (R0's mean daily error − the arm's) ÷ (R0's − NESO's), with a bootstrap interval. The weather study reported weather's effect the same way (Q2). This puts every arm on one scale: a 1% cut in error is small as a ratio, but it can be a visible share of a gap that a forecaster with more information has shown is closable. NESO had more information than any arm, so not all of the gap is weather, and the note says so.
- **Intervals:** moving-block bootstrap over days (blocks of 7, 2,000 draws), 90%, as in the earlier studies.
- **Focus set:** the tenth of days with the highest forecast stability index, chosen from forecasts only (the forecaster's dilemma; Lerch et al., 2017). If the effects exist, they should show most there.
- **Gridded check for R3, before the demand test:** score the downscaled ECMWF temperature against GB stations on the backtest days. Compare it with the interpolated coarse forecast and with a lapse-rate height correction, the baseline the demonstration left out. This says whether the downscaler improves temperature where people live, separately from whether that helps demand. It is descriptive.
- **The station check must be independent of CERRA, or say it is not.** CERRA assimilates 2 m temperature: ECMWF's assessment notes that verification at analysis time is not independent, because the stations used have been assimilated. CERRA's conventional data include SYNOP reports. The backtest days come after the downscaler's training period, but the downscaler learns fine detail from CERRA fields drawn towards assimilated stations. So it can learn each such station's local offset and look better there than it is. Before the check:
  - identify which MIDAS stations report SYNOP or were otherwise assimilated by CERRA;
  - score the check on stations CERRA did not use, if enough exist across GB's terrain and towns;
  - otherwise, label it a non-independent sanity check and do not read a downscaler's gain at those stations as evidence.
- **Reading the two checks together.** If R3 improves temperature at independent stations but closes none of the gap to NESO, better local temperature does not reach national demand, and the gap lies elsewhere. If it closes part of the gap, the temperature input mattered.
- **Reading rule:** as in the tails study. An arm helps or hurts only where its interval excludes 1. No p-values.
- **Power:** before the freeze, a short check of the smallest ratio the design can detect. R1 and R2 differ from R0 by only a few terms, so their errors will be highly correlated and the intervals narrow. The check gives the number.

## 7. Hypotheses, to be fixed before any run

- **H1:** R1's ratio to R0 is below 1 on the focus set.
- **H2:** R2's ratio to R0 is below 1 on the focus set.
- **H3:** R3's ratio to R0 is below 1 over all 960 days. Over all days, not the focus set, because the downscaler corrects every half-hour, not only calm, clear nights. The gridded check may show the downscaler beating the lapse-rate baseline at stations while H3 fails. That would mean better local temperature does not reach national demand.
- **No all-days prediction for R1 and R2:** their effects are confined to calm, clear nights, which are a minority of half-hours. H3 is the only all-days prediction, and it is for R3.

Each hypothesis is equivalent to the arm closing a positive share of the gap to NESO, with an interval wholly above 0, provided NESO's error is below R0's in every bootstrap draw. The script checks that condition and reports it.

Headline templates, in the style of the tails study, would be written for each outcome before any run.

## 8. What has been seen

The regression's backtest errors are published (`weather_study/results/`). No forecaster's error has been computed against cloud cover, stability or terrain, and no arm above has been run.

## 9. Scope and timing

This is a separate study, not part of the standing benchmark, and not a checkpoint. The battery work has priority. A realistic order:
1. Check the data in §5: cloud cover for the backtest runs, CERRA's exact years and fields, and which MIDAS stations CERRA assimilated.
2. Source and open the stability, urban-heat and lapse-rate formulas.
3. Run the power check, then freeze the plan.
4. First run: R0 against R1, the cheapest arm. R2 follows. The full downscaler arm, R3, comes last.

R3 needs no cloud cover. If the cloud data prove hard to get, it could run before R1 and R2.

Each step can stop the study cheaply.

## Sources

- Sheridan, P., Smith, S., Brown, A. and Vosper, S. (2010). A simple height-based correction for temperature downscaling in complex terrain. *Meteorological Applications*. doi:10.1002/met.177.
- Scharfmann, E., Roy Gosthipaty, A. and Rasul, K. (2026). [Do we really need bigger AI weather forecasting models to improve resolution?](https://huggingface.co/blog/EmmaScharfmann/downscaling-a-weather-forecasting-model) Hugging Face blog, 20 October 2026.
- Copernicus Climate Change Service. [Copernicus regional reanalysis for Europe (CERRA)](https://climate.copernicus.eu/copernicus-regional-reanalysis-europe-cerra), and the [CERRA single-levels dataset on the Climate Data Store](https://cds.climate.copernicus.eu/datasets/reanalysis-cerra-single-levels?tab=overview).
- ECMWF. [CERRA: strengths and weaknesses](https://confluence.ecmwf.int/spaces/CKB/pages/488285319/CERRA%2BStrengths%2Band%2Bweaknesses).
- Lerch, S., Thorarinsdottir, T. L., Ravazzolo, F. and Gneiting, T. (2017). Forecaster's dilemma: extreme events and forecast evaluation. *Statistical Science* 32(1), 106–127. doi:10.1214/16-STS588.
- Background on urban heat and electricity demand in UK cities: Antunes De Azevedo (2016), University of Birmingham PhD; Brunel University London PhD on supermarket energy demand in Greater London (bura.brunel.ac.uk/handle/2438/30102). Both are city-level studies of cooling, not national demand.
