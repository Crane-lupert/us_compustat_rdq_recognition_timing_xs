"""Round-2 data collection for RDQ (no return or outcome is computed here).

Collects, from the SEC submissions API, the filing history (form, filing date, acceptance time, 8-K items) of every
firm that was ever in the June top-3,000 universe in 2004-2024 and has a CIK in Compustat. Used for the
"periodic report overdue relative to the firm's own history" test (10-Q / 10-K filing dates) and for 8-K outcomes.
Generic User-Agent, about 2.5 requests per second, stops on HTTP 403 / 429. Resumable.
Run: python rdq2_fetch_filings.py
"""
import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

import duckdb
import pandas as pd

import os
from v2paths import MC_DIR
HERE = MC_DIR
ROOT = HERE.parent
SLIM = (ROOT / "RDQ_cadence" / "dsf_v2_slim.parquet").as_posix()
CACHE = HERE / "rdq2_cache"
PARTS = CACHE / "sec_parts"
PARTS.mkdir(parents=True, exist_ok=True)
DONE = CACHE / "sec_done.txt"
KEEP = {"10-Q", "10-K", "10-Q/A", "10-K/A", "NT 10-Q", "NT 10-K", "8-K", "8-K/A", "10-KT", "10-QT", "10-K405", "10-KSB", "10-QSB"}

con = duckdb.connect()
con.execute("SET memory_limit='6GB'")
fq = pd.read_parquet(HERE / "r1_cache" / "fundq_rdq.parquet")
hdr = con.execute(f"SELECT permno, max(hdrcusip8) AS h FROM '{SLIM}' GROUP BY 1").df()
mem = con.execute(f"""
  WITH j AS (SELECT year(date) y, max(date) d FROM '{SLIM}' WHERE month(date) = 6 AND year(date) BETWEEN 2003 AND 2024 GROUP BY 1),
       r AS (SELECT j.y, s.permno, row_number() OVER (PARTITION BY j.y ORDER BY s.dlycap DESC) rk
             FROM j JOIN '{SLIM}' s ON s.date = j.d
             WHERE s.sharetype='NS' AND s.securitytype='EQTY' AND s.securitysubtype='COM' AND s.usincflg='Y'
               AND s.issuertype IN ('CORP','ACOR') AND s.primaryexch IN ('N','A','Q') AND s.dlycap > 0)
  SELECT DISTINCT permno FROM r WHERE rk <= 3000""").df()
h_ok = set(hdr[hdr.permno.isin(mem.permno)].h)
c8 = fq.dropna(subset=["cusip"]).drop_duplicates("gvkey").assign(c8=lambda d: d.cusip.str[:8])
gv = set(c8[c8.c8.isin(h_ok)].gvkey)
cik = fq[fq.gvkey.isin(gv) & fq.cik.notna() & (fq.cik != "")].sort_values("datadate").drop_duplicates("gvkey", keep="last")
ciks = sorted(set(cik.cik.astype(str).str.zfill(10)))
done = set(DONE.read_text().split()) if DONE.exists() else set()
todo = [c for c in ciks if c not in done]
print(f"universe firms with a CIK: {len(ciks)}; already done {len(done)}; to fetch {len(todo)}", flush=True)


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": os.environ["SEC_USER_AGENT"]})
    with urllib.request.urlopen(req, timeout=40) as r:
        return json.loads(r.read().decode("utf-8"))


buf, n = [], 0
for c in todo:
    status = "ok"
    try:
        j = get(f"https://data.sec.gov/submissions/CIK{c}.json")
        time.sleep(0.3)
        blocks = [j["filings"]["recent"]]
        for f in j["filings"].get("files", []):
            blocks.append(get("https://data.sec.gov/submissions/" + f["name"]))
            time.sleep(0.3)
        for b in blocks:
            acc = b.get("acceptanceDateTime", [""] * len(b["form"]))
            rep = b.get("reportDate", [""] * len(b["form"]))
            for form, fdate, items, a, rd in zip(b["form"], b["filingDate"], b.get("items", [""] * len(b["form"])), acc, rep):
                if form in KEEP:
                    buf.append((c, form, fdate, items, a, rd))
    except urllib.error.HTTPError as e:
        if e.code in (403, 429):
            print(f"STOP: HTTP {e.code} at CIK {c}", flush=True)
            break
        status = f"http{e.code}"
    except Exception:
        status = "err"
    with open(DONE, "a") as fh:
        fh.write(c + "\n")
    n += 1
    if n % 250 == 0:
        pd.DataFrame(buf, columns=["cik10", "form", "filingDate", "items", "acceptance", "reportDate"]).to_parquet(PARTS / f"part_{int(time.time())}.parquet", index=False)
        buf = []
        print(f"  fetched {n}/{len(todo)}", flush=True)
if buf:
    pd.DataFrame(buf, columns=["cik10", "form", "filingDate", "items", "acceptance", "reportDate"]).to_parquet(PARTS / f"part_{int(time.time())}_last.parquet", index=False)
print("fetch finished", flush=True)
