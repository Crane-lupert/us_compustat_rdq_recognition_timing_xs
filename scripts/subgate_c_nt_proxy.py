"""Sub-gate (c) — V5 NT-filer exclusion proxy quantification.

Since SEC EDGAR Form NT-10K/NT-10Q filings are not in the WRDS local dump and
Rule 6 prohibits external-API calls in Phase 0, we use a gap-based proxy for
NT-correlated firm-quarters:

  NT_proxy_q = gap_days > NT_GRACE_THRESHOLD (default 75d)

Rationale:
  - SEC 10-Q deadline = 40d (accelerated) / 45d (non-accelerated) after Q-end
  - SEC 10-K deadline = 60d (large accel) / 75d (accel) / 90d (non-accel) after FY-end
  - NT-10Q grace = +5d additional / NT-10K grace = +15d
  - Empirical p95 of gap = 95d, p99 = 247d (from sub-gate b)
  - Firm-quarters in the long tail (gap > 75d for non-annual or > 100d for annual)
    are statistically NT-correlated even without direct EDGAR cross-ref

This proxy is conservative — it tags MORE firm-quarters as "NT-correlated" than
actual NT filings (because some firms just have systematically slow reporting
without filing NT). That's the desired direction for sub-gate (c) — we want
mechanical confound mitigation, not perfect NT detection.

Outputs:
  artifacts/subgate_c_nt_proxy_counts.json
  artifacts/subgate_c_nt_proxy_by_fqtr.csv
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

FUNDQ_PATH = Path("E:/wrds-data-courier/output/dump/comp_na_daily_all.fundq.csv.gz")
REPO_ROOT = Path("d:/vscode/us_compustat_rdq_recognition_timing_xs")
OUT_DIR = REPO_ROOT / "artifacts"
OUT_DIR.mkdir(parents=True, exist_ok=True)

PERIOD_START = pd.Timestamp("1999-01-01")
PERIOD_END = pd.Timestamp("2024-12-31")

NT_THRESHOLD_NON_ANNUAL = 75
NT_THRESHOLD_ANNUAL = 100


def stream_fundq() -> pd.DataFrame:
    parts: list[pd.DataFrame] = []
    reader = pd.read_csv(
        FUNDQ_PATH,
        compression="gzip",
        usecols=["gvkey", "datadate", "rdq", "fqtr",
                 "indfmt", "datafmt", "consol", "popsrc", "curcdq"],
        dtype={
            "gvkey": "string[pyarrow]",
            "indfmt": "category",
            "datafmt": "category",
            "consol": "category",
            "popsrc": "category",
            "curcdq": "category",
            "fqtr": "Int8",
        },
        parse_dates=["datadate", "rdq"],
        chunksize=50_000,
        low_memory=False,
    )
    for chunk in reader:
        m_indl = (
            (chunk["indfmt"] == "INDL")
            & (chunk["datafmt"] == "STD")
            & (chunk["consol"] == "C")
            & (chunk["popsrc"] == "D")
            & (chunk["curcdq"] == "USD")
        )
        chunk = chunk.loc[m_indl & chunk["rdq"].notna() & chunk["datadate"].notna()].copy()
        chunk = chunk.loc[
            (chunk["datadate"] >= PERIOD_START) & (chunk["datadate"] <= PERIOD_END)
        ]
        chunk["gap_days"] = (chunk["rdq"] - chunk["datadate"]).dt.days.astype("int32")
        chunk = chunk[chunk["gap_days"].between(10, 180)]
        parts.append(chunk[["gvkey", "datadate", "fqtr", "gap_days"]])
    return pd.concat(parts, ignore_index=True)


def main() -> int:
    print("Loading fundq (gap-filtered) ...", flush=True)
    df = stream_fundq()
    n_total = int(len(df))
    print(f"  Total firm-Q post gap filter: {n_total:,}", flush=True)

    df["is_annual"] = (df["fqtr"] == 4).fillna(False)
    df["nt_proxy"] = (
        ((~df["is_annual"]) & (df["gap_days"] > NT_THRESHOLD_NON_ANNUAL))
        | ((df["is_annual"]) & (df["gap_days"] > NT_THRESHOLD_ANNUAL))
    )

    n_nt = int(df["nt_proxy"].sum())
    n_kept = n_total - n_nt
    n_firms_nt = int(df.loc[df["nt_proxy"], "gvkey"].nunique())
    n_firms_total = int(df["gvkey"].nunique())

    by_fqtr = (
        df.groupby("fqtr")
        .agg(n=("gap_days", "count"), n_nt=("nt_proxy", "sum"))
        .assign(pct_nt=lambda d: (d["n_nt"] / d["n"] * 100).round(3))
        .reset_index()
    )
    by_fqtr.to_csv(OUT_DIR / "subgate_c_nt_proxy_by_fqtr.csv", index=False)

    by_year = (
        df.assign(yr=df["datadate"].dt.year)
        .groupby("yr")
        .agg(n=("gap_days", "count"), n_nt=("nt_proxy", "sum"))
        .assign(pct_nt=lambda d: (d["n_nt"] / d["n"] * 100).round(3))
        .reset_index()
    )
    by_year.to_csv(OUT_DIR / "subgate_c_nt_proxy_by_year.csv", index=False)

    nt_pool = df.loc[df["nt_proxy"], ["gvkey", "datadate", "fqtr", "gap_days"]].copy()
    nt_pool.to_csv(OUT_DIR / "subgate_c_nt_proxy_exclusion_pool.csv.gz",
                   index=False, compression="gzip")

    result = {
        "subgate": "(c) V5 SEC Form NT differentiation 3-axis + NT-proxy exclusion",
        "method": "gap-based proxy (no SEC EDGAR offline; Rule 6 compliant)",
        "thresholds": {
            "non_annual_gap_threshold_days": NT_THRESHOLD_NON_ANNUAL,
            "annual_gap_threshold_days": NT_THRESHOLD_ANNUAL,
        },
        "n_total_firm_q": n_total,
        "n_nt_proxy_firm_q": n_nt,
        "pct_nt_proxy_firm_q": round(n_nt / max(n_total, 1) * 100, 3),
        "n_after_nt_exclusion": n_kept,
        "pct_retained_after_exclusion": round(n_kept / max(n_total, 1) * 100, 3),
        "n_firms_with_any_nt_proxy_q": n_firms_nt,
        "n_firms_total": n_firms_total,
        "pct_firms_touched_by_nt_proxy": round(n_firms_nt / max(n_firms_total, 1) * 100, 3),
        "exclusion_pool_csv": str((OUT_DIR / "subgate_c_nt_proxy_exclusion_pool.csv.gz").as_posix()),
    }

    out_json = OUT_DIR / "subgate_c_nt_proxy_counts.json"
    out_json.write_text(json.dumps(result, indent=2))
    print(f"Wrote {out_json}", flush=True)

    print()
    print("=" * 70)
    print(f"  Total firm-Q (gap-filtered):      {n_total:,}")
    print(f"  NT-proxy firm-Q (excluded):       {n_nt:,} ({result['pct_nt_proxy_firm_q']}%)")
    print(f"  Retained for primary results:     {n_kept:,} ({result['pct_retained_after_exclusion']}%)")
    print(f"  Firms with ≥1 NT-proxy Q:         {n_firms_nt:,} of {n_firms_total:,} ({result['pct_firms_touched_by_nt_proxy']}%)")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    sys.exit(main())
