"""p05: statistics for the main spec (12 cells), B1, B4 (composite), D4 (Table 6 / Table 8) and the repo's
pre-registered criteria, from phase3/out/ct_monthly.csv.gz. Writes out/ct_stats.csv, out/composite.csv,
out/d4_table6.csv, out/d4_table8.csv, out/criteria.json; prints the key tables.
"""
import sys
sys.dont_write_bytecode = True
import json
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from p3common import OUT, PRIMARY, IS_FIRST, IS_LAST, LATE_FIRST, LATE_LAST, series_stats, month_index  # noqa: E402

M = pd.read_csv(OUT / "ct_monthly.csv.gz", parse_dates=["month"])
PERIODS = {"IS": (IS_FIRST, IS_LAST), "LATE": (LATE_FIRST, LATE_LAST)}
COSTS = ["gross", "net_qs_s", "net_all_s", "net_20_s", "net_qs", "net_all", "net_20"]   # *_s = DEV1 slot turnover; plain = frozen rule


def ls_series(g):
    """g: rows of one (universe,H,start,label,cell). Returns DataFrame of monthly LS by cost type (full calendar)."""
    lo = g[g.leg == 1].set_index("month")
    sh = g[g.leg == -1].set_index("month")
    idx = month_index(IS_FIRST, LATE_LAST)
    f = lambda d, c: d[c].reindex(idx).fillna(0.0)
    gross = f(lo, "R") - f(sh, "R")
    out = pd.DataFrame({"gross": gross,
                        "net_qs": gross - f(lo, "c_qs") - f(sh, "c_qs"),
                        "net_20": gross - f(lo, "c_20") - f(sh, "c_20")})
    out["net_all"] = out["net_qs"] - f(sh, "borrow")
    out["net_qs_s"] = gross - f(lo, "c_qs_s") - f(sh, "c_qs_s")
    out["net_20_s"] = gross - f(lo, "c_20_s") - f(sh, "c_20_s")
    out["net_all_s"] = out["net_qs_s"] - f(sh, "borrow")
    out["borrow"] = f(sh, "borrow")
    out["cost_qs"] = f(lo, "c_qs") + f(sh, "c_qs")
    out["cost_qs_s"] = f(lo, "c_qs_s") + f(sh, "c_qs_s")
    out["R_long"], out["R_short"] = f(lo, "R"), f(sh, "R")
    return out


series, rows = {}, []
for key, g in M.groupby(["universe", "H", "start", "label", "cell"]):
    uni, H, start, lab, cell = key
    name = f"A{H}-{cell}" + ("-SW" if start == "sw" else "") + ("-FF49" if lab == "c49" else "")
    s = ls_series(g)
    series[(uni, name)] = s
    for per, (a, b) in PERIODS.items():
        ss = s.loc[a:b]
        for c in COSTS:
            r = series_stats(ss[c])
            r.update(universe=uni, cell=name, H=H, start=start, label=lab, period=per, cost=c,
                     mean_borrow_m=float(ss["borrow"].mean()), mean_costqs_m=float(ss["cost_qs"].mean()))
            rows.append(r)
# composite of the 4 primary cells (main and b1)
for uni in ("main", "b1"):
    comp = sum(series[(uni, c)] for c in PRIMARY) / 4.0
    series[(uni, "COMPOSITE4")] = comp
    for per, (a, b) in PERIODS.items():
        ss = comp.loc[a:b]
        for c in COSTS:
            r = series_stats(ss[c])
            r.update(universe=uni, cell="COMPOSITE4", H=np.nan, start="nd", label="c12", period=per, cost=c,
                     mean_borrow_m=float(ss["borrow"].mean()), mean_costqs_m=float(ss["cost_qs"].mean()))
            rows.append(r)
S = pd.DataFrame(rows)
S.to_csv(OUT / "ct_stats.csv", index=False)
pd.to_pickle(series, OUT / "ct_series.pkl")

pd.set_option("display.width", 250)
TWELVE = [f"A{H}-{sz}{it}" for H in (60, 120, 180) for sz in "LS" for it in "HL"]


def table(uni, cells, cost="gross"):
    t = S[(S.universe == uni) & S.cell.isin(cells) & (S.cost == cost)]
    piv = t.pivot_table(index="cell", columns="period", values=["mu_m", "t_nw", "t_nw12", "sharpe"], aggfunc="first")
    piv[("mu_m", "IS")] *= 100; piv[("mu_m", "LATE")] *= 100
    return piv.reindex(cells).round(3)


def counts(uni, cells, per, cost="gross"):
    t = S[(S.universe == uni) & S.cell.isin(cells) & (S.cost == cost) & (S.period == per)]
    return dict(n=len(t), bonf2=int(t.pass_bonf2.sum()), bonf1=int(t.pass_bonf1.sum()), p278=int(t.pass_278.sum()),
                nom5=int(t.pass_nom5.sum()), sign=int(t.sign_ok.sum()), crit2=round(float(t.crit_bonf2.iloc[0]), 3),
                chance=round(0.05 * len(t), 2))


crit = {}
for uni in ("main", "b1"):
    print(f"\n===== {uni.upper()} universe: 12 cells, calendar-time LS monthly mean (%), NW t (auto lag), NW12 t, Sharpe =====")
    for cost in COSTS:
        print(f"--- {cost}")
        print(table(uni, TWELVE, cost).to_string())
        for per in PERIODS:
            c = counts(uni, TWELVE, per, cost)
            crit[f"{uni}_{cost}_{per}"] = c
            print(f"   {per}: Bonferroni-12 exact two-sided passes {c['bonf2']}/12 (crit {c['crit2']}), one-sided {c['bonf1']}, "
                  f"|t|>2.78 {c['p278']}, nominal 5% {c['nom5']} (chance {c['chance']}), sign-correct {c['sign']}/12")
    print(f"--- {uni} COMPOSITE4 (B4)")
    t = S[(S.universe == uni) & (S.cell == "COMPOSITE4")][["period", "cost", "T", "mu_m", "ann_ret", "ann_vol", "sharpe", "t_nw", "t_nw12", "p_two"]]
    print(t.assign(mu_m=t.mu_m * 100, ann_ret=t.ann_ret * 100, ann_vol=t.ann_vol * 100).round(3).to_string(index=False))
S[S.cell == "COMPOSITE4"].to_csv(OUT / "composite.csv", index=False)

# leg decomposition and cost levels (main, primary cells + composite)
print("\n===== MAIN: leg returns and cost drags (monthly %, mean over period) =====")
for name in PRIMARY + ["COMPOSITE4"]:
    s = series[("main", name)]
    for per, (a, b) in PERIODS.items():
        ss = s.loc[a:b]
        print(f"  {name:10s} {per:4s} long {100*ss.R_long.mean():6.3f} short {100*ss.R_short.mean():6.3f} gross {100*ss.gross.mean():6.3f}"
              f" | spread cost DEV1 {100*ss.cost_qs_s.mean():5.3f} (frozen {100*ss.cost_qs.mean():5.3f}) borrow {100*ss.borrow.mean():5.3f}"
              f" -> net_all DEV1 {100*ss.net_all_s.mean():6.3f} (frozen {100*ss.net_all.mean():6.3f})")

# D4 Table 6: next-day vs skip-week, like-for-like periods
t6 = []
for c in PRIMARY:
    for per in PERIODS:
        a = S[(S.universe == "main") & (S.cell == c) & (S.cost == "gross") & (S.period == per)].iloc[0]
        b = S[(S.universe == "main") & (S.cell == c + "-SW") & (S.cost == "gross") & (S.period == per)].iloc[0]
        t6.append(dict(cell=c, period=per, mu_nextday=a.mu_m, t_nextday=a.t_nw, mu_skipweek=b.mu_m, t_skipweek=b.t_nw, change_t=b.t_nw - a.t_nw))
T6 = pd.DataFrame(t6)
T6.to_csv(OUT / "d4_table6.csv", index=False)
print("\n===== D4 Table 6 (main spec, gross, like-for-like) =====")
print(T6.assign(mu_nextday=T6.mu_nextday * 100, mu_skipweek=T6.mu_skipweek * 100).round(3).to_string(index=False))

# D4 Table 8 blocks
blocks = {"FF12 primary 12 cells": TWELVE,
          "FF49 tilt 12 cells": [c + "-FF49" for c in TWELVE],
          "Extended H 240/360 (8)": [f"A{H}-{sz}{it}" for H in (240, 360) for sz in "LS" for it in "HL"],
          "Skip-week H 120/180 (8)": [f"A{H}-{sz}{it}-SW" for H in (120, 180) for sz in "LS" for it in "HL"]}
t8 = []
for bname, cl in blocks.items():
    for per in PERIODS:
        c = counts("main", cl, per, "gross")
        t8.append(dict(block=bname, period=per, cells=c["n"], bonf12_exact=c["bonf2"], abs_t_278=c["p278"], nominal5=c["nom5"],
                       chance=c["chance"], sign_correct=c["sign"]))
T8 = pd.DataFrame(t8)
tot = T8.groupby("period")[["cells", "bonf12_exact", "abs_t_278", "nominal5", "chance", "sign_correct"]].sum().reset_index().assign(block="Total")
T8 = pd.concat([T8, tot], ignore_index=True)
T8.to_csv(OUT / "d4_table8.csv", index=False)
print("\n===== D4 Table 8 (main spec, gross; each period separately) =====")
print(T8.to_string(index=False))

# pre-registered criteria (main spec)
def prim(per, cost="gross"):
    t = S[(S.universe == "main") & S.cell.isin(PRIMARY) & (S.cost == cost) & (S.period == per)]
    return int(t.pass_bonf2.sum()), int(t.pass_278.sum()), t.set_index("cell")[["mu_m", "t_nw"]]
is_b, is_278, is_tab = prim("IS")
la_b, la_278, la_tab = prim("LATE")
ret = {}
for cost in ("net_all_s", "net_all"):
    for per in PERIODS:
        g = S[(S.universe == "main") & S.cell.isin(PRIMARY) & (S.cost == "gross") & (S.period == per)].set_index("cell").mu_m
        n = S[(S.universe == "main") & S.cell.isin(PRIMARY) & (S.cost == cost) & (S.period == per)].set_index("cell").mu_m
        ret[f"{cost}_{per}"] = {c: (round(float(n[c] / g[c]), 3) if g[c] > 0 else None) for c in PRIMARY}
c12 = crit["main_gross_IS"]["bonf2"]
out = {
    "subgate_e_IS_passes_exact": c12, "subgate_e_IS_passes_278": crit["main_gross_IS"]["p278"],
    "subgate_e_verdict": "PASS" if c12 >= 3 else ("BORDERLINE" if c12 == 2 else "KILL"),
    "L1_IS_primary_passes_exact": is_b, "L1_IS_primary_passes_278": is_278, "L1_met": is_b >= 3,
    "L2_LATE_primary_passes_exact": la_b, "L2_LATE_primary_passes_278": la_278, "L2_met": la_b >= 2,
    "K1_fires": is_b < 3, "K2_fires": la_b <= 1,
    "L5_K5_net_all_over_gross": ret,
    "late_sign_correct_12": crit["main_gross_LATE"]["sign"], "IS_sign_correct_12": crit["main_gross_IS"]["sign"],
}
(OUT / "criteria.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
print("\n===== pre-registered criteria (main spec) =====")
print(json.dumps(out, indent=1, default=str))
