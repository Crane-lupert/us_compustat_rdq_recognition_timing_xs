"""Phase 1 STEP 4 (Day 4) -- OOS REVEAL + primary verdict (BINDING).

Reads:  artifacts/panel_oos.parquet  (sha256 b5d039bc...db76e6; SEAL BROKEN here)
Writes: artifacts/strategy_A_bonferroni12_oos.csv
        artifacts/strategy_A_bonferroni12_oos.json

Runs scripts/strategy_A_bonferroni.py core (build_monthly_xs_panel,
assign_subcells, run_bonferroni_12, lds_axes) VERBATIM on the OOS subset.
NO parameter tuning. NO cell re-selection. NO direction reversal.

Primary cells (Lock D §1 -- immutable):
  A120-LH  A120-SH  A180-LH  A180-SL

OOS verdict logic (Lock D §1 + Phase 1 entry §5 L2):
  >= 3/4 OOS PASS -> LAYER A LOCKED candidate (pending Day 5)
  == 2/4 OOS PASS -> LAYER A LOCKED conditional on Day 5 robustness PASS
  <= 1/4 OOS PASS -> paper-practical-only (K2 fires)
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
PANEL_PATH = ART / "panel_oos.parquet"
OUT_CSV = ART / "strategy_A_bonferroni12_oos.csv"
OUT_JSON = ART / "strategy_A_bonferroni12_oos.json"

PRIMARY_CELLS = {"A120-LH", "A120-SH", "A180-LH", "A180-SL"}
T_THRESHOLD = sab.T_THRESHOLD


def main() -> int:
    print(f"Loading {PANEL_PATH.name} (OOS partition) -- SEAL BREAK", flush=True)
    panel = pd.read_parquet(PANEL_PATH)
    print(f"  rows: {len(panel):,}", flush=True)
    n_with_returns = panel[[f"car_{h}" for h in sab.HORIZONS]].notna().any(axis=1).sum()
    print(f"  rows with >=1 horizon CAR: {n_with_returns:,}", flush=True)
    print(f"  rdq range: {panel['rdq'].min()} .. {panel['rdq'].max()}", flush=True)

    print("Building monthly XS panel for gap_var_t (OOS) ...", flush=True)
    df = sab.build_monthly_xs_panel(panel, "gap_var_t")
    df = sab.assign_subcells(df)
    print(f"  panel with q5+subcells: {len(df):,}", flush=True)

    print("Running Bonferroni-12 on OOS partition ...", flush=True)
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
    primary["primary_pass"] = (
        (primary["t_stat"].abs() > T_THRESHOLD) & primary["sign_correct"]
    )
    primary_pass_count = int(primary["primary_pass"].sum())

    # Lock D §1 + Phase 1 entry §5 L2 verdict logic
    if primary_pass_count >= 3:
        verdict_primary = "LAYER-A-LOCKED-CANDIDATE"
        kill_status = "no K2 trigger"
    elif primary_pass_count == 2:
        verdict_primary = "LAYER-A-LOCKED-CONDITIONAL-ON-DAY5"
        kill_status = "no K2 trigger"
    else:
        verdict_primary = "PAPER-PRACTICAL-ONLY"
        kill_status = "K2 FIRES" if primary_pass_count <= 1 else "no K2 trigger"

    lds = sab.lds_axes(int(n_with_returns), cells)

    summary = {
        "strategy": "A - rdq-datadate gap variance XS (RD1)",
        "phase": 1,
        "step": 4,
        "day": 4,
        "partition": "OOS (2017-01-01..2024-12-31) -- SEAL BROKEN",
        "input_panel": str(PANEL_PATH.as_posix()),
        "n_panel_rows": int(len(panel)),
        "n_panel_with_returns": int(n_with_returns),
        "verdict_bonferroni_12_oos": verdict_b12,
        "pass_count_of_12_oos": pass_count,
        "primary_cells": sorted(PRIMARY_CELLS),
        "primary_pass_count_of_4": primary_pass_count,
        "primary_verdict": verdict_primary,
        "k2_status": kill_status,
        "threshold_t": T_THRESHOLD,
        "lds_oos": lds,
        "cells_csv": str(OUT_CSV.as_posix()),
    }
    OUT_JSON.write_text(json.dumps(summary, indent=2, default=str))
    print(f"Wrote {OUT_JSON.name}", flush=True)

    print()
    print("=" * 70)
    print(f"Phase 1 STEP 4 -- OOS REVEAL")
    print(f"  Bonferroni-12 OOS pass count: {pass_count}/12 ({verdict_b12})")
    print(f"  Primary cells PASS (4): {primary_pass_count}/4")
    print(f"  Primary verdict: {verdict_primary}")
    print(f"  K2 status: {kill_status}")
    print(f"  LDS_OOS: {lds['score']}/7 {lds['verdict']}")
    print("=" * 70)
    print()
    print("Primary cell OOS detail:")
    print(primary[["cell", "n_months", "mu_spread", "t_stat",
                   "sign_correct", "primary_pass"]].to_string(index=False))
    print()
    print("All 12 OOS cells:")
    print(cells.to_string(index=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
