"""
Checkpoint 0: TimesFM 2.5's rows recomputed with its corrected forecasts (weather study correction 1). Committed before
it runs; outputs committed after.

checkpoint0/results.md (frozen plan, scored 15 November 2026) used TimesFM 2.5's batched weather-study forecasts. Weather
study correction 1 (16 November 2026) remade them one day per call. This script recomputes, with score.py's own
functions and settings, only the rows that involve TimesFM 2.5: table 1 (mean daily error and ratio to LightGBM,
defaults) and table 4's TimesFM 2.5 column. Nothing else in results.md changes. Bootstrap draws come from the same seed
as score.py but are drawn afresh here, so intervals can differ from a joint run in the last digit.
Writes checkpoint0/results_correction1.json and .md.
"""
import hashlib, json, os, sys
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import score as S

CORR = os.path.join(ROOT, 'weather_study', 'correction1', 'timesfm25_single_day_forecasts.csv')
CORR_SHA = '479ec318925cc59cd1e4f56a29ef9bc10d297fe3f8fa012482e1ce130dccd821'


def main():
    if S.sha(CORR) != CORR_SHA: sys.exit('corrected forecasts differ from the hash in score_correction.py')
    f = S.load()
    c = pd.read_csv(CORR)
    n0 = len(f); f = f.merge(c[['start_utc', 'timesfm25_weather_single_day']], on='start_utc', how='left', validate='one_to_one')
    assert len(f) == n0 and f['timesfm25_weather_single_day'].notna().all()
    f['timesfm25_weather'] = f['timesfm25_weather_single_day']
    dm, dropped = S.daily(f, ['timesfm25_weather', 'lightgbm_default'])
    assert not dropped
    rng = np.random.default_rng(S.SEED)
    t1 = S.ratio(dm['timesfm25_weather'].to_numpy(), dm['lightgbm_default'].to_numpy(), S.boot_idx(len(dm), rng))
    seas = pd.to_datetime(dm.index).month.map(S.SEASON); t4 = {}
    for s in ('DJF', 'MAM', 'JJA', 'SON'):
        d = dm[np.asarray(seas == s)]
        t4[s] = S.ratio(d['timesfm25_weather'].to_numpy(), d['lightgbm_default'].to_numpy(), S.boot_idx(len(d), rng))
    out = dict(note='TimesFM 2.5 rows with weather study correction 1', table1=t1, table4=t4,
               mean_daily_mae_mw=round(float(dm['timesfm25_weather'].mean()), 1))
    json.dump(out, open(os.path.join(HERE, 'results_correction1.json'), 'w'), indent=1)
    f2 = lambda r: f"{r['ratio']:.3f} ({r['ci90'][0]:.3f}–{r['ci90'][1]:.3f})"
    L = ['# Checkpoint 0: TimesFM 2.5 rows, corrected (weather study correction 1)', '',
         '| Table | Row | As scored (batched) | Corrected (one day per call) |', '|---|---|---|---|',
         f"| 1 | Mean daily error (MW) | 1,474 | {out['mean_daily_mae_mw']:,.0f} |",
         f"| 1 | Ratio to LightGBM (defaults) | 1.299 (1.242–1.354) | {f2(t1)} |"]
    old = {'DJF': '1.127 (1.000–1.274)', 'MAM': '1.318 (1.240–1.409)', 'JJA': '1.274 (1.195–1.347)', 'SON': '1.464 (1.375–1.577)'}
    for s in t4: L.append(f"| 4 | {s}: TimesFM 2.5 / LightGBM | {old[s]} | {f2(t4[s])} |")
    open(os.path.join(HERE, 'results_correction1.md'), 'w').write('\n'.join(L) + '\n'); print('\n'.join(L))


if __name__ == '__main__':
    main()
