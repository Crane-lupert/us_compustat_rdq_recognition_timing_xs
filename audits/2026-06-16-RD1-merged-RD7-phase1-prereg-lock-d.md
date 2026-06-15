# Lock D — Phase 1 Pre-Registration (Cell Selection + OOS Protocol)

**Date**: 2026-06-16
**Status**: **PRE-REGISTERED** for Phase 1 entry. Immutable post this audit commit.
**Sibling**: Lock C (direction matrix + Bonferroni-12 cell structure, immutable since 2026-06-16)
**Phase 0 close audit**: `audits/2026-06-16-RD1-merged-RD7-phase0-close.md`

Lock D extends Lock C by pinning the cell-level selection that distinguishes **primary** from **secondary** outcomes in Phase 1 OOS validation. Without Lock D, any Phase 1 OOS test invites cherry-picking risk: the analyst sees OOS results across 12 cells and rationalizes which subset to report as primary.

## §1 Primary cells (4)

These 4 cells PASSED Bonferroni-12 in Phase 0 (|t| > 2.78, sign-correct, 12/12 directional consistency confirmed cell-wide). They are the Phase 1 OOS primary outcomes:

| Cell | Horizon | Size | Tilt | Phase 0 μ_spread | Phase 0 t-stat |
|---|---|---|---|---|---|
| A120-LH | 120d | Large | High (BusEq/Hlth/Money) | +3.14% | 3.74 |
| A120-SH | 120d | Small | High | +3.32% | 2.89 |
| A180-LH | 180d | Large | High | +3.99% | 3.89 |
| A180-SL | 180d | Small | Low (NoDur/Durbl/Manuf/Enrgy/Chems/Telcm/Utils/Shops/Other) | +4.74% | 3.73 |

**Phase 1 PASS criterion (primary)**: ≥2/4 cells confirm |t_OOS| > 2.78 with sign-correct on the OOS hold-out partition. If <2/4 confirm, Strategy A is **not** LAYER A LOCKED — it goes to paper-practical-only.

## §2 Secondary cells (8)

These 8 cells were sign-correct in Phase 0 but did not cross Bonferroni-12 |t| > 2.78. They are reported as secondary outcomes — informative but not primary:

| Cell | Horizon | Size | Tilt | Phase 0 μ_spread | Phase 0 t-stat |
|---|---|---|---|---|---|
| A60-LH | 60d | Large | High | +1.20% | 2.00 |
| A60-LL | 60d | Large | Low | +0.69% | 1.30 |
| A60-SH | 60d | Small | High | +1.76% | 1.86 |
| A60-SL | 60d | Small | Low | +1.39% | 2.02 |
| A120-LL | 120d | Large | Low | +2.07% | 2.11 |
| A120-SL | 120d | Small | Low | +2.40% | 2.47 |
| A180-LL | 180d | Large | Low | +3.45% | 2.70 |
| A180-SH | 180d | Small | High | +3.34% | 2.35 |

**Phase 1 secondary commentary criterion**: report all 8 cells' OOS t-stats. No PASS/KILL verdict assigned to secondary cells — they inform the discussion section about the signal's effective time-scale and partition sensitivity.

## §3 OOS hold-out partition

To preserve statistical validity, Phase 1 splits the 1999-2024 sample into:

- **IS (in-sample)**: 1999-01-01 to 2016-12-31 (~216 months, 18 years)
- **OOS (hold-out)**: 2017-01-01 to 2024-12-31 (~96 months, 8 years)

The split is **non-revealable** — Phase 1 Day-0 sets a SHA pin in `audits/<date>-RD1-merged-RD7-phase1-oos-lock.md` and the OOS portion is not touched until all IS-tuning is complete. Any analyst-knob (gap-window edges, rolling-baseline window, Bonferroni threshold, t-stat lag) is fixed on IS and applied verbatim to OOS.

**Rationale for 2017 boundary**: post-Brexit / post-Trump-tariff era natural regime boundary; ≥8 years OOS provides ≥96 months for NW-12 t-stat power.

## §4 Per-cell OOS expectations

Phase 0 sub-period analysis (`artifacts/strategy_A_regime_stability.csv`) shows:

| Cell | 1999-2007 t | 2008-2016 t | 2017-2024 t | OOS expected magnitude |
|---|---|---|---|---|
| A120-LH | 2.12 | 2.65 | 1.55 | Lower than full-period 3.74 — OOS power-constrained |
| A120-SH | 1.24 | 1.76 | 1.86 | Around 2.0 if signal persists |
| A180-LH | 1.90 | 2.79 | 1.85 | Around 2.0 if signal persists |
| A180-SL | 3.44 | 1.80 | 1.74 | Around 2.0 if signal persists |

Phase 1 PASS expects ≥2/4 cells to exceed |t_OOS| > 2.78. This is a **stringent** test given Phase 0's full-period t-stats only marginally exceed 2.78 in some cells. The pre-acknowledged risk: Phase 1 OOS may drop to BORDERLINE rather than LAYER A LOCK.

## §5 Sector concentration robustness criterion

`artifacts/strategy_A_sector_concentration.csv` shows multi-sector positivity (3/3 high-tilt sectors positive in A120-LH; 8/9 low-tilt sectors positive in A180-SL with only Utils negative). Phase 1 OOS confirms sector robustness if:

- High-tilt cells (A120-LH, A120-SH, A180-LH): each of BusEq + Hlth shows OOS sign-correct positive μ_spread on the 2017-2024 partition (Money may drift — its full-period μ is small).
- Low-tilt cell (A180-SL): ≥6 of 9 sectors (NoDur/Durbl/Manuf/Enrgy/Chems/Telcm/Utils/Shops/Other) show OOS sign-correct positive μ.

If sector robustness fails, Phase 1 reports as paper-practical-only even if 2/4 cells pass.

## §6 NT-filer exclusion sensitivity (sub-gate (c) ≤50% drop)

Phase 0 primary uses NT-excluded panel (29,864 firm-Q removed). Phase 1 OOS panel:

- Primary: same NT-excluded panel construction (apply `subgate_c_nt_proxy_exclusion_pool.csv.gz` rule on OOS partition)
- Sensitivity: WITH-NT OOS for one-paragraph robustness check

If WITH-NT OOS PASS count > 2× WITHOUT-NT OOS PASS count → mechanical NT confound suspected and full audit required.

## §7 Allowed Phase 1 modifications (IS-tunable)

- 240d / 360d horizon additions (advisory; do not displace 60d/120d/180d primary)
- FF49 industry partition robustness check (advisory)
- Skip-week-1 implementation (rdq+8 to rdq+H instead of rdq+1 to rdq+H) — addresses PEAD overlap; advisory
- Transaction cost overlay (Amihud illiquidity + 100bp two-way TC) — advisory

**Not allowed**:
- Cell direction reversal (Lock C immutable)
- Bonferroni threshold reduction (|t| > 2.78 fixed)
- Sub-cell re-definition (size large/small, ind-tilt high/low fixed per Lock C §Strategy A)
- Cell merging (Lock C §6 prohibits combined 24-cell counting)

## §8 SHA pin

| Stage | SHA |
|---|---|
| Phase 0 close commit | `8818dd2` (Phase 0 close: RD1-merged-RD7 LAYER A candidate) |
| Lock D commit (this file) | TBD by post-write commit |

## §9 Lock D verdict

**Lock D is pinned by this commit.** Any Phase 1 deviation from §1-§7 requires:
1. A new branch named `phase1-deviation-<short-name>`
2. A pre-deviation audit `audits/<date>-RD1-merged-RD7-lock-d-deviation-<name>.md` explaining the deviation rationale
3. Meta-harness governance approval before merge to main

Default Phase 1 path is verbatim execution of Lock D as written.
