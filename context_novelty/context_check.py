"""
Context novelty, follow-up feasibility check: would the novel days stay novel with a longer context?

For: Andy, deciding whether a longer-context test (context_novelty/RESULTS.md, "What comes next") can work.
Committed before it runs; its outputs are committed after. It reads weather only: no demand, no forecast, no error.

Why. Chronos-2's maximum context is 8,192 steps. At half-hourly resolution that is about 170 days (24 weeks), not a
year, so a longer context cannot reach the previous winter. This check asks, for each of the 30 days in N (the 14
novel cold days among them), whether its coldest target half-hour would still be colder than its context with:
    C24   8,192 half-hours (about 24 weeks): the longest half-hourly context Chronos-2 accepts          primary
    C49   8,192 hours (about 49 weeks), approximated on the half-hourly series                          descriptive
A day that stays novel under a longer context cannot test whether the context is the cause; a day that stops being
novel can. If few of the 10 pairs' novel days change, the longer-context test has little to test.

How the longer context is built.
    the last 2,688 half-hours   exactly the covariates the models received (frozen inputs, t2m_c, adjusted)
    everything earlier          ERA5 on the same half-hours (the backtest's era5_halfhourly file, the regression's
                                training weather), shifted onto ECMWF's scale by that day's decision-13 temperature
                                factor (t2m_add in the days file). The weather processing would apply the same factor
                                to every ERA5 day of a longer context, so this is what the models would receive.
    C49 on half-hours           the minimum over 8,192 hours of half-hourly values. ERA5 is hourly, and the half-hours
                                interpolate between hours, so this minimum can sit slightly above the hourly one.
"Colder" is strict, as in PLAN.md §5.

Inputs, each hash-checked against WEATHER_LOCK.json (and the inputs file against build.json):
    ~/gb-weather-data/backtest/inputs_*.csv.gz, days_*.jsonl, era5_halfhourly_*.csv.gz
    context_novelty/days.csv and day_inputs.csv, against context_novelty/days.json; pairs.csv likewise
Outputs: context_novelty/context_check.csv (one row per N day), context_check.json (counts, hashes, commit) and
context_check.md (the table).

Modes:
    python context_novelty/context_check.py --synthetic   invented weather with known answers; writes
                                                          context_novelty/context_check_synthetic.json
    python context_novelty/context_check.py               the real check (Andy's machine)
"""
import argparse, json, os, platform, subprocess, sys
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, 'code')); sys.path.insert(0, HERE)
import common as C                                           # noqa: E402
import build_days as BD                                      # noqa: E402  (load_covariates, sha, hash paths)

ERA5_HH = os.path.join(BD.BT, f'era5_halfhourly_{BD.TAG}.csv.gz')
LENGTHS = {'C8': C.CONTEXT_LEN, 'C24': 8192, 'C49': 2 * 8192}      # in half-hours; C8 is the context as run
OUT = {k: os.path.join(HERE, f'context_check{e}') for k, e in (('csv', '.csv'), ('json', '.json'), ('md', '.md'))}
SYNTH = os.path.join(HERE, 'context_check_synthetic.json')
GUARDED = ['context_novelty/context_check.py', 'context_novelty/build_days.py', 'context_novelty/days.csv',
           'context_novelty/day_inputs.csv', 'context_novelty/pairs.csv', 'context_novelty/days.json', 'code']
H30 = pd.Timedelta(minutes=30)


def git(*a):
    return subprocess.run(['git', '-C', ROOT, *a], capture_output=True, text=True, check=True).stdout.strip()


# ------------------------------------------------------------------ the check (shared by both modes) -------------------
def longer_context_min(d, g, era5_t, t2m_add, n):
    """Coldest temperature over a context of n half-hours ending at D's input cut-off. The last 2,688 are the
    covariates as given (g, the day's frozen rows); the earlier ones are ERA5 + t2m_add. Returns (min, first period,
    count of ERA5 half-hours used)."""
    ctx = g[g.part == 'context']
    assert len(ctx) == C.CONTEXT_LEN, f'{d}: context is not {C.CONTEXT_LEN} half-hours'
    given = float(ctx.t2m_c.min())
    if n <= C.CONTEXT_LEN: return given, ctx['period_start_utc'].iloc[0], 0
    first_given = ctx['period_start_utc'].iloc[0]
    extra = pd.date_range(first_given - (n - C.CONTEXT_LEN) * H30, first_given - H30, freq='30min')
    e = era5_t.reindex(extra)
    assert e.notna().all(), f'{d}: ERA5 does not cover {extra[0]} .. {extra[-1]}'
    return min(given, float(e.min()) + t2m_add), extra[0], len(extra)


def check(days, cov, era5_t, factors, pairs):
    rows = []
    for d in days:
        g = cov[d]; r = BD.day_inputs(d, g)
        row = dict(day=d, t_tgt_min=r['t_tgt_min'], t2m_add=factors[d])
        for k, n in LENGTHS.items():
            m, start, n_era5 = longer_context_min(d, g, era5_t, factors[d], n)
            row[f'{k}_ctx_min'] = m; row[f'{k}_novel'] = bool(r['t_tgt_min'] < m)
            row[f'{k}_margin'] = m - r['t_tgt_min']; row[f'{k}_starts'] = f'{start:%Y-%m-%d}'
        assert row['C8_novel'], f'{d}: not novel with the context as run; days.csv says it is'
        row['in_pairs'] = d in set(pairs['novel']); rows.append(row)
    t = pd.DataFrame(rows)
    summ = {}
    for scope, mask in (('N', np.ones(len(t), bool)), ('paired_novel_days', t['in_pairs'].to_numpy())):
        s = t[mask]
        summ[scope] = dict(days=int(len(s)), **{f'still_novel_{k}': int(s[f'{k}_novel'].sum()) for k in ('C24', 'C49')},
                           **{f'no_longer_novel_{k}': sorted(s.loc[~s[f'{k}_novel'], 'day']) for k in ('C24', 'C49')})
    pc = pairs.assign(**{f'{k}_still_novel': pairs['novel'].map(dict(zip(t.day, t[f'{k}_novel']))) for k in ('C24', 'C49')})
    summ['spells'] = {int(c): {k: int((~grp[f'{k}_still_novel']).sum()) for k in ('C24', 'C49')} | dict(pairs=int(len(grp)))
                      for c, grp in pc.groupby('cluster')}
    return t, summ


# ------------------------------------------------------------------ real check -----------------------------------------
def real():
    if git('status', '--porcelain', '--', *GUARDED): sys.exit('Refused: uncommitted changes in ' + ', '.join(GUARDED))
    lock = json.load(open(os.path.join(ROOT, 'weather_study', 'WEATHER_LOCK.json')))['files_sha256']
    paths = dict(BD.BACKTEST, era5_halfhourly=ERA5_HH)
    hashes, bad = {}, []
    for k, p in paths.items():
        h = BD.sha(p); hashes[os.path.basename(p)] = h
        if h != lock.get('~/gb-weather-data/backtest/' + os.path.basename(p)): bad.append(p)
    if json.load(open(paths['build']))['outputs'].get(os.path.basename(paths['inputs'])) != hashes[os.path.basename(paths['inputs'])]:
        bad.append('inputs vs build.json')
    dj = json.load(open(os.path.join(HERE, 'days.json')))
    for f, k in (('days.csv', 'days_csv_sha256'), ('day_inputs.csv', 'day_inputs_csv_sha256'), ('pairs.csv', 'pairs_csv_sha256')):
        h = BD.sha(os.path.join(HERE, f)); hashes['context_novelty/' + f] = h
        if h != dj[k]: bad.append(f)
    if bad: sys.exit('Refused: hashes differ: ' + ', '.join(bad))
    sets = pd.read_csv(os.path.join(HERE, 'days.csv'), dtype={'day': str})
    days = sorted(sets.loc[sets.set == 'N', 'day'])
    pairs = pd.read_csv(os.path.join(HERE, 'pairs.csv'), dtype={'novel': str, 'control': str})
    cov = BD.load_covariates(paths['inputs'])
    meta = {json.loads(l)['target_day']: json.loads(l) for l in open(paths['days'])}
    factors = {d: float(meta[d]['history_factors']['t2m_add']) for d in days}
    era5 = pd.read_csv(ERA5_HH, index_col=0)
    era5.index = pd.to_datetime(era5.index, utc=True)
    t, summ = check(days, cov, era5['t2m'], factors, pairs)
    t.round(4).to_csv(OUT['csv'], index=False)
    res = dict(note='weather only; no demand, forecast or error read', lengths_halfhours=LENGTHS, summary=summ,
               csv_sha256=BD.sha(OUT['csv']), inputs_sha256=hashes, public_commit=git('rev-parse', 'HEAD'),
               script_sha256=BD.sha(os.path.abspath(__file__)),
               versions=dict(python=platform.python_version(), numpy=np.__version__, pandas=pd.__version__))
    json.dump(res, open(OUT['json'], 'w'), indent=1)
    L = ['# Would the novel days stay novel with a longer context? (weather only)', '',
         f"Of the 10 paired novel days, still novel with 8,192 half-hours (about 24 weeks): "
         f"{summ['paired_novel_days']['still_novel_C24']}; with about 49 weeks: {summ['paired_novel_days']['still_novel_C49']}.", '',
         '| Day | In pairs | Target min (°C) | Context min, 8 wk | 24 wk | 49 wk | Novel at 24 wk | Novel at 49 wk |',
         '|---|---|---|---|---|---|---|---|']
    for r in t.itertuples():
        L.append(f"| {r.day} | {'yes' if r.in_pairs else ''} | {r.t_tgt_min:.2f} | {r.C8_ctx_min:.2f} | {r.C24_ctx_min:.2f} | "
                 f"{r.C49_ctx_min:.2f} | {'yes' if r.C24_novel else 'no'} | {'yes' if r.C49_novel else 'no'} |")
    L += ['', 'By cold spell (paired novel days that stop being novel):', '', '```', json.dumps(summ['spells'], indent=1), '```']
    open(OUT['md'], 'w').write('\n'.join(L) + '\n')
    print('\n'.join(L))


# ------------------------------------------------------------------ synthetic ------------------------------------------
def synthetic():
    """Invented weather with known answers: a day whose only colder spell lies 23 weeks back (novel at 8 weeks, not at
    24); one whose colder spell lies 30 weeks back (novel at 24, not at 49); one never matched; the t2m_add shift
    applied to ERA5 only; and refusal when ERA5 does not reach far enough."""
    checks = {}
    days = ['2024-11-20', '2025-11-19', '2026-10-20']       # over 49 weeks apart: no shared windows
    frames = [BD.synth_frame(d, t_ctx_min=2.0, t_tgt_min=1.0) for d in days]
    cov = {d: f.reset_index(drop=True) for d, f in zip(days, frames)}
    for d in days: cov[d]['period_start_utc'] = pd.to_datetime(cov[d]['period_start_utc'], utc=True)
    first = min(cov[d]['period_start_utc'].iloc[0] for d in days) - 60 * 7 * 48 * H30
    idx = pd.date_range(first, max(cov[d]['period_start_utc'].iloc[C.CONTEXT_LEN - 1] for d in days), freq='30min')
    era5 = pd.Series(10.0, index=idx)
    cut = dict(zip('ABC', (C.input_end(pd.Timestamp(d)) for d in days)))
    era5[cut['A'] - pd.Timedelta(weeks=23)] = 0.0            # 23 weeks back: inside 24.4 weeks, outside 8 or 12
    era5[cut['B'] - pd.Timedelta(weeks=30)] = 0.0            # 30 weeks back: inside 49, outside 24
    era5[cut['C'] - pd.Timedelta(weeks=10)] = 1.5            # above the target's 1.0 until shifted by -0.6
    factors = {days[0]: 0.0, days[1]: 0.0, days[2]: -0.6}   # 1.5 - 0.6 = 0.9 < 1.0: no longer novel
    pairs = pd.DataFrame(dict(novel=days[:2], control=['x', 'y'], cluster=[1, 1]))
    t, summ = check(days, cov, era5, factors, pairs)
    r = t.set_index('day')
    checks['1_twenty_three_weeks_back'] = bool(r.at[days[0], 'C8_novel'] and not r.at[days[0], 'C24_novel'])
    checks['2_thirty_weeks_back'] = bool(r.at[days[1], 'C24_novel'] and not r.at[days[1], 'C49_novel'])
    checks['3_shift_applied_to_era5'] = bool(not r.at[days[2], 'C24_novel']
                                            and abs(r.at[days[2], 'C24_ctx_min'] - 0.9) < 1e-9)
    checks['4_summary'] = bool(summ['paired_novel_days']['still_novel_C24'] == 1
                               and summ['spells'][1] == {'C24': 1, 'C49': 2, 'pairs': 2})
    try:
        longer_context_min(days[0], cov[days[0]], era5[era5.index > cut['A'] - pd.Timedelta(weeks=12)], 0.0, 8192)
        checks['5_refuses_short_era5'] = False
    except AssertionError:
        checks['5_refuses_short_era5'] = True
    ok = all(checks.values())
    for k, v in checks.items(): print(('PASS ' if v else 'FAIL ') + k)
    json.dump(dict(passed=ok, checks=checks, script_sha256=BD.sha(os.path.abspath(__file__))), open(SYNTH, 'w'), indent=1)
    print('synthetic: ' + ('PASS' if ok else 'FAIL'))
    return ok


if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('--synthetic', action='store_true')
    if ap.parse_args().synthetic: sys.exit(0 if synthetic() else 1)
    real()
