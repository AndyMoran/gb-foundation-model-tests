# The benchmark, in design

**Do zero-shot forecasting models beat the trained models an analyst would build, on equal inputs, on days no model can have seen, and at what cost?**

This folder holds the design work for a standing, preregistered benchmark of GB day-ahead demand forecasting. It follows the weather study ([`weather_study/RESULTS.md`](../weather_study/RESULTS.md)). Nothing here is a result: the first live window opens on 1 April 2027.

## In brief

- **Entrants:** Chronos-2, TimesFM 2.5 and Timestral, used zero-shot, against two trained baselines: a weather regression and LightGBM.
- **Inputs:** the same demand history, weather and calendar for every forecaster.
- **Confirmatory claim:** Chronos-2's mean daily error is lower than each trained baseline's, tested one-sided on live days, with a family-wise error rate of 0.05.
- **Checkpoints:** summer 2027 (confirmatory), winter 2027–28 (descriptive), summer 2028 (confirmatory, with a published review). Winter is descriptive because no feasible winter window can settle a 10% difference.
- **Cost:** compute cost per forecast and a break-even price, the £/MWh of forecast error at which an entrant's gain pays for its extra cost. The benchmark does not value forecast error itself.
- **Headlines** for every outcome are fixed in advance.

## Status

The rules are drafted but not in force. They take effect when tagged `benchmark-rules-v1`; checkpoint 1's plan follows, tagged by 25 March 2027. Current state and next steps: [`HANDOVER.md`](HANDOVER.md).

## Where things are

| File | Contents |
|---|---|
| [`../BENCHMARK_RULES.md`](../BENCHMARK_RULES.md) | The rules, numbered for citation (draft until tagged) |
| [`../PROJECT.md`](../PROJECT.md) | Why the benchmark exists, how the work is done, gates before checkpoint 1, decision log |
| [`../ASSUMPTIONS.md`](../ASSUMPTIONS.md) | Each design claim, labelled GROUNDED or PROVISIONAL |
| [`HANDOVER.md`](HANDOVER.md) | Where things stand, and what comes next |
| [`CORRECTIONS.md`](CORRECTIONS.md) | Errors found in committed files, with their fixes |
| [`LESSONS.md`](LESSONS.md) | Lessons 13–21 and risks R1–R12 (lessons 1–12: [`../weather_study/LESSONS.md`](../weather_study/LESSONS.md)) |
| [`power_check.py`](power_check.py), [`.md`](power_check.md) | Power of each candidate window at true edges of 5–12.5% |
| [`summer_edge.py`](summer_edge.py), [`.md`](summer_edge.md) | The backtest's edge and error correlation by window, and summer power at the measured edge |
| [`pooled_winter.py`](pooled_winter.py), [`.md`](pooled_winter.md) | Whether two winters pooled reach adequate power (they do not) |

Each power script was committed before it ran, and its outputs after; the commit history is the evidence of timing. The scripts read only public files in this repository and check their hashes first. To rerun one: `python3 next_study/power_check.py`.

## The power findings in one table

| Window | Power at the measured edge | At the low end of its interval |
|---|---|---|
| Summer, 180 days | 93.7% (edge 10.8%) | 72.2% (edge 7.7%) |
| One winter, 120 days | 33–51% at a 10% edge | — |
| Two winters pooled, 240 days | 80.5% (edge 12.2%); 66.1% at 10% | 32.4% (edge 6.0%) |

These come from a backtest the models may have seen in training, so they guide the design and are not results.
