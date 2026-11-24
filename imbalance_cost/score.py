"""
Imbalance exposure, stage 1: the backtest pilot (imbalance_cost/PLAN.md, frozen at tag imbalance-cost-plan).
Committed before it runs; its outputs are committed after.

For: a reviewer checking that the exposure, its parts, the effective ratio, the dispatch ranking, the intervals, the
labels and the headline follow PLAN.md §5-11.

Reads, after checking every hash:
  forecasts   asymmetric/score.py's load_real() (with the tails study's and the variants' checks), plus Chronos-2 with
              weather but no calendar (chronos2_weather) from the weather study's forecasts file, the bridge (§6)
  prices      data/prices/prices_2024-03-16_2026-10-31.csv, whose SHA-256 must equal the committed manifest's
  T1          tails/days.csv; check 1 reads arbitrage/results.json
Writes imbalance_cost/results_stage1.json and results_stage1.md.

Measures (§8). A is outturn and F a forecast, in MW; SP the System Price and MIP the Market Index Price, in £/MWh.
Each half-hour's exposure is x = (A - F) * (SP - MIP) * 0.5, in £; positive is a loss.
    net exposure   each day's sum of x over its demand in GWh, then the mean over days: £ per GWh (primary)
    losses, gains  the same over half-hours with x > 0 and x < 0; net = losses + gains
    per MWh        total x over total absolute error in MWh, across the days of a set
    effective ratio  (sum of x over shortfall half-hours / shortfall MWh) over (sum of x over surplus half-hours /
                   surplus MWh): what a MWh of shortfall cost relative to a MWh of surplus; undefined if the surplus
                   figure is not positive
    dispatch       each day, mean MIP in the forecast's four highest half-hours minus in its four lowest (ties to the
                   earlier start), in £/MWh; beside outturn's own picks and the day's four dearest and cheapest
A day is scored if outturn, every forecaster, SP and MIP cover all its half-hours; others are listed as dropped.
Intervals: the tails study's 7-day moving-block bootstrap (2,000 draws), seed 20261124, the same draws throughout.
Paired comparisons are the forecaster's measure minus the regression's.

Modes:
    python imbalance_cost/score.py --synthetic   invented prices and forecasts with known answers on the real calendar;
                                                 writes imbalance_cost/score_synthetic.json; exits 1 on any failure
    python imbalance_cost/score.py               stage 1. Refused unless the synthetic check passed with this script,
                                                 the guarded files are committed and unchanged, and PLAN.md matches
                                                 the tag imbalance-cost-plan.
Stage 2's loading of the live forecasts is added before stage 2 runs, recorded in REVISIONS.md (PLAN.md §12).
"""
import argparse, importlib.util, json, os, platform, subprocess, sys
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
_spec = importlib.util.spec_from_file_location('asymmetric_score', os.path.join(ROOT, 'asymmetric', 'score.py'))
asy = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(asy)     # imported unchanged
st = asy.st                                                                       # tails/score_tails.py, unchanged

PLAN_TAG, SEED, SCHEMA = 'imbalance-cost-plan', 20261124, 1
TZ, EVE_FROM, EVE_TO, NPICK = 'Europe/London', 16 * 60, 19 * 60 + 30, 4
MANIFEST = os.path.join(HERE, 'prices_manifest_2024-03-16_2026-10-31.json')
MANIFEST_SHA = '77323a69a4f6e0b08e27dfef2a62942114d7c7c747b2fa1abd8d21c867fa5380'
ARB_RESULTS = os.path.join(ROOT, 'arbitrage', 'results.json')
ARB_RESULTS_SHA = 'ba8ad600be79b30f644a585b1a0e364bebf2e0ba23d3689bb577732a22f0c10a'
SYNTH_JSON = os.path.join(HERE, 'score_synthetic.json')
GUARDED = ['imbalance_cost/score.py', 'imbalance_cost/PLAN.md', 'imbalance_cost/score_synthetic.json',
           'imbalance_cost/prices_manifest_2024-03-16_2026-10-31.json', 'asymmetric/score.py', 'arbitrage/results.json'] \
    + [g for g in asy.GUARDED if not g.startswith('asymmetric/')]

REF, CH, V1, S1, TFM, AVG, NESO = asy.REF, asy.CH, asy.V1, asy.S1, asy.TFM, asy.AVG, asy.NESO
CHW = 'chronos2_weather'
FORECASTERS = [REF, CH, V1, S1, TFM, AVG, NESO, CHW]
NAMES = dict(asy.NAMES); NAMES[CHW] = 'Chronos-2, weather but no calendar (bridge)'
SETS = (('all', 'day'), ('winter', 'day'), ('T1', 'day'), ('evenings', 'eve'), ('evenings_T1', 'eve'))
LOWER, HIGHER, NCD = 'clearly lower', 'clearly higher', 'not clearly different'


def git(*a):
    return subprocess.run(['git', '-C', ROOT, *a], capture_output=True, text=True, check=True).stdout.strip()


# ------------------------------------------------------------------ rules ----------------------------------------------
def label(iv):
    if iv is None: return NCD                                 # no finite draws (e.g. a perfect forecast's per-MWh)
    lo, hi = iv
    return LOWER if hi < 0 else HIGHER if lo > 0 else NCD


def money(v): return f'{v:,.0f}'.replace('-', '−')


def headline(lab, x, y):
    """PLAN.md §11, stage 1, by rule."""
    m = {LOWER: 'clearly lower net imbalance exposure than', HIGHER: 'clearly higher net imbalance exposure than',
         NCD: 'net imbalance exposure not clearly different from'}[lab]
    return (f"In a backtest the foundation models may have seen in training, a price-taking supplier using Chronos-2's "
            f"day-ahead demand forecast would have had {m} one using a weather regression ({money(x)} against "
            f"{money(y)} £ per GWh of demand).")


# ------------------------------------------------------------------ per-day sums ---------------------------------------
def per_day(frame, cols):
    """Per day: validity, demand in GWh (whole day and evening window), and per forecaster the sums every measure needs,
    for the whole day ('day') and the evening window ('eve'); plus the dispatch spreads."""
    f = frame.sort_values(['day', 'start_utc'], kind='mergesort').reset_index(drop=True)
    days = sorted(f['day'].unique()); n = len(days)
    code = pd.Categorical(f['day'], categories=days).codes
    t = pd.to_datetime(f['start_utc'], utc=True); loc = t.dt.tz_convert(TZ)
    mins = (loc.dt.hour * 60 + loc.dt.minute).to_numpy(); eve = (mins >= EVE_FROM) & (mins <= EVE_TO)
    nhh = np.bincount(code, minlength=n)
    A = f['outturn'].to_numpy(float); SP = f['system_price'].to_numpy(float); MIP = f['mip'].to_numpy(float)
    fin = np.isfinite(A) & np.isfinite(SP) & np.isfinite(MIP)
    for c in cols: fin &= np.isfinite(f[c].to_numpy(float))
    ok = (np.bincount(code, weights=(~fin).astype(float), minlength=n) == 0) & (nhh == asy.expected_hh(days))
    S = lambda v, m=None: np.bincount(code[m] if m is not None else code, weights=(v[m] if m is not None else v), minlength=n)
    A0, spread = np.nan_to_num(A), np.nan_to_num(SP - MIP)
    P = dict(days=days, ok=ok, nhh=nhh, gwh=dict(day=S(A0 * 0.5) / 1000, eve=S(A0 * 0.5, eve) / 1000),
             mip_missing_days=[d for d, k in zip(days, np.bincount(code, weights=(~np.isfinite(MIP)).astype(float), minlength=n)) if k],
             F={}, D={})
    for c in cols:
        e = A0 - np.nan_to_num(f[c].to_numpy(float)); x = e * spread * 0.5
        row = {}
        for scope, m in (('day', np.ones(len(f), bool)), ('eve', eve)):
            row[scope] = dict(net=S(x, m), loss=S(np.where(x > 0, x, 0), m), gain=S(np.where(x < 0, x, 0), m),
                              abs_mwh=S(np.abs(e) * 0.5, m), mae_num=S(np.abs(e), m), n=S(np.ones(len(f)), m),
                              short_x=S(np.where(e > 0, x, 0), m), short_mwh=S(np.where(e > 0, e * 0.5, 0), m),
                              surp_x=S(np.where(e < 0, x, 0), m), surp_mwh=S(np.where(e < 0, -e * 0.5, 0), m))
        P['F'][c] = row
    cuts = np.flatnonzero(np.diff(code)) + 1; sl = np.split(np.arange(len(f)), cuts)
    def spread_by(v, m):
        pos = np.arange(len(v)); lo = np.lexsort((pos, v))[:NPICK]; hi = np.lexsort((pos, -v))[:NPICK]
        return m[hi].mean() - m[lo].mean()
    P['D']['perfect_price'] = np.array([spread_by(MIP[s], MIP[s]) if ok[i] else np.nan for i, s in enumerate(sl)])
    P['D']['perfect_demand'] = np.array([spread_by(A[s], MIP[s]) if ok[i] else np.nan for i, s in enumerate(sl)])
    for c in cols:
        v = f[c].to_numpy(float)
        P['D'][c] = np.array([spread_by(v[s], MIP[s]) if ok[i] else np.nan for i, s in enumerate(sl)])
    return P


# ------------------------------------------------------------------ summaries ------------------------------------------
def q90(x):
    x = np.asarray(x, float); x = x[np.isfinite(x)]
    return [float(v) for v in np.quantile(x, [0.05, 0.95])] if len(x) else None


def wsum(v, M, I):
    return np.where(M, np.nan_to_num(v)[I], 0).sum(1)


def summarise(P, I, masks, cols=FORECASTERS, ref=REF):
    out = {}
    for name, scope in SETS:
        if name not in masks: continue
        m = masks[name] & P['ok']; M = m[I]; cnt = M.sum(1); g = P['gwh'][scope]
        o = dict(n_days=int(m.sum()), scope=scope, forecasters={})
        draws = {}
        for c in cols:
            r = P['F'][c][scope]
            with np.errstate(invalid='ignore', divide='ignore'):
                daily = {k: np.where(g > 0, r[k] / g, np.nan) for k in ('net', 'loss', 'gain')}
                pt = {k: float(np.mean(daily[k][m])) for k in daily}
                dr = {k: wsum(daily[k], M, I) / cnt for k in daily}
                pt['per_mwh'] = float(r['net'][m].sum() / r['abs_mwh'][m].sum())
                dr['per_mwh'] = wsum(r['net'], M, I) / wsum(r['abs_mwh'], M, I)
                sh = r['short_x'][m].sum() / r['short_mwh'][m].sum(); su = r['surp_x'][m].sum() / r['surp_mwh'][m].sum()
                shb = wsum(r['short_x'], M, I) / wsum(r['short_mwh'], M, I); sub = wsum(r['surp_x'], M, I) / wsum(r['surp_mwh'], M, I)
                ratio_b = np.where(sub > 0, shb / sub, np.nan)
                pt['mae'] = float(np.mean((r['mae_num'] / np.maximum(r['n'], 1))[m]))
            res = {k: dict(value=pt[k], ci90=q90(dr[k])) for k in ('net', 'loss', 'gain', 'per_mwh')}
            res['mae'] = pt['mae']
            res['effective_ratio'] = dict(shortfall_cost_per_mwh=float(sh), surplus_cost_per_mwh=float(su),
                                          value=float(sh / su) if su > 0 else None, ci90=q90(ratio_b),
                                          draws_undefined=int(np.sum(~np.isfinite(ratio_b))))
            if scope == 'day':
                dsp = P['D'][c]; pd_, dd = float(np.nanmean(dsp[m])), wsum(dsp, M, I) / cnt
                res['dispatch'] = dict(value=pd_, ci90=q90(dd))
                draws[c + ':dispatch'] = dd
            draws.update({c + ':' + k: dr[k] for k in dr})
            o['forecasters'][c] = res
        for c in cols:
            if c == ref: continue
            o['forecasters'][c]['minus_regression'] = {}
            for k in ('net', 'loss', 'gain', 'per_mwh') + (('dispatch',) if scope == 'day' else ()):
                v = o['forecasters'][c][k]['value'] - o['forecasters'][ref][k]['value']
                iv = q90(draws[c + ':' + k] - draws[ref + ':' + k])
                o['forecasters'][c]['minus_regression'][k] = dict(value=v, ci90=iv, label=label(iv))
        if scope == 'day':
            refs = {}
            for k in ('perfect_price', 'perfect_demand'):
                v = P['D'][k]; refs[k] = dict(value=float(np.nanmean(v[m])), ci90=q90(wsum(v, M, I) / cnt))
            o['dispatch_references'] = refs
        out[name] = o
    return out


def masks_for(P, t1_days):
    dates = [pd.Timestamp(d) for d in P['days']]
    t1 = np.isin(P['days'], list(t1_days))
    return dict(all=np.ones(len(dates), bool), winter=np.array([d.month in (12, 1, 2) for d in dates]), T1=t1,
                evenings=np.ones(len(dates), bool), evenings_T1=t1)


def analyse(frame, t1_days, cols=FORECASTERS):
    P = per_day(frame, cols)
    I = st.boot_idx(len(P['days']), np.random.default_rng(SEED))
    return P, summarise(P, I, masks_for(P, t1_days), cols)


def write_headline(sets):
    a = sets['all']['forecasters']; d = a[CH]['minus_regression']['net']
    return headline(d['label'], a[CH]['net']['value'], a[REF]['net']['value'])


# ------------------------------------------------------------------ checks (PLAN.md §9) ------------------------------
def check_reproduction(frame):
    """Mean daily error over all backtest days, before any price-based drop, against the arbitrage study's."""
    arb = json.load(open(ARB_RESULTS))['sets']['all']['A']
    f = frame.sort_values(['day', 'start_utc']); rows, ok = [], True
    for c in FORECASTERS:
        mine = float(f.assign(e=(f['outturn'] - f[c]).abs()).groupby('day')['e'].mean().mean())
        if c in arb:
            want = arb[c]['mae']['value']; good = abs(mine - want) <= 0.01; ok &= good
            rows.append(dict(forecaster=c, computed=mine, arbitrage=want, passed=bool(good)))
        else:
            rows.append(dict(forecaster=c, computed=mine, note='not in the arbitrage study; reported only'))
    return dict(passed=bool(ok), rows=rows)


def check_prices(prices, man):
    pr = prices
    missing = int(pr['mip'].isna().sum())
    zero_vol_priced = int((pr['mip'].notna() & ~(pr['mip_volume'] > 0)).sum())
    unpriced_with_vol = int((pr['mip'].isna() & (pr['mip_volume'] > 0)).sum())
    good = (missing == man['checks']['mip_missing'] and zero_vol_priced == 0 and unpriced_with_vol == 0
            and int(pr['system_price'].isna().sum()) == man['checks']['system_price_missing'] and len(pr) == man['files']['prices']['rows'])
    return dict(passed=bool(good), mip_missing=missing, priced_without_volume=zero_vol_priced,
                system_price_missing=int(pr['system_price'].isna().sum()), rows=int(len(pr)))


def check_arithmetic(frame, P):
    worst = 0.0
    for c in FORECASTERS:
        for scope in ('day', 'eve'):
            r = P['F'][c][scope]; worst = max(worst, float(np.max(np.abs(r['net'] - r['loss'] - r['gain']))))
    g = frame.copy(); g['_perfect'] = g['outturn']; g['_double'] = g['outturn'] - 2 * (g['outturn'] - g[CH])
    Q = per_day(g, [CH, '_perfect', '_double'])
    zero = bool(np.all(Q['F']['_perfect']['day']['net'] == 0))
    dbl = bool(np.allclose(Q['F']['_double']['day']['net'], 2 * Q['F'][CH]['day']['net'], rtol=1e-9, atol=1e-6))
    return dict(passed=bool(worst <= 1e-6 and zero and dbl), net_minus_parts_max=worst, perfect_forecast_zero=zero,
                doubling_doubles=dbl)


# ------------------------------------------------------------------ loading --------------------------------------------
def load_real():
    if st.sha(MANIFEST) != MANIFEST_SHA: sys.exit('Refused: the price manifest differs from its recorded hash.')
    if st.sha(ARB_RESULTS) != ARB_RESULTS_SHA: sys.exit('Refused: arbitrage/results.json differs from its recorded hash.')
    man = json.load(open(MANIFEST)); pp = os.path.join(ROOT, man['files']['prices']['path'])
    if st.sha(pp) != man['files']['prices']['sha256']: sys.exit('Refused: the price file differs from the manifest.')
    t1, _ = asy.load_inputs()
    f = asy.load_real()                                        # every forecast file's hash is checked inside
    w = pd.read_csv(st.FORECASTS, usecols=['start_utc', CHW])
    f['_t'] = pd.to_datetime(f['start_utc'], utc=True); w['_t'] = pd.to_datetime(w['start_utc'], utc=True)
    n0 = len(f); f = f.merge(w[['_t', CHW]], on='_t', how='left', validate='one_to_one'); assert len(f) == n0
    pr = pd.read_csv(pp); pr['_t'] = pd.to_datetime(pr['start_utc'], utc=True)
    assert pr['_t'].is_unique
    f = f.merge(pr[['_t', 'system_price', 'mip']], on='_t', how='left', validate='one_to_one'); assert len(f) == n0
    return f.drop(columns='_t'), pr, man, t1


# ------------------------------------------------------------------ output ---------------------------------------------
def f0(x): return '–' if x is None else f'{x:,.0f}'
def f2(x): return '–' if x is None else f'{x:,.2f}'
def iv0(v): return '–' if not v else f'{v[0]:,.0f} to {v[1]:,.0f}'
def iv2(v): return '–' if not v else f'{v[0]:,.2f} to {v[1]:,.2f}'


def markdown(out, meta):
    L = ['# Imbalance exposure, stage 1 (backtest pilot): results (generated by imbalance_cost/score.py)', '',
         'A pilot on days the foundation models may have seen in training; no money claim (PLAN.md §5). Labels come '
         'from unadjusted 90% intervals and are not tests. Positive exposure is a loss.', '', '## Headline (PLAN.md §11)', '',
         out['headline'], '', f'Days scored: {out["sets"]["all"]["n_days"]}; dropped for a missing price or forecast: '
         f'{", ".join(out["dropped_days"]) or "none"}.', '']
    for name, o in out['sets'].items():
        L += [f'## Set: {name} ({o["n_days"]} days; {"whole day" if o["scope"] == "day" else "16:00 to 19:30 UK time"})', '',
              '| Forecaster | net £/GWh (90%) | losses | gains | £ per MWh of error | minus regression, net (90%) | label |',
              '|---|---|---|---|---|---|---|']
        for c, r in o['forecasters'].items():
            d = r.get('minus_regression', {}).get('net')
            L.append(f'| {NAMES[c]} | {f0(r["net"]["value"])} ({iv0(r["net"]["ci90"])}) | {f0(r["loss"]["value"])} | '
                     f'{f0(r["gain"]["value"])} | {f2(r["per_mwh"]["value"])} | '
                     f'{(f0(d["value"]) + " (" + iv0(d["ci90"]) + ")") if d else "—"} | {d["label"] if d else "—"} |')
        L += ['', '| Forecaster | shortfall £/MWh | surplus £/MWh | effective ratio (90%) |', '|---|---|---|---|']
        for c, r in o['forecasters'].items():
            e = r['effective_ratio']
            L.append(f'| {NAMES[c]} | {f2(e["shortfall_cost_per_mwh"])} | {f2(e["surplus_cost_per_mwh"])} | '
                     f'{f2(e["value"])} ({iv2(e["ci90"])}) |')
        if o['scope'] == 'day':
            refs = o['dispatch_references']
            L += ['', f'Dispatch (demand-proxy ranking, not earnings): perfect price {f2(refs["perfect_price"]["value"])} £/MWh; '
                  f'perfect demand {f2(refs["perfect_demand"]["value"])} £/MWh.', '',
                  '| Forecaster | captured spread £/MWh (90%) | minus regression (90%) | label |', '|---|---|---|---|']
            for c, r in o['forecasters'].items():
                d = r.get('minus_regression', {}).get('dispatch')
                L.append(f'| {NAMES[c]} | {f2(r["dispatch"]["value"])} ({iv2(r["dispatch"]["ci90"])}) | '
                         f'{(f2(d["value"]) + " (" + iv2(d["ci90"]) + ")") if d else "—"} | {d["label"] if d else "—"} |')
        L.append('')
    L += ['## Checks (PLAN.md §9)', ''] + [f'- {k}: {"passed" if v["passed"] else "FAILED"}' for k, v in out['checks'].items()]
    L += ['', f'Commit {meta["public_commit"]}; script SHA-256 {meta["script_sha256"]}; seed {SEED}; {st.B} draws in blocks of {st.BLOCK}.', '']
    return '\n'.join(L)


def real():
    if not os.path.exists(SYNTH_JSON): sys.exit('Refused: run --synthetic first and commit score_synthetic.json.')
    if git('status', '--porcelain', '--', *GUARDED): sys.exit('Refused: these must be committed and unchanged: ' + ', '.join(GUARDED))
    try: tagged = git('show', f'{PLAN_TAG}:imbalance_cost/PLAN.md')
    except subprocess.CalledProcessError: sys.exit(f'Refused: tag {PLAN_TAG} not found; run git fetch --tags.')
    if tagged != open(os.path.join(HERE, 'PLAN.md')).read().strip(): sys.exit(f'Refused: PLAN.md differs from tag {PLAN_TAG}.')
    sy = json.load(open(SYNTH_JSON))
    if not sy.get('passed') or sy.get('script_sha256') != st.sha(os.path.abspath(__file__)):
        sys.exit('Refused: the synthetic check has not passed with this script.')
    frame, prices, man, t1 = load_real()
    P, sets = analyse(frame, t1)
    out = dict(sets=sets, dropped_days=[d for d, k in zip(P['days'], P['ok']) if not k],
               days_missing_a_market_index_price=P['mip_missing_days'])
    out['checks'] = dict(reproduction=check_reproduction(frame), prices=check_prices(prices, man),
                         arithmetic=check_arithmetic(frame, P),
                         hashes=dict(passed=True, note='every file read matched its recorded SHA-256, or the run stops'),
                         synthetic=dict(passed=True, file='imbalance_cost/score_synthetic.json'))
    out['headline'] = write_headline(sets)
    meta = dict(public_commit=git('rev-parse', 'HEAD'), script_sha256=st.sha(os.path.abspath(__file__)), plan_tag=PLAN_TAG,
                seed=SEED, draws=st.B, block=st.BLOCK, price_manifest_sha256=MANIFEST_SHA,
                versions=dict(python=platform.python_version(), numpy=np.__version__, pandas=pd.__version__))
    res = dict(schema=SCHEMA, note='imbalance exposure, stage 1 (backtest pilot); plan frozen at tag imbalance-cost-plan',
               meta=meta, **st.round_floats(out))
    json.dump(res, open(os.path.join(HERE, 'results_stage1.json'), 'w'), indent=1)
    md = markdown(res, meta); open(os.path.join(HERE, 'results_stage1.md'), 'w').write(md); print(md)
    failed = [k for k, v in out['checks'].items() if not v['passed']]
    if failed: print('CHECKS FAILED: ' + ', '.join(failed)); sys.exit(1)


# ------------------------------------------------------------------ synthetic check (PLAN.md §9.4) -------------------
def synth_frame(grid, seed=5):
    """Invented outturn, prices and forecasts on the real calendar, with known answers."""
    rng = np.random.default_rng(seed)
    f = grid.sort_values(['day', 'start_utc'], kind='mergesort').reset_index(drop=True)
    pos = f.groupby('day').cumcount().to_numpy(); n = f.groupby('day')['day'].transform('size').to_numpy()
    A = np.round(25000 + 5000 * np.sin(2 * np.pi * (pos / n - 0.3)))
    mip = np.round(60 + 40 * np.sin(2 * np.pi * (pos / n - 0.3)) + rng.normal(0, 5, len(f)), 2)
    spread = np.where((pos // 2) % 2 == 0, 30.0, -10.0)          # system short: SP 30 above MIP; long: 10 below
    out = f[['day', 'start_utc']].copy(); out['outturn'] = A; out['mip'] = mip; out['system_price'] = mip + spread
    out['aligned'] = A - np.where(spread > 0, 100.0, -100.0)     # short exactly when the system is short
    sign = np.where(pos % 2 == 0, 1.0, -1.0)                     # within each spread class, as many + as -: unrelated
    out['independent'] = A - 100.0 * sign                        # to the spread, so its exposure sums to 0 each day
    out['exact'] = A
    out['price_shaped'] = mip * 1000.0                           # ranks half-hours exactly as MIP does
    return out, spread


def unit_rules():
    ok, n = True, 0
    for iv, l in (([-2, -1], LOWER), ([1, 2], HIGHER), ([0, 2], NCD), ([-2, 0], NCD), ([-1, 1], NCD)):
        n += 1; ok &= label(iv) == l
    want = {LOWER: "In a backtest the foundation models may have seen in training, a price-taking supplier using "
                   "Chronos-2's day-ahead demand forecast would have had clearly lower net imbalance exposure than one "
                   "using a weather regression (1,234 against 1,500 £ per GWh of demand).",
            HIGHER: "In a backtest the foundation models may have seen in training, a price-taking supplier using "
                    "Chronos-2's day-ahead demand forecast would have had clearly higher net imbalance exposure than one "
                    "using a weather regression (1,234 against 1,500 £ per GWh of demand).",
            NCD: "In a backtest the foundation models may have seen in training, a price-taking supplier using "
                 "Chronos-2's day-ahead demand forecast would have had net imbalance exposure not clearly different from "
                 "one using a weather regression (1,234 against 1,500 £ per GWh of demand)."}
    for l, w in want.items():
        n += 1; h = headline(l, 1234.4, 1500.0); ok &= h == w
        if h != w: print('FAIL headline\n' + h)
    n += 1; ok &= headline(NCD, -12.0, 3.0).endswith('(−12 against 3 £ per GWh of demand).')
    return bool(ok), n


def synthetic():
    t1, _ = asy.load_inputs()
    grid = pd.read_csv(st.FORECASTS, usecols=['day', 'start_utc'])
    fr, spread = synth_frame(grid)
    res = dict(script_sha256=st.sha(os.path.abspath(__file__)), checks={}); ok_all = True

    def rec(name, good, **info):
        nonlocal ok_all
        res['checks'][name] = dict(passed=bool(good), **info); ok_all &= bool(good)
        print(('PASS ' if good else 'FAIL ') + name, flush=True)

    g, n = unit_rules(); rec('unit_rules', g, n=n)
    cols = ['aligned', 'independent', 'exact', 'price_shaped']
    P = per_day(fr, cols); I = st.boot_idx(len(P['days']), np.random.default_rng(SEED))
    sets = summarise(P, I, masks_for(P, t1), cols, ref='independent')
    a = sets['all']['forecasters']
    # aligned: every half-hour is a loss of 100 MW x |spread| x 0.5 h; gains are zero
    A = fr['outturn'].to_numpy(); code = pd.Categorical(fr['day']).codes
    gwh = np.bincount(code, weights=A * 0.5) / 1000
    want_loss = float(np.mean(np.bincount(code, weights=100 * np.abs(spread) * 0.5) / gwh))
    rec('aligned forecaster: known losses', abs(a['aligned']['loss']['value'] - want_loss) < 1e-6 and a['aligned']['gain']['value'] == 0,
        loss=a['aligned']['loss']['value'], want=want_loss)
    rec('aligned forecaster: effective ratio 3', abs(a['aligned']['effective_ratio']['value'] - 3.0) < 1e-9,
        ratio=a['aligned']['effective_ratio']['value'])
    rec('independent forecaster: net 0, interval contains 0', abs(a['independent']['net']['value']) < 1e-9 and a['independent']['net']['ci90'][0] <= 0 <= a['independent']['net']['ci90'][1],
        ci90=a['independent']['net']['ci90'])
    rec('perfect forecast: zero exposure', a['exact']['net']['value'] == 0 and a['exact']['loss']['value'] == 0)
    rec('dispatch: perfect demand and price-shaped picks', abs(a['exact']['dispatch']['value'] - sets['all']['dispatch_references']['perfect_demand']['value']) < 1e-9
        and abs(a['price_shaped']['dispatch']['value'] - sets['all']['dispatch_references']['perfect_price']['value']) < 1e-9)
    rec('labels on a clear difference', a['aligned']['minus_regression']['net']['label'] == HIGHER)
    # a missing market price drops its day and never counts as 0
    fr2 = fr.copy(); first_day = fr2['day'].iloc[0]; fr2.loc[3, 'mip'] = np.nan
    P2 = per_day(fr2, cols)
    rec('missing MIP drops its day', (not P2['ok'][0]) and P2['ok'][1:].all() and P2['mip_missing_days'] == [first_day])
    # arithmetic on synthetic data
    worst = max(float(np.max(np.abs(P['F'][c]['day']['net'] - P['F'][c]['day']['loss'] - P['F'][c]['day']['gain']))) for c in cols)
    rec('net equals losses plus gains', worst <= 1e-6)
    # the pipeline and headline with the real forecaster names
    fr3 = fr.copy()
    for c, src in ((REF, 'independent'), (CH, 'aligned'), (V1, 'independent'), (S1, 'independent'), (TFM, 'independent'),
                   (AVG, 'independent'), (NESO, 'exact'), (CHW, 'independent')):
        fr3[c] = fr3[src]
    P3, s3 = analyse(fr3, t1); h = write_headline(s3)
    rec('pipeline and headline', 'clearly higher net imbalance exposure than' in h and s3['T1']['n_days'] == 96
        and s3['evenings']['scope'] == 'eve' and check_arithmetic(fr3, P3)['passed'], headline=h)
    res['passed'] = bool(ok_all)
    json.dump(st.round_floats(res), open(SYNTH_JSON, 'w'), indent=1, default=str)
    print('synthetic: ' + ('PASS' if ok_all else 'FAIL'))
    return ok_all


if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('--synthetic', action='store_true')
    if ap.parse_args().synthetic: sys.exit(0 if synthetic() else 1)
    real()
