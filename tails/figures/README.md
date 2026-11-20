# Figures for the tails note

Two charts drawn from the tables in `../RESULTS.md`. The numbers are typed into each script from those tables, not recomputed, so each can be checked against the note line by line.

- `paired_chart.png` (`paired_chart.py`): each forecaster's error relative to the weather regression, on other days of the same months and on the coldest tenth of days (T1). The axis is logarithmic, so each line's length is the narrow tail shift, listed with its 90% interval on the right.
- `peak_chart.png` (`peak_chart.py`): the mean daily peak error on T1 for each forecaster, with its 90% interval (outturn peak minus forecast peak; above 0 means the forecast peak was too low).

An earlier two-panel chart, `tails_chart.png`, was removed on 20 November: its left panel repeated the paired chart and its right panel is now `peak_chart.png`. It remains in the history at b008ce8.

Only the Chronos-2 and LightGBM S1 tail shifts were fixed in advance; the rest, and the peak errors, are among the study's many comparisons. To redraw: `python paired_chart.py` and `python peak_chart.py` (matplotlib).
