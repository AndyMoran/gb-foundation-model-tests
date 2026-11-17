# GB day-ahead demand benchmark: rules

**Status: DRAFT, not in force.** These rules take effect when committed and tagged `benchmark-rules-v1`. That tag's time is the evidence that they came before checkpoint 1's plan and before any day in its window.

Rules are cited by number ("rule 4.2"). Checkpoint plans and reports cite rules; they do not restate them.

## 1. Purpose and form

1.1 The benchmark tests whether forecasting foundation models, used zero-shot, forecast Great Britain's day-ahead electricity demand more accurately than trained models that an analyst would build, on equal inputs and on days no model can have seen.

1.2 It is a standing benchmark: forecasts are made every day under fixed rules and reported at dated checkpoints. It is not a single study.

1.3 The maintainer commits to a minimum of three checkpoints (rule 6.1). At the third, the benchmark is reviewed and is continued, revised or closed, with the decision and its reasons published (rule 6.4). Continuity beyond that depends on the maintainer's capacity. The code, data, forecasts and rules stay public whatever is decided.

## 2. Scope and non-claims

2.1 **In scope:** day-ahead forecasts of GB national demand (INDO outturn), for each half-hour of day D, made only from inputs public by 09:30 UK time on D−1 (demand history to 08:30), from the inputs in rule 4. A forecast may be computed later that day; it must be published before day D begins (rule 4.7).

2.2 **The benchmark does not establish:**
- model quality in general, or on any other series, market, horizon or country;
- commercial value: the benchmark does not value a lower error in money. National demand error is not paid for by any one party, so any price would be an assumption. Rule 5.6's break-even price is arithmetic on measured quantities, for each user to compare with their own price; it is not a valuation;
- performance in a season, or a year, other than the one a checkpoint covers. A summer result says nothing confirmed about winter (rule 6.2);
- performance of any model revision other than the pinned one (rule 3.3);
- that a model is "best". The confirmatory tests compare named pairs; descriptive rankings are not tests.

2.3 Every checkpoint report repeats rule 2.2's list in its first section, before any result.

## 3. Entrants

3.1 **Classes.** An entrant is either a *foundation model*, run zero-shot (no fine-tuning on GB data), or a *trained baseline*, fitted only on data available at each issue time. The trained baselines are a weather regression and LightGBM, configured as stated in each checkpoint plan.

3.2 **Who may propose.** Anyone, including a model's developer, may propose an entrant by opening a repository issue labelled `entry`. The maintainer may also add entrants. The reason for every inclusion, exclusion and refusal is published in `benchmark/ENTRANTS.md`.

3.3 **Requirements.** An entrant must:
- be publicly available at a pinned revision: weights identified by a hash, run with its inference package at a pinned version, or a versioned API whose version is recorded with each forecast (rule 3.7);
- have a stated release date for that revision, and, where the developer states one, a training-data cutoff;
- run within the benchmark's compute budget, on the hardware in rule 10.2 and `benchmark/HARDWARE.md`: CPU only; at most 15 minutes wall-clock per forecast day, including model load and any re-fit; peak memory at most 12 GB; weights at most 5 GB. An API entrant's charges may not exceed £0.25 per forecast day. The maintainer runs entrants at his own cost and may refuse those above the budget, with the reason published.

3.4 **Notice.** A proposal must be made at least 30 days before the window it is to enter opens. Configuration, including covariate encoding, is fixed when the window opens (rule 4.3).

3.5 **New revisions.** A new revision of an existing model is a new entrant. The old revision keeps running to the end of the current window; whether it continues after that is decided in the next checkpoint plan.

3.6 **Entry is descriptive first.** An entrant is reported descriptively at the first checkpoint it enters. It can be in a confirmatory family (rule 7) only from a later checkpoint, and only if the plan for that checkpoint names it before its window opens.

Launch: entrants named in checkpoint 1's plan, tagged before its window opens (rule 6.3), may be confirmatory at checkpoint 1. No entrant added after that tag may be, nor may an entrant's configuration change after that tag.

3.7 **API entrants.** An entrant reached only through an API is descriptive only. It is never in a confirmatory family and never named in a checkpoint's headline (rule 7.6). The reason is rule 4.4: its training-data cutoff cannot be verified, and the provider may retrain it on days in the window without notice. Its results are labelled "not reproducible; endpoint may change; training cutoff unverifiable" in every table, and its actual charges are recorded each day. This rule is reviewed at checkpoint 3 (rule 6.4).

## 4. Inputs, configuration and the training-cutoff rule

4.1 **Equal inputs.** Every entrant receives the same demand history, the same weather (national temperature, wind speed and solar radiation, built as in the weather study) and the same calendar (day of week and England and Wales bank holidays). An entrant that cannot accept covariates is run on demand history alone and reported as such.

4.2 **Encoding.** The harness passes covariates through each model's documented interface. Where a documented interface has a known defect, the harness may use a workaround, provided it is declared and justified in the checkpoint plan before the window opens and reported with every result it affects. (Example: Timestral's calendar rows, `mistralai/timestral#9`.)

4.3 **Configuration is frozen at window opening.** A developer may submit a configuration up to the notice date (rule 3.4). Otherwise the developer's documented defaults are used. Configuration does not change during a window; a configuration dispute is handled by rule 9.5.

4.4 **Training cutoff.** An entrant is eligible for a day only if that day falls after the later of the revision's release date and its stated training-data cutoff. Trained baselines are eligible for every day, because they use only data available at each issue time.

4.5 **Equal samples within a checkpoint.** Every entrant in a confirmatory family must be eligible for every day of that checkpoint's window, and is scored on the same days. This follows from rules 3.4, 3.6 and 4.4: a confirmatory entrant was proposed before the window opened, so the whole window lies after its release. Samples are therefore equal by construction within every confirmatory comparison.

4.6 **Unequal samples across checkpoints.** Older entrants accumulate more scored days than newer ones. Any comparison across checkpoints, such as a running league table, is descriptive. It is reported on the *common window*, the days on which every compared entrant was eligible, as its primary form, and on all eligible days, with each entrant's day count stated, as a secondary form. No confirmatory claim uses days from more than one checkpoint (rule 7.3).

4.7 **Publication before outturn.** Each day's forecasts are committed to the public repository before the start of day D. The run log of the scheduled job that made them (rule 10.2) is the evidence that no forecast saw the outturn; commit times are set by the committer and are not relied on alone. Because forecasts are public daily, anyone, including a model's developer, can score them during a window. That is intended; configuration stays frozen (rule 4.3).

4.8 **One issue day per call.** Every entrant's forecasts, live or backtest, are made one issue day per call, so that no forecast can draw on another day's data. Before an entrant's first window, a call-mode check runs its forecasts for at least 20 days both one day per call and in any batch the harness might use. If they differ by more than 1 MW on any half-hour, only one-day-per-call forecasts are allowed. The check, and the reason for this rule, are recorded in `ENTRANTS.md`. Reason: weather study correction 1 (`weather_study/CORRECTIONS.md`). There, TimesFM 2.5 fitted one covariate regression across a 64-day batch, which let each forecast draw on later days' demand.

## 5. Scoring

5.1 **Metric.** Each entrant's daily mean absolute error over the 48 half-hours of day D, against INDO outturn as first published. Comparisons are ratios of mean daily MAE: entrant over baseline.

5.2 **Uncertainty.** Moving-block bootstrap of days, blocks of 7, 2,000 draws, with a seed stated in the checkpoint plan; 90% intervals.

5.3 **Missing days.** A day on which the harness fails for any confirmatory entrant is dropped for every entrant in that family, and the count is reported. If more than 10% of a window's days are dropped, that checkpoint's confirmatory tests are reported as descriptive.

5.4 **Outturn revisions.** Scores use the outturn as first published. Later revisions are reported descriptively if they change any ratio by more than 0.005.

5.5 **Cost.** Every checkpoint reports, per entrant: wall-clock time per forecast; peak memory; hardware used; and compute cost per day, priced at a published on-demand rate for equivalent cloud hardware, not at a free tier, with the rate, its source and its date stated in the checkpoint plan. An API entrant's cost is its actual charges (rule 3.7). All costs are reported in pounds, at an exchange rate whose source and date the plan states. Cost covers compute only; staff time to build, tune and maintain a model is not measured, and every report says so. Cost is descriptive and is not weighed against accuracy by any rule.

5.6 **Break-even price.** For each entrant against each trained baseline, every checkpoint reports, descriptively:
- energy error saved per day, in MWh: 24 × (baseline's mean daily MAE − entrant's mean daily MAE), in MW, with its 90% interval (rule 5.2);
- extra compute cost per day, in £: entrant's minus baseline's (rule 5.5);
- the break-even price, in £/MWh: extra cost divided by error saved, with the range implied by the interval.

If the entrant saves no error, the break-even is reported as "none: no accuracy gain". If it saves error at no extra cost, it is reported as "any price: more accurate and no more costly". The break-even is a threshold for a user to compare with their own price for forecast error; the benchmark does not say what that price is (rule 2.2).

## 6. Checkpoints and windows

6.1 **Calendar.** Windows do not overlap, and no day belongs to more than one checkpoint.

| Checkpoint | Window | Claims | Report due |
|---|---|---|---|
| 1 | 1 April to 30 September 2027 (first 180 days) | Confirmatory and descriptive | November 2027 |
| 2 | 1 December 2027 to 31 March 2028 | Descriptive only | May 2028 |
| 3 | 1 April to 30 September 2028 (first 180 days) | Confirmatory and descriptive | November 2028 |

6.2 **Seasons.** Confirmatory claims are made in summer checkpoints only. A power check (`next_study/power_check.py`, `pooled_winter.py`) found that no feasible winter window, single or two winters pooled, reaches 80% power at a true 10% edge: 33–62% for one winter, 66–71% for two. Winter checkpoints are descriptive, and their reports say so before any result.

6.3 **Plans.** Each checkpoint has a plan, committed and tagged before its window opens. It names the confirmatory family, the seed, the cost metrics and any declared workarounds, and cites these rules by number. It may not contradict them.

6.4 **Review.** The third checkpoint's report includes the review (rule 1.3). It considers at least: whether the confirmatory results replicated across checkpoints 1 and 3; whether the entrant set is still current; the maintainer's capacity; and whether to add other series or horizons.

6.5 **Records.** Each checkpoint's report, forecasts and code are deposited as a version under the repository's Zenodo concept DOI.

## 7. Confirmatory tests

7.1 **The claim.** "Entrant X's mean daily MAE is lower than baseline Y's over the window": the ratio is below 1, one-sided. p is the share of bootstrap ratios at or above 1.

7.2 **Family.** Each checkpoint's confirmatory tests form one family, fixed in its plan, with a family-wise error rate of 0.05, split equally between tests (Bonferroni). Because windows do not overlap (rule 6.1), the checkpoints are independent tests. Agreement between them is replication, not a multiple-testing cost.

7.3 **No pooling.** No confirmatory test uses days from more than one window.

7.4 **Power requirement.** A test may be confirmatory only if the plan shows, before the window opens, at least 80% power at the edge the plan names, using the error correlation measured on comparable past days. Otherwise it is descriptive.

7.5 **The 10% bar.** Whether an entrant's ratio lies credibly below 0.9 is reported for every confirmatory pair, as a descriptive result, with its prior probability stated in the plan. It is the margin set as worth switching for; it is not a test.

7.6 **Headlines, fixed in advance.** A checkpoint report leads with the sentence below that matches its result, with names filled in. Nothing may precede it but the scope (rule 2.3).

| Outcome | Headline |
|---|---|
| (a) Credibly better, and credibly below 0.9 | "X is credibly better than Y, by at least the 10% margin set as worth switching for." |
| (b) Credibly better, not credibly below 0.9 | "X is credibly better than Y, but not by the 10% margin set as worth switching for." |
| (c) Not credibly better, power ≥ 80% at the named edge | "X was not shown to be better than Y; the test had a P% chance of detecting a true edge of E, so this is evidence against an edge that large." |
| (c) Not credibly better, power < 80% at the edge in fact observed | "X was not shown to be better than Y; the test had only a P% chance of detecting an edge of the size observed, so this does not rule one out." |
| (d) Ratio above 1 | "X was less accurate than Y in this window (ratio R, 90% interval L–U). The test was one-sided, so this is reported, not confirmed." |

Outcome (b) is a positive result that missed a decision threshold, not a failure, and reports describe it in those terms.

## 8. Versioning and corrections

8.1 **The harness** is versioned (major.minor.patch) and tagged; every forecast records the harness version that made it.

8.2 **Published results are never edited.** A checkpoint's report, forecasts and scores stay as deposited.

8.3 **Fixes apply forward.** A harness fix applies from the next day forecast. Where it would change past scores, those checkpoints are re-scored in a separately labelled addendum under a new version DOI, with the original numbers beside the new ones.

8.4 **Confirmatory verdicts are never revised.** If a correction would change a verdict, the original verdict is marked *withdrawn* in `CORRECTIONS.md` and in the addendum, with the reason. The re-scored result is reported as descriptive. It does not replace the verdict.

8.5 **Errors** in committed rules, plans or code are recorded in `CORRECTIONS.md` with the commit that holds them, the error, its effect and the fix. Committed files are not edited.

8.6 **Amendments to these rules** are made only between windows. Each is committed with its reason and a new tag (`benchmark-rules-v2`, …) before the next window opens, and it applies from that window. Rules are never changed during a window.

## 9. Disputes

9.1 **Standing.** Anyone may dispute a score, an input, a configuration or the harness, by opening a repository issue labelled `dispute`. A model's developer may dispute anything about that model's entry.

9.2 **Notice before publication.** Each entrant's developer receives that entrant's results and the full method at least 10 working days before a checkpoint report is published. A demonstrated data or method error is fixed before publication; if the fix changes results materially, the notice period restarts. Disputes that are not errors do not delay publication; the developer's reply is attached (rule 9.6).

9.3 **Timetable.** The maintainer acknowledges a dispute within 14 days. He publishes a reasoned response within 60 days, saying whether the dispute is upheld, partly upheld or not upheld, with any reproduction code.

9.4 **If upheld,** the fix follows rule 8: forward from the next forecast, an addendum for past scores, and any verdict withdrawn rather than revised.

9.5 **Configuration disputes.** A developer who says their model was misconfigured may supply a configuration. It is run on the disputed window and reported in an addendum, labelled as configured after the window. The original scores and verdicts stand. The new configuration applies from the next window.

9.6 **Right of reply.** Whatever the outcome, a developer may submit a statement of up to 500 words. It is published unedited in `benchmark/RESPONSES.md` and linked beside that model's results in every later report that shows them.

9.7 **Independence.** Where a dispute concerns the maintainer's own judgement rather than a reproducible error, he may ask an independent reviewer to adjudicate. The reviewer is chosen for each dispute and must have had no professional connection to the maintainer or to the disputing developer in the past three years. The developer may object once to a proposed reviewer, with reasons; the maintainer and developer then agree a replacement within 10 working days. If they cannot, the dispute is published with both positions and without adjudication. The reviewer's name and opinion are published with the response.

9.8 Disputes, responses and outcomes stay public, including those not upheld.

## 10. Maintainer

10.1 The benchmark is maintained by Andy Moran (ORCID 0009-0004-2194-8084). It has one maintainer, and its credibility rests on these rules, on publication of every forecast before outturn (rule 4.7), and on the public record of disputes and corrections.

10.2 Forecasts run daily on GitHub-hosted runners for the public repository, as specified in `benchmark/HARDWARE.md`, not on the maintainer's own computer. Weights are fetched from their pinned revisions and checked against their hashes on every run; any cache only saves download time. If a run fails, later scheduled attempts that day forecast only the entrants still missing; attempts never overlap. Run logs are archived weekly, because GitHub keeps them for at most 90 days. A forecast made elsewhere during an outage is labelled as such. Outages are logged publicly and count under rule 5.3.
