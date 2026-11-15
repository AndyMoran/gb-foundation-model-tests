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

## Checkpoint 0 (15 November 2026)

Plan frozen at tag `checkpoint0-plan`; all WP1 checks passed first time; scored by the committed `score.py`. Mean daily error: Chronos-2 (calendar and weather) 916 MW, weather regression 1,014, LightGBM (defaults) 1,134; S1 and S2 settings 1,061 and 1,094, still behind the regression. LightGBM matches the regression in summer and is 29% worse in winter (December to February). No leakage signature (Chronos-2 / LightGBM 0.807 before release, 0.808 after). Cost (WP2) runner committed; timing pending. Results: `checkpoint0/results.md`.

### Questions for checkpoint 1's plan, from checkpoint 0

- **Why LightGBM lost, two hypotheses, neither tested.** (a) Trees cannot extrapolate beyond the temperatures in their training data, which would hurt on cold days. (b) Structure: the regression fits 48 per-slot models with explicit Tc, Tc², wind and Tc × wind (wind chill) terms; LightGBM fits one model across all slots, and S1 and S2 changed its size and learning rate but not that structure. The two lead to different designs: (a) argues for the regression as the main trained bar; (b) argues for a per-slot LightGBM, or one given the regression's temperature terms. The first backtest analysis in checkpoint 1's plan should be a pre-specified per-slot LightGBM, before any tuning.
- **Whether to add one pre-specified combination** (for example the simple average of Chronos-2 and the regression) as an entrant.
- **Winter.** The trained baseline is weakest in winter, and winter carries no confirmatory claim. Make the winter descriptive tables prominent in every report, and let the checkpoint 3 review weigh the pooled-winter option partly on this.

## Still running from the weather study

- The prospective weather window runs from 20 November 2026 to 31 March 2027 and reports in April 2027 (descriptive). The first daily push is 19 November; check with `tail -8 ~/gb-weather-data/push.log` after 10:30.
- If Mistral replies on `mistralai/timestral#9`, record the outcome in `weather_study/RESULTS.md`.

## Standing constraints

- Commits are authored "Andy Moran" <andrewgmoran@gmail.com>, with no AI co-author or session trailers.
- The Copernicus CDS key lives only in `~/.cdsapirc` and is never written to any file, script or commit.
- Model weights and data folders are never committed.
- Any script that produces a result is committed before it runs; its outputs are committed after.
- Committed files are never edited to fix errors; the fix goes in `CORRECTIONS.md`.
