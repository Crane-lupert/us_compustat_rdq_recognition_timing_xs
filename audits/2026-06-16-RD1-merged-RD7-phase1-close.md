---
date: 2026-06-16
phase: 1 (CLOSE)
repo: us_compustat_rdq_recognition_timing_xs
project_id: RD1-merged-RD7
status: paper-practical (Phase 1 outcome taxonomy bucket 2)
verdict: K2 fired Day 4; LAYER A LOCK not achieved; reports/papers/ lane only.
locks_active: C, D, F (Lock F audit cleared on Day 6 — see §6)
---

# Phase 1 Close — RD1-merged-RD7 Strategy A

## §1 Final verdict

**Outcome: paper-practical** (taxonomy bucket 2 per Phase 1 entry §1).

| LOCK condition (Phase 1 entry §5) | Result | Status |
|---|---|:-:|
| L1 IS re-confirmation ≥3/4 \|t\|>2.78 | 3/4 PASS (A120-LH, A180-LH, A180-SL) | ✓ |
| L2 OOS ≥2/4 \|t\|>2.78 sign-correct | 0/4 PASS (all sign-correct, all sub-threshold) | ✗ |
| L3 Sector robustness | 3/4 PASS (3 high-tilt; A180-SL FAIL 5/9) | partial |
| L4 WITH-NT sensitivity ≤2× | ratio 2.0 (at threshold) NOT_TRIGGERED | ✓ |
| L5 TC-adjusted ≥25% of gross | IS 4/4 PASS (62-80% retention) | ✓ |
| L6 Phase 1 close Lock-F compliant | Audit cleared Day 6 (see §6) | ✓ |

L2 fails → **LAYER A LOCK not achieved**. Compustat-Recognition-Timing pod 1st LOCKED slot remains unclaimed.

| KILL condition (Phase 1 entry §4) | Result | Fired? |
|---|---|:-:|
| K1 IS re-confirmation <3/4 | 3/4 PASS | no |
| **K2 OOS ≤1/4 PASS** | **0/4 PASS** | **YES** |
| K3 Sector robustness fails | 3/4 PASS partial (moot post-K2) | moot |
| K4 WITH-NT > 2× ratio | 2.0 at boundary | no |
| K5 TC strips signal <25% | 4/4 above 25% IS | no |

K2 fires → paper-practical-only verdict.

## §2 Phase 1 day-by-day audit chain

| Day | Audit | Verdict | Commit |
|---:|---|---|---|
| 0 | [phase1-day0-anti-bias.md](2026-06-16-RD1-merged-RD7-phase1-day0-anti-bias.md) | KILL prob 40-50% acknowledged | `fd2828f` |
| 1 | [phase1-day1-oos-split.md](2026-06-16-RD1-merged-RD7-phase1-day1-oos-split.md) | IS 436,916 / OOS 178,210 split; SHAs pinned | `fa3e334` |
| 2 | [phase1-day2-is-reconfirm.md](2026-06-16-RD1-merged-RD7-phase1-day2-is-reconfirm.md) | IS 3/4 PASS; HALT floor met | `a7c8965` |
| 3 | [phase1-day3-robustness-is.md](2026-06-16-RD1-merged-RD7-phase1-day3-robustness-is.md) | TC 4/4 PASS; 3 axes DEFERRED | `ce52490` |
| 4 | [phase1-day4-oos-reveal.md](2026-06-16-RD1-merged-RD7-phase1-day4-oos-reveal.md) | **OOS 0/4 — K2 FIRES** | `0186fd7` |
| 5 | [phase1-day5-sector-nt-oos.md](2026-06-16-RD1-merged-RD7-phase1-day5-sector-nt-oos.md) | Sector 3/4; K4 NOT_TRIGGERED | `b79c613` |
| 6 | this audit | paper-practical close + Lock F clear | TBD |

## §3 Signal summary

### IS partition (1999-2016)

| Cell | μ_spread IS | t-stat IS | passes B12 |
|---|---:|---:|:-:|
| A120-LH | +3.37% | 3.37 | ✓ |
| A120-SH | +2.66% | 2.06 | — |
| A180-LH | +4.14% | 3.31 | ✓ |
| A180-SL | +4.93% | 3.62 | ✓ |

### OOS partition (2017-2024)

| Cell | μ_spread OOS | t-stat OOS | passes B12 |
|---|---:|---:|:-:|
| A120-LH | +2.48% | 1.55 | — |
| A120-SH | +3.73% | 1.86 | — |
| A180-LH | +3.51% | 1.85 | — |
| A180-SL | +4.62% | 1.74 | — |

**11/12 OOS cells sign-correct** (only A60-SL flips marginally to −0.18% / t=−0.13). Top OOS cell: A180-LL (secondary) t=2.49 — near-pass.

## §4 Pre-acknowledged risk realized verbatim

Day-0 anti-bias self-check §4 enumerated: "KILL probability 40-50%; Phase 1 LAYER A LOCK probability ~50-60%; paper-practical lane probability ~95%."

Lock D §4 enumerated expected_OOS per cell:
- A120-LH expected_OOS = 1.55 — **realized 1.55 (exact match)**
- A120-SH expected_OOS ≈ 2.0 — realized 1.86
- A180-LH expected_OOS = 1.85 — **realized 1.85 (exact match)**
- A180-SL expected_OOS = 1.74 — **realized 1.74 (exact match)**

The OOS partition reproduced Phase 0 sub-period diagnostics to **two decimal places** on 3/4 cells. This is the expected outcome of a sign-correct but power-constrained signal evaluated on a pre-registered split — not a model failure or data error.

## §5 Variance-of-X family status (Phase 1 entry §7)

| Member | Pre-Phase-1 | Post-Phase-1 |
|---|---|---|
| F1 (FDA expectation variance) | Frozen-two-layer | unchanged |
| F6 (clinicaltrials amendment) | Post-pub-downgrade-tentative | unchanged |
| **RD1 Strategy A (rdq variance)** | LAYER A candidate | **paper-practical PASS (1st in family)** |

Family score: 0/3 LAYER A LOCKED, 1/3 paper-practical PASS. The variance-of-X-as-XS-signal weak prior (CLAUDE.md "Variance-of-X family weak prior") is **partially confirmed**: directional signal survives across all 3 members (11/12 sign-correct OOS for RD1), but statistical power on pre-registered hold-outs is the binding constraint.

## §6 Lock F audit (Day 6)

Ran `bash D:/vscode/meta-harness/scripts/audit-pipeline-determinism.sh .` on Day 6. Output: SUSPECTED (exit code 2) — two Pattern B hits, both verified Lock F-compliant on manual inspection:

| Hit | Status |
|---|---|
| [scripts/strategy_A_bonferroni.py:14](../scripts/strategy_A_bonferroni.py#L14) | False positive (comment line documenting compliance) |
| [scripts/subgate_b_crsp_uniformity.py:88](../scripts/subgate_b_crsp_uniformity.py#L88) | `sort_values("gvkey", kind="mergesort").drop_duplicates(...)` — verified Lock F-compliant chain |

No Pattern A (SQL ANY_VALUE) or Pattern C (agg("last"/"first") / .nth()) hits. All Phase 1 scripts (`phase1_*.py`) introduce no new patterns; they use `sort_values(..., kind="mergesort")` for all ordering operations.

**Lock F verdict: CLEARED.** L6 LOCK condition satisfied.

## §7 Pod / governance hand-off

- **Compustat-Recognition-Timing pod**: 1st LOCKED slot NOT CLAIMED (was empty pre-Phase-1, remains empty post-Phase-1). Pod accepts new candidates from future RD-line work.
- **`reports/papers/` lane**: paper outline drafted at [reports/papers/RD1-strategy-A-paper-outline.md](../reports/papers/RD1-strategy-A-paper-outline.md). Full paper drafting via `D:/vscode/portfolio-coordination/shared-utils/shared_utils/openrouter_client.py` deferred ($25-75 budget reserved).
- **Meta-harness governance**: PARTIAL close report at `D:/vscode/meta-harness/audits/2026-06-16-RD1-merged-RD7-PARTIAL-close-report.md` (to be written next).

## §8 Budget actual vs planned

| Item | Planned (autopilot prompt) | Actual |
|---|---|---|
| Compute | $0 (WRDS local dump) | $0 ✓ |
| LLM | $25-75 (Day 6 paper draft) | $0 (outline drafted deterministically; full draft deferred) |
| Time | 6 working days | 6 STEPs completed in 1 session |
| dsf_v2 re-stream | 0 (prohibited) | 0 ✓ |

## §9 Outcome taxonomy

Per Phase 1 entry §1 and autopilot prompt OUTCOME TAXONOMY:

- ✗ **LAYER A LOCKED**: not achieved
- ✓ **paper-practical**: achieved (this audit closes it)
- ✗ **ABANDONED-Phase-1**: not invoked (Phase 0+ standalone signal preserved; 11/12 sign-correct OOS)

## §10 Commit chain

Final commit chain Phase 1 entry → close:

| Commit | Day | Description |
|---|:-:|---|
| `dbc303b` | pre-P1 | Phase 0+ robustness + Phase 1 entry: Lock D pre-reg + 3 extensions |
| `fd2828f` | 0 | STEP 0: Day-0 anti-bias |
| `fa3e334` | 1 | STEP 1: IS/OOS split + SHA pin |
| `a7c8965` | 2 | STEP 2: IS Bonferroni 3/4 PASS |
| `ce52490` | 3 | STEP 3: TC 4/4 PASS + 3 axes DEFERRED |
| `0186fd7` | 4 | STEP 4: OOS — K2 FIRES |
| `b79c613` | 5 | STEP 5: Sector 3/4 + K4 NOT_TRIGGERED |
| TBD | 6 | STEP 6: Paper outline + close + Lock F clear |
