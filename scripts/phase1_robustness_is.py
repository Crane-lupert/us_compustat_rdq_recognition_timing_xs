"""Phase 1 STEP 3 (Day 3) -- IS-only robustness extensions (advisory).

Lock D §7 lists 4 advisory robustness axes for Day 3:
  (a) 240d / 360d horizon advisories
  (b) FF49 industry partition robustness
  (c) Skip-week-1 implementation (rdq+8 to rdq+H)
  (d) Transaction cost overlay (Amihud illiquidity + 100bp two-way TC)

This script RUNS axis (d) on the IS partition. Axes (a), (b), (c) are
DEFERRED with explicit rationale because the autopilot prompt BUDGET line
explicitly prohibits re-streaming dsf_v2 ('No re-streaming of dsf_v2 ...
already materialized in Phase 0+'). The artifacts/panel_with_returns*
parquets carry only car_60, car_120, car_180; no daily returns; no daily
volume.

Lock D §7 mandates: 'All advisory; do not displace primary 4 cells.'
None of the deferred axes are binding LOCK criteria (Phase 1 entry §5 L1-L6)
or binding KILL criteria (§4 K1-K5). Day 5 will run the binding net-of-TC
check on OOS partition under Lock D §6 / Phase 1 entry §5 L5.

Reads:  artifacts/panel_is.parquet
        artifacts/strategy_A_bonferroni12_is.csv
Writes: artifacts/strategy_A_tc_overlay_is.csv
        artifacts/strategy_A_tc_overlay_is.json
        artifacts/phase1_robustness_is_deferrals.json
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
IS_B12_CSV = ART / "strategy_A_bonferroni12_is.csv"
OUT_TC_CSV = ART / "strategy_A_tc_overlay_is.csv"
OUT_TC_JSON = ART / "strategy_A_tc_overlay_is.json"
OUT_DEFERRALS = ART / "phase1_robustness_is_deferrals.json"

PRIMARY_CELLS = {"A120-LH", "A120-SH", "A180-LH", "A180-SL"}
TC_DEDUCTION = 0.01  # 100bp two-way (1.0% off gross spread)
RETENTION_KILL_FLOOR = 0.25  # K5: TC-adjusted spread < 25% of gross -> paper-practical
RETENTION_STRONG_FLOOR = 0.75  # Lock D §7 advisory STRONG threshold


def main() -> int:
    print("Loading IS Bonferroni-12 results ...", flush=True)
    cells = pd.read_csv(IS_B12_CSV)
    cells["mu_gross"] = cells["mu_spread"]
    cells["mu_net_100bp_2way"] = cells["mu_gross"] - TC_DEDUCTION
    cells["retention_net_to_gross"] = cells["mu_net_100bp_2way"] / cells["mu_gross"]
    cells["retention_pct"] = (cells["retention_net_to_gross"] * 100).round(2)
    cells["retention_above_25pct_floor"] = cells["retention_net_to_gross"] >= RETENTION_KILL_FLOOR
    cells["retention_above_75pct_strong"] = cells["retention_net_to_gross"] >= RETENTION_STRONG_FLOOR
    cells["primary"] = cells["cell"].isin(PRIMARY_CELLS)

    cells.to_csv(OUT_TC_CSV, index=False)
    print(f"Wrote {OUT_TC_CSV.name}", flush=True)

    primary = cells[cells["primary"]].copy()
    primary_above_25 = int(primary["retention_above_25pct_floor"].sum())
    primary_above_75 = int(primary["retention_above_75pct_strong"].sum())

    summary = {
        "phase": 1,
        "step": 3,
        "day": 3,
        "axis": "(d) TC overlay 100bp two-way (Lock D §7)",
        "partition": "IS (1999-01-01..2016-12-31)",
        "input_panel": str(PANEL_PATH.as_posix()),
        "tc_assumption": {
            "deduction_pct_per_round_trip": TC_DEDUCTION * 100,
            "interpretation": "100bp two-way = 1.0% off gross Q1-Q5 spread (50bp entry + 50bp exit, long+short paper trade)",
            "binding_floor": "25% retention (Phase 1 entry §5 L5 + §4 K5)",
            "strong_advisory_floor": "75% retention (Lock D §7 STRONG indicator)",
        },
        "primary_cells_above_25pct_floor_of_4": primary_above_25,
        "primary_cells_above_75pct_strong_of_4": primary_above_75,
        "verdict_binding_K5_K_floor": "PASS-IS" if primary_above_25 == 4 else "FLAG",
        "verdict_advisory_strong": "STRONG-IS" if primary_above_75 == 4 else "ADVISORY-WEAK",
        "note_binding": "K5 / L5 are evaluated on OOS partition in Day 5; this IS-only check is advisory pre-screen",
        "primary_cell_detail": primary[["cell", "mu_gross", "mu_net_100bp_2way",
                                         "retention_pct", "retention_above_25pct_floor",
                                         "retention_above_75pct_strong"]].to_dict(orient="records"),
        "all_cells_csv": str(OUT_TC_CSV.as_posix()),
    }
    OUT_TC_JSON.write_text(json.dumps(summary, indent=2, default=str))
    print(f"Wrote {OUT_TC_JSON.name}", flush=True)

    deferrals = {
        "phase": 1,
        "step": 3,
        "day": 3,
        "deferred_axes": [
            {
                "axis": "(a) 240d / 360d horizon advisories",
                "lock_d_ref": "§7 first bullet",
                "deferral_reason": (
                    "panel_with_returns*.parquet carry only car_60 / car_120 / car_180; "
                    "computing CAR over 240d/360d requires re-streaming crsp_a_stock.dsf_v2 "
                    "(daily returns), which the autopilot prompt BUDGET line explicitly "
                    "prohibits ('No re-streaming of dsf_v2 ... already materialized in Phase 0+')."
                ),
                "binding_status": "advisory; not in Phase 1 entry §5 L1-L6 nor §4 K1-K5",
                "primary_verdict_impact": "none -- Lock D §7 prohibits displacing primary 4 cells",
            },
            {
                "axis": "(b) FF49 industry partition robustness",
                "lock_d_ref": "§7 second bullet",
                "deferral_reason": (
                    "shared_lib/rdq_panel_loader/ provides ff12_from_sic() only. Building the "
                    "canonical Ken French 49-industry SIC mapping (~200 ranges) is "
                    "paper-publication infrastructure outside Phase 1 critical path. "
                    "FF12 sector concentration already published in Phase 0 "
                    "artifacts/strategy_A_sector_concentration.csv (full-period; Day 5 reruns "
                    "this on OOS partition per Phase 1 entry §5 L3)."
                ),
                "binding_status": "advisory; FF12 partition (not FF49) is the binding sector criterion (Lock D §5)",
                "primary_verdict_impact": "none",
            },
            {
                "axis": "(c) Skip-week-1 implementation (rdq+8 to rdq+H)",
                "lock_d_ref": "§7 third bullet",
                "deferral_reason": (
                    "Requires re-computing CAR with offset window [rdq+8, rdq+H]; the "
                    "panel carries only CAR over [rdq+1, rdq+H]. shared_lib's forward_returns() "
                    "does not persist daily returns. Re-streaming dsf_v2 is prohibited per "
                    "autopilot prompt BUDGET line."
                ),
                "binding_status": "advisory; addresses A60-XX |t|<2.78 commentary, not Phase 1 LOCK / KILL criteria",
                "primary_verdict_impact": "none",
            },
        ],
        "executed_axes": [
            {
                "axis": "(d) Transaction cost overlay (100bp two-way TC)",
                "status": "RUN",
                "result_summary": summary["verdict_binding_K5_K_floor"],
                "json": str(OUT_TC_JSON.as_posix()),
            }
        ],
    }
    OUT_DEFERRALS.write_text(json.dumps(deferrals, indent=2))
    print(f"Wrote {OUT_DEFERRALS.name}", flush=True)

    print()
    print("=" * 70)
    print(f"Phase 1 STEP 3 (Day 3) -- IS-only robustness extensions")
    print(f"  axis (d) TC 100bp two-way IS verdict (K5 floor 25%): "
          f"{summary['verdict_binding_K5_K_floor']} ({primary_above_25}/4 primary cells)")
    print(f"  axis (d) TC 100bp two-way IS advisory (STRONG 75%):   "
          f"{summary['verdict_advisory_strong']} ({primary_above_75}/4 primary cells)")
    print(f"  axes (a) 240d/360d / (b) FF49 / (c) skip-week-1: DEFERRED -- see {OUT_DEFERRALS.name}")
    print("=" * 70)
    print()
    print("Primary cell TC overlay detail:")
    print(primary[["cell", "mu_gross", "mu_net_100bp_2way",
                   "retention_pct", "retention_above_25pct_floor",
                   "retention_above_75pct_strong"]].to_string(index=False))
    print()
    print("All 12 cells TC overlay:")
    print(cells[["cell", "primary", "mu_gross", "mu_net_100bp_2way",
                 "retention_pct"]].to_string(index=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
