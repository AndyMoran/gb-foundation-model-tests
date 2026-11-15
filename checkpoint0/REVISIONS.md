# Checkpoint 0: revision log

Every change to the LightGBM script and its environment before the scored run, including each failed check and its fix, as required by `PLAN.md` §5. Changes after the scored run are deviations, logged here the same way.

| Date | Change | Commit | Reason |
|---|---|---|---|
| 2026-11-15 | Plan frozen | 8b2fc8c (tag `checkpoint0-plan`) | — |
| 2026-11-15 | Environment `gbcp0` created as a conda clone of `gbwx`; LightGBM 4.7.0 installed with `python -m pip`. numpy 2.4.6 and pandas 3.1.0 were unchanged by the install, matching the weather study. Full package list: `env_gbcp0.txt` | [Andy's commit] | `gbwx` runs the weather study's daily prospective push to 31 March 2027 and is left untouched |
| 2026-11-15 | WP2 sample days drawn (`wp2_days.py`, `wp2_days.csv`): 20 days, 5 per meteorological season, seed 20261115, before any timing or LightGBM run | this commit | `PLAN.md` WP2 |
