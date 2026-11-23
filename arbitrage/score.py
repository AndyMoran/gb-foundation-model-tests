"""
Arbitrage signal (arbitrage/PLAN.md, frozen at tag arbitrage-plan): does a forecast pick the right hours, and does it
know what NESO's forecast does not? Committed before it runs; its outputs are committed after.

For: a reviewer checking that the measures, intervals, labels and headline follow PLAN.md §6-9.

Reads, after checking hashes: the forecasts, through asymmetric/score.py's load_real() and its checks (PLAN.md §5);
tails/days.csv for T1; asymmetric/results.json for check 1. Writes arbitrage/results.json and arbitrage/results.md.

Measures (PLAN.md §6). y is outturn, F a forecast, N NESO's day-ahead forecast, all in MW, on Europe/London days.
    A  missed spread: each day, mean outturn in outturn's own four highest half-hours minus its four lowest, less the
       same in the forecast's four highest and four lowest (ties to the earlier start); mean over days. Also the
       capture share (total captured over total perfect) and hits (of 8). Part A includes NESO as a forecaster.
    B  gain: on each half-hour, sign(F - N) * (y - N); each day's mean, then the mean over days. Also the hit rate
       (half-hours with F != N on which y - N has the same sign as F - N, pooled). Bias-corrected: F and N each
       corrected by their own recent bias before scoring (REVISIONS.md 1). Combination: the mean daily error of
       (F + N) / 2 against NESO's.
    C  day-to-day direction: does the change in the forecast's daily mean (or peak) from the day before have the same
       sign as outturn's? All consecutive-day pairs, and pairs whose later day is Tuesday to Friday.
Intervals: 90%, from the tails study's 7-day moving-block bootstrap of the days (2,000 draws), seed 20261123, the
same draws for everything. Paired comparisons are the forecaster's measure minus the regression's on each draw.

Modes:
    python arbitrage/score.py --synthetic   invented outturn and forecasts with known answers on the real calendar;
                                            writes arbitrage/score_synthetic.json; exits 1 if any check fails.
    python arbitrage/score.py               the real run. Refused unless the synthetic check passed with this
                                            script, the guarded files are committed and unchanged, and PLAN.md
                                            matches the tag arbitrage-plan.
"""
import argparse, importlib.util, json, os, platform, subprocess, sys
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
_spec = importlib.util.spec_from_file_location('asymmetric_score', os.path.join(ROOT, 'asymmetric', 'score.py'))
asy = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(asy)     # imported unchanged
st = asy.st                                                                       # tails/score_tails.py, unchanged

PLAN_TAG, SEED, SCHEMA = 'arbitrage-plan', 20261123, 1
NPICK, WIN_FROM, WIN_TO = 4, 2, 29            # four half-hours each end; bias window: days D-29 to D-2
ASY_RESULTS = os.path.join(ROOT, 'asymmetric', 'results.json')
ASY_RESULTS_SHA = 'afe88d93b58a224d865574d8665f99c43256c10761a114c71d1d3a2c989532b5'
SYNTH_JSON = os.path.join(HERE, 'score_synthetic.json')
GUARDED = ['arbitrage/score.py', 'arbitrage/PLAN.md', 'arbitrage/score_synthetic.json', 'asymmetric/score.py',
           'asymmetric/results.json'] + [g for g in asy.GUARDED if not g.startswith('asymmetric/')]

REF, CH, V1, S1, TFM, AVG, NESO = asy.REF, asy.CH, asy.V1, asy.S1, asy.TFM, asy.AVG, asy.NESO
FA = [REF, CH, V1, S1, TFM, AVG, NESO]        # part A and C: NESO scored as a forecaster
FB = [REF, CH, V1, S1, TFM, AVG]              # part B: each against NESO
NAMES = dict(asy.NAMES)
SETS = ('all', 'winter', 'T1')
LOWER, HIGHER, NCD = 'clearly lower', 'clearly higher', 'not clearly different'
POS, NEG, NCD0 = 'clearly positive', 'clearly negative', 'not clearly different from 0'


def git(*a):
    return subprocess.run(['git', '-C', ROOT, *a], capture_output=True, text=True, check=True).stdout.strip()


# ------------------------------------------------------------------ rules ----------------------------------------------
def diff_label(iv):
    lo, hi = iv
    return LOWER if hi < 0 else HIGHER if lo > 0 else NCD


def gain_label(iv):
    lo, hi = iv
    return NEG if hi < 0 else POS if lo > 0 else NCD0


def headline(missed_lab, x, y, g_lab, g, iv, gr, ivr):
    """PLAN.md §9: two sentences, by rule."""
    m = {LOWER: "clearly less of each day's demand spread than", HIGHER: "clearly more of each day's demand spread than",
         NCD: "an amount of each day's demand spread not clearly different from"}[missed_lab]
    t = {POS: 'clearly towards Chronos-2', NEG: 'clearly away from Chronos-2',
         NCD0: 'neither clearly towards nor away from Chronos-2'}[g_lab]
    s1 = (f"In a backtest it may have seen in training, when choosing a battery's four lowest and four highest "
          f"half-hours, Chronos-2 missed {m} a weather regression ({x:,.0f} against {y:,.0f} MW a day).")
    s2 = (f"Where it disagreed with NESO's day-ahead forecast, outturn moved {t}, by {g:,.1f} MW on average "
          f"(90% interval {iv[0]:,.1f} to {iv[1]:,.1f}); for the regression the figure was {gr:,.1f} MW "
          f"({ivr[0]:,.1f} to {ivr[1]:,.1f}).")
    return s1 + ' ' + s2


# ------------------------------------------------------------------ per-day quantities --------------------------------
def picks(v, pos):
    """Indices of the four lowest and four highest values, ties to the earlier start."""
    return np.lexsort((pos, v))[:NPICK], np.lexsort((pos, -v))[:NPICK]


def trailing(daily, dates):
    """For each day D, the mean of daily over D-29 ... D-2 (28 calendar days), NaN unless all 28 are present."""
    at = {d: i for i, d in enumerate(dates)}
    out = np.full(len(dates), np.nan)
    for i, d in enumerate(dates):
        idx = [at.get(d - pd.Timedelta(days=k)) for k in range(WIN_FROM, WIN_TO + 1)]
        if all(j is not None for j in idx): out[i] = daily[idx].mean()
    return out


def per_day(frame, fa=FA, fb=FB, ncol=NESO):
    f = frame.sort_values(['day', 'start_utc'], kind='mergesort').reset_index(drop=True)
    days = sorted(f['day'].unique()); n = len(days)
    dates = [pd.Timestamp(d) for d in days]
    code = pd.Categorical(f['day'], categories=days).codes
    cuts = np.flatnonzero(np.diff(code)) + 1
    sl = np.split(np.arange(len(f)), cuts)
    nhh = np.array([len(s) for s in sl])
    y = f['outturn'].to_numpy(float); N = f[ncol].to_numpy(float)
    X = {c: f[c].to_numpy(float) for c in set(fa) | set(fb)}
    finite = np.isfinite(y) & np.isfinite(N)
    for c in X: finite &= np.isfinite(X[c])
    ok = np.array([finite[s].all() for s in sl]) & (nhh == asy.expected_hh(days))
    P = dict(days=days, dates=dates, nhh=nhh, ok=ok, y_mean=np.array([y[s].mean() for s in sl]),
             y_peak=np.array([y[s].max() for s in sl]), perfect=np.zeros(n), A={}, B={}, C={})
    ylo = []; yhi = []
    for i, s in enumerate(sl):
        lo, hi = picks(y[s], np.arange(len(s))); ylo.append(set(lo)); yhi.append(set(hi))
        P['perfect'][i] = y[s][hi].mean() - y[s][lo].mean()
    for c in fa:
        F = X[c]; cap = np.zeros(n); hits = np.zeros(n)
        for i, s in enumerate(sl):
            lo, hi = picks(F[s], np.arange(len(s)))
            cap[i] = y[s][hi].mean() - y[s][lo].mean()
            hits[i] = len(set(hi) & yhi[i]) + len(set(lo) & ylo[i])
        P['A'][c] = dict(captured=cap, missed=P['perfect'] - cap, hits=hits,
                         mae=np.array([np.abs(y[s] - F[s]).mean() for s in sl]),
                         bias=np.array([(y[s] - F[s]).mean() for s in sl]),
                         f_mean=np.array([F[s].mean() for s in sl]), f_peak=np.array([F[s].max() for s in sl]))
    nb = trailing(np.array([(y[s] - N[s]).mean() for s in sl]), dates)
    for c in fb:
        F = X[c]; fb_ = trailing(np.array([(y[s] - F[s]).mean() for s in sl]), dates)
        row = dict(trail_bias=fb_)
        for tag, Fx, Nx in (('raw', F, N), ('bc', F + fb_[code], N + nb[code])):
            sgn = np.sign(Fx - Nx); g = sgn * (y - Nx)
            row['gain_' + tag] = np.array([g[s].mean() for s in sl])
            row['dis_' + tag] = np.array([(sgn[s] != 0).sum() for s in sl], float)
            row['hit_' + tag] = np.array([((sgn[s] != 0) & (np.sign(y[s] - Nx[s]) == sgn[s])).sum() for s in sl], float)
        row['bc_ok'] = np.isfinite(fb_) & np.isfinite(nb)
        for k in ('gain_bc', 'dis_bc', 'hit_bc'): row[k] = np.where(row['bc_ok'], row[k], np.nan)
        cm = (F + N) / 2
        row['combo_mae'] = np.array([np.abs(y[s] - cm[s]).mean() for s in sl])
        P['B'][c] = row
    prev = np.r_[False, np.array([(dates[i] - dates[i - 1]) == pd.Timedelta(days=1) for i in range(1, n)])]
    prev &= ok & np.r_[False, ok[:-1]]
    wk = np.array([d.dayofweek in (1, 2, 3, 4) for d in dates])
    for c in fa:
        a = P['A'][c]; row = dict(pair=prev, weekday=prev & wk)
        for tag, fv, yv in (('mean', a['f_mean'], P['y_mean']), ('peak', a['f_peak'], P['y_peak'])):
            df = np.r_[np.nan, np.diff(fv)]; dy = np.r_[np.nan, np.diff(yv)]
            row['same_' + tag] = np.where(prev, (np.sign(df) == np.sign(dy)) & (dy != 0), False).astype(float)
        P['C'][c] = row
    return P


# ------------------------------------------------------------------ summaries ------------------------------------------
def q90(x):
    x = x[np.isfinite(x)]
    return [float(v) for v in np.quantile(x, [0.05, 0.95])] if len(x) else None


def bmean(v, m, I):
    v = np.nan_to_num(np.asarray(v, float)); M = m[I]; cnt = M.sum(1)
    with np.errstate(invalid='ignore', divide='ignore'):
        return float(v[m].mean()) if m.any() else None, np.where(cnt > 0, np.where(M, v[I], 0).sum(1) / cnt, np.nan)


def bratio(num, den, m, I):
    num = np.nan_to_num(np.asarray(num, float)); den = np.nan_to_num(np.asarray(den, float)); M = m[I]
    with np.errstate(invalid='ignore', divide='ignore'):
        d = np.where(M, den[I], 0).sum(1)
        return (float(num[m].sum() / den[m].sum()) if den[m].sum() else None), \
            np.where(d > 0, np.where(M, num[I], 0).sum(1) / d, np.nan)


def pack(pt, draws):
    return dict(value=pt, ci90=q90(draws))


def summarise(P, I, set_masks):
    out = {}
    for s, base in set_masks.items():
        m = base & P['ok']; o = dict(n_days=int(m.sum()), A={}, B={}, C={})
        ref_missed = bmean(P['A'][REF]['missed'], m, I)
        for c in FA:
            a = P['A'][c]
            pm, dm = bmean(a['missed'], m, I)
            ps, ds = bratio(a['captured'], P['perfect'], m, I)
            ph, dh = bmean(a['hits'], m, I)
            pe, de = bmean(a['mae'], m, I)
            r = dict(missed=pack(pm, dm), capture_share=pack(ps, ds), hits=pack(ph, dh), mae=pack(pe, de))
            if c != REF:
                iv = q90(dm - ref_missed[1])
                r['missed_minus_regression'] = dict(value=pm - ref_missed[0], ci90=iv, label=diff_label(iv))
            o['A'][c] = r
        ref_b = {t: bmean(P['B'][REF]['gain_' + t], m & (P['B'][REF]['bc_ok'] if t == 'bc' else True), I) for t in ('raw', 'bc')}
        pn, dn = bmean(P['A'][NESO]['mae'], m, I)
        for c in FB:
            b = P['B'][c]; r = {}
            for t in ('raw', 'bc'):
                mm = m & (b['bc_ok'] if t == 'bc' else True)
                pg, dg = bmean(b['gain_' + t], mm, I); iv = q90(dg)
                ph, dh = bratio(b['hit_' + t], b['dis_' + t], mm, I)
                r[t] = dict(n_days=int(mm.sum()), gain=dict(value=pg, ci90=iv, label=gain_label(iv)),
                            hit_rate=pack(ph, dh))
                if c != REF:
                    ivd = q90(dg - ref_b[t][1])
                    r[t]['gain_minus_regression'] = dict(value=pg - ref_b[t][0], ci90=ivd, label=diff_label(ivd))
            pc, dc = bmean(b['combo_mae'], m, I); ivc = q90(dc - dn)
            r['combination'] = dict(mae=pack(pc, dc), neso_mae=pn, minus_neso=dict(value=pc - pn, ci90=ivc, label=diff_label(ivc)),
                                    ratio_to_neso=pc / pn)
            o['B'][c] = r
        for c in FA:
            cc = P['C'][c]; r = {}
            for t in ('mean', 'peak'):
                for w in ('pair', 'weekday'):
                    mm = m & cc[w]; pv, dv = bmean(cc['same_' + t], mm, I)
                    r[f'{t}_{"all" if w == "pair" else "weekday"}'] = dict(share=pv, ci90=q90(dv), n_pairs=int(mm.sum()))
            o['C'][c] = r
        out[s] = o
    return out


def analyse(frame, t1_days, fa=FA, fb=FB):
    P = per_day(frame, fa, fb)
    days = P['days']
    masks = dict(all=np.ones(len(days), bool),
                 winter=np.array([d.month in (12, 1, 2) for d in P['dates']]),
                 T1=np.isin(days, list(t1_days)))
    I = st.boot_idx(len(days), np.random.default_rng(SEED))
    return P, summarise(P, I, masks)


def write_headline(res):
    a = res['all']; ma = a['A'][CH]['missed_minus_regression']
    g = a['B'][CH]['raw']['gain']; gr = a['B'][REF]['raw']['gain']
    return headline(ma['label'], a['A'][CH]['missed']['value'], a['A'][REF]['missed']['value'],
                    g['label'], g['value'], g['ci90'], gr['value'], gr['ci90'])


# ------------------------------------------------------------------ checks (PLAN.md §7) ------------------------------
def check_invariance(frame, P):
    """Adding a constant leaves part A unchanged; F = y is perfect; F = N gains 0 everywhere."""
    f = frame.copy(); f['_shift'] = f[CH] + 1024.0; f['_perfect'] = f['outturn']; f['_neso'] = f[NESO]
    Q = per_day(f, fa=[CH, '_shift', '_perfect'], fb=['_neso'])
    same = all(np.array_equal(Q['A'][CH][k], Q['A']['_shift'][k]) for k in ('captured', 'missed', 'hits'))
    perfect = bool(np.all(Q['A']['_perfect']['missed'] == 0) and np.all(Q['A']['_perfect']['hits'] == 2 * NPICK))
    zero = bool(np.all(Q['B']['_neso']['gain_raw'] == 0) and np.all(Q['B']['_neso']['dis_raw'] == 0))
    nonneg = bool(min(P['A'][c]['missed'].min() for c in P['A']) >= -1e-9)
    return dict(passed=bool(same and perfect and zero and nonneg), constant_shift_unchanged=bool(same),
                perfect_forecast=perfect, neso_gain_zero=zero, missed_nonnegative=nonneg)


def check_reproduction(P):
    pub = json.load(open(ASY_RESULTS))['means']
    rows, ok = [], True
    for c in FA:
        mine = float(P['A'][c]['mae'][P['ok']].mean()); want = pub[c]['all']['loss']['1']
        good = abs(mine - want) <= 0.01; ok &= good
        rows.append(dict(forecaster=c, computed=mine, asymmetric=want, passed=bool(good)))
    return dict(passed=bool(ok), rows=rows)


def check_alignment(P):
    return dict(passed=bool(P['ok'].all()), n_days=len(P['days']), n_halfhours=int(P['nhh'].sum()),
                days_dropped=[d for d, k in zip(P['days'], P['ok']) if not k])


# ------------------------------------------------------------------ output ---------------------------------------------
def f1(x): return '–' if x is None else f'{x:,.1f}'
def iv1(v): return '–' if not v else f'{v[0]:,.1f} to {v[1]:,.1f}'
def f3(x): return '–' if x is None else f'{x:.3f}'
def iv3(v): return '–' if not v else f'{v[0]:.3f} to {v[1]:.3f}'


def markdown(out, meta):
    L = ['# Arbitrage signal: results (generated by arbitrage/score.py)', '',
         'Exploratory, on committed forecasts (PLAN.md §4). Labels come from unadjusted 90% intervals and are not tests.',
         '', '## Headline (PLAN.md §9)', '', out['headline'], '']
    for s in SETS:
        o = out['sets'][s]
        L += [f'## Set: {s} ({o["n_days"]} days)', '', '### A. Timing: missed spread, MW a day (lower is better)', '',
              '| Forecaster | missed | 90% | capture share | hits of 8 | minus regression | 90% | label |',
              '|---|---|---|---|---|---|---|---|']
        for c in FA:
            a = o['A'][c]; d = a.get('missed_minus_regression')
            L.append(f'| {NAMES[c]} | {f1(a["missed"]["value"])} | {iv1(a["missed"]["ci90"])} | '
                     f'{f3(a["capture_share"]["value"])} | {a["hits"]["value"]:.2f} | '
                     f'{f1(d["value"]) if d else "—"} | {iv1(d["ci90"]) if d else "—"} | {d["label"] if d else "—"} |')
        for t, title in (('raw', 'B. Gain against NESO, MW'), ('bc', 'B. Gain against NESO after bias correction, MW')):
            L += ['', f'### {title}', '', '| Forecaster | days | gain | 90% | label | hit rate | minus regression | 90% | label |',
                  '|---|---|---|---|---|---|---|---|---|']
            for c in FB:
                b = o['B'][c][t]; d = b.get('gain_minus_regression')
                L.append(f'| {NAMES[c]} | {b["n_days"]} | {f1(b["gain"]["value"])} | {iv1(b["gain"]["ci90"])} | '
                         f'{b["gain"]["label"]} | {f3(b["hit_rate"]["value"])} | {f1(d["value"]) if d else "—"} | '
                         f'{iv1(d["ci90"]) if d else "—"} | {d["label"] if d else "—"} |')
        L += ['', '### B. Combination: mean daily error of (forecaster + NESO) / 2, MW', '',
              '| Forecaster | combined | NESO alone | combined minus NESO | 90% | label | ratio |', '|---|---|---|---|---|---|---|']
        for c in FB:
            k = o['B'][c]['combination']
            L.append(f'| {NAMES[c]} | {f1(k["mae"]["value"])} | {f1(k["neso_mae"])} | {f1(k["minus_neso"]["value"])} | '
                     f'{iv1(k["minus_neso"]["ci90"])} | {k["minus_neso"]["label"]} | {f3(k["ratio_to_neso"])} |')
        L += ['', '### C. Day-to-day direction: share of pairs with the right sign', '',
              '| Forecaster | mean, all | mean, weekdays | peak, all | peak, weekdays |', '|---|---|---|---|---|']
        for c in FA:
            r = o['C'][c]
            L.append('| ' + NAMES[c] + ' | ' + ' | '.join(f'{f3(r[k]["share"])} ({iv3(r[k]["ci90"])}; {r[k]["n_pairs"]})'
                                                     for k in ('mean_all', 'mean_weekday', 'peak_all', 'peak_weekday')) + ' |')
        L.append('')
    L += ['## Checks (PLAN.md §7)', ''] + [f'- {k}: {"passed" if v["passed"] else "FAILED"}' for k, v in out['checks'].items()]
    L += ['', f'Commit {meta["public_commit"]}; script SHA-256 {meta["script_sha256"]}; seed {SEED}; {st.B} draws in blocks of {st.BLOCK}.', '']
    return '\n'.join(L)


def real():
    if not os.path.exists(SYNTH_JSON): sys.exit('Refused: run --synthetic first and commit score_synthetic.json.')
    if git('status', '--porcelain', '--', *GUARDED): sys.exit('Refused: these must be committed and unchanged: ' + ', '.join(GUARDED))
    try: tagged = git('show', f'{PLAN_TAG}:arbitrage/PLAN.md')
    except subprocess.CalledProcessError: sys.exit(f'Refused: tag {PLAN_TAG} not found; run git fetch --tags.')
    if tagged != open(os.path.join(HERE, 'PLAN.md')).read().strip(): sys.exit(f'Refused: PLAN.md differs from tag {PLAN_TAG}.')
    sy = json.load(open(SYNTH_JSON))
    if not sy.get('passed') or sy.get('script_sha256') != st.sha(os.path.abspath(__file__)):
        sys.exit('Refused: the synthetic check has not passed with this script.')
    if st.sha(ASY_RESULTS) != ASY_RESULTS_SHA: sys.exit('Refused: asymmetric/results.json differs from its recorded hash.')
    t1, _ = asy.load_inputs()
    frame = asy.load_real()
    P, sets = analyse(frame, t1)
    out = dict(sets=sets)
    out['checks'] = dict(reproduction=check_reproduction(P), alignment=check_alignment(P),
                         invariance=check_invariance(frame, P),
                         hashes=dict(passed=True, note='every file read matched its recorded SHA-256, or the run stops'),
                         synthetic=dict(passed=True, file='arbitrage/score_synthetic.json'))
    out['headline'] = write_headline(sets)
    meta = dict(public_commit=git('rev-parse', 'HEAD'), script_sha256=st.sha(os.path.abspath(__file__)), plan_tag=PLAN_TAG,
                seed=SEED, draws=st.B, block=st.BLOCK, n_pick=NPICK, bias_window_days=[WIN_FROM, WIN_TO],
                versions=dict(python=platform.python_version(), numpy=np.__version__, pandas=pd.__version__))
    res = dict(schema=SCHEMA, note='arbitrage signal; exploratory; plan frozen at tag arbitrage-plan', meta=meta,
               **st.round_floats(out))
    json.dump(res, open(os.path.join(HERE, 'results.json'), 'w'), indent=1)
    md = markdown(res, meta); open(os.path.join(HERE, 'results.md'), 'w').write(md); print(md)
    failed = [k for k, v in out['checks'].items() if not v['passed']]
    if failed: print('CHECKS FAILED: ' + ', '.join(failed)); sys.exit(1)


# ------------------------------------------------------------------ synthetic check (PLAN.md §7.4) -------------------
def synth_frame(grid, seed=11):
    """Invented outturn with a daily cycle and day-to-day level changes; NESO = outturn + noise; forecasters built
    from them with known answers."""
    rng = np.random.default_rng(seed)
    f = grid.sort_values(['day', 'start_utc'], kind='mergesort').reset_index(drop=True)
    pos = f.groupby('day').cumcount().to_numpy(); nday = f.groupby('day')['day'].transform('size').to_numpy()
    days = sorted(f['day'].unique()); code = pd.Categorical(f['day'], categories=days).codes
    level = 25000 + np.cumsum(rng.normal(0, 400, len(days)))[code]
    y = np.round(level + 5000 * np.sin(2 * np.pi * (pos / nday - 0.3)) + rng.normal(0, 150, len(f)))
    N = y + rng.normal(0, 500, len(f))
    out = f[['day', 'start_utc']].copy(); out['outturn'] = y; out[NESO] = N
    out['toward'] = N + 0.5 * (y - N)
    out['away'] = N - 0.5 * (y - N)
    out['noise'] = N + rng.normal(0, 500, len(f))
    out['biased'] = out['toward'] + 300.0
    sh = np.empty(len(f))                                   # outturn two half-hours later within each day
    for d in range(len(days)):
        idx = np.flatnonzero(code == d); sh[idx] = np.roll(y[idx], 2)
    out['shifted'] = sh; out['exact'] = y
    return out


def unit_rules():
    ok, n = True, 0
    for iv, l in (([-2, -1], LOWER), ([1, 2], HIGHER), ([0, 2], NCD), ([-2, 0], NCD), ([-1, 1], NCD)):
        n += 1; ok &= diff_label(iv) == l
    for iv, l in (([-2, -1], NEG), ([1, 2], POS), ([0, 2], NCD0), ([-2, 0], NCD0)):
        n += 1; ok &= gain_label(iv) == l
    want = {
        (LOWER, POS): ("In a backtest it may have seen in training, when choosing a battery's four lowest and four highest "
                       "half-hours, Chronos-2 missed clearly less of each day's demand spread than a weather regression "
                       "(1,234 against 1,300 MW a day). Where it disagreed with NESO's day-ahead forecast, outturn moved "
                       "clearly towards Chronos-2, by 12.3 MW on average (90% interval 4.0 to 20.5); for the regression "
                       "the figure was -40.0 MW (-60.0 to -20.0)."),
        (NCD, NCD0): ("In a backtest it may have seen in training, when choosing a battery's four lowest and four highest "
                      "half-hours, Chronos-2 missed an amount of each day's demand spread not clearly different from a "
                      "weather regression (1,234 against 1,300 MW a day). Where it disagreed with NESO's day-ahead "
                      "forecast, outturn moved neither clearly towards nor away from Chronos-2, by 12.3 MW on average "
                      "(90% interval 4.0 to 20.5); for the regression the figure was -40.0 MW (-60.0 to -20.0)."),
        (HIGHER, NEG): ("In a backtest it may have seen in training, when choosing a battery's four lowest and four highest "
                        "half-hours, Chronos-2 missed clearly more of each day's demand spread than a weather regression "
                        "(1,234 against 1,300 MW a day). Where it disagreed with NESO's day-ahead forecast, outturn moved "
                        "clearly away from Chronos-2, by 12.3 MW on average (90% interval 4.0 to 20.5); for the regression "
                        "the figure was -40.0 MW (-60.0 to -20.0)."),
    }
    for ml in (LOWER, HIGHER, NCD):
        for gl in (POS, NEG, NCD0):
            h = headline(ml, 1234, 1300, gl, 12.34, [4.0, 20.5], -40.0, [-60.0, -20.0]); n += 1
            good = '[' not in h and h.count('Chronos-2') >= 2
            if (ml, gl) in want: good &= h == want[(ml, gl)]
            if not good: print('FAIL headline', ml, gl, '\n', h)
            ok &= good
    return bool(ok), n


def unit_trailing():
    """A spike on day 40 enters the window of days 42 to 59 only; a missing day voids every window that needs it."""
    dates = [pd.Timestamp('2025-01-01') + pd.Timedelta(days=i) for i in range(60)]
    v = np.zeros(60); v[40] = 1000.0
    t = trailing(v, dates)
    good = bool(np.isnan(t[:29]).all() and np.isfinite(t[29:]).all())
    good &= bool(t[40] == 0 and t[41] == 0)                    # never the target day or the day before
    good &= bool(np.allclose(t[42:60], 1000 / 28) and np.all(t[29:42] == 0))
    tg = trailing(np.delete(v, 10), [d for i, d in enumerate(dates) if i != 10])
    good &= bool(np.isnan(tg[11:39]).all() and np.isfinite(tg[39]))
    return good


def synthetic():
    t1, _ = asy.load_inputs()
    grid = pd.read_csv(st.FORECASTS, usecols=['day', 'start_utc'])
    fr = synth_frame(grid)
    res = dict(script_sha256=st.sha(os.path.abspath(__file__)), checks={}); ok_all = True

    def rec(name, good, **info):
        nonlocal ok_all
        res['checks'][name] = dict(passed=bool(good), **info); ok_all &= bool(good)
        print(('PASS ' if good else 'FAIL ') + name, flush=True)

    g, n = unit_rules(); rec('unit_rules', g, n=n)
    rec('unit_trailing', unit_trailing())
    fa = ['exact', 'shifted', 'toward', NESO]; fb = ['toward', 'away', 'noise', 'biased']
    P = per_day(fr, fa=fa, fb=fb)
    I = st.boot_idx(len(P['days']), np.random.default_rng(SEED)); m = P['ok']
    nmae = float(np.mean([P['A'][NESO]['mae'][m]]))
    b = P['B']
    rec('toward_gain_equals_neso_mae', abs(b['toward']['gain_raw'][m].mean() - nmae) < 1e-6
        and b['toward']['hit_raw'][m].sum() == b['toward']['dis_raw'][m].sum(), gain=float(b['toward']['gain_raw'][m].mean()), neso_mae=nmae)
    rec('away_gain_minus_neso_mae', abs(b['away']['gain_raw'][m].mean() + nmae) < 1e-6 and b['away']['hit_raw'][m].sum() == 0)
    _, dn = bmean(b['noise']['gain_raw'], m, I); iv = q90(dn)
    rec('noise_interval_contains_0', iv[0] <= 0 <= iv[1], ci90=iv)
    rec('exact_forecast_perfect', bool(np.all(P['A']['exact']['missed'] == 0) and np.all(P['A']['exact']['hits'] == 8)))
    rec('shift_misses_spread', P['A']['shifted']['missed'][m].mean() > 100, missed=float(P['A']['shifted']['missed'][m].mean()))
    bc_ok = b['biased']['bc_ok'] & m
    same = np.allclose(b['biased']['gain_bc'][bc_ok], b['toward']['gain_bc'][bc_ok], atol=1e-6)
    rec('bias_correction_removes_constant', same and int((~b['biased']['bc_ok']).sum()) == 29
        and abs(b['biased']['gain_raw'][m].mean() - b['toward']['gain_raw'][m].mean()) > 1,
        days_without_window=int((~b['biased']['bc_ok']).sum()))
    fr2 = fr.copy(); fr2['toward_plus'] = fr2['toward'] + 1024.0
    Q = per_day(fr2, fa=['toward', 'toward_plus'], fb=['toward'])
    rec('constant_shift_unchanged', all(np.array_equal(Q['A']['toward'][k], Q['A']['toward_plus'][k]) for k in ('captured', 'hits')))
    # the full pipeline and headline on a frame shaped like the real one
    fr3 = fr.copy()
    for c, src in ((REF, 'noise'), (CH, 'toward'), (V1, 'away'), (S1, 'noise'), (TFM, 'shifted'), (AVG, 'biased')): fr3[c] = fr3[src]
    P3, sets = analyse(fr3, t1)
    h = write_headline(sets)
    a = sets['all']
    rec('pipeline_and_headline', a['B'][CH]['raw']['gain']['label'] == POS and a['B'][V1]['raw']['gain']['label'] == NEG
        and a['A'][TFM]['missed_minus_regression']['label'] == HIGHER and 'clearly towards Chronos-2' in h
        and check_invariance(fr3, P3)['passed'] and check_alignment(P3)['passed'] and sets['T1']['n_days'] == 96,
        headline=h)
    res['passed'] = bool(ok_all)
    json.dump(st.round_floats(res), open(SYNTH_JSON, 'w'), indent=1, default=str)
    print('synthetic: ' + ('PASS' if ok_all else 'FAIL'))
    return ok_all


if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('--synthetic', action='store_true')
    if ap.parse_args().synthetic: sys.exit(0 if synthetic() else 1)
    real()
