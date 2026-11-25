"""s00 (Step 0): input existence / range / meaning checks. NO return outcome is computed here.
Writes cache/fundq_rdq.parquet (Compustat fundq INDL/STD/C/D, all currencies, needed columns only), cache/calendar.parquet,
cache/ff5umd_daily.parquet, and prints the checks.
"""
import sys
sys.dont_write_bytecode = True
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from p4common import CACHE, P3, RDQ, DSF, DUMP, FUNDQ, con, load_calendar, load_ff_daily  # noqa: E402

c = con()
f = CACHE / "fundq_rdq.parquet"
if not f.exists():
    raw = c.execute(f"""
      SELECT gvkey, TRY_CAST(datadate AS DATE) datadate, TRY_CAST(rdq AS DATE) rdq, TRY_CAST(fyearq AS INTEGER) fyearq,
             TRY_CAST(fqtr AS INTEGER) fqtr, TRY_CAST(fyr AS INTEGER) fyr, curcdq, TRY_CAST(cshoq AS DOUBLE) cshoq,
             TRY_CAST(prccq AS DOUBLE) prccq, datacqtr
      FROM read_csv('{FUNDQ}', header=true, all_varchar=true)
      WHERE indfmt='INDL' AND datafmt='STD' AND consol='C' AND popsrc='D'""").df()
    raw.to_parquet(f, index=False)
raw = pd.read_parquet(f)
for col in ("datadate", "rdq"):
    raw[col] = pd.to_datetime(raw[col])
print("fundq INDL/STD/C/D rows:", len(raw), " gvkeys:", raw.gvkey.nunique(), " USD rows:", int((raw.curcdq == "USD").sum()),
      " non-USD rows:", int((raw.curcdq != "USD").sum()))
print("  rdq non-null:", int(raw.rdq.notna().sum()), " datadate range:", raw.datadate.min().date(), raw.datadate.max().date(),
      " rdq range:", raw.rdq.min().date(), raw.rdq.max().date())
r = raw.dropna(subset=["rdq", "datadate"]).copy()
r["gap"] = (r.rdq - r.datadate).dt.days
r99 = r[r.datadate >= "1998-01-01"]
print("  gap (rdq - datadate, days) for datadate >= 1998: n", len(r99), " quantiles",
      r99.gap.quantile([0.001, 0.01, 0.05, 0.5, 0.95, 0.99, 0.999]).to_dict())
for lo, hi in ((-10**6, 0), (1, 9), (10, 120), (121, 180), (181, 365), (366, 10**6)):
    print(f"    gap in [{lo},{hi}]: {int(r99.gap.between(lo, hi).sum()):,} ({100*r99.gap.between(lo, hi).mean():.3f}%)")
print("  rows with fyearq/fqtr null among rdq rows (datadate>=1998):", int(r99[["fyearq", "fqtr"]].isna().any(axis=1).sum()))
k = ["gvkey", "fyearq", "fqtr"]
d = r99.dropna(subset=["fyearq", "fqtr"])
print("  duplicate (gvkey,fyearq,fqtr) among rdq rows:", int(d.duplicated(k, keep=False).sum()),
      " duplicate (gvkey,datadate):", int(d.duplicated(["gvkey", "datadate"], keep=False).sum()))
sd = d.groupby(["gvkey", "rdq"]).size()
print("  (gvkey, rdq) with >1 row (several quarters announced the same day):", int((sd > 1).sum()), " rows in them:", int(sd[sd > 1].sum()))
fy = raw.dropna(subset=["fyr"]).sort_values(["gvkey", "datadate"]).groupby("gvkey").fyr.nunique()
print("  gvkeys with >1 fyr value over history:", int((fy > 1).sum()), "of", len(fy))
nf = raw.fyr.isna().mean()
print("  fyr null share:", round(float(nf), 5))

cal = load_calendar()
print("\ncalendar (distinct dsf_v2 dates):", len(cal), cal.date.min().date(), cal.date.max().date(),
      " in 2000-2024:", int(cal.date.between("2000-01-01", "2024-12-31").sum()))
x = c.execute(f"""SELECT count(*) n, sum(CASE WHEN dlydelflg='Y' THEN 1 ELSE 0 END) ndel,
      sum(CASE WHEN dlydelflg='Y' AND dlyret IS NULL THEN 1 ELSE 0 END) ndel_null,
      sum(CASE WHEN dlyprc < 0 THEN 1 ELSE 0 END) nneg, min(date) d0, max(date) d1 FROM '{DSF}'""").fetchone()
print("dsf_v2_slim rows / delisting rows / delisting rows with null dlyret / dlyprc<0 / date range:", x)
y = c.execute(f"""WITH dd AS (SELECT date, count(*) n, sum(CASE WHEN dlydelflg='N' THEN 1 ELSE 0 END) nn FROM '{DSF}' GROUP BY 1)
      SELECT count(*) FILTER (WHERE nn = 0) days_only_delist_rows, min(nn) FILTER (WHERE date >= '2000-01-01' AND date <= '2024-12-31') min_normal_rows FROM dd""").fetchone()
print("calendar days with only delisting rows / min normal rows per day 2000-2024:", y)
z = c.execute(f"""SELECT count(*) FROM (SELECT permno, date, count(*) n FROM '{DSF}' GROUP BY 1,2 HAVING count(*) > 1)""").fetchone()
print("duplicate (permno, date) rows in dsf_v2_slim:", z)

ff = load_ff_daily()
print("\nFF5+UMD daily (dump ff_all.fivefactors_daily):", ff.date.min().date(), ff.date.max().date(), " cols", list(ff.columns),
      " null rows 2000-2024:", int(ff[ff.date.between("2000-01-01", "2024-12-31")].isna().any(axis=1).sum()))
fr = pd.read_parquet(RDQ.parent / "X_sec_letter/phase3/cache/french_daily.parquet")
print("X_sec_letter/phase3/cache/french_daily.parquet columns (prompt-suggested file):", list(fr.columns))
cd = set(cal.date[cal.date.between("2000-01-01", "2024-12-31")])
fd = set(ff.date[ff.date.between("2000-01-01", "2024-12-31")])
print("  CRSP days 2000-2024 without FF row:", len(cd - fd), sorted(cd - fd)[:10], " FF days without CRSP:", len(fd - cd))

mem = pd.read_parquet(P3 / "out/membership.parquet")
L = pd.read_parquet(P3 / "out/link.parquet")
lk = set(L.permno.astype(int))
mem["linked3"] = mem.permno.astype(int).isin(lk)
print("\nR3000 proxy members linked by phase-3 link.parquet, share by year:",
      mem.groupby("y").linked3.mean().round(3).loc[[1999, 2004, 2009, 2014, 2019, 2024]].to_dict(),
      " overall:", round(float(mem[mem.y <= 2024].linked3.mean()), 4))
pe = pd.read_parquet(P3 / "out/panel_ext.parquet", columns=["gvkey"])
print("gvkeys: full fundq (rdq non-null)", r.gvkey.nunique(), " in phase-3 panel_ext", pe.gvkey.nunique(),
      " in link.parquet", len(L))

print("\nIBES surpsum (EPS, QTR):", c.execute(f"""SELECT count(*), min(anndats), max(anndats), count(DISTINCT ticker)
      FROM read_csv('{DUMP}tr_ibes.surpsum.csv.gz', header=true, all_varchar=true) WHERE measure='EPS' AND fiscalp='QTR'""").fetchone())
