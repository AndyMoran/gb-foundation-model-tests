"""
Context novelty, step 1 (context_novelty/PLAN.md §9, version 2, frozen at tag context-novelty-plan-v2): build the
day sets and the matched pairs. Committed before it runs; its outputs are committed after.

For: a reviewer checking that every set was chosen from the covariates the foundation models received the day before,
and from nothing else.

Sets (PLAN.md §5), over the backtest days of weather_study/results/forecasts.csv (16 March 2024 to 31 October 2026):
    N      days whose coldest target half-hour temperature is below the coldest context half-hour    counts
    N&T1   N's days that are also in the tails study's T1                                            novel cold days
    T1-N   T1's days that are not in N                                                               pool of controls
    Nw     days with a target half-hour's wind above the context's highest, or its solar below the    descriptive
           context's lowest
"Below" and "above" are strict: a target value equal to the context's extreme is not novel.

Matched pairs (PLAN.md §5): each N&T1 day, in date order, takes the T1-N day with t_mean within 1.0 C and calendar
month within one month (December and January are one apart) that has the smallest t_mean difference; ties go to the
smaller month difference, then the earlier date. A control is used at most once. t_mean is T1's own measure, from
tails/day_inputs.csv. Cold-spell clusters: N&T1 days less than three days apart share a cluster; each pair takes its
novel day's cluster.

What it reads, and what it does not:
    covariates   the weather study's frozen backtest inputs (inputs_*.csv.gz): for each target day D, the rows
                 part = context (2,688 half-hours) and part = horizon, columns t2m_c, wind_ms and solar_wm2: the
                 adjusted values the foundation models received. run_weather.load_inputs renames these columns
                 and changes nothing else; this script reads the file directly.
    target       D's own half-hours (code/common.target_starts: 46, 48 or 50), the last rows of the horizon. The
                 horizon also holds the half-hours from the input cut-off (08:30 on D-1) to midnight; they are not
                 target half-hours and are not used for any set. Their coldest value is recorded in
                 day_inputs.csv for reference.
    T1, T4       tails/days.csv, checked against the SHA-256 in tails/days.json
    t_mean       tails/day_inputs.csv (T1's measure, and t_min for balance), checked against tails/days.json
    backtest days the `day` column of weather_study/results/forecasts.csv only
    days file    days_*.jsonl, for each day's fallback flag
No outturn and no forecast is read.

Every input file is hashed and checked: the backtest inputs and days files against WEATHER_LOCK.json, and the inputs
file also against build.json (PLAN.md §5); build.json itself against WEATHER_LOCK.json; the forecasts file against
the hash the tails study fixed. The script refuses to run while it or code/ has uncommitted changes, and records the
commit.

Outputs:
    context_novelty/days.csv        one row per (set, day): set, day, margin (C, or the wind or solar margin for Nw),
                                    reason
    context_novelty/day_inputs.csv  every backtest day's selection inputs (covariates only)
    context_novelty/pairs.csv       one row per pair: novel day, control, cluster, t_mean and t_min of each, and the
                                    differences in t_mean, t_min and month
    context_novelty/days.json       counts per set, by winter and by month; N's overlap with T1 and T4; the margins;
                                    eligible novel days, pairs retained, unmatched days, clusters and balance; whether
                                    H5 can be assessed (10 pairs or more); file hashes, commit and versions; the
                                    SHA-256 of every output

Modes:
    python context_novelty/build_days.py              the real build (Andy's machine, environment gbcp0)
    python context_novelty/build_days.py --synthetic  checks on invented covariates only; writes
                                                      context_novelty/build_days_synthetic.json

Paths: this repository's root; the weather data at ~/gb-weather-data.
"""
import argparse, gzip, hashlib, json, os, platform, subprocess, sys, tempfile
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, 'code'))
import common as C                                           # noqa: E402  (this repository's code/)

TAG = '2024-03-16_2026-10-31'
BT = os.path.join(os.path.expanduser('~/gb-weather-data'), 'backtest')
BACKTEST = {k: os.path.join(BT, f'{k}_{TAG}{ext}') for k, ext in
            (('inputs', '.csv.gz'), ('days', '.jsonl'), ('build', '.json'))}
FORECASTS = os.path.join(ROOT, 'weather_study', 'results', 'forecasts.csv')
FORECASTS_SHA = 'b5f16561dcf1a26f8d7910bcca95cd137f677760c6f80153349034d4a85f7328'      # tails/PLAN.md §4
TAILS_DAYS = os.path.join(ROOT, 'tails', 'days.csv'); TAILS_JSON = os.path.join(ROOT, 'tails', 'days.json')
TAILS_INPUTS = os.path.join(ROOT, 'tails', 'day_inputs.csv')
PLAN_TAG = 'context-novelty-plan-v2'
SETS = ('N', 'N&T1', 'T1-N', 'Nw')
CALIPER_C = 1.0                                              # PLAN.md §5: t_mean within 1.0 C
MONTHS = 1                                                   # calendar month within one month
SPELL_GAP = 3                                                # novel days less than 3 days apart share a cluster
MIN_PAIRS = 10                                               # PLAN.md §5: fewer than 10 pairs, H5 not assessed
SCHEMA = 1


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''): h.update(b)
    return h.hexdigest()


def git(*a):
    return subprocess.run(['git', '-C', ROOT, *a], capture_output=True, text=True, check=True).stdout.strip()


def winter_of(d):
    """November to March, labelled by the years it spans; other months 'Apr-Oct YYYY' (as tails/build_days.py)."""
    if d.month >= 11: return f'winter {d.year}-{str(d.year + 1)[2:]}'
    if d.month <= 3: return f'winter {d.year - 1}-{str(d.year)[2:]}'
    return f'Apr-Oct {d.year}'


# ------------------------------------------------------------------ per-day inputs (shared by both modes) ---------------
def load_covariates(path_csv):
    """The frozen inputs file, one frame per target day, rows in file order."""
    t = pd.read_csv(path_csv, usecols=['target_day', 'period_start_utc', 'part', 't2m_c', 'wind_ms', 'solar_wm2'])
    t['period_start_utc'] = pd.to_datetime(t['period_start_utc'], utc=True)
    return {d: g.reset_index(drop=True) for d, g in t.groupby('target_day', sort=True)}


def day_inputs(d, g):
    """Selection inputs for target day d from its covariate rows g. Checks the layout the models received: 2,688
    context half-hours ending at the input cut-off, then a horizon running on to the end of D, whose last rows are D's
    target half-hours."""
    D = pd.Timestamp(d)
    ctx, hor = g[g.part == 'context'], g[g.part == 'horizon']
    assert len(ctx) + len(hor) == len(g), f'{d}: a row is neither context nor horizon'
    assert len(ctx) == C.CONTEXT_LEN, f'{d}: {len(ctx)} context half-hours, not {C.CONTEXT_LEN}'
    assert ctx.index.max() < hor.index.min(), f'{d}: context rows do not all precede the horizon'
    h, i0 = C.horizon(D)
    assert len(hor) == h, f'{d}: {len(hor)} horizon half-hours, not {h}'
    end = C.input_end(D)
    assert ctx['period_start_utc'].iloc[-1] == end - pd.Timedelta(minutes=30), f'{d}: context does not end at the cut-off'
    assert hor['period_start_utc'].iloc[0] == end, f'{d}: horizon does not start at the cut-off'
    tgt, gap = hor.iloc[i0:], hor.iloc[:i0]
    assert list(tgt['period_start_utc']) == list(C.target_starts(D)), f'{d}: target half-hours differ from D'
    for frame, what in ((ctx, 'context'), (tgt, 'target')):
        assert frame[['t2m_c', 'wind_ms', 'solar_wm2']].notna().all().all(), f'{d}: missing {what} covariate'
    r = dict(day=d, n_target=len(tgt), n_gap=len(gap),
             t_ctx_min=float(ctx.t2m_c.min()), t_tgt_min=float(tgt.t2m_c.min()),
             t_gap_min=float(gap.t2m_c.min()) if len(gap) else np.nan,
             w_ctx_max=float(ctx.wind_ms.max()), w_tgt_max=float(tgt.wind_ms.max()),
             s_ctx_min=float(ctx.solar_wm2.min()), s_tgt_min=float(tgt.solar_wm2.min()))
    r['t_margin'] = r['t_ctx_min'] - r['t_tgt_min']          # > 0 on N days: how far below the context D went
    r['w_margin'] = r['w_tgt_max'] - r['w_ctx_max']          # > 0: how far above the context's highest wind
    r['s_margin'] = r['s_ctx_min'] - r['s_tgt_min']          # > 0: how far below the context's lowest solar
    r['n_below'] = int((tgt.t2m_c < r['t_ctx_min']).sum())
    r['novel_t'] = bool(r['t_tgt_min'] < r['t_ctx_min'])
    r['novel_w'] = bool(r['w_tgt_max'] > r['w_ctx_max']); r['novel_s'] = bool(r['s_tgt_min'] < r['s_ctx_min'])
    return r


# ------------------------------------------------------------------ selection (shared by both modes) --------------------
def select(feat, t1, t4):
    """feat: one row per backtest day (from day_inputs). t1, t4: the tails study's sets. Returns the rows of
    days.csv and the facts for days.json."""
    days = set(feat['day']); t1, t4 = set(t1), set(t4)
    assert t1 <= days and t4 <= days, 'a tails-study day is not a backtest day'
    f = feat.set_index('day')
    N = {d for d in days if f.at[d, 'novel_t']}
    Nw = {d for d in days if f.at[d, 'novel_w'] or f.at[d, 'novel_s']}
    members = {'N': N, 'N&T1': N & t1, 'T1-N': t1 - N, 'Nw': Nw}
    rows = []
    for s in ('N', 'N&T1', 'T1-N'):
        for d in sorted(members[s]):
            r = f.loc[d]
            why = (f'coldest target half-hour {r.t_tgt_min:.2f} C, below the context\'s coldest {r.t_ctx_min:.2f} C '
                   f'({r.n_below} half-hour(s) below)') if d in N else \
                  (f'coldest target half-hour {r.t_tgt_min:.2f} C, not below the context\'s coldest '
                   f'{r.t_ctx_min:.2f} C')
            if s != 'N': why += '; in the tails study\'s T1'
            rows.append(dict(set=s, day=d, margin=round(float(r.t_margin), 4), reason=why))
    for d in sorted(Nw):
        r = f.loc[d]; why = []
        if r.novel_w: why.append(f'wind {r.w_tgt_max:.2f} m/s above the context\'s highest {r.w_ctx_max:.2f}')
        if r.novel_s: why.append(f'solar {r.s_tgt_min:.2f} W/m2 below the context\'s lowest {r.s_ctx_min:.2f}')
        rows.append(dict(set='Nw', day=d, margin=round(float(r.w_margin if r.novel_w else r.s_margin), 4),
                         reason='; '.join(why)))
    out = pd.DataFrame(rows, columns=['set', 'day', 'margin', 'reason'])
    info = dict(n_days=len(days), n_T1=len(t1), n_T4=len(t4))
    info['counts'] = {s: len(members[s]) for s in SETS}
    info['by_winter'] = {s: dict(sorted(pd.Series([winter_of(pd.Timestamp(d)) for d in members[s]], dtype=object)
                                        .value_counts().items())) for s in SETS}
    info['by_month'] = {s: dict(sorted(pd.Series([d[:7] for d in members[s]], dtype=object).value_counts().items()))
                        for s in SETS}
    info['overlap'] = {'N&T1': len(N & t1), 'N&T4': len(N & t4), 'Nw&N': len(Nw & N), 'Nw&T1': len(Nw & t1)}
    info['Nw_by_arm'] = dict(wind=int(f['novel_w'].sum()), solar=int(f['novel_s'].sum()),
                             both=int((f['novel_w'] & f['novel_s']).sum()))
    m = f.loc[sorted(N), 't_margin'] if N else pd.Series(dtype=float)
    info['N_margin_C'] = dict(min=float(m.min()), median=float(m.median()), max=float(m.max())) if N else None
    return out, info


# ------------------------------------------------------------------ matching and clusters (shared by both modes) --------
def month_gap(a, b):
    k = abs(pd.Timestamp(a).month - pd.Timestamp(b).month)
    return min(k, 12 - k)


def clusters(novel):
    """Cold-spell clusters: novel days less than SPELL_GAP days apart share one, numbered from 1 in date order."""
    out, c, prev = {}, 0, None
    for d in sorted(novel):
        if prev is None or (pd.Timestamp(d) - pd.Timestamp(prev)).days >= SPELL_GAP: c += 1
        out[d] = c; prev = d
    return out


def match(novel, controls, t_mean, t_min):
    """PLAN.md §5. novel, controls: day lists; t_mean, t_min: dicts by day. Returns the pairs frame and facts."""
    free, rows, unmatched = set(controls), [], []
    cl = clusters(novel)
    for d in sorted(novel):
        # differences rounded to 1e-6 C (day_inputs.csv's precision) so that ties are exact
        cand = [(round(abs(t_mean[c] - t_mean[d]), 6), month_gap(c, d), c) for c in free
                if round(abs(t_mean[c] - t_mean[d]), 6) <= CALIPER_C and month_gap(c, d) <= MONTHS]
        if not cand: unmatched.append(d); continue
        _, mg, c = min(cand); free.discard(c)
        rows.append(dict(novel=d, control=c, cluster=cl[d], t_mean_novel=t_mean[d], t_mean_control=t_mean[c],
                         t_min_novel=t_min[d], t_min_control=t_min[c], d_t_mean=t_mean[d] - t_mean[c],
                         d_t_min=t_min[d] - t_min[c], d_month=mg))
    pairs = pd.DataFrame(rows, columns=['novel', 'control', 'cluster', 't_mean_novel', 't_mean_control',
                                        't_min_novel', 't_min_control', 'd_t_mean', 'd_t_min', 'd_month'])
    bal = lambda col: dict(mean=float(pairs[col].mean()), mean_abs=float(pairs[col].abs().mean()),
                           max_abs=float(pairs[col].abs().max())) if len(pairs) else None
    info = dict(eligible_novel_days=len(novel), controls_available=len(controls), pairs=len(pairs),
                unmatched=unmatched, clusters=int(pairs['cluster'].nunique()) if len(pairs) else 0,
                pairs_by_winter=dict(sorted(pd.Series([winter_of(pd.Timestamp(d)) for d in pairs['novel']],
                                                      dtype=object).value_counts().items())),
                balance=dict(t_mean_C=bal('d_t_mean'), t_min_C=bal('d_t_min'), month=bal('d_month')),
                h5_assessable=bool(len(pairs) >= MIN_PAIRS),
                rule=f'PLAN.md §5: t_mean within {CALIPER_C} C, month within {MONTHS}, date order, nearest first, '
                     f'ties by month difference then date, no reuse; fewer than {MIN_PAIRS} pairs: H5 not assessed')
    return pairs, info


# ------------------------------------------------------------------ real build ------------------------------------------
def provenance():
    dirty = git('status', '--porcelain', '--', 'context_novelty/build_days.py', 'context_novelty/PLAN.md', 'code',
                'tails/days.csv', 'tails/days.json', 'tails/day_inputs.csv')
    if dirty:
        sys.exit('Run refused: uncommitted changes (PLAN.md §9: committed before it runs):\n' + dirty)
    plan_tag = git('rev-parse', PLAN_TAG + '^{commit}')
    plan_same = not git('diff', '--name-only', PLAN_TAG, 'HEAD', '--', 'context_novelty/PLAN.md')
    if not plan_same: sys.exit(f'Run refused: context_novelty/PLAN.md differs from tag {PLAN_TAG}')
    return dict(public_commit=git('rev-parse', 'HEAD'), plan_tag_commit=plan_tag,
                script_sha256=sha(os.path.abspath(__file__)),
                code_sha256={f: sha(os.path.join(ROOT, 'code', f)) for f in ('common.py',)})


def check_hashes():
    lock = json.load(open(os.path.join(ROOT, 'weather_study', 'WEATHER_LOCK.json')))['files_sha256']
    got, bad = {}, []
    for k, p in BACKTEST.items():
        h = sha(p); got[os.path.basename(p)] = h
        if h != lock.get('~/gb-weather-data/backtest/' + os.path.basename(p)):
            bad.append(f'{p}: {h} differs from WEATHER_LOCK.json')
    build = json.load(open(BACKTEST['build']))
    if build['outputs'].get(os.path.basename(BACKTEST['inputs'])) != got[os.path.basename(BACKTEST['inputs'])]:
        bad.append('the inputs file differs from the hash in build.json')
    h = sha(FORECASTS); got['weather_study/results/forecasts.csv'] = h
    if h != FORECASTS_SHA: bad.append(f'{FORECASTS}: {h} differs from the hash in build_days.py')
    tj = json.load(open(TAILS_JSON))
    h = sha(TAILS_DAYS); got['tails/days.csv'] = h
    if h != tj['days_csv_sha256']: bad.append('tails/days.csv differs from tails/days.json')
    h = sha(TAILS_INPUTS); got['tails/day_inputs.csv'] = h
    if h != tj['day_inputs_csv_sha256']: bad.append('tails/day_inputs.csv differs from tails/days.json')
    if bad: sys.exit('Run refused: input hashes differ:\n' + '\n'.join(bad))
    return got


def tails_sets():
    t = pd.read_csv(TAILS_DAYS, usecols=['set', 'day'])
    return sorted(t.loc[t.set == 'T1', 'day']), sorted(t.loc[t.set == 'T4', 'day'])


def build(days, cov, meta, t1, t4, tin):
    feats = []
    for k, d in enumerate(days):
        assert d in cov and 'dropped' not in meta.get(d, {}), f'{d}: no built weather inputs'
        r = day_inputs(d, cov[d]); r['fallback'] = bool(meta[d].get('fallback', False))
        r['in_T1'] = d in set(t1); feats.append(r)
        if (k + 1) % 100 == 0: print(f'{k + 1} of {len(days)} days', flush=True)
    feat = pd.DataFrame(feats)
    out, info = select(feat, t1, t4)
    info['fallback_days_in_N'] = sorted(feat.loc[feat.novel_t & feat.fallback, 'day'])
    novel = sorted(out.loc[out.set == 'N&T1', 'day']); controls = sorted(out.loc[out.set == 'T1-N', 'day'])
    t_mean, t_min = dict(zip(tin['day'], tin['t_mean'])), dict(zip(tin['day'], tin['t_min']))
    pairs, minfo = match(novel, controls, t_mean, t_min)
    info['matching'] = minfo
    return out, feat, info, pairs


def real():
    prov = provenance()
    hashes = check_hashes()
    days = sorted(pd.read_csv(FORECASTS, usecols=['day'])['day'].unique())
    cov = load_covariates(BACKTEST['inputs'])
    meta = {json.loads(l)['target_day']: json.loads(l) for l in open(BACKTEST['days'])}
    t1, t4 = tails_sets()
    tin = pd.read_csv(TAILS_INPUTS, usecols=['day', 't_mean', 't_min'])
    out, feat, info, pairs = build(days, cov, meta, t1, t4, tin)
    write(out, feat, pairs, info, dict(provenance=prov, inputs_sha256=hashes,
                                versions=dict(python=platform.python_version(), numpy=np.__version__,
                                              pandas=pd.__version__)))


def write(out, feat, pairs, info, extra):
    p_csv = os.path.join(HERE, 'days.csv'); p_in = os.path.join(HERE, 'day_inputs.csv')
    p_pr = os.path.join(HERE, 'pairs.csv')
    out.to_csv(p_csv, index=False)
    feat.round(6).to_csv(p_in, index=False)
    pairs.round(6).to_csv(p_pr, index=False)
    res = dict(schema=SCHEMA, note='context novelty day sets and pairs (PLAN.md §5); chosen from the covariates the '
                                   'models received only', days_csv_sha256=sha(p_csv), day_inputs_csv_sha256=sha(p_in),
               pairs_csv_sha256=sha(p_pr), **info, **extra)
    json.dump(res, open(os.path.join(HERE, 'days.json'), 'w'), indent=1, default=str)
    m = info['matching']
    print(json.dumps(dict(counts=info['counts'], overlap=info['overlap'], by_winter=info['by_winter'],
                          pairs=m['pairs'], unmatched=m['unmatched'], clusters=m['clusters'],
                          balance=m['balance'], h5_assessable=m['h5_assessable']), indent=1))


# ------------------------------------------------------------------ synthetic checks ------------------------------------
def synth_frame(d, t_ctx_min, t_tgt_min, t_gap_min=None, w_extra=0.0, s_floor=0.0):
    """Covariate rows for target day d in the inputs file's layout. Context temperature 5..15 C with its minimum set
    to t_ctx_min; target temperature 6..14 C with its minimum set to t_tgt_min; the pre-D horizon half-hours at 10 C
    with an optional minimum t_gap_min. Wind 2..8 m/s in context, target max 8 + w_extra. Solar 0..500 W/m2 in
    context, target min s_floor (0 means equal to the context's lowest, so not novel)."""
    D = pd.Timestamp(d); end = C.input_end(D); h, i0 = C.horizon(D); H = pd.Timedelta(minutes=30)
    ctx = pd.date_range(end - C.CONTEXT_LEN * H, end - H, freq='30min')
    hor = pd.date_range(end, end + (h - 1) * H, freq='30min')
    n_t = h - i0
    tc = np.linspace(5, 15, C.CONTEXT_LEN); tc[100] = t_ctx_min
    tg = np.full(i0, 10.0)
    if t_gap_min is not None: tg[0] = t_gap_min
    tt = np.linspace(6, 14, n_t); tt[n_t // 2] = t_tgt_min
    wc = np.linspace(2, 8, C.CONTEXT_LEN); wt = np.linspace(3, 8 + w_extra, h)
    sc = np.abs(np.sin(np.linspace(0, 56 * np.pi, C.CONTEXT_LEN))) * 500; st = np.full(h, 200.0); st[-1] = s_floor
    return pd.DataFrame(dict(target_day=d, period_start_utc=list(ctx) + list(hor),
                             part=['context'] * C.CONTEXT_LEN + ['horizon'] * h,
                             t2m_c=np.r_[tc, tg, tt], wind_ms=np.r_[wc, wt], solar_wm2=np.r_[sc, st]))


def synthetic():
    """No real data. Invented covariates written in the inputs file's layout and read back by load_covariates, so the
    same reader and the same rules run on known answers. Checks: (1) layout, including clock-change days of 46 and 50
    half-hours; (2) N: strictly below, equal is not novel, a cold pre-D half-hour is ignored; (3) Nw's two arms;
    (4) the mechanism sets against T1, the small-set flag, and that a malformed day is refused."""
    checks = {}
    spec = {   # day: (context min, target min, pre-D min, wind extra, solar floor, expected N, expected Nw)
        '2025-01-10': (-2.0, -3.5, None, 0.0, 0.0, True, False),      # colder than context: N
        '2025-01-11': (-2.0, -2.0, None, 0.0, 0.0, False, False),     # equal: not N
        '2025-01-12': (-2.0, -1.0, -6.0, 0.0, 0.0, False, False),     # only a pre-D half-hour is colder: not N
        '2025-01-13': (-1.0, -1.01, None, 0.0, 0.0, True, False),     # just below: N
        '2025-01-14': (0.0, 1.0, None, 2.5, 0.0, False, True),        # wind above context: Nw only
        '2025-01-15': (0.0, -0.5, None, 0.0, -1.0, True, True),       # N, and solar below context: Nw
        '2025-03-30': (3.0, 2.0, None, 0.0, 0.0, True, False),        # clock change, 46 target half-hours
        '2025-10-26': (3.0, 4.0, None, 0.0, 0.0, False, False),       # clock change, 50 target half-hours
    }
    frames = [synth_frame(d, a, b, g, w, s) for d, (a, b, g, w, s, _, _) in spec.items()]
    with tempfile.TemporaryDirectory() as tmp:
        p = os.path.join(tmp, 'inputs_synthetic.csv.gz')
        with gzip.open(p, 'wt', newline='') as fh:
            pd.concat(frames).assign(period_start_utc=lambda x: pd.to_datetime(x.period_start_utc)
                                     .dt.strftime('%Y-%m-%dT%H:%M:%SZ')).to_csv(fh, index=False, float_format='%.4f')
        cov = load_covariates(p)
    days = sorted(spec)
    meta = {d: dict(fallback=(d == '2025-01-13')) for d in days}
    feats = [day_inputs(d, cov[d]) for d in days]
    f = pd.DataFrame(feats).set_index('day')
    n_t = {d: int(f.at[d, 'n_target']) for d in days}
    checks['1_layout'] = dict(passed=bool(n_t['2025-03-30'] == 46 and n_t['2025-10-26'] == 50
                                          and n_t['2025-01-10'] == 48 and (f['n_gap'] > 0).all()), n_target=n_t)
    got_N = sorted(f.index[f.novel_t]); want_N = sorted(d for d in days if spec[d][5])
    m = dict(f['t_margin'].round(4))
    checks['2_N'] = dict(passed=bool(got_N == want_N and m['2025-01-10'] == 1.5 and m['2025-01-11'] == 0.0
                                     and f.at['2025-01-12', 't_gap_min'] == -6.0),
                         N=got_N, expected=want_N, margins=m)
    got_Nw = sorted(f.index[f.novel_w | f.novel_s]); want_Nw = sorted(d for d in days if spec[d][6])
    checks['3_Nw'] = dict(passed=bool(got_Nw == want_Nw and f.at['2025-01-14', 'novel_w']
                                      and f.at['2025-01-15', 'novel_s'] and not f.at['2025-01-15', 'novel_w']),
                          Nw=got_Nw, expected=want_Nw)
    t1 = ['2025-01-10', '2025-01-11', '2025-01-12', '2025-01-15']; t4 = []
    tin = pd.DataFrame(dict(day=days, t_mean=[1.0, 1.5, 3.5, 4.0, 5.0, 2.0, 6.0, 9.0], t_min=-1.0))
    out, feat, info, pairs = build(days, cov, meta, t1, t4, tin)
    get = lambda s: sorted(out.loc[out.set == s, 'day'])
    refused = False
    bad = cov['2025-01-10'].drop(index=5).reset_index(drop=True)            # one context half-hour missing
    try: day_inputs('2025-01-10', bad)
    except AssertionError: refused = True
    ok4 = (get('N&T1') == ['2025-01-10', '2025-01-15'] and get('T1-N') == ['2025-01-11', '2025-01-12']
           and info['counts']['N'] == len(want_N) and info['fallback_days_in_N'] == ['2025-01-13']
           and info['overlap']['N&T1'] == 2 and refused
           # through build(): 01-10 (1.0) takes 01-11 (1.5); 01-15 (2.0) has only 01-12 (3.5) left, 1.5 C away: unmatched
           and list(zip(pairs.novel, pairs.control)) == [('2025-01-10', '2025-01-11')]
           and info['matching']['unmatched'] == ['2025-01-15'] and not info['matching']['h5_assessable'])
    checks['4_sets_and_refusal'] = dict(passed=bool(ok4), N_and_T1=get('N&T1'), T1_minus_N=get('T1-N'),
                                        pairs=list(zip(pairs.novel, pairs.control)),
                                        unmatched=info['matching']['unmatched'], malformed_day_refused=refused)
    # 5: matching and clusters on constructed values with known answers
    tm = {'2024-11-20': 0.0, '2024-11-21': 0.2, '2024-11-25': 0.5, '2025-02-10': -1.0,      # novel days
          '2024-12-01': 0.3, '2024-12-02': 0.1, '2024-10-31': 0.0,                         # controls
          '2025-01-05': -1.0, '2025-01-06': -0.4, '2025-03-01': -1.0}
    tn = {d: v - 3 for d, v in tm.items()}
    nov = ['2024-11-25', '2025-02-10', '2024-11-20', '2024-11-21']                         # order must not matter
    ctl = ['2024-12-01', '2024-12-02', '2024-10-31', '2025-01-05', '2025-01-06', '2025-03-01']
    pr, mi = match(nov, ctl, tm, tn)
    # 11-20 (0.0): 12-02 (0.1) and 10-31 (0.0, but October is one month from November): 10-31, |d| 0 < 0.1
    # 11-21 (0.2): 12-01 |0.1| and 12-02 |0.1| tie on temperature and month: earlier date, 12-01
    # 11-25 (0.5): 12-02 |0.4|; 01-06 is two months away
    # 02-10 (-1.0): 01-05 |0| and 03-01 |0| tie on temperature and month: earlier date, 01-05
    want = [('2024-11-20', '2024-10-31'), ('2024-11-21', '2024-12-01'), ('2024-11-25', '2024-12-02'),
            ('2025-02-10', '2025-01-05')]
    got = list(zip(pr.novel, pr.control))
    cl = dict(zip(pr.novel, pr.cluster))                    # 11-20, 11-21 one spell; 11-25 (4 days on) a second
    p2, m2 = match(['2024-12-15'], ['2024-12-16', '2025-01-20'], {'2024-12-15': 0.0, '2024-12-16': 1.2,
                                                                  '2025-01-20': 0.9}, {d: 0 for d in ['2024-12-15',
                                                                  '2024-12-16', '2025-01-20']})
    ok5 = (got == want and cl == {'2024-11-20': 1, '2024-11-21': 1, '2024-11-25': 2, '2025-02-10': 3}
           and mi['pairs'] == 4 and mi['clusters'] == 3 and mi['balance']['month']['max_abs'] == 1
           and list(zip(p2.novel, p2.control)) == [('2024-12-15', '2025-01-20')]      # 1.2 C is outside the caliper
           and month_gap('2024-12-31', '2025-01-01') == 1 and month_gap('2024-11-01', '2025-01-01') == 2
           # two days apart: one spell; three days apart: a new one
           and clusters(['2024-12-01', '2024-12-03', '2024-12-06']) == {'2024-12-01': 1, '2024-12-03': 1,
                                                                        '2024-12-06': 2})
    checks['5_matching_and_clusters'] = dict(passed=bool(ok5), pairs=got, expected=want, clusters=cl,
                                             caliper_case=list(zip(p2.novel, p2.control)))
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
