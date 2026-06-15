"""Strategy A robustness — sub-period stability + FF12 sector concentration.

For each of the 4 PASS cells (A120-LH, A120-SH, A180-LH, A180-SL):
  (a) Sub-period t-stat decomposition: 1999-2007 / 2008-2016 / 2017-2024
  (b) FF12 sector concentration: per-FF12 contribution to mean spread

This addresses LDS axis 5 (horizon robustness) — note: horizon robustness is about
horizons, not sub-periods. Sub-period is an auxiliary regime stability check.

Sector concentration: a PASS cell with >50% of spread from a single FF12 sector
indicates concentration risk (paper-practical caveat).
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
    HORIZONS, T_THRESHOLD, INDUSTRY_TILT_HIGH,
    build_monthly_xs_panel, assign_subcells,
    newey_west_se,
)

ART = REPO / "artifacts"
PANEL_PATH = ART / "panel_with_returns.parquet"

PASS_CELLS = [
    {"horizon": 120, "size": "L", "ind_tilt": "H", "cell": "A120-LH"},
    {"horizon": 120, "size": "S", "ind_tilt": "H", "cell": "A120-SH"},
    {"horizon": 180, "size": "L", "ind_tilt": "H", "cell": "A180-LH"},
    {"horizon": 180, "size": "S", "ind_tilt": "L", "cell": "A180-SL"},
]

SUB_PERIODS = [
    ("1999-2007", pd.Timestamp("1999-01-01"), pd.Timestamp("2007-12-31")),
    ("2008-2016", pd.Timestamp("2008-01-01"), pd.Timestamp("2016-12-31")),
    ("2017-2024", pd.Timestamp("2017-01-01"), pd.Timestamp("2024-12-31")),
]


def monthly_spread_series(df: pd.DataFrame, car_col: str) -> pd.Series:
    """Per-rdq-month Q1 − Q5 spread on the slice in df."""
    sub = df.dropna(subset=[car_col, "q5"]).copy()
    sub = sub[sub["q5"].isin([1, 5])]
    if sub.empty:
        return pd.Series(dtype="float64")
    monthly = (
        sub.groupby(["rdq_month", "q5"], observed=True, sort=False)[car_col]
        .mean().unstack("q5")
    )
    if 1 not in monthly.columns or 5 not in monthly.columns:
        return pd.Series(dtype="float64")
    spread = (monthly[1] - monthly[5]).dropna()
    return spread


def per_ff12_contribution(df: pd.DataFrame, car_col: str) -> pd.DataFrame:
    """For each FF12 sector: monthly Q1-Q5 spread restricted to that sector."""
    rows = []
    for sec in sorted(df["ff12"].dropna().unique()):
        sub = df[df["ff12"] == sec]
        spread = monthly_spread_series(sub, car_col)
        if len(spread) < 12:
            continue
        mu = float(spread.mean())
        se = newey_west_se(spread.values, lag=12)
        t = mu / se if se > 0 else float("nan")
        rows.append({"ff12": int(sec), "n_months": int(len(spread)),
                     "mu_spread": mu, "t_stat": t})
    return pd.DataFrame(rows)


def main() -> int:
    print("Loading panel_with_returns ...", flush=True)
    panel = pd.read_parquet(PANEL_PATH)
    df = build_monthly_xs_panel(panel, "gap_var_t")
    df = assign_subcells(df)
    print(f"  panel with q5+subcells: {len(df):,}", flush=True)

    regime_rows = []
    sector_rows = []

    for spec in PASS_CELLS:
        cell = spec["cell"]
        h = spec["horizon"]
        sz = spec["size"]
        it = spec["ind_tilt"]
        car_col = f"car_{h}"
        slice_df = df[(df["size_bin"] == sz) & (df["ind_bin"] == it)]
        spread = monthly_spread_series(slice_df, car_col)
        full_mu = float(spread.mean()) if len(spread) else float("nan")
        full_t = full_mu / newey_west_se(spread.values, lag=12) if len(spread) > 12 else float("nan")

        # Sub-period regime stability
        for name, start, end in SUB_PERIODS:
            spread_p = spread[
                (spread.index.to_timestamp() >= start) & (spread.index.to_timestamp() <= end)
            ]
            if len(spread_p) < 12:
                regime_rows.append({
                    "cell": cell, "regime": name,
                    "n_months": int(len(spread_p)),
                    "mu_spread": float("nan"), "t_stat": float("nan"),
                    "passes_local_bonf12": False,
                })
                continue
            mu_p = float(spread_p.mean())
            se_p = newey_west_se(spread_p.values, lag=12)
            t_p = mu_p / se_p if se_p > 0 else float("nan")
            regime_rows.append({
                "cell": cell, "regime": name,
                "n_months": int(len(spread_p)),
                "mu_spread": mu_p, "t_stat": t_p,
                "passes_local_bonf12": bool(mu_p > 0 and t_p > T_THRESHOLD),
            })

        # Sector concentration
        sector_contrib = per_ff12_contribution(slice_df, car_col)
        sector_contrib.insert(0, "cell", cell)
        sector_contrib["share_of_full_mu_pct"] = (
            sector_contrib["mu_spread"] / full_mu * 100 if full_mu else float("nan")
        ).round(2)
        sector_rows.append(sector_contrib)

    regime_df = pd.DataFrame(regime_rows)
    regime_df.to_csv(ART / "strategy_A_regime_stability.csv", index=False)
    print(f"Wrote strategy_A_regime_stability.csv ({len(regime_df)} rows)", flush=True)

    sector_df = pd.concat(sector_rows, ignore_index=True)
    sector_df.to_csv(ART / "strategy_A_sector_concentration.csv", index=False)
    print(f"Wrote strategy_A_sector_concentration.csv ({len(sector_df)} rows)", flush=True)

    # Sector concentration risk per cell
    summary = {"cells": {}}
    for cell in [s["cell"] for s in PASS_CELLS]:
        sub = sector_df[sector_df["cell"] == cell]
        max_share = float(sub["share_of_full_mu_pct"].abs().max())
        # Cells with positive mu — share of total contribution by top-1 sector
        n_pos_sectors = int((sub["mu_spread"] > 0).sum())
        n_neg_sectors = int((sub["mu_spread"] < 0).sum())
        summary["cells"][cell] = {
            "max_abs_sector_share_pct": max_share,
            "n_sectors_pos": n_pos_sectors,
            "n_sectors_neg": n_neg_sectors,
            "concentration_risk": "HIGH" if max_share > 50 else "MODERATE" if max_share > 30 else "LOW",
        }

    # Regime stability per cell
    summary["regime"] = {}
    for cell in [s["cell"] for s in PASS_CELLS]:
        sub = regime_df[regime_df["cell"] == cell]
        passes = int(sub["passes_local_bonf12"].sum())
        summary["regime"][cell] = {
            "passes_local_bonf12": passes,
            "regime_stability": "STRONG" if passes >= 2 else "MODERATE" if passes == 1 else "WEAK",
        }

    out_json = ART / "strategy_A_robustness.json"
    out_json.write_text(json.dumps(summary, indent=2, default=str))
    print(f"Wrote {out_json}", flush=True)

    print()
    print("=" * 70)
    print("Sub-period regime stability:")
    print(regime_df.to_string(index=False))
    print()
    print("=" * 70)
    print("Sector concentration:")
    print(sector_df.to_string(index=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
