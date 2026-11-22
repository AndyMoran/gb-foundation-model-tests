"""
Asymmetric cost study (asymmetric/PLAN.md, frozen at tag asymmetric-plan): score fixed day-ahead forecasts when a
shortfall costs k times a surplus. Committed before it runs; its outputs are committed after.

For: a reviewer checking that the sets, the weighted loss, the intervals, the break-even cases, the direction
statistics and the headline follow PLAN.md §4-8.

Reads, after checking each file's SHA-256:
    the tails study's saved forecasts, through tails/score_tails.load_real() and its own hash checks (PLAN.md §4)
    lgbm_variants/forecasts.csv      V1 (lgbm_v1); its hash must match lgbm_variants/forecasts.json
    tails/days.csv, day_inputs.csv   T1 and t_mean; their hashes must match tails/days.json
    checkpoint0/results.json, lgbm_variants/results.json, weather_study/correction1/correction.json,
    tails/results.json               the published figures that check 1 reproduces
Writes asymmetric/results.json and asymmetric/results.md.

Terms. Error e = outturn - forecast, in MW; positive is a shortfall. At cost ratio k an error costs k*e if e > 0,
else -e. U is a forecaster's mean shortfall and O its mean surplus, so its mean weighted loss is k*U + O.
    all       every half-hour of each scored day; a day's mean over its own 46, 48 or 50 half-hours, then the
              unweighted mean over days (the published mean daily error at k = 1)
    peaks     on each T1 day, the day's highest outturn half-hour minus the forecaster's highest forecast half-hour
              (as score_tails.per_day), then the mean over T1 days
    evenings  the eight half-hours starting 16:00 to 19:30 Europe/London on each T1 day, averaged as 'all'
For a comparison of forecaster a against reference b, the paired difference at k is a's mean weighted loss minus
b's. Its 90% interval is the 5th to 95th percentile over a 7-day moving-block bootstrap of the days (2,000 draws,
seed 20261122, score_tails.boot_idx), the same draws for every comparison and forecaster. T1 is fixed; a resampled
day counts towards a cold set if it is a T1 day, repeats included. Labels and break-even cases are in PLAN.md §5.

Modes:
    python asymmetric/score.py --synthetic   invented forecasts with known shortfalls and surpluses on the real
                                             calendar, real T1 and real t_mean; writes asymmetric/score_synthetic.json
                                             and exits 1 if any check fails. No outturn or forecast is read.
    python asymmetric/score.py               the real run. Refused unless the synthetic check passed with this
                                             script, the guarded files are committed and unchanged, and PLAN.md
                                             matches the tag asymmetric-plan.
"""
import argparse, importlib.util, json, os, platform, subprocess, sys
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
_spec = importlib.util.spec_from_file_location('score_tails', os.path.join(ROOT, 'tails', 'score_tails.py'))
st = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(st)      # imported unchanged

PLAN_TAG = 'asymmetric-plan'
SEED, KS, EPS = 20261122, (0.5, 1.0, 1.5, 2.0, 3.0, 5.0, 10.0), 1e-6
TZ, EVE_FROM, EVE_TO = 'Europe/London', 16 * 60, 19 * 60 + 30            # half-hours starting 16:00 ... 19:30
SCHEMA = 1

P = lambda *a: os.path.join(ROOT, *a)
LV_CSV, LV_JSON = P('lgbm_variants', 'forecasts.csv'), P('lgbm_variants', 'forecasts.json')
CP0_JSON, LV_RESULTS = P('checkpoint0', 'results.json'), P('lgbm_variants', 'results.json')
CORR_JSON, TAILS_JSON = P('weather_study', 'correction1', 'correction.json'), P('tails', 'results.json')
DAYS_CSV, DAYS_JSON, DAY_INPUTS = st.DAYS_CSV, st.DAYS_JSON, st.DAY_INPUTS
RECORDED = {                                    # SHA-256 of each file read here, recorded when this script was written
    CP0_JSON: '7cae4ffa56a6b151e93a0a2a159e5e475163b7f7d00913a1d71ed380ce69b1ca',
    TAILS_JSON: '236dce97bfe77eb4c012a045bad3851b37f19f85c8f6b29f0b7bc58ccbccd5a3',
    LV_RESULTS: '74cffdad188fad972ba98fa1318f7dcc8ed87ef38d12ce76ec168cf8fb61f58c',
    LV_JSON: '250b98cb903ab2892528165719f173d69bb425e14d3151cfe2ec750fe88baec8',
    CORR_JSON: '016612229b063b0e215af498435e6140f0e31a78b70dedfca6b4081af77a179f',
    DAYS_JSON: '196050a620c2bb2d916a3522712437dfbca1f3d04cd7d4f271fa27199009b181',
}
SYNTH_JSON = os.path.join(HERE, 'score_synthetic.json')
GUARDED = ['asymmetric/score.py', 'asymmetric/PLAN.md', 'asymmetric/score_synthetic.json', 'tails/score_tails.py',
           'tails/days.csv', 'tails/days.json', 'tails/day_inputs.csv', 'tails/results.json',
           'lgbm_variants/forecasts.csv', 'lgbm_variants/forecasts.json', 'lgbm_variants/results.json',
           'checkpoint0/results.json', 'weather_study/correction1/correction.json']

REF, CH, V1, AVG = st.REF, 'chronos2_A', 'lgbm_v1', 'avg_chronos2_regression'
TFM, S1, NESO = 'timesfm25_weather_single_day', 'lightgbm_s1', 'neso'
FORECASTERS = [REF, CH, V1, TFM, S1, NESO, AVG]
NAMES = {REF: 'Weather regression', CH: 'Chronos-2', V1: 'LightGBM V1', TFM: 'TimesFM 2.5 (one day per call)',
         S1: 'LightGBM S1', NESO: 'NESO day-ahead', AVG: 'Average of Chronos-2 and the regression'}
COMPARISONS = [('primary', CH, REF), ('secondary', CH, V1), ('descriptive', TFM, REF), ('descriptive', S1, REF),
               ('descriptive', NESO, REF), ('descriptive', AVG, REF), ('descriptive', AVG, CH)]
SETS = ('all', 'peaks', 'evenings')
SET_ROLE = {'all': 'primary', 'peaks': 'primary', 'evenings': 'descriptive'}
LESS, MORE, NCD = 'clearly less', 'clearly more', 'not clearly different'
CASE_TEXT = {1: 'crossing: better below the break-even ratio, worse above', 2: 'crossing: worse below, better above',
             3: 'better at every ratio above 0', 4: 'worse at every ratio above 0', 5: 'identical'}


def git(*a):
    return subprocess.run(['git', '-C', ROOT, *a], capture_output=True, text=True, check=True).stdout.strip()


def fk(k):
    return f'{k:g}'


# ------------------------------------------------------------------ rules (PLAN.md §5) -------------------------------
def label(iv):
    """'clearly less' only if the upper end is below 0; 'clearly more' only if the lower end is above 0."""
    lo, hi = iv
    return LESS if hi < 0 else MORE if lo > 0 else NCD


def case_of(dU, dO, eps=EPS):
    """Break-even case and k* for a minus b, with dU = U_a - U_b and dO = O_a - O_b. Loss difference = k*dU + dO."""
    u0, o0 = abs(dU) <= eps, abs(dO) <= eps
    if u0 and o0: return 5, None
    if u0: return (3 if dO < 0 else 4), None
    if o0: return (3 if dU < 0 else 4), 0.0                    # equal only at k = 0
    k = -dO / dU
    if k > 0: return (1 if dU > 0 else 2), k
    return (3 if dU < 0 else 4), k                             # k* < 0: no crossing at k > 0


def case_vec(dU, dO, eps=EPS):
    """case_of over arrays of bootstrap draws (NaN draws give case 0)."""
    out = np.zeros(len(dU), int); ks = np.full(len(dU), np.nan)
    for i, (u, o) in enumerate(zip(dU, dO)):
        if np.isfinite(u) and np.isfinite(o):
            c, k = case_of(u, o, eps); out[i] = c; ks[i] = np.nan if k is None else k
    return out, ks


def groups(labels):
    """Consecutive ratios with the same label, in order of k: [(label, [k, ...]), ...]."""
    g = []
    for k, l in zip(KS, labels):
        if g and g[-1][0] == l: g[-1][1].append(k)
        else: g.append((l, [k]))
    return g


def span(ks):
    return fk(ks[0]) if len(ks) == 1 else f'{fk(ks[0])} to {fk(ks[-1])}'


def rest(g):
    """', not clearly different at 1, and clearly more from 1.5 to 10' for every group after the first."""
    parts = [f'{l} {"at" if len(ks) == 1 else "from"} {span(ks)}' for l, ks in g[1:]]
    if len(parts) == 1: return ', and ' + parts[0]
    return ', ' + ', '.join(parts[:-1]) + ', and ' + parts[-1]


def first(g):
    l, ks = g[0]
    return f'where a shortfall cost {span(ks)} times a surplus'


def headline(lab_all, lab_peak):
    """PLAN.md §8, written by rule from the labels at each k for the two primary sets."""
    ga, gp = groups(lab_all), groups(lab_peak)
    if len(ga) == 1:
        a = (f'Chronos-2 had {ga[0][0]} cost-weighted error than a weather regression over all half-hours at each '
             f'tested cost ratio from {fk(KS[0])} to {fk(KS[-1])}')
    else:
        a = (f'Chronos-2 had, over all half-hours, {ga[0][0]} cost-weighted error than a weather regression '
             f'{first(ga)}{rest(ga)}')
    where = 'in the size of the daily peak on the coldest tenth of days'
    if len(gp) == 1:
        b = f'and {gp[0][0]} {where} at each tested ratio'
    else:
        b = f'and, {where}, {gp[0][0]} {first(gp)}{rest(gp)}'
    return f'In a backtest it may have seen in training, {a}{", " if len(ga) == 1 else "; "}{b}.'


def be_sentence(be_all, be_peak):
    def one(where, be):
        c = be['case']; share = f'{round(100 * be["shares"][str(c)])}% of bootstrap draws in this case'
        if c in (1, 2):
            iv = (f'; conditional 90% interval {be["k_star_ci90"][0]:.2f} to {be["k_star_ci90"][1]:.2f}'
                  if be.get('k_star_ci90') else '; no interval, as fewer than 90% of draws were in this case')
            side = 'better below it and worse above' if c == 1 else 'worse below it and better above'
            return f'{where} the break-even ratio was {be["k_star"]:.2f} (Chronos-2 {side}; {share}{iv})'
        if c == 5: return f'{where} the two were identical ({share})'
        return f'{where} there was no break-even ratio above 0 (Chronos-2 {CASE_TEXT[c]}; {share})'
    return one('Over all half-hours,', be_all) + '; ' + one('at cold-day peaks,', be_peak) + '.'


# ------------------------------------------------------------------ per-day quantities --------------------------------
def expected_hh(days):
    d0 = pd.DatetimeIndex([pd.Timestamp(d).tz_localize(TZ) for d in days])
    d1 = pd.DatetimeIndex([(pd.Timestamp(d) + pd.Timedelta(days=1)).tz_localize(TZ) for d in days])
    return ((d1 - d0) / pd.Timedelta(minutes=30)).to_numpy().astype(int)


def daily(frame, cols):
    """Per day and forecaster: U, O and loss at each k over all half-hours and the evening window; daily bias;
    peak-magnitude error; and whether the day is complete. Days are every day in the frame, in date order."""
    f = frame.sort_values(['day', 'start_utc'], kind='mergesort').reset_index(drop=True)
    t = pd.to_datetime(f['start_utc'], utc=True)
    loc = t.dt.tz_convert(TZ)
    assert (loc.dt.strftime('%Y-%m-%d') == f['day']).all(), 'a half-hour is filed under the wrong local day'
    assert t.is_unique, 'duplicate UTC start times'
    days = sorted(f['day'].unique()); code = pd.Categorical(f['day'], categories=days).codes
    nhh = np.bincount(code, minlength=len(days))
    mins = (loc.dt.hour * 60 + loc.dt.minute).to_numpy()
    eve = (mins >= EVE_FROM) & (mins <= EVE_TO)
    y = f['outturn'].to_numpy(float)
    y_ok = pd.Series(np.isfinite(y)).groupby(code).all().to_numpy()
    y_peak = pd.Series(y).groupby(code).max().to_numpy()
    n_eve = np.bincount(code[eve], minlength=len(days))
    D = dict(days=days, nhh=nhh, nhh_expected=expected_hh(days), n_eve=n_eve, hh_day=code)
    for c in cols:
        x = f[c].to_numpy(float); e = y - x; fin = np.isfinite(e)
        ok = pd.Series(fin).groupby(code).all().to_numpy() & y_ok & (nhh == D['nhh_expected'])
        ok_eve = pd.Series(fin[eve]).groupby(code[eve]).all().reindex(range(len(days)), fill_value=False).to_numpy() \
            & (n_eve == 8)
        sh, su = np.maximum(e, 0), np.maximum(-e, 0)
        mean = lambda v, m=None: (pd.Series(v[m] if m is not None else v)
                                  .groupby(code[m] if m is not None else code).mean()
                                  .reindex(range(len(days))).to_numpy())
        pe = y_peak - pd.Series(x).groupby(code).max().to_numpy()
        D[c] = dict(ok=ok, ok_eve=ok_eve, U=mean(sh), O=mean(su), bias=mean(e), mae=mean(np.abs(e)),
                    Ue=mean(sh, eve), Oe=mean(su, eve), pe=pe, Up=np.maximum(pe, 0), Op=np.maximum(-pe, 0),
                    L={k: mean(np.where(e > 0, k * e, -e)) for k in KS},
                    Le={k: mean(np.where(e > 0, k * e, -e), eve) for k in KS})
    return D


def set_arrays(D, c, s):
    """(U, O, direct loss per k, completeness) per day for forecaster c on set s; peaks have one value per day."""
    d = D[c]
    if s == 'all': return d['U'], d['O'], d['L'], d['ok']
    if s == 'evenings': return d['Ue'], d['Oe'], d['Le'], d['ok_eve']
    return d['Up'], d['Op'], {k: np.where(d['pe'] > 0, k * d['pe'], -d['pe']) for k in KS}, d['ok']


# ------------------------------------------------------------------ scoring --------------------------------------------
def bmean(v, M, cnt):
    with np.errstate(invalid='ignore', divide='ignore'):
        return np.where(cnt > 0, (np.where(M, v, 0.0)).sum(1) / np.maximum(cnt, 1), np.nan)


def q90(x):
    x = x[np.isfinite(x)]
    return [float(v) for v in np.quantile(x, [0.05, 0.95])] if len(x) else None


def compare(D, I, t1, a, b, s):
    """Paired differences, labels and break-even case for a minus b on set s (PLAN.md §5)."""
    Ua, Oa, La, oka = set_arrays(D, a, s); Ub, Ob, Lb, okb = set_arrays(D, b, s)
    m = oka & okb & (t1 if s != 'all' else True)
    M = m[I]; cnt = M.sum(1); kept = cnt > 0
    dU_b = bmean(Ua[I] - Ub[I], M, cnt); dO_b = bmean(Oa[I] - Ob[I], M, cnt)
    pt = {x: float(v[m].mean()) for x, v in (('Ua', Ua), ('Oa', Oa), ('Ub', Ub), ('Ob', Ob))}
    dU, dO = pt['Ua'] - pt['Ub'], pt['Oa'] - pt['Ob']
    rows = []
    for k in KS:
        iv = q90(k * dU_b + dO_b)
        rows.append(dict(k=k, a=k * pt['Ua'] + pt['Oa'], b=k * pt['Ub'] + pt['Ob'], diff=k * dU + dO, ci90=iv,
                         label=label(iv)))
    c0, k0 = case_of(dU, dO)
    cs, kst = case_vec(dU_b, dO_b)
    n = int(kept.sum())
    shares = {str(c): float((cs[kept] == c).sum() / n) for c in range(1, 6)}
    be = dict(case=c0, case_text=CASE_TEXT[c0], k_star=k0, shares=shares, draws=n, k_star_ci90=None)
    if c0 in (1, 2) and shares[str(c0)] >= 0.9: be['k_star_ci90'] = q90(kst[kept & (cs == c0)])
    days = np.asarray(D['days'])[m]
    nhh = int(D['nhh'][m].sum()) if s == 'all' else (int(D['n_eve'][m].sum()) if s == 'evenings' else int(m.sum()))
    excl = [str(d) for d in np.asarray(D['days'])[(t1 if s != 'all' else np.ones(len(m), bool)) & ~m]]
    return dict(a=a, b=b, set=s, n_days=int(m.sum()), n_values=nhh, days_dropped=excl,
                draws_dropped=int((~kept).sum()), **pt, rows=rows, break_even=be)


def direction(D, I, c, tmean):
    """PLAN.md §5a for forecaster c over its complete days."""
    d = D[c]; ok = d['ok']; days = np.asarray(D['days'])
    bias = np.where(ok, d['bias'], np.nan); n = int(ok.sum())
    order = np.lexsort((days, tmean))                          # coldest first; ties by date
    order = order[ok[order]]
    grp = np.full(len(days), -1);
    for g, idx in enumerate(np.array_split(order, 10)): grp[idx] = g
    G = []
    for g in range(10):
        m = grp == g; M = m[I]; cnt = M.sum(1)
        G.append(dict(group=g + 1, n_days=int(m.sum()), t_mean_range=[float(tmean[m].min()), float(tmean[m].max())],
                      bias=float(bias[m].mean()), ci90=q90(bmean(np.nan_to_num(bias)[I], M, cnt))))
    x, y = tmean[ok], bias[ok]
    slope = float(np.polyfit(x, y, 1)[0])
    Mo = ok[I]; X = np.where(Mo, tmean[I], np.nan); Y = np.where(Mo, np.nan_to_num(bias)[I], np.nan)
    Xc = X - np.nanmean(X, 1, keepdims=True); Yc = Y - np.nanmean(Y, 1, keepdims=True)
    slopes = np.nansum(Xc * Yc, 1) / np.nansum(Xc * Xc, 1)
    dt = pd.to_datetime(pd.Series(days))
    nxt = ((dt.shift(-1) - dt) == pd.Timedelta(days=1)).to_numpy()[:-1] & ok[:-1] & ok[1:]
    b0, b1 = bias[:-1][nxt], bias[1:][nxt]
    short = bias > 0
    runs = {}
    for name, flag in (('short', bias > 0), ('long', bias < 0)):
        best = (0, None, None); cur = 0; start = None
        for i in range(len(days)):
            contig = i > 0 and (dt.iloc[i] - dt.iloc[i - 1]) == pd.Timedelta(days=1)
            if flag[i] and ok[i]:
                if cur and contig: cur += 1
                else: cur, start = 1, days[i]
                if cur > best[0]: best = (cur, str(start), str(days[i]))
            else: cur = 0
        runs[name] = dict(days=best[0], first=best[1], last=best[2])
    return dict(n_days=n, mean_bias=float(np.nanmean(bias)), groups=G, slope_mw_per_c=slope, slope_ci90=q90(slopes),
                share_short=float(short[ok].mean()),
                lag1_autocorr=float(np.corrcoef(b0, b1)[0, 1]) if b0.std() > 0 and b1.std() > 0 else None,
                n_pairs=int(nxt.sum()),
                share_short_after_short=float((b1[b0 > 0] > 0).mean()) if (b0 > 0).any() else None, longest_runs=runs)


def analyse(frame, t1_days, tmean_by_day, comparisons, forecasters):
    D = daily(frame, forecasters)
    days = D['days']; n = len(days)
    t1 = np.isin(days, list(t1_days))
    tmean = np.array([tmean_by_day[d] for d in days], float)
    I = st.boot_idx(n, np.random.default_rng(SEED))
    out = dict(n_days=n, n_t1=int(t1.sum()), comparisons=[], direction={}, means={})
    for c in forecasters:
        out['means'][c] = {}
        for s in SETS:
            U, O, L, ok = set_arrays(D, c, s); m = ok & (t1 if s != 'all' else True)
            out['means'][c][s] = dict(n_days=int(m.sum()), U=float(U[m].mean()), O=float(O[m].mean()),
                                      loss={fk(k): float(L[k][m].mean()) for k in KS})
    for role, a, b in comparisons:
        for s in SETS:
            r = compare(D, I, t1, a, b, s); r['role'] = role if s != 'evenings' else 'descriptive'
            out['comparisons'].append(r)
    for c in forecasters: out['direction'][c] = direction(D, I, c, tmean)
    return D, out


def find(out, a, b, s):
    return next(r for r in out['comparisons'] if r['a'] == a and r['b'] == b and r['set'] == s)


def write_headline(out):
    ra, rp = find(out, CH, REF, 'all'), find(out, CH, REF, 'peaks')
    out['headline'] = headline([r['label'] for r in ra['rows']], [r['label'] for r in rp['rows']])
    out['break_even_sentence'] = be_sentence(ra['break_even'], rp['break_even'])


# ------------------------------------------------------------------ checks (PLAN.md §7) ------------------------------
def check_linearity(out, D, t1):
    worst = 0.0
    for c, sets in out['means'].items():
        for s, v in sets.items():
            for k in KS: worst = max(worst, abs(v['loss'][fk(k)] - (k * v['U'] + v['O'])))
    return dict(passed=bool(worst <= 0.01), max_abs_mw=worst)


def check_direction(out):
    worst = max(abs(out['direction'][c]['mean_bias'] - (out['means'][c]['all']['U'] - out['means'][c]['all']['O']))
                for c in out['direction'])
    sizes = sorted({g['n_days'] for c in out['direction'] for g in out['direction'][c]['groups']})
    return dict(passed=bool(worst <= 0.01 and sizes == [out['n_days'] // 10] and out['n_days'] % 10 == 0),
                max_abs_mw=worst, group_sizes=sizes)


def check_alignment(out, frame):
    rows = [dict(a=r['a'], b=r['b'], set=r['set'], n_days=r['n_days'], n_values=r['n_values'],
                 days_dropped=r['days_dropped']) for r in out['comparisons']]
    ok = all(not r['days_dropped'] for r in rows) and bool(frame['start_utc'].is_unique)
    return dict(passed=ok, rows=rows)


def check_reproduction(out, D, frame, t1_days):
    """Check 1 (PLAN.md §7): k = 1 over all half-hours reproduces each published mean daily error at the precision
    published; on T1 peaks U - O reproduces the published signed peak error to 4 places, and U + O equals the mean
    absolute peak error from score_tails.per_day to 0.01 MW."""
    cp0 = json.load(open(CP0_JSON))['mean_daily_mae_mw']
    lv = json.load(open(LV_RESULTS))['mean_daily_mae_mw']
    corr = json.load(open(CORR_JSON))['corrected']['mae_mw']['with_weather']
    tails = json.load(open(TAILS_JSON))['sets']['T1']['forecasters']
    pub = {REF: (cp0[REF], 1), CH: (cp0[CH], 1), S1: (cp0[S1], 1), V1: (lv[V1], 1), TFM: (corr, None)}
    rows, ok = [], True
    for c in FORECASTERS:
        m = out['means'][c]['all']['loss']['1']
        if c in pub:
            v, dp = pub[c]
            good = round(m, dp) == v if dp is not None else abs(m - v) <= 0.01
            rows.append(dict(forecaster=c, computed=m, published=v, precision=f'{dp} dp' if dp else '0.01 MW', passed=good))
            ok &= good
        else:
            rows.append(dict(forecaster=c, computed=m, published=None, note='no published 960-day figure; reported only'))
    P = st.per_day(frame[['day', 'start_utc', 'outturn'] + st.FORECASTERS])     # the tails study's own per-day path
    same_days = P['days'] == D['days']
    t1 = np.isin(P['days'], list(t1_days))
    peaks = []
    for c in [x for x in FORECASTERS if x in tails]:
        mp = out['means'][c]['peaks']
        signed = round(mp['U'] - mp['O'], 4); want = tails[c]['set']['peak']
        absmean = float(np.abs(P['peak'][c][t1 & P['ok'][c]]).mean())
        mae_same = float(np.max(np.abs(P['mae'][c] - D[c]['mae']))) if same_days else None
        pk_same = float(np.max(np.abs(P['peak'][c] - D[c]['pe']))) if same_days else None
        good = abs(signed - want) < 1e-9 and abs(mp['U'] + mp['O'] - absmean) <= 0.01 and same_days \
            and mae_same <= 1e-6 and pk_same <= 1e-6
        peaks.append(dict(forecaster=c, signed=signed, published=want, abs_mean=mp['U'] + mp['O'],
                          abs_mean_per_day=absmean, per_day_max_diff_mae=mae_same, per_day_max_diff_peak=pk_same,
                          passed=bool(good)))
        ok &= good
    return dict(passed=bool(ok), all_k1=rows, t1_peaks=peaks)


# ------------------------------------------------------------------ loading --------------------------------------------
def sha_check(extra=()):
    bad = [f'{os.path.relpath(p, ROOT)}: {st.sha(p)}' for p, h in list(RECORDED.items()) + list(extra) if st.sha(p) != h]
    if bad: sys.exit('Refused: files differ from their recorded hashes:\n' + '\n'.join(bad))


def load_inputs():
    dj = json.load(open(DAYS_JSON))
    sha_check([(DAYS_CSV, dj['days_csv_sha256']), (DAY_INPUTS, dj['day_inputs_csv_sha256']),
               (LV_CSV, json.load(open(LV_JSON))['forecasts_sha256'])])
    t1 = st.load_days(DAYS_CSV)['T1']
    di = pd.read_csv(DAY_INPUTS, dtype={'day': str})
    return t1, dict(zip(di['day'], di['t_mean']))


def load_real():
    f = st.load_real()                                         # tails hash checks inside
    lv = pd.read_csv(LV_CSV, usecols=['start_utc', V1])
    f['_t'] = pd.to_datetime(f['start_utc'], utc=True); lv['_t'] = pd.to_datetime(lv['start_utc'], utc=True)
    assert f['_t'].is_unique and lv['_t'].is_unique
    n0 = len(f)
    f = f.merge(lv[['_t', V1]], on='_t', how='left', validate='one_to_one')
    assert len(f) == n0 == len(lv), f'V1 has {len(lv)} half-hours; the tails frame has {n0}'
    assert f[V1].notna().all(), 'V1 is missing half-hours the tails frame has'
    f[AVG] = 0.5 * f[CH] + 0.5 * f[REF]                       # fixed weights, PLAN.md §4
    return f[['day', 'start_utc', 'outturn'] + st.FORECASTERS + [V1, AVG]]


# ------------------------------------------------------------------ output ---------------------------------------------
def r1(x): return f'{x:,.1f}'


def markdown(out, meta):
    L = ['# Asymmetric cost: results (generated by asymmetric/score.py)', '',
         'Exploratory sensitivity analysis on committed forecasts (PLAN.md §3). Labels come from unadjusted 90% '
         'intervals and are not tests.', '', '## Headline (PLAN.md §8)', '', out['headline'], '', out['break_even_sentence'], '',
         '## Paired differences (a minus b, MW; negative means a had less weighted error)', '']
    for r in out['comparisons']:
        L += [f'### {NAMES[r["a"]]} minus {NAMES[r["b"]]}: {r["set"]} ({r["role"]}; {r["n_days"]} days)', '',
              f'U (mean shortfall): {r1(r["Ua"])} vs {r1(r["Ub"])} MW. O (mean surplus): {r1(r["Oa"])} vs {r1(r["Ob"])} MW.', '',
              '| k | a | b | a − b | 90% interval | label |', '|---|---|---|---|---|---|']
        for x in r['rows']:
            L.append(f'| {fk(x["k"])} | {r1(x["a"])} | {r1(x["b"])} | {r1(x["diff"])} | '
                     f'{r1(x["ci90"][0])} to {r1(x["ci90"][1])} | {x["label"]} |')
        be = r['break_even']
        ks = f'{be["k_star"]:.3f}' if be['k_star'] is not None else 'none'
        iv = f'; conditional 90% interval {be["k_star_ci90"][0]:.2f} to {be["k_star_ci90"][1]:.2f}' if be['k_star_ci90'] else ''
        sh = ', '.join(f'case {c}: {100 * v:.1f}%' for c, v in be['shares'].items())
        L += ['', f'Break-even: case {be["case"]} ({be["case_text"]}); k* = {ks}{iv}. Draws by case: {sh}.', '']
    L += ['## Direction and consistency (PLAN.md §5a; descriptive)', '',
          '| Forecaster | mean bias | slope, MW/°C (90%) | share short | lag-1 autocorr | short after short | longest short run | longest long run |',
          '|---|---|---|---|---|---|---|---|']
    for c, d in out['direction'].items():
        rs, rl = d['longest_runs']['short'], d['longest_runs']['long']
        L.append(f'| {NAMES[c]} | {r1(d["mean_bias"])} | {d["slope_mw_per_c"]:.1f} ({d["slope_ci90"][0]:.1f} to '
                 f'{d["slope_ci90"][1]:.1f}) | {d["share_short"]:.3f} | {d["lag1_autocorr"]:.3f} | '
                 f'{d["share_short_after_short"]:.3f} | {rs["days"]} ({rs["first"]} to {rs["last"]}) | '
                 f'{rl["days"]} ({rl["first"]} to {rl["last"]}) |')
    L += ['', 'Mean daily bias by temperature group (1 = coldest tenth), MW, with 90% interval:', '',
          '| Forecaster | ' + ' | '.join(str(g) for g in range(1, 11)) + ' |', '|---' * 11 + '|']
    for c, d in out['direction'].items():
        L.append(f'| {NAMES[c]} | ' + ' | '.join(f'{g["bias"]:.0f} ({g["ci90"][0]:.0f}, {g["ci90"][1]:.0f})'
                                                   for g in d['groups']) + ' |')
    L += ['', '## Checks (PLAN.md §7)', '']
    for k, v in out['checks'].items(): L.append(f'- {k}: {"passed" if v["passed"] else "FAILED"}')
    L += ['', f'Commit {meta["public_commit"]}; script SHA-256 {meta["script_sha256"]}; seed {SEED}; '
              f'{st.B} draws in blocks of {st.BLOCK}.', '']
    return '\n'.join(L)


def real():
    if not os.path.exists(SYNTH_JSON): sys.exit('Refused: run --synthetic first and commit score_synthetic.json.')
    if git('status', '--porcelain', '--', *GUARDED): sys.exit('Refused: these must be committed and unchanged: ' + ', '.join(GUARDED))
    try: tagged = git('show', f'{PLAN_TAG}:asymmetric/PLAN.md')
    except subprocess.CalledProcessError: sys.exit(f'Refused: tag {PLAN_TAG} not found; fetch the tags.')
    if tagged != open(os.path.join(HERE, 'PLAN.md')).read().strip(): sys.exit(f'Refused: PLAN.md differs from tag {PLAN_TAG}.')
    sy = json.load(open(SYNTH_JSON))
    if not sy.get('passed') or sy.get('script_sha256') != st.sha(os.path.abspath(__file__)):
        sys.exit('Refused: the synthetic check has not passed with this script.')
    t1, tmean = load_inputs()
    frame = load_real()
    D, out = analyse(frame, t1, tmean, COMPARISONS, FORECASTERS)
    t1m = np.isin(D['days'], t1)
    out['checks'] = dict(reproduction=check_reproduction(out, D, frame, t1), alignment=check_alignment(out, frame),
                         linearity=check_linearity(out, D, t1m), direction=check_direction(out),
                         hashes=dict(passed=True, note='every file read matched its recorded SHA-256, or the run stops'),
                         synthetic=dict(passed=True, file='asymmetric/score_synthetic.json'))
    write_headline(out)
    a1, c1 = out['means'][AVG]['all']['loss']['1'], out['means'][CH]['all']['loss']['1']
    out['avg_over_chronos_all_k1'] = a1 / c1
    meta = dict(public_commit=git('rev-parse', 'HEAD'), script_sha256=st.sha(os.path.abspath(__file__)),
                plan_tag=PLAN_TAG, seed=SEED, draws=st.B, block=st.BLOCK, eps_mw=EPS, ks=list(KS),
                files_sha256={os.path.relpath(p, ROOT): h for p, h in RECORDED.items()},
                versions=dict(python=platform.python_version(), numpy=np.__version__, pandas=pd.__version__))
    res = dict(schema=SCHEMA, note='asymmetric cost study; exploratory; plan frozen at tag asymmetric-plan', meta=meta,
               **st.round_floats(out))
    json.dump(res, open(os.path.join(HERE, 'results.json'), 'w'), indent=1)
    md = markdown(res, meta); open(os.path.join(HERE, 'results.md'), 'w').write(md); print(md)
    failed = [k for k, v in out['checks'].items() if not v['passed']]
    if failed: print('CHECKS FAILED: ' + ', '.join(failed)); sys.exit(1)


# ------------------------------------------------------------------ synthetic check (PLAN.md §7.4, §7.6) -------------
BASE, SPIKE = 25000.0, 6000.0


def synth_frame(grid, spec):
    """Invented outturn and forecasts on the real calendar. spec[c] = (u, o, s): arrays over days (or scalars).
    On each day the forecaster's error is +2u on even-numbered half-hours and -2o on odd ones, so its daily mean
    shortfall is u and mean surplus o (every day, and the evening window, has an even number of half-hours starting
    on an even index). Outturn is BASE with a SPIKE at half-hour 2 (if s is even, 0) or 3 (if s is odd, 1), outside
    the window, so the peak error is +2u or -2o."""
    f = grid.sort_values(['day', 'start_utc'], kind='mergesort').reset_index(drop=True)
    days = sorted(f['day'].unique()); code = pd.Categorical(f['day'], categories=days).codes
    pos = f.groupby('day').cumcount().to_numpy()
    y = np.full(len(f), BASE)
    out = f[['day', 'start_utc']].copy()
    spikes = {}
    for c, (u, o, s) in spec.items():
        u = np.broadcast_to(np.asarray(u, float), (len(days),))[code]
        o = np.broadcast_to(np.asarray(o, float), (len(days),))[code]
        spikes[c] = np.broadcast_to(np.asarray(s, int), (len(days),))[code]
        e = np.where(pos % 2 == 0, 2 * u, -2 * o)
        out[c] = -e                                             # forecast = outturn - e, outturn added below
        out[c + '_spike'] = spikes[c]
    sp = next(iter(spikes.values()))
    assert all((v == sp).all() for v in spikes.values()), 'one spike position per day for all forecasters'
    y = np.where(pos == 2 + sp, BASE + SPIKE, y)
    out['outturn'] = y
    for c in spec: out[c] = y + out[c]; out.drop(columns=c + '_spike', inplace=True)
    return out, days


def unit_rules():
    ok, n = True, 0
    T = [((100, -200), 1, 2.0), ((-200, 200), 2, 1.0), ((-100, -100), 3, -1.0), ((-100, 0), 3, 0.0), ((0, -100), 3, None),
         ((100, 100), 4, -1.0), ((100, 0), 4, 0.0), ((0, 100), 4, None), ((0, 0), 5, None),
         ((5e-7, -5e-7), 5, None), ((5e-6, 0), 4, 0.0), ((-5e-6, 5e-7), 3, 0.0), ((5e-6, -5e-6), 1, 1.0)]
    for (dU, dO), c, k in T:
        got = case_of(dU, dO); n += 1
        good = got[0] == c and ((k is None and got[1] is None) or (k is not None and got[1] is not None and abs(got[1] - k) < 1e-9))
        if not good: print('FAIL case_of', dU, dO, got, c, k)
        ok &= good
    for iv, l in (([-5, -1], LESS), ([1, 5], MORE), ([0, 5], NCD), ([-5, 0], NCD), ([0, 0], NCD), ([-1, 1], NCD)):
        n += 1; good = label(iv) == l; ok &= good
        if not good: print('FAIL label', iv)
    H = [([LESS] * 7, [MORE] * 7,
          'In a backtest it may have seen in training, Chronos-2 had clearly less cost-weighted error than a weather '
          'regression over all half-hours at each tested cost ratio from 0.5 to 10, and clearly more in the size of '
          'the daily peak on the coldest tenth of days at each tested ratio.'),
         ([LESS] * 4 + [NCD] * 3, [LESS, NCD] + [MORE] * 5,
          'In a backtest it may have seen in training, Chronos-2 had, over all half-hours, clearly less cost-weighted '
          'error than a weather regression where a shortfall cost 0.5 to 2 times a surplus, and not clearly different '
          'from 3 to 10; and, in the size of the daily peak on the coldest tenth of days, clearly less where a shortfall '
          'cost 0.5 times a surplus, not clearly different at 1, and clearly more from 1.5 to 10.'),
         ([NCD] * 7, [LESS] * 6 + [NCD],
          'In a backtest it may have seen in training, Chronos-2 had not clearly different cost-weighted error than a '
          'weather regression over all half-hours at each tested cost ratio from 0.5 to 10, and, in the size of the daily '
          'peak on the coldest tenth of days, clearly less where a shortfall cost 0.5 to 5 times a surplus, and not '
          'clearly different at 10.')]
    for la, lp, want in H:
        n += 1; got = headline(la, lp); good = got == want; ok &= good
        if not good: print('FAIL headline\n got: ' + got + '\nwant: ' + want)
    return bool(ok), n


def near(a, b, tol=1e-9): return a is not None and b is not None and abs(a - b) <= tol * max(1.0, abs(b))


def synthetic():
    t1, tmean = load_inputs()
    grid = pd.read_csv(st.FORECASTS, usecols=['day', 'start_utc'])           # the real calendar; no values
    days = sorted(grid['day'].unique()); n = len(days)
    t1m = np.isin(days, t1)
    res = dict(script_sha256=st.sha(os.path.abspath(__file__)), n_days=n, n_t1=int(t1m.sum()), checks={})
    ok_all = True

    def rec(name, good, **info):
        nonlocal ok_all
        res['checks'][name] = dict(passed=bool(good), **info); ok_all &= bool(good)
        print(('PASS ' if good else 'FAIL ') + name, flush=True)

    good, nr = unit_rules(); rec('unit_rules', good, n=nr)

    # 1. every case end to end, constant per day (so every draw is the same), exact integers
    even = np.zeros(n, int)                                    # spike on an even half-hour: peak error +2u
    designs = {                     # name: ((u_a, o_a), (u_b, o_b), case, k*)
        'case1': ((300, 100), (200, 300), 1, 2.0), 'case2': ((100, 400), (300, 200), 2, 1.0),
        'case3_kneg': ((100, 100), (200, 200), 3, -1.0), 'case3_k0': ((100, 200), (200, 200), 3, 0.0),
        'case3_Ueq': ((200, 100), (200, 200), 3, None), 'case4_kneg': ((200, 200), (100, 100), 4, -1.0),
        'case4_k0': ((200, 200), (100, 200), 4, 0.0), 'case5': ((200, 300), (200, 300), 5, None),
        'eps_inside': ((200 + 5e-7, 300), (200, 300), 5, None), 'eps_outside': ((200 + 5e-6, 300), (200, 300), 4, 0.0)}
    for name, ((ua, oa), (ub, ob), case, k) in designs.items():
        fr, _ = synth_frame(grid, {'A': (ua, oa, even), 'B': (ub, ob, even)})
        D, out = analyse(fr, t1, tmean, [('primary', 'A', 'B')], ['A', 'B'])
        r = find(out, 'A', 'B', 'all'); be = r['break_even']
        good = (be['case'] == case and (near(be['k_star'], k) if k is not None else be['k_star'] is None)
                and be['shares'][str(case)] == 1.0 and near(r['Ua'], ua) and near(r['Oa'], oa))
        if case in (1, 2): good &= be['k_star_ci90'] is not None and all(near(v, k) for v in be['k_star_ci90'])
        else: good &= be['k_star_ci90'] is None
        re = find(out, 'A', 'B', 'evenings')['break_even']; good &= re['case'] == case
        rp = find(out, 'A', 'B', 'peaks')                      # spike even: peak U = 2u, O = 0
        good &= near(rp['Ua'], 2 * ua) and rp['Oa'] == 0
        good &= check_linearity(out, D, t1m)['passed'] and check_direction(out)['passed']
        rec('end_to_end_' + name, good, case=be['case'], k_star=be['k_star'], shares=be['shares'])

    # 2. an interval endpoint exactly at 0: case 2 has a - b = 0 at k = 1 in every draw
    fr, _ = synth_frame(grid, {'A': (100, 400, even), 'B': (300, 200, even)})
    _, out = analyse(fr, t1, tmean, [('primary', 'A', 'B')], ['A', 'B'])
    row = next(x for x in find(out, 'A', 'B', 'all')['rows'] if x['k'] == 1.0)
    rec('endpoint_zero', row['ci90'] == [0.0, 0.0] and row['label'] == NCD, ci90=row['ci90'])

    # 3. labels that change more than once along the grid: noisy days with k* = 3
    rng = np.random.default_rng(7)
    ua = 300 + rng.normal(0, 150, n).clip(-250, 250); oa = 200 + rng.normal(0, 150, n).clip(-150, 250)
    z = rng.normal(0, 100, n).clip(-150, 150); z -= z.mean()  # paired noise, mean 0: a - b = 0 at k = 3 exactly
    fr, _ = synth_frame(grid, {'A': (ua + 50, oa, even), 'B': (ua, oa + 150 + z, even)})
    _, out = analyse(fr, t1, tmean, [('primary', 'A', 'B')], ['A', 'B'])
    labs = [x['label'] for x in find(out, 'A', 'B', 'all')['rows']]
    changes = sum(a != b for a, b in zip(labs, labs[1:]))
    rec('labels_change_twice', changes >= 2 and labs[0] == LESS and labs[-1] == MORE and labs[KS.index(3.0)] == NCD,
        labels=labs)

    # 4. the headline from a real-shaped run: Chronos-2 and the regression named as in the real run
    sp = (np.arange(n) % 2).astype(int)                        # peaks alternate even/odd: peak U and O both > 0
    fr, _ = synth_frame(grid, {CH: (ua + 50, oa, sp), REF: (ua, oa + 150 + z, sp)})
    _, out = analyse(fr, t1, tmean, [('primary', CH, REF)], [CH, REF]); write_headline(out)
    la = [x['label'] for x in find(out, CH, REF, 'all')['rows']]
    lp = [x['label'] for x in find(out, CH, REF, 'peaks')['rows']]
    rec('headline_by_rule', out['headline'] == headline(la, lp) and out['headline'].startswith(
        'In a backtest it may have seen in training, Chronos-2 had'), headline=out['headline'],
        break_even=out['break_even_sentence'])
    rp = find(out, CH, REF, 'peaks'); m = t1m
    rec('peak_values', near(rp['Ua'], float((2 * (ua + 50) * (sp == 0))[m].mean()), 1e-9)
        and near(rp['Oa'], float((2 * oa * (sp == 1))[m].mean()), 1e-9), Ua=rp['Ua'], Oa=rp['Oa'])

    # 5. direction (§7.6): too weak a temperature response gives a negative slope; alternating signs a negative
    #    lag-1 autocorrelation; mean daily bias = U - O; ten groups of 96
    tm = np.array([tmean[d] for d in days]); b = -40.0 * (tm - tm.mean())
    alt = np.where(np.arange(n) % 2 == 0, 100.0, -100.0)
    fr, _ = synth_frame(grid, {'weak': (np.maximum(b, 0) + 50, np.maximum(-b, 0) + 50, even),
                               'alt': (np.maximum(alt, 0) + 50, np.maximum(-alt, 0) + 50, even)})
    _, out = analyse(fr, t1, tmean, [], ['weak', 'alt'])
    dw, da = out['direction']['weak'], out['direction']['alt']
    rec('direction', dw['slope_mw_per_c'] < 0 and abs(dw['slope_mw_per_c'] + 40) < 1e-6 and dw['slope_ci90'][1] < 0
        and da['lag1_autocorr'] < 0 and check_direction(out)['passed'],
        slope=dw['slope_mw_per_c'], slope_ci90=dw['slope_ci90'], autocorr=da['lag1_autocorr'],
        groups=sorted({g['n_days'] for g in dw['groups']}), runs_alt=da['longest_runs'])

    res['passed'] = bool(ok_all)
    json.dump(st.round_floats(res), open(SYNTH_JSON, 'w'), indent=1, default=str)
    print('synthetic: ' + ('PASS' if ok_all else 'FAIL'))
    return ok_all


if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('--synthetic', action='store_true')
    a = ap.parse_args()
    if a.synthetic: sys.exit(0 if synthetic() else 1)
    real()
