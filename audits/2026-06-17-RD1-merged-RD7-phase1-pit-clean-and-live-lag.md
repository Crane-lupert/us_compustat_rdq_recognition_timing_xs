---
date: 2026-06-17
phase: 1 (augmentation, post-close, post-tradability, post-deferred-robustness)
repo: us_compustat_rdq_recognition_timing_xs
project_id: RD1-merged-RD7
scripts:
  - scripts/phase1_pit_clean.py
  - scripts/make_pnl_figure_vol_matched.py
artifacts:
  - artifacts/strategy_A_pit_clean.{csv,json}
  - artifacts/strategy_A_pit_clean_monthly.csv
  - reports/figures/fig2_vs_universe_benchmark.png
  - artifacts/fig2_vs_universe_benchmark_summary.json
verdict_summary: |
  The primary backtest specification contains a within-month look-ahead in
  cross-section quintile assignment. A strict point-in-time variant -- trailing
  30-day FF12 cohort ranking with rdq+8 forward window (absorbs Compustat
  refresh delay + PEAD week) -- clears Bonferroni-12 in 3 of 4 mirror-of-primary
  cells out-of-sample. This is a POST-HOC finding; the pre-registered headline
  remains unchanged (paper-practical PARTIAL). The post-hoc variant is the
  live-implementable specification.
---

# PIT-Cleanliness, Live Data Lag, and a Vol-Matched Benchmark

This audit answers three diagnostic questions raised after Phase 1 close:

1. Is the primary backtest specification point-in-time (PIT) clean?
2. Does the signal construction account for the live data-acquisition lag?
3. How does the strategy compare to a vol-matched benchmark?

## §1 The look-ahead bias in the primary specification

The primary cross-section quintile is assigned in [strategy_A_bonferroni.py:58-61](../scripts/strategy_A_bonferroni.py#L58-L61):

```python
df["rdq_month"] = df["rdq"].dt.to_period("M")
df["q5"] = df.groupby(["rdq_month", "ff12"], sort=False, observed=True)[signal_col].transform(_qcut_safe)
```

This groups by calendar month of `rdq` and ranks within the group. **For a firm announcing on April 5, the quintile is determined by comparison against firms announcing through April 30 — including 25 calendar days of future announcers that are not yet known on April 5.** This is a within-month look-ahead bias.

The bias is bounded — typical FF12 sectors have 50–200 announcers per calendar month, so the bias is on the order of the difference between a within-month cohort and a trailing 30-day cohort. But it is real, and it should be removed for any honest live-implementation Sharpe quotation.

## §2 Live data-acquisition lag

For a practitioner attempting to trade this signal live, three lags apply:

| Source | Lag | Description |
|---|---|---|
| Compustat refresh | ~1–2 trading days | `rdq` is populated in Compustat once the firm's 8-K earnings announcement is parsed; refresh cycle is overnight to T+1 for major listings |
| Cross-section cohort completion | ~30 calendar days | The within-month cross-section in the primary specification requires waiting until all of the calendar month's announcers have reported |
| PEAD week-1 overlap | 5–7 trading days | The first week post-announcement is dominated by post-earnings-announcement drift, an unrelated well-known anomaly that adds noise to any cadence-variance forward-return measurement |

The primary specification's forward window starts at rdq+1, which assumes zero lag on all three sources. The **rdq+8 skip-week-1 specification** introduced as a robustness check in the prior audit ([phase1-deferred-robustness.md §4](2026-06-16-RD1-merged-RD7-phase1-deferred-robustness.md)) actually addresses all three lags simultaneously: it gives Compustat ≥1 day to refresh, gives the cross-section cohort time to settle, and skips the PEAD week. **The skip-week-1 specification is therefore not just a robustness check — it is the live-implementable forward window.**

For the cross-section ranking itself, the primary specification's calendar-month grouping needs to be replaced by a strict trailing cohort.

## §3 The PIT-clean variant

`scripts/phase1_pit_clean.py` constructs the signal under three strict PIT rules:

1. **Quintile assignment uses a trailing 30-day FF12 cohort.** For each firm with rdq = d, the cohort is firms in the same Fama–French 12 industry with rdq ∈ [d − 30 days, d − 1 day]. Strict less-than rdq filter.
2. **Forward-return window starts at rdq+8** (carries over from the deferred-robustness audit).
3. **Size bin uses the rdq-day market cap** (cshoq × prccq), which is genuinely PIT-clean at rdq under the standard practitioner convention.

Cohort coverage: 99.8% of firm-quarters receive a valid PIT-clean quintile assignment (cohort size ≥ 5). The 0.2% loss is mostly early-period observations where the trailing 30-day FF12 cohort is too small.

## §4 PIT-clean Bonferroni-12 — full panel

| Cell | n_months | μ_spread | t-stat (NW-12) | Sign-correct | Pass Bonferroni-12 |
|---|---:|---:|---:|:-:|:-:|
| A120-SW1-LH | 297 | +2.52% | **4.27** | ✓ | **PASS** |
| A120-SW1-LL | 293 | +2.08% | 2.24 | ✓ | — |
| A120-SW1-SH | 266 | +3.00% | 2.51 | ✓ | — |
| A120-SW1-SL | 298 | +3.44% | **4.72** | ✓ | **PASS** |
| A180-SW1-LH | 297 | +3.33% | **3.82** | ✓ | **PASS** |
| A180-SW1-LL | 293 | +3.76% | **3.10** | ✓ | **PASS** |
| A180-SW1-SH | 267 | +3.57% | 2.47 | ✓ | — |
| A180-SW1-SL | 298 | +5.51% | **5.85** | ✓ | **PASS** |

**5/8 PASS, 8/8 sign-correct.** Compared to the non-PIT version of the same skip-week-1 horizons (`phase1_robustness_extended_horizons.py`, 4/8 PASS), the strict PIT version *adds* a passing cell (A180-SW1-LL gains 0.48 t-units; A120-SW1-LH gains 0.83 t-units). **Removing the within-month look-ahead does not weaken the result.**

## §5 PIT-clean IS / OOS split

| Cell | IS months | IS t | IS pass | OOS months | OOS t | OOS pass |
|---|---:|---:|:-:|---:|---:|:-:|
| A120-SW1-LH | 199 | **3.54** | ✓ | 95 | 2.38 | — |
| A120-SW1-LL | 198 | 1.45 | — | 91 | 2.04 | — |
| A120-SW1-SH | 180 | 1.46 | — | 84 | **3.34** | ✓ |
| A120-SW1-SL | 199 | **4.55** | ✓ | 96 | 1.66 | — |
| A180-SW1-LH | 199 | **2.79** | ✓ (just) | 95 | **2.86** | ✓ |
| A180-SW1-LL | 198 | 2.14 | — | 91 | 2.48 | — |
| A180-SW1-SH | 180 | 1.59 | — | 85 | **3.21** | ✓ |
| A180-SW1-SL | 199 | **4.75** | ✓ | 96 | **2.98** | ✓ |

**IS 4/8 PASS, OOS 4/8 PASS, all 16/16 sign-correct.**

### §5.1 Mirror-of-primary cells (A120-LH, A120-SH, A180-LH, A180-SL → PIT-clean variants)

| Primary cell | Primary OOS t | PIT-clean cell | PIT-clean OOS t | Δ |
|---|---:|---|---:|---:|
| A120-LH | 1.55 | A120-SW1-LH | 2.38 | +0.83 |
| A120-SH | 1.86 | A120-SW1-SH | **3.34** | +1.48 |
| A180-LH | 1.85 | A180-SW1-LH | **2.86** | +1.01 |
| A180-SL | 1.74 | A180-SW1-SL | **2.98** | +1.24 |

**Under the PIT-clean live-implementable specification, 3 of 4 mirror-of-primary cells cross Bonferroni-12 out-of-sample.** All four mirror cells improve by 0.83 to 1.48 t-units.

## §6 Disposition — the pre-registered headline is unchanged

The pre-registered binding test (ex-ante outcome rule from the cell-selection lock) is the primary specification: calendar-month cross-section grouping + rdq+1 forward window. **That test failed Bonferroni-12 out-of-sample** ([phase1-day4-oos-reveal.md](2026-06-16-RD1-merged-RD7-phase1-day4-oos-reveal.md)), and the Phase 1 verdict is paper-practical PARTIAL.

The PIT-clean variant was **not pre-registered**. It is a post-hoc specification that emerged after the deferred-robustness audit identified skip-week-1 as the live-implementable forward window, and after the user's diagnostic question identified the within-month look-ahead in the primary specification.

Per the meta-harness paper-writing checklist §7.6 ("Silently swapping post-hoc variant into headline slot"), the PIT-clean variant **does not become the new headline**. It goes into the paper's §5.x robustness section, clearly labeled as a post-hoc specification reflecting the live-implementable convention. The pre-registered headline (paper-practical PARTIAL) stands.

The substantive read for the paper is: **the primary backtest specification was conservatively biased, not look-ahead-aggressive. Removing the within-month look-ahead** *strengthens* **the signal, indicating that the within-month look-ahead was effectively *adding* noise (presumably because firms with idiosyncratic later-month news drift correlated with quintile boundary placement).** The signal is more tradable than the primary specification suggested, but the pre-registered statistical bar miss is what we report as the headline.

## §7 Vol-matched-to-benchmark figure (fig2)

`scripts/make_pnl_figure_vol_matched.py` produces a publication-quality figure that uses **the same primary specification strategy as fig1** (calendar-month FF12 cross-section, rdq+1 forward window, composite of the four pre-registered primary cells A120-LH, A120-SH, A180-LH, A180-SL). The PIT-clean live-implementable variant from §3–§6 is NOT plotted here — its numerical result lives only in the audit / paper §5.x text. The deliberate choice is: fig2 should differ from fig1 only in the vol target and the addition of a benchmark line, not in the underlying strategy. This makes the figures intuitively comparable.

The figure shows:

1. **Strategy** = same composite as fig1.
2. **Strategy, net** = strategy minus 20 bps/month round-trip transaction cost.
3. **FF5+UMD tangent** = in-sample maximum-Sharpe combination of the six Fama-French five-factor portfolios (Mkt-RF, SMB, HML, RMW, CMA) and the Carhart momentum factor (UMD), computed via closed-form Σ⁻¹μ. Long-short by construction, so the LS-vs-LS comparison is on the same footing.

The strategy is vol-matched to the in-sample annualized volatility of the tangent benchmark (3.9% / year), with the scaling factor calibrated on the in-sample window only.

### §7.1 Headline numerics

HAC-corrected annualized Sharpe (Newey–West lag 12):

| Series | In-sample (1999–2016) | Out-of-sample (2017–2024) |
|---|---:|---:|
| Strategy gross | 1.06 | 0.87 |
| Strategy net of 20 bps/month | 1.01 | 0.82 |
| FF5+UMD tangent (in-sample max-Sharpe) | 1.05 | 1.01 |

Under the pre-registered primary specification, the strategy **roughly ties the FF5+UMD tangent in-sample (1.06 vs 1.05)** but **trails the tangent out-of-sample (0.87 vs 1.01)**. Net of transaction cost, the strategy trails the tangent in both windows. This is the honest LS-vs-LS comparison at matched volatility, and it is consistent with the pre-registered paper-practical PARTIAL verdict.

### §7.2 Where the PIT-clean improvement enters

The §3–§6 PIT-clean live-implementable variant (trailing 30-day FF12 cohort + skip-week-1 forward window) raises the strategy's HAC Sharpe to **1.23 IS / 1.38 OOS net**, exceeding the FF5+UMD tangent on both windows. The improvement from the primary specification is therefore not from vol-matching or benchmark choice; it is from the two methodology fixes (PIT-clean cross-section + skip-week-1 forward window) that the audit §1–§5 documents. Both fixes strengthen the signal because the within-month look-ahead and the rdq+1 week of PEAD contamination were *adding noise* to the primary specification, not *exploiting* future information.

For paper exposition, the disposition is:

- **fig1 (cumulative growth at 10% vol target, no external benchmark)** is the headline figure for the pre-registered specification.
- **fig2 (cumulative return at FF5+UMD tangent vol, with benchmark)** is the LS-vs-LS comparison at the standard factor-model benchmark, also for the pre-registered specification.
- The PIT-clean live-implementable variant is **discussed in §5.x text** with the cell-level Bonferroni-12 table, not given its own figure.

## §8 Paper / README implications

For the eventual paper (currently `reports/papers/paper_v1_en.md`), the §5 robustness section should add:

- **§5.7 Point-in-time cleanliness**: the primary specification's calendar-month grouping introduces a within-month look-ahead. A trailing 30-day FF12 cohort variant is the live-implementable cross-section. The PIT-clean variant *strengthens* rather than weakens the signal, indicating that the within-month look-ahead in the primary was adding noise rather than alpha.
- **§5.8 Live data-acquisition lag**: the rdq+8 skip-week-1 forward window absorbs the Compustat database refresh delay (T+1 to T+2 for major listings), the cross-section cohort completion delay (~30 days under the calendar-month grouping that the primary uses), and the PEAD week-1 contamination. The skip-week-1 variant, already reported as a PEAD-separation robustness, is *also* the live-implementable forward window.
- **§5.9 Live-implementable specification (post-hoc)**: combining the PIT-clean cross-section + rdq+8 forward window gives 3 of 4 mirror-of-primary cells crossing Bonferroni-12 out-of-sample (vs 0 of 4 in the pre-registered specification). This is reported as a post-hoc finding consistent with the live-implementable convention; it does *not* become the new headline.

The paper-practical disposition stays: the pre-registered headline failed Bonferroni-12 out-of-sample.

## §9 Lock F compliance

- `scripts/phase1_pit_clean.py` uses `kind="mergesort"` for all sort_values calls.
- The trailing-cohort lookup is implemented with `numpy.searchsorted` on a per-FF12 sorted rdq vector; deterministic.
- Re-runs against the same `panel_with_returns_ext.parquet` produce byte-identical output.

## §10 Artifacts

| Path | Contents |
|---|---|
| [scripts/phase1_pit_clean.py](../scripts/phase1_pit_clean.py) | PIT-clean signal construction |
| [scripts/make_pnl_figure_vol_matched.py](../scripts/make_pnl_figure_vol_matched.py) | fig2 builder |
| [artifacts/strategy_A_pit_clean.json](../artifacts/strategy_A_pit_clean.json) | Cell-level Bonferroni + IS/OOS split |
| [artifacts/strategy_A_pit_clean_monthly.csv] (gitignored) | Monthly Q1−Q5 spread per cell |
| [data/ff5_umd_monthly.jsonl](../data/ff5_umd_monthly.jsonl) | Fama-French 5-factor + UMD monthly returns, 1963–2026 |
| [reports/figures/fig2_vs_ff5umd_tangent.png](../reports/figures/fig2_vs_ff5umd_tangent.png) | Vol-matched-to-FF5+UMD-tangent figure |
| [artifacts/fig2_vs_ff5umd_tangent_summary.json](../artifacts/fig2_vs_ff5umd_tangent_summary.json) | Machine-readable headline numerics |

## §11 Commit pin

Prior phase-1 augmentation chain: `d255e98` (tradability + readme_kr) → `a1a5f08` (fig1 + FF49) → `ca70658` (deferred robustness) → `b7bcf3f` (English README + paper draft v1).

This audit: TBD by post-write commit.
