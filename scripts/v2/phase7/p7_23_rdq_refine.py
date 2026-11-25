"""Phase 7 - step 23: family R refinement on the DISCOVERY years only (logged in SEARCH_LOG.md as R-2).
Do the new-information conditions survive controls for the known ones (size rank, low price, prior loss, momentum, prior SUE)?
Run: python p7_23_rdq_refine.py
"""
import warnings

import numpy as np
import pandas as pd

import p7lib as L

warnings.simplefilter("ignore")


def Zof(D):
    z = np.column_stack([np.log(D.rk.values.astype(float)), (D.prc.values < 10).astype(float), np.nan_to_num(D.loss_prev.astype(float).values, nan=0.0),
                         np.nan_to_num(D.mom.clip(-80, 300).values, nan=0.0), np.nan_to_num(D.sue_prev.clip(-0.1, 0.1).values, nan=0.0)])
    return z


def t1(D, flag, base, out, label, ctrl=True):
    y = D["y_" + out].values
    m = (base & flag.notna()).values & ~np.isnan(y)
    x = flag.values[m].astype(float)
    fe, g = L.codes(D.year.values[m]), L.codes(D.ym.values[m])
    if ctrl:
        b, t, n1, n0 = L.diff_test_ctrl(y[m], x, Zof(D[m]), fe, g)
    else:
        b, t, n1, n0 = L.diff_test(y[m], x, fe, g)
    m1 = m & (flag.values == 1)
    lv, lt, _ = L.level_test(y[m1], L.codes(D.ym.values[m1])) if m1.sum() > 1 else (np.nan, np.nan, 0)
    print(f"   {label:66s} {out:6s} n1 {n1:6d} n0 {n0:6d} | diff {b:+6.3f} (t {t:+5.2f}) | level {lv:+6.3f} (t {lt:+5.2f})")
    return t


pd.set_option("display.width", 200)
print("[1] delay events: new-information conditions with controls (size rank, price < $10, prior loss, momentum, prior SUE)")
for kd in (1, 3, 5):
    D = pd.read_parquet(L.OUT / f"rdq_disc_delay{kd}.parquet")
    ALL = pd.Series(True, index=D.index)
    ic = D.ins_cov.astype(bool) & (D.date >= "2015-07-01")
    kh = D.k8hist.astype(bool)
    print(f" -- delay k={kd} (n {len(D)})")
    for out in ("hold", "w20"):
        t1(D, (D.ins_p > 0).astype(float), ic, out, "insider bought in prior 180 days")
        t1(D, ((D.ins_s > 0) & (D.ins_p == 0)).astype(float), ic, out, "insiders only sold in prior 180 days")
        t1(D, ((D.ins_s > 0) & (D.ins_p == 0)).astype(float), ic & (D.rk <= 1000), out, "insiders only sold, rank 1-1000")
        t1(D, D.fq4.astype(float), ALL, out, "fiscal fourth quarter")
        sd = D.sd_dev8
        q1, q2 = sd.quantile([1 / 3, 2 / 3])
        t1(D, pd.Series(np.where(sd > q2, 1.0, np.where(sd <= q1, 0.0, np.nan)), index=D.index), ALL, out, "irregular announcement dates (top vs bottom tercile)")
        t1(D, (D.n_late8 >= 2).where(D.n_late8.notna()).astype(float), ALL, out, "late at least twice in the previous 8 quarters")
        t1(D, (D.nt365 > 0).astype(float), ALL, out, "NT filing in prior 365 days")
        t1(D, (D.k401 > 0).astype(float), kh, out, "auditor change 8-K in prior 180 days")
        t1(D, (D.k502 > 0).astype(float), kh, out, "officer change 8-K in prior 180 days")
        t1(D, (D.let365 > 0).astype(float), ALL, out, "SEC letter released in prior 365 days")
        t1(D, (D.let3_365 > 0).astype(float), ALL, out, "SEC letter with 3+ staff letters released in prior 365 days")
        si = D.si_ratio
        q1, q2 = si.quantile([1 / 3, 2 / 3])
        t1(D, pd.Series(np.where(si > q2, 1.0, np.where(si <= q1, 0.0, np.nan)), index=D.index), ALL, out, "short interest ratio (top vs bottom tercile)")

print("[2] announcements: late announcers after the announcement (days 2-21 and 2-61), with the same controls plus the announced SUE")
A = pd.read_parquet(L.OUT / "rdq_disc_ann.parquet")
ALL = pd.Series(True, index=A.index)
for thr in (5, 10, 15, 20):
    for out in ("d2_21", "d2_61"):
        t1(A, (A.dev_td >= thr).astype(float), ALL, out, f"announced {thr}+ trading days late")
for out in ("d2_21", "d2_61"):
    t1(A, (A.dev_td >= 10).astype(float), A.rk > 1000, out, "announced 10+ days late, rank 1001-3000")
    t1(A, (A.dev_td >= 10).astype(float), A.rk <= 1000, out, "announced 10+ days late, rank 1-1000")
    t1(A, (A.dev_td >= 10).astype(float), A.sue_act < 0, out, "announced 10+ days late, among negative SUE")
    t1(A, (A.dev_td >= 10).astype(float), A.sue_act >= 0, out, "announced 10+ days late, among non-negative SUE")
    t1(A, (A.dev_td <= -5).astype(float), ALL, out, "announced 5+ trading days early")
    t1(A, (A.let365 > 0).astype(float), ALL, out, "SEC letter released in prior 365 days")
    t1(A, (A.let3_365 > 0).astype(float), ALL, out, "SEC letter with 3+ staff letters in prior 365 days")
print("   by entry year, announced 10+ days late, days 2-21 level:")
L10 = A[A.dev_td >= 10]
print("   ", {int(y): (round(v.y_d2_21.mean(), 2), int(v.y_d2_21.notna().sum())) for y, v in L10.groupby("year")})

print("[3] expected window (entry 6 trading days before the expected date, exit the day after): conditions with controls")
X = pd.read_parquet(L.OUT / "rdq_disc_exp.parquet")
ALL = pd.Series(True, index=X.index)
ic = X.ins_cov.astype(bool) & (X.date >= "2015-07-01")
t1(X, (X.ins_p > 0).astype(float), ic, "hold", "insider bought in prior 180 days")
t1(X, ((X.ins_s > 0) & (X.ins_p == 0)).astype(float), ic, "hold", "insiders only sold in prior 180 days")
t1(X, (X.let365 > 0).astype(float), ALL, "hold", "SEC letter released in prior 365 days")
t1(X, (X.let365 > 0).astype(float), X.rk > 1000, "hold", "SEC letter released in prior 365 days, rank 1001-3000")
t1(X, (X.let3_365 > 0).astype(float), ALL, "hold", "SEC letter with 3+ staff letters in prior 365 days")
t1(X, (X.let3_365 > 0).astype(float), X.rk > 1000, "hold", "SEC letter with 3+ staff letters, rank 1001-3000")
t1(X, (X.nt365 > 0).astype(float), ALL, "hold", "NT filing in prior 365 days")
t1(X, (X.n_late8 >= 2).where(X.n_late8.notna()).astype(float), ALL, "hold", "late at least twice in the previous 8 quarters")
sd = X.sd_dev8
q1, q2 = sd.quantile([1 / 3, 2 / 3])
t1(X, pd.Series(np.where(sd > q2, 1.0, np.where(sd <= q1, 0.0, np.nan)), index=X.index), ALL, "hold", "irregular announcement dates (top vs bottom tercile)")
