"""Phase 7 - step 45: R05 follow-up (interpretation, written after the confirmation and the 2025 record; descriptive only).

Question raised by the prior-art check (2026-11-25): are irregular reporters simply weak firms, whatever the timing?
If so, they should also underperform regular reporters when they are NOT late.

  [A] firms that announced on time (no later than one trading day after the expected date): abnormal return over
      (i) the five trading days before the announcement and (ii) the announcement day and the next day, by group.
  [B] every firm in the week up to the expected date (entry six trading days before it, exit one day after it), by group.
  [C] for comparison: the one-day-late firms of R05 (holding period, announcement window).
Groups use the R05 cut-offs (sd of the timing deviation over the previous 8 quarters: > 3.93 irregular, <= 2.20 regular).
Full period 2004-2024 (discovery + confirmation years). Nothing here selects a specification.
Run: python p7_45_r05_placebo.py
"""
import json
import warnings

import numpy as np
import pandas as pd

import p7lib as L

warnings.simplefilter("ignore")
cuts = json.load(open(L.OUT / "rdq_search_cuts.json"))
q1, q2 = cuts["delay1:terc:sd_dev8"]
lo, hi = cuts["delay1:hold"]
ST = ("disc", "conf")


def grp(s):
    return np.where(s > q2, "IRR", np.where(s <= q1, "REG", np.where(s.notna(), "MID", "NA")))


def report(D, col, label, ncol=None):
    out = f"   {label:44s}"
    for g in ("IRR", "MID", "REG"):
        x = D[(D.grp == g) & D[col].notna()]
        m, t, n = L.level_test(x[col].clip(lo, hi).values, L.codes(x.ym.values))
        out += f" | {g} {m:+.3f} (t {t:+5.2f}, n {n})"
    z = D[D.grp.isin(["IRR", "REG"]) & D[col].notna()]
    b, t, n1, n0 = L.diff_test(z[col].clip(lo, hi).values, (z.grp == "IRR").astype(float).values, L.codes(z.year.values), L.codes(z.ym.values))
    print(out + f" | IRR - REG {b:+.3f} (t {t:+5.2f})")
    return b


# [A] on-time announcers
A = pd.read_parquet(L.CACHE / "rdq_events_ann.parquet")
A = A[(A.year >= 2004) & A.stage.isin(ST) & (A.dev_td <= 1)].copy()
A["grp"] = grp(A.sd_dev8)
A["eid"] = np.arange(len(A))
pre = A[["eid", "permno", "stage"]].copy()
pre["k0"] = (A.k_ann - 6).values
pre["kx"] = (A.k_ann - 1).values
A = A.merge(L.ar_windows(pre, [], allow=ST, exit_col="kx").rename(columns={"ar_hold": "ar_pre", "n_hold": "n_pre"}), on="eid")
ann = A[["eid", "permno", "stage"]].copy()
ann["k0"] = (A.k_ann - 1).values
ann["kx"] = (A.k_ann + 1).values
A = A.merge(L.ar_windows(ann, [], allow=ST, exit_col="kx").rename(columns={"ar_hold": "ar_ann", "n_hold": "n_ann"}), on="eid")
print(f"=== R05 placebo, 2004-2024. [A] on-time announcers (announced no later than expected date + 1): {len(A)}; groups {pd.Series(A.grp).value_counts().to_dict()}")
a_pre = report(A, "ar_pre", "five trading days before the announcement")
a_ann = report(A, "ar_ann", "announcement day + next day")
for name, sub in (("size rank 1001-3000", A[A.rk > 1000]), ("size rank 1-1000", A[A.rk <= 1000])):
    report(sub, "ar_ann", f"announcement day + next day, {name}")

# [B] all firms, the week up to the expected date
E = pd.read_parquet(L.CACHE / "rdq_events_exp.parquet")
E = E[(E.year >= 2004) & E.stage.isin(ST)].copy()
E["grp"] = grp(E.sd_dev8)
E["eid"] = np.arange(len(E))
E = E.merge(L.ar_windows(E, [], allow=ST, exit_col="kx"), on="eid")
print(f"[B] every firm, entry six trading days before the expected date, exit one day after it: {len(E)}; groups {pd.Series(E.grp).value_counts().to_dict()}")
b_exp = report(E, "ar_hold", "expected-date week")
report(E[E.rk > 1000], "ar_hold", "expected-date week, size rank 1001-3000")

# [C] the one-day-late firms (R05), same statistics
D = pd.read_parquet(L.CACHE / "rdq_events_delay.parquet")
D = D[(D.kd == 1) & (D.year >= 2004) & D.stage.isin(ST)].copy()
D["grp"] = grp(D.sd_dev8)
D["eid"] = np.arange(len(D))
D = D.merge(L.ar_windows(D, [], allow=ST, exit_col="kx"), on="eid")
D["capped"] = D.kx < D.k_ann + 1
late = D.loc[~D.capped, ["eid", "permno", "stage"]].copy()
late["k0"] = np.maximum(D.loc[~D.capped, "k_ann"] - 1, D.loc[~D.capped, "k0"]).values
late["kx"] = D.loc[~D.capped, "kx"].values
D = D.merge(L.ar_windows(late, [], allow=ST, exit_col="kx").rename(columns={"ar_hold": "ar_ann", "n_hold": "n_ann"}), on="eid", how="left")
print(f"[C] one-day-late firms (R05): {len(D)}")
c_hold = report(D, "ar_hold", "holding period (entry to day after announcement)")
c_ann = report(D, "ar_ann", "announcement day + next day")
print(f"[D] difference in differences, announcement window: late (IRR - REG) {c_ann:+.3f} minus on-time (IRR - REG) {a_ann:+.3f} = {c_ann - a_ann:+.3f}")
# pooled interaction test on the announcement window: late x irregular, year fixed effects, month clusters
P = pd.concat([A.assign(late=0.0)[["ar_ann", "grp", "late", "year", "ym"]], D.assign(late=1.0)[["ar_ann", "grp", "late", "year", "ym"]]])
P = P[P.grp.isin(["IRR", "REG"]) & P.ar_ann.notna()].copy()
P["irr"] = (P.grp == "IRR").astype(float)
P["x"] = P.irr * P.late
y = P.ar_ann.clip(lo, hi).values
Z = np.column_stack([P.irr.values, P.late.values])
b, t, n1, n0 = L.diff_test_ctrl(y, P.x.values, Z, L.codes(P.year.values), L.codes(P.ym.values))
print(f"    pooled regression of the announcement-window return on late x irregular (controls: late, irregular; year FE; month clusters): {b:+.3f} (t {t:+.2f}); n {len(P)}")
