"""
LightGBM variants, step 1 (lgbm_variants/PLAN.md §4 and §9, frozen at tag lgbm-variants-plan): the demand history V5
needs, and a manifest for V5's data. Committed before it runs; the manifest is committed after; the data never are.

V5 trains on D-731 to D-2, which for the first backtest day (16 March 2024) reaches back to 16 March 2022. The demand
held (data/indo.csv) starts on 1 December 2022.

    python lgbm_variants/fetch_v5.py indo       fetch INDO for 1 March to 31 December 2022 with code/fetch.py's own
                                                request (indo_chunk), into data/indo_2022.csv. Checks: every half-hour
                                                of December 2022, which both files hold, must agree exactly with the
                                                frozen data/indo.csv (checked against data/fetch_manifest.json); gaps
                                                from 15 March to 30 November 2022 are listed, with the days each would
                                                remove from training under the existing rule (complete days only).
    python lgbm_variants/fetch_v5.py manifest   after gb-weather-private/weather/v5_era5.py build has run: re-hash
                                                data/indo_2022.csv and the ERA5 output, check the ERA5 build passed its
                                                overlap check, and write lgbm_variants/v5_data_manifest.json.

"Contains BMRS data © Elexon Limited copyright and database right 2026."
"""
import datetime as dt, json, os, subprocess, sys
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, 'code'))
import common as C, fetch as F, inputs as I                  # noqa: E402

FROM, TO = '2022-03-01', '2022-12-31'
NEEDED_FROM, NEEDED_TO = '2022-03-15', '2022-11-30'          # local target days before indo.csv begins, with a margin
OUT = os.path.join(ROOT, 'data', 'indo_2022.csv')
FROZEN = os.path.join(ROOT, 'data', 'indo.csv')
INDO_LOG = os.path.join(HERE, 'v5_indo_check.json')
MANIFEST = os.path.join(HERE, 'v5_data_manifest.json')
ERA5_DIR = os.path.expanduser('~/gb-weather-data/backtest')
ERA5_OUT, ERA5_JSON = (os.path.join(ERA5_DIR, f) for f in ('era5_halfhourly_v5_2022-03-15_2023-03-14.csv.gz', 'era5_v5_build.json'))


def git(*a):
    return subprocess.run(['git', '-C', ROOT, *a], capture_output=True, text=True, check=True).stdout.strip()


def indo():
    if git('status', '--porcelain', '--', 'lgbm_variants/fetch_v5.py', 'code'):
        sys.exit('Refused: commit lgbm_variants/fetch_v5.py and code/ first (committed before it runs).')
    man = json.load(open(os.path.join(ROOT, 'data', 'fetch_manifest.json')))['files']
    if C.sha(FROZEN) != man['indo.csv']['sha256']: sys.exit('Refused: data/indo.csv differs from data/fetch_manifest.json')
    parts = []
    for a in pd.date_range(FROM, TO, freq='7D'):
        b = min(a + pd.Timedelta(days=6), pd.Timestamp(TO))
        parts.append(F.indo_chunk(f'{a:%Y-%m-%d}', f'{b:%Y-%m-%d}')); print(f'  INDO {a:%Y-%m-%d}', flush=True)
    new = pd.concat(parts).drop_duplicates('start_utc').sort_values('start_utc')
    new.to_csv(OUT, index=False)
    # check 1: December 2022, held by both files, must agree exactly
    s_new, _ = I.load_indo(OUT); s_old, _ = I.load_indo(FROZEN)
    dec = s_old.index[(s_old.index >= C.local(pd.Timestamp('2022-12-01'), '00:00')) &
                      (s_old.index < C.local(pd.Timestamp('2023-01-01'), '00:00'))]
    a, b = s_new.reindex(dec), s_old.reindex(dec)
    both = a.notna() & b.notna()
    overlap = dict(half_hours=len(dec), both_present=int(both.sum()), only_new=int((a.notna() & b.isna()).sum()),
                   only_frozen=int((a.isna() & b.notna()).sum()), max_abs_diff_mw=float((a[both] - b[both]).abs().max()),
                   passed=bool(both.sum() == b.notna().sum() and (a[both] == b[both]).all()))
    # check 2: gaps before indo.csv begins, and the training days each would remove (complete days only)
    days = pd.date_range(NEEDED_FROM, NEEDED_TO)
    incomplete = []
    for d in days:
        st = C.target_starts(d)
        if s_new.reindex(st).isna().any(): incomplete.append(f'{d:%Y-%m-%d}')
    n_missing = int(sum(s_new.reindex(C.target_starts(d)).isna().sum() for d in days))
    res = dict(file='data/indo_2022.csv', sha256=C.sha(OUT), rows=int(len(new)),
               fetched_utc=dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds'),
               first=f'{new.start_utc.min()}', last=f'{new.start_utc.max()}', december_overlap=overlap,
               needed_days=f'{NEEDED_FROM} .. {NEEDED_TO}', missing_half_hours=n_missing,
               incomplete_days=incomplete, public_commit=git('rev-parse', 'HEAD'),
               script_sha256=C.sha(os.path.abspath(__file__)))
    json.dump(res, open(INDO_LOG, 'w'), indent=1)
    print(json.dumps({k: res[k] for k in ('rows', 'first', 'last', 'december_overlap', 'missing_half_hours', 'incomplete_days')}, indent=1))
    if not overlap['passed']: sys.exit('FAIL: December 2022 differs from data/indo.csv; do not use data/indo_2022.csv')
    print('INDO: PASS')


def manifest():
    ind = json.load(open(INDO_LOG))
    if C.sha(OUT) != ind['sha256']: sys.exit('Refused: data/indo_2022.csv changed since it was checked')
    if not ind['december_overlap']['passed']: sys.exit('Refused: the INDO overlap check failed')
    b = json.load(open(ERA5_JSON))
    if not b['overlap_check']['passed']: sys.exit('Refused: the ERA5 overlap check failed')
    if C.sha(ERA5_OUT) != b['output_sha256']: sys.exit('Refused: the ERA5 output differs from its build record')
    arco = sorted(d for d, r in b['era5_days'].items() if r.get('copy') != 'cds')
    m = dict(note='V5 data (lgbm_variants/PLAN.md §9 step 1); the data are not committed',
             indo=dict(file=ind['file'], sha256=ind['sha256'], rows=ind['rows'], december_overlap=ind['december_overlap'],
                       missing_half_hours=ind['missing_half_hours'], incomplete_days=ind['incomplete_days']),
             era5=dict(file='~/gb-weather-data/backtest/' + os.path.basename(ERA5_OUT), sha256=b['output_sha256'],
                       half_hours=b['half_hours'], first=b['first'], last=b['last'], overlap_check=b['overlap_check'],
                       days_from_google_copy=arco, code_sha256=b['code_sha256'], weights_sha256=b['weights_sha256']),
             build_record_sha256=C.sha(ERA5_JSON), written_utc=dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds'))
    json.dump(m, open(MANIFEST, 'w'), indent=1)
    print(json.dumps(dict(indo_incomplete_days=len(ind['incomplete_days']), era5_overlap=b['overlap_check'],
                          era5_days_from_google_copy=len(arco)), indent=1))
    print('manifest written: lgbm_variants/v5_data_manifest.json')


if __name__ == '__main__':
    step = sys.argv[1] if len(sys.argv) > 1 else ''
    if step == 'indo': indo()
    elif step == 'manifest': manifest()
    else: sys.exit('usage: python lgbm_variants/fetch_v5.py indo | manifest')
