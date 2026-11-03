"""
Power check before freezing (plan Section 8). Reads no model forecast: no foundation model is run.

It uses the weekly-lag regression's real forecast errors over the full window, and simulates a model whose errors
are partly shared with the regression's (correlation c) and scaled so that the true error ratio is r. The shared part
is the regression's own error; the rest is another day's regression error, drawn in weekly blocks, so the simulated
errors keep the real errors' shape and day-to-day dependence. The scale is set on the whole window; each replication
then tests on a block-resampled set of days (blocks of 7), so the observed ratio varies around r as a real study's
would. For each r and c it reports how often each primary
test succeeds, at the unadjusted 5% level and at 5%/6 (the strictest Holm step), as a range.

Disclosure: this computes the regression's real errors before freezing; the plan records that.

Usage: python power.py [reps]     (default 200 replications per cell)  ->  results/power.json
"""
import os, sys, json
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import common as C, inputs as I, baselines as B, stats as S

RATIOS = (1.00, 0.95, 0.90, 0.85)
CORRS = (0.5, 0.7, 0.9)
SEED = 20261105


def main(reps):
    series, _ = I.load_indo(os.path.join(C.DATA, 'indo.csv'))
    hol = {pd.Timestamp(d) for d in json.load(open(os.path.join(C.DATA, 'bank_holidays_ew.json')))}
    reg = B.Regression(series, hol)
    E, days = [], []
    for D in C.days():
        try:
            y, _ = I.targets(series, D); I.context(series, D)
        except ValueError:
            continue
        f = reg.forecast(D)
        if not np.isfinite(f).all(): continue
        E.append(y - f); days.append(D)
    n = len(E); mae_r = np.array([np.abs(e).mean() for e in E])
    print(f'{n} days; regression mean daily MAE {mae_r.mean():.0f} MW', flush=True)
    rng = np.random.default_rng(SEED); out = {'n_days': n, 'regression_mae_mw': float(mae_r.mean()), 'cells': {}}
    for c in CORRS:
        for r in RATIOS:
            hits = {k: 0 for k in ('imp_5', 'imp_holm', 'mean_5', 'mean_holm')}
            for rep in range(reps):
                perm = np.roll(np.arange(n), rng.integers(30, n - 30))     # another day's error, at least 30 days away
                raw = [c * E[i] + np.sqrt(1 - c * c) * np.resize(E[perm[i]], len(E[i])) for i in range(n)]
                k = r * mae_r.mean() / np.mean([np.abs(x).mean() for x in raw])
                mae_m = np.array([np.abs(k * x).mean() for x in raw])  # true ratio r over the whole window
                idx = S.block_indices(n, rng, C.BOOT_BLOCK)              # the sample a study might see
                cmp_ = S.compare(mae_m[idx], mae_r[idx], 500, C.BOOT_BLOCK, SEED + rep, thetas=(1.0, 1 - C.M_THRESHOLD))
                p1, p9 = cmp_['p_one_sided']['1.00'], cmp_['p_one_sided'][f'{1 - C.M_THRESHOLD:.2f}']
                hits['imp_5'] += p1 < 0.05; hits['imp_holm'] += p1 < 0.05 / 6
                hits['mean_5'] += p9 < 0.05; hits['mean_holm'] += p9 < 0.05 / 6
            cell = {k: v / reps for k, v in hits.items()}
            out['cells'][f'c{c}_r{r:.2f}'] = cell
            print(f'c={c} r={r:.2f}: improvement {cell["imp_holm"]:.2f}-{cell["imp_5"]:.2f}; '
                  f'meaningful (ratio<0.90) {cell["mean_holm"]:.2f}-{cell["mean_5"]:.2f}', flush=True)
    os.makedirs(os.path.join(C.ROOT, 'results'), exist_ok=True)
    json.dump(out, open(os.path.join(C.ROOT, 'results', 'power.json'), 'w'), indent=1)


if __name__ == '__main__':
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 200)
