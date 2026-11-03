"""
The three foundation models, zero-shot (plan Section 4.1), and a stand-in for pipeline tests.

Every forecasting argument is written out here and recorded with the results; nothing relies on a library default.
Each wrapper takes a batch of equal-length contexts (CONTEXT_LEN half-hours) and one horizon, and returns the
median (0.5 quantile) for every step, as a (batch, horizon) array. The run groups target days by horizon (77, 79
or 81 steps), so every request is exactly the horizon needed.

Pinned versions and revisions are recorded in plan/PLAN_LOCK.json at freezing; the run checks the weights hashes.
"""
import numpy as np
import common as C

REVISIONS = {
    'timesfm25': ('google/timesfm-2.5-200m-pytorch', '1d952420fba87f3c6dee4f240de0f1a0fbc790e3'),
    'chronos2': ('amazon/chronos-2', '29ec3766d36d6f73f0696f85560a422f50e8498c'),
    'timestral': ('mistralai/Timestral-209M', '9874d252ab0aae16f7f7c999f98f98d6ad7d8365'),
}
SETTINGS = {
    'timesfm25': dict(max_context=C.CONTEXT_LEN, max_horizon=128, normalize_inputs=True,
                      use_continuous_quantile_head=True, force_flip_invariance=True, infer_is_positive=True,
                      fix_quantile_crossing=True, return_backcast=False, per_core_batch_size=32),
    'chronos2': dict(context_length=C.CONTEXT_LEN, cross_learning=False, limit_prediction_length=False,
                     batch_size=64, device_map='cpu', quantile_levels=[0.5]),
    'timestral': dict(symmetric_averaging=True, clip_nonnegative=True, device='cpu', quantile=0.5),
}


class StandIn:
    """Pipeline tests only, never reported: repeats the last week, shifted to the requested horizon."""
    name = 'stand-in'
    def forecast(self, contexts, h):
        X = np.asarray(contexts, float); week = 336                # step k is the half-hour one week after X[-336 + k]
        level = (X[:, -1] - X[:, -1 - week])[:, None]              # shifted by the latest week-on-week change
        return X[:, -week:-week + h] + level


class TimesFM25:
    name = 'timesfm25'
    def __init__(self):
        import timesfm
        repo, rev = REVISIONS[self.name]
        self.m = timesfm.TimesFM_2p5_200M_torch.from_pretrained(repo, revision=rev)
        self.m.compile(timesfm.ForecastConfig(**SETTINGS[self.name]))
    def forecast(self, contexts, h):
        point, quant = self.m.forecast(horizon=h, inputs=[np.asarray(x, float) for x in contexts])
        quant = np.asarray(quant)
        if quant.shape[1] != h: raise ValueError(f'TimesFM 2.5 returned {quant.shape[1]} steps, expected {h}')
        return quant[:, :, 5].astype(float)          # index 0 = mean, 1..9 = quantiles 0.1..0.9, so 5 = median


class Chronos2:
    name = 'chronos2'
    def __init__(self):
        from chronos import Chronos2Pipeline
        repo, rev = REVISIONS[self.name]; s = SETTINGS[self.name]
        self.p = Chronos2Pipeline.from_pretrained(repo, revision=rev, device_map=s['device_map'])
    def forecast(self, contexts, h):
        s = SETTINGS[self.name]
        q, _ = self.p.predict_quantiles([np.asarray(x, float) for x in contexts], prediction_length=h,
                                        quantile_levels=s['quantile_levels'], batch_size=s['batch_size'],
                                        context_length=s['context_length'], cross_learning=s['cross_learning'],
                                        limit_prediction_length=s['limit_prediction_length'])
        out = np.stack([np.asarray(t)[0, :, 0] for t in q]).astype(float)
        if out.shape[1] != h: raise ValueError(f'Chronos-2 returned {out.shape[1]} steps, expected {h}')
        return out


class Timestral:
    name = 'timestral'
    def __init__(self):
        from timestral import TimestralForecaster
        repo, rev = REVISIONS[self.name]
        self.f = TimestralForecaster.from_pretrained(repo, revision=rev, device=SETTINGS[self.name]['device'])
    def forecast(self, contexts, h):
        s = SETTINGS[self.name]
        X = np.asarray(contexts, np.float32)[:, None, :]
        out = self.f.forecast(X, prediction_length=h, symmetric_averaging=s['symmetric_averaging'],
                              clip_nonnegative=s['clip_nonnegative'])
        med = out.quantile(s['quantile']).detach().cpu().numpy()[:, 0, :].astype(float)
        if med.shape[1] != h: raise ValueError(f'Timestral returned {med.shape[1]} steps, expected {h}')
        return med


def get(name):
    return {'stand-in': StandIn, 'timesfm25': TimesFM25, 'chronos2': Chronos2, 'timestral': Timestral}[name]()


def versions():
    out = {}
    for mod, pkg in (('timesfm', 'timesfm'), ('chronos', 'chronos-forecasting'), ('timestral', 'timestral'),
                     ('torch', 'torch'), ('numpy', 'numpy'), ('pandas', 'pandas')):
        try:
            from importlib.metadata import version
            out[pkg] = version(pkg)
        except Exception:
            out[pkg] = None
    return out
