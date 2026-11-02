# Brief 3, revision 3: zero-shot foundation models against GB day-ahead demand forecasts

Final brief · 2 November 2026 · Andy Moran (Heaviside Analytics)

The brief for a single, finishable study. Revision 3 makes the final clarifications: the threshold's scope, what Ofgem's 1B metric is and is not, daily publication of prospective forecasts, and how the intervals are labelled. Revision 2 answered a review of revision 1: one information cut-off for every forecaster, set from evidence; "post-release" in place of "clean"; a threshold set by use, not by power; a comparator hierarchy; an exact specification in place of "package defaults"; and the weights' own licences. It rests on the feasibility check (`feasibility/FEASIBILITY.md` (in this repository: `docs/feasibility/FEASIBILITY.md`), Parts 1–3). The next step is a preregistered plan.

## 1. The question

**Do zero-shot forecasting models (TimesFM 2.5, Timestral, Chronos-2) forecast GB national electricity demand a day ahead better than a simple regression, and by enough to matter? How do they compare with NESO's own published forecast? The study states in advance what it cannot establish.**

The practical-importance threshold applies to the three primary comparisons against the regression only. Comparisons with NESO's forecast are reported as estimates with intervals, without a practical-importance test.

- **For whom:** GB energy analysts, traders and battery operators, many of them interested in these models.
- **What it produces:** one archived note, one public repository, one LinkedIn post.
- **When to stop:** when the note is published. Prices, weather inputs, value and the audit service are later, separate decisions (Brief 2).

## 2. What is compared, and how the comparisons rank

| Role | Forecaster | Weights licence | Pinned revision | Post-release from |
| --- | --- | --- | --- | --- |
| Model | TimesFM 2.5 (200M) | Apache 2.0 | `1d952420…` | 15 September 2025 |
| Model | Chronos-2 (120M) | Apache 2.0 | `29ec3766…` | 30 October 2025 |
| Model | Timestral-209M | Mistral's Modified MIT | `9874d252…` | 15 October 2026 |
| **Primary comparator** | Simple regression | — | — | — |
| **Secondary comparator** | NESO's day-ahead forecast, as published | NESO and Elexon open licences | — | — |
| Floor (reported, not tested) | Seasonal naive: the same local clock time one week earlier | — | — | — |

- **Primary:** each model against the regression. Three comparisons, tested with a Holm adjustment, as in the original credit study, and judged against the practical-importance threshold (Section 4).
- **Pre-specified secondary:** each model against NESO's forecast, reported as estimates with intervals; no practical-importance threshold.
- **Exploratory:** everything else, including comparisons with seasonal naive and between models.

All three models are used zero-shot on demand history only. The plan fixes, for each: the weight revision, the library and version, every forecasting setting (not "defaults", which can change between releases), the context length, and how the horizon is produced and cut to the target half-hours.

## 3. Data and timing (from the feasibility check)

- **Series and target:** GB national demand, scored against Elexon's initial outturn (INDO). NESO scores its own forecast against INDO (matched in all 144 half-hours checked), INDO was known at the time, and it is never republished. NESO's later Historic Demand Data (ND) differs by about 95 MW and is used only as a robustness check.
- **One information cut-off for every forecaster: 09:30 UK local time on day D−1.**
  - **NESO:** for each half-hour of D, the latest Elexon publication at or before 09:30. For daytime and evening half-hours that is the 08:45 issue; early-morning half-hours come from the 09:15 update. This reproduces the forecast NESO itself records in all daytime cases checked and most early-morning ones. A blank value is replaced by that half-hour's most recent earlier publication.
  - **Models and regression:** INDO for half-hours ending at or before 08:30 UK time on D−1. The one-hour buffer covers an arrival delay Elexon's timestamps cannot measure.
- **Targets:** every half-hour of day D: 48, or 46 or 50 on clock-change days.
- **Timestamps:** Elexon's `publishTime` is the record of when a forecast was issued. NESO's performance file is used to check values, not times, because its timestamps are inconsistent.
- **Licences:** Elexon BMRS Open Data Licence ("Contains BMRS data © Elexon Limited copyright and database right [year]") and NESO Open Data Licence ("Supported by National Energy SO Open Data"). Both allow publication and commercial use.

## 4. How it is scored

- **Metric:** mean absolute error in MW over the half-hours of each target day, averaged over days. It is in physical units, and not distorted by low overnight demand as percentage errors are.
- **Comparison:** each model's error divided by the comparator's. The three primary comparisons are tested with Holm-adjusted p-values from a block bootstrap over days. Block-bootstrap 90% intervals are reported for every comparison and labelled descriptive, because they are not adjusted for multiplicity.
- **"Enough to matter":** a minimum useful reduction in error against the regression, fixed in the plan with a rationale tied to how a day-ahead demand forecast is used. NESO's reported metric 1B, the average absolute error in MW against INDO, supports the choice of metric: it is how the system operator's own day-ahead forecast is reported. It does not supply a threshold: reported metrics exist for transparency and "are not used directly in Ofgem's performance scoring" (NESO). The minimum useful gain therefore needs its own rationale, given in the plan. The power check then reports whether the study can estimate that reduction with reasonable precision; it does not set it. Smaller gains are reported, but not called practically meaningful.
- **Windows,** three columns for every model:

  | Column | Window | Label |
  | --- | --- | --- |
  | Full | January 2024 to October 2026 | "Inside possible training data"; perturbation and placebo leakage checks |
  | Post-release | From each model's post-release date (Section 2) | Shows only that the model was published before the period, not that its training excluded GB demand. About 13 months for TimesFM 2.5 and 12 for Chronos-2; about 2 weeks for Timestral, reported descriptively with no performance conclusion |
  | Prospective | Forecasts saved daily from the start of collection | Scored once enough days have passed |

  No headline compares one model's post-release column with another's full column.

## 5. What the study cannot establish, stated in advance

- **Training leakage** in the full and post-release windows: the models may have seen GB demand in training. The checks make memory more or less plausible; they cannot rule it out.
- **Generality:** one series (national demand), one country, one horizon (day ahead).
- **Fine-tuning:** zero-shot only.
- **Weather:** the models get no weather inputs; NESO's forecast uses weather. A NESO win may reflect weather information rather than modelling skill.
- **Value:** accuracy, not money.

## 6. The prospective column

Each day, after 09:30 UK time, a script makes and saves every model's forecast for the next day, from the pinned weights, before the outturn exists. Each saved forecast records the model, revision, library version, settings, context end and save time, with a SHA-256 in a manifest. **Each day's forecast file and manifest entry are pushed to the public repository the same day, before the target day begins,** so each forecast is on record before its outcome. The evidence is the push time GitHub records on its own servers (in the repository's activity log), not the commit date, which the author's machine sets and could backdate. A weekly push would not: several outcomes could already be known when it is made. The weather collection adopts the same daily push. Scoring it needs its own short plan, written before the first prospective day is scored.

## 7. Decisions for the plan

1. **The "enough to matter" threshold** and its rationale (Section 4).
2. **The regression specification:** lags, calendar terms and holiday list.
3. **Context length** for the models: for example, the last 28 days of half-hours before the cut-off.
4. **Start the prospective column now** (Section 6)?
5. **A new public repository** for the plan, scripts, manifests and results.

## 8. Next steps

1. Agree this brief.
2. Write the plan: pre-written result sentences, a validity gate (including the check that the reconstructed NESO forecast matches NESO's own record), and the power check.
3. Two review rounds at most, then freeze and tag.
4. Run, check every number independently, write the note, archive it with a DOI, post.
