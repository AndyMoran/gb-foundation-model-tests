# Context novelty: does Chronos-2 fail when tomorrow is colder than its context?

Andy Moran (Heaviside Analytics) · draft, 20 November 2026 · a backtest study, descriptive

For: a forecaster who wants to know whether a foundation model's bad cold days can be seen coming the day before.

**What this does not show.**
- **Live performance.** The foundation models may have seen these days in training.
- **That novelty causes the penalty.** The study compares matched days; it changes nothing. LightGBM, which novelty should not affect, also did worse on novel days (below).
- **A blind test.** The hypothesis was written after the tails study had shown Chronos-2 under-forecasting cold-day peaks.
- **The extremes or the whole cold tail.** The comparison covers 10 matched pairs. Four novel days could not be matched; they include the three coldest days in T1.
- **Prices, other series or other context lengths.** It covers GB national demand (INDO), a day ahead, with an eight-week context.

## Headline

In a backtest it may have seen in training, Chronos-2 under-forecast the daily peak, relative to a weather regression, by 1,241 MW more on cold days colder than its eight-week context than on matched cold days that were not (90% interval 589–1,765, above the 250 MW threshold set in advance).

The comparison rests on 10 pairs (5 in winter 2024-25 and 5 in winter 2025-26) in 4 cold spells. It does not estimate the difference for the 4 novel days that could not be matched (10 January 2025, 20 November 2025, 4 January 2026, 5 January 2026), which include the coldest days, or for the full cold tail.

The plan's rules chose these sentences, and the scoring script wrote them before anyone read the tables (`PLAN.md` §7–8; `REVISIONS.md` items 12 and 17–18).

**In short: novel cold days were associated with a much larger Chronos-2 disadvantage on these matched days, but this backtest cannot yet say how much of it is due to the eight-week context.** The interval clears the 250 MW threshold and the 500 MW sensitivity threshold, and Δ stays above 1,000 MW when any one of the four spells is left out. The four unmatched days, which include the coldest, are outside the estimate.

**LightGBM did worse on novel days too, by about half as much.** LightGBM learns from a year of training days, not an eight-week context, so novelty as defined here should not affect it. Yet its Δ was 618 MW (90% interval 147–1,184). That suggests some of the difference may come from the days themselves, or from how well the regression happens to do on them. Two readings fit:
- **The reference may do unusually well on these days.** Every Δ is measured against the regression. On the 30 novel days of all seasons, the regression over-forecast demand: its bias was −346 MW (−578 to −96).
- **Novel days may be hard for other reasons.** Six of the ten novel days in the pairs fall in mid-November, in the first cold spell of each winter.

Either way, on these pairs Chronos-2 fell further behind the regression on novel days than LightGBM did.

## What was compared

**The question.** A foundation model does not learn how demand responds to weather from a training year. It infers that from the history it receives with each forecast: here eight weeks, 2,688 half-hours. An early cold spell can be colder than anything in those eight weeks while well within a year's range. The study asks whether Chronos-2 does worse on such days.

**The forecasts are the tails study's,** checked against their hashes: Chronos-2 (primary), TimesFM 2.5 one day per call (exploratory), Timestral and LightGBM S1 (descriptive), and the weather regression as the reference for every comparison. The study made no new forecasts.

**Novel days were chosen from the weather the models received, never from outturn.** A day is novel when its coldest forecast half-hour is colder than the coldest half-hour of its context. Both temperatures are on ECMWF's scale, and both were public before the 09:30 issue time on the day before (`PLAN.md` §4). Of the 960 backtest days, 30 were novel; 14 of those were also among the coldest tenth (T1).

**Each novel cold day was matched to a cold day that was not novel,** using weather alone, before any error was computed. A match had to be within 1 °C in mean forecast temperature, the measure that defines T1, and within one calendar month. Ten of the 14 found a match. The four that did not include the three coldest days in T1: no day that was not novel came within 1 °C of them.

**The pairs are well balanced.** On average the novel day was 0.17 °C colder than its control in mean temperature (largest gap 0.83 °C) and 0.29 °C colder in daily minimum (largest gap 2.26 °C). Eight of the ten pairs fall in the same month.

**The measure.** A day's *peak error* is its highest outturn half-hour minus the forecaster's highest forecast half-hour, in MW. Positive means the forecast peak was too low. *Excess peak error* subtracts the regression's peak error on the same day, which allows for days that are hard for everyone. **Δ** is the mean, over the pairs, of the novel day's excess minus its control's.

**The interval resamples cold spells, not pairs.** Novel days fewer than three days apart form one cold spell, and there are four. Each of 2,000 draws resamples the four spells with replacement. Four spells allow only 35 distinct draws, so the interval is coarse. In effect the study has four independent pieces of evidence, not ten.

**The reading was fixed in advance.** A *meaningful penalty* needs the interval's lower bound above 250 MW, a threshold chosen for this study as about half the tails study's 511 MW cold-day peak miss. It is not a NESO standard.

## Results

### Δ by forecaster

| Forecaster | Δ (MW), 90% interval | Leaving out one spell (MW) |
|---|---|---|
| **Chronos-2** | **1,241 (589–1,765)** | 1,017 to 1,551 |
| TimesFM 2.5, one day per call (exploratory) | 2,723 (732–4,171) | 2,050 to 3,402 |
| Timestral (descriptive) | 1,981 (999–3,152) | 1,541 to 2,664 |
| LightGBM S1 (descriptive) | 618 (147–1,184) | 247 to 815 |

**H5 reads "meaningful penalty supported"** at 250 MW, and at the 100 MW and 500 MW sensitivity thresholds too.

**No single spell drives Chronos-2's result.** Leaving out any one spell keeps Δ between 1,017 and 1,551 MW.

**TimesFM 2.5 fell furthest behind on novel days.** Version 1 of the plan predicted the opposite, because TimesFM 2.5 fits a straight line to its covariates in context, which extends beyond the context's range. The prediction was dropped before the run (`PLAN.md`, changes from version 1), and the result is exploratory.

### Δ by cold spell

| Spell | Novel days in pairs | Pairs | Chronos-2 | TimesFM 2.5 | Timestral | LightGBM S1 |
|---|---|---|---|---|---|---|
| 1 | 19–21 November 2024 | 3 | 1,175 | 4,130 | 389 | 1,485 |
| 2 | 8–9 January 2025 | 2 | 1 | 6 | 2,627 | −169 |
| 3 | 17–19 November 2025 | 3 | 1,765 | 4,294 | 1,968 | 357 |
| 4 | 3 and 6 January 2026 | 2 | 1,796 | 974 | 3,744 | 498 |

Chronos-2 showed a large penalty in three spells and none in the second. Seven of its ten pairs were positive.

### The pairs (Chronos-2)

| Novel day | Control | Spell | Excess, novel (MW) | Excess, control (MW) | Difference (MW) | Mean temp. gap (°C) | Daily min. gap (°C) | Month gap |
|---|---|---|---|---|---|---|---|---|
| 2024-11-19 | 2024-11-28 | 1 | 2,648 | 1,007 | 1,640 | +0.17 | +0.58 | 0 |
| 2024-11-20 | 2025-11-21 | 1 | 2,851 | 592 | 2,259 | −0.38 | −0.03 | 0 |
| 2024-11-21 | 2025-12-31 | 1 | 2,216 | 2,591 | −375 | −0.83 | −0.83 | 1 |
| 2025-01-08 | 2026-01-10 | 2 | −429 | 97 | −526 | −0.35 | −1.27 | 0 |
| 2025-01-09 | 2025-01-11 | 2 | 1,132 | 604 | 528 | +0.03 | +0.36 | 0 |
| 2025-11-17 | 2025-11-26 | 3 | 1,931 | −1,927 | 3,858 | −0.01 | +1.44 | 0 |
| 2025-11-18 | 2025-12-30 | 3 | 549 | 1,707 | −1,158 | −0.04 | +0.21 | 1 |
| 2025-11-19 | 2024-11-22 | 3 | 2,182 | −413 | 2,595 | +0.23 | −0.97 | 0 |
| 2026-01-03 | 2025-01-03 | 4 | 1,704 | −434 | 2,138 | −0.39 | −0.17 | 0 |
| 2026-01-06 | 2025-01-04 | 4 | 1,423 | −32 | 1,455 | −0.11 | −2.26 | 0 |

Gaps are novel day minus control. A negative temperature gap means the novel day was colder. Every figure in this note is calculated from unrounded values and then rounded to whole MW, so a displayed difference or average can differ by 1 MW from one worked out from the rounded figures shown.

### The four unmatched novel days (description only)

| Day | Regression peak error (MW) | Chronos-2: peak (excess) | TimesFM 2.5 | Timestral | LightGBM S1 |
|---|---|---|---|---|---|
| 2025-01-10 | −1,424 | −551 (873) | 424 (1,847) | −1,239 (185) | 1,290 (2,713) |
| 2025-11-20 | 214 | 2,341 (2,127) | 3,341 (3,127) | 2,073 (1,859) | 1,405 (1,191) |
| 2026-01-04 | −937 | 2,573 (3,510) | 6,853 (7,791) | 3,432 (4,369) | 1,525 (2,462) |
| 2026-01-05 | −858 | 3,943 (4,802) | 6,413 (7,271) | 5,867 (6,726) | 2,845 (3,703) |

On the two coldest days, 4 and 5 January 2026, Chronos-2's forecast peak was 2,573 and 3,943 MW too low. These days had no match, so they carry no weight in Δ.

### Every novel cold day against every other cold day (description, no interval)

| Forecaster | Mean excess, 14 novel days (MW) | Mean excess, 82 other T1 days (MW) | Difference (MW) |
|---|---|---|---|
| Chronos-2 | 1,966 | 419 | 1,547 |
| TimesFM 2.5 | 4,434 | 408 | 4,026 |
| Timestral | 2,546 | 732 | 1,814 |
| LightGBM S1 | 1,477 | 314 | 1,163 |

Without matching, the gaps for Chronos-2, TimesFM 2.5 and LightGBM are larger; Timestral's is smaller. The novel days include the three coldest days and six mid-November days, so this comparison mixes novelty with coldness and season. The matched Δ is built to separate them.

### All 30 novel days, with the tails study's metrics

Over all 30 novel days, in every season, Chronos-2 under-forecast the daily peak by 1,459 MW (1,074 to 1,801), while the regression's peak error was −259 MW (−539 to 30). Against the other 930 days, Chronos-2's error relative to the regression rose: tail shift 1.241 (1.026–1.474). Against days of the same months it did not clearly rise: 1.183 (0.977–1.402). The full table is in `results.md`. Every interval in this note comes from the bootstrap draws in `score.py`; the values are recorded in `results.json`.

## Limits

- **Four cold spells.** The interval rests on four independent spells and only 35 distinct draws. Its bounds are coarse, and a fifth spell could move them.
- **The reference.** Δ measures each forecaster against the regression. LightGBM's positive Δ suggests the regression did relatively well on novel days. Measured against another reference, every Δ could be smaller.
- **Season.** Six of the ten novel days in the pairs fall in mid-November. Matching held the month, but the first cold spell of a winter may differ in ways the weather inputs do not capture.
- **Not blind.** H5, the 250 MW threshold and the matching rule were written after the tails study's results were seen, though before any error on novel days was computed.
- **Training data.** The foundation models may have seen these days in training. A live test would settle that.

## What comes next

**Whether Chronos-2's penalty is about the context can be tested directly.** Forecast the same pairs again with Chronos-2 given a longer history, one that reaches back into the previous winter, and compare it with the eight-week forecasts. The test is whether its error relative to the regression improves more on the novel days than on their matched controls. Comparing each day with itself removes the days' own difficulty and the regression's luck on them, which this study cannot separate. If the improvement is larger on novel days, the context is at least part of the cause. That needs new forecasts, under a new plan.

**Retrieval is the practical version of the same idea.** Supplying the model with past cold spells as context is a direct remedy if the context is the cause, and the longer-context test would show whether it could work.

## Reproduce

- **Plan:** `PLAN.md`, version 2, frozen at tag `context-novelty-plan-v2` (21b9a29) before any script ran on the backtest. Version 1 is at tag `context-novelty-plan`.
- **Day sets and pairs:** `build_days.py` (sha256 0a8ed597…), run at 21b9a29, after its synthetic check passed. Outputs: `days.csv`, `day_inputs.csv`, `pairs.csv`, `days.json`.
- **Scoring:** `score.py` (sha256 2f58712c…), run at 3daf6fe, after its synthetic check passed (`synthetic.json`). It imports the tails study's scoring functions unchanged. Outputs: `results.json`, `results.md`.
- **Changes:** every implementation choice and every deviation, with the reviews that led to them, is in `REVISIONS.md`.
- **Data:** the forecast files are in this repository. The weather inputs are public data that are not committed; their files are named and hashed in `days.json`.

## Use of AI

I used AI tools in this work: Claude, ChatGPT, Microsoft Copilot, DeepSeek, Kimi and Z.ai. The work is designed so that results are calculated numerically and checked against ground truths, and assumptions are checked against original sources. Both scripts passed synthetic checks with known answers, and failed them when their rules were deliberately broken, before the real data were scored.

## Sources

- Ashok, A. et al. (2026). [WhatIf-Bench: benchmarking intervention-aware time series forecasting](https://arxiv.org/abs/2610.26582). arXiv 2610.26582.
- [CovNovBench: a benchmark for evaluating time series foundation models under covariate novelty](https://neurips.cc/virtual/2026/175022). NeurIPS 2026. Abstract only.
- Lerch, S., Thorarinsdottir, T. L., Ravazzolo, F. and Gneiting, T. (2017). [Forecaster's dilemma: extreme events and forecast evaluation](https://projecteuclid.org/euclid.ss/1491465630). *Statistical Science* 32(1), 106–127.
