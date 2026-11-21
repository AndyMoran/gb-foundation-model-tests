# Context novelty 2: does a year of history remove Chronos-2's novelty penalty?

Andy Moran (Heaviside Analytics) · 21 November 2026 · **Status: parked.** Written before any new forecast exists, to fix the design and the prediction while they are fresh. Not tagged. To be reviewed, finished and tagged only after the LightGBM variants study is published.

For: a forecaster deciding whether giving a foundation model more history, or the right history, would protect it on cold days that are new to it.

**The question.** Context novelty found that Chronos-2 under-forecast the daily peak, relative to a weather regression, by 1,241 MW more on cold days colder than its eight-week context than on matched cold days that were not (`context_novelty/RESULTS.md`). LightGBM, which novelty should not touch, showed about half that gap, so the study could not say how much of the penalty comes from the short context. This study changes only the context's length and asks whether Chronos-2's peak error improves most on the days the longer context makes ordinary.

## 1. Why this design

**A longer context changes some novel days and not others.** `context_novelty/context_check.py`, using weather only, found:
- **At 24 weeks** (8,192 half-hours, Chronos-2's limit at half-hourly resolution), no novel cold day stops being novel. Twenty-four weeks back from November or January reaches only the summer.
- **At about 49 weeks** (8,192 hours), the 14 novel cold days split cleanly:
  - **7 stop being novel**, all in mid-November (19–21 November 2024; 17–20 November 2025). A year of history includes the previous winter's colder days.
  - **7 stay novel**, all in January (8–10 January 2025; 3–6 January 2026). They are colder than anything in the past year.

**That split is a built-in control.** If the short context causes the penalty, a year of history should help Chronos-2 on the November days and not on the January days. Both groups change context in the same way, with the same model and reference, so the comparison does not rest on LightGBM.

**Resolution is held fixed.** Chronos-2's limit is 8,192 steps ([model card](https://huggingface.co/autogluon/chronos-2/blob/main/README.md)), so a year of context means hourly data. Hourly data change Chronos-2's forecasts on every day, and an hourly peak is lower than a half-hourly one. So both arms are hourly, and only the context length differs:
- **H8:** hourly, 1,344 hours (eight weeks): the original context, at hourly resolution.
- **H49:** hourly, 8,192 hours (about 49 weeks).

Each day is compared with itself across the two arms. The day's own difficulty, and the regression's luck on it, cancel.

## 2. What this study will not show

- **Live performance.** Chronos-2 may have seen these days in training. That does not stop a comparison of two context lengths on the same days, but it limits what the result says about days the model has never seen.
- **Half-hourly performance.** Both arms are hourly; their peak errors are not comparable with `context_novelty`'s.
- **A general result.** Seven days in each group, from two cold spells each, is a pilot. It can show a direction, not settle the question.
- **Whether retrieval works.** Retrieval would choose which history to show the model. This study only lengthens it (§8 notes the retrieval version).

## 3. What is known before this plan

Every result in `context_novelty`, including which days are novel at 8, 24 and 49 weeks (`context_check.csv`). No forecast has been made with an hourly or a longer context. The prediction (§6) was formed after seeing those results.

## 4. Forecasts

**Chronos-2 only,** with the same weights, covariates and settings as `chronos2_A`, forecasting one day per call, in both arms:
- **Target:** INDO, as hourly means of its two half-hours.
- **Covariates:** the adjusted national temperature, wind and solar, as hourly means, built for each arm's context exactly as the weather study builds them: ECMWF for D−10 to D−1 and the target day, ERA5 shifted onto ECMWF's scale before that (decision 13). `context_check.py` already builds the 49-week temperature this way.
- **Days:** every T1 day (96), so that the controls are ordinary cold days.
- **Scored hourly.** Outturn is averaged to hours in the same way, and every error is computed on hours (§6). No hourly forecast is compared with a half-hourly outturn.

The weather regression is not re-run: each day is compared with itself, so it cancels.

## 5. Day classes, fixed now from `context_check.csv`

| Class | Definition | Days |
|---|---|---|
| **A: novel only to a short context** | In T1; novel at 8 weeks; not novel at 49 weeks | 7 (November) |
| **B: novel to any context** | In T1; novel at 49 weeks | 7 (January) |
| **C: not novel** | In T1; not novel at 8 weeks | 82 (the pool of controls) |

**Each class A and class B day is matched to one class C day,** by `context_novelty`'s rule, using weather only and before any forecast: mean forecast temperature within 1.0 °C, calendar month within one month, nearest first in date order, ties to the nearer month then the earlier date, no control used twice. A and B draw from one pool, A first. Paired forecasts cancel each day's own difficulty, but not differences in how context length affects different kinds of day; matching on season and cold reduces that. Unmatched days are listed and reported one by one, not averaged. `context_novelty` could not match the three coldest January days, so class B may keep few pairs.

## 6. Outcome and prediction

**Per day:** the change in Chronos-2's daily peak error from H8 to H49, in MW (H49 minus H8). The peak error is the day's highest hourly-mean outturn minus Chronos-2's highest hourly forecast. Negative means the longer context brought the forecast peak closer to the outturn peak.

**Per pair:** the novel day's change minus its control's. **The comparisons:**
- **A:** the mean over class A's pairs. Did the longer context help more on days it made ordinary than on matched ordinary cold days?
- **B:** the mean over class B's pairs. Did it help on days that stayed novel?

**Prediction, written before any forecast:** class A's mean pair difference is negative, and class B's is near zero. That is the pattern a context-length cause would leave. If class A's is near zero, the context is not the main cause of the penalty, at least at this length.

**Reading.** Two cold spells per class are too few for a bootstrap interval to support inference. So the result rests on what can be seen directly:
- **every pair's change, listed one by one;**
- **each cold spell's mean;**
- **whether the direction is the same in both spells of a class.**

A 90% interval from resampling spells is shown only as a rough sensitivity summary, labelled as such. The result is a directional pilot: **informative** if class A's effect is large and has the same sign in both November spells while class B's is not; **marginal** if it is small, or driven by one spell. "Large" will be fixed when the plan is finished, from the 250 MW used in `context_novelty`, before any forecast is made.

## 7. Checks before any forecast

1. **The hourly H8 arm is not the scored forecast.** Report H8's hourly mean daily error on class C beside `chronos2_A`'s averaged to hours, so that the cost of hourly resolution is visible.
2. **Covariates match the weather study's.** For every day, the last 1,344 hours of H49's covariates equal H8's, and H8's equal the half-hourly inputs averaged to hours.
3. **No look-ahead.** Every covariate value was public before 09:30 on D−1, as the weather study's check.
4. **Call mode.** One day per call; each day's forecast does not depend on another day.
5. **Synthetic.** On invented data where demand responds to cold only below a threshold the short context never reaches, H49 must improve on the novel days and not on the others.

## 8. Not yet decided

- **The retrieval version.** Instead of a longer context, give Chronos-2 the previous winter as a second, related series alongside the eight weeks, using its ability to learn across a group of series. This is closer to the retrieval idea raised by Muhammed Asker. Before it becomes an arm, check Chronos-2's documentation for how series in a group must be aligned in time. That check comes first when the plan is unparked.
- **Whether to include TimesFM 2.5,** whose context limit and covariate handling differ.
- **What counts as "large"** (§6).

## 9. Work, when unparked

1. Finish this plan (§8), review it, tag it `context-novelty-2-plan`. The review of 21 November is already reflected: scoring on hours, matched controls, and spell-level reading in place of intervals.
2. Build the hourly inputs for both arms, with checks 2 and 3, committed before they run.
3. Forecast all T1 days in both arms (Chronos-2 takes about 2 seconds a day), with checks 1, 4 and 5.
4. Score by rule; write the note.

## Sources

- `context_novelty/PLAN.md`, `RESULTS.md`, `REVISIONS.md` (items 22–23) and `context_check.md`.
- Chronos-2 model card: [autogluon/chronos-2](https://huggingface.co/autogluon/chronos-2/blob/main/README.md) (maximum context 8,192).
