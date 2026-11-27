# Related work for the quantile study: eleven sources, each opened and checked

Andy Moran (Heaviside Analytics) · 27 November 2026

Written before the plan is tagged (`PLAN.md` §11 1), to check two things. First, that its methods are standard and correctly described: the pinball loss, calibration, dressing and sorting crossed quantiles. Second, what is already known about how honest foundation models' quantiles are, and on what data. Every source below was opened in full (PDF or HTML) before it is cited (lesson 23), and figures were taken from its tables where it has them. Where a paper's numbers appear only in figures, that is said.

**Verdict.** The methods are standard, and the plan describes them correctly, with one wording fix: the quantile score approximates *half* the CRPS, and the uneven grid makes that approximate. On Chronos-2, the evidence points mostly towards honest bands, but no study tests the plan's setting: national demand, a day-ahead weather forecast treated as known, and calendar days. Two changes to the plan follow (end of this note).

## Methods

**1. Gneiting, T. and Raftery, A. E. (2007).** *Strictly proper scoring rules, prediction, and estimation.* Journal of the American Statistical Association 102(477), 359–378. Opened as University of Washington Technical Report 463R, November 2005, the version that became the article.

Section 6.1 gives the proper scoring rules for a quantile forecast: equation 27, S(r; x) = (x − r)(1{x ≥ r} − α), is the pinball loss at level α, which the paper attributes to Koenker and Machado (1999), Taylor (1999) and Theis (2005). Equation 29 gives the interval score. Equation 34 builds a proper score for a whole distribution by integrating quantile scores over levels. The paper does **not** state that the CRPS equals such an integral; it relates the CRPS to integrated Brier scores instead.

*Use:* the pinball loss is a proper score for a quantile, so a forecaster cannot improve its expected score by reporting anything other than what it believes. That is why the plan can rank forecasters by it.

**2. Laio, F. and Tamea, S. (2007).** *Verification tools for probabilistic forecasts of continuous hydrological variables.* Hydrology and Earth System Sciences 11(4), 1267–1277. Opened as the authors' post-print (Politecnico di Torino).

Equation 6 defines a cost-loss function with one parameter, the cost-loss ratio ξ; the paper states (p. 1271) that its integral over ξ "is equivalent to the continuous ranked probability score". The paper never mentions the pinball loss. But its equation 6 is exactly twice the pinball loss at level τ = 1 − ξ (checked by hand: if outturn is below the forecast, both give 2ξ times the gap; if above, both give 2(1 − ξ) times the gap). So **the CRPS is twice the integral of the pinball loss over all levels.**

*Use:* the plan's quantile score, the mean pinball loss over 21 levels, approximates **half** the CRPS. The 21 levels are not evenly spaced (0.01, 0.05, then steps of 0.05 to 0.95, then 0.99), so the approximation is rough at the tails. The plan reports the score as what it is and does not call it the CRPS.

**3. Gneiting, T., Balabdaoui, F. and Raftery, A. E. (2007).** *Probabilistic forecasts, calibration and sharpness.* Journal of the Royal Statistical Society B 69(2), 243–268. Opened in full (author's copy).

The paper proposes "maximizing the sharpness of the predictive distributions subject to calibration" (p. 243). Probabilistic calibration (Definition 1(a), p. 246) is checked by the uniformity of the PIT values, the share of outturns below each predicted level (pp. 251–252). The paper warns (p. 244) that a uniform PIT histogram is necessary but not sufficient: forecasts biased in opposite directions can produce one.

*Use:* the plan's measure B (calibration) and its report of interval width beside coverage, for sharpness. The warning is why calibration is reported for subsets of days and times, not only pooled (see change 1 below).

**4. Roulston, M. S. and Smith, L. A. (2003).** *Combining dynamical and statistical ensembles.* Tellus 55A, 16–30. Opened in full (LSE copy).

The abstract states that estimates of a forecast's likely accuracy "can be obtained by 'dressing' a single forecast using historical error statistics", and that the economic value of dressed forecasts had been shown by earlier studies. The paper itself is about dressing ensembles; dressing a single forecast is its starting point.

*Use:* the source for the term and for the plan's baseline: a point forecast plus quantiles of its own past errors.

**5. Chernozhukov, V., Fernández-Val, I. and Galichon, A. (2010).** *Quantile and probability curves without crossing.* Econometrica 78(3), 1093–1125. Opened as arXiv:0704.3649v3 (July 2014).

Proposition 4 shows that sorting an estimated quantile curve into increasing order (monotone rearrangement) gives a curve at least as close to the true one, in every L*p* norm for *p* from 1 to infinity, whatever the sample size or estimation method.

*Use:* the plan sorts each half-hour's 21 values before scoring. This paper shows that sorting cannot move a quantile curve further from the truth, so it does not favour Chronos-2 unfairly. The plan still reports raw results as well.

**6. Ziel, F. and Liu, B. (2016).** *Lasso estimation for GEFCom2014 probabilistic electric load forecasting.* arXiv:1603.01376. Opened in full.

Section 5 states that the load track of the Global Energy Forecasting Competition 2014 was scored by "the overall mean pinball loss function of the 99 percentiles", and refers to Hong et al. for details.

*Use:* evidence that the pinball loss, averaged over levels, is the established score for probabilistic load forecasts. The competition paper itself (Hong et al. 2016, International Journal of Forecasting 32(3)) was not available in full here and is not cited.

## Foundation models' quantiles

**7. Kaas, B., Treutlein, M., Gerber, H. B., Neumann, O., Phatthanakhuha, C., Resch, O., Mikut, R. and Hagenmeyer, V. (2026).** *Probabilistic low-voltage peak load forecasting with time series foundation models evaluated on application-oriented metrics.* arXiv:2607.01966v1, 2 July 2026. Opened in full.

Net load on 200 German low-voltage feeders, 15-minute resolution, four days ahead. Weather inputs are short-term forecasts one to three hours ahead, close to observed weather. Every model gives a median and the 0.05 and 0.95 quantiles. Median over feeders (Table 3): Chronos-2 had the lowest pinball loss (0.5545 kW) and its 90% intervals covered outturn 89.75% of the time; Chronos-Bolt's covered only 62%. Without weather, Chronos-2's intervals widened (16.33 to 18.28 kW) and coverage barely moved (88.44%).

*Use:* the closest published test, and it points against the plan's prediction that Chronos-2's bands are too narrow. Its weather inputs, though, are nearly observed, so they say little about a day-ahead weather forecast treated as known. Feeder net load is also not national demand.

**8. Michael, P., Symeonides, M. and Trihinas, D. (2026).** *Evaluating accuracy and probabilistic reliability of zero-shot time series foundation models.* arXiv:2609.25788v1, 22 September 2026. Opened in full.

Six foundation models, including Chronos-2, on three series, one of them hourly national load for Poland (17 months, 2024–25). Calibration is measured by interval coverage error, the absolute gap between the share of outturns outside an 80% interval and 20%. The text reports Chronos-2's error on Polish load falling from 0.17 to 0.04 as its context grew from 120 to 624 hours. Other results are in figures only. Because the measure is an absolute gap, it does not say whether intervals were too narrow or too wide.

*Use:* national load, near nominal coverage with a long context. The benchmark's context is 2,688 half-hours, longer still. No weather inputs.

**9. Decker, T. and Tresp, V. (2026).** *Evaluating uncertainty calibration in probabilistic time series foundation models.* arXiv:2611.03592; listed as a NeurIPS 2026 poster. Opened in full; the authors' names are taken from the NeurIPS and arXiv listings, as the extracted text did not carry them.

Fourteen zero-shot models, including Chronos-2, on 55 GIFT-Eval configurations (some electricity). Calibration is measured three ways: pooled over all horizons, per horizon, and conditional on the forecast's own value. Miscalibration that is "too extreme in both directions" can cancel in pooled coverage. Chronos-2 (Table 2): pooled calibration error 0.064, per-horizon average 0.092, worst horizon 0.165. One example: its 90% intervals covered 77% of outcomes on one traffic dataset. Isotonic recalibration cut pooled error by about 40% for Chronos-2, but did little for conditional miscalibration.

*Use:* pooled coverage can look right while subsets are wrong. This is the reason for change 1 below.

**10. Adler, C., Chang, Y., Draxler, F., Abdi, S. and Smyth, P. (2026).** *Beyond accuracy: are time series foundation models well-calibrated?* Proceedings of ICLR 2026; arXiv:2510.16060v2. Opened in full.

Five models (Chronos-Bolt, TimesFM, Moirai 2.0, TiRex, YingLong; not Chronos-2), six datasets (none electricity), univariate, zero-shot. Foundation models were "consistently better calibrated than baseline models" and not systematically over- or under-confident. The per-model results are in figures, not tables.

*Use:* general background only: a different model, no electricity, no covariates.

**11. Ansari, A. F., Shchur, O., Küken, J. et al. (2026).** *Chronos-2: a foundation model for multivariate time series forecasting.* arXiv:2610.41956v1, 30 October 2026, which extends the technical report arXiv:2510.15821. Opened in full.

Section 4 reports that Chronos-2 had the best calibration on 23 of 24 metric-interval pairs (weighted interval score and mean absolute coverage error, for 90%, 95% and 98% intervals) across three benchmarks, against models that give extreme quantiles. The breakdown is in a supplementary figure not available here. No electricity series is named in the calibration analysis.

*Use:* the developers' own evidence that Chronos-2's bands are well calibrated on general benchmarks. It does not cover this setting.

## Read but not cited

- **Kaljevic, T., Arzola, I. and Zhang, Y. (2026).** *Benchmarking time series foundation models for load forecasting under covariate uncertainty.* arXiv:2610.07232v1. Opened in full. It adds synthetic Gaussian noise to future weather covariates and finds Chronos-2's point error rises faster than TimesNet's as noise grows. It reports no quantile, coverage or calibration results, so it says nothing about bands. Relevant to the plan's reasoning about weather-forecast error, but only for medians and only with synthetic noise.

## What this changes in the plan

1. **Calibration by time of day.** Pooled coverage can hide errors in opposite directions (Gneiting et al. 2007; Decker and Tresp 2026). Measure B adds coverage of the 80% and 98% intervals in each of the four blocks of the day used for dressing, with the largest gap from nominal.
2. **Related work and the prediction's basis.** `PLAN.md` §1 gains a related-work paragraph. Prediction B, that Chronos-2's bands are too narrow, is kept, but now says that the closest published evidence (Kaas et al. 2026; Michael et al. 2026) points the other way. Neither study gave the model a day-ahead weather forecast, which is the reason for the prediction. The quantile score is described as approximating half the CRPS (Laio and Tamea 2007).
