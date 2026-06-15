# Strategy A — rdq-datadate gap variance XS (RD1)

**Signal**: `gap_var_t = std({gap_q : q ∈ trailing 8Q, ≥6 valid})`

**Hypothesis (NEG)**: High variance of rdq-datadate gap proxies erratic internal controls / disclosure-pipeline noise → forward CAR negative.

**Portfolio**: monthly cross-sectional quintile within Fama-French 12 sector. Long Q1 (low-variance) / short Q5 (high-variance).

**Anchor PRIMARY**: Bagnoli-Kross-Watts 2002 **JAR 40(5):1275-1296** (NOT RAST — Stage A venue mis-cite corrected).

**Tier**: SUBSTANTIAL — 3 extension axes vs Johnson-So 2018 JFQA:
1. From single-event deviation → time-series 2nd moment (8Q rolling std)
2. From signed direction → magnitude-only (variance captures erratic, both early AND late)
3. From quarterly EAD return → monthly XS quintile (different tradability surface)

**Bonferroni-12 cells**: 3 horizons (60d/120d/180d) × 4 sub-cells (size large/small × industry-tilt high/low) = 12 cells.

**Verdict (graduated 3-tier)**: PASS ≥3/12 |t|>2.78 + sign-correct / BORDERLINE 2/12 / KILL <2/12.

**Direction Lock C**: Q1 (low-var) – Q5 (high-var) spread > 0 expected (high-variance → NEG CAR).

**LDS**: 5-6/7 LIVE-DEPLOYABLE.

**Reuses**: `shared_lib/rdq_panel_loader/` (saves ~30-40% Phase 0 build cost).

See launch SPEC: `D:/vscode/meta-harness/audits/2026-06-16-RD1-merged-RD7-launch-spec.md` §2 Strategy A.
