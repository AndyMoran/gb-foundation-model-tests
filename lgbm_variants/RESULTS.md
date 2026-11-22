# LightGBM variants: can a tree model learn the heating response?

Andy Moran (Heaviside Analytics) · draft, 22 November 2026 · a backtest study, descriptive

For: a forecaster choosing a trained benchmark for GB day-ahead demand, and anyone who wants to know why LightGBM lost to a straight line.

**What this does not show.**
- **A tuned LightGBM.** V1, V3, V4 and V5 each change one aspect of S1. V2 and its control, V2c, use the modified setup described below. None was tuned.
- **An unbiased winner.** The best variant was chosen on the same 960 days it is scored on, so its figure is optimistic, and its interval does not allow for that choice.
- **Why V1 works.** Its result is consistent with giving the trees the regression's heating curve, but a backtest cannot establish the mechanism.
- **Anything about linear leaves.** V2 produced extreme forecasts on a few days, so it did not test them reliably (below).
- **Live performance.** Chronos-2 may have seen these days in training.

## Headline

In a 960-day backtest, the best of five pre-specified LightGBM variants (V1) beat a weather regression: 0.984 times its error (90% interval 0.973–0.994).

In a backtest it may have seen in training, Chronos-2 had 0.918 times that variant's error (90% interval 0.887–0.948); the variant was chosen on these same days, so its figure is optimistic.

The headline claims follow the pre-specified rules in `PLAN.md` §7; `score.py` generated the wording. "Five" counts the planned variants, V1 to V5; V2c is a control and could not be chosen. The backtest covers 16 March 2024 to 31 October 2026, two winters. Chronos-2's interval is for the ratio of its error to V1's, on paired bootstrap draws; the table below gives Chronos-2 against the regression instead.

**In plain terms:** V1 had the lowest error of the LightGBM variants on these days: 998 MW against 1,014 MW for the weather regression, a 1.6% apparent reduction. Because V1 was chosen on these same days, the true margin may be smaller. Chronos-2's error was 0.918 times V1's.

**The cold-weather gap closed.** S1 was 12.5% worse than the regression in winter and 21.8% worse on the coldest tenth of days. V1's ratios were 0.992 in winter and 0.976 on the coldest tenth, both level with the regression. That is consistent with the idea that the trees did badly in winter because they had to build the heating curve from steps.

## What was compared

**The problem.** In checkpoint 0, LightGBM with the S1 settings had 4.6% more error than a weather regression (1,061 MW against 1,014). It matched the regression in summer and fell behind in winter. The tails study ruled out one explanation: no day was colder than LightGBM's training data. The explanation this study tests is how LightGBM learns the heating response; it is not the only possible one. The regression fits 48 half-hour models, with temperature, its square and wind chill built in. LightGBM fits one model across all half-hours and builds any curve from steps.

**Five variants and a control,** chosen before any of them ran (`PLAN.md`, frozen at tag `lgbm-variants-plan`). V1, V3, V4 and V5 each change one aspect of S1. V2 cannot: LightGBM does not allow S1's L1 objective with linear leaves. So V2 uses a modified setup (L2 objective, slot as a category, scaled features), and V2c is that setup without linear leaves. V2 against V2c isolates the linear leaves; V2c against S1 shows the setup's own effect.

| Variant | What changes |
|---|---|
| **V1: residual** | The regression is fitted first; LightGBM is fitted to what it misses. The forecast is the regression's plus LightGBM's. |
| **V2: linear leaves** | Linear leaves added to the V2c setup: each leaf holds a linear model instead of a constant (`linear_tree`). |
| V2c: control for V2 | S1 with the L2 objective, slot as a category and scaled features; no linear leaves. |
| **V3: per-slot** | 48 models, one per half-hour of the day. |
| **V4: regression's terms** | The regression's temperature, temperature-squared and wind-chill terms added as features. |
| **V5: two winters** | Two years of training days instead of one. |

V1 uses a decomposition related to designs in load-forecasting work. TNEI's report for NESO, the GB system operator, modelled mean demand with a smooth model (a GAM) and used LightGBM for the quantiles of the residuals around it: related to V1's split, though V1 forecasts the residual itself, not its spread.

**Everything else was fixed:** the weather study's 960 backtest days and inputs, S1's settings, one day per call, a fresh fit for each day. Five checks passed before the run (`checks.json`), including an independent rebuild of every variant's training data and an exact reproduction of checkpoint 0's S1 forecasts.

**The measure.** Each day's mean absolute error over its half-hours, in MW, averaged over the days; and its ratio to the regression's. A 90% interval wholly below 1 beats the regression; wholly above 1 trails it; otherwise the two are level, which is not evidence that they are equal.

## Results

### Every forecaster against the regression

| Forecaster | Mean daily error (MW) | All days | Winter (Nov–Mar) | Other months | Coldest tenth (T1) |
|---|---|---|---|---|---|
| LightGBM S1 | 1,061 | 1.046 (1.022–1.068) | 1.125 (1.082–1.172) | 1.002 (0.979–1.024) | 1.218 (1.113–1.337) |
| **V1: residual** | **998** | **0.984 (0.973–0.994)** | **0.992 (0.975–1.009)** | **0.979 (0.966–0.992)** | **0.976 (0.944–1.017)** |
| V2: linear leaves | 3,089 | 3.045 (2.008–4.492) | 2.044 (1.381–2.894) | 3.594 (2.100–5.796) | 2.973 (1.287–5.641) |
| V2c: control | 1,036 | 1.021 (1.000–1.040) | 1.086 (1.049–1.127) | 0.985 (0.963–1.003) | 1.178 (1.102–1.272) |
| V3: per-slot | 1,171 | 1.154 (1.116–1.194) | 1.273 (1.189–1.375) | 1.089 (1.055–1.113) | 1.564 (1.328–1.815) |
| V4: regression's terms | 1,070 | 1.055 (1.033–1.077) | 1.130 (1.091–1.170) | 1.014 (0.991–1.037) | 1.198 (1.116–1.298) |
| V5: two winters | 1,024 | 1.010 (0.990–1.028) | 1.051 (1.017–1.087) | 0.987 (0.966–1.006) | 1.121 (1.034–1.213) |
| Regression, two years (shown, not compared) | 1,024 | 1.009 (1.001–1.017) | 1.006 (0.991–1.021) | 1.011 (1.001–1.020) | 1.010 (0.967–1.042) |
| Chronos-2 | 916 | 0.902 (0.873–0.933) | | | |
| Weather regression | 1,014 | 1 | 1 | 1 | 1 |

Ratios to the regression's mean daily error, with 90% intervals from a 7-day moving-block bootstrap (2,000 draws): the same resampled blocks for the forecaster and the regression in each ratio. The plan asks for seasonal and T1 ratios for the variants only, so the Chronos-2 row has none.

**What each variant showed:**
- **V1 was the only variant level with the regression in winter and on the coldest days,** and the only one ahead of it over all days.
- **V3, the per-slot model, did worst of the stable variants,** especially on the coldest days (1.564). In this setup, 48 small models did worse than one large one.
- **V4 was no better than S1:** slightly worse over all days and level in winter. Giving the trees the regression's heating terms as features did not help them use the terms.
- **V5 helped in winter.** A second winter cut S1's winter ratio from 1.125 to 1.051, still higher than V1's 0.992 in this backtest. The regression gained nothing from a second year (1.009).
- **V2c, the control, was slightly better than S1 (1.021).** Its changes from S1 were the L2 objective, slot as a category and scaled features.

### Each variant against S1 directly (exploratory)

The plan read H3 from whether intervals overlap. Overlap alone does not show whether two ratios differ, so this table, added after scoring at a review's request, gives each variant's ratio minus S1's (`explore.py`; `REVISIONS.md` item 21). It is post hoc. Each interval uses one set of resampled 7-day blocks for the variant, S1 and the regression; the blocks are drawn afresh, not reused from the main table. Negative means better than S1.

| Variant | All days | Winter | Coldest tenth |
|---|---|---|---|
| V1 | −0.062 (−0.082 to −0.043) | −0.133 (−0.175 to −0.096) | −0.242 (−0.347 to −0.144) |
| V2 | +1.999 (+0.962 to +3.448) | +0.919 (+0.258 to +1.771) | +1.754 (+0.014 to +4.564) |
| V2c | −0.025 (−0.034 to −0.016) | −0.040 (−0.058 to −0.021) | −0.041 (−0.090 to +0.009) |
| V3 | +0.109 (+0.082 to +0.139) | +0.148 (+0.084 to +0.221) | +0.346 (+0.191 to +0.522) |
| V4 | +0.010 (+0.002 to +0.017) | +0.005 (−0.011 to +0.019) | −0.020 (−0.060 to +0.018) |
| V5 | −0.036 (−0.049 to −0.023) | −0.074 (−0.100 to −0.050) | −0.097 (−0.170 to −0.038) |

V1, V5 and V2c were clearly better than S1 in winter; V4 was not clearly different (its interval includes no difference); V2 and V3 were worse.

### V2: unstable as specified

V2's mean daily error is dominated by a few days of extreme forecasts. On a typical day it was ordinary: its median daily error was 1,020 MW, against 956 for V2c and 943 for the regression. But on 17 days its daily error exceeded 20,000 MW. On 17 July 2025 its forecasts ranged from −9.3 million to +11.1 million MW, against an outturn of 19,813 to 29,388 MW. These are the model's raw output; nothing was clipped or capped.

Each leaf's linear model is fitted using the training rows routed to that leaf, then applied to the target day's features. LightGBM documents `linear_lambda` as regularisation for linear trees, with a default of 0, which the plan used. It does not say that regularisation prevents this. So V2 is unstable as specified, and it is not a reliable estimate of what linear leaves are worth. Regularising them is one setting a future, preplanned test could try. Changing it now would change the model after seeing the result.

### The hypotheses (`PLAN.md` §6)

| Hypothesis | Reading by the fixed rule | Comment |
|---|---|---|
| **H2:** V1 has the lowest mean daily error of the five | **Supported** | |
| **H3:** every variant's winter ratio is below S1's | **Not supported** | V1, V5 and V2c were clearly below S1 in winter (table above). V2 and V3 were above; V4 was not clearly different. The rule read V5 as "unclear" from overlapping intervals; the post hoc direct comparison shows it clearly below. |
| **H4:** V2's mean daily error is below V2c's | **Not supported** | The rule's first test failed: V2's ratio to the regression (3.045) was above V2c's (1.021), so no interval comparison was needed. The specified V2 did not support H4. Its extreme forecasts mean this is not evidence about linear leaves generally, or about regularised ones. |

"Unclear" under the fixed rule means the point estimates point the hypothesis's way but the intervals overlap (`REVISIONS.md` item 15).

### Cost

Every variant forecast a day in under 3 seconds on a laptop CPU with 4 threads: V3, with 48 fits a day, took 2.7 seconds; the rest took 0.5 to 1.1. Peak memory was about 960 MB for each, most of it the loaded data (`cost.json`). The full run took 1 hour 47 minutes.

## What this means for the benchmark

**V1 becomes the LightGBM comparator if checkpoint 1 runs.** The comparator rule (`PROJECT.md` §4) chooses on error, from configurations backtested under committed scripts. In this backtest, Chronos-2's edge over V1 was about 8%, against about 14% over S1.

**Whether checkpoint 1 runs is decided on 8 January 2027** (`HANDOVER.md`).

## Limits

- **Selection.** V1 was chosen as best on the days it is scored on. Its 1.6% margin over the regression is small, and the interval does not allow for the choice.
- **V1's residuals are in-sample.** The regression is fitted on the same training days whose residuals the trees learn from. Fitted values are slightly better than forecasts, so the residuals the trees learn may differ from the ones they must correct on the target day. Out-of-sample residuals were not available in this study; rolling or cross-fitted regression forecasts for the training days would be a possible follow-up.
- **One configuration per variant or control.** V1, V3, V4 and V5 use S1-based settings; V2 and V2c use the modified setup. None was tuned, and a tuned version of any of them could do better or worse.
- **The backtest.** Two winters, 960 days, and foundation models that may have seen them.

## Reproduce

- **Plan:** `PLAN.md`, frozen at tag `lgbm-variants-plan` (9e1002b) before any variant ran.
- **V5's data:** `fetch_v5.py` and `gb-weather-private/weather/v5_era5.py`. Demand for 2022 matched the frozen file on every half-hour of December 2022; rebuilt ERA5 matched the frozen file to its four decimals over six days (`v5_data_manifest.json`).
- **Forecasts:** `gb-weather-private/weather/lightgbm_variants.py` (sha256 69968508…, b1eb3fa), after its synthetic check (`synthetic.json`) and real checks (`checks.json`) passed. Output: `forecasts.csv`, `forecasts.json`; cost in `cost.json`.
- **Scoring:** `score.py` (sha256 e8172eef…), after its synthetic check passed (`score_synthetic.json`). Outputs: `results.json`, `results.md`.
- **Exploratory additions:** `explore.py`, written after the results were seen and committed before it ran. Outputs: `explore.json`, `explore.md`.
- **Changes:** every implementation choice, deviation and review is in `REVISIONS.md`.

## Use of AI

I used AI tools in this work: Claude, ChatGPT, Microsoft Copilot, DeepSeek, Kimi and Z.ai. The work is designed so that results are calculated numerically and checked against ground truths, and assumptions are checked against original sources. Every script passed synthetic checks with known answers before it ran on real data, and the variants' training data were rebuilt independently and matched.

## Sources

- TNEI (2024), the QWID FLEXER report for NESO, pp. 18–19 and 24.
- LightGBM [parameter documentation](https://lightgbm.readthedocs.io/en/latest/Parameters.html): `linear_tree` and `linear_lambda`.
- `PLAN.md` §1 for the other prior work; `checkpoint0/RESULTS.md` and `tails/RESULTS.md` for every earlier figure.
