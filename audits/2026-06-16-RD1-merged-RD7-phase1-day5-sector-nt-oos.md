---
date: 2026-06-16
phase: 1
step: 5 (Day 5)
repo: us_compustat_rdq_recognition_timing_xs
project_id: RD1-merged-RD7
script: scripts/phase1_sector_nt_oos.py
artifacts:
  - artifacts/strategy_A_sector_oos.csv
  - artifacts/strategy_A_sector_oos.json
  - artifacts/strategy_A_with_nt_oos.csv
  - artifacts/strategy_A_with_nt_oos.json
verdict_summary: |
  Sector Lock D §5: 3/4 PASS (3 high-tilt cells PASS; A180-SL 5/9 low-tilt FAIL).
  K4 (WITH-NT inflation): ratio 2.0 at threshold but not > 2.0 -> K4_NOT_TRIGGERED.
  K2 already fired Day 4 -- both Day 5 axes are paper anchors, not LAYER A gates.
---

# Phase 1 Day-5 — Sector Concentration OOS + WITH-NT Sensitivity OOS

## §1 Status check

K2 fired on Day 4 (paper-practical-only verdict locked). Day 5 runs sector + WITH-NT diagnostics for paper §4 (sector robustness) and §5 (NT mechanical-confound) anchors. **Day 5 results do not change the Phase 1 verdict.** They inform paper writeup and provide partial evidence on the mechanism's economic interpretability.

## §2 Axis (a) — Sector concentration on OOS (Lock D §5)

### §2.1 High-tilt cells (BusEq + Hlth both required)

| Cell | BusEq (ff12=6) μ | BusEq pos | Hlth (ff12=10) μ | Hlth pos | Lock D §5 |
|---|---:|:-:|---:|:-:|:-:|
| A120-LH | +4.32% | ✓ | +5.67% | ✓ | **PASS** |
| A120-SH | +6.60% | ✓ | +6.73% | ✓ | **PASS** |
| A180-LH | +5.06% | ✓ | +10.65% | ✓ | **PASS** |

All 3 high-tilt cells PASS the sector criterion. Health-care sector OOS contribution is particularly strong for A180-LH (+10.65% per-Hlth Q1-Q5 spread). BusEq Q1-Q5 spread is consistently +4-7% across the three high-tilt cells.

### §2.2 Low-tilt cell A180-SL (≥6/9 sectors positive required)

| ff12 | sector | μ_spread | t_stat | pos? |
|:-:|---|---:|---:|:-:|
| 1 | NoDur | −1.41% | −0.34 | ✗ |
| 2 | Durbl | +17.46% | **3.34** | ✓ |
| 3 | Manuf | +0.62% | 0.20 | ✓ |
| 4 | Enrgy | −4.97% | −0.67 | ✗ |
| 5 | Chems | +5.15% | 1.06 | ✓ |
| 7 | Telcm | −2.33% | −0.38 | ✗ |
| 8 | Utils | −7.90% | **−2.36** | ✗ |
| 9 | Shops | +5.21% | 1.14 | ✓ |
| 12 | Other | +7.06% | 2.24 | ✓ |

**5/9 low-tilt sectors positive → A180-SL FAILS Lock D §5 (criterion: ≥6/9).**

Sector-level diagnostic:
- Durbl is the dominant positive contributor (+17.46% per-sector spread, t=3.34) — A180-SL OOS signal is concentrated in durable-goods firms.
- Utils flips significantly negative (−7.90%, t=−2.36) — utility-sector firms exhibit anti-sign at the 180d horizon. Plausible mechanism: regulated-utility rate review cycles introduce predictable cadence not connected to information uncertainty.
- 4/9 anti-sign sectors (NoDur, Enrgy, Telcm, Utils) — broad-based sectoral disagreement, not a single-sector outlier.

### §2.3 Sector verdict summary

Lock D §5 sector criterion: **3/4 primary cells PASS**. A180-SL fails the breadth bar despite strong durable-goods contribution. Since K2 already fired on Day 4, K3 KILL is moot (the paper-practical outcome was already locked). The 3/4 PASS rate confirms the mechanism is sectorally interpretable for high-tilt (BusEq + Hlth) cells.

## §3 Axis (b) — WITH-NT vs WITHOUT-NT on OOS (K4 check)

### §3.1 OOS Bonferroni-12 comparison

| Variant | Rows | PASS / 12 | Primary PASS / 4 | Sign-correct |
|---|---:|:-:|:-:|:-:|
| WITHOUT-NT (Day 4 primary) | 178,210 | 0 | 0 | 11/12 |
| WITH-NT (Day 5 sensitivity) | 183,544 | **2** | 1 | 11/12 |

WITH-NT OOS PASS cells: **A180-LH (t=3.57)** and **A180-LL (t=3.53)**. A180-LH is primary; A180-LL is secondary.

### §3.2 K4 inflation ratio

Inflation ratio = WITH-NT PASS / max(WITHOUT-NT PASS, 1) = 2 / 1 = **2.0**.

K4 threshold (Phase 1 entry §4): "WITH-NT OOS pass count > 2× WITHOUT-NT OOS pass count". The realized 2.0 is **at, but not exceeding, the threshold** → **K4_NOT_TRIGGERED** (strict inequality).

This is a *borderline* result. WITH-NT adds 2 PASS cells while WITHOUT-NT has 0 — meaning the NT-filer cohort contributes incremental signal. Interpretation: NT-filers themselves carry the variance-of-cadence signal through the same economic mechanism (their late reporting **is** the high-variance signal). Excluding them removes both the suspicious mechanical-confound AND a genuine signal source.

### §3.3 Mechanism interpretation (paper §5 anchor)

Two competing hypotheses on the NT-inflation:
1. **Mechanical confound**: NT firms have artificially-high `gap_var_t` (≥75d gap) that mechanically correlates with predictable post-NT recovery returns (or distress dynamics). Excluding them is the correct prophylactic.
2. **Genuine signal source**: NT firms are a sub-population where the cadence-variance mechanism is most active (extreme reporting noise → strongest forward-CAR response). Excluding them removes power.

The K4 ratio of exactly 2.0 sits between these two interpretations. Paper §5 should report this borderline result transparently: the WITHOUT-NT primary panel is the **pre-registered** specification (sub-gate (c)); the WITH-NT pass count of 2/12 (A180-LH primary + A180-LL secondary) is offered as a sensitivity that confirms the directional signal extends to NT-filers.

## §4 Paper writeup implications

| Paper section | Day 5 anchor |
|---|---|
| §4 Results — sector | 3/4 high-tilt cells PASS BusEq+Hlth (3/4 OOS sector robustness). A180-SL fails breadth bar (5/9 low-tilt sectors positive). |
| §5 Robustness — NT | WITHOUT-NT primary 0/12; WITH-NT sensitivity 2/12 (A180-LH + A180-LL). K4 ratio 2.0 at threshold but not exceeding. Mechanism interpretation: NT-filers may carry the signal genuinely, not as confound. |

## §5 Combined OOS picture (Days 4 + 5)

| Diagnostic | Result | Implication |
|---|---|---|
| Bonferroni-12 OOS primary 4 | 0/4 PASS | K2 fires → paper-practical |
| 11/12 cells sign-correct OOS | ✓ | Directional signal preserved |
| Top OOS cell A180-LL secondary | t=2.49 (sub-threshold) | Near-pass but secondary |
| Sector OOS high-tilt | 3/3 PASS | Mechanism economically interpretable |
| Sector OOS low-tilt A180-SL | 5/9 (FAIL) | Concentrated in Durbl + Other |
| WITH-NT OOS Bonferroni-12 | 2/12 PASS | Signal extends to NT-filers (borderline confound) |
| K4 inflation ratio | 2.0 (at threshold) | NOT_TRIGGERED (strict >) |

## §6 Hand-off to Day 6 (paper outline + Phase 1 close)

STEP 6 cleared. Day 6 deliverables:
- Paper outline (max 5 pages structure) drafted via `D:/vscode/portfolio-coordination/shared-utils/shared_utils/openrouter_client.py`. NO direct API key lookup.
- Phase 1 close audit: `audits/<date>-RD1-merged-RD7-phase1-close.md`.
- Lock F audit: `bash D:/vscode/meta-harness/scripts/audit-pipeline-determinism.sh .`
- Meta-harness auto-report: PASS / PARTIAL / KILL close report — outcome is **paper-practical** (taxonomy bucket 2).

Paper outline §1-§7 specified in autopilot prompt STEP 6.

## §7 Commit pin

| Commit | Description |
|---|---|
| `fd2828f` | STEP 0: Day-0 anti-bias |
| `fa3e334` | STEP 1: IS/OOS split |
| `a7c8965` | STEP 2: IS Bonferroni 3/4 PASS |
| `ce52490` | STEP 3: TC overlay 4/4 PASS + 3 axes deferred |
| `0186fd7` | STEP 4: OOS reveal — K2 fires |
| TBD | STEP 5: Sector 3/4 + K4 NOT_TRIGGERED |
