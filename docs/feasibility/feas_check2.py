"""
Rung 1 feasibility check, part 2. No model is run and no forecast is scored. Writes feas_check2_output.txt.

  D. Which outturn does NESO's forecast-performance file score against: Elexon's initial outturn (INDO), NESO's
     Historic Demand Data (ND), or neither?
  E. How soon after each half-hour is INDO published, and is it ever republished (revised)?
  F. When is the day-ahead forecast in the performance file published: local time of day, how regular across years,
     and how many target days have a missing forecast?

Usage:  python feas_check2.py
Data: "Contains BMRS data © Elexon Limited copyright and database right 2026" and
      "Supported by National Energy SO Open Data".
"""
import io, json, datetime as dt
import requests, pandas as pd

ELEXON = 'https://data.elexon.co.uk/bmrs/api/v1'
NESO = 'https://api.neso.energy/api/3/action'
DATES = ['2024-01-17', '2025-01-15', '2026-10-14']
out = []
def say(s=''): print(s, flush=True); out.append(str(s))
def get(url, **params):
    r = requests.get(url, params=params, timeout=120); r.raise_for_status(); return r
def neso_csv(package, name_contains=''):
    for r in get(f'{NESO}/package_show', id=package).json()['result']['resources']:
        if name_contains.lower() in (r.get('name') or '').lower():
            return pd.read_csv(io.StringIO(get(r['url']).text))
    raise KeyError(f'{name_contains!r} not in {package}')
def rows(js): return pd.DataFrame(js.get('data', js) if isinstance(js, dict) else js)


def indo_outturn(d):
    df = rows(get(f'{ELEXON}/demand/outturn', settlementDateFrom=d, settlementDateTo=d, format='json').json())
    return df.set_index('settlementPeriod')['initialDemandOutturn'].astype(float), df


if __name__ == '__main__':
    say(f'Feasibility check, part 2, run {dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")}')
    perf = neso_csv('day-ahead-half-hourly-demand-forecast-performance')
    perf['Date'] = pd.to_datetime(perf['Date']).dt.strftime('%Y-%m-%d')

    # D. which outturn the performance file uses
    say('\nD. Performance-file outturn against INDO and NESO ND (MW, performance minus each)')
    nd_cache = {}
    for d in DATES:
        try:
            p = perf[perf.Date == d].set_index('Settlement_Period')['Demand_Outturn'].astype(float)
            indo, _ = indo_outturn(d)
            yr = d[:4]
            if yr not in nd_cache: nd_cache[yr] = neso_csv('historic-demand-data', f'Historic Demand Data {yr}')
            nd = nd_cache[yr]; nd['d'] = pd.to_datetime(nd['SETTLEMENT_DATE'], format='mixed', dayfirst=True).dt.strftime('%Y-%m-%d')
            nd = nd[nd.d == d].set_index('SETTLEMENT_PERIOD')['ND'].astype(float)
            for name, s in (('INDO', indo), ('ND', nd)):
                j = pd.concat([p.rename('P'), s.rename('S')], axis=1).dropna(); diff = j.P - j.S
                say(f'  {d} vs {name}: {len(j)} periods; mean {diff.mean():+.0f}, mean abs {diff.abs().mean():.0f}, '
                    f'identical (within 1 MW) in {int((diff.abs() < 1).sum())}')
        except Exception as e:
            say(f'  {d}: ERROR {e}')

    # E. INDO publication lag and revisions
    say('\nE. INDO publication lag and republication')
    for d in DATES:
        try:
            start = dt.datetime.fromisoformat(d); end = start + dt.timedelta(days=1, hours=6)
            js = get(f'{ELEXON}/datasets/INDO', publishDateTimeFrom=start.isoformat() + 'Z',
                     publishDateTimeTo=end.isoformat() + 'Z', format='json').json()
            df = rows(js)
            if df.empty: say(f'  {d}: no INDO rows returned'); continue
            if d == DATES[0]: say(f'  columns: {", ".join(df.columns)}')
            df['publishTime'] = pd.to_datetime(df['publishTime'], utc=True)
            df['startTime'] = pd.to_datetime(df['startTime'], utc=True)
            df = df[df.settlementDate == d] if 'settlementDate' in df else df
            lag = (df.publishTime - (df.startTime + pd.Timedelta(minutes=30))).dt.total_seconds() / 60
            per_sp = df.groupby('settlementPeriod').size()
            say(f'  {d}: {len(df)} rows for {per_sp.size} periods; publications per period: max {per_sp.max()}; '
                f'lag after period end (minutes): min {lag.min():.0f}, median {lag.median():.0f}, max {lag.max():.0f}')
        except Exception as e:
            say(f'  {d}: ERROR {e}')

    # F. publication time of the day-ahead forecast in the performance file
    say('\nF. Day-ahead forecast publication times in the performance file (UK local time)')
    try:
        pub = pd.to_datetime(perf['Publish_Datetime'], utc=True, errors='coerce')
        tgt = pd.to_datetime(perf['Date'])
        perf['pub_local'] = pub.dt.tz_convert('Europe/London')
        perf['days_before'] = (tgt.dt.date - perf['pub_local'].dt.date).apply(lambda x: getattr(x, 'days', None))
        by_day = perf.groupby('Date').agg(pub=('pub_local', 'min'), npub=('pub_local', 'nunique'),
                                          before=('days_before', 'min'), missing=('Demand_Forecast', lambda s: s.isna().sum()))
        by_day['year'] = by_day.index.str[:4]; by_day['hhmm'] = by_day.pub.dt.strftime('%H:%M')
        say(f'  target days: {len(by_day):,}; days with more than one publish time: {int((by_day.npub > 1).sum())}; '
            f'days with any missing forecast half-hour: {int((by_day.missing > 0).sum())}')
        say(f'  days before target: {by_day.before.value_counts().sort_index().to_dict()}')
        for y, g in by_day.groupby('year'):
            top = g.hhmm.value_counts().head(5).to_dict()
            say(f'  {y}: {len(g)} days; earliest {g.hhmm.min()}, latest {g.hhmm.max()}; most common {top}')
    except Exception as e:
        say(f'  ERROR {e}')

    open('feas_check2_output.txt', 'w').write('\n'.join(out) + '\n')
    say('\nwritten feas_check2_output.txt')
