"""
What each forecaster may know for target day D (plan Sections 2-4).

  series            INDO as a continuous half-hourly series indexed by UTC period start
  context(...)      the model input: the last CONTEXT_LEN half-hours ending at or before 08:30 UK time on D-1
  neso_forecast(..) NESO's day-ahead forecast as it stood at 09:30 UK time on D-1, from Elexon publications
"""
import numpy as np, pandas as pd
import common as C


def load_indo(path):
    """INDO from fetch.py's CSV: start_utc, settlement_date, settlement_period, mw. Returns a regular UTC series
    (missing half-hours as NaN) and the raw frame."""
    df = pd.read_csv(path)
    df['start_utc'] = pd.to_datetime(df['start_utc'], utc=True)
    df = df.drop_duplicates('start_utc', keep='first').sort_values('start_utc')
    s = df.set_index('start_utc')['mw'].astype(float)
    full = pd.date_range(s.index.min(), s.index.max(), freq='30min')
    return s.reindex(full), df


def context(series, day, n=C.CONTEXT_LEN, fill_max=C.FILL_MAX):
    """The last n half-hours of `series` ending at or before the input cut-off for day D.

    Gap rule (plan Section 2.4): a run of at most `fill_max` missing half-hours is filled by a straight line between
    its two neighbours, but only when the later neighbour is itself inside the context (so nothing after the cut-off
    is used). Longer runs, or a run at the end of the context, raise ValueError and the day is excluded. Fills apply
    to model contexts only; targets, the regression and NESO are never filled.
    Returns (values, index, filled), where `filled` lists the UTC starts of the filled half-hours."""
    end = C.input_end(day)                                  # end of the last allowed period
    last_start = end - C.HALF_HOUR
    idx = pd.date_range(last_start - (n - 1) * C.HALF_HOUR, last_start, freq='30min')
    v = series.reindex(idx).astype(float)
    filled = []
    if v.isna().any():
        miss = v.isna().values; i = 0
        while i < n:
            if not miss[i]: i += 1; continue
            j = i
            while j < n and miss[j]: j += 1               # missing run is i .. j-1
            a = idx[i] - C.HALF_HOUR; left = series.get(a, np.nan)
            ok = (j - i) <= fill_max and j < n and np.isfinite(left)
            if not ok:
                raise ValueError(f'context for {pd.Timestamp(day):%Y-%m-%d} has {int(v.isna().sum())} missing half-hours '
                                 f'(a run of {j - i} from {idx[i]:%Y-%m-%d %H:%M} UTC cannot be filled)')
            right = v.iloc[j]; k = j - i
            v.iloc[i:j] = left + (right - left) * np.arange(1, k + 1) / (k + 1)
            filled += list(idx[i:j]); i = j
    assert idx[-1] + C.HALF_HOUR <= end
    return v.values.astype(float), idx, filled


def targets(series, day):
    """Outturn for every settlement period of D, or ValueError if any is missing."""
    idx = C.target_starts(day)
    v = series.reindex(idx)
    if v.isna().any():
        raise ValueError(f'outturn for {pd.Timestamp(day):%Y-%m-%d} has {int(v.isna().sum())} missing half-hours')
    return v.values.astype(float), idx


def load_neso(path):
    """Elexon day-ahead forecast publications from fetch.py: publish_utc, start_utc, mw (blank = NaN)."""
    df = pd.read_csv(path)
    df['publish_utc'] = pd.to_datetime(df['publish_utc'], utc=True)
    df['start_utc'] = pd.to_datetime(df['start_utc'], utc=True)
    return df.sort_values(['start_utc', 'publish_utc'])


def neso_forecast(pubs, day):
    """For each period of D: the latest publication at or before 09:30 UK time on D-1; a blank value is replaced
    by that period's most recent earlier non-blank publication. Returns (values, publish times); ValueError if
    any period has no usable publication."""
    idx = C.target_starts(day); cut = C.issue_time(day)
    p = pubs[(pubs.start_utc >= idx[0]) & (pubs.start_utc <= idx[-1]) & (pubs.publish_utc <= cut)]
    p = p.dropna(subset=['mw'])
    last = p.groupby('start_utc').tail(1).set_index('start_utc')
    last = last.reindex(idx)
    if last['mw'].isna().any():
        raise ValueError(f'NESO forecast for {pd.Timestamp(day):%Y-%m-%d} lacks {int(last.mw.isna().sum())} periods')
    assert (last.publish_utc <= cut).all()
    return last['mw'].values.astype(float), last['publish_utc'].values
