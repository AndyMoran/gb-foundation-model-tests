# Zero-shot foundation models on GB electricity demand

**Do zero-shot forecasting models (TimesFM 2.5, Timestral, Chronos-2) forecast GB national electricity demand a day ahead better than a simple regression, and by enough to matter? How do they compare with NESO's own published forecast?**

Andy Moran (Heaviside Analytics) · MIT licence

## Status

- **Brief agreed, 2 November 2026:** [`docs/BRIEF.md`](docs/BRIEF.md).
- **Feasibility checked:** [`docs/feasibility/FEASIBILITY.md`](docs/feasibility/FEASIBILITY.md), with the scripts and their outputs.
- **Next:** a preregistered plan, frozen and tagged before any forecast is scored.
- **Running now:** daily collection of ECMWF weather forecasts for Great Britain ([`prospective/weather/`](prospective/weather/)).

No model has been run on GB demand data, and no forecast has been scored.

## The method

The same discipline as the author's macro forecasting series ([credit-impulse-realtime-prereg](https://github.com/AndyMoran/credit-impulse-realtime-prereg)):

1. **Plan first.** Every choice, including the wording of each possible result, is written down before any forecast is scored.
2. **Freeze in public.** The plan and scripts are committed and tagged; the tag's time is the evidence of timing.
3. **Run under a gate.** The official run is the first that passes pre-specified validity checks.
4. **Report everything,** in the pre-written sentences, with every deviation dated.

## Forecasts on record before their outcomes

The `prospective/` folder holds forecasts saved before the outcome they describe existed. Each day's manifest entry is pushed the same day. The evidence of timing is the push time GitHub records on its own servers (the repository's activity log), not the commit date, which the author's machine sets.

The weather manifest's first entries (forecast runs of 31 October to 2 November 2026) were collected before this repository existed and pushed afterwards: they are genuine ECMWF forecasts, verifiable by hash, but their timing is not independently evidenced. Daily pushes start on 3 November 2026.

## Data and licences

- **Elexon BMRS** (demand outturn and NESO's day-ahead forecast): "Contains BMRS data © Elexon Limited copyright and database right 2026."
- **NESO Data Portal:** "Supported by National Energy SO Open Data."
- **ECMWF open data** (CC-BY-4.0): "Contains modified Copernicus/ECMWF data." The forecast files stay on the author's machine; the manifest records their SHA-256.
- **Model weights** are not in this repository. They are downloaded at pinned revisions: TimesFM 2.5 and Chronos-2 under Apache 2.0, Timestral under Mistral's Modified MIT licence.

## Background

[`docs/background/BRIEF_2_ladder.md`](docs/background/BRIEF_2_ladder.md) sets out a longer programme this study could start: prices, forecast value, and an independent audit service. This repository covers only the demand study.

## Use of AI

The author is responsible for all design decisions, modelling runs, interpretation and final content. AI tools (including Claude, ChatGPT, Microsoft Copilot, DeepSeek, Kimi and Z.ai) were used for drafting text, writing and testing scripts, checking outputs, and sanity-checking reasoning and code. The work is designed so that AI output is never taken on trust: results are calculated numerically from the data and checked against known ground truths, and assumptions are checked against original sources. All modelling is executed by the author, who retains full responsibility for the analysis and results.
