"""Phase 7 - step 42: independent check of R05 with a different code path (follow-up; full period).

Differences from the phase-7 pipeline:
  events        the phase-4 agent's one-day-delay table (its own identifier link, universe and silence rule; Compustat dates only)
  irregularity  recomputed here from Compustat announcement dates in calendar days (as in the round-2 script p5_10), terciles within entry year
  returns       date-based SQL on the CRSP extract (no calendar-index machinery); benchmark = the universe series built by p5_10
Run: python p7_42_r05_independent.py
"""
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd
import statsmodels.api as sm

from v2paths import MC_DIR
HERE = MC_DIR / "phase7"
MC = HERE.parent
ROOT = MC.parent
SLIM = (ROOT / "RDQ_cadence" / "dsf_v2_slim.parquet").as_posix()
con = duckdb.connect()
con.execute("SET memory_limit='7GB'")

E = pd.read_parquet(ROOT / "RDQ_cadence" / "phase4" / "out" / "r1_events_o1.parquet")
E = E[(E.entry >= "2005-01-01") & (E.entry <= "2024-12-31")].copy()
fq = pd.read_parquet(MC / "r1_cache" / "fundq_rdq.parquet")
fq["datadate"] = pd.to_datetime(fq.datadate)
fq["rdq"] = pd.to_datetime(fq.rdq)
V = fq[fq.rdq.notna() & (fq.rdq > fq.datadate) & fq.fyearq.notna() & fq.fqtr.notna()].copy()
V = V.sort_values(["gvkey", "fyearq", "fqtr", "datadate"]).drop_duplicates(["gvkey", "fyearq", "fqtr"], keep="last")
prev = V[["gvkey", "fyearq", "fqtr", "rdq"]].rename(columns={"rdq": "rdq_prev"})
prev["fyearq"] = prev.fyearq + 1
V = V.merge(prev, on=["gvkey", "fyearq", "fqtr"], how="left")
V["dev"] = (V.rdq - (V.rdq_prev + pd.DateOffset(years=1))).dt.days
V = V[V.dev.notna() & (V.dev.abs() <= 120)].sort_values(["gvkey", "rdq"])
hist = {g: (d.rdq.values.astype("datetime64[ns]"), d.dev.values.astype(float)) for g, d in V.groupby("gvkey")}
sd = []
for g, e in zip(E.gvkey.values, E.E.values.astype("datetime64[ns]")):
    h = hist.get(g)
    if h is None:
        sd.append(np.nan)
        continue
    k = np.searchsorted(h[0], e, side="left")
    x = h[1][max(0, k - 8):k]
    sd.append(np.std(x, ddof=1) if len(x) >= 6 else np.nan)
E["sd_cal"] = sd
E = E[E.sd_cal.notna()].copy()
E["year"] = E.entry.dt.year
E["ter"] = E.groupby("year").sd_cal.transform(lambda s: pd.qcut(s.rank(method="first"), 3, labels=False))
con.register("ev", E[["eid", "permno", "entry", "exit"]])
R = con.execute(f"""SELECT e.eid, exp(sum(ln(greatest(1 + s.dlyret, 1e-9)))) - 1 AS r, count(*) AS nd
                    FROM ev e JOIN '{SLIM}' s ON s.permno = e.permno AND s.date > e.entry AND s.date <= e.exit
                    WHERE s.dlyret IS NOT NULL GROUP BY 1""").df()
E = E.merge(R, on="eid")
U = pd.read_parquet(MC / "phase5" / "cache" / "univ_ew.parquet")
U["date"] = pd.to_datetime(U["date"])
clog = np.log1p(U.sort_values("date").set_index("date").ew).cumsum()
E["bench"] = np.expm1(clog.reindex(E["exit"]).values - clog.reindex(E.entry).values)
E = E.dropna(subset=["bench"])
E["ar"] = ((E.r - E.bench) * 100).clip(-30, 30)
E["ym"] = E.year * 100 + E.entry.dt.month
print(f"agent-built one-day-delay events with an irregularity measure, 2005-2024: {len(E)}; median sd (calendar days) by tercile: {E.groupby('ter').sd_cal.median().round(1).to_dict()}")


def lev(d, label):
    f = sm.OLS(d.ar.values, np.ones(len(d))).fit(cov_type="cluster", cov_kwds={"groups": d.ym.values})
    return f"{label} {f.params[0]:+.3f}% (t {f.tvalues[0]:+.2f}, n {len(d)})"


def diff(d, label):
    X = pd.get_dummies(d.year, prefix="y", drop_first=True).astype(float)
    X.insert(0, "IRR", (d.ter == 2).astype(float).values)
    X.insert(1, "MID", (d.ter == 1).astype(float).values)
    f = sm.OLS(d.ar.values, sm.add_constant(X.values, has_constant="add")).fit(cov_type="cluster", cov_kwds={"groups": d.ym.values})
    print(f"   {label:28s} | {lev(d[d.ter == 2], 'IRR')} | {lev(d[d.ter == 0], 'REG')} | IRR - REG {f.params[1]:+.3f}pp (t {f.tvalues[1]:+.2f})")


diff(E, "2005-2024")
diff(E[E.year <= 2014], "2005-2014")
diff(E[E.year >= 2015], "2015-2024")
diff(E[E.year % 2 == 0], "even years")
diff(E[E.year % 2 == 1], "odd years")
diff(E[E.rk <= 1000], "size rank 1-1000")
diff(E[E.rk > 1000], "size rank 1001-3000")
