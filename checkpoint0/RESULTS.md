# Checkpoint 0: Chronos-2, a weather regression and LightGBM on equal inputs

Andy Moran (Heaviside Analytics) · 16 November 2026 · a backtest first look, exploratory and descriptive

**What this does not show.**
- **Live performance.** The foundation models may have seen these backtest days in training.
- **The best a trained model can do.** LightGBM is untuned.
- **That foundation models beat trained models in general.** The trained benchmark here proved weaker than expected.
- **A ranking of model families.** The study compares five forecasters, in eight configurations, on one series: GB national demand (INDO), a day ahead.
- **Commercial value.** Cost is measured, not priced.

## Headline

In a backtest the foundation models may have seen in training, Chronos-2 forecast GB demand 19.3% more accurately than a LightGBM model with library defaults, on equal inputs. The LightGBM model was 11.8% less accurate than a weather regression given the same information: with library defaults, the trained tree model did not beat the linear one. A live, preregistered test starts on 1 April 2027.

The plan's fixed rules produced the two sentences above, before any LightGBM run. They included a form for LightGBM losing to the regression (`PLAN.md` §7).

**Against the harder opponent.** The regression, not LightGBM, was the harder opponent. Chronos-2 beat it by about 10%: 916 against 1,014 MW of daily error. That reproduces exactly the weather study's exploratory check E5, which first gave Chronos-2 the same calendar as the regression.

The regression's strength is no anomaly. A per-slot linear regression with temperature terms is a known strong baseline in load forecasting: Hong, Wang and Willis's "vanilla" model, built the same way, was used as a benchmark in GEFCom2012, 2014 and 2017.

Nor was LightGBM's defeat foregone. On Greek national load, a tuned LightGBM beat four deep-learning models on every metric (Shiblee and Koukaras, 2025). That study forecast with the previous hour's load, a shorter horizon than day ahead, so it shows LightGBM is a strong system-level model, not that it should win here. Household-level benchmarks, where LightGBM has been tested most widely, report the same. That is why it was the trained baseline here. The finding concerns LightGBM's defaults and structure on this information, not LightGBM as a library.

## What was compared

The backtest is the weather study's 960 days, 16 March 2024 to 31 October 2026. Each forecaster saw:
- demand to 08:30 on D−1;
- national temperature, wind and solar as forecast at the 09:30 issue time;
- the calendar.

Two configurations lack the calendar:
- **TimesFM 2.5** got none: its eight-week context holds at most one Christmas period and few bank holidays, too few to learn from.
- **Timestral** is also shown with weather only.

The forecasters:
- **Chronos-2, Timestral and TimesFM 2.5:** zero-shot. Their forecasts are the weather study's saved forecasts, checked against their hashes.
- **The weather regression:** 48 per-slot models with temperature, its square, wind, wind chill and solar, refitted each day on the year to D−2.
- **LightGBM (new):** one model across all half-hour slots, given exactly the regression's information (slot, calendar, demand at D−2 and D−7, temperature, wind, solar) and refitted each day on the same window.
  - **Settings:** library defaults, except for an absolute-error objective, a fixed seed and day of week as a category.
  - **Why the defaults are tested again.** Defaults are not neutral: on 58 time series, random configurations cut LightGBM's mean squared error by up to 17.45% against the defaults (Barros, Cerqueira and Soares, 2021, from the abstract; the full text was not accessible). So two sensitivity runs used configurations published for load forecasting, changing only the objective:
    - **S1** (Misiurek, Olkuski and Zyśk, 2026): 500 trees, learning rate 0.05, 31 leaves, depth 8, row and column sampling 0.8.
    - **S2** (Uzzaman et al., 2026): 500 trees, learning rate 0.03, 31 leaves.

Timestral is shown both ways and not ranked, because a known defect affects its calendar input (`mistralai/timestral#9`).

## Results

Each ratio divides a forecaster's mean daily error by the comparator's. Intervals are 90%, from a moving-block bootstrap over days (blocks of 7, 2,000 draws). A difference is described only where the interval excludes 1.

| Forecaster | Mean daily error (MW) | Ratio to LightGBM (defaults) |
|---|---|---|
| Chronos-2 (calendar and weather) | 916 | 0.807 (0.778–0.837) |
| Weather regression | 1,014 | 0.894 (0.869–0.920) |
| LightGBM, defaults | 1,134 | 1 |
| TimesFM 2.5 (weather), corrected² | 1,620 | 1.428 (1.365–1.488) |

Timestral, for information and not ranked:

| Timestral | Mean daily error (MW) | Ratio to LightGBM (defaults) |
|---|---|---|
| Calendar and weather | 1,103 | 0.973 (0.942–1.006) |
| Weather only | 1,089 | 0.960 (0.930–0.993) |

**The sensitivity runs change no reading.** S1 cuts LightGBM's error to 1,061 MW and S2 to 1,094 MW, but both still trail the regression: 1.046 (1.023–1.070) and 1.079 (1.052–1.107). Chronos-2 still leads both (0.863 and 0.836).

**LightGBM fails in winter.** Its error against the regression's, by meteorological season. The backtest holds two winters, so the winter row rests on 180 days from two seasons:

| Season | Days | Ratio |
|---|---|---|
| Winter (Dec–Feb) | 180 | 1.286 (1.192–1.398) |
| Spring (Mar–May) | 261 | 1.113 (1.076–1.150) |
| Summer (Jun–Aug) | 276 | 0.990 (0.953–1.024) |
| Autumn (Sep–Nov) | 243 | 1.135 (1.087–1.175) |

**Chronos-2's lead shows no sign of training leakage.** Against LightGBM, its ratio is 0.807 (0.766–0.848) on the 593 days before its release and 0.808 (0.771–0.847) on the 367 days after.

**Cost is small.** Wall-clock seconds per forecast day, median over 20 sample days, on one laptop CPU with 4 threads, including any daily refit. Memory is the peak above what the backtest data alone occupy.

| Forecaster | Seconds per day | Memory above data |
|---|---|---|
| Weather regression | 0.22 | 15 MB |
| LightGBM (defaults; S1; S2) | 0.36; 0.62; 0.60 | 15 MB |
| Chronos-2 (calendar and weather) | 1.85 | 545 MB |
| Timestral (weather; calendar and weather) | 2.30; 7.63 | 1.3 GB |
| TimesFM 2.5, one day per call² | 10.63 | 1.9 GB |

Every forecaster runs in seconds a day. The regression's run time is the cheap part. Its real cost is the engineering of its weather terms, which no timing captures.

## Why LightGBM lost: two hypotheses, untested here

**Extrapolation.** A tree predicts in steps, and only values it has seen. On a cold day at the edge of its training data, it cannot follow the steady rise in demand that the regression's temperature terms capture. The limitation is documented:
- **In GB practice.** In a project for National Grid ESO, TNEI modelled mean national demand with a generalised additive model and used LightGBM only for the distribution of residuals around it (and, separately, for wind generation). It noted that a GBM has "reduced effectiveness when predicting values outside the range of values provided in the original training set" and added Generalised Pareto tails to the residual distribution for that reason (TNEI, 2024, pp. 18–19 and 24).
- **In load forecasting.** Gradient-boosted trees are reported to predict high loads poorly. Yang et al. (2023), motivating an additive model, note that "model extrapolation is tough for such tree-based ensemble learners as regression tree usually assigns a constant for a split feature space".
- **In general.** März and Rasul (2024), citing Godahewa et al. (2023), note that standard gradient-boosted trees "are not adept at forecasting beyond the range of the data they have been trained on".

The winter pattern fits this explanation. This study does not test it.

**Structure.** The regression fits 48 per-slot models with explicit terms for temperature, its square and wind chill. LightGBM fits one model across all slots and must discover those shapes itself. S1 and S2 changed its settings, not its structure. S1 cut its error from 1,134 to 1,061 MW and S2 to 1,094 MW. Both use 500 trees, so tree count alone does not explain S1's larger gain; its learning rate, depth limit or sampling may.

The two hypotheses point to different designs. Extrapolation argues for keeping the regression as the main trained benchmark. Structure argues for a per-slot LightGBM, or one given the regression's temperature terms.

## What checkpoint 1 should test first

Proposed for checkpoint 1's plan, before any tuning:
1. **A pre-specified per-slot LightGBM,** to test the structure hypothesis.
2. **Each forecaster's error on the highest-demand days,** for example the top 10% by outturn, to test the extrapolation hypothesis. If it holds, LightGBM's shortfall concentrates on those days rather than spreading across winter.

Neither ran here: the plan's analysis budget ends at its own tables.

## What it means for the live benchmark

- **The trained benchmark is weaker than assumed.** Given only the regression's information and default settings, LightGBM is the easier bar. Checkpoint 1's plan must choose its trained baselines with that in mind.
- **The Chronos-2–LightGBM pair is unlikely to limit power.** On the summer days used for the power checks (April to September, three years), Chronos-2 leads LightGBM by 14.9% (90% interval 12.4–18.8%), and the two forecasters' half-hourly errors correlate at 0.59 (`results.md`, table 6). The lead is larger than Chronos-2's lead over the regression. Both figures come from the backtest. Gate G2 computes the power, at the central edge and at the interval's low end, as a separate, pre-specified step. The regression pair is likely to bind.
- **Winter matters.** The trained model is weakest in winter, the season the live benchmark cannot test confirmatorily. Every checkpoint report will give the winter tables prominence.
- **Mean daily error is not the whole story.** This study was scored on it, but for a system operator or a trader the cost of error concentrates on the most extreme days, where a model that cannot extrapolate is most likely to fail. That is the second proposed test.
- **The study produced two benchmark rules,** both still in draft (`BENCHMARK_RULES.md`):
  - **Draft rule 4.4,** whose prototype is the release-date split above: each model is scored only on days after its release or stated training cut-off.
  - **Draft rule 4.8,** from the TimesFM correction: every model forecasts one day per call, and a check before entry confirms that batching changes nothing.
- **NESO is still well ahead,** at about 700 MW of daily error over the same 960 days (the weather study's figure) against Chronos-2's 916. NESO has richer weather, estimates of embedded generation and forecasters' judgement. This benchmark asks which method makes best use of public data, not whether any matches a system operator.

## Deviations and corrections

The plan was frozen at tag `checkpoint0-plan` before any LightGBM code ran. All five pre-run checks passed first time, and scoring used the committed `score.py`, unchanged. [`REVISIONS.md`](REVISIONS.md) logs every change. The ones that matter:

- **The release date for the leakage split.** The plan gave Chronos-2's release as 20 October 2025, but also said to read the split as the weather study's leakage check did, and that used 30 October. 30 October was chosen, before any run.
- **The cost runner** forecasts one day per call and runs each forecaster in its own process. The plan named neither choice.
- **² TimesFM 2.5, corrected.** The cost check found that TimesFM's weather-study forecasts depended on the other days in each 64-day batch, later days' demand included.
  - **Correction 1:** the weather study remade them one day per call (DOI [10.5281/zenodo.24284719](https://doi.org/10.5281/zenodo.24284719)).
  - **Reported upstream** as [google-research/timesfm#577](https://github.com/google-research/timesfm/issues/577).
  - **Figures:** `results.md`, as scored, shows TimesFM at 1,474 MW (ratio 1.299). The corrected rows in `results_correction1.md` show 1,620 MW (1.428), the figures this note reports.
  - **Cost:** the batched 0.33 seconds a day came from the flawed setup. One day per call costs 10.63.
- **A false warning.** The cost run's closing warning counted the one-day TimesFM row, which is not meant to match the batched forecasts. The fix changed only the message.

## Files

- **Plan and revision log:** `PLAN.md`, `REVISIONS.md`.
- **Pre-run checks:** `checks.json`.
- **LightGBM forecasts:** `lightgbm_forecasts.csv`.
- **Scored results:** `results.md`, `results.json`. Corrected TimesFM rows: `results_correction1.md`.
- **Cost:** `cost.md`, `cost.json`.
- **Code:** `score.py` and `score_correction.py` are in this repository; `lightgbm_weather.py` and `cost_wp2.py` are in the weather-processing repository, [AndyMoran/gb-weather-private](https://github.com/AndyMoran/gb-weather-private), which despite its name is public. Environment: `env_gbcp0.txt`.

## Use of AI

I used AI tools in this work: Claude, ChatGPT, Microsoft Copilot, DeepSeek, Kimi and Z.ai. The work is designed so that results are calculated numerically and checked against ground truths, and assumptions are checked against original sources.

## Sources

- [A survey and benchmark for household electricity forecasting: from statistical to foundation models](https://www.sciencedirect.com/science/article/pii/S2352484726005639) (2026), *Energy Reports*: household-level forecasting, where LightGBM has been benchmarked most widely.
- Barros, F. S., Cerqueira, V. and Soares, C. (2021), [Empirical study on the impact of different sets of parameters of gradient boosting algorithms for time-series forecasting with LightGBM](https://link.springer.com/chapter/10.1007/978-3-030-89188-6_34), PRICAI 2021.
- Hong, T., Wang, P. and Willis, H. L. (2011), A naïve multiple linear regression benchmark for short term load forecasting, IEEE Power and Energy Society General Meeting.
- März, A. and Rasul, K. (2024), [Forecasting with hyper-trees](https://arxiv.org/abs/2405.07836), arXiv 2405.07836.
- Misiurek, K., Olkuski, T. and Zyśk, J. (2026), [Short-term electrical load forecasting at a 15-minute resolution](https://doi.org/10.3390/en19133211), *Energies* 19(13), 3211.
- Shiblee, M. F. H. and Koukaras, P. (2025), [Short-term load forecasting in the Greek power distribution system: a comparative study of gradient boosting and deep learning models](https://www.mdpi.com/1996-1073/18/19/5060), *Energies* 18(19), 5060.
- TNEI Services (2024), [*QWID FLEXER: Final Report*](https://www.neso.energy/document/353991/download), report 15929-03-R0 for National Grid ESO, 10 April 2024 (NIA project; published by NESO).
- Uzzaman, M. T., Kar, P. C., Rumee, S. T. A. and Zaber, M. I. (2026), [Cross-zonal short-term load forecasting in resource-constrained distribution grids](https://www.mdpi.com/2673-4826/7/4/143), *Electricity* 7(4), 143.
- Yang, L., Ren, R., Gu, X. and Sun, L. (2023), [Interactive generalized additive model and its applications in electric load forecasting](https://arxiv.org/abs/2310.15662), KDD 2023; arXiv 2310.15662.
- The weather study, version 2 (corrected): [10.5281/zenodo.24284719](https://doi.org/10.5281/zenodo.24284719).
