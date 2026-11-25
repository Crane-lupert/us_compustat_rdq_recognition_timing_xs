"""s01: one-pass slim extract of crsp_a_stock.dsf_v2 (1999-01-01 .. ) into the work folder.

Read-only on the dump. Output: dsf_v2_slim.parquet in this folder.
Columns kept: permno, cusip8 (historical CUSIP col `cusip`), hdrcusip8, date, dlyret,
dlydelflg, dlyprc, dlycap, sharetype, securitytype, securitysubtype, usincflg,
issuertype, primaryexch, conditionaltype, tradingstatusflg.
"""
import time
from pathlib import Path

import duckdb

from v2paths import RDQ_DIR, WRDS_DUMP
OUT = RDQ_DIR / "dsf_v2_slim.parquet"
SRC = WRDS_DUMP + "crsp_a_stock.dsf_v2.csv.gz"

t0 = time.time()
con = duckdb.connect()
con.execute("PRAGMA threads=8")
con.execute(f"""
COPY (
  SELECT permno::INTEGER AS permno,
         substr(cusip, 1, 8) AS cusip8,
         substr(hdrcusip, 1, 8) AS hdrcusip8,
         dlycaldt::DATE AS date,
         TRY_CAST(dlyret AS DOUBLE) AS dlyret,
         dlydelflg, TRY_CAST(dlyprc AS DOUBLE) AS dlyprc, TRY_CAST(dlycap AS DOUBLE) AS dlycap,
         sharetype, securitytype, securitysubtype, usincflg, issuertype, primaryexch,
         conditionaltype, tradingstatusflg
  FROM read_csv('{SRC}', header=true, all_varchar=true)
  WHERE dlycaldt >= '1999-01-01'
) TO '{OUT.as_posix()}' (FORMAT PARQUET, COMPRESSION ZSTD)
""")
print(f"done in {time.time()-t0:.0f}s -> {OUT}")
n = con.execute(f"SELECT count(*), count(DISTINCT permno), min(date), max(date) FROM '{OUT.as_posix()}'").fetchall()
print(n)
