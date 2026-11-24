# Imbalance exposure, stage 1: what were the forecast misses worth at real prices? (backtest pilot)

Andy Moran (Heaviside Analytics) · 24 November 2026 · **a pilot**: the backtest days may have been in the foundation models' training data, so this note makes no claim about money. The live replication (stage 2) reports in April 2027.

For: a supplier or trader who wants to know what a better day-ahead demand forecast is worth, and which forecaster's misses would have cost least.

**What this study shows.** For a price-taking supplier whose demand follows the national shape, the net value of each forecaster's misses at the GB System Price, measured against Elexon's Market Index Price, in £ per GWh of demand; its losses and gains; what a megawatt-hour of miss was worth; how much more a shortfall cost than a surplus; and a demand-based dispatch ranking.

**What it does not show.**
- **A real supplier's bill.** No supplier holds all national demand, and real costs depend on a portfolio's own shape, hedges and trading. National demand error also helps set the System Price, which a price-taker assumption ignores.
- **The day-ahead auction price.** The reference is a near-real-time traded price: only products traded within eight hours of the Submission Deadline carry weight in it.
- **Battery earnings.** The dispatch figures rank forecasters under one demand-based rule; prices follow demand net of wind and solar.
- **Live performance.** See above.
- **A pre-registered test.** The predictions were written after earlier results were seen, and the labels come from unadjusted 90% intervals.

## Headline

In a backtest the foundation models may have seen in training, a price-taking supplier using Chronos-2's day-ahead demand forecast would have had net imbalance exposure not clearly different from one using a weather regression (75 against 86 £ per GWh of demand).

`score.py` wrote this sentence by the rule fixed in `PLAN.md` §11, frozen at tag `imbalance-cost-plan`. The backtest runs from 16 March 2024 to 31 October 2026; 953 days were scored, and seven were dropped because the Market Index Price was missing for at least one half-hour.

**In plain terms.** Picture a supplier whose demand has the same shape as Great Britain's. On an average day, its forecast misses would have cost it, net, about £75 for every GWh it served that day with Chronos-2, and £86 with the weather regression. Each day counts equally in that average, whatever its demand; it is not total cost divided by total demand, which would give busier days more weight. The difference, about £11 per GWh, is within the noise: the 90% interval runs from Chronos-2 costing £36 less to £12 more.

## The measure

A supplier buys its forecast *F* ahead of time. On the day, demand is *A*, and the gap is settled at the System Price *SP*. Measured against buying the actual demand at the Market Index Price *MIP*, each half-hour's miss is worth (*A* − *F*) × (*SP* − *MIP*) × 0.5 h. A miss in the same direction as the whole system costs money; a miss against it earns money. The net exposure is the sum over a day, divided by that day's demand in GWh, averaged over days.

Prices are open data from Elexon. The Market Index Price is the volume-weighted average of the two providers' prices, leaving out any provider that reported zero volume: under Elexon's rules its price then defaults to zero, which is not a price. EPEX alone set it in 99.7% of half-hours. The System Price had no gaps, and its selling and buying prices were equal in every half-hour.

## Results

**Table 1. Net imbalance exposure over all 953 days, £ per GWh of demand** (positive is a loss)

| Forecaster | Net (90%) | Losses | Gains | £ per MWh of error | Minus regression (90%) |
|---|---|---|---|---|---|
| Chronos-2 | 75 (52 to 102) | 430 | −355 | 1.97 | −11 (−36 to 12), not clearly different |
| Average of Chronos-2 and regression | 81 (60 to 105) | 394 | −313 | 2.35 | −5 (−18 to 6), not clearly different |
| Chronos-2, weather only (bridge) | 83 (55 to 116) | 462 | −379 | 2.12 | −3 (−27 to 20), not clearly different |
| NESO day-ahead | 85 (68 to 105) | 345 | −260 | 3.00 | −1 (−20 to 17), not clearly different |
| Weather regression | 86 (61 to 116) | 471 | −385 | 2.09 | — |
| LightGBM V1 | 93 (67 to 124) | 467 | −374 | 2.33 | +7 (−1 to 14), not clearly different |
| TimesFM 2.5 (one day per call) | 113 (71 to 152) | 736 | −623 | 1.75 | +27 (−12 to 57), not clearly different |
| LightGBM S1 | 135 (88 to 199) | 524 | −389 | 3.40 | +49 (19 to 91), clearly higher |

**A megawatt-hour of miss was worth about £2, net.** In amount, losses and gains largely offset: each forecaster's gross losses are four to six and a half times its net exposure. This note does not show how often a miss cost money rather than earned it, nor whether the offset comes from many small gains or a few large ones; only the amounts were measured. One likely reason for the offset is that a national demand miss lines up only loosely with whether the whole system is short or long, which wind and other surprises largely decide. The mean answers one question, the average net cost; it says nothing about how bad the worst misses were. The cold-evening figures below show why that matters.

**NESO's misses cost the most per megawatt-hour** (£3.00, against about £2 for the others), so its net exposure is no lower than the regression's although its errors are the smallest. One explanation, not tested here: market positions follow NESO's public forecast, so when NESO is wrong the system tends to be wrong the same way, and a miss shared with the market costs more than an independent one. This is the arbitrage study's finding seen from the other side.

**Table 2. Where the exposure falls: net £ per GWh, and the effective ratio** (what a MWh of shortfall cost relative to a MWh of surplus)

| Forecaster | Winter net | Coldest tenth net | Evenings net | Cold evenings net | Effective ratio, all day | Effective ratio, evenings |
|---|---|---|---|---|---|---|
| Weather regression | 65 | 122 | 89 | 271 | 0.87 | 72 |
| Chronos-2 | 65 | 90 | 94 | 346 | 0.86 | 11 |
| Chronos-2, weather only | 115 | 174 | 122 | 634 | 0.93 | 13 |
| Average of Chronos-2 and regression | 65 | 106 | 92 | 308 | 0.83 | 5.9 |
| NESO day-ahead | 75 | 106 | 75 | 145 | 0.89 | 3.8 |
| LightGBM S1 | 213 | 379 | 178 | 911 | 1.57 | 7.9 |

Evenings are 16:00 to 19:30 UK time; their exposure is per GWh of evening demand. The effective ratios' intervals are very wide (for example 1.24 to 92 for the regression on evenings) and should be read for direction only. Every interval is in `results_stage1.md`.

**The cost of running short is concentrated in winter evening peaks.** Over whole days, a megawatt-hour of surplus cost slightly more than one of shortfall (ratios 0.65 to 0.93, except LightGBM S1). In the evening window, a shortfall cost about £5 per MWh and a surplus well under £1. On the coldest evenings shortfalls cost £13 to £53 per MWh. This is the asymmetric study's pattern at real prices: the risk lies in cold-evening peaks, where Chronos-2 sets the peak too low.

**The calendar matters on cold evenings.** Without the calendar, Chronos-2's cold-evening exposure is clearly higher than the regression's (634 against 271 £ per GWh). With it, the difference is not clear (346).

**LightGBM S1 is clearly worse in every set,** most of all on cold evenings (911 against 271).

**Table 3. Demand-proxy dispatch ranking, all days, £/MWh** (a ranking under one rule, not battery earnings)

| | Captured spread (90%) | Minus regression (90%) |
|---|---|---|
| Perfect price knowledge | 70.2 | |
| Perfect demand forecast | 49.3 | |
| NESO day-ahead | 49.5 (46.3 to 53.0) | +1.6 (1.0 to 2.2), clearly higher |
| Chronos-2 | 48.9 (45.8 to 52.4) | +1.0 (0.5 to 1.6), clearly higher |
| Average of Chronos-2 and regression | 48.8 (45.6 to 52.1) | +0.9 (0.6 to 1.2), clearly higher |
| Weather regression | 47.9 (44.8 to 51.3) | — |

Each day the rule takes the forecast's four lowest and four highest demand half-hours and records the gap in market price between them. Every forecaster captures about 70% of what perfect price knowledge would; a perfect demand forecast does no better. The rest is the gap between demand and price that wind and solar open. Within that limit, Chronos-2 picks clearly better hours than the regression, as in the arbitrage study.

## Frequency and tail (exploratory)

*This section was added after the results above were seen, following a review that the mean answers one question, the average net cost, and not how often a forecaster made costly misses or how bad the worst were. Its figures come from `explore.py`, written and committed after the results and before it ran. They are descriptive.*

**How often misses cost money.** Between 46.6% and 47.9% of half-hours were on the costly side and between 43.6% and 45.0% on the earning side, depending on the forecaster. The remaining 8% carried no exposure, because the System Price equalled the market price. Between 53% and 59% of days ended with a net loss. So misses cost slightly more often than they earned. No forecaster was clearly more often on the earning side than the regression; LightGBM S1 was clearly less often. TimesFM 2.5 had clearly fewer net-loss days (52.9% against 57.1%).

**Most of the cost comes from a few half-hours.** For every forecaster, its worst 1% of half-hours carried about a fifth of its gross losses (19% to 25%), and its worst 10% about two-thirds (65% to 68%). The average is built from a small number of expensive moments.

**One day dominates: 8 January 2025, the worst day for every forecaster.** NESO had issued an Electricity Margin Notice the evening before, warning of a 1,700 MW shortfall against its desired margin between 16:00 and 19:00; one consultancy called it the tightest day in the GB market since 2011. On that day:

| Forecaster | Net exposure, £ per GWh | Mean absolute error, MW |
|---|---|---|
| LightGBM S1 | 29,372 | |
| Chronos-2, weather only | 12,006 | |
| LightGBM V1 | 10,631 | |
| Weather regression | 9,048 | 1,650 (forecast 1,647 MW too low on average) |
| TimesFM 2.5 | 8,709 | |
| Average of Chronos-2 and regression | 7,094 | |
| NESO day-ahead | 6,146 | |
| Chronos-2 | 5,141 | 565 |

For each forecaster, that one day cost as much as 60 to 220 average days. This is the asymmetric study's cold-evening risk, at real prices.

**The tail ranks forecasters differently from the mean.** On the mean of each forecaster's worst 5% of days (£ per GWh), against the regression's 1,331:

| Forecaster | Worst 5% of days (90%) | Against the regression |
|---|---|---|
| NESO day-ahead | 1,065 (869 to 1,282) | clearly lower |
| Average of Chronos-2 and regression | 1,209 (943 to 1,514) | clearly lower |
| Chronos-2 | 1,348 (1,073 to 1,652) | not clearly different |
| LightGBM V1 | 1,358 (1,034 to 1,747) | not clearly different |
| Chronos-2, weather only | 1,538 (1,146 to 2,014) | clearly higher |
| LightGBM S1 | 1,948 (1,211 to 3,058) | clearly higher |
| TimesFM 2.5 | 2,213 (1,819 to 2,584) | clearly higher |

NESO's average exposure was no lower than the regression's, but its bad days were clearly less bad. The fixed 50:50 average was the only forecaster built here with a clearly better tail.

**In the most expensive half-hours, staying on the right side is close to a coin flip.** In the top tenth of half-hours by the gap between System Price and market price (at least £40/MWh), every forecaster was on the costly side 51% to 52% of the time, except NESO at 54%, clearly higher than the regression. Those half-hours carried about a third of each forecaster's gross losses. NESO's higher rate fits the interpretation that its misses line up with the system's, because market positions follow its forecast. That remains an interpretation.

**The worst days cluster on unusual calendar days.** Besides 8 January 2025, the ten worst days for most forecasters include clock changes (27 October 2024, 30 March 2025, 29 March 2026, and 24 to 26 October 2026 around that autumn's change) and the Easter weekends of 2024 and 2026. This is not a data artefact: the price timestamps passed their alignment check, and forecast errors themselves were large on those days (the regression's mean error was 1,816 MW on 30 March 2025, against 943 MW on a median day). Unusual calendar days are hard to forecast, and the misses cost money.

**The two averages agree.** Weighting each day equally (the headline measure) or dividing total exposure by total demand gives figures within £6 per GWh of each other for every forecaster (Chronos-2 75 and 70; the regression 86 and 83). The headline does not depend on the choice.

## The predictions, against the results

| Prediction (`PLAN.md` §10) | Result |
|---|---|
| Every forecaster's net exposure positive | Held: 75 to 135 £ per GWh |
| NESO's lowest | Did not hold: Chronos-2's was lowest (75); NESO's was 85 |
| Chronos-2 clearly lower than the regression in stage 1 | Did not hold: not clearly different |
| Effective ratio above 1 for every forecaster | Did not hold over whole days (0.65 to 0.93, except S1's 1.57) |
| Effective ratio higher on cold evenings than on all days | Held where defined: 3.2 to 23 on the coldest evenings, against 0.65 to 1.57 over whole days. Undefined for the regression, V1 and NESO, whose surpluses on those evenings earned money on balance |
| More than half of each forecaster's losses in winter | Did not hold: 19% to 26% (measured by `explore.py`, added later). Winter's 180 days are 19% of the 953, so losses were not concentrated in winter overall, although cold evenings were expensive per GWh |
| Every forecaster captures well under the perfect-price spread | Held: about 70% |
| Chronos-2 captures more than the regression, but not clearly | Did not hold: clearly more (+1.0 £/MWh) |

## What this means

- **For a supplier, on this evidence, the choice between Chronos-2 and the regression is not worth much money on average.** The difference is small and unclear. The larger risk is in cold winter evenings, where shortfalls are expensive.
- **Smaller errors do not mean lower exposure, but they may mean smaller disasters.** What matters on average is whether a forecaster's misses line up with the system's: NESO's errors are the smallest and its average exposure is no lower. In the tail, NESO and the 50:50 average had clearly less bad worst days than the regression.
- **The average hides where the money goes.** About two-thirds of gross losses came from each forecaster's worst tenth of half-hours, and one tight day, 8 January 2025, cost each forecaster as much as 60 to 220 average days. A supplier choosing a forecaster should look at the tail, not only the mean.
- **Stage 2 decides whether any of this holds on days no model could have seen.** It runs on the live window from November 2026 to March 2027, including Chronos-2 calendar forecasts issued daily since 24 November.

## Limits

- **The price-taker assumption.** National demand error is part of what sets the System Price, so a supplier holding all of it would move the price. The figures are per GWh so that a small supplier can scale them, but a small supplier's own errors will line up with the system less than the national error does.
- **The reference price.** A supplier buying in the day-ahead auction faces a different spread.
- **The settlement run** behind each System Price cannot be named from the open data; each price's creation time is recorded instead.
- **Training data.** Chronos-2's published pretraining data include energy datasets. That does not show it saw GB demand on these days, but overlap is credible.
- **Seven days dropped** for missing market prices (13 April 2024; 27 to 29 June 2025; 27 July 2026; 11 and 12 September 2026).

## Reproduce

- **Plan:** `PLAN.md`, frozen at tag `imbalance-cost-plan` (f0678fa).
- **Prices:** `fetch_prices.py` (cda8165) fetched and checked them; the manifest (ceeacf0) records every file's hash and every count.
- **Scoring:** `score.py` (fa794fa). It passed its synthetic check (`score_synthetic.json`, 4a52801) and its real checks before writing `results_stage1.json` and `results_stage1.md` (058f043). Every forecaster's mean daily error reproduced the arbitrage study's exactly.
- **Frequency and tail:** `explore.py` (2c4c748), added after the results and committed before it ran; its synthetic check (bfb5ca8) passed, and its day-weighted means reproduced `score.py`'s. Its outputs are `explore_results.json` and `explore_results.md` (b5dd652).
- **Changes:** every implementation choice is in `REVISIONS.md` (items 1 to 15), including a code review of `explore.py` that changed no figure (item 15).

## Use of AI

I used AI tools in this work: Claude, ChatGPT, Microsoft Copilot, DeepSeek, Kimi and Z.ai. The work is designed so that results are calculated numerically and checked against ground truths, and assumptions are checked against original sources. The scoring script passed synthetic checks with known answers before it ran on real data.

## Sources

- Elexon, [Market Index Definition Statement Review 2023](https://elexon.co.uk/article/market-index-definition-statement-review-2023), and [Review 2022](https://www.elexon.co.uk/article/market-index-definition-statement-review-2022/): the liquidity threshold, the default to zero, and the products that carry weight.
- Elexon, [Imbalance pricing](https://elexon.co.uk/settlement/imbalance-pricing).
- Elexon Insights API: [system prices](https://data.elexon.co.uk/bmrs/api/v1/balancing/settlement/system-prices/2025-01-15) and [market index data](https://data.elexon.co.uk/bmrs/api/v1/balancing/pricing/market-index?from=2025-01-15T00:00Z&to=2025-01-15T02:00Z) (example requests). Contains BMRS data © Elexon Limited copyright and database right.
- NESO, [What happened with margins on 8 January?](https://www.neso.energy/news/what-happened-margins-8-january); Smartest Energy, [Cold snap sees margin notice issued](https://smartestenergy.com/en_GB/insights/the-informer/cold-snap-sees-margin-notice-issued).
- Ansari, A. F. et al. [Chronos-2: from univariate to universal forecasting](https://www.ecb.europa.eu/press/conferences/shared/pdf/20260323_forecasting/Guerron_paper.pdf), appendix table 6.
- `PLAN.md` for the other sources; `asymmetric/RESULTS.md` and `arbitrage/RESULTS.md` for earlier figures.
