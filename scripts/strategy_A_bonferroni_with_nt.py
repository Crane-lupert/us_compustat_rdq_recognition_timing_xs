"""Strategy A — WITH-NT sensitivity (sub-gate (c) ≤50% drop sub-criterion close).

Compares Bonferroni-12 PASS count WITH-NT vs WITHOUT-NT.

Reads:
  artifacts/panel_with_returns.parquet      (post-NT exclusion, primary)
  artifacts/panel_with_returns_full.parquet (NO NT exclusion, sensitivity)

If WITH-NT PASS count > 2× WITHOUT-NT PASS count → mechanical NT confound suspected.
If WITH-NT PASS count is similar (±1 cell) → primary is NT-independent.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

REPO = Path("d:/vscode/us_compustat_rdq_recognition_timing_xs")
sys.path.insert(0, str(REPO / "scripts"))

from strategy_A_bonferroni import (  # type: ignore[import-not-found]
    build_monthly_xs_panel, assign_subcells, run_bonferroni_12, lds_axes,
    HORIZONS, T_THRESHOLD,
)

ART = REPO / "artifacts"


def run_one(panel: pd.DataFrame, label: str) -> dict:
    df = build_monthly_xs_panel(panel, "gap_var_t")
    df = assign_subcells(df)
    cells = run_bonferroni_12(df, sign_positive=True)
    out_csv = ART / f"strategy_A_bonferroni12_{label}.csv"
    cells.to_csv(out_csv, index=False)
    pass_count = int(cells["passes_bonferroni"].sum())
    sign_correct = int(cells["sign_correct"].sum())
    n_with_returns = int(panel[[f"car_{h}" for h in HORIZONS]].notna().any(axis=1).sum())
    return {
        "label": label,
        "n_panel_rows": int(len(panel)),
        "n_with_returns": n_with_returns,
        "pass_count": pass_count,
        "sign_correct_count": sign_correct,
        "cells_csv": str(out_csv.as_posix()),
        "lds": lds_axes(n_with_returns, cells),
        "cells": cells.to_dict(orient="records"),
    }


def main() -> int:
    print("Running WITHOUT-NT (primary, post-NT exclusion) ...", flush=True)
    panel_w_excl = pd.read_parquet(ART / "panel_with_returns.parquet")
    res_excl = run_one(panel_w_excl, "primary_post_nt_excl")
    print(f"  PASS: {res_excl['pass_count']}/12  sign-correct: {res_excl['sign_correct_count']}/12  LDS: {res_excl['lds']['score']}/7", flush=True)

    print("Running WITH-NT (sensitivity, no exclusion) ...", flush=True)
    panel_full = pd.read_parquet(ART / "panel_with_returns_full.parquet")
    res_full = run_one(panel_full, "sensitivity_with_nt")
    print(f"  PASS: {res_full['pass_count']}/12  sign-correct: {res_full['sign_correct_count']}/12  LDS: {res_full['lds']['score']}/7", flush=True)

    drop = res_full["pass_count"] - res_excl["pass_count"]  # positive = WITH-NT > WITHOUT-NT
    inflation_ratio = (
        res_full["pass_count"] / max(res_excl["pass_count"], 1)
    )
    if inflation_ratio > 2.0:
        verdict = "NT_CONFOUND_SUSPECTED — WITH-NT > 2× WITHOUT-NT"
    elif abs(drop) <= 1:
        verdict = "NT_INDEPENDENT — primary stands without NT-filers"
    else:
        verdict = "NT_CONTRIBUTES_MILDLY — WITH-NT adds ≤2 cells"

    summary = {
        "subgate_c_50pct_drop_close": verdict,
        "without_nt": {
            "pass_count": res_excl["pass_count"],
            "sign_correct": res_excl["sign_correct_count"],
            "lds_score": res_excl["lds"]["score"],
        },
        "with_nt": {
            "pass_count": res_full["pass_count"],
            "sign_correct": res_full["sign_correct_count"],
            "lds_score": res_full["lds"]["score"],
        },
        "drop_cells": drop,
        "inflation_ratio": round(inflation_ratio, 3),
        "threshold": "WITH-NT > 2× WITHOUT-NT → NT_CONFOUND_SUSPECTED",
        "cells_detail_without_nt": res_excl["cells"],
        "cells_detail_with_nt": res_full["cells"],
    }
    out_json = ART / "strategy_A_with_nt_sensitivity.json"
    out_json.write_text(json.dumps(summary, indent=2, default=str))
    print(f"Wrote {out_json}", flush=True)

    print()
    print("=" * 70)
    print(f"Sub-gate (c) ≤50% drop formal close")
    print(f"  WITHOUT-NT: {res_excl['pass_count']}/12  sign: {res_excl['sign_correct_count']}/12  LDS: {res_excl['lds']['score']}/7")
    print(f"  WITH-NT:    {res_full['pass_count']}/12  sign: {res_full['sign_correct_count']}/12  LDS: {res_full['lds']['score']}/7")
    print(f"  inflation ratio: {summary['inflation_ratio']}")
    print(f"  verdict: {verdict}")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    sys.exit(main())
