"""Strategy A — Bonferroni-12 + LDS empirical (rdq-datadate gap variance XS).

Reads:  artifacts/panel_with_returns.parquet (620,290 firm-Q with gap_var_t, ff12, car_60/120/180)
Writes: artifacts/strategy_A_bonferroni12.json + .csv
        artifacts/strategy_A_lds.json

Signal: gap_var_t — std of 8-Q rolling gap (Strategy A)
Direction Lock C: Q1 (low-var) − Q5 (high-var) > 0 (high-var = NEG forward CAR)
Bonferroni-12: 3 horizons × 4 sub-cells (size large/small × ind-tilt high/low)
Threshold: |t| > 2.78 AND sign-correct
Verdict (graduated): PASS ≥3 / BORDERLINE 2 / KILL <2

Lock F: all sort_values calls use kind="mergesort" + explicit by-columns;
        no groupby.agg first/last/nth without sort; no drop_duplicates without sort.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ART = Path("d:/vscode/us_compustat_rdq_recognition_timing_xs/artifacts")
PANEL_PATH = ART / "panel_with_returns.parquet"

HORIZONS = [60, 120, 180]
BONF_ALPHA = 0.05 / 12
T_THRESHOLD = 2.78
LDS_AXES = 7

INDUSTRY_TILT_HIGH = {6, 10, 11}  # BusEq, Hlth, Money — high cadence-sensitivity sectors
INDUSTRY_TILT_LOW = {1, 2, 3, 4, 5, 7, 8, 9, 12}


def _qcut_safe(s: pd.Series, q: int = 5) -> pd.Series:
    """Quintile assignment that returns NaN when group has too few unique ranks."""
    s = s.dropna()
    if len(s) < q:
        return pd.Series([np.nan] * len(s), index=s.index)
    try:
        return pd.qcut(s.rank(method="first"), q, labels=list(range(1, q + 1)))
    except (ValueError, IndexError):
        return pd.Series([np.nan] * len(s), index=s.index)


def build_monthly_xs_panel(panel: pd.DataFrame, signal_col: str) -> pd.DataFrame:
    """Monthly cross-sectional quintile within FF12 sector.

    For Strategy A: quintile by gap_var_t, where Q5 = high-var (NEG prediction),
    Q1 = low-var. Spread = Q1 − Q5 (pre-registered POSITIVE).
    """
    df = panel.dropna(subset=[signal_col, "ff12"]).copy()
    df["rdq_month"] = df["rdq"].dt.to_period("M")
    df = df.sort_values(["rdq_month", "ff12", signal_col], kind="mergesort").reset_index(drop=True)
    df["q5"] = (
        df.groupby(["rdq_month", "ff12"], sort=False, observed=True)[signal_col]
        .transform(_qcut_safe)
    )
    df["q5"] = pd.to_numeric(df["q5"], errors="coerce").astype("Int8")
    return df


def assign_subcells(df: pd.DataFrame) -> pd.DataFrame:
    """Assign size and industry-tilt sub-cells per firm-Q.

    size large/small: monthly XS median of mcap_mil within FF12
    ind_tilt high/low: per-FF12 bucket membership (fixed mapping)
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


def compute_qspread_t(df: pd.DataFrame, car_col: str, q_long: int, q_short: int) -> tuple[float, float, int]:
    """Cell statistic = mean monthly portfolio spread (Q_long − Q_short).

    Per rdq-month: average car within Q_long and Q_short, take difference.
    Across months: mean and Newey-West t-stat (12-lag — quarterly autocorr).
    """
    sub = df.dropna(subset=[car_col, "q5"]).copy()
    sub = sub[sub["q5"].isin([q_long, q_short])]
    if sub.empty:
        return float("nan"), float("nan"), 0

    monthly = (
        sub.groupby(["rdq_month", "q5"], observed=True, sort=False)[car_col]
        .mean()
        .unstack("q5")
    )
    if q_long not in monthly.columns or q_short not in monthly.columns:
        return float("nan"), float("nan"), 0
    spread = (monthly[q_long] - monthly[q_short]).dropna()
    if len(spread) < 12:
        return float("nan"), float("nan"), int(len(spread))

    mu = float(spread.mean())
    se = newey_west_se(spread.values, lag=12)
    t = mu / se if se > 0 else float("nan")
    return mu, t, int(len(spread))


def newey_west_se(x: np.ndarray, lag: int = 12) -> float:
    n = len(x)
    if n <= 1:
        return float("nan")
    x_dm = x - x.mean()
    gamma_0 = (x_dm @ x_dm) / n
    long_run_var = gamma_0
    for k in range(1, lag + 1):
        w = 1.0 - k / (lag + 1)
        gamma_k = (x_dm[k:] @ x_dm[:-k]) / n
        long_run_var += 2.0 * w * gamma_k
    if long_run_var < 0:
        long_run_var = gamma_0
    return float(np.sqrt(long_run_var / n))


def run_bonferroni_12(df: pd.DataFrame, sign_positive: bool = True) -> pd.DataFrame:
    """3 horizons × 4 sub-cells. Strategy A: long Q1, short Q5 → spread (Q1−Q5)>0 expected.

    sign_positive=True → pass requires mu > 0 AND t > T_THRESHOLD
    """
    rows = []
    for h in HORIZONS:
        for sz in ("L", "S"):
            for it in ("H", "L"):
                sub = df[(df["size_bin"] == sz) & (df["ind_bin"] == it)]
                mu, t, n_months = compute_qspread_t(sub, f"car_{h}", q_long=1, q_short=5)
                sign_ok = (mu > 0) if sign_positive else (mu < 0)
                t_ok = (abs(t) > T_THRESHOLD) if not np.isnan(t) else False
                passed = bool(sign_ok and t_ok and (t > 0 if sign_positive else t < 0))
                rows.append({
                    "horizon_d": h,
                    "size": sz,
                    "ind_tilt": it,
                    "cell": f"A{h}-{sz}{it}",
                    "n_months": n_months,
                    "mu_spread": mu,
                    "t_stat": t,
                    "sign_correct": sign_ok,
                    "passes_bonferroni": passed,
                })
    return pd.DataFrame(rows)


def lds_axes(panel_size: int, cells: pd.DataFrame) -> dict:
    """Score 7 LDS axes for Strategy A. Each axis 0 or 1; ≥5/7 → LIVE-DEPLOYABLE."""
    pass_cells = int(cells["passes_bonferroni"].sum())
    sign_correct_cells = int(cells["sign_correct"].sum())

    axes = {
        "1_signal_well_defined": 1,
        "2_sample_size_sufficient": 1 if panel_size >= 200 * 12 else 0,
        "3_bonferroni_pass_floor": 1 if pass_cells >= 3 else 0,
        "4_sign_majority_correct": 1 if sign_correct_cells >= 7 else 0,
        "5_horizon_robustness": 1 if cells.groupby("horizon_d")["passes_bonferroni"].sum().min() >= 1 else 0,
        "6_subcell_diversity": 1 if cells.loc[cells["passes_bonferroni"], "size"].nunique() >= 2 and cells.loc[cells["passes_bonferroni"], "ind_tilt"].nunique() >= 2 else 0,
        "7_anchor_post_pub_decay_resilience": 1 if pass_cells >= 4 else 0,
    }
    total = sum(axes.values())
    if total >= 6:
        verdict = "LIVE-DEPLOYABLE-STRONG"
    elif total >= 5:
        verdict = "LIVE-DEPLOYABLE"
    elif total >= 4:
        verdict = "BORDERLINE"
    else:
        verdict = "PRACTITIONER-PAPER-ONLY"
    return {"axes": axes, "score": total, "max": 7, "verdict": verdict,
            "pass_cells": pass_cells, "sign_correct_cells": sign_correct_cells}


def main() -> int:
    print("Loading panel_with_returns ...", flush=True)
    panel = pd.read_parquet(PANEL_PATH)
    print(f"  rows: {len(panel):,}", flush=True)
    n_with_returns = panel[[f"car_{h}" for h in HORIZONS]].notna().any(axis=1).sum()
    print(f"  rows with ≥1 horizon CAR: {n_with_returns:,}", flush=True)

    print("Building monthly XS panel for gap_var_t ...", flush=True)
    df = build_monthly_xs_panel(panel, "gap_var_t")
    df = assign_subcells(df)
    print(f"  panel with q5+subcells: {len(df):,}", flush=True)

    print("Running Bonferroni-12 ...", flush=True)
    cells = run_bonferroni_12(df, sign_positive=True)
    cells_path = ART / "strategy_A_bonferroni12.csv"
    cells.to_csv(cells_path, index=False)
    print(f"Wrote {cells_path}", flush=True)

    pass_count = int(cells["passes_bonferroni"].sum())
    if pass_count >= 3:
        verdict = "PASS"
    elif pass_count == 2:
        verdict = "BORDERLINE"
    else:
        verdict = "KILL"

    lds = lds_axes(int(n_with_returns), cells)

    summary = {
        "strategy": "A - rdq-datadate gap variance XS (RD1)",
        "verdict_bonferroni_12": verdict,
        "pass_count_of_12": pass_count,
        "threshold_t": T_THRESHOLD,
        "n_panel_rows": int(len(panel)),
        "n_panel_with_returns": int(n_with_returns),
        "n_cells_pass": pass_count,
        "n_cells_borderline_floor": 2,
        "n_cells_kill_max": 1,
        "lds": lds,
        "cells_csv": str(cells_path.as_posix()),
    }
    out_json = ART / "strategy_A_bonferroni12.json"
    out_json.write_text(json.dumps(summary, indent=2, default=str))
    print(f"Wrote {out_json}", flush=True)

    print()
    print("=" * 70)
    print(f"STRATEGY A — Bonferroni-12 verdict: {verdict}")
    print(f"  pass cells: {pass_count}/12  (PASS ≥3 / BORDERLINE 2 / KILL <2)")
    print(f"  LDS: {lds['score']}/7 {lds['verdict']}")
    print("=" * 70)
    print(cells.to_string(index=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
