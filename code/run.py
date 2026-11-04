"""
The official run (plan Sections 3-10).

Modes
  pipeline-test OUTDIR [--synthetic]
        The whole pipeline with the stand-in forecaster in every model slot. No foundation model is loaded, so no
        model forecasts GB demand. With --synthetic, synthetic data replace the downloaded files.
  real  The official run. Refuses without plan/PLAN_LOCK.json, and once an attempt has passed the gate. Each attempt
        is saved to results/attemptN/; the first attempt that passes every gate check is the run.

Outputs: forecasts.csv (every forecaster, every target half-hour), daily_mae.csv, exclusions.csv, context_fills.csv,
neso_file_mismatches.csv, results.json.

Deviation 1 (deviations/DEVIATIONS.md) changed gate checks 3 and 4, and added the robustness rescoring, the NESO
sensitivity checks and the exploratory tables the plan lists; no forecast is computed differently.
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
        perf = synth.performance_file(pubs, s); nd = I.load_nd(synth.historic_nd(s))
        return s, pubs, hol, perf, nd
    s, _ = I.load_indo(os.path.join(C.DATA, 'indo.csv'))
    pubs = I.load_neso(os.path.join(C.DATA, 'neso_dayahead_publications.csv'))
    hol = {pd.Timestamp(d) for d in json.load(open(os.path.join(C.DATA, 'bank_holidays_ew.json')))}
    perf = pd.read_csv(os.path.join(C.DATA, 'neso_forecast_performance.csv'))
    nd_path = os.path.join(C.DATA, 'neso_historic_nd.csv')
    nd = I.load_nd(nd_path) if os.path.exists(nd_path) else None
    return s, pubs, hol, perf, nd


def build_days(series, pubs, reg, days):
    """Per target day: targets, context, regression, seasonal naive, NESO (or the reason a day is excluded)."""
    rec, excl = {}, []
    for D in days:
        r = dict(day=D)
        try:
            r['y'], r['idx'] = I.targets(series, D)
            r['ctx'], cidx, r['filled'] = I.context(series, D)
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


def neso_file_comparison(rec, perf, indep):
    """NESO's performance file against the forecast used, SP 17-48 (descriptive since deviation 1). For each
    mismatch: where the file's value first appears among the Elexon publications."""
    p = perf.copy(); p['Date'] = pd.to_datetime(p['Date']).dt.normalize()
    p = p.drop_duplicates(['Date', 'Settlement_Period'], keep='first')
    p = p[(p.Settlement_Period >= 17) & (p.Settlement_Period <= 48)]
    ours = [(D, k + 1, t, v) for D in rec if rec[D]['neso'] is not None
            for k, (t, v) in enumerate(zip(rec[D]['idx'], rec[D]['neso']))]
    o = pd.DataFrame(ours, columns=['Date', 'Settlement_Period', 'start_utc', 'ours'])
    j = o.merge(p[['Date', 'Settlement_Period', 'Demand_Forecast']], on=['Date', 'Settlement_Period'])
    j['match'] = (j.ours - j.Demand_Forecast).abs() < 0.5
    mm = j[~j.match].copy()
    def where(r):
        f = indep.first_with_value(r.start_utc, r.Demand_Forecast)
        if f is None: return 'in no publication'
        f = pd.Timestamp(f, tz='UTC')
        return 'at or before 09:30 on D-1' if f <= C.issue_time(r.Date) else (
            'later on D-1' if f < C.local(r.Date, '00:00') else 'on D')
    mm['file_value_first_published'] = [where(r) for r in mm.itertuples()] if len(mm) else []
    share = float(j.match.mean()) if len(j) else 0.0
    return share, len(j), mm.drop(columns='match')


def gates(mode, rec, models, series, hol, pubs, perf, lock):
    """Returns (checks, info): checks are the pass/fail items of plan Section 9 as amended by deviation 1;
    info holds descriptive numbers that never decide the gate."""
    g, info = {}, {}
    if mode == 'real':
        g['1_data_hashes'] = all(C.sha(os.path.join(C.DATA, f)) == h for f, h in lock['data_sha256'].items())
    g['2_no_lookahead'] = all((rec[D]['neso'] is None) or (pd.to_datetime(rec[D]['neso_pub'], utc=True) <= C.issue_time(D)).all()
                              for D in rec)                       # inputs are asserted where they are built
    # 3 (deviation 1): the NESO forecast used equals an independent selection from the raw Elexon publications
    indep = I.NesoIndependent(pubs); diffs = []
    for D in rec:
        if rec[D]['neso'] is None: continue
        cut = C.issue_time(D)
        alt = np.array([indep.value(t, cut) for t in rec[D]['idx']])
        diffs.append(np.nan if np.isnan(alt).any() else float(np.abs(alt - rec[D]['neso']).max()))
    g['3_neso_selection_independent'] = bool(len(diffs) > 0 and np.nanmax(diffs) == 0.0 and not np.isnan(diffs).any())
    info['3_neso_days_checked'] = len(diffs)
    mm = None
    if perf is not None:
        share, n, mm = neso_file_comparison(rec, perf, indep)
        info['3_neso_file_agreement_share'] = share; info['3_neso_file_halfhours_compared'] = n
        info['3_neso_file_mismatch_days'] = int(mm.Date.nunique())
        info['3_neso_file_mismatch_where'] = mm.file_value_first_published.value_counts().to_dict()
    for name in models['names']:
        fc = models[name + '_fc']
        g[f'4_{name}_finite_and_length'] = all(np.isfinite(fc[D]).all() and len(fc[D]) == len(rec[D]['y']) for D in rec)
        # 4 (deviation 1): repeat exactly the call that made the forecasts: the first batch, same days, same order
        groups = {}
        for D in rec: groups.setdefault(C.horizon(D), []).append(D)
        (h, first), ds = next(iter(groups.items())); batch = ds[:64]
        F = models[name].forecast([rec[D]['ctx'] for D in batch], h)
        g[f'4_{name}_repeatable'] = all(np.array_equal(f[first:first + len(rec[D]['y'])], fc[D]) for D, f in zip(batch, F))
        small = model_forecasts(models[name], {D: rec[D] for D in batch[:3]})
        info[f'4_{name}_batch_size_effect_mw'] = float(max(np.abs(small[D] - fc[D]).max() for D in small))
        D = batch[0]; c = rec[D]['ctx'].copy(); c[-1] += 1000
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
    return g, info, mm


def evaluate(rec, models, nd_map=None, perf_mm=None, hol=frozenset()):
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
    names = models['names']; fcs = {n: models[n + '_fc'] for n in names}
    fcs['regression'] = {D: rec[D]['regression'] for D in rec}; fcs['naive'] = {D: rec[D]['naive'] for D in rec}
    comp = lambda a, b, m: S.compare(dm.loc[m, a], dm.loc[m, b], C.BOOT_B, C.BOOT_BLOCK, SEED_BOOT)

    # Robustness (plan Section 6): primary ratios rescored against NESO's later ND series, descriptive only
    if nd_map is not None:
        nd_mae = {}
        for k, f in fcs.items():
            v = {}
            for D in rec:
                y = np.array([nd_map.get((D, i + 1), np.nan) for i in range(len(rec[D]['y']))])
                if np.isfinite(y).all(): v[D] = S.daily_mae(y, f[D])
            nd_mae[k] = pd.Series(v)
        dnd = pd.DataFrame(nd_mae); mnd = dnd.index[(dnd.index >= pd.Timestamp(C.FULL_START)) & (dnd.index <= pd.Timestamp(C.FULL_END))]
        res['robustness_nd'] = {f'{n}_vs_regression': S.compare(dnd.loc[mnd, n], dnd.loc[mnd, 'regression'], C.BOOT_B, C.BOOT_BLOCK, SEED_BOOT)
                                for n in names}
        res['robustness_nd']['n_days'] = int(len(mnd))

    # NESO sensitivity (deviation 1): the days on which NESO's own file records a different forecast
    if perf_mm is not None and len(perf_mm):
        bad = set(pd.to_datetime(perf_mm.Date))
        keep = full & dm['neso'].notna() & ~dm.index.isin(bad)
        sens = {f'{n}_vs_neso_excluding_file_mismatch_days': comp(n, 'neso', keep) for n in names}
        alt = {D: rec[D]['neso'].copy() for D in rec if rec[D]['neso'] is not None}
        for r in perf_mm.itertuples():
            D = pd.Timestamp(r.Date)
            if D in alt: alt[D][r.Settlement_Period - 1] = r.Demand_Forecast
        dm_alt = daily({D: rec[D] for D in alt}, alt)
        both = full & dm['neso'].notna()
        for n in names:
            sens[f'{n}_vs_neso_file_values_on_mismatch_days'] = S.compare(dm.loc[both, n], dm_alt.loc[dm.index[both]], C.BOOT_B, C.BOOT_BLOCK, SEED_BOOT)
        sens['n_mismatch_days'] = len(bad)
        res['secondary_sensitivity'] = sens

    # Exploratory tables (plan Section 6): between models; by season, weekday, holiday and time of day
    pairs = [(a, b) for i, a in enumerate(names) for b in names[i + 1:]]
    for a, b in pairs: res['exploratory'][f'{a}_vs_{b}'] = comp(a, b, full)
    cols = names + ['regression', 'naive', 'neso']
    d = dm.loc[full, cols]
    season = d.index.month.map({12: 'winter', 1: 'winter', 2: 'winter', 3: 'spring', 4: 'spring', 5: 'spring',
                                6: 'summer', 7: 'summer', 8: 'summer', 9: 'autumn', 10: 'autumn', 11: 'autumn'})
    res['exploratory']['mae_by_season'] = d.groupby(season).mean().round(1).to_dict()
    res['exploratory']['mae_by_weekday'] = d.groupby(d.index.day_name()).mean().round(1).to_dict()
    res['exploratory']['mae_by_holiday'] = d.groupby(np.where(d.index.isin(list(hol)), 'bank holiday', 'other day')).mean().round(1).to_dict()
    tod = {k: {} for k in cols}
    for D in d.index:
        clock = [t.tz_convert(C.UK).strftime('%H:%M') for t in rec[D]['idx']]
        for k in cols:
            f = rec[D]['neso'] if k == 'neso' else fcs[k][D]
            if f is None: continue
            for c, e in zip(clock, np.abs(rec[D]['y'] - f)): tod[k].setdefault(c, []).append(e)
    res['exploratory']['mae_by_time_of_day'] = {k: {c: round(float(np.mean(v)), 1) for c, v in sorted(t.items())} for k, t in tod.items()}

    th = 1 - C.M_THRESHOLD                                   # Section 8, interpretation rule 2
    for n in models['names']:
        c = res['primary'][n]; h = res['primary_tests_holm']
        c['ci90_upper_below_threshold'] = bool(c['ci90_descriptive'][1] < th)
        c['threshold_confirmed_after_holm'] = h[f'{n}_meaningful']['rejected']
        c['interval_below_threshold_but_not_confirmed'] = c['ci90_upper_below_threshold'] and not c['threshold_confirmed_after_holm']
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
    G, info, perf_mm = gates(mode, rec, models, series, hol, pubs, perf, lock)
    res, dm = evaluate(rec, models, nd, perf_mm, hol)
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
    if perf_mm is not None: perf_mm.to_csv(os.path.join(outdir, 'neso_file_mismatches.csv'), index=False)
    fills = sorted({t for D in rec for t in rec[D]['filled']})
    pd.DataFrame({'filled_start_utc': fills, 'n_target_days_using_it': [sum(t in rec[D]['filled'] for D in rec) for t in fills]}
                 ).to_csv(os.path.join(outdir, 'context_fills.csv'), index=False)
    out = dict(mode=mode, synthetic=synthetic, run_utc=dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds'),
               python=platform.python_version(), versions=M.versions(), settings=M.SETTINGS, revisions=M.REVISIONS,
               scripts={f: C.sha(os.path.join(HERE, f)) for f in sorted(os.listdir(HERE)) if f.endswith('.py')},
               n_days=len(rec), n_excluded=len(excl), n_context_fills=len(fills), gates=G, gate_info=info, gate_passed=bool(all(G.values())),
               results=res)
    if lock: out['plan_lock'] = lock
    json.dump(out, open(os.path.join(outdir, 'results.json'), 'w'), indent=1, default=str)
    print(json.dumps({'gates': G, 'gate_info': info, 'gate_passed': out['gate_passed']}, indent=1, default=str))
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
        expected = dict(lock['files_sha256']); amends = []
        for af in sorted(glob.glob(os.path.join(C.ROOT, 'plan', 'LOCK_AMENDMENT_*.json'))):
            a = json.load(open(af)); amends.append(a)
            expected.update({f: v['new'] for f, v in a['files_changed'].items()})
        lock = dict(lock, amendments=amends)
        changed = [f for f, h in expected.items() if C.sha(os.path.join(C.ROOT, f)) != h]
        if changed: sys.exit('Real run refused: changed since the freeze (a deviation; log it first): ' + ', '.join(changed))
        done = sorted(glob.glob(os.path.join(C.ROOT, 'results', 'attempt*')))
        for d in done:
            f = os.path.join(d, 'results.json')
            if not os.path.exists(f): sys.exit(f'Real run refused: {d} has no results.json; log it first.')
            if json.load(open(f)).get('gate_passed'): sys.exit(f'Real run refused: {os.path.basename(d)} already passed.')
        run(mode, os.path.join(C.ROOT, 'results', f'attempt{len(done) + 1}'), lock=lock)
    else:
        sys.exit(__doc__)
