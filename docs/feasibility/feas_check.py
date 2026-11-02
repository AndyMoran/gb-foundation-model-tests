"""
Rung 1 feasibility check: can NESO's day-ahead demand forecast be used as a baseline, and which outturn matches it?
No model is run and no forecast is scored. Prints a short report to paste back; writes feas_check_output.txt.

Checks
  A. Elexon Insights API, day-ahead demand forecast "evolution": for sample settlement periods in 2024, 2025 and
     2026, list every publication (publishTime) and its nationalDemand. Answers: how far back the published history
     goes, how many times a day the forecast is issued, and at what times.
  B. Outturn: Elexon initial national demand outturn (INDO) against NESO's Historic Demand Data (ND) for the same
     settlement periods. Answers: are they the same series, and has NESO's ND been revised since first publication?
  C. NESO "Day Ahead Half Hourly Demand Forecast Performance": date range and columns of the half-hourly
     forecast-and-outturn file.

Usage:  python feas_check.py
Data: "Contains BMRS data © Elexon Limited copyright and database right 2026" and
      "Supported by National Energy SO Open Data".
"""
import io, sys, json, datetime as dt
import requests, pandas as pd

ELEXON = 'https://data.elexon.co.uk/bmrs/api/v1'
NESO = 'https://api.neso.energy/api/3/action'
SAMPLES = ['2024-01-17', '2025-01-15', '2026-10-14']        # mid-week winter days, plus a recent one
PERIODS = [6, 18, 36]                                      # 02:30, 08:30 and 17:30 (local time) settlement periods
out = []
def say(s=''): print(s, flush=True); out.append(str(s))
def get(url, **params):
    r = requests.get(url, params=params, timeout=60); r.raise_for_status(); return r


def check_a():
    say('A. Day-ahead forecast publications (Elexon evolution endpoint)')
    for d in SAMPLES:
        for sp in PERIODS:
            try:
                js = get(f'{ELEXON}/forecast/demand/day-ahead/evolution', settlementDate=d,
                         settlementPeriod=sp, format='json').json()
                rows = js.get('data', js)
                if not rows:
                    say(f'  {d} SP{sp}: no publications returned'); continue
                df = pd.DataFrame(rows).sort_values('publishTime')
                pubs = ', '.join(f"{p[5:16]}={v}" for p, v in zip(df.publishTime, df.nationalDemand))
                say(f'  {d} SP{sp}: {len(df)} publications | {pubs}')
            except Exception as e:
                say(f'  {d} SP{sp}: ERROR {e}')


def neso_resource_url(package, name_contains):
    js = get(f'{NESO}/package_show', id=package).json()
    for r in js['result']['resources']:
        if name_contains.lower() in (r.get('name') or '').lower():
            return r['url'], r.get('name')
    raise KeyError(f'no resource containing {name_contains!r} in {package}')


def check_b():
    say('\nB. Outturn: Elexon INDO against NESO Historic Demand Data (ND)')
    for d in SAMPLES[:2]:
        try:
            js = get(f'{ELEXON}/demand/outturn', settlementDateFrom=d, settlementDateTo=d, format='json').json()
            indo = pd.DataFrame(js.get('data', js))
            indo = indo.set_index('settlementPeriod')['initialDemandOutturn'].astype(float)
            url, name = neso_resource_url('historic-demand-data', f'Historic Demand Data {d[:4]}')
            nd = pd.read_csv(io.StringIO(get(url).text))
            nd['SETTLEMENT_DATE'] = pd.to_datetime(nd['SETTLEMENT_DATE'], format='mixed', dayfirst=True).dt.strftime('%Y-%m-%d')
            nd = nd[nd.SETTLEMENT_DATE == d].set_index('SETTLEMENT_PERIOD')['ND'].astype(float)
            j = pd.concat([indo.rename('INDO'), nd.rename('ND')], axis=1).dropna()
            diff = j.ND - j.INDO
            say(f'  {d}: {len(j)} periods matched; ND - INDO: mean {diff.mean():+.0f} MW, '
                f'mean abs {diff.abs().mean():.0f} MW, max abs {diff.abs().max():.0f} MW; identical in '
                f'{int((diff.abs() < 1).sum())} of {len(j)} ({name})')
        except Exception as e:
            say(f'  {d}: ERROR {e}')


def check_c():
    say('\nC. NESO day-ahead half-hourly forecast performance file')
    try:
        url, name = neso_resource_url('day-ahead-half-hourly-demand-forecast-performance', '')
        df = pd.read_csv(io.StringIO(get(url).text))
        say(f'  resource: {name}; rows {len(df):,}; columns: {", ".join(df.columns)}')
        say('  first row: ' + json.dumps(df.iloc[0].to_dict(), default=str))
        say('  last row:  ' + json.dumps(df.iloc[-1].to_dict(), default=str))
    except Exception as e:
        say(f'  ERROR {e}')


if __name__ == '__main__':
    say(f'Feasibility check run {dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")}')
    check_a(); check_b(); check_c()
    open('feas_check_output.txt', 'w').write('\n'.join(out) + '\n')
    say('\nwritten feas_check_output.txt')
