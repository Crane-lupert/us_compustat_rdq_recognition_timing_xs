---
date: 2026-06-19
phase: 1 (augmentation, post-close, post-tradability, post-deferred-robustness, post-PIT-clean)
repo: us_compustat_rdq_recognition_timing_xs
project_id: RD1-merged-RD7
script: scripts/phase1_robustness_borrow_overlay.py
artifacts:
  - artifacts/strategy_A_borrow_overlay.{csv,json}
  - artifacts/strategy_A_borrow_overlay_monthly.csv
verdict_summary: |
  Size-differentiated borrow on the short leg alone (Scenario S1) costs
  the composite Sharpe ~22pct in-sample (1.02 to 0.80) and ~19pct out-of-
  sample (0.84 to 0.68). Excluding sub-$5 short names (S2) collapses IS
  Sharpe to 0.13 (-87pct) and pushes OOS to 0.42 (-50pct) -- the signal
  depends substantively on penny-stock short exposure. Restricting the
  short basket to mid + large cap ($2B+) with $5+ price (S4) recovers
  some IS Sharpe (0.59) but pushes OOS to 0.30. The conclusion: under
  realistic stock-borrow conditions, the strategy still produces
  positive risk-adjusted return on the held-out window, but the
  headline 0.84 OOS Sharpe is materially shaved (to 0.30-0.68
  depending on how aggressive the borrow filter is).
---

# Realistic Borrow Overlay Robustness Check

## §1 Motivation

The transaction-cost convention used throughout the rest of the project is a flat 20 basis-points-per-month round-trip applied uniformly to every firm. That is conservative for execution on the long leg but understates the realistic stock-borrow fee on the short leg, which scales sharply with market capitalization and often excludes hard-to-borrow (HTB) or penny-stock names entirely.

The variance-of-cadence signal places the highest-variance firms in the short basket. Those firms are systematically skewed toward smaller market capitalization and lower share price (see §3 distribution), which are precisely the names where stock-borrow is most expensive or unavailable. The headline net Sharpe of 0.84 on the hold-out is therefore an upper bound on what a realistic short-side trade would deliver.

This audit estimates the realistic-borrow Sharpe under five overlay scenarios that progressively tighten the short-side admissible universe.

## §2 Borrow-fee schedule and scenario definitions

### §2.1 Annualized borrow-fee schedule

Calibrated to standard U.S. stock-loan conventions (S&P 500 large-caps borrow at 25 bps/yr or less; small-caps median ~200 bps/yr; micro-caps frequently 500-2,000 bps/yr; nano-caps often unborrowable at any cost):

| Market cap (USD millions) | Annualized borrow fee (bps/yr) |
|---|---:|
| ≥ 10,000 | 25 |
| 2,000 ≤ mcap < 10,000 | 50 |
| 300 ≤ mcap < 2,000 | 200 |
| 100 ≤ mcap < 300 | 800 |
| < 100 | 2,000 |

The borrow drag per month is computed as the equal-weighted mean of (annualized bps / 12 / 10,000) over the firms in the surviving Q5 short basket that month, subtracted from the gross Q1 − Q5 spread.

### §2.2 Five scenarios

| Scenario | Definition |
|---|---|
| **S0** | Baseline: flat 20 bps/month round-trip, no borrow differentiation. Matches the headline specification used elsewhere in the paper. |
| **S1** | S0 + add size-differentiated borrow on the short leg (per §2.1 schedule). |
| **S2** | S1 + drop short names with announcement-day closing price below $5 (penny / HTB exclusion). |
| **S3** | S2 + drop short names with market cap below $100M (nano-cap exclusion). |
| **S4** | Aggressive realism: short basket restricted to firms with market cap ≥ $2B and price ≥ $5, with size-differentiated borrow applied to the survivors. |

## §3 Borrow-tier distribution on the full panel

Distribution of the 620,290 firm-quarters across the five borrow tiers:

| Annualized borrow (bps/yr) | Count | Pct of panel |
|---|---:|---:|
| 25 (mcap ≥ $10B) | 53,202 | 8.6% |
| 50 ($2B-$10B) | 87,419 | 14.1% |
| 200 ($300M-$2B) | 151,413 | 24.4% |
| 800 ($100M-$300M) | 87,236 | 14.1% |
| 2,000 (< $100M) | 241,020 | **38.9%** |

The panel is dominated by sub-$100M nano-caps (38.9%), which carry the punitive 2,000 bps/yr borrow assumption and are often unborrowable in practice. This is structural: Compustat coverage extends well below the Russell 3000 lower bound. The Q5 (high-variance) sub-population skews further toward these tiers, which is the source of the realistic-borrow Sharpe shaving documented below.

## §4 Composite results across scenarios

Four pre-specified primary cells (A120-LH, A120-SH, A180-LH, A180-SL), equal-weighted composite:

| Scenario | HAC Sharpe IS | HAC Sharpe OOS | Annualized return IS | Annualized return OOS |
|---|---:|---:|---:|---:|
| **S0** baseline | **+1.02** | **+0.84** | +45.5% | +42.6% |
| S1 size-borrow | +0.80 | +0.68 | +34.9% | +34.8% |
| S2 + sub-$5 drop | +0.13 | +0.42 | +4.6% | +23.7% |
| S3 + nano-cap drop | +0.21 | +0.67 | +9.5% | +35.4% |
| S4 mid+large only | +0.59 | +0.30 | +36.5% | +11.3% |

### §4.1 Reading

- **S0 → S1 (add size-differentiated borrow, no exclusions)**: composite Sharpe loses 22% IS (1.02 → 0.80) and 19% OOS (0.84 → 0.68). The size-differentiated borrow alone is a meaningful but not destructive overlay.

- **S1 → S2 (drop sub-$5 short names)**: composite IS Sharpe collapses from 0.80 to 0.13 (−84%) while OOS retains 0.42. The collapse on IS is the dominant evidence that **a substantial fraction of the in-sample signal comes from penny-stock short positions** — exactly the names that are often hardest to borrow. The OOS drop is milder (0.68 → 0.42, −38%) because the OOS period had less penny-stock contribution.

- **S2 → S3 (additionally drop sub-$100M nano-caps)**: composite IS Sharpe recovers slightly to 0.21 and OOS lifts to 0.67. This is counter-intuitive at first but reflects that the firms in the $100M-$300M / $5+ tier carry a stronger signal than the sub-$100M tier; removing nano-caps stops them from diluting the surviving basket.

- **S4 (mid + large only, $2B+, $5+)**: composite Sharpe 0.59 IS / 0.30 OOS, with annualized returns 36.5% / 11.3%. This is the institutional-deployment-feasible scenario. Per-cell, A120-SH has surviving Q5 fraction 0% (no Q5 firm in the small-high-tilt cell is also ≥ $2B and ≥ $5) and A180-SL has surviving Q5 fraction 2%. So the institutional version of the strategy effectively reduces to the two large-cap-high-tilt cells (A120-LH, A180-LH) plus a thin contribution from the surviving small-cap names. The two large-cap-high-tilt cells alone deliver Sharpe ~0.55-0.70 IS / 0.58-0.66 OOS under S4, which is the institutional-realistic core of the strategy.

### §4.2 Per-cell breakdown under S4 (institutional-realistic)

| Cell | Surviving Q5 fraction | Mean Q5 borrow (bps/yr) | Sharpe IS | Sharpe OOS |
|---|---:|---:|---:|---:|
| A120-LH | 26% | 43 | +0.70 | +0.66 |
| A120-SH | 0% | n/a | n/a | +0.29 |
| A180-LH | 27% | 43 | +0.55 | +0.58 |
| A180-SL | 2% | 50 | +0.02 | −0.60 |

Under S4, the strategy is essentially **two cells**: A120-LH and A180-LH (large-cap, high-tilt). Both deliver Sharpe ~0.55-0.70 IS and 0.58-0.66 OOS at a borrow cost of approximately 43 bps/yr — a meaningfully positive risk-adjusted return on an institutionally tradeable subset.

## §5 Implications for the paper-practical disposition

The headline disposition (paper-practical PARTIAL — family-wise corrected significance not cleared on the 8-year hold-out) is unchanged. What the borrow overlay adds:

1. **Realistic execution Sharpe is materially below the 0.84 headline**. Under the size-differentiated borrow alone (S1), composite OOS Sharpe is 0.68; under any restrictive filter (S2-S4), composite OOS Sharpe ranges from 0.30 to 0.67.

2. **The strategy retains positive realistic-borrow Sharpe on the institutional-deployable subset (S4)**. Composite OOS Sharpe 0.30 with annualized return 11.3% net of all costs is below the academic significance bar but is not zero. The mid+large-cap-only core (A120-LH + A180-LH) carries this contribution.

3. **A substantial part of the in-sample signal sits in penny / nano-cap short positions**. This is consistent with the cross-sectional anomaly literature, where small-cap shorts are commonly the source of un-arbitraged premia. It does not invalidate the channel; it does mean that **scaled deployment requires either a small-cap-focused borrow ledger or restriction to the large-cap subset with a lower Sharpe**.

4. **Comparison to V5 (sister project)**: the V5 NT late-filing recurring-filer XS short collapsed to Sharpe −0.65 to −0.81 under sub-$5 borrow restriction. RD1's borrow-restricted Sharpe (S4 OOS 0.30) is materially better — the variance-of-cadence signal survives the realistic-borrow filter better than the NT recurring-filer signal does, presumably because RD1 is universe-wide and the large-cap-high-tilt cells are intrinsically part of the signal rather than a corner case.

## §6 Honest framing for downstream documents

For the paper (§5.4.x), add a borrow-overlay sub-section with the S0-S4 table and the institutional-realistic conclusion: the strategy delivers approximately Sharpe 0.30-0.68 OOS depending on how aggressively the short universe is restricted, with the headline 0.84 representing the no-borrow-cost-differentiation upper bound.

For the LinkedIn post, the "Borrow cost on the short leg" caveat is now quantitatively backed: the size-differentiated borrow alone shaves ~20% off the headline; restriction to a borrowable institutional universe shaves another 30-60% on OOS depending on the cutoff.

For the deployment-decision framing in the career-workspace deep-dive (Part 19), update §7 limitations + §8 outcome-class to cite the borrow-overlay numbers explicitly.

## §7 Lock F compliance

- `scripts/phase1_robustness_borrow_overlay.py` re-uses `strategy_A_bonferroni.py` core functions (Lock F-compliant) for the quintile assignment and HAC standard error.
- The borrow filter is a deterministic function of `mcap_mil` and `price` (no sort-dependent operations).
- Re-runs against the same input panel produce byte-identical output.

## §8 Artifacts

| Path | Contents |
|---|---|
| [scripts/phase1_robustness_borrow_overlay.py](../scripts/phase1_robustness_borrow_overlay.py) | Borrow overlay sweep across S0-S4 |
| [artifacts/strategy_A_borrow_overlay.csv](../artifacts/strategy_A_borrow_overlay.csv) | Per-(scenario, cell) row: mean borrow bps, surviving Q5 fraction, IS / OOS Sharpe, annualized return |
| [artifacts/strategy_A_borrow_overlay.json](../artifacts/strategy_A_borrow_overlay.json) | Composite-summary verdict + tier distribution + scenario descriptions |
| [artifacts/strategy_A_borrow_overlay_monthly.csv](../artifacts/strategy_A_borrow_overlay_monthly.csv) | Monthly composite Q1−Q5 spread series per scenario (for figure use) |
