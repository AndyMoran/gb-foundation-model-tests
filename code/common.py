"""
Shared constants and time rules (plan: plan/PLAN.md, Sections 3 and 5).

Every time rule in the study lives here, so that the forecasters, the gate and the tests use one definition.
Times are handled as timezone-aware pandas Timestamps; UK local time is Europe/London.
"""
import os, hashlib
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA = os.path.join(ROOT, 'data')
UK = 'Europe/London'
HALF_HOUR = pd.Timedelta(minutes=30)

ISSUE_TIME = '09:30'            # UK local time on D-1: NESO's information cut-off (Section 3)
INPUT_CUTOFF = '08:30'          # UK local time on D-1: model and regression inputs end at or before this (one-hour buffer)
CONTEXT_LEN = 2688              # half-hours (8 weeks), the same for every model (Section 4.1)
FILL_MAX = 2                    # model contexts only: runs of at most 2 missing half-hours are filled (Section 2.4)
TRAIN_DAYS = 365                # regression training target days, D-366 .. D-2 (Section 4.2)

FULL_START, FULL_END = '2024-01-01', '2026-10-31'          # full window, target days inclusive (Section 5)
POST_RELEASE = {'timesfm25': '2025-09-15', 'chronos2': '2025-10-30', 'timestral': '2026-10-15'}
MODELS = ('timesfm25', 'chronos2', 'timestral')
M_THRESHOLD = 0.10              # minimum useful reduction against the regression (Section 8)

BOOT_B, BOOT_BLOCK = 2000, 7    # moving-block bootstrap over days (Section 6)
L1_SD_MW, L1_DRAWS, L1_FLAG = 300.0, 20, 0.05              # perturbation test (Section 7)

sha = lambda p: hashlib.sha256(open(p, 'rb').read()).hexdigest()


def local(day, hhmm):
    """The UTC Timestamp of a UK local clock time on a given day (a date string or Timestamp)."""
    return pd.Timestamp(f'{pd.Timestamp(day):%Y-%m-%d} {hhmm}').tz_localize(UK).tz_convert('UTC')


def day_bounds(day):
    """UTC start of day D (00:00 local) and of day D+1: the target half-hours start in [start, end)."""
    d = pd.Timestamp(day)
    return local(d, '00:00'), local(d + pd.Timedelta(days=1), '00:00')


def input_end(day):
    """End of the last input half-hour allowed for target day D: 08:30 UK local time on D-1."""
    return local(pd.Timestamp(day) - pd.Timedelta(days=1), INPUT_CUTOFF)


def issue_time(day):
    """NESO's information cut-off for target day D: 09:30 UK local time on D-1."""
    return local(pd.Timestamp(day) - pd.Timedelta(days=1), ISSUE_TIME)


def target_starts(day):
    """UTC start times of every settlement period of day D (46, 48 or 50)."""
    a, b = day_bounds(day)
    return pd.date_range(a, b - HALF_HOUR, freq='30min')


def horizon(day):
    """Steps from the input cut-off to the end of D, and the index of D's first period in the forecast."""
    a, b = day_bounds(day)
    end = input_end(day)
    return int((b - end) / HALF_HOUR), int((a - end) / HALF_HOUR)


def clock(ts):
    """UK local clock time 'HH:MM' of a UTC Timestamp."""
    return ts.tz_convert(UK).strftime('%H:%M')


def days(start=FULL_START, end=FULL_END):
    return pd.date_range(start, end, freq='D')
