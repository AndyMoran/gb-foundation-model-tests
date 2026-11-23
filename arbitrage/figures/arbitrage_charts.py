"""Two charts for the arbitrage note, read from ../results.json (all 960 days):
timing_chart.png       missed spread by forecaster, with 90% intervals
combination_chart.png  mean daily error of each forecaster averaged with NESO, minus NESO's own, with 90% intervals"""
import json, os
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
HERE = os.path.dirname(os.path.abspath(__file__))
BLUE, ORANGE, GREY = "#2a78d6", "#c2410c", "#8a8984"; TXT, TXT2, BG = "#0b0b0b", "#52514e", "#fcfcfb"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 13, "text.color": TXT, "axes.labelcolor": TXT2,
                     "xtick.color": TXT2, "ytick.color": TXT})
r = json.load(open(os.path.join(HERE, "..", "results.json")))["sets"]["all"]
NAMES = {"regression_weather": "Weather regression", "chronos2_A": "Chronos-2", "lgbm_v1": "LightGBM V1",
         "lightgbm_s1": "LightGBM S1", "timesfm25_weather_single_day": "TimesFM 2.5", "neso": "NESO day-ahead",
         "avg_chronos2_regression": "Average of Chronos-2\nand regression"}
COL = {"chronos2_A": BLUE, "timesfm25_weather_single_day": BLUE, "avg_chronos2_regression": ORANGE}
mw = lambda v: f"{v:,.0f}".replace("-", "−")


def dotplot(rows, fname, title, xlabel, foot, zero=False):
    fig, ax = plt.subplots(figsize=(12, 6.8), dpi=100, facecolor=BG); ax.set_facecolor(BG)
    for i, (c, v, lo, hi) in enumerate(rows):
        col = COL.get(c, GREY); bold = c in COL
        ax.plot([lo, hi], [i, i], color=col, lw=2.5, solid_capstyle="round")
        ax.plot(v, i, "o", ms=11, color=col, mec=BG, mew=2)
        ax.text(hi, i, f"   {mw(v)} MW ({mw(lo)} to {mw(hi)})", va="center", ha="left", fontsize=12,
                fontweight="bold" if bold else "normal")
    if zero: ax.axvline(0, color=TXT2, lw=1, ls=(0, (4, 3)))
    ax.set_yticks(range(len(rows))); ax.set_yticklabels([NAMES[x[0]] for x in rows])
    for t, x in zip(ax.get_yticklabels(), rows):
        if x[0] in COL: t.set_fontweight("bold")
    ax.invert_yaxis()
    lo = min(x[2] for x in rows); hi = max(x[3] for x in rows)
    ax.set_xlim(min(lo, 0) - 0.05 * (hi - lo), hi + 0.55 * (hi - lo))
    ax.set_xlabel(xlabel, fontsize=11.5)
    ax.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: mw(v)))
    for s in ["top", "right", "left"]: ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_color("#d6d5d0"); ax.tick_params(axis="y", length=0)
    ax.grid(axis="x", color="#ebeae6", lw=0.8); ax.set_axisbelow(True)
    fig.suptitle(title, x=0.02, ha="left", fontsize=17, fontweight="bold", y=0.975)
    fig.text(0.02, 0.015, foot, fontsize=10.5, color=TXT2, ha="left", va="bottom")
    fig.subplots_adjust(left=0.2, right=0.985, top=0.86, bottom=0.24)
    fig.savefig(os.path.join(HERE, fname), facecolor=BG)


A = r["A"]
rows = sorted(((c, A[c]["missed"]["value"], *A[c]["missed"]["ci90"]) for c in A), key=lambda x: x[1])
dotplot(rows, "timing_chart.png",
        "Picking a battery's hours: Chronos-2 missed far less of each\nday's demand spread than the weather regression",
        "Missed spread, MW a day (lower is better)",
        "Each day, take the forecast's four lowest and four highest half-hours (a two-hour battery). Missed spread: how much smaller the actual\n"
        "demand gap between those hours was than the gap between the day's actual four lowest and four highest. Dots: means over 960 days;\n"
        "lines: 90% intervals (7-day block bootstrap). Blue: foundation models; orange: a fixed 50:50 average. Demand, not prices. GB day-ahead\n"
        "backtest, 16 March 2024 to 31 October 2026, which the foundation models may have seen in training.")
B = r["B"]
rows = sorted(((c, B[c]["combination"]["minus_neso"]["value"], *B[c]["combination"]["minus_neso"]["ci90"]) for c in B), key=lambda x: x[1])
dotplot(rows, "combination_chart.png",
        "Does a forecast know something NESO's doesn't?\nAveraging with NESO helped only for Chronos-2 and the 50:50 average",
        "Error of (forecast + NESO) ÷ 2, minus NESO's own error, MW a day\n← averaging helps          averaging hurts →",
        "Mean daily absolute error of the half-hour average of each forecast and NESO's day-ahead forecast, minus NESO's alone (700 MW).\n"
        "Dots: means over 960 days; lines: 90% intervals (7-day block bootstrap). Blue: foundation models; orange: a fixed 50:50 average of\n"
        "Chronos-2 and the regression. GB day-ahead backtest, 16 March 2024 to 31 October 2026, which the foundation models may have seen in\n"
        "training. NESO's forecast uses information to 09:30 the day before; the models' inputs end at 08:30.", zero=True)
