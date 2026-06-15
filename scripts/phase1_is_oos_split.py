"""Phase 1 STEP 1 (Day 1) — IS/OOS split + SHA pin.

Reads:  artifacts/panel_with_returns.parquet (Phase 0 frozen panel)
Writes: artifacts/panel_is.parquet     (1999-01-01 .. 2016-12-31)
        artifacts/panel_oos.parquet    (2017-01-01 .. 2024-12-31)  SEALED until Day 4
        artifacts/phase1_is_oos_split.json (SHA pins + row counts)

Per Lock D §3: 2025 rdq rows (partial year, post-OOS boundary) are excluded.
Per autopilot prompt PROHIBITIONS: panel_oos.parquet is written but not analysed
until Day 4. This script computes only row counts on OOS (a SHA-pin metadata
operation; no Strategy A statistics are touched).

Lock F: SHA-256 over byte-stable parquet output (engine=pyarrow, default
compression). Re-runs yield identical SHA when source SHA matches.
"""

from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ART = Path("d:/vscode/us_compustat_rdq_recognition_timing_xs/artifacts")
SOURCE_PANEL = ART / "panel_with_returns.parquet"
IS_PANEL = ART / "panel_is.parquet"
OOS_PANEL = ART / "panel_oos.parquet"
SUMMARY = ART / "phase1_is_oos_split.json"

IS_START = "1999-01-01"
IS_END = "2016-12-31"
OOS_START = "2017-01-01"
OOS_END = "2024-12-31"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    print(f"Loading {SOURCE_PANEL.name} ...", flush=True)
    panel = pd.read_parquet(SOURCE_PANEL)
    n_total = len(panel)
    src_sha = sha256_file(SOURCE_PANEL)
    print(f"  source rows: {n_total:,}", flush=True)
    print(f"  source sha256: {src_sha}", flush=True)

    is_mask = (panel["rdq"] >= IS_START) & (panel["rdq"] <= IS_END)
    oos_mask = (panel["rdq"] >= OOS_START) & (panel["rdq"] <= OOS_END)
    excl_pre = (panel["rdq"] < IS_START).sum()
    excl_post = (panel["rdq"] > OOS_END).sum()

    panel_is = panel.loc[is_mask].sort_values(
        ["gvkey", "rdq"], kind="mergesort"
    ).reset_index(drop=True)
    panel_oos = panel.loc[oos_mask].sort_values(
        ["gvkey", "rdq"], kind="mergesort"
    ).reset_index(drop=True)

    print(f"  IS rows ({IS_START}..{IS_END}): {len(panel_is):,}", flush=True)
    print(f"  OOS rows ({OOS_START}..{OOS_END}): {len(panel_oos):,}  [SEALED until Day 4]", flush=True)
    print(f"  excluded pre-{IS_START[:4]}: {int(excl_pre):,}", flush=True)
    print(f"  excluded post-{OOS_END[:4]}: {int(excl_post):,}", flush=True)

    panel_is.to_parquet(IS_PANEL, engine="pyarrow", index=False)
    panel_oos.to_parquet(OOS_PANEL, engine="pyarrow", index=False)
    is_sha = sha256_file(IS_PANEL)
    oos_sha = sha256_file(OOS_PANEL)
    print(f"  wrote {IS_PANEL.name}  sha256={is_sha}", flush=True)
    print(f"  wrote {OOS_PANEL.name} sha256={oos_sha}", flush=True)

    is_year_counts = (
        panel_is["rdq"].dt.year.value_counts().sort_index().to_dict()
    )
    oos_year_counts = (
        panel_oos["rdq"].dt.year.value_counts().sort_index().to_dict()
    )

    n_with_returns_is = (
        panel_is[["car_60", "car_120", "car_180"]].notna().any(axis=1).sum()
    )
    n_with_returns_oos = (
        panel_oos[["car_60", "car_120", "car_180"]].notna().any(axis=1).sum()
    )

    summary = {
        "phase": 1,
        "step": 1,
        "day": 1,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "lock_d_section_3": "IS 1999-01-01..2016-12-31 / OOS 2017-01-01..2024-12-31",
        "source": {
            "path": str(SOURCE_PANEL.as_posix()),
            "rows": int(n_total),
            "sha256": src_sha,
        },
        "is_partition": {
            "path": str(IS_PANEL.as_posix()),
            "rows": int(len(panel_is)),
            "sha256": is_sha,
            "n_with_returns": int(n_with_returns_is),
            "year_counts": {int(y): int(c) for y, c in is_year_counts.items()},
        },
        "oos_partition": {
            "path": str(OOS_PANEL.as_posix()),
            "rows": int(len(panel_oos)),
            "sha256": oos_sha,
            "n_with_returns": int(n_with_returns_oos),
            "year_counts": {int(y): int(c) for y, c in oos_year_counts.items()},
            "sealed_until": "Day 4 (STEP 4) — strategy_A_bonferroni verbatim",
        },
        "excluded": {
            "pre_1999": int(excl_pre),
            "post_2024": int(excl_post),
        },
        "row_balance_check": int(len(panel_is)) + int(len(panel_oos))
        + int(excl_pre) + int(excl_post) == int(n_total),
    }
    SUMMARY.write_text(json.dumps(summary, indent=2))
    print(f"  wrote {SUMMARY.name}", flush=True)

    print()
    print("=" * 70)
    print(f"Phase 1 STEP 1 -- IS/OOS split + SHA pin: {'OK' if summary['row_balance_check'] else 'BALANCE FAIL'}")
    print(f"  source sha256:  {src_sha}")
    print(f"  IS    sha256:   {is_sha}")
    print(f"  OOS   sha256:   {oos_sha}   [SEALED]")
    print("=" * 70)
    return 0 if summary["row_balance_check"] else 1


if __name__ == "__main__":
    sys.exit(main())
