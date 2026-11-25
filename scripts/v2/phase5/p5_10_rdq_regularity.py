"""Phase 5 - RDQ-R: does the information in an earnings delay depend on how regular the firm's reporting dates are?

Sample: SEC-verified silent overdue events of R1 (2005-2024). Regularity = standard deviation of (actual - expected)
announcement dates over the 8 quarters before the event (>= 6 required); terciles within entry year (REG = most regular).
Outcome = holding-period return of the stock minus the equal-weighted universe return over the same days.
Statistic = coefficient of REG (vs IRR) with entry-year fixed effects, clustered by entry month. Expected sign negative.
Definitions fixed in PHASE5_SPEC.md section 3 before this script computed any return.
Run: python p5_10_rdq_regularity.py
"""
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd
import statsmodels.api as sm

from v2paths import MC_DIR
HERE = MC_DIR / "phase5"
MC = HERE.parent
ROOT = MC.parent
SLIM = (ROOT / "RDQ_cadence" / "dsf_v2_slim.parquet").as_posix()
CACHE = HERE / "cache"
CACHE.mkdir(exist_ok=True)
con = duckdb.connect()
con.execute("SET memory_limit='7GB'")

E = pd.read_parquet(MC / "r1_cache" / "r1_events_sec_verified.parquet")
E = E[E.grp == "verified silent"].copy()
for c in ("E", "t_e", "exit"):
    E[c] = pd.to_datetime(E[c])
print("verified silent events:", len(E))

# ---- regularity from the announcement history
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
    k = np.searchsorted(h[0], e, side="left")           # announcements strictly before the expected date
    x = h[1][max(0, k - 8):k]
    sd.append(np.std(x, ddof=1) if len(x) >= 6 else np.nan)
E["reg_sd"] = sd
E = E[E.reg_sd.notna()].copy()
E["year"] = E.t_e.dt.year
E["ter"] = E.groupby("year").reg_sd.transform(lambda s: pd.qcut(s.rank(method="first"), 3, labels=False))
print("events with a regularity measure:", len(E), "| median sd by tercile:", E.groupby("ter").reg_sd.median().round(1).to_dict())

# ---- universe equal-weighted daily return
uf = CACHE / "univ_ew.parquet"
if not uf.exists():
    con.execute(f"""COPY (
      WITH j AS (SELECT year(date) y, max(date) d FROM '{SLIM}' WHERE month(date) = 6 GROUP BY 1),
           r AS (SELECT j.y, s.permno, row_number() OVER (PARTITION BY j.y ORDER BY s.dlycap DESC) rk
                 FROM j JOIN '{SLIM}' s ON s.date = j.d
                 WHERE s.sharetype='NS' AND s.securitytype='EQTY' AND s.securitysubtype='COM' AND s.usincflg='Y'
                   AND s.issuertype IN ('CORP','ACOR') AND s.primaryexch IN ('N','A','Q') AND s.dlycap > 0),
           m AS (SELECT y, permno FROM r WHERE rk <= 3000)
      SELECT s.date, avg(s.dlyret) AS ew, count(*) AS n
      FROM '{SLIM}' s JOIN m ON m.permno = s.permno AND m.y = CASE WHEN month(s.date) >= 7 THEN year(s.date) ELSE year(s.date) - 1 END
      WHERE s.dlyret IS NOT NULL AND s.date >= DATE '2004-07-01' GROUP BY 1) TO '{uf.as_posix()}' (FORMAT parquet)""")
U = pd.read_parquet(uf)
U["date"] = pd.to_datetime(U["date"])
U = U.sort_values("date").set_index("date")
clog = np.log1p(U.ew).cumsum()

# ---- holding-period returns
con.register("ev", E[["eid", "permno", "t_e", "exit"]])
R = con.execute(f"""SELECT e.eid, exp(sum(ln(greatest(1 + s.dlyret, 1e-9)))) - 1 AS r, count(*) AS nd
                    FROM ev e JOIN '{SLIM}' s ON s.permno = e.permno AND s.date > e.t_e AND s.date <= e.exit
                    WHERE s.dlyret IS NOT NULL GROUP BY 1""").df()
E = E.merge(R, on="eid", how="inner")
E["bench"] = np.expm1(clog.reindex(E["exit"]).values - clog.reindex(E.t_e).values)
E = E.dropna(subset=["bench"])
E["ar"] = (E.r - E.bench) * 100
E["ym"] = E.t_e.dt.year * 100 + E.t_e.dt.month
E.to_parquet(HERE / "rdq_r_events.parquet", index=False)


def run(d, label):
    X = pd.get_dummies(d.year, prefix="y", drop_first=True).astype(float)
    X["REG"] = (d.ter == 0).astype(float).values
    X["MID"] = (d.ter == 1).astype(float).values
    f = sm.OLS(d.ar.values, sm.add_constant(X.values, has_constant="add")).fit(cov_type="cluster", cov_kwds={"groups": d.ym.values, "use_correction": True})
    names = ["const"] + list(X.columns)
    i = names.index("REG")
    m = d.groupby("ter").ar.agg(["mean", "size"])
    print(f"   {label:26s} n {len(d):5d} | mean abnormal return REG {m.loc[0, 'mean']:+.2f}% (n {int(m.loc[0, 'size'])}), MID {m.loc[1, 'mean']:+.2f}%, IRR {m.loc[2, 'mean']:+.2f}% (n {int(m.loc[2, 'size'])}) "
          f"| REG - IRR {f.params[i]:+.3f}pp, t {f.tvalues[i]:+.2f} (months {d.ym.nunique()})")


print("[RDQ-R] holding-period abnormal return of verified-silent overdue firms by timing regularity (REG = most regular)")
run(E, "2005-2024")
run(E[E.year <= 2014], "2005-2014")
run(E[E.year >= 2015], "2015-2024")
al = E.ar.mean()
print(f"   all events: mean abnormal return {al:+.2f}% over an average holding period of {E.nd.mean():.1f} trading days")
