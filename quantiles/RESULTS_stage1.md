# Quantile study, stage 1 (backtest pilot): results

Andy Moran (Heaviside Analytics) · 28 November 2026 · Plan frozen at tag `quantiles-plan` (5885516). Generated figures: `results_stage1.json` and `results_stage1.md`, from `score.py` at 93d8ab2, committed at d77ed2f. This note interprets them; where they differ, the generated files govern (`REVISIONS.md` 2).

## Headline (PLAN.md §10)

In a backtest the foundation model may have seen in training, a day-ahead position on GB demand set from Chronos-2's quantile forecasts, averaged with equal weight over quantile levels 0.10 to 0.90 (cost ratios from 1:9 to 9:1), cost clearly less than one set from its own median with a band built from its recent errors (score 370 against 373 MW, ratio 0.990, 90% interval 0.983 to 0.998; practically equal), and clearly more than one set from NESO's forecast with a band built the same way (ratio 1.320, 90% interval 1.263 to 1.374; practically higher). Chronos-2's 80% intervals contained outturn 71.7% of the time (too narrow; practically too narrow).

This is a pilot on 931 of the 960 backtest days; the first 29 lack the error history to dress. Stage 2, on days no model could have seen, reports in April 2027 (PLAN.md §5).

## In plain terms

A supplier whose shortfall costs *k* times its surplus should position at the *k*/(1 + *k*) quantile. Chronos-2 gives those quantiles directly. Anyone can also build them in a spreadsheet, by adding the quantiles of a forecast's recent errors to it. On the decision, the two came out the same in practice: Chronos-2's own quantiles cost about 1% less than its median with a spreadsheet band. That difference is clear but below the 5% the plan set as practically meaningful. The alternative a supplier actually has, NESO's free forecast with the same spreadsheet band, cost about a quarter less than either: 24% less than Chronos-2's quantiles (1/1.320) and 25% less than its spreadsheet band (280 against 373 MW).

## The model's bands are overconfident, but carry a signal

Chronos-2's 80% bands held outturn 71.7% of the time, and its 98% bands 95.3%. Both are too narrow, strictly and practically, in every set. Its bands are also narrower than its spreadsheet band: 2,365 MW against 2,890 for the 80% interval.

The narrowness has a pattern. By block of the day, its 80% coverage was:

| 00:00–05:30 | 06:00–11:30 | 12:00–17:30 | 18:00–23:30 | evening window, 16:00–19:30 |
|---|---|---|---|---|
| 80.2% | 66.9% | 63.0% | 76.7% | 69.5% |

The overconfidence runs from morning into the early evening; only the night and late evening are near nominal. INDO is demand net of embedded solar, so solar uncertainty is one candidate cause. Winter peaks fall after sunset, which argues against it being the only one. This note tests neither.

The bands do widen before a miss, weakly. Within each month, the quarter of days with Chronos-2's widest bands had 35% more median error than the quarter with its narrowest (ratio 1.347, 90% interval 1.220 to 1.470). The median monthly correlation of width with error was 0.20, positive in 24 of 30 months. The spreadsheet band carries no such signal: its widest days had less error than its narrowest (0.845). So sharper but overconfident bands with some signal cost about the same as wider, honest bands with none.

## Where the quantiles earn their keep, and where every band fails

| Set | days | against its dressed median | against dressed NESO | against the dressed regression |
|---|---|---|---|---|
| All | 931 | 0.990 (clearly lower; practically equal) | 1.320 (clearly higher) | 0.914 (clearly lower) |
| T1, the coldest tenth | 96 | 0.937 (clearly and practically lower) | 1.304 (clearly higher) | 0.925 (not clearly different) |
| Winter | 180 | 0.989 (not clearly different) | 1.386 (clearly higher) | 0.915 (clearly lower) |
| Evenings | 931 | 0.977 (clearly lower; practically equal) | 1.324 (clearly higher) | 0.872 (clearly lower) |
| Calendar days | 40 | 1.018 (not clearly different) | 2.092 (clearly higher) | 1.067 (not clearly different) |
| Stage 2's season | 264 | 0.993 (not clearly different) | 1.317 (clearly higher) | 0.927 (clearly lower) |

Every ratio against dressed NESO is also practically higher. On the coldest days, Chronos-2's quantiles beat its spreadsheet band by 6%, clearly and practically: the one place they earn their keep.

Calendar days defeat every band. Bank holidays, Easter, Christmas to New Year and clock changes are among Chronos-2's inputs, yet its 80% coverage fell to 58%, its dressed median's to 57% and the regression's to 60%. NESO's fell to 71%. On these days Chronos-2 cost twice what dressed NESO did, but no more than its own spreadsheet band or the regression's.

By level, the gain over the dressed median is clear only from 0.45 to 0.85. At the tails (0.01, 0.05, 0.95 and 0.99) no difference is detectable. The dressed tails rest on about seven errors each, so that comparison is noisy by construction: the evidence does not show that the tails add nothing, only that it cannot see whether they do.

## Robustness and the named cost ratios

Against the dressed median, the practical label, practically equal, held under all five dressing variants. The clear label did not: windows of 28 days gave 0.976 (clearly lower), 90 days gave 0.998 (not clearly different). Against dressed NESO, both labels held under all five (1.291 to 1.323).

At each named cost ratio, *k* = 1, 3, 4 and 9 (levels 0.50, 0.75, 0.80 and 0.90), dressed NESO cost clearly and practically less, by ratios from 1.258 to 1.312. Against the dressed median, Chronos-2 was practically equal at all four. Of the ten primary comparisons, 4 were clearly lower, 5 clearly higher and 1 not clearly different.

## Predictions, scored (PLAN.md §9)

| Prediction | Result | Verdict |
|---|---|---|
| A: practically equal to the dressed median; clearly and practically higher than dressed NESO | 0.990, practically equal; 1.320, clearly and practically higher | held |
| A: any gain in the centre, not the tails | clear only from 0.45 to 0.85 | held |
| A: robust to the dressing | practical label held under all five variants; clear label did not (90-day window) | partly failed |
| A: dressed NESO clearly and practically better at every named ratio | 1.258 to 1.312, all clearly and practically higher | held |
| B: Chronos-2's 80% and 98% intervals too narrow and practically too narrow, overall and in winter | 71.7% and 95.3% overall; 73.0% and 96.2% in winter; all four labels | held |
| B: coverage furthest from nominal in the evening block | furthest in 12:00–17:30 (63.0%), then 06:00–11:30 (66.9%); 18:00–23:30 was 76.7% | failed |
| B: dressed 80% bands consistent on all days, too narrow on T1 | overall, NESO's and the regression's were strictly too narrow (78.7%, 77.9%), though practically consistent; on T1 only NESO's was too narrow | failed |
| C: within months, widest quarter more error than narrowest; correlation below 0.3; ratio smaller than over the year | 1.347; 0.20; 1.347 against 1.418 | held |
| D: coverage worst on calendar days | 58.4%, the lowest of any set | held |

## What stage 2 can and cannot settle

Stage 2 has about 130 winter days. Resampling stage 1's days in the same season, it would label a difference of 10.5% (lower) or 13.5% (higher) from dressed NESO as clear in at least half of such windows, and 2.5% from the dressed median. So stage 2 can confirm or refute the 32% gap to NESO. It cannot resolve a 1% edge over the dressed median: a result like stage 1's will read "not clearly different" in April by construction, and that will not be a reversal.

## Caveats

- **Training overlap.** Chronos-2's disclosed training data contain no GB demand (`ASSUMPTIONS.md` A16), but overlap with the backtest cannot be ruled out. Overlap would flatter Chronos-2's median. Its native quantiles and its dressed band share that median, so the comparison between them is the least exposed. The gap to NESO is the most exposed, and could be understated.
- **Labels are not tests.** Every label comes from an unadjusted 90% interval; ten primary comparisons make one clear result weak evidence on its own.
- **No money.** Costs are in MW of pinball loss. The tolerances behind the practical labels are conventions, not measured costs (PLAN.md §7).
- **No fix is tested.** Widening Chronos-2's bands would change the decision cost, which this study has not measured. A single widening factor could not repair coverage that is already right overnight. Recalibration is outside this plan.

## Checks (PLAN.md §8)

All passed:
- **Check 1.** All 960 days' 0.5 quantiles equal the scored `chronos2_A` forecast exactly, with the largest difference 0.0 MW.
- **Reproduction.** The medians' mean daily errors match checkpoint 0 to 0.01 MW.
- **No look-ahead.** Changing outturn on D − 1 or later leaves D's dressed bands unchanged.
- **Arithmetic.** Half-hour counts match, including clock changes; a perfect forecast scores 0; the 0.5 level is half the mean absolute error to 0.0 MW.
- **Hashes and synthetic check.** Every input matched its hash, and the synthetic check passed with this script.

Crossing quantiles were sorted in 130 scored half-hours, by at most 52.4 MW; sorting never moved the 0.5 quantile, and raw and sorted results agree to three decimals.
