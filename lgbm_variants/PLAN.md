# What makes LightGBM competitive on GB demand?

Andy Moran (Heaviside Analytics) · 19 November 2026 · **Status: draft, to be frozen at tag `lgbm-variants-plan` before any variant runs**

For: a forecasting team deciding how to build a trained model for GB demand, and a reader checking whether a foundation model beats the strongest trained model, not a weak one.

**The question:** of five changes aimed at how LightGBM learns the heating response, which closes its gap to the weather regression, and does Chronos-2 still beat the best of them?

## 1. Why, and why these five

In checkpoint 0, LightGBM lost to a weather regression: 11.8% more error with library defaults, 4.6% with the S1 settings (1,061 MW against 1,014). It matched the regression in summer and fell behind in winter. The tails study then ruled out one explanation. No backtest day gave LightGBM a forecast temperature below the coldest in its training year (closest margin 0.40 °C), so the gap is not temperatures outside its training range. And the gap was already there on ordinary winter days: 10.5% behind the regression on the days of the coldest months that were not among the coldest tenth (`tails/RESULTS.md`).

That points at how LightGBM learns the heating response, not at the cold edge. The regression fits 48 half-hour models with temperature, its square and wind chill built in. LightGBM fits one model across all half-hours, from raw temperature, wind and solar, and builds any curve from steps. Each variant below changes one part of that. They were chosen after the seasonal and tails results were seen; their results have not been.

## 2. Non-claims

This study does not establish:
- live performance: the variants and Chronos-2 are scored on the backtest, and Chronos-2 may have seen it in training;
- that the best variant is the best LightGBM possible: five variants are tried, not a search;
- an unbiased error for the best variant: it is chosen on the same 960 days it is scored on, so its figure is optimistic;
- which part of a winning variant does the work, beyond what its one change isolates.

## 3. What has been seen before this plan

Everything about LightGBM with defaults, S1 and S2: overall, by season, by block, and on the tails study's day sets (`checkpoint0/results.md`, `tails/RESULTS.md`). The regression's and Chronos-2's results, likewise. No variant below has been run on any day.

## 4. The forecasters

The reference, the comparison and the variants, all on the weather study's 960 backtest days (16 March 2024 to 31 October 2026), with the same inputs, refitted for each target day D on complete days D−366 to D−2 unless stated:

| Name | What changes from S1 | Tests |
|---|---|---|
| Weather regression | (reference) | — |
| LightGBM S1 | (baseline: checkpoint 0's forecasts, `checkpoint0/lightgbm_forecasts.csv`) | — |
| **V1: residual** | The regression is fitted on the training days first. LightGBM S1 is then fitted to the regression's residuals on those days, with the same features. The forecast is the regression's forecast plus LightGBM's forecast of the residual. | Smooth heating curve from the regression; trees for what is left |
| **V2: linear leaves** | `linear_tree=True`: each leaf holds a linear model of the numerical features in its branch, not a constant. | Slopes instead of steps |
| V2c: control for V2 | As V2 without linear leaves. | Separates V2's two changes |
| **V3: per-slot** | 48 models, one per local clock slot, each with S1's settings on that slot's rows; `slot` is dropped as a feature. | The structure of the regression, without its formula |
| **V4: regression's terms** | Three features added: Tc (temperature minus its mean over the slot's training rows), Tc² and Tc × wind, built exactly as the regression builds them. | Hands LightGBM the regression's heating shape |
| **V5: two winters** | Training days D−731 to D−2. | More winter rows per fit |
| Regression, two years | The regression with training days D−731 to D−2. Shown beside V5, not compared. | Whether a longer window helps both |
| Chronos-2 | (checkpoint 0's forecasts, calendar and weather, `chronos2_A`) | Does it still beat the best? |

**Why V2 needs a control.** LightGBM does not support the L1 objective with linear leaves. Its documentation, in the source of version 4.7.0, the version checkpoint 0 used (`include/LightGBM/config.h`; `checkpoint0/env_gbcp0.txt`), says: "`regression_l1` objective is not supported with linear tree boosting". S1 uses L1. So V2 also switches to the L2 objective (`regression`). V2c makes the same switch without linear leaves, so V2 against V2c isolates the linear leaves. In both, `slot` is declared categorical, so the leaf models do not treat a clock slot as a number. The same documentation says categorical features are used for splits but not in the linear models, and recommends rescaling. Numerical features in V2 and V2c are standardised by their mean and standard deviation over each fit's training rows.

**V1's residuals are in-sample.** The regression's fitted values on its own training days are slightly better than its forecasts would be, so V1's trees see residuals somewhat smaller than the errors they will meet. Out-of-sample residuals would need a regression forecast for every training day back to March 2023, which does not exist. The note states this.

**V5 depends on data not yet held.** A two-year window for the first backtest day reaches back to March 2022. The demand history held (`data/indo.csv`, 68,734 half-hours) starts in December 2022, and ERA5 for the training weather is cached from March 2023. Demand for March to November 2022 and ERA5 for March 2022 to March 2023 must be fetched and checked before V5 runs (§9, step 1). The Copernicus key is read from `~/.cdsapirc` only. If either cannot be fetched and checked by 3 December 2026, V5 and the two-year regression are dropped, and `REVISIONS.md` says why.

**Fixed for every variant:** S1's settings (500 rounds, learning rate 0.05, 31 leaves, depth 8, row and column sampling 0.8 with bagging frequency 1), seed 20261115, deterministic, row-wise, 4 threads, one day per call (draft rule 4.8). Only the change named in the table differs.

## 5. Metrics

As checkpoint 0. For each forecaster:
1. **Mean daily error** over the 960 days, and its ratio to the regression's, with a 90% interval (moving-block bootstrap, 7-day blocks, 2,000 draws, seed 20261119, percentile method).
2. **The same ratio in winter (November to March) and in the other months,** with intervals.
3. **The ratio on the tails study's coldest tenth of days** (T1, from the committed `tails/days.csv`), with its interval.
4. **Chronos-2's ratio to each variant,** with its interval.
5. **Time and memory per forecast day,** as in checkpoint 0's cost check, on 20 sample days.

**Reading rule:** as in checkpoint 0. No p-values, and nothing is called significant. A variant beats, or trails, the regression only where the interval of its ratio lies wholly below, or wholly above, 1. Otherwise it is level with it, which is not evidence that the two are equal.

**The best variant** is the one with the lowest mean daily error over the 960 days, among V1, V2, V3, V4 and V5 (V2c is a control and cannot be chosen). Ties go to the earlier in that list. This is the choice `PROJECT.md` §4 makes for the LightGBM comparator: on error, never on power. Because it is chosen on the days it is scored on, its figure carries the optimism stated in §2.

## 6. Hypotheses, written before any variant runs

- **H2:** V1 has the lowest mean daily error of the five. Reason: it gives the trees the regression's heating curve and asks them only for what the regression misses, the design TNEI used for NESO (a GAM for the mean, LightGBM for the residual quantiles).
- **H3:** every one of V1 to V5 has a lower winter ratio to the regression than S1.
- **H4:** V2's mean daily error is lower than V2c's.

Each is reported as supported, not supported, or unclear. H3 and H4 compare point estimates and state whether the intervals of the two ratios overlap; they do not claim a difference where they do.

## 7. Headlines, fixed now

The note and any post lead with two sentences, chosen by `score.py` by rule and copied unchanged. "V" is the best variant's name, "R" its ratio to the regression and "L–U" its interval.

| Result | First sentence |
|---|---|
| Interval wholly below 1 | "In a 960-day backtest, the best of five pre-specified LightGBM variants (V) beat a weather regression: R times its error (90% interval L–U)." |
| Interval includes 1 | "In a 960-day backtest, the best of five pre-specified LightGBM variants (V) drew level with a weather regression: R times its error (90% interval L–U)." |
| Interval wholly above 1 | "In a 960-day backtest, the best of five pre-specified LightGBM variants (V) still trailed a weather regression: R times its error (90% interval L–U)." |

Second sentence, whatever the first: "In a backtest it may have seen in training, Chronos-2 had C times that variant's error (90% interval L–U); the variant was chosen on these same days, so its figure is optimistic."

Every other result follows: each variant's row, the winter and T1 ratios, H2 to H4, and the cost.

## 8. Checks before scoring

As checkpoint 0's WP1, extended to each variant:
1. **No leakage:** an assertion in the code that every training row is from a day on or before D−2 (D−731 to D−2 for V5).
2. **Independent build:** each variant's training matrix and target-day rows are rebuilt by a second function sharing no code beyond the time rules and calendar, and must match exactly. For V1, the regression's in-sample residuals are rebuilt the same way.
3. **Synthetic recovery:** on invented demand with a known heating curve, V1 to V5 run without error and V1 recovers the curve to a stated tolerance.
4. **Determinism:** two runs of each variant on 20 sample days give identical forecasts.
5. **Call mode (draft rule 4.8):** one day per call, so no forecast depends on another target day.

Only the scoring step reads outturn for the backtest days. The checks read it only as training data, as each forecaster does.

## 9. Work

1. **Data for V5** (by 3 December): fetch INDO for March to November 2022 and ERA5 for March 2022 to March 2023, record their SHA-256 in the fetch manifests, and check them as the weather study checked its inputs. Commit the manifests, never the data.
2. **`gb-weather-private/weather/lightgbm_variants.py`**: the variants, built on `lightgbm_weather.py` without changing it, with the checks in §8 and a `--synthetic` mode. Committed before it runs. Its forecasts, `lgbm_variants/forecasts.csv`, are committed after, with their SHA-256.
3. **`lgbm_variants/score.py`**: checks the hashes of every forecast file it reads (`weather_study/results/forecasts.csv`, `calendar_forecasts.csv`, `checkpoint0/lightgbm_forecasts.csv`, `tails/days.csv`, and the new forecasts), computes §5, picks the headline sentences and the hypotheses' outcomes by rule, and writes `results.json` and `results.md`. Committed before it runs; outputs committed after.
4. **`lgbm_variants/RESULTS.md`**: the note, with non-claims first. It follows `WRITING.md`.

Any change to a script after it has run on the backtest is a deviation, logged in `lgbm_variants/REVISIONS.md` with its date, commit and reason. Both scripts run on Andy's machine, where the data are held.

## 10. Timing

| Step | Target |
|---|---|
| Plan reviewed and tagged `lgbm-variants-plan` | 26 November 2026 |
| V5's data fetched and checked, or V5 dropped | 3 December 2026 |
| Variants script committed; checks passed; forecasts committed | 10 December 2026 |
| Scored; note published | 17 December 2026 |

The study must finish before gate G2 (January 2027). If checkpoint 1 runs, its LightGBM comparator is chosen from configurations backtested under committed scripts before G2 (`PROJECT.md` §4), so the best variant here would become it.

## Sources

- LightGBM 4.7.0, `include/LightGBM/config.h`, the documentation of `linear_tree` (read from the source distribution, 19 November 2026).
- TNEI (2024), the QWID FLEXER report for NESO, pp. 18–19 and 24, as cited in `checkpoint0/RESULTS.md`.
- `checkpoint0/RESULTS.md` and `tails/RESULTS.md` for every earlier figure.
