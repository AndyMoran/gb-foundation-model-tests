# Asymmetric cost: when does a shortfall make Chronos-2 the worse forecaster?

Andy Moran (Heaviside Analytics) · 22 November 2026 · **Status: draft, to be frozen at tag `asymmetric-plan` before any script runs.** An exploratory sensitivity study on committed forecasts (§3).

For: a forecaster or trader deciding whether a model that is better on average is worse for them, because their shortfalls cost more than their surpluses.

**The question.** Chronos-2 has the lowest mean daily error of the forecasters tested, including on the coldest days, but it set the daily peak too low on cold days (`tails/RESULTS.md`). If a shortfall costs *k* times a surplus, at which *k* does Chronos-2 stop beating the weather regression: over all half-hours, and in the size of the daily peak on the coldest days?

## 1. Why

Mean absolute error charges a shortfall and a surplus of the same size equally. For many users they do not cost the same: being short on a cold evening is usually dearer than being long. Rather than guess one cost ratio, this study scores the forecasts at a range of ratios. A reader picks the ratio that fits their position and reads off which forecaster is better.

**Prior work, and what is not new.** The loss and the idea are standard. Under asymmetric piecewise-linear loss the optimal point forecast is a quantile (Gneiting 2011a), and the scoring function should match the task (Gneiting 2011b). Christoffersen and Diebold (1996) solved prediction problems under asymmetric loss with piecewise-linear approximations and folded model selection into the same loss. In load forecasting, cost-oriented work trains models on asymmetric loss: Wu et al. (2021) report daily cost reductions of 42–57% against a standard support vector regression, depending on the cost ratio, and Zhang, Wang and Hug propose a general cost-oriented framework. Lipiecki and Weron evaluate foundation models for electricity prices on decision outcomes, including battery operation, and find their value depends on the decision problem. No novelty is claimed for the loss, the break-even idea or decision-based evaluation. What this study adds is narrow: break-even ratios across a grid of costs, for fixed day-ahead GB demand forecasts including a foundation model, over all half-hours and at cold-day peaks.

The weighted error is the asymmetric piecewise-linear loss used to evaluate quantile forecasts: under it, the best point forecast is a quantile, the *k*/(1 + *k*) quantile, so *k* = 2 corresponds to the two-thirds quantile (Gneiting 2011a). The forecasts here were not issued as quantiles, so scoring them this way does not make them quantile forecasts. *k* is used only as a cost scenario for comparing fixed forecasts. No new forecast is made.

## 2. What this study does not show

- **A cost.** *k* is a ratio a reader chooses, the same for every half-hour in a set. It is not a measured NESO, market or company cost, and none is estimated.
- **Which forecaster is best for a given user.** That depends on the user's *k*, and on whether their costs vary by hour, which this study does not model.
- **The cost of mistiming a peak.** The cold-peak measure (§4) scores the size of the daily peak, not when it falls.
- **Live performance.** The foundation models may have seen these days in training.
- **A pre-registered test.** See §3.

## 3. What is known before this plan

Every forecaster's mean daily error on all 960 days and on the tails study's sets, its bias, and its daily peak error on those sets. On the coldest tenth of days (T1), Chronos-2's mean daily error was 968 MW against the regression's 1,025, and its daily peak error +511 MW against the regression's −134. No asymmetric loss has been computed for any forecaster.

The prediction (§6) was written after seeing those results, so it is not blind. Freezing the code and rules before the asymmetric loss is computed guards against choosing them after, but the study is an exploratory sensitivity analysis, not a pre-registered test.

## 4. Forecasters and sets

**Forecasters:** the tails study's saved forecasts, read through its loader with its hash checks (`tails/PLAN.md` §4), and the LightGBM variants' V1 (`lgbm_variants/forecasts.csv`, checked against `forecasts.json`).
- **Primary:** Chronos-2 (`chronos2_A`) against the weather regression.
- **Secondary:** Chronos-2 against V1, the best LightGBM variant. V1's forecasts exist, so this runs whether or not checkpoint 1 does.
- **Descriptive:** TimesFM 2.5 one day per call, LightGBM S1, and NESO's day-ahead forecast, each against the regression.

**Three sets, each chosen without outturn.** Error is outturn minus forecast; positive is a shortfall.
- **All (primary):** every scored half-hour on the 960 backtest days.
- **Cold peaks (primary):** the **daily peak-magnitude error** on each T1 day, the coldest tenth of days by mean forecast temperature (`tails/days.csv`): the day's highest outturn half-hour minus the forecaster's highest forecast half-hour, wherever each falls. This is one derived number per day, not a half-hour error. It scores whether the size of the peak was right, which matters for capacity. A forecast whose highest half-hour is too high scores as a surplus even if its peak came at the wrong time; the measure says nothing about the cost of mistiming.
- **Cold evenings (descriptive):** the eight half-hours starting at 16:00, 16:30, … 19:30 UK local time (Europe/London), both ends included, on each T1 day. Clocks change overnight, so every such day has all eight. A fixed window, so its half-hours are not chosen by outturn, and it scores errors at the times peaks usually fall. Measuring the error at each day's actual peak half-hour would choose by outcome within the day, the problem the tails study avoided (`tails/PLAN.md` §5), so it is not used.

**Which days count.** Half-hours are indexed by start time in UTC; "local" times and day boundaries are Europe/London. A day is scored for a comparison only if both forecasters have:
- **all and cold peaks:** every half-hour of the local day (46, 48 or 50), as in the tails study (`score_tails.per_day`);
- **cold evenings:** all eight half-hours of the window.

In the backtest, every forecaster named in §4, NESO included, has every half-hour on all 960 days, and V1 has none missing. So no day is dropped, and each comparison's days are the published days. The script checks this and reports any day dropped.

**T1 is fixed.** It is the 96 days in `tails/days.csv`, never recomputed. In each bootstrap draw, a resampled day-slot counts towards a cold set if it is a T1 day scored for that comparison, with repeats counted, as the tails study does (`score_tails.region`).

## 5. The measure

**Weighted loss.** For a cost ratio *k* ≥ 0, an error *e* costs *k* × *e* if *e* > 0 and −*e* otherwise. At *k* = 1 this is the absolute error.

**Averaging, as the published error.** For the all and cold-evening sets: each day's mean weighted loss over its own half-hours (46, 48 or 50), then the unweighted mean over the scored days. That is the estimator of the published mean daily error (`score_tails.per_day`; `checkpoint0/score.daily`), so at *k* = 1 it reproduces it exactly, clock-change days included. For cold peaks: the mean over the T1 days of each day's weighted peak error.

**The main result: the paired difference at each ratio.** For each set and each *k* in {0.5, 1, 1.5, 2, 3, 5, 10}: Chronos-2's mean weighted loss minus the reference's, in MW, with a 90% interval: the 5th and 95th percentiles of the paired difference over the bootstrap draws, as the tails study's intervals. A difference is labelled **clearly less** (Chronos-2 better) only if the interval's upper end is below 0, and **clearly more** only if its lower end is above 0. An endpoint exactly at 0 means **not clearly different**. These are labels from unadjusted 90% intervals, not formal tests: there is no correction for seven ratios and three sets. The point difference is linear in *k*, but whether an interval excludes 0 need not change only once along the grid, so labels are read ratio by ratio.

**Secondary: the break-even ratio.** Each forecaster's mean weighted loss is *k U* + *O*, where *U* is its mean shortfall and *O* its mean surplus, both averaged as above. Two forecasters are equal at

*k\** = (*O*_ref − *O*_Chronos) / (*U*_Chronos − *U*_ref).

The cases, for *k* > 0 (shortfalls cost something):
1. **Crossing, better below:** *k\** > 0 and Chronos-2 falls short more (*U*_Chronos > *U*_ref). Better below *k\**, worse above.
2. **Crossing, better above:** *k\** > 0 and Chronos-2 falls short less. Worse below *k\**, better above.
3. **Better throughout:** no crossing at any *k* > 0, Chronos-2 lower. This covers *k\** < 0, *U* equal with *O*_Chronos < *O*_ref, and the boundary *k\** = 0 (*O* equal, *U*_Chronos < *U*_ref), where the two are equal only at *k* = 0.
4. **Worse throughout:** the mirror of case 3.
5. **Identical:** *U* and *O* both equal.

**Equality has a tolerance.** Two means count as equal if they differ by at most ε = 10⁻⁶ MW, far below any reported figure. So *U* is equal if |*U*_Chronos − *U*_ref| ≤ ε, and likewise *O*. A crossing case needs *U* and *O* both unequal, with *k\** > 0; if the denominator is within ε of zero, the case is 3, 4 or 5, decided by *O*. A *k\** of 0, or one whose numerator is within ε of zero, belongs to case 3 or 4, never to a crossing case. Each bootstrap draw is assigned by the same rule.

**Uncertainty for the break-even ratio.** The share of bootstrap draws in each of the five cases is always reported. If the point estimate is a crossing case (1 or 2) and at least 90% of draws fall in that same case, a 90% interval for *k\** is also given. It is conditional: the 5th and 95th percentiles of *k\** over those same-case draws only. Otherwise no interval is given.

**Bootstrap:** the tails study's 7-day moving-block bootstrap of the 960 days (2,000 draws, seed 20261122), with each set taken within each draw as the tails study takes its sets, and the same draws for both forecasters in each comparison.

## 6. Prediction, written before any asymmetric loss is computed

**Over all half-hours,** Chronos-2 is clearly better than the regression at *k* = 1 and 2, and its break-even ratio is above 2 (case 1). **At cold-day peaks,** its break-even ratio is below 2, and possibly below 1, meaning it is already level or worse there when the two costs are equal. TimesFM 2.5 is worse than the regression at every ratio in both sets.

## 7. Checks before the real run

1. **Reproduction, on the published days.** Over all half-hours, at *k* = 1, each forecaster's mean weighted loss must equal its published mean daily error at the precision published: `checkpoint0/results.json` stores one decimal place, so the two must agree when rounded to it. Over cold peaks, the published figure is the signed mean peak error on T1 (`tails/results.json`, four decimal places), so *U* − *O* must agree with it when rounded to four places; and *U* + *O* must equal the mean absolute peak error computed directly from `score_tails.per_day`, to 0.01 MW. Before any asymmetric loss is computed, a check on the backtest found all 960 days scored for every forecaster, and these means reproduced: regression 1,014.399 MW (published 1,014.4), Chronos-2 915.527 (915.5), LightGBM S1 1,060.606 (1,060.6); T1 signed peak errors −133.9076 and +510.6032.
2. **Alignment.** Both forecasters in each comparison have the same scored days and half-hours, matched by UTC start time; the counts are reported.
3. **Linearity.** For each forecaster and set, the mean weighted loss at every *k* must equal *k U* + *O* computed directly, to 0.01 MW.
4. **Synthetic.** On invented forecasts with known shortfalls and surpluses, the script must recover each of the five cases in §5, including the *k\** = 0 and *k\** < 0 boundaries, the right *k\**, the right case shares when every draw is the same, an interval endpoint exactly at 0 labelled not clearly different, means within ε treated as equal and just outside it as unequal, a grid whose labels change more than once, and the right headline.
5. **Hashes.** Every file read is checked against its recorded SHA-256.

## 8. Headline, fixed now

The note and any post lead with one sentence, written by the script by rule from the paired differences (§5), for the two primary sets:

"In a backtest it may have seen in training, Chronos-2 had [**clearly less** / **clearly more** / **not clearly different**] cost-weighted error than a weather regression over all half-hours at each tested cost ratio from 0.5 to 10, [**…**]."

Where the label changes across the ratios, the sentence lists them instead: the script groups consecutive ratios with the same label, in order of *k*, for example "clearly less where a shortfall cost 0.5 to 2 times a surplus, and not clearly different from 3 to 10". It does the same for the cold-peak set in a second clause: "… and in the size of the daily peak on the coldest tenth of days …". The break-even ratios and their case shares follow in the next sentence.

## 9. Work

1. **`asymmetric/score.py`:** reuses the tails study's loader, peak-error and bootstrap functions, imported unchanged. Runs checks §7, then computes §5 and writes the headline by rule. Committed before it runs, with its synthetic check; outputs after. It needs only committed files, so it can run anywhere.
2. **`asymmetric/RESULTS.md`:** what it does not show; the headline unchanged; the tables of paired differences; the break-even ratios and shares; and a plain reading for a reader who wants to plug in their own *k*. Its language stays exploratory: "clearly less" is an interval label, and nothing "confirms" or is "proven".

## 10. Timing

A day's work once the plan is reviewed and tagged. No deadline: it uses only committed forecasts.

## Sources

- Gneiting, T. (2011a). [Quantiles as optimal point forecasts](https://doi.org/10.1016/j.ijforecast.2009.12.015). *International Journal of Forecasting* 27(2), 197–207. The asymmetric piecewise-linear loss and quantiles as its optimal point forecasts. Bibliographic record and abstract read; full text behind a paywall.
- Gneiting, T. (2011b). [Making and evaluating point forecasts](https://arxiv.org/abs/0912.0902) (arXiv 0912.0902). On matching the scoring function to the forecasting task.
- Christoffersen, P. F. and Diebold, F. X. (1996). [Further results on forecasting and model selection under asymmetric loss](https://econpapers.repec.org/RePEc:jae:japmet:v:11:y:1996:i:5:p:561-71). *Journal of Applied Econometrics* 11(5), 561–571. Abstract read.
- Wu, J., Wang, Y.-G., Tian, Y.-C., Burrage, K. and Cao, T. (2021). [Support vector regression with asymmetric loss for optimal electric load forecasting](https://doi.org/10.1016/j.energy.2021.119969). *Energy* 223, 119969. Abstract read.
- Zhang, J., Wang, Y. and Hug, G. [Cost-oriented load forecasting](https://arxiv.org/abs/2107.01861) (arXiv 2107.01861). Abstract read.
- Lipiecki, A. and Weron, R. [Foundation models for electricity price forecasting and battery arbitrage: can they replace market-specific forecasting models?](https://arxiv.org/abs/2609.00089) (arXiv 2609.00089). Abstract read.
- `tails/PLAN.md`, `tails/RESULTS.md`, `lgbm_variants/RESULTS.md` and `checkpoint0/RESULTS.md` for every earlier rule and figure.
