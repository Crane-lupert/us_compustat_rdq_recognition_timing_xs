"""p08 (D2): Chambers-Penman (1984) early/late test with the original expected-date definition and a 3-day
announcement window (FROZEN_PARAMS D2).
  dev_cp = rdq - (prior-year same-fiscal-quarter rdq + 1 year)  [p01]
  sample : main universe (Russell-3000 proxy, PIT link, duplicate rules), rdq <= 2024-12-31, dev_cp non-null
  sort   : dev_cp quintiles within (rdq month, FF12); early = Q1, late = Q5; statistic early - late
  window : market trading days [t-1, t+1], t = first CRSP trading day >= rdq; 3 non-null stock returns
  outcome: market-adjusted (minus CRSP VW dsix vwretd) 3-day simple return (primary); raw 3-day (secondary)
Writes out/d2_cp.csv (stats) and out/d2_cp_monthly.csv; prints results.
"""
import sys
sys.dont_write_bytecode = True
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd
from scipy import stats as st

sys.path.insert(0, str(Path(__file__).resolve().parent))
from p3common import OUT, DSF, DUMP, quintile_within, nw_se, nw_lag_auto  # noqa: E402

cm = pd.read_parquet(OUT / "cells_main.parquet")
d = cm.dropna(subset=["dev_cp", "ff12"]).copy()
d = d.drop(columns=["q5"])
d["rdq_month"] = d["rdq"].dt.to_period("M")
d = quintile_within(d, "dev_cp", ["rdq_month", "ff12"])
print("D2 sample events:", len(d), " with quintile:", int(d.q5.notna().sum()))
print("mean dev_cp by quintile (days):", d.groupby("q5").dev_cp.mean().round(2).to_dict())

con = duckdb.connect()
con.execute("PRAGMA threads=8")
con.execute(f"CREATE TEMP TABLE cal AS SELECT date, row_number() OVER (ORDER BY date) k FROM (SELECT DISTINCT date FROM '{DSF}')")
con.execute(f"CREATE TEMP TABLE vw AS SELECT caldt::DATE date, TRY_CAST(vwretd AS DOUBLE) vw FROM read_csv('{DUMP}crsp_a_indexes.dsix.csv.gz', header=true, all_varchar=true)")
e = d[d.q5.isin([1, 5])][["rid", "permno", "rdq"]].copy()
e["permno"] = e["permno"].astype("int64")
con.register("e", e)
con.execute(f"CREATE TEMP TABLE s AS SELECT permno::BIGINT permno, date, dlyret r FROM '{DSF}' WHERE dlyret IS NOT NULL AND permno IN (SELECT DISTINCT permno FROM e)")
r3 = con.execute("""
  WITH t AS (SELECT e.rid, e.permno, c.k k0 FROM e ASOF JOIN cal c ON c.date >= e.rdq),
       w AS (SELECT t.rid, t.permno, c.date FROM t JOIN cal c ON c.k BETWEEN t.k0 - 1 AND t.k0 + 1)
  SELECT w.rid, count(s.r) n_r, count(v.vw) n_vw,
         exp(sum(ln(greatest(1 + s.r, 1e-9)))) - 1 AS raw3,
         exp(sum(ln(1 + v.vw))) - 1 AS mkt3
  FROM w LEFT JOIN s ON s.permno = w.permno AND s.date = w.date LEFT JOIN vw v ON v.date = w.date
  GROUP BY w.rid""").df()
d = d.merge(r3, on="rid", how="left")
ok = (d.n_r == 3)
d["raw3"] = np.where(ok, d.raw3, np.nan)
d["ar3"] = np.where(ok & (d.n_vw == 3), d.raw3 - d.mkt3, np.nan)
print("Q1/Q5 events:", int(d.q5.isin([1, 5]).sum()), " with 3 stock returns:", int((ok & d.q5.isin([1, 5])).sum()),
      " with market-adjusted:", int(d.ar3.notna().sum()))

PER = {"IS": ("2000-02-01", "2016-12-01"), "LATE": ("2017-01-01", "2024-12-01")}
rows, mon = [], []
for col in ("ar3", "raw3"):
    m = d[d.q5.isin([1, 5])].groupby(["rdq_month", "q5"], observed=True)[col].mean().unstack("q5")
    s = (m[1] - m[5]).dropna().sort_index()
    s.index = s.index.to_timestamp()
    mon.append(s.rename(col))
    for per, (a, b) in PER.items():
        ss = s.loc[a:b]
        T = len(ss); L = nw_lag_auto(T)
        mu = float(ss.mean()); t = mu / nw_se(ss.values, L)
        q1 = float(m[1].loc[pd.Period(a, 'M'):pd.Period(b, 'M')].mean()); q5 = float(m[5].loc[pd.Period(a, 'M'):pd.Period(b, 'M')].mean())
        rows.append(dict(outcome=col, period=per, T=T, nw_lag=L, early_minus_late=mu, t_nw=t,
                         p_two=float(2 * st.t.sf(abs(t), T - 1)), early_mean=q1, late_mean=q5,
                         n_events=int(d[d.q5.isin([1, 5]) & d[col].notna() & (d.rdq >= a) & (d.rdq < pd.Timestamp(b) + pd.offsets.MonthBegin(1))].shape[0])))
R = pd.DataFrame(rows)
R.to_csv(OUT / "d2_cp.csv", index=False)
pd.concat(mon, axis=1).to_csv(OUT / "d2_cp_monthly.csv")
pd.set_option("display.width", 200)
print(R.assign(early_minus_late=R.early_minus_late * 100, early_mean=R.early_mean * 100, late_mean=R.late_mean * 100).round(3).to_string(index=False))
