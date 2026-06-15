"""Sub-gate (b) addendum — sample-shape vs CRSP universe (Rule 10 audit).

Joins post-filter sample to comp_na_daily_all.names for SIC + FF12 bucket
distribution. Compares the gap-filter sample (n=740,523 firm-Q) against the
pre-filter superset (n=2,116,530 raw fundq rows). A pass means the gap filter
does NOT materially distort SIC, FF12, or mcap-quintile distributions.

We do NOT load dsf_v2 here — that's 4.42 GB. The fundq pre-filter superset is
an adequate proxy for the CRSP-listed Compustat universe at this audit stage.
A full dsf_v2 cross-check can be deferred to Day-2 inside shared_lib.
"""

from __future__ import annotations

import gzip
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

FUNDQ_PATH = Path("E:/wrds-data-courier/output/dump/comp_na_daily_all.fundq.csv.gz")
NAMES_PATH = Path("E:/wrds-data-courier/output/dump/comp_na_daily_all.names.csv.gz")
REPO_ROOT = Path("d:/vscode/us_compustat_rdq_recognition_timing_xs")
OUT_DIR = REPO_ROOT / "artifacts"
OUT_DIR.mkdir(parents=True, exist_ok=True)

PERIOD_START = pd.Timestamp("1999-01-01")
PERIOD_END = pd.Timestamp("2024-12-31")


def ff12_from_sic(sic) -> int:
    """Fama-French 12 industry mapping (Ken French, 4-digit SIC)."""
    if pd.isna(sic):
        return 12
    s = int(sic)
    # 1 NoDur
    if (100 <= s <= 999 or 2000 <= s <= 2399 or 2700 <= s <= 2749
            or 2770 <= s <= 2799 or 3100 <= s <= 3199 or 3940 <= s <= 3989):
        return 1
    # 2 Durbl
    if (2500 <= s <= 2519 or 2590 <= s <= 2599 or 3630 <= s <= 3659
            or 3710 <= s <= 3711 or s == 3714 or s == 3716
            or 3750 <= s <= 3751 or s == 3792 or 3900 <= s <= 3939 or 3990 <= s <= 3999):
        return 2
    # 3 Manuf
    if (2520 <= s <= 2589 or 2600 <= s <= 2699 or 2750 <= s <= 2769
            or 3000 <= s <= 3099 or 3200 <= s <= 3569 or 3580 <= s <= 3629
            or 3700 <= s <= 3709 or 3712 <= s <= 3713 or s == 3715
            or 3717 <= s <= 3749 or 3752 <= s <= 3791 or 3793 <= s <= 3799
            or 3830 <= s <= 3839 or 3860 <= s <= 3899):
        return 3
    # 4 Enrgy
    if 1200 <= s <= 1399 or 2900 <= s <= 2999:
        return 4
    # 5 Chems
    if 2800 <= s <= 2829 or 2840 <= s <= 2899:
        return 5
    # 6 BusEq
    if (3570 <= s <= 3579 or 3660 <= s <= 3692 or 3694 <= s <= 3699
            or 3810 <= s <= 3829 or 7370 <= s <= 7379):
        return 6
    # 7 Telcm
    if 4800 <= s <= 4899:
        return 7
    # 8 Utils
    if 4900 <= s <= 4949:
        return 8
    # 9 Shops
    if 5000 <= s <= 5999 or 7200 <= s <= 7299 or 7600 <= s <= 7699:
        return 9
    # 10 Hlth
    if 2830 <= s <= 2839 or s == 3693 or 3840 <= s <= 3859 or 8000 <= s <= 8099:
        return 10
    # 11 Money
    if 6000 <= s <= 6999:
        return 11
    return 12  # 12 Other


def load_names() -> pd.DataFrame:
    df = pd.read_csv(
        NAMES_PATH,
        usecols=["gvkey", "sic", "conm"],
        dtype={"gvkey": "string[pyarrow]", "sic": "Int32", "conm": "string[pyarrow]"},
    )
    df = df.sort_values("gvkey", kind="mergesort").drop_duplicates(
        subset=["gvkey"], keep="last"
    )
    return df


def stream_fundq_minimal() -> pd.DataFrame:
    parts: list[pd.DataFrame] = []
    reader = pd.read_csv(
        FUNDQ_PATH,
        compression="gzip",
        usecols=["gvkey", "datadate", "rdq",
                 "indfmt", "datafmt", "consol", "popsrc", "curcdq",
                 "cshoq", "prccq"],
        dtype={
            "gvkey": "string[pyarrow]",
            "indfmt": "category",
            "datafmt": "category",
            "consol": "category",
            "popsrc": "category",
            "curcdq": "category",
            "cshoq": "float32",
            "prccq": "float32",
        },
        parse_dates=["datadate", "rdq"],
        chunksize=50_000,
        low_memory=False,
    )
    for i, chunk in enumerate(reader):
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
        chunk = chunk[["gvkey", "datadate", "gap_days", "cshoq", "prccq"]]
        parts.append(chunk)
    return pd.concat(parts, ignore_index=True)


def make_buckets(df: pd.DataFrame, names: pd.DataFrame) -> pd.DataFrame:
    df = df.merge(names, on="gvkey", how="left")
    df["ff12"] = df["sic"].apply(lambda s: ff12_from_sic(s) if not pd.isna(s) else 12).astype("int8")
    df["mcap_mil"] = (df["cshoq"] * df["prccq"]).astype("float64")
    return df


def dist_table(df: pd.DataFrame, col: str, label: str) -> pd.DataFrame:
    counts = df[col].value_counts(dropna=False).sort_index()
    out = pd.DataFrame({"bucket": counts.index.astype(str), label: counts.values})
    out[label + "_pct"] = (out[label] / out[label].sum() * 100).round(3)
    return out


def main() -> int:
    print("Loading names ...", flush=True)
    names = load_names()
    print(f"  names rows: {len(names):,}", flush=True)

    print("Loading fundq (pre-filter superset) ...", flush=True)
    full = stream_fundq_minimal()
    print(f"  fundq pre-filter rows: {len(full):,}", flush=True)

    full = make_buckets(full, names)
    sub = full[full["gap_days"].between(10, 180)].copy()
    print(f"  fundq post-gap-filter rows: {len(sub):,}", flush=True)

    ff_full = dist_table(full, "ff12", "n_pre")
    ff_sub = dist_table(sub, "ff12", "n_post")
    ff = ff_full.merge(ff_sub, on="bucket", how="outer").fillna(0)
    ff["drift_pp"] = (ff["n_post_pct"] - ff["n_pre_pct"]).round(3)
    ff.to_csv(OUT_DIR / "subgate_b_crsp_uniformity_ff12.csv", index=False)

    full["mcap_q"] = pd.qcut(
        full["mcap_mil"].rank(method="first", na_option="keep"), 5, labels=[1, 2, 3, 4, 5]
    )
    sub_mcap = full.loc[full["gap_days"].between(10, 180), ["mcap_q"]].dropna()
    mq_full = dist_table(full.dropna(subset=["mcap_q"]), "mcap_q", "n_pre")
    mq_sub = dist_table(sub_mcap, "mcap_q", "n_post")
    mq = mq_full.merge(mq_sub, on="bucket", how="outer").fillna(0)
    mq["drift_pp"] = (mq["n_post_pct"] - mq["n_pre_pct"]).round(3)
    mq.to_csv(OUT_DIR / "subgate_b_crsp_uniformity_mcap_quintile.csv", index=False)

    summary = {
        "subgate_b_rule10": "CRSP-uniformity sample-shape audit",
        "n_pre_filter": int(len(full)),
        "n_post_filter": int(len(sub)),
        "retention_pct": round(len(sub) / max(len(full), 1) * 100, 3),
        "ff12_max_abs_drift_pp": float(ff["drift_pp"].abs().max()),
        "mcap_quintile_max_abs_drift_pp": float(mq["drift_pp"].abs().max()),
        "ff12_table": ff.to_dict(orient="records"),
        "mcap_quintile_table": mq.to_dict(orient="records"),
    }

    out_json = OUT_DIR / "subgate_b_crsp_uniformity.json"
    out_json.write_text(json.dumps(summary, indent=2, default=str))
    print(f"Wrote {out_json}", flush=True)

    print()
    print("=" * 70)
    print(f"FF12 max abs drift:        {summary['ff12_max_abs_drift_pp']:.2f} pp")
    print(f"mcap quintile max drift:   {summary['mcap_quintile_max_abs_drift_pp']:.2f} pp")
    print(f"retention post gap filter: {summary['retention_pct']:.2f}%")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    sys.exit(main())
