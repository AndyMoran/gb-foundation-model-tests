"""
Power check for the weather study (Brief 4, Section 7). Reads no weather forecast and computes no weather-forecast
error: it uses only rung 1's published no-weather forecasts (results/attempt2/forecasts.csv) and outturn.

Method, as rung 1's power check (code/power.py): for each forecaster, the "with weather" arm is simulated from its
own real no-weather errors. A share c of each half-hour's simulated error is the real error; the rest is the same
forecaster's error on another day at least 30 days away (a circular shift, so weekly dependence is kept). The result
is scaled so that the true effect holds over the window. Each replication then tests on a block-resampled set of
days (blocks of 7, as a real study would see), and tested with rung 1's bootstrap scheme and p-value method
(code/stats.py: moving blocks of 7 days; p = share of bootstrap ratios at or beyond the null), vectorised here and
with 1,000 draws, so that p-values resolve in steps of 0.001 near the small levels used.

The noise, c: the brief requires it to be estimated from the spread between rung 1's similar forecasters, never from
weather forecasts. Half-hourly error correlations between pairs of rung 1's forecasters give a lower bound: one model
with and without weather should agree at least as closely as two different models. The table is computed at that
bound and at 0.9.

Tests (Brief 4, Sections 1, 6, 7):
  Q1   ratio of mean daily error, with weather / without; H0 ratio >= 1. Effects: 2, 3, 5, 7, 10% cuts.
  Q4a  fractional error reduction, evening (16:00-20:00 UK) minus overnight (00:00-04:00); H0 <= 0.
       Effects: the evening's reduction exceeds overnight's by 2, 4, 6, 8, 10 points (overnight at 5%).
  Q4b  midday (12:00-16:00) reduction minus the other five blocks' together; H0 >= 0 (i.e. test midday smaller).
       Effects: midday's falls short by 2, 4, 6, 8, 10 points (the others at 5%).
Windows: the backtest, 960 days (16 March 2024 to 31 October 2026); one winter, 132 days (20 November to 31 March,
each of rung 1's two winters in turn); two winters, 264 days (both).
Levels: Q1 at its initial share of the study-wide 5%, 0.05/8 = 0.00625, and at 0.0125 (after its other window's test
rejects). Q4 at 0.00625 (the share it receives once its model's Q1 tests have rejected in both windows) and 0.0125.

Usage: python weather_study/power.py [reps]     (default 200)  ->  weather_study/power.json
"""
import json, os, sys
import numpy as np, pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, os.path.join(ROOT, 'code'))
import stats as S

FORECASTERS = ('chronos2', 'timestral', 'timesfm25', 'regression')
Q1_EFFECTS = (0.02, 0.03, 0.05, 0.07, 0.10)
Q4_EFFECTS = (0.02, 0.04, 0.06, 0.08, 0.10)
BASE_FR = 0.05
LEVELS = (0.05 / 8, 0.05 / 4)
BLOCK, B, SEED = 7, 1000, 20261108
BLOCKS = {'00-04': 0, '04-08': 1, '08-12': 2, '12-16': 3, '16-20': 4, '20-24': 5}


def load():
    f = pd.read_csv(os.path.join(ROOT, 'results', 'attempt2', 'forecasts.csv'), parse_dates=['start_utc'])
    f['block'] = f['start_utc'].dt.tz_convert('Europe/London').dt.hour // 4
    return f


def window_days(days, kind):
    d = pd.to_datetime(pd.Series(days))
    if kind == 'backtest':
        return [x for x in days if '2024-03-16' <= x <= '2026-10-31']
    w1 = [x for x in days if '2024-11-20' <= x <= '2025-03-31']; w2 = [x for x in days if '2025-11-20' <= x <= '2026-03-31']
    return {'one winter': [w1, w2], 'two winters': [w1 + w2]}[kind]


def arrays(f, name, days):
    g = f[f['day'].isin(days)]
    e = {d: (x['outturn'] - x[name]).to_numpy() for d, x in g.groupby('day')}
    b = {d: x['block'].to_numpy() for d, x in g.groupby('day')}
    keep = [d for d in days if d in e and np.isfinite(e[d]).all()]
    return [e[d] for d in keep], [b[d] for d in keep]


def boot_idx(n, rng):
    """B moving-block resamples of n days at once: the same scheme as code/stats.py's block_indices, vectorised."""
    nb = int(np.ceil(n / BLOCK)); starts = rng.integers(0, n - BLOCK + 1, size=(B, nb))
    return (starts[:, :, None] + np.arange(BLOCK)).reshape(B, -1)[:, :n]


def simulate(E, rng, c):
    n = len(E); shift = rng.integers(30, n - 30) if n > 90 else rng.integers(7, n - 7)
    perm = np.roll(np.arange(n), shift)
    return [c * E[i] + np.sqrt(1 - c * c) * np.resize(E[perm[i]], len(E[i])) for i in range(n)]


def block_sums(E, Bk):
    """Per day: sum |e| and count, in each of the six blocks."""
    s = np.zeros((len(E), 6)); k = np.zeros((len(E), 6))
    for i, (e, b) in enumerate(zip(E, Bk)):
        np.add.at(s[i], b, np.abs(e)); np.add.at(k[i], b, 1)
    return s, k


def p_q4(s0, k0, s1, k1, num, den, rng, sign):
    """One-sided bootstrap p for H0: sign * (FR_num - FR_den) <= 0, FR = 1 - error with / error without, by blocks."""
    n = len(s0); idx = boot_idx(n, rng)
    def fr(cols, ii):
        e1 = s1[ii][:, :, cols].sum((1, 2)) / k1[ii][:, :, cols].sum((1, 2))
        e0 = s0[ii][:, :, cols].sum((1, 2)) / k0[ii][:, :, cols].sum((1, 2))
        return 1 - e1 / e0
    d = sign * (fr(num, idx) - fr(den, idx))
    return float((d <= 0).mean())


def main(reps):
    f = load(); days = sorted(f['day'].unique())
    # the noise: half-hourly error correlations between rung 1's forecasters, on the backtest window
    bt = window_days(days, 'backtest'); g = f[f['day'].isin(bt)]
    err = {n: (g['outturn'] - g[n]).to_numpy() for n in FORECASTERS}
    pairs = {f'{a}~{b}': float(np.corrcoef(err[a], err[b])[0, 1]) for i, a in enumerate(FORECASTERS) for b in FORECASTERS[i + 1:]}
    c_low = round(min(v for k, v in pairs.items() if 'regression' not in k), 2)   # between the models
    corrs = sorted({c_low, 0.9})
    print('half-hourly error correlations (backtest):', {k: round(v, 3) for k, v in pairs.items()}, f'-> c = {corrs}', flush=True)
    rng = np.random.default_rng(SEED)
    out = dict(source='results/attempt2/forecasts.csv (rung 1, no weather)', correlations=pairs, c_values=corrs,
               reps=reps, bootstrap_draws=B, block=BLOCK, levels=LEVELS, cells={})
    for name in FORECASTERS:
        for wkind in ('backtest', 'one winter', 'two winters'):
            wins = [window_days(days, 'backtest')] if wkind == 'backtest' else window_days(days, wkind)
            data = [arrays(f, name, w) for w in wins]
            for c in corrs:
                for eff in Q1_EFFECTS:
                    hits = np.zeros(len(LEVELS))
                    for rep in range(reps):
                        E, Bk = data[rep % len(data)]; n = len(E)
                        raw = simulate(E, rng, c); m0 = np.array([np.abs(e).mean() for e in E])
                        k = (1 - eff) * m0.mean() / np.mean([np.abs(x).mean() for x in raw])
                        m1 = np.array([np.abs(k * x).mean() for x in raw])
                        idx = S.block_indices(n, rng, BLOCK); a, b = m1[idx], m0[idx]   # the sample a study might see
                        bi = boot_idx(n, rng)
                        p = float(((a[bi].mean(1) / b[bi].mean(1)) >= 1.0).mean())        # percentile method, H0 ratio >= 1
                        hits += np.array([p < a for a in LEVELS])
                    out['cells'][f'Q1|{name}|{wkind}|c{c}|{eff:.2f}'] = (hits / reps).round(3).tolist()
                    print(f'Q1 {name:10s} {wkind:11s} c={c} cut {eff:.0%}: power {hits[0]/reps:.2f} (at 0.00625) - {hits[1]/reps:.2f} (at 0.0125)', flush=True)
                if name == 'regression' or wkind == 'backtest': continue
                for test, num, den, sign in (('Q4a', [4], [0], 1), ('Q4b', [3], [0, 1, 2, 4, 5], -1)):
                    for eff in Q4_EFFECTS:
                        hits = np.zeros(len(LEVELS))
                        for rep in range(reps):
                            E, Bk = data[rep % len(data)]; n = len(E)
                            raw = simulate(E, rng, c)
                            s0, k0 = block_sums(E, Bk); sr, kr = block_sums(raw, Bk)
                            r = np.full(6, 1 - BASE_FR)                            # error ratio in each block
                            if test == 'Q4a': r[4] = 1 - (BASE_FR + eff)
                            else: r[3] = 1 - (BASE_FR - eff)
                            kb = r * s0.sum(0) / sr.sum(0)                          # true ratio per block over the window
                            s1 = sr * kb
                            idx = S.block_indices(n, rng, BLOCK)
                            p = p_q4(s0[idx], k0[idx], s1[idx], k0[idx], num, den, rng, sign)
                            hits += np.array([p < a for a in LEVELS])
                        out['cells'][f'{test}|{name}|{wkind}|c{c}|{eff:.2f}'] = (hits / reps).round(3).tolist()
                        print(f'{test} {name:10s} {wkind:11s} c={c} +{eff*100:.0f} pts: power {hits[0]/reps:.2f} - {hits[1]/reps:.2f}', flush=True)
    json.dump(out, open(os.path.join(ROOT, 'weather_study', 'power.json'), 'w'), indent=1)
    print('written to weather_study/power.json')


if __name__ == '__main__':
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 200)
