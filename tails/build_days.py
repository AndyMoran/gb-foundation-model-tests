"""
Tails study, step 1 (tails/PLAN.md §9, frozen at tag tails-plan): build the tail day sets. Committed before it runs;
its outputs are committed after.

For: a reviewer checking that every tail set was chosen from information known before the forecasts were issued.

Sets (PLAN.md §5), over the backtest days of weather_study/results/forecasts.csv (16 March 2024 to 31 October 2026):
    T1   the coldest 10% by mean forecast temperature over D's half-hours                       primary
    T1b  the coldest 10% by D's coldest forecast half-hour                                     sensitivity
    T2   the top 10% by NESO's day-ahead forecast of D's peak half-hourly demand               secondary
    T3   bank holidays (England and Wales) and 24 December to 2 January                        secondary
    T4   days with a forecast half-hour below the lowest temperature in LightGBM's training    mechanism
         rows for D (target days D-366 .. D-2)
"10%" is floor(0.1 x the number of days ranked). Ties at the boundary are broken by date, earliest first.

What it reads, and what it does not:
    forecast temperature  the population-weighted national 2 m temperature the regression received for D:
                          regression_weather.weather_for (gb-weather-private), on the frozen backtest inputs
    LightGBM's rows       built by lightgbm_weather.LightGBMW.features, the code that made the scored forecasts.
                          Which training rows exist depends on which INDO half-hours are present, so the script
                          reads INDO's timestamps and replaces every value by 1.0 before any array is built. No
                          demand value reaches any array; the temperature column is unaffected (checked in
                          --synthetic against the same build on real-valued demand).
    NESO's forecast       code/inputs.neso_forecast on data/neso_dayahead_publications.csv, as the weather study
                          used it; checked against the `neso` column of results/attempt2/forecasts.csv
    calendar              data/bank_holidays_ew.json
    backtest days         the `day` column of weather_study/results/forecasts.csv only
No outturn and no forecast being scored is read.

Every input file is hashed and checked: the weather study's backtest files against WEATHER_LOCK.json (and the inputs
file also against build.json, as the plan says); data/ files against data/fetch_manifest.json; the forecasts file
and results/attempt2/forecasts.csv against fixed hashes. The script refuses to run while it, code/ or
gb-weather-private's weather/ has uncommitted changes, and records both commits.

Outputs:
    tails/days.csv        one row per (set, day): set, day, rank, value, reason
    tails/day_inputs.csv  every backtest day's selection inputs (no outturn, no scored forecast)
    tails/days.json       counts per set, by winter and by month, pairwise overlaps, boundary values, days left
                          out of T2, the T4 cross-check, file hashes, commits and versions; days.csv's SHA-256

Modes:
    python tails/build_days.py              the real build (Andy's machine, environment gbcp0)
    python tails/build_days.py --synthetic  checks on synthetic data only; writes tails/build_days_synthetic.json

Paths: this repository's root; gb-weather-private at $GBWX_PRIVATE (default ~/gb-weather-private); the weather
data at ~/gb-weather-data.
"""
import argparse, hashlib, json, math, os, platform, subprocess, sys
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
PRIVATE = os.path.expanduser(os.environ.get('GBWX_PRIVATE', '~/gb-weather-private'))
os.environ.setdefault('GBFM_PUBLIC', ROOT)                   # lightgbm_weather finds this repository through it
sys.path.insert(0, os.path.join(PRIVATE, 'weather')); sys.path.insert(0, os.path.join(ROOT, 'code'))
import common as C, inputs as I, baselines as B             # noqa: E402  (this repository's code/)
import regression_weather as RW                             # noqa: E402  (gb-weather-private's weather/)

TAG = '2024-03-16_2026-10-31'
BT = os.path.join(os.path.expanduser('~/gb-weather-data'), 'backtest')
FORECASTS = os.path.join(ROOT, 'weather_study', 'results', 'forecasts.csv')
FORECASTS_SHA = 'b5f16561dcf1a26f8d7910bcca95cd137f677760c6f80153349034d4a85f7328'      # PLAN.md §4
ATTEMPT2 = os.path.join(ROOT, 'results', 'attempt2', 'forecasts.csv')
ATTEMPT2_SHA = '891ff5031935fdb095298071550c20086d68bcc49e71908ef64169deb40a6027'       # at commit 8410639
BACKTEST = {k: os.path.join(BT, f'{k}_{TAG}{ext}') for k, ext in
            (('inputs', '.csv.gz'), ('days', '.jsonl'), ('era5_halfhourly', '.csv.gz'), ('build', '.json'))}
DATA = {k: os.path.join(ROOT, 'data', k) for k in ('neso_dayahead_publications.csv', 'bank_holidays_ew.json', 'indo.csv')}
SETS = ('T1', 'T1b', 'T2', 'T3', 'T4')
SHARE = 0.1
NESO_TOL_MW = 0.5                                            # NESO publications are whole MW
TEMP_TOL_C = 1e-9
SCHEMA = 1


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''): h.update(b)
    return h.hexdigest()


def git(repo, *a):
    return subprocess.run(['git', '-C', repo, *a], capture_output=True, text=True, check=True).stdout.strip()


# ------------------------------------------------------------------ selection (shared by both modes) --------------------
def k_of(n):
    return math.floor(SHARE * n)


def take(values, days, k, coldest):
    """The k days with the lowest (coldest=True) or highest values; ties broken by date, earliest first.
    Returns [(day, value, rank)] in rank order, and whether a tie straddled the boundary."""
    df = pd.DataFrame({'day': days, 'v': values}).dropna()
    df['key'] = df['v'] if coldest else -df['v']
    df = df.sort_values(['key', 'day'], kind='mergesort').reset_index(drop=True)
    tie = bool(0 < k < len(df) and df['key'].iloc[k - 1] == df['key'].iloc[k])
    return [(r.day, float(r.v), i + 1) for i, r in df.head(k).iterrows()], tie, len(df)


def is_xmas(d):
    return (d.month == 12 and d.day >= 24) or (d.month == 1 and d.day <= 2)


def winter_of(d):
    """November to March, labelled by the years it spans; other months 'Apr-Oct YYYY'."""
    if d.month >= 11: return f'winter {d.year}-{str(d.year + 1)[2:]}'
    if d.month <= 3: return f'winter {d.year - 1}-{str(d.year)[2:]}'
    return f'Apr-Oct {d.year}'


def select(feat, hol):
    """feat: one row per backtest day (day, t_mean, t_min, neso_peak, t4, ...). Returns the rows of days.csv and the
    selection facts for days.json."""
    days = list(feat['day']); n = len(days)
    rows, info = [], dict(n_days=n, share=SHARE)
    for name, col, coldest, what, unit in (('T1', 't_mean', True, 'mean forecast temperature', 'C'),
                                           ('T1b', 't_min', True, 'coldest forecast half-hour', 'C'),
                                           ('T2', 'neso_peak', False, "NESO's forecast peak", 'MW')):
        ranked, tie, n_ranked = take(feat[col].to_numpy(float), days, k_of(int(feat[col].notna().sum())), coldest)
        k = len(ranked)
        for d, v, r in ranked:
            rows.append(dict(set=name, day=d, rank=r, value=round(v, 4),
                             reason=f'{what} {v:.2f} {unit}: rank {r} of {n_ranked} '
                                    f'({"coldest" if coldest else "highest"} first); the set takes {k}'))
        info[name] = dict(n_ranked=n_ranked, k=k, boundary_value=ranked[-1][1] if ranked else None,
                          tie_at_boundary=tie)
    info['T2']['left_out_no_neso'] = [d for d, v in zip(days, feat['neso_peak']) if not np.isfinite(v)]
    for d in days:
        D = pd.Timestamp(d); why = []
        if D in hol: why.append('bank holiday (England and Wales)')
        if is_xmas(D): why.append('24 December to 2 January')
        if why: rows.append(dict(set='T3', day=d, rank=None, value=None, reason='; '.join(why)))
    for r in feat.itertuples():
        if r.t4:
            rows.append(dict(set='T4', day=r.day, rank=None, value=round(r.t_lgb_min, 4),
                             reason=f'{r.n_below} forecast half-hour(s) below {r.t_train_min:.2f} C, the lowest '
                                    f'temperature in LightGBM\'s training rows; coldest {r.t_lgb_min:.2f} C'))
    out = pd.DataFrame(rows, columns=['set', 'day', 'rank', 'value', 'reason'])
    members = {s: set(out.loc[out.set == s, 'day']) for s in SETS}
    info['counts'] = {s: len(members[s]) for s in SETS}
    info['by_winter'] = {s: dict(sorted(pd.Series([winter_of(pd.Timestamp(d)) for d in members[s]], dtype=object)
                                        .value_counts().items())) for s in SETS}
    info['by_month'] = {s: dict(sorted(pd.Series([d[:7] for d in members[s]], dtype=object).value_counts().items()))
                        for s in SETS}
    info['overlap'] = {f'{a}&{b}': len(members[a] & members[b]) for i, a in enumerate(SETS) for b in SETS[i + 1:]}
    info['small_sets'] = {s: len(members[s]) < 10 for s in SETS}      # PLAN.md §5: reported day by day
    for s in SETS:
        if members[s]:
            top = max(info['by_winter'][s].values()) / len(members[s])
            info.setdefault('largest_winter_share', {})[s] = round(top, 3)
    return out, info


# ------------------------------------------------------------------ per-day selection inputs ----------------------------
def presence(series):
    """INDO with every present value replaced by 1.0: which half-hours exist, and nothing else."""
    return series.notna().astype(float).where(series.notna())


def day_features(D, inputs_day, era5_hh, model):
    """Forecast temperature for D, and LightGBM's training and predict-time temperatures for D."""
    import lightgbm_weather as L
    w = RW.weather_for(D, inputs_day, era5_hh)
    starts = C.target_starts(D)
    t = w['t2m'].reindex(starts).to_numpy(float)
    assert len(t) == len(starts) and np.isfinite(t).all(), f'{D:%Y-%m-%d}: forecast temperature missing'
    X, _, x0 = model.features(D, inputs_day, era5_hh)
    j = L.FEATURES.index('t2m')
    train, pred = X[:, j], x0[:, j]
    assert len(train) and np.isfinite(train).all(), f'{D:%Y-%m-%d}: no LightGBM training temperatures'
    # LightGBM's predict-time temperature is D's forecast temperature, slot by slot (first occurrence)
    first = {}
    for s, v in zip(starts, t): first.setdefault(C.clock(s), v)
    for k, slot in enumerate(B.SLOTS):
        if slot in first: assert abs(pred[k] - first[slot]) <= TEMP_TOL_C, f'{D:%Y-%m-%d} {slot}: x0 differs'
        else: assert not np.isfinite(pred[k]), f'{D:%Y-%m-%d} {slot}: x0 has a slot D lacks'
    pred = pred[np.isfinite(pred)]
    tmin = float(train.min())
    # cross-check: the lowest temperature anywhere on D-366 .. D-2, ignoring which rows LightGBM kept
    wx = RW._by_day_slot(w)['t2m']
    lo, hi = D - pd.Timedelta(days=C.TRAIN_DAYS + 1), D - pd.Timedelta(days=2)
    tmin_all = float(np.nanmin(wx.loc[(wx.index >= lo) & (wx.index <= hi)].to_numpy()))
    return dict(day=f'{D:%Y-%m-%d}', t_mean=float(t.mean()), t_min=float(t.min()), n_halfhours=len(t),
                t_lgb_min=float(pred.min()), t_train_min=tmin, t_window_min=tmin_all, n_train_rows=int(len(train)),
                n_below=int((pred < tmin).sum()), t4=bool((pred < tmin).any()),
                t4_window=bool((pred < tmin_all).any()))


def neso_peak(pubs, D, attempt2):
    try:
        v, _ = I.neso_forecast(pubs, D)
    except ValueError as e:
        return np.nan, str(e)
    a = attempt2.get(f'{D:%Y-%m-%d}')
    assert a is not None and len(a) == len(v) and np.allclose(a, v, atol=NESO_TOL_MW, rtol=0), \
        f'{D:%Y-%m-%d}: NESO forecast differs from results/attempt2'
    return float(np.max(v)), None


# ------------------------------------------------------------------ real build ------------------------------------------
def provenance():
    dirty = git(ROOT, 'status', '--porcelain', '--', 'tails/build_days.py', 'code')
    dirty_p = git(PRIVATE, 'status', '--porcelain', '--', 'weather')
    if dirty or dirty_p:
        sys.exit('Run refused: uncommitted changes (PLAN.md §9: committed before it runs):\n' + dirty + dirty_p)
    return dict(public_commit=git(ROOT, 'rev-parse', 'HEAD'), private_commit=git(PRIVATE, 'rev-parse', 'HEAD'),
                script_sha256=sha(os.path.abspath(__file__)),
                private_sha256={f: sha(os.path.join(PRIVATE, 'weather', f)) for f in
                                ('regression_weather.py', 'lightgbm_weather.py', 'run_weather.py', 'national.py')},
                code_sha256={f: sha(os.path.join(ROOT, 'code', f)) for f in ('common.py', 'inputs.py', 'baselines.py')})


def check_hashes():
    lock = json.load(open(os.path.join(ROOT, 'weather_study', 'WEATHER_LOCK.json')))['files_sha256']
    man = json.load(open(os.path.join(ROOT, 'data', 'fetch_manifest.json')))['files']
    got, bad = {}, []
    for k, p in BACKTEST.items():
        h = sha(p); got[os.path.basename(p)] = h
        want = lock.get('~/gb-weather-data/backtest/' + os.path.basename(p))
        if h != want: bad.append(f'{p}: {h} differs from WEATHER_LOCK.json')
    build = json.load(open(BACKTEST['build']))
    if build['outputs'].get(os.path.basename(BACKTEST['inputs'])) != got[os.path.basename(BACKTEST['inputs'])]:
        bad.append('the inputs file differs from the hash in build.json')
    for k, p in DATA.items():
        h = sha(p); got[k] = h
        if h != man[k]['sha256']: bad.append(f'{p}: {h} differs from data/fetch_manifest.json')
    for p, want in ((FORECASTS, FORECASTS_SHA), (ATTEMPT2, ATTEMPT2_SHA)):
        h = sha(p); got[os.path.relpath(p, ROOT)] = h
        if h != want: bad.append(f'{p}: {h} differs from the hash in build_days.py')
    if bad: sys.exit('Run refused: input hashes differ:\n' + '\n'.join(bad))
    return got


def real():
    import lightgbm as lgb, lightgbm_weather as L, run_weather as RWX
    prov = provenance()
    hashes = check_hashes()
    days = sorted(pd.read_csv(FORECASTS, usecols=['day'])['day'].unique())
    days_inputs, meta = RWX.load_inputs(BACKTEST['inputs'], BACKTEST['days'])
    era5_hh = pd.read_csv(BACKTEST['era5_halfhourly'], index_col=0, parse_dates=True)
    hol = {pd.Timestamp(d) for d in json.load(open(DATA['bank_holidays_ew.json']))}
    pubs = I.load_neso(DATA['neso_dayahead_publications.csv'])
    a2 = pd.read_csv(ATTEMPT2, usecols=['day', 'neso'])
    attempt2 = {d: g['neso'].to_numpy(float) for d, g in a2.groupby('day')}
    raw = pd.read_csv(DATA['indo.csv'], usecols=['start_utc', 'mw'])
    raw['mw'] = raw['mw'].notna().astype(float).where(raw['mw'].notna())   # presence only, before any use
    raw['start_utc'] = pd.to_datetime(raw['start_utc'], utc=True)
    raw = raw.drop_duplicates('start_utc', keep='first').sort_values('start_utc')   # as inputs.load_indo
    s = raw.set_index('start_utc')['mw']
    series = s.reindex(pd.date_range(s.index.min(), s.index.max(), freq='30min'))
    assert set(np.unique(series.dropna())) <= {1.0}
    model = L.LightGBMW(series, hol)
    feats, neso_notes = [], {}
    for k, d in enumerate(days):
        D = pd.Timestamp(d)
        assert D in days_inputs and 'dropped' not in meta.get(D, {}), f'{d}: no built weather inputs'
        f = day_features(D, days_inputs[D], era5_hh, model)
        f['neso_peak'], note = neso_peak(pubs, D, attempt2)
        if note: neso_notes[d] = note
        f['holiday'] = D in hol; f['xmas'] = is_xmas(D)
        feats.append(f)
        if (k + 1) % 100 == 0: print(f'{k + 1} of {len(days)} days', flush=True)
    feat = pd.DataFrame(feats)
    out, info = select(feat, hol)
    info['T4_check'] = dict(
        rule='T4 uses LightGBM\'s training rows; t4_window uses every half-hour of D-366 .. D-2. Dropping rows can '
             'only raise the training minimum, so every t4_window day must be a T4 day.',
        n_t4=int(feat.t4.sum()), n_t4_window=int(feat.t4_window.sum()),
        t4_not_window=sorted(feat.loc[feat.t4 & ~feat.t4_window, 'day']))
    assert not (feat.t4_window & ~feat.t4).any(), 'a day below the whole window minimum is not in T4'
    info['neso_left_out_reasons'] = neso_notes
    write(out, feat, info, dict(provenance=prov, inputs_sha256=hashes,
                                versions=dict(python=platform.python_version(), numpy=np.__version__,
                                              pandas=pd.__version__, lightgbm=lgb.__version__)))


def write(out, feat, info, extra):
    p_csv = os.path.join(HERE, 'days.csv'); p_in = os.path.join(HERE, 'day_inputs.csv')
    out.to_csv(p_csv, index=False)
    feat.round(6).to_csv(p_in, index=False)
    res = dict(schema=SCHEMA, note='tails study day sets (PLAN.md §5); chosen from forecasts and the calendar only',
               days_csv_sha256=sha(p_csv), day_inputs_csv_sha256=sha(p_in), **info, **extra)
    json.dump(res, open(os.path.join(HERE, 'days.json'), 'w'), indent=1, default=str)
    print(json.dumps(dict(counts=info['counts'], overlap=info['overlap'], by_winter=info['by_winter']), indent=1))


# ------------------------------------------------------------------ synthetic checks ------------------------------------
def synthetic():
    """No real data. (1) The presence trick: LightGBM's training and predict-time temperatures are identical whether
    demand carries its values or 1.0, and the row count matches. (2) day_features runs and its x0 check holds.
    (3) Selection: ranking, ties at the boundary by date, NESO gaps, T3 and T4, counts and overlaps."""
    import lightgbm_weather as L
    series, hol, rec, wx = L.synthetic_data()
    checks = {}
    real_m, pres_m = L.LightGBMW(series, hol), L.LightGBMW(presence(series), hol)
    j = L.FEATURES.index('t2m'); same = True; n = 0
    for D in sorted(rec)[::5]:
        X1, _, x01 = real_m.features(D, rec[D]['wx'], wx)
        X2, y2, x02 = pres_m.features(D, rec[D]['wx'], wx)
        same &= X1.shape == X2.shape and np.array_equal(X1[:, j], X2[:, j]) and \
            np.array_equal(x01[:, j], x02[:, j], equal_nan=True) and set(np.unique(y2)) == {1.0}
        n += 1
    checks['1_presence_gives_lightgbm_temperatures'] = dict(passed=bool(same), days=n)
    feats = [day_features(D, rec[D]['wx'], wx, pres_m) for D in sorted(rec)]
    f = pd.DataFrame(feats)
    checks['2_day_features'] = dict(passed=bool(len(f) == len(rec) and f.t_mean.notna().all()), days=len(f),
                                    t4_days=int(f.t4.sum()))
    # 3: selection on constructed values with known answers
    days = [f'{d:%Y-%m-%d}' for d in pd.date_range('2024-12-20', periods=40)]
    t = np.arange(40, dtype=float); t[[3, 7]] = -5.0; t[[11, 30]] = 0.5          # 3 and 7 tie for coldest
    peak = 40000 - 100 * np.arange(40, dtype=float); peak[0] = np.nan; peak[[5, 6]] = 45000
    g = pd.DataFrame(dict(day=days, t_mean=t, t_min=t - 1, neso_peak=peak, t4=False, n_below=0,
                          t_lgb_min=t, t_train_min=0.0))
    g.loc[[3, 7], 't4'] = True
    hol3 = {pd.Timestamp('2024-12-25'), pd.Timestamp('2024-12-26'), pd.Timestamp('2025-01-01')}
    out, info = select(g, hol3)
    get = lambda s: list(out.loc[out.set == s, 'day'])
    want_T1 = [days[3], days[7], days[0], days[11]]          # floor(0.1 x 40) = 4: -5, -5 (by date), 0, 0.5
    want_T2 = [days[5], days[6], days[1]]                    # 39 ranked (one NaN): floor(3.9) = 3
    want_T3 = [d for d in days if is_xmas(pd.Timestamp(d)) or pd.Timestamp(d) in hol3]
    ok3 = (get('T1') == want_T1 and get('T2') == want_T2 and sorted(get('T3')) == sorted(want_T3)
           and get('T4') == [days[3], days[7]] and info['T2']['left_out_no_neso'] == [days[0]]
           and info['T2']['n_ranked'] == 39 and info['counts']['T1'] == 4 and info['overlap']['T1&T4'] == 2)
    # a tie straddling the boundary is broken by date
    t2 = np.r_[np.zeros(3), np.ones(37)]
    o2, i2 = select(g.assign(t_mean=t2), hol3)
    ok_tie = list(o2.loc[o2.set == 'T1', 'day']) == days[:4] and i2['T1']['tie_at_boundary']
    checks['3_selection'] = dict(passed=bool(ok3 and ok_tie), T1=get('T1'), T2=get('T2'), T3=get('T3'),
                                 T4=get('T4'), tie_case=bool(ok_tie))
    ok = all(c['passed'] for c in checks.values())
    for k, c in checks.items(): print(('PASS ' if c['passed'] else 'FAIL ') + k)
    json.dump(dict(passed=ok, script_sha256=sha(os.path.abspath(__file__)), checks=checks),
              open(os.path.join(HERE, 'build_days_synthetic.json'), 'w'), indent=1, default=str)
    print('synthetic: ' + ('PASS' if ok else 'FAIL'))
    return ok


if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('--synthetic', action='store_true')
    a = ap.parse_args()
    if a.synthetic: sys.exit(0 if synthetic() else 1)
    real()
