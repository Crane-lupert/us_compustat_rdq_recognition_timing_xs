# us_compustat_rdq_recognition_timing_xs

**RD1-merged-RD7** — 2-strategy paper-practical research on Compustat `rdq` (earnings press-release date) cadence and market participant recognition timing.

**Status**: Phase 0 entry (2026-06-16). LAUNCH-with-tag MERGE. Paper-practical primary lane (Gate G methodology/discovery).

## What this repo studies

Two complementary signals on shared data (`comp_na_daily_all.fundq` + `crsp_a_stock.dsf_v2`):

1. **Strategy A — rdq-datadate gap variance XS (RD1)**: rolling 8-quarter standard deviation of (announcement date − fiscal period end). High variance = erratic disclosure cadence proxy → predicts negative forward CAR.

2. **Strategy B — within-firm rolling baseline deviation XS (RD7)**: current quarter's gap minus firm's own 8-quarter rolling median. Positive deviation (late vs own baseline) = hiding bad news → NEG forward CAR; negative deviation (early) = highlighting good news → POS forward CAR. Asymmetric portfolio symmetric-recoded to Q5-Q1 spread.

MERGE saves ~30-40% Phase 0 build cost via `shared_lib/rdq_panel_loader/` (shared cohort, shared fundq loader, shared CCM bridge, shared forward-returns joiner).

## Anchors (P8 verified — 5 Stage B corrections)

- **Bagnoli-Kross-Watts 2002 JAR** (NOT RAST, Stage A venue corrected) — Strategy A PRIMARY
- **Chambers-Penman 1984 JAR** — Strategy B PRIMARY (Stage B addition)
- **Johnson-So 2018 JFQA** — adjacent (level/direction of lag)
- **Begley-Fischer 1998 RAST** — Strategy B supporting
- **Berger-Hann 2003 JAR** — Chambers-Penman lineage secondary
- **Noh-So-Verdi 2021 JFE** — within-firm baseline validation
- **deHaan-Shevlin-Thornock 2015 JAE** — strategic timing secondary
- **Bannouh-Geng-Peeters 2019 SSRN-only** — MIS-CITED secondary (NN IP practitioner bridge only, NOT peer-reviewed)

## V5 SEC Form NT differentiation

This repo is **distinct** from V5 (`us_sec_form_nt_late_filing_xs`, LAYER A LOCKED 2026-06-11) — V5 uses SEC EDGAR Form NT regulatory filings as binary event marker; this repo uses Compustat `rdq` press-release date as continuous within-firm cadence signal. NT-filer firm-quarters are explicitly excluded to avoid mechanical confound.

## Rule 9 LAUNCH-with-tag (P(fail) 40-55% MEDIUM-UPPER)

This is a high-prior-fail launch (variance-of-X family 0/2 LAYER A LOCKED; V5 NT overlap risk; RD1↔RD7 coupling risk; heavy anchor post-pub decay). ABANDONED-pre-Phase0 at any Stage 0 sub-gate is an EXPECTED outcome per Rule 9.

LDS: Strategy A 5-6/7 LIVE-DEPLOYABLE / Strategy B 4/7 BORDERLINE.

## Source of truth

- Launch SPEC: `D:/vscode/meta-harness/audits/2026-06-16-RD1-merged-RD7-launch-spec.md`
- Autopilot prompt: `D:/vscode/meta-harness/audits/2026-06-16-RD1-merged-RD7-autopilot-prompt.txt`
- This repo CLAUDE.md: top-level operational guardrails

## Data

WRDS local dump only (no `wrds.Connection()`):
- `E:/wrds-data-courier/output/dump/comp_na_daily_all.fundq.csv.gz` (675 MB REAL)
- `E:/wrds-data-courier/output/dump/crsp_a_stock.dsf_v2.parquet` (4.42 GB REAL)
- `E:/wrds-data-courier/output/dump/comp_na_daily_all.names.csv.gz` (CCM fallback)

## License

Research repo — not for production trading. Code released under repo terms when paper publishes.
