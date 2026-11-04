# Zero-shot forecasting models and GB electricity demand

Results note · 4 November 2026 · Andy Moran (Heaviside Analytics)

A preregistered test of three off-the-shelf forecasting models on Great Britain's national electricity demand, a day ahead. Plan: `plan/PLAN.md`, frozen at tag `demand-plan` (3 November 2026, 18:04 UTC) and locked in `plan/PLAN_LOCK.json`, with one amendment (`plan/LOCK_AMENDMENT_1.json`, tag `demand-plan-dev1`). Two deviations are logged in `deviations/DEVIATIONS.md` and summarised below.

**Result.** Used zero-shot, two of the three models forecast GB demand credibly better than a simple weekly-lag regression: Chronos-2 by about 7% and Timestral by about 9%. Neither was shown to reach the 10% gain set in advance as the smallest worth switching for. TimesFM 2.5 was no better than the regression. NESO's own forecast, which uses weather, had about half the error of every model.

## The question

Do zero-shot forecasting models forecast GB national demand a day ahead better than a simple regression, and by enough to matter? How do they compare with NESO's published forecast?

Every forecaster had the same information. At 09:30 UK time on the day before the target day, each saw national demand up to 08:30 that morning and forecast every half-hour of the next day. The models saw eight weeks of history and nothing else: no weather, no calendar, no training on GB data. The regression saw the same demand history, two lagged days (D−2 and D−7), the day of the week, bank holidays and the Christmas period. NESO's forecast is the one Elexon had published by 09:30.

Each forecast was scored by its mean absolute error in megawatts over the half-hours of the target day, against NESO's initial national demand outturn. The scoring window is 1 January 2024 to 31 October 2026: 1,035 days, none excluded.

## The run

**Official run: attempt 2,** 4 November 2026, finishing at 15:11 UTC, on the author's machine. All sixteen gate checks passed (plan Section 9, as amended by deviation 1). An independent recalculation from `results/attempt2/forecasts.csv`, written separately from the study's code, reproduced every ratio to six decimal places and every Holm decision.

**Attempt 1 failed two checks.** Both failures lay in the checks, not in the forecasts:

- **The NESO check compared two different forecasts.** On 94 days, NESO's performance file holds values that appear in no Elexon publication available at 09:30. The check was replaced by an exact, independent check against Elexon's raw publications; the threshold was not lowered.
- **The repeatability check tested batch size, not repetition.** Timestral repeats exactly; a different batch size changes its forecasts by 0.006 MW.

The author and the AI assistant saw attempt 1's results before these fixes. So the deviation log recorded a prediction before attempt 2 ran: every forecast, and every number attempt 1 reported, would be identical. **The prediction held.** All 49,680 forecast rows, and every primary, secondary and leakage number, are identical in the two attempts.

**Deviation 2** records that the amendment's lock file reached GitHub only after attempt 2. The code attempt 2 ran was on GitHub, with a server timestamp, before the run started; the lock file records the hashes of that same code.

## Primary results

Each model against the regression over the full window, labelled "inside possible training data". A ratio below 1 means the model's error was smaller.

| Model | Mean daily error (MW) | Ratio to regression | 90% interval (descriptive) | Better at all? | Better by 10%? |
| --- | --- | --- | --- | --- | --- |
| Regression | 1,553 | — | — | — | — |
| TimesFM 2.5 | 1,568 | 1.009 | 0.978–1.042 | No | No |
| Chronos-2 | 1,441 | 0.928 | 0.902–0.955 | **Yes** | Not shown |
| Timestral | 1,413 | 0.910 | 0.885–0.935 | **Yes** | Not shown |

The two right-hand columns are the six one-sided tests, Holm-adjusted together at a family-wise 5% level. One-sided p-values for "better at all", before adjustment: TimesFM 2.5 0.695; Chronos-2 and Timestral below 0.0005 (no bootstrap draw out of 2,000 reached a ratio of 1). For "better by 10%": TimesFM 2.5 1.000, Chronos-2 0.962, Timestral 0.730.

The plan's sentences, written before any forecast was made:

- **TimesFM 2.5.** Over 2024–2026, TimesFM 2.5, zero-shot, did not forecast GB demand a day ahead credibly better than the simple regression (error ratio 1.009; 90% interval 0.978–1.042, descriptive).
- **Chronos-2.** Over 2024–2026, Chronos-2 forecast credibly better than the simple regression (error ratio 0.928; 90% interval 0.902–0.955, descriptive), but the gain was not shown to reach the 10% threshold set in advance.
- **Timestral.** Over 2024–2026, Timestral forecast credibly better than the simple regression (error ratio 0.910; 90% interval 0.885–0.935, descriptive), but the gain was not shown to reach the 10% threshold set in advance.

Both intervals reach above 0.90, so a gain below 10% is consistent with the data. "Not shown to reach 10%" is not evidence that the gain is below 10% (plan Section 8). The power check expected exactly this outcome as likely: a true gain of 10–14% would usually be reported this way.

**Leakage note,** for each model: the model may have seen GB demand from this period in training; the perturbation check did not raise a flag, which makes memory no more plausible but cannot rule it out.

## NESO's forecast

| Model | Ratio to NESO, full window | 90% interval | Ratio to NESO, after the model's release | 90% interval | Days |
| --- | --- | --- | --- | --- | --- |
| TimesFM 2.5 | 2.258 | 2.179–2.337 | 2.179 | 2.058–2.313 | 412 |
| Chronos-2 | 2.076 | 2.002–2.151 | 2.088 | 1.956–2.214 | 367 |
| Timestral | 2.035 | 1.961–2.108 | 2.510 | 2.468–3.200 | 17 |

NESO's mean daily error was 694 MW. Against NESO's published forecast, every model's error was about twice as large. NESO's forecast uses weather information the models did not have.

One NESO forecast was badly wrong. On 5 March 2025, Elexon's 08:45 publication put demand at 13,625 MW at midday, against an outturn of 25,524 MW. The plan scores what was published at 09:30, so this forecast counts as published. Leaving that day out moves the NESO ratios by less than 0.01.

## Checks on the results

**Leakage (L1).** Adding random noise (standard deviation 300 MW) to every input half-hour, in 20 draws, raised the regression's error by 0.8%. The models' errors changed by −0.1% (TimesFM 2.5), −0.05% (Chronos-2) and +0.8% (Timestral). A model relying on memory of the exact series should degrade more than the regression; the flag needs an excess of 0.05. The largest excess was Timestral's, 0.0004, so no flag was raised.

**Robustness.** Rescored against NESO's later ND series instead of the initial outturn, over the 1,017 days it covers, the ratios barely move: 1.001 (TimesFM 2.5), 0.921 (Chronos-2) and 0.904 (Timestral).

**After each model's release.** Over the days after each model was published, against the regression: TimesFM 2.5 1.024 (0.985–1.063; 412 days from 15 September 2025), Chronos-2 0.965 (0.923–1.006; 367 days from 30 October 2025) and Timestral 1.089 (1.018–1.206; 17 days from 15 October 2026). These windows show only that a model was published before the period, not that it never saw GB demand. Seventeen days are too few to read anything into Timestral's figure.

## Exploratory findings

None of these was tested. They describe where the errors lie.

- **Ranking.** Timestral had slightly smaller errors than Chronos-2 (ratio 1.020; 1.007–1.034), and both beat TimesFM 2.5.
- **Seasons.** The models gained most in winter: Timestral's mean daily error was 1,592 MW against the regression's 1,876. In spring they did no better than the regression: 1,521 MW for Timestral against 1,512.
- **Time of day.** The models gained most overnight. At 03:00, Chronos-2's mean error was 869 MW against the regression's 1,099. Every forecaster, NESO included, had its largest errors between 12:30 and 13:00, probably because that is when solar generation behind the meter, which the transmission network does not see, varies most.
- **Bank holidays.** On bank holidays every model lost to the regression: the models' mean daily errors were 2,387–2,549 MW against the regression's 1,800. The regression has a bank-holiday term; the models know nothing of the calendar.
- **NESO's own record.** NESO's performance file agrees with Elexon's 09:30 record on 91.2% of daytime half-hours. Excluding the 94 days on which they differ, or using the file's values on those days, moves the NESO ratios to between 2.06 and 2.29. These checks were added by deviation 1, after attempt 1, and are not preregistered.

## What this study cannot show

These limits were stated in the plan before any forecast was made.

- **Freedom from training leakage.** The models may have seen GB demand from 2024–2026 in training. The leakage check cannot rule that out. A prospective test, forecasting days that had not yet happened when the forecast was made, is the only clean defence; it starts after this note.
- **Generality.** One series, one country, one horizon.
- **Fine-tuning.** Zero-shot only. A model trained on GB data might do better or worse.
- **Weather.** Neither the models nor the regression saw weather. NESO did, which may explain much of its lead.
- **Value.** The study measures accuracy in megawatts, not money.

## What it means

Off the shelf, with eight weeks of history and nothing else, two of the three models beat a transparent regression by 7–9%. That is a real gain, credibly above zero, but not shown to reach the 10% that would justify replacing a simple model with a third party's. The regression's advantage on bank holidays shows what the models miss: they know nothing of the calendar or the weather. NESO's lead shows how much the weather is worth. The next test in this series gives the models and the regression the same weather forecasts, to see how much of that gap they close.

## Run record

- **Models:** TimesFM 2.5, `google/timesfm-2.5-200m-pytorch` @ `1d952420`, weights SHA-256 `2f776efe…`, `timesfm` 3.0.2. Chronos-2, `amazon/chronos-2` @ `29ec3766`, weights `ddcda3c7…`, `chronos-forecasting` 2.3.2, `cross_learning` off. Timestral-209M, `mistralai/Timestral-209M` @ `9874d252`, weights `1456effb…`, `timestral` 1.0.0 @ `a534bdbd`. Median forecasts; 64 days per call; every setting written out in `code/models.py`.
- **Environment:** torch 2.15.0 (CPU), numpy 2.4.6, pandas 3.1.0, Python 3.11.18, Linux under WSL2.
- **Data:** downloaded once on 3 November 2026 and hashed in `data/fetch_manifest.json`: Elexon initial national demand outturn and day-ahead demand forecast publications; NESO's day-ahead forecast performance file and historic demand data; GOV.UK bank holidays for England and Wales. One missing half-hour (03:30 on 29 December 2023) was filled in the models' inputs under the plan's gap rule; it lies in the input history of 54 target days.
- **Outputs:** `results/attempt2/`: `results.json`, `forecasts.csv`, `daily_mae.csv`, `exclusions.csv`, `context_fills.csv` and `neso_file_mismatches.csv`. Attempt 1's outputs are kept unchanged in `results/attempt1/`.
- **Statistics:** moving-block bootstrap over days, blocks of 7, 2,000 draws, seed 20261103; leakage check seeds 20261104 onwards.

Contains BMRS data © Elexon Limited copyright and database right 2026. Supported by National Energy SO Open Data.

## Use of AI

The author is responsible for all design decisions, modelling runs, interpretation and final content. AI tools (including Claude, ChatGPT, Microsoft Copilot, DeepSeek, Kimi and Z.ai) were used for drafting text, writing and testing scripts, checking outputs, and sanity-checking reasoning and code. The work is designed so that AI output is never taken on trust: results are calculated numerically from the data and checked against known ground truths, and assumptions are checked against original sources. All modelling was executed by the author, who retains full responsibility for the analysis and results.
