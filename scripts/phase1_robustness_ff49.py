"""Phase 1 deferred robustness (b): FF49 industry partition.

Re-runs Bonferroni-12 with industry-tilt sub-cells defined on Fama-French 49
(vs FF12 in the primary specification). Tests whether the variance-of-cadence
signal survives a finer industry classification.

FF49 'high-tilt' bucket = the FF12 'high-tilt' codes (FF12 6/10/11 = BusEq +
Hlth + Money) re-expressed in FF49:
  FF12 6  BusEq  -> FF49 {12 MedEq, 35 Hardw, 36 Softw, 37 Chips, 38 LabEq}
  FF12 10 Hlth   -> FF49 {11 Hlth, 13 Drugs}
  FF12 11 Money  -> FF49 {45 Banks, 46 Insur, 48 Fin}

Everything else -> low-tilt.

Reads:  artifacts/panel_with_returns.parquet
Writes: artifacts/strategy_A_bonferroni12_ff49.{csv,json}

This script runs on existing car_60/120/180 columns; no dsf_v2 re-stream.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path("d:/vscode/us_compustat_rdq_recognition_timing_xs")
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "shared_lib" / "rdq_panel_loader"))

import strategy_A_bonferroni as sab  # type: ignore  # noqa: E402
from ff49 import ff49_from_sic, FF49_NAMES  # type: ignore  # noqa: E402

ART = ROOT / "artifacts"
PANEL_PATH = ART / "panel_with_returns.parquet"
OUT_CSV = ART / "strategy_A_bonferroni12_ff49.csv"
OUT_JSON = ART / "strategy_A_bonferroni12_ff49.json"

# FF49 codes that re-express the FF12 high-tilt buckets (BusEq + Hlth + Money).
FF49_HIGH_TILT = {12, 35, 36, 37, 38, 11, 13, 45, 46, 48}


def assign_ff49_subcells(panel: pd.DataFrame) -> pd.DataFrame:
    """Re-label ind_bin under FF49-defined tilt (size_bin retains FF12 monthly XS
    median definition for fairness vs primary results)."""
    df = panel.copy()
    df["ff49"] = df["sic"].apply(ff49_from_sic).astype("int8")
    df["mcap_mil"] = df["cshoq"] * df["prccq"]
    df["rdq_month"] = df["rdq"].dt.to_period("M")
    df = df.sort_values(["rdq_month", "ff12", "mcap_mil"], kind="mergesort").reset_index(drop=True)
    grp = df.groupby(["rdq_month", "ff12"], sort=False, observed=True)["mcap_mil"]
    median_mcap = grp.transform("median")
    df["size_bin"] = np.where(df["mcap_mil"] >= median_mcap, "L", "S")
    df["ind_bin"] = np.where(df["ff49"].isin(FF49_HIGH_TILT), "H", "L")
    return df


def main() -> int:
    print(f"Loading {PANEL_PATH.name} ...", flush=True)
    panel = pd.read_parquet(PANEL_PATH)
    print(f"  rows: {len(panel):,}", flush=True)

    print("Building monthly XS panel for gap_var_t (FF49 partition) ...", flush=True)
    df = sab.build_monthly_xs_panel(panel, "gap_var_t")
    df = assign_ff49_subcells(df)
    print(f"  panel with q5+subcells: {len(df):,}", flush=True)

    # FF49 high-tilt incidence
    n_high = int((df["ind_bin"] == "H").sum())
    n_low = int((df["ind_bin"] == "L").sum())
    print(f"  ind_tilt H (FF49 high-tilt): {n_high:,}  ({n_high/len(df)*100:.1f}%)", flush=True)
    print(f"  ind_tilt L (rest):           {n_low:,}  ({n_low/len(df)*100:.1f}%)", flush=True)

    print("Running Bonferroni-12 on FF49 partition ...", flush=True)
    cells = sab.run_bonferroni_12(df, sign_positive=True)
    cells.to_csv(OUT_CSV, index=False)
    print(f"Wrote {OUT_CSV.name}", flush=True)

    pass_count = int(cells["passes_bonferroni"].sum())
    sign_correct = int(cells["sign_correct"].sum())
    if pass_count >= 3:
        verdict = "PASS"
    elif pass_count == 2:
        verdict = "BORDERLINE"
    else:
        verdict = "KILL"

    # Comparison to FF12 primary specification
    ff12_results = pd.read_csv(ART / "strategy_A_bonferroni12.csv")
    ff12_pass = int(ff12_results["passes_bonferroni"].sum())

    summary = {
        "phase": 1,
        "step": "deferred_robustness_axis_b_ff49",
        "axis_lock_d_ref": "§7 (b) FF49 industry partition (advisory)",
        "input_panel": str(PANEL_PATH.as_posix()),
        "n_panel_rows": int(len(panel)),
        "ff49_high_tilt_codes": sorted(FF49_HIGH_TILT),
        "ff49_high_tilt_name_map": {k: FF49_NAMES[k] for k in sorted(FF49_HIGH_TILT)},
        "n_ind_tilt_H": n_high,
        "n_ind_tilt_L": n_low,
        "pct_ind_tilt_H": round(n_high / len(df) * 100, 2),
        "ff49_pass_count_of_12": pass_count,
        "ff49_sign_correct_of_12": sign_correct,
        "ff49_verdict": verdict,
        "ff12_pass_count_of_12_primary": ff12_pass,
        "concordance_note": (
            "FF49 vs FF12 partition agreement on the Bonferroni-12 verdict "
            "is the key sensitivity check: if FF49 yields broadly similar pass "
            "count, the FF12 result is robust to industry-classification choice."
        ),
        "cells_csv": str(OUT_CSV.as_posix()),
        "cells_detail": cells.to_dict(orient="records"),
    }
    OUT_JSON.write_text(json.dumps(summary, indent=2, default=str))
    print(f"Wrote {OUT_JSON.name}", flush=True)

    print()
    print("=" * 70)
    print(f"FF49 partition robustness")
    print(f"  FF49 Bonferroni-12 pass: {pass_count}/12   verdict: {verdict}")
    print(f"  FF49 sign-correct:       {sign_correct}/12")
    print(f"  FF12 primary pass (ref): {ff12_pass}/12")
    print(f"  concordance: {'consistent' if abs(pass_count - ff12_pass) <= 1 else 'divergent (review)'}")
    print("=" * 70)
    print()
    print(cells.to_string(index=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
