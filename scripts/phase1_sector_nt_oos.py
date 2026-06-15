"""Phase 1 STEP 5 (Day 5) -- Sector concentration + WITH-NT sensitivity on OOS.

Reads:  artifacts/panel_oos.parquet                (WITHOUT-NT OOS, from Day 1 split)
        artifacts/panel_with_returns_full.parquet  (WITH-NT full panel, filter to OOS)
Writes: artifacts/strategy_A_sector_oos.csv
        artifacts/strategy_A_sector_oos.json       (per-FF12 + Lock D §5 verdict)
        artifacts/strategy_A_with_nt_oos.csv
        artifacts/strategy_A_with_nt_oos.json      (K4 ratio + verdict)

Day 5 is moot for the binding Phase 1 LAYER A LOCK verdict (K2 already
fired on Day 4 -- paper-practical-only). These artifacts serve as Day 6
paper §4 (sector robustness) and §5 (NT mechanical-confound) anchors.

Per Lock D §5 sector conditions (for paper completeness reporting):
  - High-tilt cells (A120-LH, A120-SH, A180-LH): BusEq (ff12=6) and Hlth (ff12=10)
    must both show OOS sign-correct positive mu_spread.
  - Low-tilt cell A180-SL: >=6 of 9 low-tilt sectors must show OOS sign-correct
    positive mu_spread.

Per Phase 1 entry §4 K4 (for paper §5 commentary):
  WITH-NT OOS pass count > 2x WITHOUT-NT OOS pass count -> mechanical NT
  confound suspected.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path("d:/vscode/us_compustat_rdq_recognition_timing_xs")
sys.path.insert(0, str(ROOT / "scripts"))

import strategy_A_bonferroni as sab  # type: ignore  # noqa: E402
import strategy_A_robustness as sar  # type: ignore  # noqa: E402

ART = ROOT / "artifacts"

PANEL_OOS_NOEXCL = ART / "panel_oos.parquet"
PANEL_FULL_WITH_NT = ART / "panel_with_returns_full.parquet"

OOS_START = pd.Timestamp("2017-01-01")
OOS_END = pd.Timestamp("2024-12-31")

PRIMARY_CELLS = [
    {"horizon": 120, "size": "L", "ind_tilt": "H", "cell": "A120-LH"},
    {"horizon": 120, "size": "S", "ind_tilt": "H", "cell": "A120-SH"},
    {"horizon": 180, "size": "L", "ind_tilt": "H", "cell": "A180-LH"},
    {"horizon": 180, "size": "S", "ind_tilt": "L", "cell": "A180-SL"},
]

FF12_BUSEQ = 6
FF12_HLTH = 10
FF12_LOW_TILT_SECTORS = {1, 2, 3, 4, 5, 7, 8, 9, 12}  # NoDur, Durbl, Manuf, Enrgy, Chems, Telcm, Utils, Shops, Other


def sector_robustness_oos(panel: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    df = sab.build_monthly_xs_panel(panel, "gap_var_t")
    df = sab.assign_subcells(df)

    rows = []
    for spec in PRIMARY_CELLS:
        cell = spec["cell"]
        h = spec["horizon"]
        sz = spec["size"]
        it = spec["ind_tilt"]
        car_col = f"car_{h}"
        slice_df = df[(df["size_bin"] == sz) & (df["ind_bin"] == it)]
        sector_contrib = sar.per_ff12_contribution(slice_df, car_col)
        sector_contrib.insert(0, "cell", cell)
        rows.append(sector_contrib)
    out = pd.concat(rows, ignore_index=True)

    # Lock D §5 verdict per cell
    lockd_results = {}
    for spec in PRIMARY_CELLS:
        cell = spec["cell"]
        is_low_tilt = spec["ind_tilt"] == "L"
        cell_sectors = out[out["cell"] == cell]
        if is_low_tilt:
            n_low_tilt_pos = int(
                ((cell_sectors["ff12"].isin(FF12_LOW_TILT_SECTORS))
                 & (cell_sectors["mu_spread"] > 0)).sum()
            )
            n_low_tilt_present = int(
                cell_sectors["ff12"].isin(FF12_LOW_TILT_SECTORS).sum()
            )
            criterion = ">=6 of 9 low-tilt sectors sign-correct positive"
            passes = n_low_tilt_pos >= 6
            detail = {
                "criterion": criterion,
                "n_low_tilt_pos": n_low_tilt_pos,
                "n_low_tilt_present": n_low_tilt_present,
                "passes_lock_d_5": passes,
            }
        else:
            row_buseq = cell_sectors[cell_sectors["ff12"] == FF12_BUSEQ]
            row_hlth = cell_sectors[cell_sectors["ff12"] == FF12_HLTH]
            buseq_mu = float(row_buseq["mu_spread"].iloc[0]) if not row_buseq.empty else float("nan")
            hlth_mu = float(row_hlth["mu_spread"].iloc[0]) if not row_hlth.empty else float("nan")
            buseq_pos = buseq_mu > 0 if not row_buseq.empty else False
            hlth_pos = hlth_mu > 0 if not row_hlth.empty else False
            criterion = "BusEq AND Hlth both sign-correct positive"
            passes = bool(buseq_pos and hlth_pos)
            detail = {
                "criterion": criterion,
                "buseq_mu_spread": buseq_mu,
                "buseq_pos": buseq_pos,
                "hlth_mu_spread": hlth_mu,
                "hlth_pos": hlth_pos,
                "passes_lock_d_5": passes,
            }
        lockd_results[cell] = detail

    return out, lockd_results


def with_nt_oos_bonferroni(panel_full: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """Filter full WITH-NT panel to OOS dates and run Bonferroni-12."""
    oos_mask = (panel_full["rdq"] >= OOS_START) & (panel_full["rdq"] <= OOS_END)
    panel_with_nt_oos = panel_full.loc[oos_mask].copy()
    df = sab.build_monthly_xs_panel(panel_with_nt_oos, "gap_var_t")
    df = sab.assign_subcells(df)
    cells = sab.run_bonferroni_12(df, sign_positive=True)
    pass_count = int(cells["passes_bonferroni"].sum())
    return cells, pass_count, int(len(panel_with_nt_oos))


def main() -> int:
    print("=" * 70)
    print("Day 5 (a) -- Sector concentration on OOS (WITHOUT-NT, paper anchor)")
    print("=" * 70)
    panel_oos_noexcl = pd.read_parquet(PANEL_OOS_NOEXCL)
    print(f"  OOS WITHOUT-NT rows: {len(panel_oos_noexcl):,}", flush=True)
    sector_df, lockd_results = sector_robustness_oos(panel_oos_noexcl)
    sector_csv = ART / "strategy_A_sector_oos.csv"
    sector_df.to_csv(sector_csv, index=False)
    print(f"Wrote {sector_csv.name} ({len(sector_df)} rows)", flush=True)

    sector_summary = {
        "phase": 1,
        "step": 5,
        "day": 5,
        "axis": "(a) sector concentration on OOS (paper anchor; K3 moot since K2 fired)",
        "lock_d_section_5_per_cell": lockd_results,
        "sector_csv": str(sector_csv.as_posix()),
    }
    sector_json = ART / "strategy_A_sector_oos.json"
    sector_json.write_text(json.dumps(sector_summary, indent=2, default=str))
    print(f"Wrote {sector_json.name}", flush=True)

    print()
    for cell, detail in lockd_results.items():
        print(f"  {cell}: {'PASS' if detail['passes_lock_d_5'] else 'FAIL'} -- {detail['criterion']}")
        if detail.get("buseq_pos") is not None:
            print(f"    BusEq mu = {detail['buseq_mu_spread']:+.4f} ({'+' if detail['buseq_pos'] else '-'})")
            print(f"    Hlth  mu = {detail['hlth_mu_spread']:+.4f} ({'+' if detail['hlth_pos'] else '-'})")
        else:
            print(f"    {detail['n_low_tilt_pos']}/{detail['n_low_tilt_present']} low-tilt sectors positive")

    print()
    print("=" * 70)
    print("Day 5 (b) -- WITH-NT vs WITHOUT-NT on OOS (paper anchor; K4 moot)")
    print("=" * 70)
    panel_full = pd.read_parquet(PANEL_FULL_WITH_NT)
    print(f"  full panel rows: {len(panel_full):,}", flush=True)
    cells_with_nt_oos, pass_with_nt_oos, n_with_nt_oos = with_nt_oos_bonferroni(panel_full)
    nt_csv = ART / "strategy_A_with_nt_oos.csv"
    cells_with_nt_oos.to_csv(nt_csv, index=False)
    print(f"  WITH-NT OOS rows: {n_with_nt_oos:,}  PASS: {pass_with_nt_oos}/12", flush=True)
    print(f"Wrote {nt_csv.name}", flush=True)

    # Load WITHOUT-NT OOS results from Day 4 (artifacts/strategy_A_bonferroni12_oos.csv)
    cells_without_nt_oos = pd.read_csv(ART / "strategy_A_bonferroni12_oos.csv")
    pass_without_nt_oos = int(cells_without_nt_oos["passes_bonferroni"].sum())
    primary = {"A120-LH", "A120-SH", "A180-LH", "A180-SL"}
    primary_pass_without_nt = int(
        ((cells_without_nt_oos["cell"].isin(primary))
         & cells_without_nt_oos["passes_bonferroni"]).sum()
    )
    primary_pass_with_nt = int(
        ((cells_with_nt_oos["cell"].isin(primary))
         & cells_with_nt_oos["passes_bonferroni"]).sum()
    )

    # K4 ratio
    denom = max(pass_without_nt_oos, 1)
    inflation_ratio = pass_with_nt_oos / denom
    if pass_without_nt_oos == 0 and pass_with_nt_oos == 0:
        k4_verdict = "MOOT -- no PASS cells in either to compare"
    elif inflation_ratio > 2.0 and pass_with_nt_oos >= 2:
        k4_verdict = "K4_FLAG -- WITH-NT > 2x WITHOUT-NT"
    else:
        k4_verdict = "K4_NOT_TRIGGERED"

    nt_summary = {
        "phase": 1,
        "step": 5,
        "day": 5,
        "axis": "(b) WITH-NT vs WITHOUT-NT on OOS (paper anchor; K4 moot since K2 fired)",
        "without_nt_oos_pass_count_12": pass_without_nt_oos,
        "without_nt_oos_primary_pass_4": primary_pass_without_nt,
        "with_nt_oos_pass_count_12": pass_with_nt_oos,
        "with_nt_oos_primary_pass_4": primary_pass_with_nt,
        "with_nt_oos_rows": n_with_nt_oos,
        "inflation_ratio_with_nt_to_without": round(inflation_ratio, 3),
        "k4_threshold": "> 2.0 -> K4_FLAG",
        "k4_verdict": k4_verdict,
        "cells_with_nt_oos_csv": str(nt_csv.as_posix()),
        "cells_with_nt_oos": cells_with_nt_oos.to_dict(orient="records"),
    }
    nt_json = ART / "strategy_A_with_nt_oos.json"
    nt_json.write_text(json.dumps(nt_summary, indent=2, default=str))
    print(f"Wrote {nt_json.name}", flush=True)

    print()
    print(f"  WITHOUT-NT OOS PASS: {pass_without_nt_oos}/12 (primary {primary_pass_without_nt}/4)")
    print(f"  WITH-NT    OOS PASS: {pass_with_nt_oos}/12 (primary {primary_pass_with_nt}/4)")
    print(f"  inflation ratio: {round(inflation_ratio, 3)}")
    print(f"  K4 verdict: {k4_verdict}")
    print()
    print("Sector OOS detail (all 4 primary cells):")
    print(sector_df.to_string(index=False))
    print()
    print("WITH-NT OOS Bonferroni-12 cells:")
    print(cells_with_nt_oos.to_string(index=False))

    return 0


if __name__ == "__main__":
    sys.exit(main())
