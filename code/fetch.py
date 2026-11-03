"""
Download every input once, save it to data/, and record SHA-256, row counts and fetch time in data/fetch_manifest.json
(plan Section 2). Run on the author's machine; the data hashes go into plan/PLAN_LOCK.json at freezing.

  indo.csv                         Elexon initial national demand outturn (INDO), 1 December 2022 - 1 November 2026
  neso_dayahead_publications.csv   Elexon national demand forecast publications (NDF), with publishTime
  neso_forecast_performance.csv    NESO's own record of its day-ahead forecast (gate check 3)
  neso_historic_nd.csv             NESO Historic Demand Data, 2024-2026 (robustness only)
  bank_holidays_ew.json            GOV.UK bank holidays, England and Wales

Usage:  python fetch.py --probe    one day of each source: prints columns and counts, saves nothing
        python fetch.py            the full download (about 20-40 minutes)
        python fetch.py --gaps     after the download: missing INDO half-hours, and days lost under each gap rule

"Contains BMRS data © Elexon Limited copyright and database right 2026"; "Supported by National Energy SO Open Data".
"""
import os, sys, io, json, time, datetime as dt
import numpy as np, requests, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import common as C

ELEXON = 'https://data.elexon.co.uk/bmrs/api/v1'
NESO = 'https://api.neso.energy/api/3/action'
INDO_FROM, INDO_TO = '2022-12-01', '2026-11-01'
NDF_FROM, NDF_TO = '2023-12-28', '2026-10-31'          # publication days needed for target days 2024-01-01 .. 2026-10-31


def get(url, **params):
    for attempt in range(5):
        try:
            r = requests.get(url, params=params, timeout=120); r.raise_for_status(); return r
        except Exception as e:
            if attempt == 4: raise
            time.sleep(5 * (attempt + 1))


def rows(js):
    return pd.DataFrame(js.get('data', js) if isinstance(js, dict) else js)


def indo_chunk(a, b):
    df = rows(get(f'{ELEXON}/demand/outturn', settlementDateFrom=a, settlementDateTo=b, format='json').json())
    return pd.DataFrame({'start_utc': pd.to_datetime(df.startTime, utc=True), 'settlement_date': df.settlementDate,
                         'settlement_period': df.settlementPeriod, 'mw': df.initialDemandOutturn.astype(float)})


def ndf_chunk(day):
    a = C.local(day, '00:00'); b = a + pd.Timedelta(days=1)
    df = rows(get(f'{ELEXON}/datasets/NDF', publishDateTimeFrom=a.strftime('%Y-%m-%dT%H:%MZ'),
                  publishDateTimeTo=b.strftime('%Y-%m-%dT%H:%MZ'), format='json').json())
    if df.empty: return df
    col = 'nationalDemand' if 'nationalDemand' in df else 'demand'
    out = pd.DataFrame({'publish_utc': pd.to_datetime(df.publishTime, utc=True), 'start_utc': pd.to_datetime(df.startTime, utc=True),
                        'settlement_date': df.settlementDate, 'settlement_period': df.settlementPeriod,
                        'mw': pd.to_numeric(df[col], errors='coerce')})
    keep = (out.start_utc >= out.publish_utc - pd.Timedelta(hours=1)) & (out.start_utc <= out.publish_utc + pd.Timedelta(days=3))
    return out[keep]


def neso_resource(package, name_contains=''):
    for r in get(f'{NESO}/package_show', id=package).json()['result']['resources']:
        if name_contains.lower() in (r.get('name') or '').lower():
            return pd.read_csv(io.StringIO(get(r['url']).text)), r['url']
    raise KeyError(name_contains)


def probe():
    d = '2025-01-15'
    i = indo_chunk(d, d); print('INDO', len(i), 'rows;', i.head(2).to_dict('records'))
    n = ndf_chunk(d); print('NDF', len(n), 'rows; publish times', sorted(n.publish_utc.dt.tz_convert(C.UK).dt.strftime('%H:%M').unique())[:12], '...')
    print('NDF sample', n.head(2).to_dict('records'))
    p, u = neso_resource('day-ahead-half-hourly-demand-forecast-performance'); print('performance file', len(p), 'rows', u)
    h = get('https://www.gov.uk/bank-holidays.json').json()['england-and-wales']['events']
    print('bank holidays', len(h), 'from', h[0]['date'], 'to', h[-1]['date'])


def full():
    os.makedirs(C.DATA, exist_ok=True); man = {'fetched_utc': dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds'), 'files': {}}
    def save(df, name):
        p = os.path.join(C.DATA, name); df.to_csv(p, index=False)
        man['files'][name] = dict(sha256=C.sha(p), rows=int(len(df))); print(f'{name}: {len(df):,} rows', flush=True)
    parts = []
    for a in pd.date_range(INDO_FROM, INDO_TO, freq='7D'):
        b = min(a + pd.Timedelta(days=6), pd.Timestamp(INDO_TO))
        parts.append(indo_chunk(f'{a:%Y-%m-%d}', f'{b:%Y-%m-%d}'))
    save(pd.concat(parts).drop_duplicates('start_utc').sort_values('start_utc'), 'indo.csv')
    parts = []
    for k, d in enumerate(pd.date_range(NDF_FROM, NDF_TO)):
        parts.append(ndf_chunk(d))
        if k % 50 == 0: print(f'  NDF {d:%Y-%m-%d}', flush=True)
    save(pd.concat(parts).drop_duplicates(['publish_utc', 'start_utc']).sort_values(['start_utc', 'publish_utc']),
         'neso_dayahead_publications.csv')
    save(neso_resource('day-ahead-half-hourly-demand-forecast-performance')[0], 'neso_forecast_performance.csv')
    nd = pd.concat([neso_resource('historic-demand-data', f'Historic Demand Data {y}')[0] for y in (2024, 2025, 2026)])
    save(nd, 'neso_historic_nd.csv')
    h = get('https://www.gov.uk/bank-holidays.json').json()['england-and-wales']['events']
    p = os.path.join(C.DATA, 'bank_holidays_ew.json'); json.dump(sorted(e['date'] for e in h), open(p, 'w'))
    man['files']['bank_holidays_ew.json'] = dict(sha256=C.sha(p), rows=len(h))
    json.dump(man, open(os.path.join(C.DATA, 'fetch_manifest.json'), 'w'), indent=1)
    print('written data/fetch_manifest.json')


def compare(target='2025-01-16', periods=(6, 18, 36)):
    """Does the NDF stream carry the same forecasts as the /evolution endpoint the feasibility check validated?
    For each period, prints every publication up to 10:00 UK on D-1 from both sources, with the value."""
    D = pd.Timestamp(target); cut = C.local(D - pd.Timedelta(days=1), '10:00')
    ndf = pd.concat([ndf_chunk(D - pd.Timedelta(days=k)) for k in (2, 1)])
    for sp in periods:
        ev = rows(get(f'{ELEXON}/forecast/demand/day-ahead/evolution', settlementDate=target, settlementPeriod=sp,
                      format='json').json())
        ev['pub'] = pd.to_datetime(ev.publishTime, utc=True)
        ev = ev[ev.pub <= cut].sort_values('pub')
        n = ndf[(ndf.settlement_date == target) & (ndf.settlement_period == sp) & (ndf.publish_utc <= cut)].sort_values('publish_utc')
        fmt = lambda t: t.tz_convert(C.UK).strftime('%d %H:%M')
        print(f'SP{sp} evolution: ' + ', '.join(f'{fmt(t)}={v}' for t, v in zip(ev.pub, ev.nationalDemand)))
        print(f'SP{sp} NDF:       ' + ', '.join(f'{fmt(t)}={v:.0f}' for t, v in zip(n.publish_utc, n.mw)))


def gaps():
    """Missing INDO half-hours, and how many target days each candidate rule would exclude. Reads only INDO."""
    import inputs as I
    s, _ = I.load_indo(os.path.join(C.DATA, 'indo.csv'))
    miss = s.isna(); run_id = (miss != miss.shift()).cumsum()
    runs = [(g.index[0], len(g)) for _, g in s[miss].groupby(run_id[miss])]
    print(f'{int(miss.sum())} missing half-hours in {len(runs)} runs; run lengths: '
          f'{pd.Series([n for _, n in runs]).value_counts().sort_index().to_dict()}')
    for t, n in runs[:40]: print(f'  {t.tz_convert(C.UK):%Y-%m-%d %H:%M} UK, {n} half-hour(s)')
    for limit in (0, 2):
        filled = s.copy()
        for t, n in runs:                                    # straight line between the neighbours; short runs only
            if n > limit: continue
            a, b = t - C.HALF_HOUR, t + n * C.HALF_HOUR
            if a in s.index and b in s.index and np.isfinite(s[a]) and np.isfinite(s[b]):
                filled[t:b - C.HALF_HOUR] = s[a] + (s[b] - s[a]) * np.arange(1, n + 1) / (n + 1)
        lost_t = lost_c = 0
        for D in C.days():
            try: I.targets(s, D)
            except ValueError: lost_t += 1; continue
            try: I.context(filled, D)
            except ValueError: lost_c += 1
        print(f'rule "fill runs of <= {limit} in contexts only": {lost_t} days lost to missing outturn, '
              f'{lost_c} to missing context, of {len(C.days())}')


if __name__ == '__main__':
    if '--probe' in sys.argv: probe()
    elif '--compare' in sys.argv: compare()
    elif '--gaps' in sys.argv: gaps()
    else: full()
