"""
Imbalance exposure, data step (imbalance_cost/PLAN.md §7, frozen at tag imbalance-cost-plan). Committed before it runs;
its manifest is committed after. It fetches and checks prices; it computes no exposure and reads no forecast.

For: a reviewer checking that the prices are the plan's, that thin-trading zeros never become prices, and that every
gap is listed.

Fetches, from Elexon's Insights API (open, no key), for every local day in the range:
  System Price      /balancing/settlement/system-prices/{date}   (dataset DISEBSP): systemSellPrice, systemBuyPrice,
                    createdDateTime. GB has a single imbalance price, so the two must be equal; any period where
                    they differ is counted and listed.
  Market Index Data /balancing/pricing/market-index?from=&to=     price and volume from each provider (APXMIDP for
                    EPEX, N2EXMIDP for N2EX).
Builds, per settlement period:
  mip               the volume-weighted average of the providers with volume > 0. A provider reporting zero volume
                    is left out: under the Market Index Definition Statement its price defaults to 0 when trading is
                    below the liquidity threshold, and that 0 is not a price. With no provider volume, mip is missing.
Writes (data/ is not committed):
  data/prices/raw_system_prices_<A>_<B>.csv, data/prices/raw_market_index_<A>_<B>.csv   as fetched
  data/prices/prices_<A>_<B>.csv     start_utc, settlement_date, settlement_period, system_price, mip, mip_volume,
                                     mip_providers, sp_created_utc
  imbalance_cost/prices_manifest_<A>_<B>.json   SHA-256 of every file, counts, gaps and defaults by month, the
                                     settlement-price creation times, the endpoints, the fetch time and attribution

Modes:
    python imbalance_cost/fetch_prices.py --self-test                  invented records with known answers; no network
    python imbalance_cost/fetch_prices.py                              stage 1: 16 March 2024 to 31 October 2026
    python imbalance_cost/fetch_prices.py --first 2026-11-05 --last 2027-03-31    stage 2, after 31 March 2027
"""
import argparse, datetime as dt, hashlib, json, os, sys, time
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, 'code'))
import common as C

API = 'https://data.elexon.co.uk/bmrs/api/v1'
SP_PATH, MID_PATH = '/balancing/settlement/system-prices/{date}', '/balancing/pricing/market-index'
PROVIDERS = ('APXMIDP', 'N2EXMIDP')
STAGE1 = ('2024-03-16', '2026-10-31')
DATA = os.path.join(ROOT, 'data', 'prices')
ATTRIBUTION = 'Contains BMRS data © Elexon Limited copyright and database right.'
PAUSE = 0.2                                                   # seconds between requests


def say(*a): print(f'{dt.datetime.now():%H:%M:%S}', *a, flush=True)
def sha(p): return hashlib.sha256(open(p, 'rb').read()).hexdigest()


def get(url, params=None):
    import requests
    for attempt in range(5):
        try:
            r = requests.get(url, params=params, timeout=60, headers={'Accept': 'application/json'})
            if r.status_code == 200: return r.json()['data']
            if r.status_code in (429, 500, 502, 503, 504): time.sleep(5 * (attempt + 1)); continue
            raise RuntimeError(f'{r.status_code} from {r.url}: {r.text[:200]}')
        except requests.RequestException as e:
            if attempt == 4: raise
            say(f'retrying after {e.__class__.__name__}'); time.sleep(5 * (attempt + 1))
    raise RuntimeError(f'no answer from {url}')


def periods(day):
    """Every settlement period of local day D: (period number, UTC start)."""
    starts = C.target_starts(pd.Timestamp(day))
    return pd.DataFrame({'settlement_date': f'{pd.Timestamp(day):%Y-%m-%d}', 'settlement_period': range(1, len(starts) + 1),
                         'start_utc': starts})


def fetch_day(day):
    d = f'{pd.Timestamp(day):%Y-%m-%d}'
    sp = pd.DataFrame(get(API + SP_PATH.format(date=d)))
    a, b = C.day_bounds(pd.Timestamp(day))
    a = a - C.HALF_HOUR                                       # a margin either side; records are kept by settlementDate
    mid = pd.DataFrame(get(API + MID_PATH, params={'from': a.strftime('%Y-%m-%dT%H:%MZ'), 'to': b.strftime('%Y-%m-%dT%H:%MZ')}))
    if len(mid): mid = mid[mid['settlementDate'] == d]
    return sp, mid


def build(day, sp, mid):
    """One row per settlement period of D, with the checks' counts. Pure: no network, testable."""
    P = periods(day)
    s = sp.rename(columns={'settlementPeriod': 'settlement_period'})
    s = s[s['settlementDate'] == P['settlement_date'].iloc[0]] if len(s) else s
    out = P.copy()
    if len(s):
        s = s.drop_duplicates('settlement_period', keep='last').set_index('settlement_period')
        out['system_price'] = out['settlement_period'].map(s['systemSellPrice']).astype(float)
        out['system_buy_price'] = out['settlement_period'].map(s['systemBuyPrice']).astype(float)
        out['sp_created_utc'] = out['settlement_period'].map(s['createdDateTime'])
        out['sp_start_ok'] = out['settlement_period'].map(pd.to_datetime(s['startTime'], utc=True)) == out['start_utc']
    else:
        out['system_price'] = np.nan; out['system_buy_price'] = np.nan; out['sp_created_utc'] = None; out['sp_start_ok'] = False
    m = mid.rename(columns={'settlementPeriod': 'settlement_period'}) if len(mid) else mid
    vols, prices, provs, defaulted, start_ok = [], [], [], [], []
    for _, row in out.iterrows():
        g = m[m['settlement_period'] == row['settlement_period']] if len(m) else m
        g = g.drop_duplicates('dataProvider', keep='last') if len(g) else g
        live = g[g['volume'].astype(float) > 0] if len(g) else g
        v = float(live['volume'].astype(float).sum()) if len(live) else 0.0
        prices.append(float((live['price'].astype(float) * live['volume'].astype(float)).sum() / v) if v > 0 else np.nan)
        vols.append(v); provs.append('+'.join(sorted(live['dataProvider'])) if len(live) else '')
        defaulted.append(int((g['volume'].astype(float) <= 0).sum()) if len(g) else 0)
        start_ok.append(bool((pd.to_datetime(g['startTime'], utc=True) == row['start_utc']).all()) if len(g) else True)
    out['mip'], out['mip_volume'], out['mip_providers'] = prices, vols, provs
    out['mid_defaulted_providers'], out['mid_start_ok'] = defaulted, start_ok
    return out


def summarise(frame):
    f = frame.copy(); f['month'] = pd.to_datetime(f['settlement_date']).dt.strftime('%Y-%m')
    by = lambda mask: {k: int(v) for k, v in f[mask].groupby('month').size().items()}
    sp_missing = f['system_price'].isna(); mip_missing = f['mip'].isna()
    split = f['system_price'].notna() & f['system_buy_price'].notna() & (f['system_price'] != f['system_buy_price'])
    return dict(periods=int(len(f)), days=int(f['settlement_date'].nunique()),
                system_price_missing=int(sp_missing.sum()), system_price_missing_by_month=by(sp_missing),
                sell_buy_differ=int(split.sum()), sell_buy_differ_periods=f.loc[split, ['settlement_date', 'settlement_period']].values.tolist(),
                mip_missing=int(mip_missing.sum()), mip_missing_by_month=by(mip_missing),
                mip_providers=f['mip_providers'].replace('', 'none').value_counts().to_dict(),
                provider_records_defaulted_to_zero=int(f['mid_defaulted_providers'].sum()),
                mip_zero_with_volume=int(((f['mip'] == 0) & (f['mip_volume'] > 0)).sum()),
                start_time_mismatches=int((~f['sp_start_ok'] & f['system_price'].notna()).sum() + (~f['mid_start_ok']).sum()),
                sp_created_utc=dict(first=str(f['sp_created_utc'].dropna().min()), last=str(f['sp_created_utc'].dropna().max())))


def run(first, last):
    days = pd.date_range(first, last); os.makedirs(DATA, exist_ok=True)
    tag = f'{pd.Timestamp(first):%Y-%m-%d}_{pd.Timestamp(last):%Y-%m-%d}'
    raw_sp, raw_mid, rows = [], [], []
    for i, D in enumerate(days):
        sp, mid = fetch_day(D); raw_sp.append(sp); raw_mid.append(mid); rows.append(build(D, sp, mid))
        if i % 30 == 0: say(f'{D:%Y-%m-%d} ({i + 1} of {len(days)})')
        time.sleep(PAUSE)
    fetched = dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds')
    frame = pd.concat(rows, ignore_index=True)
    paths = {'raw_system_prices': os.path.join(DATA, f'raw_system_prices_{tag}.csv'),
             'raw_market_index': os.path.join(DATA, f'raw_market_index_{tag}.csv'),
             'prices': os.path.join(DATA, f'prices_{tag}.csv')}
    pd.concat(raw_sp, ignore_index=True).to_csv(paths['raw_system_prices'], index=False)
    pd.concat(raw_mid, ignore_index=True).to_csv(paths['raw_market_index'], index=False)
    keep = ['start_utc', 'settlement_date', 'settlement_period', 'system_price', 'mip', 'mip_volume', 'mip_providers', 'sp_created_utc']
    out = frame[keep].copy(); out['start_utc'] = out['start_utc'].map(lambda t: t.isoformat())
    out.to_csv(paths['prices'], index=False)
    summary = summarise(frame)
    man = dict(note='imbalance exposure, data step (PLAN.md §7); prices only, no exposure computed',
               first_day=f'{pd.Timestamp(first):%Y-%m-%d}', last_day=f'{pd.Timestamp(last):%Y-%m-%d}', fetched_utc=fetched,
               endpoints=dict(system_price=API + SP_PATH, market_index=API + MID_PATH, providers=list(PROVIDERS)),
               files={k: dict(path=os.path.relpath(p, ROOT), sha256=sha(p), rows=int(sum(1 for _ in open(p)) - 1)) for k, p in paths.items()},
               checks=summary, script_sha256=sha(os.path.abspath(__file__)), attribution=ATTRIBUTION)
    mpath = os.path.join(HERE, f'prices_manifest_{tag}.json'); json.dump(man, open(mpath, 'w'), indent=1, default=str)
    say(f'wrote {os.path.relpath(mpath, ROOT)}')
    for k in ('periods', 'days', 'system_price_missing', 'sell_buy_differ', 'mip_missing', 'mip_providers',
              'provider_records_defaulted_to_zero', 'mip_zero_with_volume', 'start_time_mismatches'):
        say(f'{k}: {summary[k]}')
    if summary['start_time_mismatches']: say('WARNING: start times disagree with the settlement periods; see the manifest')


def self_test():
    ok = True
    def rec(name, good):
        nonlocal ok; ok &= bool(good); print(('PASS ' if good else 'FAIL ') + name, flush=True)

    def fake(day, sp_price=50.0, mid_rows=None, drop_sp=()):
        P = periods(day); d = P['settlement_date'].iloc[0]
        sp = pd.DataFrame([dict(settlementDate=d, settlementPeriod=int(r.settlement_period), startTime=r.start_utc.strftime('%Y-%m-%dT%H:%M:%SZ'),
                                createdDateTime='2025-01-02T00:00:00Z', systemSellPrice=sp_price, systemBuyPrice=sp_price)
                           for r in P.itertuples() if r.settlement_period not in drop_sp])
        mid = pd.DataFrame([dict(startTime=r.start_utc.strftime('%Y-%m-%dT%H:%M:%SZ'), dataProvider=p, settlementDate=d,
                                 settlementPeriod=int(r.settlement_period), price=pr, volume=v)
                            for r in P.itertuples() for p, pr, v in (mid_rows(r.settlement_period) if mid_rows else [])])
        return sp, mid

    # two providers with volume: volume-weighted average
    sp, mid = fake('2025-01-15', mid_rows=lambda k: [('APXMIDP', 80.0, 300.0), ('N2EXMIDP', 100.0, 100.0)])
    b = build('2025-01-15', sp, mid)
    rec('volume-weighted average', np.allclose(b['mip'], 85.0) and (b['mip_providers'] == 'APXMIDP+N2EXMIDP').all())
    # one provider defaulted to zero: left out, never averaged in as a price of 0
    sp, mid = fake('2025-01-15', mid_rows=lambda k: [('APXMIDP', 88.96, 1494.85), ('N2EXMIDP', 0.0, 0.0)])
    b = build('2025-01-15', sp, mid)
    rec('defaulted provider left out', np.allclose(b['mip'], 88.96) and (b['mip_providers'] == 'APXMIDP').all()
        and b['mid_defaulted_providers'].sum() == 48)
    # both defaulted: missing, not zero
    sp, mid = fake('2025-01-15', mid_rows=lambda k: [('APXMIDP', 0.0, 0.0), ('N2EXMIDP', 0.0, 0.0)] if k == 7 else [('APXMIDP', 70.0, 50.0)])
    b = build('2025-01-15', sp, mid); s = summarise(b)
    rec('both defaulted is missing', np.isnan(b.loc[6, 'mip']) and s['mip_missing'] == 1 and s['mip_missing_by_month'] == {'2025-01': 1})
    # a genuine zero price with volume is kept and counted
    sp, mid = fake('2025-01-15', mid_rows=lambda k: [('APXMIDP', 0.0, 40.0)] if k == 3 else [('APXMIDP', 70.0, 50.0)])
    b = build('2025-01-15', sp, mid)
    rec('zero price with volume kept', b.loc[2, 'mip'] == 0 and summarise(b)['mip_zero_with_volume'] == 1)
    # no market index records at all for a day: every period missing
    sp, mid = fake('2025-01-15')
    rec('no market index records', build('2025-01-15', sp, mid)['mip'].isna().all())
    # clock changes: 46 and 50 periods, start times aligned
    for day, n in (('2025-03-30', 46), ('2025-10-26', 50)):
        sp, mid = fake(day, mid_rows=lambda k: [('APXMIDP', 60.0, 10.0)])
        b = build(day, sp, mid)
        rec(f'{n} periods on {day}', len(b) == n and b['sp_start_ok'].all() and b['mid_start_ok'].all() and b['mip'].notna().all())
    # a missing System Price period and a sell/buy split are counted
    sp, mid = fake('2025-01-15', mid_rows=lambda k: [('APXMIDP', 60.0, 10.0)], drop_sp=(10,))
    sp.loc[0, 'systemBuyPrice'] = 51.0
    s = summarise(build('2025-01-15', sp, mid))
    rec('missing System Price counted', s['system_price_missing'] == 1)
    rec('sell and buy split counted', s['sell_buy_differ'] == 1 and s['sell_buy_differ_periods'] == [['2025-01-15', 1]])
    # a misdated record is caught
    sp, mid = fake('2025-01-15', mid_rows=lambda k: [('APXMIDP', 60.0, 10.0)])
    mid.loc[0, 'startTime'] = '2025-01-15T05:00:00Z'
    rec('misaligned start time caught', summarise(build('2025-01-15', sp, mid))['start_time_mismatches'] == 1)
    print('self-test: ' + ('PASS' if ok else 'FAIL')); return ok


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--self-test', action='store_true'); ap.add_argument('--first', default=STAGE1[0]); ap.add_argument('--last', default=STAGE1[1])
    a = ap.parse_args()
    if a.self_test: sys.exit(0 if self_test() else 1)
    run(a.first, a.last)
