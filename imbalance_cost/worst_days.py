"""
Imbalance exposure, stage 1: what makes up each forecaster's worst days (exploratory). Added after stage 1's results
and explore.py's were seen, to answer one question: Chronos-2 had the lowest exposure of every forecaster on
8 January 2025, so why was the mean of its worst 5% of days no better than the weather regression's? The ten worst
days in explore_results.json suggested the calendar (a clock change, Easter). This script looks at all of them.
Nothing here was planned before those results; every figure is descriptive, with no intervals and no labels.
Committed before it runs; its outputs are committed after. It changes nothing in score.py, explore.py or their results.

For: a reviewer checking the definitions below and that the days and exposure are score.py's and explore.py's.

Reads exactly what score.py reads, through score.py's own loader and hash checks (imported unchanged), and the same
953 days. Also reads data/bank_holidays_ew.json (GOV.UK, England and Wales), whose SHA-256 is checked against the
committed data/fetch_manifest.json, and imbalance_cost/explore_results.json for the reproduction check.

Each half-hour's exposure is x = (A - F) * (SP - MIP) * 0.5, in £; a day's exposure is its total over its demand in
GWh, as in score.py. For each forecaster, its worst days are its own worst 5% by that figure: k = ceil(0.05 n) days.
Each day is flagged:
  clock change   46 or 50 half-hours
  bank holiday   on GOV.UK's England and Wales list
  Easter         Good Friday to Easter Monday inclusive (Good Friday: a bank holiday Friday in March or April)
  Christmas      24 December to 1 January inclusive
  calendar       any of the four above
  cold           in T1, the coldest tenth of days (tails/days.csv)
  weekend        Saturday or Sunday
Reported per forecaster:
  - its worst days, with exposure, mean absolute error (MW), mean error A - F (MW, positive = forecast too low),
    mean |SP - MIP| (£/MWh) and flags
  - the share of its worst days carrying each flag, beside that flag's share of all days
  - the mean of its worst 5% of days (reproduces explore.py's figure); the share of that total from calendar days;
    and the mean of the worst 5% of its non-calendar days (k recomputed on those days)
  - on its worst days against all days: mean absolute error and mean |SP - MIP|, as ratios (does a bad day come
    from a big miss, from stressed prices, or both?)
And for each pair (Chronos-2 and the regression; NESO and the regression): how many worst days they share, and each
one's exposure on the other's worst days.

Modes:
    python imbalance_cost/worst_days.py --synthetic   invented data with known answers on the real calendar; writes
                                                      worst_days_synthetic.json; exits 1 on any failure
    python imbalance_cost/worst_days.py               the real run; refused unless the synthetic check passed with
                                                      this script and the guarded files are committed and unchanged
Writes imbalance_cost/worst_days_results.json and worst_days_results.md.
"""
import argparse, importlib.util, json, math, os, platform, subprocess, sys
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
_spec = importlib.util.spec_from_file_location('imbalance_score', os.path.join(HERE, 'score.py'))
sc = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(sc)       # imported unchanged
st = sc.st

SYNTH_JSON = os.path.join(HERE, 'worst_days_synthetic.json')
EXPLORE = os.path.join(HERE, 'explore_results.json')
EXPLORE_SHA = '7a65a30f98baa9eafbc13247b2998a60a5b1b907ec06023725e1105e77d95042'
HOLIDAYS = os.path.join(ROOT, 'data', 'bank_holidays_ew.json')
DATA_MANIFEST = os.path.join(ROOT, 'data', 'fetch_manifest.json')
GUARDED = ['imbalance_cost/worst_days.py', 'imbalance_cost/worst_days_synthetic.json', 'imbalance_cost/explore_results.json',
           'imbalance_cost/results_stage1.json', 'data/fetch_manifest.json'] + sc.GUARDED
FORECASTERS, REF, NAMES, CH, NESO = sc.FORECASTERS, sc.REF, sc.NAMES, sc.CH, sc.NESO
PAIRS = ((CH, REF), (NESO, REF))
FLAGS = ('clock_change', 'bank_holiday', 'easter', 'christmas', 'calendar', 'cold', 'weekend')


def git(*a):
    return subprocess.run(['git', '-C', ROOT, *a], capture_output=True, text=True, check=True).stdout.strip()


# ------------------------------------------------------------------ building blocks -------------------------------------
def day_flags(days, nhh, holidays, t1_days):
    d = pd.to_datetime(pd.Series(days)); hol = {pd.Timestamp(h) for h in holidays}
    easter = set()
    for h in hol:
        if h.dayofweek == 4 and h.month in (3, 4):                           # Good Friday
            easter |= {h + pd.Timedelta(days=i) for i in range(4)}
    f = dict(clock_change=np.asarray(nhh) != 48,
             bank_holiday=d.isin(hol).to_numpy(),
             easter=d.isin(easter).to_numpy(),
             christmas=(((d.dt.month == 12) & (d.dt.day >= 24)) | ((d.dt.month == 1) & (d.dt.day == 1))).to_numpy(),
             cold=np.isin(days, list(t1_days)),
             weekend=(d.dt.dayofweek >= 5).to_numpy())
    f['calendar'] = f['clock_change'] | f['bank_holiday'] | f['easter'] | f['christmas']
    return {k: np.asarray(v, bool) for k, v in f.items()}


def per_day(frame, cols, ok_days):
    f = frame[frame['day'].isin(ok_days)].sort_values(['day', 'start_utc'], kind='mergesort').reset_index(drop=True)
    days = sorted(f['day'].unique()); n = len(days); code = pd.Categorical(f['day'], categories=days).codes
    S = lambda w: np.bincount(code, weights=w, minlength=n)
    A = f['outturn'].to_numpy(float); spread = (f['system_price'] - f['mip']).to_numpy(float)
    nhh = np.bincount(code, minlength=n); gwh = S(A * 0.5) / 1000
    out = dict(days=days, nhh=nhh, gwh=gwh, abs_spread=S(np.abs(spread)) / nhh, F={})
    for c in cols:
        F = f[c].to_numpy(float); e = A - F
        out['F'][c] = dict(daily=S(e * spread * 0.5) / gwh, mae=S(np.abs(e)) / nhh, bias=S(e) / nhh)
    return out


def worst_idx(v, frac=0.05):
    k = max(1, math.ceil(frac * len(v)))
    return np.argsort(-v, kind='stable')[:k]


def analyse(D, flags, cols, pairs=PAIRS):
    days = D['days']; base = {k: float(flags[k].mean()) for k in FLAGS}; out = dict(n_days=len(days), base_rates=base, forecasters={})
    W = {}
    for c in cols:
        v = D['F'][c]['daily']; w = worst_idx(v); W[c] = w
        cal = flags['calendar']; rest = np.flatnonzero(~cal)
        out['forecasters'][c] = dict(
            k=int(len(w)),
            worst_5pct_mean=float(v[w].mean()),
            calendar_share_of_worst_total=float(v[w][cal[w]].sum() / v[w].sum()),
            worst_5pct_mean_non_calendar=float(v[rest][worst_idx(v[rest])].mean()),
            flag_share_of_worst_days={k: float(flags[k][w].mean()) for k in FLAGS},
            mae_ratio_worst_to_all=float(D['F'][c]['mae'][w].mean() / D['F'][c]['mae'].mean()),
            abs_spread_ratio_worst_to_all=float(D['abs_spread'][w].mean() / D['abs_spread'].mean()),
            worst_days=[dict(day=days[i], weekday=pd.Timestamp(days[i]).day_name()[:3], net_gbp_per_gwh=float(v[i]),
                             mae_mw=float(D['F'][c]['mae'][i]), mean_error_mw=float(D['F'][c]['bias'][i]),
                             abs_spread_gbp_per_mwh=float(D['abs_spread'][i]),
                             flags=[k for k in FLAGS if k != 'calendar' and flags[k][i]]) for i in w])
    out['pairs'] = []
    for a, b in pairs:
        if a not in W or b not in W: continue
        va, vb = D['F'][a]['daily'], D['F'][b]['daily']
        out['pairs'].append(dict(a=a, b=b, shared_worst_days=int(len(set(W[a]) & set(W[b]))), k=int(len(W[a])),
                                 a_on_own_worst=float(va[W[a]].mean()), b_on_a_worst=float(vb[W[a]].mean()),
                                 b_on_own_worst=float(vb[W[b]].mean()), a_on_b_worst=float(va[W[b]].mean())))
    return out


def load_holidays():
    man = json.load(open(DATA_MANIFEST))['files']['bank_holidays_ew.json']['sha256']
    if not os.path.exists(HOLIDAYS): sys.exit('Refused: data/bank_holidays_ew.json not found (run code/fetch.py).')
    if st.sha(HOLIDAYS) != man: sys.exit('Refused: data/bank_holidays_ew.json differs from data/fetch_manifest.json.')
    with open(HOLIDAYS) as fh: return json.load(fh)


# ------------------------------------------------------------------ output ---------------------------------------------
def g(v): return '–' if v is None else f'{v:,.0f}'.replace('-', '−')
def p(v): return '–' if v is None else f'{100 * v:.0f}%'


def markdown(res, meta):
    b = res['base_rates']
    L = ['# Imbalance exposure, stage 1: what makes up each forecaster\'s worst days (generated by worst_days.py)', '',
         'Exploratory, added after stage 1\'s results and explore.py\'s were seen. Descriptive only: no intervals, no labels. '
         'A forecaster\'s worst days are its own worst 5% by daily net exposure (£ per GWh).', '',
         f'Days: {res["n_days"]}. Share of all days flagged: clock change {p(b["clock_change"])}, bank holiday {p(b["bank_holiday"])}, '
         f'Easter {p(b["easter"])}, Christmas {p(b["christmas"])}, any calendar {p(b["calendar"])}, cold (T1) {p(b["cold"])}, '
         f'weekend {p(b["weekend"])}.', '', '## Summary', '',
         '| Forecaster | worst 5% mean | share of that total from calendar days | worst 5% mean, non-calendar days | calendar | clock change | Easter | cold | weekend | error on worst days ÷ all days | price stress on worst days ÷ all days |',
         '|---|---|---|---|---|---|---|---|---|---|---|']
    for c, r in res['forecasters'].items():
        s = r['flag_share_of_worst_days']
        L.append(f'| {NAMES[c]} | {g(r["worst_5pct_mean"])} | {p(r["calendar_share_of_worst_total"])} | {g(r["worst_5pct_mean_non_calendar"])} | '
                 f'{p(s["calendar"])} | {p(s["clock_change"])} | {p(s["easter"])} | {p(s["cold"])} | {p(s["weekend"])} | '
                 f'{r["mae_ratio_worst_to_all"]:.2f} | {r["abs_spread_ratio_worst_to_all"]:.2f} |')
    L += ['', '## Pairs', '', '| Pair | shared worst days | A on its worst days | B on A\'s worst days | B on its worst days | A on B\'s worst days |',
          '|---|---|---|---|---|---|']
    for q in res['pairs']:
        L.append(f'| {NAMES[q["a"]]} (A), {NAMES[q["b"]]} (B) | {q["shared_worst_days"]} of {q["k"]} | {g(q["a_on_own_worst"])} | '
                 f'{g(q["b_on_a_worst"])} | {g(q["b_on_own_worst"])} | {g(q["a_on_b_worst"])} |')
    for c in (CH, REF, NESO):
        if c not in res['forecasters']: continue
        L += ['', f'## {NAMES[c]}: its worst days', '', '| Day | | £ per GWh | MAE, MW | mean error, MW | mean \\|SP − MIP\\|, £/MWh | flags |',
              '|---|---|---|---|---|---|---|']
        for x in res['forecasters'][c]['worst_days']:
            L.append(f'| {x["day"]} | {x["weekday"]} | {g(x["net_gbp_per_gwh"])} | {g(x["mae_mw"])} | {g(x["mean_error_mw"])} | '
                     f'{x["abs_spread_gbp_per_mwh"]:.1f} | {", ".join(x["flags"]).replace("_", " ")} |')
    L += ['', '## Checks', ''] + [f'- {k}: {"passed" if v["passed"] else "FAILED"}' for k, v in res['checks'].items()]
    L += ['', f'Commit {meta["public_commit"]}; script SHA-256 {meta["script_sha256"]}; holidays SHA-256 {meta["holidays_sha256"]}.', '']
    return '\n'.join(L)


# ------------------------------------------------------------------ real run -------------------------------------------
def real():
    if not os.path.exists(SYNTH_JSON): sys.exit('Refused: run --synthetic first and commit worst_days_synthetic.json.')
    if git('status', '--porcelain', '--', *GUARDED): sys.exit('Refused: these must be committed and unchanged: ' + ', '.join(GUARDED))
    with open(SYNTH_JSON) as fh: sy = json.load(fh)
    if not sy.get('passed') or sy.get('script_sha256') != st.sha(os.path.abspath(__file__)):
        sys.exit('Refused: the synthetic check has not passed with this script.')
    if st.sha(EXPLORE) != EXPLORE_SHA: sys.exit('Refused: explore_results.json differs from its recorded hash.')
    holidays = load_holidays()
    frame, prices, man, t1 = sc.load_real()
    P = sc.per_day(frame, FORECASTERS); ok_days = [d for d, k in zip(P['days'], P['ok']) if k]
    with open(os.path.join(HERE, 'results_stage1.json')) as fh: stage1 = json.load(fh)
    if len(ok_days) != stage1['sets']['all']['n_days']: sys.exit('Refused: scored days differ from score.py\'s.')
    D = per_day(frame, FORECASTERS, ok_days)
    flags = day_flags(D['days'], D['nhh'], holidays, t1)
    res = analyse(D, flags, FORECASTERS)
    with open(EXPLORE) as fh: ex = json.load(fh)['forecasters']
    diff_es = max(abs(res['forecasters'][c]['worst_5pct_mean'] - ex[c]['daily_es5']['value']) for c in FORECASTERS)
    diff_mean = max(abs(float(D['F'][c]['daily'].mean()) - stage1['sets']['all']['forecasters'][c]['net']['value']) for c in FORECASTERS)
    res['checks'] = dict(worst_5pct_mean_matches_explore=dict(passed=bool(diff_es <= 0.01), max_abs_diff=diff_es),
                         day_mean_matches_score=dict(passed=bool(diff_mean <= 0.01), max_abs_diff=diff_mean),
                         clock_changes_found=dict(passed=bool(flags['clock_change'].sum() >= 4), n=int(flags['clock_change'].sum())))
    meta = dict(public_commit=git('rev-parse', 'HEAD'), script_sha256=st.sha(os.path.abspath(__file__)),
                holidays_sha256=st.sha(HOLIDAYS), explore_sha256=EXPLORE_SHA,
                versions=dict(python=platform.python_version(), numpy=np.__version__, pandas=pd.__version__))
    failed = [k for k, v in res['checks'].items() if not v['passed']]
    if failed: sys.exit('CHECKS FAILED, nothing written: ' + ', '.join(failed) + '\n' + json.dumps(res['checks'], default=str))
    out = dict(note='exploratory, added after stage 1 and explore.py results; descriptive only', meta=meta, **st.round_floats(res))
    with open(os.path.join(HERE, 'worst_days_results.json'), 'w') as fh: json.dump(out, fh, indent=1, default=str)
    md = markdown(out, meta)
    with open(os.path.join(HERE, 'worst_days_results.md'), 'w') as fh: fh.write(md)
    print(md)


# ------------------------------------------------------------------ synthetic check ------------------------------------
SYN_HOLIDAYS = ['2024-03-29', '2024-04-01', '2024-05-06', '2024-12-25', '2024-12-26', '2025-04-18', '2025-04-21',
                '2025-12-25', '2025-12-26', '2026-04-03', '2026-04-06']


def synth_frame(grid):
    """Outturn 30,000 MW, prices with |SP - MIP| = 10, every forecaster exact except on planted days, where it is
    1,000 MW too low against a positive spread: a known loss on exactly those days."""
    f = grid.sort_values(['day', 'start_utc'], kind='mergesort').reset_index(drop=True)
    out = f[['day', 'start_utc']].copy(); out['outturn'] = 30000.0; out['mip'] = 50.0; out['system_price'] = 60.0
    plant = dict(calendar_heavy=['2024-10-27', '2026-04-04', '2025-03-30', '2025-12-25'],
                 ordinary=['2024-06-12', '2025-02-05', '2025-09-17', '2026-01-14'])
    for c, ds in plant.items():
        out[c] = 30000.0; m = out['day'].isin(ds); out.loc[m, c] = 29000.0
    out['ordinary_more'] = out['ordinary']; m = out['day'] == '2024-06-12'; out.loc[m, 'ordinary_more'] = 27000.0
    return out, plant


def synthetic():
    t1, _ = sc.asy.load_inputs()
    grid = pd.read_csv(st.FORECASTS, usecols=['day', 'start_utc'])
    fr, plant = synth_frame(grid); days = sorted(fr['day'].unique()); cols = ['calendar_heavy', 'ordinary', 'ordinary_more']
    res = dict(script_sha256=st.sha(os.path.abspath(__file__)), checks={}); ok_all = True

    def rec(name, good, **info):
        nonlocal ok_all
        res['checks'][name] = dict(passed=bool(good), **info); ok_all &= bool(good)
        print(('PASS ' if good else 'FAIL ') + name, flush=True)

    D = per_day(fr, cols, days); flags = day_flags(D['days'], D['nhh'], SYN_HOLIDAYS, t1)
    at = {d: i for i, d in enumerate(D['days'])}
    rec('clock changes found from half-hour counts', all(flags['clock_change'][at[d]] for d in ('2024-03-31', '2024-10-27', '2025-03-30', '2025-10-26'))
        and not flags['clock_change'][at['2024-06-12']], n=int(flags['clock_change'].sum()))
    rec('Easter is Good Friday to Easter Monday', all(flags['easter'][at[d]] for d in ('2026-04-03', '2026-04-04', '2026-04-05', '2026-04-06', '2024-03-31'))
        and not flags['easter'][at['2026-04-07']] and not flags['easter'][at['2026-04-02']])
    rec('Christmas is 24 December to 1 January', flags['christmas'][at['2025-12-24']] and flags['christmas'][at['2026-01-01']]
        and not flags['christmas'][at['2026-01-02']] and not flags['christmas'][at['2025-12-23']])
    rec('weekend and cold flags', flags['weekend'][at['2024-10-27']] and not flags['weekend'][at['2024-06-12']]
        and int(flags['cold'].sum()) == 96)
    R = analyse(D, flags, cols, pairs=(('calendar_heavy', 'ordinary'),))
    ch, od = R['forecasters']['calendar_heavy'], R['forecasters']['ordinary']
    top = [x['day'] for x in ch['worst_days'][:4]]
    rec('planted days are the worst, and only they lose', sorted(top) == sorted(plant['calendar_heavy'])
        and all(x['net_gbp_per_gwh'] == 0 for x in ch['worst_days'][4:]) and ch['k'] == math.ceil(0.05 * len(days)))
    rec('calendar share: all of the calendar-heavy loss, none of the ordinary loss',
        abs(ch['calendar_share_of_worst_total'] - 1) < 1e-12 and od['calendar_share_of_worst_total'] == 0
        and ch['worst_5pct_mean_non_calendar'] == 0 and od['worst_5pct_mean_non_calendar'] > 0)
    want = float(np.mean([D['F']['calendar_heavy']['daily'][at[d]] for d in plant['calendar_heavy']] + [0] * (ch['k'] - 4)))
    rec('worst 5% mean is the mean of the k worst days', abs(ch['worst_5pct_mean'] - want) < 1e-9)
    rec('error on worst days exceeds the average; prices the same', ch['mae_ratio_worst_to_all'] > 5 and abs(ch['abs_spread_ratio_worst_to_all'] - 1) < 1e-12)
    pr = R['pairs'][0]
    rec('pairs: no shared loss days, each zero on the other\'s planted days', pr['b_on_a_worst'] == 0 and pr['a_on_b_worst'] == 0)
    rec('a larger miss ranks first', R['forecasters']['ordinary_more']['worst_days'][0]['day'] == '2024-06-12')
    res['passed'] = bool(ok_all)
    with open(SYNTH_JSON, 'w') as fh: json.dump(st.round_floats(res), fh, indent=1, default=str)
    print('synthetic: ' + ('PASS' if ok_all else 'FAIL'))
    return ok_all


if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('--synthetic', action='store_true')
    if ap.parse_args().synthetic: sys.exit(0 if synthetic() else 1)
    real()
