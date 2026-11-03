"""
The official run (plan Sections 3-10).

Modes
  pipeline-test OUTDIR [--synthetic]
        The whole pipeline with the stand-in forecaster in every model slot. No foundation model is loaded, so no
        model forecasts GB demand. With --synthetic, synthetic data replace the downloaded files.
  real  The official run. Refuses without plan/PLAN_LOCK.json, and once an attempt has passed the gate. Each attempt
        is saved to results/attemptN/; the first attempt that passes every gate check is the run.

Outputs: forecasts.csv (every forecaster, every target half-hour), daily_mae.csv, exclusions.csv, results.json.
"""
import os, sys, json, glob, datetime as dt, platform
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import common as C, inputs as I, baselines as B, stats as S, models as M

SEED_BOOT, SEED_L1 = 20261103, 20261104
GATE_SAMPLE_DAYS = ('2024-03-31', '2025-01-15', '2026-10-25')    # a spring change, a winter day, an autumn change


def load_data(synthetic=False):
    if synthetic:
        import synth
        s = synth.demand(); pubs = synth.neso_publications(s); hol = synth.holidays()
        perf = None; nd = None
        return s, pubs, hol, perf, nd
    s, _ = I.load_indo(os.path.join(C.DATA, 'indo.csv'))
    pubs = I.load_neso(os.path.join(C.DATA, 'neso_dayahead_publications.csv'))
    hol = {pd.Timestamp(d) for d in json.load(open(os.path.join(C.DATA, 'bank_holidays_ew.json')))}
    perf = pd.read_csv(os.path.join(C.DATA, 'neso_forecast_performance.csv'))
    nd_path = os.path.join(C.DATA, 'neso_historic_nd.csv')
    nd = pd.read_csv(nd_path) if os.path.exists(nd_path) else None
    return s, pubs, hol, perf, nd


def build_days(series, pubs, reg, days):
    """Per target day: targets, context, regression, seasonal naive, NESO (or the reason a day is excluded)."""
    rec, excl = {}, []
    for D in days:
        r = dict(day=D)
        try:
            r['y'], r['idx'] = I.targets(series, D)
            r['ctx'], cidx = I.context(series, D)
            assert cidx[-1] + C.HALF_HOUR <= C.input_end(D)
        except ValueError as e:
            excl.append(dict(day=f'{D:%Y-%m-%d}', scope='all', reason=str(e))); continue
        r['regression'] = reg.forecast(D); r['naive'] = reg.seasonal_naive(D)
        if not np.isfinite(r['regression']).all():
            excl.append(dict(day=f'{D:%Y-%m-%d}', scope='all', reason='regression not estimable')); continue
        try:
            r['neso'], r['neso_pub'] = I.neso_forecast(pubs, D)
        except ValueError as e:
            r['neso'] = None; excl.append(dict(day=f'{D:%Y-%m-%d}', scope='neso', reason=str(e)))
        rec[D] = r
    return rec, excl


def model_forecasts(model, rec, contexts=None):
    """Median forecasts for each day's target periods, batching days that share a horizon."""
    out, groups = {}, {}
    for D in rec:
        groups.setdefault(C.horizon(D), []).append(D)
    for (h, first), ds in groups.items():
        X = [contexts[D] if contexts is not None else rec[D]['ctx'] for D in ds]
        for i in range(0, len(ds), 64):
            F = model.forecast(X[i:i + 64], h)
            for D, f in zip(ds[i:i + 64], F):
                out[D] = f[first:first + len(rec[D]['y'])]
    return out


def daily(rec, fc):
    return pd.Series({D: S.daily_mae(rec[D]['y'], fc[D]) for D in rec if D in fc})


def l1(models, series, hol, rec):
    """Perturbation test (plan Section 7): the same noise draws for every forecaster, inputs only."""
    base = {k: daily(rec, models[k + '_fc']).mean() for k in models['names']}
    base['regression'] = daily(rec, {D: rec[D]['regression'] for D in rec}).mean()
    pert = {k: [] for k in base}
    for k in range(1, C.L1_DRAWS + 1):
        rng = np.random.default_rng(SEED_L1 + k)
        noisy = series + rng.normal(0, C.L1_SD_MW, len(series))
        reg = B.Regression(noisy, hol)
        ctx = {D: I.context(noisy, D)[0] for D in rec}
        pert['regression'].append(daily(rec, {D: reg.forecast(D) for D in rec}).mean())
        for name in models['names']:
            pert[name].append(daily(rec, model_forecasts(models[name], rec, ctx)).mean())
    res = {k: dict(unperturbed=float(base[k]), perturbed_mean=float(np.mean(pert[k])),
                   ratio=float(np.mean(pert[k]) / base[k]), draws=[float(v) for v in pert[k]]) for k in base}
    for name in models['names']:
        ex = res[name]['ratio'] - res['regression']['ratio']
        res[name].update(excess=float(ex), flag=bool(ex > C.L1_FLAG))
    return res


def gates(mode, rec, models, series, hol, pubs, perf, lock):
    g = {}
    if mode == 'real':
        g['1_data_hashes'] = all(C.sha(os.path.join(C.DATA, f)) == h for f, h in lock['data_sha256'].items())
    g['2_no_lookahead'] = all((rec[D]['neso'] is None) or (pd.to_datetime(rec[D]['neso_pub'], utc=True) <= C.issue_time(D)).all()
                              for D in rec)                       # inputs are asserted where they are built
    if perf is not None:
        p = perf.copy(); p['Date'] = pd.to_datetime(p['Date']).dt.normalize()
        p = p[(p.Settlement_Period >= 17) & (p.Settlement_Period <= 48)]
        ours = []
        for D in rec:
            if rec[D]['neso'] is None: continue
            for k, (t, v) in enumerate(zip(rec[D]['idx'], rec[D]['neso'])):
                ours.append((D, k + 1, v))
        o = pd.DataFrame(ours, columns=['Date', 'Settlement_Period', 'ours'])
        j = o.merge(p[['Date', 'Settlement_Period', 'Demand_Forecast']], on=['Date', 'Settlement_Period'])
        share = float((np.abs(j.ours - j.Demand_Forecast) < 0.5).mean()) if len(j) else 0.0
        g['3_neso_reconstruction'] = share >= 0.95
        g['3_neso_match_share'] = share
    for name in models['names']:
        fc = models[name + '_fc']
        g[f'4_{name}_finite_and_length'] = all(np.isfinite(fc[D]).all() and len(fc[D]) == len(rec[D]['y']) for D in rec)
        sample = [D for D in rec][:3]
        again = model_forecasts(models[name], {D: rec[D] for D in sample})
        g[f'4_{name}_repeatable'] = all(np.array_equal(again[D], fc[D]) for D in sample)
        D = sample[0]; c = rec[D]['ctx'].copy(); c[-1] += 1000
        moved = model_forecasts(models[name], {D: rec[D]}, {D: c})[D]
        g[f'5_{name}_responsive'] = bool(np.abs(moved - fc[D]).max() > 1e-6)
    ok = True
    for d in GATE_SAMPLE_DAYS:
        D = pd.Timestamp(d)
        if D not in rec: continue
        ok &= bool(np.abs(B.regression_independent(series, D, hol) - rec[D]['regression']).max() <= 0.1)
    g['6_regression_independent'] = ok
    if mode == 'real':
        from huggingface_hub import hf_hub_download
        for name, (repo, rev) in M.REVISIONS.items():
            g[f'7_{name}_weights'] = C.sha(hf_hub_download(repo, 'model.safetensors', revision=rev)) == lock['weights_sha256'][name]
    return g


def evaluate(rec, models):
    dm = pd.DataFrame({'regression': daily(rec, {D: rec[D]['regression'] for D in rec}),
                       'naive': daily(rec, {D: rec[D]['naive'] for D in rec}),
                       **{n: daily(rec, models[n + '_fc']) for n in models['names']}})
    nd = {D: rec[D]['neso'] for D in rec if rec[D]['neso'] is not None}
    dm['neso'] = daily({D: rec[D] for D in nd}, nd)
    full = (dm.index >= pd.Timestamp(C.FULL_START)) & (dm.index <= pd.Timestamp(C.FULL_END))
    res = {'primary': {}, 'secondary': {}, 'exploratory': {}}
    pv = {}
    for n in models['names']:
        c = S.compare(dm.loc[full, n], dm.loc[full, 'regression'], C.BOOT_B, C.BOOT_BLOCK, SEED_BOOT,
                      thetas=(1.0, 1 - C.M_THRESHOLD))
        res['primary'][n] = c
        pv[f'{n}_improvement'] = c['p_one_sided']['1.00']; pv[f'{n}_meaningful'] = c['p_one_sided'][f'{1 - C.M_THRESHOLD:.2f}']
        both = full & dm['neso'].notna()
        res['secondary'][f'{n}_vs_neso_full'] = S.compare(dm.loc[both, n], dm.loc[both, 'neso'], C.BOOT_B, C.BOOT_BLOCK, SEED_BOOT)
        post = (dm.index >= pd.Timestamp(C.POST_RELEASE.get(n, C.FULL_START))) & full
        res['exploratory'][f'{n}_vs_regression_post_release'] = S.compare(dm.loc[post, n], dm.loc[post, 'regression'], C.BOOT_B, C.BOOT_BLOCK, SEED_BOOT)
        pn = post & dm['neso'].notna()
        if pn.sum() > 1:
            res['secondary'][f'{n}_vs_neso_post_release'] = S.compare(dm.loc[pn, n], dm.loc[pn, 'neso'], C.BOOT_B, C.BOOT_BLOCK, SEED_BOOT)
        res['exploratory'][f'{n}_vs_naive'] = S.compare(dm.loc[full, n], dm.loc[full, 'naive'], C.BOOT_B, C.BOOT_BLOCK, SEED_BOOT)
    res['exploratory']['regression_vs_naive'] = S.compare(dm.loc[full, 'regression'], dm.loc[full, 'naive'], C.BOOT_B, C.BOOT_BLOCK, SEED_BOOT)
    res['primary_tests_holm'] = S.holm(pv)
    return res, dm


def run(mode, outdir, synthetic=False, lock=None):
    series, pubs, hol, perf, nd = load_data(synthetic)
    if mode == 'real':
        names = list(C.MODELS); models = {n: M.get(n) for n in names}
    else:
        names = list(C.MODELS); stand = M.get('stand-in'); models = {n: stand for n in names}
    models['names'] = names
    reg = B.Regression(series, hol)
    rec, excl = build_days(series, pubs, reg, C.days())
    for n in names: models[n + '_fc'] = model_forecasts(models[n], rec)
    G = gates(mode, rec, models, series, hol, pubs, perf, lock)
    res, dm = evaluate(rec, models)
    res['L1'] = l1(models, series, hol, rec)
    os.makedirs(outdir)
    rows = []
    for D in rec:
        for k, t in enumerate(rec[D]['idx']):
            row = dict(day=f'{D:%Y-%m-%d}', period=k + 1, start_utc=t.isoformat(), outturn=rec[D]['y'][k],
                       regression=rec[D]['regression'][k], naive=rec[D]['naive'][k],
                       neso=None if rec[D]['neso'] is None else rec[D]['neso'][k])
            for n in names: row[n] = models[n + '_fc'][D][k]
            rows.append(row)
    pd.DataFrame(rows).to_csv(os.path.join(outdir, 'forecasts.csv'), index=False)
    dm.to_csv(os.path.join(outdir, 'daily_mae.csv'), index_label='day')
    pd.DataFrame(excl, columns=['day', 'scope', 'reason']).to_csv(os.path.join(outdir, 'exclusions.csv'), index=False)
    out = dict(mode=mode, synthetic=synthetic, run_utc=dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds'),
               python=platform.python_version(), versions=M.versions(), settings=M.SETTINGS, revisions=M.REVISIONS,
               scripts={f: C.sha(os.path.join(HERE, f)) for f in sorted(os.listdir(HERE)) if f.endswith('.py')},
               n_days=len(rec), n_excluded=len(excl), gates=G, gate_passed=bool(all(v for k, v in G.items() if not k.endswith('share'))),
               results=res)
    if lock: out['plan_lock'] = lock
    json.dump(out, open(os.path.join(outdir, 'results.json'), 'w'), indent=1, default=str)
    print(json.dumps({'gates': G, 'gate_passed': out['gate_passed']}, indent=1, default=str))
    return out


if __name__ == '__main__':
    mode = sys.argv[1] if len(sys.argv) > 1 else ''
    if mode == 'pipeline-test':
        if len(sys.argv) < 3: sys.exit('Give an output folder.')
        run(mode, sys.argv[2], synthetic='--synthetic' in sys.argv)
    elif mode == 'real':
        lockf = os.path.join(C.ROOT, 'plan', 'PLAN_LOCK.json')
        if not os.path.exists(lockf): sys.exit('Real run refused: plan/PLAN_LOCK.json not found (plan not frozen).')
        lock = json.load(open(lockf))
        done = sorted(glob.glob(os.path.join(C.ROOT, 'results', 'attempt*')))
        for d in done:
            f = os.path.join(d, 'results.json')
            if not os.path.exists(f): sys.exit(f'Real run refused: {d} has no results.json; log it first.')
            if json.load(open(f)).get('gate_passed'): sys.exit(f'Real run refused: {os.path.basename(d)} already passed.')
        run(mode, os.path.join(C.ROOT, 'results', f'attempt{len(done) + 1}'), lock=lock)
    else:
        sys.exit(__doc__)
