"""Phase 7 - step 22: family R search on the DISCOVERY years only (even entry years <= 2024).

Grid = event set x outcome window x condition x universe (PHASE7_SEARCH_PROTOCOL.md section 2.2). Statistic = mean abnormal return
of events with the condition minus those without, entry-year fixed effects, clustered by entry month; the level of the
condition = 1 group is reported next to it. Only events with stage == "disc" get returns.
Run: python p7_22_rdq_search.py
"""
import json
import warnings

import numpy as np
import pandas as pd

import p7lib as L

warnings.simplefilter("ignore")
cuts = {}


def prep(ev, windows, exit_col=None):
    D = ev[ev.stage == "disc"].copy()
    D["eid"] = np.arange(len(D))
    A = L.ar_windows(D, windows, allow=("disc",), exit_col=exit_col)
    D = D.merge(A, on="eid")
    return D


def winsor(D, cols, tag):
    for c_ in cols:
        lo, hi = D["ar_" + c_].quantile([.01, .99])
        cuts[f"{tag}:{c_}"] = (float(lo), float(hi))
        D["y_" + c_] = D["ar_" + c_].clip(lo, hi)
    return D


def conds_common(D, tag):
    C = {}
    ALL = pd.Series(True, index=D.index)

    def add(name, flag, base=ALL):
        C[name] = (flag.astype(float), base & flag.notna())

    def terc(name, v, base=ALL):
        x = v[base & v.notna()]
        if x.nunique() < 3:
            return
        q1, q2 = x.quantile([1 / 3, 2 / 3])
        cuts[f"{tag}:terc:{name}"] = (float(q1), float(q2))
        f = pd.Series(np.nan, index=D.index)
        f[v <= q1] = 0.0
        f[v > q2] = 1.0
        C[name + "_hi"] = (f, base & f.notna())

    sp = D.sue_prev
    add("sue_prev_neg", (sp < 0).where(sp.notna()))
    terc("sue_prev", sp)
    add("loss_prev", D.loss_prev)
    terc("mom", D.mom)
    terc("r1m", D.r1m)
    add("small_rk1000", D.rk > 1000)
    add("small_rk2000", D.rk > 2000)
    add("prc_lt10", D.prc < 10)
    add("fq4", D.fq4)
    add("financial", D.sic1 == "6")
    add("tech_sic7", D.sic1 == "7")
    nl = D.n_late8
    add("late_before_1plus", (nl >= 1).where(nl.notna()))
    add("late_before_2plus", (nl >= 2).where(nl.notna()))
    terc("sd_dev8", D.sd_dev8)
    add("nt365", D.nt365 > 0)
    kh = D.k8hist.astype(bool)
    add("k401_auditor_change", D.k401 > 0, kh)
    add("k402_nonreliance", D.k402 > 0, kh)
    add("k502_officer_change", D.k502 > 0, kh)
    add("k2056_restructuring_impairment", D.k2056 > 0, kh)
    ic = D.ins_cov.astype(bool) & (D.date >= "2015-07-01")
    add("insider_sell_only", (D.ins_s > 0) & (D.ins_p == 0), ic)
    add("insider_buy", D.ins_p > 0, ic)
    terc("si_ratio", D.si_ratio)
    terc("si_chg", D.si_chg)
    add("letter_365", D.let365 > 0)
    add("letter3_365", D.let3_365 > 0)
    return C, add, terc


def univs(D):
    ALL = pd.Series(True, index=D.index)
    return {"all": ALL, "rank_1_1000": D.rk <= 1000, "rank_1001_3000": D.rk > 1000, "8k_history": D.k8cov.astype(bool)}


def run(D, C, U, outs, setname):
    fe, g = L.codes(D.year.values), L.codes(D.ym.values)
    rows = []
    for cn, (flag, base) in C.items():
        for un, um in U.items():
            if (cn.startswith("small_rk") and un.startswith("rank_")):
                continue
            m0 = (base & um).values
            for o in outs:
                y = D["y_" + o].values
                m = m0 & ~np.isnan(y)
                if m.sum() < 100:
                    continue
                x = flag.values[m]
                b, t, n1, n0 = L.diff_test(y[m], x, L.codes(fe[m]), L.codes(g[m]))
                m1 = m & (flag.values == 1)
                lv, lt, _ = L.level_test(y[m1], L.codes(g[m1])) if m1.sum() > 1 else (np.nan, np.nan, 0)
                rows.append(dict(set=setname, cond=cn, univ=un, out=o, diff=b, t=t, n1=n1, n0=n0, level1=lv, t_level1=lt))
    return rows


rows = []
# ---------------- delay ----------------
DEL = pd.read_parquet(L.CACHE / "rdq_events_delay.parquet")
DEL = DEL[(DEL.year >= 2004)]
for kd in (1, 3, 5, 10):
    D = prep(DEL[DEL.kd == kd], [("w5", 0, 5), ("w10", 0, 10), ("w20", 0, 20)], exit_col="kx")
    D = winsor(D, ["hold", "w5", "w10", "w20"], f"delay{kd}")
    fe, g = L.codes(D.year.values), L.codes(D.ym.values)
    for o in ("hold", "w5", "w10", "w20"):
        y = D["y_" + o].dropna()
        m, t, n = L.level_test(y.values, L.codes(D.loc[y.index, "ym"].values))
        print(f"[delay k={kd}] base effect, {o:5s}: {m:+.3f}% (t {t:+.2f}), n {n}")
    C, add, terc = conds_common(D, f"delay{kd}")
    rows += run(D, C, univs(D), ["hold", "w5", "w10", "w20"], f"delay{kd}")
    D.to_parquet(L.OUT / f"rdq_disc_delay{kd}.parquet", index=False)

# ---------------- announcements ----------------
ANN = pd.read_parquet(L.CACHE / "rdq_events_ann.parquet")
ANN = ANN[ANN.year >= 2004]
D = prep(ANN, [("d2_21", 1, 21), ("d2_61", 1, 61)])
D = winsor(D, ["d2_21", "d2_61"], "ann")
for o in ("d2_21", "d2_61"):
    y = D["y_" + o].dropna()
    m, t, n = L.level_test(y.values, L.codes(D.loc[y.index, "ym"].values))
    print(f"[ann] base effect, {o}: {m:+.3f}% (t {t:+.2f}), n {n}")
C, add, terc = conds_common(D, "ann")
dv, sa = D.dev_td, D.sue_act
add("early_5plus", dv <= -5)
add("late_5plus", dv >= 5)
add("late_10plus", dv >= 10)
add("sue_act_neg", (sa < 0).where(sa.notna()))
terc("sue_act", sa)
add("late5_and_sue_neg", (dv >= 5) & (sa < 0), sa.notna())
add("late5_and_sue_pos", (dv >= 5) & (sa > 0), sa.notna())
add("early5_and_sue_pos", (dv <= -5) & (sa > 0), sa.notna())
add("early5_and_sue_neg", (dv <= -5) & (sa < 0), sa.notna())
la = D.loss_act
add("loss_act", la)
add("late5_and_loss", (dv >= 5) & (la == 1), la.notna())
rows += run(D, C, univs(D), ["d2_21", "d2_61"], "ann")
D.to_parquet(L.OUT / "rdq_disc_ann.parquet", index=False)

# ---------------- expected window ----------------
EXP = pd.read_parquet(L.CACHE / "rdq_events_exp.parquet")
EXP = EXP[EXP.year >= 2004]
D = prep(EXP, [], exit_col="kx")
D = winsor(D, ["hold"], "exp")
y = D.y_hold.dropna()
m, t, n = L.level_test(y.values, L.codes(D.loc[y.index, "ym"].values))
print(f"[exp] base effect, expected window: {m:+.3f}% (t {t:+.2f}), n {n}")
C, add, terc = conds_common(D, "exp")
rows += run(D, C, univs(D), ["hold"], "exp")
D.to_parquet(L.OUT / "rdq_disc_exp.parquet", index=False)

R = pd.DataFrame(rows)
R.to_csv(L.OUT / "rdq_search_disc.csv", index=False)
json.dump(cuts, open(L.OUT / "rdq_search_cuts.json", "w"), indent=1)
ok = R[(R.n1 >= 200) & (R.n0 >= 200)]
print(f"combinations evaluated: {len(R)}; with at least 200 events on each side: {len(ok)}; |t| >= 3.0: {int((ok.t.abs() >= 3).sum())}; |t| >= 4.0: {int((ok.t.abs() >= 4).sum())}; "
      f"expected by chance at |t| >= 3.0 if independent: {len(ok) * 0.0027:.1f}")
pd.set_option("display.width", 220)
for s in ("delay1", "delay3", "delay5", "delay10", "ann", "exp"):
    o = ok[ok.set == s]
    print(f"--- {s}: {len(o)} combinations, |t| >= 3: {int((o.t.abs() >= 3).sum())}")
    print(o.reindex(o.t.abs().sort_values(ascending=False).index).head(14).round(3).to_string(index=False))
