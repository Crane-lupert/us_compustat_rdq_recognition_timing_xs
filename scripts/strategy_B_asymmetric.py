"""Strategy B — asymmetric decomposition (post-mortem on the symmetric-recoded KILL).

The primary Strategy B test uses spread (Q5_early − Q1_late) > 0 (symmetric-recoded).
That spread is 0/12 PASS + 5/12 sign-correct. To understand WHY, we decompose:

  Leg L (late, Q1, gap_dev_t > 80th pct within FF12-month):
    Chambers-Penman 1984 prediction: car < 0 (late = hide bad news)
    Test: H1: mu_L (residual vs FF12-month mean) < 0, |t| > T_THRESHOLD

  Leg E (early, Q5, gap_dev_t < 20th pct within FF12-month):
    Chambers-Penman 1984 prediction: car > 0 (early = highlight good news)
    Test: H1: mu_E (residual vs FF12-month mean) > 0, |t| > T_THRESHOLD

By splitting the spread into its 2 legs we identify which leg drives the KILL:
- If both legs sign-wrong → mechanism fundamentally absent in modern era
- If 1 leg sign-correct + 1 leg sign-wrong → asymmetric mechanism present but
  one direction is dominated (e.g. early-leg works, late-leg doesn't)

Bonferroni threshold adjusted: 3 horizons × 4 sub-cells × 2 legs = 24 tests.
alpha = 0.05/24 = 0.00208 → |t| > 2.92 (two-tailed normal approx).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path("d:/vscode/us_compustat_rdq_recognition_timing_xs")
sys.path.insert(0, str(REPO / "scripts"))

from strategy_A_bonferroni import (  # type: ignore[import-not-found]
    HORIZONS, INDUSTRY_TILT_HIGH, _qcut_safe,
    assign_subcells, newey_west_se,
)

ART = REPO / "artifacts"
PANEL_PATH = ART / "panel_with_returns.parquet"

T_BONF_24 = 2.92


def build_quintile_panel(panel: pd.DataFrame) -> pd.DataFrame:
    df = panel.dropna(subset=["gap_dev_t", "ff12"]).copy()
    df["rdq_month"] = df["rdq"].dt.to_period("M")
    df = df.sort_values(["rdq_month", "ff12", "gap_dev_t"], kind="mergesort").reset_index(drop=True)
    df["q5"] = df.groupby(["rdq_month", "ff12"], sort=False, observed=True)["gap_dev_t"].transform(_qcut_safe)
    df["q5"] = pd.to_numeric(df["q5"], errors="coerce").astype("Int8")
    return df


def leg_test(
    df: pd.DataFrame,
    car_col: str,
    quintile: int,
    sign_direction: int,  # -1 for late-leg NEG prediction, +1 for early-leg POS prediction
) -> tuple[float, float, int]:
    """Mean residual return for firm-Q in `quintile` minus that month's FF12 mean.

    Returns (mu, t_stat, n_months).
    Sign-check: PASS if sign(mu) == sign_direction AND |t| > T_BONF_24.
    """
    sub = df.dropna(subset=[car_col, "q5"]).copy()
    sub = sub[sub["q5"] == quintile]
    if sub.empty:
        return float("nan"), float("nan"), 0

    monthly_sector_mean = (
        df.dropna(subset=[car_col])
        .groupby(["rdq_month", "ff12"], observed=True, sort=False)[car_col]
        .transform("mean")
    )
    sub = sub.assign(month_sector_mean=monthly_sector_mean.loc[sub.index])
    sub["residual"] = sub[car_col] - sub["month_sector_mean"]

    monthly_resid = sub.groupby(["rdq_month", "ff12"], observed=True, sort=False)["residual"].mean()
    # Across (month, sector) → equal-weight average per month
    monthly = monthly_resid.groupby(level="rdq_month").mean().dropna()
    if len(monthly) < 12:
        return float("nan"), float("nan"), int(len(monthly))

    mu = float(monthly.mean())
    se = newey_west_se(monthly.values, lag=12)
    t = mu / se if se > 0 else float("nan")
    return mu, t, int(len(monthly))


def run_24_cell_decomposition(df: pd.DataFrame) -> pd.DataFrame:
    """3 horizons × 4 sub-cells × 2 legs = 24 cells. Each leg is a separate t-test."""
    rows = []
    for h in HORIZONS:
        for sz in ("L", "S"):
            for it in ("H", "L"):
                sub = df[(df["size_bin"] == sz) & (df["ind_bin"] == it)]
                # Late leg (Q1, gap_dev_t high → late) — NEG prediction
                mu_l, t_l, n_l = leg_test(sub, f"car_{h}", quintile=1, sign_direction=-1)
                sign_l = (mu_l < 0) if not np.isnan(mu_l) else False
                pass_l = bool(sign_l and abs(t_l) > T_BONF_24 and t_l < 0)
                rows.append({
                    "horizon_d": h, "size": sz, "ind_tilt": it, "leg": "Late(Q1)",
                    "cell": f"B{h}-{sz}{it}-L", "n_months": n_l,
                    "mu_resid": mu_l, "t_stat": t_l,
                    "sign_correct": sign_l, "passes_bonf24": pass_l,
                })
                # Early leg (Q5, gap_dev_t low → early) — POS prediction
                mu_e, t_e, n_e = leg_test(sub, f"car_{h}", quintile=5, sign_direction=+1)
                sign_e = (mu_e > 0) if not np.isnan(mu_e) else False
                pass_e = bool(sign_e and abs(t_e) > T_BONF_24 and t_e > 0)
                rows.append({
                    "horizon_d": h, "size": sz, "ind_tilt": it, "leg": "Early(Q5)",
                    "cell": f"B{h}-{sz}{it}-E", "n_months": n_e,
                    "mu_resid": mu_e, "t_stat": t_e,
                    "sign_correct": sign_e, "passes_bonf24": pass_e,
                })
    return pd.DataFrame(rows)


def main() -> int:
    print("Loading panel_with_returns ...", flush=True)
    panel = pd.read_parquet(PANEL_PATH)
    print(f"  rows: {len(panel):,}", flush=True)

    df = build_quintile_panel(panel)
    df = assign_subcells(df)
    print(f"  panel with q5+subcells: {len(df):,}", flush=True)

    print("Running 24-cell asymmetric decomposition ...", flush=True)
    cells = run_24_cell_decomposition(df)
    out_csv = ART / "strategy_B_asymmetric_24cells.csv"
    cells.to_csv(out_csv, index=False)
    print(f"Wrote {out_csv}", flush=True)

    n_pass = int(cells["passes_bonf24"].sum())
    n_sign = int(cells["sign_correct"].sum())
    late_sub = cells[cells["leg"] == "Late(Q1)"]
    early_sub = cells[cells["leg"] == "Early(Q5)"]

    summary = {
        "strategy": "B asymmetric decomposition (24 cells = 3 horizons * 4 sub-cells * 2 legs)",
        "bonferroni_threshold_t": T_BONF_24,
        "pass_count_of_24": n_pass,
        "sign_correct_count_of_24": n_sign,
        "late_leg_pass": int(late_sub["passes_bonf24"].sum()),
        "late_leg_sign_correct": int(late_sub["sign_correct"].sum()),
        "late_leg_mean_t": float(late_sub["t_stat"].mean()),
        "early_leg_pass": int(early_sub["passes_bonf24"].sum()),
        "early_leg_sign_correct": int(early_sub["sign_correct"].sum()),
        "early_leg_mean_t": float(early_sub["t_stat"].mean()),
    }
    if n_pass >= 5:
        summary["verdict"] = "PARTIAL-RECOVERY (≥5/24 PASS)"
    elif n_sign >= 16:
        summary["verdict"] = "SIGN-CORRECT-BUT-WEAK (≥16/24 sign-correct, asymmetric mechanism plausible)"
    else:
        summary["verdict"] = "DEAD-CONFIRMED (no leg recovery)"

    out_json = ART / "strategy_B_asymmetric_24cells.json"
    out_json.write_text(json.dumps(summary, indent=2))
    print(f"Wrote {out_json}", flush=True)

    print()
    print("=" * 70)
    print(f"STRATEGY B asymmetric decomposition")
    print(f"  pass cells: {n_pass}/24 (Bonferroni-24 |t|>{T_BONF_24})")
    print(f"  sign-correct: {n_sign}/24")
    print(f"  Late(Q1) leg pass: {summary['late_leg_pass']}/12  sign: {summary['late_leg_sign_correct']}/12  mean t: {summary['late_leg_mean_t']:.2f}")
    print(f"  Early(Q5) leg pass: {summary['early_leg_pass']}/12  sign: {summary['early_leg_sign_correct']}/12  mean t: {summary['early_leg_mean_t']:.2f}")
    print(f"  verdict: {summary['verdict']}")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    sys.exit(main())
