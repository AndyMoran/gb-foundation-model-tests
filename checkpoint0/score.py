"""
Checkpoint 0 scoring (PLAN.md WP3, frozen at tag checkpoint0-plan). Committed before it runs; outputs committed after.

Reads, after checking each file's sha256:
    weather_study/results/forecasts.csv           (published backtest forecasts and outturn)
    weather_study/results/calendar_forecasts.csv  (E5: chronos2_A, timestral_A)
    checkpoint0/lightgbm_forecasts.csv            (lightgbm_default, lightgbm_s1, lightgbm_s2)
Writes checkpoint0/results.json and checkpoint0/results.md.

Daily mean absolute error over each day's half-hours; ratios of mean daily error; moving-block bootstrap of days (blocks
of 7, 2,000 draws, seed 20261115), 90% intervals. No p-values. Reading rule (PLAN.md section 6): a difference is
described only where the 90% interval of the ratio excludes 1. Headlines are chosen by PLAN.md section 7's rules.
Table 5 splits at 30 October 2025 (REVISIONS.md, 15 November 2026). Table 7 (cost, WP2) is reported separately.
"""
import hashlib, json, os, sys
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, 'next_study'))
import power_check as PC                                     # windows() only

FILES = {
    os.path.join(ROOT, 'weather_study', 'results', 'forecasts.csv'): 'b5f16561dcf1a26f8d7910bcca95cd137f677760c6f80153349034d4a85f7328',
    os.path.join(ROOT, 'weather_study', 'results', 'calendar_forecasts.csv'): '976e27ef28d0eef1ddf351c6557af9f771c308b94f389fe0f06b84ec86c8e2fe',
    os.path.join(HERE, 'lightgbm_forecasts.csv'): '812ffb251e7c4428ec1bb9f1e7467c51bc4f8ae55caf5b78b3fd0c840b6250cd',
}
SEED, B, BLOCK = 20261115, 2000, 7
RELEASE = '2025-10-30'
RANKED = ['chronos2_A', 'timesfm25_weather', 'regression_weather', 'lightgbm_default']
UNRANKED = ['timestral_A', 'timestral_weather']
NAMES = {'chronos2_A': 'Chronos-2 (calendar and weather)', 'timesfm25_weather': 'TimesFM 2.5 (weather)',
         'regression_weather': 'Weather regression', 'lightgbm_default': 'LightGBM, defaults',
         'lightgbm_s1': 'LightGBM, S1 settings', 'lightgbm_s2': 'LightGBM, S2 settings',
         'timestral_A': 'Timestral (calendar and weather; not ranked)', 'timestral_weather': 'Timestral (weather; not ranked)'}
SOURCES = {'lightgbm_s1': 'Misiurek et al. (Energies, 2026)', 'lightgbm_s2': 'Uzzaman et al. (Electricity, 2026)'}
SEASON = {12: 'DJF', 1: 'DJF', 2: 'DJF', 3: 'MAM', 4: 'MAM', 5: 'MAM', 6: 'JJA', 7: 'JJA', 8: 'JJA',
          9: 'SON', 10: 'SON', 11: 'SON'}


def sha(p):
    h = hashlib.sha256(); h.update(open(p, 'rb').read()); return h.hexdigest()


def boot_idx(n, rng):
    nb = int(np.ceil(n / BLOCK)); starts = rng.integers(0, n - BLOCK + 1, size=(B, nb))
    return (starts[:, :, None] + np.arange(BLOCK)).reshape(B, -1)[:, :n]


def ratio(a, b, bi):
    bs = a[bi].mean(1) / b[bi].mean(1)
    lo, hi = np.quantile(bs, [0.05, 0.95])
    return dict(ratio=round(float(a.mean() / b.mean()), 4), ci90=[round(float(lo), 4), round(float(hi), 4)],
                mw_a=round(float(a.mean()), 1), mw_b=round(float(b.mean()), 1),
                mw_diff=round(float(a.mean() - b.mean()), 1), n_days=int(len(a)))


def reading(r):
    lo, hi = r['ci90']
    return 'below' if hi < 1 else 'above' if lo > 1 else 'includes 1'


def load():
    for p, h in FILES.items():
        if sha(p) != h: sys.exit(f'{os.path.relpath(p, ROOT)} differs from the hash in score.py')
    f = pd.read_csv(list(FILES)[0]); cal = pd.read_csv(list(FILES)[1]); lg = pd.read_csv(list(FILES)[2])
    assert (f['start_utc'].to_numpy() == cal['start_utc'].to_numpy()).all(), 'calendar forecasts misaligned'
    for c in ('chronos2_A', 'timestral_A'): f[c] = cal[c].to_numpy()
    n0 = len(f)
    f = f.merge(lg.drop(columns='day'), on='start_utc', how='left', validate='one_to_one')
    assert len(f) == n0
    return f


def daily(f, cols):
    """Mean absolute error per day, on days where every listed forecaster has every half-hour."""
    e = f[['day']].copy()
    for c in cols: e[c] = (f['outturn'] - f[c]).abs()
    full = e.groupby('day')[cols].apply(lambda g: g.notna().all().all())
    dm = e.groupby('day')[cols].mean()
    return dm[full], sorted(set(dm.index) - set(dm[full].index))


def table_vs(dm, target, cols, rng):
    bi = boot_idx(len(dm), rng); b = dm[target].to_numpy()
    return {c: ratio(dm[c].to_numpy(), b, bi) for c in cols}


def main():
    f = load()
    lgbs = ['lightgbm_default', 'lightgbm_s1', 'lightgbm_s2']
    cols = RANKED + UNRANKED + lgbs[1:]
    dm, dropped = daily(f, cols)
    rng = np.random.default_rng(SEED)
    out = dict(note='checkpoint 0, exploratory and descriptive; plan frozen at tag checkpoint0-plan',
               n_days=len(dm), days_dropped=dropped, mean_daily_mae_mw={c: round(float(dm[c].mean()), 1) for c in cols})
    # Tables 1-3: every forecaster against each LightGBM setting; LightGBM against the regression
    out['t1_vs_lightgbm'] = {}; out['t2_lightgbm_vs_regression'] = {}
    for L in lgbs:
        others = [c for c in RANKED + UNRANKED if c != 'lightgbm_default']
        out['t1_vs_lightgbm'][L] = table_vs(dm, L, others, rng)
        bi = boot_idx(len(dm), rng)
        out['t2_lightgbm_vs_regression'][L] = ratio(dm[L].to_numpy(), dm['regression_weather'].to_numpy(), bi)
    # Table 4: by meteorological season, pooled across years
    seas = pd.to_datetime(dm.index).month.map(SEASON)
    out['t4_by_season'] = {}
    for s in ('DJF', 'MAM', 'JJA', 'SON'):
        d = dm[np.asarray(seas == s)]
        out['t4_by_season'][s] = dict(
            n_days=len(d),
            vs_lightgbm={L: table_vs(d, L, ['chronos2_A', 'timesfm25_weather', 'regression_weather'], rng) for L in lgbs},
            lightgbm_vs_regression={L: ratio(d[L].to_numpy(), d['regression_weather'].to_numpy(), boot_idx(len(d), rng))
                                    for L in lgbs})
    # Table 5: Chronos-2 against LightGBM (defaults), before and after release
    out['t5_release'] = {'split': RELEASE}
    for part, d in (('before', dm[dm.index < RELEASE]), ('after', dm[dm.index >= RELEASE])):
        out['t5_release'][part] = ratio(d['chronos2_A'].to_numpy(), d['lightgbm_default'].to_numpy(), boot_idx(len(d), rng))
    # Table 6: c and Chronos-2's edge over LightGBM (defaults), by power_check.windows, for gate G2
    W = PC.windows(list(dm.index))
    out['t6_for_g2'] = {}
    for w in ('summer 180 days (Apr-Sep)', 'winter 120 days (Dec-Mar)'):
        ds = [x for s in W[w] for x in s]; g = f[f['day'].isin(ds)]
        c = float(np.corrcoef(g['outturn'] - g['chronos2_A'], g['outturn'] - g['lightgbm_default'])[0, 1])
        d = dm.loc[ds]
        r = ratio(d['chronos2_A'].to_numpy(), d['lightgbm_default'].to_numpy(), boot_idx(len(d), rng))
        out['t6_for_g2'][w] = dict(c=round(c, 4), years=[len(s) for s in W[w]], **r)
    out['t7_cost'] = 'reported separately (WP2)'
    out['headline'] = headline(out)
    json.dump(out, open(os.path.join(HERE, 'results.json'), 'w'), indent=1)
    open(os.path.join(HERE, 'results.md'), 'w').write(markdown(out))
    print(markdown(out))


def headline(out):
    t1 = out['t1_vs_lightgbm']; t2 = out['t2_lightgbm_vs_regression']
    c = t1['lightgbm_default']['chronos2_A']; g = t2['lightgbm_default']
    pre = 'In a backtest the foundation models may have seen in training, '
    z = lambda r: f"{abs(1 - r['ratio']) * 100:.1f}%" if r['ratio'] < 1 else f"{(r['ratio'] - 1) * 100:.1f}%"
    zc = lambda r: f"{(1 - r['ratio']) * 100:.1f}%" if r['ratio'] < 1 else f"{(1 - 1 / r['ratio']) * 100:.1f}%"
    iv = lambda r: f"ratio {r['ratio']:.3f}, 90% interval {r['ci90'][0]:.3f}–{r['ci90'][1]:.3f}"
    s1 = {'below': pre + f"Chronos-2 forecast GB demand {zc(c)} more accurately than a LightGBM model with library defaults, on equal inputs.",
          'above': pre + f"a LightGBM model with library defaults forecast GB demand {zc(c)} more accurately than Chronos-2, on equal inputs.",
          'includes 1': pre + f"Chronos-2 and a LightGBM model with library defaults forecast GB demand about equally well, on equal inputs ({iv(c)})."}[reading(c)]
    s2 = {'below': f"The LightGBM model was {zc(g)} more accurate than a weather regression given the same information.",
          'above': f"The LightGBM model was {z(g)} less accurate than a weather regression given the same information: with library defaults, the trained tree model did not beat the linear one.",
          'includes 1': f"The LightGBM model and a weather regression given the same information were about equally accurate ({iv(g)})."}[reading(g)]
    extra = []
    for L in ('lightgbm_s1', 'lightgbm_s2'):
        cc, gg = t1[L]['chronos2_A'], t2[L]
        ch = []
        pc = {'below': 'Chronos-2 was more accurate than LightGBM', 'above': 'LightGBM was more accurate than Chronos-2',
              'includes 1': 'Chronos-2 and LightGBM were about equally accurate'}
        pg = {'below': 'LightGBM was more accurate than the regression', 'above': 'LightGBM was less accurate than the regression',
              'includes 1': 'LightGBM and the regression were about equally accurate'}
        if reading(cc) != reading(c): ch.append(f"{pc[reading(cc)]} ({iv(cc)})")
        if reading(gg) != reading(g): ch.append(f"{pg[reading(gg)]} ({iv(gg)})")
        if ch: extra.append(f"With the settings of {SOURCES[L]}, " + '; '.join(ch) + '.')
    return ' '.join([s1, s2] + extra + ['A live, preregistered test starts on 1 April 2027.'])


def markdown(out):
    L = ['# Checkpoint 0: results (exploratory, descriptive)', '',
         'Backtest days the foundation models may have seen in training. LightGBM is untuned. One series (GB INDO), day ahead. '
         'Ratios are mean daily error over that of the comparator; 90% intervals by moving-block bootstrap. '
         'A difference is described only where the interval excludes 1.', '',
         f"**Headline (PLAN.md §7):** {out['headline']}", '',
         f"Days scored: {out['n_days']}; dropped (a forecaster missing a half-hour): {len(out['days_dropped'])}.", '',
         '## Table 1: mean daily error, and ratio to LightGBM (defaults)', '',
         '| Forecaster | Mean daily error (MW) | Ratio to LightGBM | 90% interval |', '|---|---|---|---|']
    t = out['t1_vs_lightgbm']['lightgbm_default']
    for c in RANKED + UNRANKED:
        if c == 'lightgbm_default': L.append(f"| {NAMES[c]} | {out['mean_daily_mae_mw'][c]:,.0f} | 1 | — |"); continue
        r = t[c]; L.append(f"| {NAMES[c]} | {out['mean_daily_mae_mw'][c]:,.0f} | {r['ratio']:.3f} | {r['ci90'][0]:.3f}–{r['ci90'][1]:.3f} |")
    L += ['', '## Tables 2 and 3: LightGBM against the weather regression, and the sensitivity settings', '',
          '| LightGBM | Mean daily error (MW) | Ratio to regression | 90% interval | MW difference | Chronos-2 ratio to it | 90% interval |',
          '|---|---|---|---|---|---|---|']
    for k in ('lightgbm_default', 'lightgbm_s1', 'lightgbm_s2'):
        g = out['t2_lightgbm_vs_regression'][k]; c = out['t1_vs_lightgbm'][k]['chronos2_A']
        L.append(f"| {NAMES[k]} | {g['mw_a']:,.0f} | {g['ratio']:.3f} | {g['ci90'][0]:.3f}–{g['ci90'][1]:.3f} | {g['mw_diff']:+,.0f} | "
                 f"{c['ratio']:.3f} | {c['ci90'][0]:.3f}–{c['ci90'][1]:.3f} |")
    L += ['', '## Table 4: by meteorological season, pooled across years (LightGBM defaults)', '',
          '| Season | Days | Chronos-2 / LightGBM | TimesFM 2.5 / LightGBM | Regression / LightGBM | LightGBM / regression |',
          '|---|---|---|---|---|---|']
    for s, v in out['t4_by_season'].items():
        x = v['vs_lightgbm']['lightgbm_default']; g = v['lightgbm_vs_regression']['lightgbm_default']
        f = lambda r: f"{r['ratio']:.3f} ({r['ci90'][0]:.3f}–{r['ci90'][1]:.3f})"
        L.append(f"| {s} | {v['n_days']} | {f(x['chronos2_A'])} | {f(x['timesfm25_weather'])} | {f(x['regression_weather'])} | {f(g)} |")
    t5 = out['t5_release']
    L += ['', f"## Table 5: Chronos-2 / LightGBM (defaults), before and after {t5['split']}", '',
          '| Period | Days | Ratio | 90% interval |', '|---|---|---|---|']
    for p in ('before', 'after'):
        r = t5[p]; L.append(f"| {p} | {r['n_days']} | {r['ratio']:.3f} | {r['ci90'][0]:.3f}–{r['ci90'][1]:.3f} |")
    L += ['', '## Table 6: for gate G2 (Chronos-2 against LightGBM, defaults)', '',
          '| Window (years pooled) | Days | c | Ratio | 90% interval | Edge |', '|---|---|---|---|---|---|']
    for w, r in out['t6_for_g2'].items():
        L.append(f"| {w} | {r['n_days']} | {r['c']:.2f} | {r['ratio']:.3f} | {r['ci90'][0]:.3f}–{r['ci90'][1]:.3f} | {1 - r['ratio']:.1%} |")
    L += ['', 'Table 7 (cost) is reported separately, from WP2.', '']
    return '\n'.join(L)


if __name__ == '__main__':
    main()
