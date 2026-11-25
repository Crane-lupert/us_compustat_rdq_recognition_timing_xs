"""s03: independent rebuild of the RD1 signal panel from the raw Compustat dumps.

Reads (read-only): comp_na_daily_all.fundq / names dumps; repo panel_post_nt_excl.parquet (comparison only).
Writes (work folder): panel_rebuild.parquet, s03 log on stdout.

Replicates the repo logic (shared_lib/rdq_panel_loader/__init__.py):
  INDL/STD/C/D/USD, rdq & datadate non-null, datadate in [1999-01-01, 2024-12-31]
  gap = rdq - datadate in [10, 180]; rolling 8 rows (min 6) std/median per gvkey over rows sorted by datadate
  names: last row per gvkey (header) -> cusip8, sic -> FF12
  NT proxy: drop fqtr in 1-3 & gap > 75, fqtr == 4 & gap > 100
Also reports: rdq coverage before 1999 (paper L140 claim), duplicate (gvkey, datadate) rows,
and whether rdq can precede datadate+10 etc.
"""
import sys
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd

from v2paths import RDQ_DIR, WRDS_DUMP, V1_ARTIFACTS
HERE = RDQ_DIR
FUNDQ = WRDS_DUMP + "comp_na_daily_all.fundq.csv.gz"
NAMES = WRDS_DUMP + "comp_na_daily_all.names.csv.gz"
REPO_PANEL = V1_ARTIFACTS + "panel_post_nt_excl.parquet"
sys.path.insert(0, str(HERE))
from common import ff12_from_sic  # noqa: E402

con = duckdb.connect()
con.execute("PRAGMA threads=8")
raw = con.execute(f"""
  SELECT gvkey, TRY_CAST(datadate AS DATE) AS datadate, TRY_CAST(rdq AS DATE) AS rdq,
         TRY_CAST(fyearq AS INTEGER) AS fyearq, TRY_CAST(fqtr AS INTEGER) AS fqtr,
         TRY_CAST(atq AS DOUBLE) AS atq, TRY_CAST(cshoq AS DOUBLE) AS cshoq, TRY_CAST(prccq AS DOUBLE) AS prccq
  FROM read_csv('{FUNDQ}', header=true, all_varchar=true)
  WHERE indfmt='INDL' AND datafmt='STD' AND consol='C' AND popsrc='D' AND curcdq='USD'
""").df()
print("fundq INDL/STD/C/D/USD rows:", len(raw))
raw["year"] = pd.to_datetime(raw["datadate"]).dt.year
cov = raw.groupby("year").agg(n=("gvkey", "size"), rdq_nonnull=("rdq", lambda s: s.notna().sum()))
cov["rdq_frac"] = (cov["rdq_nonnull"] / cov["n"]).round(3)
print("rdq coverage by datadate year (1985-2001):")
print(cov.loc[1985:2001].to_string())

df = raw.dropna(subset=["rdq", "datadate"]).copy()
df["datadate"] = pd.to_datetime(df["datadate"])
df["rdq"] = pd.to_datetime(df["rdq"])
df = df[(df["datadate"] >= "1999-01-01") & (df["datadate"] <= "2024-12-31")]
print("after non-null + period:", len(df))
df["gap_days"] = (df["rdq"] - df["datadate"]).dt.days
dup = df.duplicated(["gvkey", "datadate"], keep=False).sum()
print("duplicate (gvkey, datadate) rows in this subset:", int(dup))
df = df[df["gap_days"].between(10, 180)].copy()
print("after gap [10,180]:", len(df))
df = df.sort_values(["gvkey", "datadate"], kind="mergesort").reset_index(drop=True)
g = df.groupby("gvkey", sort=False)["gap_days"]
df["gap_var_t"] = g.transform(lambda s: s.rolling(8, min_periods=6).std())
df["gap_dev_t"] = df["gap_days"] - g.transform(lambda s: s.rolling(8, min_periods=6).median())
# calendar span of the 8-row window (to check the "8 quarters" claim)
df["win_start"] = df.groupby("gvkey", sort=False)["datadate"].shift(7)
df = df.dropna(subset=["gap_var_t"]).reset_index(drop=True)
print("after rolling >=6:", len(df))
span = (df["datadate"] - df["win_start"]).dt.days
print("8-row window calendar span (days) for rows with 8 rows: quantiles",
      span.quantile([0.5, 0.9, 0.99]).round(0).to_dict(), " share > 2.25y:", round(float((span > 821).mean()), 4))

names = con.execute(f"SELECT gvkey, cusip, TRY_CAST(sic AS INTEGER) AS sic, conm FROM read_csv('{NAMES}', header=true, all_varchar=true)").df()
names = names.sort_values("gvkey", kind="mergesort").drop_duplicates("gvkey", keep="last")
names["cusip8"] = names["cusip"].str.slice(0, 8)
names["ff12"] = names["sic"].apply(ff12_from_sic).astype("int8")
df = df.merge(names[["gvkey", "cusip8", "sic", "ff12", "conm"]], on="gvkey", how="left")
pre_nt = len(df)
is_ann = df["fqtr"] == 4
keep = ((~is_ann) & (df["gap_days"] <= 75)) | (is_ann & (df["gap_days"] <= 100))
df = df[keep].reset_index(drop=True)
print(f"after NT proxy: {len(df)} (dropped {pre_nt-len(df)}, {100*(pre_nt-len(df))/pre_nt:.2f}%)")
print("cusip8 null:", int(df["cusip8"].isna().sum()), " unique gvkey:", df["gvkey"].nunique())

rp = pd.read_parquet(REPO_PANEL)
print("repo panel rows:", len(rp), " unique gvkey:", rp["gvkey"].nunique())
k = ["gvkey", "datadate"]
m = df.merge(rp[k + ["gap_var_t", "cusip8", "ff12"]], on=k, how="outer", suffixes=("", "_repo"), indicator=True)
print(m["_merge"].value_counts().to_dict())
both = m[m["_merge"] == "both"]
print("max |gap_var_t diff|:", float((both["gap_var_t"] - both["gap_var_t_repo"]).abs().max()),
      " cusip8 equal:", float((both["cusip8"] == both["cusip8_repo"]).mean()),
      " ff12 equal:", float((both["ff12"] == both["ff12_repo"]).mean()))
df.drop(columns=["win_start", "year"]).to_parquet(HERE / "panel_rebuild.parquet", index=False)
print("wrote panel_rebuild.parquet")
