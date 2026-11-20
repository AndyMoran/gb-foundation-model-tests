# Context novelty: results (descriptive backtest)

Backtest days the foundation models may have seen in training. Peak error: the day's highest outturn half-hour minus the forecaster's highest forecast half-hour (MW); positive means the forecast peak was too low. Excess peak error: a forecaster's peak error minus the regression's. Δ: the mean over pairs of the novel day's excess minus its control's. 90% intervals resample the cold spells (PLAN.md §6).

**Headline (PLAN.md §8):**

In a backtest it may have seen in training, Chronos-2 under-forecast the daily peak, relative to a weather regression, by 1,241 MW more on cold days colder than its eight-week context than on matched cold days that were not (90% interval 589–1,765, above the 250 MW threshold set in advance).

The comparison rests on 10 pairs (5 in winter 2024-25 and 5 in winter 2025-26) in 4 cold spells. It does not estimate the difference for the 4 novel days that could not be matched (10 January 2025, 20 November 2025, 4 January 2026, 5 January 2026), which include the coldest days, or for the full cold tail.

H5 (Chronos-2): **meaningful penalty supported** at the 250 MW threshold. At 100 MW: meaningful penalty supported. At 500 MW: meaningful penalty supported.

## Δ by forecaster

| Forecaster | Δ (MW), 90% interval | Distinct bootstrap draws | Leave-one-spell-out range (MW) |
|---|---|---|---|
| Chronos-2 | 1,241 (589–1,765) | 35 | 1,017 to 1,551 |
| TimesFM 2.5, one day per call (exploratory) | 2,723 (732–4,171) | 35 | 2,050 to 3,402 |
| Timestral (descriptive) | 1,981 (999–3,152) | 35 | 1,541 to 2,664 |
| LightGBM S1 (descriptive) | 618 (147–1,184) | 35 | 247 to 815 |

## Δ by cold spell (description)

| Spell | Pairs | Chronos-2 | TimesFM 2.5, one day per call (exploratory) | Timestral (descriptive) | LightGBM S1 (descriptive) |
|---|---|---|---|---|---|
| 1 | 3 | 1,175 | 4,130 | 389 | 1,485 |
| 2 | 2 | 1 | 6 | 2,627 | −169 |
| 3 | 3 | 1,765 | 4,294 | 1,968 | 357 |
| 4 | 2 | 1,796 | 974 | 3,744 | 498 |

## The pairs (Chronos-2) and their balance

| Novel day | Control | Spell | Excess, novel (MW) | Excess, control (MW) | Difference (MW) | Δ mean temp (°C) | Δ daily min (°C) | Δ month |
|---|---|---|---|---|---|---|---|---|
| 2024-11-19 | 2024-11-28 | 1 | 2,648 | 1,007 | 1,640 | +0.17 | +0.58 | 0 |
| 2024-11-20 | 2025-11-21 | 1 | 2,851 | 592 | 2,259 | -0.38 | -0.03 | 0 |
| 2024-11-21 | 2025-12-31 | 1 | 2,216 | 2,591 | −375 | -0.83 | -0.83 | 1 |
| 2025-01-08 | 2026-01-10 | 2 | −429 | 97 | −526 | -0.35 | -1.27 | 0 |
| 2025-01-09 | 2025-01-11 | 2 | 1,132 | 604 | 528 | +0.03 | +0.36 | 0 |
| 2025-11-17 | 2025-11-26 | 3 | 1,931 | −1,927 | 3,858 | -0.01 | +1.44 | 0 |
| 2025-11-18 | 2025-12-30 | 3 | 549 | 1,707 | −1,158 | -0.04 | +0.21 | 1 |
| 2025-11-19 | 2024-11-22 | 3 | 2,182 | −413 | 2,595 | +0.23 | -0.97 | 0 |
| 2026-01-03 | 2025-01-03 | 4 | 1,704 | −434 | 2,138 | -0.39 | -0.17 | 0 |
| 2026-01-06 | 2025-01-04 | 4 | 1,423 | −32 | 1,455 | -0.11 | -2.26 | 0 |

## The unmatched novel days, one by one (description)

| Day | Weather regression: peak (excess) | Chronos-2: peak (excess) | TimesFM 2.5, one day per call (exploratory): peak (excess) | Timestral (descriptive): peak (excess) | LightGBM S1 (descriptive): peak (excess) |
|---|---|---|---|---|---|
| 2025-01-10 | −1,424 | −551 (873) | 424 (1,847) | −1,239 (185) | 1,290 (2,713) |
| 2025-11-20 | 214 | 2,341 (2,127) | 3,341 (3,127) | 2,073 (1,859) | 1,405 (1,191) |
| 2026-01-04 | −937 | 2,573 (3,510) | 6,853 (7,791) | 3,432 (4,369) | 1,525 (2,462) |
| 2026-01-05 | −858 | 3,943 (4,802) | 6,413 (7,271) | 5,867 (6,726) | 2,845 (3,703) |

## Unmatched comparison: every novel day against every T1∖N day (description, no interval)

| Forecaster | Mean excess, novel days (MW) | Mean excess, T1∖N (MW) | Difference (MW) |
|---|---|---|---|
| Chronos-2 | 1,966 | 419 | 1,547 |
| TimesFM 2.5, one day per call (exploratory) | 4,434 | 408 | 4,026 |
| Timestral (descriptive) | 2,546 | 732 | 1,814 |
| LightGBM S1 (descriptive) | 1,477 | 314 | 1,163 |

## The tails study's metrics on N (30 days; narrow complement 276, broad 930)

| Forecaster | Mean daily error (MW) | Ratio to regression | Shift, narrow | Shift, broad | Bias (MW) | Peak error (MW) | Worst day (MW) | 95th pct (MW) |
|---|---|---|---|---|---|---|---|---|
| Weather regression | 1,023 | 1.000 (1.000–1.000) | 1.000 (1.000–1.000) | 1.000 (1.000–1.000) | −346 (−578 to −96) | −259 (−539 to 30) | 2026-01-03: 1,790 | 2,718 |
| Chronos-2 | 1,137 | 1.112 (0.916–1.315) | 1.183 (0.977–1.402) | 1.241 (1.026–1.474) | 694 (435–929) | 1,459 (1,074–1,801) | 2026-01-05: 2,493 | 2,897 |
| TimesFM 2.5, one day per call (exploratory) | 2,857 | 2.792 (2.163–3.438) | 1.685 (1.327–2.070) | 1.792 (1.388–2.204) | 2,683 (2,014–3,248) | 3,725 (2,829–4,434) | 2024-11-19: 6,100 | 6,382 |
| Timestral (descriptive) | 1,544 | 1.509 (1.159–1.892) | 1.261 (0.966–1.577) | 1.405 (1.079–1.763) | 1,183 (688–1,685) | 1,848 (1,213–2,541) | 2026-01-05: 5,306 | 4,111 |
| LightGBM S1 (descriptive) | 1,188 | 1.161 (1.003–1.337) | 1.042 (0.911–1.184) | 1.115 (0.970–1.275) | 232 (−195 to 685) | 657 (179–1,174) | 2025-01-08: 3,845 | 3,117 |

## Provenance

```
{
 "public_commit": "3daf6fea9cfa76f2643e15431f890390af84cca4",
 "plan_tag_commit": "21b9a292d6f74bab07d44090cad8221d3e0efd4f",
 "script_sha256": "2f58712cdd7aaf448acbff09ba9e2da0e8b40c9ef2bb991b9b5dd29ec5515add",
 "tails_script_sha256": "07b508de203e595fe03c7369525b31601760e2c1cbdd76f7a47d4a9775f6f1ee",
 "pairs_csv_sha256": "cdf2b62d1b4b37dd9f6bef76e0c7ac23bc343e5658fd27133942b59a398f6494",
 "days_csv_sha256": "649e596f1c30506d6e41f6c5d3fbece8d17b374062c200a74490469f1c0c59c7",
 "files_sha256": {
  "weather_study/results/forecasts.csv": "b5f16561dcf1a26f8d7910bcca95cd137f677760c6f80153349034d4a85f7328",
  "weather_study/results/calendar_forecasts.csv": "976e27ef28d0eef1ddf351c6557af9f771c308b94f389fe0f06b84ec86c8e2fe",
  "checkpoint0/lightgbm_forecasts.csv": "812ffb251e7c4428ec1bb9f1e7467c51bc4f8ae55caf5b78b3fd0c840b6250cd",
  "weather_study/correction1/timesfm25_single_day_forecasts.csv": "479ec318925cc59cd1e4f56a29ef9bc10d297fe3f8fa012482e1ce130dccd821"
 },
 "seed": 20261120,
 "draws": 2000,
 "versions": {
  "python": "3.11.18",
  "numpy": "2.4.6",
  "pandas": "3.1.0"
 }
}
```
