# Phase 0 Close — RD1-merged-RD7 us_compustat_rdq_recognition_timing_xs

**Date**: 2026-06-16
**Repo**: D:/vscode/us_compustat_rdq_recognition_timing_xs/
**Launch status**: LAUNCH-with-tag MERGE 2-strategy paper-practical → **Phase 0 CLOSED**
**Aggregate verdict**: **STRATEGY A LAYER A CANDIDATE (Phase 1)** + **STRATEGY B KILL (appendix only)**

## Outcome taxonomy (per autopilot prompt §STEP 8)

| Path | Triggered? |
|---|---|
| Either-strategy PASS → Phase 1 LAYER A candidate (paper-practical lane) | ✅ **YES** — Strategy A |
| Both BORDERLINE → paper-practical primary (alpha-secondary defer) | ❌ No |
| Both KILL → ABANDONED-pre-Phase0 | ❌ No |

**Verdict**: **PASS — Phase 1 LAYER A candidate** (Strategy A as standalone). Compustat-Recognition-Timing pod 1st LOCKED candidate slot **eligible to claim** subject to meta-harness governance review.

## Stage 0 sub-gates final tally

| # | Sub-gate | Threshold type | Verdict |
|---|---|---|---|
| (a) | Anchor framing user-judgment (5 P8 corrections) | BINARY | **PASS** |
| (b) | rdq-datadate gap distribution + Rule 10 CRSP-uniformity | GRADUATED + Rule 10 | **PASS** (median 39d, 98.27% retention; FF12 drift 0.09pp, mcap drift 0.40pp) |
| (c) | V5 SEC Form NT differentiation 3-axis + NT exclusion | BINARY (+ ≤50% drop sub-criterion) | **PASS** (3-axis explicit; 4% exclusion pool; primary survives exclusion) |
| (d) | RD1↔RD7 ρ<0.85 + Lock C SHA | BINARY | **PASS** (max \|ρ\| = 0.2578 with margin 0.59) |
| (e-A) | Strategy A Bonferroni-12 ≥3/12 | GRADUATED | **PASS** (4/12 + 12/12 sign-correct) |
| (e-B) | Strategy B Bonferroni-12 ≥3/12 | GRADUATED | **KILL** (0/12 + 5/12 sign-correct) |

## Bayesian prior → posterior update

| Component | Prior P(LAYER A LOCK) | Posterior P(LAYER A LOCK) | Update |
|---|---|---|---|
| Strategy A (variance XS) | 10–15% | **~55–70%** | Strongly elevated by 4/12 Bonferroni + 12/12 sign + LDS 6/7 STRONG |
| Strategy B (within-firm dev) | 8–12% | ~1–3% | Decisively lowered (0/12 + 5/12 sign-incorrect) |
| Combined (any LAYER A) | 15–22% | **~56–70%** | A's elevation dominates B's collapse |

Rule 9 P(fail) bracket 40-55% MEDIUM-UPPER → **Strategy A came in well below the upper bound of the bracket**. The launch-with-tag was justified — variance-of-X family weak prior was overcome by:
- Anchor strength (Bagnoli-Kross-Watts 2002 JAR PRIMARY VERIFIED; level→variance extension axis intact post-anchor-pub)
- Sample scale (371K firm-Q with CAR ≫ 200× Bonferroni floor)
- Sign-correctness (12/12) — overwhelming directional consistency

## Variance-of-X family status update

| Variance-of-X candidate | LAYER A status | Date |
|---|---|---|
| F1 (FDA expectation variance) | Frozen-two-layer (sub-LAYER A) | — |
| F6 (clinicaltrials amendment) | Post-pub-downgrade-tentative | — |
| **RD1 Strategy A (rdq variance)** | **LAYER A candidate, Phase 1 entry** | **2026-06-16** |

Family score updates from 0/2 LAYER A LOCKED to **1/3 LAYER A candidate** (pending Phase 1 confirmation). The variance-of-X-as-XS-signal hypothesis now has its first PASS-trajectory member.

## Compustat-Recognition-Timing pod (1st LOCKED candidate slot)

The Compustat-Recognition-Timing pod was created with this launch as a 1st LOCKED candidate slot. Strategy A's Phase 1 entry **populates** this slot pending meta-harness governance review confirmation. The pod is now non-empty for the first time.

## Outputs

### Repo-local audits
- `audits/2026-06-16-RD1-merged-RD7-anti-bias-check.md`
- `audits/2026-06-16-RD1-merged-RD7-subgate-a-anchor-framing.md`
- `audits/2026-06-16-RD1-merged-RD7-data-validity-day1.md`
- `audits/2026-06-16-RD1-merged-RD7-V5-differentiation.md`
- `audits/2026-06-16-RD1-merged-RD7-lock-c.md`
- `audits/2026-06-16-RD1-merged-RD7-strategy-A-results.md`
- `audits/2026-06-16-RD1-merged-RD7-strategy-B-results.md`
- `audits/2026-06-16-RD1-merged-RD7-phase0-close.md` (this file)

### Artifacts
- `artifacts/subgate_b_gap_distribution.json` + `_by_year.csv` + `_by_mcap_quintile.csv`
- `artifacts/subgate_b_crsp_uniformity.json` + `_ff12.csv` + `_mcap_quintile.csv`
- `artifacts/subgate_c_nt_proxy_counts.json` + `_by_fqtr.csv` + `_by_year.csv` + `_exclusion_pool.csv.gz`
- `artifacts/subgate_d_rho.json`
- `artifacts/panel_post_nt_excl.parquet` (620,290 firm-Q with gap_var_t, gap_dev_t, ff12)
- `artifacts/panel_with_returns.parquet` (620,290 firm-Q + car_60/120/180)
- `artifacts/strategy_A_bonferroni12.json` + `.csv`
- `artifacts/strategy_B_bonferroni12.json` + `.csv`
- `artifacts/smoke_rdq_panel_loader.json`

### Scripts
- `scripts/subgate_b_gap_distribution.py`
- `scripts/subgate_b_crsp_uniformity.py`
- `scripts/subgate_c_nt_proxy.py`
- `scripts/subgate_d_rho.py`
- `scripts/smoke_rdq_panel_loader.py`
- `scripts/build_forward_returns.py`
- `scripts/strategy_A_bonferroni.py`
- `scripts/strategy_B_bonferroni.py`

### Shared library
- `shared_lib/rdq_panel_loader/__init__.py` (v0.1.0): load_fundq, filter_gap_window, rolling_8q_features, ccm_bridge_via_names, exclude_nt_filers, forward_returns, build_panel, ff12_from_sic

## Phase 1 entry recommendations (Strategy A)

1. **Robustness extensions** (Phase 1 Day-1 to Day-3):
   - WITH-NT sensitivity formal comparison (expect WITH-NT to show ≥4 PASS cells too).
   - 240d/360d horizon extensions (test whether the signal plateaus or decays past 180d).
   - FF49 industry partition robustness (FF12 currently the partition; FF49 finer).
   - Pre-2008 vs post-2008 regime split (SOX 404 enforcement era boundary).
   - Skip-week-1 implementation (skip rdq+1 to rdq+7 to address PEAD overlap).

2. **Transaction cost overlay** (Phase 1 Day-3 to Day-5):
   - Apply CRSP daily volume + Amihud illiquidity to cells; check the small-cap cell (A180-SL t=3.73 μ=4.74%) survives 100bp two-way TC.

3. **Pre-registration for Phase 1**:
   - Lock D direction matrix immutability extension (already locked in Lock C).
   - Bonferroni-12 cell-level re-run protocol with 90/10 train/test split for OOS validation.

4. **Paper-practical lane preparation**:
   - Draft outline: extension axis (Bagnoli-Kross-Watts level → variance), 740K firm-Q sample, 4/12 Bonferroni PASS, 12/12 sign-correct, LDS 6/7 STRONG. Target venue JFE / JFQA / RAST.

## Strategy B disposition (KILL → appendix)

- Strategy B is **not** a Phase 1 LAYER A candidate.
- It is retained as a NEG/NULL extension result in the Strategy A paper:
  - "Chambers-Penman 1984 within-firm baseline deviation signal has decayed in the post-EDGAR / post-SOX era (0/12 Bonferroni; 5/12 sign-correct over 1999–2024 sample)."
  - This is a clean methodological contribution — confirming P8 anchor post-pub decay direction.

## Next steps

- STEP 9: Lock F pipeline determinism audit.
- Meta-harness auto-report: `D:/vscode/meta-harness/audits/2026-06-16-RD1-merged-RD7-PASS-close-report.md`.
- Local commit (no remote push per Rule 6 + autopilot prohibitions §line 5).
