# Figures for the tails note

Two charts drawn from the tables in `../RESULTS.md`. The numbers are typed into each script from those tables, not recomputed, so each can be checked against the note line by line.

- `paired_chart.png` (`paired_chart.py`): each forecaster's error relative to the weather regression, on other days of the same months and on the coldest tenth of days (T1). The axis is logarithmic, so each line's length is the narrow tail shift, listed with its 90% interval on the right.
- `tails_chart.png` (`tails_chart.py`): left, the narrow tail shifts on T1 with their 90% intervals; right, the mean daily peak error on T1 (outturn peak minus forecast peak; above 0 means the forecast peak was too low).

Only the Chronos-2 and LightGBM S1 tail shifts were fixed in advance; the rest are among the study's many comparisons. To redraw: `python tails_chart.py` and `python paired_chart.py` (matplotlib).
