REDIRECT — Launch SPEC + autopilot prompt moved to meta-harness/audits/ per 2026-05-30 governance lock.

Source-of-truth (SPEC): D:/vscode/meta-harness/audits/2026-06-16-RD1-merged-RD7-launch-spec.md
Source-of-truth (autopilot prompt): D:/vscode/meta-harness/audits/2026-06-16-RD1-merged-RD7-autopilot-prompt.txt
Source-of-truth (Stage A verify): D:/vscode/meta-harness/audits/2026-06-16-RD1-rdq-datadate-gap-variance-xs-verify.md
Source-of-truth (Stage B verify): D:/vscode/meta-harness/audits/2026-06-16-RD7-rdq-rolling-baseline-deviation-xs-verify.md

Launch ID: RD1-merged-RD7
Date: 2026-06-16
Repo: us_compustat_rdq_recognition_timing_xs
Status: Phase 0 entry — LAUNCH-with-tag MERGE 2-strategy paper-practical
Iter: 22 (user-origin theme "WRDS fundamental data × market participant recognition timing")

P8 corrections from Stage B (5 mandatory):
  1. Bagnoli-Kross-Watts 2002 venue = JAR 40(5):1275-1296 (NOT RAST)
  2. Bannouh-Geng-Peeters 2019 SSRN 3432446 = SSRN-only NOT peer-reviewed MIS-CITED secondary
  3. Chambers-Penman 1984 JAR 22(1):21-47 PRIMARY added for Strategy B
  4. Berger-Hann 2003 JAR secondary supporting added
  5. Framing corrections: variance-of-lag / within-firm baseline deviation extension axes vs anchor level/direction explicit

Tier: SUBSTANTIAL (Strategy A) / PARTIAL (Strategy B)
Bayesian prior LAYER A combined: 15-22%
Rule 9 P(fail): 40-55% MEDIUM-UPPER → LAUNCH-with-tag (autopilot WARNING header)
LDS: Strategy A 5-6/7 LIVE-DEPLOYABLE / Strategy B 4/7 BORDERLINE
Project type (Gate G): methodology/discovery → reports/papers/ lane
Alpha-primary lock §1.5.3: EXPLICITLY waived (paper-practical primary)
Pod: Compustat-Recognition-Timing 1st LOCKED candidate (currently empty)
V5 SEC Form NT differentiation: 3-axis explicit + NT-filer firm-quarter exclusion mandatory

5 Stage 0 sub-gates (Day-0 binding):
  (a) Anchor framing user-judgment BINARY
  (b) rdq-datadate gap distribution GRADUATED (PASS [25,90]d median + ≥70% in [10,180]d filter)
  (c) V5 SEC Form NT differentiation 3-axis BINARY + NT-filer exclusion
  (d) RD1↔RD7 ρ<0.85 BINARY + Lock C SHA
  (e) Bonferroni-12 ≥3/12 PASS floor GRADUATED per strategy
