"""
Statistics (plan Section 6).

  daily MAE   mean absolute error in MW over the settlement periods of each target day
  ratio       mean daily MAE of the model / mean daily MAE of the comparator, over the window's days
  bootstrap   moving-block bootstrap over days (block 7, 2,000 draws); the same resampled days for both forecasters
  p-values    one-sided, percentile method: p(theta) = share of bootstrap ratios >= theta, for H0: ratio >= theta
  Holm        across the six primary tests (improvement and 10% improvement, for three models)
  intervals   90% percentile intervals, labelled descriptive (not adjusted for multiplicity)
"""
import numpy as np


def daily_mae(y, f):
    return float(np.mean(np.abs(np.asarray(y) - np.asarray(f))))


def block_indices(n, rng, block):
    starts = rng.integers(0, n - block + 1, size=int(np.ceil(n / block)))
    return np.concatenate([np.arange(s, s + block) for s in starts])[:n]


def boot_ratios(mae_model, mae_comp, B, block, seed):
    a, b = np.asarray(mae_model), np.asarray(mae_comp); n = len(a)
    rng = np.random.default_rng(seed)
    out = np.empty(B)
    for k in range(B):
        i = block_indices(n, rng, block)
        out[k] = a[i].mean() / b[i].mean()
    return out


def compare(mae_model, mae_comp, B, block, seed, thetas=(1.0,)):
    a, b = np.asarray(mae_model, float), np.asarray(mae_comp, float)
    r = a.mean() / b.mean()
    bs = boot_ratios(a, b, B, block, seed)
    lo, hi = np.quantile(bs, [0.05, 0.95])
    return dict(ratio=float(r), ci90_descriptive=[float(lo), float(hi)], n_days=int(len(a)),
                p_one_sided={f'{t:.2f}': float(np.mean(bs >= t)) for t in thetas},
                mae_model=float(a.mean()), mae_comparator=float(b.mean()))


def holm(pvals, alpha=0.05):
    """pvals: dict name -> p. Returns dict name -> (adjusted p, rejected)."""
    names = sorted(pvals, key=pvals.get); m = len(names); adj = {}; running = 0.0
    for k, n in enumerate(names):
        running = max(running, min(1.0, (m - k) * pvals[n]))
        adj[n] = running
    return {n: dict(p=pvals[n], p_holm=adj[n], rejected=bool(adj[n] < alpha)) for n in pvals}
