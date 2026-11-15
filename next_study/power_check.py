"""
Power check for the next study: can a live window this winter decide whether a zero-shot foundation model beats the
trained baselines? Specified and committed on 15 November 2026 before it was run. It decides timing only.

The next study (to be briefed): Chronos-2 (and possibly Timestral) given the same weather and calendar as two trained
baselines, the weather regression and LightGBM, scored on a live window that is confirmatory; any backtest is
descriptive.

Confirmatory claim, per comparison: the foundation model's ratio of mean daily error to the baseline's is below 1,
one-sided. Two comparisons (Chronos-2 against LightGBM, and against the regression), each at alpha = 0.025.
Reported alongside, as a descriptive, decision-relevant result: whether the 10% bar is shown, meaning the same
one-sided test at 0.025 against a ratio of 0.9. A model can be credibly better without showing the 10% bar; that is a
positive result that misses the threshold set in the first study as worth switching for, not a failed test.

Method (weather_study/power.py's, applied to a paired comparison). The baseline's real half-hourly errors are those of
the weather regression in the scored weather backtest (weather_study/results/forecasts.csv, `regression_weather`).
The foundation model's arm is simulated from them: a share c of each half-hour's error is the baseline's real error,
the rest is the baseline's error on another day at least 30 days away (a circular shift, keeping weekly dependence),
scaled so the true ratio over the window is 1 - edge. Each replication draws its days as a study would see them
(blocks of 7), then tests with a moving-block bootstrap (blocks of 7, 1,000 draws); p = share of bootstrap ratios at
or above the null. 1,000 replications per cell; the four cells the decision rule reads are rerun with 2,000.

Grid:
  true edge   5%, 7.5%, 10%, 12.5%  (ratio 0.95, 0.925, 0.90, 0.875)
  c           measured: the half-hourly error correlation between Chronos-2 with calendar and weather (E5 arm A,
              weather_study/results/calendar_forecasts.csv, `chronos2_A`) and the weather regression, on the same
              winter days; both had the same weather and calendar, so this is the matched-input case.
              0.7: a pessimistic bound for LightGBM, on the assumption that a tree model's errors are less correlated
              with Chronos-2's than a linear model's. If LightGBM's errors are at least as correlated with
              Chronos-2's as the regression's are, power exceeds the 0.7 case.
  windows     winter, 1 December to 31 March: 100 and 120 days (120 is the most a December-to-March window holds);
              150 days, 1 November to 31 March, for comparison (a November start changes the season mix);
              summer, 180 days, April to September, for the rolling-from-spring option.
              Winter windows are drawn from the backtest's two Decembers-to-March (2024-25, 2025-26) in turn;
              summer windows from its three summers (2024, 2025, 2026) in turn.

Decision rule, fixed before running (it reads power for the claim "ratio below 1", at alpha 0.025):
  This winter:               power >= 80% at a true 10% edge, c = 0.7, 120-day winter window.
  This winter, with caveat:  power >= 80% at a true 10% edge only at the measured c, 120-day window; the brief then
                             states that the study is powered only if LightGBM's errors are about as correlated
                             with Chronos-2's as the regression's are.
  Next winter:               otherwise.
This rule settles timing only. The design gate is separate: Timestral's calendar encoding, LightGBM's tuning, the cost
metrics, the confirmatory and descriptive split, and the 10% rationale must all be resolved before any freeze.

Inputs (sha256): weather_study/results/forecasts.csv b5f16561dcf1a26f8d7910bcca95cd137f677760c6f80153349034d4a85f7328
                 weather_study/results/calendar_forecasts.csv 976e27ef28d0eef1ddf351c6557af9f771c308b94f389fe0f06b84ec86c8e2fe

Usage: python next_study/power_check.py   ->  next_study/power_check.json, next_study/power_check.md
"""
import hashlib, json, os, sys
import numpy as np, pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'weather_study')); import power as P
FC = os.path.join(ROOT, 'weather_study', 'results', 'forecasts.csv')
CAL = os.path.join(ROOT, 'weather_study', 'results', 'calendar_forecasts.csv')
SHA = {FC: 'b5f16561dcf1a26f8d7910bcca95cd137f677760c6f80153349034d4a85f7328',
       CAL: '976e27ef28d0eef1ddf351c6557af9f771c308b94f389fe0f06b84ec86c8e2fe'}
EDGES = (0.05, 0.075, 0.10, 0.125)
ALPHA, BAR, REPS, REPS_DECISION, SEED = 0.025, 0.90, 1000, 2000, 20261115


def sha(p):
    h = hashlib.sha256(); h.update(open(p, 'rb').read()); return h.hexdigest()


def windows(days):
    d = pd.to_datetime(pd.Series(days)).dt.date.astype(str).tolist()
    win = lambda a, b: [x for x in d if a <= x <= b]
    w = [win('2024-12-01', '2025-03-31'), win('2025-12-01', '2026-03-31')]
    n = [win('2024-11-01', '2025-03-31'), win('2025-11-01', '2026-03-31')]
    s = [win('2024-04-01', '2024-09-30'), win('2025-04-01', '2025-09-30'), win('2026-04-01', '2026-09-30')]
    return {'winter 100 days (Dec-Mar)': [x[:100] for x in w], 'winter 120 days (Dec-Mar)': [x[:120] for x in w],
            'winter 150 days (Nov-Mar)': [x[:150] for x in n], 'summer 180 days (Apr-Sep)': [x[:180] for x in s]}


def cell(E_sets, c, edge, reps, rng):
    hits = dict(below_1=0, below_bar=0)
    for rep in range(reps):
        E = E_sets[rep % len(E_sets)]; n = len(E)
        raw = P.simulate(E, rng, c)
        m0 = np.array([np.abs(e).mean() for e in E])
        k = (1 - edge) * m0.mean() / np.mean([np.abs(x).mean() for x in raw])
        m1 = np.array([np.abs(k * x).mean() for x in raw])
        idx = P.S.block_indices(n, rng, P.BLOCK); a, b = m1[idx], m0[idx]
        bi = P.boot_idx(n, rng); bs = a[bi].mean(1) / b[bi].mean(1)
        hits['below_1'] += (bs >= 1.0).mean() < ALPHA
        hits['below_bar'] += (bs >= BAR).mean() < ALPHA
    return {k: v / reps for k, v in hits.items()}


def main():
    for p, h in SHA.items():
        if sha(p) != h: sys.exit(f'{p} differs from the hash in the specification')
    f = pd.read_csv(FC); c = pd.read_csv(CAL)
    assert (f['day'].to_numpy() == c['day'].to_numpy()).all() and (f['start_utc'].to_numpy() == c['start_utc'].to_numpy()).all()
    f['chronos2_A'] = c['chronos2_A'].to_numpy()
    days = list(dict.fromkeys(f['day']))
    W = windows(days)
    winter_days = set(sum(W['winter 120 days (Dec-Mar)'], []))
    g = f[f['day'].isin(winter_days)]
    c_meas = float(np.corrcoef(g['outturn'] - g['chronos2_A'], g['outturn'] - g['regression_weather'])[0, 1])
    E_by = {w: [[(f[f['day'] == d]['outturn'] - f[f['day'] == d]['regression_weather']).to_numpy() for d in ds] for ds in sets]
            for w, sets in W.items()}
    rng = np.random.default_rng(SEED)
    out = dict(note='specified and committed 15 November 2026 before running', alpha=ALPHA, bar=BAR, reps=REPS,
               c_measured=round(c_meas, 4), c_values=[round(c_meas, 4), 0.7], inputs=SHA, cells={})
    for w in W:
        for cv in (round(c_meas, 4), 0.7):
            for e in EDGES:
                decision = w.startswith('winter 120') and e == 0.10
                r = cell(E_by[w], cv, e, REPS_DECISION if decision else REPS, rng)
                out['cells'][f'{w}|c={cv}|edge={e}'] = dict(**r, reps=REPS_DECISION if decision else REPS)
                print(f'{w:27s} c={cv:<6} edge {e:5.3f}: credibly better {r["below_1"]:.3f}; shows 10% bar {r["below_bar"]:.3f}', flush=True)
    d_meas = out['cells'][f'winter 120 days (Dec-Mar)|c={round(c_meas, 4)}|edge=0.1']['below_1']
    d_pess = out['cells']['winter 120 days (Dec-Mar)|c=0.7|edge=0.1']['below_1']
    out['decision'] = ('this winter' if d_pess >= 0.8 else 'this winter, with caveat' if d_meas >= 0.8 else 'next winter')
    json.dump(out, open(os.path.join(ROOT, 'next_study', 'power_check.json'), 'w'), indent=1)
    md = ['# Power check for the next study', '', f"Measured c (Chronos-2 with calendar and weather against the regression, winter days): {c_meas:.3f}.",
          f"Decision, by the rule fixed in advance: **{out['decision']}** (power at a true 10% edge, 120-day winter window: "
          f"{d_pess:.1%} at c = 0.7, {d_meas:.1%} at the measured c).", '',
          '| Window | c | True edge | Credibly better (ratio < 1) | Shows the 10% bar |', '| --- | --- | --- | --- | --- |']
    for k, v in out['cells'].items():
        w, cv, e = k.split('|')
        md.append(f"| {w} | {cv[2:]} | {float(e[5:]):.1%} | {v['below_1']:.1%} | {v['below_bar']:.1%} |")
    open(os.path.join(ROOT, 'next_study', 'power_check.md'), 'w').write('\n'.join(md) + '\n'); print('\n'.join(md[:4]))


if __name__ == '__main__':
    main()
