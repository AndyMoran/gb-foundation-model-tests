# Disagreement value: revisions

Choices made after the plan was frozen. None changes a forecaster, a measure, a set, a label rule, a prediction or a headline.

1. **Which tag freezes the plan.** The tag `disagreement-plan` was made before the plan's commit, 3a260a2, had been pushed, so it points to ddb2798, which holds no `disagreement/` files. The repository's rules stop tags being deleted, so it stays where it is. The plan is frozen at `disagreement-plan-3a260a2`, made on 24 November 2026 before any script existed, and `score.py` checks `PLAN.md` against that tag. The plan's text is the same either way.
2. **Readings of the plan that `score.py` fixes.**
   - *Groups by size of disagreement (measure B) and by price stress (C)* are equal groups by rank, ties broken in time order. Each group's largest |*F* − *N*| is reported as its threshold. The fixed bands are 0 to 250 MW inclusive, then over 250 to 500, over 500 to 1,000, and over 1,000. A group or band with no disagreement has an **undefined** value per MWh.
   - *Groups within a set* are formed from that set's own half-hours.
   - *The evening set* gives value per GWh of evening demand, as in the imbalance study (its REVISIONS 11).
   - *Accuracy (measure F)* is the ratio of mean daily absolute errors. "Credibly below 0.9" means the upper end of its 90% interval is below 0.9.
   - *The tail (measure E)* carries a 90% interval beside each figure.
   - *The sign-flip null* runs on all days. For value in the top quarter by price stress, each day's value from its stressed half-hours is divided by that whole day's demand. The 7-day blocks are counted in calendar days from the first scored day, and use seed 20261128 (the null's seed plus one). The share of null draws at or above the observed figure is reported beside each label.
   - *The year-by-year split* uses whole days by UK date. Each period's bootstrap uses the stage 1 seed on that period's days alone.
   - *The headline* has no sentence for an undefined value. If one occurs, the run stops rather than writing a headline the plan did not fix.
3. **The imbalance study's REVISIONS 15, applied from the start.** An interval with no finite draws is labelled **undefined**. The scored days must equal the imbalance study's as a set, and that check runs before any output is written. No half-hour is resampled: every measure is built from per-day sums, and whole days are resampled. Every file is opened with `with`, every JSON write uses `default=str`, and the interval function is named `ci90`. Paired intervals use only draws where both measures are finite. The synthetic gate uses 400 draws.
4. **Every check runs before any output.** If any check in PLAN.md §8 fails, nothing is written and the failures are printed.
5. **The synthetic data use whole numbers** for outturn, prices and disagreements, so that a forecaster with no value has exactly zero, not floating-point dust. A first draft used fractional sizes and prices; the noise forecaster's value came out at about −3 × 10⁻¹⁵ £ per GWh, with an interval just below 0, and was labelled "clearly negative". The fix is in the test data only; nothing real was read.
