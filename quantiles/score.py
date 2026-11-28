"""
The quantile study, stage 1: the backtest pilot (quantiles/PLAN.md, frozen at tag quantiles-plan). Committed before it
runs; its synthetic output is committed next, and only then does it score.

For: a reviewer checking that the dressing, the scores, the ratios, the labels, the calibration, the width test, the
sets, the stage 2 power estimate, the checks and the headline follow PLAN.md §6 to §10.

Reads, after checking every hash:
  forecasts   the imbalance study's loader (imbalance_cost/score.py, load_real), imported unchanged: outturn,
              chronos2_A (Chronos-2's median), neso and regression_weather, with the tails study's hash checks inside
  quantiles   quantiles/backtest_quantiles.csv and backtest_check.csv, whose hashes must match backtest_manifest.json,
              whose own hash is recorded below
  T1          tails/days.csv, through the same loader; calendar days by imbalance_cost/worst_days.py's day_flags and
              its hash-checked holiday file, imported unchanged
Writes quantiles/results_stage1.json and results_stage1.md.

Definitions (PLAN.md §6, §7). y is outturn, q_t the forecast at level t, in MW.
  pinball      t(y - q_t) if y >= q_t, else (1 - t)(q_t - y)
  score        mean pinball over the 17 levels 0.10 to 0.90 (primary); full score over all 21 levels
  day, study   a day's score is the mean over its half-hours; the study's figure is the mean over days
  ratio        Chronos-2's total of daily scores over a dressed forecaster's, over the same days
  dressing     forecast + the level's quantile of the forecaster's errors (outturn - forecast) on the latest W days
               on or before D - 2 with a complete forecast and outturn, in the half-hour's block of the day (UK local
               start time); NumPy's default interpolation; a day with fewer than 28 such days is not scored.
               Primary W = 56, 4 blocks; variants (28, 4), (90, 4), (56, 2), (56, 8)
  crossing     Chronos-2's 21 values in each half-hour are sorted before scoring; raw results are reported too
A day is scored if outturn, Chronos-2's quantiles and median, NESO and the regression cover all its half-hours, and
every dressed forecaster has at least 28 days in its window. Others are listed.

Labels (§7). Ratios: clearly lower / clearly higher / not clearly different, from the 90% interval against 1; practically
lower (< 0.95) / higher (> 1.05) / equal, from the point ratio. Coverage: too narrow / too wide / consistent with its
level, from the 90% interval against nominal; practically consistent within 3 points (80% interval) or 1 point (98%
interval) of nominal, else practically too narrow or too wide. Anything that cannot be computed is "undefined".
Intervals: the tails study's 7-day moving-block bootstrap over scored days, 2,000 draws, seed 20261129, the same draws
throughout. The stage 2 power estimate draws its windows from the generator seeded with (20261129, 1).

Modes:
    python quantiles/score.py --synthetic   invented outturn, forecasts and quantiles with known answers on the real
                                            calendar; writes quantiles/score_synthetic.json; exits 1 on any failure
    python quantiles/score.py               stage 1. Refused unless the synthetic check passed with this script, the
                                            guarded files are committed and unchanged, PLAN.md matches the tag
                                            quantiles-plan, and check 1 finds no mismatched day.
Stage 2's loading of the live quantiles is added before stage 2 runs, recorded in quantiles/REVISIONS.md (§11).
"""
import argparse, importlib.util, json, os, platform, subprocess, sys
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
_spec = importlib.util.spec_from_file_location('worst_days', os.path.join(ROOT, 'imbalance_cost', 'worst_days.py'))
wd = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(wd)        # imported unchanged
ic = wd.sc                                                                        # imbalance_cost/score.py, unchanged
asy, st = ic.asy, ic.st

PLAN_TAG, SEED, SCHEMA = 'quantiles-plan', 20261129, 1
CH, NESO, REF = 'chronos2_A', 'neso', 'regression_weather'
GRID = [0.01, 0.05] + [round(0.1 + 0.05 * i, 2) for i in range(17)] + [0.95, 0.99]
QCOLS = [f'q{int(round(q * 100)):02d}' for q in GRID]
CENTRAL = [i for i, q in enumerate(GRID) if 0.10 - 1e-9 <= q <= 0.90 + 1e-9]          # 17 levels
I10, I50, I90, I01, I99 = (GRID.index(q) for q in (0.10, 0.5, 0.90, 0.01, 0.99))
K_LEVELS = {1: 0.5, 3: 0.75, 4: 0.8, 9: 0.9}
DRESSED = {'chronos2_dressed': CH, 'neso_dressed': NESO, 'regression_dressed': REF}
NAMES = {'chronos2_quantiles': "Chronos-2's quantiles", 'chronos2_quantiles_raw': "Chronos-2's quantiles, unsorted",
         'chronos2_dressed': "Chronos-2's median, dressed", 'neso_dressed': "NESO's forecast, dressed",
         'regression_dressed': "The weather regression, dressed"}
PRIMARY, VARIANTS = (56, 4), [(56, 4), (28, 4), (90, 4), (56, 2), (56, 8)]
MIN_DAYS, PRACTICAL, BAR = 28, 0.05, 0.9
COVERAGE = {'80': (I10, I90, 0.80, 0.03), '98': (I01, I99, 0.98, 0.01)}
EVE_FROM, EVE_TO, TZ = ic.EVE_FROM, ic.EVE_TO, 'Europe/London'
EXACT, CLOSE = 0.001, 0.01
QFILE = os.path.join(HERE, 'backtest_quantiles.csv')
QCHECK = os.path.join(HERE, 'backtest_check.csv')
QMANIFEST = os.path.join(HERE, 'backtest_manifest.json')
QMANIFEST_SHA = '704dc496cd4b96eb25a2e4c447c6c95731a3a00f92b7a1df84e991f8aad3a21f'
ARB_RESULTS, ARB_RESULTS_SHA = ic.ARB_RESULTS, ic.ARB_RESULTS_SHA
SYNTH_JSON = os.path.join(HERE, 'score_synthetic.json')
GUARDED = ['quantiles/score.py', 'quantiles/PLAN.md', 'quantiles/score_synthetic.json', 'quantiles/backtest_quantiles.csv',
           'quantiles/backtest_check.csv', 'quantiles/backtest_manifest.json', 'imbalance_cost/worst_days.py'] + ic.GUARDED
POWER_WINDOWS, POWER_DAYS = 500, 130
LOWER, HIGHER, NCD, UNDEF = 'clearly lower', 'clearly higher', 'not clearly different', 'undefined'
P_LOWER, P_HIGHER, P_EQUAL = 'practically lower', 'practically higher', 'practically equal'
NARROW, WIDE, CONSISTENT = 'too narrow', 'too wide', 'consistent with its level'
P_CONS, P_NARROW, P_WIDE = 'practically consistent', 'practically too narrow', 'practically too wide'


def git(*a):
    return subprocess.run(['git', '-C', ROOT, *a], capture_output=True, text=True, check=True).stdout.strip()


# ------------------------------------------------------------------ labels (PLAN.md §7) --------------------------------
def ratio_label(iv):
    if iv is None: return UNDEF
    return LOWER if iv[1] < 1 else HIGHER if iv[0] > 1 else NCD


def practical_label(r):
    if r is None or not np.isfinite(r): return UNDEF
    return P_LOWER if r < 1 - PRACTICAL else P_HIGHER if r > 1 + PRACTICAL else P_EQUAL


def coverage_label(iv, nominal):
    if iv is None: return UNDEF
    return NARROW if iv[1] < nominal else WIDE if iv[0] > nominal else CONSISTENT


def coverage_practical(c, nominal, tol):
    if c is None or not np.isfinite(c): return UNDEF
    return P_NARROW if c < nominal - tol - 1e-12 else P_WIDE if c > nominal + tol + 1e-12 else P_CONS


def q90(x):
    x = np.asarray(x, float); x = x[np.isfinite(x)]
    return [float(v) for v in np.quantile(x, [0.05, 0.95])] if len(x) else None


def ratio_result(num, den, M, I):
    """num, den: per scored day; M: set mask over scored days; I: bootstrap indices. Ratio of totals."""
    with np.errstate(invalid='ignore', divide='ignore'):
        a, b = float(num[M].sum()), float(den[M].sum())
        r = a / b if b > 0 else None
        W = M[I]; draws = np.where(W, num[I], 0).sum(1) / np.where(W, den[I], 0).sum(1)
    iv = q90(draws) if r is not None else None
    return dict(value=r, ci90=iv, label=ratio_label(iv), practical=practical_label(r),
                credibly_below_bar=bool(iv is not None and iv[1] < BAR))


def is_gain(res): return res['label'] == LOWER and res['practical'] == P_LOWER


# ------------------------------------------------------------------ building blocks -------------------------------------
def pinball(y, Q, levels=GRID):
    t = np.asarray(levels)[None, :]; d = y[:, None] - Q
    return np.where(d >= 0, t * d, (t - 1) * d)


def prepare(frame, qdf):
    """One row per half-hour, sorted; the quantiles merged on start time; per-day validity and indices."""
    f = frame.sort_values(['day', 'start_utc'], kind='mergesort').reset_index(drop=True)
    q = qdf.rename(columns={'day': 'qday'})
    f['_t'] = pd.to_datetime(f['start_utc'], utc=True); q['_t'] = pd.to_datetime(q['start_utc'], utc=True)
    n0 = len(f); f = f.merge(q[['_t', 'qday'] + QCOLS], on='_t', how='left', validate='one_to_one'); assert len(f) == n0
    days = sorted(f['day'].unique()); n = len(days)
    code = pd.Categorical(f['day'], categories=days).codes
    loc = f['_t'].dt.tz_convert(TZ); mins = (loc.dt.hour * 60 + loc.dt.minute).to_numpy()
    y = f['outturn'].to_numpy(float)
    Qraw = f[QCOLS].to_numpy(float); Qs = np.sort(Qraw, axis=1)
    nhh = np.bincount(code, minlength=n); exp = asy.expected_hh(days)
    bad = lambda v: np.bincount(code, weights=(~np.isfinite(v)).astype(float), minlength=n) > 0
    full = nhh == exp
    complete = {c: full & ~bad(y) & ~bad(f[c].to_numpy(float)) for c in (CH, NESO, REF)}
    q_ok = full & ~bad(Qraw.sum(1))
    starts = np.r_[0, np.flatnonzero(np.diff(code)) + 1]; stops = np.r_[starts[1:], len(f)]
    return dict(f=f, days=days, dates=[pd.Timestamp(d) for d in days], code=code, mins=mins, y=y, Qraw=Qraw, Qs=Qs,
                med={c: f[c].to_numpy(float) for c in (CH, NESO, REF)}, nhh=nhh, exp=exp, complete=complete, q_ok=q_ok,
                rows=[np.arange(a, b) for a, b in zip(starts, stops)])


def blocks_of(mins, nb): return (mins // (1440 // nb)).astype(int)


def dress_day(i, err, rows, dates, complete, blk, nb, W):
    """Error quantiles (nb x 21) for day i from the latest W complete days on or before D - 2; None if fewer than 28."""
    cut = dates[i] - pd.Timedelta(days=2)
    window = [j for j in range(i - 1, -1, -1) if complete[j] and dates[j] <= cut][:W]
    if len(window) < MIN_DAYS: return None
    idx = np.concatenate([rows[j] for j in window])
    e, b = err[idx], blk[idx]
    out = np.empty((nb, len(GRID)))
    for k in range(nb):
        v = e[b == k]
        if len(v) == 0: return None
        out[k] = np.quantile(v, GRID)
    return out


def dress(S, c, nb, W):
    """Dressed quantiles for every half-hour of every day that can be dressed; NaN elsewhere."""
    err = S['y'] - S['med'][c]; blk = blocks_of(S['mins'], nb)
    Q = np.full((len(err), len(GRID)), np.nan); ok = np.zeros(len(S['days']), bool)
    for i, r in enumerate(S['rows']):
        E = dress_day(i, err, S['rows'], S['dates'], S['complete'][c], blk, nb, W)
        if E is None: continue
        Q[r] = S['med'][c][r][:, None] + E[blk[r]]; ok[i] = True
    return Q, ok


def daysums(code, n, V, hm):
    """Per-day sums of the columns of V over the half-hours in mask hm, and the count of those half-hours."""
    cnt = np.bincount(code[hm], minlength=n).astype(float)
    if V.ndim == 1: return np.bincount(code[hm], weights=V[hm], minlength=n), cnt
    return np.stack([np.bincount(code[hm], weights=V[hm, j], minlength=n) for j in range(V.shape[1])], 1), cnt


# ------------------------------------------------------------------ measures -------------------------------------------
def scores_by_day(S, Q, sel, hm):
    """Per scored day: mean pinball per level over the half-hours in hm (days x 21)."""
    P = pinball(S['y'], np.nan_to_num(Q))
    s, cnt = daysums(S['code'], len(S['days']), P, hm)
    with np.errstate(invalid='ignore', divide='ignore'): per = s / cnt[:, None]
    return per[sel]


def measure_a(PL, M, I):
    """PL: forecaster -> (scored days x 21) mean pinball. Primary and full scores, both ratios, named and per level."""
    sc = {k: dict(central=v[:, CENTRAL].mean(1), full=v.mean(1)) for k, v in PL.items()}
    out = dict(scores_mw={k: dict(primary=float(v['central'][M].mean()), full=float(v['full'][M].mean()))
                          for k, v in sc.items()}, ratios={})
    C = 'chronos2_quantiles'
    for ref in ('chronos2_dressed', 'neso_dressed', 'regression_dressed'):
        r = dict(primary=ratio_result(sc[C]['central'], sc[ref]['central'], M, I),
                 full=ratio_result(sc[C]['full'], sc[ref]['full'], M, I))
        if 'chronos2_quantiles_raw' in sc:
            r['primary_raw'] = ratio_result(sc['chronos2_quantiles_raw']['central'], sc[ref]['central'], M, I)
        r['named'] = {f'k={k}': dict(level=t, **ratio_result(PL[C][:, GRID.index(t)], PL[ref][:, GRID.index(t)], M, I))
                      for k, t in K_LEVELS.items()}
        r['by_level'] = {QCOLS[j]: ratio_result(PL[C][:, j], PL[ref][:, j], M, I) for j in range(len(GRID))}
        out['ratios'][ref] = r
    prim = [out['ratios'][ref]['primary'] for ref in ('chronos2_dressed', 'neso_dressed')]
    named = [out['ratios'][ref]['named'][k] for ref in ('chronos2_dressed', 'neso_dressed') for k in out['ratios'][ref]['named']]
    allten = prim + named
    out['count_of_ten'] = dict(clearly_lower=sum(x['label'] == LOWER for x in allten),
                               clearly_higher=sum(x['label'] == HIGHER for x in allten),
                               not_clearly_different=sum(x['label'] == NCD for x in allten))
    return out


def calibration(S, Qs, sel, hm, M, I, blocks=None):
    """Share at or below each level; coverage and width of the 80% and 98% intervals; by block of the day."""
    n = len(S['days']); y = S['y']; Qn = np.nan_to_num(Qs)
    below, cnt = daysums(S['code'], n, (y[:, None] <= Qn).astype(float), hm)
    out = dict(share_at_or_below={QCOLS[j]: dict(level=GRID[j], value=float(below[sel][M, j].sum() / cnt[sel][M].sum()))
                                  for j in range(len(GRID))}, intervals={})
    for name, (lo, hi, nom, tol) in COVERAGE.items():
        cov = ((Qn[:, lo] <= y) & (y <= Qn[:, hi])).astype(float); wid = Qn[:, hi] - Qn[:, lo]
        cs, _ = daysums(S['code'], n, cov, hm); ws, _ = daysums(S['code'], n, wid, hm)
        cs, ws, cn = cs[sel], ws[sel], cnt[sel]
        c = float(cs[M].sum() / cn[M].sum()) if cn[M].sum() else None
        W = M[I]; draws = np.where(W, cs[I], 0).sum(1) / np.where(W, cn[I], 0).sum(1)
        iv = q90(draws) if c is not None else None
        res = dict(nominal=nom, coverage=c, ci90=iv, label=coverage_label(iv, nom), practical=coverage_practical(c, nom, tol),
                   mean_width_mw=float(ws[M].sum() / cn[M].sum()) if c is not None else None)
        if blocks is not None:
            blk = blocks_of(S['mins'], 4); byb = {}
            for k in range(4):
                bs, bn = daysums(S['code'], n, cov, hm & (blk == k))
                bs, bn = bs[sel], bn[sel]
                byb[f'block_{k}'] = float(bs[M].sum() / bn[M].sum()) if bn[M].sum() else None
            gaps = [abs(v - nom) for v in byb.values() if v is not None]
            res['by_block'] = byb; res['largest_block_gap'] = float(max(gaps)) if gaps else None
        out['intervals'][name] = res
    return out


def spearman(a, b):
    a, b = pd.Series(a), pd.Series(b)
    if len(a) < 3 or a.nunique() < 2 or b.nunique() < 2: return None
    return float(a.rank().corr(b.rank()))


def width_test(width, err, dates, I, by_month=True):
    """Measure C: days split into four equal groups by width (within each month, or over the whole year); the
    median's mean daily error per group, widest over narrowest with its interval; Spearman correlation."""
    width, err = np.asarray(width, float), np.asarray(err, float); n = len(width)
    group = np.empty(n, int)
    keys = [f'{d:%Y-%m}' for d in dates] if by_month else ['all'] * n
    for k in sorted(set(keys)):
        ix = np.array([i for i in range(n) if keys[i] == k])
        r = pd.Series(width[ix]).rank(method='first').to_numpy() - 1
        group[ix] = np.minimum((4 * r / len(ix)).astype(int), 3)
    means = [float(err[group == g].mean()) if (group == g).any() else None for g in range(4)]
    hi, lo = group == 3, group == 0
    r = means[3] / means[0] if means[0] and means[3] is not None else None
    draws = np.where(hi[I], err[I], 0).sum(1) / np.maximum(hi[I].sum(1), 1) / \
            (np.where(lo[I], err[I], 0).sum(1) / np.maximum(lo[I].sum(1), 1))
    out = dict(group_mean_error_mw=means, widest_over_narrowest=r, ci90=q90(draws) if r is not None else None)
    if by_month:
        rho = {}
        for k in sorted(set(keys)):
            ix = [i for i in range(n) if keys[i] == k]
            if len(ix) >= 20: rho[k] = spearman(width[ix], err[ix])
        v = [x for x in rho.values() if x is not None]
        out.update(spearman_by_month=rho, spearman_median=float(np.median(v)) if v else None,
                   months_positive=int(sum(x > 0 for x in v)), months=len(v))
    else:
        out['spearman'] = spearman(width, err)
    return out


def power_estimate(num, den, season, rng):
    """§9 stage 2: 130-day windows drawn from the season's days by the 7-day block bootstrap; per window, the ratio and
    its 90% interval; the smallest true difference in the ratio labelled clearly different in at least half the
    windows. Scaling Chronos-2's scores by k scales a window's ratio and interval by k, so each window is bootstrapped
    once and every candidate difference is read from it."""
    ix = np.flatnonzero(season)
    if len(ix) < POWER_DAYS: return None
    a, b = num[ix], den[ix]; R = a.sum() / b.sum()
    starts = rng.integers(0, len(ix) - st.BLOCK + 1, size=(POWER_WINDOWS, int(np.ceil(POWER_DAYS / st.BLOCK))))
    win = (starts[:, :, None] + np.arange(st.BLOCK)).reshape(POWER_WINDOWS, -1)[:, :POWER_DAYS]
    lo, hi = np.empty(POWER_WINDOWS), np.empty(POWER_WINDOWS)
    for w in range(POWER_WINDOWS):
        aw, bw = a[win[w]], b[win[w]]
        Iw = st.boot_idx(POWER_DAYS, rng)
        d = aw[Iw].sum(1) / bw[Iw].sum(1); lo[w], hi[w] = np.quantile(d, [0.05, 0.95])
    grid = np.round(np.arange(0.0, 0.5001, 0.005), 3); res = {}
    for side, sign in (('lower', -1), ('higher', 1)):
        found = None
        for dlt in grid:
            k = (1 + sign * dlt) / R
            rate = float(np.mean(k * hi < 1)) if sign < 0 else float(np.mean(k * lo > 1))
            if rate >= 0.5: found = float(dlt); break
        res[side] = found
    return dict(smallest_detectable_difference=res, windows=POWER_WINDOWS, window_days=POWER_DAYS, season_days=int(len(ix)))


# ------------------------------------------------------------------ the analysis ---------------------------------------
def analyse(S, t1_days, holidays, power=True):
    n = len(S['days'])
    dressed = {}
    for nb_w in VARIANTS:
        W, nb = nb_w
        dressed[nb_w] = {k: dress(S, c, nb, W) for k, c in DRESSED.items()}
    ok = S['q_ok'] & S['complete'][CH] & S['complete'][NESO] & S['complete'][REF]
    for nb_w in VARIANTS:
        for k in DRESSED: ok &= dressed[nb_w][k][1]
    sel = np.flatnonzero(ok); days = [S['days'][i] for i in sel]; dates = [S['dates'][i] for i in sel]
    I = st.boot_idx(len(sel), np.random.default_rng(SEED))
    hm_all = np.ones(len(S['y']), bool); hm_eve = (S['mins'] >= EVE_FROM) & (S['mins'] <= EVE_TO)
    flags = wd.day_flags(S['days'], S['nhh'], holidays, t1_days)
    D = pd.DatetimeIndex(dates)
    masks = {'all': np.ones(len(sel), bool), 'T1': np.isin(days, list(t1_days)),
             'winter': D.month.isin([12, 1, 2]), 'evenings': np.ones(len(sel), bool),
             'calendar': flags['calendar'][sel],
             'stage2_season': ((D.month == 11) & (D.day >= 20)) | D.month.isin([12, 1, 2, 3])}
    masks = {k: np.asarray(v, bool) for k, v in masks.items()}
    Qp = {'chronos2_quantiles': S['Qs'], 'chronos2_quantiles_raw': S['Qraw']}
    Qp.update({k: dressed[PRIMARY][k][0] for k in DRESSED})
    out = dict(n_days_scored=int(len(sel)), days_not_scored=[S['days'][i] for i in np.flatnonzero(~ok)], sets={})
    PL = {k: scores_by_day(S, Q, sel, hm_all) for k, Q in Qp.items()}
    PLe = {k: scores_by_day(S, Q, sel, hm_eve) for k, Q in Qp.items()}
    for name, M in masks.items():
        P_ = PLe if name == 'evenings' else PL; hm = hm_eve if name == 'evenings' else hm_all
        a = measure_a(P_, M, I)
        cal = {k: calibration(S, Qp[k], sel, hm, M, I, blocks=(name == 'all'))
               for k in ('chronos2_quantiles', 'chronos2_dressed', 'neso_dressed', 'regression_dressed')}
        out['sets'][name] = dict(n_days=int(M.sum()), A=a, B=cal)
    # robustness to the dressing (§7 A)
    rob = {}
    M = masks['all']; C = PL['chronos2_quantiles'][:, CENTRAL].mean(1)
    for W, nb in VARIANTS:
        r = {}
        for k in ('chronos2_dressed', 'neso_dressed'):
            Pv = scores_by_day(S, dressed[(W, nb)][k][0], sel, hm_all)[:, CENTRAL].mean(1)
            r[k] = ratio_result(C, Pv, M, I)
        rob[f'W{W}_blocks{nb}'] = r
    out['robustness'] = dict(variants=rob, robust={k: len({(v[k]['label'], v[k]['practical']) for v in rob.values()}) == 1
                                                   for k in ('chronos2_dressed', 'neso_dressed')})
    # measure C (§7 C)
    y = S['y']; rows = [S['rows'][i] for i in sel]
    width = np.array([np.mean(S['Qs'][r, I90] - S['Qs'][r, I10]) for r in rows])
    err = np.array([np.mean(np.abs(y[r] - S['med'][CH][r])) for r in rows])
    Qd = dressed[PRIMARY]['chronos2_dressed'][0]
    width_d = np.array([np.mean(Qd[r, I90] - Qd[r, I10]) for r in rows])
    out['C'] = dict(chronos2_within_month=width_test(width, err, dates, I),
                    dressed_median_within_month=width_test(width_d, err, dates, I),
                    chronos2_whole_year_not_interpreted=width_test(width, err, dates, I, by_month=False),
                    dressed_median_whole_year_not_interpreted=width_test(width_d, err, dates, I, by_month=False))
    # crossing and sorting
    cross = (np.diff(S['Qraw'], axis=1) < 0).any(1)
    moved50 = np.flatnonzero(S['Qs'][:, I50] != S['Qraw'][:, I50])
    scored_hh = np.concatenate(rows); in_scored = set(scored_hh.tolist())
    out['crossing'] = dict(halfhours_sorted=int(cross[scored_hh].sum()),
                           largest_move_mw=float(np.max(np.abs(S['Qs'][scored_hh] - S['Qraw'][scored_hh]))),
                           median_moved=[dict(day=str(S['f']['day'].iloc[i]), start_utc=str(S['f']['start_utc'].iloc[i]))
                                         for i in moved50 if i in in_scored])
    # stage 2 power (§9)
    if power:
        rng = np.random.default_rng([SEED, 1]); season = masks['stage2_season']
        out['stage2_power'] = {k: power_estimate(C, PL[k][:, CENTRAL].mean(1), season, rng)
                               for k in ('chronos2_dressed', 'neso_dressed')}
    out['headline'] = headline(out['sets']['all'])
    return out, dict(sel=sel, dressed=dressed, I=I, masks=masks)


# ------------------------------------------------------------------ headline (PLAN.md §10) -----------------------------
CLEAR_WORDS = {LOWER: 'clearly less than', HIGHER: 'clearly more than', NCD: 'not clearly different from'}
COV_WORDS = {NARROW: 'too narrow', WIDE: 'too wide', CONSISTENT: 'consistent with their level'}


def headline(s):
    a = s['A']; r1 = a['ratios']['chronos2_dressed']['primary']; r2 = a['ratios']['neso_dressed']['primary']
    cov = s['B']['chronos2_quantiles']['intervals']['80']
    labels = [r1['label'], r1['practical'], r2['label'], r2['practical'], cov['label'], cov['practical']]
    if UNDEF in labels: return 'Headline undefined: ' + ', '.join(l for l in labels)
    x, yv = a['scores_mw']['chronos2_quantiles']['primary'], a['scores_mw']['chronos2_dressed']['primary']
    f3 = lambda v: f'{v:.3f}'
    return (f"In a backtest the foundation model may have seen in training, a day-ahead position on GB demand set from "
            f"Chronos-2's quantile forecasts, averaged with equal weight over quantile levels 0.10 to 0.90 (cost ratios from "
            f"1:9 to 9:1), cost {CLEAR_WORDS[r1['label']]} one set from its own median with a band built from its recent "
            f"errors (score {x:,.0f} against {yv:,.0f} MW, ratio {f3(r1['value'])}, 90% interval {f3(r1['ci90'][0])} to "
            f"{f3(r1['ci90'][1])}; {r1['practical']}), and {CLEAR_WORDS[r2['label']]} one set from NESO's forecast with a "
            f"band built the same way (ratio {f3(r2['value'])}, 90% interval {f3(r2['ci90'][0])} to {f3(r2['ci90'][1])}; "
            f"{r2['practical']}). Chronos-2's 80% intervals contained outturn {100 * cov['coverage']:.1f}% of the time "
            f"({COV_WORDS[cov['label']]}; {cov['practical']}).")


# ------------------------------------------------------------------ checks (PLAN.md §8) --------------------------------
def check_quantile_files():
    if st.sha(QMANIFEST) != QMANIFEST_SHA: sys.exit('Refused: backtest_manifest.json differs from its recorded hash.')
    man = json.load(open(QMANIFEST))
    for f, h in man['files_sha256'].items():
        if st.sha(os.path.join(HERE, f)) != h: sys.exit(f'Refused: {f} differs from backtest_manifest.json.')
    return man


def check_medians(S, qcheck):
    """Check 1: each day's raw 0.5 quantile against the scored chronos2_A forecast, recomputed here."""
    rows = []
    for i, r in enumerate(S['rows']):
        q, m = S['Qraw'][r, I50], S['med'][CH][r]
        dev = float(np.max(np.abs(q - m))) if np.isfinite(q).all() and np.isfinite(m).all() else float('inf')
        rows.append(dict(day=S['days'][i], max_abs_diff_mw=dev,
                         category='exact' if dev <= EXACT else 'close' if dev <= CLOSE else 'mismatched'))
    cats = pd.DataFrame(rows)
    counts = {c: int((cats['category'] == c).sum()) for c in ('exact', 'close', 'mismatched')}
    agree = qcheck.set_index('day')['category'].reindex(cats['day']).fillna('missing').tolist() == cats['category'].tolist()
    return dict(passed=bool(counts['mismatched'] == 0 and agree), counts=counts, agrees_with_backtest_check=bool(agree),
                largest_difference_mw=float(cats['max_abs_diff_mw'].replace(np.inf, np.nan).max()),
                close_days=cats.loc[cats['category'] == 'close', 'day'].tolist(),
                mismatched_days=cats.loc[cats['category'] == 'mismatched', 'day'].tolist())


def check_reproduction(frame):
    """Check 2: the medians' mean daily errors against the arbitrage study's (checkpoint 0's) figures, to 0.01 MW."""
    arb = json.load(open(ARB_RESULTS))['sets']['all']['A']; f = frame.sort_values(['day', 'start_utc']); rows, ok = [], True
    for c in (CH, NESO, REF):
        mine = float(f.assign(e=(f['outturn'] - f[c]).abs()).groupby('day')['e'].mean().mean())
        want = arb[c]['mae']['value']; good = abs(mine - want) <= 0.01; ok &= good
        rows.append(dict(forecaster=c, computed=mine, recorded=want, passed=bool(good)))
    return dict(passed=bool(ok), rows=rows)


def check_lookahead(S, every=96):
    """Check 3: changing outturn on D - 1 or later leaves D's dressed quantiles unchanged (primary dressing)."""
    W, nb = PRIMARY; blk = blocks_of(S['mins'], nb); ok, tried = True, 0
    for c in (CH, NESO, REF):
        err = S['y'] - S['med'][c]
        for i in range(MIN_DAYS + 2, len(S['days']), every):
            E0 = dress_day(i, err, S['rows'], S['dates'], S['complete'][c], blk, nb, W)
            if E0 is None: continue
            e2 = err.copy(); late = np.concatenate([S['rows'][j] for j in range(len(S['days']))
                                                     if S['dates'][j] >= S['dates'][i] - pd.Timedelta(days=1)])
            e2[late] += 1e5
            E1 = dress_day(i, e2, S['rows'], S['dates'], S['complete'][c], blk, nb, W)
            ok &= E1 is not None and np.array_equal(E0, E1); tried += 1
    return dict(passed=bool(ok and tried > 0), days_tried=tried)


def check_arithmetic(S, sel):
    rows = [S['rows'][i] for i in sel]
    counts = bool(np.all(S['nhh'][sel] == S['exp'][sel]))
    y = S['y']; Y = np.repeat(y[:, None], len(GRID), 1)
    zero = bool(np.all(pinball(y, Y) == 0))
    half = max(abs(2 * np.mean(pinball(y[r], S['Qraw'][r][:, [I50]], [0.5])) - np.mean(np.abs(y[r] - S['Qraw'][r, I50])))
               for r in rows)
    uncrossed = ~(np.diff(S['Qraw'], axis=1) < 0).any(1)
    same = bool(np.array_equal(S['Qs'][uncrossed], S['Qraw'][uncrossed]))
    return dict(passed=bool(counts and zero and half <= 1e-9 and same), halfhour_counts_match=counts, exact_scores_zero=zero,
                half_level_is_half_mae_max_gap=float(half), sorting_leaves_uncrossed=same)


# ------------------------------------------------------------------ loading and output ---------------------------------
def load_real():
    man = check_quantile_files()
    if st.sha(ARB_RESULTS) != ARB_RESULTS_SHA: sys.exit('Refused: arbitrage/results.json differs from its recorded hash.')
    frame, _, _, t1 = ic.load_real()                         # hashes checked inside
    q = pd.read_csv(QFILE, dtype={'day': str}); qc = pd.read_csv(QCHECK, dtype={'day': str})
    return frame, q, qc, man, t1, wd.load_holidays()


def fr(v, d=3): return '–' if v is None else f'{v:.{d}f}'
def fiv(v, d=3): return '–' if not v else f'{v[0]:.{d}f} to {v[1]:.{d}f}'


def markdown(res):
    L = ['# Quantile study, stage 1 (backtest pilot): results (generated by quantiles/score.py)', '',
         'A pilot on days the foundation model may have seen in training (PLAN.md §5). Labels come from unadjusted 90% '
         'intervals and are not tests. Lower scores are better.', '', '## Headline (PLAN.md §10)', '', res['headline'], '',
         f'Days scored: {res["n_days_scored"]}; not scored: {len(res["days_not_scored"])} '
         f'(first and last: {", ".join(res["days_not_scored"][:3])} … {", ".join(res["days_not_scored"][-3:])}).', '']
    for name, s in res['sets'].items():
        a = s['A']
        L += [f'## Set: {name} ({s["n_days"]} days)', '', '| Forecaster | score, 0.10–0.90 (MW) | full score (MW) |', '|---|---|---|']
        for k, v in a['scores_mw'].items(): L.append(f'| {NAMES[k]} | {v["primary"]:,.1f} | {v["full"]:,.1f} |')
        L += ['', '| Chronos-2 against | ratio (90%) | label | practical | full-score ratio | unsorted |', '|---|---|---|---|---|---|']
        for ref, r in a['ratios'].items():
            p = r['primary']
            L.append(f'| {NAMES[ref]} | {fr(p["value"])} ({fiv(p["ci90"])}) | {p["label"]} | {p["practical"]} | '
                     f'{fr(r["full"]["value"])} | {fr(r.get("primary_raw", {}).get("value"))} |')
        L += ['', '| Named cost ratio | level | against dressed median | against dressed NESO |', '|---|---|---|---|']
        for k in a['ratios']['chronos2_dressed']['named']:
            u, v = a['ratios']['chronos2_dressed']['named'][k], a['ratios']['neso_dressed']['named'][k]
            L.append(f'| {k} | {u["level"]:.2f} | {fr(u["value"])} ({u["label"]}; {u["practical"]}) | '
                     f'{fr(v["value"])} ({v["label"]}; {v["practical"]}) |')
        c = a['count_of_ten']
        L += ['', f'Of the ten primary comparisons: {c["clearly_lower"]} clearly lower, {c["clearly_higher"]} clearly higher, '
              f'{c["not_clearly_different"]} not clearly different.', '',
              '| Forecaster | 80% coverage (90%) | label | practical | width (MW) | 98% coverage | label | practical |',
              '|---|---|---|---|---|---|---|---|']
        for k, b in s['B'].items():
            i8, i9 = b['intervals']['80'], b['intervals']['98']
            L.append(f'| {NAMES[k]} | {fr(i8["coverage"])} ({fiv(i8["ci90"])}) | {i8["label"]} | {i8["practical"]} | '
                     f'{fr(i8["mean_width_mw"], 0)} | {fr(i9["coverage"])} | {i9["label"]} | {i9["practical"]} |')
        L += ['', "The dressed bands' 98% coverage is reported, not interpreted (PLAN.md §7 B).", '']
    L += ['## By level, all days', '', '| Level | against dressed median | against dressed NESO |', '|---|---|---|']
    a = res['sets']['all']['A']
    for q in QCOLS:
        u, v = a['ratios']['chronos2_dressed']['by_level'][q], a['ratios']['neso_dressed']['by_level'][q]
        L.append(f'| {q} | {fr(u["value"])} ({u["label"]}) | {fr(v["value"])} ({v["label"]}) |')
    L += ['', '## Robustness to the dressing', '', '| Variant | against dressed median | against dressed NESO |', '|---|---|---|']
    for k, v in res['robustness']['variants'].items():
        L.append(f'| {k} | {fr(v["chronos2_dressed"]["value"])} ({v["chronos2_dressed"]["label"]}; {v["chronos2_dressed"]["practical"]}) | '
                 f'{fr(v["neso_dressed"]["value"])} ({v["neso_dressed"]["label"]}; {v["neso_dressed"]["practical"]}) |')
    rb = res['robustness']['robust']
    L += ['', f'Robust to the dressing: against dressed median {rb["chronos2_dressed"]}; against dressed NESO {rb["neso_dressed"]}.', '']
    b = res['sets']['all']['B']['chronos2_quantiles']['intervals']
    L += ['## Coverage by block of the day (Chronos-2, all days)', '',
          f'80%: {b["80"]["by_block"]} (largest gap {fr(b["80"]["largest_block_gap"])}); '
          f'98%: {b["98"]["by_block"]} (largest gap {fr(b["98"]["largest_block_gap"])}).', '', '## Does the band widen before a miss? (§7 C)', '']
    for k, v in res['C'].items():
        L.append(f'- {k}: group mean errors {[round(x) if x is not None else None for x in v["group_mean_error_mw"]]} MW; '
                 f'widest over narrowest {fr(v["widest_over_narrowest"])} ({fiv(v["ci90"])}); '
                 + (f'median monthly Spearman {fr(v["spearman_median"])}, positive in {v["months_positive"]} of {v["months"]} months'
                    if 'spearman_median' in v else f'Spearman {fr(v["spearman"])}'))
    cr = res['crossing']
    L += ['', f'Crossing: {cr["halfhours_sorted"]} scored half-hours sorted; largest move {cr["largest_move_mw"]:.1f} MW; '
          f'0.5 quantile moved in {len(cr["median_moved"])} half-hours.', '']
    if 'stage2_power' in res:
        L += ['## Stage 2: smallest detectable difference (§9)', '']
        for k, v in res['stage2_power'].items():
            if v: L.append(f'- against {NAMES[k]}: lower {v["smallest_detectable_difference"]["lower"]}, '
                           f'higher {v["smallest_detectable_difference"]["higher"]} ({v["windows"]} windows of {v["window_days"]} days)')
        L.append('')
    L += ['## Checks (PLAN.md §8)', ''] + [f'- {k}: {"passed" if v["passed"] else "FAILED"}' for k, v in res['checks'].items()]
    m = res['meta']
    L += ['', f'Commit {m["public_commit"]}; script SHA-256 {m["script_sha256"]}; seed {SEED}; {st.B} draws in blocks of {st.BLOCK}.', '']
    return '\n'.join(L)


def real():
    if not os.path.exists(SYNTH_JSON): sys.exit('Refused: run --synthetic first and commit score_synthetic.json.')
    if git('status', '--porcelain', '--', *GUARDED): sys.exit('Refused: these must be committed and unchanged: ' + ', '.join(GUARDED))
    try: tagged = git('show', f'{PLAN_TAG}:quantiles/PLAN.md')
    except subprocess.CalledProcessError: sys.exit(f'Refused: tag {PLAN_TAG} not found; run git fetch --tags.')
    if tagged != open(os.path.join(HERE, 'PLAN.md')).read().strip(): sys.exit(f'Refused: PLAN.md differs from tag {PLAN_TAG}.')
    sy = json.load(open(SYNTH_JSON))
    if not sy.get('passed') or sy.get('script_sha256') != st.sha(os.path.abspath(__file__)):
        sys.exit('Refused: the synthetic check has not passed with this script.')
    frame, q, qc, man, t1, hol = load_real()
    S = prepare(frame, q)
    c1 = check_medians(S, qc)
    if not c1['passed']:
        sys.exit(f'Stopped by check 1 (PLAN.md §8): {c1["counts"]}; mismatched days {c1["mismatched_days"][:10]}. '
                 'Find the cause and record it in quantiles/REVISIONS.md before scoring.')
    res, aux = analyse(S, t1, hol)
    res['checks'] = dict(quantiles_belong_to_medians=c1, reproduction=check_reproduction(frame), no_lookahead=check_lookahead(S),
                         arithmetic=check_arithmetic(S, aux['sel']),
                         hashes=dict(passed=True, note='every file read matched its recorded SHA-256, or the run stops'),
                         synthetic=dict(passed=True, file='quantiles/score_synthetic.json'))
    if c1['counts']['close']:
        res['check1_three_ways'] = 'close days exist: rerun on exact days alone and on all days is required (PLAN.md §8)'
    res['meta'] = dict(public_commit=git('rev-parse', 'HEAD'), script_sha256=st.sha(os.path.abspath(__file__)), plan_tag=PLAN_TAG,
                       seed=SEED, draws=st.B, block=st.BLOCK, quantile_manifest_sha256=QMANIFEST_SHA,
                       versions=dict(python=platform.python_version(), numpy=np.__version__, pandas=pd.__version__))
    out = dict(schema=SCHEMA, note='quantile study, stage 1 (backtest pilot); plan frozen at tag quantiles-plan', **st.round_floats(res))
    json.dump(out, open(os.path.join(HERE, 'results_stage1.json'), 'w'), indent=1, default=str)
    md = markdown(out); open(os.path.join(HERE, 'results_stage1.md'), 'w').write(md); print(md)
    failed = [k for k, v in res['checks'].items() if not v['passed']]
    if failed: print('CHECKS FAILED: ' + ', '.join(failed)); sys.exit(1)


# ------------------------------------------------------------------ synthetic check (PLAN.md §8.5) ---------------------
SYN_HOLIDAYS = wd.SYN_HOLIDAYS
Z = None


def zq():
    from statistics import NormalDist
    return np.array([NormalDist().inv_cdf(q) for q in GRID])


def synth(grid, seed=7, sigma=500.0, scale=1.0):
    """Invented outturn = signal + noise (sd sigma); medians = signal; Chronos-2's quantiles = signal + scale * sigma * z."""
    rng = np.random.default_rng(seed)
    f = grid.sort_values(['day', 'start_utc'], kind='mergesort').reset_index(drop=True)
    pos = f.groupby('day').cumcount().to_numpy(); n = f.groupby('day')['day'].transform('size').to_numpy()
    sig = np.round(25000 + 5000 * np.sin(2 * np.pi * (pos / n - 0.3)))
    fr_ = f[['day', 'start_utc']].copy(); fr_['outturn'] = sig + rng.normal(0, sigma, len(f))
    fr_[CH] = sig; fr_[NESO] = sig; fr_[REF] = sig
    q = f[['day', 'start_utc']].copy()
    Qv = sig[:, None] + scale * sigma * zq()[None, :]
    for j, c in enumerate(QCOLS): q[c] = Qv[:, j]
    return fr_, q


def unit_rules():
    ok, n = True, 0
    def t(cond):
        nonlocal ok, n; n += 1; ok &= bool(cond)
    t(ratio_label([0.9, 0.98]) == LOWER); t(ratio_label([1.01, 1.2]) == HIGHER); t(ratio_label([0.9, 1.1]) == NCD)
    t(ratio_label(None) == UNDEF); t(practical_label(None) == UNDEF); t(practical_label(float('nan')) == UNDEF)
    t(practical_label(0.94) == P_LOWER); t(practical_label(1.06) == P_HIGHER); t(practical_label(0.96) == P_EQUAL)
    t(practical_label(0.95) == P_EQUAL and practical_label(1.05) == P_EQUAL)
    # 0.96 with a tight interval: clearly lower and practically equal, so not a gain
    r = dict(label=ratio_label([0.955, 0.965]), practical=practical_label(0.96)); t(r['label'] == LOWER and r['practical'] == P_EQUAL and not is_gain(r))
    t(is_gain(dict(label=LOWER, practical=P_LOWER)))
    t(coverage_label([0.70, 0.75], 0.8) == NARROW); t(coverage_label([0.85, 0.9], 0.8) == WIDE); t(coverage_label([0.78, 0.81], 0.8) == CONSISTENT)
    t(coverage_label(None, 0.8) == UNDEF)
    t(coverage_practical(0.78, 0.80, 0.03) == P_CONS); t(coverage_practical(0.76, 0.80, 0.03) == P_NARROW)
    t(coverage_practical(0.77, 0.80, 0.03) == P_CONS); t(coverage_practical(0.84, 0.80, 0.03) == P_WIDE)
    t(coverage_practical(0.965, 0.98, 0.01) == P_NARROW); t(coverage_practical(0.975, 0.98, 0.01) == P_CONS)
    t(coverage_practical(None, 0.8, 0.03) == UNDEF)
    t(spearman([1, 1, 1, 1], [1, 2, 3, 4]) is None); t(spearman([1, 2], [1, 2]) is None)
    t(abs(spearman([1, 2, 3, 4], [10, 20, 30, 40]) - 1) < 1e-12)
    # pinball
    t(np.allclose(pinball(np.array([10.0]), np.array([[8.0, 12.0]]), [0.9, 0.9]), [[1.8, 0.2]]))
    # headline, exact text
    s = dict(A=dict(scores_mw={'chronos2_quantiles': dict(primary=301.4), 'chronos2_dressed': dict(primary=310.0)},
                    ratios={'chronos2_dressed': dict(primary=dict(value=0.97226, ci90=[0.951, 0.993], label=LOWER, practical=P_EQUAL)),
                            'neso_dressed': dict(primary=dict(value=1.3, ci90=[1.25, 1.35], label=HIGHER, practical=P_HIGHER))}),
             B={'chronos2_quantiles': dict(intervals={'80': dict(coverage=0.7612, label=NARROW, practical=P_NARROW)})})
    want = ("In a backtest the foundation model may have seen in training, a day-ahead position on GB demand set from "
            "Chronos-2's quantile forecasts, averaged with equal weight over quantile levels 0.10 to 0.90 (cost ratios from "
            "1:9 to 9:1), cost clearly less than one set from its own median with a band built from its recent errors "
            "(score 301 against 310 MW, ratio 0.972, 90% interval 0.951 to 0.993; practically equal), and clearly more than "
            "one set from NESO's forecast with a band built the same way (ratio 1.300, 90% interval 1.250 to 1.350; "
            "practically higher). Chronos-2's 80% intervals contained outturn 76.1% of the time (too narrow; practically "
            "too narrow).")
    h = headline(s); t(h == want)
    if h != want: print('FAIL headline\n' + h)
    s['A']['ratios']['neso_dressed']['primary']['label'] = NCD; s['B']['chronos2_quantiles']['intervals']['80']['label'] = CONSISTENT
    s['B']['chronos2_quantiles']['intervals']['80']['practical'] = P_CONS
    h2 = headline(s); t('and not clearly different from one set from NESO' in h2 and '(consistent with their level; practically consistent)' in h2)
    s['A']['ratios']['chronos2_dressed']['primary']['practical'] = UNDEF; t(headline(s).startswith('Headline undefined'))
    return bool(ok), n


def synthetic():
    t1, _ = asy.load_inputs()
    grid = pd.read_csv(st.FORECASTS, usecols=['day', 'start_utc'], dtype={'day': str})
    res = dict(script_sha256=st.sha(os.path.abspath(__file__)), checks={}); ok_all = True

    def rec(name, good, **info):
        nonlocal ok_all
        res['checks'][name] = dict(passed=bool(good), **info); ok_all &= bool(good)
        print(('PASS ' if good else 'FAIL ') + name, flush=True)

    g, n = unit_rules(); rec('unit rules, labels and headline', g, n=n)
    # honest, too narrow and too wide bands, through the whole pipeline
    for scale, want in ((1.0, CONSISTENT), (0.5, NARROW), (2.0, WIDE)):
        fr_, q = synth(grid, scale=scale); S = prepare(fr_, q)
        out, aux = analyse(S, t1, SYN_HOLIDAYS, power=(scale == 1.0))
        cov = out['sets']['all']['B']['chronos2_quantiles']['intervals']['80']
        rec(f'bands at {scale} x the true width: {want}', cov['label'] == want, coverage=cov['coverage'], ci90=cov['ci90'])
        if scale == 1.0:
            dr = out['sets']['all']['B']['chronos2_dressed']['intervals']['80']
            rec('dressed bands of an honest forecaster: consistent with their level', dr['label'] == CONSISTENT, coverage=dr['coverage'])
            rec('days scored after the first month; T1 and calendar sets present',
                out['n_days_scored'] < 960 and out['n_days_scored'] > 900 and out['sets']['T1']['n_days'] > 80
                and out['sets']['calendar']['n_days'] > 10 and out['sets']['stage2_season']['n_days'] > 200,
                n=out['n_days_scored'])
            rec('headline written', out['headline'].startswith('In a backtest') and 'consistent with their level' in out['headline'],
                headline=out['headline'])
            pw = out['stage2_power']['chronos2_dressed']
            rec('stage 2 power estimate computed', pw is not None and pw['smallest_detectable_difference']['lower'] is not None, power=pw)
            rec('no look-ahead in the dressing', check_lookahead(S)['passed'])
            rec('arithmetic', check_arithmetic(S, aux['sel'])['passed'])
            rec('check 1 on exact medians', check_medians(S, pd.DataFrame(dict(day=S['days'], category='exact')))['counts']['exact'] == 960)
            # a forecaster equal to its dressed version scores exactly 1 under every variant
            sel = aux['sel']; ones = True
            for W, nb in VARIANTS:
                Qd, _ = dress(S, CH, nb, W)
                S2 = dict(S, Qs=Qd, Qraw=Qd)
                C = scores_by_day(S2, Qd, sel, np.ones(len(S['y']), bool))[:, CENTRAL].mean(1)
                D_ = scores_by_day(S, Qd, sel, np.ones(len(S['y']), bool))[:, CENTRAL].mean(1)
                r = ratio_result(C, D_, np.ones(len(sel), bool), aux['I'])
                ones &= r['value'] == 1.0 and r['ci90'] == [1.0, 1.0]
            rec('a forecaster equal to its dressed version scores exactly 1 under every variant', ones)
    # a mismatched median stops check 1
    fr_, q = synth(grid); q.loc[5, 'q50'] += 0.02; S = prepare(fr_, q)
    c1 = check_medians(S, pd.DataFrame(dict(day=S['days'], category=['mismatched'] + ['exact'] * 959)))
    rec('a median 0.02 MW out is mismatched and fails check 1', (not c1['passed']) and c1['counts']['mismatched'] == 1)
    q.loc[5, 'q50'] -= 0.015; S = prepare(fr_, q)
    c1 = check_medians(S, pd.DataFrame(dict(day=S['days'], category=['close'] + ['exact'] * 959)))
    rec('a median 0.005 MW out is close and passes', c1['passed'] and c1['counts']['close'] == 1)
    # measure C on invented days
    days = sorted(grid['day'].unique()); dates = [pd.Timestamp(d) for d in days]; rng = np.random.default_rng(3)
    I = st.boot_idx(len(days), np.random.default_rng(SEED))
    s = np.exp(rng.normal(0, 0.5, len(days))); err = s * np.abs(rng.normal(0, 1, len(days))) * 500
    c = width_test(s, err, dates, I)
    rec('width that tracks the error: widest over narrowest above 1', c['ci90'][0] > 1, ratio=c['widest_over_narrowest'])
    c = width_test(np.ones(len(days)), err, dates, I)
    rec('constant width: ratio about 1, correlation undefined', c['ci90'][0] <= 1 <= c['ci90'][1] and c['spearman_median'] is None,
        ratio=c['widest_over_narrowest'])
    season = np.array([1 + 0.6 * np.cos(2 * np.pi * (d.month - 1) / 12) for d in dates])
    w_s = season * (1 + 0.001 * rng.random(len(days))); e_s = season * np.abs(rng.normal(0, 1, len(days))) * 500
    cy, cm = width_test(w_s, e_s, dates, I, by_month=False), width_test(w_s, e_s, dates, I)
    rec('shared season only: above 1 over the year, about 1 within months',
        cy['ci90'][0] > 1 and cm['ci90'][0] <= 1 <= cm['ci90'][1], year=cy['widest_over_narrowest'], month=cm['widest_over_narrowest'])
    # sorting: a crossed half-hour is sorted and counted; an uncrossed one is untouched
    fr_, q = synth(grid); S0 = prepare(fr_, q); row = int(S0['rows'][200][0])          # a half-hour on a scored day
    q = q.sort_values(['day', 'start_utc'], kind='mergesort').reset_index(drop=True)
    q.loc[row, 'q20'] = q.loc[row, 'q25'] + 30; S = prepare(fr_, q)
    out, _ = analyse(S, t1, SYN_HOLIDAYS, power=False)
    rec('a crossed half-hour is sorted and counted; nothing else moves',
        out['crossing']['halfhours_sorted'] == 1 and abs(out['crossing']['largest_move_mw'] - 30) < 1e-6
        and not out['crossing']['median_moved'], crossing=out['crossing'])
    res['passed'] = bool(ok_all)
    json.dump(st.round_floats(res), open(SYNTH_JSON, 'w'), indent=1, default=str)
    print('synthetic: ' + ('PASS' if ok_all else 'FAIL'))
    return ok_all


if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('--synthetic', action='store_true')
    if ap.parse_args().synthetic: sys.exit(0 if synthetic() else 1)
    real()
