# Code

Run in this order, from this folder. No step before the tag runs a foundation model on real GB demand.

| Step | Command | Reads | Runs a model? |
|---|---|---|---|
| 1 | `python fetch.py --probe` | one day of each source | no |
| 2 | `python fetch.py` | downloads everything to `../data/`, hashes in `fetch_manifest.json` | no |
| 3 | `python fetch.py --gaps` | real INDO only | no |
| 4 | `python selftest.py` | synthetic data | no |
| 5 | `python selftest.py --models` | synthetic data | yes, on synthetic data only |
| 6 | `python run.py pipeline-test OUT --synthetic` | synthetic data, stand-in in every model slot | no |
| 7 | `python power.py` | real INDO, regression errors only | no |
| 8 | `python freeze.py`, then `python freeze.py --tag` | checks; writes `../plan/PLAN_LOCK.json`, tags `demand-plan`, pushes | no |
| 9 | `python run.py real` | real data; refuses if any locked file has changed | yes, after the tag only |

| File | Contents |
|---|---|
| `common.py` | timing rules and constants (issue time, cut-offs, horizons, windows, seeds) |
| `inputs.py` | INDO loading, model contexts, targets, NESO forecast reconstruction |
| `baselines.py` | weekly-lag regression, seasonal naive, independent regression for gate check 6 |
| `stats.py` | daily MAE, moving-block bootstrap, one-sided p-values, Holm |
| `models.py` | TimesFM 2.5, Chronos-2, Timestral wrappers with every setting written out; the stand-in |
| `synth.py` | synthetic GB-like demand and NESO publications, for tests |
| `run.py` | the run: forecasts, exclusions, L1 check, gates, results |
| `selftest.py` | checks A–G |
| `power.py` | power check from the regression's real errors |
| `fetch.py` | download, probe, comparison and gap report |
| `freeze.py` | the freeze: checks, lock file, tag |

Data: "Contains BMRS data © Elexon Limited copyright and database right 2026"; "Supported by National Energy SO Open Data".
