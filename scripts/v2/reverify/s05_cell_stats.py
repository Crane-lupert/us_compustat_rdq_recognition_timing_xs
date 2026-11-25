"""s05: 12-cell statistics, replication + principled variants.

Input: panel_ret.parquet (s04), dsf_v2_slim.parquet (for the Russell-3000 proxy).
Output: s05_cells.csv (all variants x cells x IS/OOS/FULL), s05 log.

Variants
  V0  repo replica: log CAR, names-CUSIP <-> historical CUSIP link, sort universe = full Compustat panel
  V1  V0 but simple buy-and-hold return exp(CAR)-1 (what a portfolio earns)
  V2  permno link via CRSP header CUSIP (recovers pre-CUSIP-change history), log CAR
  V3  V2 + simple return
  V4  V3 restricted to CRSP common stock (NS/EQTY/COM/US-inc/CORP|ACOR) on NYSE/AMEX/Nasdaq at entry
      (the SPEC §3 universe), quintiles and size median re-formed inside the restricted universe
  V5  V4 restricted to a Russell-3000 proxy: top-3000 CRSP common stocks by market cap on the last
      trading day of May, membership July..June (the universe the paper claims)
Stats per cell: mean monthly cohort spread, NW(12) t (repo), plus HH(K-1) t with K = H/30 months.
"""
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd

from common import build_cells, monthly_spread, cell_stat, nw_se, hh_se, split, IS_END, OOS_START, OOS_END

from v2paths import RDQ_DIR
HERE = RDQ_DIR
P = pd.read_parquet(HERE / "panel_ret.parquet")
print("panel rows", len(P))

# ---- Russell 3000 proxy membership ----
con = duckdb.connect()
mem = con.execute(f"""
WITH m AS (
  SELECT year(date) AS y, max(date) AS d FROM '{(HERE/'dsf_v2_slim.parquet').as_posix()}'
  WHERE month(date) = 5 GROUP BY 1),
c AS (
  SELECT m.y, s.permno, s.dlycap FROM '{(HERE/'dsf_v2_slim.parquet').as_posix()}' s JOIN m ON s.date = m.d
  WHERE s.sharetype='NS' AND s.securitytype='EQTY' AND s.securitysubtype='COM' AND s.usincflg='Y'
    AND s.issuertype IN ('CORP','ACOR') AND s.primaryexch IN ('N','A','Q') AND s.dlycap > 0)
SELECT y, permno FROM (SELECT *, row_number() OVER (PARTITION BY y ORDER BY dlycap DESC) rk FROM c) WHERE rk <= 3000
""").df()
print("R3000 proxy members per year (first/last):", mem.groupby("y").size().iloc[[0, -1]].to_dict())
P["mem_y"] = np.where(P["rdq"].dt.month >= 7, P["rdq"].dt.year, P["rdq"].dt.year - 1)
memset = set(zip(mem["y"], mem["permno"]))
P["r3000"] = [((y, int(p)) in memset) if pd.notna(p) else False for y, p in zip(P["mem_y"], P["permno"])]

HORIZONS = [60, 120, 180]
for H in HORIZONS:
    P[f"scar_{H}"] = np.expm1(P[f"car_{H}"])
    P[f"spcar_{H}"] = np.expm1(P[f"pcar_{H}"])

variants = {
    "V0_repo": (P, "car_{H}"),
    "V1_simple": (P, "scar_{H}"),
    "V2_permno": (P, "pcar_{H}"),
    "V3_permno_simple": (P, "spcar_{H}"),
}
common_mask = P["common"].fillna(False).astype(bool) & P["major_exch"].fillna(False).astype(bool) & P["spcar_180"].notna()
variants["V4_common_exch"] = (P[common_mask].copy(), "spcar_{H}")
variants["V5_r3000proxy"] = (P[common_mask & P["r3000"]].copy(), "spcar_{H}")

rows = []
for vname, (pan, colpat) in variants.items():
    df = build_cells(pan)
    for H in HORIZONS:
        K = int(round(H / 30))
        for sz in ("L", "S"):
            for it in ("H", "L"):
                cell = f"A{H}-{sz}{it}"
                s = monthly_spread(df, colpat.format(H=H), sz, it)
                s = s[s.index <= OOS_END]
                for per, ss in (("IS", split(s)[0]), ("OOS", split(s)[1]), ("FULL", s)):
                    mu, t, n = cell_stat(ss, 12)
                    t_hh = mu / hh_se(ss.values, max(K - 1, 1)) if n >= 12 else np.nan
                    t_nw24 = mu / nw_se(ss.values, 24) if n >= 12 else np.nan
                    rows.append(dict(variant=vname, cell=cell, H=H, period=per, n_months=n, mu=mu,
                                     t_nw12=t, t_hh=t_hh, t_nw24=t_nw24))
    nfq = df.dropna(subset=[colpat.format(H=180)])
    print(f"{vname}: firm-quarters with 180d return {len(nfq):,}")
R = pd.DataFrame(rows)
R.to_csv(HERE / "s05_cells.csv", index=False)

pd.set_option("display.width", 200)
for per in ("IS", "OOS", "FULL"):
    print(f"\n==== {per}: t (NW12) by cell ====")
    piv = R[R.period == per].pivot(index="cell", columns="variant", values="t_nw12")
    print(piv.round(2).to_string())
    print("Bonferroni passes (t>2.78):", (piv > 2.78).sum().to_dict())
print("\n==== IS mu (cohort spread, %) ====")
print((R[R.period == "IS"].pivot(index="cell", columns="variant", values="mu") * 100).round(2).to_string())
print("\n==== OOS mu (cohort spread, %) ====")
print((R[R.period == "OOS"].pivot(index="cell", columns="variant", values="mu") * 100).round(2).to_string())
print("\n==== V0 IS/OOS: NW12 vs HH(K-1) vs NW24 t ====")
print(R[(R.variant == "V0_repo") & (R.period != "FULL")][["cell", "period", "t_nw12", "t_hh", "t_nw24"]].round(2).to_string(index=False))
