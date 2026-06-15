"""shared_lib/rdq_panel_loader — shared cohort + features for Strategy A and B.

Loads Compustat fundq + builds rolling 8-Q features + bridges to CRSP daily
returns + applies NT-filer proxy exclusion. Used by both
experiments/strategy_A_variance_xs/ and
experiments/strategy_B_within_firm_rolling_baseline_xs/ — saves ~30-40% Phase 0
build cost.

Lock F compliance: every groupby/rolling operation is preceded by an explicit
sort to make ordering deterministic. No drop_duplicates without sort. No
groupby.agg first/last/nth without sort.
"""

from __future__ import annotations

import gzip
import logging
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

__version__ = "0.1.0"

FUNDQ_PATH = Path("E:/wrds-data-courier/output/dump/comp_na_daily_all.fundq.csv.gz")
NAMES_PATH = Path("E:/wrds-data-courier/output/dump/comp_na_daily_all.names.csv.gz")
DSF_V2_PATH = Path("E:/wrds-data-courier/output/dump/crsp_a_stock.dsf_v2.csv.gz")

PERIOD_START = pd.Timestamp("1999-01-01")
PERIOD_END = pd.Timestamp("2024-12-31")

GAP_FILTER_MIN_DAYS = 10
GAP_FILTER_MAX_DAYS = 180
ROLLING_WINDOW_Q = 8
ROLLING_MIN_VALID_Q = 6
NT_THRESHOLD_NON_ANNUAL_DAYS = 75
NT_THRESHOLD_ANNUAL_DAYS = 100


def ff12_from_sic(sic) -> int:
    """Fama-French 12 industry from 4-digit SIC."""
    if pd.isna(sic):
        return 12
    s = int(sic)
    if (100 <= s <= 999 or 2000 <= s <= 2399 or 2700 <= s <= 2749
            or 2770 <= s <= 2799 or 3100 <= s <= 3199 or 3940 <= s <= 3989):
        return 1
    if (2500 <= s <= 2519 or 2590 <= s <= 2599 or 3630 <= s <= 3659
            or 3710 <= s <= 3711 or s == 3714 or s == 3716
            or 3750 <= s <= 3751 or s == 3792 or 3900 <= s <= 3939 or 3990 <= s <= 3999):
        return 2
    if (2520 <= s <= 2589 or 2600 <= s <= 2699 or 2750 <= s <= 2769
            or 3000 <= s <= 3099 or 3200 <= s <= 3569 or 3580 <= s <= 3629
            or 3700 <= s <= 3709 or 3712 <= s <= 3713 or s == 3715
            or 3717 <= s <= 3749 or 3752 <= s <= 3791 or 3793 <= s <= 3799
            or 3830 <= s <= 3839 or 3860 <= s <= 3899):
        return 3
    if 1200 <= s <= 1399 or 2900 <= s <= 2999:
        return 4
    if 2800 <= s <= 2829 or 2840 <= s <= 2899:
        return 5
    if (3570 <= s <= 3579 or 3660 <= s <= 3692 or 3694 <= s <= 3699
            or 3810 <= s <= 3829 or 7370 <= s <= 7379):
        return 6
    if 4800 <= s <= 4899:
        return 7
    if 4900 <= s <= 4949:
        return 8
    if 5000 <= s <= 5999 or 7200 <= s <= 7299 or 7600 <= s <= 7699:
        return 9
    if 2830 <= s <= 2839 or s == 3693 or 3840 <= s <= 3859 or 8000 <= s <= 8099:
        return 10
    if 6000 <= s <= 6999:
        return 11
    return 12


def load_fundq(
    path: Path = FUNDQ_PATH,
    period_start: pd.Timestamp = PERIOD_START,
    period_end: pd.Timestamp = PERIOD_END,
    chunksize: int = 50_000,
) -> pd.DataFrame:
    """Stream comp_na_daily_all.fundq.csv.gz with standard NA/INDL/STD filters.

    Returns DataFrame with columns:
        gvkey (str), datadate (datetime), rdq (datetime), fyearq (int), fqtr (int),
        gap_days (int), atq (float), cshoq (float), prccq (float).
    """
    parts: list[pd.DataFrame] = []
    reader = pd.read_csv(
        path,
        compression="gzip",
        usecols=["gvkey", "datadate", "rdq", "fyearq", "fqtr",
                 "indfmt", "datafmt", "consol", "popsrc", "curcdq",
                 "atq", "cshoq", "prccq"],
        dtype={
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
        },
        parse_dates=["datadate", "rdq"],
        chunksize=chunksize,
        low_memory=False,
    )
    for chunk in reader:
        m = (
            (chunk["indfmt"] == "INDL")
            & (chunk["datafmt"] == "STD")
            & (chunk["consol"] == "C")
            & (chunk["popsrc"] == "D")
            & (chunk["curcdq"] == "USD")
            & chunk["rdq"].notna()
            & chunk["datadate"].notna()
        )
        chunk = chunk.loc[m].copy()
        chunk = chunk.loc[
            (chunk["datadate"] >= period_start) & (chunk["datadate"] <= period_end)
        ]
        chunk["gap_days"] = (chunk["rdq"] - chunk["datadate"]).dt.days.astype("int32")
        parts.append(chunk[["gvkey", "datadate", "rdq", "fyearq", "fqtr",
                             "gap_days", "atq", "cshoq", "prccq"]])
    df = pd.concat(parts, ignore_index=True)
    df = df.sort_values(["gvkey", "datadate"], kind="mergesort").reset_index(drop=True)
    return df


def filter_gap_window(
    df: pd.DataFrame,
    min_days: int = GAP_FILTER_MIN_DAYS,
    max_days: int = GAP_FILTER_MAX_DAYS,
) -> pd.DataFrame:
    """Drop firm-quarters with gap outside [min_days, max_days] (restatements/special periods)."""
    return df[df["gap_days"].between(min_days, max_days)].copy().reset_index(drop=True)


def rolling_8q_features(
    df: pd.DataFrame,
    window: int = ROLLING_WINDOW_Q,
    min_valid: int = ROLLING_MIN_VALID_Q,
) -> pd.DataFrame:
    """Compute gap_var_t (Strategy A) + gap_dev_t (Strategy B) per (gvkey, datadate).

    gap_var_t = std({gap_q : q in trailing `window` Q, ≥ `min_valid` valid})  # Strategy A
    gap_dev_t = gap_t − median({gap_q : q in trailing `window` Q, ≥ `min_valid` valid})  # Strategy B

    Input MUST contain ['gvkey','datadate','gap_days']. Sort is applied internally.

    Output adds columns: gap_var_t (float), gap_dev_t (float), n_valid_q (int).
    """
    df = df.sort_values(["gvkey", "datadate"], kind="mergesort").reset_index(drop=True)
    grouped = df.groupby("gvkey", sort=False, observed=True)["gap_days"]
    df["_roll_std"] = grouped.transform(
        lambda s: s.rolling(window=window, min_periods=min_valid).std()
    )
    df["_roll_med"] = grouped.transform(
        lambda s: s.rolling(window=window, min_periods=min_valid).median()
    )
    df["_roll_n"] = grouped.transform(
        lambda s: s.rolling(window=window, min_periods=1).count()
    )
    df["gap_var_t"] = df["_roll_std"].astype("float64")
    df["gap_dev_t"] = (df["gap_days"] - df["_roll_med"]).astype("float64")
    df["n_valid_q"] = df["_roll_n"].astype("int32")
    df = df.drop(columns=["_roll_std", "_roll_med", "_roll_n"])
    return df


def exclude_nt_filers(
    panel: pd.DataFrame,
    non_annual_threshold: int = NT_THRESHOLD_NON_ANNUAL_DAYS,
    annual_threshold: int = NT_THRESHOLD_ANNUAL_DAYS,
) -> pd.DataFrame:
    """Drop firm-quarters whose `gap_days` exceeds the NT-proxy threshold.

    fqtr in {1,2,3} (10-Q): gap_days > non_annual_threshold → drop
    fqtr == 4 (10-K):       gap_days > annual_threshold     → drop

    Sub-gate (c) audit established this proxy at ~4% of the sample.
    """
    is_annual = panel["fqtr"] == 4
    keep = (
        ((~is_annual) & (panel["gap_days"] <= non_annual_threshold))
        | (is_annual & (panel["gap_days"] <= annual_threshold))
    )
    return panel.loc[keep].reset_index(drop=True)


def ccm_bridge_via_names(panel: pd.DataFrame) -> pd.DataFrame:
    """Add 8-char CUSIP from comp_na_daily_all.names (USAGE-blocked crsp_a_ccm fallback).

    Input MUST contain 'gvkey'. Adds: cusip8, sic, ff12, conm.
    """
    names = pd.read_csv(
        NAMES_PATH,
        usecols=["gvkey", "cusip", "sic", "conm"],
        dtype={
            "gvkey": "string[pyarrow]",
            "cusip": "string[pyarrow]",
            "sic": "Int32",
            "conm": "string[pyarrow]",
        },
    )
    names = names.sort_values("gvkey", kind="mergesort").drop_duplicates(
        subset=["gvkey"], keep="last"
    )
    names["cusip8"] = names["cusip"].str.slice(0, 8)
    names["ff12"] = names["sic"].apply(ff12_from_sic).astype("int8")
    out = panel.merge(
        names[["gvkey", "cusip8", "sic", "ff12", "conm"]], on="gvkey", how="left"
    )
    return out


def forward_returns(
    panel: pd.DataFrame,
    horizons_days: Iterable[int] = (60, 120, 180),
    dsf_path: Path = DSF_V2_PATH,
    chunksize: int = 1_000_000,
) -> pd.DataFrame:
    """Compute forward log cumulative returns over `horizons_days` after rdq+1.

    Input MUST contain ['gvkey','rdq','cusip8']. Adds columns:
        car_<H> for each H in horizons_days (cumulative log return rdq+1 → rdq+H).

    Streams crsp_a_stock.dsf_v2 in chunks. Only loads rows whose cusip[:8] is
    in the panel's cusip8 set.

    Lock F: sort by (permno, dlycaldt) before any per-stock rolling.
    """
    panel = panel.copy()
    panel = panel.dropna(subset=["cusip8"])
    cusip8_set = set(panel["cusip8"].dropna().unique().tolist())
    if not cusip8_set:
        return panel

    parts: list[pd.DataFrame] = []
    reader = pd.read_csv(
        dsf_path,
        compression="gzip",
        usecols=["permno", "cusip", "dlycaldt", "dlyret"],
        dtype={
            "permno": "int32",
            "cusip": "string[pyarrow]",
            "dlyret": "float32",
        },
        parse_dates=["dlycaldt"],
        chunksize=chunksize,
        low_memory=False,
    )
    for chunk in reader:
        chunk["cusip8"] = chunk["cusip"].str.slice(0, 8)
        chunk = chunk[chunk["cusip8"].isin(cusip8_set)]
        if chunk.empty:
            continue
        chunk = chunk[["cusip8", "permno", "dlycaldt", "dlyret"]].copy()
        parts.append(chunk)
    if not parts:
        for h in horizons_days:
            panel[f"car_{h}"] = np.nan
        return panel

    dsf = pd.concat(parts, ignore_index=True)
    dsf = dsf.dropna(subset=["dlyret"])
    dsf = dsf.sort_values(["cusip8", "dlycaldt"], kind="mergesort").reset_index(drop=True)
    dsf["log_ret"] = np.log1p(dsf["dlyret"].astype("float64"))

    horizons = sorted(set(int(h) for h in horizons_days))
    h_max = horizons[-1]

    grp = dsf.groupby("cusip8", sort=False, observed=True)["log_ret"]
    # cumulative log return from t+1 to t+h:
    #   c[t+h] - c[t]    where c is cumulative
    dsf["cum_log_ret"] = grp.cumsum()

    panel = panel.copy()
    panel["rdq_p1"] = panel["rdq"] + pd.Timedelta(days=1)

    cum_by_cusip = (
        dsf.set_index("dlycaldt")
        .groupby("cusip8", sort=False)["cum_log_ret"]
    )
    cum_dict = {c: g for c, g in cum_by_cusip}

    car_arrays = {h: np.full(len(panel), np.nan, dtype="float64") for h in horizons}
    for i, (cu, rdq_p1) in enumerate(zip(panel["cusip8"].values, panel["rdq_p1"].values)):
        if cu is None or pd.isna(cu) or cu not in cum_dict:
            continue
        series = cum_dict[cu]
        # cumulative at the trading day at or after rdq+1
        idx0 = series.index.searchsorted(rdq_p1, side="left")
        if idx0 >= len(series):
            continue
        c0 = series.iloc[idx0]
        for h in horizons:
            target = pd.Timestamp(rdq_p1) + pd.Timedelta(days=h)
            idx1 = series.index.searchsorted(target, side="right") - 1
            if idx1 < idx0:
                continue
            c1 = series.iloc[idx1]
            car_arrays[h][i] = c1 - c0

    for h in horizons:
        panel[f"car_{h}"] = car_arrays[h]

    panel = panel.drop(columns=["rdq_p1"])
    return panel


def build_panel(
    apply_nt_exclusion: bool = True,
    include_returns: bool = False,
) -> pd.DataFrame:
    """End-to-end shared panel constructor used by both strategies.

    Pipeline:
      1. load_fundq()
      2. filter_gap_window([10, 180])
      3. rolling_8q_features(window=8, min_valid=6)
      4. drop rows with NaN gap_var_t (insufficient history)
      5. ccm_bridge_via_names() (add cusip8, sic, ff12, conm)
      6. exclude_nt_filers() if requested
      7. forward_returns() if requested
    """
    logger.info("rdq_panel_loader.build_panel: loading fundq")
    df = load_fundq()
    df = filter_gap_window(df)
    df = rolling_8q_features(df)
    df = df.dropna(subset=["gap_var_t"]).reset_index(drop=True)
    df = ccm_bridge_via_names(df)
    if apply_nt_exclusion:
        df = exclude_nt_filers(df)
    if include_returns:
        df = forward_returns(df)
    return df
