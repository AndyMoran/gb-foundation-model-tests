"""
Synthetic GB-like demand for tests only (never used for results): daily and weekly cycles, a seasonal swing,
bank-holiday dips, autocorrelated noise, on the real UK clock (so clock-change days have 46 and 50 periods).
"""
import numpy as np, pandas as pd
import common as C


def demand(start='2022-11-01', end='2026-11-03', seed=1, gaps=()):
    idx = pd.date_range(C.local(start, '00:00'), C.local(end, '00:00') - C.HALF_HOUR, freq='30min')
    loc = idx.tz_convert(C.UK)
    h = np.asarray(loc.hour + loc.minute / 60, float)
    doy = np.asarray(loc.dayofyear)
    rng = np.random.default_rng(seed)
    base = 28000 + 6000 * np.cos(2 * np.pi * (doy - 15) / 365.25)                  # winter high
    daily = 5000 * np.sin(np.pi * (h - 6) / 15).clip(0) + 2500 * np.exp(-((h - 18) ** 2) / 4)
    weekend = np.where(np.asarray(loc.dayofweek) >= 5, -3000, 0.0)
    noise = np.zeros(len(idx)); e = rng.normal(0, 250, len(idx))
    for i in range(1, len(idx)): noise[i] = 0.97 * noise[i - 1] + e[i]
    s = pd.Series(base + daily + weekend + noise, index=idx)
    for g in gaps: s.loc[g[0]:g[1]] = np.nan
    return s


def neso_publications(series, seed=2):
    """Synthetic Elexon-style publications: an 08:45 issue on D-1 for SP 17-48 of D, 09:15 for SP 1-16, and a
    later 11:45 revision (which must never be used), with a blank value now and then."""
    rng = np.random.default_rng(seed); rows = []
    days = pd.date_range(series.index.min().tz_convert(C.UK).normalize().tz_localize(None) + pd.Timedelta(days=2),
                         series.index.max().tz_convert(C.UK).normalize().tz_localize(None), freq='D')
    for D in days:
        prev = D - pd.Timedelta(days=1)
        for k, t in enumerate(C.target_starts(D)):
            truth = series.get(t, np.nan)
            first = C.local(prev, '08:45') if k >= 16 else C.local(prev, '09:15')
            v = truth + rng.normal(0, 600)
            rows.append((first, t, np.nan if rng.random() < 0.002 else v))
            rows.append((first - pd.Timedelta(hours=20), t, v + 50))                  # an earlier publication
            rows.append((C.local(prev, '11:45'), t, v + 9999))                       # after the cut-off: poison
    return pd.DataFrame(rows, columns=['publish_utc', 'start_utc', 'mw'])


def holidays():
    return {pd.Timestamp(d) for d in ['2023-01-02', '2023-04-07', '2023-04-10', '2023-05-01', '2023-12-25', '2023-12-26',
                                       '2024-01-01', '2024-03-29', '2024-04-01', '2024-05-06', '2024-12-25', '2024-12-26',
                                       '2025-01-01', '2025-04-18', '2025-04-21', '2025-05-05', '2025-12-25', '2025-12-26',
                                       '2026-01-01', '2026-04-03', '2026-04-06', '2026-05-04']}
