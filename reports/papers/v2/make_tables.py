"""Series and tables for the revised RDQ paper (v2): missed expected earnings dates and reporting regularity.

Reads the phase-7 event tables ($RDQ_V2_WORK/_main_checks/phase7/cache) through p7lib and writes tables/*.csv.
Everything here restates statistics that were fixed and reported before (PHASE7_SEARCH_PROTOCOL.md, CANDIDATES.md,
SEARCH_LOG.md, log_40..log_45); nothing selects a specification. The 2025 rows use the record year, which was opened
once on 2026-11-23 (log_40_r05_rec2025.txt); they are recomputed here only to tabulate the same statistic by year.
Run: python make_tables.py
"""
import json
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
P7 = HERE.parents[2] / "scripts" / "v2" / "phase7"
sys.path.insert(0, str(P7))
import p7lib as L  # noqa: E402

warnings.simplefilter("ignore")
T = HERE / "tables"
T.mkdir(exist_ok=True)
cuts = json.load(open(L.OUT / "rdq_search_cuts.json"))
q1, q2 = cuts["delay1:terc:sd_dev8"]
ST = ("disc", "conf")
ev = pd.read_parquet(L.CACHE / "rdq_events_delay.parquet")
ev = ev[ev.year >= 2004].copy()
ev["grp"] = np.where(ev.sd_dev8 > q2, "IRR", np.where(ev.sd_dev8 <= q1, "REG", np.where(ev.sd_dev8.notna(), "MID", "NA")))

# ---- T2: the delay effect by length of silence, all firms, 2004-2024
rows = []
for kd in (1, 3, 5, 10):
    D = ev[(ev.kd == kd) & ev.stage.isin(ST)].copy()
    D["eid"] = np.arange(len(D))
    D = D.merge(L.ar_windows(D, [], allow=ST, exit_col="kx"), on="eid")
    lo, hi = cuts[f"delay{kd}:hold"]
    D["y"] = D.ar_hold.clip(lo, hi)
    x = D[D.y.notna()]
    m, t, n = L.level_test(x.y.values, L.codes(x.ym.values))
    r = {"delay_days": kd, "events": n, "mean_ar_pct": m, "t": t, "days_held": x.n_hold.mean(), "bp_per_day": x.y.sum() / x.n_hold.sum() * 100,
         "share_irregular": float((x.grp == "IRR").mean()), "share_regular": float((x.grp == "REG").mean())}
    for h, lab in (((2004, 2013), "2004_2013"), ((2014, 2024), "2014_2024")):
        z = x[(x.year >= h[0]) & (x.year <= h[1])]
        mm, tt, nn = L.level_test(z.y.values, L.codes(z.ym.values))
        r[f"mean_{lab}"], r[f"t_{lab}"] = mm, tt
    rows.append(r)
t2 = pd.DataFrame(rows)
t2.to_csv(T / "T2_delay_by_length.csv", index=False)
print("T2 delay effect by length (all firms, 2004-2024)\n", t2.round(3).to_string(index=False))

# ---- one-day-late events with returns (discovery + confirmation years)
D1 = ev[(ev.kd == 1) & ev.stage.isin(ST)].copy()
D1["eid"] = np.arange(len(D1))
W = [(f"d{d}", 0, d) for d in range(1, 21)]
D1 = D1.merge(L.ar_windows(D1, W, allow=ST, exit_col="kx"), on="eid")
lo, hi = cuts["delay1:hold"]
D1["y"] = D1.ar_hold.clip(lo, hi)

# ---- series for Figure 1: abnormal return path in event time (fixed windows from the entry day).
# Each window is winsorized at its own 1st/99th percentile of the discovery years, the rule of the search (p7_22 winsor()).
path = []
for d in range(0, 21):
    r = {"day": d}
    if d:
        wl, wh = D1.loc[D1.stage == "disc", f"ar_d{d}"].quantile([.01, .99])
    for g in ("IRR", "MID", "REG"):
        r[g] = 0.0 if d == 0 else float(D1.loc[D1.grp == g, f"ar_d{d}"].clip(wl, wh).mean())
    path.append(r)
pd.DataFrame(path).to_csv(T / "series_event_time.csv", index=False)
chk = pd.DataFrame(path).set_index("day").loc[[1, 5, 10, 20]].round(3)
print("event-time path at days 1, 5, 10, 20 (compare log_40_r05.txt: IRR -0.033 / -0.271 / -0.383 / -0.476; REG +0.052 / +0.119 / +0.125 / +0.141)\n", chk.to_string())

# ---- series for Figure 2: irregular minus regular by entry year, 2004-2025
R = ev[(ev.kd == 1) & (ev.stage == "rec")].copy()
R["eid"] = np.arange(len(R))
R = R.merge(L.ar_windows(R, [], allow=("rec",), exit_col="kx"), on="eid")
R["y"] = R.ar_hold.clip(lo, hi)
A = pd.concat([D1[["year", "stage", "grp", "y", "ym"]], R[["year", "stage", "grp", "y", "ym"]]])
by = []
for y_, g_ in A[A.grp.isin(["IRR", "REG"]) & A.y.notna()].groupby("year"):
    i, r_ = g_[g_.grp == "IRR"], g_[g_.grp == "REG"]
    by.append({"year": int(y_), "stage": g_.stage.iloc[0], "irr": i.y.mean(), "reg": r_.y.mean(), "diff": i.y.mean() - r_.y.mean(), "n_irr": len(i), "n_reg": len(r_)})
by = pd.DataFrame(by)
by.to_csv(T / "series_by_year.csv", index=False)
neg = by[by["diff"] < 0]
print(f"by year: {len(neg)} of {len(by)} years negative; discovery {int((neg.stage == 'disc').sum())}/{int((by.stage == 'disc').sum())},"
      f" confirmation {int((neg.stage == 'conf').sum())}/{int((by.stage == 'conf').sum())}, record {int((neg.stage == 'rec').sum())}/{int((by.stage == 'rec').sum())}")
print(by.round(3).to_string(index=False))

# ---- T1: sample description of the one-day-late events by group (no outcome data except days held)
D1["late"] = np.where(D1.k_ann < 10 ** 7, D1.k_ann - D1.kE, np.nan)
t1 = D1[D1.grp.isin(["IRR", "MID", "REG"])].groupby("grp").agg(
    events=("eid", "size"), sd_dev_median=("sd_dev8", "median"), size_rank_median=("rk", "median"), price_median=("prc", "median"),
    prior_loss_share=("loss_prev", "mean"), days_held_mean=("n_hold", "mean"), late_median=("late", "median"),
    still_silent_after_5=("late", lambda s: float(np.mean(s > 5))), still_silent_after_10=("late", lambda s: float(np.mean(s > 10))),
    verified_8k_share=("k8cov", "mean")).reindex(["IRR", "MID", "REG"])
t1.to_csv(T / "T1_groups.csv")
print("T1 groups\n", t1.round(3).to_string())
print(f"events 2004-2024: {len(D1)}; with an irregularity measure: {int(D1.grp.isin(['IRR', 'MID', 'REG']).sum())}; firms: {D1.permno.nunique()};"
      f" cut-offs {q1:.2f} / {q2:.2f}; winsorization {lo:.2f} / {hi:.2f}; first entry {D1.date.min().date()}, last {D1.date.max().date()}")
