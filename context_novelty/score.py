"""
Context novelty, step 2 (context_novelty/PLAN.md §9, version 2, frozen at tag context-novelty-plan-v2; deviations 12-16
in REVISIONS.md): score the matched pairs and the novelty set. Committed before it runs; its outputs are committed after.

For: a reviewer checking that Δ, its interval, the H5 reading and the headline follow PLAN.md §6-8 and REVISIONS.md.

Reads, after checking each file's SHA-256:
    the tails study's forecast files, through tails/score_tails.load_real (its hashes, its outturn check)
    context_novelty/days.csv, pairs.csv, day_inputs.csv   against the hashes in context_novelty/days.json
    tails/days.csv                                        against tails/days.json (T1, for the unmatched comparison)
Writes context_novelty/results.json and context_novelty/results.md.

Imported from tails/score_tails.py, unchanged: load_real, per_day (which days are scored; each day's peak error and
mean absolute error), masks, region, boot_idx and ci (the secondary metrics on N, PLAN.md §6).

Primary (PLAN.md §6). Peak error: the day's highest outturn half-hour minus the forecaster's highest forecast
half-hour, in MW. Excess peak error: a forecaster's peak error minus the regression's on the same day. Δ: the mean over
the pairs of (novel day's excess − its control's). Interval: 90% percentile interval from 2,000 draws (seed 20261120),
each resampling the cold spells (pairs.csv's `cluster`) with replacement and keeping every pair in each spell drawn.

H5 reading (PLAN.md §7), on Chronos-2's Δ, with "above" and "below" strict:
    lower bound > 250 MW            meaningful penalty supported
    lower bound > 0 MW              positive penalty supported; meaningful size not shown
    upper bound < 0 MW              smaller on novel days
    otherwise                       unclear
    fewer than 10 pairs             not assessed (no average or interval; pairs one by one)
The same rule is reported at 100 MW and 500 MW (sensitivity). TimesFM 2.5: Δ and interval, no reading (exploratory).
Timestral and LightGBM S1: Δ and interval (descriptive).

Also reported (REVISIONS.md 12-16): Δ for each cold spell and the leave-one-spell-out range; each pair, with its
balance; the four unmatched novel days one by one; the unmatched comparison (every novel day against every T1-N day,
point estimate only, descriptive); the tails study's metrics on N against its broad and narrow complements.

Headline: PLAN.md §8's sentence for the H5 reading, then a second sentence giving the pairs, their winters, the cold
spells and the unmatched days (REVISIONS.md 12). Numbers are whole MW. Where an interval's lower bound is negative,
"L–U" is written "L to U", because a dash after a minus sign misreads (REVISIONS.md 17).

Modes:
    python context_novelty/score.py --synthetic   invented forecasts with known Δ on the real calendar and the real
                                                  pairs; writes context_novelty/synthetic.json; exits 1 on any failure.
                                                  No outturn or forecast value is read.
    python context_novelty/score.py               the real run. Refused unless the synthetic check passed with this
                                                  script and these pairs, and every guarded file is committed and
                                                  unchanged, and PLAN.md matches tag context-novelty-plan-v2.
"""
import argparse, hashlib, json, os, platform, subprocess, sys
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, 'tails'))
import score_tails as T                                      # noqa: E402  (the tails study's scoring, unchanged)

DAYS_CSV, PAIRS_CSV = os.path.join(HERE, 'days.csv'), os.path.join(HERE, 'pairs.csv')
DAY_INPUTS, DAYS_JSON = os.path.join(HERE, 'day_inputs.csv'), os.path.join(HERE, 'days.json')
BUILD, SYNTH_JSON = os.path.join(HERE, 'build_days.py'), os.path.join(HERE, 'synthetic.json')
PLAN_TAG = 'context-novelty-plan-v2'
GUARDED = ['context_novelty/score.py', 'context_novelty/build_days.py', 'context_novelty/PLAN.md',
           'context_novelty/REVISIONS.md', 'context_novelty/days.csv', 'context_novelty/pairs.csv',
           'context_novelty/day_inputs.csv', 'context_novelty/days.json', 'context_novelty/synthetic.json',
           'tails/score_tails.py', 'tails/days.csv', 'tails/days.json']
SEED, B = 20261120, 2000
THRESHOLD, SENSITIVITY = 250.0, (100.0, 500.0)
MIN_PAIRS = 10
SCHEMA = 1

REF = T.REF
PRIMARY = 'chronos2_A'
EXPLORATORY = ['timesfm25_weather_single_day']
DESCRIPTIVE = ['timestral_A', 'lightgbm_s1']
DELTA_FORECASTERS = [PRIMARY] + EXPLORATORY + DESCRIPTIVE
N_FORECASTERS = [REF] + DELTA_FORECASTERS
NAMES = dict(T.NAMES, timestral_A='Timestral (descriptive)', lightgbm_s1='LightGBM S1 (descriptive)',
             timesfm25_weather_single_day='TimesFM 2.5, one day per call (exploratory)')
READINGS = ('meaningful penalty supported', 'positive penalty supported; meaningful size not shown', 'unclear',
            'smaller on novel days', 'not assessed')


def sha(p):
    return T.sha(p)


def git(*a):
    return subprocess.run(['git', '-C', ROOT, *a], capture_output=True, text=True, check=True).stdout.strip()


# ------------------------------------------------------------------ inputs ---------------------------------------------
def load_sets():
    dj = json.load(open(DAYS_JSON))
    for p, k in ((DAYS_CSV, 'days_csv_sha256'), (PAIRS_CSV, 'pairs_csv_sha256'), (DAY_INPUTS, 'day_inputs_csv_sha256')):
        if sha(p) != dj[k]: sys.exit(f'Refused: {os.path.relpath(p, ROOT)} differs from the hash in days.json.')
    if sha(T.DAYS_CSV) != json.load(open(T.DAYS_JSON))['days_csv_sha256']:
        sys.exit('Refused: tails/days.csv differs from tails/days.json.')
    d = pd.read_csv(DAYS_CSV, dtype={'day': str})
    sets = {s: sorted(set(d.loc[d['set'] == s, 'day'])) for s in ('N', 'N&T1', 'T1-N', 'Nw')}
    sets['T1'] = T.load_days(T.DAYS_CSV)['T1']
    pairs = pd.read_csv(PAIRS_CSV, dtype={'novel': str, 'control': str})
    return sets, pairs, dj['matching']['unmatched'], dj


# ------------------------------------------------------------------ the primary comparison -----------------------------
def excess(P, c):
    """Per scored day: forecaster c's peak error minus the regression's, MW."""
    return dict(zip(P['days'], P['peak'][c] - P['peak'][REF]))


def cluster_draws(pairs, diff, rng):
    """Δ in each of B draws: resample cold spells with replacement, keep every pair in each spell drawn."""
    spells = sorted(pairs['cluster'].unique())
    by = {k: diff[(pairs['cluster'] == k).to_numpy()] for k in spells}
    pick = rng.integers(0, len(spells), size=(B, len(spells)))
    sums = np.array([[by[spells[j]].sum() for j in row] for row in pick])
    cnts = np.array([[len(by[spells[j]]) for j in row] for row in pick])
    return sums.sum(1) / cnts.sum(1)


def reading(iv, threshold):
    lo, hi = iv
    if lo > threshold: return READINGS[0]
    if lo > 0: return READINGS[1]
    if hi < 0: return READINGS[3]
    return READINGS[2]


def compare(P, pairs, c, rng):
    """Δ for forecaster c on the pairs, with its interval, its spells and the leave-one-spell-out range."""
    e = excess(P, c)
    en = pairs['novel'].map(e).to_numpy(float); ec = pairs['control'].map(e).to_numpy(float)
    diff = en - ec
    res = dict(pairs=[dict(novel=r.novel, control=r.control, cluster=int(r.cluster), excess_novel=float(a),
                           excess_control=float(b), difference=float(a - b))
                      for r, a, b in zip(pairs.itertuples(), en, ec)])
    if len(pairs) < MIN_PAIRS:
        res['delta'] = None; return res
    draws = cluster_draws(pairs, diff, rng)
    spells = sorted(pairs['cluster'].unique())
    res['delta'] = float(diff.mean()); res['ci90'] = T.ci(draws)
    res['distinct_draws'] = int(len(np.unique(np.round(draws, 6))))
    res['spells'] = {int(k): dict(pairs=int((pairs['cluster'] == k).sum()),
                                  delta=float(diff[(pairs['cluster'] == k).to_numpy()].mean())) for k in spells}
    loo = {int(k): float(diff[(pairs['cluster'] != k).to_numpy()].mean()) for k in spells}
    res['leave_one_spell_out'] = dict(by_spell_left_out=loo, min=min(loo.values()), max=max(loo.values()))
    return res


# ------------------------------------------------------------------ headline -------------------------------------------
def mw(x):
    s = f'{abs(x):,.0f}'
    return ('−' + s) if round(x) < 0 else s


def iv_text(iv):
    lo, hi = iv
    return f'{mw(lo)} to {mw(hi)}' if round(lo) < 0 else f'{mw(lo)}–{mw(hi)}'


TEMPLATES = {
    READINGS[0]: "In a backtest it may have seen in training, Chronos-2 under-forecast the daily peak, relative to a weather "
                 "regression, by {D} MW more on cold days colder than its eight-week context than on matched cold days "
                 "that were not (90% interval {LU}, above the 250 MW threshold set in advance).",
    READINGS[1]: "In a backtest it may have seen in training, Chronos-2 under-forecast the daily peak, relative to a weather "
                 "regression, by {D} MW more on cold days colder than its eight-week context than on matched cold days "
                 "that were not (90% interval {LU}). A penalty of 250 MW, the threshold set in advance, was not shown.",
    READINGS[2]: "In a backtest it may have seen in training, Chronos-2's peak error relative to a weather regression did "
                 "not clearly differ between cold days colder than its eight-week context and matched cold days that were "
                 "not (difference {D} MW, 90% interval {LU}).",
    READINGS[3]: "In a backtest it may have seen in training, Chronos-2 under-forecast the daily peak, relative to a weather "
                 "regression, by {D} MW less on cold days colder than its eight-week context than on matched cold days "
                 "that were not (90% interval {LU}).",
    READINGS[4]: "Too few cold days colder than Chronos-2's eight-week context could be matched for a comparison "
                 "({n} pairs from {m} novel days).",
}


def winter(d):
    D = pd.Timestamp(d)
    if D.month >= 11: return f'winter {D.year}-{str(D.year + 1)[2:]}'
    if D.month <= 3: return f'winter {D.year - 1}-{str(D.year)[2:]}'
    return f'Apr-Oct {D.year}'


def headline(primary, pairs, n_novel, unmatched):
    if primary['delta'] is None:
        k = READINGS[4]; first = TEMPLATES[k].format(n=len(pairs), m=n_novel)
    else:
        k = reading(primary['ci90'], THRESHOLD); d = primary['delta']
        D = mw(d) if k == READINGS[2] else f'{abs(d):,.0f}'
        first = TEMPLATES[k].format(D=D, LU=iv_text(primary['ci90']))
    wc = pd.Series([winter(d) for d in pairs['novel']]).value_counts().sort_index()
    wtxt = ' and '.join(f'{v} in {w}' for w, v in wc.items())
    second = (f"The comparison rests on {len(pairs)} pairs ({wtxt}) in {pairs['cluster'].nunique()} cold spells. "
              f"It does not estimate the difference for the {len(unmatched)} novel days that could not be matched "
              f"({', '.join(pd.Timestamp(d).strftime('%-d %B %Y') for d in unmatched)}), which include the coldest days, "
              f"or for the full cold tail.")
    return k, first, second


# ------------------------------------------------------------------ scoring --------------------------------------------
def score(frame, sets, pairs, unmatched):
    P = T.per_day(frame)
    scored = set(P['days'])
    missing = sorted((set(pairs['novel']) | set(pairs['control']) | set(unmatched)) - scored)
    if missing: sys.exit(f'Stopped: paired or unmatched days not scored: {missing}. The plan does not cover this.')
    out = dict(n_scored_days=len(P['days']), n_pairs=len(pairs), n_spells=int(pairs['cluster'].nunique()),
               n_novel=len(sets['N&T1']), unmatched=unmatched, forecasters={})
    for c in DELTA_FORECASTERS:
        out['forecasters'][c] = compare(P, pairs, c, np.random.default_rng(SEED))
    p = out['forecasters'][PRIMARY]
    if p['delta'] is not None:
        out['h5'] = dict(reading=reading(p['ci90'], THRESHOLD), threshold_mw=THRESHOLD,
                         sensitivity={f'{t:.0f}': reading(p['ci90'], t) for t in SENSITIVITY})
    else:
        out['h5'] = dict(reading=READINGS[4], threshold_mw=THRESHOLD)
    k, s1, s2 = headline(p, pairs, len(sets['N&T1']), unmatched)
    out['headline'] = dict(reading=k, sentence=s1, second=s2)
    # unmatched novel days, one by one (REVISIONS.md 13)
    pe = {c: dict(zip(P['days'], P['peak'][c])) for c in N_FORECASTERS}
    out['unmatched_days'] = [dict(day=d, **{c: dict(peak=float(pe[c][d]),
                                                    excess=None if c == REF else float(pe[c][d] - pe[REF][d]))
                                            for c in N_FORECASTERS}) for d in unmatched]
    # unmatched comparison: every novel day against every T1-N day, point estimate only (PLAN.md §6)
    out['unmatched_comparison'] = {}
    for c in DELTA_FORECASTERS:
        e = excess(P, c)
        out['unmatched_comparison'][c] = dict(
            novel_mean=float(np.mean([e[d] for d in sets['N&T1']])),
            control_pool_mean=float(np.mean([e[d] for d in sets['T1-N']])),
            difference=float(np.mean([e[d] for d in sets['N&T1']]) - np.mean([e[d] for d in sets['T1-N']])))
    # the tails study's metrics on N (PLAN.md §6), with its own bootstrap and this study's seed
    I = T.boot_idx(len(P['days']), np.random.default_rng(SEED))
    mk = T.masks(P['days'], sets['N'])
    out['N'] = dict(n_scored=int(mk['set'].sum()), n_narrow=int(mk['narrow'].sum()), n_broad=int(mk['broad'].sum()),
                    forecasters={})
    for c in N_FORECASTERS:
        R, D = {}, {}
        for r in T.REGIONS: R[r], D[r] = T.region(P, I, c, mk[r])
        for comp in ('broad', 'narrow'):
            bs = D['set']['ratio'] / D[comp]['ratio']
            R['shift_' + comp] = dict(value=float(R['set']['ratio'] / R[comp]['ratio']), ci90=T.ci(bs),
                                      draws_dropped=int((~np.isfinite(bs)).sum()))
        out['N']['forecasters'][c] = R
    out['N']['ratios_withheld'] = bool(out['N']['forecasters'][REF]['set']['mde'] < 100)    # PLAN.md §6
    return out


# ------------------------------------------------------------------ report ---------------------------------------------
def fmt_iv(v, iv):
    return f"{mw(v)} ({iv_text(iv)})" if iv else mw(v)


def markdown(out, meta, pairs):
    h, H5 = out['headline'], out['h5']
    L = ['# Context novelty: results (descriptive backtest)', '',
         'Backtest days the foundation models may have seen in training. Peak error: the day\'s highest outturn '
         'half-hour minus the forecaster\'s highest forecast half-hour (MW); positive means the forecast peak was too '
         'low. Excess peak error: a forecaster\'s peak error minus the regression\'s. Δ: the mean over pairs of the '
         'novel day\'s excess minus its control\'s. 90% intervals resample the cold spells (PLAN.md §6).', '',
         '**Headline (PLAN.md §8):**', '', h['sentence'], '', h['second'], '',
         f"H5 (Chronos-2): **{H5['reading']}** at the 250 MW threshold."
         + (f" At 100 MW: {H5['sensitivity']['100']}. At 500 MW: {H5['sensitivity']['500']}." if 'sensitivity' in H5 else ''),
         '', '## Δ by forecaster', '',
         '| Forecaster | Δ (MW), 90% interval | Distinct bootstrap draws | Leave-one-spell-out range (MW) |', '|---|---|---|---|']
    for c in DELTA_FORECASTERS:
        F = out['forecasters'][c]
        if F['delta'] is None: L.append(f"| {NAMES[c]} | not assessed | — | — |"); continue
        lo = F['leave_one_spell_out']
        L.append(f"| {NAMES[c]} | {fmt_iv(F['delta'], F['ci90'])} | {F['distinct_draws']} | {mw(lo['min'])} to {mw(lo['max'])} |")
    L += ['', '## Δ by cold spell (description)', '', '| Spell | Pairs | ' + ' | '.join(NAMES[c] for c in DELTA_FORECASTERS) + ' |',
          '|---|---|' + '---|' * len(DELTA_FORECASTERS)]
    F0 = out['forecasters'][PRIMARY]
    if F0['delta'] is not None:
        for k in sorted(F0['spells']):
            L.append(f"| {k} | {F0['spells'][k]['pairs']} | " +
                     ' | '.join(mw(out['forecasters'][c]['spells'][k]['delta']) for c in DELTA_FORECASTERS) + ' |')
    L += ['', '## The pairs (Chronos-2) and their balance', '',
          '| Novel day | Control | Spell | Excess, novel (MW) | Excess, control (MW) | Difference (MW) | Δ mean temp (°C) | Δ daily min (°C) | Δ month |',
          '|---|---|---|---|---|---|---|---|---|']
    for r, b in zip(F0['pairs'], pairs.itertuples()):
        L.append(f"| {r['novel']} | {r['control']} | {r['cluster']} | {mw(r['excess_novel'])} | {mw(r['excess_control'])} | "
                 f"{mw(r['difference'])} | {b.d_t_mean:+.2f} | {b.d_t_min:+.2f} | {b.d_month} |")
    L += ['', '## The unmatched novel days, one by one (description)', '',
          '| Day | ' + ' | '.join(f'{NAMES[c]}: peak (excess)' for c in N_FORECASTERS) + ' |', '|---|' + '---|' * len(N_FORECASTERS)]
    for u in out['unmatched_days']:
        L.append(f"| {u['day']} | " + ' | '.join(mw(u[c]['peak']) + ('' if u[c]['excess'] is None else f" ({mw(u[c]['excess'])})")
                                                 for c in N_FORECASTERS) + ' |')
    L += ['', '## Unmatched comparison: every novel day against every T1∖N day (description, no interval)', '',
          '| Forecaster | Mean excess, novel days (MW) | Mean excess, T1∖N (MW) | Difference (MW) |', '|---|---|---|---|']
    for c in DELTA_FORECASTERS:
        U = out['unmatched_comparison'][c]
        L.append(f"| {NAMES[c]} | {mw(U['novel_mean'])} | {mw(U['control_pool_mean'])} | {mw(U['difference'])} |")
    N = out['N']
    if N['ratios_withheld']: L += ['', "Ratios withheld on N: the regression's mean daily error is below 100 MW (PLAN.md §6)."]
    L += ['', f"## The tails study's metrics on N ({N['n_scored']} days; narrow complement {N['n_narrow']}, broad {N['n_broad']})", '',
          '| Forecaster | Mean daily error (MW) | Ratio to regression | Shift, narrow | Shift, broad | Bias (MW) | Peak error (MW) | Worst day (MW) | 95th pct (MW) |',
          '|---|---|---|---|---|---|---|---|---|']
    for c in N_FORECASTERS:
        R = N['forecasters'][c]; st = R['set']; sn, sb = R['shift_narrow'], R['shift_broad']
        L.append(f"| {NAMES[c]} | {st['mde']:,.0f} | {T.fmt_iv(st['ratio'], st['ratio_ci90'])} | {T.fmt_iv(sn['value'], sn['ci90'])} | "
                 f"{T.fmt_iv(sb['value'], sb['ci90'])} | {fmt_iv(st['bias'], st['bias_ci90'])} | {fmt_iv(st['peak'], st['peak_ci90'])} | "
                 f"{st['worst_day']['day']}: {st['worst_day']['mw']:,.0f} | {st['p95']:,.0f} |")
    L += ['', '## Provenance', '', '```', json.dumps(meta, indent=1), '```', '']
    return '\n'.join(L)


# ------------------------------------------------------------------ real run -------------------------------------------
def real():
    if not os.path.exists(SYNTH_JSON): sys.exit('Refused: run --synthetic first, and commit synthetic.json.')
    if git('status', '--porcelain', '--', *GUARDED):
        sys.exit('Refused: these must be committed and unchanged: ' + ', '.join(GUARDED))
    if git('diff', '--name-only', PLAN_TAG, 'HEAD', '--', 'context_novelty/PLAN.md'):
        sys.exit(f'Refused: PLAN.md differs from tag {PLAN_TAG}.')
    sets, pairs, unmatched, dj = load_sets()
    if sha(BUILD) != dj['provenance']['script_sha256']: sys.exit('Refused: days.json was not made by the committed build_days.py.')
    sy = json.load(open(SYNTH_JSON))
    if not sy.get('passed') or sy.get('script_sha256') != sha(os.path.abspath(__file__)) or sy.get('pairs_csv_sha256') != sha(PAIRS_CSV):
        sys.exit('Refused: the synthetic check has not passed with this script and these pairs.')
    frame = T.load_real()
    out = score(frame, sets, pairs, unmatched)
    meta = dict(public_commit=git('rev-parse', 'HEAD'), plan_tag_commit=git('rev-parse', PLAN_TAG + '^{commit}'),
                script_sha256=sha(os.path.abspath(__file__)), tails_script_sha256=sha(os.path.join(ROOT, 'tails', 'score_tails.py')),
                pairs_csv_sha256=sha(PAIRS_CSV), days_csv_sha256=sha(DAYS_CSV),
                files_sha256={os.path.relpath(p, ROOT): h for p, h in T.FILES.items()}, seed=SEED, draws=B,
                versions=dict(python=platform.python_version(), numpy=np.__version__, pandas=pd.__version__))
    out = dict(schema=SCHEMA, note='context novelty; descriptive backtest; plan version 2 at tag ' + PLAN_TAG,
               meta=meta, **T.round_floats(out))
    json.dump(out, open(os.path.join(HERE, 'results.json'), 'w'), indent=1)
    md = markdown(out, meta, pairs)
    open(os.path.join(HERE, 'results.md'), 'w').write(md)
    print(md)


# ------------------------------------------------------------------ synthetic check ------------------------------------
BASE_MW, REF_EXTRA, BACKGROUND_MW = 30000.0, 120.0, 50.0


def synth_frame(grid, peaks):
    """Invented outturn on the real calendar; each forecaster's forecast is outturn minus a per-day constant, so its
    peak error on day d is exactly peaks[c][d] (BACKGROUND_MW where not given, so no ratio divides by zero)."""
    f = grid.copy()
    slot = f.groupby('day').cumcount().to_numpy(float)
    f['outturn'] = BASE_MW + 8000 * np.sin(np.pi * slot / 48)
    for c in T.FORECASTERS:
        f[c] = f['outturn'] - f['day'].map(peaks.get(c, {})).fillna(BACKGROUND_MW).to_numpy(float)
    return f


def case(grid, sets, pairs, unmatched, by_spell, ref_extra=REF_EXTRA, other=None, ref_novel=None):
    """Chronos-2's excess on each novel day = by_spell[its spell]; controls 0. The regression's peak error is
    ref_extra on controls and unmatched days and ref_novel (default ref_extra) on novel days, and Chronos-2's carries
    it too, so only the subtraction leaves Δ."""
    peaks = {REF: {}, PRIMARY: {}}
    novel = set(pairs['novel'])
    for d in novel | set(pairs['control']) | set(unmatched):
        r = ref_novel if (ref_novel is not None and d in novel) else ref_extra
        peaks[REF][d] = r; peaks[PRIMARY][d] = r
    for r in pairs.itertuples(): peaks[PRIMARY][r.novel] = peaks[REF][r.novel] + by_spell[r.cluster]
    for c, v in (other or {}).items():
        peaks[c] = {d: peaks[REF][d] + (v if d in novel else 0.0) for d in peaks[REF]}
    for c in T.FORECASTERS:
        if c not in peaks: peaks[c] = dict(peaks[REF])
    return score(synth_frame(grid, peaks), sets, pairs, unmatched)


def synthetic():
    T.check_files()
    sets, pairs, unmatched, dj = load_sets()
    grid = pd.read_csv(T.FORECASTS, usecols=['day', 'start_utc'])       # the real calendar; no values
    spells = sorted(pairs['cluster'].unique())
    res = dict(script_sha256=sha(os.path.abspath(__file__)), pairs_csv_sha256=sha(PAIRS_CSV), n_pairs=len(pairs),
               spells=[int(k) for k in spells], cases={})
    ok_all = True

    def check(name, cond, **info):
        nonlocal ok_all
        res['cases'][name] = dict(passed=bool(cond), **info); ok_all &= bool(cond)
        print(('PASS ' if cond else 'FAIL ') + name, flush=True)

    # each reading, with a known Δ; constant within and across spells, so the interval is the value itself
    for name, v, want in (('meaningful_400', 400.0, READINGS[0]), ('at_threshold_250', 250.0, READINGS[1]),
                          ('positive_150', 150.0, READINGS[1]), ('smaller_-300', -300.0, READINGS[3])):
        o = case(grid, sets, pairs, unmatched, {k: v for k in spells})
        p = o['forecasters'][PRIMARY]
        check(name, abs(p['delta'] - v) < 1e-6 and o['h5']['reading'] == want and o['headline']['reading'] == want
              and abs(p['ci90'][0] - v) < 1e-6, delta=p['delta'], ci90=p['ci90'], reading=o['h5']['reading'],
              sentence=o['headline']['sentence'])
    # unclear: spells alternate +400 / -400, so draws straddle 0
    alt = {k: (400.0 if i % 2 == 0 else -400.0) for i, k in enumerate(spells)}
    o = case(grid, sets, pairs, unmatched, alt)
    p = o['forecasters'][PRIMARY]
    w = (pairs['cluster'].map(alt)).mean()
    check('unclear_alternating', abs(p['delta'] - w) < 1e-6 and p['ci90'][0] < 0 < p['ci90'][1]
          and o['h5']['reading'] == READINGS[2] and ' to ' in o['headline']['sentence'],
          delta=p['delta'], ci90=p['ci90'], sentence=o['headline']['sentence'])
    # sensitivity thresholds: Δ = 200 is meaningful at 100, positive at 250 and at 500
    o = case(grid, sets, pairs, unmatched, {k: 200.0 for k in spells})
    check('sensitivity_200', o['h5']['reading'] == READINGS[1] and o['h5']['sensitivity'] == {'100': READINGS[0], '500': READINGS[1]},
          h5=o['h5'])
    # spells and leave-one-out: spell k carries 100 x k; Δ is the pair-weighted mean
    sp = {k: 100.0 * k for k in spells}
    o = case(grid, sets, pairs, unmatched, sp, other={'timesfm25_weather_single_day': 50.0})
    p = o['forecasters'][PRIMARY]
    loo_want = {int(k): float(pairs.loc[pairs.cluster != k, 'cluster'].map(sp).mean()) for k in spells}
    check('spells_and_leave_one_out', all(abs(p['spells'][int(k)]['delta'] - sp[k]) < 1e-6 for k in spells)
          and all(abs(p['leave_one_spell_out']['by_spell_left_out'][k] - v) < 1e-6 for k, v in loo_want.items())
          and abs(p['delta'] - pairs['cluster'].map(sp).mean()) < 1e-6
          and abs(o['forecasters']['timesfm25_weather_single_day']['delta'] - 50.0) < 1e-6
          and p['distinct_draws'] <= 35, spells=p['spells'], loo=p['leave_one_spell_out'], distinct=p['distinct_draws'])
    # the subtraction: the regression errs 900 MW more on novel days than on controls, and Chronos-2 shares that
    # error; Δ must still be 200, the part that is Chronos-2's own
    o1 = case(grid, sets, pairs, unmatched, {k: 200.0 for k in spells}, ref_extra=0.0)
    o2 = case(grid, sets, pairs, unmatched, {k: 200.0 for k in spells}, ref_extra=900.0, ref_novel=1800.0)
    check('regression_subtracted', abs(o1['forecasters'][PRIMARY]['delta'] - 200) < 1e-6
          and abs(o2['forecasters'][PRIMARY]['delta'] - 200) < 1e-6
          and abs(o2['unmatched_days'][0][PRIMARY]['excess']) < 1e-6 and abs(o2['unmatched_days'][0][REF]['peak'] - 900) < 1e-6)
    # not assessed below 10 pairs, with no average
    few = pairs.iloc[:MIN_PAIRS - 1]
    o = case(grid, sets, few, unmatched, {k: 400.0 for k in spells})
    check('not_assessed_9_pairs', o['h5']['reading'] == READINGS[4] and o['forecasters'][PRIMARY]['delta'] is None
          and o['headline']['sentence'].startswith('Too few') and f'{MIN_PAIRS - 1} pairs' in o['headline']['sentence'],
          sentence=o['headline']['sentence'])
    # the second sentence names the pairs, spells and unmatched days
    s2 = case(grid, sets, pairs, unmatched, {k: 0.0 for k in spells})['headline']['second']
    check('second_sentence', f'{len(pairs)} pairs' in s2 and f"{pairs['cluster'].nunique()} cold spells" in s2
          and f'{len(unmatched)} novel days' in s2, second=s2)
    # formatting
    check('formatting', iv_text([-120.4, 340.6]) == '−120 to 341' and iv_text([45.0, 580.0]) == '45–580'
          and mw(-0.4) == '0' and mw(1234.5) == '1,234')
    res['passed'] = bool(ok_all)
    json.dump(T.round_floats(res), open(SYNTH_JSON, 'w'), indent=1, default=str)
    print('synthetic: ' + ('PASS' if ok_all else 'FAIL'))
    return ok_all


if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('--synthetic', action='store_true')
    a = ap.parse_args()
    if a.synthetic: sys.exit(0 if synthetic() else 1)
    real()
