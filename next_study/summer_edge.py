"""Summer edge: the size of effect the summer power figures should assume.

Exploratory addendum to power_check.py, specified and committed 15 November 2026 before running.

The power check assumed a true edge of 5-12.5% in every window. Weather helps the regression least in
summer, so Chronos-2's edge may be smaller there. This script measures, from the E5 backtest
(Chronos-2 with calendar and weather, `chronos2_A`, against the weather regression, which also has the
calendar), the edge and the error correlation c in each window power_check.py uses, then re-runs the
summer power cell at the measured summer edge and at the low end of its 90% interval.

Measured per window, pooling the window's years:
  ratio = mean daily MAE of chronos2_A / mean daily MAE of regression_weather, with a 90% moving-block
  bootstrap interval (7-day blocks, 2,000 draws); edge = 1 - ratio; c as in power_check.py.
Power, summer 180-day window, 2,000 simulations each, for: the measured summer edge with the measured
summer c; the low end of the interval with the measured summer c. Same test as power_check.py.

Reading, fixed in advance: if power at the measured summer edge is >= 80%, summer 2027 is powered for the
edge the backtest shows; if only at a 10% edge, the brief says the summer window is powered for 10% but
the backtest suggests a smaller summer edge, for which it is underpowered.
These numbers come from the backtest, which the models may have seen in training; they guide the design
and are not results.
"""
import json, os, sys
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import power_check as PC
P = PC.P
SEED, REPS = 20261116, 2000


def main():
    for p, h in PC.SHA.items():
        if PC.sha(p) != h: sys.exit(f'{p} differs from the hash in the specification')
    f = pd.read_csv(PC.FC); cal = pd.read_csv(PC.CAL)
    assert (f['start_utc'].to_numpy() == cal['start_utc'].to_numpy()).all()
    f['chronos2_A'] = cal['chronos2_A'].to_numpy()
    f['e_c'] = (f['outturn'] - f['chronos2_A']).abs(); f['e_r'] = (f['outturn'] - f['regression_weather']).abs()
    daily = f.groupby('day')[['e_c', 'e_r']].mean()
    W = PC.windows(list(dict.fromkeys(f['day'])))
    rng = np.random.default_rng(SEED); out = dict(note='specified and committed 15 November 2026 before running',
                                                  seed=SEED, reps=REPS, windows={})
    for w, sets in W.items():
        ds = [d for s in sets for d in s]; g = f[f['day'].isin(ds)]; dd = daily.loc[ds]
        a, b = dd['e_c'].to_numpy(), dd['e_r'].to_numpy(); bi = P.boot_idx(len(ds), rng)
        bs = a[bi].mean(1) / b[bi].mean(1)
        c = float(np.corrcoef(g['outturn'] - g['chronos2_A'], g['outturn'] - g['regression_weather'])[0, 1])
        out['windows'][w] = dict(days=len(ds), ratio=round(a.mean() / b.mean(), 4),
                                 interval_90=[round(float(np.quantile(bs, .05)), 4), round(float(np.quantile(bs, .95)), 4)],
                                 c=round(c, 4), years=[len(s) for s in sets])
    s = out['windows']['summer 180 days (Apr-Sep)']; sets = W['summer 180 days (Apr-Sep)']
    E = [[(f[f['day'] == d]['outturn'] - f[f['day'] == d]['regression_weather']).to_numpy() for d in ds] for ds in sets]
    prng = np.random.default_rng(SEED + 1); out['summer_power'] = {}
    for label, edge in (('measured edge', 1 - s['ratio']), ('low end of interval', 1 - s['interval_90'][1])):
        out['summer_power'][label] = dict(edge=round(edge, 4), c=s['c'],
                                          **PC.cell(E, s['c'], edge, REPS, prng)) if edge > 0 else dict(edge=round(edge, 4), note='no edge')
    json.dump(out, open(os.path.join(HERE, 'summer_edge.json'), 'w'), indent=1)
    L = ['# Summer edge (exploratory addendum to the power check)', '',
         '| Window | Days | Ratio (90% interval) | Edge | c |', '|---|---|---|---|---|']
    for w, r in out['windows'].items():
        L.append(f"| {w} | {r['days']} | {r['ratio']:.3f} ({r['interval_90'][0]:.3f}-{r['interval_90'][1]:.3f}) | {1 - r['ratio']:.1%} | {r['c']:.2f} |")
    L += ['', '| Summer 180-day power at | Edge | Credibly better | Shows 10% bar |', '|---|---|---|---|']
    for k, r in out['summer_power'].items():
        L.append(f"| {k} | {r['edge']:.1%} | {r.get('below_1', float('nan')):.1%} | {r.get('below_bar', float('nan')):.1%} |")
    open(os.path.join(HERE, 'summer_edge.md'), 'w').write('\n'.join(L) + '\n'); print('\n'.join(L))


if __name__ == '__main__':
    main()
