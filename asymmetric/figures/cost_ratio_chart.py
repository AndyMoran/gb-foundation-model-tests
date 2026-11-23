"""Paired difference in cost-weighted error, Chronos-2 minus the weather regression, at each cost ratio, for all
half-hours and for the daily peak on the coldest tenth of days. Read from ../results.json."""
import json, os
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
HERE = os.path.dirname(os.path.abspath(__file__))
BLUE, ORANGE = "#2a78d6", "#c2410c"; TXT, TXT2, BG = "#0b0b0b", "#52514e", "#fcfcfb"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 13, "text.color": TXT, "axes.labelcolor": TXT2,
                     "xtick.color": TXT2, "ytick.color": TXT})
r = json.load(open(os.path.join(HERE, "..", "results.json")))
get = lambda s: next(c for c in r["comparisons"] if c["a"] == "chronos2_A" and c["b"] == "regression_weather" and c["set"] == s)
fig, ax = plt.subplots(figsize=(12, 6.8), dpi=100, facecolor=BG); ax.set_facecolor(BG)
kk = np.geomspace(0.5, 10, 200)
for s, col, name, dy in (("all", BLUE, "All half-hours", -1), ("peaks", ORANGE, "Daily peak, coldest tenth of days", 1)):
    c = get(s); dU, dO = c["Ua"] - c["Ub"], c["Oa"] - c["Ob"]
    ax.plot(kk, kk * dU + dO, color=col, lw=2.2)
    for row in c["rows"]:
        lo, hi = row["ci90"]; ax.plot([row["k"]] * 2, [lo, hi], color=col, lw=2.2, solid_capstyle="round", alpha=0.55)
        ax.plot(row["k"], row["diff"], "o", ms=9, color=col, mec=BG, mew=2)
    last = c["rows"][-1]
    ax.text(10.6, last["diff"], name.replace(", ", ",\n"), color=col, fontsize=12.5, fontweight="bold", va="center", ha="left")
ax.axhline(0, color=TXT2, lw=1, ls=(0, (4, 3)))
pk = get("peaks")["break_even"]["k_star"]
ax.annotate(f"Break-even ≈ {pk:.2f}", xy=(pk, 0), xytext=(0.52, 1300), fontsize=11.5, color=TXT2,
            arrowprops=dict(arrowstyle="-", color=TXT2, lw=0.8))
ax.set_xscale("log"); ks = [0.5, 1, 1.5, 2, 3, 5, 10]
ax.set_xticks(ks); ax.set_xticklabels([f"{k:g}" for k in ks]); ax.minorticks_off()
ax.set_xlim(0.45, 30)
ax.set_xlabel("Cost of a shortfall ÷ cost of an equal surplus", fontsize=12)
ax.set_ylabel("Chronos-2 minus regression, MW", fontsize=11.5)
ax.text(0.47, 5600, "↑ Chronos-2 worse", color=TXT2, fontsize=11, va="center")
ax.text(0.47, -900, "↓ Chronos-2 better", color=TXT2, fontsize=11, va="center")
ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:,.0f}".replace("-", "−")))
for sp in ["top", "right"]: ax.spines[sp].set_visible(False)
for sp in ["left", "bottom"]: ax.spines[sp].set_color("#d6d5d0")
ax.grid(axis="y", color="#ebeae6", lw=0.8); ax.set_axisbelow(True)
fig.suptitle("Chronos-2 wins over all half-hours at every tested cost ratio,\nbut sizes cold-day peaks worse once a shortfall costs twice a surplus",
             x=0.02, ha="left", fontsize=17, fontweight="bold", y=0.975)
fig.text(0.02, 0.015, "Cost-weighted error: a shortfall costs k times an equal surplus. Dots: Chronos-2's mean weighted error minus the weather regression's;\n"
         "bars: 90% intervals (7-day block bootstrap, 2,000 draws). 960-day GB day-ahead backtest, 16 March 2024 to 31 October 2026, which\n"
         "Chronos-2 may have seen in training. Peaks: each day's highest actual half-hour minus the highest forecast, on the 96 coldest days.",
         fontsize=10.5, color=TXT2, ha="left", va="bottom")
fig.subplots_adjust(left=0.09, right=0.985, top=0.855, bottom=0.2)
fig.savefig(os.path.join(HERE, "cost_ratio_chart.png"), facecolor=BG)
