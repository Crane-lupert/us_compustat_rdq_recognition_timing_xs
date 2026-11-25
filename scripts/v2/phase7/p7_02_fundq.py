"""Phase 7 - step 2: quarterly Compustat fields, company classification and short interest from the local dump (inputs only).
Run: python p7_02_fundq.py
"""
from pathlib import Path

import duckdb

from v2paths import MC_DIR, WRDS_DUMP
HERE = MC_DIR / "phase7"
CACHE = HERE / "cache"
CACHE.mkdir(exist_ok=True)
DUMP = WRDS_DUMP.rstrip("/")
con = duckdb.connect()
con.execute("SET memory_limit='7GB'")

f = CACHE / "fundq_ext.parquet"
if not f.exists():
    con.execute(f"""COPY (SELECT gvkey, CAST(datadate AS DATE) datadate, TRY_CAST(fyearq AS INT) fyearq, TRY_CAST(fqtr AS INT) fqtr, TRY_CAST(fyr AS INT) fyr,
                           cusip, cik, tic, TRY_CAST(rdq AS DATE) rdq, TRY_CAST(epspxq AS DOUBLE) epspxq, TRY_CAST(epsfxq AS DOUBLE) epsfxq,
                           TRY_CAST(ibq AS DOUBLE) ibq, TRY_CAST(niq AS DOUBLE) niq, TRY_CAST(saleq AS DOUBLE) saleq, TRY_CAST(atq AS DOUBLE) atq,
                           TRY_CAST(ceqq AS DOUBLE) ceqq, TRY_CAST(cshoq AS DOUBLE) cshoq, TRY_CAST(prccq AS DOUBLE) prccq,
                           TRY_CAST(pdateq AS DATE) pdateq, TRY_CAST(fdateq AS DATE) fdateq, TRY_CAST(apdedateq AS DATE) apdedateq
                    FROM read_csv('{DUMP}/comp_na_daily_all.fundq.csv.gz', all_varchar=true, header=true, ignore_errors=true)
                    WHERE indfmt='INDL' AND datafmt='STD' AND consol='C' AND popsrc='D' AND datadate >= '1999-01-01')
                   TO '{f.as_posix()}' (FORMAT parquet)""")
print("fundq_ext:", con.execute(f"SELECT count(*), min(datadate), max(datadate), max(rdq) FROM '{f.as_posix()}'").fetchall())

g = CACHE / "company.parquet"
if not g.exists():
    con.execute(f"""COPY (SELECT gvkey, sic, gsector, ggroup, loc, fic, conm FROM read_csv('{DUMP}/comp_na_daily_all.company.csv.gz', all_varchar=true, header=true, ignore_errors=true))
                   TO '{g.as_posix()}' (FORMAT parquet)""")
print("company:", con.execute(f"SELECT count(*) FROM '{g.as_posix()}'").fetchall())

s = CACHE / "shortint.parquet"
if not s.exists():
    hdr = con.execute(f"SELECT * FROM read_csv('{DUMP}/comp_na_daily_all.sec_shortint.csv.gz', all_varchar=true, header=true, ignore_errors=true) LIMIT 1").df().columns.tolist()
    print("shortint columns:", hdr)
    con.execute(f"""COPY (SELECT * FROM read_csv('{DUMP}/comp_na_daily_all.sec_shortint.csv.gz', all_varchar=true, header=true, ignore_errors=true)
                    WHERE datadate >= '2002-01-01') TO '{s.as_posix()}' (FORMAT parquet)""")
print("shortint:", con.execute(f"SELECT count(*), min(datadate), max(datadate) FROM '{s.as_posix()}'").fetchall())
