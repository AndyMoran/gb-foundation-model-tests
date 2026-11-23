# Figures for the arbitrage note

- `timing_chart.png`: each forecaster's missed spread on all 960 days, with 90% intervals. Lower is better.
- `combination_chart.png`: the mean daily error of each forecast averaged with NESO's, minus NESO's own, with 90% intervals. Below 0 means averaging helped.

Both come from `arbitrage_charts.py`, which reads `../results.json`, so each figure can be checked against `../RESULTS.md`. The note compares each forecaster with the regression; comparisons between other pairs, such as Chronos-2 and NESO, were not tested directly. To redraw: `python arbitrage_charts.py` (matplotlib). The colours passed a colour-blind separation check.
