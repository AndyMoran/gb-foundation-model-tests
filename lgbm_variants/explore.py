"""
LightGBM variants: exploratory additions, written after the scored results were seen (REVISIONS.md item 21).
Committed before it runs; its outputs are committed after. Nothing here changes a scored result, a hypothesis reading
or the headline.

For: a reader of RESULTS.md checking the two additions a review asked for.

1. H3, the direct comparison. The fixed rule (REVISIONS.md item 15) read H3 from point estimates and from whether
   intervals overlap. Overlap alone does not show whether two ratios differ. So, for each variant, the difference
   between its winter ratio to the regression and S1's, with a 90% interval from the same bootstrap as score.py
   (7-day moving blocks, 2,000 draws), the same draws used for both ratios so the comparison is paired. The seed is
   score.py's, 20261119, on a fresh generator. The same for T1, and for V1 against S1 over all days.
2. V2's errors. Each day's mean absolute error over its half-hours, in MW: its median, 90th and 99th percentiles and
   maximum; the number of days above 5,000 and 20,000 MW; V2c's and the regression's medians beside it; the five
   worst days, with V2's lowest and highest half-hourly forecast on each. The forecasts are the raw model output
   written by lightgbm_variants.py, with no post-processing.

Reads, after their hash checks: the same files as score.py (through its load_real). Writes lgbm_variants/explore.json
and explore.md.
"""
import json, os, sys
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
import importlib.util
# loaded under its own name: both scoring scripts are called score.py, and `import score` here would make
# lgbm_variants/score.py find itself, not checkpoint 0's, when it imports `score` in turn (REVISIONS.md item 22)
_spec = importlib.util.spec_from_file_location('lgbm_variants_score', os.path.join(HERE, 'score.py'))
SC = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(SC)

S0 = SC.S0


def paired(dm, a, b, ref, bi):
    """Ratio of a to ref minus ratio of b to ref, with a 90% interval, on the same bootstrap draws."""
    A, Bv, R = (dm[c].to_numpy() for c in (a, b, ref))
    d = A[bi].mean(1) / R[bi].mean(1) - Bv[bi].mean(1) / R[bi].mean(1)
    lo, hi = np.quantile(d, [0.05, 0.95])
    return dict(difference=round(float(A.mean() / R.mean() - Bv.mean() / R.mean()), 4),
                ci90=[round(float(lo), 4), round(float(hi), 4)], n_days=int(len(dm)))


def main():
    f, t1, cols_v, fj = SC.load_real()
    cols = [SC.REF, SC.CHRONOS, SC.S1] + cols_v
    dm, _ = S0.daily(f, cols)
    rng = np.random.default_rng(SC.SEED)
    month = pd.to_datetime(dm.index).month
    parts = dict(all_days=dm, winter=dm[np.isin(month, list(SC.WINTER))], T1=dm[dm.index.isin(t1)])
    out = dict(note='exploratory, after the scored results; REVISIONS.md item 21', h3_differences={})
    for part, d in parts.items():
        bi = S0.boot_idx(len(d), rng)
        out['h3_differences'][part] = {v: paired(d, SC.COL[v], SC.S1, SC.REF, bi) for v in SC.CANDIDATES + ['V2c']}
    e = dm[SC.COL['V2']]
    worst = e.nlargest(5)
    fv = f.set_index('day')
    out['v2'] = dict(
        measure='each day\'s mean absolute error over its half-hours, MW; raw model output, no post-processing',
        median=round(float(e.median())), p90=round(float(e.quantile(0.9))), p99=round(float(e.quantile(0.99))),
        max=round(float(e.max())), days_over_5000=int((e > 5000).sum()), days_over_20000=int((e > 20000).sum()),
        v2c_median=round(float(dm[SC.COL['V2c']].median())), regression_median=round(float(dm[SC.REF].median())),
        worst_days=[dict(day=d, daily_mae_mw=round(float(v)),
                         lowest_forecast_mw=round(float(fv.loc[d, SC.COL['V2']].min())),
                         highest_forecast_mw=round(float(fv.loc[d, SC.COL['V2']].max())),
                         outturn_range_mw=[round(float(fv.loc[d, 'outturn'].min())), round(float(fv.loc[d, 'outturn'].max()))])
                    for d, v in worst.items()])
    out['meta'] = dict(script_sha256=S0.sha(os.path.abspath(__file__)), forecasts_sha256=fj['forecasts_sha256'],
                       seed=SC.SEED, draws=S0.B, block=S0.BLOCK)
    json.dump(out, open(os.path.join(HERE, 'explore.json'), 'w'), indent=1)
    L = ['# LightGBM variants: exploratory additions (after the scored results)', '',
         '## Each variant\'s ratio to the regression minus S1\'s (negative: better than S1), 90% intervals on paired draws', '',
         '| Variant | All days | Winter (Nov–Mar) | T1 |', '|---|---|---|---|']
    for v in SC.CANDIDATES + ['V2c']:
        c = [out['h3_differences'][p][v] for p in ('all_days', 'winter', 'T1')]
        L.append(f'| {v} | ' + ' | '.join(f"{x['difference']:+.3f} ({x['ci90'][0]:+.3f} to {x['ci90'][1]:+.3f})" for x in c) + ' |')
    V = out['v2']
    L += ['', '## V2\'s daily errors (mean absolute error over each day\'s half-hours, MW; raw model output)', '',
          f"Median {V['median']:,}; 90th percentile {V['p90']:,}; 99th percentile {V['p99']:,}; maximum {V['max']:,}. "
          f"Days above 5,000 MW: {V['days_over_5000']}; above 20,000 MW: {V['days_over_20000']}. "
          f"Medians beside it: V2c {V['v2c_median']:,}, regression {V['regression_median']:,}.", '',
          '| Day | V2 daily error (MW) | V2 lowest forecast (MW) | V2 highest forecast (MW) | Outturn range (MW) |', '|---|---|---|---|---|']
    for w in V['worst_days']:
        L.append(f"| {w['day']} | {w['daily_mae_mw']:,} | {w['lowest_forecast_mw']:,} | {w['highest_forecast_mw']:,} | "
                 f"{w['outturn_range_mw'][0]:,}–{w['outturn_range_mw'][1]:,} |")
    open(os.path.join(HERE, 'explore.md'), 'w').write('\n'.join(L) + '\n')
    print('\n'.join(L))


if __name__ == '__main__':
    main()
