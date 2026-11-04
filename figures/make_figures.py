"""
Figures for RESULTS.md, drawn from results/attempt2/results.json only. No new analysis: every number plotted is in
that file. Run from the repository root:  python figures/make_figures.py
"""
import os, json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
R = json.load(open(os.path.join(ROOT, 'results', 'attempt2', 'results.json')))['results']
OUT = os.path.join(ROOT, 'figures')

SURFACE, INK, INK2, MUTED, GRID = '#fcfcfb', '#0b0b0b', '#52514e', '#8a8984', '#e4e3df'
MODELS = ['timesfm25', 'chronos2', 'timestral']
NAME = {'timesfm25': 'TimesFM 2.5', 'chronos2': 'Chronos-2', 'timestral': 'Timestral',
        'regression': 'Regression', 'neso': 'NESO', 'naive': 'Seasonal naive'}
COLOUR = {'timesfm25': '#2a78d6', 'chronos2': '#eb6834', 'timestral': '#1baf7a',
          'regression': INK2, 'neso': INK, 'naive': '#b5b4ae'}
SOURCE = 'Source: Elexon BMRS and NESO data; results/attempt2. Andy Moran (Heaviside Analytics).'

plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 10, 'axes.edgecolor': GRID, 'axes.labelcolor': INK2,
                     'xtick.color': INK2, 'ytick.color': INK2, 'axes.facecolor': SURFACE, 'figure.facecolor': SURFACE,
                     'savefig.facecolor': SURFACE, 'axes.spines.top': False, 'axes.spines.right': False})


def frame(fig, title, subtitle, note=SOURCE, sub_y=0.905):
    fig.text(0.02, 0.97, title, fontsize=13, fontweight='bold', color=INK, va='top')
    fig.text(0.02, sub_y, subtitle, fontsize=10, color=INK2, va='top')
    fig.text(0.02, 0.015, note, fontsize=7.5, color=MUTED, va='bottom')


def save(fig, name):
    fig.savefig(os.path.join(OUT, name), dpi=200); plt.close(fig); print('wrote', name)


# 1. The headline: ratio to the regression, with 90% intervals, against 1.0 and the 10% threshold
H = R['primary_tests_holm']
fig, ax = plt.subplots(figsize=(9.2, 3.9)); fig.subplots_adjust(left=0.14, right=0.70, top=0.72, bottom=0.2)
for x, lab in ((1.0, 'No better than\nthe regression'), (0.90, '10% better:\nthe threshold')):
    ax.axvline(x, color=MUTED, lw=1, ls='--', zorder=1)
    ax.text(x, 3.05, lab, ha='center', va='bottom', fontsize=8, color=INK2)
ax.text(1.03, 3.05, 'Holm-adjusted decisions\n(6 tests, 5% family-wise)', transform=ax.get_yaxis_transform(),
        ha='left', va='bottom', fontsize=8, color=INK2)
for i, m in enumerate(reversed(MODELS)):
    c = R['primary'][m]; lo, hi = c['ci90_descriptive']; y = i + 0.5
    ax.plot([lo, hi], [y, y], color=COLOUR[m], lw=2.5, solid_capstyle='butt', zorder=2)
    for e in (lo, hi): ax.plot([e, e], [y - 0.09, y + 0.09], color=COLOUR[m], lw=1.5, zorder=2)
    ax.plot(c['ratio'], y, 'o', ms=9, color=COLOUR[m], mec=SURFACE, mew=2, zorder=3)
    ax.text(c['ratio'], y + 0.17, f"{c['ratio']:.3f}", ha='center', va='bottom', fontsize=9, color=INK, fontweight='bold')
    ax.text(lo, y - 0.15, f'{lo:.3f}', ha='center', va='top', fontsize=8, color=INK2)
    ax.text(hi, y - 0.15, f'{hi:.3f}', ha='center', va='top', fontsize=8, color=INK2)
    better = 'Yes' if H[f'{m}_improvement']['rejected'] else 'No'
    ten = 'yes' if H[f'{m}_meaningful']['rejected'] else 'not shown'
    ax.text(1.03, y, f'Better at all: {better}\nBy 10%: {ten}', transform=ax.get_yaxis_transform(),
            ha='left', va='center', fontsize=8.5, color=INK)
ax.set_yticks([0.5, 1.5, 2.5]); ax.set_yticklabels([NAME[m] for m in reversed(MODELS)], fontsize=10, color=INK)
ax.tick_params(axis='y', length=0); ax.spines['left'].set_visible(False)
ax.set_xlim(0.87, 1.055); ax.set_ylim(0, 3.0); ax.set_xlabel('Error ratio to the weekly-lag regression (lower is better)')
ax.grid(axis='x', color=GRID, lw=0.6, zorder=0)
frame(fig, 'Two models beat the regression; neither was shown to reach 10%',
      "Day-ahead GB demand, 1,035 days, 2024–2026. Dot: ratio of mean daily errors. Bar: 90% interval (descriptive).\n"
      "Chronos-2's lower bound sits 0.002 above 0.90, within the bootstrap's seed-to-seed variation; Timestral's crosses it.")
save(fig, 'fig1_ratios.png')


# 2. The error ladder: mean daily error for every forecaster
order = ['naive', 'timesfm25', 'regression', 'chronos2', 'timestral', 'neso']
mae = {m: R['primary'][m]['mae_model'] for m in MODELS}
mae['regression'] = R['primary']['timesfm25']['mae_comparator']
mae['neso'] = R['secondary']['timesfm25_vs_neso_full']['mae_comparator']
mae['naive'] = R['exploratory']['timesfm25_vs_naive']['mae_comparator']
fig, ax = plt.subplots(figsize=(8, 3.8)); fig.subplots_adjust(left=0.18, right=0.95, top=0.76, bottom=0.18)
for i, m in enumerate(reversed(order)):
    ax.barh(i, mae[m], height=0.62, color=COLOUR[m], edgecolor=SURFACE, lw=2, zorder=2)
    ax.text(mae[m] + 25, i, f'{mae[m]:,.0f} MW', va='center', fontsize=9, color=INK)
ax.set_yticks(range(len(order))); ax.set_yticklabels([NAME[m] for m in reversed(order)], fontsize=10, color=INK)
ax.tick_params(axis='y', length=0); ax.spines['left'].set_visible(False)
ax.set_xlim(0, 2450); ax.set_xlabel('Mean daily absolute error (MW)'); ax.grid(axis='x', color=GRID, lw=0.6, zorder=0)
frame(fig, "NESO's forecast has less than half the error of every model",
      'Mean daily absolute error, day-ahead GB demand, 2024–2026. NESO uses weather; the others do not.')
save(fig, 'fig2_error_ladder.png')


# 3. Error by time of day (exploratory): levels, and each model's difference from the regression
tod = R['exploratory']['mae_by_time_of_day']
slots = [f'{h:02d}:{m:02d}' for h in range(24) for m in (0, 30)]
fig, (ax, bx) = plt.subplots(2, 1, figsize=(9, 7.2), sharex=True, gridspec_kw={'height_ratios': [1.25, 1]})
fig.subplots_adjust(left=0.1, right=0.97, top=0.855, bottom=0.11, hspace=0.18)
lines = ['regression', 'timesfm25', 'chronos2', 'timestral', 'neso']
for m in lines:
    ax.plot(range(48), [tod[m][s_] for s_ in slots], color=COLOUR[m], lw=2, ls='--' if m == 'regression' else '-',
            zorder=3 if m in MODELS else 2)
ax.set_ylim(0, 2850); ax.set_ylabel('Mean absolute error (MW)'); ax.grid(axis='y', color=GRID, lw=0.6, zorder=0)
ax.legend([plt.Line2D([], [], color=COLOUR[m], lw=2, ls='--' if m == 'regression' else '-') for m in lines],
          [NAME[m] for m in lines], ncol=5, frameon=False, fontsize=8.5, loc='upper left', bbox_to_anchor=(0, 1.02))
ax.text(0.0, 1.07, 'Error by time of day', transform=ax.transAxes, fontsize=9.5, color=INK, fontweight='bold')
bx.axhline(0, color=INK2, lw=1, ls='--', zorder=1)
for m in MODELS:
    bx.plot(range(48), [tod[m][s_] - tod['regression'][s_] for s_ in slots], color=COLOUR[m], lw=2, zorder=3)
bx.set_ylabel('Model minus regression (MW)'); bx.grid(axis='y', color=GRID, lw=0.6, zorder=0)
bx.text(0.0, 1.03, 'Difference from the regression (below the dashed line: the model gains)', transform=bx.transAxes,
        fontsize=9.5, color=INK, fontweight='bold')
bx.set_xticks(range(0, 48, 6)); bx.set_xticklabels(slots[::6]); bx.set_xlim(0, 47)
bx.set_xlabel('UK clock time (start of half-hour)')
frame(fig, "The models' edge is largest from midnight to late morning and fades by evening",
      'Mean absolute error by half-hour of the target day, 2024–2026. Exploratory: not tested; no intervals shown.',
      sub_y=0.935)
save(fig, 'fig3_time_of_day.png')


# 4. Where the models win and lose: season and bank holidays (exploratory), with NESO for comparison
season = R['exploratory']['mae_by_season']; hol = R['exploratory']['mae_by_holiday']
rows = [('Winter', season, 'winter'), ('Spring', season, 'spring'), ('Summer', season, 'summer'),
        ('Autumn', season, 'autumn'), (None, None, None), ('Bank holidays', hol, 'bank holiday'), ('Other days', hol, 'other day')]
who = ['regression', 'timesfm25', 'chronos2', 'timestral', 'neso']
MARK = {'regression': 'D', 'neso': 's'}
fig, ax = plt.subplots(figsize=(8.4, 5.0)); fig.subplots_adjust(left=0.16, right=0.96, top=0.76, bottom=0.17)
labels, ys = [], []
for i, (lab, tab, key) in enumerate(rows):
    y = len(rows) - 1 - i
    if lab is None: continue
    labels.append(lab); ys.append(y)
    for k, m in enumerate(who):     # offset within the row (the category axis) so no marker hides another;
        dy = 0.30 - 0.15 * k        # the values, on the horizontal axis, are plotted exactly
        if m in MODELS:
            ax.plot([tab['regression'][key], tab[m][key]], [y + dy, y + dy], color=COLOUR[m], lw=1.2, alpha=0.45, zorder=1)
        ax.plot(tab[m][key], y + dy, MARK.get(m, 'o'), ms=7, color=COLOUR[m], mec=SURFACE, mew=1.2, zorder=3)
ax.set_yticks(ys); ax.set_yticklabels(labels, fontsize=10, color=INK); ax.tick_params(axis='y', length=0)
ax.spines['left'].set_visible(False); ax.set_xlim(500, 2700); ax.set_ylim(-0.6, 7.0)
ax.set_xlabel('Mean daily absolute error (MW)'); ax.grid(axis='x', color=GRID, lw=0.6, zorder=0)
ax.legend([plt.Line2D([], [], marker=MARK.get(m, 'o'), ls='', ms=8, color=COLOUR[m]) for m in who],
          [NAME[m] for m in who], ncol=5, frameon=False, fontsize=9, loc='upper left', bbox_to_anchor=(0, 1.1))
frame(fig, 'The models gain in winter and lose on bank holidays',
      'Mean daily error by season and day type, 2024–2026. Thin lines run from the regression. Exploratory.\n'
      'Markers are offset within each row for legibility only; the error values are on the horizontal axis.')
save(fig, 'fig4_season_holiday.png')
