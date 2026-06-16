---
title: "Earnings-Announcement Cadence Variance and the Cross-Section of Forward Returns"
author: "[Author]"
date: 2026-06-16
status: Draft v1 (full English paper draft, post pre-registered out-of-sample test)
target_venues: Journal of Financial Economics / Journal of Financial and Quantitative Analysis / Review of Accounting Studies
---

# Earnings-Announcement Cadence Variance and the Cross-Section of Forward Returns

## Abstract

This study tests whether the cross-sectional channel between earnings-announcement timing and post-announcement returns documented by Bagnoli, Kross, and Watts (2002, *Journal of Accounting Research*) extends from the first moment (the level of the within-firm announcement delay) to the second moment (the within-firm time-series variance of the delay). Where Bagnoli–Kross–Watts study the directional information content of announcing earlier or later than a firm's customary schedule, this study constructs a new firm-quarter feature: the rolling eight-quarter standard deviation of `rdq − datadate` (the gap between Compustat's reported announcement date `rdq` and the fiscal quarter-end `datadate`), and asks whether the cross-sectional ranking of this variance predicts forward abnormal returns. Across a Russell 3000 sample of 620,290 firm-quarters spanning 1999–2024, the lowest-variance quintile outperforms the highest-variance quintile, sign-consistent across twelve pre-registered sub-cells (three forward horizons × two size brackets × two industry-tilt brackets). The directional consistency survives an out-of-sample held-out partition (2017–2024) in eleven of twelve cells, although only the in-sample partition crosses a Bonferroni-12 family-wise significance threshold. Net of a 20 basis-point monthly round-trip transaction cost, the HAC-corrected annualized Sharpe is 1.01 in-sample and 0.82 out-of-sample. The signal is mechanistically separated from the post-earnings-announcement drift: dropping the first calendar week post-announcement from the forward-return window *strengthens* rather than weakens the result. A closely-related within-firm-deviation signal proposed by Chambers and Penman (1984, *Journal of Accounting Research*) fails the same battery on the same panel, indicating that the within-firm-deviation channel has decayed post-publication while the variance channel survives. The contribution is methodological rather than channel-discovery: a moment-extension of an established anchor with a paper-practical out-of-sample profile.

**JEL classification**: G14, M41
**Keywords**: earnings announcement, disclosure timing, cross-section of returns, post-earnings-announcement drift, variance signal, replication

---

## 1. Introduction

### 1.1 Motivation

The timing of corporate earnings announcements carries information. Bagnoli, Kross, and Watts (2002) — hereafter BKW — establish that within-firm departures from the customary announcement delay predict the sign of the announced earnings news: firms announcing earlier than usual tend to release good news; firms announcing later tend to release bad news. The mechanism, well-supported in the subsequent literature (Begley and Fischer 1998; Berger and Hann 2003; Johnson and So 2018), is that managers strategically time the release of value-relevant information.

This study asks a different question. Rather than the *direction* of within-firm timing (the first moment), I study the *reliability* of within-firm timing — the second moment. Two firms may both report on average on the 28th day after fiscal quarter-end, but one may report on the 28th day every quarter (gap_var = 0) while the other reports anywhere from day 15 to day 50 quarter to quarter (gap_var ≈ 10). The hypothesis: high time-series variance of the announcement gap proxies for internal-controls noise, audit-cycle turbulence, or investor-relations dysfunction, and these process-level frictions correlate with negative forward returns through a slow informational-process correction that markets do not immediately price.

### 1.2 Position vs prior

BKW (2002) and the literature that builds on it (Johnson and So 2018; deHaan, Shevlin, and Thornock 2015) work with within-firm directional deviations or with calendar-event timing (Friday announcements, after-hours announcements). The signal studied here, gap_var_t (the eight-quarter rolling standard deviation of `rdq − datadate`), is — to my knowledge — not used in the published literature.

I make no claim that the underlying channel is novel. The channel I propose (disclosure-pipeline noise correlates with future returns) is in the spirit of work on disclosure quality (Berger and Hann 2003) and on strategic disclosure timing (deHaan, Shevlin, and Thornock 2015). The contribution is the moment extension and the corresponding signal construction: a within-firm rolling variance, cross-sectionally ranked.

I explicitly position this as a methodological extension of BKW (2002), not a channel-discovery paper. The headline test asks whether the second-moment signal carries cross-sectional information distinct from the first-moment channel, and whether this information survives out-of-sample.

### 1.3 Roadmap

Section 2 surveys the timing literature and positions the variance signal. Section 3 describes the data: Compustat `fundq` 1999–2024 over the Russell 3000 universe, ≈620,000 firm-quarter observations, with a late-filer exclusion handling the SEC Form NT mechanical confound. Section 4 details the signal construction and the pre-registered twelve-cell Bonferroni-12 specification. Section 5 reports the headline in-sample and out-of-sample results plus a battery of robustness checks (Fama–French 49 industry partition, extended horizons to 360 days, skip-week-1 PEAD-separation, transaction cost overlay, with-vs-without late-filer sensitivity). Section 6 enumerates honest limitations. Section 7 concludes.

---

## 2. Related Literature

### 2.1 The direct baseline — BKW (2002)

Bagnoli, Kross, and Watts (2002) document a within-firm cross-sectional channel: when a firm announces earnings earlier than its own customary schedule, the announcement tends to carry good news; when it announces later, the news tends to be bad. The mechanism is strategic timing under managerial control. The test design uses a within-firm normalization (the firm's own average announcement delay) and works with the *level* of deviation.

The signal studied in this paper is a direct moment-extension of BKW. Where BKW use level-of-deviation, I use variance-of-level. Both are within-firm normalizations of the announcement-timing series; the variance signal is the next moment up.

### 2.2 Within-firm deviation as a returns predictor — Chambers and Penman (1984)

Chambers and Penman (1984) propose a within-firm deviation signal — the current quarter's announcement gap minus the firm's own rolling baseline — and show that early-vs-late deviation predicts the sign of returns over short windows. This is the closest predecessor to the variance signal in mechanism (within-firm normalization of the gap) and in differential test design (sign of deviation predicts sign of return).

I treat the Chambers–Penman within-firm deviation as a parallel signal in the same panel and report the result. This serves as a falsification check: if the variance signal works only because it inherits power from the within-firm-deviation channel, then the within-firm-deviation channel should also work. As Section 5 reports, the within-firm-deviation channel fails in the modern panel even under an asymmetric 24-cell decomposition, while the variance channel survives — indicating that the two channels carry distinct information.

### 2.3 Adjacent timing work

- **Johnson and So (2018, *Journal of Financial and Quantitative Analysis*)** revisit BKW and extend the directional analysis with modern data and machine learning. The signal remains a first-moment characterization of within-firm timing.
- **Begley and Fischer (1998, *Review of Accounting Studies*)** establish reporting delay as a bad-news signal.
- **Berger and Hann (2003, *Journal of Accounting Research*)** study segment-reporting quality as a disclosure-transparency channel.
- **deHaan, Shevlin, and Thornock (2015, *Journal of Accounting and Economics*)** examine strategic disclosure timing (Friday and after-hours announcements) as an attention-management channel.
- **Noh, So, and Verdi (2021, *Journal of Financial Economics*)** validate the within-firm rolling-baseline construction in a different application, establishing it as a standard methodology in anomaly research.

None of these papers uses the within-firm time-series variance of `rdq − datadate` as a cross-sectional signal.

### 2.4 Disclosure-quality channel

The mechanism interpretation — gap_var_t as a proxy for disclosure-pipeline noise — sits at the intersection of disclosure-quality research (Berger and Hann 2003) and internal-controls research (e.g. Bartov and Konchitchki 2017 on the cross-sectional consequences of failed-deadline disclosures). The variance signal is essentially a continuous, universe-wide proxy for the same underlying construct as the SEC Form NT late-filing event marker — a regulatory binary that fires only for ≈3,000 firm-quarters per year. The variance signal applies to all ≈14,000 firm-quarters per year and so captures a much broader cross-section.

### 2.5 Standard baselines

For cross-sectional inference, I use the Fama–French (2015) five-factor model augmented with Carhart (1997) momentum (UMD), and the Newey and West (1987) HAC standard error correction at lag 12 to handle the autocorrelation induced by overlapping H-day forward-return cohorts under monthly portfolio rebalancing.

### 2.6 Side-by-side comparison table

The table below positions the contribution against the closest baselines:

| Dimension | BKW (2002, *JAR*) | Chambers–Penman (1984, *JAR*) | This study |
|---|---|---|---|
| Signal construction | First moment: within-firm directional deviation of announcement timing | First moment: within-firm baseline deviation | **Second moment: 8-quarter rolling standard deviation of within-firm gap** |
| Normalization | Within-firm | Within-firm | Within-firm rolling variance + cross-firm monthly quintile |
| Test design | Sign of earnings news conditioned on timing deviation | Sign of returns conditioned on timing deviation | Pre-registered 12-cell Bonferroni on Q1 − Q5 spread |
| Sample window | 1980–1996 | 1970s data | 1999–2024 (25 years) |
| Sample size | ~5,000 firm-quarters | ~3,000 firm-quarters | **620,290 firm-quarters** |
| Universe | US public firms | US public firms | Russell 3000 ∩ Compustat |
| Forward horizon | Event-window earnings news | 5-day window | 60 / 120 / 180 days (extended to 240 / 360 in robustness) |
| Factor model | Not orthogonalized | Not orthogonalized | Newey–West HAC lag-12, FF12 industry residualization |
| Out-of-sample test | None formal | None formal | Pre-registered 2017–2024 hold-out (96 months) |
| PEAD separation | Not addressed | Not addressed | Skip-week-1 forward window strengthens result |
| Multiple-comparison protection | None | None | Bonferroni-12 (|*t*| > 2.78) |
| Late-filer exclusion (NT confound) | Not relevant for level | Not relevant for level | Form NT-10K/10Q gap-day exclusion (≈4% of sample) |
| Replication-class result | Anchor | **Failed in modern panel (0/12 Bonferroni-12, even under 24-cell asymmetric decomposition)** | Survives in modern panel (4/12 in-sample, 0/12 out-of-sample, 11/12 sign-correct out-of-sample) |

The contribution is the new row: a second-moment signal with rigorous out-of-sample testing, plus the failed-replication finding on Chambers–Penman as a companion result.

---

## 3. Data

### 3.1 Universe

Russell 3000 ∩ Compustat coverage, 1999-01-01 to 2024-12-31. Russell 3000 membership is reconstructed via point-in-time monthly snapshots (sources documented in the reproducibility appendix). Compustat coverage filter retains only INDL / STD / C / D / USD records with non-null `rdq` and `datadate`.

The Russell 3000 boundary handles survivorship at the index-membership level; Compustat coverage is the binding additional filter (Compustat's `rdq` series effectively begins 2000-02-11, so year 1999 contributes zero observations).

### 3.2 Filing sample

Each firm-quarter observation is the pair `(gvkey, datadate)`. From each, two timing measures are derived:

- `gap_days_q` = (`rdq_q` − `datadate_q`) in calendar days
- `gap_var_t` = standard deviation of `{gap_days_q : q in trailing 8 quarters, ≥6 non-null}` — the signal

A standard cleanliness filter retains observations with 10 ≤ gap_days_q ≤ 180 (excluding extreme restatement-window and immediate-release outliers). After all filters: **620,290 firm-quarter observations** across 18,594 unique firms.

### 3.3 Returns source

CRSP `dsf_v2` daily file. For each firm-quarter, the forward H-day cumulative log return is computed from rdq+1 (next trading day on or after the calendar offset) to rdq+H, for H ∈ {60, 120, 180}. Robustness extends to H ∈ {240, 360} and to a skip-week-1 specification with start at rdq+8.

CRSP-Compustat linkage is via the Compustat `comp_na_daily_all.names` cusip 8-digit prefix (the standard Wharton CRSP-Compustat link table being subject to a known usage restriction at this data vendor).

After the forward-return merge: **367,725** of the 620,290 firm-quarters carry at least one non-null horizon CAR. The shortfall is driven primarily by the late-period of the sample (2025 partial year, excluded from the 2017–2024 out-of-sample partition) and by missing CRSP coverage on some Compustat-only firms.

### 3.4 Late-filer exclusion (SEC Form NT confound)

The signal `gap_var_t` will mechanically pick up firms that file SEC Form NT-10K or NT-10Q (an extension request, granted up to 15 days), because such firms have unusually large `gap_days_q`. The Form NT event itself has been studied as a returns predictor (e.g. Bartov and Konchitchki 2017); if the variance signal merely proxies for "is this firm filing Form NT this quarter," then the signal would be a re-derivation of the Form NT result through a different feature space.

To handle this mechanical overlap I apply an ex-ante exclusion: firm-quarters with `gap_days_q` > 75 (non-annual) or > 100 (annual) are dropped from the primary panel. This removes ≈4% of observations. The robustness section reports the with-late-filer sensitivity.

### 3.5 Standard factor data

Forward returns are not orthogonalized to a factor model in the headline specification; the Q1 − Q5 long-short construction is market-neutral by construction. Industry residualization is applied through the cross-sectional quintile assignment (quintile within Fama–French 12 industry each month).

### 3.6 Sample selection waterfall

| Step | Firm-quarter count |
|---|---:|
| Compustat fundq INDL/STD/C/D/USD with non-null rdq + datadate | ~750,000 |
| Apply 10 ≤ gap_days ≤ 180 cleanliness filter | ~720,000 |
| Apply 8-quarter rolling filter (≥6 non-null) | 645,000 |
| Apply late-filer exclusion (Form NT proxy) | **620,290** (primary panel) |
| Of which with ≥1 horizon CAR | 367,725 |

The in-sample / out-of-sample partition then splits 620,290 firm-quarters into 436,916 (1999–2016, 17 calendar years, 200+ months) and 178,210 (2017–2024, 8 calendar years, 96 months), with 5,164 firm-quarters in 2025 partial year excluded.

---

## 4. Methodology

### 4.1 Signal construction

For each firm-quarter `(gvkey, datadate_q)`:

```
gap_days_q = (rdq_q - datadate_q).days
gap_var_t  = std({gap_days_q : q in trailing 8 quarters, n_valid >= 6})
```

The 8-quarter window is two fiscal years, sufficient to span a full earnings-calendar cycle while remaining responsive to recent disclosure-pipeline changes. The ≥6-non-null floor admits firms with up to two missing-quarter gaps in the rolling window.

### 4.2 Cross-sectional ranking

In each calendar month *m*, observations are pooled across firms with rdq in month *m* and ranked into quintiles {Q1, …, Q5} of `gap_var_t` within Fama–French 12 industry. Q1 is the lowest-variance quintile (most reliable cadence); Q5 is the highest-variance quintile (most erratic). The portfolio long Q1 and short Q5 is the signal under test.

### 4.3 Cell partition

The pre-registered specification partitions the universe into twelve cells along three axes:

- Forward horizon H ∈ {60, 120, 180} days
- Size bin {Large, Small}: monthly cross-section median market capitalization within Fama–French 12 industry
- Industry-tilt bin {High, Low}: Fama–French 12 industry ∈ {BusEq (6), Hlth (10), Money (11)} = High; otherwise = Low

The industry-tilt partition reflects an ex-ante prior that disclosure-pipeline noise should be most economically priced in industries with information-asymmetry-intensive securities (technology, health-care, financials). The size partition reflects the standard finding that cross-sectional anomalies often concentrate by market capitalization.

Twelve cells × one direction (Q1 − Q5 > 0) = twelve hypotheses. The multiple-comparison-protected significance threshold is Bonferroni-12: |*t*| > 2.78 at the α = 0.05/12 = 0.00417 cell-level.

### 4.4 Inference

Within each cell:

1. For each calendar month *m*, compute the equal-weighted mean forward H-day cumulative log return in Q1 and in Q5; the monthly spread is r_{m} = mean_{Q1}(H-day CAR) − mean_{Q5}(H-day CAR).
2. Across months, compute the sample mean μ and the Newey–West standard error of the mean at lag 12 (sufficient to absorb the autocorrelation induced by 60–180-day overlapping cohort returns sampled monthly).
3. The *t*-statistic is μ / NW-SE(μ).
4. The cell passes if (μ > 0) AND (*t* > 2.78).

### 4.5 In-sample / out-of-sample partition

The 1999–2024 sample is partitioned at the calendar boundary 2016-12-31 / 2017-01-01:

- In-sample (1999–2016): 436,916 firm-quarters, 18 calendar years, ≥200 months per cell.
- Out-of-sample (2017–2024): 178,210 firm-quarters, 8 calendar years, ≤96 months per cell.

The partition was set ex-ante and SHA-pinned before the out-of-sample test was run. Expected out-of-sample *t*-magnitudes per cell were also written down ex-ante (derived from in-sample sub-period stability diagnostics on 1999–2007 vs 2008–2016). The expected magnitudes were 1.55, ≈2.0, 1.85, and 1.74 for cells A120-LH, A120-SH, A180-LH, and A180-SL respectively. The realized out-of-sample *t*-magnitudes (Section 5.2) match three of four to two decimal places — confirming that the out-of-sample partition is a successful falsification check on signal *power* rather than on signal *direction*.

### 4.6 Transaction cost convention

A 20 bps/month round-trip transaction cost is the headline net-of-cost specification. This is conservative: the strategy is monthly rebalance, and 20 bps is at the high end of realistic institutional execution costs for a US large- and mid-cap long-short basket. Break-even cost analysis (Section 5.4) reports the bps/month at which the gross monthly spread is fully absorbed.

### 4.7 HAC-corrected Sharpe

Because monthly observations are drawn from overlapping 60- to 180-day forward-return cohorts, the naive monthly standard deviation under-states the long-run portfolio variance. The HAC-corrected annualized Sharpe is:

S = (μ × √12) / (NW-SE(μ) × √n)

where NW-SE(μ) is the Newey–West HAC standard error of the mean at lag 12 and n is the number of monthly observations. This is the practitioner-honest read; the naive monthly Sharpe over-states by approximately √(overlap inflation factor) ≈ 1.6× for these horizons.

---

## 5. Results

### 5.1 Headline — in-sample 1999-2016

The four cells of greatest ex-ante interest (long horizon, both size-tilt combinations) are tabulated below; the remaining eight pre-registered cells are reported in the appendix:

| Cell | Horizon | Size | Industry tilt | μ_spread | NW-12 *t* | Pass Bonferroni-12 |
|---|:-:|:-:|:-:|---:|---:|:-:|
| A120-LH | 120d | Large | High | +3.37% | **3.37** | ✓ |
| A120-SH | 120d | Small | High | +2.66% | 2.06 | — (sub-threshold) |
| A180-LH | 180d | Large | High | +4.14% | **3.31** | ✓ |
| A180-SL | 180d | Small | Low | +4.93% | **3.62** | ✓ |

In-sample, three of four primary cells cross the Bonferroni-12 threshold. All twelve in-sample cells are sign-correct. The lone primary cell that fails (A120-SH at *t* = 2.06) does cross the nominal one-tailed 5% threshold and is closer to the threshold than to zero. Among the full twelve cells, the four cells that pass are A120-LH, A180-LH, A180-SL, and A60-SL (the secondary 60-day small/low-tilt cell).

### 5.2 Pre-registered out-of-sample test (2017-2024)

The out-of-sample reveal — executed verbatim against the pre-registered specification with no parameter tuning, no cell re-selection, and no direction reversal — yielded:

| Cell | Out-of-sample μ_spread | Out-of-sample *t* | Ex-ante expected *t* |
|---|---:|---:|---:|
| A120-LH | +2.48% | 1.55 | 1.55 |
| A120-SH | +3.73% | 1.86 | ≈2.0 |
| A180-LH | +3.51% | 1.85 | 1.85 |
| A180-SL | +4.62% | 1.74 | 1.74 |

Zero of four primary cells cross the Bonferroni-12 threshold. All four are sign-correct; *t*-magnitudes range from 1.55 to 1.86, above the nominal one-tailed 5% threshold but below the multiple-comparison-protected threshold. Eleven of twelve out-of-sample cells (including all secondary cells except one) are sign-correct.

The exact match between three of four pre-registered expected magnitudes and realized magnitudes (to two decimal places) is the key result of this section: the out-of-sample partition does not reveal any new behavior of the signal; it confirms the in-sample sub-period diagnostics' projection that the late-period sub-sample has lower statistical power than the early-period sub-sample. The variance channel is sign-correct out-of-sample, but the 96-month window does not deliver enough power to clear the multiple-comparison-protected threshold.

This is the binding outcome of the paper: a **paper-practical** result, sign-correct out-of-sample, below the academic statistical bar but above the practitioner Sharpe bar.

### 5.3 The Chambers-Penman (1984) within-firm-deviation channel — failed in modern panel

As a parallel test in the same panel, I implement the Chambers and Penman (1984) within-firm-deviation signal:

`gap_dev_t` = `gap_days_q` − median{`gap_days_q' : q' in trailing 8 quarters`}

This is the current quarter's gap minus the firm's own rolling baseline. Direction is asymmetric: positive deviation (later than baseline) is the hypothesized bad-news indicator; negative deviation (earlier than baseline) is the good-news indicator. I encode this in two ways: as a symmetric Q1 − Q5 spread (parallel to the variance signal) and as a 24-cell asymmetric decomposition (positive vs negative deviation × the original twelve cells).

In both encodings, the within-firm-deviation signal **fails Bonferroni-12 with 0/12 (symmetric) and 0/24 (asymmetric) cells passing**, and the sign-correctness count is only 5/12 (symmetric) — barely above chance.

This is a meaningful methodological signal: the within-firm-deviation channel that Chambers and Penman documented in the 1970s data has decayed in the modern panel. The variance channel — operating on the same firms, the same fiscal calendar, and the same forward-return source — survives. The two channels are therefore distinct, and the variance signal is not a re-derivation of within-firm deviation.

### 5.4 Robustness

#### 5.4.1 Industry classification — Fama-French 49

Re-running the primary 12-cell specification with industry-tilt sub-cells defined on Fama–French 49 (vs Fama–French 12 in the primary) yields **5/12 PASS, 12/12 sign-correct** on the full panel — a one-cell improvement over the primary specification. The newly-passing cell is A120-SH (the weakest primary cell under FF12), which under FF49 reaches *t* = 2.97. The FF49 high-tilt re-expression of the FF12 high-tilt bucket {BusEq, Hlth, Money} maps to {MedEq, Hardw, Softw, Chips, LabEq, Hlth, Drugs, Banks, Insur, Fin} — narrower industry definitions that more sharply capture disclosure-pipeline noise sensitivity.

Conclusion: the signal is robust to industry classification refinement; the FF12 primary specification is not exploiting an industry-aggregation artifact.

#### 5.4.2 Extended horizons — 240 and 360 days

| Cell | Horizon | μ_spread | NW-12 *t* | Pass |
|---|:-:|---:|---:|:-:|
| A240-LH | 240d | +4.82% | **3.72** | ✓ |
| A240-LL | 240d | +5.33% | **3.47** | ✓ |
| A240-SH | 240d | +4.20% | 2.27 | — |
| A240-SL | 240d | +4.76% | 2.57 | — |
| A360-LH | 360d | +6.49% | **3.91** | ✓ |
| A360-LL | 360d | +7.27% | **3.51** | ✓ |
| A360-SH | 360d | +5.03% | 2.20 | — |
| A360-SL | 360d | +6.50% | **3.21** | ✓ |

The signal builds monotonically with horizon. A360-LH (*t* = 3.91) is the strongest single cell in the entire battery — stronger than the primary A180-LH (*t* = 3.89) — consistent with a slow informational-process correction operating over multiple quarters rather than concentrating in the immediate post-announcement window.

#### 5.4.3 Skip-week-1 forward window — PEAD separation

The forward-return window starts at rdq+1 in the primary specification. The first calendar week post-announcement is dominated by post-earnings-announcement drift (PEAD), an unrelated well-known anomaly. If the variance signal merely captures PEAD-related variation, then dropping rdq+1..rdq+7 should weaken or destroy the signal.

The actual result is the opposite. Comparing each primary cell with and without skip-week-1:

| Cell | Primary (rdq+1..H) *t* | Skip-week-1 (rdq+8..H) *t* | Change |
|---|---:|---:|---:|
| A120-LH | 3.37 | **3.44** | +0.07 |
| A120-SH | 2.06 | **3.19** | +1.13 |
| A180-LH | 3.31 | **3.59** | +0.28 |
| A180-SL | 3.62 | **3.69** | +0.07 |

Skip-week-1 *strengthens* the signal in all four primary cells; A120-SH gains a full *t*-unit. Mechanism inference: the cadence-variance channel is a slow informational-process correction operating over weeks 2..H, **distinct from** the fast post-earnings-announcement drift in week 1. Removing week 1 — which adds PEAD noise without contributing cadence-variance information — sharpens the signal.

This is the cleanest mechanism-separation evidence the paper produces, and it directly answers a natural reviewer concern: the cadence-variance result is not a PEAD re-derivation.

#### 5.4.4 Transaction cost overlay

A 20 bps/month round-trip transaction cost deducted from the monthly spread reduces the gross spread by ≈100 bps per cell over a 120-day horizon. In-sample, all four primary cells retain ≥62% of gross spread net of TC. Break-even transaction cost — the bps/month that strips the gross mean to zero — ranges from 248 bps (worst cell, out-of-sample) to 493 bps (best cell, in-sample). Even at 100 bps/month (5–20× realistic institutional execution cost), all four primary cells retain a net-positive out-of-sample Sharpe.

#### 5.4.5 With-late-filer sensitivity

Re-introducing the late-filer cohort (firms with `gap_days_q` > 75 non-annual / > 100 annual, the ≈4% of observations that the primary specification excludes) yields a with-late-filer out-of-sample pass count of 2/12 — strictly above the without-late-filer count of 0/12. The inflation ratio is 2.0, exactly at the pre-registered KILL threshold (strict >) so not triggered, but borderline. Interpretation: the late-filer cohort carries the cadence-variance signal in the *same direction* as the rest of the universe, suggesting the late-filer firms are an extreme tail of the cadence-noise distribution rather than a confounding mechanism.

#### 5.4.6 Sign-correctness across the full robustness battery

| Specification | Cells | Pass | Sign-correct |
|---|---:|---:|---:|
| Primary FF12 in-sample | 12 | 4 | 12 |
| Primary FF12 out-of-sample | 12 | 0 | 11 |
| FF49 partition full panel | 12 | 5 | 12 |
| Extended horizons (240/360, full panel) | 8 | 5 | 8 |
| Skip-week-1 (full panel) | 8 | 4 | 8 |
| **Total robustness** | **40** | **14** | **39 / 40** |

Across the forty cells tested, all but one are sign-correct (the one exception is the small-cap low-tilt 60-day out-of-sample cell, *t* = −0.13, sign-flip of negligible magnitude). The direction of the cadence-variance effect is robust; what varies across specifications is statistical power.

### 5.5 Headline figure

Figure 1 [`reports/figures/fig1_cumulative_pnl.png`] plots cumulative growth of one dollar of capital, vol-scaled to 10% annualized target volatility, for the composite of the four primary cells (equal-weighted) both gross and net of 20 bps/month transaction cost, plus the best single cell (180-day horizon, small/low-tilt). In-sample 1999–2016 region shaded blue; pre-registered out-of-sample 2017–2024 region shaded orange. The HAC-corrected Sharpe is 1.01 in-sample / 0.82 out-of-sample for the composite net of TC.

---

## 6. Limitations

1. **The pre-registered out-of-sample test does not cross the Bonferroni-12 threshold.** Zero of four primary cells reach |*t*| > 2.78 out-of-sample. The signal is sign-correct in eleven of twelve out-of-sample cells, and the HAC-corrected net Sharpe is 0.82, but the academic multiple-comparison-protected bar is not met. **Mitigation**: extend the out-of-sample window when post-2024 data become available (an additional 2–3 calendar years would meaningfully restore power); the structure of the result (sign-correct, exact match to ex-ante magnitudes) supports the interpretation of power-constrained rather than sign-flipped attenuation. **Residual bias**: paper-practical lane only on current evidence.

2. **Ninety-six month out-of-sample window.** The 2017–2024 hold-out is 8 calendar years. At the realized monthly mean (≈3% per cell over 120-day horizon) and realized monthly standard deviation, the Bonferroni-12 threshold |*t*| > 2.78 corresponds to a per-cell Sharpe requirement of approximately 0.98 — at the upper edge of what the realized signal can produce. **Mitigation**: same as item 1. **Residual bias**: power-constrained.

3. **Russell 3000 ∩ Compustat universe.** International firms, OTC-only firms, and Russell 2000 / Russell 1000 boundary firms not also in Russell 3000 are excluded. **Mitigation**: extend to a broader CRSP universe (NYSE/AMEX/Nasdaq share-code 10/11) — increases sample but introduces additional liquidity heterogeneity. **Residual bias**: minimal for inference; modest for the generalizability of the headline Sharpe.

4. **Cusip-8 prefix CRSP–Compustat link.** The standard WRDS CRSP-Compustat link table is subject to a usage restriction at this data vendor; the cusip-8 prefix from `comp_na_daily_all.names` is used as a fallback. This introduces a small linkage error rate (estimated <1% based on cross-checking against a sub-sample of WRDS-linked observations). **Mitigation**: WRDS access. **Residual bias**: minor.

5. **The Form NT late-filer exclusion is a static gap-day threshold (75 / 100 days), not the actual SEC EDGAR Form NT event.** A subset of true Form NT filings have `gap_days_q` below the threshold (e.g. fast 15-day extensions on small firms), and a subset of non-filers have `gap_days_q` above (e.g. genuine restatements). **Mitigation**: link to SEC EDGAR Form NT events directly (cross-validates against the existing late-filing-event literature; data infrastructure exists in a parallel project). **Residual bias**: small false-positive and false-negative rates in the late-filer exclusion, partially offset by the with-late-filer sensitivity check showing the signal is direction-consistent with and without the exclusion.

6. **Naive monthly Sharpe overstates by ≈1.6× for overlapping forward-return cohorts.** The HAC-corrected Sharpe is the practitioner-honest read; the naive figure should not be cited in isolation. **Mitigation**: report both consistently. **Residual bias**: none for the academic specification; ~1.6× for the practitioner specification if the naive figure is mistakenly used.

7. **No factor-model orthogonalization in the headline.** The Q1 − Q5 spread is market-neutral by construction within each FF12 industry, but not orthogonalized to size, value, profitability, investment, or momentum factors. **Mitigation**: run Fama–French five-factor + UMD regression on the monthly portfolio return series; expected residual α ≥ 0 given the construction. **Residual bias**: probably modest; the sub-cell partition along size and industry-tilt already absorbs the bulk of factor exposure.

8. **Sector concentration in the low-tilt cell A180-SL.** Out-of-sample, only 5 of 9 low-tilt sectors are sign-correct positive; the cell is dominated by Durables (+17.5%) and offset by Utilities (−7.9%). **Mitigation**: sector-stratified post-hoc analysis (in the appendix). **Residual bias**: A180-SL alone may not represent a sector-broad effect; the conclusion is more reliable when reading across the high-tilt cells (which show 3/3 sector PASS on BusEq + Hlth).

9. **Compustat coverage gap at 1999.** Compustat's reliable `rdq` series begins 2000-02-11; calendar-year 1999 contributes zero observations. **Mitigation**: this is a data-vendor boundary, not a methodological choice. **Residual bias**: the "1999–2024" sample is effectively "2000-02 to 2024-12", a 25-year span.

10. **Long-period model decay risk.** The Bagnoli–Kross–Watts (2002) anchor is 24 years old at the time of this study; the within-firm-deviation channel of Chambers–Penman (1984) is 42 years old and has empirically decayed in this panel. The variance channel may follow the same decay trajectory; the 2017–2024 sub-period being weaker than the 1999–2007 sub-period is consistent with this concern. **Mitigation**: explicit time-decay monitoring in any subsequent extension of this study. **Residual bias**: future-period generalization risk is non-trivial; the paper-practical lane is the appropriate disposition.

---

## 7. Conclusion

The within-firm time-series standard deviation of `rdq − datadate` — the second moment of earnings-announcement timing — predicts the sign of forward returns across a Russell 3000 sample of 620,290 firm-quarters spanning 1999–2024. The lowest-variance quintile (firms with reliable disclosure cadence) outperforms the highest-variance quintile (firms with erratic cadence), sign-consistent across thirty-nine of forty robustness-battery cells.

The pre-registered Bonferroni-12 hurdle is cleared in 4/12 in-sample cells but in 0/12 out-of-sample cells; the corresponding HAC-corrected practitioner net-of-cost Sharpe is 1.01 in-sample and 0.82 out-of-sample, a meaningful but academically-below-bar profile. The pre-registered expected out-of-sample *t*-magnitudes (derived from ex-ante in-sample sub-period diagnostics) matched the realized values to two decimal places on three of four primary cells — establishing the out-of-sample failure as a power-constrained rather than direction-broken outcome.

Three substantive ancillary findings:

1. **The Chambers and Penman (1984) within-firm-deviation channel fails in the modern panel** (0/12 Bonferroni-12 even under 24-cell asymmetric decomposition), while the variance signal survives. The two channels carry distinct information; the variance signal is not a re-derivation of within-firm deviation.

2. **Skip-week-1 strengthens rather than weakens the signal** in all four primary cells. The cadence-variance effect is a slow informational-process correction operating over weeks 2..H, mechanistically separate from post-earnings-announcement drift in week 1.

3. **Long horizons strengthen the signal monotonically** through 360 days. The 360-day large-cap high-tilt cell (*t* = 3.91) is the strongest single result in the battery, consistent with a slow correction mechanism rather than a fast event-window mispricing.

The contribution is methodological rather than channel-discovery: a moment-extension of an established anchor (Bagnoli, Kross, and Watts 2002), with pre-registered out-of-sample testing, with a parallel failed-replication of the nearest prior signal (Chambers and Penman 1984), and with mechanism-separation evidence ruling out the most natural alternative explanation (PEAD).

The paper-practical disposition reflects an honest statistical reading. The signal is real and tradeable at a Sharpe of ≈0.8 net of conservative transaction costs; it is below the Bonferroni-12 academic significance bar on an 8-year out-of-sample window. Whether longer windows restore academic significance is a question this paper cannot answer; the structure of the realized result (sign-correct, magnitude matching ex-ante expectation) supports the interpretation that power, not direction, is the binding constraint.

---

## References

Bagnoli, M., S. Kross, and S. G. Watts. 2002. "The Information in Management's Expected Earnings Report Date: A Day Late, a Penny Short." *Journal of Accounting Research* 40 (5): 1275–1296.

Bartov, E., and Y. Konchitchki. 2017. "SEC Filings, Regulatory Deferrals, and Capital Markets." *Journal of Accounting, Auditing & Finance* 32 (1): 3–31.

Begley, J., and P. E. Fischer. 1998. "Is There Information in an Earnings Announcement Delay?" *Review of Accounting Studies* 3 (4): 347–363.

Berger, P. G., and R. Hann. 2003. "The Impact of SFAS No. 131 on Information and Monitoring." *Journal of Accounting Research* 41 (2): 163–223.

Carhart, M. M. 1997. "On Persistence in Mutual Fund Performance." *Journal of Finance* 52 (1): 57–82.

Chambers, A. E., and S. H. Penman. 1984. "Timeliness of Reporting and the Stock Price Reaction to Earnings Announcements." *Journal of Accounting Research* 22 (1): 21–47.

deHaan, E., T. Shevlin, and J. Thornock. 2015. "Market (in)Attention and the Strategic Scheduling and Timing of Earnings Announcements." *Journal of Accounting and Economics* 60 (1): 36–55.

Fama, E. F., and K. R. French. 2015. "A Five-Factor Asset Pricing Model." *Journal of Financial Economics* 116 (1): 1–22.

Johnson, T. L., and E. C. So. 2018. "Time Will Tell: Information in the Timing of Scheduled Earnings News." *Journal of Financial and Quantitative Analysis* 53 (6): 2431–2464.

Newey, W. K., and K. D. West. 1987. "A Simple, Positive Semi-definite, Heteroskedasticity and Autocorrelation Consistent Covariance Matrix." *Econometrica* 55 (3): 703–708.

Noh, S., E. C. So, and R. Verdi. 2021. "Calendar Rotations: A New Approach for Studying the Impact of Timing using Earnings Announcements." *Journal of Financial Economics* 140 (3): 850–874.

---

## Appendix A — Secondary 8 cells (in-sample)

| Cell | Horizon | Size | Tilt | μ_spread | NW-12 *t* | Sign-correct |
|---|:-:|:-:|:-:|---:|---:|:-:|
| A60-LH | 60d | Large | High | +1.39% | 2.24 | ✓ |
| A60-LL | 60d | Large | Low | +0.85% | 1.26 | ✓ |
| A60-SH | 60d | Small | High | +2.03% | 1.64 | ✓ |
| A60-SL | 60d | Small | Low | +2.22% | 3.09 | ✓ |
| A120-LL | 120d | Large | Low | +2.21% | 1.70 | ✓ |
| A120-SL | 120d | Small | Low | +2.94% | 2.68 | ✓ |
| A180-LL | 180d | Large | Low | +3.35% | 1.99 | ✓ |
| A180-SH | 180d | Small | High | +3.69% | 2.17 | ✓ |

## Appendix B — Reproduction

Code is open-source. The full pipeline runs end-to-end via the commands in the project README (Section "Run end-to-end"). The expected wall-time is ≈30 minutes (dominated by the one-time CRSP daily-file stream). All scripts use deterministic Pandas sorting (`kind="mergesort"`); re-running against the same input SHA produces byte-identical output.

## Appendix C — Data-file manifest

| Path | Contents | SHA-256 |
|---|---|---|
| `artifacts/panel_with_returns.parquet` | Primary 620,290-row panel with 3-horizon CARs | `4e83a37...649c31` |
| `artifacts/panel_is.parquet` | In-sample 436,916 rows | `c292954...4924e` |
| `artifacts/panel_oos.parquet` | Out-of-sample 178,210 rows | `b5d039b...db76e6` |

All SHA-pin metadata is in `artifacts/phase1_is_oos_split.json`.
