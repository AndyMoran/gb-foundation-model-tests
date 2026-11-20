import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt, numpy as np
from matplotlib.ticker import FixedLocator, NullLocator, FixedFormatter
BLUE="#2a78d6"; ORANGE="#eb6834"; TXT="#0b0b0b"; TXT2="#52514e"; BG="#fcfcfb"; GRID="#ebeae6"
plt.rcParams.update({"font.family":"DejaVu Sans","font.size":13,"text.color":TXT,"axes.labelcolor":TXT2,"xtick.color":TXT2,"ytick.color":TXT})
rows=[("NESO day-ahead",0.649,0.721,"1.111","0.964–1.282",False),
      ("Chronos-2",0.895,0.944,"1.055","0.915–1.213",False),
      ("Weather regression",1.0,1.0,"","reference",False),
      ("LightGBM (main settings)",1.105,1.218,"1.102","0.988–1.217",False),
      ("TimesFM 2.5",1.554,2.024,"1.302","1.117–1.533",True)]
fig,ax=plt.subplots(figsize=(12,6.6),dpi=100,facecolor=BG); ax.set_facecolor(BG)
ax.set_xscale("log"); ax.set_xlim(0.55,2.3)
n=len(rows)
for i,(name,a,b,ts,ci,clear) in enumerate(rows):
    y=n-1-i
    if name=="Weather regression":
        ax.plot(1,y,"D",ms=9,color=TXT2,mec=BG,mew=2,zorder=3)
    else:
        ax.plot([a,b],[y,y],color="#b5b4ae",lw=2.5,solid_capstyle="round",zorder=1)
        ax.plot(a,y,"o",ms=11,color=BLUE,mec=BG,mew=2,zorder=3)
        ax.plot(b,y,"o",ms=11,color=ORANGE,mec=BG,mew=2,zorder=3)
    lab=f"{ts}  ({ci})" if ts else ci
    ax.text(1.03,y,lab,transform=ax.get_yaxis_transform(),va="center",ha="left",fontsize=12.5,
            color=TXT,fontweight="bold" if clear else "normal")
ax.text(1.03,1.0,"Tail shift (90% interval)",transform=ax.transAxes,ha="left",va="bottom",fontsize=12,color=TXT2,fontweight="bold")
ax.axvline(1,color=TXT2,lw=1,ls=(0,(4,3)),zorder=0)
ax.set_yticks(range(n)); ax.set_yticklabels([r[0] for r in rows][::-1])
ticks=[0.6,0.8,1.0,1.25,1.5,2.0]
ax.xaxis.set_major_locator(FixedLocator(ticks)); ax.xaxis.set_major_formatter(FixedFormatter([f"{t:g}" for t in ticks]))
ax.xaxis.set_minor_locator(NullLocator())
ax.set_ylim(-0.6,n-0.3)
ax.set_xlabel("Error relative to the weather regression (log scale)\n← lower error than the regression          higher error than the regression →",fontsize=11.5)
for s in ["top","right","left"]: ax.spines[s].set_visible(False)
ax.spines["bottom"].set_color("#d6d5d0"); ax.tick_params(axis="y",length=0)
ax.grid(axis="x",color=GRID,lw=0.8); ax.set_axisbelow(True)
# legend
from matplotlib.lines import Line2D
h=[Line2D([],[],marker="o",ls="",ms=11,color=BLUE,mec=BG,mew=2,label="Other days in the same months"),
   Line2D([],[],marker="o",ls="",ms=11,color=ORANGE,mec=BG,mew=2,label="Coldest 10% of days")]
fig.legend(handles=h,loc="upper left",bbox_to_anchor=(0.012,0.925),ncol=2,frameon=False,fontsize=12.5,handletextpad=0.3,columnspacing=1.5)
fig.suptitle("How forecast error changed on Britain's coldest demand days",x=0.02,ha="left",fontsize=18,fontweight="bold",y=0.985)
fig.text(0.02,0.015,"Each line's length is the tail shift: how much further behind the regression a forecaster fell on the coldest days. Tail-shift intervals are 90%\n(block bootstrap); only TimesFM's excludes 1. 96 coldest days, chosen from the day-ahead temperature forecast, in a 960-day backtest the\nfoundation models may have seen in training. Only the Chronos-2 and LightGBM tail shifts were fixed in advance. NESO is shown for reference.",fontsize=10.5,color=TXT2,ha="left",va="bottom")
fig.tight_layout(rect=(0,0.11,0.78,0.86))
fig.savefig("paired_chart.png",facecolor=BG)
