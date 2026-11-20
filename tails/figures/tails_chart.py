import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
BLUE="#2a78d6"; GREY="#8a8984"; TXT="#0b0b0b"; TXT2="#52514e"; BG="#fcfcfb"
plt.rcParams.update({"font.family":"DejaVu Sans","font.size":13,"text.color":TXT,"axes.labelcolor":TXT2,"xtick.color":TXT2,"ytick.color":TXT})
# tail shift, narrow (same months), T1
ts=[("LightGBM (main settings)",1.102,0.988,1.217,False),
    ("NESO day-ahead",1.111,0.964,1.282,False),
    ("Chronos-2",1.055,0.915,1.213,True),
    ("TimesFM 2.5",1.302,1.117,1.533,True)]
# peak error, T1 (outturn peak minus forecast peak; + = under-forecast)
pk=[("Weather regression",-134,-357,91,False),
    ("NESO day-ahead",130,-51,328,False),
    ("LightGBM (main settings)",349,-65,741,False),
    ("Chronos-2",511,195,837,True),
    ("TimesFM 2.5",861,198,1539,True)]
fig,axes=plt.subplots(1,2,figsize=(12,6.6),dpi=100,facecolor=BG)
def panel(ax,rows,ref,title,xlabel,fmt):
    ax.set_facecolor(BG)
    for i,(n,v,lo,hi,fm) in enumerate(rows):
        c=BLUE if fm else GREY
        ax.plot([lo,hi],[i,i],color=c,lw=2.5,solid_capstyle="round")
        ax.plot(v,i,"o",ms=10,color=c,mec=BG,mew=2)
        ax.text(hi,i+0.22,"  "+fmt(v),va="bottom",ha="right",fontsize=12,color=TXT)
    ax.axvline(ref,color=TXT2,lw=1,ls=(0,(4,3)))
    ax.set_yticks(range(len(rows))); ax.set_yticklabels([r[0] for r in rows])
    for t,r in zip(ax.get_yticklabels(),rows):
        if r[4]: t.set_fontweight("bold")
    ax.set_ylim(-0.6,len(rows)-0.4)
    ax.set_title(title,loc="left",fontsize=14,fontweight="bold",pad=12)
    ax.set_xlabel(xlabel,fontsize=11.5)
    for s in ["top","right","left"]: ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_color("#d6d5d0"); ax.tick_params(axis="y",length=0)
    ax.grid(axis="x",color="#ebeae6",lw=0.8); ax.set_axisbelow(True)
panel(axes[0],ts,1,"Falling behind on cold days","Tail shift vs weather regression\n(above 1 = further behind than on other winter days)",lambda v:f"{v:.3f}")
panel(axes[1],pk,0,"Missing the cold-day peak","Daily peak under-forecast, MW\n(above 0 = peak forecast too low)",lambda v:f"{v:,.0f} MW")
fig.suptitle("What average error hid on GB's coldest 10% of days",x=0.02,ha="left",fontsize=18,fontweight="bold",y=0.985)
fig.text(0.02,0.015,"Dots: estimates. Lines: 90% intervals (block bootstrap). Blue: foundation models. 96 coldest days, chosen from the day-ahead temperature\nforecast, in a 960-day backtest the foundation models may have seen in training. Only the Chronos-2 and LightGBM tail shifts were fixed in advance.",fontsize=10.5,color=TXT2,ha="left",va="bottom")
fig.tight_layout(rect=(0,0.08,1,0.96),w_pad=4)
fig.savefig("tails_chart.png",facecolor=BG)
