# Asymmetric cost: when does a shortfall make Chronos-2 the worse forecaster?

Andy Moran (Heaviside Analytics) · 22 November 2026 · an exploratory sensitivity analysis on committed forecasts

For: a forecaster or trader deciding whether a model that is better on average is worse for them, because their shortfalls cost more than their surpluses.

**What this does not show.**
- **A cost.** The cost ratio *k* is a scenario the reader chooses. No NESO, market or company cost was measured or estimated.
- **Which forecaster is best for a given user.** That depends on the user's *k*, and on whether their costs vary by hour, which this study does not model.
- **The cost of mistiming a peak.** The cold-peak measure scores the size of the daily peak, not when it falls.
- **What Chronos-2 could do if asked for a quantile.** Under a cost ratio *k*, the best point forecast is the *k*/(1 + *k*) quantile. Chronos-2 can produce quantiles, but the saved forecasts hold only its median. At *k* ≠ 1 this study therefore understates what Chronos-2 could offer.
- **Live performance.** The foundation models may have seen these days in training.
- **A pre-registered test.** The predictions were written after earlier results were seen. The labels below come from unadjusted 90% intervals, not formal tests.

## Headline

In a backtest it may have seen in training, Chronos-2 had clearly less cost-weighted error than a weather regression over all half-hours at each tested cost ratio from 0.5 to 10, and, in the size of the daily peak on the coldest tenth of days, not clearly different where a shortfall cost 0.5 to 1.5 times a surplus, and clearly more from 2 to 10.

Over all half-hours, there was no break-even ratio above 0 (Chronos-2 better at every ratio above 0; 96% of bootstrap draws in this case); at cold-day peaks, the break-even ratio was 0.69 (Chronos-2 better below it and worse above; 100% of bootstrap draws in this case; conditional 90% interval 0.38 to 1.53).

`score.py` wrote both sentences by the rules fixed in `PLAN.md` §8, frozen at tag `asymmetric-plan`. "Clearly less" means the 90% interval for the difference lay wholly below zero. The backtest runs from 16 March 2024 to 31 October 2026: 960 days, two winters.

**In plain terms:** across all half-hours, Chronos-2 beat the weather regression whatever a shortfall cost relative to a surplus. It erred less in both directions: it fell short by 405 MW on average against the regression's 459, and overshot by 511 against 556. On the coldest tenth of days the picture reverses for the size of the daily peak. Chronos-2 set the peak too low by 776 MW on average, against the regression's 395. If a shortfall at the cold-day peak costs twice a surplus or more, the regression sized that peak clearly better.

**A finding outside the headline.** The equal-weight average of Chronos-2 and the regression was specified before the run, not fitted. Over all half-hours, it had clearly less weighted error than Chronos-2 at every ratio: 833 MW against 915 at equal costs, 9% less. At cold-day peaks, it also had clearly less than Chronos-2 at every ratio from 1 to 10. Against the regression at cold-day peaks, it was clearly better at 0.5, not clearly different from 1 to 3, and clearly worse at 5 and 10. This result is descriptive and was not one of the headline comparisons. The average was not compared with NESO, whose day-ahead forecast remains the most accurate tested (700 MW).

## The measure

Error is outturn minus forecast, so a positive error is a shortfall. At cost ratio *k*, a shortfall of *e* MW costs *k* × *e* and a surplus of *e* MW costs *e*. At *k* = 1 this is the ordinary absolute error.

Each forecaster's mean weighted error is *k U* + *O*. Here *U* is its mean shortfall and *O* its mean surplus, both averaged as the published mean daily error is: first within each day, then over days. So two numbers per forecaster and set give its error at any *k* (table 3). The break-even ratio is where two such lines cross.

**Sets.**
- **All:** every half-hour on all 960 days. This is a primary set.
- **Cold peaks:** on each of the 96 coldest days by mean forecast temperature (T1 in the tails study), the day's highest outturn half-hour minus the forecaster's highest forecast half-hour. This is the second primary set.
- **Cold evenings:** the eight half-hours from 16:00 to 19:30 UK time on the same 96 days. This set is descriptive.

**Intervals.** The 90% intervals come from a 7-day moving-block bootstrap of the 960 days, with 2,000 draws. Both forecasters in a comparison use the same draws.

## Results

**Table 1. Chronos-2 minus the weather regression, MW** (negative: Chronos-2 had less weighted error)

| *k* | All half-hours | 90% interval | Label | Cold peaks | 90% interval | Label |
|---|---|---|---|---|---|---|
| 0.5 | −72 | −104 to −43 | clearly less | −73 | −218 to 61 | not clearly different |
| 1 | −99 | −133 to −67 | clearly less | +117 | −97 to 336 | not clearly different |
| 1.5 | −126 | −170 to −81 | clearly less | +308 | −6 to 625 | not clearly different |
| 2 | −153 | −210 to −93 | clearly less | +498 | 88 to 923 | clearly more |
| 3 | −206 | −299 to −110 | clearly less | +879 | 253 to 1,522 | clearly more |
| 5 | −314 | −478 to −137 | clearly less | +1,641 | 584 to 2,738 | clearly more |
| 10 | −582 | −935 to −207 | clearly less | +3,546 | 1,458 to 5,790 | clearly more |

The cold evenings follow the cold peaks: not clearly different from 0.5 to 1.5, and clearly more from 2 to 10. Their break-even ratio is 0.72, with a conditional interval of 0.41 to 1.68.

**Table 2. Every comparison** (L: clearly less; M: clearly more; –: not clearly different; for *k* = 0.5, 1, 1.5, 2, 3, 5, 10)

| Comparison | Set | Labels by *k* | Break-even case | *k\** | Draws in case | Conditional 90% interval |
|---|---|---|---|---|---|---|
| Chronos-2 − regression | all | L L L L L L L | better throughout | — | 96% | — |
| | cold peaks | – – – M M M M | crossing, better below | 0.69 | 100% | 0.38 to 1.53 |
| Chronos-2 − V1 | all | L L L L L L L | better throughout | — | 83% | — |
| | cold peaks | – – – M M M M | crossing, better below | 0.47 | 95% | 0.11 to 1.55 |
| TimesFM 2.5 − regression | all | M M M M M M M | worse throughout | — | 100% | — |
| | cold peaks | M M M M M M M | worse throughout | — | 89% | — |
| LightGBM S1 − regression | all | M M M M M M M | worse throughout | — | 57% | — |
| | cold peaks | – M M M M M M | crossing, better below | 0.22 | 89% | none (under 90%) |
| NESO − regression | all | L L L L L L L | better throughout | — | 100% | — |
| | cold peaks | L L L – – – – | crossing, better below | 11.9 | 61% | none (under 90%) |
| Average − regression | all | L L L L L L L | better throughout | — | 100% | — |
| | cold peaks | L – – – – M M | crossing, better below | 1.40 | 100% | 0.82 to 3.63 |
| Average − Chronos-2 | all | L L L L L L L | better throughout | — | 100% | — |
| | cold peaks | – L L L L L L | crossing, better above | 0.24 | 95% | 0.05 to 0.66 |

"Average" is the equal-weight average of Chronos-2 and the regression. Where a case is "better" or "worse throughout", the two lines do not cross at any positive *k*. A conditional interval is given only when at least 90% of draws fall in the same crossing case. Every row, the cold evenings included, is in `results.md`.

**Table 3. Plug in your own ratio: mean shortfall *U* and mean surplus *O*, MW.** A forecaster's mean weighted error at ratio *k* is *k U* + *O*.

| Forecaster | All: *U* | All: *O* | Cold peaks: *U* | Cold peaks: *O* | Cold evenings: *U* | Cold evenings: *O* |
|---|---|---|---|---|---|---|
| Weather regression | 459 | 556 | 395 | 529 | 386 | 588 |
| Chronos-2 | 405 | 511 | 776 | 265 | 730 | 339 |
| LightGBM V1 | 467 | 530 | 512 | 390 | 507 | 441 |
| LightGBM S1 | 500 | 560 | 792 | 443 | 733 | 500 |
| TimesFM 2.5 (one day per call) | 827 | 793 | 1,540 | 679 | 1,567 | 591 |
| Average of Chronos-2 and regression | 366 | 467 | 544 | 320 | 496 | 401 |
| NESO day-ahead | 348 | 353 | 415 | 286 | 452 | 301 |

For example, at *k* = 3 Chronos-2's cold-peak error is 3 × 776 + 265 = 2,593 MW, against the regression's 3 × 395 + 529 = 1,714 MW. These are point figures. Their uncertainty is in tables 1 and 2.

## Direction and consistency (descriptive)

Daily bias is a day's mean of outturn minus forecast; positive means short. The 960 days were split into ten groups of 96 by mean forecast temperature, coldest first.

**Table 4. Mean daily bias by temperature group, MW** (group 1: −1.5 to 4.7 °C; group 10: 18.4 to 25.0 °C)

| Forecaster | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 |
|---|---|---|---|---|---|---|---|---|---|---|
| Weather regression | −178 | −11 | −397 | −145 | 37 | 57 | −165 | −137 | −177 | 143 |
| Chronos-2 | +170 | −170 | −329 | −133 | −218 | −123 | −11 | −122 | −282 | 160 |
| Average | −4 | −91 | −363 | −139 | −91 | −33 | −88 | −129 | −230 | 152 |
| NESO day-ahead | 45 | −91 | −31 | −12 | 8 | 64 | −6 | −4 | −120 | 96 |

Intervals and the other forecasters are in `results.md`. Chronos-2's +170 MW in the coldest group has a 90% interval of −15 to 356, so it is not clearly above zero. Its −170 in group 2 and −329 in group 3 are clearly below zero.

**Table 5. Direction and persistence**

| Forecaster | Mean bias | Slope on temperature, MW/°C (90% interval) | Share of days short | Lag-1 autocorrelation | Short after short |
|---|---|---|---|---|---|
| Weather regression | −97 | +10.8 (−2.8 to 23.6) | 0.45 | 0.42 | 0.62 |
| Chronos-2 | −106 | +1.2 (−10.9 to 13.7) | 0.45 | 0.26 | 0.56 |
| LightGBM V1 | −63 | +2.2 (−10.0 to 14.4) | 0.47 | 0.40 | 0.61 |
| LightGBM S1 | −60 | +0.4 (−17.0 to 16.2) | 0.49 | 0.46 | 0.62 |
| TimesFM 2.5 | +34 | −11.5 (−38.6 to 15.7) | 0.52 | 0.43 | 0.64 |
| Average | −102 | +6.0 (−4.5 to 17.0) | 0.46 | 0.34 | 0.59 |
| NESO day-ahead | −5 | +1.0 (−6.4 to 8.9) | 0.49 | 0.27 | 0.60 |

"Short after short" is the share of short days followed by another short day. Set it beside the share of days short: the gap shows how much the misses cluster. The longest runs, with their dates, are in `results.md`. The regression's longest run of long days was 20 days, from 25 July to 13 August 2025.

**What this shows.** Chronos-2's lean is not a straight-line response to temperature. Its slope is close to zero, but its bias swings from short in the coldest group to clearly long in the next two. A single correction proportional to temperature would not remove it. Every forecaster's daily bias was positively autocorrelated, so misses came in runs. The regression and Chronos-2 both forecast too high on average, by about 100 MW. NESO was within 5 MW of zero.

## The predictions, against the results

These were written before any asymmetric loss was computed (`PLAN.md` §5a, §6).

| Prediction | Result |
|---|---|
| All half-hours: Chronos-2 clearly better at *k* = 1 and 2 | Held |
| All half-hours: break-even above 2, Chronos-2 better below it | Did not hold. There was no crossing: Chronos-2 was better at every ratio (96% of draws) |
| Cold peaks: break-even below 2, possibly below 1 | Held: 0.69. But at *k* = 1 the difference was not clearly different from zero |
| TimesFM 2.5 worse than the regression at every ratio, in both sets | Held |
| The average beats Chronos-2 at cold peaks at every *k* from 1 up | Held: clearly less at each |
| Over all half-hours at *k* = 1, the average within 3% of Chronos-2 | Did not hold: the average was 9% lower |
| Chronos-2's slope negative, with interval below 0 | Did not hold: +1.2 (−10.9 to 13.7) |
| TimesFM 2.5's slope more steeply negative | Not supported: −11.5, but its interval includes 0 |
| The regression's slope near 0 or slightly positive | Held: +10.8 (−2.8 to 23.6) |
| NESO's slope near 0 | Held: +1.0 |
| The average's slope between Chronos-2's and the regression's, closer to 0 than Chronos-2's | Between them, but not closer to 0 |
| Every daily bias positively autocorrelated | Held: 0.26 to 0.46 |

The slope predictions came from the tails study, which found Chronos-2 too high on mild winter days and too low on the coldest days. These results narrow that finding: the lean is concentrated in the coldest tenth of days and does not run across the whole temperature range.

## What this means for a user

- **If your costs are roughly symmetric, or you care about every half-hour,** Chronos-2 was the better of the two at every ratio tested.
- **If you size capacity for cold-day peaks and a shortfall costs about twice a surplus or more,** the regression sized those peaks clearly better here. Between ratios of 0.5 and 1.5 the two were not clearly different.
- **Combining the two looks worth testing.** The fixed 50:50 average beat both over all half-hours and beat Chronos-2 at cold peaks. It is one descriptive result on the same days, not a tested method.
- **Asking Chronos-2 for a higher quantile is the untested option.** A user who fears shortfalls would not use its median. This study cannot say how its two-thirds quantile would score.

## Limits

- The ratio *k* is fixed across all half-hours in a set. Real imbalance costs vary by hour and day.
- T1 has only 96 days, so the cold-peak intervals are wide.
- The labels are unadjusted across 7 ratios, 3 sets and 7 comparisons. Some "clearly" labels near a boundary may not survive a stricter reading.
- Chronos-2, TimesFM 2.5 and the average built from Chronos-2 may have seen these days in training. V1 was chosen on these same days, so its figures are optimistic.

## Reproduce

- **Plan:** `PLAN.md`, frozen at tag `asymmetric-plan`.
- **Scoring:** `score.py` (sha256 190d540a…, commit 15a479a). It reuses the tails study's loader, peak error and bootstrap. It passed its synthetic check (`score_synthetic.json`, commit a3ff952) and its real checks before writing `results.json` and `results.md` (commit 77fe107). At *k* = 1 it reproduced every published mean daily error and both published cold-peak errors.
- **Changes:** every implementation choice is in `REVISIONS.md`.

## Use of AI

I used AI tools in this work: Claude, ChatGPT, Microsoft Copilot, DeepSeek, Kimi and Z.ai. The work is designed so that results are calculated numerically and checked against ground truths, and assumptions are checked against original sources. The scoring script passed synthetic checks with known answers before it ran on real data, and at equal costs it reproduced every published figure.

## Sources

- Gneiting, T. (2011a). [Quantiles as optimal point forecasts](https://doi.org/10.1016/j.ijforecast.2009.12.015). *International Journal of Forecasting* 27(2), 197–207.
- `PLAN.md` §1 for the other prior work; `tails/RESULTS.md`, `lgbm_variants/RESULTS.md` and `checkpoint0/RESULTS.md` for every earlier figure.
