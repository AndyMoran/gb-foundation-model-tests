"""Pooled winter: can two winters together settle the question one winter cannot?

Exploratory addendum to power_check.py, specified and committed 15 November 2026 before running.
It feeds the benchmark's checkpoint calendar: whether a winter confirmatory claim is possible once two winters
of live days have accumulated.

Window: the backtest's two Decembers-to-March (2024-25 and 2025-26), pooled into one sample: 2 x 120 days (240)
and 2 x 150 days, November to March (300). There is only one such pooled sample in the backtest, so every
simulation draws from it.
c: measured on the pooled days, as in power_check.py.
Edges: 5%, 7.5%, 10%, 12.5%; plus the pooled sample's measured edge and the low end of its 90% interval
(E5: Chronos-2 with calendar and weather, `chronos2_A`, against the weather regression), from summer_edge.py's
method. 2,000 simulations per cell. Same test as power_check.py: ratio below 1, one-sided, alpha 0.025.

Reading, fixed in advance: if power at a true 10% edge with the measured c is >= 80% for the 240-day pool, the
benchmark's rules may allow a pooled-winter confirmatory claim after two live winters; otherwise winter stays
descriptive.
"""
import json, os, sys
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import power_check as PC
P = PC.P
SEED, REPS = 20261117, 2000


def main():
    for p, h in PC.SHA.items():
        if PC.sha(p) != h: sys.exit(f'{p} differs from the hash in the specification')
    f = pd.read_csv(PC.FC); cal = pd.read_csv(PC.CAL)
    assert (f['start_utc'].to_numpy() == cal['start_utc'].to_numpy()).all()
    f['chronos2_A'] = cal['chronos2_A'].to_numpy()
    W = PC.windows(list(dict.fromkeys(f['day'])))
    pools = {'pooled winters, 2 x 120 days (Dec-Mar)': sum(W['winter 120 days (Dec-Mar)'], []),
             'pooled winters, 2 x 150 days (Nov-Mar)': sum(W['winter 150 days (Nov-Mar)'], [])}
    rng = np.random.default_rng(SEED)
    out = dict(note='specified and committed 15 November 2026 before running', seed=SEED, reps=REPS, pools={})
    for name, ds in pools.items():
        g = f[f['day'].isin(ds)]
        c = float(np.corrcoef(g['outturn'] - g['chronos2_A'], g['outturn'] - g['regression_weather'])[0, 1])
        daily = g.assign(a=(g['outturn'] - g['chronos2_A']).abs(), b=(g['outturn'] - g['regression_weather']).abs()) \
                 .groupby('day')[['a', 'b']].mean().loc[ds]
        a, b = daily['a'].to_numpy(), daily['b'].to_numpy(); bi = P.boot_idx(len(ds), rng)
        bs = a[bi].mean(1) / b[bi].mean(1); ratio = a.mean() / b.mean(); hi = float(np.quantile(bs, .95))
        E = [[(f[f['day'] == d]['outturn'] - f[f['day'] == d]['regression_weather']).to_numpy() for d in ds]]
        cells = {}
        for label, edge in [(f'{e:.1%}', e) for e in PC.EDGES] + [('measured edge', 1 - ratio), ('low end of interval', 1 - hi)]:
            cells[label] = dict(edge=round(edge, 4), **PC.cell(E, c, edge, REPS, rng)) if edge > 0 else dict(edge=round(edge, 4))
        out['pools'][name] = dict(days=len(ds), c=round(c, 4), ratio=round(ratio, 4),
                                  interval_90=[round(float(np.quantile(bs, .05)), 4), round(hi, 4)], power=cells)
    p240 = out['pools']['pooled winters, 2 x 120 days (Dec-Mar)']['power']['10.0%']['below_1']
    out['reading'] = ('pooled-winter confirmatory claim possible' if p240 >= 0.8 else 'winter stays descriptive')
    json.dump(out, open(os.path.join(HERE, 'pooled_winter.json'), 'w'), indent=1)
    L = ['# Pooled winter (exploratory addendum to the power check)', '']
    for name, r in out['pools'].items():
        L += [f"## {name}: {r['days']} days, c = {r['c']:.2f}, measured ratio {r['ratio']:.3f} "
              f"({r['interval_90'][0]:.3f}-{r['interval_90'][1]:.3f})", '',
              '| True edge | Credibly better | Shows 10% bar |', '|---|---|---|']
        for k, v in r['power'].items():
            L.append(f"| {k} ({v['edge']:.1%}) | {v.get('below_1', float('nan')):.1%} | {v.get('below_bar', float('nan')):.1%} |")
        L.append('')
    L.append(f"Reading, fixed in advance: **{out['reading']}** (240-day pool, true 10% edge, measured c: {p240:.1%}).")
    open(os.path.join(HERE, 'pooled_winter.md'), 'w').write('\n'.join(L) + '\n'); print('\n'.join(L))


if __name__ == '__main__':
    main()
