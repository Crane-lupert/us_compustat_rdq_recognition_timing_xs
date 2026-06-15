"""WITH-NT panel + forward returns (apply_nt_exclusion=False).

Reads:  comp_na_daily_all.fundq.csv.gz + names.csv.gz + crsp_a_stock.dsf_v2.csv.gz
Writes: artifacts/panel_with_returns_full.parquet (no NT exclusion)

Used by scripts/strategy_A_bonferroni_with_nt.py for sub-gate (c) ≤50% drop
formal sensitivity comparison (primary is post-NT exclusion; this is the
sensitivity panel).
"""

from __future__ import annotations

import gc
import shutil
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path("d:/vscode/us_compustat_rdq_recognition_timing_xs")
sys.path.insert(0, str(REPO))

from shared_lib.rdq_panel_loader import (
    load_fundq, filter_gap_window, rolling_8q_features, ccm_bridge_via_names,
)

ART = REPO / "artifacts"
TMP = ART / "_tmp_dsf_batches_full"
DSF_V2_PATH = Path("E:/wrds-data-courier/output/dump/crsp_a_stock.dsf_v2.csv.gz")
OUT_PATH = ART / "panel_with_returns_full.parquet"

HORIZONS = [60, 120, 180]
CHUNK_SIZE = 250_000
BATCH_FLUSH_ROWS = 1_000_000


def build_full_panel() -> pd.DataFrame:
    df = load_fundq()
    df = filter_gap_window(df)
    df = rolling_8q_features(df)
    df = df.dropna(subset=["gap_var_t"]).reset_index(drop=True)
    df = ccm_bridge_via_names(df)
    # NO exclude_nt_filers — this is the WITH-NT sensitivity panel
    return df


def stream_dsf(cusip8_set: set[str]) -> None:
    if TMP.exists():
        shutil.rmtree(TMP)
    TMP.mkdir(parents=True, exist_ok=True)
    batch_parts: list[pd.DataFrame] = []
    batch_rows = 0
    batch_id = 0
    n_total = 0
    n_kept = 0
    t0 = time.time()
    reader = pd.read_csv(
        DSF_V2_PATH, compression="gzip",
        usecols=["cusip", "dlycaldt", "dlyret"],
        dtype={"cusip": "string[pyarrow]", "dlyret": "float32"},
        parse_dates=["dlycaldt"], chunksize=CHUNK_SIZE, low_memory=False,
    )
    for i, chunk in enumerate(reader):
        n_total += len(chunk)
        chunk["cusip8"] = chunk["cusip"].str.slice(0, 8)
        chunk = chunk[chunk["cusip8"].isin(cusip8_set)]
        if not chunk.empty:
            chunk = chunk.dropna(subset=["dlyret", "dlycaldt"])
            batch_parts.append(chunk[["cusip8", "dlycaldt", "dlyret"]])
            batch_rows += len(chunk)
            n_kept += len(chunk)
        if batch_rows >= BATCH_FLUSH_ROWS:
            df_batch = pd.concat(batch_parts, ignore_index=True)
            df_batch.to_parquet(TMP / f"batch_{batch_id:04d}.parquet", index=False)
            batch_parts = []
            batch_rows = 0
            batch_id += 1
            gc.collect()
        if (i + 1) % 20 == 0:
            print(f"  chunk {i+1}: total={n_total:,} kept={n_kept:,} elapsed={time.time()-t0:.1f}s",
                  flush=True)
    if batch_parts:
        df_batch = pd.concat(batch_parts, ignore_index=True)
        df_batch.to_parquet(TMP / f"batch_{batch_id:04d}.parquet", index=False)
        batch_id += 1
    print(f"  DONE streaming: total={n_total:,} kept={n_kept:,} batches={batch_id} "
          f"elapsed={time.time()-t0:.1f}s", flush=True)


def main() -> int:
    print("Building WITH-NT panel ...", flush=True)
    panel = build_full_panel()
    print(f"  panel rows (with NT): {len(panel):,}", flush=True)
    cusip8_set = set(panel["cusip8"].dropna().unique().tolist())
    print(f"  unique cusip8: {len(cusip8_set):,}", flush=True)

    if not (TMP / "batch_0000.parquet").exists():
        print("Streaming dsf_v2 ...", flush=True)
        stream_dsf(cusip8_set)
    else:
        print("Reusing dsf_v2 batches.", flush=True)

    print("Loading batches ...", flush=True)
    parts = [pd.read_parquet(f) for f in sorted(TMP.glob("batch_*.parquet"))]
    dsf = pd.concat(parts, ignore_index=True)
    del parts
    gc.collect()
    print(f"  dsf rows: {len(dsf):,}", flush=True)

    print("Sorting + cumulative log returns ...", flush=True)
    dsf = dsf.sort_values(["cusip8", "dlycaldt"], kind="mergesort").reset_index(drop=True)
    dsf["log_ret"] = np.log1p(dsf["dlyret"].astype("float64"))
    dsf["cum_log_ret"] = dsf.groupby("cusip8", sort=False, observed=True)["log_ret"].cumsum()
    dsf = dsf.drop(columns=["dlyret", "log_ret"])
    gc.collect()

    cum_idx = {
        cu: (sub["dlycaldt"].values.astype("datetime64[ns]"),
             sub["cum_log_ret"].values.astype("float64"))
        for cu, sub in dsf.groupby("cusip8", sort=False, observed=True)
    }
    print(f"  cusip8 indexed: {len(cum_idx):,}", flush=True)
    del dsf
    gc.collect()

    print("Computing CARs ...", flush=True)
    t0 = time.time()
    car_arrs = {h: np.full(len(panel), np.nan, dtype="float64") for h in HORIZONS}
    rdq_vals = panel["rdq"].values.astype("datetime64[ns]")
    cu_vals = panel["cusip8"].values
    for i in range(len(panel)):
        cu = cu_vals[i]
        if cu is None or pd.isna(cu) or cu not in cum_idx:
            continue
        dates, cums = cum_idx[cu]
        rdq_p1 = rdq_vals[i] + np.timedelta64(1, "D")
        idx0 = int(np.searchsorted(dates, rdq_p1, side="left"))
        if idx0 >= len(dates):
            continue
        c0 = cums[idx0]
        for h in HORIZONS:
            target = rdq_vals[i] + np.timedelta64(h, "D")
            idx1 = int(np.searchsorted(dates, target, side="right")) - 1
            if idx1 < idx0:
                continue
            car_arrs[h][i] = cums[idx1] - c0
    for h in HORIZONS:
        panel[f"car_{h}"] = car_arrs[h]
    n_with = panel[[f"car_{h}" for h in HORIZONS]].notna().any(axis=1).sum()
    print(f"  panel rows with >=1 horizon: {n_with:,} elapsed={time.time()-t0:.1f}s", flush=True)
    panel.to_parquet(OUT_PATH, index=False)
    print(f"Wrote {OUT_PATH}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
