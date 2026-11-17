"""
Tails study, step 2 (tails/PLAN.md §9, frozen at tag tails-plan): score every forecaster on the tail day sets.
Committed before it runs; its outputs are committed after.

For: a reviewer checking that the metrics, intervals, headline templates and H1's reading follow PLAN.md §6-8.

Reads, after checking each file's SHA-256:
    weather_study/results/forecasts.csv                          outturn, regression_weather       (PLAN.md §4)
    weather_study/results/calendar_forecasts.csv                 chronos2_A, timestral_A           (PLAN.md §4)
    checkpoint0/lightgbm_forecasts.csv                           lightgbm_s1, _default, _s2        (PLAN.md §4)
    weather_study/correction1/timesfm25_single_day_forecasts.csv timesfm25_weather_single_day      (PLAN.md §4)
    results/attempt2/forecasts.csv                               neso, as scored by code/run.py; its outturn must
                                                                 equal forecasts.csv's on every shared half-hour
    tails/days.csv                                               the day sets; its hash must match tails/days.json
Writes tails/results.json and tails/results.md.

Metrics (PLAN.md §6). Error is outturn minus forecast, in MW. For each forecaster, each set and each complement
(broad: every other scored day; narrow: every other scored day in a calendar month holding one of the set's scored
days): (1) mean daily error; (2) ratio to the regression; (3) tail shift, the set's ratio over the complement's;
(4) bias, the mean signed error over the half-hours; (5) peak error, each day's highest outturn half-hour minus the
forecaster's highest forecast half-hour, averaged over days; (6) worst day; (7) 95th percentile of absolute
half-hourly errors. 90% intervals for (1)-(5) from one moving-block bootstrap of the scored days in calendar order
(blocks of 7, 2,000 draws, seed 20261117), shared by every metric. A draw with no days in a set or complement is
dropped for that metric, and the count is reported. A set with fewer than 10 scored days is reported day by day,
with no averages or intervals (PLAN.md §5). NESO is scored on the days its forecast is complete, with the
regression on the same days.

Reading (PLAN.md §6-8): no p-values. A tail shift is above or below 1 only where its interval lies wholly above or
below 1; a bias or peak error is positive or negative only where its interval lies wholly above or below 0. The
headline sentences (§8) and H1's outcome (§7) are chosen by rule and written into results.md.

H1's reading. "Supported" needs all four T1 conditions; where the T4 clause is assessed (T4 has at least 10 scored
days) it must hold as well. If the four T1 conditions hold and the T4 clause does not, H1 is "unclear".

Modes:
    python tails/score_tails.py --synthetic   invented forecasts with known tail shifts, biases and peak errors,
                                              on the real calendar and tails/days.csv; writes tails/synthetic.json
                                              and exits 1 if any check fails. No outturn or forecast is read.
    python tails/score_tails.py               the real run. Refused unless the synthetic check passed with this
                                              script and this days.csv, and both, with days.json and
                                              synthetic.json, are committed and unchanged.
    --days PATH                               (development only) a stand-in day-set file for --synthetic
"""
import argparse, hashlib, json, os, platform, subprocess, sys
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
FILES = {
    os.path.join(ROOT, 'weather_study', 'results', 'forecasts.csv'): 'b5f16561dcf1a26f8d7910bcca95cd137f677760c6f80153349034d4a85f7328',
    os.path.join(ROOT, 'weather_study', 'results', 'calendar_forecasts.csv'): '976e27ef28d0eef1ddf351c6557af9f771c308b94f389fe0f06b84ec86c8e2fe',
    os.path.join(ROOT, 'checkpoint0', 'lightgbm_forecasts.csv'): '812ffb251e7c4428ec1bb9f1e7467c51bc4f8ae55caf5b78b3fd0c840b6250cd',
    os.path.join(ROOT, 'weather_study', 'correction1', 'timesfm25_single_day_forecasts.csv'): '479ec318925cc59cd1e4f56a29ef9bc10d297fe3f8fa012482e1ce130dccd821',
}
FORECASTS, CALENDAR, LIGHTGBM, TIMESFM = list(FILES)
ATTEMPT2 = os.path.join(ROOT, 'results', 'attempt2', 'forecasts.csv')
ATTEMPT2_SHA = '891ff5031935fdb095298071550c20086d68bcc49e71908ef64169deb40a6027'
DAYS_CSV, DAYS_JSON = os.path.join(HERE, 'days.csv'), os.path.join(HERE, 'days.json')
SYNTH_JSON = os.path.join(HERE, 'synthetic.json')
DAY_INPUTS, BUILD = os.path.join(HERE, 'day_inputs.csv'), os.path.join(HERE, 'build_days.py')
GUARDED = ['tails/score_tails.py', 'tails/build_days.py', 'tails/days.csv', 'tails/days.json', 'tails/day_inputs.csv',
           'tails/synthetic.json', 'weather_study/WEATHER_LOCK.json', 'data/fetch_manifest.json']
SEED, B, BLOCK = 20261117, 2000, 7
SMALL = 10
SCHEMA = 1

REF = 'regression_weather'
COMPARED = ['chronos2_A', 'timesfm25_weather_single_day', 'lightgbm_s1']
SENSITIVITY = ['lightgbm_default', 'lightgbm_s2']
SHOWN = ['timestral_A', 'neso']
FORECASTERS = [REF] + COMPARED + SENSITIVITY + SHOWN
OPTIONAL = {'neso'}                       # scored on its own complete days; never drops a day for the others
NAMES = {REF: 'Weather regression', 'chronos2_A': 'Chronos-2', 'timesfm25_weather_single_day': 'TimesFM 2.5 (one day per call)',
         'lightgbm_s1': 'LightGBM, S1 settings', 'lightgbm_default': 'LightGBM, defaults (sensitivity)',
         'lightgbm_s2': 'LightGBM, S2 settings (sensitivity)', 'timestral_A': 'Timestral (shown, not compared)',
         'neso': 'NESO day-ahead (reference)'}
SETS = ('T1', 'T1b', 'T2', 'T3', 'T4')
SET_NAMES = {'T1': 'T1: coldest 10% by mean forecast temperature (primary)',
             'T1b': 'T1b: coldest 10% by coldest forecast half-hour (sensitivity)',
             'T2': "T2: top 10% by NESO's forecast peak (secondary)",
             'T3': 'T3: bank holidays and 24 December to 2 January (calendar; not a cold-day set)',
             'T4': "T4: forecast below LightGBM's training range (mechanism)"}
REGIONS = ('set', 'broad', 'narrow')


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''): h.update(b)
    return h.hexdigest()


def git(*a):
    return subprocess.run(['git', '-C', ROOT, *a], capture_output=True, text=True, check=True).stdout.strip()


# ------------------------------------------------------------------ loading --------------------------------------------
def check_files():
    bad = [f'{os.path.relpath(p, ROOT)}: {sha(p)}' for p, h in list(FILES.items()) + [(ATTEMPT2, ATTEMPT2_SHA)]
           if sha(p) != h]
    if bad: sys.exit('Refused: files differ from the hashes in score_tails.py:\n' + '\n'.join(bad))


def load_days(path):
    d = pd.read_csv(path, dtype={'day': str})
    assert set(d['set']) <= set(SETS), f'unknown set in {path}'
    return {s: sorted(set(d.loc[d['set'] == s, 'day'])) for s in SETS}


def load_real():
    check_files()
    f = pd.read_csv(FORECASTS, usecols=['day', 'start_utc', 'outturn', REF])
    cal = pd.read_csv(CALENDAR); tfm = pd.read_csv(TIMESFM); lg = pd.read_csv(LIGHTGBM)
    for g, cols in ((cal, ['chronos2_A', 'timestral_A']), (tfm, ['timesfm25_weather_single_day'])):
        assert (f['start_utc'].to_numpy() == g['start_utc'].to_numpy()).all(), 'forecast files misaligned'
        for c in cols: f[c] = g[c].to_numpy()
    n0 = len(f)
    f = f.merge(lg.drop(columns='day'), on='start_utc', how='left', validate='one_to_one')
    a2 = pd.read_csv(ATTEMPT2, usecols=['start_utc', 'outturn', 'neso']).rename(columns={'outturn': 'outturn_a2'})
    f = f.merge(a2, on='start_utc', how='left', validate='one_to_one')
    assert len(f) == n0
    both = f['outturn_a2'].notna()
    assert np.array_equal(f.loc[both, 'outturn'].to_numpy(), f.loc[both, 'outturn_a2'].to_numpy()), \
        "results/attempt2's outturn differs from forecasts.csv's"
    return f.drop(columns='outturn_a2')[['day', 'start_utc', 'outturn'] + FORECASTERS]


# ------------------------------------------------------------------ per-day quantities ---------------------------------
def per_day(frame):
    """Per scored day and forecaster: mean absolute error, signed-error sum, half-hour count, peak error; and the
    absolute half-hourly errors. A day is scored if outturn and every forecaster but NESO cover all its half-hours."""
    f = frame.sort_values(['day', 'start_utc'], kind='mergesort')
    need = ['outturn'] + [c for c in FORECASTERS if c not in OPTIONAL]
    full = f.groupby('day')[need].apply(lambda g: bool(np.isfinite(g.to_numpy(float)).all()))
    days = sorted(full.index[full.values]); dropped = sorted(full.index[~full.values])
    f = f[f['day'].isin(days)]
    g = f.groupby('day', sort=True)
    y_peak = g['outturn'].max().to_numpy()
    nhh = g.size().to_numpy().astype(float)
    out = dict(days=days, dropped=dropped, nhh=nhh, mae={}, ssum={}, peak={}, ok={}, abs_err={})
    day_codes = pd.Categorical(f['day'], categories=days).codes
    out['hh_day'] = day_codes
    for c in FORECASTERS:
        e = (f['outturn'] - f[c]).to_numpy(float)
        ok = pd.Series(np.isfinite(e)).groupby(day_codes).all().reindex(range(len(days)), fill_value=False).to_numpy()
        out['ok'][c] = ok
        out['mae'][c] = pd.Series(np.abs(e)).groupby(day_codes).mean().to_numpy()
        out['ssum'][c] = pd.Series(e).groupby(day_codes).sum().to_numpy()
        out['peak'][c] = y_peak - g[c].max().to_numpy()
        out['abs_err'][c] = np.abs(e)
    return out


def masks(days, members):
    """Set, broad and narrow complement masks over the scored days."""
    d = pd.Index(days); s = d.isin(members)
    months = set(pd.to_datetime(d[s]).to_period('M'))
    in_month = np.asarray(pd.to_datetime(d).to_period('M').isin(list(months)))
    return dict(set=np.asarray(s), broad=np.asarray(~s), narrow=in_month & np.asarray(~s))


def boot_idx(n, rng):
    nb = int(np.ceil(n / BLOCK)); starts = rng.integers(0, n - BLOCK + 1, size=(B, nb))
    return (starts[:, :, None] + np.arange(BLOCK)).reshape(B, -1)[:, :n]


def ci(x):
    x = x[np.isfinite(x)]
    if not len(x): return None
    lo, hi = np.quantile(x, [0.05, 0.95]); return [round(float(lo), 4), round(float(hi), 4)]


# ------------------------------------------------------------------ scoring --------------------------------------------
def region(P, I, c, m):
    """Metrics 1-7 for forecaster c on mask m (and the regression on the same days), with bootstrap draws."""
    m = m & P['ok'][c]
    mae, ref, ss, nh, pk = P['mae'][c], P['mae'][REF], P['ssum'][c], P['nhh'], P['peak'][c]
    n = int(m.sum())
    if n == 0: return dict(n_days=0), None
    M = m[I]; cnt = M.sum(1); keep = cnt > 0
    with np.errstate(invalid='ignore', divide='ignore'):
        draws = dict(mde=np.where(keep, (mae[I] * M).sum(1) / cnt, np.nan),
                     ratio=np.where(keep, (mae[I] * M).sum(1) / (ref[I] * M).sum(1), np.nan),
                     bias=np.where(keep, (ss[I] * M).sum(1) / (nh[I] * M).sum(1), np.nan),
                     peak=np.where(keep, (pk[I] * M).sum(1) / cnt, np.nan))
    hh = m[P['hh_day']]
    ad = np.asarray(P['days'])[m]; k = int(np.argmax(mae[m]))
    pt = dict(n_days=n, mde=float(mae[m].mean()), ratio=float(mae[m].sum() / ref[m].sum()),
              bias=float(ss[m].sum() / nh[m].sum()), peak=float(pk[m].mean()),
              worst_day=dict(day=str(ad[k]), mw=float(mae[m][k])),
              p95=float(np.percentile(P['abs_err'][c][hh], 95)), draws_dropped=int((~keep).sum()))
    for q in ('mde', 'ratio', 'bias', 'peak'): pt[q + '_ci90'] = ci(draws[q])
    return pt, draws


def day_by_day(P, c, m):
    m = m & P['ok'][c]; idx = np.nonzero(m)[0]
    return [dict(day=P['days'][i], mde=round(float(P['mae'][c][i]), 1),
                 ratio=round(float(P['mae'][c][i] / P['mae'][REF][i]), 4),
                 bias=round(float(P['ssum'][c][i] / P['nhh'][i]), 1), peak=round(float(P['peak'][c][i]), 1))
            for i in idx]


def score(frame, members):
    P = per_day(frame)
    n = len(P['days'])
    I = boot_idx(n, np.random.default_rng(SEED))
    out = dict(n_scored_days=n, days_not_scored=P['dropped'], sets={})
    keep_draws = {}
    for s in SETS:
        mk = masks(P['days'], members[s])
        n_set = int(mk['set'].sum())
        S = dict(n_listed=len(members[s]), n_scored=n_set,
                 listed_not_scored=sorted(set(members[s]) - set(P['days'])),
                 n_narrow=int(mk['narrow'].sum()), n_broad=int(mk['broad'].sum()),
                 narrow_months=sorted({d[:7] for d in np.asarray(P['days'])[mk['set']]}), forecasters={})
        if n_set < SMALL:
            S['day_by_day'] = True
            for c in FORECASTERS: S['forecasters'][c] = dict(days=day_by_day(P, c, mk['set']))
            out['sets'][s] = S; continue
        S['day_by_day'] = False
        for c in FORECASTERS:
            R, D = {}, {}
            for r in REGIONS: R[r], D[r] = region(P, I, c, mk[r])
            for comp in ('broad', 'narrow'):
                if D['set'] is None or D[comp] is None: R['shift_' + comp] = None; continue
                bs = D['set']['ratio'] / D[comp]['ratio']
                R['shift_' + comp] = dict(value=float(R['set']['ratio'] / R[comp]['ratio']), ci90=ci(bs),
                                          draws_dropped=int((~np.isfinite(bs)).sum()))
            S['forecasters'][c] = R; keep_draws[(s, c)] = D
        out['sets'][s] = S
    out['h1'] = h1(out, keep_draws)
    out['headlines'] = headlines(out)
    return out


# ------------------------------------------------------------------ reading rules --------------------------------------
def side(iv, ref):
    """'above', 'below' or 'includes' for an interval against a reference value."""
    if iv is None: return 'includes'
    return 'above' if iv[0] > ref else 'below' if iv[1] < ref else 'includes'


def h1_outcome(narrow, broad, bias, peak, t4):
    """PLAN.md §7. narrow, broad: sides of the T1 tail-shift intervals against 1; bias, peak: sides against 0;
    t4: 'holds', 'fails' or 'not assessed'. Returns (outcome, case)."""
    if narrow == 'below' and broad == 'below': return 'not supported', 'both tail shifts lie wholly below 1'
    if narrow == 'below': return 'not supported', 'the narrow tail shift lies wholly below 1'
    if broad == 'below': return 'not supported', 'the broad tail shift lies wholly below 1'
    if narrow != 'above' and broad != 'above': return 'not supported', 'neither tail shift lies wholly above 1'
    if narrow == 'above' and broad == 'above':
        if bias != 'above' and peak != 'above': return 'unclear', 'neither bias nor peak error clearly positive'
        if bias != 'above': return 'unclear', 'bias not clearly positive'
        if peak != 'above': return 'unclear', 'peak error not clearly positive'
        if t4 == 'fails': return 'unclear', 'T1 conditions met; T4 clause did not hold'
        return 'supported', 'all T1 conditions met' + ('; T4 clause held' if t4 == 'holds' else '; T4 clause not assessed')
    if broad == 'above': return 'unclear', 'a winter effect, not a cold-day effect'
    return 'unclear', 'a cold-day effect not seen against all other days'


def h1(out, draws):
    c = 'lightgbm_s1'; T1 = out['sets']['T1']
    if T1['day_by_day']:
        return dict(outcome='not assessed', case='T1 has fewer than 10 scored days',
                    sentence=f"H1 was not assessed: T1 has {T1['n_scored']} scored days, fewer than {SMALL}.")
    R = T1['forecasters'][c]
    sides = dict(narrow=side(R['shift_narrow']['ci90'], 1), broad=side(R['shift_broad']['ci90'], 1),
                 bias=side(R['set']['bias_ci90'], 0), peak=side(R['set']['peak_ci90'], 0))
    T4 = out['sets']['T4']; t4 = dict(n_scored=T4['n_scored'])
    if T4['n_scored'] == 0:
        t4['clause'] = 'not assessed'
        t4['why'] = "no scored day had a forecast temperature below the lowest in LightGBM's training rows, so T4 is empty"
    elif T4['n_scored'] < SMALL:
        t4['clause'] = 'not assessed'; t4['why'] = f"T4 has {T4['n_scored']} scored days, fewer than {SMALL}"
    else:
        a, b = draws[('T4', c)]['set']['bias'], draws[('T1', c)]['set']['bias']
        d = T4['forecasters'][c]['set']['bias'] - R['set']['bias']
        iv = ci(a - b)
        t4.update(difference_mw=round(float(d), 1), ci90=iv, draws_dropped=int((~np.isfinite(a - b)).sum()),
                  clause='holds' if d > 0 and side(iv, 0) == 'above' else 'fails')
    outcome, case = h1_outcome(sides['narrow'], sides['broad'], sides['bias'], sides['peak'], t4['clause'])
    return dict(outcome=outcome, case=case, sides=sides, t4=t4, sentence=h1_sentence(outcome, case, t4))


def h1_sentence(outcome, case, t4):
    t4s = {'holds': " Its bias was larger on days colder than any in its training rows (T4) than on T1.",
           'fails': '', 'not assessed': f" The T4 clause was not assessed: {t4.get('why', '')}."}[t4['clause']]
    body = {
        'all T1 conditions met': 'on the coldest tenth of days LightGBM S1 lost ground to the regression against other '
                                 'days of the same months and against all other days, and under-forecast both demand '
                                 'and the daily peak.',
        'both tail shifts lie wholly below 1': 'on the coldest tenth of days LightGBM S1 gained ground on the regression, '
                                               'so its relative error was lower, not higher, on the coldest days.',
        'the narrow tail shift lies wholly below 1': 'on the coldest tenth of days LightGBM S1 gained ground on the '
                                                     'regression against other days of the same months, so its relative '
                                                     'error was lower, not higher, on the coldest days.',
        'the broad tail shift lies wholly below 1': 'on the coldest tenth of days LightGBM S1 gained ground on the '
                                                    'regression against all other days, so its relative error was '
                                                    'lower, not higher, on the coldest days.',
        'neither tail shift lies wholly above 1': 'LightGBM S1 did not clearly lose ground to the regression on the '
                                                  'coldest tenth of days, against other days of the same months or '
                                                  'against all other days.',
        'neither bias nor peak error clearly positive': 'LightGBM S1 lost ground on the coldest tenth of days in both '
                                                        'comparisons, but did not clearly under-forecast demand or the '
                                                        'daily peak.',
        'bias not clearly positive': 'LightGBM S1 lost ground on the coldest tenth of days in both comparisons and '
                                     'under-forecast the daily peak, but did not clearly under-forecast demand.',
        'peak error not clearly positive': 'LightGBM S1 lost ground on the coldest tenth of days in both comparisons and '
                                           'under-forecast demand, but did not clearly under-forecast the daily peak.',
        'T1 conditions met; T4 clause did not hold': 'every condition on T1 held, but LightGBM S1\'s bias was not '
                                                     'clearly larger on days colder than any in its training rows (T4).',
        'a winter effect, not a cold-day effect': 'LightGBM S1 lost ground against all other days but not clearly '
                                                  'against other days of the same months: a winter effect, not a '
                                                  'cold-day effect.',
        'a cold-day effect not seen against all other days': 'LightGBM S1 lost ground against other days of the same '
                                                             'months but not clearly against all other days: a cold-day '
                                                             'effect not seen against all other days.',
    }[case.split(';')[0] if case.startswith('all T1') else case]
    return f"H1 was {outcome}: {body}" + (t4s if outcome == 'supported' or t4['clause'] == 'not assessed' else '')


TEMPLATES = {
    'chronos2_A': {
        'above': "In a backtest Chronos-2 may have seen in training, it lost ground to a weather regression on the coldest "
                 "tenth of days: relative to the regression, its error was {Z} higher than on other days of the same months.",
        'below': "In a backtest Chronos-2 may have seen in training, it gained ground on a weather regression on the coldest "
                 "tenth of days: relative to the regression, its error was {Z} lower than on other days of the same months.",
        'includes': "In a backtest Chronos-2 may have seen in training, it did not clearly lose or gain ground against a "
                    "weather regression on the coldest tenth of days, compared with other days of the same months "
                    "(tail shift {S}, 90% interval {L}–{U})."},
    'lightgbm_s1': {
        'above': "On the coldest tenth of days in a 960-day backtest, LightGBM lost ground to a weather regression: "
                 "relative to the regression, its error was {Z} higher than on other days of the same months.",
        'below': "On the coldest tenth of days in a 960-day backtest, LightGBM gained ground on a weather regression: "
                 "relative to the regression, its error was {Z} lower than on other days of the same months.",
        'includes': "On the coldest tenth of days in a 960-day backtest, LightGBM did not clearly lose or gain ground "
                    "against a weather regression, compared with other days of the same months "
                    "(tail shift {S}, 90% interval {L}–{U})."},
}


def headline(c, sh):
    k = side(sh['ci90'], 1); S = sh['value']; L, U = sh['ci90']
    return k, TEMPLATES[c][k].format(Z=f'{abs(S - 1) * 100:.1f}%', S=f'{S:.3f}', L=f'{L:.3f}', U=f'{U:.3f}')


def headlines(out):
    T1 = out['sets']['T1']
    if T1['day_by_day']: return dict(note='T1 has fewer than 10 scored days; no headline')
    h = {}
    for c in ('chronos2_A', 'lightgbm_s1'):
        k, s = headline(c, T1['forecasters'][c]['shift_narrow']); h[c] = dict(template=k, sentence=s)
    h['h1'] = out['h1']['sentence']
    return h


# ------------------------------------------------------------------ report ---------------------------------------------
def fmt_iv(v, iv, d=3):
    if v is None: return '—'
    return f"{v:.{d}f} ({iv[0]:.{d}f}–{iv[1]:.{d}f})" if iv else f"{v:.{d}f}"


def markdown(out, meta):
    h = out['headlines']
    L = ['# Tails: results (descriptive)', '',
         'Backtest days the foundation models may have seen in training. Error is outturn minus forecast (MW): positive '
         'means under-forecast. Tail shift = ratio to the regression on the set ÷ ratio on the complement. 90% intervals '
         'by moving-block bootstrap. A forecaster loses or gains ground only where the shift\'s interval excludes 1 '
         '(PLAN.md §6).', '',
         '**Headline (PLAN.md §8):**', '',
         h.get('chronos2_A', {}).get('sentence', h.get('note', '')), '',
         h.get('lightgbm_s1', {}).get('sentence', ''), '',
         h.get('h1', ''), '',
         f"Days scored: {out['n_scored_days']}; not scored: {len(out['days_not_scored'])}.", '']
    for s in SETS:
        S = out['sets'][s]
        L += [f"## {SET_NAMES[s]}", '',
              f"Scored days: {S['n_scored']} (listed {S['n_listed']}; not scored: {S['listed_not_scored'] or 'none'}). "
              f"Narrow complement: {S['n_narrow']} days in {len(S['narrow_months'])} months; broad: {S['n_broad']} days.", '']
        if S['n_scored'] == 0:
            L += ['No days: no metrics.', '']; continue
        if S['day_by_day']:
            L += [f'Fewer than {SMALL} scored days: reported day by day, without averages or intervals (PLAN.md §5).', '',
                  '| Forecaster | Day | Daily error (MW) | Ratio to regression | Bias (MW) | Peak error (MW) |',
                  '|---|---|---|---|---|---|']
            for c in FORECASTERS:
                for r in S['forecasters'][c]['days']:
                    L.append(f"| {NAMES[c]} | {r['day']} | {r['mde']:,.0f} | {r['ratio']:.3f} | {r['bias']:+,.0f} | {r['peak']:+,.0f} |")
            L.append(''); continue
        L += ['| Forecaster | Days | Mean daily error (MW) | Ratio to regression | Tail shift, narrow | Tail shift, broad | '
              'Bias (MW) | Peak error (MW) | Worst day (MW) | 95th pct (MW) |', '|---|---|---|---|---|---|---|---|---|---|']
        for c in FORECASTERS:
            R = S['forecasters'][c]; st = R['set']
            if not st.get('n_days'): L.append(f"| {NAMES[c]} | 0 | — | — | — | — | — | — | — | — |"); continue
            sn, sb = R['shift_narrow'], R['shift_broad']
            L.append(f"| {NAMES[c]} | {st['n_days']} | {st['mde']:,.0f} | {fmt_iv(st['ratio'], st['ratio_ci90'])} | "
                     f"{fmt_iv(sn['value'], sn['ci90']) if sn else '—'} | {fmt_iv(sb['value'], sb['ci90']) if sb else '—'} | "
                     f"{fmt_iv(st['bias'], st['bias_ci90'], 0)} | {fmt_iv(st['peak'], st['peak_ci90'], 0)} | "
                     f"{st['worst_day']['day']}: {st['worst_day']['mw']:,.0f} | {st['p95']:,.0f} |")
        L += ['', '| Forecaster | Ratio, narrow complement | Ratio, broad complement | Bias, narrow (MW) | Bias, broad (MW) |',
              '|---|---|---|---|---|']
        for c in FORECASTERS:
            R = S['forecasters'][c]
            if not R['narrow'].get('n_days') or not R['broad'].get('n_days'): continue
            n_, b_ = R['narrow'], R['broad']
            L.append(f"| {NAMES[c]} | {fmt_iv(n_['ratio'], n_['ratio_ci90'])} | {fmt_iv(b_['ratio'], b_['ratio_ci90'])} | "
                     f"{fmt_iv(n_['bias'], n_['bias_ci90'], 0)} | {fmt_iv(b_['bias'], b_['bias_ci90'], 0)} |")
        drops = {f"{c}/{k}": v for c in FORECASTERS for k, v in
                 (('narrow', (S['forecasters'][c].get('shift_narrow') or {}).get('draws_dropped', 0)),
                  ('broad', (S['forecasters'][c].get('shift_broad') or {}).get('draws_dropped', 0))) if v}
        L += ['', f"Bootstrap draws dropped (no days in the set or complement): {drops or 'none'}.", '']
    H = out['h1']
    L += ['## H1 (PLAN.md §7)', '', f"Outcome: **{H['outcome']}** ({H['case']}).", '']
    if 'sides' in H:
        L += ['| Condition on T1 (LightGBM S1) | Interval |', '|---|---|',
              f"| Narrow tail shift above 1 | {H['sides']['narrow']} |", f"| Broad tail shift above 1 | {H['sides']['broad']} |",
              f"| Bias above 0 | {H['sides']['bias']} |", f"| Peak error above 0 | {H['sides']['peak']} |",
              f"| T4 clause | {H['t4']['clause']}" + (f": bias T4 − T1 {H['t4']['difference_mw']:+,.0f} MW, 90% interval "
                                                      f"{H['t4']['ci90'][0]:+,.0f} to {H['t4']['ci90'][1]:+,.0f}"
                                                      if 'difference_mw' in H['t4'] else f" ({H['t4'].get('why', '')})") + ' |', '']
    L += ['## Provenance', '', '```', json.dumps(meta, indent=1), '```', '']
    return '\n'.join(L)


def round_floats(x):
    if isinstance(x, float): return round(x, 4)
    if isinstance(x, dict): return {k: round_floats(v) for k, v in x.items()}
    if isinstance(x, list): return [round_floats(v) for v in x]
    return x


# ------------------------------------------------------------------ real run -------------------------------------------
def real():
    for p in (DAYS_CSV, DAYS_JSON, SYNTH_JSON):
        if not os.path.exists(p): sys.exit(f'Refused: {os.path.relpath(p, ROOT)} is missing (build_days.py, then --synthetic).')
    if git('status', '--porcelain', '--', *GUARDED):
        sys.exit('Refused: these must be committed and unchanged: ' + ', '.join(GUARDED))
    dj = json.load(open(DAYS_JSON))
    if sha(DAYS_CSV) != dj['days_csv_sha256']: sys.exit('Refused: days.csv differs from the hash in days.json.')
    if sha(DAY_INPUTS) != dj['day_inputs_csv_sha256']: sys.exit('Refused: day_inputs.csv differs from the hash in days.json.')
    if sha(BUILD) != dj['provenance']['script_sha256']:
        sys.exit('Refused: days.json was not made by the committed build_days.py.')
    lock = json.load(open(os.path.join(ROOT, 'weather_study', 'WEATHER_LOCK.json')))['files_sha256']
    man = json.load(open(os.path.join(ROOT, 'data', 'fetch_manifest.json')))['files']
    for k, h in dj['inputs_sha256'].items():                  # the build's inputs, against the committed manifests
        want = lock.get('~/gb-weather-data/backtest/' + k) or (man.get(k) or {}).get('sha256')
        if want is not None and want != h: sys.exit(f'Refused: days.json records {k} with a hash the manifests do not.')
    sy = json.load(open(SYNTH_JSON))
    if not sy.get('passed') or sy.get('script_sha256') != sha(os.path.abspath(__file__)) or sy.get('days_csv_sha256') != sha(DAYS_CSV):
        sys.exit('Refused: the synthetic check has not passed with this script and this days.csv.')
    frame = load_real()
    out = score(frame, load_days(DAYS_CSV))
    meta = dict(public_commit=git('rev-parse', 'HEAD'), script_sha256=sha(os.path.abspath(__file__)),
                days_csv_sha256=sha(DAYS_CSV), files_sha256={os.path.relpath(p, ROOT): h for p, h in FILES.items()},
                attempt2_sha256=ATTEMPT2_SHA, seed=SEED, draws=B, block=BLOCK,
                versions=dict(python=platform.python_version(), numpy=np.__version__, pandas=pd.__version__))
    out = dict(schema=SCHEMA, note='tails study; descriptive; plan frozen at tag tails-plan', meta=meta, **round_floats(out))
    json.dump(out, open(os.path.join(HERE, 'results.json'), 'w'), indent=1)
    md = markdown(out, meta)
    open(os.path.join(HERE, 'results.md'), 'w').write(md)
    print(md)


# ------------------------------------------------------------------ synthetic check ------------------------------------
A_MW, PEAK_MW, DELTA = 400.0, 6000.0, 0.2


def synth_case(grid, members, spec, seed):
    """Invented outturn and forecasts on the real calendar. Every forecaster's error on day d is A * g_d * u, with
    u = +1 or -1 on each half-hour: |error| = A * g_d, so the ratio to the regression (g = 1) on any days is the mean
    of g. A day's share p of positive half-hours sets its bias; the sign at the outturn peak (a 6,000 MW spike, larger
    than any forecast error swing) sets its peak error. g_d = level x (1 + 0.2 z_d), with z demeaned within each design
    region (T1, the rest of T1's months, all other days), so each region's mean g is its level exactly."""
    rng = np.random.default_rng(seed)
    days = sorted(grid['day'].unique()); n = len(days)
    T1, T4 = set(members['T1']), set(members['T4'])
    t1_months = {d[:7] for d in T1}
    reg = np.array(['set' if d in T1 else 'narrow' if d[:7] in t1_months else 'rest' for d in days])
    g0 = grid.sort_values(['day', 'start_utc'], kind='mergesort').reset_index(drop=True)
    pos = g0.groupby('day').cumcount().to_numpy(); H = g0.groupby('day')['day'].transform('size').to_numpy()
    dix = pd.Categorical(g0['day'], categories=days).codes
    kpk = np.minimum(34, H - 1)                                   # the outturn's peak half-hour, by position
    y = 30000 + 1000 * np.cos(2 * np.pi * pos / H) + PEAK_MW * (pos == kpk)
    frame = g0[['day', 'start_utc']].copy(); frame['outturn'] = y
    design = {}
    Hd = np.bincount(dix)
    for c in FORECASTERS:
        sp = spec.get(c, {})
        lev = sp.get('level', {}); level = np.array([lev.get(r, 1.0) for r in reg])
        z = np.clip(rng.normal(size=n), -2.5, 2.5)
        for r in ('set', 'narrow', 'rest'):
            k = reg == r
            if k.any(): z[k] -= z[k].mean()
        g = level * (1 + (0.0 if c == REF else DELTA) * z)
        pr = sp.get('p', {})
        p = np.array([pr.get('T4', pr.get('T1', 0.5)) if d in T4 else pr.get('T1', 0.5) if d in T1 else 0.5 for d in days])
        npos = np.rint(p * Hd).astype(int)
        psign = np.array([sp.get('peak', {}).get('T1' if d in T1 else 'other', 1) for d in days])
        npos = np.clip(npos, np.where(psign > 0, 1, 0), np.where(psign > 0, Hd, Hd - 1))
        u = np.empty(len(g0))
        for i in range(n):
            rows = np.nonzero(dix == i)[0]; k = rows[pos[rows] == kpk[rows]][0]
            others = [r for r in rows if r != k]
            u[rows] = -1.0
            if psign[i] > 0: u[k] = 1.0; u[others[:npos[i] - 1]] = 1.0
            else: u[others[:npos[i]]] = 1.0
        x = A_MW * g[dix] * u
        frame[c] = y - x
        design[c] = dict(g=g, npos=npos, peak=psign * A_MW * g)
    for c, (d, hh) in spec.get('_blank', {}).items():                  # one blank half-hour: the day is not scored
        frame.loc[(frame['day'] == d) & (frame.groupby('day').cumcount() == hh), c] = np.nan
    return frame, design, days, Hd


def expected(design, days, Hd, members, unscored):
    """Each metric from the design arrays, without per_day or masks: the independent side of the check."""
    keep = np.array([d not in unscored for d in days]); dd = [d for d, k in zip(days, keep) if k]
    E = {}
    for s in SETS:
        S = set(members[s]) & set(dd); mon = {d[:7] for d in S}
        reg = {'set': np.array([d in S for d in days]) & keep,
               'broad': np.array([d not in S for d in days]) & keep,
               'narrow': np.array([d not in S and d[:7] in mon for d in days]) & keep}
        for c, D in design.items():
            for r, m in reg.items():
                if not m.any(): continue
                g = D['g'][m]
                E[(s, c, r)] = dict(mde=A_MW * g.mean(), ratio=g.mean() / design[REF]['g'][m].mean(),
                                    bias=A_MW * (g * (2 * D['npos'][m] - Hd[m])).sum() / Hd[m].sum(),
                                    peak=D['peak'][m].mean(), worst=A_MW * g.max(),
                                    p95=np.percentile(np.repeat(A_MW * g, Hd[m]), 95))
    for c, D in design.items():
        for i, d in enumerate(days):
            if keep[i]:
                E[('day', c, d)] = dict(mde=A_MW * D['g'][i], ratio=D['g'][i] / design[REF]['g'][i],
                                        bias=A_MW * D['g'][i] * (2 * D['npos'][i] - Hd[i]) / Hd[i], peak=D['peak'][i])
    return E


def synthetic_cases(members, n_t4):
    """Each case fixes Chronos-2's and LightGBM S1's T1 levels (set, rest of T1's months, all other days), LightGBM's
    share of positive half-hours (bias) on T1 and T4, the sign of its error at the outturn's peak, and the expected
    template and H1 outcome. Cases D and E put a negative error at the peak on days whose other errors are mostly
    positive, so the peak error differs from the day's largest error."""
    t4c = 'holds' if n_t4 >= SMALL else 'not assessed'
    sup = ('supported', 'all T1 conditions met; T4 clause ' + ('held' if t4c == 'holds' else 'not assessed'))
    up = dict(p={'T1': 0.75, 'T4': 0.95}, peak={'T1': 1, 'other': 1})
    cases = {
        'A_lose_supported': dict(spec={'chronos2_A': dict(level=dict(set=1.4)),
                                       'lightgbm_s1': dict(level=dict(set=1.35, rest=0.95), **up)},
                                 want=dict(chronos2_A='above', lightgbm_s1='above', h1=sup)),
        'B_gain_winter': dict(spec={'chronos2_A': dict(level=dict(set=0.7)),
                                    'lightgbm_s1': dict(level=dict(set=1.3, narrow=1.3, rest=0.9), **up)},
                              want=dict(chronos2_A='below', lightgbm_s1='includes',
                                        h1=('unclear', 'a winter effect, not a cold-day effect'))),
        'C_none_cold_not_broad': dict(spec={'lightgbm_s1': dict(level='cold_not_broad', **up)},
                                      want=dict(chronos2_A='includes', lightgbm_s1='above',
                                                h1=('unclear', 'a cold-day effect not seen against all other days'))),
        'D_not_supported': dict(spec={'chronos2_A': dict(level=dict(set=1.25)),
                                      'lightgbm_s1': dict(level=dict(set=0.8), p={'T1': 0.3}, peak={'T1': -1, 'other': -1})},
                                want=dict(chronos2_A='above', lightgbm_s1='below',
                                          h1=('not supported', 'both tail shifts lie wholly below 1'))),
        'E_unclear_peak_over': dict(spec={'lightgbm_s1': dict(level=dict(set=1.35), p={'T1': 0.7}, peak={'T1': -1})},
                                  want=dict(chronos2_A='includes', lightgbm_s1='above',
                                            h1=('unclear', 'peak error not clearly positive'))),
        'F_none_not_supported': dict(spec={}, want=dict(chronos2_A='includes', lightgbm_s1='includes',
                                                        h1=('not supported', 'neither tail shift lies wholly above 1'))),
    }
    if n_t4 >= SMALL:
        cases['G_t4_fails'] = dict(spec={'lightgbm_s1': dict(level=dict(set=1.35), p={'T1': 0.9, 'T4': 0.55},
                                                             peak={'T1': 1, 'other': 1})},
                                   want=dict(chronos2_A='includes', lightgbm_s1='above',
                                             h1=('unclear', 'T1 conditions met; T4 clause did not hold')))
    return cases


def resolve_levels(spec, days, members):
    """'cold_not_broad': LightGBM 1.3 on T1, 0.85 on the rest of T1's months, and on all other days the level that
    makes the broad complement's mean exactly 1.3, so the broad shift is 1 and the narrow shift 1.3 / 0.85."""
    for c, sp in spec.items():
        if sp.get('level') != 'cold_not_broad': continue
        T1 = set(members['T1']); mon = {d[:7] for d in T1}
        nn = sum(d not in T1 and d[:7] in mon for d in days); nr = sum(d[:7] not in mon for d in days)
        sp['level'] = dict(set=1.3, narrow=0.85, rest=(1.3 * (nn + nr) - 0.85 * nn) / nr)
    return spec


def unit_rules():
    """The reading rules on hand-made intervals, every branch."""
    t = []
    t.append(side([1.01, 1.2], 1) == 'above' and side([0.8, 0.99], 1) == 'below' and side([1.0, 1.2], 1) == 'includes'
             and side([0.8, 1.0], 1) == 'includes' and side(None, 1) == 'includes')
    cases = [(('above', 'above', 'above', 'above', 'not assessed'), 'supported'),
             (('above', 'above', 'above', 'above', 'holds'), 'supported'),
             (('above', 'above', 'above', 'above', 'fails'), 'unclear'),
             (('above', 'above', 'includes', 'above', 'holds'), 'unclear'),
             (('above', 'above', 'above', 'below', 'holds'), 'unclear'),
             (('includes', 'above', 'above', 'above', 'holds'), 'unclear'),
             (('above', 'includes', 'above', 'above', 'holds'), 'unclear'),
             (('includes', 'includes', 'above', 'above', 'holds'), 'not supported'),
             (('below', 'above', 'above', 'above', 'holds'), 'not supported'),
             (('above', 'below', 'above', 'above', 'holds'), 'not supported')]
    t += [h1_outcome(*a)[0] == want for a, want in cases]
    t.append(h1_outcome('includes', 'above', 'above', 'above', 'holds')[1] == 'a winter effect, not a cold-day effect')
    t.append(h1_outcome('above', 'includes', 'above', 'above', 'holds')[1] == 'a cold-day effect not seen against all other days')
    t.append(h1_outcome('below', 'below', 'above', 'above', 'holds')[1] == 'both tail shifts lie wholly below 1')
    t.append(h1_outcome('above', 'above', 'includes', 'above', 'holds')[1] == 'bias not clearly positive')
    t.append(h1_outcome('above', 'above', 'above', 'below', 'holds')[1] == 'peak error not clearly positive')
    t.append(h1_outcome('above', 'above', 'includes', 'includes', 'holds')[1] == 'neither bias nor peak error clearly positive')
    t.append(all(h1_sentence(*h1_outcome('above', 'above', b, q, 'holds'), {'clause': 'holds'})
                 for b in ('above', 'below', 'includes') for q in ('above', 'below', 'includes')))
    t.append(h1_outcome('below', 'includes', 'above', 'above', 'holds')[1] == 'the narrow tail shift lies wholly below 1')
    t.append(h1_outcome('includes', 'below', 'above', 'above', 'holds')[1] == 'the broad tail shift lies wholly below 1')
    t.append(all(h1_sentence(*h1_outcome(*a), {'clause': 'holds'}) for a in
                 [(x, y, 'above', 'above', 'holds') for x in ('above', 'below', 'includes') for y in ('above', 'below', 'includes')]))
    k, s = headline('lightgbm_s1', dict(value=1.234, ci90=[1.1, 1.4]))
    t.append(k == 'above' and '23.4% higher' in s)
    k, s = headline('chronos2_A', dict(value=0.9, ci90=[0.8, 0.95]))
    t.append(k == 'below' and '10.0% lower' in s)
    k, s = headline('chronos2_A', dict(value=1.02, ci90=[0.95, 1.1]))
    t.append(k == 'includes' and 'tail shift 1.020, 90% interval 0.950–1.100' in s)
    return all(t), len(t)


def unit_peak():
    """Peak error is the difference of the two daily peaks, wherever each falls (PLAN.md §6, metric 5). Hand-made days
    where it differs from the error at the outturn's peak half-hour and from the day's largest error."""
    rows = []
    for d, y, f in (('2025-01-01', [10, 50, 20, 30], [10, 40, 20, 70]),    # peaks 50 and 70: -20 (not +10, not +10)
                    ('2025-01-02', [5, 5, 9, 5], [6, 8, 1, 5])):           # peaks 9 and 8: +1 (not +8, not +8)
        for k in range(4): rows.append(dict(day=d, start_utc=f'{d}T{k:02d}:00:00+00:00', outturn=float(y[k]),
                                            **{c: float(f[k]) for c in FORECASTERS}))
    P = per_day(pd.DataFrame(rows))
    return all(np.array_equal(P['peak'][c], [-20.0, 1.0]) for c in FORECASTERS)


def unit_bootstrap():
    """The bootstrap's constants are the plan's; each draw is moving blocks of 7 consecutive days; the same seed gives
    the same draws; a draw with no days in a region is dropped and counted."""
    t = [SEED == 20261117, B == 2000, BLOCK == 7]
    n = 960; I = boot_idx(n, np.random.default_rng(SEED)); I2 = boot_idx(n, np.random.default_rng(SEED))
    t.append(I.shape == (B, n) and np.array_equal(I, I2) and I.min() >= 0 and I.max() < n)
    full = (n // BLOCK) * BLOCK
    t.append(bool((np.diff(I[:, :full].reshape(B, -1, BLOCK), axis=2) == 1).all()))
    # dropped draws: a one-day region, counted independently
    rows = [dict(day=f'2025-{1 + i // 28:02d}-{1 + i % 28:02d}', start_utc=f'{i:04d}', outturn=100.0,
                 **{c: 90.0 + (i % 3) for c in FORECASTERS}) for i in range(60)]
    P = per_day(pd.DataFrame(rows)); I3 = boot_idx(60, np.random.default_rng(1))
    m = np.zeros(60, bool); m[17] = True
    pt, _ = region(P, I3, 'chronos2_A', m)
    t.append(pt['draws_dropped'] == int((~(I3 == 17).any(1)).sum()) and pt['draws_dropped'] > 0)
    return all(t), len(t)


def compare(out, E, members, unscored):
    """Point estimates equal the design to 1e-9 (relative); the design lies in every 90% interval."""
    bad = []
    for s in SETS:
        S = out['sets'][s]
        for c in FORECASTERS:
            if S['day_by_day']:
                for r in S['forecasters'][c]['days']:
                    e = E[('day', c, r['day'])]
                    for q, tol in (('mde', 0.05), ('ratio', 5e-5), ('bias', 0.05), ('peak', 0.05)):
                        if abs(r[q] - e[q]) > tol: bad.append((s, c, r['day'], q, r[q], e[q]))
                continue
            R = S['forecasters'][c]
            for r in REGIONS:
                e = E.get((s, c, r))
                if e is None: continue
                pt = R[r]
                for q in ('mde', 'ratio', 'bias', 'peak', 'p95'):
                    if not np.isclose(pt[q], e[q], rtol=1e-9, atol=1e-6): bad.append((s, c, r, q, pt[q], e[q]))
                if not np.isclose(pt['worst_day']['mw'], e['worst'], rtol=1e-9): bad.append((s, c, r, 'worst'))
                for q in ('mde', 'ratio', 'bias', 'peak'):
                    iv = pt[q + '_ci90']
                    if iv and not (iv[0] - 1e-9 <= e[q] <= iv[1] + 1e-9): bad.append((s, c, r, q + '_ci', iv, e[q]))
            for comp in ('broad', 'narrow'):
                es, ec = E.get((s, c, 'set')), E.get((s, c, comp))
                if es is None or ec is None: continue
                want = es['ratio'] / ec['ratio']; sh = R['shift_' + comp]
                if not np.isclose(sh['value'], want, rtol=1e-9): bad.append((s, c, 'shift_' + comp, sh['value'], want))
                if sh['ci90'] and not (sh['ci90'][0] - 1e-9 <= want <= sh['ci90'][1] + 1e-9):
                    bad.append((s, c, 'shift_' + comp + '_ci', sh['ci90'], want))
        if S['n_scored'] != len(set(members[s]) - set(unscored)): bad.append((s, 'n_scored'))
    return bad


def synthetic(days_path):
    check_files()
    members = load_days(days_path)
    grid = pd.read_csv(FORECASTS, usecols=['day', 'start_utc'])           # the real calendar; no values
    all_days = sorted(grid['day'].unique())
    in_any = set().union(*members.values())
    blank_day = next(d for d in all_days if d not in in_any)
    n_t4 = len(members['T4'])
    res = dict(days_csv=os.path.relpath(days_path, ROOT), days_csv_sha256=sha(days_path),
               script_sha256=sha(os.path.abspath(__file__)), set_sizes={s: len(v) for s, v in members.items()}, cases={})
    ok_rules, n_rules = unit_rules(); res['unit_rules'] = dict(passed=ok_rules, checks=n_rules)
    ok_peak = unit_peak(); res['unit_peak'] = dict(passed=ok_peak)
    ok_boot, n_boot = unit_bootstrap(); res['unit_bootstrap'] = dict(passed=ok_boot, checks=n_boot)
    for k in ('unit_rules', 'unit_peak', 'unit_bootstrap'): print(('PASS ' if res[k]['passed'] else 'FAIL ') + k)
    ok_all = ok_rules and ok_peak and ok_boot
    # the real sets, then two constructed T4 sets drawn from T1 (14 and 5 days) to exercise the T4 clause and the
    # day-by-day path; the constructed sets stand in for a T4 the real data did not produce
    t1 = sorted(members['T1'])
    runs = [('', members, synthetic_cases(members, n_t4))]
    for n4 in (14, 5):
        mem = dict(members, T4=t1[:n4]); cs = synthetic_cases(mem, n4)
        runs.append((f'T4x{n4}_', mem, {k: cs[k] for k in cs if k[0] in 'AG'}))
    ok_all &= run_cases(runs, grid, all_days, blank_day, res)
    if n_t4 < SMALL:
        res['note_t4'] = (f'The real T4 has {n_t4} days, fewer than {SMALL}: on the real sets the clause is not assessed. '
                          'The T4x14_ and T4x5_ cases use constructed T4 sets drawn from T1.')
    res['passed'] = bool(ok_all)
    json.dump(round_floats(res), open(SYNTH_JSON if days_path == DAYS_CSV else os.path.join(HERE, 'synthetic_dev.json'), 'w'),
              indent=1, default=str)
    print('synthetic: ' + ('PASS' if ok_all else 'FAIL'))
    return ok_all


def run_cases(runs, grid, all_days, blank_day, res):
    ok_all = True
    flat = [(prefix + name, name, members, case) for prefix, members, cases in runs for name, case in cases.items()]
    for i, (name, base, members, case) in enumerate(flat):
        spec = resolve_levels({k: dict(v) for k, v in case['spec'].items()}, all_days, members)
        if base.startswith('A'): spec['_blank'] = {'timesfm25_weather_single_day': (blank_day, 3)}
        frame, design, days, Hd = synth_case(grid, members, spec, seed=1000 + i)
        unscored = {blank_day} if '_blank' in spec else set()
        out = score(frame, members)
        E = expected(design, days, Hd, members, unscored)
        bad = compare(out, E, members, unscored)
        got = dict(chronos2_A=out['headlines']['chronos2_A']['template'],
                   lightgbm_s1=out['headlines']['lightgbm_s1']['template'], h1=(out['h1']['outcome'], out['h1']['case']))
        want = case['want']
        match = got['chronos2_A'] == want['chronos2_A'] and got['lightgbm_s1'] == want['lightgbm_s1'] and \
            tuple(got['h1']) == tuple(want['h1'])
        scored_ok = out['days_not_scored'] == sorted(unscored)
        passed = not bad and match and scored_ok
        if base.startswith('A'):                                            # deterministic: the same output again
            again = score(synth_case(grid, members, spec, seed=1000 + i)[0], members)
            passed &= json.dumps(round_floats(again), sort_keys=True) == json.dumps(round_floats(out), sort_keys=True)
        T1 = out['sets']['T1']['forecasters']
        res['cases'][name] = dict(passed=bool(passed), expected=want, got=got, mismatches=[str(b) for b in bad[:20]],
                                  n_mismatches=len(bad), days_not_scored=out['days_not_scored'],
                                  lightgbm_T1=dict(narrow=T1['lightgbm_s1']['shift_narrow'],
                                                   broad=T1['lightgbm_s1']['shift_broad'],
                                                   bias=[T1['lightgbm_s1']['set']['bias'], T1['lightgbm_s1']['set']['bias_ci90']],
                                                   peak=[T1['lightgbm_s1']['set']['peak'], T1['lightgbm_s1']['set']['peak_ci90']]),
                                  chronos_T1_narrow=T1['chronos2_A']['shift_narrow'], h1_t4=out['h1'].get('t4'),
                                  headlines=out['headlines'])
        ok_all &= passed
        print(('PASS ' if passed else 'FAIL ') + name, json.dumps(got), f'{len(bad)} mismatches', flush=True)
    return ok_all


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--synthetic', action='store_true'); ap.add_argument('--days', default=DAYS_CSV)
    a = ap.parse_args()
    if a.synthetic: sys.exit(0 if synthetic(os.path.abspath(a.days)) else 1)
    if a.days != DAYS_CSV: sys.exit('--days is for --synthetic only.')
    real()
