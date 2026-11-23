# Imbalance exposure: what were the forecast misses worth at real prices?

Andy Moran (Heaviside Analytics) · 23 November 2026 · **Status: draft, to be frozen at tag `imbalance-cost-plan` before any price is read.** Redrafted from the parked version of 22 November (7b4ffc6) after the asymmetric and arbitrage studies and one review. An exploratory study in two stages (§5).

For: a supplier or trader who wants to know what a better day-ahead demand forecast is worth in money, and which forecaster's misses would have cost least.

**The question.** A price-taking supplier buys its forecast demand ahead of time and settles every miss at the GB imbalance price. Using each forecaster in turn, what would its net imbalance exposure have been, first on the backtest and then on days no model could have seen?

## 1. Why

The asymmetric study asked at what cost ratio two forecasters swap places, without knowing any real ratio. The arbitrage study found, in MW of demand, that Chronos-2 picks a battery's hours better than the regression and adds a little information to NESO's forecast. Neither study used a price. This one does.

**The exposure of one miss.** A supplier buys its forecast *F* ahead of time at a reference price. On the day, demand is *A*, and the gap *A* − *F* is settled at the System Price *SP*. Measured against buying the actual demand at the reference price *MIP*, the miss is worth

**exposure = (*A* − *F*) × (*SP* − *MIP*) × 0.5 h**, in £ per half-hour.

The same formula covers both directions. A shortfall (*A* > *F*) is bought at *SP* instead of *MIP*; a surplus is sold back at *SP*.

**Why it can be negative.** GB settles imbalance at a single System Price. A miss in the same direction as the whole system costs money: a supplier that is short when the system is short pays a high price. A miss against the system earns money. So the study reports **net imbalance exposure**, with gains and losses shown separately, not a "cost".

**Why this is not a fixed cost ratio.** In any one half-hour, a 1 MWh shortfall and a 1 MWh surplus are worth the same amount with opposite signs. Asymmetry appears only across half-hours: if a forecaster's shortfalls tend to fall when the System Price is high, its shortfalls cost more per MWh on average than its surpluses. The study measures that directly (§8, effective ratio) and sets it beside the asymmetric study's break-even ratios.

**What is not new.** Valuing forecast errors at imbalance prices is standard practice for suppliers. No novelty is claimed. What this study adds is narrow: the exposure of fixed day-ahead GB demand forecasts, including foundation models, at open prices, with a live replication.

## 2. What this study shows

- **What each forecaster's misses were worth** to a price-taking supplier whose demand follows the national shape, per GWh of demand served, with gains and losses separately.
- **Whether Chronos-2's exposure was clearly lower or higher than the regression's,** first in the backtest pilot and then on live days.
- **The effective cost of a shortfall against a surplus,** per MWh, for each forecaster, and how it compares with the asymmetric study's break-even ratios.
- **Where the exposure falls:** winter, the coldest tenth of days and cold evenings.
- **A demand-proxy dispatch ranking:** how much of each day's price spread a fixed, demand-based battery rule captures with each forecast (§8). This ranks forecasters under one stated rule. It is not battery earnings.

## 3. What this study does not show

- **A real supplier's bill.** No supplier holds all national demand, and real costs depend on a portfolio's own shape, hedges and trading. National demand error also helps set the System Price, so treating the price as given overstates how well a supplier's misses line up with the system's.
- **The day-ahead auction price.** The reference is Elexon's Market Index Price. Only the Half Hour, One Hour, Two Hour and Four Hour products traded within eight hours of the Submission Deadline carry weight in it; every other product, the day-ahead auction included, carries zero weight (Elexon's 2023 review). So the reference is a near-real-time traded price. A supplier that bought its forecast in the day-ahead auction would face a different spread, which this study cannot measure with open data.
- **Real battery value.** Prices follow demand net of wind, solar and interconnectors. A real battery also depends on its power, capacity, efficiency and state of charge. The dispatch exercise is a ranking under a demand-based rule, nothing more.
- **The value of a forecast to NESO,** whose costs come from balancing actions, not settlement.
- **A pre-registered test.** See §4.

## 4. What is known before this plan

Every result of the earlier studies. The author has not seen GB System Prices or Market Index Prices for the backtest or the live window, and no price has been joined to any forecast in this project.

The predictions (§10) are written before any price is read for this study. The plan is frozen before the data step (§7) runs.

## 5. Two stages

**Stage 1: backtest pilot.** The 960 backtest days, 16 March 2024 to 31 October 2026. Chronos-2's published pretraining data include energy datasets (its technical report, appendix table 6). That does not show it saw GB national demand on these dates, but overlap is credible, so stage 1 is labelled a pilot and carries no money claim.

**Stage 2: live replication.** The days no model could have seen, scored after 31 March 2027 with the same code, unchanged:
- **No-weather forecasts:** made and pushed daily since 5 November 2026 under the frozen prospective plan (`prospective/PLAN.md`), with code, weights and input hashes locked and GitHub's server-side push record as the evidence of timing.
- **Weather forecasts:** made after the window from weather inputs pushed daily since 20 November 2026 (`weather_study/inputs/`), with the weather study's frozen code (`weather_study/PLAN.md` §6.3).
- **NESO's forecast:** fetched afterwards with Elexon's publication timestamps, as in every earlier study.

Only stage 2 can support a statement about money. With about 130 winter days, its intervals will be wide.

## 6. Forecasters, comparisons and days

**Stage 1:** the forecasters of the arbitrage study, loaded the same way (`asymmetric/score.py`, `load_real`, with its hash checks): the weather regression, Chronos-2 (`chronos2_A`), LightGBM V1 and S1, TimesFM 2.5 one day per call, the fixed equal-weight average of Chronos-2 and the regression, and NESO's day-ahead forecast. Chronos-2 with weather but no calendar (`chronos2_weather`) is added from the weather study's forecasts file, under the tails study's hash check, as the bridge described below.

**Stage 2:** the forecasters of stage 1 that exist for live days, configured as in stage 1:
- **The regression with weather:** the weather study's prospective arm, which is the backtest's `regression_weather` (same code, fitted day by day).
- **Chronos-2 with calendar and weather,** as the backtest's `chronos2_A` (the weather study's check E5). The weather study's prospective scoring has no calendar arm, and E5's script (`gb-weather-private/weather/calendar_study.py`) runs only on the 960 backtest days. So a new script, `calendar_live.py`, makes these forecasts with E5's code, settings and pinned weights unchanged, using only the weather and calendar inputs archived before each target day. It is committed and frozen before its first run, and its six-day reproduction check (§12) confirms the code is E5's; it is never used to tune anything.
  - **Issued daily from its first run:** it joins the daily push, so each day's forecast is made after the day's weather inputs are pushed and pushed to GitHub before 00:00 UK time on the target day. A day counts as issued only by GitHub's server-side push record, as in the prospective plan.
  - **Reconstructed before that:** target days from 20 November 2026 to the day before its first issued forecast are made once, after the script is frozen, from the inputs archived for those days, and labelled reconstructed.
  - **Missed days:** a day whose forecast misses its push is reconstructed after the window from its archived inputs and labelled so. No day is dropped for that reason alone.

**Issued or reconstructed.** Freezing a script in advance is a safeguard. Issuing and archiving a forecast before its target day is stronger evidence. The no-weather forecasts, NESO's and Chronos-2's calendar forecasts from the first daily run are issued; the weather study's own weather forecasts, TimesFM's one-day forecasts and the earlier calendar forecasts are reconstructed from inputs archived in advance. The stage 2 note says which is which, plainly, for every forecaster and day, and reports the primary comparison on issued days alone as well as on all days.
- **The equal-weight average** of those two, **TimesFM 2.5 with weather**, one day per call only (`weather_study/CORRECTIONS.md` 1 and 3), and **NESO**.

LightGBM has no live forecasts and is not in stage 2. The no-weather forecasts pushed daily since 5 November are reported descriptively.

**A bridge between configurations.** Chronos-2 with weather but no calendar (`chronos2_weather` in the backtest; the weather study's prospective arm live) is reported in both stages as a descriptive forecaster, so a reader can see how much the calendar matters to the exposure.

**Comparisons.** Primary: Chronos-2 (calendar and weather) against the regression with weather, in each stage. Descriptive: every other forecaster against the regression.

**Days.** A day counts if every forecaster in the comparison and outturn cover all its half-hours, and if its prices pass the checks in §7 on every half-hour; otherwise it is dropped and listed. Days, half-hours and clock changes are handled as in the earlier studies.

**Checked before tagging (23 November 2026):** the weather study's prospective regression is the backtest's `regression_weather`. Its prospective Chronos-2 has weather but no calendar, unlike `chronos2_A`; hence the new script above. Its prospective scoring batches days (`run_weather.py`, rung 1's batch of 64), which is harmless for Chronos-2 and the regression but would reproduce TimesFM 2.5's batching error. That is recorded as `weather_study/CORRECTIONS.md` 3: TimesFM is run one day per call before the live window is scored, and batched results are excluded.

## 7. Data

**Prices, both open, from Elexon:**
- **System Price** per settlement period. The settlement run used is recorded for every period. Stage 1 uses the latest run available at fetch time; stage 2 uses the latest run available when it is scored, and the note says which runs those are.
- **Market Index Price**, built from the Market Index Data of both providers, EPEX and N2EX, as their volume-weighted average.

**Thin trading.** Under the Market Index Definition Statement, a provider's price and volume default to zero when its traded volume falls below the Individual Liquidity Threshold (25 MWh at the 2023 review). A zero there is not a price. A provider with zero volume is left out of the average; a half-hour where both have zero volume has no reference price and is treated as missing. Missing half-hours are counted and listed by month.

**Fetch and check.** A committed script fetches the prices, records SHA-256 hashes in a manifest, lists gaps, defaulted half-hours and settlement runs, and commits the manifest but not the data. It computes no exposure.

**Licence.** The current BMRS data licence and API terms are read before publication, and `ATTRIBUTION.md` is updated with the attribution they require.

## 8. The measures

*A* is outturn and *F* a forecast, in MW; *SP* and *MIP* are in £/MWh. Each half-hour's exposure is *x* = (*A* − *F*) × (*SP* − *MIP*) × 0.5, in £.

**Net exposure (primary).** Each day's net exposure divided by that day's demand in GWh, then the mean over days: £ per GWh of demand served. Dividing by demand means the supplier's share cancels, so no share has to be chosen. Lower is better; it can be negative.

**Losses and gains.** The same, using only half-hours with *x* > 0 (losses) and only those with *x* < 0 (gains). Net exposure is their sum.

**Per MWh of error.** Total net exposure divided by total absolute error in MWh: what a megawatt-hour of miss was worth on average, for each forecaster.

**Effective ratio (descriptive).** For each forecaster, the mean of (*SP* − *MIP*) over its shortfall half-hours, divided by the mean of (*MIP* − *SP*) over its surplus half-hours, each weighted by the size of the miss. This is what a megawatt-hour of shortfall cost, on average, relative to a megawatt-hour of surplus. It is set beside the asymmetric study's break-even ratios, on all days and on cold evenings. Where the denominator is not positive, the ratio is reported as undefined, with both parts shown.

**Demand-proxy dispatch ranking (secondary).** Each day, take the forecast's four lowest and four highest half-hours, as in the arbitrage study. The **captured price spread** is the mean *MIP* in its four highest half-hours minus the mean *MIP* in its four lowest, in £/MWh. It is set beside the same spread for outturn's own picks (a perfect demand forecast) and for the day's four dearest and four cheapest half-hours (perfect price knowledge). A day with a missing price in any of these half-hours is left out of this measure. The result is a ranking under this rule, not battery earnings.

**Intervals and labels.** As in the arbitrage study: the tails study's 7-day moving-block bootstrap over days, 2,000 draws, the same draws for every forecaster. The seed is 20261124 for stage 1 and 20270401 for stage 2 (the prospective plan's scoring seed). Paired comparisons are the forecaster's measure minus the regression's. A difference is **clearly lower** if its 90% interval lies wholly below 0, **clearly higher** if wholly above, and otherwise **not clearly different**. These labels are unadjusted and are not tests.

**Sets.** All days (primary). Descriptive: winter (December to February), the coldest tenth of days (T1, `tails/days.csv`; stage 1 only, as T1 is defined on the backtest), and the cold-evening window of the asymmetric study (16:00 to 19:30 UK time) on all days and on T1.

## 9. Checks before each real run

1. **Reproduction.** Each forecaster's mean daily error matches the arbitrage study's to 0.01 MW (stage 1) or the weather study's prospective figures (stage 2, once published).
2. **Prices.** Every price half-hour matches the manifest's hash; defaulted and missing half-hours are counted; no zero-volume price enters the average.
3. **Arithmetic.** For every forecaster, net exposure equals losses plus gains; exposure is exactly 0 for a perfect forecast (*F* = *A*); doubling every error doubles every exposure.
4. **Synthetic.** On invented prices and forecasts with known answers:
   - a forecaster short exactly when the system price is high has the expected losses and effective ratio;
   - one whose errors are independent of the price spread has net exposure near 0, with an interval containing it;
   - a half-hour where both providers report zero volume is treated as missing, never as a price of 0;
   - the dispatch rule picks the right half-hours, and a perfect-price day captures the full spread;
   - the labels and headlines are right for every combination of labels.
5. **Hashes.** Every file read matches its recorded SHA-256.

## 10. Prediction, written before any price is read

- **Net exposure.** Every forecaster's net exposure is positive: national demand error helps set the System Price, so a price-taker with national-shaped misses tends to miss in the same direction as the system. NESO's is lowest. In stage 1, Chronos-2's is clearly lower than the regression's, roughly in proportion to its smaller error. In stage 2 the two are not clearly different, because the window is short.
- **Effective ratio.** Above 1 for every forecaster, because the System Price spikes further above the market price when the system is short than it falls below it when long. Higher on cold evenings than on all days.
- **Where it falls.** More than half of each forecaster's losses fall in winter.
- **Dispatch ranking.** Every forecaster captures well under the perfect-price spread, because demand picks ignore solar and wind. Chronos-2 captures more than the regression, as in the arbitrage study, but not clearly so.

## 11. Headlines, fixed now

The note and any post lead with these sentences, written by the script by rule (§8).

Stage 1: "In a backtest the foundation models may have seen in training, a price-taking supplier using Chronos-2's day-ahead demand forecast would have had [**clearly lower net imbalance exposure than** / **clearly higher net imbalance exposure than** / **net imbalance exposure not clearly different from**] one using a weather regression ([X] against [Y] £ per GWh of demand)."

Stage 2: "On [n] days no model could have seen, a price-taking supplier using Chronos-2's day-ahead demand forecast would have had [**clearly lower net imbalance exposure than** / **clearly higher net imbalance exposure than** / **net imbalance exposure not clearly different from**] one using a weather regression ([X] against [Y] £ per GWh of demand)."

When stage 2 is reported, its sentence leads and stage 1's follows as the pilot.

## 12. Work

1. **`imbalance_cost/fetch_prices.py`:** fetches and checks the prices for the backtest (§7) and writes the manifest. Committed before it runs; manifest committed after.
2. **`imbalance_cost/score.py`:** reuses the arbitrage study's loading and the tails study's bootstrap, unchanged; runs the checks in §9; computes §8; writes the headline by rule. Committed before it runs, with its synthetic check; outputs after.
3. **`imbalance_cost/RESULTS.md` (stage 1):** labelled a pilot, with the stage 1 headline unchanged.
4. **As soon as the plan is tagged:** `gb-weather-private/weather/calendar_live.py`, which makes Chronos-2's calendar-and-weather forecasts for live days with E5's code and settings unchanged. Committed before it runs, with a check that it reproduces `chronos2_A` on six backtest days to within 1 MW. It then runs daily from the push task, and once to reconstruct the days since 20 November.
5. **After 31 March 2027:** the same scripts, unchanged, fetch the live window's prices and score stage 2. Any change to them is recorded in `REVISIONS.md` before stage 2 runs. The stage 2 note leads with its own headline.

## 13. Timing

Stage 1: about two days once the plan is reviewed and tagged. Stage 2: April 2027, after the weather study's prospective scoring.

## Sources

- Ansari, A. F., Shchur, O., Küken, J. et al. [Chronos-2: from univariate to universal forecasting](https://www.ecb.europa.eu/press/conferences/shared/pdf/20260323_forecasting/Guerron_paper.pdf) (technical report). Appendix table 6 lists the real pretraining datasets, including electricity, solar and wind series. Read 23 November 2026.
- Elexon, [Market Index Definition Statement Review 2023](https://elexon.co.uk/article/market-index-definition-statement-review-2023): the Individual Liquidity Threshold, below which default rules apply; weightings of 1 or 0; the four products with weight 1, traded within eight hours of the Submission Deadline. Read 23 November 2026.
- Elexon, [Consultation on the MIDS review 2023](https://www.elexon.co.uk/consultation/consultation-on-the-market-index-definition-statement-mids-review-2023/): the threshold at 25 MWh; the Market Index Price and Volume defaulting to zero. Read 23 November 2026.
- Elexon, [Imbalance pricing](https://elexon.co.uk/settlement/imbalance-pricing): Market Index Data reflects the price of wholesale electricity in the short-term market. Read 23 November 2026.
- Elexon, [Issue 64 final report](https://assets.elexon.co.uk/wp-content/uploads/sites/11/2016/07/28161831/262_07_Issue-64_Final-Report-v1.0.pdf): Market Index Data comes from two providers, EPEX and N2EX. Read 23 November 2026.
- Elexon, [Market Index Definition Statement Review 2022](https://www.elexon.co.uk/article/market-index-definition-statement-review-2022/): when the Market Index Volume does not meet the threshold, the price and volume default to zero. Read 23 November 2026.
- Elexon, [CP1358 decision paper](https://assets.elexon.co.uk/wp-content/uploads/2012/02/28170754/CP1358_ISG131_decision_paper.pdf) (2011): the day-ahead auction product was added to the statement with zero weighting. Read 23 November 2026. The 2023 review confirms which products now carry weight.
- `asymmetric/RESULTS.md`, `arbitrage/RESULTS.md`, `prospective/PLAN.md` and `weather_study/PLAN.md` for earlier rules and figures.
