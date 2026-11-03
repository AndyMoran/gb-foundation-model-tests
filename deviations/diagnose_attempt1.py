"""
Diagnose the two gate failures in results/attempt1 (deviation 1). Changes no locked file and no result.

  A  Gate 3, NESO reconstruction (91.2% < 95%): how the performance file is laid out, where the mismatches fall,
     and which Elexon publication (if any) carries the value NESO's file records.
  B  Gate 4, Timestral repeatability: the gate re-forecast 3 days as a batch of 3 and compared them bit for bit with
     forecasts made in batches of up to 64. This separates "not repeatable" from "batch size changes the rounding".

Run from the repository root, in the model environment:
    python deviations/diagnose_attempt1.py > deviations/diagnose_attempt1.txt 2>&1
"""
import os, sys
import numpy as np, pandas as pd
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, os.path.join(ROOT, 'code'))
import common as C, inputs as I, baselines as B, models as M, run as R

A1 = os.path.join(ROOT, 'results', 'attempt1')
fc = pd.read_csv(os.path.join(A1, 'forecasts.csv'))
fc['day'] = pd.to_datetime(fc['day'])

print('=== A. Gate 3: NESO reconstruction ===')
perf = pd.read_csv(os.path.join(C.DATA, 'neso_forecast_performance.csv'))
print('columns:', list(perf.columns)); print(perf.head(3).to_string()); print('dtypes:', perf.dtypes.to_dict())
print('Date samples:', perf['Date'].astype(str).sample(8, random_state=1).tolist())
for label, kw in (('default parse', {}), ('dayfirst', {'dayfirst': True})):
    d = pd.to_datetime(perf['Date'], errors='coerce', **kw)
    print(f'{label}: range {d.min()} .. {d.max()}, unparsed {int(d.isna().sum())}')
p = perf.copy(); p['Date'] = pd.to_datetime(p['Date']).dt.normalize()
dup = p.duplicated(['Date', 'Settlement_Period'], keep=False)
print(f'rows sharing a (Date, Settlement_Period): {int(dup.sum())}')
if dup.any(): print(p[dup].head(10).to_string())
p = p[(p.Settlement_Period >= 17) & (p.Settlement_Period <= 48)]
o = fc[fc.neso.notna()][['day', 'period', 'start_utc', 'neso']].rename(columns={'day': 'Date', 'period': 'Settlement_Period'})
j = o.merge(p[['Date', 'Settlement_Period', 'Demand_Forecast']], on=['Date', 'Settlement_Period'])
j['diff'] = j.neso - j.Demand_Forecast; j['match'] = j['diff'].abs() < 0.5
print(f'merged rows {len(j)} (ours SP17-48: {int(((o.Settlement_Period >= 17) & (o.Settlement_Period <= 48)).sum())}); '
      f'match share {j.match.mean():.4f}')
mm = j[~j.match].copy()
mm['year'] = mm.Date.dt.year; mm['month'] = mm.Date.dt.month
mm['bst'] = pd.to_datetime(mm.start_utc, utc=True).dt.tz_convert(C.UK).map(lambda t: bool(t.dst()))
print('mismatches by year:', mm.year.value_counts().sort_index().to_dict())
print('mismatches by month:', mm.month.value_counts().sort_index().to_dict())
print('mismatches by settlement period:', mm.Settlement_Period.value_counts().sort_index().to_dict())
print('mismatches in BST / GMT:', mm.bst.value_counts().to_dict())
days_mm = mm.groupby('Date').size()
print(f'days with any mismatch: {len(days_mm)}; half-hours per such day: {days_mm.value_counts().sort_index().to_dict()}')
print('abs difference quantiles (MW):', mm['diff'].abs().quantile([.1, .5, .9, 1]).round(1).to_dict())
pubs = I.load_neso(os.path.join(C.DATA, 'neso_dayahead_publications.csv'))
pick = mm.sort_values('Date').iloc[np.linspace(0, len(mm) - 1, min(15, len(mm))).astype(int)]
print('\nSample mismatches: which Elexon publications carry NESO-file value (UK times)')
for _, r in pick.iterrows():
    t = pd.Timestamp(r.start_utc); q = pubs[pubs.start_utc == t]
    hit = q[(q.mw - r.Demand_Forecast).abs() < 0.5].publish_utc.dt.tz_convert(C.UK).dt.strftime('%m-%d %H:%M').tolist()
    used = q[(q.mw - r.neso).abs() < 0.5].publish_utc.dt.tz_convert(C.UK).dt.strftime('%m-%d %H:%M').tolist()
    print(f'  {r.Date:%Y-%m-%d} SP{r.Settlement_Period}: ours {r.neso:.0f}, file {r.Demand_Forecast:.0f}; '
          f'file value in publications {hit[:4] or "none"}; ours in {used[:3]}')

print('\n=== B. Gate 4: Timestral repeatability ===')
series, pubs2, hol, perf2, nd = R.load_data(False)
reg = B.Regression(series, hol)
rec, _ = R.build_days(series, pubs2, reg, C.days())
groups = {}
for D in rec: groups.setdefault(C.horizon(D), []).append(D)
(h, first), ds = next(iter(groups.items())); chunk = ds[:64]; sample = list(rec)[:3]
m = M.get('timestral')
saved = {D: fc[fc.day == D].timestral.values for D in sample}
def run_batch(days):
    F = m.forecast([rec[D]['ctx'] for D in days], h)
    return {D: f[first:first + len(rec[D]['y'])] for D, f in zip(days, F)}
same1, same2 = run_batch(chunk), run_batch(chunk)
small1, small2 = run_batch(sample), run_batch(sample)
mx = lambda a, b, ks: max(float(np.abs(a[k] - b[k]).max()) for k in ks)
print(f'horizon {h}; original batch {len(chunk)} days; gate sample {[f"{D:%Y-%m-%d}" for D in sample]}')
print(f'same batch of {len(chunk)}, run twice: max difference {mx(same1, same2, chunk):.3g} MW')
print(f'batch of {len(chunk)} now vs attempt 1 saved: max difference {mx(same1, saved, sample):.3g} MW')
print(f'batch of 3, run twice: max difference {mx(small1, small2, sample):.3g} MW')
print(f'batch of 3 vs batch of {len(chunk)}: max difference {mx(small1, same1, sample):.3g} MW')
