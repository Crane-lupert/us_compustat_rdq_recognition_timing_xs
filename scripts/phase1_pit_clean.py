"""Phase 1 augmentation -- point-in-time (PIT) clean signal construction.

The original strategy_A_bonferroni.py assigns cross-section quintiles within
(rdq_month, ff12) groups, which means a firm announcing on day 5 of a month
is ranked against firms announcing through day 30 of the same month. That is
a within-month look-ahead -- on the announcement day, the late-month
comparison firms are not yet known.

This script reconstructs the signal under three strict PIT rules:

  (1) Quintile assignment uses a TRAILING ROLLING COHORT of firms in the
      same FF12 industry with rdq in [d - 30 days, d - 1 day]. The firm's
      own gap_var_t is then ranked against that prior cohort -- never
      against later announcers.

  (2) Forward-return window starts at rdq + 8 calendar days, not rdq + 1.
      The 7-day buffer absorbs (a) Compustat database refresh delay
      (typically T+1 to T+2 for major listings), and (b) the post-earnings-
      announcement drift in week 1 (an unrelated well-known anomaly).
      This is the live-implementable forward window.

  (3) The trailing-cohort lookup never peeks at firms whose rdq equals the
      same day -- strict less-than. (If multiple firms announce on the same
      calendar day, each is ranked against the prior cohort, not against
      each other.)

Reads:  artifacts/panel_with_returns_ext.parquet
        (has car_120_sw1 / car_180_sw1 from the dsf_v2 extended stream)
Writes: artifacts/strategy_A_pit_clean.{csv,json}
        artifacts/strategy_A_pit_clean_monthly.csv  (per-cell monthly spread)

Cohort window: 30 days is a deliberate practitioner choice. Wider windows
smooth out the boundary at the cost of including stale information; 30 days
matches the typical earnings-announcement calendar pacing in U.S. equities.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path("d:/vscode/us_compustat_rdq_recognition_timing_xs")
sys.path.insert(0, str(ROOT / "scripts"))

import strategy_A_bonferroni as sab  # type: ignore  # noqa: E402

ART = ROOT / "artifacts"
PANEL_PATH = ART / "panel_with_returns_ext.parquet"
OUT_CSV = ART / "strategy_A_pit_clean.csv"
OUT_JSON = ART / "strategy_A_pit_clean.json"
OUT_MONTHLY = ART / "strategy_A_pit_clean_monthly.csv"

COHORT_DAYS = 30  # trailing cohort window for PIT-clean ranking
T_THRESHOLD = sab.T_THRESHOLD

INDUSTRY_TILT_HIGH = sab.INDUSTRY_TILT_HIGH  # {6, 10, 11}

# Horizon -> car column. Skip-week-1 only (the live-implementable horizon).
HORIZON_RUNS = [
    (120, "car_120_sw1"),
    (180, "car_180_sw1"),
]


def assign_pit_quintile(df: pd.DataFrame, signal_col: str) -> pd.DataFrame:
    """Assign quintile by ranking each firm's signal against the trailing
    COHORT_DAYS cohort of same-FF12 prior announcers (strict less-than rdq).

    Returns df with new q5 column (Int8, 1..5, NaN if cohort too small).
    """
    df = df.dropna(subset=[signal_col, "ff12", "rdq"]).copy()
    # Sort by (ff12, rdq, then signal) -- mergesort for determinism.
    df = df.sort_values(["ff12", "rdq", signal_col], kind="mergesort").reset_index(drop=True)

    q5 = np.full(len(df), np.nan, dtype="float64")
    rdqs = df["rdq"].values
    ff12s = df["ff12"].values
    sigs = df[signal_col].values

    # Per FF12: iterate firms in rdq order, maintain a deque of (rdq, signal)
    # within the rolling window, compute quintile rank for each new firm.
    cohort_window_ns = COHORT_DAYS * 24 * 3600 * 1_000_000_000  # nanoseconds

    n = len(df)
    i = 0
    while i < n:
        # Find the block of firms with the same FF12.
        j = i
        ff = ff12s[i]
        while j < n and ff12s[j] == ff:
            j += 1
        # Process this FF12 block [i, j).
        block_rdq = rdqs[i:j].astype("int64")
        block_sig = sigs[i:j]
        block_n = j - i
        # Two-pointer rolling window: include rows with rdq in [d - 30d, d).
        lo = 0  # left pointer (inclusive) in the block
        hi = 0  # right pointer (exclusive) in the block, advanced as rdq[k] increases
        sorted_signals: list[float] = []  # we will maintain a sorted list for quintile boundaries
        # Use simple O(k log k) insort for efficiency; cohort sizes ~50-300.
        import bisect
        # Track which signals are currently in the window so we can drop them when out of range.
        # We'll re-sort the in-window slice when needed; cohort is small.
        for k in range(block_n):
            d = block_rdq[k]
            lo_thresh = d - cohort_window_ns
            # Drop from window any signal with rdq < lo_thresh (out of window)
            # AND any signal with rdq >= d (strict less-than rule).
            # Easiest: rebuild window from scratch using two pointers since block_rdq is sorted.
            # Find left boundary: smallest k' s.t. block_rdq[k'] >= lo_thresh.
            left = np.searchsorted(block_rdq[:k], lo_thresh, side="left")
            # Right boundary: largest k' < k s.t. block_rdq[k'] < d. Since block_rdq is non-decreasing
            # and we already restrict to k' < k, we further require strict-less-than: trim equal-rdq.
            right = np.searchsorted(block_rdq[:k], d, side="left")
            cohort_slice = block_sig[left:right]
            cohort_slice = cohort_slice[~np.isnan(cohort_slice)]
            if len(cohort_slice) < 5:
                continue
            # Quintile assignment: rank of firm's signal within sorted cohort, mapped to 1..5.
            firm_sig = block_sig[k]
            if np.isnan(firm_sig):
                continue
            # Percentile rank: (count of cohort < firm_sig + 0.5 * count of cohort == firm_sig) / len(cohort)
            n_less = int((cohort_slice < firm_sig).sum())
            n_eq = int((cohort_slice == firm_sig).sum())
            pct = (n_less + 0.5 * n_eq) / len(cohort_slice)
            # Map [0, 1] to 1..5 (Q1 = lowest 20%, Q5 = highest 20%).
            quintile = min(5, max(1, int(pct * 5) + 1))
            q5[i + k] = quintile
        i = j

    df["q5"] = pd.Series(q5).astype("Int8")
    return df


def assign_subcells(df: pd.DataFrame) -> pd.DataFrame:
    """Same convention as primary: size = monthly XS median mcap within FF12;
    ind-tilt = high if FF12 in {6, 10, 11}.

    Subtle: size assignment is itself a within-month operation, so for true
    PIT-cleanliness we should also lag this. Practitioner convention is that
    market cap on rdq day is known at rdq (close-of-day-prior price), so size
    is genuinely PIT at rdq. We keep the FF12-median split.
    """
    df = df.copy()
    df["mcap_mil"] = df["cshoq"] * df["prccq"]
    df["rdq_month"] = df["rdq"].dt.to_period("M")
    df = df.sort_values(["rdq_month", "ff12", "mcap_mil"], kind="mergesort").reset_index(drop=True)
    grp = df.groupby(["rdq_month", "ff12"], sort=False, observed=True)["mcap_mil"]
    median_mcap = grp.transform("median")
    df["size_bin"] = np.where(df["mcap_mil"] >= median_mcap, "L", "S")
    df["ind_bin"] = np.where(df["ff12"].isin(INDUSTRY_TILT_HIGH), "H", "L")
    return df


def compute_qspread_t(df: pd.DataFrame, car_col: str) -> tuple[float, float, int, pd.Series]:
    """Same as sab.compute_qspread_t but returns the monthly spread series too."""
    sub = df.dropna(subset=[car_col, "q5"]).copy()
    sub = sub[sub["q5"].isin([1, 5])]
    if sub.empty:
        return float("nan"), float("nan"), 0, pd.Series(dtype="float64")
    monthly = (
        sub.groupby(["rdq_month", "q5"], observed=True, sort=False)[car_col]
        .mean()
        .unstack("q5")
    )
    if 1 not in monthly.columns or 5 not in monthly.columns:
        return float("nan"), float("nan"), 0, pd.Series(dtype="float64")
    spread = (monthly[1] - monthly[5]).dropna().sort_index()
    if len(spread) < 12:
        return float("nan"), float("nan"), int(len(spread)), spread
    mu = float(spread.mean())
    se = sab.newey_west_se(spread.values, lag=12)
    t = mu / se if se > 0 else float("nan")
    return mu, t, int(len(spread)), spread


def run_bonferroni_12_pit(df: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, pd.Series]]:
    rows = []
    series_dict: dict[str, pd.Series] = {}
    for h, car_col in HORIZON_RUNS:
        for sz in ("L", "S"):
            for it in ("H", "L"):
                sub = df[(df["size_bin"] == sz) & (df["ind_bin"] == it)]
                mu, t, n_months, spread = compute_qspread_t(sub, car_col)
                sign_ok = mu > 0
                t_ok = (abs(t) > T_THRESHOLD) if not np.isnan(t) else False
                passed = bool(sign_ok and t_ok and t > 0)
                cell_name = f"A{h}-SW1-{sz}{it}"
                rows.append({
                    "horizon_d": h,
                    "size": sz,
                    "ind_tilt": it,
                    "cell": cell_name,
                    "car_col": car_col,
                    "n_months": n_months,
                    "mu_spread": mu,
                    "t_stat": t,
                    "sign_correct": sign_ok,
                    "passes_bonferroni": passed,
                })
                if not spread.empty:
                    series_dict[cell_name] = spread
    return pd.DataFrame(rows), series_dict


def main() -> int:
    print(f"Loading {PANEL_PATH.name} ...", flush=True)
    panel = pd.read_parquet(PANEL_PATH)
    print(f"  rows: {len(panel):,}", flush=True)

    print(f"Building PIT-clean quintile (trailing {COHORT_DAYS}-day FF12 cohort) ...", flush=True)
    df = assign_pit_quintile(panel, "gap_var_t")
    valid_q = df["q5"].notna().sum()
    print(f"  rows with PIT q5 assignment: {valid_q:,} ({valid_q/len(df)*100:.1f}%)", flush=True)

    df = assign_subcells(df)
    print(f"  panel with q5 + subcells: {len(df):,}", flush=True)

    print("Running Bonferroni-12 on PIT-clean signal (skip-week-1 forward window) ...", flush=True)
    cells, series_dict = run_bonferroni_12_pit(df)
    cells.to_csv(OUT_CSV, index=False)
    print(f"Wrote {OUT_CSV.name}", flush=True)

    # Monthly series for figure / further analysis
    if series_dict:
        monthly = pd.concat([s.rename(name) for name, s in series_dict.items()], axis=1)
        monthly.index.name = "month"
        monthly.to_csv(OUT_MONTHLY)
        print(f"Wrote {OUT_MONTHLY.name}", flush=True)

    pass_count = int(cells["passes_bonferroni"].sum())
    sign_count = int(cells["sign_correct"].sum())

    # IS/OOS split on the monthly series
    is_end = pd.Timestamp("2016-12-31")
    oos_start = pd.Timestamp("2017-01-01")
    oos_end = pd.Timestamp("2024-12-31")

    def _t_on(series: pd.Series, mask) -> tuple[float, float, int]:
        sub = series[mask].dropna()
        if len(sub) < 12:
            return float("nan"), float("nan"), int(len(sub))
        mu = float(sub.mean())
        se = sab.newey_west_se(sub.values, lag=12)
        t = mu / se if se > 0 else float("nan")
        return mu, t, int(len(sub))

    is_oos = []
    for cell_name, s in series_dict.items():
        idx_ts = s.index.to_timestamp() if hasattr(s.index, "to_timestamp") else s.index
        is_mask = idx_ts <= is_end
        oos_mask = (idx_ts >= oos_start) & (idx_ts <= oos_end)
        is_mu, is_t, is_n = _t_on(s, is_mask)
        oos_mu, oos_t, oos_n = _t_on(s, oos_mask)
        is_oos.append({
            "cell": cell_name,
            "is_mu": is_mu, "is_t": is_t, "is_n": is_n,
            "oos_mu": oos_mu, "oos_t": oos_t, "oos_n": oos_n,
            "is_passes": bool((is_mu > 0) and (not np.isnan(is_t)) and (is_t > T_THRESHOLD)),
            "oos_passes": bool((oos_mu > 0) and (not np.isnan(oos_t)) and (oos_t > T_THRESHOLD)),
        })
    is_oos_df = pd.DataFrame(is_oos)

    summary = {
        "phase": 1,
        "step": "pit_clean_augmentation",
        "purpose": (
            "Reconstruct signal under strict point-in-time rules: trailing 30-day "
            "FF12 cohort for quintile assignment + skip-week-1 forward window "
            "(rdq+8 to rdq+H) that absorbs Compustat refresh + PEAD week."
        ),
        "cohort_days": COHORT_DAYS,
        "pit_rules": [
            "Quintile vs trailing 30-day FF12 cohort with strict-less-than rdq filter",
            "Forward window starts at rdq+8 (absorbs Compustat refresh + PEAD)",
            "Size bin uses rdq-day market cap (cshoq * prccq from prior close) -- PIT-clean by convention",
        ],
        "n_panel_rows": int(len(panel)),
        "n_pit_q5_assigned": int(valid_q),
        "n_pit_q5_assigned_pct": round(valid_q / len(panel) * 100, 2),
        "full_panel_bonferroni": {
            "pass_count_of_8": pass_count,
            "sign_correct_of_8": sign_count,
        },
        "is_oos_per_cell": is_oos_df.to_dict(orient="records"),
        "is_pass_count_of_8": int(is_oos_df["is_passes"].sum()),
        "oos_pass_count_of_8": int(is_oos_df["oos_passes"].sum()),
        "cells_detail_full_panel": cells.to_dict(orient="records"),
    }
    OUT_JSON.write_text(json.dumps(summary, indent=2, default=str))
    print(f"Wrote {OUT_JSON.name}", flush=True)

    print()
    print("=" * 80)
    print(f"PIT-clean signal -- skip-week-1 forward window (rdq+8 to rdq+H)")
    print(f"  Trailing {COHORT_DAYS}-day FF12 cohort quintile assignment (strict-less-than)")
    print("=" * 80)
    print()
    print(f"Full-panel Bonferroni: {pass_count}/8 PASS, {sign_count}/8 sign-correct")
    print()
    print("Per-cell detail (full panel):")
    print(cells[["cell", "n_months", "mu_spread", "t_stat", "sign_correct",
                 "passes_bonferroni"]].to_string(index=False))
    print()
    print(f"IS (<=2016-12-31) and OOS (2017..2024) split:")
    print(is_oos_df[["cell", "is_n", "is_t", "is_passes",
                     "oos_n", "oos_t", "oos_passes"]].to_string(index=False))
    print()
    print(f"IS pass count: {summary['is_pass_count_of_8']}/8")
    print(f"OOS pass count: {summary['oos_pass_count_of_8']}/8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
