# Phase 1 Entry — RD1 Strategy A (us_compustat_rdq_recognition_timing_xs)

**Date**: 2026-06-16 (entry day)
**Repo**: D:/vscode/us_compustat_rdq_recognition_timing_xs/
**Project type (Gate G)**: methodology/discovery → `reports/papers/` lane
**Phase 0 verdict**: Strategy A PASS (4/12 Bonferroni, LDS 6/7 LIVE-DEPLOYABLE-STRONG); Strategy B KILL (appendix only)
**Locks active**: Lock C (direction matrix + cell structure), Lock D (cell selection + OOS protocol), Lock F (pipeline determinism)

## §1 Mission

Confirm Strategy A as a **LAYER A LOCKED** signal in the Compustat-Recognition-Timing pod (1st LOCKED candidate slot, currently empty) via:
1. OOS 2017–2024 hold-out validation (≥2/4 primary cells confirm |t| > 2.78 sign-correct)
2. Multi-axis robustness portfolio (TC overlay, FF49 partition, skip-week-1, sector validation)
3. Paper draft for target venue JFE / JFQA / RAST

## §2 Work plan (Day-by-day)

### Day 1 — OOS lock SHA pin + IS/OOS split

- Pin `audits/<date>-RD1-merged-RD7-phase1-oos-lock.md` with SHA of `panel_with_returns.parquet` (frozen).
- Rebuild panel by year filter: IS = 1999-2016, OOS = 2017-2024 (per Lock D §3).
- Do **not** touch OOS partition until Day 4.

### Day 2 — IS re-confirmation of 4 primary cells

- Re-run `scripts/strategy_A_bonferroni.py` on IS-only panel.
- Expectations (from Phase 0 sub-period analysis):
  - A120-LH IS t ≈ 2.85 (combining 1999-2007 + 2008-2016)
  - A180-LH IS t ≈ 3.30
  - A180-SL IS t ≈ 2.62
  - A120-SH IS t ≈ 1.50 (weakest — may dip below threshold on IS-only)
- If <3/4 cells exceed |t| > 2.78 on IS, halt + diagnostics audit (do not advance to OOS).

### Day 3 — IS-only robustness extensions (tunable)

- 240d / 360d horizon advisories (4 advisory cells per horizon × 2 horizons = 8 advisory cells).
- FF49 industry partition robustness on IS only.
- Skip-week-1 implementation (rdq+8 → rdq+H) — addresses A60-XX |t| < 2.78 question.
- TC overlay: Amihud illiquidity-adjusted spread + 100bp two-way TC; verify primary cells retain ≥75% of gross spread.

### Day 4 — OOS reveal + primary verdict

- Run `scripts/strategy_A_bonferroni.py` verbatim on OOS partition.
- Report 4 cells' OOS μ_spread + t-stat + sign + Bonferroni-12 verdict.
- Verdict logic (Lock D §1):
  - ≥3/4 OOS cells PASS → LAYER A LOCKED (Compustat-Recognition-Timing pod slot claim)
  - 2/4 OOS cells PASS → LAYER A LOCKED conditional on Day 5 sector robustness PASS
  - ≤1/4 OOS cells PASS → paper-practical-only

### Day 5 — Sector concentration validation + WITH-NT sensitivity

- Per-FF12 sector OOS t-stats for each cell.
- Sector robustness PASS (Lock D §5):
  - high-tilt cells: BusEq + Hlth OOS sign-correct positive
  - low-tilt cell A180-SL: ≥6/9 sectors OOS sign-correct positive
- WITH-NT vs WITHOUT-NT OOS Bonferroni-12 comparison (Lock D §6).

### Day 6 — Paper outline + Phase 1 close audit

- Draft outline (max 5 pages structure):
  - §1 Introduction — extension axis from Bagnoli-Kross-Watts 2002 level → variance
  - §2 Data — Compustat fundq 1999-2024 + CRSP dsf_v2; sample 371K firm-Q with CAR
  - §3 Methodology — gap_var_t = 8Q rolling std; monthly XS quintile within FF12; Bonferroni-12 cells
  - §4 Results — IS 4/4 PASS + OOS confirmation + sector robustness + sub-period stability
  - §5 Robustness — TC overlay + FF49 + skip-week-1 + WITH-NT sensitivity
  - §6 Strategy B NEG appendix — Chambers-Penman 1984 post-pub decay (24-cell asymmetric decomposition supports DEAD-CONFIRMED)
  - §7 Discussion — variance-of-X family update (1/3 LAYER A); pod assignment; LDS evolution
- Phase 1 close audit `audits/<date>-RD1-merged-RD7-phase1-close.md` + meta-harness auto-report.

## §3 Budget

| Item | Estimate |
|---|---|
| Compute (Day 1-5 re-runs) | $0 (WRDS local dump; no LLM) |
| LLM (paper draft Day 6) | $25-75 (OpenRouter via shared_utils, NOT direct API key) |
| Time | 6 working days |
| Phase 1 KILL probability (pre-mortem) | 35-45% (OOS power-constrained; A120-SH IS may fail) |

## §4 Phase 1 KILL conditions

If any of these fire, Phase 1 closes with paper-practical-only outcome (no LAYER A LOCK):

| Condition | Trigger | Action |
|---|---|---|
| IS re-confirmation fails | <3/4 primary cells |t| > 2.78 on IS-only | Halt + diagnostics audit |
| OOS primary verdict ≤1/4 | <2/4 OOS cells PASS | paper-practical-only |
| Sector robustness fails | high-tilt: BusEq + Hlth not both PASS sign-correct OOS; low-tilt: <6/9 sectors positive | paper-practical-only |
| WITH-NT mechanical confound | WITH-NT OOS pass > 2× WITHOUT-NT OOS | Full NT audit required |
| TC overlay strips signal | TC-adjusted spread <25% of gross | paper-practical-only |

## §5 Phase 1 LAYER A LOCK conditions (POSITIVE outcome)

All of the following must hold for the **LAYER A LOCKED** verdict:

- [ ] IS re-confirmation ≥3/4 |t| > 2.78
- [ ] OOS ≥2/4 |t| > 2.78 sign-correct
- [ ] Sector robustness PASS (Lock D §5)
- [ ] WITH-NT sensitivity within 50% drop bound
- [ ] TC-adjusted spread ≥25% of gross
- [ ] Phase 1 close audit Lock-F compliant

If all 6 → **Compustat-Recognition-Timing pod 1st LOCKED candidate slot CLAIMED.**

## §6 Source-of-truth provenance

- Phase 0 close: `audits/2026-06-16-RD1-merged-RD7-phase0-close.md`
- Lock C (direction matrix + cell structure): `audits/2026-06-16-RD1-merged-RD7-lock-c.md`
- Lock D (Phase 1 pre-reg cell selection + OOS): `audits/2026-06-16-RD1-merged-RD7-phase1-prereg-lock-d.md`
- Lock F (pipeline determinism): `audits/2026-06-16-RD1-merged-RD7-lock-f-determinism.md`
- Meta-harness PASS close report: `D:/vscode/meta-harness/audits/2026-06-16-RD1-merged-RD7-PASS-close-report.md`

## §7 Variance-of-X family status pre-Phase-1

| Member | Phase | LAYER A status |
|---|---|---|
| F1 (FDA expectation variance) | Closed | Frozen-two-layer (sub-LAYER A) |
| F6 (clinicaltrials amendment) | Closed | Post-pub-downgrade-tentative |
| **RD1 Strategy A (rdq variance)** | **Phase 1 entry 2026-06-16** | **LAYER A candidate** |

Phase 1 outcome will move RD1 from 1/3 LAYER A candidate to either:
- 1/3 LAYER A LOCKED (variance-of-X first LAYER A LOCK in family)
- 1/3 paper-practical (family score remains 0 LAYER A LOCKED, but RD1 is the first paper-practical PASS)

## §8 Hand-off

This audit is the binding entry document for Phase 1 work. Subsequent Phase 1 audits reference §1-§7 by name. Any deviation requires Lock D §9 deviation protocol.

**Phase 1 cleared to begin** subject to Phase 0+ consolidated audit (WITH-NT sensitivity + Strategy B asymmetric + Strategy A robustness) closure — see `audits/2026-06-16-RD1-merged-RD7-phase0-plus-consolidated.md`.
