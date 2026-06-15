# Lock C — RD1-merged-RD7 Direction Matrix + Bonferroni-12 Cell Structure + Sub-Gate (d) ρ

**Date**: 2026-06-16
**Step**: STEP 5 (autopilot prompt)
**Sub-gate**: (d) RD1 vs RD7 ρ<0.85 BINARY + Lock C SHA pin
**Verdict**: **PASS** — max |ρ| = 0.2578 (margin +0.5922 below 0.85 threshold). Both strategies retained.
**SHA pin (base)**: `184ca4bd8f22a5118bd41b7e41cdf08045982e0e` (Initial bootstrap, 2026-06-16)
**Immutability**: Lock C is **immutable post-Phase-0** per autopilot prompt §PROHIBITIONS.

## Sub-gate (d) ρ redundancy reconciliation

Panel basis: `artifacts/panel_post_nt_excl.parquet` — 620,290 firm-Q post NT exclusion.

| ρ flavor | Value | Threshold | Within bound? |
|---|---|---|---|
| Pearson(gap_var_t, gap_dev_t) | +0.0659 | < 0.85 | ✅ |
| Spearman(gap_var_t, gap_dev_t) | −0.0135 | < 0.85 | ✅ |
| Pearson(gap_var_t, \|gap_dev_t\|) | **+0.2578** | < 0.85 | ✅ (max) |
| Spearman(gap_var_t, \|gap_dev_t\|) | +0.1737 | < 0.85 | ✅ |

**Interpretation**:
- Near-zero raw correlation (Pearson +0.07, Spearman −0.01) confirms gap_var_t (Strategy A: 2nd moment) and gap_dev_t (Strategy B: signed deviation from rolling median) are essentially orthogonal signals.
- Moderate absolute correlation (Pearson +0.26) on |gap_dev_t| reflects the obvious mechanical link — a firm whose current gap deviates strongly from its rolling median has a noisier gap series.
- Even the worst-case axis (+0.26) is far below the 0.85 redundancy threshold. **MERGE retains both strategies.**

## Strategy A — Lock C direction matrix (variance XS)

| Component | Value | Source |
|---|---|---|
| Signal | `gap_var_t = std({gap_q : q in trailing 8Q, ≥6 valid})` | shared_lib §`rolling_8q_features` |
| Direction prior | high-variance → NEG forward CAR (erratic disclosure cadence → information-asymmetry penalty) | Bagnoli-Kross-Watts 2002 JAR PRIMARY |
| Cross-section | monthly XS quintile within FF12 sector | SPEC.md §2 Strategy A |
| Portfolio | Long Q1 (low-var) − Short Q5 (high-var) | Lock C immutable |
| Pre-registered sign | spread Q1 − Q5 > 0 | Lock C |
| LDS target | 5–6 / 7 LIVE-DEPLOYABLE | Stage A verify |

### Strategy A — Bonferroni-12 cell structure

3 horizons × 4 sub-cells = 12 cells. Threshold |t| > 2.78 + sign-correct.

| Horizon | Size-large × IndTilt-high | Size-large × IndTilt-low | Size-small × IndTilt-high | Size-small × IndTilt-low |
|---|---|---|---|---|
| 60d | A60-LH | A60-LL | A60-SH | A60-SL |
| 120d | A120-LH | A120-LL | A120-SH | A120-SL |
| 180d | A180-LH | A180-LL | A180-SH | A180-SL |

Verdict per sub-gate (e): PASS ≥3/12 / BORDERLINE 2/12 / KILL <2/12.

## Strategy B — Lock C direction matrix (within-firm baseline deviation XS)

| Component | Value | Source |
|---|---|---|
| Signal | `gap_dev_t = gap_t − median({gap_q : q in trailing 8Q, ≥6 valid})` | shared_lib §`rolling_8q_features` |
| Direction prior (asymmetric) | Pos dev (late) → NEG forward CAR; Neg dev (early) → POS forward CAR | Chambers-Penman 1984 JAR PRIMARY |
| Cross-section | monthly XS quintile within FF12 sector | SPEC.md §2 Strategy B |
| Symmetric recoding for Bonferroni-12 parity | Q5 (early, neg dev) − Q1 (late, pos dev) > 0 | Lock C immutable |
| Pre-registered sign | spread Q5 − Q1 > 0 (recoded) | Lock C |
| LDS target | 4 / 7 BORDERLINE (paper-practical OK) | Stage B verify |

### Strategy B — Bonferroni-12 cell structure

3 horizons × 4 sub-cells = 12 cells (symmetric-recoded). Threshold |t| > 2.78 + sign-correct.

| Horizon | Size-large × IndTilt-high | Size-large × IndTilt-low | Size-small × IndTilt-high | Size-small × IndTilt-low |
|---|---|---|---|---|
| 60d | B60-LH | B60-LL | B60-SH | B60-SL |
| 120d | B120-LH | B120-LL | B120-SH | B120-SL |
| 180d | B180-LH | B180-LL | B180-SH | B180-SL |

Verdict per sub-gate (e): PASS ≥3/12 / BORDERLINE 2/12 / KILL <2/12.

## Joint cell counting — explicit non-merge

Strategies A and B are **decoupled in Bonferroni cell counting**: each strategy independently satisfies (or fails) its own ≥3/12 PASS floor. The combined 24-cell count is **never** used for any verdict — per autopilot prompt §PROHIBITIONS line 8.

## NT-filer exclusion artifact pin

- Exclusion pool file: `artifacts/subgate_c_nt_proxy_exclusion_pool.csv.gz` (29,864 firm-Q)
- Exclusion criterion: `(fqtr in {1,2,3} AND gap_days > 75) OR (fqtr == 4 AND gap_days > 100)`
- All primary results (STEPS 6 and 7) use the NT-excluded panel as base.
- Sensitivity check WITH NT-filers is reported alongside primary results for the ≤50% drop sub-criterion in sub-gate (c).

## Lock F compliance affirmation

`shared_lib/rdq_panel_loader/__init__.py` observes Lock F pipeline determinism:
- Every `groupby` is preceded by `sort_values(['gvkey','datadate'], kind='mergesort')`.
- `rolling()` operates within explicitly sorted groups.
- `drop_duplicates()` in `ccm_bridge_via_names` is preceded by `sort_values('gvkey', kind='mergesort')`.
- No `groupby.agg` first/last/nth without sort. No SQL — Python only.

STEP 9 will run `D:/vscode/meta-harness/scripts/audit-pipeline-determinism.sh` to mechanically verify.

## SHA pin protocol

| Stage | SHA |
|---|---|
| Pre-Phase-0 base (Initial bootstrap) | `184ca4bd8f22a5118bd41b7e41cdf08045982e0e` |
| Lock C audit commit (this file) | TBD — pinned by post-write commit |
| Post-Phase-0 verdict commit | TBD — pinned by STEP 8 close |

Lock C content (direction matrix + cell structure + sub-gate (d) ρ) is **immutable** post the audit commit. Any subsequent revision requires a new repo branch under the meta-harness governance review.

## Output

- This audit: `audits/2026-06-16-RD1-merged-RD7-lock-c.md`
- Sub-gate (d) artifact: `artifacts/subgate_d_rho.json`
- Panel artifact: `artifacts/panel_post_nt_excl.parquet` (620,290 firm-Q)
- Script: `scripts/subgate_d_rho.py`
- Next: STEP 6 — Strategy A Bonferroni-12 + LDS empirical
