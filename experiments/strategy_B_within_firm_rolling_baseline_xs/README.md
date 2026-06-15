# Strategy B — within-firm rolling baseline deviation XS (RD7)

**Signal**: `gap_dev_t = gap_t − median({gap_q : q ∈ trailing 8Q, ≥6 valid})`

**Hypothesis (asymmetric)**:
- Pos deviation (rdq later than firm's 8-Q rolling median) = hiding bad news → forward CAR NEG
- Neg deviation (rdq earlier than firm's 8-Q rolling median) = highlighting good news → forward CAR POS

**Portfolio**: monthly cross-sectional quintile within Fama-French 12 sector. Asymmetric construction symmetric-recoded into single Q5-Q1 (early – late) spread for Bonferroni-12 parity.

**Anchor PRIMARY**: Chambers-Penman 1984 **JAR 22(1):21-47** (Stage B addition — most direct thesis match for early/late deviation → return).

**Tier**: PARTIAL — extension axis vs Chambers-Penman + Begley-Fischer:
- Anchor mechanism = "deviation from expected timing → information" (level signal)
- RD7 extension axis = firm-specific expected timing (8-Q rolling median) rather than industry/calendar-rotation baseline
- Noh-So-Verdi 2021 JFE validates within-firm timing variation (25.6%/yr ≥1 change)

**Bonferroni-12 cells**: 3 horizons (60d/120d/180d) × 4 sub-cells (size × industry-tilt) = 12 cells. Symmetric-recoded.

**Verdict (graduated 3-tier)**: PASS ≥3/12 |t|>2.78 + sign-correct / BORDERLINE 2/12 / KILL <2/12.

**Direction Lock C**: Q5 (early, neg dev) – Q1 (late, pos dev) spread > 0 expected.

**LDS**: 4/7 BORDERLINE (Axis 2 alpha decay + Axis 5 cost + Axis 7 post-pub decay all weak; Chambers-Penman 42yr post-pub heavy).

**NT-filer exclusion mandatory**: drop NT-10K/NT-10Q firm-quarters from positive-deviation tail (V5 mechanical confound mitigation).

**Reuses**: `shared_lib/rdq_panel_loader/` (saves ~30-40% Phase 0 build cost).

See launch SPEC: `D:/vscode/meta-harness/audits/2026-06-16-RD1-merged-RD7-launch-spec.md` §2 Strategy B.
