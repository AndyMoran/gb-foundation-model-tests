# Disagreement value, stage 1 (backtest pilot): results

Andy Moran (Heaviside Analytics) · 24 November 2026 · Plan frozen at tag `disagreement-plan-3a260a2` (REVISIONS 1). Generated figures: `results_stage1.json` and `results_stage1.md`, from `score.py` at a402043. This note interprets them; where they differ, the generated files govern.

## Headline (PLAN.md §10)

In a backtest the foundation models may have seen in training, Chronos-2's day-ahead demand forecast had 1.31 times the daily error of NESO's (90% interval 1.26 to 1.36), and a supplier that bought it instead of NESO's would have **neither clearly gained nor lost** (9 £ per GWh of demand, 90% interval −11 to 28); for the weather regression the figure was −1 £ per GWh (−20 to 18). Where Chronos-2 disagreed with NESO most (the largest quarter of its disagreements), each MWh of disagreement was worth 0.07 £ (−0.80 to 0.90), against −0.45 £ (−0.91 to 0.07) in the smallest quarter.

This is a pilot. The foundation models may have seen these days in training, and stage 2, on days no model could have seen, carries the primary result (PLAN.md §5).

## The coin-flip test

Imagine a second forecaster that disagrees with NESO by exactly as much as Chronos-2 does in every half-hour, but tosses a coin each morning to decide which way. It has Chronos-2's sizes and none of its sense of direction. The sign-flip null (PLAN.md §7 D) builds 2,000 such copies and asks where Chronos-2 falls among them.

| Chronos-2, all 953 days | observed | coin-flipped copies, 5th to 95th percentile | copies that did as well or better | label |
|---|---|---|---|---|
| Hit rate | 50.0% | 49.3% to 50.7% | 52% | within chance |
| Sign payoff, £ per MWh traded | 0.36 | −0.40 to 0.40 | 7% | within chance |
| Value, £ per GWh | 9.4 | −20.3 to 20.2 | 25% | within chance |

The labels are the same when the coin is tossed once a week instead of once a day. Chronos-2's disagreements with NESO point the right way exactly half the time. Its £9 per GWh is the same size chance would produce, and a quarter of the coin-flipped copies earned as much. Sign payoff comes nearest the edge, but 7% of copies still matched it. At this sample size, Chronos-2 is indistinguishable from a forecaster with no sense of direction.

The plan predicted this for every forecaster (§9). It held for Chronos-2, the regression, their average, LightGBM V1 and Chronos-2 without calendar. It failed for two, both on the losing side: below.

## What the test can and cannot detect

A null result is only as good as the test's ability to see something. Over 953 days, the coin-flipped copies' value ranges about ±£20 per GWh, and so does the bootstrap interval around each forecaster's value. So the test would flag a gain or loss of roughly £20 per GWh or more, and would miss a real edge of £9.

It did flag losses. LightGBM S1 lost £50 per GWh against NESO (90% interval −100 to −13) and was **worse than chance** on hit rate (48.8%), sign payoff and value, by day and by week. TimesFM's hit rate (49.2%) was also worse than chance. Both were clearly negative in the evening window (S1 −104, TimesFM −72 £ per GWh). So the instrument is not blind. It found reliably bad forecasters and no reliably good one.

## For a supplier

On this evidence, a supplier has no reason to switch from NESO's forecast to Chronos-2. Chronos-2 is about 31% less accurate, and its settlement edge cannot be told apart from a coin-flipped copy of itself. No forecaster tested came within the project's 10% bar of NESO's accuracy (rule 7.5): the best, the average of Chronos-2 and the regression, had 1.19 times NESO's error (1.15 to 1.23).

## Predictions, scored (PLAN.md §9)

| Prediction | Result | Verdict |
|---|---|---|
| Divergence: Chronos-2's error ratio above 1.2, interval wholly above 1; its value positive | 1.31 (1.26 to 1.36); +9 | held |
| A: Chronos-2 positive, not clearly; regression near 0; average positive, not clearly | +9, −1, +4; none clear | held |
| A, year by year: Chronos-2 positive in both full years, clear in neither | +15 (−21 to 46), then −1 (−25 to 26) | failed: the second year is slightly negative |
| B: higher value per MWh in the top disagreement quarter than the bottom, not clearly, for Chronos-2 and the average; flat for the regression | +0.51 and +0.10, not clear; regression +0.36, not clear | held broadly; Chronos-2's groups do not rise steadily (below) |
| C: more than half of each forecaster's value in the top stress quarter | S1 80%; Chronos-2 31% and the average 23%, of totals not clearly different from 0 | not testable where the total is near 0 (REVISIONS 6) |
| D: hit rates between 49% and 53% for every forecaster | S1 48.8% | failed for S1 |
| D: Chronos-2's hit rate above 50% in the top stress quarter | 50.4% (49.1 to 51.5) | held at the point estimate, within chance |
| D: every forecaster within chance on the null | S1 worse than chance on all three measures; TimesFM on hit rate | failed for S1 and TimesFM |
| E: 8 January 2025 is Chronos-2's best day | +1,005 £ per GWh that day; days were not ranked | not scored (REVISIONS 7) |

## The other measures

**B. Does value grow with disagreement?** No. Chronos-2's value per MWh of disagreement runs −0.45, 0.44, 0.98 and 0.07 £ from its smallest quarter to its largest. It peaks in the third quarter and falls back in the largest, the opposite of what skill would show. No forecaster's top-minus-bottom difference is clearly positive. S1's is clearly negative: its largest disagreements cost most.

**C. Does value concentrate where prices are stressed?** Not for Chronos-2. Its value per MWh of disagreement in the most stressed quarter minus the calmest is £0.42 (−1.69 to 2.32). Shares of value mean something only where the total is clearly non-zero (REVISIONS 6). Where it is, losses concentrate in stress: 80% of S1's loss falls in the most stressed quarter of half-hours.

**E. The tail of days.** Chronos-2's worst 5% of days averaged −£914 per GWh and its best 5% +£874. Its daily swings are about a hundred times its mean. NESO's misses and Chronos-2's take turns being the costlier, and over 953 days they nearly cancel. On 8 January 2025, the NESO Electricity Margin Notice, switching to Chronos-2 would have earned £1,005 per GWh; switching to the regression would have lost £2,901.

**F. Accuracy.** Every forecaster had more daily error than NESO, from 1.19 times (the average) to 2.32 times (TimesFM). None is credibly below 0.9.

**Year by year.** Chronos-2's value was +15 £ per GWh in the year to March 2025, −1 in the year to March 2026, and +16 in the seven months to October 2026, with every interval spanning zero. Three numbers that move between −1 and +16 show no trend. They are weak evidence either way, and they do not change what stage 2 should expect: the plan's prediction, not clearly different from zero.

## Counting the labels

The run labels about 109 intervals: measures A, B and C for seven forecasters in four sets, the paired comparison in each set, and A in each of three periods. With unadjusted 90% intervals, about 11 would read "clear" with no effect behind them. Six do, all negative: S1 four times, TimesFM twice. The null adds 84 labels, of which 8 read "worse than chance": S1's three measures and TimesFM's hit rate, each by day and by week. None reads "beyond chance".

So the clear results are fewer than chance alone would produce, but they are not scattered: every one is a loss, and they come from two forecasters. That pattern looks like a real effect in S1 and TimesFM, not noise. Single unlabelled figures that look striking, such as Chronos-2's winter sign payoff (£1.08 per MWh, 0.13 to 2.08), are one of many and are not reported as findings.

## What this does not show

- **That Chronos-2 has no edge.** It shows any edge is smaller than about £20 per GWh, the smallest this backtest could detect.
- **Live performance.** These are backtest days the models may have seen in training. Stage 2 scores the live window from April 2027, with the replication criterion fixed in REVISIONS 8.
- **A trading strategy.** No costs, position limits or market impact (PLAN.md §3).
- **Value against the market.** NESO's forecast is a public benchmark, not the market's expectation.

## Checks (PLAN.md §8)

All passed before any output was written: the scored days equal the imbalance study's 953; exposure reconciles with error for every forecaster; each forecaster's value equals NESO's net exposure minus its own, matching `imbalance_cost/results_stage1.json` to £0.01 per GWh; every file matched its recorded hash; and the synthetic check passed 13 of 13.

Seeds 20261126 (bootstrap) and 20261127 (null); 2,000 draws in 7-day blocks. Script SHA-256 310c4d1f5c6c923f40b06e3f89a43fccc14d928b2cb605c6cefc76c306ee885b.
