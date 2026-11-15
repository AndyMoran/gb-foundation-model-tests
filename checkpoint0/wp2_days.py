"""WP2 sample days (checkpoint0/PLAN.md, WP2): 20 backtest days, 5 per meteorological season, drawn at random
within each season with seed 20261115, from the days in weather_study/results/forecasts.csv. Reads only dates."""
import os
import numpy as np, pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
days = pd.to_datetime(pd.Series(pd.read_csv(os.path.join(ROOT, 'weather_study', 'results', 'forecasts.csv'),
                                            usecols=['day'])['day'].unique()))
season = days.dt.month.map({12: 'DJF', 1: 'DJF', 2: 'DJF', 3: 'MAM', 4: 'MAM', 5: 'MAM',
                            6: 'JJA', 7: 'JJA', 8: 'JJA', 9: 'SON', 10: 'SON', 11: 'SON'})
rng = np.random.default_rng(20261115)
out = []
for s in ('DJF', 'MAM', 'JJA', 'SON'):
    pool = days[season == s].sort_values().to_numpy()
    out += [(str(pd.Timestamp(d).date()), s) for d in sorted(rng.choice(pool, 5, replace=False))]
pd.DataFrame(out, columns=['day', 'season']).to_csv(os.path.join(ROOT, 'checkpoint0', 'wp2_days.csv'), index=False)
print('\n'.join(f'{d} {s}' for d, s in out))
