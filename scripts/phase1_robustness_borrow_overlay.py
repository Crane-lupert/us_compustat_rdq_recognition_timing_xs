"""Phase 1 borrow-cost overlay robustness.

The headline transaction cost in the rest of the project is a flat 20 bps/month
round-trip applied uniformly to every firm. That is conservative for execution
on the long leg but understates the realistic stock-borrow fee on the short
leg, which scales sharply with market capitalization and excludes hard-to-
borrow / penny-stock names entirely.

This script estimates how much of the headline Sharpe survives under realistic
short-side borrow conditions. It defines four overlay scenarios on top of the
flat 20 bps round-trip, applied only to firms in the Q5 (high-variance) short
basket of each cell:

  S0  Baseline (20 bps/month flat round-trip; no borrow differentiation).
      This is the headline specification used in the rest of the paper.

  S1  Add size-differentiated annualized borrow fee on the short leg:
        market cap >= $10B           -> 25 bps/yr
        $2B <= market cap < $10B     -> 50 bps/yr
        $300M <= market cap < $2B    -> 200 bps/yr
        $100M <= market cap < $300M  -> 800 bps/yr
        market cap < $100M           -> 2000 bps/yr (often uneconomic)
      Borrow drag per month = (mean borrow bps over Q5 firms in that
      month) / 12 / 10000, subtracted from the monthly Q1-Q5 spread.

  S2  S1 + drop Q5 firms with announcement-day closing price below $5
      from the short basket (penny / hard-to-borrow exclusion).

  S3  S2 + drop Q5 firms with market cap below $100M from the short
      basket (nano-cap exclusion -- many of these have no borrowable
      shares at any cost).

  S4  Aggressive realism: short leg restricted to firms with market cap
      at least $2B (mid + large cap only) and price at least $5, with
      size-differentiated borrow applied to the surviving subset.

For each (cell, scenario) the script reports the HAC-corrected annualized
Sharpe ratio on the in-sample (1999-2016) and hold-out (2017-2024) windows,
plus the fraction of Q5 short notional that survives the borrow filter.

Reads:  artifacts/panel_with_returns.parquet  (gvkey, rdq, ff12, cshoq,
                                                prccq, car_60/120/180,
                                                gap_var_t)
Writes: artifacts/strategy_A_borrow_overlay.{csv,json}
        artifacts/strategy_A_borrow_overlay_monthly.csv (monthly composite
        spread series per scenario, for figure use)
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
OUT_CSV = ART / "strategy_A_borrow_overlay.csv"
OUT_JSON = ART / "strategy_A_borrow_overlay.json"
OUT_MONTHLY = ART / "strategy_A_borrow_overlay_monthly.csv"

PRIMARY_CELLS = [
    ("A120-LH", 120, "L", "H"),
    ("A120-SH", 120, "S", "H"),
    ("A180-LH", 180, "L", "H"),
    ("A180-SL", 180, "S", "L"),
]

IS_END = pd.Timestamp("2016-12-31")
OOS_START = pd.Timestamp("2017-01-01")
OOS_END = pd.Timestamp("2024-12-31")

TC_FLAT_MONTHLY = 20 / 10_000  # 20 bps round-trip baseline (long + short legs combined)

# Annualized borrow-fee schedule in bps, by market cap (USD millions).
# Calibrated to US small-cap stock-loan conventions:
#   - Top-of-S&P 500 names typically borrow at 25 bps/yr or less
#   - Mid-cap names at 50-100 bps/yr
#   - Small-cap names at 100-500 bps/yr (median ~200 bps/yr)
#   - Micro-cap names commonly 500-2000 bps/yr when borrowable at all
#   - Nano-cap names often unborrowable; we assign a punitive 2000 bps/yr
BORROW_SCHEDULE_BPS_PER_YEAR = [
    (10_000.0, float("inf"),  25.0),
    ( 2_000.0,    10_000.0,   50.0),
    (   300.0,     2_000.0,  200.0),
    (   100.0,       300.0,  800.0),
    (     0.0,       100.0, 2000.0),
]


def borrow_bps_per_year(mcap_millions: float) -> float:
    if pd.isna(mcap_millions):
        return 2000.0  # treat missing market cap as nano-cap
    for lo, hi, bps in BORROW_SCHEDULE_BPS_PER_YEAR:
        if lo <= mcap_millions < hi:
            return bps
    return 2000.0


def build_panel_with_quintiles(panel: pd.DataFrame) -> pd.DataFrame:
    df = sab.build_monthly_xs_panel(panel, "gap_var_t")
    df = sab.assign_subcells(df)
    # market cap in millions: cshoq is in millions of shares, prccq is price
    df["mcap_mil"] = df["cshoq"] * df["prccq"]
    df["price"] = df["prccq"]
    df["borrow_bps_yr"] = df["mcap_mil"].apply(borrow_bps_per_year)
    return df


def short_filter(df: pd.DataFrame, scenario: str) -> pd.Series:
    """Return a boolean mask indicating which firms ARE allowed in the short
    basket under each scenario. Long leg (Q1) is never filtered."""
    keep = pd.Series(True, index=df.index)
    if scenario == "S0":
        return keep
    if scenario in ("S1",):
        return keep  # all firms allowed, just charge differentiated borrow
    if scenario in ("S2", "S3", "S4"):
        keep &= df["price"] >= 5.0
    if scenario in ("S3", "S4"):
        keep &= df["mcap_mil"] >= 100.0
    if scenario == "S4":
        keep &= df["mcap_mil"] >= 2000.0
    return keep


def monthly_spread_with_borrow(
    df: pd.DataFrame,
    car_col: str,
    sz: str,
    it: str,
    scenario: str,
) -> tuple[pd.Series, float, float]:
    """Compute the monthly Q1 - Q5 spread for a given (size, tilt) cell, with
    the short basket filtered per scenario and a size-differentiated borrow
    fee applied per month.

    Returns: (monthly_spread_series, mean_q5_surviving_fraction,
              mean_q5_borrow_bps_per_year).
    """
    sub = df[(df["size_bin"] == sz) & (df["ind_bin"] == it)].dropna(
        subset=[car_col, "q5", "mcap_mil"]
    ).copy()
    if sub.empty:
        return pd.Series(dtype="float64"), float("nan"), float("nan")

    # Long leg (Q1) is always all-firms (no borrow filter on long side)
    q1 = sub[sub["q5"] == 1]
    # Short leg (Q5): apply filter
    q5_all = sub[sub["q5"] == 5]
    q5_keep = q5_all[short_filter(q5_all, scenario)]

    q1_monthly = q1.groupby("rdq_month", sort=False, observed=True)[car_col].mean()
    q5_monthly = q5_keep.groupby("rdq_month", sort=False, observed=True)[car_col].mean()

    # Gross spread
    spread_gross = (q1_monthly - q5_monthly).dropna()

    # Borrow drag per month: equal-weighted across surviving Q5 firms
    if scenario == "S0":
        borrow_monthly_drag = pd.Series(0.0, index=spread_gross.index)
    else:
        # Mean borrow bps over surviving Q5 firms in that month
        borrow_per_month = q5_keep.groupby(
            "rdq_month", sort=False, observed=True
        )["borrow_bps_yr"].mean()
        # Convert annualized bps to monthly fractional drag (short side)
        borrow_monthly_drag = borrow_per_month.reindex(spread_gross.index).fillna(0) / 12.0 / 10_000.0

    # Apply flat 20 bps/month TC + size-differentiated borrow drag
    spread_net = spread_gross - TC_FLAT_MONTHLY - borrow_monthly_drag

    # Surviving Q5 fraction (used as a capacity proxy)
    q5_total_count = q5_all.groupby("rdq_month", sort=False, observed=True).size()
    q5_keep_count = q5_keep.groupby("rdq_month", sort=False, observed=True).size()
    surviving_frac = (q5_keep_count.reindex(q5_total_count.index).fillna(0) / q5_total_count).mean()

    # Mean Q5 borrow bps (over surviving names, monthly-averaged)
    if scenario == "S0":
        mean_borrow_bps = 0.0
    else:
        mean_borrow_bps = float(
            q5_keep.groupby("rdq_month", sort=False, observed=True)["borrow_bps_yr"]
            .mean()
            .mean()
        )

    return spread_net.sort_index(), float(surviving_frac), mean_borrow_bps


def annualized_sharpe_hac(monthly: pd.Series, lag: int = 12) -> float:
    m = monthly.dropna()
    if len(m) < 12:
        return float("nan")
    n = len(m)
    mu = float(m.mean())
    se = sab.newey_west_se(m.values, lag=lag)
    if se <= 0 or np.isnan(se):
        return float("nan")
    long_run_std = se * np.sqrt(n)
    return float(mu / long_run_std * np.sqrt(12))


def main() -> int:
    print(f"Loading {PANEL_PATH.name} ...", flush=True)
    panel = pd.read_parquet(PANEL_PATH)
    print(f"  rows: {len(panel):,}", flush=True)

    print("Building XS panel with quintiles + borrow tier ...", flush=True)
    df = build_panel_with_quintiles(panel)
    df_idx_ts = pd.PeriodIndex(df["rdq_month"]).to_timestamp()
    print(f"  panel with q5 + borrow tier: {len(df):,}", flush=True)

    # Borrow-tier distribution
    tier_counts = (df["borrow_bps_yr"].value_counts().sort_index()
                   .rename("count").to_frame())
    tier_counts["pct"] = (tier_counts["count"] / len(df) * 100).round(2)
    print(f"  borrow-tier distribution (annualized bps -> firm-month count):")
    print(tier_counts.to_string())
    print()

    scenarios = ["S0", "S1", "S2", "S3", "S4"]
    scenario_desc = {
        "S0": "Baseline (20 bps/mo flat, no borrow differentiation)",
        "S1": "S0 + size-differentiated borrow on short leg",
        "S2": "S1 + drop short names with price < $5",
        "S3": "S2 + drop short names with market cap < $100M",
        "S4": "Mid+large only (mcap >= $2B), price >= $5, with size borrow",
    }

    monthly_series_by_scenario_cell: dict[str, dict[str, pd.Series]] = {}
    rows = []
    for scenario in scenarios:
        cell_series_in_scenario: dict[str, pd.Series] = {}
        print(f"=== {scenario}: {scenario_desc[scenario]} ===", flush=True)
        for cell_name, horizon, sz, it in PRIMARY_CELLS:
            car_col = f"car_{horizon}"
            spread, surv_frac, mean_borrow = monthly_spread_with_borrow(
                df, car_col, sz, it, scenario
            )
            cell_series_in_scenario[cell_name] = spread

            # IS / OOS split
            ts = spread.index.to_timestamp() if hasattr(spread.index, "to_timestamp") else spread.index
            is_mask = ts <= IS_END
            oos_mask = (ts >= OOS_START) & (ts <= OOS_END)
            sharpe_is = annualized_sharpe_hac(spread[is_mask])
            sharpe_oos = annualized_sharpe_hac(spread[oos_mask])
            mu_is = float(spread[is_mask].mean()) if int(is_mask.sum()) >= 12 else float("nan")
            mu_oos = float(spread[oos_mask].mean()) if int(oos_mask.sum()) >= 12 else float("nan")
            n_is = int(is_mask.sum())
            n_oos = int(oos_mask.sum())
            rows.append({
                "scenario": scenario,
                "scenario_desc": scenario_desc[scenario],
                "cell": cell_name,
                "horizon_d": horizon,
                "n_months_is": n_is,
                "n_months_oos": n_oos,
                "mean_borrow_bps_yr": mean_borrow,
                "surviving_q5_fraction": surv_frac,
                "mu_monthly_is": mu_is,
                "mu_monthly_oos": mu_oos,
                "ann_mu_pct_is": mu_is * 12 * 100,
                "ann_mu_pct_oos": mu_oos * 12 * 100,
                "sharpe_hac_is": sharpe_is,
                "sharpe_hac_oos": sharpe_oos,
            })
            print(f"  {cell_name}: surv_frac={surv_frac:.2f}  borrow_bps={mean_borrow:>6.1f}  "
                  f"Sharpe IS={sharpe_is:>+.2f} / OOS={sharpe_oos:>+.2f}", flush=True)

        # Composite (equal-weight across 4 primary cells)
        comp = pd.concat(cell_series_in_scenario.values(), axis=1).mean(axis=1, skipna=True)
        ts_comp = comp.index.to_timestamp() if hasattr(comp.index, "to_timestamp") else comp.index
        is_mask_c = ts_comp <= IS_END
        oos_mask_c = (ts_comp >= OOS_START) & (ts_comp <= OOS_END)
        comp_sharpe_is = annualized_sharpe_hac(comp[is_mask_c])
        comp_sharpe_oos = annualized_sharpe_hac(comp[oos_mask_c])
        comp_mu_is = float(comp[is_mask_c].mean()) if int(is_mask_c.sum()) >= 12 else float("nan")
        comp_mu_oos = float(comp[oos_mask_c].mean()) if int(oos_mask_c.sum()) >= 12 else float("nan")
        rows.append({
            "scenario": scenario,
            "scenario_desc": scenario_desc[scenario],
            "cell": "COMPOSITE",
            "horizon_d": "NA",
            "n_months_is": int(is_mask_c.sum()),
            "n_months_oos": int(oos_mask_c.sum()),
            "mean_borrow_bps_yr": float("nan"),
            "surviving_q5_fraction": float("nan"),
            "mu_monthly_is": comp_mu_is,
            "mu_monthly_oos": comp_mu_oos,
            "ann_mu_pct_is": comp_mu_is * 12 * 100,
            "ann_mu_pct_oos": comp_mu_oos * 12 * 100,
            "sharpe_hac_is": comp_sharpe_is,
            "sharpe_hac_oos": comp_sharpe_oos,
        })
        print(f"  COMPOSITE (EW 4 primary): Sharpe IS={comp_sharpe_is:>+.2f} / OOS={comp_sharpe_oos:>+.2f}",
              flush=True)
        print(flush=True)

        cell_series_in_scenario["COMPOSITE"] = comp
        monthly_series_by_scenario_cell[scenario] = cell_series_in_scenario

    table = pd.DataFrame(rows)
    table.to_csv(OUT_CSV, index=False)
    print(f"Wrote {OUT_CSV.name} ({len(table)} rows)", flush=True)

    # Monthly composite series by scenario (for downstream figure / paper text)
    monthly_panel = pd.DataFrame({
        scenario: monthly_series_by_scenario_cell[scenario]["COMPOSITE"]
        for scenario in scenarios
    })
    monthly_panel.index.name = "month"
    monthly_panel.to_csv(OUT_MONTHLY)
    print(f"Wrote {OUT_MONTHLY.name} (composite spreads per scenario)", flush=True)

    # Verdict summary
    verdict = {
        "borrow_schedule_bps_per_year": [
            {"mcap_lo_millions": lo, "mcap_hi_millions": hi if hi != float("inf") else None,
             "bps_per_year": bps}
            for lo, hi, bps in BORROW_SCHEDULE_BPS_PER_YEAR
        ],
        "flat_tc_bps_per_month": int(TC_FLAT_MONTHLY * 10_000),
        "scenarios": scenario_desc,
        "composite_summary": [
            {
                "scenario": r["scenario"],
                "sharpe_hac_is": r["sharpe_hac_is"],
                "sharpe_hac_oos": r["sharpe_hac_oos"],
                "ann_mu_pct_is": r["ann_mu_pct_is"],
                "ann_mu_pct_oos": r["ann_mu_pct_oos"],
            }
            for r in rows if r["cell"] == "COMPOSITE"
        ],
        "tier_distribution_full_panel": tier_counts.reset_index().to_dict(orient="records"),
    }
    OUT_JSON.write_text(json.dumps(verdict, indent=2, default=str))
    print(f"Wrote {OUT_JSON.name}", flush=True)

    print()
    print("=" * 80)
    print("Borrow overlay verdict summary (composite of 4 primary cells)")
    print("=" * 80)
    print(f"{'Scenario':<6} {'IS Sharpe':>10} {'OOS Sharpe':>11} {'IS ann %':>10} {'OOS ann %':>10}  description")
    for r in verdict["composite_summary"]:
        scen = r["scenario"]
        print(f"{scen:<6} "
              f"{r['sharpe_hac_is']:>+10.2f} "
              f"{r['sharpe_hac_oos']:>+11.2f} "
              f"{r['ann_mu_pct_is']:>+10.2f} "
              f"{r['ann_mu_pct_oos']:>+10.2f}  "
              f"{scenario_desc[scen]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
