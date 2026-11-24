# Disagreement value: is a foundation model's small settlement edge over NESO skill or chance?

Andy Moran (Heaviside Analytics) · 24 November 2026 · **Status: draft, to be frozen at tag `disagreement-plan` before any script runs.** An exploratory study in two stages (§5), built on the imbalance study's data and code.

For: a supplier or trader deciding whether to switch from NESO's free day-ahead demand forecast to a foundation model, and anyone doing due diligence on that choice.

**The question.** A supplier that buys NESO's day-ahead demand forecast ahead of time could instead buy another forecaster's. Measured at real prices, what would switching have been worth, and does the value grow where the two forecasts disagree most and where prices are most stressed?

## 1. Why

**The 10% bar, both ways.** The project's rules set a 10% improvement in error as "the margin set as worth switching for" (`BENCHMARK_RULES.md` rule 7.5). On the backtest, Chronos-2 with calendar and weather had 9.7% less daily error than the weather regression with the same inputs (916 against 1,014 MW; checkpoint 0), just short of the bar at the point estimate. Against NESO's free public forecast it is the other way round: Chronos-2's error is about 31% higher (916 against about 700 MW). By the project's own rule there is no accuracy case for switching from NESO to Chronos-2. NESO is not a fair opponent, because it has more information, but a supplier's choice does not depend on fairness.

So the only remaining case for switching is settlement value: whether the foundation model's disagreements with NESO earn money at real prices. At the point estimate from the imbalance study, that value is about £10 per GWh, a penny per MWh. This study asks whether even that is skill or chance. A likely answer is a calibrated near-null, which is worth knowing and publishing.

**Why test pennies.** A penny per MWh is about 0.01% of a wholesale price near £70 per MWh. But it scales with volume: for a supplier serving 10 TWh a year, a real penny per MWh would be about £100,000 a year, before the cost of running the model. Whether that clears a supplier's costs is the supplier's judgement; this study gives the value in a form each can compare.

**Average against direction.** NESO is judged on average error: Ofgem's metric for its day-ahead demand forecast is a mean error in MW against a benchmark. A trader is judged on something else, being right when it matters and when others are wrong. A forecaster can lose to NESO on average and still earn money if its disagreements with NESO point the right way on the half-hours that count.

**The value of switching.** In each half-hour, buying a forecast *F* instead of NESO's *N* changes the supplier's position by *F* − *N*. The change is settled at the System Price *SP* rather than the Market Index Price *MIP*. So switching is worth

**v = (*F* − *N*) × (*SP* − *MIP*) × 0.5 h**, in £.

This is exactly NESO's imbalance exposure minus *F*'s, as defined in the imbalance study. A positive *v* means switching earned money. The measure is weighted by payoff and gives larger disagreements larger positions.

**Why this is the stricter test.** The arbitrage study's "gain" asked whether outturn moved towards a forecaster where it disagreed with NESO. Every forecaster passed, because any forecast whose errors differ from NESO's tends to be right when NESO is wrong. Here the yardstick is a traded price, not outturn. A disagreement earns only if it lines up with whether the whole system is short or long, and so with the price.

**What would look like skill, not luck.** Value that is positive overall; that rises with the size of the disagreement; that concentrates where prices are stressed; and that the regression, the plain benchmark, does not also show.

**Prior work.** Forecast encompassing (Harvey, Leybourne and Newbold 1998) asks whether one forecast adds information to another; the arbitrage study's combination result is that question in error terms. Valuing forecasts by decisions at prices is standard in energy trading. No novelty is claimed; what this adds is the test for GB day-ahead demand forecasts, including foundation models, against NESO at open prices, with a live replication.

**Related work.** Recent studies agree that foundation models help in some energy tasks and not others. A review of 42 studies finds "conditional forecasting benefits rather than universal superiority" (Tahavori and Shaker 2026). On day-ahead prices, Chronos-Bolt beats a seasonal decomposition baseline in France and loses to it in Germany (Hornek et al. 2025). Two studies speak to this one's premise. In battery arbitrage on German, Polish and Spanish prices, the most accurate foundation model was not the most profitable at every level of risk: "statistical dominance does not translate directly into economic dominance" (Lipiecki and Weron 2026). In Belgium, Chronos-2 was more accurate than trained models on day-ahead prices but less accurate on imbalance prices at most horizons, and least accurate in the price extremes (Bui et al. 2026; figures recomputed from its tables, because its abstract overstates the gap). Two more shape the design. Look-ahead bias roughly halved the apparent error of some carbon-price models (Wu et al. 2026), and pre-registered live forecasts remove leakage by construction (Meyer et al. 2026), which is why stage 2 carries the result. Each paper was opened and checked; `LITERATURE.md` gives the details.

## 2. What this study shows

- **Each forecaster's accuracy against NESO's,** as a ratio of daily error, beside its settlement value, so that the divergence between accuracy and value is visible.
- **What switching from NESO's forecast to each forecaster would have been worth,** in £ per GWh of demand and per TWh a year, overall and in the tail.
- **Whether that value grows with the size of the disagreement** and **concentrates where prices are stressed.**
- **How often each forecaster's disagreement with NESO points the same way as the price spread,** with each disagreement counted once, regardless of size.
- **Whether a foundation model shows this and the regression does not.**

## 3. What this study does not show

- **Skill, from a positive value alone.** A forecast that is worse than NESO's on average can earn positive value if its errors happen to line up with the price spread. A worse-than-NESO forecast earning a small positive value is exactly the pattern chance would produce. The burden of proof is on measures B to D (§7) and on the live replication, not on the point estimate.
- **A switching hurdle in pounds.** Rule 7.5's 10% bar is set on error. No cost of switching is known, so no hurdle in pounds is set; the value is reported in units a supplier can set against its own costs.
- **A trading strategy.** It ignores costs, position limits and market impact. A supplier that bought differently from NESO's forecast at national scale would move the price.
- **Value against the market.** NESO's forecast is a public benchmark, one input to what the market expects; no market-implied demand forecast is available in open data. The yardstick is the realised spread between the System Price and a near-real-time traded price, which already contains information that arrived after the day-ahead forecasts.
- **Why NESO forecasts as it does.** That NESO is judged on average error is a fact about its incentive, not evidence of how its forecast is built.
- **Live performance from the backtest.** See §5.

## 4. What is known before this plan

Accuracy: over the 960 backtest days, NESO's mean daily error was about 700 MW, Chronos-2's 916, the regression's 1,014 (weather study; checkpoint 0). The imbalance study's stage 1 reconciled NESO's higher exposure with its lower error: its misses cost £3.00 per MWh of error against Chronos-2's £1.97, so it errs less but in costlier places. Every forecaster's error reproduced exactly there.

The imbalance study's stage 1 gives each forecaster's mean net exposure over 953 days: NESO 85, Chronos-2 75, the regression 86, the 50:50 average 81 £ per GWh. So the **point figures for overall value are already known**: switching to Chronos-2 is worth about +10 £ per GWh, to the regression about −1. Their intervals, and every conditional measure below, have not been computed. The tail results of stage 1 are known for exposure, not for value. The direction of each forecaster's disagreement with NESO has not been compared with prices.

This is why stage 2, on days no one has seen, carries the primary result, and why the predictions (§9) concentrate on what is not yet known.

## 5. Two stages

**Stage 1: backtest pilot.** The 953 days the imbalance study scored, with the same prices (`imbalance_cost/prices_manifest_2024-03-16_2026-10-31.json`) and forecasts. The foundation models may have seen these days in training, and "Chronos-2 knows something NESO's forecast does not" is exactly what leakage could fake. So stage 1 is labelled a pilot.

**Stage 2: live replication.** The imbalance study's live window (`imbalance_cost/PLAN.md` §5–6), scored after 31 March 2027 with the same code: Chronos-2's calendar forecasts issued daily since 24 November 2026, the weather arm made after the window from inputs archived in advance, NESO's forecast and prices fetched afterwards. The stage 2 note reports issued days alone as well as all days.

## 6. Forecasters

Each against NESO's day-ahead forecast (`neso`), the reference *N*:
- **Primary:** Chronos-2 with calendar and weather (`chronos2_A`), and the weather regression (`regression_weather`), the plain benchmark.
- **Descriptive:** the equal-weight average of the two, fixed in advance; LightGBM V1 and S1 (stage 1 only); TimesFM 2.5 one day per call; Chronos-2 with weather only (`chronos2_weather`).

Loaded through the imbalance study's `score.py` (`load_real`, with every hash check), imported unchanged.

## 7. The measures

All on the days and half-hours the imbalance study scored (a day counts only if every forecaster, outturn and both prices cover all its half-hours). *v* is defined in §1.

**A. Value of switching (primary).** Each day's sum of *v*, divided by that day's demand in GWh, then the mean over days: £ per GWh. Positive means switching from NESO to the forecaster earned money. Reported with its 90% interval and labelled **clearly positive**, **clearly negative** or **not clearly different from 0**. Also reported: the paired difference between Chronos-2's value and the regression's.

**B. Does it grow with disagreement? (primary)** For each forecaster, the scored half-hours are split into four equal groups by the size of the disagreement, |*F* − *N*|, ranked separately for each forecaster. In each group, the **value per MWh of disagreement** is the sum of *v* over the sum of |*F* − *N*| × 0.5 h, in £/MWh. The test is the top group minus the bottom group, with its 90% interval. The thresholds in MW are reported. Also reported, for comparison across forecasters: the same in fixed bands of 0–250, 250–500, 500–1,000 and over 1,000 MW.

**C. Does it concentrate where prices are stressed?** The scored half-hours are split into four equal groups by |*SP* − *MIP*|, the same groups for every forecaster. In each, the value per MWh of disagreement, and the share of the forecaster's total value. The top group minus the bottom group, with its interval.

**D. Direction alone.** On half-hours where *F* ≠ *N* and *SP* ≠ *MIP*: the **hit rate**, the share where the sign of *F* − *N* equals the sign of *SP* − *MIP*; and the **sign payoff**, the mean of sign(*F* − *N*) × (*SP* − *MIP*), in £ per MWh traded, as if each disagreement were the same size. Overall, and in the top quarter by price stress. This separates being right about the direction from being right about the size.

**D, null by sign-flipping.** What would a forecaster with no sense of direction score? Adapted from Upadhyay (2026), who gives each return its own size and a random sign. Here each day's half-hours keep their disagreements and price spreads, but all of them take one random sign for the day, +1 or −1, drawn independently for each day. Under that flip, *v* changes sign for the whole day, so the hit rate becomes one minus itself on flipped days, and the sign payoff and the value (measure A) change sign. Signs are flipped by whole days, not by half-hours, because a forecaster's errors persist through a day; flipping half-hours separately would make chance look steadier than it is, and skill easier to claim. As a check on persistence across days, the same is done flipping whole 7-day blocks, as in the bootstrap. 2,000 draws, seed 20261127 for stage 1 and 20270403 for stage 2. Reported for the hit rate, the sign payoff and measure A, overall and in the top quarter by price stress: the observed figure, the null's 5th and 95th percentiles, and the share of null draws at or above the observed figure. A figure above the null's 95th percentile is labelled **beyond chance**; below its 5th, **worse than chance**; otherwise **within chance**. Like the other labels, these are unadjusted and descriptive.

**E. Tail.** The mean of each forecaster's worst 5% of days by value (most negative) and its best 5%, in £ per GWh, and its value on 8 January 2025.

**F. Accuracy beside value.** For every forecaster: its mean daily absolute error, its ratio to NESO's (with a paired 90% interval), and whether that ratio is credibly below 0.9, reported descriptively in the manner of rule 7.5. Every table of value carries the forecaster's error ratio to NESO in the same row.

**Scaling.** Value is also given per TWh served in a year (£ per GWh × 1,000), as an aid for a supplier to scale by its own volume. Its demand will not follow the national shape exactly, so this is an upper guide, not a forecast.

**Sets.** All days (primary); winter; the coldest tenth (stage 1 only); the evening window, 16:00 to 19:30 UK time.

**Year by year (stage 1 only).** A result that holds in one market or year can reverse in the next (Hornek et al. 2025). So measures A and F are also reported for each 12-month period of the backtest, counted from its first scored day (16 March 2024 to 15 March 2025, and 16 March 2025 to 15 March 2026), each with its own interval, from a bootstrap that resamples only that period's days (7-day blocks, 2,000 draws, the stage 1 seed). The remaining days, 16 March to 31 October 2026, are reported too, with their count, but are not compared with the full years because they contain no winter. The question is whether Chronos-2's value has the same sign in both full years. Stage 2 is one winter, so it has no split.

**Intervals and labels.** The tails study's 7-day moving-block bootstrap over days, 2,000 draws, the same draws throughout; seed 20261126 for stage 1 and 20270402 for stage 2. Whole days are resampled with their half-hours, and the disagreement and stress groups stay fixed in each draw. Ratios are of totals over the resampled days. An interval with no finite draws is labelled **undefined**. Labels are unadjusted and are not tests.

## 8. Checks before each real run

1. **Reconciliation of accuracy and exposure.** For every forecaster and NESO, demand-weighted net exposure equals £ per MWh of error times MWh of error per GWh of demand, exactly; the report lists both factors, so that any forecaster ranked differently on accuracy and on exposure shows why. A mismatch stops the run.
2. **Identity.** For every forecaster, its value (measure A) equals NESO's net exposure minus its own, as `imbalance_cost/score.py` computes them, to £0.01 per GWh; in stage 1, against `results_stage1.json`.
3. **Days.** The scored days equal the imbalance study's, as a set. The yearly periods share no day, and together they contain every scored day.
4. **Synthetic.** On invented data with known answers:
   - a forecaster equal to NESO has *v* = 0 on every half-hour;
   - one equal to NESO plus noise unrelated to prices has value with an interval containing 0, and flat value per MWh across disagreement groups;
   - one that moves away from NESO in the direction of the price spread has positive value, a hit rate of 1, and value per MWh that is the same in every disagreement group if every move is the same size;
   - one whose moves line up with prices only when they are large has value per MWh rising across the groups;
   - under the sign-flip null, the noise forecaster is labelled "within chance" and the price-following one "beyond chance"; flipping every day's sign at once gives exactly the negated figures;
   - the groups, the fixed bands and the labels, including "undefined", come out right.
5. **Hashes.** Every file read matches its recorded SHA-256.

## 9. Prediction, written before any of these measures is computed

- **The divergence.** Chronos-2's error is clearly higher than NESO's (ratio above 1.2, interval wholly above 1) in both stages, while its value is positive at the point estimate. Measures B to D decide whether the value is skill.
- **A.** In stage 1, Chronos-2's value is positive (its point figure is known) but not clearly different from 0. The regression's is close to 0. The 50:50 average's is positive and not clearly different from 0. In stage 2, no forecaster's value is clearly different from 0, because the window is short. Year by year, Chronos-2's value is positive at the point estimate in both full years, and clearly different from 0 in neither.
- **B.** For Chronos-2 and the average, value per MWh of disagreement is higher in the top disagreement group than in the bottom one, but not clearly. For the regression it is flat.
- **C.** More than half of each forecaster's value, positive or negative, falls in the top quarter by price stress.
- **D.** Hit rates lie between 49% and 53% overall for every forecaster. In the top quarter by price stress, Chronos-2's hit rate is above 50%, because NESO's misses line up with the system's there (the imbalance study's stage 1 found NESO on the costly side 54% of the time in the most stressed half-hours). Against the sign-flip null, every forecaster's overall hit rate, sign payoff and value are **within chance** in both stages.
- **E.** 8 January 2025 is the best day of value for Chronos-2, because NESO's forecast lost more that day than Chronos-2's.

## 10. Headlines, fixed now

Written by the script by rule (§7).

Stage 1: "In a backtest the foundation models may have seen in training, Chronos-2's day-ahead demand forecast had [R] times the daily error of NESO's (90% interval [l] to [u]), and a supplier that bought it instead of NESO's would have [**clearly gained** / **clearly lost** / **neither clearly gained nor lost**] ([X] £ per GWh of demand, 90% interval [a] to [b]); for the weather regression the figure was [Y] £ per GWh ([c] to [d]). Where Chronos-2 disagreed with NESO most (the largest quarter of its disagreements), each MWh of disagreement was worth [Z] £ ([e] to [f]), against [W] £ ([g] to [h]) in the smallest quarter."

Stage 2: the same, opening "On [n] days no model could have seen," in place of "In a backtest the foundation models may have seen in training,". When stage 2 is reported, its sentences lead and stage 1's follow as the pilot.

## 11. Work

1. **`disagreement/score.py`:** loads through `imbalance_cost/score.py`, imported unchanged; runs the checks in §8; computes §7; writes the headline by rule. It includes the fixes listed in `imbalance_cost/REVISIONS.md` 15 from the start. Committed before it runs, with its synthetic check; outputs after. Stage 1 uses only committed files and the price data already fetched.
2. **`disagreement/RESULTS_stage1.md`:** a pilot note, led by its headline.
3. **After 31 March 2027:** stage 2, with the imbalance study's stage 2 data and the same script; any change recorded in `REVISIONS.md` before it runs.

## 12. Timing

Stage 1: a day or two once the plan is reviewed and tagged. Stage 2: April 2027, with the imbalance study's stage 2.

## Sources

- `BENCHMARK_RULES.md` rule 7.5 (the 10% bar) and `checkpoint0/RESULTS.md` (Chronos-2 against the regression).
- NESO, monthly incentive performance reports, metric 1B (day-ahead demand forecasting error against a benchmark): for example [this report](https://neso.energy/document/308851/download). Read 24 November 2026.
- National Grid ESO, [forward plan technical annex](https://nationalgrid.com/sites/default/files/documents/P2209_forward_plan_technical_annexe_1202_2.pdf): the day-ahead demand incentive measured half-hourly by mean absolute percentage error against seasonal targets. Read 24 November 2026.
- Harvey, D., Leybourne, S. and Newbold, P. (1998). [Tests for forecast encompassing](https://econpapers.repec.org/RePEc:bes:jnlbes:v:16:y:1998:i:2:p:254-59). *Journal of Business & Economic Statistics* 16(2), 254–259.
- `imbalance_cost/PLAN.md`, `imbalance_cost/RESULTS_stage1.md` and `arbitrage/RESULTS.md` for the data, code and earlier figures.
- Bui, C., Mascarenhas, M. M., Verstraeten, A. and Kazmi, H. (2026). Empirical evaluation of time series foundation models for day-ahead and imbalance electricity price forecasting in Belgium. [arXiv:2605.17045](https://arxiv.org/abs/2605.17045).
- Hornek, T., Sartipi, A., Tchappi, I. and Fridgen, G. (2025). Benchmarking pre-trained time series models for electricity price forecasting. IEEE, European Energy Market conference. [Open copy](https://orbilu.uni.lu/bitstream/10993/65383/1/Hornek_et_al_2025%20Benchmarking_EEM.pdf).
- Lipiecki, A. and Weron, R. (2026). Foundation models for electricity price forecasting and battery arbitrage: Can they replace market-specific forecasting models? [arXiv:2609.00089](https://arxiv.org/abs/2609.00089).
- Meyer, M., Kaltenpoth, S. B., Albers, H., Zalipski, K. and Müller, O. (2026). TS-Arena: A live forecast pre-registration platform. Proceedings of KDD 2026. [doi:10.1145/3770855.3817515](https://doi.org/10.1145/3770855.3817515).
- Tahavori, M. and Shaker, H. R. (2026). Time-series foundation models for energy infrastructure: Evidence and requirements for digital-twin-grade integration. *Energy and AI* 26, 100959. [ScienceDirect](https://www.sciencedirect.com/science/article/pii/S2666546826002855).
- Upadhyay, R. (2026). Do time-series foundation models forecast index-futures returns? A preregistered evaluation of models, metrics, and input representations. [arXiv:2611.12141](https://arxiv.org/abs/2611.12141).
- Wu, R., Jamaludin, J. B. and Selvaraj, J. (2026). Do time series foundation models forecast carbon prices? Leakage-free evidence from the EU ETS and China's carbon markets. *Energies* 19(20), 4999. [doi:10.3390/en19204999](https://doi.org/10.3390/en19204999).
- `disagreement/LITERATURE.md`: how each was checked.
