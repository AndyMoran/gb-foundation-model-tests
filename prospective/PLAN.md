# Prospective forecasts: a leakage check for the demand study

Analysis plan · draft for agreement · 4 November 2026 · Andy Moran (Heaviside Analytics)

> **Status.** No prospective forecast has been made. This plan, the daily forecast script and their lock are frozen at tag `prospective-plan` before the first one is. The scoring script is written, tested and frozen before any prospective day is scored (Section 8).
>
> **What the author has seen.** The full results of the demand study (DOI [10.5281/zenodo.23962005](https://doi.org/10.5281/zenodo.23962005)), including its daily errors, which this plan uses to fix its reference ratios (Section 4) and to judge how precise one winter can be (Section 7).

## 1. The question

**Did the demand study's results depend on the models having seen GB demand in training?**

The study scored three zero-shot models on 1 January 2024 to 31 October 2026, a period that may lie inside their training data. A memorised series would flatter a model. Days that had not happened when a model's weights were fixed cannot be memorised. So each model forecasts every day of one winter, before the day begins, with the weights pinned in the study; the forecasts are pushed to GitHub the day they are made. If the backtest gains depended on memory, the models should do clearly worse on these days than in the same months of the backtest.

Secondary: do the models still beat the regression on days none of them can have seen?

## 2. The forecasts

Everything is computed exactly as in the demand study, with its locked code (`code/`, as amended at tag `demand-plan-dev1`), settings, weights and bank-holiday file:

- **Issue:** for target day D, at 09:30 UK time on D−1. A scheduled task starts `prospective/forecasts/forecast_daily.py` at 09:45; it retries every 15 minutes until 11:30 if Elexon's latest half-hours have not arrived.
- **Inputs:** Elexon's initial national demand outturn (INDO) for half-hours ending at or before 08:30 UK time on D−1, fetched that morning. The series is cut at that point before anything else is done with it.
- **Forecasters:** TimesFM 2.5, Chronos-2 and Timestral (median forecasts, eight weeks of context, the plan's gap rule), the weekly-lag regression, and the seasonal naive. One day per model call; the demand study used batches of 64 days, which changes Timestral's forecasts by at most 0.006 MW.
- **Record:** for each D, a file of every forecaster's forecast for every half-hour of D, and a record of the run: start and finish times, the last input half-hour, the SHA-256 of the input series, any filled half-hours, the code, weights and package versions. The script refuses to run if any locked file or weights file differs from the lock, or if the tag `prospective-plan` is not on GitHub.
- **Late runs:** if the scheduled run fails, a run started by hand later on D−1 also counts, provided its push reaches GitHub before 00:00 UK time on D. Its inputs are cut at 08:30 like any other, and its start time is recorded.
- **Push:** the script commits the day's files, pushes them, and confirms the push reached GitHub; if it cannot, it logs the failure. NESO's forecasts need no daily saving: Elexon timestamps every publication, so the scorer fetches them afterwards, exactly as in the study.

## 3. Which days count

- **Window:** target days from the first after the tag to **31 March 2027**, about 145 days.
- **A day counts only if** its forecast file reached GitHub before 00:00 UK time on D, by GitHub's server-side push record (the repository's activity log). Commit dates, which the author's machine sets, are not evidence. A day without such a push is missing; no day is ever forecast after the fact.
- **A day counts for every forecaster or for none.** If any of the five forecasts, or INDO outturn for any half-hour of D, is missing, the day is excluded and listed.
- **Outturn:** INDO, fetched after 31 March 2027 and hashed, as in the study.

## 4. The reference: the same months of the backtest

The models gain most in winter and little in spring, and their gains vary from winter to winter. So each prospective ratio is compared with the backtest's ratio over the **same calendar span**: the backtest days whose day and month fall within the counted prospective span (for a span of 6 November to 31 March, 383 days). The values below are fixed now, from `results/attempt2/daily_mae.csv`, for that span; the scorer recomputes them for the exact span counted.

| Model | Reference ratio to the regression, pooled | Jan–Mar 2024 | 6 Nov 2024 – 31 Mar 2025 | 6 Nov 2025 – 31 Mar 2026 |
| --- | --- | --- | --- | --- |
| TimesFM 2.5 | 0.966 | 0.946 | 0.943 | 1.004 |
| Chronos-2 | 0.894 | 0.900 | 0.842 | 0.948 |
| Timestral | 0.884 | 0.863 | 0.838 | 0.947 |

The latest winter was the weakest for all three models, including Timestral, which may have seen it in training. That points to year-to-year variation, and it is why the interpretation below uses the range across winters as well as the pooled value.

## 5. Statistics

- **Daily error and ratio:** as in the study: mean absolute error in MW over the half-hours of each day; ratio of a model's mean daily error to the regression's over the counted days, R.
- **Resampling:** moving-block bootstrap over days, block length 7, 2,000 draws, seed **20270401**.
- **Primary tests:** three one-sided tests, one per model, Holm-adjusted together at a family-wise 5% level. Null: the prospective ratio is no worse than the reference (R ≤ R_ref). Alternative: it is worse (R > R_ref). p-value: the share of bootstrap ratios at or below R_ref. The reference is treated as fixed; its own sampling error is ignored, which makes the test slightly more likely to flag.
- **Secondary tests:** three one-sided tests of improvement on the regression (R < 1), Holm-adjusted together, as in the study.
- **Descriptive:** 90% intervals for every ratio; each model against NESO's forecast; each ratio against 0.90, the study's 10% threshold; ratios by month.

## 6. Pre-written results sentences

For each model, the primary result is reported in one of three sentences, chosen by these rules:

| Rule | Sentence |
| --- | --- |
| Flagged, and R above the worst backtest winter's ratio for that model | "On days that did not exist when its weights were fixed, [model] did credibly worse than in the same months of the backtest (ratio R, 90% interval a–b, against R_ref), and worse than in any backtest winter. That is consistent with its backtest gains having depended partly on memory of GB demand; it cannot prove it." |
| Flagged, but R within the backtest's range of winters | "On days that did not exist when its weights were fixed, [model] did credibly worse than the backtest's average for the same months (ratio R, 90% interval a–b, against R_ref), but within the range seen from one backtest winter to another. This one winter cannot separate memory from year-to-year variation." |
| Not flagged | "On days that did not exist when its weights were fixed, [model] did not do credibly worse than in the same months of the backtest (ratio R, 90% interval a–b, against R_ref). This gives no evidence that its backtest results depended on memory of GB demand." |

Secondary, for each model, using the demand study's sentences: "On days that did not exist when its weights were fixed, [model] [forecast / did not forecast] credibly better than the simple regression (ratio R; 90% interval a–b, descriptive)."

## 7. What this can and cannot show

- **Precision.** In the backtest, one winter's ratio had a 90% interval of about ±0.05 to ±0.11. So only a large drop, of roughly 0.08 or more against the reference, is likely to be flagged. A modest effect of memory would go undetected.
- **Year-to-year variation.** The backtest's winters already differ by about 0.11 for each model. One prospective winter cannot fully separate memory from an unusual winter; the three-way rule in Section 6 says so in advance rather than after.
- **What it does establish.** The forecasts cannot have been memorised, and they are on record before their outcomes. A ratio close to the reference would show that the backtest's results hold on genuinely unseen days.
- **Unchanged limits.** One series, one horizon, zero-shot, no weather, accuracy not money.

## 8. Procedure

1. Agree this plan.
2. Test `forecast_daily.py` (`selftest_prospective.py --models`): on synthetic data, a forecast made from a series cut at 08:30 on D−1 equals the demand study's forecast for D; nothing after the cut-off moves a forecast; a missing latest half-hour triggers a retry; a failed push is detected and logged; and the three real models run inside the script, on synthetic data only. Then run the script once on the real inputs with the stand-in forecaster, without pushing (the demand study's lesson: every check must run on the real inputs before the freeze). No model forecasts real GB demand before the tag.
3. Freeze: `prospective/freeze_prospective.py` writes `prospective/PROSPECTIVE_LOCK.json` (hashes of this plan, the script, the locked study code, the bank-holiday file and the weights), commits it, tags `prospective-plan`, pushes, and confirms the tag and the commit are on GitHub before reporting success.
4. Schedule the daily task. Forecasting starts at the next 09:45 run.
5. Before 31 March 2027, write the scoring script, test it on synthetic data and on the real data with stand-in forecasts, including deliberately corrupted inputs it must reject, and freeze it under a short amendment to this plan.
6. After 31 March 2027, fetch outturn and NESO's publications, score once, recompute independently, and report with the Section 6 sentences.

**Deviations** are logged in `deviations/DEVIATIONS.md` under "Prospective", with the same rules as the study: any change after the tag to the forecasts, data, windows, statistics or wording; a missed or late day is not a deviation but is listed.

## 9. Lessons applied from the demand study

- The freeze reports success only once GitHub has the tag and the commit (deviation 2).
- Every run records its start time as well as its finish (deviation 2).
- Every check runs on the real inputs, and is shown to fail on corrupted input, before the freeze (deviation 1).
- The batch size is fixed and recorded.
