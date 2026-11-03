"""
The comparators that are not foundation models (plan Sections 4.2-4.3).

  Regression     the weekly-lag regression: one least-squares fit per local clock slot, re-estimated for each target
                 day D on the training target days D-366 .. D-2 that are complete
  seasonal naive the same local clock time on D-7

Lookups by clock time: a clock time absent on the looked-up day (spring clock change) or missing there is taken
from the same clock time one further week back (D-9 for the D-2 lag, D-14 for the D-7 lag). A clock time repeated
on the autumn clock-change day takes its first occurrence, and both occurrences of a target use the same slot model.

Information set: for target day D, only target days up to D-2 and lagged values from days up to D-2 are read, all
of which ended before 08:30 UK time on D-1. `forecast` asserts this for every day it touches.

`regression_independent` is a second implementation for the gate (plan Section 9, check 6): plain loops and normal
equations over the raw series, sharing no code with `Regression` beyond the time rules in common.py.
"""
import numpy as np, pandas as pd
import common as C

SLOTS = [f'{h:02d}:{m:02d}' for h in range(24) for m in (0, 30)]


def calendar(day, holidays):
    """Intercept, 6 day-of-week indicators (Monday base), bank holiday, 24 December - 2 January."""
    d = pd.Timestamp(day)
    xmas = (d.month == 12 and d.day >= 24) or (d.month == 1 and d.day <= 2)
    return [1.0] + [float(d.dayofweek == k) for k in range(1, 7)] + [float(d.normalize() in holidays), float(xmas)]


def complete_days(series):
    """Local days whose every settlement period (46, 48 or 50) is present."""
    s = series.dropna()
    count = pd.Series(1, index=s.index.tz_convert(C.UK).normalize().tz_localize(None)).groupby(level=0).sum()
    exp = pd.Series({d: len(C.target_starts(d)) for d in count.index})
    return set(count.index[count.values == exp.reindex(count.index).values])


class Regression:
    def __init__(self, series, holidays):
        s = series.dropna()
        loc = s.index.tz_convert(C.UK)
        df = pd.DataFrame({'day': loc.normalize().tz_localize(None), 'slot': loc.strftime('%H:%M'), 'mw': s.values})
        df = df.drop_duplicates(['day', 'slot'], keep='first')
        first, last = df.day.min(), df.day.max()
        self.days = pd.date_range(first, last, freq='D')
        self.pos = {d: i for i, d in enumerate(self.days)}
        self.Y = df.pivot(index='day', columns='slot', values='mw').reindex(index=self.days, columns=SLOTS).values
        lag = lambda k: np.vstack([np.full((k, 48), np.nan), self.Y[:-k]])
        self.L2 = np.where(np.isfinite(lag(2)), lag(2), lag(9))
        self.L7 = np.where(np.isfinite(lag(7)), lag(7), lag(14))
        self.CAL = np.array([calendar(d, holidays) for d in self.days])
        comp = complete_days(series)
        self.complete = np.array([d in comp for d in self.days])
        self.holidays = holidays

    def forecast(self, day):
        D = pd.Timestamp(day).normalize()
        cal = np.array(calendar(D, self.holidays))
        tr = [self.pos[d] for d in pd.date_range(D - pd.Timedelta(days=C.TRAIN_DAYS + 1), D - pd.Timedelta(days=2))
              if d in self.pos and self.complete[self.pos[d]]]
        assert all(self.days[i] <= D - pd.Timedelta(days=2) for i in tr), 'training day after D-2'
        # regressors for D itself: lags read from D-2 / D-9 and D-7 / D-14 only
        def at(off):
            d = D - pd.Timedelta(days=off)
            return self.Y[self.pos[d]] if d in self.pos else np.full(48, np.nan)
        x2 = np.where(np.isfinite(at(2)), at(2), at(9)); x7 = np.where(np.isfinite(at(7)), at(7), at(14))
        fc = np.full(48, np.nan)
        for j in range(48):
            X = np.column_stack([self.CAL[tr, :1], self.L2[tr, j], self.L7[tr, j], self.CAL[tr, 1:]])
            y = self.Y[tr, j]
            ok = np.isfinite(y) & np.isfinite(X).all(1)
            if ok.sum() < 20: continue
            b, *_ = np.linalg.lstsq(X[ok], y[ok], rcond=None)
            x0 = np.r_[cal[:1], x2[j], x7[j], cal[1:]]
            if np.isfinite(x0).all(): fc[j] = x0 @ b
        return np.array([fc[SLOTS.index(C.clock(t))] for t in C.target_starts(D)])

    def seasonal_naive(self, day):
        D = pd.Timestamp(day).normalize()
        def at(off):
            d = D - pd.Timedelta(days=off)
            return self.Y[self.pos[d]] if d in self.pos else np.full(48, np.nan)
        x7 = np.where(np.isfinite(at(7)), at(7), at(14))
        return np.array([x7[SLOTS.index(C.clock(t))] for t in C.target_starts(D)])


def regression_independent(series, day, holidays):
    """Second implementation for the gate: loops over raw half-hours and solves the normal equations."""
    D = pd.Timestamp(day).normalize()
    s = series[series.index + C.HALF_HOUR <= C.input_end(D)].dropna()
    by, count = {}, {}
    for ts, v in zip(s.index, s.values):
        L = ts.tz_convert(C.UK); d = L.normalize().tz_localize(None); k = (d, L.strftime('%H:%M'))
        if k not in by: by[k] = v
        count[d] = count.get(d, 0) + 1
    def look(d, slot, lag):
        for extra in (0, 7):
            k = (d - pd.Timedelta(days=lag + extra), slot)
            if k in by: return by[k]
        return np.nan
    out = []
    for t in C.target_starts(D):
        slot = C.clock(t); X, y = [], []
        for td in pd.date_range(D - pd.Timedelta(days=366), D - pd.Timedelta(days=2), freq='D'):
            if count.get(td, 0) != len(C.target_starts(td)) or (td, slot) not in by: continue
            cal = calendar(td, holidays); r = [cal[0], look(td, slot, 2), look(td, slot, 7)] + cal[1:]
            if all(np.isfinite(r)): X.append(r); y.append(by[(td, slot)])
        X, y = np.array(X), np.array(y)
        b = np.linalg.solve(X.T @ X, X.T @ y)
        cal = calendar(D, holidays)
        out.append(float(np.array([cal[0], look(D, slot, 2), look(D, slot, 7)] + cal[1:]) @ b))
    return np.array(out)
