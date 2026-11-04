"""
Daily prospective forecast (prospective/PLAN.md, Section 2).

Run on D-1, after 08:30 UK time: forecasts every half-hour of tomorrow (D) with the three models, the weekly-lag
regression and the seasonal naive, using the demand study's locked code, settings and weights, and INDO cut at 08:30
on D-1. Writes days/D.csv and days/D.json, appends manifest.csv, commits, pushes, and confirms the push reached GitHub.

Real use (from the repository root, in the model environment; the scheduled task does this at 09:45):
    python prospective/forecasts/forecast_daily.py

Tests (never push; outputs are marked as tests):
    python prospective/forecasts/forecast_daily.py --test --stand-in --data-file F --now 2025-01-14T09:45 --out DIR
    python prospective/forecasts/forecast_daily.py --test --no-push        (real data and models, no push)

A target day counts only if its files reach GitHub before 00:00 UK time on D (plan Section 3). Retries every 15
minutes until 11:30 UK time if the latest half-hours have not arrived; a manual run later the same day also counts if
its push precedes D. "Contains BMRS data © Elexon Limited copyright and database right 2026."
"""
import argparse, datetime as dt, json, os, subprocess, sys, time
import numpy as np, pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(ROOT, 'code'))
import common as C, inputs as I, baselines as B, models as M

LOCK = os.path.join(ROOT, 'prospective', 'PROSPECTIVE_LOCK.json')
TAG = 'prospective-plan'
CACHE = os.path.join(C.DATA, 'prospective_indo.csv')       # data/ is not committed
HOLIDAYS = os.path.join(C.DATA, 'bank_holidays_ew.json')
RETRY_EVERY, LAST_RETRY = 900, '11:30'
NAMES = ['regression', 'naive'] + list(C.MODELS)
utc = lambda: dt.datetime.now(dt.timezone.utc)
stamp = lambda: utc().isoformat(timespec='seconds')


def say(msg):
    print(msg, flush=True)


def git(*a):
    r = subprocess.run(['git', '-C', ROOT, *a], capture_output=True, text=True)
    return r.returncode, (r.stdout + r.stderr).strip()


def check_lock():
    """Refuse to run unless the lock exists, the tag is on GitHub, and every locked file and weights file matches."""
    if not os.path.exists(LOCK): sys.exit('refused: prospective/PROSPECTIVE_LOCK.json not found (plan not frozen)')
    lock = json.load(open(LOCK))
    code, out = git('ls-remote', '--tags', 'origin', TAG)
    if code or TAG not in out: sys.exit(f'refused: tag {TAG} is not on GitHub ({out or "no output"})')
    bad = [f for f, h in lock['files_sha256'].items() if C.sha(os.path.join(ROOT, f)) != h]
    if bad: sys.exit('refused: changed since the prospective freeze: ' + ', '.join(bad))
    from huggingface_hub import hf_hub_download
    for name, (repo, rev) in M.REVISIONS.items():
        if C.sha(hf_hub_download(repo, 'model.safetensors', revision=rev)) != lock['weights_sha256'][name]:
            sys.exit(f'refused: {name} weights differ from the lock')
    return lock


def load_series(data_file, today):
    """INDO as a regular UTC series. Real use: the study's download, extended by fetching the last 14 days each run;
    a value already cached is never overwritten (what was known then stays), and any disagreement is counted."""
    if data_file:
        return I.load_indo(data_file)[0], 0
    import fetch                                             # the study's locked downloader
    base = CACHE if os.path.exists(CACHE) else os.path.join(C.DATA, 'indo.csv')
    old = pd.read_csv(base); old['start_utc'] = pd.to_datetime(old['start_utc'], utc=True)
    a = (today - pd.Timedelta(days=14)).strftime('%Y-%m-%d'); b = today.strftime('%Y-%m-%d')
    new = fetch.indo_chunk(a, b)
    both = old.merge(new, on='start_utc', how='inner', suffixes=('', '_new'))
    revised = int(((both.mw - both.mw_new).abs() > 0.5).sum())
    merged = pd.concat([old, new[~new.start_utc.isin(old.start_utc)]]).sort_values('start_utc')
    merged.to_csv(CACHE, index=False)
    return I.load_indo(CACHE)[0], revised


def forecast(series, D, hol, stand_in):
    """Every forecaster for D, from a series cut at 08:30 UK time on D-1. Raises ValueError if the context is
    incomplete (the caller retries)."""
    cut = C.input_end(D)
    s = series[series.index + C.HALF_HOUR <= cut]
    ctx, cidx, filled = I.context(s, D)
    reg = B.Regression(s, hol)
    h, first = C.horizon(D); n = len(C.target_starts(D))
    out = {'regression': reg.forecast(D), 'naive': reg.seasonal_naive(D)}
    for name in C.MODELS:
        m = M.get('stand-in' if stand_in else name)
        out[name] = m.forecast([ctx], h)[0][first:first + n]
    for k, v in out.items():
        if len(v) != n or not np.isfinite(v).all(): raise RuntimeError(f'{k}: forecast not finite or wrong length')
    meta = dict(last_input_halfhour_start_utc=str(cidx[-1]), input_cut_utc=str(cut),
                input_sha256=__import__('hashlib').sha256(s.dropna().to_csv().encode()).hexdigest(),
                context_fills_utc=[str(t) for t in filled])
    return out, meta


def push(paths, D):
    """Commit, push, and confirm GitHub has the commit. Prints git's own messages on failure."""
    git('add', *paths)
    code, out = git('commit', '-m', f'Prospective forecast for {D:%Y-%m-%d}', '--', *paths)
    if code: say(f'commit failed: {out}'); return False
    for attempt in range(3):
        c1, o1 = git('pull', '--rebase', '-q')
        c2, o2 = git('push', '-q')
        c3, _ = git('fetch', '-q', 'origin')
        c4, _ = git('merge-base', '--is-ancestor', 'HEAD', 'origin/main')
        if c4 == 0:
            say(f'pushed {git("rev-parse", "--short", "HEAD")[1]} at {stamp()}; GitHub has it'); return True
        say(f'push attempt {attempt + 1} failed: {o1} {o2}'.strip()); time.sleep(60)
    return False


def main():
    a = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    a.add_argument('--test', action='store_true', help='test run: no lock check, never pushes, output marked test')
    a.add_argument('--stand-in', action='store_true', help='with --test: the stand-in in every model slot')
    a.add_argument('--no-push', action='store_true', help='with --test: real models, no push')
    a.add_argument('--data-file', help='with --test: INDO CSV to use instead of fetching')
    a.add_argument('--now', help='with --test: pretend the UK local time is this (YYYY-MM-DDTHH:MM)')
    a.add_argument('--holidays-file', help='with --test: bank-holiday JSON to use instead of data/bank_holidays_ew.json')
    a.add_argument('--out', default=os.path.join(HERE, 'days'), help='output folder')
    args = a.parse_args()
    if (args.stand_in or args.no_push or args.data_file or args.now or args.holidays_file) and not args.test:
        sys.exit('--stand-in, --no-push, --data-file, --now and --holidays-file need --test')
    started = stamp(); say(f'=== start {started}{" (TEST)" if args.test else ""}')
    now = pd.Timestamp(args.now, tz=C.UK) if args.now else pd.Timestamp.now(tz=C.UK)
    today = now.normalize().tz_localize(None); D = today + pd.Timedelta(days=1)
    if now < C.input_end(D).tz_convert(C.UK) + pd.Timedelta(minutes=5):
        sys.exit(f'refused: too early; inputs to 08:30 UK on {today:%Y-%m-%d} may not have arrived')
    os.makedirs(args.out, exist_ok=True)
    f_csv, f_json = (os.path.join(args.out, f'{D:%Y-%m-%d}.{x}') for x in ('csv', 'json'))
    if os.path.exists(f_csv): say(f'{D:%Y-%m-%d}: already forecast'); say(f'=== end {stamp()}: ok'); return
    lock = None if args.test else check_lock()
    hol = {pd.Timestamp(d) for d in json.load(open(args.holidays_file or HOLIDAYS))}
    while True:
        try:
            series, revised = load_series(args.data_file, today)
            fc, meta = forecast(series, D, hol, args.stand_in); break
        except ValueError as e:
            if args.test or pd.Timestamp.now(tz=C.UK) >= C.local(today, LAST_RETRY).tz_convert(C.UK):
                say(f'{D:%Y-%m-%d}: no forecast: {e}'); say(f'=== end {stamp()}: FAILED'); sys.exit(1)
            say(f'inputs incomplete at {stamp()} ({e}); retrying in 15 minutes'); time.sleep(RETRY_EVERY)
    idx = C.target_starts(D)
    pd.DataFrame({'start_utc': [t.isoformat() for t in idx], 'settlement_period': range(1, len(idx) + 1),
                  **{k: fc[k] for k in NAMES}}).to_csv(f_csv, index=False)
    rec = dict(target_day=f'{D:%Y-%m-%d}', issue_time_utc=str(C.issue_time(D)), run_started_utc=started,
               forecast_written_utc=stamp(), test=args.test, stand_in=args.stand_in, batch_days=1,
               indo_cached_values_disagreeing_with_fetch=revised, **meta,
               forecasts_sha256=C.sha(f_csv), versions=M.versions(), settings=M.SETTINGS, revisions=M.REVISIONS,
               lock_sha256=C.sha(LOCK) if lock else None,
               code_sha256={f: C.sha(os.path.join(ROOT, 'code', f)) for f in ('common.py', 'inputs.py', 'baselines.py', 'models.py', 'fetch.py')},
               script_sha256=C.sha(os.path.abspath(__file__)))
    json.dump(rec, open(f_json, 'w'), indent=1, default=str)
    man = os.path.join(args.out, 'manifest.csv'); new = not os.path.exists(man)
    with open(man, 'a') as m:
        if new: m.write('target_day,run_started_utc,forecast_written_utc,forecasts_sha256\n')
        m.write(f'{rec["target_day"]},{started},{rec["forecast_written_utc"]},{rec["forecasts_sha256"]}\n')
    say(f'{D:%Y-%m-%d}: forecasts written ({len(idx)} half-hours); sha256 {rec["forecasts_sha256"][:12]}')
    if args.test: say(f'=== end {stamp()}: ok (test; not pushed)'); return
    ok = push([os.path.relpath(p, ROOT) for p in (f_csv, f_json, man)], D)
    say(f'=== end {stamp()}: {"ok" if ok else "PUSH FAILED: the day will not count unless pushed before 00:00 UK on D"}')
    if not ok: sys.exit(2)


if __name__ == '__main__':
    main()
