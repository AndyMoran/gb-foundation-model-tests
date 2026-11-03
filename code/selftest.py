"""
Self-test before freezing (plan Section 11, step 2). Synthetic data only: no real GB demand is read, and no model
forecasts real GB demand.

  A  time rules: horizons of 77, 79 and 81 steps around clock changes; cut-offs at 08:30 and 09:30 UK time
  B  no look-ahead, shown by changing the future: every value after 08:30 on D-1 is altered, and every NESO
     publication after 09:30; the regression, seasonal naive, model contexts and NESO forecast must not move
  C  NESO blanks are replaced by the most recent earlier publication; the 11:45 revision is never used
  D  the regression matches an independent implementation on six days, including both clock-change days
  E  statistics: a planted forecaster 15% better than the regression is detected; one with no gain is not
  F  a gap in the data excludes the target day and every day whose context contains it, with reasons
  G  (--models) each foundation model on synthetic contexts: horizon exact, finite, repeatable, responsive,
     batch-independent (a day forecast alone equals the same day forecast in a batch), and an L1 pilot of the
     300 MW perturbation; prints each weights file's SHA-256 for the lock file

Usage: python selftest.py            (A-F, no models)
       python selftest.py --models   (A-G; downloads the pinned weights)
"""
import os, sys
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import common as C, inputs as I, baselines as B, stats as S, models as M, synth

log = []
def check(ok, msg):
    line = ('PASS  ' if ok else 'FAIL  ') + msg; print(line, flush=True); log.append(line); return bool(ok)


def main(with_models):
    ok = True
    s = synth.demand(); pubs = synth.neso_publications(s); hol = synth.holidays()
    reg = B.Regression(s, hol)

    # A
    h = {d: C.horizon(d)[0] for d in ('2024-03-31', '2024-06-12', '2024-10-27')}
    ok &= check(h == {'2024-03-31': 77, '2024-06-12': 79, '2024-10-27': 81}, f'A horizons around clock changes: {h}')
    ok &= check(C.input_end('2024-06-12').tz_convert(C.UK).strftime('%m-%d %H:%M') == '06-11 08:30'
                and C.issue_time('2024-01-17').tz_convert(C.UK).strftime('%m-%d %H:%M') == '01-16 09:30',
                'A cut-offs: inputs end 08:30 and NESO at 09:30, UK local time, on D-1')

    # B
    days = [pd.Timestamp(d) for d in ('2024-01-17', '2024-03-31', '2024-10-27', '2025-07-16')]
    moved = []
    for D in days:
        s2 = s.copy(); s2[s2.index + C.HALF_HOUR > C.input_end(D)] += 5000
        r2 = B.Regression(s2, hol)
        p2 = pubs.copy(); p2.loc[p2.publish_utc > C.issue_time(D), 'mw'] += 5000
        same = (np.allclose(r2.forecast(D), reg.forecast(D)) and np.allclose(r2.seasonal_naive(D), reg.seasonal_naive(D))
                and np.array_equal(I.context(s2, D)[0], I.context(s, D)[0])
                and np.allclose(I.neso_forecast(p2, D)[0], I.neso_forecast(pubs, D)[0]))
        moved.append(same)
    ok &= check(all(moved), 'B changing everything after the cut-offs moves no forecaster (4 days, incl. both clock changes)')

    # C
    blanks = pubs[pubs.mw.isna()]
    D = blanks.start_utc.iloc[0].tz_convert(C.UK).normalize().tz_localize(None)
    vals, _ = I.neso_forecast(pubs, D)
    t = blanks.start_utc.iloc[0]; k = list(C.target_starts(D)).index(t)
    earlier = pubs[(pubs.start_utc == t) & (pubs.publish_utc < blanks.publish_utc.iloc[0])].mw.dropna().iloc[-1]
    all_d = [pd.Timestamp('2024-01-01') + pd.Timedelta(days=i) for i in range(0, 1000, 37)]
    poison = any(np.abs(I.neso_forecast(pubs, d)[0] - s.reindex(C.target_starts(d)).values).max() > 5000 for d in all_d)
    ok &= check(np.isclose(vals[k], earlier) and not poison, 'C a blank takes the earlier publication; the 11:45 revision is never used')

    # D
    diffs = []
    for d in ('2024-01-17', '2024-03-31', '2024-10-27', '2024-10-28', '2025-12-25', '2026-10-31'):
        diffs.append(np.abs(B.regression_independent(s, d, hol) - reg.forecast(d)).max())
    ok &= check(max(diffs) < 0.1, f'D regression matches the independent implementation (max difference {max(diffs):.1e} MW)')

    # E
    full = C.days(); rng = np.random.default_rng(5)
    yy = {D: I.targets(s, D)[0] for D in full}; rf = {D: reg.forecast(D) for D in full}
    mr = pd.Series({D: S.daily_mae(yy[D], rf[D]) for D in full})
    def planted(ratio):
        f = {D: yy[D] + (rf[D] - yy[D]) * ratio for D in full}
        return pd.Series({D: S.daily_mae(yy[D], f[D]) for D in full})
    e85 = S.compare(planted(0.85), mr, 500, 7, 1, thetas=(1.0, 0.9)); e100 = S.compare(planted(1.0), mr, 500, 7, 1, thetas=(1.0, 0.9))
    hb = S.holm({'a1': e85['p_one_sided']['1.00'], 'a9': e85['p_one_sided']['0.90'],
                 'b1': e100['p_one_sided']['1.00'], 'b9': e100['p_one_sided']['0.90']})
    ok &= check(abs(e85['ratio'] - 0.85) < 0.005 and hb['a1']['rejected'] and hb['a9']['rejected'] and not hb['b1']['rejected'],
                f"E planted 15% gain detected (ratio {e85['ratio']:.3f}); no gain not detected (ratio {e100['ratio']:.3f})")

    # F
    s3 = synth.demand(gaps=[(C.local('2025-02-03', '10:00'), C.local('2025-02-03', '11:00'))])
    import run as R
    rec, excl = R.build_days(s3, pubs, B.Regression(s3, hol), pd.date_range('2025-02-01', '2025-02-08'))
    bad = sorted({e['day'] for e in excl})
    ok &= check(bad == ['2025-02-03', '2025-02-05', '2025-02-06', '2025-02-07', '2025-02-08'] and len(rec) == 3,
                f'F a gap on 3 February 10:00-11:00 excludes 3 February (outturn) and, from 5 February, every day whose '
                f'8-week context contains it; 4 February (context ends 08:30 on 3 February) is kept: {bad}')

    # G
    if with_models:
        from huggingface_hub import hf_hub_download
        D = pd.Timestamp('2025-01-15'); ctx = I.context(s, D)[0]
        ds = [pd.Timestamp('2025-01-15') + pd.Timedelta(days=i) for i in range(6)]
        batch = [I.context(s, d)[0] for d in ds]
        for name in C.MODELS:
            m = M.get(name)
            shapes = all(m.forecast([ctx], hh).shape == (1, hh) for hh in (77, 79, 81))
            f1 = m.forecast([ctx], 79); f2 = m.forecast([ctx], 79)
            c2 = ctx.copy(); c2[-1] += 1000; f3 = m.forecast([c2], 79)
            fb = m.forecast(batch, 79)
            indep = np.allclose(fb[0], m.forecast([batch[0]], 79)[0], atol=1e-3)
            ok &= check(shapes and np.isfinite(f1).all(), f'G {name}: exact horizons 77/79/81, finite')
            ok &= check(np.array_equal(f1, f2), f'G {name}: repeat call identical')
            ok &= check(np.abs(f3 - f1).max() > 1e-6, f'G {name}: responsive to the last half-hour')
            ok &= check(indep, f'G {name}: a day forecast alone equals the same day in a batch (no cross-day pooling)')
            # L1 pilot on synthetic data: degradation of the model and of the regression under 300 MW noise
            pdays = [pd.Timestamp('2025-01-01') + pd.Timedelta(days=7 * i) for i in range(12)]
            y = [I.targets(s, d)[0] for d in pdays]; first = [C.horizon(d)[1] for d in pdays]
            base = np.mean([S.daily_mae(yv, f[fi:fi + len(yv)]) for yv, f, fi in
                            zip(y, m.forecast([I.context(s, d)[0] for d in pdays], 79), first)])
            noisy = s + np.random.default_rng(1).normal(0, C.L1_SD_MW, len(s))
            pert = np.mean([S.daily_mae(yv, f[fi:fi + len(yv)]) for yv, f, fi in
                            zip(y, m.forecast([I.context(noisy, d)[0] for d in pdays], 79), first)])
            rn = B.Regression(noisy, hol)
            rb = np.mean([S.daily_mae(yv, reg.forecast(d)) for yv, d in zip(y, pdays)])
            rp = np.mean([S.daily_mae(yv, rn.forecast(d)) for yv, d in zip(y, pdays)])
            log.append(f'INFO  {name}: L1 pilot, model ratio {pert / base:.3f}, regression ratio {rp / rb:.3f}')
            print(log[-1])
            repo, rev = M.REVISIONS[name]
            log.append(f'INFO  {name}: weights {repo}@{rev[:8]} sha256 {C.sha(hf_hub_download(repo, "model.safetensors", revision=rev))}')
            print(log[-1])
        log.append('INFO  versions ' + str(M.versions())); print(log[-1])
    line = 'OVERALL: ' + ('PASS' if ok else 'FAIL'); print(line); log.append(line)
    open(os.path.join(HERE, 'selftest_models.txt' if with_models else 'selftest.txt'), 'w').write('\n'.join(log) + '\n')


if __name__ == '__main__':
    main('--models' in sys.argv)
