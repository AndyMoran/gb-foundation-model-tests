# Next study: where things stand (15 November 2026)

Read this first in a new session. Then read `BENCHMARK_RULES.md`, `next_study/CORRECTIONS.md` and `weather_study/LESSONS.md`.

## What the next study is

A standing benchmark, not a one-off study: zero-shot foundation models against trained baselines for GB day-ahead demand, on equal weather and calendar inputs, on live days no model can have seen, with cost measured. A minimum of three checkpoints, reviewed at the third. Rules: `BENCHMARK_RULES.md` (draft, untagged).

## Decided

- **The live window is summer.** Checkpoint 1 runs from 1 April 2027 (first 180 days) and is confirmatory. Checkpoint 2, winter 2027–28, is descriptive. Checkpoint 3, summer 2028, is confirmatory, with the review.
- **Why summer:** winter cannot settle a 10% edge. Power at a true 10% edge is 33–62% for one winter and 66–71% for two pooled. Summer 180 days gives 93.7% at the backtest's summer edge (10.8%, c = 0.47), and 72.2% at the low end of its interval (7.7%). Files: `power_check.*`, `summer_edge.*`, `pooled_winter.*`.
- **c correction:** the power-check specification (`332631e`) called c = 0.7 pessimistic; it is optimistic. Recorded in `CORRECTIONS.md`, not edited. The measured c (0.54 winter, 0.47 summer) is the reference. In E5 the regression already had the calendar, so 0.54 is a measurement, not a bound.
- **Confirmatory claim:** Chronos-2 (with calendar and weather) has lower mean daily MAE than each trained baseline (weather regression, LightGBM), one-sided, family-wise 0.05 split equally. The 10% bar is descriptive; its chance is about 6% even at the backtest edge.
- **Outcome headlines are fixed** in rule 7.6. Outcome (b), "credibly better, but not by the 10% margin set as worth switching for", is the likeliest and is a positive result.
- **Caveat to carry:** the backtest edges come from days the models may have seen in training, so the 72% lower-bound sensitivity anchors the brief.

## Next steps, in order

1. Andy settles the three bracketed items in `BENCHMARK_RULES.md`: compute budget (3.3), standing reviewer (9.7), infrastructure for daily runs (10.2). D-1 (user and £ value) and the cost metrics were settled on 15 November: see `PROJECT.md` §2 and rules 5.5–5.6.
2. Commit and tag `benchmark-rules-v1`.
3. Write checkpoint 1's plan, citing rules by number. It must resolve:
   - Timestral's calendar encoding: the categorical route (target encoding), and whether the mirror pass is exempt (`mistralai/timestral#9`);
   - LightGBM tuning: only on the past, with a search budget fixed before scoring (lesson 12);
   - the compute price for rule 5.5: a published cloud rate, its source and date;
   - the input table and its gate check (lesson 1);
   - the 10% rationale.
4. Move the daily pipeline off Andy's laptop before the window opens.
5. Freeze checkpoint 1's plan by March 2027.

## Still running from the weather study

- The prospective weather window runs from 20 November 2026 to 31 March 2027 and reports in April 2027 (descriptive). The first daily push is 19 November; check with `tail -8 ~/gb-weather-data/push.log` after 10:30.
- If Mistral replies on `mistralai/timestral#9`, record the outcome in `weather_study/RESULTS.md`.

## Standing constraints

- Commits are authored "Andy Moran" <andrewgmoran@gmail.com>, with no AI co-author or session trailers.
- The Copernicus CDS key lives only in `~/.cdsapirc` and is never written to any file, script or commit.
- Model weights and data folders are never committed.
- Any script that produces a result is committed before it runs; its outputs are committed after.
- Committed files are never edited to fix errors; the fix goes in `CORRECTIONS.md`.
