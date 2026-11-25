"""s01b: slim extract of bid/ask/volume from crsp_a_stock.dsf_v2 (1999+) for cost estimates. Read-only on dump."""
import time
from pathlib import Path
import duckdb
from v2paths import RDQ_DIR, WRDS_DUMP
OUT = RDQ_DIR / "dsf_v2_bidask.parquet"
SRC = WRDS_DUMP + "crsp_a_stock.dsf_v2.csv.gz"
t0 = time.time()
con = duckdb.connect(); con.execute("PRAGMA threads=8")
con.execute(f"""
COPY (SELECT permno::INTEGER AS permno, dlycaldt::DATE AS date,
  TRY_CAST(dlybid AS DOUBLE) AS bid, TRY_CAST(dlyask AS DOUBLE) AS ask,
  TRY_CAST(dlyprc AS DOUBLE) AS prc, TRY_CAST(dlyvol AS DOUBLE) AS vol, TRY_CAST(shrout AS DOUBLE) AS shrout
  FROM read_csv('{SRC}', header=true, all_varchar=true) WHERE dlycaldt >= '1999-01-01')
TO '{OUT.as_posix()}' (FORMAT PARQUET, COMPRESSION ZSTD)""")
print(f"done in {time.time()-t0:.0f}s")
