# Related work: seven papers, each opened and checked

Andy Moran (Heaviside Analytics) · 24 November 2026

A reviewer sent six papers, with summaries and quotations, as related work for the disagreement study. A seventh, Hornek et al., was cited by one of them. Every paper below was opened in full (PDF or publisher page) before it was cited (lesson 23). Each quotation was checked against the paper's own text, and figures were recomputed from the paper's tables where they matter.

**Verdict.** All seven exist, and six are cited in `PLAN.md` §1. One has a headline that its own tables do not support (Bui et al., below). That error had passed through two summaries before it reached us.

## Cited in the plan

**1. Lipiecki, A. and Weron, R. (2026).** *Foundation models for electricity price forecasting and battery arbitrage: Can they replace market-specific forecasting models?* arXiv:2609.00089, submitted 31 August 2026.

Nine foundation-model variants are tested against two price-forecasting benchmarks (LEAR+CP and DDNN-JSU) on day-ahead prices in Germany, Poland and Spain, 2021–2025. Only TabPFN beats the benchmarks on every statistical measure. In battery arbitrage the ranking changes: TabPFN earns most with unlimited bids and riskier strategies, DDNN-JSU when risk tolerance is lower. The authors write that "this statistical dominance does not translate directly into economic dominance" and that "foundation models cannot universally replace market-specific models". They also say they cannot rule out test-period contamination for models pretrained partly on real series.

*Use:* the closest precedent for this study's premise, that accuracy and money can rank forecasters differently.

**2. Tahavori, M. and Shaker, H. R. (2026).** *Time-series foundation models for energy infrastructure: Evidence and requirements for digital-twin-grade integration.* Energy and AI 26, 100959.

A structured review of 42 studies, drawn from 164 records in a search completed on 28 September 2026. Its abstract says the evidence "shows conditional forecasting benefits rather than universal superiority". Its strongest positive result, a district-heating study (Chronos-2 12.48% against 14.57% CVRMSE), treats observed future temperature as known, and tunes on weeks of the year it is scored on. The review calls for "leakage-aware evaluation" and prospective testing.

*Use:* the state of the evidence in energy, and the case for a live window.

**3. Hornek, T., Sartipi, A., Tchappi, I. and Fridgen, G. (2025).** *Benchmarking pre-trained time series models for electricity price forecasting.* IEEE, 2025; the review places it at the International Conference on the European Energy Market. The open copy (orbilu.uni.lu) gives no DOI; look it up before final citation.

Six foundation models against statistical and machine-learning models, on 2024 day-ahead prices in five European markets, one day ahead, with no exogenous inputs. The abstract reports "no TSFM statistically outperforming" MSTL, a seasonal decomposition baseline (one-sided Diebold-Mariano, multivariate form). The winner flips between neighbours: Chronos-Bolt Small has 16.02 against MSTL's 16.50 €/MWh MAE in France, but 21.52 against 20.69 in Germany. The paper does not discuss whether 2024 was in the models' pretraining data.

*Use:* evidence that foundation models do not win everywhere, even in adjacent markets. Not a comparison for our figures: prices not demand, no inputs, an easier baseline.

**4. Bui, C., Mascarenhas, M. M., Verstraeten, A. and Kazmi, H. (2026).** *Empirical evaluation of time series foundation models for day-ahead and imbalance electricity price forecasting in Belgium.* arXiv:2605.17045v1, 16 May 2026.

Chronos-2, Chronos-Bolt and TimesFM 2.5 against LEAR, a neural network and their ensemble, on Belgian day-ahead prices (test year 2024) and imbalance prices (test year 2023, 15-minute periods up to two hours ahead). The test periods were checked against the vendors' disclosed training data.

**The abstract overstates the imbalance result.** It says Chronos-2 "yields 10% higher MAE predicting imbalance prices across all forecast horizons, except for the two-hour-ahead horizon". Recomputed from the paper's Tables II and III, Chronos-2 with inputs against the ML ensemble:

| Horizon | MAE | RMSE |
|---|---|---|
| Day-ahead | −6.0% | −1.8% |
| Imbalance, 15 min | +4.3% | +6.4% |
| Imbalance, 1 h | +0.5% | +3.3% |
| Imbalance, 2 h | −0.3% | +2.3% |

The direction holds, but no figure is near 10%. The day-ahead gain has no reported significance test. The one Diebold-Mariano test reported, Chronos-2 combined with the ML models against the ML ensemble alone, finds the improvement "not significant". In the most extreme tenth of imbalance prices, Chronos-2's error is well above the trained models' (101.7 against 81.2 €/MWh MAE, 15 minutes ahead, top decile).

*Use:* cite the recomputed table figures, not the abstract. Evidence that a gain in day-ahead accuracy need not carry over to imbalance settlement, and that foundation models do worst in price extremes. Not a direct comparison: it forecasts imbalance prices; we forecast demand and settle the misses at them.

**5. Wu, R., Jamaludin, J. B. and Selvaraj, J. (2026).** *Do time series foundation models forecast carbon prices? Leakage-free evidence from the EU ETS and China's carbon markets.* Energies 19(20), 4999. doi:10.3390/en19204999.

Rolling-origin, no-look-ahead tests. Both reviewer quotations are in the abstract: "No model significantly outperforms the random walk in the EU ETS" and "Look-ahead bias roughly halves the apparent error of decomposition-based models". The second comes from decomposing the full series before forecasting (VMD), which lets future data into past forecasts. Results differ by market: foundation models are best in the Hubei pilot, worse than the random walk in the national and Guangdong markets.

*Use:* a measured size for look-ahead bias, and the reason for this benchmark's look-ahead checks.

**6. Meyer, M., Kaltenpoth, S. B., Albers, H., Zalipski, K. and Müller, O. (2026).** *TS-Arena: A live forecast pre-registration platform.* Proceedings of the 32nd ACM SIGKDD Conference on Knowledge Discovery and Data Mining V.2. doi:10.1145/3770855.3817515. First issued as arXiv:2512.20761 (December 2025) under a different title.

The reviewer's citation named three of the five authors and the old title. The v1 abstract says foundation models "risk triggering a fundamental evaluation crisis" through leakage. The platform requires forecasts to be submitted before the outcome exists, and was first applied to energy series.

*Use:* the precedent for this project's issued live forecasts.

**7. Upadhyay, R. (2026).** *Do time-series foundation models forecast index-futures returns? A preregistered evaluation of models, metrics, and input representations.* arXiv:2611.12141. The paper gives no date; its blind set was opened on 4 November 2026.

Five frozen foundation models and Kronos, against a no-change forecast, on E-mini Nasdaq-100 and S&P 500 futures returns 5 to 120 minutes ahead. None of 160 blind-set cells beats no-change. All three reviewer phrases are in the conclusion: no improvement "under any tested representation"; Kronos "gave no evidence of an economically useful forecasting advantage"; and the advice to "calibrate rank metrics with a sign-randomised null". The null keeps each return's size and gives it a random sign, over 200 seeds.

*Use:* method only. The sign-randomised null is adapted for measure D (`PLAN.md` §7). Financial returns are not demand.

## Checked, not cited

**ChandraMohan, K. (2026).** *How seasonal reference choice changes the apparent gains of Chronos models in electricity load forecasting.* arXiv:2611.29653. Single author.

The figures are right: a week ahead, Chronos-Bolt's median gain is 17.3% against weekly persistence and 11.9% against a validation-selected reference. But one day ahead, the horizon of this benchmark, changing the reference "hardly matters" (23 against 22 clear wins out of 30). The references are naive seasonal forecasts, not a weather regression. The reviewer's summary called this "the same phenomenon" as Chronos-2's 9.7% against the 10% bar. It is not, so it is not cited.

**Li, Z. et al. (2025).** *TSFM-Bench: A comprehensive and unified benchmark of foundation models for time series forecasting.* KDD 2025, pp. 5595–5606. doi:10.1145/3711896.3737442. Found while searching for the Tahavori and Shaker review, which cites it. A general benchmark on 21 datasets; not relevant to settlement value.

## What the checking found

- **No paper was invented.** All the reviewer's direct quotations from Lipiecki and Weron, Tahavori and Shaker, Wu et al., TS-Arena and Upadhyay are in the papers' own text.
- **Two citations were incomplete:** TS-Arena's authors and title, and the review's missing authors.
- **One headline did not survive its own tables:** Bui et al.'s "10% higher" imbalance error. The review quoted the abstract faithfully, and the reviewer's summary quoted the review. Each summary was accurate to its source; the error was in the source's abstract.
- **One analogy was stretched:** ChandraMohan's week-ahead result applied to a day-ahead question.

The lesson for this project: check a paper's tables, not only its abstract, before citing a number.
