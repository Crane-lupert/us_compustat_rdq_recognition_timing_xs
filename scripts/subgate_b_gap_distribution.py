"""Sub-gate (b) — rdq-datadate gap empirical distribution.

Reads E:/wrds-data-courier/output/dump/comp_na_daily_all.fundq.csv.gz in chunks,
computes the (rdq - datadate) gap distribution post standard Compustat filters,
and writes artifacts/subgate_b_gap_distribution.json + .csv.

Graduated 3-tier verdict (SPEC.md §0):
  PASS:       median in [25, 90] AND ≥70% rows in [10, 180]
  BORDERLINE: median in [20, 100] AND ≥60% rows in [10, 180]
  KILL:       median outside [20, 100] OR <60% rows in [10, 180]

Filters (standard Compustat NA INDL/STD/C/D):
  indfmt == 'INDL'
  datafmt == 'STD'
  consol == 'C'
  popsrc == 'D'
  curcdq == 'USD'
  1999-01-01 <= datadate <= 2024-12-31
  rdq not null
"""

from __future__ import annotations

import gzip
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

FUNDQ_PATH = Path("E:/wrds-data-courier/output/dump/comp_na_daily_all.fundq.csv.gz")
REPO_ROOT = Path("d:/vscode/us_compustat_rdq_recognition_timing_xs")
OUT_DIR = REPO_ROOT / "artifacts"
OUT_DIR.mkdir(parents=True, exist_ok=True)

USECOLS = [
    "gvkey", "datadate", "rdq", "fyearq", "fqtr",
    "indfmt", "datafmt", "consol", "popsrc", "curcdq",
    "atq", "cshoq", "prccq",
]

DTYPE = {
    "gvkey": "string[pyarrow]",
    "indfmt": "category",
    "datafmt": "category",
    "consol": "category",
    "popsrc": "category",
    "curcdq": "category",
    "fyearq": "Int32",
    "fqtr": "Int8",
    "atq": "float32",
    "cshoq": "float32",
    "prccq": "float32",
}

PARSE_DATES = ["datadate", "rdq"]

CHUNK_SIZE = 50_000

PERIOD_START = pd.Timestamp("1999-01-01")
PERIOD_END = pd.Timestamp("2024-12-31")
GAP_FILTER_MIN = 10
GAP_FILTER_MAX = 180


def stream_fundq() -> pd.DataFrame:
    parts: list[pd.DataFrame] = []
    total_rows_raw = 0
    total_rows_post_indl = 0
    total_rows_post_rdq = 0
    reader = pd.read_csv(
        FUNDQ_PATH,
        compression="gzip",
        usecols=USECOLS,
        dtype=DTYPE,
        parse_dates=PARSE_DATES,
        chunksize=CHUNK_SIZE,
        low_memory=False,
    )
    for i, chunk in enumerate(reader):
        total_rows_raw += len(chunk)
        m_indl = (
            (chunk["indfmt"] == "INDL")
            & (chunk["datafmt"] == "STD")
            & (chunk["consol"] == "C")
            & (chunk["popsrc"] == "D")
            & (chunk["curcdq"] == "USD")
        )
        chunk = chunk.loc[m_indl].copy()
        total_rows_post_indl += len(chunk)
        chunk = chunk.loc[chunk["rdq"].notna() & chunk["datadate"].notna()].copy()
        total_rows_post_rdq += len(chunk)
        chunk = chunk.loc[
            (chunk["datadate"] >= PERIOD_START) & (chunk["datadate"] <= PERIOD_END)
        ].copy()
        chunk["gap_days"] = (chunk["rdq"] - chunk["datadate"]).dt.days.astype("Int64")
        parts.append(chunk)
        if (i + 1) % 5 == 0:
            print(f"  chunk {i+1}: raw={total_rows_raw:,} post-INDL={total_rows_post_indl:,} post-rdq={total_rows_post_rdq:,}", flush=True)

    df = pd.concat(parts, ignore_index=True)
    df.attrs["total_rows_raw"] = total_rows_raw
    df.attrs["total_rows_post_indl"] = total_rows_post_indl
    df.attrs["total_rows_post_rdq"] = total_rows_post_rdq
    return df


def main() -> int:
    print("Loading comp_na_daily_all.fundq.csv.gz ...", flush=True)
    df = stream_fundq()
    print(f"Loaded {len(df):,} firm-quarter rows post filters", flush=True)

    gap = df["gap_days"].dropna().astype("int64")
    n = int(len(gap))

    pct_in_filter = float((gap.between(GAP_FILTER_MIN, GAP_FILTER_MAX)).mean()) if n else 0.0
    pct_neg = float((gap < 0).mean()) if n else 0.0
    pct_zero = float((gap == 0).mean()) if n else 0.0
    pct_huge = float((gap > 365).mean()) if n else 0.0

    quantiles = {f"q{int(q*100):02d}": float(gap.quantile(q)) for q in
                 [0.01, 0.05, 0.10, 0.25, 0.50, 0.75, 0.90, 0.95, 0.99]}

    median = float(gap.median())
    mean = float(gap.mean())
    std = float(gap.std())

    median_pass = 25 <= median <= 90
    yield_pass = pct_in_filter >= 0.70
    median_borderline = 20 <= median <= 100
    yield_borderline = pct_in_filter >= 0.60

    if median_pass and yield_pass:
        verdict = "PASS"
    elif median_borderline and yield_borderline:
        verdict = "BORDERLINE"
    else:
        verdict = "KILL"

    df_post_filter = df[df["gap_days"].between(GAP_FILTER_MIN, GAP_FILTER_MAX)].copy()
    by_year = (
        df_post_filter.assign(yr=df_post_filter["datadate"].dt.year)
        .groupby("yr")["gap_days"]
        .agg(["count", "median", "mean", "std"])
        .reset_index()
    )

    n_firms = int(df["gvkey"].nunique())
    n_firms_post_filter = int(df_post_filter["gvkey"].nunique())

    df_with_mcap = df_post_filter.assign(
        mcap_mil=lambda d: d["cshoq"] * d["prccq"]
    )
    mcap_quintile_summary = (
        df_with_mcap.dropna(subset=["mcap_mil"])
        .assign(mcap_q=lambda d: pd.qcut(d["mcap_mil"].rank(method="first"), 5, labels=[1, 2, 3, 4, 5]))
        .groupby("mcap_q", observed=True)["gap_days"]
        .agg(["count", "median", "mean"])
        .reset_index()
    )
    mcap_quintile_summary["mcap_q"] = mcap_quintile_summary["mcap_q"].astype("int")

    result = {
        "subgate": "(b) rdq-datadate gap distribution GRADUATED",
        "verdict": verdict,
        "thresholds": {
            "PASS_median_range": [25, 90],
            "PASS_yield_floor": 0.70,
            "BORDERLINE_median_range": [20, 100],
            "BORDERLINE_yield_floor": 0.60,
            "gap_filter_window_days": [GAP_FILTER_MIN, GAP_FILTER_MAX],
        },
        "n_rows_raw": int(df.attrs["total_rows_raw"]),
        "n_rows_post_indl_std_c_d_usd": int(df.attrs["total_rows_post_indl"]),
        "n_rows_post_rdq_notna": int(df.attrs["total_rows_post_rdq"]),
        "n_rows_period_1999_2024": int(len(df)),
        "n_firms_pre_filter": n_firms,
        "n_firms_post_filter": n_firms_post_filter,
        "n_rows_post_gap_filter": int(len(df_post_filter)),
        "median_days": median,
        "mean_days": mean,
        "std_days": std,
        "pct_in_filter_window": pct_in_filter,
        "pct_neg_gap": pct_neg,
        "pct_zero_gap": pct_zero,
        "pct_over_365d": pct_huge,
        "quantiles": quantiles,
    }

    out_json = OUT_DIR / "subgate_b_gap_distribution.json"
    out_json.write_text(json.dumps(result, indent=2))
    print(f"Wrote {out_json}", flush=True)

    by_year.to_csv(OUT_DIR / "subgate_b_gap_by_year.csv", index=False)
    mcap_quintile_summary.to_csv(OUT_DIR / "subgate_b_gap_by_mcap_quintile.csv", index=False)
    print(f"Wrote per-year + mcap quintile summaries", flush=True)

    print()
    print("=" * 70)
    print(f"SUB-GATE (b) VERDICT: {verdict}")
    print("=" * 70)
    print(f"  n rows post period filter: {len(df):,}")
    print(f"  n firms post gap filter:   {n_firms_post_filter:,}")
    print(f"  median gap:                {median:.2f}d")
    print(f"  mean gap:                  {mean:.2f}d")
    print(f"  std:                       {std:.2f}d")
    print(f"  % in [{GAP_FILTER_MIN},{GAP_FILTER_MAX}]d window: {pct_in_filter*100:.2f}%")
    print(f"  % neg gap:                 {pct_neg*100:.4f}%")
    print(f"  % zero gap:                {pct_zero*100:.4f}%")
    print(f"  % >365d:                   {pct_huge*100:.4f}%")
    print(f"  quantiles: {quantiles}")

    return 0 if verdict != "KILL" else 2


if __name__ == "__main__":
    sys.exit(main())
