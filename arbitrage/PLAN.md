# Arbitrage signal: does a forecast pick the right hours, and does it know what NESO does not?

Andy Moran (Heaviside Analytics) · 23 November 2026 · **Status: draft, to be frozen at tag `arbitrage-plan` before any script runs.** An exploratory study of committed forecasts (§4).

For: a battery operator or trader who wants to know whether a forecast that is better on average could earn more than a weather regression.

**Two questions.**
- **A. Timing.** A battery charges in the cheapest hours and discharges in the dearest. Do a forecaster's lowest and highest half-hours fall on the day's actual lowest and highest?
- **B. Edge.** Prices already reflect NESO's day-ahead forecast. Where a forecaster disagrees with NESO, does outturn move its way?

## 1. Why

Arbitrage rewards right decisions, not small errors. A forecast that is 500 MW too high all day still picks the right hours, because adding a constant does not change which half-hours are lowest. And a right call earns nothing if the market made it too. Value lies only where a forecast disagrees with the market and is right.

Mean absolute error measures neither. This study measures both, in MW of demand and without prices, as a screen. If no forecaster shows a timing advantage or an edge over NESO here, a study with prices is unlikely to find one.

**Prior work.** Pesaran and Timmermann (1992) give a test of whether forecasts predict the direction of change. Harvey, Leybourne and Newbold (1998) test whether one forecast adds information to another, which is called forecast encompassing. Lipiecki and Weron judge foundation models for electricity prices by battery decisions and find that their value depends on the decision. The measures here are not new. What is new is narrow: applying them to fixed day-ahead GB demand forecasts, including foundation models, against NESO's own forecast.

## 2. What this study shows

On the 960 backtest days, in MW of demand:

- **Whether each forecaster picks the right hours** for a two-hour battery that cycles once a day, and whether Chronos-2 does so clearly better or worse than the regression. Bias does not affect this.
- **Whether each forecaster knew something NESO's forecast did not.** A clearly positive gain (§6) means outturn moved its way where it disagreed with NESO.
- **Whether that edge survives** once each forecast is corrected for its own recent bias, using only data available at the 09:30 cut-off.
- **Whether averaging a forecaster with NESO beats NESO alone.**
- **How often each forecaster calls the day-to-day rise or fall,** with and without the weekend effect.
- **Whether a study with prices is worth doing.** No edge here makes one unlikely. An edge here is needed for profit but does not prove it; the parked `imbalance_cost/PLAN.md` would test the money.

Winter and the coldest tenth of days are reported too, as descriptive results.

## 3. What this study does not show

- **Profit.** It uses no prices. Prices follow demand net of wind, solar and interconnectors, among much else, so a demand forecast is one input to a price view.
- **A trading strategy.** It ignores costs, position limits, battery losses and wear, and does not require charging to come before discharging.
- **The whole market's view.** NESO's forecast is one public view. Traders hold others.
- **Live performance.** The foundation models may have seen these days in training. That matters more for a claim about money than for anything published so far.
- **A pre-registered test.** See §4.

## 4. What is known before this plan

The asymmetric study reports every forecaster's mean daily error, bias and cost-weighted error. NESO's forecast had the lowest error (700 MW, against 915 for Chronos-2 and 1,014 for the regression) and a mean bias of −5 MW. Chronos-2 and the regression both forecast about 100 MW too high on average. No timing or disagreement measure has been computed.

The predictions (§8) were written after those results, so they are not blind. Freezing the code and rules first stops them being chosen after the fact, but the study is exploratory.

## 5. Forecasters and days

**Forecasters**, loaded as in the asymmetric study (`asymmetric/score.py`, `load_real`, with its hash checks):
- the weather regression;
- Chronos-2 (`chronos2_A`);
- LightGBM V1 (`lgbm_v1`) and S1 (`lightgbm_s1`);
- TimesFM 2.5, one day per call (`timesfm25_weather_single_day`);
- the equal-weight average of Chronos-2 and the regression, fixed in advance.

NESO's day-ahead forecast (`neso`) is a forecaster in part A and the market's forecast in part B.

**Comparisons.** Primary: Chronos-2 against the regression. Descriptive: each other forecaster against the regression.

**Information.** NESO's forecast is the latest published by 09:30 UK time on the day before. The models' inputs end at 08:30 (`code/common.py`). No forecaster knew more than NESO.

**Days.** All 960 backtest days, 16 March 2024 to 31 October 2026. Each day runs midnight to midnight UK time, with 46, 48 or 50 half-hours matched by UTC start time. Every forecaster has every half-hour; the script checks this again and reports any day dropped.

## 6. The measures

*y* is outturn, *F* a forecaster's forecast and *N* NESO's, all in MW.

**A. Missed spread (primary).** Each day, take the forecaster's four lowest half-hours and its four highest, breaking ties by the earlier start. That is a two-hour battery charging and discharging once at full power.
- **Captured spread:** mean outturn in the four highest, minus mean outturn in the four lowest.
- **Perfect spread:** the same, using outturn's own four highest and four lowest.
- **Missed spread:** perfect minus captured. It cannot be negative.

The measure is the mean missed spread over days; lower is better. Also reported: the **capture share**, total captured over total perfect; and the **hits**, how many of the eight chosen half-hours are among outturn's own eight, averaged over days. Adding a constant to a forecast changes none of these.

**B. Gain (primary).** On each half-hour, the forecaster's **direction** is the sign of *F* − *N*: does it expect more demand than NESO, or less? Its **gain** is that sign times *y* − *N*: how far outturn moved its way, in MW. Where *F* = *N*, the gain is 0. The measure is each day's mean gain, averaged over days. A positive gain means outturn moved towards the forecaster when it disagreed with NESO; any edge needs that. Also reported: the **hit rate**, the share of half-hours with *F* ≠ *N* on which outturn moved the forecaster's way, against 50%.

**B, bias-corrected (secondary).** A forecaster 100 MW above NESO everywhere always bets "more", so its gain mostly reflects NESO's bias. Each forecast, NESO's included, is therefore also scored after subtracting its own recent bias: its mean error, *y* minus forecast, over the 28 days ending two days before the target day. Two days, because the day before is incomplete at the 09:30 cut-off. The first 29 days have no full window and are left out of this measure; the count is reported.

**B, combination (descriptive).** The mean daily error of the half-hour average of each forecaster and NESO, against NESO's own. If the average beats NESO, the forecaster adds information NESO's forecast lacks.

**C. Day-to-day direction (descriptive).** For each pair of consecutive days: does the forecast's change in daily mean demand have the same sign as outturn's? Likewise for the daily peak. Weekends drive most of these changes, so shares are reported for all pairs and for weekday pairs only (Tuesday to Friday against the day before).

**Intervals and labels.** The 90% intervals come from the tails study's 7-day moving-block bootstrap of the 960 days (2,000 draws, `score_tails.boot_idx`), seed 20261123. Every forecaster and measure uses the same draws. Comparisons are paired: the forecaster's measure minus the regression's, draw by draw. A difference is **clearly lower** if its interval lies wholly below 0, **clearly higher** if wholly above, and otherwise **not clearly different**, including when an endpoint is exactly 0. A gain is **clearly positive** or **clearly negative** by the same rule. These labels are unadjusted and are not tests.

**Sets.** Primary: all 960 days. Descriptive: winter (December to February) and the coldest tenth of days (T1, `tails/days.csv`). As in the tails study, set membership is fixed in each draw and repeated days count.

## 7. Checks before the real run

1. **Reproduction.** Each forecaster's mean daily error over the 960 days matches the asymmetric study's figure at *k* = 1 to 0.01 MW, NESO's 700.13 included.
2. **Alignment.** Every forecaster and NESO cover the same days and half-hours; the counts are reported.
3. **Invariance.** Adding a constant to a forecast leaves part A exactly unchanged. A perfect forecast (*F* = *y*) has missed spread 0, capture share 1 and 8 hits. *F* = *N* has gain 0 on every half-hour.
4. **Synthetic.** On invented data with known answers:
   - a forecaster equal to *N* moved part way towards *y* has hit rate 1, and its gain equals NESO's mean absolute error;
   - one moved the other way has minus that gain;
   - one equal to *N* plus independent noise has a gain interval that contains 0;
   - one shifted two half-hours later misses spread the unshifted one captures;
   - one with a constant bias and true information has, after day 29, the same bias-corrected gain as the unbiased one;
   - the bias correction never uses the target day or the day before;
   - the labels and headline are right for every combination of labels.
5. **Hashes.** Every file read matches its recorded SHA-256.

## 8. Prediction, written before any of these measures is computed

- **A.** Every forecaster captures at least 90% of the perfect spread, because demand's daily shape is regular. Chronos-2's missed spread is not clearly different from the regression's. NESO misses least, TimesFM 2.5 most.
- **B.** NESO is the most accurate forecaster here, so where any other disagrees with it, outturn moves towards NESO on average. Every gain is negative, clearly so for the regression, TimesFM 2.5 and S1. Chronos-2's gain is negative but closer to 0 than the regression's, and its hit rate is below 50%. Bias correction moves both gains towards 0 but makes neither clearly positive. Averaging NESO with Chronos-2 lowers NESO's error by no more than 2%.
- **C.** Every forecaster calls the direction of day-to-day change on more than 90% of all pairs, and on fewer of the weekday pairs.

## 9. Headline, fixed now

The note and any post lead with two sentences, written by the script by rule (§6):

"In a backtest it may have seen in training, when choosing a battery's four lowest and four highest half-hours, Chronos-2 missed [**clearly less of each day's demand spread than** / **clearly more of each day's demand spread than** / **an amount of each day's demand spread not clearly different from**] a weather regression ([X] against [Y] MW a day)."

"Where it disagreed with NESO's day-ahead forecast, outturn moved [**clearly towards Chronos-2** / **clearly away from Chronos-2** / **neither clearly towards nor away from Chronos-2**], by [G] MW on average (90% interval [a] to [b]); for the regression the figure was [G'] MW ([a'] to [b'])."

## 10. Work

1. **`arbitrage/score.py`** reuses the asymmetric study's loader and the tails study's bootstrap, unchanged. It runs the checks in §7, computes §6 and writes the headline by rule. It is committed before it runs, with its synthetic check, and its outputs after. It needs only committed files.
2. **`arbitrage/RESULTS.md`** gives what the study does and does not show, the headline unchanged, the tables, and a plain reading for a battery operator or trader, including whether a study with prices is worth doing.

## 11. Timing

A day's work once the plan is reviewed and tagged. It uses only committed forecasts.

## Sources

- Pesaran, M. H. and Timmermann, A. (1992). [A simple nonparametric test of predictive performance](https://econpapers.repec.org/RePEc:bes:jnlbes:v:10:y:1992:i:4:p:561-65). *Journal of Business & Economic Statistics* 10(4), 561–565. Abstract read.
- Harvey, D., Leybourne, S. and Newbold, P. (1998). [Tests for forecast encompassing](https://econpapers.repec.org/RePEc:bes:jnlbes:v:16:y:1998:i:2:p:254-59). *Journal of Business & Economic Statistics* 16(2), 254–259. Abstract read.
- Lipiecki, A. and Weron, R. [Foundation models for electricity price forecasting and battery arbitrage: can they replace market-specific forecasting models?](https://arxiv.org/abs/2609.00089) (arXiv 2609.00089). Abstract read.
- `code/common.py` for NESO's 09:30 cut-off; `asymmetric/RESULTS.md`, `tails/RESULTS.md` and `checkpoint0/RESULTS.md` for earlier figures.
