"""Sub-gate (d) — ρ(gap_var_t, gap_dev_t) redundancy check.

Threshold:
  ρ < 0.85 → MERGE OK, retain both Strategy A and Strategy B
  ρ ≥ 0.85 → drop Strategy B, repo continues as us_compustat_rdq_variance_xs

Uses the panel materialized in artifacts/panel_post_nt_excl.parquet (smoke test output).
We compute three correlations:
  (i)   Pearson ρ on raw values
  (ii)  Spearman ρ on ranks (robust to outliers)
  (iii) Pearson ρ on |gap_dev_t| (since Strategy B is asymmetric, the magnitude
        of deviation is the part conceptually closest to Strategy A's variance)

If any of (i)/(ii)/(iii) is ≥ 0.85, the two strategies are flagged redundant.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ART = Path("d:/vscode/us_compustat_rdq_recognition_timing_xs/artifacts")
PANEL_PATH = ART / "panel_post_nt_excl.parquet"


def main() -> int:
    df = pd.read_parquet(PANEL_PATH)
    print(f"Loaded panel: {len(df):,} firm-Q rows", flush=True)

    mask = df["gap_var_t"].notna() & df["gap_dev_t"].notna()
    sub = df.loc[mask, ["gap_var_t", "gap_dev_t"]].copy()
    sub["abs_gap_dev_t"] = sub["gap_dev_t"].abs()

    pearson = sub[["gap_var_t", "gap_dev_t"]].corr(method="pearson").iloc[0, 1]
    spearman = sub[["gap_var_t", "gap_dev_t"]].corr(method="spearman").iloc[0, 1]
    pearson_abs = sub[["gap_var_t", "abs_gap_dev_t"]].corr(method="pearson").iloc[0, 1]
    spearman_abs = sub[["gap_var_t", "abs_gap_dev_t"]].corr(method="spearman").iloc[0, 1]

    rhos = {
        "pearson_raw": float(pearson),
        "spearman_raw": float(spearman),
        "pearson_abs_gap_dev": float(pearson_abs),
        "spearman_abs_gap_dev": float(spearman_abs),
    }
    max_abs_rho = max(abs(v) for v in rhos.values())

    verdict = "PASS" if max_abs_rho < 0.85 else "KILL"
    decoupling_margin = 0.85 - max_abs_rho

    out = {
        "subgate": "(d) RD1 vs RD7 rho redundancy BINARY",
        "verdict": verdict,
        "threshold": 0.85,
        "max_abs_rho": max_abs_rho,
        "decoupling_margin_to_threshold": decoupling_margin,
        "rhos": rhos,
        "n_observations": int(mask.sum()),
        "panel_path": str(PANEL_PATH.as_posix()),
        "note": "ρ ≥ 0.85 on any of 4 axes → KILL (drop Strategy B); ρ < 0.85 on all 4 axes → PASS (retain both)",
    }
    out_path = ART / "subgate_d_rho.json"
    out_path.write_text(json.dumps(out, indent=2))
    print(f"Wrote {out_path}", flush=True)

    print()
    print("=" * 70)
    print(f"SUB-GATE (d) ρ REDUNDANCY VERDICT: {verdict}")
    print("=" * 70)
    print(f"  Pearson ρ(gap_var_t, gap_dev_t):     {pearson:+.4f}")
    print(f"  Spearman ρ(gap_var_t, gap_dev_t):    {spearman:+.4f}")
    print(f"  Pearson ρ(gap_var_t, |gap_dev_t|):   {pearson_abs:+.4f}")
    print(f"  Spearman ρ(gap_var_t, |gap_dev_t|):  {spearman_abs:+.4f}")
    print(f"  Max |ρ|:                              {max_abs_rho:.4f}")
    print(f"  Threshold:                            0.85")
    print(f"  Decoupling margin:                    {decoupling_margin:+.4f}")
    return 0 if verdict == "PASS" else 2


if __name__ == "__main__":
    sys.exit(main())
