---
date: 2026-06-16
phase: 1
step: 4 (Day 4)
repo: us_compustat_rdq_recognition_timing_xs
project_id: RD1-merged-RD7
script: scripts/phase1_strategy_A_oos.py
artifacts:
  - artifacts/strategy_A_bonferroni12_oos.csv
  - artifacts/strategy_A_bonferroni12_oos.json
verdict: K2 FIRES -- PAPER-PRACTICAL-ONLY (0/4 primary cells PASS on OOS)
---

# Phase 1 Day-4 — OOS REVEAL + Primary Verdict (BINDING)

## §1 Seal break

OOS partition (`panel_oos.parquet`, sha256 `b5d039bc0892a9cd4fc91481de6f3ffd1a397840fab6029c1756c6c05cdb76e6`) opened. `scripts/strategy_A_bonferroni.py` core executed verbatim on the OOS subset via [scripts/phase1_strategy_A_oos.py](../scripts/phase1_strategy_A_oos.py). No parameter tuning. No cell re-selection. No Lock C direction reversal. No Bonferroni-12 threshold reduction.

## §2 Verdict: **K2 FIRES — PAPER-PRACTICAL-ONLY**

| Metric | Result |
|---|---|
| Bonferroni-12 OOS pass count | **0/12** (KILL) |
| Primary cells PASS (Lock D §1) | **0/4** |
| Phase 1 entry §4 K2 ("OOS ≤1/4 PASS") | **FIRES** |
| Phase 1 entry §5 L2 ("OOS ≥2/4 \|t\|>2.78 sign-correct") | **does not hold** |
| All 12 cells sign-correct | 11/12 (only A60-SL flips negative, marginally) |
| LDS_OOS | 3/7 PRACTITIONER-PAPER-ONLY |

**Outcome (Phase 1 entry §4 / autopilot prompt STEP 4)**: paper-practical-only. RD1 Strategy A is **not** a LAYER A LOCKED candidate; the Compustat-Recognition-Timing pod 1st LOCKED slot remains unclaimed. RD1 becomes the variance-of-X family's **first paper-practical PASS** (family score: 0/3 LAYER A LOCKED, 1/3 paper-practical).

## §3 Primary cell OOS detail

| Cell | n_months | μ_spread OOS | t_stat OOS | sign✓ | primary_pass | Lock D §4 expected_OOS |
|---|---:|---:|---:|:-:|:-:|---:|
| A120-LH | 96 | +2.48% | **1.55** | ✓ | FAIL | 1.55 (Phase 0 sub-period) |
| A120-SH | 90 | +3.73% | **1.86** | ✓ | FAIL | ~2.0 |
| A180-LH | 96 | +3.51% | **1.85** | ✓ | FAIL | 1.85 (Phase 0 sub-period) |
| A180-SL | 96 | +4.62% | **1.74** | ✓ | FAIL | 1.74 (Phase 0 sub-period) |

OOS t-stats match the Phase 0 sub-period diagnostics to two decimal places — confirming that the OOS partition did not introduce any new regime shift; it merely reproduced the late-period weakness already visible in Phase 0 close audit `artifacts/strategy_A_regime_stability.csv`.

**Pre-acknowledgement honored**: Lock D §4 explicitly warned "Phase 1 PASS expects ≥2/4 cells to exceed |t_OOS| > 2.78. This is a **stringent** test given Phase 0's full-period t-stats only marginally exceed 2.78 in some cells. The pre-acknowledged risk: Phase 1 OOS may drop to BORDERLINE rather than LAYER A LOCK." The actual outcome (0/4) is one notch below BORDERLINE; the signal is **sign-correct but power-constrained on the 8-year OOS window**.

## §4 All 12 OOS cells

| horizon | size | tilt | cell | n_mo | μ_spread OOS | t_stat OOS | sign✓ | passes |
|---:|:-:|:-:|---|---:|---:|---:|:-:|:-:|
| 60 | L | H | A60-LH | 96 | +0.78% | 0.58 | ✓ | — |
| 60 | L | L | A60-LL | 93 | +0.56% | 0.71 | ✓ | — |
| 60 | S | H | A60-SH | 89 | +1.26% | 0.87 | ✓ | — |
| 60 | S | L | A60-SL | 96 | −0.18% | −0.13 | ✗ | — |
| 120 | L | H | A120-LH | 96 | +2.48% | 1.55 | ✓ | — primary |
| 120 | L | L | A120-LL | 93 | +2.09% | 1.55 | ✓ | — |
| 120 | S | H | A120-SH | 90 | +3.73% | 1.86 | ✓ | — primary |
| 120 | S | L | A120-SL | 96 | +1.52% | 0.81 | ✓ | — |
| 180 | L | H | A180-LH | 96 | +3.51% | 1.85 | ✓ | — primary |
| 180 | L | L | A180-LL | 93 | +4.23% | 2.49 | ✓ | — (BORDERLINE) |
| 180 | S | H | A180-SH | 90 | +3.20% | 1.21 | ✓ | — |
| 180 | S | L | A180-SL | 96 | +4.62% | 1.74 | ✓ | — primary |

Top OOS cell: A180-LL t=2.49 — sign-correct, below the |t|>2.78 Bonferroni-12 threshold but visible as a near-pass. A180-LL is a **secondary** cell (Lock D §2) — its near-pass does not change the primary verdict. The 11/12 sign-correct count is a meaningful **economic signal**: the variance-of-X mechanism is directionally consistent on OOS even though statistically under-powered.

## §5 LDS_OOS detail (3/7)

| Axis | Score | Reason |
|---|:-:|---|
| 1 signal_well_defined | 1 | `gap_var_t` unchanged |
| 2 sample_size_sufficient | 1 | n_with_returns 122,527 >> 200×12 floor |
| 3 bonferroni_pass_floor | 0 | 0 pass cells < 3 floor |
| 4 sign_majority_correct | 1 | 11/12 sign-correct ≥ 7/12 floor |
| 5 horizon_robustness | 0 | 0 pass in 60d/120d/180d (no cell passes any horizon) |
| 6 subcell_diversity | 0 | 0 pass cells |
| 7 anchor_post_pub_decay_resilience | 0 | 0 pass cells < 4 floor |

3/7 LDS_OOS lands in PRACTITIONER-PAPER-ONLY band. This is consistent with the K2 KILL outcome: the signal is academically interesting (11/12 sign-correct, μ_spread economically meaningful at 3-5% over 120-180d) but does not meet the LAYER A LOCK statistical bar on an 8-year OOS window.

## §6 IS vs OOS comparison (primary cells)

| Cell | IS t (Day 2) | OOS t (Day 4) | Δ (OOS − IS) | OOS PASS? |
|---|---:|---:|---:|:-:|
| A120-LH | 3.37 | 1.55 | −1.82 | ✗ |
| A120-SH | 2.06 | 1.86 | −0.20 | ✗ |
| A180-LH | 3.31 | 1.85 | −1.46 | ✗ |
| A180-SL | 3.62 | 1.74 | −1.88 | ✗ |

Notable: A120-SH (the weakest IS cell) is the **most stable** across IS→OOS (only −0.20 drop). A180-SL and A120-LH show the largest drops (~−1.8). The signal's late-period weakening is broad-based across the primary cell grid, not concentrated in a single horizon/size/tilt sub-cell.

## §7 Implications for Phase 1 outcome taxonomy

Per Phase 1 entry §1 mission: "Confirm Strategy A as a **LAYER A LOCKED** signal in the Compustat-Recognition-Timing pod."

This mission is **not achieved** at the LAYER A LOCK bar. The outcome maps to taxonomy bucket **paper-practical** (Phase 1 entry §1 / autopilot prompt OUTCOME TAXONOMY):

- ❌ Compustat-Recognition-Timing pod 1st LOCKED slot — NOT CLAIMED
- ✓ `reports/papers/` lane — eligible (paper-practical outcome)
- ✓ Variance-of-X family — RD1 becomes the **1st paper-practical PASS** (family score 0/3 LAYER A LOCKED → 1/3 paper-practical PASS)
- ✓ Strategy A signal is sign-correct on OOS (11/12 cells) — economically interesting but power-constrained

## §8 Day 5 and Day 6 still required (paper completeness)

K2 firing **does not terminate Phase 1**. Day 5 sector + WITH-NT analyses and Day 6 paper outline are still required to complete the paper-practical writeup. These results inform the paper's §4 Results and §5 Robustness sections regardless of LAYER A LOCK status.

Specifically:
- Day 5 sector OOS → paper §4 (sector-level signal robustness on OOS)
- Day 5 WITH-NT OOS → paper §5 (mechanical confound diagnostic)
- Day 6 paper outline → reports/papers/ lane deliverable

K4 (WITH-NT mechanical confound) and K3 (sector robustness) are technically moot now that K2 has fired — there is no LAYER A LOCK to deny. But Day 5 results still anchor paper §5 commentary.

## §9 Variance-of-X family update (Phase 1 entry §7)

| Member | Pre-Phase-1 status | Post-Phase-1 status |
|---|---|---|
| F1 (FDA expectation variance) | Frozen-two-layer (sub-LAYER A) | unchanged |
| F6 (clinicaltrials amendment) | Post-pub-downgrade-tentative | unchanged |
| **RD1 Strategy A (rdq variance)** | LAYER A candidate | **paper-practical PASS** |

Family score: 0/3 LAYER A LOCKED, 1/3 paper-practical PASS. The variance-of-X-as-XS-signal weak prior (CLAUDE.md Variance-of-X family weak prior section) is confirmed — Phase 0+ §3 Bayesian prior (combined 15-22% failure compound) was within the realized range.

## §10 Hand-off to Day 5

STEP 5 (Day 5) cleared with revised scope:

- Input: `artifacts/panel_oos.parquet` (seal already broken Day 4; further reads now allowed)
- Script: `scripts/phase1_sector_nt_oos.py`
- Output: `artifacts/strategy_A_sector_oos.csv`, `artifacts/strategy_A_with_nt_oos.csv`, `.json` summaries
- Day 5 results are now informational (paper §4-§5 anchors) — they do not change the paper-practical verdict K2 fired today.

## §11 Commit pin

| Commit | Description |
|---|---|
| `fd2828f` | STEP 0: Day-0 anti-bias |
| `fa3e334` | STEP 1: IS/OOS split |
| `a7c8965` | STEP 2: IS Bonferroni-12 PASS 3/4 |
| `ce52490` | STEP 3: TC overlay IS PASS 4/4, 3 axes DEFERRED |
| TBD | STEP 4: OOS REVEAL — **K2 FIRES, paper-practical-only** |
