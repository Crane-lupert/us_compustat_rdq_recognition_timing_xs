"""p03: event selection (duplicate rules) and Lock C cell assignment inside each universe (FROZEN_PARAMS link/cells).
No return outcome is used. Writes phase3/out/cells_main.parquet and cells_b1.parquet.
"""
import sys
sys.dont_write_bytecode = True
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from p3common import OUT, DUMP, assign_cells, borrow_bps  # noqa: E402

ev = pd.read_parquet(OUT / "events.parquet")
L = pd.read_parquet(OUT / "link.parquet")
con = duckdb.connect()
nm = con.execute(f"""SELECT permno::INT permno, namedt::DATE namedt, nameendt::DATE nameendt, ncusip
                     FROM read_csv('{DUMP}crsp_a_stock.dsenames.csv.gz', header=true, all_varchar=true)""").df()
nm["namedt"] = pd.to_datetime(nm["namedt"]); nm["nameendt"] = pd.to_datetime(nm["nameendt"])

base = ev[ev.in_phase0 & (ev.rdq <= "2024-12-31") & ev.permno.notna()].copy()
n0 = len(base)
base = base[~base.lookahead]
print(f"phase-0 linked events rdq<=2024: {n0:,}; after dropping look-ahead signal rows: {len(base):,}")

# ---- shared-permno rule ----
shared = L[L.permno.duplicated(keep=False)][["gvkey", "permno"]]
cus = ev.drop_duplicates("gvkey")[["gvkey", "cusip8"]]
sh = shared.merge(cus, on="gvkey")
iv = sh.merge(nm, left_on=["permno", "cusip8"], right_on=["permno", "ncusip"])[["gvkey", "permno", "namedt", "nameendt"]]
drop_ids = []
sub = base[base.permno.isin(shared.permno)]
for p, g in sub.groupby("permno"):
    ivp = iv[iv.permno == p]
    for idx, row in g.iterrows():
        best, bestd, beststart = None, None, None
        for gk, gi in ivp.groupby("gvkey"):
            d = np.where((row.rdq >= gi.namedt) & (row.rdq <= gi.nameendt), 0,
                         np.minimum((row.rdq - gi.nameendt).dt.days.abs(), (gi.namedt - row.rdq).dt.days.abs())).min()
            st = gi.namedt.max()
            if best is None or d < bestd or (d == bestd and st > beststart):
                best, bestd, beststart = gk, d, st
        if best != row.gvkey:
            drop_ids.append(idx)
print(f"shared-permno rule: {len(sub):,} events on {sub.permno.nunique()} shared permnos; dropped {len(drop_ids):,}")
base = base.drop(index=drop_ids)

# ---- one event per (permno, rdq month): latest datadate ----
base["rdq_m"] = base["rdq"].dt.to_period("M")
base = base.sort_values(["permno", "rdq_m", "datadate", "rid"], kind="mergesort")
dups = int(base.duplicated(["permno", "rdq_m"], keep=False).sum())
base = base.drop_duplicates(["permno", "rdq_m"], keep="last").drop(columns=["rdq_m"])
print(f"one event per (permno, rdq month): {dups:,} events in duplicated groups -> kept {len(base):,} events")

base["borrow_bps"] = [borrow_bps(c if pd.notna(c) else m) for c, m in zip(base["cap_d0_mil"], base["cshoq"] * base["prccq"])]
keep_cols = ["rid", "gvkey", "permno", "datadate", "rdq", "fyearq", "fqtr", "gap_var_t", "gap_dev_t", "dev_cp", "ff12", "ff49",
             "sic", "cshoq", "prccq", "d0", "d0_sw", "valid_entry", "valid_entry_sw", "cap_d0_mil", "borrow_bps", "in_r3000", "common_rdq", "step"]
for name, mask in (("main", base.in_r3000), ("b1", base.common_rdq)):
    u = base.loc[mask, keep_cols].copy()
    c = assign_cells(u, "gap_var_t")
    c["permno"] = c["permno"].astype("int64")
    c.to_parquet(OUT / f"cells_{name}.parquet", index=False)
    pos = c[c.q5.isin([1, 5]) & c.valid_entry]
    print(f"[{name}] sorting universe {len(c):,} events, gvkeys {c.gvkey.nunique():,}; with quintile {int(c.q5.notna().sum()):,}; "
          f"Q1/Q5 tradable positions {len(pos):,} (valid entry share of Q1/Q5 {pos.shape[0]/max(1,int(c.q5.isin([1,5]).sum())):.3f})")
    print(f"   positions per cell (Q1/Q5, FF12 tilt):", pos.groupby(["size_bin", "ind_bin"]).size().to_dict())
    print(f"   median CRSP cap at entry $M Q1 / Q5:", round(float(pos[pos.q5 == 1].cap_d0_mil.median()), 0), "/",
          round(float(pos[pos.q5 == 5].cap_d0_mil.median()), 0), "; short-leg borrow bps mean:", round(float(pos[pos.q5 == 5].borrow_bps.mean()), 0))
