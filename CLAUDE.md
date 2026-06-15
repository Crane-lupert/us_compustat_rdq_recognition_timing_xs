# us_compustat_rdq_recognition_timing_xs

**ID**: RD1-merged-RD7
**Status**: **Phase 1 CLOSED — paper-practical PARTIAL** (K2 fired Day 4 OOS reveal; LAYER A LOCK denied)
**Date**: 2026-06-16
**Iter**: 22 (user-origin "WRDS fundamental data × market participant recognition timing")
**Project type (Gate G)**: methodology/discovery — `reports/papers/` lane

## Phase 1 close summary (2026-06-16)

- **Outcome**: paper-practical (Phase 1 outcome taxonomy bucket 2). Compustat-Recognition-Timing pod 1st LOCKED slot NOT CLAIMED.
- **IS Bonferroni-12 (1999-2016)**: 4/12 PASS, primary 3/4 PASS (HALT floor met).
- **OOS Bonferroni-12 (2017-2024)**: 0/12 PASS, primary 0/4 (K2 fires). 11/12 sign-correct OOS.
- **Sector OOS (Lock D §5)**: 3/4 PASS (3 high-tilt; A180-SL 5/9 FAIL).
- **K4 WITH-NT inflation ratio**: 2.0 at threshold, NOT_TRIGGERED.
- **TC overlay IS**: 4/4 above 25% K5 floor.
- **Variance-of-X family**: 1/3 paper-practical PASS (RD1 1st in family); 0/3 LAYER A LOCKED.
- **Phase 1 close audit**: `audits/2026-06-16-RD1-merged-RD7-phase1-close.md`
- **Paper outline**: `reports/papers/RD1-strategy-A-paper-outline.md`
- **Meta-harness PARTIAL report**: `D:/vscode/meta-harness/audits/2026-06-16-RD1-merged-RD7-phase1-PARTIAL-close-report.md`

## Source of truth

- Launch SPEC: `D:/vscode/meta-harness/audits/2026-06-16-RD1-merged-RD7-launch-spec.md`
- Autopilot prompt: `D:/vscode/meta-harness/audits/2026-06-16-RD1-merged-RD7-autopilot-prompt.txt`
- Stage A verify: `D:/vscode/meta-harness/audits/2026-06-16-RD1-rdq-datadate-gap-variance-xs-verify.md`
- Stage B verify: `D:/vscode/meta-harness/audits/2026-06-16-RD7-rdq-rolling-baseline-deviation-xs-verify.md`
- `.claude/settings.json` template-of-truth: `D:/vscode/meta-harness/templates/external-repo-claude-settings.template.json`

## P8 anchor corrections (5 from Stage B — MANDATORY)

| # | Correction | Status |
|---|---|---|
| 1 | **Bagnoli-Kross-Watts 2002 venue = JAR 40(5):1275-1296** (Stage A "RAST" mis-cite CORRECTED) | VERIFIED PRIMARY |
| 2 | **Bannouh-Geng-Peeters 2019 SSRN 3432446 = SSRN-only, NOT peer-reviewed** | MIS-CITED SECONDARY (motivation bridge only) |
| 3 | **Chambers-Penman 1984 JAR 22(1):21-47** added as **PRIMARY** for Strategy B | VERIFIED PRIMARY |
| 4 | **Berger-Hann 2003 JAR 41(2):163-223** secondary supporting for Chambers-Penman lineage | VERIFIED SECONDARY |
| 5 | Framing correction: "variance-of-lag / within-firm baseline deviation" extension axes vs anchor level/direction signals explicit | DOCUMENTED |

## Anchor stack (post-corrections)

- Bagnoli-Kross-Watts 2002 JAR — Strategy A PRIMARY (level-of-lag → variance extension)
- Chambers-Penman 1984 JAR — Strategy B PRIMARY (early/late deviation → return)
- Johnson-So 2018 JFQA — Strategy A + B adjacent (level/direction-of-deviation)
- Begley-Fischer 1998 RAST — Strategy B supporting (delay as bad news)
- Berger-Hann 2003 JAR — Chambers-Penman lineage secondary
- Noh-So-Verdi 2021 JFE — within-firm baseline construction validation (25.6%/yr)
- deHaan-Shevlin-Thornock 2015 JAE — secondary
- Bannouh-Geng-Peeters 2019 SSRN-only — MIS-CITED secondary (NN IP practitioner bridge only)

**Tier**: SUBSTANTIAL (Strategy A) / PARTIAL (Strategy B). See `audits/2026-06-16-RD1-merged-RD7-launch-redirect.md`.

## 2-strategy mechanism

### Strategy A — rdq-datadate gap variance XS (RD1)

Rolling 8-Q std-dev of (rdq − datadate) ↑ → erratic internal controls / disclosure-pipeline noise → forward CAR negative. Pre-reg high-variance Q5 < low-variance Q1 (long Q1 / short Q5).

`gap_var_t = std({gap_q : q ∈ trailing 8Q, ≥6 valid})`, monthly XS quintile within FF12 sector.

### Strategy B — within-firm rolling baseline deviation XS (RD7)

Current Q gap minus firm's 8-Q rolling median. Asymmetric:
- Pos deviation (rdq later than baseline) = hiding bad news → forward CAR NEG
- Neg deviation (rdq earlier than baseline) = highlighting good news → forward CAR POS

Symmetric-recoded into Q5-Q1 spread for Bonferroni-12 parity.

`gap_dev_t = gap_t − median({gap_q : q ∈ trailing 8Q})`, monthly XS quintile within FF12 sector.

## Stage 0 sub-gates (5 binding — Day-0)

| # | Sub-gate | Threshold |
|---|---|---|
| (a) | Anchor framing user-judgment | BINARY — 5 P8 corrections EXPLICIT + Bannouh SSRN-only label + Chambers-Penman JAR PRIMARY swap |
| (b) | rdq-datadate gap distribution | GRADUATED — PASS median [25,90]d + ≥70% in [10,180]d / BORDERLINE [20,100]d + ≥60% / KILL outside |
| (c) | V5 SEC Form NT differentiation 3-axis | BINARY — 3-axis table + NT-filer exclusion mandatory; NT-only Bonferroni drop ≤50% |
| (d) | RD1 vs RD7 ρ<0.85 + Lock C | BINARY — ρ<0.85 retain both; ρ≥0.85 drop Strategy B; Lock C SHA pinned |
| (e) | Bonferroni-12 ≥3/12 PASS per strategy | GRADUATED — PASS ≥3 / BORDERLINE 2 / KILL <2 |

## Bayesian prior + Rule 9

- LAYER A LOCKED prior: **~15-22% combined** (Strategy A 10-15% + Strategy B 8-12% independent failure compound).
- Rule 9 **P(fail) 40-55% MEDIUM-UPPER → LAUNCH-with-tag**. Drivers: variance-of-X 0/2 portfolio (F1+F6) / V5 NT overlap / RD1↔RD7 coupling / anchor heavy post-pub decay.
- LDS: Strategy A 5-6/7 LIVE-DEPLOYABLE / Strategy B 4/7 BORDERLINE.

## Gate G + alpha-primary lock §1.5.3 EXPLICITLY waived

- Project type = **methodology/discovery**, output lane = `reports/papers/`.
- Strategy B LDS 4/7 BORDERLINE → paper-practical primary path triggered.
- Compustat-Recognition-Timing pod: **1st LOCKED candidate** (pod currently empty).

## V5 differentiation 3-axis (mandatory)

| Axis | V5 (LAYER A LOCKED 2026-06-11) | RD1-merged-RD7 |
|---|---|---|
| Data | SEC EDGAR Form NT filings (regulatory marker, ~3K NT/yr) | Compustat `rdq` press-release date (universe-wide ~14K firm-Q/yr) |
| Design | Event-study on NT filing date | Within-firm panel + monthly XS quintile |
| Trigger | Explicit "miss deadline" — binary signed | Continuous cadence-noise / signed within-firm deviation |

**NT-filer exclusion**: drop NT-10K/NT-10Q firm-quarters from primary results (mechanical confound mitigation). ≥0.5σ deviation suspected NT-correlated.

## Operational guardrails

- **WRDS**: local dump path `E:/wrds-data-courier/output/dump/` ONLY. NO `wrds.Connection()` / `.pgpass`. Reload `D:/vscode/meta-harness/data/wrds-dump-usability-snapshot.md` if doubt.
- **LLM**: Phase 0 uses ZERO LLM. If needed, route via `D:/vscode/portfolio-coordination/shared-utils/shared_utils/openrouter_client.py`. NO direct API key lookup. NO repo-local `.env` with API keys.
- **External-API reachability**: N/A (WRDS-only); if added → Rule 7 corroboration `templates/external-api-reachability-corroboration.py`.
- **Public push gate**: NO `git push` / `gh push` (deny). Local commits only until meta-harness governance review.
- **Pipeline determinism (Lock F)**: run `bash D:/vscode/meta-harness/scripts/audit-pipeline-determinism.sh .` before Phase 0 verdict.
- **As-of manifest**: `_vendored/asof.py` + `_vendored/asof_manifest/*.json` (bootstrap-time vendored copy). `comp.fundq` datadate → rdq +32d shift empirical.
- **Sample CRSP-uniformity (Rule 10)**: Day-1 audit obligatory; sample-shape table SIC + cap + liquidity quintile vs CRSP universe.

## Data sources (WRDS REAL)

- `comp_na_daily_all.fundq` 675 MB REAL (snapshot §B row 38) — rdq + datadate + gvkey + conm
- `crsp_a_stock.dsf_v2` 4.42 GB REAL (snapshot §A modern substitute) — forward returns
- `comp_na_daily_all.names` REAL — CCM bridge fallback (`crsp_a_ccm` USAGE-blocked per U44)

## Cohort

- Universe: CRSP US-listed share code 10/11 NYSE/Nasdaq/Amex ∩ Russell 3000 ∩ Compustat coverage
- Period: 1999–2024 (25 years)
- Raw: ~350K firm-Q → ~300K post 8-Q filter → ~225K post NT-filer exclusion → 200× Bonferroni-12 floor

## Phase 0 schedule

| Day | Output |
|---|---|
| 0 | Sub-gates (a) + (c) BINARY |
| 1 | Sub-gate (b) gap distribution + CRSP-uniformity check |
| 2 | `shared_lib/rdq_panel_loader/` + sub-gate (d) ρ + Lock C SHA |
| 3-5 | Strategy A Bonferroni-12 + LDS |
| 5-7 | Strategy B Bonferroni-12 + LDS |
| 7 | Phase 0 verdict close + meta-harness auto-report |

Budget: $0-25 LLM / 2-3 day build. MERGE saves ~30-40% via `shared_lib/rdq_panel_loader/`.

## Variance-of-X family weak prior (counterweight)

- F1 (FDA expectation variance) frozen-two-layer
- F6 (clinicaltrials amendment) post-pub-downgrade-tentative
- 0/2 LAYER A LOCKED → variance-as-XS-signal weak portfolio track record
- Strategy A inherits this prior; Strategy B (within-firm baseline deviation) is direction-conditional, NOT variance-of-X — partially insulated

## Karpathy 4 + 12 principles

This repo follows `D:/vscode/meta-harness/skills/karpathy-guidelines/SKILL.md` (Think Before Coding / Simplicity First / Surgical Changes / Goal-Driven Execution) and `D:/vscode/meta-harness/docs/principles.md` 12 principles.
