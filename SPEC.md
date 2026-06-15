# SPEC — us_compustat_rdq_recognition_timing_xs (RD1-merged-RD7)

This is an abbreviated repo-local SPEC. Source of truth = meta-harness audit.

**Authoritative SPEC**: `D:/vscode/meta-harness/audits/2026-06-16-RD1-merged-RD7-launch-spec.md`

**Date**: 2026-06-16
**Status**: Phase 0 entry — LAUNCH-with-tag MERGE 2-strategy paper-practical
**Project type (Gate G)**: methodology/discovery — `reports/papers/` lane
**Alpha-primary lock §1.5.3**: EXPLICITLY waived (paper-practical primary)

## §0 Change Manifest (P1/P2/P3 lock numbers — see meta-harness SPEC §0)

| Lock key | Value |
|---|---|
| Bonferroni-N per strategy | 12 |
| Bonferroni threshold | \|t\| > 2.78 |
| PASS floor cells per strategy | ≥3/12 (graduated 0.7× BORDERLINE 2/12, KILL <2) |
| ρ redundancy KILL threshold | 0.85 |
| Gap filter window (days) | [10, 180] |
| Rolling baseline window (quarters) | 8 |
| Min valid rdq in window | 6 |
| Gap distribution PASS median range (days) | [25, 90] |
| Gap distribution filter yield floor | 0.70 |
| NT-filer exclusion KILL threshold | Bonferroni drop > 50% |
| Sample target firm-Q | ~300,000 (200× floor) |
| Strategy A LDS axes pass | 5-6 / 7 |
| Strategy B LDS axes pass | 4 / 7 BORDERLINE |
| Bayesian prior LAYER A combined | 15-22% |
| Rule 9 P(fail) bracket | 40-55% MEDIUM-UPPER |

## §0.3 Data-validity HARD KILL — `RD1-merged-RD7-11`

5 sub-gates: see meta-harness SPEC §0.3.
- (a) Anchor framing user-judgment BINARY Day-0
- (b) rdq-datadate gap distribution GRADUATED
- (c) V5 SEC Form NT 3-axis BINARY + NT-filer exclusion
- (d) RD1↔RD7 ρ<0.85 BINARY + Lock C SHA pin
- (e) Bonferroni-12 ≥3/12 PASS per strategy GRADUATED

## §1 Data (WRDS local dump REAL)

- `comp_na_daily_all.fundq` 675 MB REAL (§B row 38)
- `crsp_a_stock.dsf_v2` 4.42 GB REAL (§A)
- `comp_na_daily_all.names` REAL — CCM fallback

## §2 2-strategy mechanism + Lock C

### Strategy A — rdq-datadate gap variance XS

`gap_var_t = std({gap_q : q ∈ trailing 8Q, ≥6 valid})`. Monthly XS quintile FF12.

Direction Lock C: Q1 (low-var) – Q5 (high-var) > 0 (high-var = NEG forward CAR).

### Strategy B — within-firm rolling baseline deviation XS

`gap_dev_t = gap_t − median({gap_q : q ∈ trailing 8Q})`. Monthly XS quintile FF12.

Direction Lock C: Q5 (early, neg dev) – Q1 (late, pos dev) > 0 spread.

## §3 Cohort

CRSP US-listed (sh code 10/11, NYSE/Nasdaq/Amex) ∩ Russell 3000 ∩ Compustat 1999-2024.

~350K firm-Q raw → ~300K post 8-Q filter → ~225K post NT-filer exclusion.

## §4 Anchors

- Bagnoli-Kross-Watts 2002 **JAR 40(5):1275-1296** (NOT RAST) — Strategy A PRIMARY
- Chambers-Penman 1984 **JAR 22(1):21-47** — Strategy B PRIMARY
- Johnson-So 2018 JFQA — adjacent
- Begley-Fischer 1998 RAST — supporting
- Berger-Hann 2003 JAR — secondary supporting
- Noh-So-Verdi 2021 JFE — within-firm baseline validation
- deHaan-Shevlin-Thornock 2015 JAE — secondary
- Bannouh-Geng-Peeters 2019 SSRN-only MIS-CITED secondary

## §5 Bootstrap manifest

- `.claude/settings.json` = template drop-in copy (Rule 11)
- `_vendored/asof.py` + `_vendored/asof_manifest/` synced
- `experiments/strategy_A_variance_xs/` + `experiments/strategy_B_within_firm_rolling_baseline_xs/`
- `shared_lib/rdq_panel_loader/` (saves ~30-40% Phase 0 build cost)

## §6 Phase 0 schedule

Day 0-7 per meta-harness SPEC §6. Budget $0-25 LLM, 2-3 day build.
