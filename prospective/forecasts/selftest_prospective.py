"""
Self-test for the daily prospective forecast (prospective/PLAN.md, Section 8, step 2). Synthetic data and the
stand-in only: no real GB demand is read and no foundation model is run.

  P1  a forecast made from a series cut at 08:30 UK time on D-1 equals the demand study's forecast for D, for the
      regression, the seasonal naive and the model context (four days, including both clock changes)
  P2  no look-ahead: altering every value after the cut-off changes no forecast
  P3  a missing latest half-hour raises the error that makes the script retry
  P4  the script end to end: files written with every half-hour and forecaster; a second run does nothing
  P5  the script refuses to run before 08:35 on D-1, and refuses a real run without the lock
  P6  a push that reaches the remote is confirmed; a push that cannot reach it is reported as failed

Run from the repository root:  python prospective/forecasts/selftest_prospective.py [--models]
  P7  (--models) the three real models run inside the script, on synthetic data only
"""
import os, sys, json, subprocess, tempfile, shutil
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, 'code')); sys.path.insert(0, HERE)
import common as C, inputs as I, baselines as B, models as M, synth
import forecast_daily as F

log = []
def check(ok, msg):
    line = ('PASS  ' if ok else 'FAIL  ') + msg; print(line, flush=True); log.append(line); return bool(ok)


ok = True
s = synth.demand(); hol = synth.holidays(); reg_full = B.Regression(s, hol)
days = [pd.Timestamp(d) for d in ('2025-01-15', '2025-03-30', '2025-07-02', '2025-10-26')]

# P1
same = []
for D in days:
    fc, meta = F.forecast(s, D, hol, stand_in=True)
    h, first = C.horizon(D); n = len(C.target_starts(D))
    ctx = I.context(s, D)[0]
    same.append(np.allclose(fc['regression'], reg_full.forecast(D), rtol=0, atol=1e-6)
                and np.array_equal(fc['naive'], reg_full.seasonal_naive(D))
                and np.array_equal(fc['timesfm25'], M.StandIn().forecast([ctx], h)[0][first:first + n]))
ok &= check(all(same), 'P1 forecasts from a series cut at 08:30 on D-1 equal the study\'s forecasts (4 days, both clock changes)')

# P2
moved = []
for D in days:
    s2 = s.copy(); s2[s2.index + C.HALF_HOUR > C.input_end(D)] += 7000
    a, _ = F.forecast(s, D, hol, True); b, _ = F.forecast(s2, D, hol, True)
    moved.append(all(np.array_equal(a[k], b[k]) for k in a))
ok &= check(all(moved), 'P2 altering every value after the cut-off changes no forecast')

# P3
D = days[0]; s3 = s.copy(); s3[C.input_end(D) - C.HALF_HOUR] = np.nan
try: F.forecast(s3, D, hol, True); raised = False
except ValueError: raised = True
ok &= check(raised, 'P3 a missing latest half-hour raises the error that triggers a retry')

# P4, P5
tmp = tempfile.mkdtemp()
df = pd.DataFrame({'start_utc': s.index, 'settlement_date': '', 'settlement_period': 0, 'mw': s.values})
data = os.path.join(tmp, 'indo.csv'); df.to_csv(data, index=False); out = os.path.join(tmp, 'days')
hols = os.path.join(tmp, 'hol.json'); json.dump(sorted(f'{d:%Y-%m-%d}' for d in hol), open(hols, 'w'))
script = os.path.join(HERE, 'forecast_daily.py')
run = lambda *a: subprocess.run([sys.executable, script, *a, '--holidays-file', hols], capture_output=True, text=True)
r1 = run('--test', '--stand-in', '--data-file', data, '--now', '2025-01-14T09:45', '--out', out)
csv = os.path.join(out, '2025-01-15.csv'); js = os.path.join(out, '2025-01-15.json')
good = r1.returncode == 0 and os.path.exists(csv) and os.path.exists(js)
if good:
    f = pd.read_csv(csv); rec = json.load(open(js))
    good = (len(f) == 48 and all(c in f for c in F.NAMES) and f[F.NAMES].notna().all().all() and rec['test']
            and rec['batch_days'] == 1 and rec['run_started_utc'] and rec['forecasts_sha256'] == C.sha(csv)
            and rec['last_input_halfhour_start_utc'].startswith('2025-01-14 08:00'))
r2 = run('--test', '--stand-in', '--data-file', data, '--now', '2025-01-14T09:45', '--out', out)
ok &= check(good and 'already forecast' in r2.stdout,
            'P4 end to end: 48 half-hours x 5 forecasters written, start time and hashes recorded; a second run does nothing')
r3 = run('--test', '--stand-in', '--data-file', data, '--now', '2025-01-14T08:20', '--out', out)
r4 = subprocess.run([sys.executable, script], capture_output=True, text=True, cwd=ROOT)
ok &= check(r3.returncode != 0 and 'too early' in (r3.stdout + r3.stderr)
            and r4.returncode != 0 and 'refused' in (r4.stdout + r4.stderr),
            'P5 refuses to run before 08:35 on D-1, and refuses a real run without the lock')

# P6
bare = os.path.join(tmp, 'remote.git'); clone = os.path.join(tmp, 'clone')
g = lambda *a, cwd=None: subprocess.run(['git', *a], cwd=cwd, capture_output=True, text=True)
g('init', '-q', '--bare', '-b', 'main', bare); g('clone', '-q', bare, clone)
for k, v in (('user.name', 'test'), ('user.email', 'test@example.com')): g('config', k, v, cwd=clone)
open(os.path.join(clone, 'a.txt'), 'w').write('a'); g('add', 'a.txt', cwd=clone); g('commit', '-qm', 'a', cwd=clone)
g('push', '-q', 'origin', 'main', cwd=clone)
F.ROOT = clone; F.time.sleep = lambda s: None
open(os.path.join(clone, 'b.txt'), 'w').write('b'); good_push = F.push(['b.txt'], pd.Timestamp('2025-01-15'))
g('remote', 'set-url', 'origin', os.path.join(tmp, 'missing.git'), cwd=clone)
open(os.path.join(clone, 'c.txt'), 'w').write('c'); bad_push = F.push(['c.txt'], pd.Timestamp('2025-01-16'))
ok &= check(good_push and not bad_push, 'P6 a push that reaches the remote is confirmed; one that cannot is reported as failed')
# P7 (--models): the real models inside the script, on synthetic data only
if '--models' in sys.argv:
    out7 = os.path.join(tmp, 'days7')
    r7 = run('--test', '--data-file', data, '--now', '2025-01-14T09:45', '--out', out7)
    f7 = os.path.join(out7, '2025-01-15.csv'); good7 = r7.returncode == 0 and os.path.exists(f7)
    if good7:
        f = pd.read_csv(f7); rec = json.load(open(os.path.join(out7, '2025-01-15.json')))
        good7 = len(f) == 48 and f[F.NAMES].notna().all().all() and not rec['stand_in']
    else:
        print(r7.stdout[-2000:], r7.stderr[-2000:])
    ok &= check(good7, 'P7 the three real models run inside the script (synthetic data): 48 finite half-hours each')
shutil.rmtree(tmp)

line = 'OVERALL: ' + ('PASS' if ok else 'FAIL'); print(line); log.append(line)
open(os.path.join(HERE, 'selftest_prospective.txt'), 'w').write('\n'.join(log) + '\n')
