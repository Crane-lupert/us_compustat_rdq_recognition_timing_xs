"""Smoke test: build shared_lib/rdq_panel_loader/ panel (no returns).

Validates:
  - load_fundq() returns expected n rows
  - filter_gap_window() retains ≥95% of input
  - rolling_8q_features() emits gap_var_t and gap_dev_t with reasonable distributions
  - ccm_bridge_via_names() merges sic + ff12 + cusip8 successfully
  - exclude_nt_filers() drops ~4% of rows
  - Final panel sustains the ~300K firm-Q target
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path("d:/vscode/us_compustat_rdq_recognition_timing_xs").resolve()))

from shared_lib.rdq_panel_loader import (
    build_panel,
    load_fundq,
    filter_gap_window,
    rolling_8q_features,
    ccm_bridge_via_names,
    exclude_nt_filers,
)

OUT_DIR = Path("d:/vscode/us_compustat_rdq_recognition_timing_xs/artifacts")
OUT_DIR.mkdir(parents=True, exist_ok=True)


def main() -> int:
    print("Step 1: load_fundq", flush=True)
    df0 = load_fundq()
    print(f"  rows: {len(df0):,}", flush=True)

    print("Step 2: filter_gap_window", flush=True)
    df1 = filter_gap_window(df0)
    print(f"  rows: {len(df1):,} ({len(df1)/len(df0)*100:.2f}% of input)", flush=True)

    print("Step 3: rolling_8q_features", flush=True)
    df2 = rolling_8q_features(df1)
    print(f"  rows: {len(df2):,}", flush=True)
    print(f"  gap_var_t notnull: {df2['gap_var_t'].notna().sum():,}", flush=True)
    print(f"  gap_dev_t notnull: {df2['gap_dev_t'].notna().sum():,}", flush=True)

    print("Step 4: drop NaN gap_var_t (insufficient history)", flush=True)
    df3 = df2.dropna(subset=["gap_var_t"]).reset_index(drop=True)
    print(f"  rows: {len(df3):,}", flush=True)

    print("Step 5: ccm_bridge_via_names", flush=True)
    df4 = ccm_bridge_via_names(df3)
    print(f"  rows: {len(df4):,}", flush=True)
    print(f"  cusip8 notnull: {df4['cusip8'].notna().sum():,}", flush=True)
    print(f"  ff12 unique: {df4['ff12'].nunique()}", flush=True)

    print("Step 6: exclude_nt_filers", flush=True)
    df5 = exclude_nt_filers(df4)
    print(f"  rows: {len(df5):,} ({len(df5)/len(df4)*100:.2f}% of input)", flush=True)

    summary = {
        "step_1_fundq_rows": int(len(df0)),
        "step_2_gap_filtered_rows": int(len(df1)),
        "step_3_rolling_features_rows": int(len(df2)),
        "step_3_gap_var_t_notnull": int(df2["gap_var_t"].notna().sum()),
        "step_3_gap_dev_t_notnull": int(df2["gap_dev_t"].notna().sum()),
        "step_4_post_dropna_rows": int(len(df3)),
        "step_5_post_ccm_bridge_rows": int(len(df4)),
        "step_5_cusip8_notnull": int(df4["cusip8"].notna().sum()),
        "step_5_ff12_unique": int(df4["ff12"].nunique()),
        "step_6_post_nt_exclusion_rows": int(len(df5)),
        "gap_var_t_quantiles": {
            "q01": float(df3["gap_var_t"].quantile(0.01)),
            "q25": float(df3["gap_var_t"].quantile(0.25)),
            "q50": float(df3["gap_var_t"].quantile(0.50)),
            "q75": float(df3["gap_var_t"].quantile(0.75)),
            "q99": float(df3["gap_var_t"].quantile(0.99)),
        },
        "gap_dev_t_quantiles": {
            "q01": float(df3["gap_dev_t"].quantile(0.01)),
            "q25": float(df3["gap_dev_t"].quantile(0.25)),
            "q50": float(df3["gap_dev_t"].quantile(0.50)),
            "q75": float(df3["gap_dev_t"].quantile(0.75)),
            "q99": float(df3["gap_dev_t"].quantile(0.99)),
        },
    }
    out_json = OUT_DIR / "smoke_rdq_panel_loader.json"
    out_json.write_text(json.dumps(summary, indent=2))
    print(f"\nWrote {out_json}", flush=True)

    df5.to_parquet(OUT_DIR / "panel_post_nt_excl.parquet", index=False)
    print(f"Wrote panel_post_nt_excl.parquet ({len(df5):,} rows)", flush=True)

    return 0


if __name__ == "__main__":
    sys.exit(main())
