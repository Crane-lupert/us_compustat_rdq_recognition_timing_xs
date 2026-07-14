# Earnings-Announcement Cadence-Variance Cross-Section

**Status**: Phase 1 out-of-sample test closed 2026-06-16. Paper-practical outcome (sign-correct out-of-sample, below multiple-comparison-protected statistical threshold). **SSRN preprint LIVE 2026-07-15**: <https://papers.ssrn.com/sol3/papers.cfm?abstract_id=7095738> (Ahn, Hyun. "Earnings-Announcement Cadence Variance and the Cross-Section of Forward Returns", working paper, June 2026). **한국어 실무 보고**: [readme_kr.md](readme_kr.md). Full paper: [reports/papers/paper_v1_en.md](reports/papers/paper_v1_en.md) / [reports/papers/paper_v1_en.pdf](reports/papers/paper_v1_en.pdf). Headline figure: [reports/figures/fig2_vs_ff5umd_tangent.png](reports/figures/fig2_vs_ff5umd_tangent.png).

## What this is

Cross-sectional equity signal from the **time-series volatility of the gap between a U.S. firm's fiscal quarter-end (`datadate`) and its actual earnings-announcement date (`rdq`)**. Compustat `fundq` 1999–2024, Russell 3000 universe, 620,290 firm-quarter observations after standard filters. The signal is `gap_var_t` = rolling 8-quarter standard deviation of (`rdq` − `datadate`); the hypothesis is that firms with erratic earnings-announcement cadence carry an unpriced disclosure-pipeline-noise component that resolves negatively in forward returns. Long the lowest-variance quintile, short the highest, monthly cross-section within Fama–French 12 industry.

## 5-minute skim

1. **Hypothesis**: an extension from earnings-announcement *level* (the within-firm direction of `rdq` deviation, e.g. Bagnoli, Kross and Watts 2002 in *JAR*) to earnings-announcement *variance* (the within-firm reliability of cadence). High `gap_var_t` proxies for internal-controls noise / disclosure-pipeline turbulence.

2. **Method**: Compustat `fundq` (NA INDL STD C D USD) → 8-quarter rolling standard deviation of `gap_days` with ≥6 valid quarters → monthly Q1/Q5 quintile within Fama–French 12 industry → long Q1, short Q5 → forward cumulative log return on CRSP `dsf_v2` over 60/120/180 days post-`rdq`. Twelve pre-registered cells (3 horizons × 4 sub-cells defined by size × industry-tilt) under a Bonferroni-12 |*t*| > 2.78 multiple-comparison-protected threshold with Newey–West *t*-statistics at lag 12. Late-filer exclusion (Form NT-10K / NT-10Q gap-day cutoff: 75 / 100 days) removes ≈4% of the sample as a mechanical-confound prophylactic.

3. **Headline (Russell 3000, 620,290 firm-Q, 1999–2024)**:

   | Specification | Pass / 12 | Sign-correct / 12 |
   |---|:-:|:-:|
   | In-sample 1999–2016 (primary, Fama–French 12 industry) | **4 / 12** | 12 / 12 |
   | Out-of-sample 2017–2024 (primary, Fama–French 12 industry) | 0 / 12 | **11 / 12** |
   | Out-of-sample sector concentration (3 high-tilt cells) | **3 / 3** | — |
   | Full panel under Fama–French 49 industry (robustness) | **5 / 12** | 12 / 12 |
   | Full panel under skip-week-1 forward window (PEAD-overlap clean) | **4 / 8** | 8 / 8 |
   | Full panel at 240-day and 360-day horizons (extended) | **5 / 8** | 8 / 8 |

   The four primary out-of-sample cells are sign-correct with *t*-statistics 1.55, 1.74, 1.85, 1.86 — below the Bonferroni-12 threshold but above the nominal one-tailed 5% threshold. Annualized HAC-corrected net Sharpe (Newey–West lag 12, 20 bps/month round-trip transaction cost) is 1.01 in-sample and 0.82 out-of-sample (−19% degradation).

4. **Mechanism clarification (skip-week-1)**: dropping rdq+1..rdq+7 from the forward-return window *strengthens* the signal in all four primary cells (e.g. A180-LH *t* 3.31 → 3.59; A120-SH *t* 2.06 → 3.19). The cadence-variance effect is therefore a slow informational-process correction over weeks 2..H, distinct from the fast post-earnings-announcement drift (PEAD) operating in week 1.

5. **Transaction cost**: break-even ≈250–500 bps/month round-trip, 10–100× margin over realistic institutional 5–20 bps. Transaction cost is not the binding constraint.

6. **Reproducibility**: deterministic Python pipeline (Pandas with `kind="mergesort"` throughout; no `groupby.agg('first'/'last'/'nth')` without prior sort; no `drop_duplicates` without prior sort); SHA-pinned in-sample / out-of-sample partitions; ex-ante outcome rules committed before the out-of-sample reveal. See **Pre-registration discipline** section below.

## Repo structure

```
shared_lib/rdq_panel_loader/
  __init__.py                       # canonical panel constructor (fundq + CRSP + late-filer exclusion)
  ff49.py                           # Ken French 49-industry SIC mapping (16 sanity tests; all 49 buckets used)

scripts/
  build_forward_returns.py          # 60/120/180-day forward CARs from dsf_v2
  build_forward_returns_extended.py # 240/360/120-skip-week-1/180-skip-week-1 (additional stream)
  subgate_b_*.py                    # gap-distribution + CRSP-uniformity diagnostics
  subgate_c_nt_proxy.py             # late-filer exclusion construction
  subgate_d_rho.py                  # signal-pair correlation pre-check

  strategy_A_bonferroni.py          # primary 12-cell Bonferroni specification
  strategy_A_bonferroni_with_nt.py  # with-late-filer vs without-late-filer sensitivity
  strategy_A_robustness.py          # FF12 sector concentration + regime stability
  strategy_B_bonferroni.py          # within-firm rolling-baseline deviation (Chambers-Penman 1984 replication; kill)
  strategy_B_asymmetric.py          # asymmetric 24-cell decomposition

  phase1_is_oos_split.py            # IS / OOS partition + SHA pin
  phase1_strategy_A_is.py           # in-sample 12-cell re-confirmation
  phase1_robustness_is.py           # in-sample transaction-cost overlay
  phase1_strategy_A_oos.py          # out-of-sample reveal (binding test)
  phase1_sector_nt_oos.py           # out-of-sample sector + with-late-filer sensitivity
  phase1_tradability.py             # Sharpe / DD / TC-break-even / hit-rate per cell × partition
  phase1_robustness_ff49.py         # Fama-French 49 partition Bonferroni
  phase1_robustness_extended_horizons.py  # 240/360/skip-week-1 Bonferroni
  make_pnl_figure_vol_matched.py    # publication + LinkedIn figure (vs FF5+UMD tangent, vol-matched)

audits/
  2026-06-16-RD1-merged-RD7-phase1-prereg-lock-d.md           # ex-ante outcome rule
  2026-06-16-RD1-merged-RD7-phase1-day0-anti-bias.md          # opening-session bias-surface enumeration
  2026-06-16-RD1-merged-RD7-phase1-day{1..5}-*.md             # day-by-day execution trail
  2026-06-16-RD1-merged-RD7-phase1-close.md                   # binding outcome audit
  2026-06-16-RD1-merged-RD7-phase1-tradability.md             # practitioner Sharpe / TC / DD
  2026-06-16-RD1-merged-RD7-phase1-deferred-robustness.md     # FF49 + extended horizons + skip-week-1

artifacts/
  panel_*.parquet                   # constructed panels (gitignored; SHA in JSON manifests)
  strategy_A_*.{csv,json}           # cell-level statistics + tradability + robustness
  fig2_vs_ff5umd_tangent_summary.json  # machine-readable headline-figure numerics
  phase1_is_oos_split.json          # IS / OOS SHA pin manifest

data/
  ff5_umd_monthly.jsonl             # Ken French 5-factor + UMD monthly returns

reports/
  papers/RD1-strategy-A-paper-outline.md   # paper outline (full draft pending)
  papers/paper_v1_en.md                     # full English paper draft v1
  figures/fig2_vs_ff5umd_tangent.png        # publication + LinkedIn figure
```

## Setup

```bash
cd D:/vscode/us_compustat_rdq_recognition_timing_xs
python -m venv .venv
.venv/Scripts/activate
pip install pandas pyarrow numpy matplotlib
```

External data: this repo reads from a local WRDS dump at `E:/wrds-data-courier/output/dump/` (`comp_na_daily_all.fundq.csv.gz`, `comp_na_daily_all.names.csv.gz`, `crsp_a_stock.dsf_v2.csv.gz`). No live WRDS connection; no `.pgpass`.

## Run end-to-end

```bash
# 1. Panel construction (one-time; ~5-10 min for fundq + 15-25 min for CRSP stream)
python scripts/build_forward_returns.py             # creates panel_with_returns.parquet
python scripts/build_forward_returns_extended.py    # adds car_240/360/120_sw1/180_sw1

# 2. Phase 0 diagnostics + Phase 1 IS/OOS split
python scripts/subgate_b_gap_distribution.py
python scripts/subgate_c_nt_proxy.py
python scripts/phase1_is_oos_split.py               # SHA-pinned partition

# 3. Primary 12-cell Bonferroni (in-sample, then out-of-sample reveal)
python scripts/phase1_strategy_A_is.py              # in-sample re-confirmation
python scripts/phase1_robustness_is.py              # in-sample transaction-cost overlay
python scripts/phase1_strategy_A_oos.py             # binding out-of-sample test

# 4. Out-of-sample sector + with-late-filer sensitivity
python scripts/phase1_sector_nt_oos.py

# 5. Augmentation: tradability + deferred robustness
python scripts/phase1_tradability.py                # Sharpe / TC / DD per cell × partition
python scripts/phase1_robustness_ff49.py            # FF49 partition (5/12)
python scripts/phase1_robustness_extended_horizons.py  # 240/360/skip-week-1 (9/16)

# 6. Publication + LinkedIn figure
python scripts/make_pnl_figure_vol_matched.py       # reports/figures/fig2_vs_ff5umd_tangent.png
```

## Pre-registration discipline

Three commit-locked ex-ante decisions, all dated 2026-06-16 (pre out-of-sample reveal):

| Commit | Document | Purpose |
|---|---|---|
| `dbc303b` | `audits/...-phase1-prereg-lock-d.md` | 4 primary cells + 8 secondary cells + in-sample / out-of-sample boundary + per-cell expected out-of-sample *t*-magnitudes |
| `fd2828f` | `audits/...-phase1-day0-anti-bias.md` | Bias-surface enumeration + KILL-condition acknowledgment + out-of-sample sealing protocol |
| `fa3e334` | `artifacts/phase1_is_oos_split.json` | SHA-pin of in-sample (1999-2016) and out-of-sample (2017-2024) partitions |

The out-of-sample reveal commit `0186fd7` ran the binding test verbatim against the pre-registered specification with zero parameter tuning, zero cell re-selection, and zero direction reversal. The pre-registered expected out-of-sample *t*-magnitudes (1.55, ~2.0, 1.85, 1.74) matched the realized values (1.55, 1.86, 1.85, 1.74) to two decimal places on three of four cells — the test was a successful falsification check on the signal's power, not on its direction.

## Honest acknowledgments

- **The signal does not cross the Bonferroni-12 multiple-comparison-protected threshold on the pre-registered out-of-sample partition** (0 of 4 primary cells, 0 of 12 total). It is sign-correct in 11 of 12 cells and the corresponding HAC-corrected practitioner Sharpe net of transaction cost is 0.82 — meaningful but below the academic statistical bar.
- **The closely-related signal of within-firm rolling-baseline deviation (Chambers and Penman 1984 in *JAR*) fails Bonferroni-12 in the same panel** (0 of 12, even under asymmetric 24-cell decomposition). This is a failed-replication contribution: the within-firm deviation channel has decayed post-publication, while the variance channel survives.
- **Universe boundary**: Russell 3000 ∩ Compustat coverage; 1999 has zero `rdq` observations (Compustat coverage begins 2000-02). Out-of-sample partition is 96 calendar months — power-constrained for a Bonferroni-12 threshold.
- **Mechanism overlap with SEC Form NT late-filing**: handled by an ex-ante exclusion (gap > 75 days for non-annual, > 100 days for annual filings, ≈4% of sample); the with-late-filer vs without-late-filer out-of-sample inflation ratio is 2.0 — exactly at the pre-registered KILL threshold (strict >) so not triggered, but borderline.
- **Fama-French 12 industry is the primary partition**; the Fama-French 49 partition is an advisory robustness check (5/12 PASS on full panel) that slightly *strengthens* rather than degrades the headline.
- **Naive monthly Sharpe overstates by ≈1.6×** for overlapping H-day forward-return cohorts; the HAC-corrected (Newey–West lag 12) Sharpe is the practitioner-honest read.

See [audits/2026-06-16-RD1-merged-RD7-phase1-close.md](audits/2026-06-16-RD1-merged-RD7-phase1-close.md) for the full ledger of binding LOCK / KILL conditions and their realized values.

## Cost / performance budgets

- Compute: $0 (local WRDS dump; no paid API).
- LLM: $0 (no language-model use in this project).
- Wall time: ≈30 minutes for the full pipeline (one-time CRSP stream dominates).
- All scripts are deterministic; re-running against the same input SHA produces byte-identical output (pandas `kind="mergesort"` throughout).

## Repo philosophy

Open-source, reproducible, ex-ante-rule-locked. The out-of-sample test was sealed for three working days before reveal and executed verbatim against a specification committed at the start of phase 1. The negative pre-registered outcome is reported with the same prominence as the positive ancillary results (sector robustness, skip-week-1 PEAD-separation, FF49 strengthening). If a finding can be cherry-picked, it is not reported as a finding. If a measurement can be deflated by a defensible correction (HAC, transaction cost, multiple-comparison protection), it is.

---

**Contact**: fawkes4700@gmail.com
