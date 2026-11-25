"""Phase 7 - step 1: 8-K item panel from data already on this laptop (no SEC request, no outcome data).

Sources:
  (a) archived submissions JSON (16,351 CIKs; the most recent 1,000 filings of each, with acceptance time)
  (b) phase-4 cache of full filing histories for comment-letter recipients (X_sec_letter/phase4/xa/cache/sec_filings.parquet)
  (c) phase-4 caches of 8-K histories for the firms of the R1 events (_main_checks/r1_cache/sec_parts, rdq2_cache/sec_parts)
Output: cache/k8_all.parquet (cik10, date, form, items) and cache/k8_coverage.parquet (cik10, cov_start = first date from
which the 8-K history of that CIK is complete in these sources, sic, name).
Run: python p7_01_8k_panel.py
"""
import glob
import json
import re
import zipfile
from pathlib import Path

import pandas as pd

from v2paths import MC_DIR, EDGAR_ARCHIVE
HERE = MC_DIR / "phase7"
MC = HERE.parent
ROOT = MC.parent
CACHE = HERE / "cache"
CACHE.mkdir(exist_ok=True)
ARCHIVE = EDGAR_ARCHIVE

rows, cov = [], []
z = zipfile.ZipFile(ARCHIVE)
subs = [n for n in z.namelist() if n.startswith("sec-data/submissions/") and n.endswith(".json")]
for i, n in enumerate(subs):
    try:
        j = json.loads(z.read(n))
    except Exception:
        continue
    cik10 = re.search(r"CIK(\d{10})", n).group(1)
    r = j.get("filings", {}).get("recent", {})
    forms, fd = r.get("form", []), r.get("filingDate", [])
    items = r.get("items", [""] * len(forms))
    acc = r.get("acceptanceDateTime", [""] * len(forms))
    truncated = len(j.get("filings", {}).get("files", [])) > 0
    cov.append((cik10, (min(fd) if (fd and truncated) else "1994-01-01"), str(j.get("sic") or ""), str(j.get("name") or "")[:80], "archive"))
    for f, d, it, a in zip(forms, fd, items, acc):
        if f in ("8-K", "8-K/A"):
            rows.append((cik10, d, f, it or "", a or ""))
    if (i + 1) % 4000 == 0:
        print(f"  archive {i + 1}/{len(subs)}", flush=True)
A = pd.DataFrame(rows, columns=["cik10", "date", "form", "items", "accepted"])
print("archive 8-K rows:", len(A), "| CIKs:", A.cik10.nunique())

xa = pd.read_parquet(ROOT / "X_sec_letter" / "phase4" / "xa" / "cache" / "sec_filings.parquet")
xa8 = xa[xa.form.isin(["8-K", "8-K/A"])][["cik10", "filingDate", "form", "items"]].rename(columns={"filingDate": "date"})
xa8["accepted"] = ""
cov += [(c, "1994-01-01", "", "", "xa") for c in xa.cik10.unique()]
parts = []
for f in glob.glob((MC / "r1_cache" / "sec_parts" / "*.parquet").as_posix()) + glob.glob((MC / "rdq2_cache" / "sec_parts" / "*.parquet").as_posix()):
    p = pd.read_parquet(f)
    if {"cik10", "form", "filingDate", "items"} <= set(p.columns):
        parts.append(p[["cik10", "filingDate", "form", "items"]].rename(columns={"filingDate": "date"}))
R = pd.concat(parts, ignore_index=True) if parts else pd.DataFrame(columns=["cik10", "date", "form", "items"])
R = R[R.form.isin(["8-K", "8-K/A"])].copy()
R["accepted"] = ""
cov += [(c, "1994-01-01", "", "", "r1") for c in R.cik10.unique()]
print("phase-4 caches: XA 8-K rows", len(xa8), "| R1 8-K rows", len(R))

K = pd.concat([A, xa8, R], ignore_index=True)
K["items"] = K["items"].fillna("").astype(str)
K = K.sort_values(["cik10", "date", "accepted"], ascending=[True, True, False]).drop_duplicates(["cik10", "date", "form", "items"], keep="first")
for it in ("1.01", "2.02", "2.05", "2.06", "3.01", "4.01", "4.02", "5.02"):
    K["i" + it.replace(".", "")] = K["items"].apply(lambda s, it=it: it in [t.strip() for t in s.split(",")])
K.to_parquet(CACHE / "k8_all.parquet", index=False)
C = pd.DataFrame(cov, columns=["cik10", "cov_start", "sic", "name", "src"]).sort_values(["cik10", "cov_start"])
C = C.groupby("cik10").agg(cov_start=("cov_start", "min"), sic=("sic", "max"), name=("name", "max"), src=("src", lambda s: ",".join(sorted(set(s))))).reset_index()
C.to_parquet(CACHE / "k8_coverage.parquet", index=False)
print(f"8-K panel: {len(K)} rows, {K.cik10.nunique()} CIKs, {K.date.min()}..{K.date.max()}; coverage table {len(C)} CIKs; "
      f"complete history from the start for {int((C.cov_start <= '1994-01-01').sum())}, truncated for {int((C.cov_start > '1994-01-01').sum())} (median start {C[C.cov_start > '1994-01-01'].cov_start.median() if (C.cov_start > '1994-01-01').any() else None})")
print("item counts:", {c: int(K[c].sum()) for c in K.columns if c.startswith("i") and c[1:].isdigit()})
