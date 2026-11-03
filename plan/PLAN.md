# Preregistered plan: zero-shot foundation models against GB day-ahead demand forecasts

Analysis plan · draft for agreement, revision 3 · 3 November 2026 · Andy Moran (Heaviside Analytics)

> **Status.** No model has been run on GB demand data, and no forecast of any kind has been scored. The author has seen the feasibility outputs (`docs/feasibility/`): the timing and values of a handful of NESO forecasts and outturns, used to fix the data and timing rules. He has also seen the row counts and missing half-hours of the full download (Section 2), used to set the gap rule. The plan will be committed and tagged before the first scored run; the tag's time is the evidence of timing.
>
> **Decisions.** The seven decisions in Section 12 were settled by the author on 3 November 2026. The power check (Section 8) has been run and its consequences recorded; no decision was changed.

## 1. The question, and what the answer can and cannot show

**Do zero-shot forecasting models (TimesFM 2.5, Timestral, Chronos-2) forecast GB national electricity demand a day ahead better than a simple regression, and by enough to matter? How do they compare with NESO's own published forecast?**

What it can show: how three off-the-shelf models, given only demand history available at the issue time, compare with a transparent statistical baseline and with the system operator's published forecast, over 2024–2026.

What it cannot show, stated in advance:

- **Freedom from training leakage.** The models may have seen GB demand in training. The leakage check (Section 7) makes memory more or less plausible; it cannot rule it out. The post-release windows show only that a model was published before the period.
- **Generality.** One series, one country, one horizon.
- **Fine-tuning.** Zero-shot only.
- **Weather.** The models and the regression get no weather inputs; NESO's forecast uses weather. A NESO win may reflect weather information rather than modelling skill.
- **Value.** Accuracy, not money.

## 2. Data

| Item | Source | Use |
| --- | --- | --- |
| Outturn | Elexon Insights API, `/demand/outturn`, `initialDemandOutturn` (INDO) | Model and regression inputs; the scoring target |
| NESO's forecast | Elexon Insights API, dataset `NDF` (day-ahead national demand forecast), every publication with its `publishTime` | Secondary comparator |
| NESO's record of its forecast | NESO Data Portal, "Day Ahead Half Hourly Demand Forecast Performance" | Validity gate only (Section 9) |
| NESO Historic Demand Data (ND) | NESO Data Portal | Robustness only (Section 6) |
| Bank holidays | GOV.UK bank-holidays JSON (England and Wales), fetched once and hashed | Regression calendar terms |

All downloads are made once by `fetch.py`, saved, and hashed; the hashes go in the lock file. Attribution: "Contains BMRS data © Elexon Limited copyright and database right 2026"; "Supported by National Energy SO Open Data".

**Why the NDF stream.** It carries the same publications as the `/evolution` endpoint used in the feasibility check, and can be downloaded by publication day rather than one half-hour at a time. On 3 November 2026 the two were compared for three half-hours of 16 January 2025: every publication up to 10:00 on D−1 matched in time and value.

**Gaps in the data.** The download of 3 November 2026 (68,734 INDO half-hours, 1 December 2022 to 1 November 2026) has two missing half-hours: 22:00 UK time on 17 July 2023 and 03:30 on 29 December 2023. The first lies outside every model context and affects only the regression's training days. The second lies in the context of every target day from 1 January to about 23 February 2024; Section 4.1 sets how it is handled.

**Why INDO.** NESO's own record scores its forecast against INDO (all 144 half-hours checked matched), INDO was known at the time, and it is never republished. NESO's later ND series differs by about 95 MW.

## 3. Timing: one information set for every forecaster

- **Target day D:** every settlement period of D in UK local time: 48 half-hours, or 46 or 50 on clock-change days.
- **Issue time:** 09:30 UK local time on D−1.
- **Models and regression:** INDO for half-hours ending at or before 08:30 UK local time on D−1. The one-hour buffer covers an arrival delay that Elexon's timestamps cannot measure (feasibility check E).
- **NESO:** for each half-hour of D, the latest Elexon publication with `publishTime` at or before 09:30 UK local time on D−1. In practice that is the 08:45 issue for daytime and evening half-hours and the 09:15 update for early-morning ones. If that publication's value is blank, the most recent earlier non-blank publication is used.
- **Series order:** inputs are a continuous half-hourly series in UTC, so clock changes need no special handling in the input; targets are mapped back to settlement periods.

## 4. Forecasters

### 4.1 The three models, zero-shot

| Model | Weights (Hugging Face) | Revision | Weights licence | Library |
| --- | --- | --- | --- | --- |
| TimesFM 2.5 (200M) | `google/timesfm-2.5-200m-pytorch` | `1d952420fba87f3c6dee4f240de0f1a0fbc790e3` | Apache 2.0 | `timesfm` 3.0.2 (the version pinned in the TimesFM extension) |
| Chronos-2 (120M) | `amazon/chronos-2` | `29ec3766d36d6f73f0696f85560a422f50e8498c` | Apache 2.0 | `chronos-forecasting` 2.3.2 |
| Timestral-209M | `mistralai/Timestral-209M` | `9874d252ab0aae16f7f7c999f98f98d6ad7d8365` | Mistral's Modified MIT | `timestral` 1.0.0, commit `a534bdbd` |

- **Context:** the last **2,688 continuous UTC half-hours (8 weeks) ending at or before 08:30 UK local time on D−1**, the same for every model. Eight weeks gives every model several weekly cycles; all three accept it (maximum contexts: TimesFM 2.5 16k, Chronos-2 8k, Timestral 32k). **Gap rule (decided 3 November 2026):** a run of one or two missing half-hours inside a context is filled on a straight line between its two neighbours, provided the later neighbour is itself inside the context, so nothing after the cut-off is used. Fills apply to model contexts only: targets, the regression's inputs and NESO's forecast are never filled. Every filled half-hour, and the number of target days whose context uses it, is listed in `context_fills.csv`. A longer run, or a run at the end of the context, excludes the target day from every comparison. In the data as downloaded, this fills one half-hour (03:30 on 29 December 2023) and keeps 54 target days that strict exclusion would lose.
- **Horizon:** the number of half-hours from the cut-off to the end of D (normally 31 + 48 = 79), requested in one call; only the half-hours of D are scored.
- **Point forecast:** the median (0.5 quantile).
- **Days forecast independently:** each target day is forecast from its own context alone. Chronos-2 can share information across the series in a batch (`cross_learning`); it is set to False, and the self-test checks for every model that a day forecast alone equals the same day forecast within a batch.
- **Settings:** every forecasting argument is written out in `models.py` and recorded with the forecasts; no setting relies on a library default. Settings follow each model's published usage guidance, fixed before any GB forecast is made, and are not tuned.
- **Weights:** the run checks each weights file's SHA-256 before the first forecast. Recorded at setup (3 November 2026, `selftest.py --models`):
  - TimesFM 2.5: `2f776efe6245e42b24bc4153ffdf61810140210e4bd3b01fb21f7aa779ab6ce8`
  - Chronos-2: `ddcda3c7508bf2528087723e98a20707cc04b7f370ae275a9fd88078ddba4f42`
  - Timestral-209M: `1456effb9927e3daa8c7234f10497e3424233869245a9c72b8ecebaf7ad2b7fa`
- **Environment:** Python 3.11, torch 2.15.0 (CPU), numpy 2.4.6, pandas 3.1.0, with the three libraries above (`requirements-models.txt`).
- **L1 pilot (synthetic data, 12 days):** under 300 MW noise the regression's error rose 1.9%; the models' changed by −4.9% (TimesFM 2.5), −0.8% (Chronos-2) and +0.9% (Timestral). The noise is neither saturating nor inert, so the size stays at 300 MW.

### 4.2 The primary comparator: a weekly-lag regression

One least-squares regression for each half-hour slot of the day (48, by local clock time), re-estimated for every target day. **Training target days: the 365 complete days ending at D−2, that is D−366 to D−2 inclusive** (D−1 is not fully observed at the cut-off). Training days with any missing half-hour are dropped; nothing is imputed.

> demand(D, slot) = a + b₁ · demand(D−2, slot) + b₂ · demand(D−7, slot) + day-of-week terms (6) + bank-holiday term + 24 December–2 January term

- **Why D−2 and D−7.** At the cut-off, D−2 is the latest full day observed; D−7 carries the weekly pattern.
- **Calendar terms:** the bank-holiday and Christmas-period indicators refer to the target day. Bank holidays are England and Wales only (GOV.UK); Scottish holidays are not modelled. That is a stated limitation of a deliberately simple comparator, not changed later.
- **Clock-change days:** the extra or missing hour is matched by local clock time; the 50-period day's repeated hour uses the first occurrence's coefficients.
- It is deliberately simple and transparent: the benchmark the models must beat, as the AR(2) was in the macro series, though it is not an autoregression of that kind.

### 4.3 Floor and secondary comparator

- **Seasonal naive** (floor, reported, not tested): demand at the same local clock time on D−7.
- **NESO's day-ahead forecast** (secondary): as defined in Section 3.

## 5. Windows

| Column | Target days | Label |
| --- | --- | --- |
| **Full** | 1 January 2024 to 31 October 2026 | "Inside possible training data" |
| **Post-release** | From each model's post-release date to 31 October 2026: TimesFM 2.5 from 15 September 2025; Chronos-2 from 30 October 2025; Timestral from 15 October 2026 | Shows only that the model was published before the period. Timestral's 17 days are reported descriptively, with no test |
| **Prospective** | From the start of daily forecast saving | Scored under a separate short plan, written before the first prospective day is scored |

The primary tests use the full window. No headline compares one model's post-release column with another's full column.

## 6. Statistics

- **Daily error:** for each forecaster and day, the mean absolute error in MW over the half-hours of D.
- **Ratio:** mean daily error of the model ÷ mean daily error of the comparator, over the window's days.
- **Resampling:** moving-block bootstrap over days, block length 7 (weekly dependence), 2,000 draws, seed 20261103.
- **Primary tests:** six one-sided tests, two for each model against the regression on the full window, Holm-adjusted together at a family-wise 5% level:
  1. **Improvement:** reject ratio ≥ 1 in favour of ratio < 1.
  2. **Practically meaningful improvement:** reject ratio ≥ 0.90 in favour of ratio < 0.90 (m = 10%, Section 8).

  Failing to reject ratio ≥ 0.90 is not evidence that the gain is below 10%; it is reported as "not shown to reach the threshold". The p-values come from the block bootstrap below, by the percentile method for each null value.
- **Intervals:** bootstrap 90% intervals for every comparison, labelled descriptive (not adjusted for multiplicity).
- **Secondary:** each model against NESO's forecast, full window and post-release window: estimates with descriptive intervals; no practical-importance test.
- **Exploratory:** seasonal naive; comparisons between models; errors by season, time of day, weekday and holiday; the post-release windows for the primary comparisons.
- **Robustness:** primary ratios rescored against NESO's later ND series.
- **Missing data:** a target day missing INDO for any half-hour, or with a context gap the rule in Section 4.1 does not fill, is excluded from every comparison. A day missing a NESO publication for any half-hour (after the blank-value rule) is excluded from NESO comparisons only. Every exclusion is listed.

## 7. Leakage check

**Perturbation test (L1),** adapted from the TimesFM extension: independent Gaussian noise of standard deviation **300 MW** (about 1% of typical GB demand) is added to every half-hour of the input history, 20 draws with seeds 20261104 + k (k = 0 … 19), on the full window. The same draws are applied to every model's context and to the regression's inputs; targets are never perturbed. A model relying on memory of the exact GB series should degrade more than the regression.

**Flag:** (model perturbed error ÷ model unperturbed error) − (regression perturbed error ÷ regression unperturbed error) > 0.05, using mean daily errors averaged over the 20 draws. The flag is reported, never used to drop a result. If the synthetic pilot (Section 11, step 2) shows 300 MW is clearly saturated or clearly inert, the size is changed before freezing, never after.

The TimesFM extension's shape-matched placebo (L2) is not repeated: it needs a single historical episode to transplant, which daily demand does not have.

## 8. "Enough to matter"

**m = 10%** (decided 3 November 2026). A model counts as practically better only if the test in Section 6 rejects ratio ≥ 0.90.

**Rationale:** a zero-shot model is a heavier dependency than a regression (more compute, a third party's weights and licence, less transparency). A small gain does not justify that cost in an operational forecasting chain, where the forecast feeds balancing and trading decisions whose error costs scale roughly with absolute error. 10% is a judgement of the smallest gain that would justify the switch; it is not derived from any regulatory threshold. NESO's reported metric 1B (average absolute MW error against INDO) supports the choice of metric only. Gains between 0 and m are reported as improvements that are not practically meaningful.

**Power.** Before freezing, `power.py` simulates model forecasts with known true ratios (1.00, 0.95, 0.90, 0.85) by combining the regression's real errors on the full window with synthetic error components of the right size and correlation, and reports how often each primary test succeeds. The power check does not set m; it reports how precisely the study can estimate it. If power at a true ratio of 0.90 is very low, the author decides before freezing whether "not shown to reach 10%" is an acceptable likely answer, and records that decision here. m is never changed in light of model results. The power check reads no model forecast. **Disclosure:** it computes the regression's real errors on the full window before freezing; nothing about the models is learned from it.

**Power check result (3 November 2026, `results/power.json`, 200 replications per cell).** The regression's mean daily error over the full window is 1,553 MW. The simulated model's errors share a fraction c of the regression's (c = 0.5, 0.7, 0.9). Each cell gives the share of replications in which the test rejects, as a range from the strictest Holm step (5%/6) to the loosest (5%):

| True ratio | Improvement (ratio < 1), c = 0.5 / 0.7 / 0.9 | Meaningful (ratio < 0.90), c = 0.5 / 0.7 / 0.9 |
| --- | --- | --- |
| 1.00 | 0.03–0.05 / 0.01–0.07 / 0.04–0.08 | 0 / 0 / 0 |
| 0.95 | 0.27–0.54 / 0.47–0.72 / 0.94–0.99 | 0 / 0 / 0 |
| 0.90 | 0.88–0.94 / 0.96–0.99 / 1.00 | 0.01–0.03 / 0.01–0.05 / 0.04–0.07 |
| 0.85 | 0.99 / 1.00 / 1.00 | 0.39–0.60 / 0.65–0.79 / 0.97–0.99 |

The power check uses the same estimand, block length, p-value method and test family as Section 6, with 500 bootstrap draws per replication rather than 2,000. Each cell's Monte Carlo standard error is at most about 0.035 (200 replications).

**What this means, decided before freezing (3 November 2026).** The study reliably detects a real gain of 10% or more, but can confirm that a gain exceeds 10% only when it is well above 10%. "Not shown to reach 10%" is therefore a likely answer even for a useful model. The author accepts this and freezes as planned:
- m was set on substance (above) and is not changed to suit the power.
- The threshold test stays primary. Demoting it would change the question from "better enough to switch?" to "better at all?".
- The window cannot grow without breaking comparability with rung 2, whose weather archive starts in January 2024.
- The conservative direction is deliberate: a heavier dependency needs a stronger case, so missing a marginal winner is the preferred error over adopting one on a noisy estimate.

**Assumption.** Model and regression errors are expected to be highly correlated (c near 0.7–0.9), since neither sees weather and both should miss the same surprises. This is a judgement, not a measurement. If correlation is low (c = 0.5), the threshold test confirms a true 15% gain only 39–60% of the time.

**Two interpretation rules, fixed now:**
1. A failure to reject ratio ≥ 0.90 is reported as "not shown to reach 10%". It is never reported or read as evidence that the gain is below 10%.
2. For every primary comparison, the ratio and its 90% interval are reported against 0.90 as well as 1. When the interval's upper bound is below 0.90 but the Holm-adjusted test does not reject, the report says so descriptively, giving the ratio and both bounds. A useful model must not disappear behind the conservative gate without a visible trace of the evidence.

## 9. Validity gate

The official run is the first run whose outputs pass every check. A failed run is logged as a deviation, its outputs kept, and the cause fixed before a rerun.

1. **Data:** every download matches its hash in the lock file.
2. **No look-ahead:** for every target day, no model or regression input has a settlement time after 08:30 UK local time on D−1 (checked value by value); no NESO publication used has `publishTime` after 09:30.
3. **NESO reconstruction:** for daytime and evening half-hours (settlement periods 17–48), the reconstructed NESO forecast equals NESO's own recorded forecast (performance file) in at least 95% of half-hours over the full window; every mismatch is listed.
4. **Model outputs:** finite, the requested horizon exactly, median equal to the 0.5 quantile, identical on repetition for a sample of days.
5. **Responsiveness:** moving the last observed half-hour moves each model's forecast.
6. **Regression:** a hand-computed forecast for three sample days, by an independent implementation, matches the pipeline's to 0.1 MW.
7. **Weights:** each model's weights file matches its recorded SHA-256.

## 10. Pre-written results sentences

Every sentence names the window, the ratio and its interval.

| Result | Sentence |
| --- | --- |
| No credible improvement | "Over [window], [model], zero-shot, did not forecast GB demand a day ahead credibly better than the simple regression (error ratio r; 90% interval a–b, descriptive)." |
| Improvement, not practically meaningful | "Over [window], [model] forecast credibly better than the simple regression (error ratio r; 90% interval a–b, descriptive), but the gain was not shown to reach the [m]% threshold set in advance." |
| Improvement; interval below 0.90 but threshold not confirmed after adjustment | Add to the second sentence: "The ratio's 90% interval (a–b, descriptive) lies below 0.90, but after adjustment for the six tests the gain is not confirmed to reach [m]%." |
| Practically meaningful improvement | "Over [window], [model] forecast credibly better than the simple regression, by at least the [m]% set in advance as practically meaningful (error ratio r; 90% interval a–b, descriptive)." |
| NESO comparison | "Against NESO's published forecast, [model]'s error ratio was r (90% interval a–b, descriptive). NESO's forecast uses weather information the model did not have." |

Every primary sentence is followed by the leakage note: "The model may have seen GB demand from this period in training; the perturbation check [raised / did not raise] a flag, which makes memory [more / no more] plausible but cannot rule it out."

## 11. Procedure

1. Agree this plan (decisions in Section 12).
2. Write and test the scripts on synthetic data and on the real inputs with stand-in forecasters only: `common.py`, `fetch.py`, `inputs.py`, `baselines.py`, `stats.py`, `models.py`, `synth.py`, `run.py`, `selftest.py`, `power.py`, with model versions pinned in `requirements-models.txt`. The models are tested on synthetic series only, including a pilot of the L1 perturbation size. **No model forecasts real GB demand before the tag,** for the backtest or the prospective column.
3. Run the power check; record it in this plan.
4. Freeze: commit, tag `demand-plan`, write `PLAN_LOCK.json` (tag, file hashes, data hashes, weights hashes, versions, seeds).
5. Run until one attempt passes the gate.
6. Recompute every number independently from the saved forecasts; write the note with the Section 10 sentences; archive with a DOI.

**What counts as a deviation** after the tag: any change to the data, timing, forecasters, settings, windows, statistics, threshold, gate or wording; a second passing run; a comparison not listed here reported as anything but exploratory; an unreported listed output.

## 12. Decisions taken before freezing (3 November 2026)

| # | Decision | Settled as |
| --- | --- | --- |
| 1 | m, the minimum useful reduction | 10%, a judgement about when switching from a transparent regression to a third-party model is worth it (Section 8). Not changed after any model result |
| 2 | Primary test family | Six one-sided tests, Holm-adjusted together: improvement and practically meaningful improvement, for each of three models (Section 6) |
| 3 | Comparator | The weekly-lag regression: 365 complete training days ending at D−2; England and Wales bank holidays, with the GB limitation stated (Section 4.2) |
| 4 | Model context | 2,688 continuous UTC half-hours ending at or before 08:30 on D−1, the same for every model (Section 4.1) |
| 5 | L1 perturbation | 300 MW, 20 draws, the same draws for every forecaster, inputs only; flag defined in Section 7 |
| 6 | Prospective column | **Starts at the first issue time after the tag and lock file**, not before. Daily saving is automated at 09:30 UK time and records inputs, forecasts, hashes, versions and failures, pushed the same day; it is never adjusted by hand. A separate short plan is written before any prospective forecast is scored. Any pre-tag model run is a synthetic pilot and is never scored |
| 7 | Gap rule | Runs of one or two missing half-hours filled on a straight line, in model contexts only, and listed; longer runs exclude the day. Chosen after counting gaps in the real INDO and before any model forecast of it (Section 4.1) |
