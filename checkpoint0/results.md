# Checkpoint 0: results (exploratory, descriptive)

Backtest days the foundation models may have seen in training. LightGBM is untuned. One series (GB INDO), day ahead. Ratios are mean daily error over that of the comparator; 90% intervals by moving-block bootstrap. A difference is described only where the interval excludes 1.

**Headline (PLAN.md §7):** In a backtest the foundation models may have seen in training, Chronos-2 forecast GB demand 19.3% more accurately than a LightGBM model with library defaults, on equal inputs. The LightGBM model was 11.8% less accurate than a weather regression given the same information: with library defaults, the trained tree model did not beat the linear one. A live, preregistered test starts on 1 April 2027.

Days scored: 960; dropped (a forecaster missing a half-hour): 0.

## Table 1: mean daily error, and ratio to LightGBM (defaults)

| Forecaster | Mean daily error (MW) | Ratio to LightGBM | 90% interval |
|---|---|---|---|
| Chronos-2 (calendar and weather) | 916 | 0.807 | 0.778–0.837 |
| TimesFM 2.5 (weather) | 1,474 | 1.299 | 1.242–1.354 |
| Weather regression | 1,014 | 0.894 | 0.869–0.920 |
| LightGBM, defaults | 1,134 | 1 | — |
| Timestral (calendar and weather; not ranked) | 1,103 | 0.973 | 0.942–1.006 |
| Timestral (weather; not ranked) | 1,089 | 0.960 | 0.930–0.993 |

## Tables 2 and 3: LightGBM against the weather regression, and the sensitivity settings

| LightGBM | Mean daily error (MW) | Ratio to regression | 90% interval | MW difference | Chronos-2 ratio to it | 90% interval |
|---|---|---|---|---|---|---|
| LightGBM, defaults | 1,134 | 1.118 | 1.088–1.149 | +120 | 0.807 | 0.778–0.837 |
| LightGBM, S1 settings | 1,061 | 1.046 | 1.023–1.070 | +46 | 0.863 | 0.837–0.893 |
| LightGBM, S2 settings | 1,094 | 1.079 | 1.052–1.107 | +80 | 0.836 | 0.807–0.866 |

## Table 4: by meteorological season, pooled across years (LightGBM defaults)

| Season | Days | Chronos-2 / LightGBM | TimesFM 2.5 / LightGBM | Regression / LightGBM | LightGBM / regression |
|---|---|---|---|---|---|
| DJF | 180 | 0.710 (0.656–0.769) | 1.127 (1.000–1.274) | 0.778 (0.717–0.837) | 1.286 (1.192–1.398) |
| MAM | 261 | 0.805 (0.752–0.867) | 1.318 (1.240–1.409) | 0.898 (0.869–0.929) | 1.113 (1.076–1.150) |
| JJA | 276 | 0.856 (0.818–0.891) | 1.274 (1.195–1.347) | 1.010 (0.976–1.048) | 0.990 (0.953–1.024) |
| SON | 243 | 0.850 (0.797–0.911) | 1.464 (1.375–1.577) | 0.881 (0.852–0.921) | 1.135 (1.087–1.175) |

## Table 5: Chronos-2 / LightGBM (defaults), before and after 2025-10-30

| Period | Days | Ratio | 90% interval |
|---|---|---|---|
| before | 593 | 0.807 | 0.766–0.848 |
| after | 367 | 0.808 | 0.771–0.847 |

## Table 6: for gate G2 (Chronos-2 against LightGBM, defaults)

| Window (years pooled) | Days | c | Ratio | 90% interval | Edge |
|---|---|---|---|---|---|
| summer 180 days (Apr-Sep) | 540 | 0.59 | 0.851 | 0.812–0.876 | 14.9% |
| winter 120 days (Dec-Mar) | 240 | 0.58 | 0.704 | 0.656–0.750 | 29.6% |

Table 7 (cost) is reported separately, from WP2.
