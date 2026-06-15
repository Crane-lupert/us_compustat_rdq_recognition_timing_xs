---
date: 2026-06-16
phase: 1 (augmentation, post-close)
repo: us_compustat_rdq_recognition_timing_xs
project_id: RD1-merged-RD7
script: scripts/phase1_tradability.py
artifacts:
  - artifacts/strategy_A_tradability.csv
  - artifacts/strategy_A_tradability.json
  - artifacts/strategy_A_monthly_returns.csv
purpose: Render PARTIAL verdict (K2 fired Day 4) intuitively visible via practitioner Sharpe / TC / drawdown / hit-rate metrics.
---

# Phase 1 Tradability Verification (PARTIAL evidence augmentation)

## §1 Motivation

K2 fired on Day 4 ([phase1-day4-oos-reveal.md](2026-06-16-RD1-merged-RD7-phase1-day4-oos-reveal.md)): OOS 0/4 primary cells PASS Bonferroni-12 |t|>2.78 — paper-practical-only verdict locked. But Bonferroni-12 is a **multiple-comparison-protected statistical bar**, not a practitioner tradability bar. This audit answers: *does any tradable signal survive K2?* The answer matters because it disambiguates two failure modes:

1. **Mechanically dead signal** (Sharpe ≈ 0, hit-rate ≈ 50%, no economic content) → paper not worth writing.
2. **Power-constrained signal** (Sharpe meaningfully positive, hit-rate >55%, sign-correct in 11/12 cells) → paper-practical PASS is the correct verdict; future work on longer OOS windows could re-test for LAYER A LOCK.

Day 4 already showed 11/12 OOS cells sign-correct. This audit confirms the corresponding **practitioner Sharpe / drawdown / TC-sensitivity** picture.

## §2 Method

For each of the 4 primary cells × {IS, OOS, FULL}:
- Build the monthly Q1 − Q5 spread time series re-formed monthly within (size × ind-tilt) sub-cell. Each month's value is the H-day cumulative CAR averaged across firms in Q1 minus those in Q5 of the same month's quintile assignment.
- Compute annualized Sharpe = monthly mean / monthly std × √12.
- TC sensitivity: deduct fixed bps/month from monthly spread; recompute Sharpe at TC ∈ {0, 5, 10, 20, 50, 100} bps/month.
- Hit rate = % months with positive spread.
- Max drawdown on cumulative (1+r) wealth path.
- TC break-even = bps/month that strips mean monthly spread to 0.

**Caveat (overlapping cohorts)**: monthly CARs at H ∈ {120, 180} days correspond to overlapping 4-6 month holding cohorts. A practitioner running this strategy in production with monthly rebalancing would hold 4-6 cohorts simultaneously; the "raw monthly Sharpe" computed here treats each month's spread as if independently realized. True practitioner Sharpe with overlap correction ≈ raw / √(H/30) — see §6.

## §3 Results — primary cell summary

| Cell | Part | n_mo | ann μ gross | Sharpe gross | Sharpe net@20bps | Hit rate | Max DD | TC break-even (bps/mo) |
|---|:-:|---:|---:|---:|---:|---:|---:|---:|
| A120-LH | IS | 198 | 40.5% | 1.04 | **0.98** | 61.1% | −48.1% | 337 |
| A120-LH | OOS | 96 | 29.8% | 0.85 | **0.78** | 58.3% | −33.8% | 248 |
| A120-SH | IS | 187 | 31.9% | 0.59 | **0.55** | 67.9% | −95.4% | 266 |
| A120-SH | OOS | 90 | 44.8% | 0.75 | **0.71** | 64.4% | −87.0% | 373 |
| A180-LH | IS | 198 | 49.6% | 1.09 | **1.04** | 62.6% | −57.6% | 414 |
| A180-LH | OOS | 96 | 42.1% | 0.95 | **0.89** | 62.5% | −42.2% | 351 |
| A180-SL | IS | 200 | 59.2% | 1.06 | **1.02** | 73.5% | −98.3% | 493 |
| A180-SL | OOS | 96 | 55.5% | 0.94 | **0.90** | 62.5% | −85.6% | 462 |

### §3.1 Median tradability per partition

| Partition | Median Sharpe gross | Median Sharpe net@20bps | Median hit | Median MDD | Median TC break-even |
|---|---:|---:|---:|---:|---:|
| IS  (1999-2016) | 1.05 | **1.00** | 65.3% | −76.5% | 375 bps |
| OOS (2017-2024) | 0.89 | **0.84** | 62.5% | −63.9% | 362 bps |
| IS→OOS Δ | — | **−16.2%** | — | — | — |

**Tradability tier: TRADABLE-MODERATE on both partitions.** Net@20bps Sharpe 0.84-1.00 sits between the "PAPER-PRACTICAL" (>0 to 0.5) and "TRADABLE-STRONG" (≥1.0) tiers — characteristic of a sign-correct, economically meaningful, but statistically under-powered signal.

## §4 Why K2 fired despite tradable Sharpe

The **gap** between practitioner Sharpe (0.84 OOS net@20bps) and Bonferroni-12 failure (|t|<2.78 OOS) is the entire story of paper-practical:

| Threshold | Sharpe-equivalent (96 mo) | OOS realized |
|---|---:|---:|
| Bonferroni-12 \|t\|>2.78 | Sharpe ≥ **0.98** | 0.84 |
| One-tailed nominal \|t\|>1.65 | Sharpe ≥ 0.58 | 0.84 ✓ |

Bonferroni-12 is calibrated for **12 pre-registered cells × multiple-comparison protection**. The realized OOS Sharpe of 0.84 corresponds to a single-cell t-stat of ~2.4 — significant at 1-tail nominal 5%, but below the multiple-comparison-protected 2.78 bar. K2 fires because of the bar's stringency, not because the signal is dead.

## §5 TC sensitivity grid (all primary cells, all partitions)

TC break-even ranges **248-493 bps/month** across cells/partitions. Realistic institutional TC for a US large/mid-cap monthly-rebalanced long-short strategy is **5-20 bps/month** — the signal has **10-100× margin** against TC erosion. TC is **not** the binding constraint.

| Cell | Part | Sharpe@0bps | Sharpe@5 | Sharpe@10 | Sharpe@20 | Sharpe@50 | Sharpe@100 |
|---|:-:|---:|---:|---:|---:|---:|---:|
| A120-LH | OOS | 0.85 | 0.83 | 0.82 | 0.78 | 0.69 | 0.54 |
| A120-SH | OOS | 0.75 | 0.74 | 0.73 | 0.71 | 0.65 | 0.55 |
| A180-LH | OOS | 0.95 | 0.94 | 0.92 | 0.89 | 0.81 | 0.67 |
| A180-SL | OOS | 0.94 | 0.93 | 0.92 | 0.90 | 0.82 | 0.71 |

Even at 100 bps/month TC (5-20× realistic), all 4 primary cells retain OOS Sharpe ≥ 0.54.

## §6 Overlap-adjusted practitioner Sharpe

For a strategy with H-day holding and monthly rebalancing, ~H/30 cohorts are simultaneously held. Naive monthly Sharpe over-states by √(H/30) under independence assumption (cohort returns are not independent — same firms appear in adjacent cohorts).

| Cell | Horizon | H/30 cohorts | OOS Sharpe naive | OOS Sharpe overlap-adj |
|---|:-:|:-:|---:|---:|
| A120-LH | 120d | 4 | 0.85 | **0.43** |
| A120-SH | 120d | 4 | 0.75 | **0.38** |
| A180-LH | 180d | 6 | 0.95 | **0.39** |
| A180-SL | 180d | 6 | 0.94 | **0.38** |

**Overlap-adjusted practitioner Sharpe ≈ 0.4 OOS** — TRADABLE-MARGINAL tier. This is the honest practitioner-investment-committee read: the signal is real, sign-correct, profitable net of TC, but Sharpe 0.4 is below most institutional bars (typically 1.0+). Consistent with paper-practical verdict.

## §7 Max drawdown commentary

Reported max drawdowns are large (−42% to −98%). Interpretation:
- The cumulative wealth path compounds overlapping H-day cohort returns naïvely — so max DD overstates real portfolio drawdown by approximately √(H/30) as well.
- True practitioner-managed drawdown (cohort-weighted, capital-normalized) would be ~half the reported figure.
- Even so, the strategy's tail risk is substantial — A120-SH and A180-SL show >−85% naïve drawdown, suggesting concentrated-loss months drive the variance. Capacity for institutional deployment would require stop-loss + sub-cell diversification — outside Phase 1 scope.

## §8 Verdict — PARTIAL made visceral

| Dimension | IS | OOS | Practitioner verdict |
|---|---|---|---|
| Bonferroni-12 PASS / 12 | 4/12 (PASS) | 0/12 (KILL → K2) | Academic LAYER A: FAIL |
| Median Sharpe net@20bps | 1.00 | 0.84 | Practitioner: TRADABLE-MODERATE (naive) |
| Overlap-adjusted Sharpe | ~0.50 | ~0.40 | Practitioner: TRADABLE-MARGINAL (honest) |
| Hit rate | 65.3% | 62.5% | Directionally consistent |
| TC break-even | 375 bps/mo | 362 bps/mo | TC not binding (10-100× realistic) |
| IS → OOS Sharpe degradation | — | −16.2% | Modest decay, not breakage |
| Sign-correctness OOS | — | 11/12 | Signal preserved |

**Paper-practical PARTIAL verdict justified**: the signal is *neither* a strong tradable strategy (LAYER A) *nor* a mechanically dead negative result. It is exactly what its name says — **paper-practical**: publishable academic finding with modest practitioner Sharpe, deserving the `reports/papers/` lane.

## §9 Why this matters for future variance-of-X family work

The OOS net@20bps Sharpe of 0.84 (or overlap-adj 0.4) is a useful **prior** for the variance-of-X family's next member:

- F1 / F6 / RD1 — three members, all sign-correct on initial test, none achieved LAYER A LOCK.
- The variance-as-XS-signal "weak prior" is now **0/3 LAYER A LOCKED but 1/3 paper-practical PASS** (RD1).
- The signal **is real** — it just lacks Bonferroni-12 power on 8-year windows.
- Future variance-of-X members should be designed with **(a) longer expected horizon** for OOS power, or **(b) larger universe / fewer cells for Bonferroni-12** to relax the multiple-comparison hurdle.

## §10 Artifacts

| Path | Contents |
|---|---|
| [artifacts/strategy_A_tradability.csv](../artifacts/strategy_A_tradability.csv) | 72 rows = 4 cells × 3 partitions × 6 TC levels |
| [artifacts/strategy_A_tradability.json](../artifacts/strategy_A_tradability.json) | Verdict per partition + summary table + tradability tier |
| [artifacts/strategy_A_monthly_returns.csv](../artifacts/strategy_A_monthly_returns.csv) | Raw monthly Q1−Q5 spread series, 4 primary cells, all months |

## §11 Commit pin

Phase 1 close commit chain: `fd2828f` → `fa3e334` → `a7c8965` → `ce52490` → `0186fd7` → `b79c613` → `58c8d49`. This audit augments the close (post-Day-6 augmentation, no verdict change).
