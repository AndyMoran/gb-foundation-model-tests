# Figures for the asymmetric cost note

- `cost_ratio_chart.png` (`cost_ratio_chart.py`): Chronos-2's cost-weighted error minus the weather regression's at each tested cost ratio, over all half-hours and for the daily peak on the coldest tenth of days, with 90% intervals. The curves are the exact differences between the ratios, *k* × ΔU + ΔO. The x axis is logarithmic.

The script reads `../results.json`, so each figure can be checked against `../RESULTS.md`. To redraw: `python cost_ratio_chart.py` (matplotlib). The colours passed a colour-blind separation check.
