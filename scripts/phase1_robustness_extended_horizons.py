"""Phase 1 deferred robustness (a + c): extended horizons + skip-week-1.

Runs Bonferroni-12 on four additional horizons computed by
scripts/build_forward_returns_extended.py:

  car_240         [rdq+1,  rdq+240]   horizon advisory
  car_360         [rdq+1,  rdq+360]   horizon advisory
  car_120_sw1     [rdq+8,  rdq+120]   skip-week-1 (PEAD-overlap-clean)
  car_180_sw1     [rdq+8,  rdq+180]   skip-week-1

For each horizon: 4 sub-cells (size L/S x ind-tilt H/L) under primary FF12
partition. Sub-cells inherit Lock C direction matrix (Q1 long / Q5 short).

Reads:  artifacts/panel_with_returns_ext.parquet (built upstream)
Writes: artifacts/strategy_A_extended_horizons.{csv,json}
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
OUT_CSV = ART / "strategy_A_extended_horizons.csv"
OUT_JSON = ART / "strategy_A_extended_horizons.json"

# (label, car_column, horizon_days, axis_descriptor)
HORIZON_RUNS = [
    ("A240", "car_240", 240, "horizon advisory"),
    ("A360", "car_360", 360, "horizon advisory"),
    ("A120-SW1", "car_120_sw1", 120, "skip-week-1 (rdq+8 to rdq+120)"),
    ("A180-SW1", "car_180_sw1", 180, "skip-week-1 (rdq+8 to rdq+180)"),
]


def run_cells_for_car(df: pd.DataFrame, car_col: str, prefix: str) -> pd.DataFrame:
    rows = []
    for sz in ("L", "S"):
        for it in ("H", "L"):
            sub = df[(df["size_bin"] == sz) & (df["ind_bin"] == it)]
            mu, t, n_months = sab.compute_qspread_t(sub, car_col, q_long=1, q_short=5)
            sign_ok = mu > 0
            t_ok = (abs(t) > sab.T_THRESHOLD) if not np.isnan(t) else False
            passed = bool(sign_ok and t_ok and t > 0)
            rows.append({
                "cell": f"{prefix}-{sz}{it}",
                "horizon_label": prefix,
                "car_col": car_col,
                "size": sz,
                "ind_tilt": it,
                "n_months": n_months,
                "mu_spread": mu,
                "t_stat": t,
                "sign_correct": sign_ok,
                "passes_bonferroni": passed,
            })
    return pd.DataFrame(rows)


def main() -> int:
    print(f"Loading {PANEL_PATH.name} ...", flush=True)
    panel = pd.read_parquet(PANEL_PATH)
    print(f"  rows: {len(panel):,}", flush=True)
    for _, col, _, _ in HORIZON_RUNS:
        if col not in panel.columns:
            print(f"  ERROR: column {col} missing -- did you run build_forward_returns_extended.py?", flush=True)
            return 1
        n_nn = panel[col].notna().sum()
        print(f"  {col}: {n_nn:,} non-null", flush=True)

    print("Building monthly XS panel for gap_var_t ...", flush=True)
    df = sab.build_monthly_xs_panel(panel, "gap_var_t")
    df = sab.assign_subcells(df)
    print(f"  panel with q5+subcells: {len(df):,}", flush=True)

    all_cells = []
    for label, car_col, h, axis in HORIZON_RUNS:
        print(f"Running {label} ({car_col}, {axis}) ...", flush=True)
        cells = run_cells_for_car(df, car_col, label)
        all_cells.append(cells)
        pass_count = int(cells["passes_bonferroni"].sum())
        sign_count = int(cells["sign_correct"].sum())
        print(f"  {label}: {pass_count}/4 PASS, {sign_count}/4 sign-correct", flush=True)

    combined = pd.concat(all_cells, ignore_index=True)
    combined.to_csv(OUT_CSV, index=False)
    print(f"Wrote {OUT_CSV.name}", flush=True)

    summary = {
        "phase": 1,
        "step": "deferred_robustness_extended_horizons",
        "axes": [
            "(a) 240d / 360d horizon advisories (Lock D §7)",
            "(c) Skip-week-1 (rdq+8 to rdq+H) -- PEAD-overlap clean (Lock D §7)",
        ],
        "input_panel": str(PANEL_PATH.as_posix()),
        "n_panel_rows": int(len(panel)),
        "horizon_runs": [
            {
                "label": label,
                "car_col": col,
                "horizon_d": h,
                "axis": axis,
                "n_cells": 4,
                "pass_count": int(combined[combined["horizon_label"] == label]["passes_bonferroni"].sum()),
                "sign_correct": int(combined[combined["horizon_label"] == label]["sign_correct"].sum()),
            }
            for label, col, h, axis in HORIZON_RUNS
        ],
        "total_cells": int(len(combined)),
        "total_pass": int(combined["passes_bonferroni"].sum()),
        "total_sign_correct": int(combined["sign_correct"].sum()),
        "threshold_t": sab.T_THRESHOLD,
        "cells_csv": str(OUT_CSV.as_posix()),
        "cells_detail": combined.to_dict(orient="records"),
    }
    OUT_JSON.write_text(json.dumps(summary, indent=2, default=str))
    print(f"Wrote {OUT_JSON.name}", flush=True)

    print()
    print("=" * 78)
    print(f"Extended horizons + skip-week-1: {summary['total_pass']}/16 PASS, "
          f"{summary['total_sign_correct']}/16 sign-correct")
    print("=" * 78)
    print(combined.to_string(index=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
