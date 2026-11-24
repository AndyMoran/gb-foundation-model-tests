# GB day-ahead demand benchmark: project

Andy Moran (Heaviside Analytics) · 15 November 2026, revised 17 November 2026

This file says why the benchmark exists, how the work is done, and what happens before checkpoint 1. The rules themselves live in `BENCHMARK_RULES.md`, and this file cites them by number rather than restating them. Current state and next steps are in `next_study/HANDOVER.md`; claims not yet checked are in `ASSUMPTIONS.md`.

## 1. Objective

Publish a standing, preregistered benchmark that answers one question on fair terms: do forecasting foundation models, used zero-shot, forecast GB day-ahead demand better than trained models an analyst would build, on equal inputs and on days no model can have seen? The answer comes with its cost and its uncertainty (rules 1.1–1.3).

The aim is a public reference point that a forecasting team can use before switching models, and that model developers can be measured against. It is not a service and not a product.

### Related work and what is distinct

Live, pre-registered forecasting benchmarks already exist. TS-Arena (Meyer et al., Paderborn University; arXiv 2512.20761) requires forecasts before the ground truth exists, runs on energy series, and lists Chronos-2. EnFoBench reports accuracy alongside computational cost for building energy. A public repository on German national day-ahead demand ([germany-load-forecast](https://github.com/hfthefeitong-dev/germany-load-forecast)) compares LightGBM with zero-shot Chronos-2 on the same covariates, with a preregistered live test; the two were level on its main test year. This benchmark does not claim to be the first of its kind. What it adds:
- GB national demand, with weather forecasts as they were available at issue time;
- equal weather and calendar inputs for every forecaster, foundation and trained;
- confirmatory tests, powered and fixed in advance, with fixed outcome headlines;
- a break-even price per entrant (rule 5.6).

## 2. The decision test

Every artifact must change a decision someone makes.

| Decision | Who decides | Addressed by |
|---|---|---|
| Adopt a zero-shot foundation model, or build and maintain a trained one | Head of a forecasting team (supplier, trader, aggregator, system operator) | Confirmatory results, cost per forecast |
| Which foundation model to trial | Same | Descriptive comparisons across entrants (rule 4.6) |
| What inputs a model must be given to be competitive | Same; model developers | Equal-input design (rule 4.1); encoding notes (rule 4.2) |
| Whether to fix a covariate defect | Model developer | Upstream reports (e.g. `mistralai/timestral#9`) |

**User and £ value (decision D-1, settled 15 November 2026).** The user is the head of a forecasting team deciding whether to adopt a foundation model. National INDO demand is a test bed: no single party pays for its error, so the benchmark does not value error in money (rule 2.2). Instead, each checkpoint reports a break-even price (rule 5.6): the £/MWh of forecast error at which an entrant's accuracy gain pays for its extra compute cost. A user compares that with their own price. The benchmark measures; the user values.

The battery project's criterion, that every artifact carries a £ number for an asset owner, does not apply to this thread. The benchmark is a separate line of work, with a capped commitment of three checkpoints (rule 1.3). It is not part of the battery objective.

Considered and not taken: pricing INDO error at imbalance cost (a valuation the data cannot support), and adding a portfolio-like demand series (deferred to the checkpoint 3 review, rule 6.4).

## 3. How the work is done

### 3.1 Test before opinion
- If a query, a primary document or a short script can settle a question, settle it that way before arguing about it. If a check takes under an hour, run it first.
- A view from me, a reviewer or an AI tool is a hypothesis. It enters a document either after a check or as a PROVISIONAL row in `ASSUMPTIONS.md`.
- Feedback is checked, not adopted. Each review point is tested against sources and code before it changes a document. Points that fail the check are recorded, with the reason.
- Every factual claim is either GROUNDED, with a citation, or PROVISIONAL, with the check that would settle it.
- Prefer the measurement to the model. For example, the summer edge was measured rather than assumed.

### 3.2 Decide before looking
- Any script that produces a result is committed and pushed before it runs, with its decision rule in its docstring. Its outputs are committed after.
- Fallbacks are written in order, with the trigger for each and a final "no trigger met" row, before the data that decides between them is seen (lesson 14).
- Thresholds are filled in before gates are evaluated.
- Every decision goes in the decision log (§10), with its date and reason.

### 3.3 Measurement, not verdict
- Every published number carries its uncertainty and its limits. Non-claims come first (rule 2.3).
- A null result is a valid result. Outcome (b) is a positive result that missed a decision threshold (rule 7.6).
- Named parties see their results before publication, and their replies are published (§7).

### 3.4 One source of truth
- Each rule, definition or table lives in one file; other files cite it. Copies drift.
- Code is the source of truth for every number; prose explains code. Every published number regenerates from the repository against hashed inputs.
- The repository is canonical. Project files elsewhere are snapshots.

### 3.5 Adversarial self-review
Own work is held to the standard applied to external critique. If two files disagree, or a file breaks a principle it states, that is a defect, recorded in `CORRECTIONS.md` (rule 8.5).

### 3.6 Pipeline and writing
- Code follows `PIPELINE_RULES.md`: checks enforced in code, visible failure, excluded days kept and labelled, versioned formats, deterministic outputs. Adapted from the battery project.
- Documentation follows `WRITING.md`: Strunk and White and Zinsser, with the point first, needless words cut, one idea per sentence, and every claim specific and sourced. Adopted from the battery project.

### 3.7 Small, finished, named
Each checkpoint is a finished, dated artifact with its own DOI (rule 6.5). Outreach is 10–15 people, not a market.

## 4. Work before checkpoint 1

Checkpoint 1's window opens on 1 April 2027 (rule 6.1). Everything below happens before then.

| Step | Work | Gate | Target |
|---|---|---|---|
| 1 | Settle the bracketed items in the rules (done 17 November); tag `benchmark-rules-v1` | **G1:** rules tagged | December 2026 |
| 2 | Build LightGBM and backtest it on the weather study's days: checkpoint 0 (`checkpoint0/PLAN.md`, done). Backtest any further LightGBM configuration, such as per-slot, under its own committed script before G2 runs; none added after that counts for the comparator | — | January 2027 |
| 3 | Compute G2's power table for both confirmatory pairs (below), at alpha 0.025 and 0.05, at each pair's measured summer edge and its interval's low end, at c − 0.05, c and c + 0.05 (R1) | **G2:** power | January 2027 |
| 4 | Simulate at a true edge of zero to check each test's false-positive rate (R12) | **G3:** size | January 2027 |
| 5 | Resolve Timestral's encoding (categorical route; mirror pass) and record it as a declared workaround (rule 4.2) | — | February 2027 |
| 6 | Move daily runs off the laptop; add a missed-day alert; run unattended | **G4:** pipeline | Running by 1 March 2027 |
| 7 | Write checkpoint 1's plan, citing rules by number; freeze and tag | **G5:** plan tagged | By 25 March 2027 |

### The confirmatory pairs

Checkpoint 1's confirmatory pairs are named here, before G2:
- Chronos-2 against the weather regression;
- Chronos-2 against the LightGBM comparator: of the LightGBM configurations backtested under committed scripts before G2 runs (step 2), the one with the lowest mean daily error on the backtest's summer days (April to September). From checkpoint 0 that is S1 unless a later configuration beats it. The comparator is chosen on error, never on power: the benchmark tests against the hardest trained opponent it has.

The ratio is entrant error over baseline error, and the claim is that it lies below 1, one-sided (rules 5.1 and 7.1).

### Gate fallbacks, fixed before each gate is evaluated

**G2 (power), evaluated on backtest forecasts only.** Power is reported as a table: for each pair, at its measured summer edge and at the low end of that edge's interval, at c − 0.05, c and c + 0.05, where c is the pair's measured summer error correlation. The measured c is a backtest estimate, so the decision reads the c − 0.05 column, at the measured edge. A pair with no measured edge (ratio interval including or above 1) cannot be confirmatory.

The gate reads power at the measured edge, not the low end of its interval. Leakage in training (lesson 2) would make the backtest edge too large, and a true edge near the low end may go undetected. The plan states power at both. If the test then fails, the report's headline says how much power it had (rule 7.6, outcome (c)).

| Order | Condition | Then |
|---|---|---|
| 1 | Both pairs ≥ 80% at the measured summer edge, with alpha 0.025 each | Confirmatory family is both pairs |
| 2 | Not order 1, and at least one pair ≥ 80% at alpha 0.05 | Family is the pair with the higher power at 0.05, alone at 0.05; on a tie, the pair against the baseline with the lower summer error. The other pair is descriptive |
| — | Neither | Checkpoint 1 is descriptive; plan says so before the window opens |

**G3 (size):** run 5,000 simulations at a true edge of zero, over the window's 180 days (rule 6.1), measured c, with the confirmatory test exactly as in rules 5.2 and 7.1: one-sided, p the share of bootstrap ratios at or above 1. The gate checks the *per-test* false-positive rate at alpha 0.025, which is what rule 7.2's Bonferroni split needs: if each test holds 0.025, the two-pair family holds 0.05 whatever the correlation between them. The joint family rate is reported beside it, descriptively.

What the gate can see: at 5,000 simulations the Monte Carlo standard error at 0.025 is 0.0022. A correctly sized test passes the 0.032 threshold 99.9% of the time; a true rate of 0.035 fails it 87% of the time, and 0.040 almost always. A pass rules out gross undercoverage; it does not certify exact size.

| Order | Condition | Then |
|---|---|---|
| 1 | Per-test false-positive rate ≤ 0.032 | Keep 7-day blocks |
| 2 | Above 0.032 with 7-day blocks, ≤ 0.032 with 14-day blocks | Use 14-day blocks; rerun G2 |
| 3 | Above 0.032 with both | Calibrate the critical value with 14-day blocks: for each test, the p-value cut-off α* is the quantile of G3's 5,000 null p-values matching that test's alpha (2.5th percentile for 0.025, 5th for 0.05). Confirm α* on 5,000 new simulations with a new seed. If the per-test rate is ≤ 0.032 there, the plan uses α*, and G2 is rerun at α* |
| — | α* not confirmed | Checkpoint 1 is descriptive; the plan says so before the window opens |

**G4 (pipeline):** at least 28 consecutive calendar days of unattended running before 1 April, with at most one of those days missed.

| Order | Condition | Then |
|---|---|---|
| 1 | Met | Window opens 1 April 2027 |
| — | Not met | Window opens on the first of the month after G4 is met and runs to 30 September. G2 and G3 are rerun at that window's length, and the plan is revised and re-tagged before the window opens. Below 80% power, checkpoint 1 is descriptive |

## 5. Out of scope

- **Cut: fine-tuning foundation models on GB data.** The question is zero-shot use (rule 3.1).
- **Cut: probabilistic and quantile scoring.** It may be added by amendment between windows; it is not in checkpoint 1.
- **Cut: other horizons, series and countries.** Revisit at the checkpoint 3 review (rule 6.4).
- **Cut: a forecasting service or consultancy** built on the benchmark.
- **Cut: further analysis of the weather study's backtest.** E5 was its last analysis. Checkpoint 0 and the tails study (`tails/PLAN.md`) are separate studies, each with its own plan frozen before it runs.
- **Cut: valuing forecast error in £.** The break-even price (rule 5.6) is reported instead.
- **Deferred: a portfolio-like demand series.** For the checkpoint 3 review (rule 6.4).
- **Deferred: tails 2,** uncertainty on the hardest days (spread–skill and interval coverage). Comes back if tails 1 finds any cold-day effect (`next_study/HANDOVER.md`, step 3).

## 6. Risks

Risks R1–R12, their warning signs and actions are in `next_study/LESSONS.md`, Part 2. R12 matters most before the freeze:

**R12. The block bootstrap may undercover.** The credit project found that block-bootstrap intervals undercover. If they do here, p-values are optimistic and each confirmatory test's false-positive rate exceeds its 0.025 (rule 7.2). *Action:* G3.

Two risks from outside the benchmark:

- **Capacity.** The battery declaration work runs to January 2027, overlapping steps 1–4. Being late at G1–G3 delays G5, not the window, unless G5 misses 25 March. In that case the window moves under G4's fallback.
- **The weather study's live window reports in April 2027,** as checkpoint 1 opens. Its report is drafted in March.

## 7. Publication and outreach

### 7.1 Before each checkpoint report
- Developers receive their entrant's results and the method at least 10 working days before publication (rule 9.2). Every correction is logged publicly with its reason (rule 8).
- Disputes that are not errors are published with the developer's reply attached (rule 9.6). Results are not withheld.
- Before the first report, check the licence terms for publishing derived forecasts: ECMWF open data, NESO data, and each model's licence. [PROVISIONAL; see `ASSUMPTIONS.md`.]

### 7.2 Outreach
Rules: one narrow ask; offer before asking; email the first author, not the last; one follow-up after two weeks; expect silence.

| Group | Who | Number |
|---|---|---|
| Model developers | The Chronos, TimesFM and Timestral teams | 3 |
| Benchmark builders | The TS-Arena team (Paderborn University) | 1 |
| System operator | NESO's demand forecasting team | 2 |
| Practitioners | Forecasters at suppliers, traders and aggregators | 4 |
| Academic | Researchers in energy and time-series forecasting | 3–4 |

The ask, before checkpoint 1 opens: "I'm running a preregistered live benchmark of zero-shot forecasting models on GB demand, and I'd value your reaction to the rules." After each report: "Checkpoint N found …, and I'd value your reaction."

## 8. Definition of done

**Before the window:** G1–G5 passed, or their fallbacks recorded; the pipeline running unattended; checkpoint 1's plan tagged.

**Checkpoint 1:** report published with its DOI by November 2027, headline per rule 7.6, developers' replies attached, and 10–15 people having seen it.

**The commitment:** three checkpoints and the published review (rules 1.3 and 6.4).

## 9. Files

| File | Holds |
|---|---|
| `BENCHMARK_RULES.md` | The rules (draft until tagged) |
| `PROJECT.md` | This file: why and how |
| `PIPELINE_RULES.md`, `WRITING.md` | How code and documents are written (§3.6) |
| `ASSUMPTIONS.md` | Claims labelled GROUNDED or PROVISIONAL |
| `next_study/HANDOVER.md` | Current state and next steps |
| `next_study/CORRECTIONS.md` | Errors in committed files |
| `next_study/LESSONS.md`, `weather_study/LESSONS.md` | Lessons 1–24; risks R1–R12 |
| `next_study/*.py`, `.json`, `.md` | Power checks, including `pooled_winter.md` (rule 6.2) |
| `checkpoint0/` | The LightGBM backtest: plan, revisions, results and cost |
| `tails/` | Errors on the coldest, peak and holiday days of the backtest |
| `lgbm_variants/` | Five LightGBM variants aimed at the heating response |
| `context_novelty/` | Foundation models on days colder than their eight-week context |
| `.github/workflows/runner_check.yml` | One-off check of the GitHub runner (A13) |
| `benchmark/HARDWARE.md` | The runner and budget specification (rules 3.3, 10.2); to be written at G4 |

## 10. Decision log

| Date | Decision | Reason |
|---|---|---|
| 2026-11-12 | E5 is the weather backtest's last analysis | Avoid a chain of further looks (lesson 4) |
| 2026-11-15 | Next study uses equal weather and calendar for every forecaster | The weather study's unequal calendar (lesson 1) |
| 2026-11-15 | LightGBM added as the trained benchmark | The regression is a weak bar |
| 2026-11-15 | The live window, not a backtest, carries confirmatory claims | Possible training leakage (lesson 2) |
| 2026-11-15 | Power-check rule gave "next winter"; superseded | Both branches failed; the fallback's premise was false (`CORRECTIONS.md` 2) |
| 2026-11-15 | c = 0.7 relabelled optimistic; measured c is the reference | Specification error (`CORRECTIONS.md` 1) |
| 2026-11-15 | Checkpoint 1 is summer 2027, 180 days from 1 April | 93.7% power at the backtest's summer edge; 72.2% at its lower bound |
| 2026-11-15 | Winter checkpoints are descriptive | No feasible winter window reaches 80%, single or pooled (`pooled_winter.md`) |
| 2026-11-15 | Standing benchmark, minimum three checkpoints, review at the third | Model churn; a commitment that can be kept |
| 2026-11-15 | Rules document written and tagged before checkpoint 1's plan | The plan cites rules by number |
| 2026-11-15 | Outcome headlines fixed in advance (rule 7.6) | Stops the result being reframed after it is known |
| 2026-11-15 | Gate fallbacks for G2–G4 written before evaluation (§4) | Choice provably made before results are seen |
| 2026-11-15 | D-1: the user is the forecasting team; no £ valuation; each checkpoint reports MWh saved, compute cost and a break-even £/MWh, descriptively (rule 5.6) | National demand error has no single owner who pays for it, so a valuation would be an assumption; the break-even lets each user apply their own price |
| 2026-11-15 | The battery project's £ criterion does not apply; the benchmark is a separate thread with a capped commitment | Avoid drift between the two objectives |
| 2026-11-15 | Developers get 10 working days' notice before each report (rule 9.2) | Adopted from the battery project's publication policy |
| 2026-11-15 | Related work (TS-Arena, EnFoBench) acknowledged; the benchmark's distinct contribution stated (§1) | Live pre-registered benchmarks already exist |
| 2026-11-15 | G2 power read at c − 0.05 | The measured c comes from backtest days the models may have seen |
| 2026-11-15 | Checkpoint 0: a backtest first look adding LightGBM (`checkpoint0/PLAN.md`), descriptive only | A new study, not E6 of the weather backtest; it builds the LightGBM backtest gate G2 needs anyway |
| 2026-11-17 | Compute budget: CPU only, 15 minutes, 12 GB and 5 GB of weights per entrant-day (rule 3.3) | About 85 times the slowest entrant's measured time (`checkpoint0/cost.md`); fits a 4-CPU, 16 GB runner |
| 2026-11-17 | Daily runs on GitHub-hosted runners; run logs, not commit times, are the timestamp evidence (rules 4.7, 10.2) | Free for public repositories; server-side timestamps; logs archived weekly as GitHub keeps them 90 days |
| 2026-11-17 | Disputes: reviewer chosen per dispute, with an objection fallback (rule 9.7) | No one has agreed to a standing role; rule 8.6 allows one later |
| 2026-11-17 | Launch clause: checkpoint 1's named entrants may be confirmatory there (rule 3.6) | Otherwise the first confirmatory window would slip to summer 2028 |
| 2026-11-17 | API entrants descriptive only, labelled, actual spend recorded, reviewed at checkpoint 3 (rule 3.7) | Their training cutoff cannot be verified (rule 4.4) |
| 2026-11-17 | Issue time is defined by the inputs used (public by 09:30 on D−1), not by when the job runs (rule 2.1) | Scheduled runs come after 09:30; the weather study already works this way |
| 2026-11-17 | G3: 5,000 simulations, per-test threshold 0.032, one-sided as rule 7.1 | 2,000 at 0.035 detected a true 0.035 only half the time; the unqualified "false-positive rate" was misread as family-wise |
| 2026-11-17 | Confirmatory pairs named before G2: Chronos-2 against the regression and against the LightGBM comparator, chosen on summer backtest error (§4) | The comparator must be the hardest opponent, and chosen before power is seen |
| 2026-11-17 | G2 order 2 covers "both pairs powered at 0.05, not both at 0.025"; power read at the measured edge, with the low end stated | The table had no row for that case (`CORRECTIONS.md` 3) |
| 2026-11-17 | G3's last fallback specified: calibrated α* from the null p-values, confirmed on fresh simulations, or descriptive | "Calibrate the threshold" left the threshold to be chosen after the result |
| 2026-11-17 | G4's fallback reruns G2 and G3 at the shorter window and re-tags the plan | Power and size depend on the window's length |
| 2026-11-17 | `PIPELINE_RULES.md` and `WRITING.md` added, adapted from the battery project with this repository's examples | §3.6 cited them before they existed here |
| 2026-11-17 | Tails study added: errors on the backtest's coldest days, descriptive, before G2 (`tails/PLAN.md`) | The cost of error concentrates on extreme days, which mean error hides; checkpoint 0 proposed the test and no tail result has been seen |
| 2026-11-17 | Tails 1 frozen as reviewed; spread–skill and interval coverage deferred to tails 2, with a trigger | Both concern uncertainty, need their own design and (for coverage) new quantile forecasts; keeps tails 1 bounded |
| 2026-11-18 | Rules revised before tagging, after an external review: outcome labels (c)–(e); "credibly better" and "credibly below 0.9" defined, with the per-test level 0.05 ÷ n and G3's calibrated cut-off; one headline per confirmatory pair; harness and entrant failures separated by a mechanical test, with unclear cases decided by the maintainer, recorded and open to dispute (5.3); the existing gap rule written into 4.1; 0.005 stated as a chosen reporting threshold (5.4); half-hours per day on clock changes (5.1); 180-day windows dated exactly (6.1); "absolute error avoided" in MWh (5.6); API rule's reason corrected (3.7); smaller clarifications in 3.1, 3.3, 4.1, 4.5, 4.8, 5.4, 5.5, 7.4, 8.6, 9.2, 10.1 | The review found real gaps before the tag. Not adopted: relaxing 4.8's 1 MW check (it compares one model in two call modes, with seeds fixed, so it should match exactly); a boundary for 5.3's 10% ("more than" already settles it); dropping the 5 GB cap (current time-series foundation models are far smaller) |
| 2026-11-18 | The revised rules are tagged `benchmark-rules-v2`; `benchmark-rules-v1` stays where it is, at 9d1e357 | `v1` had already been tagged and pushed on 17 November, before the review. A published tag is evidence and is not moved; rule 8.6 provides a new tag for amendments before the next window opens |
| 2026-11-19 | LightGBM variants study planned (`lgbm_variants/PLAN.md`): five pre-specified changes, best chosen on error, before G2 | The tails study ruled out temperatures outside the training range and found the gap on ordinary winter days; the comparator should be the strongest trained opponent |
| 2026-11-19 | Literature check for the LightGBM variants plan: no variant is new; the German repository is the nearest study and is added to related work | Opened before citing |
| 2026-11-20 | Context novelty study planned (`context_novelty/PLAN.md`): are the foundation models worse when tomorrow is colder than their context, among equally cold days? | Tails found Chronos-2's cold-peak under-forecast; WhatIf-Bench and CovNovBench (NeurIPS 2026) and a German price study point to covariates outside the context |
| 2026-11-20 | Checkpoint 1 made conditional: Andy decides on 8 January 2027, with the variants result in hand; if not, the rules are published as a proposal | Andy's concern is a commitment running far into 2027; the December studies are backtest-only |
| 2026-11-20 | Context novelty plan revised to version 2 after two reviews, before any script ran on real data; to be tagged `context-novelty-plan-v2`, with `context-novelty-plan` (9e1002b) kept as version 1: weather provenance stated; novel cold days matched to non-novel cold days on T1's temperature measure and month; one primary outcome (Chronos-2's peak error relative to the regression, matched difference) read against a chosen 250 MW threshold by its interval's lower bound; cold-spell cluster bootstrap; TimesFM exploratory and LightGBM descriptive; references fixed | "Equally cold" could confuse novelty with coldness or season; an interval above zero alone is not decision-relevant. Not adopted: re-matching inside block-bootstrap draws (the matching uses covariates only and is fixed before errors are seen; whole cold spells are resampled instead) |
| 2026-11-21 | Context novelty 2 drafted and parked (`context_novelty_2/PLAN.md`), not tagged: Chronos-2 at hourly resolution with 8 weeks and with about 49 weeks of context; 7 November novel days that a year of history makes ordinary, against 7 January days that stay novel, each matched to an ordinary cold control; scored on hours; read day by day and spell by spell as a directional pilot | The weather-only check (`context_novelty/context_check.py`) showed a 24-week half-hourly context changes no novel day, while about 49 weeks splits them by month, a built-in control the first study lacked. One review on 21 November is reflected. Unparked after the LightGBM variants study is published |
| 2026-11-22 | Imbalance cost study drafted and parked (`imbalance_cost/PLAN.md`), not tagged: each forecaster's misses costed as (outturn − forecast) × (System Price − day-ahead price) for a price-taking supplier with national-shaped demand; the implied cost ratio per half-hour; indicative only | Andy asked whether the misses could be costed. Separate from the asymmetric study because it needs new price data, a licence check (day-ahead auction prices are licensed; Elexon's Market Index Price is the open proxy) and its own rules. Unparked after the asymmetric study is published |
| 2026-11-22 | LightGBM variants published (96f8ba6): V1, the residual on the regression, is the best variant (0.984 times the regression's error) and the LightGBM comparator if checkpoint 1 runs | Chosen on error as the plan required; optimistic, as chosen on the same days |
| 2026-11-22 | Asymmetric cost study planned, tagged `asymmetric-plan` (dc78a88), run and published (53e340d): cost-weighted error at shortfall-to-surplus ratios 0.5 to 10, all half-hours and cold-day peaks, with a pre-specified 50:50 average of Chronos-2 and the regression as a descriptive forecaster | Chronos-2 was best on average but set cold-day peaks too low (tails study); a reader with asymmetric costs needs to know where that matters |
| 2026-11-23 | Arbitrage signal study planned, tagged `arbitrage-plan` (468ccdc), run and published (468b3fe): battery timing (missed spread), gain against NESO's forecast, combination with NESO, day-to-day direction; in MW of demand, no prices | Andy asked whether being wrong in the right direction could be profitable against a regression; a demand-only screen before any price study |
| 2026-11-23 | The arbitrage plan's bias-correction sign is corrected in `arbitrage/REVISIONS.md` 1, not in the tagged plan | The plan's wording would have doubled the bias; the code does what the plan intended (lesson 26) |
| 2026-11-23 | The price study (`imbalance_cost/PLAN.md`) is to be reopened, after three design questions are settled with Andy: training leakage, which prices, and net demand | Its unparking condition is met, and the arbitrage study found both demand-side preconditions for an edge |
| 2026-11-23 | Imbalance study redrafted and tagged `imbalance-cost-plan` (f0678fa): two stages (backtest pilot, then live), System Price against Market Index Price, net exposure in £ per GWh, demand-proxy dispatch ranking, no net-demand forecast | Training overlap makes a money claim from the backtest unsafe; open prices only; the supplier case needs demand error alone (a review agreed) |
| 2026-11-23 | Chronos-2 calendar forecasts issued daily for the live window (`calendar_live.py`, e0704d5), each tied by hash to the prospective run's demand input | The weather study's live arm has no calendar version; issuing before each day is stronger evidence than reconstructing later |
| 2026-11-24 | Daily push and calendar tasks moved to first run at 11:15 and 11:45 | The 10:00 push failed two days running until the hourly ERA5 download refreshed the month's file |
| 2026-11-24 | Imbalance stage 1 published as a pilot (ecfd1e0): exposure not clearly different, Chronos-2 against the regression; frequency and tail added after the results (`explore.py`) | A review noted the mean cannot show how often misses cost or how bad the worst were |
| 2026-11-24 | Disagreement value study planned (`disagreement/PLAN.md`): what switching from NESO's day-ahead forecast to each forecaster would have earned, v = (F − NESO) × (SP − MIP) × 0.5 h; measures by size of disagreement, price stress and direction, a sign-flip null and a year-by-year split; two stages, as the imbalance study. Frozen at tag `disagreement-plan-3a260a2` (3a260a2) | Andy asked whether the foundation models are "more directionally right" than NESO, where a trader's edge would lie. Against NESO, Chronos-2 is about 31% less accurate, so its only case is settlement value; the plan treats a near-null as likely and worth publishing |
| 2026-11-24 | The tag `disagreement-plan` points to ddb2798, not the plan, and stays: the repository's rules forbid deleting tags. The plan is frozen at `disagreement-plan-3a260a2` (`disagreement/REVISIONS.md` 1) | The plan's commit had not been pushed when the tag was made. Push before asking Andy to tag |
| 2026-11-24 | Literature check for the disagreement plan (`disagreement/LITERATURE.md`): seven papers a reviewer sent or cited, each opened; six cited | All exist. Two citations were incomplete, one analogy was stretched, and Bui et al.'s abstract overstates its imbalance result against its own tables (recomputed figures cited). The sign-flip null and year-by-year split came from this check |
| 2026-11-24 | Disagreement stage 1 published as a pilot (aaf12c6; `score.py` a402043, results aa1021c): Chronos-2 had 1.31 times NESO's daily error, and switching to it was neither clearly a gain nor a loss (9 £ per GWh, −11 to 28); within chance on every sign-flip measure. LightGBM S1 clearly lost (−50) and was worse than chance | The test detects about ±£20 per GWh; it found reliably bad forecasters and no reliably good one. On this evidence a supplier has no reason to switch from NESO to Chronos-2 |
| 2026-11-24 | The disagreement study's stage 2 replication rule fixed (`disagreement/REVISIONS.md` 8) before any stage 2 outturn, NESO forecast or price is fetched | A review asked what would count as replication, given stage 2's short window. Fixing it now keeps it independent of the stage 2 data |
