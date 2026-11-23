# Arbitrage signal: does a forecast pick the right hours, and does it know what NESO does not?

Andy Moran (Heaviside Analytics) · 23 November 2026 · an exploratory study of committed forecasts

For: a battery operator or trader who wants to know whether a forecast that is better on average could earn more than a weather regression.

**What this study shows.** Measured in MW of demand on 960 days: how well each forecaster picks a battery's hours; whether, where it disagreed with NESO's day-ahead forecast, outturn moved its way; whether averaging it with NESO beats NESO; and how often it calls the day-to-day rise or fall.

**What it does not show.**
- **Profit.** It uses no prices. Prices follow demand net of wind, solar and interconnectors, among much else.
- **A trading strategy.** It ignores costs, position limits, and battery losses and wear.
- **The whole market's view.** NESO's forecast is one public view.
- **Live performance.** The foundation models may have seen these days in training. That matters more for a claim about money than for any earlier result.
- **A pre-registered test.** The predictions were written after earlier results were seen, and the labels come from unadjusted 90% intervals.

## Headline

In a backtest it may have seen in training, when choosing a battery's four lowest and four highest half-hours, Chronos-2 missed clearly less of each day's demand spread than a weather regression (219 against 409 MW a day). Where it disagreed with NESO's day-ahead forecast, outturn moved clearly towards Chronos-2, by 272.4 MW on average (90% interval 245.4 to 299.0); for the regression the figure was 261.7 MW (237.4 to 284.7).

`score.py` wrote both sentences by the rules fixed in `PLAN.md` §9, frozen at tag `arbitrage-plan`. The backtest runs from 16 March 2024 to 31 October 2026.

**Read the second sentence with care.** Every forecaster had a clearly positive gain against NESO, the regression included, and the gain does not separate Chronos-2 from the regression (difference +10.6 MW, interval −12.7 to 33.5). The test turned out to be easy to pass (below). The stronger test of information NESO lacks is the combination, and on that Chronos-2 passes and the regression does not.

**In plain terms:**
- **Timing.** Chronos-2 picked a battery's hours clearly better than the regression, and on the point figures better than NESO, though the two were not compared directly. Its picks missed 219 MW of each day's spread, against 409 for the regression and 255 for NESO.
- **Information beyond NESO.** Averaging Chronos-2 with NESO's forecast cut NESO's error by 3%, from 700 to 679 MW, clearly. Averaging the regression with NESO did not help (704 MW).
- **Not money.** These are demand figures. Whether they are worth anything depends on prices, which this study does not use.

## Results

### A. Timing: picking the battery's hours

Each day, take the forecast's four lowest and four highest half-hours. The **missed spread** is how much smaller the outturn gap between those hours was than the gap between outturn's own four lowest and four highest. Lower is better. Bias does not affect it.

| Forecaster | Missed spread, MW a day (90%) | Capture share | Hits of 8 | Minus regression (90%) |
|---|---|---|---|---|
| Chronos-2 | 219 (192 to 247) | 0.982 | 6.5 | −190 (−227 to −159), clearly lower |
| Average of Chronos-2 and regression | 239 (212 to 270) | 0.980 | 6.4 | −170 (−199 to −145), clearly lower |
| NESO day-ahead | 255 (225 to 289) | 0.979 | 6.4 | −154 (−195 to −120), clearly lower |
| LightGBM S1 | 387 (352 to 427) | 0.968 | 6.1 | −22 (−58 to 10), not clearly different |
| Weather regression | 409 (370 to 457) | 0.966 | 6.1 | — |
| LightGBM V1 | 440 (401 to 484) | 0.963 | 6.0 | +31 (7 to 54), clearly higher |
| TimesFM 2.5 (one day per call) | 532 (463 to 606) | 0.955 | 6.0 | +123 (52 to 192), clearly higher |

Every forecaster captured at least 95% of the perfect spread. The differences lie in the last few per cent, and they are mostly outside winter. In winter, Chronos-2 missed 98 MW a day against the regression's 133, still clearly less. On the coldest tenth of days the two were not clearly different (110 against 119).

### B. Edge over NESO

**The gain.** On each half-hour where a forecaster disagreed with NESO, how far did outturn move its way? The mean is positive if outturn tended to move towards the forecaster.

| Forecaster | Gain, MW (90%) | Hit rate | Gain after bias correction, MW (90%) | Minus regression, raw (90%) |
|---|---|---|---|---|
| Average of Chronos-2 and regression | 297 (272 to 321) | 0.640 | 303 (277 to 330) | +36 (24 to 48), clearly higher |
| Chronos-2 | 272 (245 to 299) | 0.628 | 278 (251 to 307) | +11 (−13 to 34), not clearly different |
| Weather regression | 262 (237 to 285) | 0.619 | 262 (236 to 286) | — |
| LightGBM V1 | 257 (232 to 281) | 0.616 | 261 (235 to 287) | −4 (−13 to 4), not clearly different |
| LightGBM S1 | 227 (202 to 251) | 0.605 | 232 (206 to 257) | −35 (−49 to −21), clearly lower |
| TimesFM 2.5 (one day per call) | 105 (78 to 132) | 0.557 | 94 (66 to 120) | −156 (−190 to −125), clearly lower |

Every gain is clearly positive, even TimesFM 2.5's, though it is far less accurate than NESO. Removing each forecast's recent bias changes little.

**Why the test is easy to pass.** Suppose a forecaster's errors are independent of NESO's. Whenever NESO overshoots, the forecaster is likely to sit below NESO, and outturn then moves its way. So any forecaster that sometimes misses where NESO does not wins this bet more than half the time, however inaccurate it is. Only a forecaster whose errors simply copy NESO's, plus noise, scores zero (the synthetic check confirms this). A positive gain is therefore necessary for an edge but says little on its own. The comparison between forecasters is more telling. On that, the fixed 50:50 average beat the regression; Chronos-2 and V1 were not clearly different from it.

**The combination.** A stricter test: does averaging a forecaster with NESO beat NESO alone?

| Forecaster averaged with NESO | Mean daily error, MW | Minus NESO alone (700 MW), 90% | Ratio |
|---|---|---|---|
| Average of Chronos-2 and regression | 645 | −55 (−69 to −39), clearly lower | 0.922 |
| Chronos-2 | 679 | −21 (−38 to −3), clearly lower | 0.970 |
| LightGBM V1 | 702 | +2 (−13 to 18), not clearly different | 1.003 |
| Weather regression | 704 | +3 (−12 to 19), not clearly different | 1.005 |
| LightGBM S1 | 734 | +34 (17 to 52), clearly higher | 1.048 |
| TimesFM 2.5 (one day per call) | 979 | +279 (250 to 311), clearly higher | 1.399 |

On this test only Chronos-2 and the Chronos-2/regression average add information NESO's forecast lacks. In winter and on the coldest tenth of days, only the average still clearly beats NESO (9% lower in both).

### C. Day-to-day direction

The share of consecutive-day pairs on which the forecast's change in daily mean demand had the same sign as outturn's:

| Forecaster | All pairs (90%) | Weekday pairs (90%) |
|---|---|---|
| NESO day-ahead | 0.873 (0.855 to 0.890) | 0.830 (0.803 to 0.856) |
| LightGBM V1 | 0.847 (0.828 to 0.864) | 0.797 (0.770 to 0.825) |
| Weather regression | 0.836 (0.818 to 0.854) | 0.790 (0.763 to 0.816) |
| Average of Chronos-2 and regression | 0.836 (0.817 to 0.854) | 0.794 (0.766 to 0.820) |
| Chronos-2 | 0.806 (0.784 to 0.826) | 0.737 (0.705 to 0.769) |
| LightGBM S1 | 0.799 (0.777 to 0.821) | 0.752 (0.719 to 0.785) |
| TimesFM 2.5 (one day per call) | 0.671 (0.647 to 0.695) | 0.553 (0.517 to 0.588) |

NESO called the direction most often. Chronos-2 called the change in daily mean less often than the regression, but the change in daily peak slightly more often (0.785 against 0.767). The tables for winter and the coldest days, and for the daily peak, are in `results.md`.

## The predictions, against the results

| Prediction (`PLAN.md` §8) | Result |
|---|---|
| Every forecaster captures at least 90% of the perfect spread | Held: 95.5% to 98.2% |
| Chronos-2's missed spread not clearly different from the regression's | Did not hold: clearly lower (219 against 409) |
| NESO misses least, TimesFM 2.5 most | Half held: TimesFM 2.5 missed most, but Chronos-2 and the average missed less than NESO on the point figures |
| Every gain negative; Chronos-2's hit rate below 50% | Did not hold: every gain clearly positive; Chronos-2's hit rate 0.628 |
| Bias correction makes no gain clearly positive | Did not hold: every gain was already clearly positive |
| Averaging NESO with Chronos-2 lowers NESO's error by no more than 2% | Did not hold: 3.0%, clearly |
| More than 90% of day-to-day directions right; fewer on weekdays | Half held: 67% to 87%, and fewer on weekdays for every forecaster |

The gain prediction rested on a mistake. It assumed that because NESO is more accurate, outturn would side with NESO when the two disagree. But the direction of a disagreement depends on both forecasters' errors. When NESO is wrong, any forecaster that does not share its error tends to be on the right side.

## What this means for a battery operator or trader

- **For picking hours,** Chronos-2 had the lowest missed spread of any forecaster here, NESO included, on the point figures. On the coldest tenth of days it was not clearly better than the regression.
- **For an edge over the market's public forecast,** Chronos-2 adds a little information to NESO's forecast (3%), and the fixed average of Chronos-2 and the regression adds more (8%). The regression on its own adds none.
- **A study with prices now looks worth doing.** The timing advantage and the combination result are both necessary for a demand-based edge, and both appeared. Whether they survive prices, net demand and costs is the question for the parked `imbalance_cost/PLAN.md`. Training-data leakage is the first thing that study must address, because a model that saw these days could look clairvoyant.

## Limits

- Demand is not price, and two hours a day at full power is a simple battery.
- The foundation models may have seen these days in training; a prospective test would settle it.
- The labels are unadjusted across many forecasters, sets and measures.
- The predictions were written after earlier results, and several were wrong in ways that favour Chronos-2. Read the favourable results with that in mind.

## Reproduce

- **Plan:** `PLAN.md`, frozen at tag `arbitrage-plan`.
- **Scoring:** `score.py` (commit 000879c). It reuses the asymmetric study's loader and the tails study's bootstrap. It passed its synthetic check (`score_synthetic.json`, commit 6d2ddc7) and its real checks before writing `results.json` and `results.md` (commit fe866ce). Its mean daily errors reproduced the asymmetric study's to 0.01 MW.
- **Changes:** every implementation choice, including the correction to the plan's bias-correction sign, is in `REVISIONS.md`.

## Use of AI

I used AI tools in this work: Claude, ChatGPT, Microsoft Copilot, DeepSeek, Kimi and Z.ai. The work is designed so that results are calculated numerically and checked against ground truths, and assumptions are checked against original sources. The scoring script passed synthetic checks with known answers before it ran on real data.

## Sources

- Pesaran, M. H. and Timmermann, A. (1992). [A simple nonparametric test of predictive performance](https://econpapers.repec.org/RePEc:bes:jnlbes:v:10:y:1992:i:4:p:561-65). *Journal of Business & Economic Statistics* 10(4), 561–565.
- Harvey, D., Leybourne, S. and Newbold, P. (1998). [Tests for forecast encompassing](https://econpapers.repec.org/RePEc:bes:jnlbes:v:16:y:1998:i:2:p:254-59). *Journal of Business & Economic Statistics* 16(2), 254–259.
- `PLAN.md` for the other prior work; `asymmetric/RESULTS.md` and `checkpoint0/RESULTS.md` for earlier figures.
