"""Phase 7 - step 40: follow-up of the confirmed candidate R05 (PHASE7_SEARCH_PROTOCOL.md section 3, item 3).

R05: among firms still silent one trading day after their expected announcement date, those with irregular past
announcement timing (sd of the timing deviation over the previous 8 quarters above 3.93 trading days = top tercile on the
discovery years) do worse until the day after they announce than those with regular timing (sd <= 2.20).

  python p7_40_r05_followup.py          full period 2004-2024: calendar-time alphas, costs, decomposition
  python p7_40_r05_followup.py rec      the 2025 record (run once, last)
"""
import json
import sys
import warnings

import numpy as np
import pandas as pd
import statsmodels.api as sm

import p7lib as L

warnings.simplefilter("ignore")
REC = len(sys.argv) > 1 and sys.argv[1] == "rec"
cuts = json.load(open(L.OUT / "rdq_search_cuts.json"))
q1, q2 = cuts["delay1:terc:sd_dev8"]
FC = ["mktrf", "smb", "hml", "rmw", "cma", "umd"]
cal = L.calendar()
c = L.con()
ff = c.execute(f"SELECT * FROM read_csv('{L.DUMP}/ff_all.fivefactors_daily.csv.gz', header=true)").df()
ff["date"] = pd.to_datetime(ff["date"])
ff = ff.set_index("date").astype(float)

ev = pd.read_parquet(L.CACHE / "rdq_events_delay.parquet")
ev = ev[(ev.kd == 1) & (ev.year >= 2004)].copy()
ev["grp"] = np.where(ev.sd_dev8 > q2, "IRR", np.where(ev.sd_dev8 <= q1, "REG", np.where(ev.sd_dev8.notna(), "MID", "NA")))

if REC:
    D = ev[ev.stage == "rec"].copy()
    D["eid"] = np.arange(len(D))
    D = D.merge(L.ar_windows(D, [("w5", 0, 5), ("w20", 0, 20)], allow=("rec",), exit_col="kx"), on="eid")
    lo, hi = cuts["delay1:hold"]
    D["y"] = D.ar_hold.clip(lo, hi)
    print(f"=== 2025 record: delay k=1 events entered in 2025: {len(D)}; by group {D.grp.value_counts().to_dict()}; last entry {D.date.max().date()}")
    d = D[D.grp.isin(["IRR", "REG"]) & D.y.notna()]
    b, t, n1, n0 = L.diff_test(d.y.values, (d.grp == "IRR").astype(float).values, np.zeros(len(d), dtype=int), L.codes(d.ym.values))
    print(f"   R05 on 2025: irregular minus regular {b:+.3f}pp (t {t:+.2f}, month-clustered, {d.ym.nunique()} months), n {n1} / {n0}")
    for gname in ("IRR", "MID", "REG"):
        x = D[(D.grp == gname) & D.y.notna()]
        m, tt, n = L.level_test(x.y.values, L.codes(x.ym.values))
        print(f"   level {gname}: {m:+.3f}% (t {tt:+.2f}), n {n}, mean days held {x.n_hold.mean():.1f}")
    sys.exit(0)

D = ev[ev.stage.isin(["disc", "conf"])].copy()
D["eid"] = np.arange(len(D))
A = L.ar_windows(D, [("w1", 0, 1), ("w5", 0, 5), ("w10", 0, 10), ("w20", 0, 20)], allow=("disc", "conf"), exit_col="kx")
D = D.merge(A, on="eid")
lo, hi = cuts["delay1:hold"]
D["y"] = D.ar_hold.clip(lo, hi)
D["late_td"] = np.where(D.k_ann < 10 ** 7, D.k_ann - D.kE, np.nan)
print(f"=== R05 follow-up, 2004-2024: delay k=1 events {len(D)}; groups {D.grp.value_counts().to_dict()}")
print("[1] what the groups look like (no returns)")
g = D[D.grp.isin(["IRR", "MID", "REG"])].groupby("grp")
print(pd.DataFrame({"events": g.size(), "days_held_mean": g.n_hold.mean().round(1), "days_held_median": g.n_hold.median(), "eventual_lateness_median": g.late_td.median(),
                    "eventual_lateness_p75": g.late_td.quantile(.75), "late_5plus_share": g.late_td.apply(lambda s: (s >= 5).mean()).round(3),
                    "size_rank_median": g.rk.median(), "price_median": g.prc.median().round(1), "prior_loss_share": g.loss_prev.mean().round(3)}).to_string())

print("[2] event-level abnormal return (stock minus equal-weighted universe), percent")
for out in ("hold", "w1", "w5", "w10", "w20"):
    col = "y" if out == "hold" else "ar_" + out
    line = f"   {out:5s}"
    for gname in ("IRR", "MID", "REG"):
        x = D[(D.grp == gname) & D[col].notna()]
        v = x[col].clip(*cuts.get(f"delay1:{out}", (lo, hi)))
        m, t, n = L.level_test(v.values, L.codes(x.ym.values))
        line += f" | {gname} {m:+.3f} (t {t:+5.2f})"
    d = D[D.grp.isin(["IRR", "REG"]) & D[col].notna()]
    v = d[col].clip(*cuts.get(f"delay1:{out}", (lo, hi)))
    b, t, n1, n0 = L.diff_test(v.values, (d.grp == "IRR").astype(float).values, L.codes(d.year.values), L.codes(d.ym.values))
    print(line + f" | IRR - REG {b:+.3f} (t {t:+5.2f})")
print("   per day held: abnormal return / days held")
for gname in ("IRR", "MID", "REG"):
    x = D[(D.grp == gname) & D.y.notna()]
    print(f"   {gname}: {x.y.sum() / x.n_hold.sum() * 100:+.2f} bp per position-day ({int(x.n_hold.sum())} position-days)")
print("[3] IRR - REG on the holding-period return by subsample (year fixed effects, month clusters)")


def sub(mask, label):
    d = D[mask & D.grp.isin(["IRR", "REG"]) & D.y.notna()]
    if (d.grp == "IRR").sum() < 100 or (d.grp == "REG").sum() < 100:
        print(f"   {label:40s} too few events")
        return
    b, t, n1, n0 = L.diff_test(d.y.values, (d.grp == "IRR").astype(float).values, L.codes(d.year.values), L.codes(d.ym.values))
    x = d[d.grp == "IRR"]
    m, tt, _ = L.level_test(x.y.values, L.codes(x.ym.values))
    print(f"   {label:40s} n {n1:5d} / {n0:5d} | IRR - REG {b:+.3f} (t {t:+5.2f}) | IRR level {m:+.3f} (t {tt:+5.2f})")


ALL = pd.Series(True, index=D.index)
sub(ALL, "2004-2024")
sub(D.year <= 2013, "2004-2013")
sub(D.year >= 2014, "2014-2024")
for a, b_ in [(2004, 2008), (2009, 2013), (2014, 2018), (2019, 2024)]:
    sub((D.year >= a) & (D.year <= b_), f"{a}-{b_}")
sub(D.rk <= 1000, "size rank 1-1000")
sub((D.rk > 1000) & (D.rk <= 2000), "size rank 1001-2000")
sub(D.rk > 2000, "size rank 2001-3000")
sub(D.k8cov.astype(bool), "8-K history available (silence verified)")
sub(D.fqtr == 4, "fiscal Q4")
sub(D.fqtr != 4, "fiscal Q1-Q3")
sub(D.n_late8 == 0, "never 5+ days late in the previous 8 quarters")
sub(D.n_late8 >= 1, "5+ days late at least once before")

print("[4] calendar-time portfolios (daily equal-weighted, days with >= 10 names), FF5+UMD intercept, Newey-West(5)")
c.register("evp", D[["eid", "permno", "k0", "kx"]])
R = c.execute(f"SELECT e.eid, r.k, exp(r.lr) - 1 AS ret FROM evp e JOIN '{L.ret_k()}' r ON r.permno = e.permno AND r.k > e.k0 AND r.k <= e.kx").df()
R = R.merge(D[["eid", "grp", "year", "rk", "permno", "k0", "kx"]], on="eid")
R["date"] = cal.date.values[R.k.values]
R["first"] = R.k == R.k0 + 1
R["last"] = R.k == R.groupby("eid").k.transform("max")
# costs: half the quoted closing spread at entry and at exit, plus 1% a year borrow
q = pd.concat([D[["permno", "k0"]].rename(columns={"k0": "k"}), R[R["last"]][["permno", "k"]]]).drop_duplicates()
q["date"] = cal.date.values[q.k.values]
q["date"] = q["date"].dt.date
c.register("qq", q[["permno", "date", "k"]])
qs = c.execute(f"""SELECT q.permno, q.k, (b.ask - b.bid) / ((b.ask + b.bid) / 2) qs FROM qq q JOIN '{L.BIDASK}' b ON b.permno = q.permno AND b.date = q.date
                   WHERE b.bid > 0 AND b.ask >= b.bid AND (b.ask - b.bid) / ((b.ask + b.bid) / 2) < 1""").df()
R = R.merge(qs.rename(columns={"k": "k0", "qs": "qs_in"}), on=["permno", "k0"], how="left")
R = R.merge(qs.rename(columns={"qs": "qs_out"}), on=["permno", "k"], how="left")
med = float(qs.qs.median())
dcal = np.r_[1, np.diff(cal.date.values).astype("timedelta64[D]").astype(int)]
R["cost"] = np.where(R["first"], R.qs_in.fillna(med) / 2, 0.0) + np.where(R["last"], R.qs_out.fillna(med) / 2, 0.0) + 0.01 * dcal[R.k.values] / 365.0
print(f"   median quoted spread at entry/exit {med * 1e4:.0f}bp; mean by group at entry: " + ", ".join(f"{k} {v * 1e4:.0f}bp" for k, v in R[R['first']].groupby('grp').qs_in.mean().items()))


def port(mask, label, short_net=False):
    d = R[mask]
    gb = d.groupby("date")
    p, n = gb.ret.mean(), gb.ret.size()
    p = p[n >= 10]
    if len(p) < 250:
        print(f"   {label:46s} only {len(p)} days")
        return None
    x = pd.DataFrame({"p": p, "n": n[n >= 10]}).join(ff, how="inner")
    if short_net:
        y = -(x.p - x.rf) - gb.cost.mean().reindex(x.index)
    else:
        y = x.p - x.rf
    f = sm.OLS(y, sm.add_constant(x[FC])).fit(cov_type="HAC", cov_kwds={"maxlags": 5})
    print(f"   {label:46s} days {len(x):5d} names {x.n.mean():6.1f} | alpha {f.params['const'] * 1e4:+6.2f}bp/day (t {f.tvalues['const']:+5.2f})")
    return x.p


for gname in ("IRR", "MID", "REG"):
    port(R.grp == gname, f"{gname}, 2004-2024")
pi = port(R.grp == "IRR", "IRR (again, for the spread)")
pr = port(R.grp == "REG", "REG (again, for the spread)")
j = pd.concat([pi.rename("i"), pr.rename("r")], axis=1).dropna().join(ff, how="inner")
f = sm.OLS(j.i - j.r, sm.add_constant(j[FC])).fit(cov_type="HAC", cov_kwds={"maxlags": 5})
print(f"   IRR minus REG on common days                   days {len(j):5d}               | alpha {f.params['const'] * 1e4:+6.2f}bp/day (t {f.tvalues['const']:+5.2f})")
port((R.grp == "IRR") & (R.year <= 2013), "IRR, entries 2004-2013")
port((R.grp == "IRR") & (R.year >= 2014), "IRR, entries 2014-2024")
port((R.grp == "IRR") & (R.year % 2 == 0), "IRR, discovery (even) years")
port((R.grp == "IRR") & (R.year % 2 == 1), "IRR, confirmation (odd) years")
port((R.grp == "IRR") & (R.rk <= 1000), "IRR, size rank 1-1000")
port((R.grp == "IRR") & (R.rk > 1000), "IRR, size rank 1001-3000")
print("   short side net of half-spreads and a 1% borrow fee (expected sign positive):")
port(R.grp == "IRR", "short IRR, net, 2004-2024", short_net=True)
port((R.grp == "IRR") & (R.year <= 2013), "short IRR, net, 2004-2013", short_net=True)
port((R.grp == "IRR") & (R.year >= 2014), "short IRR, net, 2014-2024", short_net=True)
port((R.grp == "IRR") & (R.rk <= 1000), "short IRR, net, size rank 1-1000", short_net=True)
