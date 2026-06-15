---
date: 2026-06-16
phase: 1
step: 0 (anti-bias self-check)
repo: us_compustat_rdq_recognition_timing_xs
project_id: RD1-merged-RD7
source_of_truth: D:/vscode/meta-harness/audits/2026-06-16-RD1-merged-RD7-phase1-autopilot-prompt.txt
---

# Phase 1 Day-0 Anti-Bias Self-Check

## §1 Purpose

Open Phase 1 with an explicit acknowledgement of the bias surface, KILL conditions, OOS-sealing protocol, and the immutability of Lock C / Lock D. This audit is the binding entry artifact for Phase 1 execution. STEP 0 of `2026-06-16-RD1-merged-RD7-phase1-autopilot-prompt.txt`.

## §2 KILL conditions internalized (Phase 1 entry §4)

I have re-read [phase1-entry.md §4](2026-06-16-RD1-merged-RD7-phase1-entry.md) and reproduce the binding conditions here. Any one trigger → paper-practical-only (no LAYER A LOCK).

| # | Condition | Trigger | Action |
|---|---|---|---|
| K1 | IS re-confirmation fails | <3/4 primary cells \|t\| > 2.78 on IS-only | Halt + diagnostics audit (do not advance to OOS) |
| K2 | OOS primary verdict ≤1/4 | <2/4 OOS cells PASS Bonferroni-12 sign-correct | paper-practical-only |
| K3 | Sector robustness fails | high-tilt: BusEq + Hlth not both PASS sign-correct OOS; low-tilt A180-SL: <6/9 sectors positive | paper-practical-only |
| K4 | WITH-NT mechanical confound | WITH-NT OOS pass count > 2× WITHOUT-NT OOS pass count | Full NT audit required, paper-practical-only |
| K5 | TC overlay strips signal | TC-adjusted spread <25% of gross | paper-practical-only |

## §3 LAYER A LOCK conditions (Phase 1 entry §5)

All six must hold to claim the Compustat-Recognition-Timing pod 1st LOCKED candidate slot.

| # | Condition | Threshold |
|---|---|---|
| L1 | IS re-confirmation | ≥3/4 \|t\| > 2.78 |
| L2 | OOS primary | ≥2/4 \|t\| > 2.78 sign-correct |
| L3 | Sector robustness | high-tilt BusEq + Hlth both positive OOS; low-tilt A180-SL ≥6/9 sectors positive |
| L4 | WITH-NT sensitivity | WITH-NT OOS pass ≤ 2× WITHOUT-NT OOS pass |
| L5 | TC-adjusted spread | ≥25% of gross |
| L6 | Phase 1 close audit | Lock-F (pipeline determinism) compliant |

## §4 Phase 1 KILL probability (revised)

**Acknowledged: KILL probability 40-50%** (revised up from Phase 0 entry's 35-45% estimate).

Drivers from Phase 0+ §3 regime stability (`phase0-plus-consolidated.md`):

1. **Per-period Bonferroni 2/12 pass — power-constrained ~90-108 month sub-samples.** Phase 0 full-period passes are statistically robust but sub-period t-stats marginally exceed 2.78. NW-12 t-stat power on ~96-month OOS partition is the binding constraint.
2. **OOS partition 2017-2024 is the weakest sub-period in Phase 0 data.** Sub-period t-stats:
   - A120-LH 2017-2024 t = 1.55 (vs Phase 0 full t = 3.74)
   - A180-LH 2017-2024 t = 1.85 (vs Phase 0 full t = 3.89)
   - A180-SL 2017-2024 t = 1.74 (vs Phase 0 full t = 3.73)
   - A120-SH 2017-2024 t = 1.86 (vs Phase 0 full t = 2.89)
   These are not Phase 1 results (the OOS partition is sealed until Day 4) — they are Phase 0 regime-stability diagnostics derived from the same partition that Phase 1 will re-test. The expected magnitudes in Lock D §4 suggest ~2.0 OOS t-stat per cell, which is below 2.78. **Pre-acknowledged: Phase 1 LAYER A LOCK probability ~50-60%; paper-practical lane probability ~95%.**
3. **WITH-NT sensitivity 56% drop TECHNICAL FLAG.** Phase 0+ flagged this as borderline mechanical confound diagnosis. Re-evaluation on OOS partition is mandatory (Day 5).

## §5 OOS sealing protocol

**The OOS partition (2017-01-01 to 2024-12-31) is sealed until Day 4.** No analysis touches OOS until IS-tuning + IS robustness extensions complete (Days 1–3).

Specifically, I will:
- Day 1: split `panel_with_returns.parquet` → `panel_is.parquet` + `panel_oos.parquet`, SHA-pin both. Build OOS subset for SHA-pin but do not read its rows.
- Days 2–3: all IS-only analysis. Any cross-check that would require OOS data is deferred to Day 4.
- Day 4: open OOS partition, run `strategy_A_bonferroni.py` verbatim (no parameter tuning, no cell re-selection), publish OOS verdict.

**Acknowledged constraints (from autopilot prompt PROHIBITIONS):**
- No OOS partition access before Day 4.
- No cell direction reversal (Lock C immutable).
- No Bonferroni-12 threshold reduction below \|t\| > 2.78.
- No sub-cell re-definition (size × ind-tilt structure fixed per Lock C).
- No Strategy A / B combined 24-cell merging.
- No Lock C revision. No Lock D revision.

## §6 Bias surface enumeration

| Bias risk | Mitigation |
|---|---|
| Look-ahead from Phase 0 sub-period t-stats biasing IS interpretation | Phase 0 sub-period stats are documented (Lock D §4); IS re-confirmation simply re-runs `strategy_A_bonferroni.py` on `panel_is.parquet` with no parameter changes. |
| Cherry-picking cells if IS shows 4/4 mixed signs | Lock D §1 pre-registers the 4 primary cells; all 4 reported regardless of IS results. |
| Reading OOS partition early to gauge feasibility | Day 1 SHA-pin pipeline produces OOS subset rows without computing any statistic; Day 4 is the binding reveal date. |
| Robustness-axis selection bias (Day 3) | All robustness axes listed in Lock D §7 are advisory; primary 4 cells are not displaced by 240d/360d/FF49/skip-week-1/TC results. |
| Sector verdict cherry-picking | Lock D §5 pre-specifies which sectors must be sign-correct positive (BusEq + Hlth for high-tilt; ≥6/9 sectors for low-tilt A180-SL). |
| WITH-NT verdict re-defining mechanical-confound bound | Lock D §6 pre-specifies the 2× ratio bound. |
| Strategy B back-door re-validation | Phase 0 verdict KILL; Strategy B is appendix-only. No Phase 1 Strategy B Bonferroni re-run. |

## §7 Outcome taxonomy (commitment)

I will close Phase 1 with one of three verdicts:

1. **LAYER A LOCKED** — all 6 conditions in §3 satisfied → Compustat-Recognition-Timing pod 1st LOCKED candidate slot claimed; auto-report to meta-harness.
2. **paper-practical** — any KILL condition fires → `reports/papers/` lane only; no pod claim; RD1 remains the family's 1st paper-practical PASS; variance-of-X family stays 0/3 LAYER A LOCKED.
3. **ABANDONED-Phase-1** — unlikely (Phase 0+ already confirmed standalone primary); only triggered by TC catastrophic or sector full failure beyond paper-practical recoverability.

No fourth verdict. No conditional escapes.

## §8 Hand-off

STEP 0 complete. STEP 1 (Day 1 — OOS lock SHA pin + IS/OOS split) is cleared to begin. Day 1 deliverables:

- `scripts/phase1_is_oos_split.py`
- `artifacts/panel_is.parquet`
- `artifacts/panel_oos.parquet` (SEALED — no reads until Day 4)
- `audits/2026-06-17-RD1-merged-RD7-phase1-day1-oos-split.md` with SHA-pin entries for both subsets.

## §9 SHA pin

| Artifact | SHA |
|---|---|
| Phase 0 close commit | `8818dd2` |
| Phase 1 entry commit | `dbc303b` (Phase 0+ robustness + Phase 1 entry: Lock D pre-reg + 3 extensions) |
| Day-0 anti-bias commit | TBD by post-write commit |
