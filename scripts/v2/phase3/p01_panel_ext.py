"""p01: extended signal panel from the raw Compustat dump (no return outcomes are computed here).

Repo logic (shared_lib/rdq_panel_loader, replicated in phase 1-2 s03): INDL/STD/C/D/USD, rdq & datadate non-null,
datadate >= 1999-01-01, gap = rdq - datadate in [10, 180], rolling 8 rows (min 6) std (gap_var_t) / median
(gap_dev_t) per gvkey over rows sorted by datadate, names header -> cusip8/sic/FF12, NT proxy drop.
Differences vs the repo panel: no datadate <= 2024-12-31 cap (rows after it are flagged in_phase0 = False; used only
for the D1 count). Added columns:
  lookahead      : any row in the trailing 8-row window has rdq > current rdq (signal would use a later announcement)
  dev_cp         : Chambers-Penman (1984) deviation = rdq - (rdq of same fiscal quarter in the previous fiscal year
                   + 1 calendar year), days; expected-date definition per Trueman (1990, JAE 13:285-301, fn. 1)
  ff49           : FF49 industry (repo ff49.py copy)
Writes phase3/out/panel_ext.parquet, log to stdout.
"""
import sys
sys.dont_write_bytecode = True
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from p3common import OUT, PARENT, DUMP, ff12_from_sic  # noqa: E402
from ff49_copy import ff49_from_sic  # noqa: E402

FUNDQ = DUMP + "comp_na_daily_all.fundq.csv.gz"
NAMES = DUMP + "comp_na_daily_all.names.csv.gz"
con = duckdb.connect()
con.execute("PRAGMA threads=8")
raw = con.execute(f"""
  SELECT gvkey, TRY_CAST(datadate AS DATE) AS datadate, TRY_CAST(rdq AS DATE) AS rdq,
         TRY_CAST(fyearq AS INTEGER) AS fyearq, TRY_CAST(fqtr AS INTEGER) AS fqtr,
         TRY_CAST(atq AS DOUBLE) AS atq, TRY_CAST(cshoq AS DOUBLE) AS cshoq, TRY_CAST(prccq AS DOUBLE) AS prccq
  FROM read_csv('{FUNDQ}', header=true, all_varchar=true)
  WHERE indfmt='INDL' AND datafmt='STD' AND consol='C' AND popsrc='D' AND curcdq='USD'
""").df()
raw["datadate"] = pd.to_datetime(raw["datadate"])
raw["rdq"] = pd.to_datetime(raw["rdq"])
print("fundq INDL/STD/C/D/USD rows:", len(raw), " max datadate:", raw.datadate.max().date(), " max rdq:", raw.rdq.max().date())

# ---------- Chambers-Penman expected date: same fiscal quarter, previous fiscal year (any gap) ----------
cp = raw.dropna(subset=["rdq", "fyearq", "fqtr"]).sort_values(["gvkey", "fyearq", "fqtr", "datadate"], kind="mergesort")
cp = cp.drop_duplicates(["gvkey", "fyearq", "fqtr"], keep="last")[["gvkey", "fyearq", "fqtr", "rdq"]]
cp = cp.rename(columns={"rdq": "rdq_prev"})
cp["fyearq"] = cp["fyearq"] + 1          # key it to the following fiscal year

# ---------- repo panel logic ----------
df = raw.dropna(subset=["rdq", "datadate"]).copy()
df = df[df["datadate"] >= "1999-01-01"]
df["gap_days"] = (df["rdq"] - df["datadate"]).dt.days
df = df[df["gap_days"].between(10, 180)].copy()
df = df.sort_values(["gvkey", "datadate"], kind="mergesort").reset_index(drop=True)
g = df.groupby("gvkey", sort=False)["gap_days"]
df["gap_var_t"] = g.transform(lambda s: s.rolling(8, min_periods=6).std())
df["gap_dev_t"] = df["gap_days"] - g.transform(lambda s: s.rolling(8, min_periods=6).median())
rint = df["rdq"].values.astype("datetime64[D]").astype("int64").astype(float)
df["_r"] = rint
df["max_rdq_win"] = df.groupby("gvkey", sort=False)["_r"].transform(lambda s: s.rolling(8, min_periods=1).max())
df["lookahead"] = df["max_rdq_win"] > df["_r"]
df = df.dropna(subset=["gap_var_t"]).reset_index(drop=True)

names = con.execute(f"SELECT gvkey, cusip, TRY_CAST(sic AS INTEGER) AS sic FROM read_csv('{NAMES}', header=true, all_varchar=true)").df()
names = names.sort_values("gvkey", kind="mergesort").drop_duplicates("gvkey", keep="last")
names["cusip8"] = names["cusip"].str.slice(0, 8)
names["ff12"] = names["sic"].apply(ff12_from_sic).astype("int8")
names["ff49"] = names["sic"].apply(ff49_from_sic).astype("int8")
df = df.merge(names[["gvkey", "cusip8", "sic", "ff12", "ff49"]], on="gvkey", how="left")
is_ann = df["fqtr"] == 4
keep = ((~is_ann) & (df["gap_days"] <= 75)) | (is_ann & (df["gap_days"] <= 100))
df = df[keep].reset_index(drop=True)
df = df.merge(cp, on=["gvkey", "fyearq", "fqtr"], how="left")
exp_date = df["rdq_prev"] + pd.DateOffset(years=1)
df["dev_cp"] = (df["rdq"] - exp_date).dt.days
df["in_phase0"] = df["datadate"] <= "2024-12-31"
print("extended panel rows:", len(df), " in_phase0:", int(df.in_phase0.sum()), " beyond:", int((~df.in_phase0).sum()))

# ---------- checks against the phase 1-2 rebuild (= repo panel) ----------
pr = pd.read_parquet(PARENT / "panel_rebuild.parquet", columns=["gvkey", "datadate", "rdq", "fyearq", "fqtr", "gap_var_t"])
k = ["gvkey", "datadate", "rdq", "fyearq", "fqtr"]
a = df[df.in_phase0].sort_values(k, kind="mergesort").reset_index(drop=True)
b = pr.sort_values(k, kind="mergesort").reset_index(drop=True)
same_rows = len(a) == len(b) and bool((a[k].astype(str).values == b[k].astype(str).values).all())
print("phase-0 rows identical to panel_rebuild:", same_rows, " max|gap_var_t diff|:",
      float((a["gap_var_t"] - b["gap_var_t"]).abs().max()) if same_rows else "n/a")
p0 = df[df.in_phase0]
print("look-ahead rows (trailing window holds a later rdq): phase0", int(p0.lookahead.sum()),
      f"({100*p0.lookahead.mean():.3f}%)")
print("dev_cp available: phase0", int(p0.dev_cp.notna().sum()), f"({100*p0.dev_cp.notna().mean():.1f}%)",
      " quantiles:", p0.dev_cp.quantile([0.01, 0.1, 0.5, 0.9, 0.99]).to_dict())
print("corr(dev_cp, gap_dev_t) phase0:", round(float(p0[["dev_cp", "gap_dev_t"]].corr().iloc[0, 1]), 3))
df.drop(columns=["_r", "max_rdq_win", "rdq_prev"]).to_parquet(OUT / "panel_ext.parquet", index=False)
print("wrote", OUT / "panel_ext.parquet")
