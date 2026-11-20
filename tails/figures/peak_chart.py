import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
BLUE="#2a78d6"; GREY="#8a8984"; TXT="#0b0b0b"; TXT2="#52514e"; BG="#fcfcfb"
plt.rcParams.update({"font.family":"DejaVu Sans","font.size":13,"text.color":TXT,"axes.labelcolor":TXT2,"xtick.color":TXT2,"ytick.color":TXT})
# Mean daily peak error on T1 (outturn peak minus forecast peak; above 0 = forecast peak too low), from RESULTS.md
pk=[("Weather regression",-134,-357,91,False),
    ("NESO day-ahead",130,-51,328,False),
    ("LightGBM (main settings)",349,-65,741,False),
    ("Chronos-2",511,195,837,True),
    ("TimesFM 2.5",861,198,1539,True)]
fig,ax=plt.subplots(figsize=(12,6.6),dpi=100,facecolor=BG); ax.set_facecolor(BG)
for i,(n,v,lo,hi,fm) in enumerate(pk):
    c=BLUE if fm else GREY
    ax.plot([lo,hi],[i,i],color=c,lw=2.5,solid_capstyle="round")
    ax.plot(v,i,"o",ms=11,color=c,mec=BG,mew=2)
    ax.text(hi,i,f"   {v:,.0f} MW ({lo:,.0f} to {hi:,.0f})".replace("-","−"),va="center",ha="left",fontsize=12.5,
            color=TXT,fontweight="bold" if fm else "normal")
ax.axvline(0,color=TXT2,lw=1,ls=(0,(4,3)))
ax.set_yticks(range(len(pk))); ax.set_yticklabels([r[0] for r in pk])
for t,r in zip(ax.get_yticklabels(),pk):
    if r[4]: t.set_fontweight("bold")
ax.set_xlim(-450,2350); ax.set_ylim(-0.6,len(pk)-0.4)
ax.set_xticks([-250,0,250,500,750,1000,1250,1500])
ax.set_xlabel("Mean daily peak under-forecast on the coldest days, MW\n← forecast peak too high          forecast peak too low →",fontsize=11.5)
for s in ["top","right","left"]: ax.spines[s].set_visible(False)
ax.spines["bottom"].set_color("#d6d5d0"); ax.tick_params(axis="y",length=0)
ax.grid(axis="x",color="#ebeae6",lw=0.8); ax.set_axisbelow(True)
fig.suptitle("On the coldest days, the foundation models set their peaks too low",x=0.02,ha="left",fontsize=18,fontweight="bold",y=0.975)
fig.text(0.02,0.015,"Peak error: each day's highest actual half-hour minus the highest forecast half-hour, averaged over the 96 coldest days. Dots: estimates;\nlines and brackets: 90% intervals (block bootstrap). Blue: foundation models. Days chosen from the day-ahead temperature forecast, in a\n960-day backtest the foundation models may have seen in training. These peak results were not fixed in advance. NESO is shown for reference.",fontsize=10.5,color=TXT2,ha="left",va="bottom")
fig.tight_layout(rect=(0,0.11,1,0.92))
fig.savefig("peak_chart.png",facecolor=BG)
