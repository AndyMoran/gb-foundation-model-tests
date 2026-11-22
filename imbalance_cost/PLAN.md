# Imbalance cost, indicative: what would the forecast misses have cost?

Andy Moran (Heaviside Analytics) · 22 November 2026 · **Status: parked.** Written to fix the idea while it is fresh. Not tagged. To be finished after the asymmetric cost study (`asymmetric/`) is run and published.

For: a supplier or trader asking what a better day-ahead demand forecast is worth in money, and which forecaster's misses cost least.

**The question.** If a price-taking supplier bought its forecast demand day-ahead and settled every miss at the GB imbalance price, what would each forecaster's misses have cost over the backtest, and what cost ratio between shortfalls and surpluses do real prices imply?

## 1. Why

The asymmetric study asks at what cost ratio the ranking of two forecasters flips, without knowing any real ratio. This study takes the ratio from prices.

**The cost of a miss.** A supplier buys its forecast *F* day-ahead at price *P*_DA. On the day, demand is *A*, and the gap *A* − *F* is settled at the System Price *P*_SP. Compared with a perfect forecast, the miss costs

**cost = (*A* − *F*) × (*P*_SP − *P*_DA) × 0.5 h**, per half-hour, in £.

The same formula covers both directions. A shortfall is bought at *P*_SP instead of *P*_DA; a surplus is sold back at *P*_SP.

**The twist.** GB settles imbalance at a single System Price, so the cost can be negative:
- **A miss in the same direction as the system** costs money. A supplier short when the system is short pays a high System Price.
- **A miss against the system** earns money. A supplier long when the system is short sells its surplus at that high price.

So real prices give a different, sometimes negative, implied cost ratio in every half-hour, unlike the asymmetric study's fixed *k*. The study reports that implied ratio, especially on cold evenings, as the realistic range for *k*.

## 2. What this study will not show

- **A real supplier's bill.** INDO is national demand. No supplier holds all of it, and a national forecast error is a large part of the system's imbalance, which helps set the System Price. The study treats the price as given: a price-taking supplier whose demand follows the national shape, scaled to a stated share. Real costs depend on a portfolio's own shape, hedges and trading.
- **Day-ahead auction prices,** unless their licence allows (§4).
- **The value of a forecast to NESO,** whose costs come from balancing actions, not settlement.
- **Live performance.** The foundation models may have seen these days in training.

The result is indicative: a comparison of forecasters under one stated, simple trading rule.

## 3. What is known before this plan

Every result of the earlier studies, and, once it is run, of the asymmetric study. No price has been read for the backtest.

## 4. Data, to be checked before the plan is finished

- **System Price,** per settlement period, from Elexon's BMRS. Open data, covered by the attribution in `ATTRIBUTION.md`. Check the dataset, its history over the backtest, and any revisions between initial and final settlement runs; use the final run where available.
- **Day-ahead price.** The GB day-ahead auction prices (N2EX, EPEX) are licensed, not open. The open alternative is Elexon's Market Index Price, which reflects short-term trading, not the auction alone. Check both licences and choose before the plan is tagged; if only the Market Index Price is usable, the note says so in its title.
- **Fetch and check** as for V5's data: a committed script, hashes in a manifest, gaps listed, no data committed.

## 5. Measures, to be fixed when unparked

- **Total and mean cost** of each forecaster's misses over the 960 days, per GWh of demand served and per MWh of absolute error, for a stated supplier share.
- **The difference between forecasters,** with 7-day block-bootstrap intervals, as in the earlier studies.
- **Cold days and cold evenings** separately, on the tails study's T1 and the asymmetric study's evening window.
- **The implied cost ratio** in each half-hour, from the sign and size of *P*_SP − *P*_DA, summarised as a distribution, and compared with the asymmetric study's break-even ratios.
- **The share of cost earned or lost** by misses with or against the system.

## 6. Not yet decided

- The supplier's share, and whether results are reported per unit so that the share cancels.
- Whether to add a sensitivity in which the price responds to the error, rather than taking it as given.
- Whether the battery project, which asks whether real decisions change, is the better home for any part of this.
- A prediction, to be written before any price is read.

## Sources

- `asymmetric/PLAN.md` for the cost-ratio framing; `tails/PLAN.md` for T1; `lgbm_variants/RESULTS.md` for V1.
- Elexon BMRS documentation and licence, and the day-ahead price licences: to be opened before the plan is finished.
