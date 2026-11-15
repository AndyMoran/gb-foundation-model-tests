# GB day-ahead demand benchmark: project

Andy Moran (Heaviside Analytics) · 15 November 2026

This file says why the benchmark exists, how the work is done, and what happens before checkpoint 1. The rules themselves live in `BENCHMARK_RULES.md`, and this file cites them by number rather than restating them. Current state and next steps are in `next_study/HANDOVER.md`; claims not yet checked are in `ASSUMPTIONS.md`.

## 1. Objective

Publish a standing, preregistered benchmark that answers one question on fair terms: do forecasting foundation models, used zero-shot, forecast GB day-ahead demand better than trained models an analyst would build, on equal inputs and on days no model can have seen? The answer comes with its cost and its uncertainty (rules 1.1–1.3).

The aim is a public reference point that a forecasting team can use before switching models, and that model developers can be measured against. It is not a service and not a product.

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
- Code follows `PIPELINE_RULES.md`: checks enforced in code, visible failure, excluded days kept and labelled, versioned formats, deterministic outputs. [Copy from the battery repository.]
- Documentation follows `WRITING.md`: Strunk and White and Zinsser, with the point first, needless words cut, one idea per sentence, and every claim specific and sourced. [Copy from the battery repository.]

### 3.7 Small, finished, named
Each checkpoint is a finished, dated artifact with its own DOI (rule 6.5). Outreach is 10–15 people, not a market.

## 4. Work before checkpoint 1

Checkpoint 1's window opens on 1 April 2027 (rule 6.1). Everything below happens before then.

| Step | Work | Gate | Target |
|---|---|---|---|
| 1 | Settle the three bracketed items in the rules (compute budget 3.3, standing reviewer 9.7, infrastructure 10.2); tag `benchmark-rules-v1` | **G1:** rules tagged | December 2026 |
| 2 | Build LightGBM, tuned only on the past within a fixed search budget (lesson 12); backtest it on the weather study's days | — | January 2027 |
| 3 | Measure c for the Chronos-2–LightGBM pair; rerun the summer power cell for both pairs at alpha 0.025 (R1) | **G2:** power | January 2027 |
| 4 | Run the power cell at a true edge of zero to check the bootstrap's false-positive rate (R12) | **G3:** size | January 2027 |
| 5 | Resolve Timestral's encoding (categorical route; mirror pass) and record it as a declared workaround (rule 4.2) | — | February 2027 |
| 6 | Move daily runs off the laptop; add a missed-day alert; run unattended | **G4:** pipeline | Running by 1 March 2027 |
| 7 | Write checkpoint 1's plan, citing rules by number; freeze and tag | **G5:** plan tagged | By 25 March 2027 |

### Gate fallbacks, fixed before each gate is evaluated

**G2 (power), evaluated on backtest forecasts only:**

| Order | Condition | Then |
|---|---|---|
| 1 | Both pairs ≥ 80% at the measured summer edge, with alpha 0.025 each | Confirmatory family is both pairs |
| 2 | Only one pair ≥ 80% at alpha 0.05 | Family is that pair alone, at 0.05; the other pair is descriptive |
| — | Neither | Checkpoint 1 is descriptive; plan says so before the window opens |

**G3 (size):** run 2,000 simulations at a true edge of zero, summer 180 days, measured c.

| Order | Condition | Then |
|---|---|---|
| 1 | False-positive rate ≤ 0.035 | Keep 7-day blocks |
| 2 | Above 0.035 with 7-day blocks, ≤ 0.035 with 14-day blocks | Use 14-day blocks; rerun G2 |
| — | Above 0.035 with both | Calibrate the threshold by simulation, and record it in the plan |

**G4 (pipeline):** at least 28 consecutive unattended days before 1 April, with no more than one missed day.

| Order | Condition | Then |
|---|---|---|
| 1 | Met | Window opens 1 April 2027 |
| — | Not met | Window opens on the first of the month after G4 is met and runs to 30 September; the plan reports power for the shorter window; below 80%, checkpoint 1 is descriptive |

## 5. Out of scope

- **Cut: fine-tuning foundation models on GB data.** The question is zero-shot use (rule 3.1).
- **Cut: probabilistic and quantile scoring.** It may be added by amendment between windows; it is not in checkpoint 1.
- **Cut: other horizons, series and countries.** Revisit at the checkpoint 3 review (rule 6.4).
- **Cut: a forecasting service or consultancy** built on the benchmark.
- **Cut: further analysis of the weather study's backtest.** E5 was its last analysis. Checkpoint 0 is a separate study with its own plan.
- **Cut: valuing forecast error in £.** The break-even price (rule 5.6) is reported instead.
- **Deferred: a portfolio-like demand series.** For the checkpoint 3 review (rule 6.4).

## 6. Risks

Risks R1–R12, their warning signs and actions are in `next_study/LESSONS.md`, Part 2. R12 matters most before the freeze:

**R12. The block bootstrap may undercover.** The credit project found that block-bootstrap intervals undercover. If they do here, p-values are optimistic and the confirmatory false-positive rate exceeds 0.025. *Action:* G3.

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
| `ASSUMPTIONS.md` | Claims labelled GROUNDED or PROVISIONAL |
| `next_study/HANDOVER.md` | Current state and next steps |
| `next_study/CORRECTIONS.md` | Errors in committed files |
| `next_study/LESSONS.md`, `weather_study/LESSONS.md` | Lessons 1–21; risks R1–R12 |
| `next_study/*.py`, `.json`, `.md` | Power checks |

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
| 2026-11-15 | Checkpoint 0: a backtest first look adding LightGBM (`checkpoint0/PLAN.md`), descriptive only | A new study, not E6 of the weather backtest; it builds the LightGBM backtest gate G2 needs anyway |
