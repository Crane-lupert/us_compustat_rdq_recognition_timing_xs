"""Strategy B — Bonferroni-12 + LDS empirical (within-firm rolling baseline deviation XS).

Reads:  artifacts/panel_with_returns.parquet
Writes: artifacts/strategy_B_bonferroni12.json + .csv
        artifacts/strategy_B_lds.json

Signal: gap_dev_t = gap_t − median(8Q rolling)  (Strategy B asymmetric)
Direction Lock C (symmetric-recoded for Bonferroni-12 parity):
  Q5 (early, neg dev) − Q1 (late, pos dev) > 0
Bonferroni-12: 3 horizons × 4 sub-cells (size large/small × ind-tilt high/low)
Threshold: |t| > 2.78 AND sign-correct
Verdict (graduated): PASS ≥3 / BORDERLINE 2 / KILL <2
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

# Reuse computation primitives from Strategy A script.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from strategy_A_bonferroni import (  # type: ignore[import-not-found]
    HORIZONS, T_THRESHOLD,
    INDUSTRY_TILT_HIGH, INDUSTRY_TILT_LOW,
    build_monthly_xs_panel, assign_subcells,
    compute_qspread_t, lds_axes,
)

ART = Path("d:/vscode/us_compustat_rdq_recognition_timing_xs/artifacts")
PANEL_PATH = ART / "panel_with_returns.parquet"


def run_bonferroni_12_strategy_b(df: pd.DataFrame) -> pd.DataFrame:
    """3 horizons × 4 sub-cells. Strategy B symmetric-recoded spread Q5 − Q1 > 0."""
    rows = []
    for h in HORIZONS:
        for sz in ("L", "S"):
            for it in ("H", "L"):
                sub = df[(df["size_bin"] == sz) & (df["ind_bin"] == it)]
                mu, t, n_months = compute_qspread_t(sub, f"car_{h}", q_long=5, q_short=1)
                sign_ok = (mu > 0)
                t_ok = (abs(t) > T_THRESHOLD) if not np.isnan(t) else False
                passed = bool(sign_ok and t_ok and t > 0)
                rows.append({
                    "horizon_d": h,
                    "size": sz,
                    "ind_tilt": it,
                    "cell": f"B{h}-{sz}{it}",
                    "n_months": n_months,
                    "mu_spread": mu,
                    "t_stat": t,
                    "sign_correct": sign_ok,
                    "passes_bonferroni": passed,
                })
    return pd.DataFrame(rows)


def main() -> int:
    print("Loading panel_with_returns ...", flush=True)
    panel = pd.read_parquet(PANEL_PATH)
    print(f"  rows: {len(panel):,}", flush=True)
    n_with_returns = panel[[f"car_{h}" for h in HORIZONS]].notna().any(axis=1).sum()
    print(f"  rows with ≥1 horizon CAR: {n_with_returns:,}", flush=True)

    print("Building monthly XS panel for gap_dev_t ...", flush=True)
    df = build_monthly_xs_panel(panel, "gap_dev_t")
    df = assign_subcells(df)
    print(f"  panel with q5+subcells: {len(df):,}", flush=True)

    print("Running Bonferroni-12 (Strategy B) ...", flush=True)
    cells = run_bonferroni_12_strategy_b(df)
    cells_path = ART / "strategy_B_bonferroni12.csv"
    cells.to_csv(cells_path, index=False)
    print(f"Wrote {cells_path}", flush=True)

    pass_count = int(cells["passes_bonferroni"].sum())
    if pass_count >= 3:
        verdict = "PASS"
    elif pass_count == 2:
        verdict = "BORDERLINE"
    else:
        verdict = "KILL"

    lds = lds_axes(int(n_with_returns), cells)
    # Strategy B baseline LDS target = 4/7 BORDERLINE, paper-practical OK
    if lds["score"] >= 4:
        lds["paper_practical_ok"] = True
    else:
        lds["paper_practical_ok"] = False

    summary = {
        "strategy": "B - within-firm rolling baseline deviation XS (RD7)",
        "verdict_bonferroni_12": verdict,
        "pass_count_of_12": pass_count,
        "threshold_t": T_THRESHOLD,
        "n_panel_rows": int(len(panel)),
        "n_panel_with_returns": int(n_with_returns),
        "lds": lds,
        "cells_csv": str(cells_path.as_posix()),
    }
    out_json = ART / "strategy_B_bonferroni12.json"
    out_json.write_text(json.dumps(summary, indent=2, default=str))
    print(f"Wrote {out_json}", flush=True)

    print()
    print("=" * 70)
    print(f"STRATEGY B — Bonferroni-12 verdict: {verdict}")
    print(f"  pass cells: {pass_count}/12  (PASS ≥3 / BORDERLINE 2 / KILL <2)")
    print(f"  LDS: {lds['score']}/7 {lds['verdict']}  paper_practical_ok={lds['paper_practical_ok']}")
    print("=" * 70)
    print(cells.to_string(index=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
