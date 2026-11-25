"""Figures for the revised RDQ paper (v2). Static PNGs for a PDF; the plotted values are in tables/series_*.csv.

Palette: categorical slots 1-2 of the reference palette (#2a78d6 blue, #eb6834 orange), the pair validated for the
SLOOS v3 figures with validate_palette.js (--mode light --pairs all: all checks pass); the middle group and the 2025
bar use neutral ink, not a third hue. Identity never rests on colour alone: lines carry direct labels, and the bar
groups differ by fill style as well as colour. Text uses ink tokens, not series colours.
Run: python make_figures.py   (after make_tables.py)
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.patches import Patch

HERE = Path(__file__).resolve().parent
T = HERE / "tables"
F = HERE.parent / "figures_v2"
F.mkdir(exist_ok=True)
SURF, INK, INK2, MUTED, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#898781", "#e1e0d9"
C1, C2 = "#2a78d6", "#eb6834"
plt.rcParams.update({"font.size": 8, "axes.edgecolor": GRID, "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK2,
                     "axes.linewidth": 0.6, "figure.facecolor": SURF, "axes.facecolor": SURF, "savefig.facecolor": SURF,
                     "axes.spines.top": False, "axes.spines.right": False, "xtick.major.size": 0, "ytick.major.size": 0})


def style(ax):
    ax.grid(axis="y", color=GRID, linewidth=0.6)
    ax.set_axisbelow(True)


# ---------------- Figure 1: abnormal return in event time after the first missed day
p = pd.read_csv(T / "series_event_time.csv")
fig, ax = plt.subplots(figsize=(7.2, 3.0))
ax.axhline(0, color=MUTED, linewidth=0.6)
ax.plot(p.day, p.MID, color=MUTED, linewidth=1.2)
ax.plot(p.day, p.REG, color=C1, linewidth=1.8)
ax.plot(p.day, p.IRR, color=C2, linewidth=1.8)
style(ax)
last = p.iloc[-1]
ax.annotate(f"regular reporters  {last.REG:+.2f}%", (last.day, last.REG), xytext=(6, 2), textcoords="offset points", fontsize=7.5, color=INK2, va="center")
ax.annotate(f"middle third  {last.MID:+.2f}%", (last.day, last.MID), xytext=(6, -3), textcoords="offset points", fontsize=7.5, color=INK2, va="center")
ax.annotate(f"irregular reporters  {last.IRR:+.2f}%", (last.day, last.IRR), xytext=(6, 0), textcoords="offset points", fontsize=7.5, color=INK2, va="center")
ax.set_xlim(0, 27.5)
ax.set_xticks(range(0, 21, 5))
ax.set_xlabel("Trading days after the entry day (the first trading day after the expected announcement date)")
ax.set_ylabel("Mean cumulative abnormal return (%)")
ax.set_title("Firms silent one day after their expected announcement date: abnormal return by reporting history, 2004-2024", loc="left", fontsize=8.5, color=INK)
fig.tight_layout()
fig.savefig(F / "fig1_event_time.png", dpi=300)
plt.close(fig)

# ---------------- Figure 2: irregular minus regular by entry year
b = pd.read_csv(T / "series_by_year.csv")
fig, ax = plt.subplots(figsize=(7.2, 2.9))
ax.axhline(0, color=MUTED, linewidth=0.6)
for _, r in b.iterrows():
    if r.stage == "disc":
        ax.bar(r.year, r["diff"], width=0.72, color=C1, edgecolor=SURF, linewidth=0.8)
    elif r.stage == "conf":
        ax.bar(r.year, r["diff"], width=0.72, color=C2, edgecolor=SURF, linewidth=0.8, hatch="////")
    else:
        ax.bar(r.year, r["diff"], width=0.72, color=SURF, edgecolor=INK2, linewidth=1.0)
style(ax)
ax.set_xticks(range(2004, 2026, 3))
ax.set_ylabel("Irregular minus regular (pp)")
ax.set_title("Holding-period abnormal return of irregular minus regular reporters, by entry year", loc="left", fontsize=8.5, color=INK)
leg = ax.legend(handles=[Patch(facecolor=C1, edgecolor=SURF, label="discovery years (even)"),
                         Patch(facecolor=C2, edgecolor=SURF, hatch="////", label="confirmation years (odd)"),
                         Patch(facecolor=SURF, edgecolor=INK2, label="2025 (opened last)")],
                loc="lower center", bbox_to_anchor=(0.5, -0.34), ncol=3, frameon=False, fontsize=7.5, handlelength=1.6)
for t_ in leg.get_texts():
    t_.set_color(INK2)
n_neg = int((b["diff"] < 0).sum())
ax.text(0.995, 0.96, f"negative in {n_neg} of {len(b)} years", transform=ax.transAxes, ha="right", va="top", fontsize=7.5, color=INK2)
fig.tight_layout()
fig.savefig(F / "fig2_by_year.png", dpi=300)
plt.close(fig)
print("figures written:", [x.name for x in sorted(F.glob("*.png"))], "| day-20 values", {k: round(float(last[k]), 3) for k in ("IRR", "MID", "REG")})
