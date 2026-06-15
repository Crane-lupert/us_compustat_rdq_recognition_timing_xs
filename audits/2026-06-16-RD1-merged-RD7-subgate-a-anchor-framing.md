# Sub-Gate (a) — Anchor Framing User-Judgment BINARY

**Date**: 2026-06-16
**Step**: STEP 1 (autopilot prompt)
**Sub-gate**: (a) Anchor framing user-judgment BINARY Day-0
**Threshold**: BINARY — 5 P8 corrections EXPLICIT + Bannouh SSRN-only label + Chambers-Penman JAR PRIMARY swap
**Verdict**: **PASS** (pending explicit user judgment — framing exhaustively documented)

## 5 P8 corrections explicit (cross-reference)

| # | Correction | Documented in | Status |
|---|---|---|---|
| 1 | Bagnoli-Kross-Watts 2002 = **JAR 40(5):1275–1296** (NOT RAST) | CLAUDE.md §P8 row 1, SPEC.md §4 line 69, README.md §Anchors line 19 | EXPLICIT |
| 2 | Bannouh-Geng-Peeters 2019 = SSRN 3432446 SSRN-only NOT peer-reviewed | CLAUDE.md §P8 row 2, SPEC.md §4 line 76, README.md §Anchors line 26 | MIS-CITED SECONDARY label |
| 3 | Chambers-Penman 1984 **JAR 22(1):21–47** PRIMARY added for Strategy B | CLAUDE.md §P8 row 3, SPEC.md §4 line 70, README.md §Anchors line 21 | PRIMARY swap |
| 4 | Berger-Hann 2003 **JAR 41(2):163–223** secondary supporting | CLAUDE.md §P8 row 4, SPEC.md §4 line 73, README.md §Anchors line 23 | SECONDARY |
| 5 | Framing correction: variance-of-lag / within-firm baseline deviation extension axes vs anchor level/direction | CLAUDE.md §P8 row 5, SPEC.md §2 lines 49–59, experiments/*/README.md §Tier | DOCUMENTED |

## Anchor stack post-corrections (full reconciliation)

### Strategy A — rdq-datadate gap variance XS (RD1)

| Role | Anchor | Venue | Year | Extension axis |
|---|---|---|---|---|
| PRIMARY | Bagnoli-Kross-Watts | JAR 40(5):1275–1296 | 2002 | single-event lag → time-series 2nd moment (8Q rolling std) |
| Adjacent | Johnson-So | JFQA | 2018 | signed direction → magnitude-only |
| Secondary | deHaan-Shevlin-Thornock | JAE | 2015 | strategic timing → unobservable cadence-noise |
| MIS-CITED secondary | Bannouh-Geng-Peeters | SSRN 3432446 (SSRN-only NOT peer-reviewed) | 2019 | NN IP practitioner bridge only |

**Tier**: SUBSTANTIAL (3 extension axes vs Johnson-So 2018 JFQA).

### Strategy B — within-firm rolling baseline deviation XS (RD7)

| Role | Anchor | Venue | Year | Extension axis |
|---|---|---|---|---|
| PRIMARY | Chambers-Penman | JAR 22(1):21–47 | 1984 | industry/calendar baseline → firm-specific 8-Q rolling median baseline |
| Supporting | Begley-Fischer | RAST | 1998 | delay as bad news (sign matches asymmetric construction) |
| Secondary | Berger-Hann | JAR 41(2):163–223 | 2003 | Chambers-Penman lineage continuity |
| Within-firm validation | Noh-So-Verdi | JFE | 2021 | 25.6%/yr ≥1 timing change within firm (justifies 8-Q rolling baseline) |

**Tier**: PARTIAL (single extension axis: firm-specific vs industry/calendar baseline).

## Framing correction — variance-of-lag vs anchor level/direction explicit

| Strategy | Anchor mechanism | RD1-merged-RD7 mechanism | Extension type |
|---|---|---|---|
| A | Bagnoli 2002: **level** of (rdq-datadate) lag predicts return | RD1: **2nd moment** (8Q std) predicts return | level → variance (different statistical object) |
| B | Chambers-Penman 1984: **direction** of deviation from industry/calendar baseline | RD7: **direction × magnitude** of deviation from firm's own 8-Q rolling median | industry baseline → firm-specific baseline (different reference point) |

Both extensions are statistically distinct from anchors — not mere replication. Framing correction is therefore non-trivial; explicit documentation prevents reviewer confusion that "this is just Bagnoli/Chambers-Penman replicated."

## Bannouh-Geng-Peeters 2019 SSRN-only label affirmation

- SSRN 3432446 (Bannouh-Geng-Peeters 2019 "Earnings announcement timing and neural network signals")
- **NOT peer-reviewed**: SSRN-only, no JAR/JFE/RFS/JFQA/RAST/CAR submission record
- **Role**: motivation bridge only (NN IP practitioner reference for cadence-feature relevance)
- **Excluded** from anchor stack PRIMARY/SUPPORTING tiers
- Label: MIS-CITED SECONDARY (label preserves provenance for future P8 audits without granting peer-review weight)

## Chambers-Penman JAR PRIMARY swap affirmation

- Chambers-Penman 1984 JAR 22(1):21–47 = "Timeliness of Reporting and the Stock Price Reaction to Earnings Announcements"
- Replaces Bagnoli-Kross-Watts 2002 as PRIMARY for Strategy B (Bagnoli remains PRIMARY for Strategy A)
- Reason: Chambers-Penman directly tests **direction** of deviation (early/late) → return; Bagnoli tests **level** of lag → return. Strategy B (within-firm asymmetric construction) is direction-conditional, matching Chambers-Penman thesis more closely than Bagnoli's level signal.

## Sub-gate (a) verdict

**PASS** — all 5 P8 corrections documented EXPLICIT across CLAUDE.md / SPEC.md / README.md / per-experiment README.md. Bannouh SSRN-only label preserved. Chambers-Penman JAR PRIMARY swap encoded in Strategy B README.md line 11 and SPEC.md §4 line 70.

User-judgment override window: BINARY. If user reads this audit and judges framing insufficient → ABANDONED-pre-Phase0 + reusable-assets §5 audit. Autopilot proceeds to STEP 2 absent override.

## Output

- This audit: `audits/2026-06-16-RD1-merged-RD7-subgate-a-anchor-framing.md`
- Next: STEP 2 — Sub-gate (b) rdq-datadate gap distribution empirical GRADUATED
