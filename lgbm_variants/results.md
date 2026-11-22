# LightGBM variants: results (descriptive backtest)

960 days. Mean daily error: each day's mean absolute error over its half-hours. Ratios are to the weather regression's mean daily error; 90% intervals from a 7-day moving-block bootstrap (2,000 draws, seed 20261119). An interval wholly below 1 beats the regression; wholly above, trails it; otherwise level.

**Headline (PLAN.md §7):**

In a 960-day backtest, the best of five pre-specified LightGBM variants (V1) beat a weather regression: 0.984 times its error (90% interval 0.973–0.994).

In a backtest it may have seen in training, Chronos-2 had 0.918 times that variant's error (90% interval 0.887–0.948); the variant was chosen on these same days, so its figure is optimistic.

Best variant: **V1** (lowest mean daily error among V1, V2, V3, V4, V5).

## Against the regression

| Forecaster | Mean daily error (MW) | All days | Winter (Nov–Mar) | Other months | T1 (coldest tenth) | Chronos-2 ÷ forecaster |
|---|---|---|---|---|---|---|
| LightGBM S1 | 1,061 | 1.046 (1.022–1.068) | 1.125 (1.082–1.172) | 1.002 (0.979–1.024) | 1.218 (1.113–1.337) | 0.863 (0.835–0.892) |
| V1 | 998 | 0.984 (0.973–0.994) | 0.992 (0.975–1.009) | 0.979 (0.966–0.992) | 0.976 (0.944–1.017) | 0.918 (0.887–0.948) |
| V2 | 3,089 | 3.045 (2.008–4.492) | 2.044 (1.381–2.894) | 3.594 (2.100–5.796) | 2.973 (1.287–5.641) | 0.296 (0.204–0.450) |
| V3 | 1,171 | 1.154 (1.116–1.194) | 1.273 (1.189–1.375) | 1.089 (1.055–1.113) | 1.564 (1.328–1.815) | 0.782 (0.753–0.811) |
| V4 | 1,070 | 1.055 (1.033–1.077) | 1.130 (1.091–1.170) | 1.014 (0.991–1.037) | 1.198 (1.116–1.298) | 0.855 (0.828–0.885) |
| V2c (control) | 1,036 | 1.021 (1.000–1.040) | 1.086 (1.049–1.127) | 0.985 (0.963–1.003) | 1.178 (1.102–1.272) | 0.884 (0.856–0.915) |
| V5 | 1,024 | 1.010 (0.990–1.028) | 1.051 (1.017–1.087) | 0.987 (0.966–1.006) | 1.121 (1.034–1.213) | 0.894 (0.863–0.927) |
| Regression, two years (shown, not compared) | 1,024 | 1.009 (1.001–1.017) | 1.006 (0.991–1.021) | 1.011 (1.001–1.020) | 1.010 (0.967–1.042) | 0.894 (0.864–0.927) |
| Chronos-2 | 916 | 0.902 (0.873–0.933) | | | | |
| Weather regression | 1,014 | 1 | 1 | 1 | 1 | |

## Hypotheses (PLAN.md §6)

- **H2** (V1 is the best variant): supported; the best was V1.
- **H3** (every variant's winter ratio below S1's): not supported. By variant: V1 supported, V2 not supported, V3 not supported, V4 not supported, V5 unclear.
- **H4** (V2 below V2c): not supported.

"Unclear" means the point estimates point the hypothesis's way but the intervals overlap (REVISIONS.md item 15).

## Cost (PLAN.md §5 item 5; 20 sample days, 4 threads)

| Forecaster | Seconds per day (median) | Peak memory (MB) |
|---|---|---|
| V1 | 0.866 | 959 |
| V2 | 0.718 | 958 |
| V2c | 0.639 | 959 |
| V3 | 2.721 | 958 |
| V4 | 0.696 | 960 |
| V5 | 1.144 | 958 |
| REG2 | 0.475 | 959 |
