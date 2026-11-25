"""Phase 6 - RDQ-F: does the direction of insider trading before a missed earnings date separate the delays that matter?

Fixed in PHASE6_SPEC.md section 2 before any return was computed:
  sample   SEC-verified silent overdue events of R1 with expected date E >= 2015-07-01 and Form 4 records of the issuer
           in the entry year or the year before
  D        +1 if an officer or director bought on the open market in [E - 180d, E), -1 if insiders only sold, 0 otherwise
  outcome  holding-period return (R1 entry and exit) minus the equal-weighted universe return over the same days, percent
  model    outcome ~ D + log(market cap at entry) + entry-year fixed effects, clustered by entry month; expected sign of D positive
  pass     |t| >= 2.64, same sign in 2015-2019 and 2020-2024, later half alone |t| >= 1.96
Run: python p6_01_rdq_insider.py
"""
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd
import statsmodels.api as sm

from v2paths import MC_DIR
HERE = MC_DIR / "phase6"
MC = HERE.parent
ROOT = MC.parent
SLIM = (ROOT / "RDQ_cadence" / "dsf_v2_slim.parquet").as_posix()
con = duckdb.connect()
con.execute("SET memory_limit='7GB'")

E = pd.read_parquet(MC / "r1_cache" / "r1_events_sec_verified.parquet")
E = E[E.grp == "verified silent"].copy()
for c in ("E", "t_e", "exit"):
    E[c] = pd.to_datetime(E[c]).astype("datetime64[ns]")
E["cik10"] = E.cik10.astype(str)
E["year"] = E.t_e.dt.year
E = E[E.E >= "2015-07-01"].copy()
P = pd.read_parquet(MC / "x2a_cache" / "issuer_presence.parquet")
pres = set(zip(P.cik, P.year))
E = E[[((c, y) in pres) or ((c, y - 1) in pres) for c, y in zip(E.cik10, E.year)]].copy()

S = pd.read_parquet(MC / "x2a_cache" / "od_sales.parquet")
S["d"] = pd.to_datetime(S.dt.astype(str), format="%Y%m%d", errors="coerce")
by = {c: (g.d.values.astype("datetime64[ns]"), g.code.values) for c, g in S.dropna(subset=["d"]).sort_values("d").groupby("cik")}
D = []
for c, e in zip(E.cik10.values, E.E.values.astype("datetime64[ns]")):
    g = by.get(c)
    if g is None:
        D.append(0)
        continue
    lo, hi = np.searchsorted(g[0], e - np.timedelta64(180, "D"), side="left"), np.searchsorted(g[0], e, side="left")
    codes = g[1][lo:hi]
    D.append(1 if (codes == "P").any() else (-1 if (codes == "S").any() else 0))
E["D"] = D
print(f"[sample] events {len(E)}: insiders bought {int((E.D == 1).sum())}, only sold {int((E.D == -1).sum())}, neither {int((E.D == 0).sum())}; by half {int((E.year <= 2019).sum())} / {int((E.year >= 2020).sum())}")

U = pd.read_parquet(MC / "phase5" / "cache" / "univ_ew.parquet")
U["date"] = pd.to_datetime(U["date"])
clog = np.log1p(U.sort_values("date").set_index("date").ew).cumsum()
con.register("ev", E[["eid", "permno", "t_e", "exit"]])
R = con.execute(f"""SELECT e.eid, exp(sum(ln(greatest(1 + s.dlyret, 1e-9)))) - 1 AS r, count(*) AS nd
                    FROM ev e JOIN '{SLIM}' s ON s.permno = e.permno AND s.date > e.t_e AND s.date <= e.exit
                    WHERE s.dlyret IS NOT NULL GROUP BY 1""").df()
C = con.execute(f"SELECT e.eid, s.dlycap cap FROM ev e JOIN '{SLIM}' s ON s.permno = e.permno AND s.date = e.t_e").df()
E = E.merge(R, on="eid").merge(C, on="eid")
E["bench"] = np.expm1(clog.reindex(E["exit"]).values - clog.reindex(E.t_e).values)
E = E.dropna(subset=["bench", "cap"])
E = E[E.cap > 0].copy()
E["ar"] = (E.r - E.bench) * 100
E["lcap"] = np.log(E.cap)
E["ym"] = E.t_e.dt.year * 100 + E.t_e.dt.month
E.to_parquet(HERE / "rdq_f_events.parquet", index=False)


def run(d, label, xvar="D", size=True):
    X = pd.get_dummies(d.year, prefix="y", drop_first=True).astype(float)
    X.insert(0, xvar, d[xvar].astype(float).values)
    if size:
        X.insert(1, "lcap", d.lcap.values)
    f = sm.OLS(d.ar.values, sm.add_constant(X.values, has_constant="add")).fit(cov_type="cluster", cov_kwds={"groups": d.ym.values, "use_correction": True})
    tail = f" | log cap {f.params[2]:+.3f} (t {f.tvalues[2]:+.2f})" if size else ""
    print(f"   {label:46s} n {len(d):5d} months {d.ym.nunique():3d} | {xvar} {f.params[1]:+.3f}pp (t {f.tvalues[1]:+.2f}){tail}")


print("[RDQ-F primary] holding-period abnormal return on insider direction D (+1 bought, 0 none, -1 only sold); expected sign positive; "
      "pass needs |t| >= 2.64, both halves positive, later half |t| >= 1.96")
run(E, "2015-2024")
run(E[E.year <= 2019], "2015-2019")
run(E[E.year >= 2020], "2020-2024")
print("[RDQ-F side reports]")
m = E.groupby("D").ar.agg(["mean", "median", "size"])
print("   mean abnormal return by group:", {int(k): (round(v["mean"], 3), int(v["size"])) for k, v in m.iterrows()}, f"| all events {E.ar.mean():+.3f}% over {E.nd.mean():.1f} days")
E["BUY"] = (E.D == 1).astype(float)
E["SELL"] = (E.D == -1).astype(float)
run(E, "bought vs the rest", xvar="BUY")
run(E, "only sold vs the rest", xvar="SELL")
run(E, "D without the size control", size=False)
run(E[E.rk > 1000], "D, size rank 1001-3000")
run(E[E.rk <= 1000], "D, size rank 1-1000")
