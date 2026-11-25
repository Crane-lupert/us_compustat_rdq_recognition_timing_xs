"""Phase 7 - step 30: the frozen candidates (CANDIDATES.md) on one stage.

  python p7_30_confirm.py disc   self-check: must reproduce the discovery numbers of the grid
  python p7_30_confirm.py conf   the one confirmation run on the odd years (run once)
Winsorisation cut-offs and tercile cut-offs are the ones fixed on the discovery years.
"""
import json
import sys
import warnings

import numpy as np
import pandas as pd

import p7lib as L

warnings.simplefilter("ignore")
STAGE = sys.argv[1]
assert STAGE in ("disc", "conf")
cuts = json.load(open(L.OUT / "rdq_search_cuts.json"))
sc = json.load(open(L.OUT / "sec_search_cuts.json"))


def load(name, windows, exit_col=None, sel=None):
    ev = pd.read_parquet(L.CACHE / name)
    ev = ev[ev.year >= 2004]
    if sel is not None:
        ev = ev[sel(ev)]
    D = ev[ev.stage == STAGE].copy()
    D["eid"] = np.arange(len(D))
    D = D.merge(L.ar_windows(D, windows, allow=(STAGE,), exit_col=exit_col), on="eid")
    return D


def wins(D, out, key):
    lo, hi = cuts[key]
    D["y_" + out] = D["ar_" + out].clip(lo, hi)


def terc(v, key):
    q1, q2 = cuts[key]
    return pd.Series(np.where(v > q2, 1.0, np.where(v <= q1, 0.0, np.nan)), index=v.index)


def Zof(D):
    return np.column_stack([np.log(D.rk.values.astype(float)), (D.prc.values < 10).astype(float), np.nan_to_num(D.loss_prev.astype(float).values, nan=0.0),
                            np.nan_to_num(D.mom.clip(-80, 300).values, nan=0.0), np.nan_to_num(D.sue_prev.clip(-0.1, 0.1).values, nan=0.0)])


res = []


def stat(cid, D, flag, base, out, label, ctrl=False, record=True):
    y = D["y_" + out].values
    f = flag.astype(float)
    m = (base & f.notna()).values & ~np.isnan(y)
    fe, g = L.codes(D.year.values[m]), L.codes(D.ym.values[m])
    if ctrl:
        b, t, n1, n0 = L.diff_test_ctrl(y[m], f.values[m], Zof(D[m]), fe, g)
    else:
        b, t, n1, n0 = L.diff_test(y[m], f.values[m], fe, g)
    m1 = m & (f.values == 1)
    lv, lt, _ = L.level_test(y[m1], L.codes(D.ym.values[m1])) if m1.sum() > 1 else (np.nan, np.nan, 0)
    print(f"   {cid:4s} {label:62s} n1 {n1:6d} n0 {n0:6d} | diff {b:+7.3f} (t {t:+5.2f}) | level {lv:+7.3f} (t {lt:+5.2f})")
    if record:
        res.append(dict(id=cid, stage=STAGE, label=label, diff=b, t=t, n1=n1, n0=n0, level1=lv, t_level1=lt))


print(f"=== stage: {STAGE} ===")
ALLW = [("w5", 0, 5), ("w10", 0, 10), ("w20", 0, 20)]
D1 = load("rdq_events_delay.parquet", ALLW, exit_col="kx", sel=lambda e: e.kd == 1)
for o in ("hold", "w10", "w20"):
    wins(D1, o, f"delay1:{o}")
D3 = load("rdq_events_delay.parquet", ALLW, exit_col="kx", sel=lambda e: e.kd == 3)
for o in ("hold", "w20"):
    wins(D3, o, f"delay3:{o}")
A = load("rdq_events_ann.parquet", [("d2_21", 1, 21), ("d2_61", 1, 61)])
for o in ("d2_21", "d2_61"):
    wins(A, o, f"ann:{o}")
X = load("rdq_events_exp.parquet", [], exit_col="kx")
wins(X, "hold", "exp:hold")
print(f"events: delay k=1 {len(D1)}, delay k=3 {len(D3)}, announcements {len(A)}, expected window {len(X)}; years {sorted(D1.year.unique())}")


def T(D):
    return pd.Series(True, index=D.index)


def ic(D):
    return D.ins_cov.astype(bool) & (D.date >= "2015-07-01")


print("[family R - the ten frozen candidates]")
stat("R01", A, terc(A.sue_act, "ann:terc:sue_act"), A.rk > 1000, "d2_21", "announced-quarter SUE top vs bottom tercile, rank 1001-3000")
stat("R02", D3, D3.rk > 2000, T(D3), "w20", "delay k=3: size rank beyond 2000")
stat("R03", D1, D1.fq4, D1.rk > 1000, "w20", "delay k=1: fiscal fourth quarter, rank 1001-3000")
stat("R04", D3, D3.loss_prev, D3.k8cov.astype(bool), "hold", "delay k=3: loss in the prior quarter, 8-K history")
stat("R05", D1, terc(D1.sd_dev8, "delay1:terc:sd_dev8"), T(D1), "hold", "delay k=1: irregular announcement dates, top vs bottom tercile")
stat("R06", A, A.dev_td >= 10, T(A), "d2_21", "announced 10+ trading days late: days 2-21 after")
stat("R07", D1, (D1.ins_s > 0) & (D1.ins_p == 0), ic(D1) & (D1.rk <= 1000), "w20", "delay k=1: insiders only sold in prior 180 days, rank 1-1000")
stat("R08", D1, D1.ins_p > 0, ic(D1) & D1.k8cov.astype(bool), "hold", "delay k=1: insider bought in prior 180 days, 8-K history")
stat("R09", D1, D1.nt365 > 0, T(D1), "w10", "delay k=1: NT filing in prior 365 days")
stat("R10", X, X.ins_p > 0, ic(X) & X.k8cov.astype(bool), "hold", "expected window: insider bought in prior 180 days, 8-K history")
print("[family R - reported with the candidates, not used for the verdict]")
stat("R06", A, A.dev_td >= 10, T(A), "d2_21", "  with controls (size, price, prior loss, momentum, prior SUE)", ctrl=True, record=False)
stat("R06", A, A.dev_td >= 10, A.sue_act < 0, "d2_21", "  among negative announced SUE", record=False)
stat("R06", A, A.dev_td >= 10, A.rk > 1000, "d2_21", "  rank 1001-3000", record=False)
stat("R06", A, A.dev_td >= 10, A.rk <= 1000, "d2_21", "  rank 1-1000", record=False)
stat("R06", A, A.dev_td >= 10, T(A), "d2_61", "  days 2-61", record=False)
stat("R06", A, A.dev_td >= 5, T(A), "d2_21", "  5+ trading days late", record=False)
stat("R07", D1, (D1.ins_s > 0) & (D1.ins_p == 0), ic(D1) & (D1.rk <= 1000), "w20", "  with controls", ctrl=True, record=False)
stat("R08", D1, D1.ins_p > 0, ic(D1) & D1.k8cov.astype(bool), "hold", "  with controls", ctrl=True, record=False)
stat("R05", D1, terc(D1.sd_dev8, "delay1:terc:sd_dev8"), T(D1), "hold", "  with controls", ctrl=True, record=False)
stat("R03", D1, D1.fq4, D1.rk > 1000, "w20", "  with controls", ctrl=True, record=False)
for nm, D_ in (("delay k=1 hold", D1), ("delay k=3 hold", D3)):
    y = D_.y_hold.dropna()
    m, t, n = L.level_test(y.values, L.codes(D_.loc[y.index, "ym"].values))
    print(f"   base effect, {nm}: {m:+.3f}% (t {t:+.2f}), n {n}")
print("   R06 by year (level, n):", {int(y): (round(v.y_d2_21.mean(), 2), int(v.y_d2_21.notna().sum())) for y, v in A[A.dev_td >= 10].groupby("year")})

print("[family S - the one frozen candidate]")
E = pd.read_parquet(L.CACHE / "sec_events.parquet")
S = E[E.stage == STAGE].copy()
S = S.merge(L.ar_windows(S, [("w126", 0, 126)], allow=(STAGE,)), on="eid")
lo, hi = sc["cut"]["w126"]
S["y_w126"] = S.ar_w126.clip(lo, hi)
q1, q2 = sc["cut"]["terc_first_ncomm"]
tf = S.txt_first.astype(bool) & (S.first_ltype == "COMMENT")
fl = pd.Series(np.where(S.first_ncomm > q2, 1.0, np.where(S.first_ncomm <= q1, 0.0, np.nan)), index=S.index)
big = S.cap >= sc["cap_med"]
y = S.y_w126.values


def sstat(cid, flag, base, label, Z=None, record=True):
    m = (base & flag.notna()).values & ~np.isnan(y)
    if Z is not None:
        m = m & ~np.isnan(Z).any(axis=1)
    fe, g = L.codes(S.year.values[m]), L.codes(S.ym.values[m])
    if Z is not None:
        b, t, n1, n0 = L.diff_test_ctrl(y[m], flag.values[m], Z[m], fe, g)
    else:
        b, t, n1, n0 = L.diff_test(y[m], flag.values[m], fe, g)
    m1 = m & (flag.values == 1)
    lv, lt, _ = L.level_test(y[m1], L.codes(S.ym.values[m1])) if m1.sum() > 1 else (np.nan, np.nan, 0)
    print(f"   {cid:4s} {label:62s} n1 {n1:6d} n0 {n0:6d} | diff {b:+7.3f} (t {t:+5.2f}) | level {lv:+7.3f} (t {lt:+5.2f})")
    if record:
        res.append(dict(id=cid, stage=STAGE, label=label, diff=b, t=t, n1=n1, n0=n0, level1=lv, t_level1=lt))


sstat("S01", fl, tf & big, "comments in the first letter, top vs bottom tercile, big firms, 126 days")
seas = S.seasoned.astype(bool)
sstat("S01", fl, tf & big & seas, "  listed 3+ years only", record=False)
sstat("S01", fl, tf & big & ~seas, "  newly listed only", record=False)
S["eid2"] = S.eid
pr = L.past_returns(S.assign(eid=S.eid), [("mom126", -126, 0)])
S = S.merge(pr, on="eid", how="left")
Z = np.column_stack([np.log(S.cap.where(S.cap > 0)).values, S.mom126.values, (~seas).astype(float).values])
sstat("S01", fl, tf & big, "  with controls (size, prior return, newly listed)", Z=Z, record=False)
nl = (~seas)
m = nl.values & ~np.isnan(y)
mm, tt, nn = L.level_test(y[m], L.codes(S.ym.values[m]))
print(f"   all conversations of newly listed firms, 126 days: {mm:+.2f}% (t {tt:+.2f}), n {nn}")
pd.DataFrame(res).to_csv(L.OUT / f"confirm_{STAGE}.csv", index=False)
