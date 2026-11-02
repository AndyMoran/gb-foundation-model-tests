# Brief 2, revision 6: a ladder from forecast tests to a paid service

Draft · 2 November 2026 · Andy Moran (Heaviside Analytics)

Revision 6 records the decisions taken on 2 November 2026 (Section 7). Revision 5 made the final pre-freeze edits: the re-decision criteria after rung 2, a pivot signal for rung 2, the prospective track named as the primary leakage defence, and a precise statement of what the GridFM repository holds. Revision 4 added the prospective track (Section 3.2). Revision 3 answered a review of revision 2: a named fallback for rung 2's weather data, a sharper account of the audit niche, the Timestral licence gap, and decisions scoped to the next step. Revision 2 had checked every claim against its original source (Section 8). The end point is unchanged: an independent, preregistered audit service for GB battery owners, investors and lenders. Three things change: the second rung is cheaper, the ladder has four rungs instead of five, and the audit's credential is the method, not a model of our own.

## 1. The goal, for whom, and the end point

- **End point.** A paid audit: an independent, preregistered evaluation of whether a client's forecast or optimiser delivers what it claims, on the client's own sites and data.
- **Why there is a gap.** enspired, a battery optimiser, writes that bankable forecasts "are, by nature, pessimistic", that optimiser backtests "cannot be validated", and that only "an assurance service by a credible and well-known independent party" can confirm reported figures.
- **Who fills it today.** enspired's own answer was to have KPMG review its calculation method and issue a limited assurance report. That checks that reported figures were calculated as stated, not whether a forecast is skilful. Judging skill needs forecasting methodology (information sets, leakage, benchmarks, power), which is a research skill rather than an audit one. That is the niche, and why a partnership with assurance firms is plausible: each supplies what the other lacks. "Well-known" is the gap to close, which is why the public benchmark matters.
- **Commercial reality.** Business to business, bespoke and relationship-driven: a handful of engagements, not a subscription. Test willingness to pay before building the full pipeline (Section 6).
- **The credential.** The method: plans frozen before results, validity gates, every number recomputed. An auditor who also owns a competing forecast model has a conflict of interest, so any model built on the ladder is a research result, never a product sold to the same market.

## 2. What is already known (literature search, 30 October and 2 November 2026)

- **Zero-shot is not yet operational.** NREL judged zero-shot errors on ERCOT load, wind and solar "too high for operational use" and found fine-tuning necessary. A Google study found supervised models ahead of TimesFM 2.5 and Chronos by roughly a factor of two on energy data (transformer oil temperature), and noted that common benchmarks may sit in the models' training data.
- **Against naive forecasts, the models win easily:** about 47% better than seasonal naive on ERCOT load.
- **Weather inputs matter, and so does their honesty.** Chronos-2 led when weather covariates were accurate; a conventional model led when realistic forecast errors were added.
- **Prices are mixed.** In Germany, Poland and Spain only TabPFN consistently beat the specialist price models, and accuracy did not always become battery profit. In Belgium, Chronos-2 was about 5% better on day-ahead prices and about 10% worse on imbalance prices.
- **Physics-informed adaptation can help.** GridFM (Sayghe et al., *Energies*, January 2026) freezes a Moirai-MoE backbone, adds trained adapters, a frequency-mixing layer and zonal power-balance constraints, and reports 2.14% load MAPE and 7.8% price MAPE on NYISO, 18.5% and 23.2% better than baselines. It is fine-tuned, not zero-shot; against a fine-tuned baseline its repository reports a 10.1% load improvement; and its constraints need zonal data.
- **The revenue link is shown, rarely.** A Re-Twin and Electricity Maps backtest on German day-ahead prices (January–March 2026, a vendor case study) found that better forecasts raised a battery's revenue from 78% to 87% of the perfect-foresight maximum.
- **Not covered by any study found:** Great Britain; Timestral; preregistration; a comparison with NESO's own forecast; a forecast-to-revenue test on GB batteries.

## 3. The ladder: four rungs

| Rung | Question | What it builds | Go / no-go for the next rung |
| --- | --- | --- | --- |
| **1. Demand, zero-shot** | Can TimesFM 2.5, Timestral or Chronos-2, zero-shot, match NESO's published day-ahead demand forecast? | The GB pipeline, the method applied to energy, the public track record | **Go whatever the result.** Expect a gap; publish it as "here is the gap" |
| **2. Demand, with physics** | Does giving the models the physics NESO itself uses, temperature and embedded solar, as *forecast* inputs close the gap? | The leakage-honest covariate test; a physics-first result | **Go** to rung 3 either way: rung 2 is a research question, not a dependency for prices. **Pivot signal:** if honest forecast weather closes none of the gap, the public message changes from "here is how to close the gap" to "the gap is real, and here is how to measure it"; the audit is unaffected, because its credential is the method, not model performance. **Stretch goal** (Section 3.1) only if a GridFM reproduction succeeds |
| **3. Prices** | Do any of the models beat a standard price model on GB day-ahead and imbalance prices? | Market data and a price benchmark on the series that carry money | **Go** to rung 4 if any model beats the standard model by a margin worth testing for value. **Otherwise stop,** and offer the benchmark as lead generation |
| **4. Value** | Do better price forecasts earn a GB battery more money in a simple, published dispatch backtest? | The forecast-to-revenue link buyers ask about; ties to the battery dispatch project | Decides what is offered: an audit, an edge, or both |

The paid service follows the ladder; it is not a rung. Each rung gets its own short brief and preregistered plan, with a stopping point and a go/no-go rule written before it starts, and at most two review rounds before freezing. **The whole ladder is re-decided after rung 2,** against three questions written down now:

1. **Did rungs 1 and 2 each produce a result worth publishing,** whatever its direction?
2. **Did the buyer conversations (Section 6) name a decision an audit would change** (switching optimiser, lender terms, a board report), and so what rungs 3 and 4 must measure?
3. **Is the prospective track collecting cleanly:** a manifest row for most days, no unexplained gaps, files that open?

Three yeses: rung 3 proceeds as planned. A no on question 2: rungs 3 and 4 are reshaped around what buyers said, or deferred. A no on question 3: fix collection before anything else, because it cannot be recovered later. A no on question 1 alone: publish what there is and re-scope before going on.

### 3.1 The GridFM stretch goal

GridFM is MIT-licensed and its core code is public (about 2,600 lines). Whether it reproduces the paper is unverified. At the latest commit (f6f72fd, 7 January 2026), the README's reproduction steps name `scripts/download_data.py`, `scripts/evaluate.py` and `scripts/generate_figures.py`, but `scripts/` contains only `train.py`; the README loads pretrained weights (`gridfm-base-nyiso`), but no weights are in the repository, and whether they are hosted elsewhere is unknown; and the README's clone address (`GridFM/GridFM`) differs from the repository's (`asayghe1/GridFM`). Hence the one-week time-box. Its power-balance constraints also need zonal demand, generation and flow data, which a single GB national-demand series does not provide. So:

1. First, try to reproduce one NYISO result from the public code, time-boxed to a week.
2. Only if that succeeds, consider a GB version using regional data, as its own brief.

### 3.2 The prospective track, running alongside the ladder

**This track is the project's primary defence against leakage; the backtests are fast, secondary evidence.** A backtest can be checked for leakage; a forecast made before the outcome exists cannot leak at all. So, from November 2026, a daily script saves ECMWF's free open-data forecasts for Great Britain (temperature, solar radiation, wind and cloud, 0–72 hours ahead), with each file's download time and SHA-256 recorded in a manifest that is pushed to a public repository. The manifest is the evidence that each weather forecast existed before the weather it describes.

- **Why now.** ECMWF's open portal keeps only about the last two or three days of forecasts; earlier ones need a paid service agreement. Every day not collected is lost.
- **What it enables.** After a winter of collection, the models in rungs 1 and 2 forecast GB demand day by day using only these saved forecasts, over a period after both TimesFM's and Timestral's release dates. That removes input leakage and training leakage together.
- **How it relates to the ladder.** The backtests (rungs 1 and 2, on archived forecasts from 2024) give fast results; the prospective track later confirms or contradicts them with no leakage. It also becomes the public GB benchmark, updated monthly (Section 4).
- **Its own plan.** Before the first prospective forecast is scored, a short plan fixes the models, benchmarks, period and wording, as for every rung. Collection itself needs no plan: it records weather forecasts, not results.
- **Cost.** A small script run daily on the author's machine, about 1–2 MB a day after cropping to GB.

## 4. Routes to revenue, most to least likely

1. **Independent forecast and optimiser audits.** Bespoke, preregistered, on the client's data; measured against simple and published benchmarks, never against a model we sell.
2. **A public GB forecasting benchmark, updated monthly.** Lead generation, not revenue: it builds the "well-known" part.
3. **A forecast product.** Only if rung 4 shows a real, repeatable edge, and only if it does not compromise the audit's independence. Least likely.

## 5. Constraints

- **Weather-data licences.** ECMWF open data: CC-BY-4.0, commercial use allowed with attribution ("Contains modified Copernicus/ECMWF data" or the wording in ECMWF's Terms of Use). Open-Meteo's commercial terms still to be read before any paid use.
- **Model licences.** TimesFM 2.5 and Chronos-2: Apache 2.0, commercially clean. Timestral: fine for the public rungs (Heaviside Analytics is below the $20 million monthly revenue limit). In paid work it is a different matter: running it inside an audit for a client above the limit may fall outside the licence, which restricts use, not only redistribution. So a buyer may ask why a model in the public benchmark is missing from an audit. The answer: the audit tests the models the client chooses, and includes Timestral only where the client holds a commercial licence from Mistral or Mistral confirms in writing that the use is covered. TimesFM 3.0: non-commercial, not used. GridFM code: MIT.
- **Data licences.** NESO, Elexon, Sheffield Solar PV_Live and weather-data terms for publication and commercial use must be read before each rung.
- **Rung 2's weather forecasts, and the fallback.** Rung 2 needs the weather forecasts that existed the day before, not the weather that happened. Open-Meteo's Previous Runs API archives forecasts at fixed lead times of one to seven days, from January 2024 for the high-resolution models (its documentation, checked 2 November 2026). Its separate Historical Forecast API stitches together the first hours of each run, so it behaves like observed weather and must not be used. The plan is fixed now, in order:
  1. **Primary:** one-day-ahead temperature and solar forecasts from the Previous Runs API, with the test period set to January 2024 onwards. Rung 1 uses the same period, so the two rungs compare like with like.
  2. **Fallback, if the archive proves unusable for GB** (gaps, wrong lead times, or licence): observed weather with forecast-sized errors added, the error size taken from the archive's own forecast-minus-outturn errors where any exist, or from published Met Office verification statistics. Results are then labelled "simulated forecast error", reported as a sensitivity check, not a test of real forecasts.
  3. **If neither is possible:** rung 2 drops weather and tests embedded solar alone, using PV_Live's published forecasts if an archive exists, and its brief says so before freezing.
- **Time.** Four rungs at two to four weeks each: about two to four months.

## 6. Test the end point first, cheaply

The enspired post shows the gap is real, not that anyone will pay this business to fill it. In parallel with rung 1, ask two or three battery owners, optimisers or investors two questions:

1. "What would an independent check of your forecaster or optimiser need to show for you to act on it: switch optimiser, change lender terms, report to your board?"
2. "Would you pay for that, and roughly what is it worth to you?"

The first question matters more. Willingness to pay alone can return "yes, maybe" from everyone; the decision a result would change tells you what the audit must measure, and so what rungs 3 and 4 must test.

## 7. Decisions taken, 2 November 2026

The end point is the audit, with a forecast product considered only if rung 4 shows a real, repeatable edge (Section 4).

1. **Rung 1 models:** TimesFM 2.5, Timestral and Chronos-2.
2. **Test period and windows.** Each model is reported in three columns, so that differences in what each window can show are visible rather than hidden:

   | Column | Window | Label |
   | --- | --- | --- |
   | Full | January 2024 onwards, matching the weather-forecast archive | "Inside possible training data", with perturbation and placebo leakage checks |
   | Clean | From the model's own release date, recorded from its repository history | Reported only where long enough to say something (power stated); expected for TimesFM 2.5 and Chronos-2, not for Timestral (released 15 October 2026) |
   | Prospective | From the start of collection | "Pending" until scored; the definitive column for all three models |

   No headline compares one model's clean column with another's full column.
3. **Rung 2:** forecast-weather covariates with the fallback order in Section 5; GridFM as a one-week reproduction attempt first.
4. **Buyer conversations:** start this week, three conversations, asking first what decision a result would change and only then whether they would pay.

**Prospective track timing, for later claims to be auditable.**

- Collection began on 2 November 2026, with earlier runs recovered from the portal where still available; the manifest is the record of which days exist.
- A day-ahead forecast for day D can be scored once NESO publishes outturn demand for D, so the first targets are scorable within days, but a single month is too short to say much. The first monthly scoreboard appears in December 2026 at the earliest, and its power is stated.
- Timestral was released on 15 October 2026, before collection began. The prospective window is clean for it because it starts after release, but it does not cover Timestral's first weeks, and no claim is made that it does.
- The model weights are pinned at revisions recorded before scoring, so forecasts made later from the saved inputs are equivalent to forecasts made on the day. Saving each model's forecast daily as well, with its own manifest row, would make that equivalence directly checkable; this is considered when the prospective plan is written.

## 8. Evidence check, 2 November 2026

Every claim from the previous revision was checked against its original source.

| Claim | Result | Source |
| --- | --- | --- |
| enspired: bankable forecasts pessimistic; backtests "cannot be validated"; need for an independent assurance service | **Confirmed.** enspired's own remedy was a KPMG limited assurance report on its calculation method | enspired blog, 30 January 2025 |
| Re-Twin backtest: better forecasts changed dispatch and narrowed the gap to perfect foresight | **Confirmed.** A vendor case study: German day-ahead, January–March 2026, 78.4% to 87.4% of perfect foresight | Electricity Maps case study |
| GridFM: 18.5% load and 23.2% price improvement, 67% fewer physically inconsistent predictions | **Confirmed,** with qualifications: fine-tuned, not zero-shot; 10.1% against a fine-tuned baseline in the repository; zonal data needed; reproduction scripts named in the README are not in the repository | Sayghe et al., *Energies* 19(2):357; github.com/asayghe1/GridFM, cloned and inspected at commit f6f72fd |
| Open-Meteo archives day-ahead weather forecasts (added in revision 3) | **Confirmed.** Previous Runs API: fixed lead times of 1–7 days from January 2024 for high-resolution models; the Historical Forecast API is stitched short-lead data and unsuitable | Open-Meteo documentation, read 2 November 2026 |
| ECMWF open data: free 9 km forecasts (added in revision 4) | **Confirmed, with a limit.** Temperature (2t) and solar radiation (ssrd) out to 15 days; 0.1° grid from 20 October 2026, produced from the ~9 km model; CC-BY-4.0, commercial use allowed with attribution. The open portal keeps only about the last 12 runs; the historical archive needs a paid service agreement | ECMWF open-data page, read 2 November 2026 |
| Supervised models "an order of magnitude" better than TimesFM 2.5 and Chronos-Bolt on load | **Not found.** The nearest study shows about a factor of two, on transformer oil temperature. Replaced in Section 2 | Soni, Das and Guduguntla, arXiv 2605.24381 |

An earlier check wrongly called the GridFM forecasting paper "probably confused" with a different project of the same name (a power-flow model, GridFM.org). The paper is real; the error was corrected after the author checked the DOI.

## Sources

- Lipiecki and Weron, arXiv 2609.00089
- Bui et al., arXiv 2605.17045
- Kaljevic, Arzola and Zhang, arXiv 2610.07232
- Za'ter and Hodge, arXiv 2604.22077
- Simeone, arXiv 2602.10848
- Soni, Das and Guduguntla, arXiv 2605.24381
- Sayghe et al., *Energies* 19(2):357, DOI 10.3390/en19020357
- enspired, "Measuring actual battery optimization performance", 30 January 2025
- Electricity Maps, Re-Twin Energy case study
- Open-Meteo, Historical Forecast API and Previous Runs API documentation
- ECMWF, Open data (ecmwf.int/en/forecasts/datasets/open-data)
