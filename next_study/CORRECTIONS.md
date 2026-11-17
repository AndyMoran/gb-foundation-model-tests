# Corrections to the next study's committed files

Committed files are not edited. Errors found after commit are recorded here, with the commit that holds them, the error and the fix.

## 1. The direction of c in the power check (15 November 2026)

**Where:** `power_check.py`, docstring, "Grid" and "Decision rule", committed as `332631e` before running.

**Error:** The specification called c = 0.7 "a pessimistic bound for LightGBM, on the assumption that a tree model's errors are less correlated with Chronos-2's than a linear model's". That has the direction backwards. The more the two forecasters' errors are correlated, the more noise cancels in the ratio and the higher the power. A value of 0.7 sits above the measured 0.54, so it is the optimistic case, not the pessimistic one. A LightGBM less correlated with Chronos-2 than the regression would have c below 0.54. The sentence "If LightGBM's errors are at least as correlated with Chronos-2's as the regression's are, power exceeds the 0.7 case" is also wrong; in that case power is at least that of the measured case.

**Effect on the decision:** none. The rule's top branch read the c = 0.7 cell (50.8% power) and its second branch read the measured-c cell (33.1%). Both fell short of 80%, so the rule gave "next winter" either way. Had either cleared 80%, the branches would have been in the wrong order: "this winter" would have rested on the optimistic case.

**Fix:** The measured c, 0.54 (winter, 120-day window), is the reference value. It is a measurement, not a bound. In E5 the regression already had the calendar and weather, so matched inputs in the next study give no reason to expect a higher c. LightGBM's correlation with Chronos-2 is unknown and may be lower, which would lower power. Every power figure the next study's brief cites uses the measured c for its window: 0.54 for winter, 0.47 for summer (`summer_edge.json`). The c = 0.7 figures in `power_check.json` and `power_check.md` are read as an optimistic sensitivity only.

## 2. The rule's fallback assumed next winter would be powered (15 November 2026)

**Where:** `power_check.py`, "Decision rule", `332631e`.

**Error:** The rule's last branch, "Next winter: otherwise", assumed that a later winter would be adequately powered. The results show it would not. At a true 10% edge, no feasible winter window reaches 80%: 33–51% for 120 days from December to March, and 49–62% for 150 days from November to March. The limit is winter's variance, not the year.

**Fix:** The live window is summer 2027, 180 days from April to September. That window was in the committed specification. It was chosen on the strength of the power calculation, before any live data existed. Power is 93.7% at the backtest's summer edge (10.8%) and 72.2% at the low end of its interval (7.7%), with c = 0.47 (`summer_edge.py`, committed as `12d419b` before running).

## 3. G2's fallback table had no row for a likely case (17 November 2026)

**Where:** `PROJECT.md`, §4, "Gate fallbacks", G2 table, as committed in `0013c4a` and `b7cc0f3`.

**Error:** Order 1 needed both pairs at 80% power at alpha 0.025; order 2 fired only if exactly one pair reached 80% at 0.05. If both pairs reached 80% at 0.05 but not both at 0.025, no row applied, and the table fell through to "checkpoint 1 is descriptive". That case is likely: power at the low end of the summer edge was 72.2% at 0.025 (`summer_edge.json`). Found by a reviewer.

**Effect:** none. G2 has not run.

**Fix:** Order 2 now reads "not order 1, and at least one pair at 80% at 0.05": the family is the pair with the higher power at 0.05, alone at 0.05, with a tie-break fixed in advance. The pairs are now named in `PROJECT.md` §4.

