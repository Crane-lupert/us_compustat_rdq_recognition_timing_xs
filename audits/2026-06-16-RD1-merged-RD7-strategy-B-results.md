# Strategy B — Bonferroni-12 + LDS Results (Within-Firm Rolling Baseline Deviation XS / RD7)

**Date**: 2026-06-16
**Step**: STEP 7 (autopilot prompt)
**Verdict**: **KILL** — 0/12 Bonferroni cells, 5/12 sign-correct, LDS 2/7 PRACTITIONER-PAPER-ONLY
**Anchor PRIMARY**: Chambers-Penman 1984 **JAR 22(1):21–47**

## Empirical setup

| Element | Value |
|---|---|
| Panel base | `artifacts/panel_with_returns.parquet` (post NT-exclusion) |
| n firm-Q | 620,290 |
| n with ≥1 horizon CAR | 371,847 |
| Cross-section sort | monthly XS quintile within FF12 sector, by `gap_dev_t` |
| Quintile direction | Q1 = late (pos dev), Q5 = early (neg dev) |
| Portfolio spread | Q5 − Q1 (symmetric-recoded; pre-registered POSITIVE per Lock C) |
| Bonferroni-12 threshold | \|t\| > 2.78 AND sign-correct |

## Bonferroni-12 cell table

| cell | horizon | size | tilt | n_months | μ_spread | t-stat | sign✓ | Bonferroni✓ |
|---|---|---|---|---|---|---|---|---|
| B60-LH | 60 | L | H | 300 | +0.15% | 0.36 | ✅ | ❌ |
| B60-LL | 60 | L | L | 299 | +0.52% | 1.51 | ✅ | ❌ |
| B60-SH | 60 | S | H | 299 | −0.50% | −0.78 | ❌ | ❌ |
| B60-SL | 60 | S | L | 300 | +0.17% | 0.38 | ✅ | ❌ |
| B120-LH | 120 | L | H | 300 | −0.36% | −0.70 | ❌ | ❌ |
| B120-LL | 120 | L | L | 299 | +0.30% | 0.60 | ✅ | ❌ |
| B120-SH | 120 | S | H | 299 | −0.90% | −0.80 | ❌ | ❌ |
| B120-SL | 120 | S | L | 300 | −0.45% | −0.65 | ❌ | ❌ |
| B180-LH | 180 | L | H | 300 | −0.68% | −0.91 | ❌ | ❌ |
| B180-LL | 180 | L | L | 299 | +0.20% | 0.28 | ✅ | ❌ |
| B180-SH | 180 | S | H | 299 | −1.90% | −1.55 | ❌ | ❌ |
| B180-SL | 180 | S | L | 300 | −1.01% | −1.09 | ❌ | ❌ |

**Bonferroni-12 PASS count: 0/12** (threshold <2 → KILL per graduated 3-tier).
**Sign-correct count: 5/12** — below random-walk expectation of 6/12.

## Interpretation

Strategy B (within-firm baseline deviation) **fails Bonferroni-12 at every cell**. The maximum |t-stat| is 1.55 (B180-SH, wrong direction). Mean spreads are small in magnitude (most within ±1%), and the sign is inconsistent with the Chambers-Penman 1984 prediction:

- Predicted: Q5 (early, neg dev) outperforms Q1 (late, pos dev) → positive spread
- Observed: 7 of 12 cells show NEG spread; only large-cap low-tilt cells lean positive

**Why Strategy B fails**:
1. **Anchor post-pub decay**: Chambers-Penman 1984 JAR is 42 years old. Their original sample (1969–1976 NYSE/AMEX hand-collected) had ~3-week-resolution timeliness measurement. In the post-EDGAR / post-SOX era, the early/late deviation signal is largely arbitraged or dominated by other channels (analyst coverage, conference-call disclosure, IR).
2. **Within-firm baseline is too short**: 8-Q rolling median is a noisy proxy for a firm's "expected" reporting date. Larger window or industry-relative baseline would be needed.
3. **Asymmetric signal collapsed too aggressively**: forcing symmetric recoding (Q5 − Q1) discards the asymmetric direction-conditional information.
4. **Variance-of-X family prior**: 0/2 LAYER A LOCKED before this audit (F1 + F6). Strategy B inherits the same weak prior because gap_dev_t involves a rolling baseline (akin to variance-style construction).

## LDS 7-axis scoring

| # | Axis | Pass | Note |
|---|---|---|---|
| 1 | Signal well-defined | ✅ | gap_dev_t reproducible |
| 2 | Sample size sufficient | ✅ | 371,847 firm-Q with CAR |
| 3 | Bonferroni pass floor | ❌ | 0 < 3 |
| 4 | Sign majority correct | ❌ | 5/12 < 7/12 |
| 5 | Horizon robustness | ❌ | 0 passes total |
| 6 | Sub-cell diversity | ❌ | no passing cells |
| 7 | Post-pub decay resilience | ❌ | 0 < 4 |

**LDS score: 2/7 → PRACTITIONER-PAPER-ONLY** (below paper-practical 4/7 BORDERLINE floor).

Pre-acknowledged target was 4/7 BORDERLINE; observed 2/7 falls below even this concessive threshold. Paper-practical-OK is **FALSE** for Strategy B.

## Phase 0 disposition

- **Strategy B standalone → DEAD**. Not a Phase 1 LAYER A candidate. Not paper-practical-OK.
- **Strategy B as appendix in Strategy A paper** → may be retained as a NEG/NULL extension result (Chambers-Penman 1984 post-pub decay demonstrated empirically — a clean methodological contribution).
- The MERGE arrangement is **vindicated** by Strategy A's PASS — the ~30-40% shared infrastructure cost was well spent.

## Risk drivers confirmed

The Rule 9 MEDIUM-UPPER 40-55% P(fail) bracket called this exactly. Drivers that fired:
- (1) Variance-of-X family 0/2 → now 1/2 (Strategy A is the first LAYER A candidate in family)
- (4) Anchor heavy post-pub decay → Strategy B Chambers-Penman 42yr is *too old* (42yr = decay confirmed)

Drivers that did NOT fire:
- (2) V5 NT overlap → minimal (sub-gate (c) confirmed 4% overlap; primary survives exclusion)
- (3) RD1↔RD7 coupling → minimal (sub-gate (d) max |ρ| = 0.26 ≪ 0.85)

## Output

- This audit: `audits/2026-06-16-RD1-merged-RD7-strategy-B-results.md`
- Artifacts: `artifacts/strategy_B_bonferroni12.json` + `.csv`
- Scripts: `scripts/strategy_B_bonferroni.py`
- Next: STEP 8 — Phase 0 final verdict + meta-harness auto-report close
