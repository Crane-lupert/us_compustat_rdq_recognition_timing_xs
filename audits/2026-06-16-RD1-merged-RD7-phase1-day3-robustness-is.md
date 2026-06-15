---
date: 2026-06-16
phase: 1
step: 3 (Day 3)
repo: us_compustat_rdq_recognition_timing_xs
project_id: RD1-merged-RD7
script: scripts/phase1_robustness_is.py
artifacts:
  - artifacts/strategy_A_tc_overlay_is.csv
  - artifacts/strategy_A_tc_overlay_is.json
  - artifacts/phase1_robustness_is_deferrals.json
verdict: TC overlay axis (d) PASS-IS 4/4 (binding 25% floor); 3 axes DEFERRED per autopilot prompt BUDGET prohibition on re-streaming dsf_v2.
---

# Phase 1 Day-3 — IS-Only Robustness Extensions (Lock D §7 Advisory)

## §1 Purpose

Execute Lock D §7 advisory robustness extensions on the IS partition. The autopilot prompt explicitly notes "All advisory; do not displace primary 4 cells." None of Day 3's axes are binding LOCK criteria (Phase 1 entry §5 L1-L6) nor binding KILL criteria (§4 K1-K5).

## §2 Axis-by-axis status

| Axis | Status | Notes |
|---|:-:|---|
| (a) 240d / 360d horizon advisories | **DEFERRED** | Panel CARs limited to 60/120/180d; CAR over 240/360d requires re-streaming `crsp_a_stock.dsf_v2`, prohibited per autopilot prompt BUDGET line. |
| (b) FF49 industry partition | **DEFERRED** | `shared_lib/rdq_panel_loader/ff12_from_sic()` only; building canonical Ken French 49-industry SIC mapping is paper-publication infra outside Phase 1 critical path. FF12 sector partition is the binding sector criterion (Lock D §5). |
| (c) Skip-week-1 (rdq+8 → rdq+H) | **DEFERRED** | Panel CARs are over [rdq+1, rdq+H]; offset CARs require re-streaming dsf_v2, prohibited per BUDGET line. |
| (d) Transaction cost overlay 100bp two-way | **RUN** | Applied 1.0% deduction from gross μ_spread for all 12 cells. |

Deferral rationale persisted to [artifacts/phase1_robustness_is_deferrals.json](../artifacts/phase1_robustness_is_deferrals.json) for Lock F audit reproducibility.

## §3 Axis (d) — TC overlay 100bp two-way verdict

### §3.1 TC assumption

- Deduction: **1.0%** off gross Q1−Q5 μ_spread per primary cell
- Interpretation: 100bp two-way = 50bp entry + 50bp exit on a paper long-short trade (round-trip TC)
- Binding floor (K5 / L5): retention ≥ **25%** of gross spread
- Advisory STRONG floor (Lock D §7): retention ≥ **75%** of gross spread

### §3.2 Primary cell results (IS)

| Cell | μ_gross | μ_net (1% off) | Retention | ≥25% floor (K5) | ≥75% STRONG |
|---|---:|---:|---:|:-:|:-:|
| A120-LH | +3.37% | +2.37% | 70.4% | ✓ | — |
| A120-SH | +2.66% | +1.66% | 62.4% | ✓ | — |
| A180-LH | +4.14% | +3.14% | 75.8% | ✓ | ✓ |
| A180-SL | +4.93% | +3.93% | 79.7% | ✓ | ✓ |

**Verdict (binding)**: **PASS-IS** — 4/4 primary cells exceed 25% retention floor; K5 KILL condition does not fire on IS.

**Verdict (advisory)**: **ADVISORY-WEAK** — 2/4 primary cells exceed 75% STRONG floor; 120d horizon cells fall in the 62-70% band. Driven by the 100bp deduction being a larger fraction of the lower 120d gross spread (~3%) than of the 180d gross spread (~4-5%).

### §3.3 All 12 IS cells TC overlay

```
   cell    prim    gross   net   retention%
 A60-LH       F   1.39%  0.39%    27.8
 A60-LL       F   0.85% -0.15%   -17.1 (flips sign)
 A60-SH       F   2.03%  1.03%    50.8
 A60-SL       F   2.22%  1.22%    55.0
A120-LH       T   3.37%  2.37%    70.4
A120-LL       F   2.21%  1.21%    54.7
A120-SH       T   2.66%  1.66%    62.4
A120-SL       F   2.94%  1.94%    66.0
A180-LH       T   4.14%  3.14%    75.8
A180-LL       F   3.35%  2.35%    70.1
A180-SH       F   3.69%  2.69%    72.9
A180-SL       T   4.93%  3.93%    79.7
```

**Sign-stability**: 11/12 cells retain positive μ_net. A60-LL flips negative at the 1.0% deduction; a 60d horizon with gross 0.85% cannot survive a 100bp TC charge. A60-LL is a secondary cell — its TC-stability not material to Phase 1 verdict.

## §4 Note on binding TC criterion

The K5 KILL and L5 LOCK conditions in Phase 1 entry §4-§5 are evaluated on the **OOS partition** at Day 5 (via `phase1_sector_nt_oos.py` or paired script). This Day 3 IS-only TC overlay is an advisory pre-screen.

If OOS-net retention < 25% for ≥3/4 primary cells → K5 fires → paper-practical-only outcome.
If OOS-net retention ≥ 25% for ≥3/4 primary cells → L5 holds → contributes to LAYER A LOCK.

Pre-acknowledged risk: OOS μ_gross is expected to be lower than IS (Lock D §4 expects ~2.0 OOS t-stat per primary cell vs IS 2.06-3.62), which tightens the K5 floor on OOS-net. If OOS A120-SH μ_gross drops to ~2% gross, the 1.0% TC charge would yield ~50% retention (still > 25% K5 floor, but close to it).

## §5 Lock F compliance

- All sort calls in [scripts/phase1_robustness_is.py](../scripts/phase1_robustness_is.py) use Pandas DataFrame operations on pre-sorted IS Bonferroni CSV; no group-by aggregation without explicit ordering.
- TC deduction is a deterministic scalar (1.0%) — no stochastic input.
- Re-runs against same `strategy_A_bonferroni12_is.csv` produce identical TC overlay output (verified by file hash on re-execution).

## §6 Hand-off to Day 4 (OOS REVEAL)

STEP 4 cleared. Day 4 deliverables:

- Input: `artifacts/panel_oos.parquet` (sha256 `b5d039bc...db76e6`) — **SEAL BREAKS Day 4**
- Script: `scripts/phase1_strategy_A_oos.py` — runs `strategy_A_bonferroni.py` core verbatim on OOS subset
- Output: `artifacts/strategy_A_bonferroni12_oos.csv` + `.json`
- Verdict (Lock D §1 / Phase 1 entry §5 L2):
  - **≥3/4 OOS PASS** → LAYER A LOCKED candidate (pending Day 5 sector + WITH-NT)
  - **2/4 OOS PASS** → LAYER A LOCKED conditional on Day 5 robustness PASS
  - **≤1/4 OOS PASS** → paper-practical-only (K2 fires)

No parameter tuning. No cell re-selection. Lock C direction matrix and Lock D primary cells are immutable.

## §7 Commit pin

| Commit | Description |
|---|---|
| `fd2828f` | STEP 0: Day-0 anti-bias self-check |
| `fa3e334` | STEP 1 (Day 1): IS/OOS split + SHA pin |
| `a7c8965` | STEP 2 (Day 2): IS Bonferroni-12 PASS 3/4 |
| TBD | STEP 3 (Day 3): TC overlay axis RUN + 3 axes DEFERRED |
