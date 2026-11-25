"""s04: independent forward-return computation for the rebuilt panel.

Inputs: panel_rebuild.parquet (s03), dsf_v2_slim.parquet (s01). Repo panel_with_returns.parquet read for comparison only.
Output: panel_ret.parquet (work folder) with
  car_{60,120,180}        repo-replica: link = names current cusip8 == dsf_v2 historical `cusip`[:8];
                          series per cusip8 with null dlyret dropped; c0 = cum at first date >= rdq+1
                          (that day excluded), c1 = cum at last date <= rdq+H (calendar days)
  pcar_{60,120,180}       permno link: names cusip8 == dsf_v2 hdrcusip8 (header CUSIP) -> permno full history
  permno, common (sharetype NS & EQTY/COM & usincflg Y & issuertype CORP/ACOR at entry), exch (N/A/Q at entry),
  prc_entry (|dlyprc| at entry day), cap_entry (dlycap, $000) at entry day.
"""
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd

from v2paths import RDQ_DIR, V1_ARTIFACTS
HERE = RDQ_DIR
con = duckdb.connect()
con.execute("PRAGMA threads=8")
con.execute("SET memory_limit='10GB'")
con.execute(f"CREATE TEMP TABLE panel AS SELECT row_number() OVER () - 1 AS rid, gvkey, datadate, rdq, cusip8 FROM '{(HERE/'panel_rebuild.parquet').as_posix()}'")
con.execute(f"CREATE TEMP TABLE d AS SELECT * FROM '{(HERE/'dsf_v2_slim.parquet').as_posix()}' WHERE dlyret IS NOT NULL")

# ---------- (A) repo replica: historical cusip8 series ----------
con.execute("""
CREATE TEMP TABLE sa AS
SELECT cusip8, date, sum(ln(1+dlyret)) OVER (PARTITION BY cusip8 ORDER BY date, permno ROWS UNBOUNDED PRECEDING) AS cum
FROM d WHERE cusip8 IN (SELECT DISTINCT cusip8 FROM panel)
""")
# if a cusip8 has 2 rows on a date (shared by 2 permnos) keep the last cum on that date (repo: searchsorted side semantics)
con.execute("CREATE TEMP TABLE sa1 AS SELECT cusip8, date, max_by(cum, rn) cum_last, min_by(cum, rn) cum_first FROM (SELECT *, row_number() OVER (PARTITION BY cusip8 ORDER BY date) rn FROM sa) GROUP BY cusip8, date")


def car_asof(series_tbl, key_panel, key_series, H, label):
    q = f"""
    SELECT p.rid,
           e.cum_first AS c0_alt, e.date AS d0
    FROM panel p ASOF JOIN {series_tbl} e
      ON p.{key_panel} = e.{key_series} AND e.date >= p.rdq + INTERVAL 1 DAY
    """
    return q


out = con.execute("SELECT rid, gvkey, datadate, rdq FROM panel").df()
for H in (60, 120, 180):
    df = con.execute(f"""
    WITH s0 AS (
      SELECT p.rid, e.date AS d0, e.cum_first AS c0
      FROM panel p ASOF JOIN sa1 e ON p.cusip8 = e.cusip8 AND e.date >= p.rdq + INTERVAL 1 DAY),
    s1 AS (
      SELECT p.rid, e.date AS d1, e.cum_last AS c1
      FROM panel p ASOF JOIN sa1 e ON p.cusip8 = e.cusip8 AND e.date <= p.rdq + INTERVAL {H} DAY)
    SELECT s0.rid, CASE WHEN s1.d1 >= s0.d0 THEN s1.c1 - s0.c0 END AS car
    FROM s0 JOIN s1 USING (rid)""").df()
    out = out.merge(df.rename(columns={"car": f"car_{H}"}), on="rid", how="left")
print("(A) non-null:", {c: int(out[c].notna().sum()) for c in ["car_60", "car_120", "car_180"]},
      " any:", int(out[["car_60", "car_120", "car_180"]].notna().any(axis=1).sum()))

# ---------- (B) permno link via header CUSIP ----------
con.execute("CREATE TEMP TABLE hdr AS SELECT DISTINCT hdrcusip8, permno FROM d")
con.execute("CREATE TEMP TABLE pl AS SELECT p.*, h.permno FROM panel p LEFT JOIN hdr h ON p.cusip8 = h.hdrcusip8")
nperm = con.execute("SELECT count(*), count(permno) FROM pl").fetchall()
print("(B) panel rows / with permno via hdrcusip:", nperm)
con.execute("""
CREATE TEMP TABLE sb AS
SELECT permno, date, sum(ln(greatest(1+dlyret, 1e-6))) OVER (PARTITION BY permno ORDER BY date ROWS UNBOUNDED PRECEDING) AS cum
FROM d WHERE permno IN (SELECT DISTINCT permno FROM pl WHERE permno IS NOT NULL)
""")
for H in (60, 120, 180):
    df = con.execute(f"""
    WITH s0 AS (SELECT p.rid, e.date d0, e.cum c0 FROM pl p ASOF JOIN sb e ON p.permno = e.permno AND e.date >= p.rdq + INTERVAL 1 DAY),
         s1 AS (SELECT p.rid, e.date d1, e.cum c1 FROM pl p ASOF JOIN sb e ON p.permno = e.permno AND e.date <= p.rdq + INTERVAL {H} DAY)
    SELECT s0.rid, CASE WHEN s1.d1 >= s0.d0 THEN s1.c1 - s0.c0 END AS pcar FROM s0 JOIN s1 USING (rid)""").df()
    out = out.merge(df.rename(columns={"pcar": f"pcar_{H}"}), on="rid", how="left")
# entry-day attributes (permno link)
attr = con.execute("""
  SELECT p.rid, p.permno, e.date AS entry_date, abs(e.dlyprc) AS prc_entry, e.dlycap AS cap_entry,
         (e.sharetype='NS' AND e.securitytype='EQTY' AND e.securitysubtype='COM' AND e.usincflg='Y'
          AND e.issuertype IN ('CORP','ACOR')) AS common,
         e.primaryexch IN ('N','A','Q') AS major_exch
  FROM pl p ASOF JOIN d e ON p.permno = e.permno AND e.date >= p.rdq + INTERVAL 1 DAY
""").df()
out = out.merge(attr, on="rid", how="left")
print("(B) non-null:", {c: int(out[c].notna().sum()) for c in ["pcar_60", "pcar_120", "pcar_180"]},
      " any:", int(out[["pcar_60", "pcar_120", "pcar_180"]].notna().any(axis=1).sum()))

# ---------- compare (A) to repo ----------
rp = pd.read_parquet(V1_ARTIFACTS + "panel_with_returns.parquet")
pr = pd.read_parquet(HERE / "panel_rebuild.parquet")
pr["rid"] = np.arange(len(pr))
pr = pr.merge(out.drop(columns=["gvkey", "datadate", "rdq"]), on="rid")
# align row-by-row on (gvkey, datadate, rdq, fqtr, fyearq) -- duplicates resolved by order
k = ["gvkey", "datadate", "rdq", "fyearq", "fqtr"]
rp = rp.sort_values(k, kind="mergesort").reset_index(drop=True)
pr2 = pr.sort_values(k, kind="mergesort").reset_index(drop=True)
assert (rp[k].astype(str).values == pr2[k].astype(str).values).all(), "row alignment failed"
for H in (60, 120, 180):
    a, b = pr2[f"car_{H}"], rp[f"car_{H}"]
    both = a.notna() & b.notna()
    print(f"H={H}: repo nonnull {int(b.notna().sum())}  mine {int(a.notna().sum())}  both {int(both.sum())}"
          f"  max|diff| {float((a[both]-b[both]).abs().max()):.2e}  mismatch-null {int((a.notna()!=b.notna()).sum())}")
    print(f"   gap_var_t max|diff| {float((pr2['gap_var_t']-rp['gap_var_t']).abs().max()):.2e}")
pr2.to_parquet(HERE / "panel_ret.parquet", index=False)
print("wrote panel_ret.parquet", len(pr2))
