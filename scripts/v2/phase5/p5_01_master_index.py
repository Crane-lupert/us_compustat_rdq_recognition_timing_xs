"""Phase 5 / step 1 - filing dates of periodic reports from the EDGAR quarterly master index (no outcome data).

Downloads https://www.sec.gov/Archives/edgar/full-index/<year>/QTR<q>/master.gz for 2001-2025 and keeps only the rows
of periodic reports (10-Q / 10-K families) and late-filing notices (NT 10-Q / NT 10-K).
Generic User-Agent, one request every 1.5 s, stops on HTTP 403 / 429. Resumable (one parquet per quarter).
Run: python p5_01_master_index.py
"""
import gzip
import io
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

import pandas as pd

import os
from v2paths import MC_DIR
HERE = MC_DIR / "phase5"
OUT = HERE / "cache" / "master"
OUT.mkdir(parents=True, exist_ok=True)
KEEP = {"10-Q", "10-K", "10-K405", "10-KSB", "10-QSB", "10-KT", "10-QT", "10-KSB40", "NT 10-Q", "NT 10-K", "NT 10-KT", "NT 10-QT"}

for y in range(2001, 2026):
    for q in (1, 2, 3, 4):
        f = OUT / f"{y}Q{q}.parquet"
        if f.exists():
            continue
        url = f"https://www.sec.gov/Archives/edgar/full-index/{y}/QTR{q}/master.gz"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": os.environ["SEC_USER_AGENT"]})
            raw = urllib.request.urlopen(req, timeout=120).read()
        except urllib.error.HTTPError as e:
            print(f"{y}Q{q}: HTTP {e.code}", flush=True)
            if e.code in (403, 429):
                print("STOP", flush=True)
                sys.exit(1)
            continue
        txt = gzip.decompress(raw).decode("latin-1")
        rows = []
        for line in txt.splitlines():
            p = line.split("|")
            if len(p) == 5 and p[2] in KEEP:
                rows.append((p[0], p[2], p[3]))
        pd.DataFrame(rows, columns=["cik", "form", "date"]).to_parquet(f, index=False)
        print(f"{y}Q{q}: kept {len(rows)} rows", flush=True)
        time.sleep(1.5)
print("done", flush=True)
