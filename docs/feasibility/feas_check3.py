"""
Rung 1 feasibility check, part 3. No model is run and no forecast is scored. Writes feas_check3_output.txt.

  G. Which Elexon publication does NESO's performance file record as "the" day-ahead forecast? For sample days,
     match the file's forecast values against every Elexon publication for the same half-hours.
  H. Model weights: licence, current revision and creation date of each model's Hugging Face repository.

Usage:  python feas_check3.py
Data: "Contains BMRS data © Elexon Limited copyright and database right 2026" and
      "Supported by National Energy SO Open Data".
"""
import io, datetime as dt
import requests, pandas as pd

ELEXON = 'https://data.elexon.co.uk/bmrs/api/v1'
NESO = 'https://api.neso.energy/api/3/action'
DAYS = ['2024-01-17', '2024-07-17', '2025-01-15', '2025-07-16', '2026-07-15', '2026-10-28']
SPS = [6, 18, 30, 36]
MODELS = ['google/timesfm-2.5-200m-pytorch', 'amazon/chronos-2', 'mistralai/Timestral-209M']
out = []
def say(s=''): print(s, flush=True); out.append(str(s))
def get(url, **params):
    r = requests.get(url, params=params, timeout=120); r.raise_for_status(); return r


if __name__ == '__main__':
    say(f'Feasibility check, part 3, run {dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")}')
    res = get(f'{NESO}/package_show', id='day-ahead-half-hourly-demand-forecast-performance').json()['result']['resources'][0]
    perf = pd.read_csv(io.StringIO(get(res['url']).text))
    perf['Date'] = pd.to_datetime(perf['Date']).dt.strftime('%Y-%m-%d')

    say('\nG. Performance-file forecast matched against Elexon publications (UK local times)')
    for d in DAYS:
        for sp in SPS:
            try:
                row = perf[(perf.Date == d) & (perf.Settlement_Period == sp)]
                if row.empty: say(f'  {d} SP{sp}: not in performance file'); continue
                fval = float(row.Demand_Forecast.iloc[0]); fpub = row.Publish_Datetime.iloc[0]
                js = get(f'{ELEXON}/forecast/demand/day-ahead/evolution', settlementDate=d,
                         settlementPeriod=sp, format='json').json()
                ev = pd.DataFrame(js.get('data', js))
                ev['pub'] = pd.to_datetime(ev.publishTime, utc=True).dt.tz_convert('Europe/London')
                ev = ev.sort_values('pub')
                match = ev[(ev.nationalDemand.astype(float) - fval).abs() < 0.5]
                first = ev.pub.iloc[0].strftime('%m-%d %H:%M')
                m = ', '.join(match.pub.dt.strftime('%m-%d %H:%M').head(4)) or 'none'
                say(f'  {d} SP{sp}: file {fval:.0f} MW (file publish {fpub}); first Elexon publication {first}; '
                    f'Elexon publications with this value: {m}')
            except Exception as e:
                say(f'  {d} SP{sp}: ERROR {e}')

    say('\nH. Model weights on Hugging Face')
    for mid in MODELS:
        try:
            info = get(f'https://huggingface.co/api/models/{mid}').json()
            lic = [t for t in info.get('tags', []) if t.startswith('license:')]
            say(f"  {mid}: licence tag {lic or 'none'}; revision {info.get('sha')}; created {info.get('createdAt')}; "
                f"last modified {info.get('lastModified')}")
        except Exception as e:
            say(f'  {mid}: ERROR {e}')

    open('feas_check3_output.txt', 'w').write('\n'.join(out) + '\n')
    say('\nwritten feas_check3_output.txt')
