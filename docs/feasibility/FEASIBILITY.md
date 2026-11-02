# Rung 1 feasibility check: GB day-ahead demand

2 November 2026 · Andy Moran (Heaviside Analytics)

The study: do zero-shot forecasting models (TimesFM 2.5, Timestral, Chronos-2) forecast GB national electricity demand a day ahead better than seasonal naive, a simple regression and NESO's own forecast, and by enough to matter? This note checks, before any plan is written, whether the data can support that comparison honestly. Part 1 was checked online from published documentation. Part 2 must be confirmed by downloading the data (`feas_check.py`).

## Part 1. What the documentation shows

### NESO's day-ahead forecast: three possible sources

| Source | Resolution | Coverage | Publication time recorded? | Verdict |
| --- | --- | --- | --- | --- |
| NESO, "Historic Day Ahead Demand Forecasts" | Four cardinal points a day (overnight minimum, daytime peak, daytime minimum, evening peak), not half-hourly | 2018 onwards | Yes (`FORECAST_TIMESTAMP`); a few were recovered from emails and carry later timestamps | Not suitable as the main baseline: not half-hourly |
| NESO, "Day Ahead Half Hourly Demand Forecast Performance" | Half-hourly | April 2021 onwards, updated monthly | Not stated. Described as forecasts "as published via BMRS", with outturn, TRIAD adjustments (which "may be revised") and percentage errors | A useful cross-check, not the baseline: the issue time is unknown |
| Elexon Insights API, `/forecast/demand/day-ahead` | Half-hourly (settlement periods) | To be confirmed (Part 2, check A) | Yes: every row has `publishTime`. The `/evolution` endpoint returns the forecast's changes over time for a given settlement period; `/history` returns everything published at one time | **The candidate baseline.** It can show what was published, when, and for which periods: the three conditions set for using NESO as a baseline |

The Elexon field to use is `nationalDemand`: per the API specification it excludes station load, pumped storage pumping and interconnector demand. `transmissionSystemDemand` includes them.

### Outturn, and matching definitions

- NESO's Historic Demand Data gives half-hourly **ND** (national demand), defined as metered generation excluding station load, pumped storage pumping and interconnector exports. NESO states it is "equivalent to INDO and the National Demand Forecast on BM Reports". So ND outturn and Elexon's `nationalDemand` forecast are defined the same way, which is the matching pair. TSD, which adds station load, pumped storage and exports, must not be mixed with it.
- ND is metered **transmission** generation. Embedded (distribution-connected) wind and solar reduce it, so ND falls on sunny afternoons. This matters for interpreting errors, not for the comparison: every model forecasts the same series.
- **Open question: initial or revised?** NESO's page calls ND equivalent to INDO (the *initial* outturn) but does not say whether its file is ever revised. Part 2, check B, compares the two for the same periods. This is the energy version of the macro vintage question: score against the outturn as first published, or as later revised, fixed in advance.

### Licences

- **NESO Open Data Licence v1.0:** publication, adaptation and commercial use allowed; attribution "Supported by National Energy SO Open Data"; no implied endorsement. Applies to the day-ahead forecast and forecast-performance datasets. The Historic Day Ahead and Historic Demand Data pages did not state a licence; confirm at download that they sit under the same licence.
- **Elexon BMRS Open Data Licence:** publication, adaptation and commercial use allowed; attribution "Contains BMRS data © Elexon Limited copyright and database right [year]"; no implied endorsement; sub-licences must carry the same attribution.

Neither blocks a public study or later paid work.

### Model release dates, from repository histories

| Model | Evidence | Date |
| --- | --- | --- |
| TimesFM 2.5 | First commit of its model code in `google-research/timesfm` | 11 September 2025 |
| Chronos-2 | Commit "Add Chronos-2 (#319)" in `amazon-science/chronos-forecasting` | 20 October 2025 |
| Timestral | Commit "Timestral release" in `mistralai/timestral` | 15 October 2026 |

These are the dates the code appeared publicly; the weights may have appeared on Hugging Face within days, and the training data stop earlier still. For the "clean" column, a window starting after these dates is conservative. Approximate clean windows to the end of October 2026: TimesFM 2.5, about 13 months; Chronos-2, about 12 months; Timestral, about 2 weeks (so its clean result comes from the prospective track).

### Implications for the plan

1. **NESO can be a baseline,** if check A shows the Elexon history reaches back over the test period and records each publication's time. Otherwise the pre-stated rule applies: two baselines only.
2. **The forecast origin can be defined by publication time.** For each target day D, NESO's forecast is the last one published before a fixed issue time on day D−1, and the models may use only outturn published before that same moment. Check A shows when NESO publishes, which fixes the issue time.
3. **The outturn vintage is decided by check B,** before any plan is frozen.

## Part 2. Results by download, 2 November 2026

Run on the author's machine: `feas_check.py` (19:31 UTC) and `feas_check2.py` (19:39 UTC). Outputs: `feas_check_output.txt`, `feas_check2_output.txt`.

| Check | Result | Consequence |
| --- | --- | --- |
| **A. Elexon forecast history** | Every publication is recorded, with `publishTime`, back to at least January 2024. The first day-ahead forecast for day D appears at about 08:45 UK time on D−1 (08:45 UTC in January, 07:45 UTC in October), then about 11:45, then every half hour. A few publications are blank. | **NESO passes as a baseline.** What was published, when, and for which periods can all be established. |
| **B. NESO ND against INDO** | NESO's Historic Demand Data ND exceeds Elexon's INDO by about 95 MW on average and matches it in none of 96 half-hours, despite NESO calling them equivalent. | ND is a later or differently processed series. Using it as model input would be a small leak. |
| **C. NESO forecast-performance file** | Half-hourly, April 2021 to 2 November 2026, 97,985 rows, with `Publish_Datetime`, forecast, outturn and errors. | A cross-check on forecast values. |
| **D. Which outturn NESO scores against** | The performance file's outturn equals INDO in all 144 half-hours checked, and differs from ND by about 95 MW. | **Score against INDO.** It is NESO's own target and was known at the time. |
| **E. INDO publication** | Published once per half-hour; never republished on the three days checked. Recorded lag is exactly 0 minutes for every half-hour, so `publishTime` is evidently set to the period's end, not the arrival time. | INDO is not revised. Its true arrival delay cannot be measured from this field, so a one-hour buffer is used (below). |
| **F. Issue times in the performance file** | 2,042 target days, each with one publish time on D−1 and no missing half-hours. Local times swing between 08:45 and 10:45 with the clock change (2021–24) and shift to 09:33–11:03 in 2025–26, unlike Elexon's consistent 08:45. | The performance file's timestamps look mislabelled by time zone. **Elexon's `publishTime` is the authoritative record of when a forecast was issued**; the performance file is a cross-check on values only. |

**Definition of "a day ahead", fixed by these results:**

- **Issue time:** 09:00 UK local time on day D−1.
- **NESO's forecast:** for each half-hour of D, the latest Elexon day-ahead publication before the issue time (normally the 08:45 issue). A blank value is replaced by that half-hour's most recent earlier publication.
- **Model inputs:** INDO for half-hours that ended at or before 08:00 UK time on D−1 (a one-hour buffer for the unmeasured arrival delay).
- **Targets:** every half-hour of day D (48, or 46 or 50 on clock-change days), scored against INDO.

## Part 3. Which forecast issue, and the weights' licences (2 November 2026, 19:50 UTC)

**G. Which Elexon publication NESO's performance file records.** Six sample days (January and July 2024, January and July 2025, July and October 2026), four half-hours each:

- For daytime and evening half-hours (SP18, SP30, SP36), the file's forecast equals the Elexon publication of **08:45 UK time on D−1** in all 18 cases.
- For an early-morning half-hour (SP6), the file's value matches the **09:16 update on D−1** (or an earlier publication carried unchanged to it) in 2025–26, and no Elexon publication exactly in 2024 (27,611 MW against 27,617 MW at 09:15). The 08:45 issue does not include the early-morning half-hours of D; they come from the half-hourly updates.
- The file's `Publish_Datetime` (08:45Z in January, 09:45Z in July, 08:33Z and 09:33Z in 2026) does not match Elexon's times consistently, confirming that Elexon's `publishTime` is the record to use.

**Consequence: issue time 09:30 UK local time on D−1.** NESO's forecast is, for each half-hour of D, the latest Elexon publication at or before 09:30. That reproduces NESO's own recorded day-ahead forecast in all daytime cases checked and in most early-morning ones. The models and the regression use INDO for half-hours ending at or before 08:30, the same one-hour buffer. The plan's validity gate checks the reconstructed NESO forecast against the performance file and lists every mismatch.

**H. Weights on Hugging Face.**

| Model | Licence tag | Revision | Repository created | Public release | Post-release window starts |
| --- | --- | --- | --- | --- | --- |
| TimesFM 2.5 | apache-2.0 | `1d952420…` (the revision pinned in the TimesFM extension) | 2 September 2025 | 15 September 2025 (README: "TimesFM 2.5 is out!") | 15 September 2025 |
| Chronos-2 | apache-2.0 | `29ec3766…` | 30 October 2025 | 20 October 2025 (README) | 30 October 2025, the later date |
| Timestral-209M | other (Mistral's Modified MIT, read 29 October 2026) | `9874d252…` | 14 October 2026 | 15 October 2026 | 15 October 2026 |

Each window starts at the later of the public announcement and the weights' repository creation. A post-release window shows only that the model was published before the period; it does not show that the training data excluded GB demand.

## Sources

- NESO Data Portal: Day Ahead Demand Forecast; Historic Day Ahead Demand Forecasts; Day Ahead Half Hourly Demand Forecast Performance; Historic Demand Data 2024; NESO Open Licence.
- Elexon: Insights Solution API specification (demand forecast endpoints); Copyright: Licence to use BMRS open data.
- GitHub commit histories of google-research/timesfm, amazon-science/chronos-forecasting and mistralai/timestral, read 2 November 2026.
