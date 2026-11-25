"""p09 (D3, EXPLORATORY - outside the pre-registration; run once, no re-specification): does the top signal quintile
predict performance-related delisting within 12 months?
  sample : main universe trading events (Russell-3000 proxy, PIT link, valid entry, duplicate rules) with a main-spec
           quintile; estimation rdq 2000-02..2016-12, confirmation rdq 2017-01..2024-12 (identical spec)
  y      : CIZ stkdelists delactiontype in {GLI, GDR} (= legacy dlstcd 400-599) with delistingdt in (rdq, rdq+365]
  x      : Q2..Q5 dummies (Q1 omitted); report Q5
  ctrl   : log CRSP cap at d0 ($M); trailing vol = sd(daily dlyret over [rdq-365, rdq-1]) x sqrt(252), >= 100 days;
           calendar-year FE
  est    : OLS LPM, gvkey-clustered CR1 SE, t(G-1)
Writes out/d3_lpm.csv; prints results.
"""
import sys
sys.dont_write_bytecode = True
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats as st

sys.path.insert(0, str(Path(__file__).resolve().parent))
from p3common import OUT, DSF, DUMP  # noqa: E402

cm = pd.read_parquet(OUT / "cells_main.parquet")
d = cm[cm.q5.notna() & cm.valid_entry].copy()
d["permno"] = d["permno"].astype("int64")
con = duckdb.connect()
con.execute("PRAGMA threads=8")
con.execute("SET memory_limit='10GB'")
con.register("e", d[["rid", "permno", "rdq"]])
dl = con.execute(f"""SELECT permno::BIGINT permno, delistingdt::DATE dt, delactiontype a
                     FROM read_csv('{DUMP}crsp_a_stock.stkdelists.csv.gz', header=true, all_varchar=true)""").df()
con.register("dl", dl)
y = con.execute("""SELECT e.rid, max(CASE WHEN dl.a IN ('GLI','GDR') AND dl.dt > e.rdq AND dl.dt <= e.rdq + INTERVAL 365 DAY THEN 1 ELSE 0 END) y,
                          max(CASE WHEN dl.dt > e.rdq AND dl.dt <= e.rdq + INTERVAL 365 DAY THEN 1 ELSE 0 END) any_delist
                   FROM e LEFT JOIN dl ON dl.permno = e.permno GROUP BY e.rid""").df()
vol = con.execute(f"""SELECT e.rid, stddev_samp(s.dlyret) * sqrt(252) vol12, count(s.dlyret) nvol
                      FROM e JOIN '{DSF}' s ON s.permno = e.permno AND s.date >= e.rdq - INTERVAL 365 DAY AND s.date < e.rdq
                      WHERE s.dlyret IS NOT NULL GROUP BY e.rid""").df()
d = d.merge(y, on="rid", how="left").merge(vol, on="rid", how="left")
d["y"] = d["y"].fillna(0)
d.loc[d.nvol < 100, "vol12"] = np.nan
d["lcap"] = np.log(d["cap_d0_mil"])
d["year"] = d["rdq"].dt.year
print("D3 events with quintile & valid entry:", len(d), " performance delistings within 12m:", int(d.y.sum()),
      f" (rate {d.y.mean()*100:.3f}%)")
print("  rate by quintile (%):", (d.groupby("q5").y.mean() * 100).round(3).to_dict())

rows = []
for per, (a, b) in {"IS_2000_2016": ("2000-02-01", "2016-12-31"), "LATE_2017_2024": ("2017-01-01", "2024-12-31")}.items():
    s = d[(d.rdq >= a) & (d.rdq <= b)].dropna(subset=["lcap", "vol12", "y"]).copy()
    X = pd.get_dummies(s["q5"].astype(int), prefix="Q", drop_first=True).astype(float)
    X["lcap"] = s["lcap"].values
    X["vol12"] = s["vol12"].values
    X = X.join(pd.get_dummies(s["year"], prefix="Y", drop_first=True).astype(float).set_index(X.index))
    X = sm.add_constant(X)
    g = pd.factorize(s["gvkey"])[0]
    fit = sm.OLS(s["y"].astype(float).values, X.values).fit(cov_type="cluster", cov_kwds={"groups": g})
    names = list(X.columns)
    G = int(len(np.unique(g)))
    for v in ["Q_2", "Q_3", "Q_4", "Q_5", "lcap", "vol12"]:
        i = names.index(v)
        b_, se_ = float(fit.params[i]), float(fit.bse[i])
        t_ = b_ / se_
        rows.append(dict(period=per, var=v, coef=b_, se=se_, t=t_, p_two=float(2 * st.t.sf(abs(t_), G - 1)),
                         N=int(len(s)), clusters=G, base_rate_Q1=float(s.loc[s.q5 == 1, "y"].mean()),
                         rate_Q5=float(s.loc[s.q5 == 5, "y"].mean()), mean_y=float(s.y.mean())))
R = pd.DataFrame(rows)
R.to_csv(OUT / "d3_lpm.csv", index=False)
pd.set_option("display.width", 200)
out = R.copy()
for c in ("coef", "se", "base_rate_Q1", "rate_Q5", "mean_y"):
    out[c] = out[c] * (100 if c != "coef" or True else 1)
print(out.assign(coef=R.coef * 100, se=R.se * 100).round(4).to_string(index=False))
print("(coef/se in percentage points of 12-month performance-delisting probability; lcap/vol12 coefficients x100 per unit)")
