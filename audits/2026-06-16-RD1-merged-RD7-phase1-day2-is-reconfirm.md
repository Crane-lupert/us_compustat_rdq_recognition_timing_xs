---
date: 2026-06-16
phase: 1
step: 2 (Day 2)
repo: us_compustat_rdq_recognition_timing_xs
project_id: RD1-merged-RD7
script: scripts/phase1_strategy_A_is.py
artifacts:
  - artifacts/strategy_A_bonferroni12_is.csv
  - artifacts/strategy_A_bonferroni12_is.json
verdict: PASS (3/4 primary cells |t| > 2.78 on IS) — HALT floor met
---

# Phase 1 Day-2 — IS Re-confirmation of 4 Primary Cells (Strategy A)

## §1 Purpose

Re-run Strategy A Bonferroni-12 on the IS-only partition (1999-01-01..2016-12-31, sha256 `c2929544...4924e`) to re-confirm the 4 primary cells [Lock D §1](2026-06-16-RD1-merged-RD7-phase1-prereg-lock-d.md). HALT condition (autopilot prompt STEP 2): if <3/4 primary cells achieve |t| > 2.78 on IS, halt and trigger diagnostics audit; do not advance to STEP 3.

## §2 Verdict: **PASS — 3/4 primary cells confirm**

| | Result |
|---|---|
| Bonferroni-12 IS pass count | **4/12** (matches Phase 0 full-period 4/12) |
| Primary cells PASS (4) | **3/4** ≥ HALT floor 3 → **PASS** |
| All 12 cells sign-correct | ✓ |
| LDS_IS axes score | **7/7 LIVE-DEPLOYABLE-STRONG** |

## §3 Primary cell detail (Lock D §1 four cells)

| Cell | n_months | μ_spread (IS) | t_stat (IS) | Phase 0 expected_IS | sign | primary_pass |
|---|---:|---:|---:|---:|:-:|:-:|
| A120-LH | 198 | +3.37% | **3.37** | 2.85 | ✓ | **PASS** |
| A120-SH | 187 | +2.66% | 2.06 | 1.50 | ✓ | FAIL (sign-correct, sub-threshold) |
| A180-LH | 198 | +4.14% | **3.31** | 3.30 | ✓ | **PASS** |
| A180-SL | 200 | +4.93% | **3.62** | 2.62 | ✓ | **PASS** |

**Pre-acknowledged**: A120-SH was tagged in Lock D §4 as the weakest primary cell ("around 2.0 if signal persists; weakest — may dip below threshold on IS-only"). Empirical IS t=2.06 lands exactly in that range. A120-SH remains primary for OOS reporting (Lock C / Lock D immutable) but did not contribute to the HALT-floor count.

A180-SL is materially stronger than expected (3.62 vs 2.62 expected). This is consistent with Phase 0 full-period t=3.73, suggesting the late-period sub-sample (which lifts the full-period stat) is contained within the IS partition rather than the OOS partition. Reinforces the pre-acknowledged risk that OOS A180-SL may be lower than Phase 0 full.

## §4 Full 12-cell IS Bonferroni-12

| horizon | size | tilt | cell | n_mo | μ_spread | t_stat | sign✓ | passes |
|---:|:-:|:-:|---|---:|---:|---:|:-:|:-:|
| 60 | L | H | A60-LH | 198 | +1.39% | 2.24 | ✓ | — |
| 60 | L | L | A60-LL | 199 | +0.85% | 1.26 | ✓ | — |
| 60 | S | H | A60-SH | 187 | +2.03% | 1.64 | ✓ | — |
| 60 | S | L | A60-SL | 200 | +2.22% | **3.09** | ✓ | **PASS** |
| 120 | L | H | A120-LH | 198 | +3.37% | **3.37** | ✓ | **PASS** primary |
| 120 | L | L | A120-LL | 199 | +2.21% | 1.70 | ✓ | — |
| 120 | S | H | A120-SH | 187 | +2.66% | 2.06 | ✓ | — primary |
| 120 | S | L | A120-SL | 200 | +2.94% | 2.68 | ✓ | — (borderline) |
| 180 | L | H | A180-LH | 198 | +4.14% | **3.31** | ✓ | **PASS** primary |
| 180 | L | L | A180-LL | 199 | +3.35% | 1.99 | ✓ | — |
| 180 | S | H | A180-SH | 187 | +3.69% | 2.17 | ✓ | — |
| 180 | S | L | A180-SL | 200 | +4.93% | **3.62** | ✓ | **PASS** primary |

Bonferroni-12 PASS cells (IS): A60-SL, A120-LH, A180-LH, A180-SL = 4. Note A60-SL is a **secondary** cell (Lock D §2) — its IS pass is informative but does not change the primary verdict. A120-SH (primary) and A60-SL (secondary) swap their threshold-crossing status relative to Phase 0 full-period in opposite directions — sample-period sensitivity within IS, not a Lock C structural shift.

## §5 LDS_IS detail (7/7)

| Axis | Pass | Reason |
|---|:-:|---|
| 1 signal_well_defined | 1 | `gap_var_t` 8Q rolling std, formula unchanged |
| 2 sample_size_sufficient | 1 | n_with_returns 245,198 >> 200×12 floor |
| 3 bonferroni_pass_floor | 1 | 4 pass cells ≥ 3 floor |
| 4 sign_majority_correct | 1 | 12/12 sign-correct ≥ 7/12 floor |
| 5 horizon_robustness | 1 | ≥1 pass in each of 60d / 120d / 180d horizons |
| 6 subcell_diversity | 1 | Pass cells span size {L,S} and tilt {H,L} |
| 7 anchor_post_pub_decay_resilience | 1 | 4 pass cells ≥ 4 floor |

## §6 Comparison to Phase 0 full-period

| Cell | Phase 0 full t | IS t | Δ (IS − full) | Interpretation |
|---|---:|---:|---:|---|
| A120-LH | 3.74 | 3.37 | −0.37 | IS slightly weaker, expected |
| A120-SH | 2.89 | 2.06 | −0.83 | IS drops below threshold (expected per Lock D §4) |
| A180-LH | 3.89 | 3.31 | −0.58 | IS slightly weaker, expected |
| A180-SL | 3.73 | 3.62 | −0.11 | IS nearly matches full — late-period contribution muted |

The IS partition (1999-2016) carries most of the Phase 0 signal. The OOS partition (2017-2024) sub-period t-stats are already known to be weaker (Lock D §4 references 1.55-1.86 range from Phase 0 sub-period diagnostics). Day 4 OOS reveal will test whether ≥2/4 primary cells exceed |t| > 2.78 on OOS.

## §7 Hand-off to Day 3

STEP 3 (Day 3) cleared to begin:

- Input: `artifacts/panel_is.parquet` only (IS-tunable robustness extensions per Lock D §7)
- Script: `scripts/phase1_robustness_is.py`
- Axes:
  - (a) 240d / 360d horizon advisories (8 additional advisory cells)
  - (b) FF49 industry partition (vs FF12 primary)
  - (c) Skip-week-1 (rdq+8 → rdq+H)
  - (d) Transaction cost overlay (Amihud illiquidity + 100bp two-way TC); verify primary cells retain ≥75% of gross spread
- All robustness results are advisory; do not displace primary 4 cells.

## §8 Commit pin

| Commit | Description |
|---|---|
| `fd2828f` | Phase 1 STEP 0: Day-0 anti-bias self-check audit |
| `fa3e334` | Phase 1 STEP 1 (Day 1): IS/OOS split + OOS lock SHA pin |
| TBD | Phase 1 STEP 2 (Day 2): IS re-confirmation 3/4 PASS |
