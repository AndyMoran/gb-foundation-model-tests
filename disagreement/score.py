"""
Disagreement value, stage 1: the backtest pilot (disagreement/PLAN.md, frozen at tag disagreement-plan-3a260a2; see
REVISIONS.md 1 for why not disagreement-plan). Committed before it runs; its outputs are committed after.

For: a reviewer checking that the value, its groups, the direction measures, the sign-flip null, the intervals, the
labels and the headline follow PLAN.md §7-10.

Reads, through imbalance_cost/score.py's own loader and hash checks (imported unchanged): the forecasts, outturn, System
Price and Market Index Price, and T1. Also reads imbalance_cost/results_stage1.json, whose SHA-256 is recorded below.
Writes disagreement/results_stage1.json and results_stage1.md.

N is NESO's day-ahead forecast and F another forecaster's, A outturn, in MW; SP and MIP in £/MWh. Each half-hour:
    d = F - N (the disagreement), v = d * (SP - MIP) * 0.5, in £: the value of switching from N to F.
    A  value         each day's sum of v over its demand in GWh, then the mean over days (£ per GWh); x 1,000 per TWh
    B  disagreement  the set's half-hours ranked by |d| (ties in time order) and cut into four equal groups; in each,
                     sum of v over sum of |d| * 0.5 (£ per MWh of disagreement); top minus bottom. Also fixed bands of
                     |d|: 0-250, over 250-500, over 500-1,000 and over 1,000 MW
    C  price stress  the same, grouped by |SP - MIP| (one grouping for every forecaster); and each group's share of v
    D  direction     where d != 0 and SP != MIP: hit rate (sign of d = sign of SP - MIP) and sign payoff (mean of
                     sign(d) * (SP - MIP), £ per MWh traded); overall and in the top stress quarter
       null          every half-hour of a day takes one random sign (2,000 draws); also with one sign per 7-day block
    E  tail          mean of the worst and best 5% of days by A; A on 8 January 2025
    F  accuracy      mean daily absolute error over NESO's, with a paired interval; "credibly below 0.9" if the
                     interval's upper end is below 0.9 (rule 7.5, descriptive)
Sets: all days; winter (December to February); T1, the coldest tenth; the evening window, 16:00 to 19:30 UK time (value
per GWh of evening demand). Year by year: A and F in each 12-month period from 16 March 2024, each bootstrapped alone.
Intervals: the tails study's 7-day moving-block bootstrap over days, 2,000 draws, seed 20261126, the same draws
throughout. Labels are unadjusted and are not tests.

Modes:
    python disagreement/score.py --synthetic   invented data with known answers on the real calendar (400 draws);
                                               writes disagreement/score_synthetic.json; exits 1 on any failure
    python disagreement/score.py               stage 1. Refused unless the synthetic check passed with this script,
                                               the guarded files are committed and unchanged, and PLAN.md matches the
                                               tag disagreement-plan-3a260a2.
Stage 2's loading of the live forecasts is added before stage 2 runs, recorded in REVISIONS.md first (PLAN.md §11).
"""
import argparse, importlib.util, json, math, os, platform, subprocess, sys
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
_spec = importlib.util.spec_from_file_location('imbalance_score', os.path.join(ROOT, 'imbalance_cost', 'score.py'))
sc = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(sc)        # imported unchanged
st, asy = sc.st, sc.asy

PLAN_TAG, SCHEMA = 'disagreement-plan-3a260a2', 1
SEED, NULL_SEED, B_SYNTH = 20261126, 20261127, 400
TZ, EVE_FROM, EVE_TO = sc.TZ, sc.EVE_FROM, sc.EVE_TO
STAGE1 = os.path.join(ROOT, 'imbalance_cost', 'results_stage1.json')
STAGE1_SHA = '39be61af6046530296947e6915e28b28a8697357bfaf8057a740738bd17efea9'
SYNTH_JSON = os.path.join(HERE, 'score_synthetic.json')
GUARDED = ['disagreement/score.py', 'disagreement/PLAN.md', 'disagreement/score_synthetic.json',
           'imbalance_cost/results_stage1.json'] + sc.GUARDED

NESO, CH, REF, AVG = sc.NESO, sc.CH, sc.REF, sc.AVG
COLS = [CH, REF, AVG, sc.V1, sc.S1, sc.TFM, sc.CHW]            # primary first (PLAN.md §6); each against NESO
NAMES = sc.NAMES
BANDS = ((0, 250), (250, 500), (500, 1000), (1000, np.inf))    # |d| in MW, each (lo, hi]; the first includes 0
PERIODS = (('2024-03-16', '2025-03-15'), ('2025-03-16', '2026-03-15'), ('2026-03-16', '2026-10-31'))
EMN_DAY = '2025-01-08'
POS, NEG, NCD0, UND = 'clearly positive', 'clearly negative', 'not clearly different from 0', 'undefined'
HIGHER, LOWER, NCD = 'clearly higher', 'clearly lower', 'not clearly different'
BEYOND, WITHIN, WORSE = 'beyond chance', 'within chance', 'worse than chance'


def git(*a):
    return subprocess.run(['git', '-C', ROOT, *a], capture_output=True, text=True, check=True).stdout.strip()


# ------------------------------------------------------------------ rules ----------------------------------------------
def ci90(x):
    """The 90% interval of the finite draws; None if there are none."""
    x = np.asarray(x, float); x = x[np.isfinite(x)]
    return [float(v) for v in np.quantile(x, [0.05, 0.95])] if len(x) else None


def label0(iv):
    if iv is None: return UND
    return NEG if iv[1] < 0 else POS if iv[0] > 0 else NCD0


def label_diff(iv):
    if iv is None: return UND
    return LOWER if iv[1] < 0 else HIGHER if iv[0] > 0 else NCD


def label_null(obs, null):
    lo, hi = np.quantile(null, [0.05, 0.95])
    return BEYOND if obs > hi else WORSE if obs < lo else WITHIN


def money(v): return f'{v:,.0f}'.replace('-', '−')
def pence(v): return f'{v:,.2f}'.replace('-', '−')


def headline(R, Riv, lab, X, Xiv, Y, Yiv, Z, Ziv, W, Wiv):
    """PLAN.md §10, stage 1, by rule. An undefined value has no sentence: the run stops."""
    verb = {POS: '**clearly gained**', NEG: '**clearly lost**', NCD0: '**neither clearly gained nor lost**'}.get(lab)
    if verb is None or None in (Riv, Xiv, Yiv, Ziv, Wiv): raise ValueError('the headline needs every interval defined')
    return (f"In a backtest the foundation models may have seen in training, Chronos-2's day-ahead demand forecast had "
            f"{R:.2f} times the daily error of NESO's (90% interval {Riv[0]:.2f} to {Riv[1]:.2f}), and a supplier that "
            f"bought it instead of NESO's would have {verb} ({money(X)} £ per GWh of demand, 90% interval "
            f"{money(Xiv[0])} to {money(Xiv[1])}); for the weather regression the figure was {money(Y)} £ per GWh "
            f"({money(Yiv[0])} to {money(Yiv[1])}). Where Chronos-2 disagreed with NESO most (the largest quarter of its "
            f"disagreements), each MWh of disagreement was worth {pence(Z)} £ ({pence(Ziv[0])} to {pence(Ziv[1])}), "
            f"against {pence(W)} £ ({pence(Wiv[0])} to {pence(Wiv[1])}) in the smallest quarter.")


# ------------------------------------------------------------------ building blocks ------------------------------------
def boot(n, seed, B):
    """The tails study's moving-block bootstrap (score_tails.boot_idx), with the number of draws as an argument."""
    rng = np.random.default_rng(seed); nb = int(np.ceil(n / st.BLOCK))
    starts = rng.integers(0, n - st.BLOCK + 1, size=(B, nb))
    return (starts[:, :, None] + np.arange(st.BLOCK)).reshape(B, -1)[:, :n]


def rank_groups(x, k=4):
    """Equal groups by rank of x, ties in their given (time) order: 0 is the smallest."""
    order = np.lexsort((np.arange(len(x)), x)); g = np.empty(len(x), int)
    for i, part in enumerate(np.array_split(order, k)): g[part] = i
    return g


def band_of(absd):
    g = np.zeros(len(absd), int)
    for i, (lo, _) in enumerate(BANDS[1:], start=1): g[absd > lo] = i
    return g


def halfhours(frame, cols, ok_days):
    """Scored half-hours only, in day order."""
    f = frame[frame['day'].isin(ok_days)].sort_values(['day', 'start_utc'], kind='mergesort').reset_index(drop=True)
    days = sorted(f['day'].unique()); code = pd.Categorical(f['day'], categories=days).codes
    loc = pd.to_datetime(f['start_utc'], utc=True).dt.tz_convert(TZ); mins = (loc.dt.hour * 60 + loc.dt.minute).to_numpy()
    return dict(days=days, code=code, A=f['outturn'].to_numpy(float), N=f[NESO].to_numpy(float),
                spread=(f['system_price'] - f['mip']).to_numpy(float), eve=(mins >= EVE_FROM) & (mins <= EVE_TO),
                F={c: f[c].to_numpy(float) for c in cols})


def wsum(v, M, I): return np.where(M, v[I], 0).sum(1)


def ratio_draws(num, den, M, I):
    a, b = wsum(num, M, I), wsum(den, M, I)
    with np.errstate(invalid='ignore', divide='ignore'): return np.where(b > 0, a / b, np.nan)


def ratio_pt(num, den, m):
    b = den[m].sum(); return float(num[m].sum() / b) if b > 0 else None


def tail_means(a, frac=0.05):
    if not len(a): return np.nan, np.nan
    k = max(1, math.ceil(frac * len(a))); s = np.sort(a)
    return float(s[:k].mean()), float(s[-k:].mean())


# ------------------------------------------------------------------ one set --------------------------------------------
def measure_set(H, cols, dm, hm, I, with_tail=True):
    """Measures A-F for the days dm and half-hours hm (hm already within dm)."""
    n = len(H['days']); code = H['code']; S = lambda w: np.bincount(code, weights=w, minlength=n)
    M = dm[I]; cnt = M.sum(1); one = hm.astype(float)
    gwh = S(H['A'] * 0.5 * one) / 1000; nhh = S(one)
    sp = H['spread']; stress = np.full(len(sp), -1); stress[hm] = rank_groups(np.abs(sp[hm]))
    maeN = S(np.abs(H['A'] - H['N']) * one) / np.maximum(nhh, 1)
    out = dict(n_days=int(dm.sum()), n_halfhours=int(hm.sum()),
               stress_thresholds_gbp_per_mwh=[float(np.abs(sp[stress == k]).max()) for k in range(4)], forecasters={})
    draws_A = {}
    for c in cols:
        d = H['F'][c] - H['N']; v = d * sp * 0.5 * one; ad = np.abs(d) * 0.5 * one
        with np.errstate(invalid='ignore', divide='ignore'): a = np.where(gwh > 0, S(v) / gwh, np.nan)
        dA = wsum(np.nan_to_num(a), M, I) / cnt; draws_A[c] = dA
        A_ = dict(value=float(np.mean(a[dm])), ci90=ci90(dA)); A_['label'] = label0(A_['ci90'])
        A_['per_twh'] = A_['value'] * 1000
        maeF = S(np.abs(H['A'] - H['F'][c]) * one) / np.maximum(nhh, 1)
        Rd = ratio_draws(maeF, maeN, M, I); Rv = float(maeF[dm].mean() / maeN[dm].mean())
        Fm = dict(mae=float(maeF[dm].mean()), mae_neso=float(maeN[dm].mean()), ratio=Rv, ci90=ci90(Rd))
        Fm['credibly_below_0_9'] = bool(Fm['ci90'] is not None and Fm['ci90'][1] < 0.9)
        res = dict(A=A_, F=Fm)
        # B: groups by size of disagreement, and fixed bands
        g = np.full(len(d), -1); g[hm] = rank_groups(np.abs(d[hm])); bd = np.full(len(d), -1); bd[hm] = band_of(np.abs(d[hm]))
        for key, grp, kk in (('B_groups', g, 4), ('B_bands', bd, len(BANDS))):
            rows, gd = [], []
            for k in range(kk):
                mk = (grp == k).astype(float); num, den = S(v * mk), S(ad * mk); dr = ratio_draws(num, den, M, I); gd.append(dr)
                row = dict(value=ratio_pt(num, den, dm), ci90=ci90(dr), n_halfhours=int((grp == k).sum()))
                if key == 'B_groups' and row['n_halfhours']: row['max_abs_d_mw'] = float(np.abs(d[grp == k]).max())
                if key == 'B_bands': row['band_mw'] = [BANDS[k][0], None if np.isinf(BANDS[k][1]) else BANDS[k][1]]
                rows.append(row)
            res[key] = dict(groups=rows)
            if key == 'B_groups':
                top_bot = gd[-1] - gd[0]
                v0 = None if rows[-1]['value'] is None or rows[0]['value'] is None else rows[-1]['value'] - rows[0]['value']
                res[key]['top_minus_bottom'] = dict(value=v0, ci90=ci90(top_bot), label=label0(ci90(top_bot)))
        # C: groups by price stress
        rows, gd = [], []; totV = S(v)
        for k in range(4):
            mk = (stress == k).astype(float); num, den = S(v * mk), S(ad * mk); dr = ratio_draws(num, den, M, I); gd.append(dr)
            rows.append(dict(value=ratio_pt(num, den, dm), ci90=ci90(dr),
                             share_of_value=(float(num[dm].sum() / totV[dm].sum()) if totV[dm].sum() != 0 else None)))
        tb = gd[-1] - gd[0]
        v0 = None if rows[-1]['value'] is None or rows[0]['value'] is None else rows[-1]['value'] - rows[0]['value']
        res['C'] = dict(groups=rows, top_minus_bottom=dict(value=v0, ci90=ci90(tb), label=label0(ci90(tb))))
        # D: direction alone
        q = hm & (d != 0) & (sp != 0)
        for key, qq in (('D_all', q), ('D_stress', q & (stress == 3))):
            w = qq.astype(float); hit = S(w * (np.sign(d) == np.sign(sp))); nn = S(w); pay = S(w * np.sign(d) * sp)
            res[key] = dict(n_halfhours=int(qq.sum()),
                            hit_rate=dict(value=ratio_pt(hit, nn, dm), ci90=ci90(ratio_draws(hit, nn, M, I))),
                            sign_payoff=dict(value=ratio_pt(pay, nn, dm), ci90=ci90(ratio_draws(pay, nn, M, I))))
        # E: tail of days
        if with_tail:
            av = a[dm]; worst, best = tail_means(av)
            dw = np.array([tail_means(a[I[b]][M[b]]) for b in range(len(I))])
            days_in = [H['days'][i] for i in np.flatnonzero(dm)]
            res['E'] = dict(worst_5pct=dict(value=worst, ci90=ci90(dw[:, 0])), best_5pct=dict(value=best, ci90=ci90(dw[:, 1])),
                            on_2025_01_08=(float(a[H['days'].index(EMN_DAY)]) if EMN_DAY in days_in else None))
        out['forecasters'][c] = res
    if CH in cols and REF in cols:
        dd = draws_A[CH] - draws_A[REF]; iv = ci90(dd)
        out['chronos2_minus_regression_A'] = dict(value=out['forecasters'][CH]['A']['value'] - out['forecasters'][REF]['A']['value'],
                                                   ci90=iv, label=label_diff(iv))
    return out


# ------------------------------------------------------------------ sign-flip null (PLAN.md §7 D) ----------------------
def day_stats(H, c, hm):
    """Per day, for the null: hits and count where d != 0 and SP != MIP, sum of sign(d) * spread, and A; each overall and
    in the top stress quarter (A there: that day's v in its stressed half-hours over the whole day's demand)."""
    n = len(H['days']); S = lambda w: np.bincount(H['code'], weights=w, minlength=n)
    d = H['F'][c] - H['N']; sp = H['spread']; one = hm.astype(float)
    stress = np.full(len(sp), -1); stress[hm] = rank_groups(np.abs(sp[hm]))
    gwh = S(H['A'] * 0.5 * one) / 1000; out = {}
    for key, part in (('all', hm), ('stress', hm & (stress == 3))):
        q = (part & (d != 0) & (sp != 0)).astype(float)
        out[key] = dict(hit=S(q * (np.sign(d) == np.sign(sp))), n=S(q), pay=S(q * np.sign(d) * sp),
                        a=S(d * sp * 0.5 * part) / gwh)
    return out


def flipped(stats, s):
    """The three statistics with day signs s (draws x days, each +1 or -1). s of all +1 gives the observed figures."""
    h, n, p, a = stats['hit'], stats['n'], stats['pay'], stats['a']
    tot = n.sum()
    with np.errstate(invalid='ignore', divide='ignore'):
        hit = (((1 + s) / 2) @ h + ((1 - s) / 2) @ (n - h)) / tot
        pay = (s @ p) / tot
    return dict(hit_rate=hit, sign_payoff=pay, A=(s @ a) / len(a))


def null_signs(days, B, seed, block):
    rng = np.random.default_rng(seed)
    if block == 1: return rng.integers(0, 2, size=(B, len(days))) * 2 - 1
    t = np.array([(pd.Timestamp(x) - pd.Timestamp(days[0])).days // block for x in days])
    sb = rng.integers(0, 2, size=(B, t.max() + 1)) * 2 - 1
    return sb[:, t]


def null_test(H, cols, hm, B, seed):
    out = {}
    S1 = null_signs(H['days'], B, seed, 1); S7 = null_signs(H['days'], B, seed + 1, 7)
    for c in cols:
        ds = day_stats(H, c, hm); out[c] = {}
        for part in ('all', 'stress'):
            obs = {k: float(v[0]) for k, v in flipped(ds[part], np.ones((1, len(H['days'])))).items()}
            r = {}
            for k in ('hit_rate', 'sign_payoff', 'A'):
                r[k] = dict(observed=obs[k])
                for tag, Sx in (('by_day', S1), ('by_7_day_block', S7)):
                    nl = flipped(ds[part], Sx)[k]; nl = nl[np.isfinite(nl)]
                    r[k][tag] = (dict(p5=float(np.quantile(nl, 0.05)), p95=float(np.quantile(nl, 0.95)),
                                      share_at_or_above=float(np.mean(nl >= obs[k])), label=label_null(obs[k], nl))
                                 if len(nl) and np.isfinite(obs[k]) else dict(label=UND))
            out[c][part] = r
    return out


# ------------------------------------------------------------------ year by year (PLAN.md §7) ------------------------
def periods(days):
    dd = np.array([pd.Timestamp(x) for x in days])
    return [(lo, hi, (dd >= pd.Timestamp(lo)) & (dd <= pd.Timestamp(hi))) for lo, hi in PERIODS]


def by_year(H, cols, B, seed):
    out = []
    for lo, hi, m in periods(H['days']):
        idx = np.flatnonzero(m); keep = np.isin(H['code'], idx)
        sub = dict(days=[H['days'][i] for i in idx], code=pd.Categorical(H['code'][keep], categories=idx).codes,
                   A=H['A'][keep], N=H['N'][keep], spread=H['spread'][keep], eve=H['eve'][keep],
                   F={c: H['F'][c][keep] for c in cols})
        n = len(idx); I = boot(n, seed, B)
        r = measure_set(sub, cols, np.ones(n, bool), np.ones(keep.sum(), bool), I, with_tail=False)
        out.append(dict(period=[lo, hi], n_days=n, full_year=(lo, hi) != PERIODS[-1],
                        forecasters={c: dict(A=r['forecasters'][c]['A'], F=r['forecasters'][c]['F']) for c in cols}))
    return out


# ------------------------------------------------------------------ analysis -------------------------------------------
def set_masks(H, t1_days):
    dates = [pd.Timestamp(x) for x in H['days']]; n = len(dates); allhh = np.ones(len(H['code']), bool)
    winter = np.array([x.month in (12, 1, 2) for x in dates]); t1 = np.isin(H['days'], list(t1_days))
    return dict(all=(np.ones(n, bool), allhh), winter=(winter, winter[H['code']]), T1=(t1, t1[H['code']]),
                evenings=(np.ones(n, bool), H['eve']))


def analyse(H, t1_days, cols=COLS, B=None):
    B = B or st.B; n = len(H['days']); I = boot(n, SEED, B)
    sets = {name: measure_set(H, cols, dm, hm, I) for name, (dm, hm) in set_masks(H, t1_days).items()}
    return dict(sets=sets, null=null_test(H, cols, np.ones(len(H['code']), bool), B, NULL_SEED),
                by_year=by_year(H, cols, B, SEED))


def write_headline(res):
    a = res['sets']['all']['forecasters']; c, r = a[CH], a[REF]; g = c['B_groups']['groups']
    return headline(c['F']['ratio'], c['F']['ci90'], c['A']['label'], c['A']['value'], c['A']['ci90'],
                    r['A']['value'], r['A']['ci90'], g[-1]['value'], g[-1]['ci90'], g[0]['value'], g[0]['ci90'])


# ------------------------------------------------------------------ checks (PLAN.md §8) ------------------------------
def check_reconciliation(H, cols):
    """Demand-weighted net exposure = £ per MWh of error x MWh of error per GWh, for NESO and every forecaster."""
    gwh = (H['A'] * 0.5).sum() / 1000; rows, ok = [], True
    for c in [NESO] + list(cols):
        F = H['N'] if c == NESO else H['F'][c]; e = H['A'] - F; x = (e * H['spread'] * 0.5).sum(); mwh = (np.abs(e) * 0.5).sum()
        dw, per, epg = x / gwh, x / mwh, mwh / gwh; good = abs(dw - per * epg) <= 1e-9 * max(1.0, abs(dw)); ok &= good
        rows.append(dict(forecaster=c, net_gbp_per_gwh_demand_weighted=float(dw), gbp_per_mwh_of_error=float(per),
                         mwh_of_error_per_gwh=float(epg), passed=bool(good)))
    return dict(passed=bool(ok), rows=rows)


def check_identity(frame, ok_days, res, cols, stage1=None):
    """Value A = NESO's net exposure minus the forecaster's, from imbalance_cost/score.py's own sums, to £0.01/GWh."""
    P = sc.per_day(frame[frame['day'].isin(ok_days)], [NESO] + list(cols)); m = P['ok']; g = P['gwh']['day']
    net = {c: float(np.mean((P['F'][c]['day']['net'] / g)[m])) for c in [NESO] + list(cols)}
    rows, ok = [], True
    for c in cols:
        mine = res['sets']['all']['forecasters'][c]['A']['value']; want = net[NESO] - net[c]
        good = abs(mine - want) <= 0.01
        row = dict(forecaster=c, value=mine, neso_minus_own=want)
        if stage1 is not None:
            s1 = stage1['sets']['all']['forecasters']; w1 = s1[NESO]['net']['value'] - s1[c]['net']['value']
            row['stage1_json'] = w1; good &= abs(mine - w1) <= 0.01
        row['passed'] = bool(good); ok &= good; rows.append(row)
    return dict(passed=bool(ok), rows=rows)


def check_days(ok_days, all_days, dropped):
    want = sorted(set(all_days) - set(dropped)); same = list(ok_days) == want
    ps = periods(ok_days); cover = np.sum([m for _, _, m in ps], axis=0)
    return dict(passed=bool(same and np.all(cover == 1)), n_days=len(ok_days), equal_to_imbalance_stage1=bool(same),
                periods_partition_days=bool(np.all(cover == 1)), period_days=[int(m.sum()) for _, _, m in ps])


# ------------------------------------------------------------------ output ---------------------------------------------
def f0(x): return '–' if x is None else money(x)
def f2(x): return '–' if x is None else pence(x)
def i0(v): return '–' if not v else f'{money(v[0])} to {money(v[1])}'
def i2(v): return '–' if not v else f'{pence(v[0])} to {pence(v[1])}'
def pc(x): return '–' if x is None else f'{100 * x:.1f}%'
def ipc(v): return '–' if not v else f'{100 * v[0]:.1f} to {100 * v[1]:.1f}'


def markdown(res, meta):
    L = ['# Disagreement value, stage 1 (backtest pilot): results (generated by disagreement/score.py)', '',
         'A pilot on days the foundation models may have seen in training (PLAN.md §5). Value is what switching from '
         "NESO's day-ahead forecast to the forecaster would have earned at System Price against MIP; positive is a gain. "
         'Labels come from unadjusted 90% intervals and are not tests.', '', '## Headline (PLAN.md §10)', '', res['headline'], '',
         f'Days scored: {res["sets"]["all"]["n_days"]}.', '']
    for name, o in res['sets'].items():
        L += [f'## Set: {name} ({o["n_days"]} days, {o["n_halfhours"]:,} half-hours)', '',
              '| Forecaster | value £/GWh (90%) | label | £ per TWh | error ÷ NESO\'s (90%) | below 0.9? |', '|---|---|---|---|---|---|']
        for c, r in o['forecasters'].items():
            A_, F_ = r['A'], r['F']
            L.append(f'| {NAMES[c]} | {f0(A_["value"])} ({i0(A_["ci90"])}) | {A_["label"]} | {f0(A_["per_twh"])} | '
                     f'{F_["ratio"]:.3f} ({F_["ci90"][0]:.3f} to {F_["ci90"][1]:.3f}) | {"credibly" if F_["credibly_below_0_9"] else "no"} |')
        d = o.get('chronos2_minus_regression_A')
        if d: L += ['', f'Chronos-2 minus the regression: {f0(d["value"])} £/GWh ({i0(d["ci90"])}), {d["label"]}.']
        L += ['', '**B. Value per MWh of disagreement, by size of disagreement (£/MWh; group upper bound in MW)**', '',
              '| Forecaster | smallest quarter | 2nd | 3rd | largest quarter | top − bottom (90%) | label |', '|---|---|---|---|---|---|---|']
        for c, r in o['forecasters'].items():
            g = r['B_groups']['groups']; tb = r['B_groups']['top_minus_bottom']
            cells = [f'{f2(x["value"])} (≤{x.get("max_abs_d_mw", 0):,.0f})' for x in g]
            L.append(f'| {NAMES[c]} | ' + ' | '.join(cells) + f' | {f2(tb["value"])} ({i2(tb["ci90"])}) | {tb["label"]} |')
        L += ['', '| Forecaster | ' + ' | '.join(f'{lo}–{hi} MW' if hi else f'over {lo} MW' for lo, hi in
                                                 [(b[0], None if np.isinf(b[1]) else b[1]) for b in BANDS]) + ' |', '|---' * 5 + '|']
        for c, r in o['forecasters'].items():
            L.append(f'| {NAMES[c]} | ' + ' | '.join(f'{f2(x["value"])} (n={x["n_halfhours"]:,})' for x in r['B_bands']['groups']) + ' |')
        th = o['stress_thresholds_gbp_per_mwh']
        L += ['', f'**C. By price stress (|SP − MIP| quarters, upper bounds £{th[0]:.2f}, £{th[1]:.2f}, £{th[2]:.2f}, £{th[3]:.2f}/MWh): '
              '£ per MWh of disagreement, and share of value**', '',
              '| Forecaster | calmest | 2nd | 3rd | most stressed | top − bottom (90%) | label |', '|---|---|---|---|---|---|---|']
        for c, r in o['forecasters'].items():
            g = r['C']['groups']; tb = r['C']['top_minus_bottom']
            L.append(f'| {NAMES[c]} | ' + ' | '.join(f'{f2(x["value"])} ({pc(x["share_of_value"])})' for x in g)
                     + f' | {f2(tb["value"])} ({i2(tb["ci90"])}) | {tb["label"]} |')
        L += ['', '**D. Direction alone**', '', '| Forecaster | hit rate (90%) | sign payoff £/MWh (90%) | stressed: hit rate | stressed: payoff |',
              '|---|---|---|---|---|']
        for c, r in o['forecasters'].items():
            a, s = r['D_all'], r['D_stress']
            L.append(f'| {NAMES[c]} | {pc(a["hit_rate"]["value"])} ({ipc(a["hit_rate"]["ci90"])}) | {f2(a["sign_payoff"]["value"])} '
                     f'({i2(a["sign_payoff"]["ci90"])}) | {pc(s["hit_rate"]["value"])} ({ipc(s["hit_rate"]["ci90"])}) | '
                     f'{f2(s["sign_payoff"]["value"])} ({i2(s["sign_payoff"]["ci90"])}) |')
        L += ['', '**E. Tail of days, £/GWh**', '', '| Forecaster | worst 5% of days (90%) | best 5% (90%) | 8 January 2025 |', '|---|---|---|---|']
        for c, r in o['forecasters'].items():
            e = r['E']
            L.append(f'| {NAMES[c]} | {f0(e["worst_5pct"]["value"])} ({i0(e["worst_5pct"]["ci90"])}) | '
                     f'{f0(e["best_5pct"]["value"])} ({i0(e["best_5pct"]["ci90"])}) | {f0(e["on_2025_01_08"])} |')
        L.append('')
    L += ['## Sign-flip null (PLAN.md §7 D), all days', '',
          'Each day keeps its disagreements and price spreads; all its half-hours take one random sign. Label by day; by 7-day block in brackets.', '',
          '| Forecaster | part | hit rate | sign payoff £/MWh | value £/GWh |', '|---|---|---|---|---|']
    for c, r in res['null'].items():
        for part in ('all', 'stress'):
            cells = []
            for k, fm in (('hit_rate', pc), ('sign_payoff', f2), ('A', f0)):
                x = r[part][k]; cells.append(f'{fm(x["observed"])}: {x["by_day"]["label"]} ({x["by_7_day_block"]["label"]})')
            L.append(f'| {NAMES[c]} | {"all half-hours" if part == "all" else "top stress quarter"} | ' + ' | '.join(cells) + ' |')
    L += ['', '## Year by year (PLAN.md §7)', '']
    for y in res['by_year']:
        L += [f'**{y["period"][0]} to {y["period"][1]}** ({y["n_days"]} days{"" if y["full_year"] else "; no winter, not compared"})', '',
              '| Forecaster | value £/GWh (90%) | label | error ÷ NESO\'s |', '|---|---|---|---|']
        for c, r in y['forecasters'].items():
            L.append(f'| {NAMES[c]} | {f0(r["A"]["value"])} ({i0(r["A"]["ci90"])}) | {r["A"]["label"]} | {r["F"]["ratio"]:.3f} |')
        L.append('')
    L += ['## Checks (PLAN.md §8)', ''] + [f'- {k}: {"passed" if v["passed"] else "FAILED"}' for k, v in res['checks'].items()]
    L += ['', f'Commit {meta["public_commit"]}; script SHA-256 {meta["script_sha256"]}; seeds {SEED} (bootstrap) and '
          f'{NULL_SEED} (null); {meta["draws"]} draws in blocks of {st.BLOCK}.', '']
    return '\n'.join(L)


# ------------------------------------------------------------------ real run -------------------------------------------
def real():
    if not os.path.exists(SYNTH_JSON): sys.exit('Refused: run --synthetic first and commit score_synthetic.json.')
    if git('status', '--porcelain', '--', *GUARDED): sys.exit('Refused: these must be committed and unchanged: ' + ', '.join(GUARDED))
    try: tagged = git('show', f'{PLAN_TAG}:disagreement/PLAN.md')
    except subprocess.CalledProcessError: sys.exit(f'Refused: tag {PLAN_TAG} not found; run git fetch --tags.')
    with open(os.path.join(HERE, 'PLAN.md')) as fh:
        if tagged != fh.read().strip(): sys.exit(f'Refused: PLAN.md differs from tag {PLAN_TAG}.')
    with open(SYNTH_JSON) as fh: sy = json.load(fh)
    if not sy.get('passed') or sy.get('script_sha256') != st.sha(os.path.abspath(__file__)):
        sys.exit('Refused: the synthetic check has not passed with this script.')
    if st.sha(STAGE1) != STAGE1_SHA: sys.exit('Refused: imbalance_cost/results_stage1.json differs from its recorded hash.')
    with open(STAGE1) as fh: stage1 = json.load(fh)
    frame, prices, man, t1 = sc.load_real()                       # every file's hash is checked inside
    P = sc.per_day(frame, [NESO] + COLS); ok_days = [d for d, k in zip(P['days'], P['ok']) if k]
    checks = dict(days=check_days(ok_days, P['days'], stage1['dropped_days']))
    if not checks['days']['passed']: sys.exit('Refused: the scored days differ from the imbalance study\'s stage 1.')
    if not np.array_equal(boot(50, SEED, st.B), st.boot_idx(50, np.random.default_rng(SEED))):
        sys.exit('Refused: the bootstrap differs from the tails study\'s.')
    H = halfhours(frame, COLS, ok_days)
    res = analyse(H, t1)
    checks['reconciliation'] = check_reconciliation(H, COLS)
    checks['identity'] = check_identity(frame, ok_days, res, COLS, stage1)
    checks['hashes'] = dict(passed=True, note='every file read matched its recorded SHA-256, or the run stops')
    checks['synthetic'] = dict(passed=True, file='disagreement/score_synthetic.json')
    res['checks'] = checks
    failed = [k for k, v in checks.items() if not v['passed']]
    if failed: sys.exit('CHECKS FAILED, nothing written: ' + ', '.join(failed) + '\n' + json.dumps(st.round_floats(checks), default=str))
    res['headline'] = write_headline(res)
    meta = dict(public_commit=git('rev-parse', 'HEAD'), script_sha256=st.sha(os.path.abspath(__file__)), plan_tag=PLAN_TAG,
                seed=SEED, null_seed=NULL_SEED, draws=st.B, block=st.BLOCK, stage1_sha256=STAGE1_SHA,
                versions=dict(python=platform.python_version(), numpy=np.__version__, pandas=pd.__version__))
    out = dict(schema=SCHEMA, note='disagreement value, stage 1 (backtest pilot); plan frozen at tag ' + PLAN_TAG,
               meta=meta, **st.round_floats(res))
    with open(os.path.join(HERE, 'results_stage1.json'), 'w') as fh: json.dump(out, fh, indent=1, default=str)
    md = markdown(out, meta)
    with open(os.path.join(HERE, 'results_stage1.md'), 'w') as fh: fh.write(md)
    print(md)


# ------------------------------------------------------------------ synthetic check (PLAN.md §8.4) -------------------
def synth_frame(grid):
    """Invented outturn, prices and forecasts on the real calendar. |SP - MIP| is 20 on every half-hour, so a forecaster
    that always moves with the price earns exactly £20 per MWh of disagreement in every group. Each pair of half-hours
    shares a price state and a size; 'noise' moves up in one and down in the other, so its value is 0 in every pair."""
    f = grid.sort_values(['day', 'start_utc'], kind='mergesort').reset_index(drop=True)
    pos = f.groupby('day').cumcount().to_numpy(); n = f.groupby('day')['day'].transform('size').to_numpy()
    A = np.round(25000 + 5000 * np.sin(2 * np.pi * (pos / n - 0.3)))
    mip = np.round(60 + 40 * np.sin(2 * np.pi * (pos / n - 0.3)))   # whole numbers: every sum below is exact
    spread = np.where((pos // 2) % 2 == 0, 20.0, -20.0)
    pair = np.cumsum(pos % 2 == 0) - 1; size = 50 + (900 * pair) // pair.max()   # 50 to 950 MW, whole, rising in time
    alt = np.where(pos % 2 == 0, 1.0, -1.0); sgn = np.sign(spread); N = A + 300
    out = f[['day', 'start_utc']].copy(); out['outturn'] = A; out['mip'] = mip; out['system_price'] = mip + spread
    out[NESO] = N; out['same'] = N; out['noise'] = N + alt * size; out['follow'] = N + sgn * size
    out['bigonly'] = N + np.where(size > np.median(size), sgn, alt) * size
    return out, spread, size


def unit_rules():
    ok, n = True, 0
    for iv, l in (([-2, -1], NEG), ([1, 2], POS), ([0, 2], NCD0), ([-2, 0], NCD0), (None, UND)):
        n += 1; ok &= label0(iv) == l
    for iv, l in (([-2, -1], LOWER), ([1, 2], HIGHER), ([-1, 1], NCD), (None, UND)):
        n += 1; ok &= label_diff(iv) == l
    nl = np.arange(101.0)
    for obs, l in ((99, BEYOND), (50, WITHIN), (1, WORSE)): n += 1; ok &= label_null(obs, nl) == l
    args = (1.3124, [1.25, 1.38], None, 10.4, [-6.2, 27.9], -1.2, [-19.0, 16.0], 0.456, [0.1, 0.8], 0.1234, [-0.2, 0.4])
    want = {POS: '**clearly gained**', NEG: '**clearly lost**', NCD0: '**neither clearly gained nor lost**'}
    for lab, w in want.items():
        n += 1; a = list(args); a[2] = lab; h = headline(*a)
        good = h == ("In a backtest the foundation models may have seen in training, Chronos-2's day-ahead demand forecast had "
                     "1.31 times the daily error of NESO's (90% interval 1.25 to 1.38), and a supplier that bought it instead of "
                     f"NESO's would have {w} (10 £ per GWh of demand, 90% interval −6 to 28); for the weather regression the "
                     "figure was −1 £ per GWh (−19 to 16). Where Chronos-2 disagreed with NESO most (the largest quarter of its "
                     "disagreements), each MWh of disagreement was worth 0.46 £ (0.10 to 0.80), against 0.12 £ (−0.20 to 0.40) "
                     "in the smallest quarter.")
        if not good: print('FAIL headline\n' + h)
        ok &= good
    n += 1; a = list(args); a[2] = UND
    try: headline(*a); ok = False
    except ValueError: pass
    n += 1; ok &= list(rank_groups(np.array([5.0, 1, 1, 3, 2, 8, 7, 6]))) == [2, 0, 0, 1, 1, 3, 3, 2]
    n += 1; ok &= list(band_of(np.array([0.0, 250, 250.5, 500, 501, 1000, 1000.1]))) == [0, 0, 1, 1, 2, 2, 3]
    return bool(ok), n


def synthetic():
    t1, _ = asy.load_inputs()
    grid = pd.read_csv(st.FORECASTS, usecols=['day', 'start_utc'])
    fr, spread, size = synth_frame(grid)
    res = dict(script_sha256=st.sha(os.path.abspath(__file__)), draws=B_SYNTH, checks={}); ok_all = True

    def rec(name, good, **info):
        nonlocal ok_all
        res['checks'][name] = dict(passed=bool(good), **info); ok_all &= bool(good)
        print(('PASS ' if good else 'FAIL ') + name, flush=True)

    g, n = unit_rules(); rec('unit rules: labels, headline, groups, bands', g, n=n)
    cols = ['same', 'noise', 'follow', 'bigonly']; days = sorted(fr['day'].unique())
    H = halfhours(fr, cols, days); R = analyse(H, t1, cols, B=B_SYNTH); a = R['sets']['all']['forecasters']; nl = R['null']
    rec('same as NESO: v = 0 everywhere, direction undefined',
        a['same']['A']['value'] == 0 and a['same']['D_all']['hit_rate']['value'] is None
        and all(x['value'] is None for x in a['same']['B_bands']['groups']))
    groups = [x['value'] for x in a['noise']['B_groups']['groups']]
    iv = a['noise']['A']['ci90']
    rec('noise: value 0, interval contains 0, flat across groups, hit rate 1/2',
        abs(a['noise']['A']['value']) < 1e-9 and iv[0] <= 0 <= iv[1] and all(abs(x) < 0.01 for x in groups)
        and abs(a['noise']['D_all']['hit_rate']['value'] - 0.5) < 1e-12, groups=groups)
    code = H['code']; gwh = np.bincount(code, weights=H['A'] * 0.5) / 1000
    want = float(np.mean(np.bincount(code, weights=size * 20 * 0.5) / gwh))
    gf = [x['value'] for x in a['follow']['B_groups']['groups']]
    rec('follow: known value, clearly positive, hit rate 1, £20 per MWh in every group',
        abs(a['follow']['A']['value'] - want) < 1e-6 and a['follow']['A']['label'] == POS
        and a['follow']['D_all']['hit_rate']['value'] == 1.0 and all(abs(x - 20) < 1e-9 for x in gf), value=a['follow']['A']['value'], want=want)
    gb = [x['value'] for x in a['bigonly']['B_groups']['groups']]; tb = a['bigonly']['B_groups']['top_minus_bottom']
    rec('bigonly: value per MWh rises across groups', abs(gb[0]) < 0.05 and abs(gb[-1] - 20) < 0.05 and tb['label'] == POS, groups=gb)
    bands = a['follow']['B_bands']['groups']
    rec('bands: fixed edges, an empty band is undefined',
        bands[-1]['n_halfhours'] == 0 and bands[-1]['value'] is None and bands[-1]['ci90'] is None
        and all(abs(x['value'] - 20) < 1e-9 for x in bands[:-1]))
    rec('null: noise within chance, follow beyond chance (by day and by 7-day block)',
        all(nl['noise']['all'][k][t]['label'] == WITHIN for k in ('hit_rate', 'sign_payoff', 'A') for t in ('by_day', 'by_7_day_block'))
        and all(nl['follow']['all'][k][t]['label'] == BEYOND for k in ('hit_rate', 'sign_payoff', 'A') for t in ('by_day', 'by_7_day_block')))
    ds = day_stats(H, 'bigonly', np.ones(len(code), bool))['all']; nd = len(H['days'])
    o, m = flipped(ds, np.ones((1, nd))), flipped(ds, -np.ones((1, nd)))
    rec('null: flipping every day negates the figures', abs(m['hit_rate'][0] - (1 - o['hit_rate'][0])) < 1e-12
        and abs(m['sign_payoff'][0] + o['sign_payoff'][0]) < 1e-12 and abs(m['A'][0] + o['A'][0]) < 1e-12)
    rec('reconciliation identity', check_reconciliation(H, cols)['passed'])
    fr2 = fr.copy()
    for c, src in ((CH, 'follow'), (REF, 'noise'), (AVG, 'bigonly'), (sc.V1, 'noise'), (sc.S1, 'same'), (sc.TFM, 'noise'), (sc.CHW, 'noise')):
        fr2[c] = fr2[src]
    H2 = halfhours(fr2, COLS, days); R2 = analyse(H2, t1, COLS, B=B_SYNTH)
    rec('value equals NESO exposure minus own (imbalance_cost/score.py sums)', check_identity(fr2, days, R2, COLS)['passed'])
    cd = check_days(days, days + ['2099-01-01'], ['2099-01-01']); bad = check_days(days[1:], days, [])
    rec('days: equal as a set, periods partition every day', cd['passed'] and not bad['passed'], periods=cd['period_days'])
    h = write_headline(R2)
    rec('pipeline and headline with the real names', '**clearly gained**' in h and R2['sets']['T1']['n_days'] == 96
        and R2['sets']['evenings']['n_halfhours'] == 8 * len(days) and len(R2['by_year']) == 3, headline=h)
    rec('bootstrap equals the tails study\'s', np.array_equal(boot(50, SEED, st.B), st.boot_idx(50, np.random.default_rng(SEED))))
    res['passed'] = bool(ok_all)
    with open(SYNTH_JSON, 'w') as fh: json.dump(st.round_floats(res), fh, indent=1, default=str)
    print('synthetic: ' + ('PASS' if ok_all else 'FAIL'))
    return ok_all


if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('--synthetic', action='store_true')
    if ap.parse_args().synthetic: sys.exit(0 if synthetic() else 1)
    real()
