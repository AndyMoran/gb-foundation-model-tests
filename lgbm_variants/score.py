"""
LightGBM variants: scoring (PLAN.md §5-7, frozen at tag lgbm-variants-plan; REVISIONS.md). Committed before it runs;
its outputs are committed after.

For: a reviewer checking that every ratio, the best-variant choice, H2-H4 and the headline follow PLAN.md §5-7.

Reads, after checking each file's SHA-256:
    the published backtest forecasts and outturn, the calendar forecasts and checkpoint 0's LightGBM forecasts, through
        checkpoint0/score.load (its own hashes); S1 is checkpoint 0's saved `lightgbm_s1`, which lightgbm_variants.py
        check 6 reproduced exactly
    lgbm_variants/forecasts.csv   against forecasts.json, and both, with checks.json, against the committed
                                  lightgbm_variants.py (LV_SHA below)
    tails/days.csv                against tails/days.json (T1)
    lgbm_variants/cost.json       if present (PLAN.md §5 item 5); reported, not scored
Writes lgbm_variants/results.json and results.md.

Imported from checkpoint0/score.py, unchanged: load, daily (mean absolute error per day, on days where every listed
forecaster has every half-hour), boot_idx (7-day moving blocks, 2,000 draws), ratio (percentile 90% interval) and
reading. The seed is this plan's, 20261119.

Metrics (PLAN.md §5), for S1, V1-V5, V2c and the two-year regression (REG2, shown, not compared):
    1 mean daily error and its ratio to the regression, over the 960 days
    2 the same ratio in winter (November to March) and in the other months
    3 the same ratio on the tails study's T1
    4 Chronos-2's ratio to each variant
Best variant: the lowest mean daily error among V1, V2, V3, V4 and V5 (V2c and REG2 cannot be chosen); a tie goes to
the earlier in that list. If V5 was dropped (PLAN.md §4), the choice is among the other four.

Hypotheses (PLAN.md §6). "Supported", "not supported" or "unclear" (REVISIONS.md item 15):
    H2  V1 is the best variant: supported or not supported (a choice on point estimates).
    H3  every variant's winter ratio is below S1's. Not supported if any point estimate is not below S1's; supported
        if all are and no variant's winter interval overlaps S1's; otherwise unclear.
    H4  V2's mean daily error is below V2c's: the same rule, on their ratios to the regression.

Headline (PLAN.md §7): the first sentence by the best variant's interval against 1, the second always.

Modes:
    python lgbm_variants/score.py --synthetic   invented forecasts with known ratios on the real calendar; writes
                                                lgbm_variants/score_synthetic.json. No outturn or forecast value read.
    python lgbm_variants/score.py               the real run; refused unless the synthetic check passed with this
                                                script, every guarded file is committed, and PLAN.md matches its tag.
"""
import argparse, json, os, subprocess, sys
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, 'checkpoint0'))
import score as S0                                           # noqa: E402  (checkpoint 0's scoring, unchanged)

SEED = 20261119
LV_SHA = '69968508e27a553c086bb6ce87958a7352c85b6f196863523b33cde28bce6671'   # gb-weather-private b1eb3fa
PLAN_TAG = 'lgbm-variants-plan'
FORECASTS, FJSON, CHECKS, COST = (os.path.join(HERE, f) for f in ('forecasts.csv', 'forecasts.json', 'checks.json', 'cost.json'))
TAILS_DAYS, TAILS_JSON = os.path.join(ROOT, 'tails', 'days.csv'), os.path.join(ROOT, 'tails', 'days.json')
SYNTH = os.path.join(HERE, 'score_synthetic.json')
GUARDED = ['lgbm_variants/score.py', 'lgbm_variants/PLAN.md', 'lgbm_variants/REVISIONS.md', 'lgbm_variants/forecasts.csv',
           'lgbm_variants/forecasts.json', 'lgbm_variants/checks.json', 'lgbm_variants/score_synthetic.json',
           'checkpoint0/score.py', 'tails/days.csv', 'tails/days.json']
REF, CHRONOS, S1 = 'regression_weather', 'chronos2_A', 'lightgbm_s1'
CANDIDATES = ['V1', 'V2', 'V3', 'V4', 'V5']
COL = {v: f'lgbm_{v.lower()}' for v in CANDIDATES + ['V2c', 'REG2']}
NAMES = {S1: 'LightGBM S1', **{COL[v]: v for v in COL}, REF: 'Weather regression', CHRONOS: 'Chronos-2'}
NAMES.update({COL['V2c']: 'V2c (control)', COL['REG2']: 'Regression, two years (shown, not compared)'})
WINTER = {11, 12, 1, 2, 3}

HEAD = {'below': 'In a 960-day backtest, the best of five pre-specified LightGBM variants ({V}) beat a weather regression: '
                 '{R} times its error (90% interval {L}–{U}).',
        'includes 1': 'In a 960-day backtest, the best of five pre-specified LightGBM variants ({V}) drew level with a '
                      'weather regression: {R} times its error (90% interval {L}–{U}).',
        'above': 'In a 960-day backtest, the best of five pre-specified LightGBM variants ({V}) still trailed a weather '
                 'regression: {R} times its error (90% interval {L}–{U}).'}
SECOND = ('In a backtest it may have seen in training, Chronos-2 had {C} times that variant\'s error (90% interval '
          '{L}–{U}); the variant was chosen on these same days, so its figure is optimistic.')


def git(*a):
    return subprocess.run(['git', '-C', ROOT, *a], capture_output=True, text=True, check=True).stdout.strip()


def f3(x):
    return f'{x:.3f}'


# ------------------------------------------------------------------ scoring (shared by both modes) ---------------------
def hyp_order(a, b):
    """'supported' if a's point estimate is below b's and their intervals do not overlap; 'unclear' if below but they
    overlap; 'not supported' otherwise. a, b: ratio dicts."""
    if not a['ratio'] < b['ratio']: return 'not supported'
    return 'supported' if a['ci90'][1] < b['ci90'][0] else 'unclear'


def score(f, t1, cols_v):
    """f: the merged half-hourly frame; t1: T1's days; cols_v: the variant columns present."""
    cols = [REF, CHRONOS, S1] + cols_v
    dm, dropped = S0.daily(f, cols)
    rng = np.random.default_rng(SEED)
    out = dict(n_days=len(dm), days_dropped=dropped, mean_daily_mae_mw={c: round(float(dm[c].mean()), 1) for c in cols})
    cmp = [S1] + cols_v
    out['vs_regression'] = S0.table_vs(dm, REF, cmp + [CHRONOS], rng)
    month = pd.to_datetime(dm.index).month
    for part, mask in (('winter', np.isin(month, list(WINTER))), ('other_months', ~np.isin(month, list(WINTER)))):
        out['vs_regression_' + part] = S0.table_vs(dm[mask], REF, cmp, rng)
    d1 = dm[dm.index.isin(t1)]
    out['vs_regression_T1'] = S0.table_vs(d1, REF, cmp, rng)
    out['chronos_vs_variant'] = {c: S0.ratio(dm[CHRONOS].to_numpy(), dm[c].to_numpy(), S0.boot_idx(len(dm), rng)) for c in cmp}
    cands = [v for v in CANDIDATES if COL[v] in cols_v]
    best = min(cands, key=lambda v: (round(float(dm[COL[v]].mean()), 9), CANDIDATES.index(v)))
    out['best_variant'] = dict(name=best, candidates=cands, column=COL[best])
    R = out['vs_regression'][COL[best]]; Cr = out['chronos_vs_variant'][COL[best]]
    k = S0.reading(R)
    out['headline'] = dict(reading=k,
                           first=HEAD[k].format(V=best, R=f3(R['ratio']), L=f3(R['ci90'][0]), U=f3(R['ci90'][1])),
                           second=SECOND.format(C=f3(Cr['ratio']), L=f3(Cr['ci90'][0]), U=f3(Cr['ci90'][1])))
    W = out['vs_regression_winter']
    h3 = {v: hyp_order(W[COL[v]], W[S1]) for v in cands}
    out['hypotheses'] = dict(
        H2=dict(reading='supported' if best == 'V1' else 'not supported', best=best),
        H3=dict(reading=('not supported' if 'not supported' in h3.values() else
                         'supported' if all(r == 'supported' for r in h3.values()) else 'unclear'), by_variant=h3,
                note='V5 dropped' if 'V5' not in cands else ''),
        H4=dict(reading=hyp_order(out['vs_regression'][COL['V2']], out['vs_regression'][COL['V2c']])))
    return out


# ------------------------------------------------------------------ report ---------------------------------------------
def iv(r):
    return f"{f3(r['ratio'])} ({f3(r['ci90'][0])}–{f3(r['ci90'][1])})"


def markdown(out, cols_v, cost):
    h, H = out['headline'], out['hypotheses']
    rows = [S1] + cols_v
    L = ['# LightGBM variants: results (descriptive backtest)', '',
         f"{out['n_days']} days. Mean daily error: each day's mean absolute error over its half-hours. Ratios are to the "
         'weather regression\'s mean daily error; 90% intervals from a 7-day moving-block bootstrap (2,000 draws, seed '
         '20261119). An interval wholly below 1 beats the regression; wholly above, trails it; otherwise level.', '',
         '**Headline (PLAN.md §7):**', '', h['first'], '', h['second'], '',
         f"Best variant: **{out['best_variant']['name']}** (lowest mean daily error among {', '.join(out['best_variant']['candidates'])}).", '',
         '## Against the regression', '',
         '| Forecaster | Mean daily error (MW) | All days | Winter (Nov–Mar) | Other months | T1 (coldest tenth) | Chronos-2 ÷ forecaster |',
         '|---|---|---|---|---|---|---|']
    for c in rows:
        L.append(f"| {NAMES.get(c, c)} | {out['mean_daily_mae_mw'][c]:,.0f} | {iv(out['vs_regression'][c])} | "
                 f"{iv(out['vs_regression_winter'][c])} | {iv(out['vs_regression_other_months'][c])} | "
                 f"{iv(out['vs_regression_T1'][c])} | {iv(out['chronos_vs_variant'][c])} |")
    L += [f"| {NAMES[CHRONOS]} | {out['mean_daily_mae_mw'][CHRONOS]:,.0f} | {iv(out['vs_regression'][CHRONOS])} | | | | |",
          f"| {NAMES[REF]} | {out['mean_daily_mae_mw'][REF]:,.0f} | 1 | 1 | 1 | 1 | |", '',
          '## Hypotheses (PLAN.md §6)', '',
          f"- **H2** (V1 is the best variant): {H['H2']['reading']}; the best was {H['H2']['best']}.",
          f"- **H3** (every variant's winter ratio below S1's): {H['H3']['reading']}. By variant: "
          + ', '.join(f'{k} {v}' for k, v in H['H3']['by_variant'].items()) + (f" ({H['H3']['note']})" if H['H3']['note'] else '') + '.',
          f"- **H4** (V2 below V2c): {H['H4']['reading']}.", '',
          '"Unclear" means the point estimates point the hypothesis\'s way but the intervals overlap (REVISIONS.md item 15).']
    if out['days_dropped']: L += ['', f"Days dropped (a forecaster missing a half-hour): {', '.join(out['days_dropped'])}."]
    if cost:
        L += ['', '## Cost (PLAN.md §5 item 5; 20 sample days, 4 threads)', '', '| Forecaster | Seconds per day (median) | Peak memory (MB) |', '|---|---|---|']
        for r in cost['rows']: L.append(f"| {r['name']} | {r['seconds_per_day_median']} | {r['peak_rss_mb']} |")
    return '\n'.join(L) + '\n'


# ------------------------------------------------------------------ real run -------------------------------------------
def load_real():
    fj, ck = json.load(open(FJSON)), json.load(open(CHECKS))
    if S0.sha(FORECASTS) != fj['forecasts_sha256']: sys.exit('Refused: forecasts.csv differs from forecasts.json.')
    if fj['script_sha256'] != LV_SHA or ck['script_sha256'] != LV_SHA or not ck['passed']:
        sys.exit('Refused: forecasts or checks are not from the committed lightgbm_variants.py, or its checks failed.')
    if S0.sha(TAILS_DAYS) != json.load(open(TAILS_JSON))['days_csv_sha256']: sys.exit('Refused: tails/days.csv changed.')
    f = S0.load()
    v = pd.read_csv(FORECASTS)
    n0 = len(f)
    f = f.merge(v.drop(columns='day'), on='start_utc', how='left', validate='one_to_one'); assert len(f) == n0
    cols_v = [COL[x] for x in CANDIDATES[:4] + ['V2c'] + (['V5', 'REG2'] if not fj['v5_dropped'] else []) if COL[x] in v.columns]
    t = pd.read_csv(TAILS_DAYS, usecols=['set', 'day'])
    return f, sorted(t.loc[t.set == 'T1', 'day']), cols_v, fj


def real():
    sy = json.load(open(SYNTH)) if os.path.exists(SYNTH) else {}
    if not sy.get('passed') or sy.get('script_sha256') != S0.sha(os.path.abspath(__file__)):
        sys.exit('Refused: the synthetic check has not passed with this script.')
    if git('status', '--porcelain', '--', *GUARDED): sys.exit('Refused: commit these first: ' + ', '.join(GUARDED))
    if git('diff', '--name-only', PLAN_TAG, 'HEAD', '--', 'lgbm_variants/PLAN.md'): sys.exit(f'Refused: PLAN.md differs from {PLAN_TAG}.')
    f, t1, cols_v, fj = load_real()
    out = score(f, t1, cols_v)
    cost = json.load(open(COST)) if os.path.exists(COST) else None
    meta = dict(public_commit=git('rev-parse', 'HEAD'), plan_tag_commit=git('rev-parse', PLAN_TAG + '^{commit}'),
                script_sha256=S0.sha(os.path.abspath(__file__)), lightgbm_variants_sha256=LV_SHA,
                forecasts_sha256=fj['forecasts_sha256'], v5_dropped=fj['v5_dropped'], seed=SEED,
                cost_sha256=S0.sha(COST) if cost else None)
    res = dict(note='LightGBM variants; descriptive backtest; plan frozen at tag ' + PLAN_TAG, meta=meta, **out)
    json.dump(res, open(os.path.join(HERE, 'results.json'), 'w'), indent=1)
    md = markdown(out, cols_v, cost)
    open(os.path.join(HERE, 'results.md'), 'w').write(md)
    print(md)


# ------------------------------------------------------------------ synthetic check ------------------------------------
def synth_frame(grid, factors, t1=(), t1_factor=None, winter_factor=None):
    """Outturn 30,000 MW on every half-hour of the real calendar; forecaster c misses by 1,000 x factors[c] MW on every
    half-hour, so its mean daily error is exactly that and every ratio is exact. t1_factor / winter_factor override a
    forecaster's factor on T1 or winter days."""
    f = grid.copy(); f['outturn'] = 30000.0
    month = pd.to_datetime(f['day']).dt.month.to_numpy(); in_t1 = f['day'].isin(set(t1)).to_numpy()
    for c, k in factors.items():
        kk = np.full(len(f), float(k))
        if winter_factor and c in winter_factor: kk[np.isin(month, list(WINTER))] = winter_factor[c]
        if t1_factor and c in t1_factor: kk[in_t1] = t1_factor[c]
        f[c] = f['outturn'] - 1000.0 * kk
    return f


def synthetic():
    for p, h in list(S0.FILES.items())[:1]:
        if S0.sha(p) != h: sys.exit('Refused: forecasts.csv hash')
    grid = pd.read_csv(list(S0.FILES)[0], usecols=['day', 'start_utc'])           # the real calendar; no values
    t = pd.read_csv(TAILS_DAYS, usecols=['set', 'day']); t1 = sorted(t.loc[t.set == 'T1', 'day'])
    allv = [COL[v] for v in ['V1', 'V2', 'V3', 'V4', 'V2c', 'V5', 'REG2']]
    base = {REF: 1.0, CHRONOS: 0.9, S1: 1.05, COL['V1']: 0.95, COL['V2']: 1.02, COL['V3']: 1.03, COL['V4']: 1.01,
            COL['V2c']: 1.04, COL['V5']: 0.97, COL['REG2']: 0.99}
    checks, ok = {}, True

    def check(name, cond, **info):
        nonlocal ok
        checks[name] = dict(passed=bool(cond), **info); ok &= bool(cond)
        print(('PASS ' if cond else 'FAIL ') + name, flush=True)

    # 1: exact ratios, best variant, headline "below", H2 supported, H4 supported (no spread, so no overlap)
    o = score(synth_frame(grid, base), t1, allv)
    r = o['vs_regression']
    check('1_ratios_best_below', abs(r[COL['V1']]['ratio'] - 0.95) < 1e-9 and r[COL['V1']]['ci90'] == [0.95, 0.95]
          and o['best_variant']['name'] == 'V1' and o['headline']['reading'] == 'below'
          and o['headline']['first'].startswith('In a 960-day backtest, the best of five pre-specified LightGBM variants (V1) beat')
          and '0.950 times its error (90% interval 0.950–0.950)' in o['headline']['first']
          and abs(o['chronos_vs_variant'][COL['V1']]['ratio'] - 0.9 / 0.95) < 1e-4
          and o['hypotheses']['H2']['reading'] == 'supported' and o['hypotheses']['H4']['reading'] == 'supported',
          headline=o['headline'], hyp=o['hypotheses'])
    # 2: V2c is never chosen, REG2 is never chosen; tie between V3 and V4 goes to V3; trailing headline
    f2 = dict(base, **{COL['V1']: 1.2, COL['V2']: 1.2, COL['V3']: 1.1, COL['V4']: 1.1, COL['V5']: 1.2,
                       COL['V2c']: 0.5, COL['REG2']: 0.5})
    o = score(synth_frame(grid, f2), t1, allv)
    check('2_control_excluded_tie_trailing', o['best_variant']['name'] == 'V3' and o['headline']['reading'] == 'above'
          and 'still trailed' in o['headline']['first'] and o['hypotheses']['H2']['reading'] == 'not supported'
          and o['hypotheses']['H4']['reading'] == 'not supported', best=o['best_variant'], headline=o['headline'])
    # 3: level headline: the best variant equals the regression on average but varies, so its interval spans 1
    f3_ = synth_frame(grid, dict(base, **{COL['V1']: 1.0, COL['V5']: 1.1}))
    days = sorted(f3_['day'].unique()); half = set(days[::2])
    f3_.loc[f3_['day'].isin(half), COL['V1']] = 30000 - 800.0; f3_.loc[~f3_['day'].isin(half), COL['V1']] = 30000 - 1200.0
    o = score(f3_, t1, allv)
    check('3_level', o['best_variant']['name'] == 'V1' and o['headline']['reading'] == 'includes 1'
          and 'drew level' in o['headline']['first'], ci=o['vs_regression'][COL['V1']]['ci90'])
    # 4: winter and T1 split; H3 supported when every winter ratio is below S1's; not supported when one is not
    w = {S1: 1.3, COL['V1']: 1.1, COL['V2']: 1.1, COL['V3']: 1.1, COL['V4']: 1.1, COL['V5']: 1.1}
    # T1 days are winter days, so S1 is raised on T1 too, keeping every variant's winter ratio below S1's
    o = score(synth_frame(grid, base, t1=t1, t1_factor={COL['V4']: 2.0, S1: 2.5}, winter_factor=w), t1, allv)
    W, T = o['vs_regression_winter'], o['vs_regression_T1']
    okw = (abs(W[COL['V1']]['ratio'] - 1.1) < 1e-9 and abs(o['vs_regression_other_months'][S1]['ratio'] - 1.05) < 1e-9
           and abs(T[COL['V4']]['ratio'] - 2.0) < 1e-9 and abs(T[S1]['ratio'] - 2.5) < 1e-9
           and o['hypotheses']['H3']['reading'] == 'supported')
    o2 = score(synth_frame(grid, base, winter_factor=dict(w, **{COL['V3']: 1.4})), t1, allv)
    check('4_winter_T1_H3', okw and o2['hypotheses']['H3']['reading'] == 'not supported'
          and o2['hypotheses']['H3']['by_variant']['V3'] == 'not supported', H3=[o['hypotheses']['H3'], o2['hypotheses']['H3']])
    # 5: unclear: points below but intervals overlap (V2 and V2c both vary across days)
    f5 = synth_frame(grid, base)
    f5.loc[f5['day'].isin(half), COL['V2']] = 30000 - 700.0; f5.loc[~f5['day'].isin(half), COL['V2']] = 30000 - 1290.0
    f5.loc[f5['day'].isin(half), COL['V2c']] = 30000 - 710.0; f5.loc[~f5['day'].isin(half), COL['V2c']] = 30000 - 1300.0
    o = score(f5, t1, allv)
    check('5_unclear', o['hypotheses']['H4']['reading'] == 'unclear', V2=o['vs_regression'][COL['V2']], V2c=o['vs_regression'][COL['V2c']])
    # 6: V5 dropped: the choice is among the other four, H3 notes it
    cols4 = [COL[v] for v in ['V1', 'V2', 'V3', 'V4', 'V2c']]
    o = score(synth_frame(grid, dict(base, **{COL['V5']: 0.1})), t1, cols4)
    check('6_v5_dropped', o['best_variant']['candidates'] == ['V1', 'V2', 'V3', 'V4'] and o['best_variant']['name'] == 'V1'
          and o['hypotheses']['H3']['note'] == 'V5 dropped', best=o['best_variant'])
    json.dump(dict(passed=bool(ok), script_sha256=S0.sha(os.path.abspath(__file__)), checks=checks),
              open(SYNTH, 'w'), indent=1, default=str)
    print('synthetic: ' + ('PASS' if ok else 'FAIL'))
    return ok


if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('--synthetic', action='store_true')
    if ap.parse_args().synthetic: sys.exit(0 if synthetic() else 1)
    real()
