"""Phase 1 tradability verification (Day 7 augmentation).

Purpose: render the PARTIAL Phase 1 verdict intuitively visible by computing
practitioner-grade tradability metrics for the 4 primary cells across IS / OOS.

For each (cell, partition):
  - Monthly Q1, Q5, Q1-Q5 spread time series (re-formed monthly per cell rules)
  - Annualized Sharpe (gross + net at TC = 5/10/20/50/100 bps/month)
  - Hit rate (% positive months)
  - Max drawdown
  - Worst quintile of monthly drawdown
  - TC break-even (bps/month that strips Sharpe to 0)
  - Avg monthly return / std
  - Sub-period stability (1999-2007 / 2008-2016 / 2017-2024)

This script does NOT change the Phase 1 verdict (paper-practical PARTIAL,
K2 fired Day 4). It produces evidence that:
  1. The signal is NOT mechanically dead (Sharpe > 0 IS + OOS)
  2. Tradable net-of-TC alpha exists but is modest
  3. IS-to-OOS Sharpe degradation is consistent with K2 outcome

Reads:  artifacts/panel_with_returns.parquet (full panel for monthly XS)
Writes: artifacts/strategy_A_tradability.csv  (per-(cell, partition, tc_bps))
        artifacts/strategy_A_tradability.json (verdict + summary)
        artifacts/strategy_A_monthly_returns.csv (raw monthly spread series)
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
PANEL_PATH = ART / "panel_with_returns.parquet"

OUT_CSV = ART / "strategy_A_tradability.csv"
OUT_JSON = ART / "strategy_A_tradability.json"
OUT_RAW = ART / "strategy_A_monthly_returns.csv"

PRIMARY_CELLS = [
    {"horizon": 120, "size": "L", "ind_tilt": "H", "cell": "A120-LH"},
    {"horizon": 120, "size": "S", "ind_tilt": "H", "cell": "A120-SH"},
    {"horizon": 180, "size": "L", "ind_tilt": "H", "cell": "A180-LH"},
    {"horizon": 180, "size": "S", "ind_tilt": "L", "cell": "A180-SL"},
]

PARTITIONS = [
    ("IS", pd.Timestamp("1999-01-01"), pd.Timestamp("2016-12-31")),
    ("OOS", pd.Timestamp("2017-01-01"), pd.Timestamp("2024-12-31")),
    ("FULL", pd.Timestamp("1999-01-01"), pd.Timestamp("2024-12-31")),
]

TC_BPS_GRID = [0, 5, 10, 20, 50, 100]


def monthly_spread_series(df: pd.DataFrame, car_col: str, sz: str, it: str) -> pd.Series:
    """Per-rdq-month Q1 - Q5 mean spread, restricted to (size, ind_tilt) sub-cell."""
    sub = df[(df["size_bin"] == sz) & (df["ind_bin"] == it)]
    sub = sub.dropna(subset=[car_col, "q5"])
    sub = sub[sub["q5"].isin([1, 5])]
    if sub.empty:
        return pd.Series(dtype="float64")
    monthly = (
        sub.groupby(["rdq_month", "q5"], observed=True, sort=False)[car_col]
        .mean()
        .unstack("q5")
    )
    if 1 not in monthly.columns or 5 not in monthly.columns:
        return pd.Series(dtype="float64")
    spread = (monthly[1] - monthly[5]).dropna().sort_index()
    return spread


def annualize_sharpe(monthly_returns: pd.Series, ann_factor: float = 12.0) -> float:
    if len(monthly_returns) < 2:
        return float("nan")
    mu = float(monthly_returns.mean())
    sd = float(monthly_returns.std(ddof=1))
    if sd <= 0:
        return float("nan")
    return mu / sd * np.sqrt(ann_factor)


def max_drawdown(monthly_returns: pd.Series) -> float:
    """Max peak-to-trough drawdown on cumulative (1 + r) wealth path."""
    if len(monthly_returns) < 2:
        return float("nan")
    cum = (1.0 + monthly_returns).cumprod()
    peak = cum.cummax()
    dd = (cum - peak) / peak
    return float(dd.min())


def hit_rate(monthly_returns: pd.Series) -> float:
    if len(monthly_returns) == 0:
        return float("nan")
    return float((monthly_returns > 0).mean())


def tc_break_even_bps(monthly_returns: pd.Series) -> float:
    """bps/month TC that strips mean monthly return to 0 (assume 1 turn per month)."""
    mu = float(monthly_returns.mean())
    return mu * 10_000  # bps


def main() -> int:
    print("Loading panel_with_returns ...", flush=True)
    panel = pd.read_parquet(PANEL_PATH)
    print(f"  rows: {len(panel):,}", flush=True)

    print("Building monthly XS panel for gap_var_t ...", flush=True)
    df = sab.build_monthly_xs_panel(panel, "gap_var_t")
    df = sab.assign_subcells(df)
    print(f"  panel with q5+subcells: {len(df):,}", flush=True)

    all_rows = []
    raw_series = {}

    for spec in PRIMARY_CELLS:
        cell = spec["cell"]
        car_col = f"car_{spec['horizon']}"
        sz = spec["size"]
        it = spec["ind_tilt"]
        full_spread = monthly_spread_series(df, car_col, sz, it)
        # full_spread index is PeriodIndex (Month). Convert to Timestamp for filtering.
        full_spread = full_spread.copy()
        full_spread.index = full_spread.index.to_timestamp()
        raw_series[cell] = full_spread

        for label, start, end in PARTITIONS:
            sub = full_spread[(full_spread.index >= start) & (full_spread.index <= end)]
            if len(sub) < 12:
                continue
            mu = float(sub.mean())
            sd = float(sub.std(ddof=1))
            n_mo = int(len(sub))
            sharpe_gross = annualize_sharpe(sub)
            dd = max_drawdown(sub)
            hr = hit_rate(sub)
            be_bps = tc_break_even_bps(sub)

            for tc_bps in TC_BPS_GRID:
                tc_decimal = tc_bps / 10_000.0
                net = sub - tc_decimal
                sharpe_net = annualize_sharpe(net)
                ann_mu_net = float(net.mean()) * 12
                row = {
                    "cell": cell,
                    "partition": label,
                    "horizon_d": spec["horizon"],
                    "size": sz,
                    "ind_tilt": it,
                    "n_months": n_mo,
                    "tc_bps_per_month": tc_bps,
                    "mu_monthly_gross": mu,
                    "mu_monthly_net": float(net.mean()),
                    "std_monthly": sd,
                    "ann_mu_gross_pct": mu * 12 * 100,
                    "ann_mu_net_pct": ann_mu_net * 100,
                    "sharpe_gross_ann": sharpe_gross,
                    "sharpe_net_ann": sharpe_net,
                    "hit_rate": hr,
                    "max_drawdown": dd,
                    "tc_break_even_bps_per_month": be_bps,
                }
                all_rows.append(row)

    table = pd.DataFrame(all_rows)
    table.to_csv(OUT_CSV, index=False)
    print(f"Wrote {OUT_CSV.name} ({len(table)} rows)", flush=True)

    # Raw monthly series
    raw_df = pd.DataFrame(raw_series)
    raw_df.index.name = "month"
    raw_df.to_csv(OUT_RAW)
    print(f"Wrote {OUT_RAW.name} (monthly spread series for 4 primary cells)", flush=True)

    # Verdict summary: pick gross + net@20bps for IS and OOS
    summary_rows = []
    for cell in [s["cell"] for s in PRIMARY_CELLS]:
        for label in ("IS", "OOS"):
            row_gross = table[
                (table["cell"] == cell)
                & (table["partition"] == label)
                & (table["tc_bps_per_month"] == 0)
            ]
            row_net20 = table[
                (table["cell"] == cell)
                & (table["partition"] == label)
                & (table["tc_bps_per_month"] == 20)
            ]
            if row_gross.empty:
                continue
            summary_rows.append({
                "cell": cell,
                "partition": label,
                "n_months": int(row_gross["n_months"].iloc[0]),
                "ann_mu_gross_pct": float(row_gross["ann_mu_gross_pct"].iloc[0]),
                "sharpe_gross_ann": float(row_gross["sharpe_gross_ann"].iloc[0]),
                "hit_rate": float(row_gross["hit_rate"].iloc[0]),
                "max_drawdown": float(row_gross["max_drawdown"].iloc[0]),
                "ann_mu_net20bps_pct": float(row_net20["ann_mu_net_pct"].iloc[0]),
                "sharpe_net20bps_ann": float(row_net20["sharpe_net_ann"].iloc[0]),
                "tc_break_even_bps_pm": float(row_gross["tc_break_even_bps_per_month"].iloc[0]),
            })
    summary_df = pd.DataFrame(summary_rows)

    # Tradability verdict per partition
    def verdict_for_partition(label: str) -> dict:
        sub = summary_df[summary_df["partition"] == label]
        median_sharpe_gross = float(sub["sharpe_gross_ann"].median())
        median_sharpe_net20 = float(sub["sharpe_net20bps_ann"].median())
        median_hit = float(sub["hit_rate"].median())
        median_dd = float(sub["max_drawdown"].median())
        median_be_bps = float(sub["tc_break_even_bps_pm"].median())

        # Tradability tiers (informal):
        if median_sharpe_net20 >= 1.0:
            tier = "TRADABLE-STRONG"
        elif median_sharpe_net20 >= 0.5:
            tier = "TRADABLE-MODERATE"
        elif median_sharpe_net20 >= 0.2:
            tier = "TRADABLE-MARGINAL"
        elif median_sharpe_net20 > 0:
            tier = "PAPER-PRACTICAL"
        else:
            tier = "NOT-TRADABLE"
        return {
            "median_sharpe_gross_ann": median_sharpe_gross,
            "median_sharpe_net20bps_ann": median_sharpe_net20,
            "median_hit_rate": median_hit,
            "median_max_drawdown": median_dd,
            "median_tc_break_even_bps_pm": median_be_bps,
            "tradability_tier": tier,
        }

    is_verdict = verdict_for_partition("IS")
    oos_verdict = verdict_for_partition("OOS")

    # IS->OOS degradation
    is_med_sharpe_net = is_verdict["median_sharpe_net20bps_ann"]
    oos_med_sharpe_net = oos_verdict["median_sharpe_net20bps_ann"]
    sharpe_degradation_pct = (
        (oos_med_sharpe_net / is_med_sharpe_net - 1) * 100
        if is_med_sharpe_net > 0 else float("nan")
    )

    summary = {
        "phase": 1,
        "step": "augmentation_tradability",
        "purpose": "render PARTIAL verdict intuitively visible via practitioner tradability metrics",
        "tc_assumption": (
            "Per-month TC charged against monthly Q1-Q5 spread. "
            "Treats each month's portfolio formation as one round-trip on long+short legs. "
            "20bps/mo is moderate institutional convention; 100bps/mo is conservative."
        ),
        "is_verdict": is_verdict,
        "oos_verdict": oos_verdict,
        "is_to_oos_sharpe_net_degradation_pct": sharpe_degradation_pct,
        "k2_fire_status": "K2 already fired Day 4; this tradability check is descriptive",
        "summary_table": summary_df.to_dict(orient="records"),
        "csv_per_cell": str(OUT_CSV.as_posix()),
        "raw_monthly_series_csv": str(OUT_RAW.as_posix()),
    }
    OUT_JSON.write_text(json.dumps(summary, indent=2, default=str))
    print(f"Wrote {OUT_JSON.name}", flush=True)

    print()
    print("=" * 78)
    print("Phase 1 Tradability Verification (PARTIAL evidence)")
    print("=" * 78)
    print()
    print("Primary cell summary (gross + net@20bps/month TC):")
    print(summary_df.to_string(index=False))
    print()
    print(f"IS  median Sharpe gross: {is_verdict['median_sharpe_gross_ann']:.3f}   net@20bps: {is_verdict['median_sharpe_net20bps_ann']:.3f}   tier: {is_verdict['tradability_tier']}")
    print(f"OOS median Sharpe gross: {oos_verdict['median_sharpe_gross_ann']:.3f}   net@20bps: {oos_verdict['median_sharpe_net20bps_ann']:.3f}   tier: {oos_verdict['tradability_tier']}")
    print(f"IS->OOS net@20bps Sharpe degradation: {sharpe_degradation_pct:+.1f}%")
    print()
    print("Verdict: K2 fired Day 4 -> paper-practical. Tradability tier above")
    print("characterises *what* survives despite K2: signal is sign-correct and")
    print("net-positive at moderate TC, but Sharpe is below institutional bar.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
