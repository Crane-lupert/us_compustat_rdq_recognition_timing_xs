"""Extended forward returns for Phase 1 deferred robustness (post-autopilot).

Streams crsp_a_stock.dsf_v2 ONE more time to compute four additional CARs that
the original panel_with_returns*.parquet did not carry:

  car_240          [rdq+1,  rdq+240]   horizon advisory
  car_360          [rdq+1,  rdq+360]   horizon advisory
  car_120_sw1      [rdq+8,  rdq+120]   skip-week-1 (PEAD-overlap-clean)
  car_180_sw1      [rdq+8,  rdq+180]   skip-week-1

Reads:  artifacts/panel_with_returns.parquet  (existing post-NT panel)
Writes: artifacts/panel_with_returns_ext.parquet  (panel + 4 new car_* cols)

Lock F-equivalent: sort by (cusip8, dlycaldt) with kind='mergesort' before any
per-stock rolling; no agg(first/last/nth) without sort; deterministic output.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path("d:/vscode/us_compustat_rdq_recognition_timing_xs")
sys.path.insert(0, str(ROOT))

ART = ROOT / "artifacts"
DSF_PATH = Path("E:/wrds-data-courier/output/dump/crsp_a_stock.dsf_v2.csv.gz")
PANEL_IN = ART / "panel_with_returns.parquet"
PANEL_OUT = ART / "panel_with_returns_ext.parquet"

# (start_offset_days, end_offset_days, out_col)
HORIZONS = [
    (1, 240, "car_240"),
    (1, 360, "car_360"),
    (8, 120, "car_120_sw1"),
    (8, 180, "car_180_sw1"),
]


def stream_dsf(cusip8_set: set, chunksize: int = 1_000_000) -> pd.DataFrame:
    parts = []
    t0 = time.time()
    n_chunks = 0
    n_kept = 0
    reader = pd.read_csv(
        DSF_PATH,
        compression="gzip",
        usecols=["permno", "cusip", "dlycaldt", "dlyret"],
        dtype={"permno": "int32", "cusip": "string[pyarrow]", "dlyret": "float32"},
        parse_dates=["dlycaldt"],
        chunksize=chunksize,
        low_memory=False,
    )
    for chunk in reader:
        n_chunks += 1
        chunk["cusip8"] = chunk["cusip"].str.slice(0, 8)
        chunk = chunk[chunk["cusip8"].isin(cusip8_set)]
        if chunk.empty:
            continue
        chunk = chunk[["cusip8", "permno", "dlycaldt", "dlyret"]].copy()
        parts.append(chunk)
        n_kept += len(chunk)
        if n_chunks % 5 == 0:
            print(f"  chunk {n_chunks}: kept {n_kept:,} rows  ({time.time()-t0:.0f}s)", flush=True)
    print(f"  done streaming: {n_chunks} chunks, kept {n_kept:,} rows in {time.time()-t0:.0f}s", flush=True)
    dsf = pd.concat(parts, ignore_index=True)
    dsf = dsf.dropna(subset=["dlyret"])
    dsf = dsf.sort_values(["cusip8", "dlycaldt"], kind="mergesort").reset_index(drop=True)
    dsf["log_ret"] = np.log1p(dsf["dlyret"].astype("float64"))
    dsf["cum_log_ret"] = dsf.groupby("cusip8", sort=False, observed=True)["log_ret"].cumsum()
    return dsf


def compute_horizons(panel: pd.DataFrame, dsf: pd.DataFrame) -> pd.DataFrame:
    panel = panel.copy()
    cum_by_cusip = dsf.set_index("dlycaldt").groupby("cusip8", sort=False)["cum_log_ret"]
    cum_dict = {c: g for c, g in cum_by_cusip}

    car_arrays = {out_col: np.full(len(panel), np.nan, dtype="float64") for _, _, out_col in HORIZONS}

    cusips = panel["cusip8"].values
    rdqs = panel["rdq"].values
    n = len(panel)
    log_every = max(1, n // 20)
    t0 = time.time()
    for i in range(n):
        cu = cusips[i]
        if cu is None or pd.isna(cu) or cu not in cum_dict:
            continue
        series = cum_dict[cu]
        rdq_ts = pd.Timestamp(rdqs[i])
        for start_off, end_off, out_col in HORIZONS:
            start_ts = rdq_ts + pd.Timedelta(days=start_off)
            end_ts = rdq_ts + pd.Timedelta(days=end_off)
            idx0 = series.index.searchsorted(start_ts, side="left")
            if idx0 >= len(series):
                continue
            c0 = series.iloc[idx0]
            idx1 = series.index.searchsorted(end_ts, side="right") - 1
            if idx1 < idx0:
                continue
            c1 = series.iloc[idx1]
            car_arrays[out_col][i] = c1 - c0
        if (i + 1) % log_every == 0:
            elapsed = time.time() - t0
            eta = elapsed / (i + 1) * (n - i - 1)
            print(f"  row {i+1:,}/{n:,}  ({elapsed:.0f}s elapsed, {eta:.0f}s eta)", flush=True)

    for _, _, out_col in HORIZONS:
        panel[out_col] = car_arrays[out_col]
    return panel


def main() -> int:
    print(f"Loading {PANEL_IN.name} ...", flush=True)
    panel = pd.read_parquet(PANEL_IN)
    print(f"  rows: {len(panel):,}", flush=True)

    cusip8_set = set(panel["cusip8"].dropna().unique().tolist())
    print(f"  unique cusip8: {len(cusip8_set):,}", flush=True)

    print(f"Streaming {DSF_PATH.name} (4.4 GB) ...", flush=True)
    dsf = stream_dsf(cusip8_set)
    print(f"  dsf rows after filter: {len(dsf):,}", flush=True)

    print("Computing 4 extended horizons (car_240 / car_360 / car_120_sw1 / car_180_sw1) ...", flush=True)
    panel_ext = compute_horizons(panel, dsf)

    for _, _, out_col in HORIZONS:
        n_nonnull = panel_ext[out_col].notna().sum()
        print(f"  {out_col}: {n_nonnull:,} non-null", flush=True)

    panel_ext.to_parquet(PANEL_OUT, engine="pyarrow", index=False)
    print(f"Wrote {PANEL_OUT.name}  ({len(panel_ext):,} rows)", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
