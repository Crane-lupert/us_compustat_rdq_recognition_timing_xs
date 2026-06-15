"""Phase 1 STEP 2 (Day 2) -- IS-only Strategy A Bonferroni-12 re-confirmation.

Reads:  artifacts/panel_is.parquet  (SHA pinned in phase1_is_oos_split.json)
Writes: artifacts/strategy_A_bonferroni12_is.csv
        artifacts/strategy_A_bonferroni12_is.json

Re-uses scripts/strategy_A_bonferroni.py core (build_monthly_xs_panel,
assign_subcells, run_bonferroni_12, lds_axes) verbatim. Only the input
panel and output filenames differ.

HALT condition (Lock D + autopilot prompt STEP 2): if <3/4 primary cells
(A120-LH, A120-SH, A180-LH, A180-SL) achieve |t| > 2.78 on IS, halt and
trigger diagnostics audit; do not advance to STEP 3.

Primary cells (Lock D §1):
  A120-LH  Phase 0 t=3.74  IS expected ~2.85
  A120-SH  Phase 0 t=2.89  IS expected ~1.50  (weakest -- may dip <2.78)
  A180-LH  Phase 0 t=3.89  IS expected ~3.30
  A180-SL  Phase 0 t=3.73  IS expected ~2.62
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path("d:/vscode/us_compustat_rdq_recognition_timing_xs")
sys.path.insert(0, str(ROOT / "scripts"))

import strategy_A_bonferroni as sab  # type: ignore  # noqa: E402

ART = ROOT / "artifacts"
PANEL_PATH = ART / "panel_is.parquet"
OUT_CSV = ART / "strategy_A_bonferroni12_is.csv"
OUT_JSON = ART / "strategy_A_bonferroni12_is.json"

PRIMARY_CELLS = {"A120-LH", "A120-SH", "A180-LH", "A180-SL"}
IS_EXPECTED = {
    "A120-LH": 2.85,
    "A120-SH": 1.50,
    "A180-LH": 3.30,
    "A180-SL": 2.62,
}
T_THRESHOLD = sab.T_THRESHOLD
HALT_PRIMARY_FLOOR = 3  # <3/4 primary cells |t|>2.78 triggers HALT


def main() -> int:
    print(f"Loading {PANEL_PATH.name} (IS partition) ...", flush=True)
    panel = pd.read_parquet(PANEL_PATH)
    print(f"  rows: {len(panel):,}", flush=True)
    n_with_returns = panel[[f"car_{h}" for h in sab.HORIZONS]].notna().any(axis=1).sum()
    print(f"  rows with >=1 horizon CAR: {n_with_returns:,}", flush=True)
    print(f"  rdq range: {panel['rdq'].min()} .. {panel['rdq'].max()}", flush=True)

    print("Building monthly XS panel for gap_var_t (IS) ...", flush=True)
    df = sab.build_monthly_xs_panel(panel, "gap_var_t")
    df = sab.assign_subcells(df)
    print(f"  panel with q5+subcells: {len(df):,}", flush=True)

    print("Running Bonferroni-12 on IS partition ...", flush=True)
    cells = sab.run_bonferroni_12(df, sign_positive=True)
    cells.to_csv(OUT_CSV, index=False)
    print(f"Wrote {OUT_CSV.name}", flush=True)

    pass_count = int(cells["passes_bonferroni"].sum())
    if pass_count >= 3:
        verdict_b12 = "PASS"
    elif pass_count == 2:
        verdict_b12 = "BORDERLINE"
    else:
        verdict_b12 = "KILL"

    primary = cells[cells["cell"].isin(PRIMARY_CELLS)].copy()
    primary["expected_t_is"] = primary["cell"].map(IS_EXPECTED)
    primary["primary_pass"] = (
        (primary["t_stat"].abs() > T_THRESHOLD) & primary["sign_correct"]
    )
    primary_pass_count = int(primary["primary_pass"].sum())
    halt = primary_pass_count < HALT_PRIMARY_FLOOR
    verdict_primary = "PASS" if not halt else "HALT"

    lds = sab.lds_axes(int(n_with_returns), cells)

    summary = {
        "strategy": "A - rdq-datadate gap variance XS (RD1)",
        "phase": 1,
        "step": 2,
        "day": 2,
        "partition": "IS (1999-01-01..2016-12-31)",
        "input_panel": str(PANEL_PATH.as_posix()),
        "n_panel_rows": int(len(panel)),
        "n_panel_with_returns": int(n_with_returns),
        "verdict_bonferroni_12_is": verdict_b12,
        "pass_count_of_12_is": pass_count,
        "primary_cells": sorted(PRIMARY_CELLS),
        "primary_pass_count_of_4": primary_pass_count,
        "primary_halt_floor": HALT_PRIMARY_FLOOR,
        "primary_verdict": verdict_primary,
        "threshold_t": T_THRESHOLD,
        "lds_is": lds,
        "cells_csv": str(OUT_CSV.as_posix()),
    }
    OUT_JSON.write_text(json.dumps(summary, indent=2, default=str))
    print(f"Wrote {OUT_JSON.name}", flush=True)

    print()
    print("=" * 70)
    print(f"Phase 1 STEP 2 -- IS Bonferroni-12: {verdict_b12} ({pass_count}/12)")
    print(f"  primary cells PASS: {primary_pass_count}/4  (HALT floor: {HALT_PRIMARY_FLOOR})")
    print(f"  primary verdict: {verdict_primary}")
    print(f"  LDS_IS: {lds['score']}/7 {lds['verdict']}")
    print("=" * 70)
    print()
    print("Primary cell detail:")
    print(primary[["cell", "n_months", "mu_spread", "t_stat",
                   "sign_correct", "primary_pass", "expected_t_is"]].to_string(index=False))
    print()
    print("All 12 cells:")
    print(cells.to_string(index=False))
    return 0 if not halt else 2


if __name__ == "__main__":
    sys.exit(main())
