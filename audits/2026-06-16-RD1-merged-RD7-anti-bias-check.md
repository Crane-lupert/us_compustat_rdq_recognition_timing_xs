# Anti-Bias Self-Check — RD1-merged-RD7 us_compustat_rdq_recognition_timing_xs

**Date**: 2026-06-16
**Step**: STEP 0 (autopilot prompt)
**Repo**: D:/vscode/us_compustat_rdq_recognition_timing_xs/
**Status**: Phase 0 entry — LAUNCH-with-tag MERGE 2-strategy paper-practical
**Project type (Gate G)**: methodology/discovery — `reports/papers/` lane

## Bayesian prior LAYER A LOCKED — combined 15–22%

| Component | Prior P(success) | Source |
|---|---|---|
| Strategy A — rdq-datadate gap variance XS (RD1) | 10–15% | Stage A verify §Prior |
| Strategy B — within-firm rolling baseline deviation XS (RD7) | 8–12% | Stage B verify §Prior |
| Combined (independent failure compound) | **15–22%** | Launch SPEC §0 + CLAUDE.md §Bayesian |

**Independence justification**: ρ(gap_var, gap_dev) < 0.85 retain hypothesis (sub-gate (d) BINARY); empirical confirmation Day-2. If ρ ≥ 0.85, drop Strategy B and combined collapses to A-only 10–15%.

## Rule 9 P(fail) bracket — 40–55% MEDIUM-UPPER

Drivers (cross-referenced against CLAUDE.md §Risks):

| # | Driver | Magnitude |
|---|---|---|
| (1) | **Variance-of-X family 0/2 LAYER A LOCKED**: F1 (FDA expectation variance) frozen-two-layer + F6 (clinicaltrials amendment) post-pub-downgrade-tentative. Strategy A inherits this prior. | HIGH |
| (2) | **V5 NT-filer overlap risk**: SEC Form NT regulatory marker LAYER A LOCKED 2026-06-11. Continuous `rdq` cadence may statistically overlap NT-filer firm-quarter tail. NT-only Bonferroni drop ≤50% threshold sub-gate (c). | HIGH |
| (3) | **RD1↔RD7 MERGE coupling**: gap_var_t and gap_dev_t both derive from trailing 8-Q gap series. Bonferroni-12 PASS per strategy decoupling rests on ρ<0.85 (sub-gate (d) BINARY). | MEDIUM |
| (4) | **Anchor heavy post-pub decay**: Chambers-Penman 1984 (42yr) + Bagnoli-Kross-Watts 2002 (24yr) + Johnson-So 2018 (8yr). Strategy B LDS 4/7 BORDERLINE pre-acknowledged. | MEDIUM |

P(fail) 40–55% < 70% LAUNCH-with-tag threshold (per Rule 9) → autopilot WARNING header attached, ABANDONED-pre-Phase0 at sub-gates (a)/(b)/(c)/(d)/(e) is EXPECTED outcome.

## Gate G methodology/discovery — alpha-primary lock §1.5.3 EXPLICITLY waived

- Output lane = `reports/papers/` (paper-practical primary)
- Alpha-secondary defer permitted (Strategy B LDS 4/7 BORDERLINE)
- Compustat-Recognition-Timing pod 1st LOCKED candidate (currently empty)

## 5 P8 corrections from Stage B (MANDATORY)

1. **Bagnoli-Kross-Watts 2002** venue = JAR 40(5):1275–1296 (Stage A "RAST" mis-cite CORRECTED) — VERIFIED PRIMARY
2. **Bannouh-Geng-Peeters 2019 SSRN 3432446** = SSRN-only NOT peer-reviewed — MIS-CITED SECONDARY (motivation bridge only)
3. **Chambers-Penman 1984 JAR 22(1):21–47** added as PRIMARY for Strategy B — VERIFIED PRIMARY
4. **Berger-Hann 2003 JAR 41(2):163–223** secondary supporting for Chambers-Penman lineage — VERIFIED SECONDARY
5. Framing correction: "variance-of-lag / within-firm baseline deviation" extension axes vs anchor level/direction signals — DOCUMENTED

## Internal-bias declaration

I declare no internal bias toward LAUNCH-with-tag completion. ABANDONED-pre-Phase0 at any sub-gate (a)/(b)/(c)/(d)/(e) is a fully acceptable Phase 0 outcome. Specifically:

- Sub-gate (a) BINARY: if user judges anchor framing insufficient → ABANDONED + reusable-assets §5 audit
- Sub-gate (b) GRADUATED: if median outside [20,100]d or <60% in [10,180]d filter → ABANDONED
- Sub-gate (c) BINARY: if NT-filer Bonferroni drop >50% → MERGE-into-V5 + ABANDONED standalone
- Sub-gate (d) BINARY: if ρ ≥ 0.85 → drop Strategy B, retain Strategy A only (repo continues but reduced)
- Sub-gate (e) GRADUATED: if both strategies KILL → ABANDONED-pre-Phase0

I will not bias toward PASS or BORDERLINE because of MERGE-launch sunk cost. Each sub-gate is judged independently against pre-registered thresholds.

## Prohibitions affirmed (autopilot prompt §PROHIBITIONS)

- [x] no `wrds.Connection()` / `.pgpass` — local `E:/wrds-data-courier/output/dump/*.csv.gz` only
- [x] no direct OpenRouter/Anthropic/OpenAI API key lookup (Phase 0 = ZERO LLM)
- [x] no HARD KILL fire on urllib non-200 alone (N/A — no external API this repo)
- [x] no external-data PAID tier auto-fallback (N/A — WRDS-only)
- [x] no `git push` / `gh push` (deny) — local commits only
- [x] no Strategy A/B Bonferroni cell merging (24 combined) — decoupled per-strategy 12 each
- [x] no NT-filer firm-quarter in primary results — V5 confound mitigation mandatory
- [x] no Lock C revision post-Phase-0 — direction matrix immutable pre-Phase-0

## Output

- This audit: `audits/2026-06-16-RD1-merged-RD7-anti-bias-check.md`
- Next step: STEP 1 — Sub-gate (a) anchor framing user-judgment BINARY Day-0
