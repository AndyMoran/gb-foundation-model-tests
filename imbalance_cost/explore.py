"""
Imbalance exposure, stage 1: frequency and tail (exploratory). Added after stage 1's results were seen, following a
review that the mean net exposure answers one question (the average net cost) and not how often a forecaster made
costly misses or how bad the worst were. Nothing here was planned before those results; every figure is descriptive.
Committed before it runs; its outputs are committed after. It changes nothing in score.py or its results.

For: a reviewer checking the definitions below and that they use the same data, days and exposure as score.py.

Reads exactly what score.py reads, through score.py's own loader and hash checks (imported unchanged), and scores the
same 953 days (score.py's per_day validity). Each half-hour's exposure is x = (A - F) * (SP - MIP) * 0.5, in £.
For each forecaster, all scored days unless stated:
  frequency      share of half-hours with x > 0 (the costly side) and with x < 0; share of days whose net exposure
                 is positive
  concentration  share of gross losses (the sum of x > 0) that comes from the forecaster's own worst 1% and worst 10%
                 of half-hours by x
  price stress   the top tenth of scored half-hours by |SP - MIP|, one set for every forecaster: the share of them on
                 the costly side, mean x in them (£ per half-hour), and the share of gross losses that falls in them
  tail days      the 95th and 99th percentiles of daily net exposure (£ per GWh), the mean of the worst 5% of days,
                 and the ten worst days with their dates
  two averages   day-weighted (each day's £/GWh, averaged: score.py's measure) and demand-weighted (total £ over
                 total GWh)
  winter share   the share of all gross losses that fell in December to February (scores PLAN.md §10's prediction,
                 which score.py did not measure)
Intervals: the tails study's 7-day moving-block bootstrap over days (2,000 draws), seed 20261125, the same draws for
every measure and forecaster; whole days are resampled, with their half-hours. Paired comparisons are the
forecaster's measure minus the regression's; labels as in score.py, unadjusted, not tests.

Modes:
    python imbalance_cost/explore.py --synthetic   invented data with known answers; writes explore_synthetic.json
    python imbalance_cost/explore.py               the real run; refused unless the synthetic check passed with this
                                                   script and the guarded files are committed and unchanged
Writes imbalance_cost/explore_results.json and explore_results.md.
"""
import argparse, importlib.util, json, math, os, platform, subprocess, sys
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
_spec = importlib.util.spec_from_file_location('imbalance_score', os.path.join(HERE, 'score.py'))
sc = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(sc)       # imported unchanged
st = sc.st

SEED = 20261125
SYNTH_JSON = os.path.join(HERE, 'explore_synthetic.json')
GUARDED = ['imbalance_cost/explore.py', 'imbalance_cost/explore_synthetic.json', 'imbalance_cost/score.py',
           'imbalance_cost/results_stage1.json'] + [g for g in sc.GUARDED if g != 'imbalance_cost/score.py']
FORECASTERS, REF, NAMES = sc.FORECASTERS, sc.REF, sc.NAMES


def git(*a):
    return subprocess.run(['git', '-C', ROOT, *a], capture_output=True, text=True, check=True).stdout.strip()


# ------------------------------------------------------------------ building blocks -------------------------------------
def halfhours(frame, cols, ok_days):
    """Scored half-hours only, in day order: day code, month, A, SP - MIP, and x per forecaster."""
    f = frame[frame['day'].isin(ok_days)].sort_values(['day', 'start_utc'], kind='mergesort').reset_index(drop=True)
    days = sorted(f['day'].unique()); code = pd.Categorical(f['day'], categories=days).codes
    A = f['outturn'].to_numpy(float); spread = (f['system_price'] - f['mip']).to_numpy(float)
    X = {c: (A - f[c].to_numpy(float)) * spread * 0.5 for c in cols}
    return dict(days=days, code=code, A=A, spread=spread, X=X,
                winter=np.array([pd.Timestamp(d).month in (12, 1, 2) for d in days]))


def top_share(x, frac):
    """Share of gross losses (sum of x > 0) from the worst `frac` of half-hours by x."""
    loss = x[x > 0].sum()
    if loss <= 0: return np.nan
    k = max(1, math.ceil(frac * len(x)))
    return float(np.partition(x, len(x) - k)[len(x) - k:].clip(min=0).sum() / loss)


def es(v, frac=0.05):
    """Mean of the worst `frac` of values (largest)."""
    k = max(1, math.ceil(frac * len(v)))
    return float(np.sort(v)[-k:].mean())


def q90(x):
    x = np.asarray(x, float); x = x[np.isfinite(x)]
    return [float(v) for v in np.quantile(x, [0.05, 0.95])] if len(x) else None


def analyse(frame, cols, ok_days, ref=REF):
    with np.errstate(invalid='ignore', divide='ignore'):      # a perfect forecast has no losses: its shares are NaN
        return _analyse(frame, cols, ok_days, ref)


def _analyse(frame, cols, ok_days, ref):
    H = halfhours(frame, cols, ok_days); n = len(H['days']); code = H['code']
    S = lambda w: np.bincount(code, weights=w, minlength=n)
    gwh = S(H['A'] * 0.5) / 1000
    stress = np.abs(H['spread']) >= np.quantile(np.abs(H['spread']), 0.9)
    I = st.boot_idx(n, np.random.default_rng(SEED))
    starts = np.r_[0, np.cumsum(np.bincount(code, minlength=n))]
    rows_of = lambda draw: np.concatenate([np.arange(starts[d], starts[d + 1]) for d in draw])
    nhh = S(np.ones(len(code)))
    out, draws = {}, {}
    hh_draws = [rows_of(I[b]) for b in range(len(I))]                                   # whole days, with repeats
    for c in cols:
        x = H['X'][c]; net = S(x); loss = S(np.clip(x, 0, None))
        daily = net / gwh
        cost_n, earn_n = S((x > 0).astype(float)), S((x < 0).astype(float))
        st_cost, st_n, st_x, st_loss = S(((x > 0) & stress).astype(float)), S(stress.astype(float)), S(np.where(stress, x, 0)), S(np.where(stress & (x > 0), x, 0))
        r = lambda num, den, idx=None: float(num.sum() / den.sum()) if idx is None else num[idx].sum(1) / den[idx].sum(1)
        res = dict(
            share_costly_halfhours=r(cost_n, nhh), share_earning_halfhours=r(earn_n, nhh),
            share_days_net_loss=float(np.mean(net > 0)),
            loss_share_worst_1pct=top_share(x, 0.01), loss_share_worst_10pct=top_share(x, 0.10),
            stress_share_costly=r(st_cost, st_n), stress_mean_x_gbp=r(st_x, st_n), stress_share_of_losses=r(st_loss, loss),
            daily_p95=float(np.quantile(daily, 0.95)), daily_p99=float(np.quantile(daily, 0.99)), daily_es5=es(daily),
            day_weighted=float(daily.mean()), demand_weighted=r(net, gwh),
            winter_share_of_losses=float(loss[H['winter']].sum() / loss.sum()),
            worst_days=[dict(day=H['days'][i], net_gbp_per_gwh=float(daily[i])) for i in np.argsort(daily)[::-1][:10]])
        d = dict(share_costly_halfhours=r(cost_n, nhh, I), share_earning_halfhours=r(earn_n, nhh, I),
                 share_days_net_loss=(net[I] > 0).mean(1),
                 loss_share_worst_1pct=np.array([top_share(x[h], 0.01) for h in hh_draws]),
                 loss_share_worst_10pct=np.array([top_share(x[h], 0.10) for h in hh_draws]),
                 stress_share_costly=r(st_cost, st_n, I), stress_mean_x_gbp=r(st_x, st_n, I),
                 stress_share_of_losses=r(st_loss, loss, I),
                 daily_p95=np.quantile(daily[I], 0.95, axis=1), daily_p99=np.quantile(daily[I], 0.99, axis=1),
                 daily_es5=np.array([es(v) for v in daily[I]]), day_weighted=daily[I].mean(1), demand_weighted=r(net, gwh, I),
                 winter_share_of_losses=np.where(H['winter'][I], loss[I], 0).sum(1) / loss[I].sum(1))
        out[c] = {k: (dict(value=v, ci90=q90(d[k])) if k in d else v) for k, v in res.items()}
        draws[c] = d
    for c in cols:
        if c == ref: continue
        out[c]['minus_regression'] = {}
        for k in draws[c]:
            iv = q90(draws[c][k] - draws[ref][k])
            out[c]['minus_regression'][k] = dict(value=out[c][k]['value'] - out[ref][k]['value'], ci90=iv, label=sc.label(iv))
    return dict(n_days=n, n_halfhours=int(len(code)), stress_threshold_gbp_per_mwh=float(np.quantile(np.abs(H['spread']), 0.9)),
                forecasters=out)


# ------------------------------------------------------------------ output ---------------------------------------------
def p(v): return '–' if v is None or not np.isfinite(v) else f'{100 * v:.1f}%'
def piv(v): return '–' if not v else f'{100 * v[0]:.1f} to {100 * v[1]:.1f}'
def g(v): return '–' if v is None or not np.isfinite(v) else f'{v:,.0f}'.replace('-', '−')
def giv(v): return '–' if not v else f'{v[0]:,.0f} to {v[1]:,.0f}'.replace('-', '−')


def markdown(res, meta):
    F = res['forecasters']
    L = ['# Imbalance exposure, stage 1: frequency and tail (exploratory; generated by imbalance_cost/explore.py)', '',
         'Added after stage 1\'s results were seen; descriptive only. Same 953 days and exposure as score.py. Labels come '
         'from unadjusted 90% intervals and are not tests.', '',
         f'{res["n_days"]} days, {res["n_halfhours"]:,} half-hours. Price-stress half-hours: the top tenth by |SP − MIP| '
         f'(at least £{res["stress_threshold_gbp_per_mwh"]:.2f}/MWh).', '']
    def table(title, keys, fmt, ivf):
        rows = [f'### {title}', '', '| Forecaster | ' + ' | '.join(k for k, _ in keys) + ' |', '|---' * (len(keys) + 1) + '|']
        for c, r in F.items():
            cells = []
            for _, k in keys:
                v = r[k]; s = f'{fmt(v["value"])} ({ivf(v["ci90"])})'
                d = r.get('minus_regression', {}).get(k)
                if d: s += f'; vs reg. {d["label"]}'
                cells.append(s)
            rows.append(f'| {NAMES[c]} | ' + ' | '.join(cells) + ' |')
        return rows + ['']
    L += table('Frequency', [('costly half-hours', 'share_costly_halfhours'), ('earning half-hours', 'share_earning_halfhours'),
                             ('days with a net loss', 'share_days_net_loss')], p, piv)
    L += table('Concentration of gross losses', [('from worst 1% of half-hours', 'loss_share_worst_1pct'),
                                                 ('from worst 10%', 'loss_share_worst_10pct')], p, piv)
    L += table('Price-stress half-hours (top tenth by |SP − MIP|)', [('on the costly side', 'stress_share_costly'),
                                                                   ('share of gross losses', 'stress_share_of_losses')], p, piv)
    L += table('Price-stress half-hours: mean exposure, £ per half-hour', [('mean x', 'stress_mean_x_gbp')], g, giv)
    L += table('Tail days, net £ per GWh', [('95th percentile', 'daily_p95'), ('99th percentile', 'daily_p99'),
                                            ('mean of worst 5% of days', 'daily_es5')], g, giv)
    L += table('Two averages, net £ per GWh', [('day-weighted (score.py)', 'day_weighted'), ('demand-weighted', 'demand_weighted')], g, giv)
    L += table('Winter share of gross losses (PLAN.md §10)', [('December to February', 'winter_share_of_losses')], p, piv)
    L += ['### Ten worst days, net £ per GWh', '']
    for c, r in F.items():
        L.append(f'- **{NAMES[c]}:** ' + '; '.join(f'{w["day"]} ({g(w["net_gbp_per_gwh"])})' for w in r['worst_days']))
    L += ['', f'Commit {meta["public_commit"]}; script SHA-256 {meta["script_sha256"]}; seed {SEED}; {st.B} draws in blocks of {st.BLOCK}.', '']
    return '\n'.join(L)


def real():
    if not os.path.exists(SYNTH_JSON): sys.exit('Refused: run --synthetic first and commit explore_synthetic.json.')
    if git('status', '--porcelain', '--', *GUARDED): sys.exit('Refused: these must be committed and unchanged: ' + ', '.join(GUARDED))
    sy = json.load(open(SYNTH_JSON))
    if not sy.get('passed') or sy.get('script_sha256') != st.sha(os.path.abspath(__file__)):
        sys.exit('Refused: the synthetic check has not passed with this script.')
    frame, prices, man, t1 = sc.load_real()
    P = sc.per_day(frame, FORECASTERS); ok_days = [d for d, k in zip(P['days'], P['ok']) if k]
    stage1 = json.load(open(os.path.join(HERE, 'results_stage1.json')))
    if len(ok_days) != stage1['sets']['all']['n_days']: sys.exit('Refused: scored days differ from score.py\'s.')
    res = analyse(frame, FORECASTERS, ok_days)
    worst = max(abs(res['forecasters'][c]['day_weighted']['value'] - stage1['sets']['all']['forecasters'][c]['net']['value'])
                for c in FORECASTERS)
    res['check_day_weighted_matches_score'] = dict(passed=bool(worst <= 0.01), max_abs_diff=worst)
    meta = dict(public_commit=git('rev-parse', 'HEAD'), script_sha256=st.sha(os.path.abspath(__file__)), seed=SEED,
                draws=st.B, block=st.BLOCK, versions=dict(python=platform.python_version(), numpy=np.__version__, pandas=pd.__version__))
    out = dict(note='exploratory, added after stage 1 results; descriptive only', meta=meta, **st.round_floats(res))
    json.dump(out, open(os.path.join(HERE, 'explore_results.json'), 'w'), indent=1)
    md = markdown(out, meta); open(os.path.join(HERE, 'explore_results.md'), 'w').write(md); print(md)
    if not res['check_day_weighted_matches_score']['passed']: print('CHECK FAILED: day-weighted mean differs from score.py'); sys.exit(1)


# ------------------------------------------------------------------ synthetic check ------------------------------------
def synthetic():
    grid = pd.read_csv(st.FORECASTS, usecols=['day', 'start_utc'])
    fr, spread = sc.synth_frame(grid)
    res = dict(script_sha256=st.sha(os.path.abspath(__file__)), checks={}); ok = True
    def rec(name, good, **info):
        nonlocal ok; ok &= bool(good); res['checks'][name] = dict(passed=bool(good), **info)
        print(('PASS ' if good else 'FAIL ') + name, flush=True)
    rec('top_share on a known array', abs(top_share(np.array([10.0, 5, 5, -3] + [0.0] * 96), 0.01) - 0.5) < 1e-12
        and abs(top_share(np.array([10.0, 5, 5, -3] + [0.0] * 96), 0.10) - 1.0) < 1e-12)
    rec('es on a known array', es(np.arange(100.0), 0.05) == 97.0)
    cols = ['aligned', 'independent', 'exact']
    days = sorted(fr['day'].unique())
    r = analyse(fr, cols, days, ref='independent')['forecasters']
    rec('aligned: every half-hour costly', r['aligned']['share_costly_halfhours']['value'] == 1.0
        and r['aligned']['share_days_net_loss']['value'] == 1.0 and r['aligned']['stress_share_costly']['value'] == 1.0)
    rec('independent: half the half-hours costly', abs(r['independent']['share_costly_halfhours']['value'] - 0.5) < 1e-12
        and abs(r['independent']['day_weighted']['value']) < 1e-9)
    rec('perfect forecast: no costly half-hour', r['exact']['share_costly_halfhours']['value'] == 0
        and r['exact']['share_earning_halfhours']['value'] == 0)
    A = fr['outturn'].to_numpy(); code = pd.Categorical(fr['day'], categories=days).codes; x = (A - fr['aligned'].to_numpy()) * spread * 0.5
    winter = np.array([pd.Timestamp(d).month in (12, 1, 2) for d in days])
    want_w = float(np.bincount(code, weights=x)[winter].sum() / x.sum())
    rec('winter share of losses', abs(r['aligned']['winter_share_of_losses']['value'] - want_w) < 1e-12, want=want_w)
    want_dw = float(np.bincount(code, weights=x).sum() / (np.bincount(code, weights=A * 0.5).sum() / 1000))
    rec('demand-weighted average', abs(r['aligned']['demand_weighted']['value'] - want_dw) < 1e-9)
    rec('paired labels', r['aligned']['minus_regression']['share_costly_halfhours']['label'] == sc.HIGHER)
    res['passed'] = bool(ok)
    json.dump(st.round_floats(res), open(SYNTH_JSON, 'w'), indent=1, default=str)
    print('synthetic: ' + ('PASS' if ok else 'FAIL')); return ok


if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('--synthetic', action='store_true')
    if ap.parse_args().synthetic: sys.exit(0 if synthetic() else 1)
    real()
