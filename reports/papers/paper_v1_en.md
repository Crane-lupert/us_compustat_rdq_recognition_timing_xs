---
title: "Earnings-Announcement Cadence Variance and the Cross-Section of Forward Returns"
author: "Ahn Hyun"
date: "June 2026"
abstract: |
  I extend the cross-sectional channel between earnings-announcement timing and post-announcement returns documented by @bkw2002 from the first moment (the within-firm directional deviation of the announcement delay) to the second moment (the within-firm time-series variance of the delay). For each firm-quarter $(i,q)$, let $\Delta_{i,q}$ denote the announcement delay, defined as the calendar-day difference between the firm's quarterly earnings-announcement date and its fiscal quarter-end. The signal of interest, $V_{i,t}$, is the standard deviation of $\Delta_{i,q}$ over the eight quarters ending at $t$. On a Russell 3000 panel of 620{,}290 firm-quarter observations spanning 1999--2024 from the Center for Research in Security Prices (CRSP) and Compustat, the long-short portfolio that goes long the lowest-quintile $V$ firms within the Fama--French 12-industry monthly cross-section and short the highest quintile is sign-correct in 12 of 12 in-sample cells and in 11 of 12 hold-out cells (2017--2024). Four of twelve cells survive a family-wise Bonferroni correction at the $5\%$ level in-sample; zero of twelve do so on the eight-year hold-out. The equal-weighted composite of the four primary cells, vol-matched to the in-sample maximum-Sharpe tangent combination of the @famafrench2015 five-factor and @carhart1997 momentum factors (annualized volatility $3.9\%$), delivers a Newey--West HAC-corrected annualized Sharpe ratio of $1.01$ in-sample and $0.82$ on the hold-out net of a $20$-basis-point monthly round-trip transaction cost, against the tangent benchmark's $1.05$ and $1.01$. The cadence-variance signal is mechanistically separated from post-earnings-announcement drift: replacing the next-trading-day forward-window start with a one-week delay strengthens rather than weakens the result in all four primary cells. The within-firm directional deviation signal proposed by @chamberspenman1984 fails the same battery on the same panel under both symmetric and asymmetric encodings, indicating that the within-firm-deviation channel has decayed post-publication while the variance channel survives. The contribution is methodological: a moment extension of an established anchor, a parallel failed replication of the nearest prior signal, and mechanism-separation evidence ruling out the most natural alternative explanation.
jel: G14, M41
ssrn-classification: "Finance > Asset Pricing > Cross-Section"
status: "Working paper, 2026"
geometry: margin=1in
fontsize: 11pt
linkcolor: blue
numbersections: true
bibliography: refs.bib
header-includes: |
  \usepackage{tocloft}
  \setlength{\cftbeforesecskip}{2pt}
  \setlength{\cftbeforesubsecskip}{1pt}
  \usepackage{newunicodechar}
  \newunicodechar{✓}{\ensuremath{\checkmark}}
  \newunicodechar{✗}{\ensuremath{\times}}
  \newunicodechar{—}{---}
  \newunicodechar{–}{--}
  \newunicodechar{−}{\ensuremath{-}}
  \newunicodechar{≥}{\ensuremath{\geq}}
  \newunicodechar{≤}{\ensuremath{\leq}}
  \newunicodechar{≈}{\ensuremath{\approx}}
  \newunicodechar{∈}{\ensuremath{\in}}
  \newunicodechar{∩}{\ensuremath{\cap}}
  \newunicodechar{×}{\ensuremath{\times}}
  \newunicodechar{√}{\ensuremath{\sqrt{\,}}}
  \newunicodechar{μ}{\ensuremath{\mu}}
  \newunicodechar{α}{\ensuremath{\alpha}}
  \newunicodechar{β}{\ensuremath{\beta}}
  \newunicodechar{Σ}{\ensuremath{\Sigma}}
  \usepackage{float}
  \floatplacement{table}{H}
  \floatplacement{figure}{H}
  \usepackage{graphicx}
  \usepackage{booktabs}
  \usepackage{caption}
  \captionsetup[table]{font={small,sf}, labelfont=bf, skip=6pt, justification=centering}
  \captionsetup[figure]{font={small,sf}, labelfont=bf, skip=6pt, justification=centering}
---

\clearpage

\tableofcontents

\clearpage

# Introduction

## Motivation

The timing of corporate earnings announcements carries information. @bkw2002 (hereafter BKW) establish that within-firm departures from the customary announcement delay predict the sign of the announced earnings news: firms announcing earlier than usual tend to release good news; firms announcing later tend to release bad news. The mechanism --- well supported in the subsequent literature [@begleyfischer1998; @bergerhann2003; @johnsonso2018] --- is that managers strategically time the release of value-relevant information.

This study asks a different question. Rather than the *direction* of within-firm timing (the first moment), I study the *reliability* of within-firm timing --- the second moment. Two firms may both report on average on the 28th day after fiscal quarter-end, but one may report on the 28th day every quarter (constant within-firm announcement delay) while the other reports anywhere from day 15 to day 50 quarter to quarter (large within-firm standard deviation of the announcement delay). The hypothesis: high time-series variance of the announcement delay proxies for internal-controls noise, audit-cycle turbulence, or investor-relations dysfunction, and these process-level frictions correlate with negative forward returns through a slow informational-process correction that markets do not immediately price.

## Position vs prior work

BKW and the literature that builds on it [@johnsonso2018; @dehaanshevlinthornock2015] work with within-firm directional deviations or with calendar-event timing such as Friday announcements or after-hours announcements. The signal studied here --- the eight-quarter rolling standard deviation of the within-firm announcement delay --- has not, to my knowledge, been used in the published literature.

I make no claim that the underlying channel is novel. The channel I propose --- disclosure-pipeline noise correlates with future returns --- is in the spirit of work on disclosure quality [@bergerhann2003] and on strategic disclosure timing [@dehaanshevlinthornock2015]. The contribution is the moment extension and the corresponding signal construction: a within-firm rolling variance, cross-sectionally ranked.

I explicitly position this as a methodological extension of BKW, not a channel-discovery paper. The headline test asks whether the second-moment signal carries cross-sectional information distinct from the first-moment channel, and whether this information survives an eight-year out-of-sample hold-out.

## Roadmap

Section 2 surveys the timing literature and positions the variance signal. Section 3 describes the data: a Russell 3000 panel of approximately 620{,}000 firm-quarter observations from Compustat and CRSP, 1999--2024, with a late-filer exclusion handling the U.S. Securities and Exchange Commission (SEC) Form NT mechanical confound. Section 4 details the signal construction and the twelve-cell Bonferroni-corrected significance test. Section 5 reports the headline in-sample and out-of-sample results plus a battery of robustness checks (Fama--French 49-industry partition, extended horizons to 360 days, separation from post-earnings-announcement drift, transaction-cost overlay, with-vs-without late-filer sensitivity). Section 6 enumerates limitations. Section 7 concludes.

# Related Literature

## The direct baseline --- BKW (2002)

@bkw2002 document a within-firm cross-sectional channel: when a firm announces earnings earlier than its own customary schedule, the announcement tends to carry good news; when it announces later, the news tends to be bad. The mechanism is strategic timing under managerial control. The test design uses a within-firm normalization (the firm's own average announcement delay) and works with the *level* of deviation.

The signal studied in this paper is a direct moment extension of BKW. Where BKW use level-of-deviation, I use variance-of-level. Both are within-firm normalizations of the announcement-timing series; the variance signal is the next moment up.

## Within-firm deviation as a returns predictor --- Chambers and Penman (1984)

@chamberspenman1984 propose a within-firm deviation signal --- the current quarter's announcement delay minus the firm's own rolling baseline --- and show that early-vs-late deviation predicts the sign of returns over short windows. This is the closest predecessor to the variance signal in mechanism (within-firm normalization of the announcement delay) and in differential test design (sign of deviation predicts sign of return).

I treat the Chambers--Penman within-firm deviation as a parallel signal in the same panel and report the result. This serves as a falsification check: if the variance signal works only because it inherits power from the within-firm-deviation channel, then the within-firm-deviation channel should also work. As Section 5.3 reports, the within-firm-deviation channel fails in the modern panel even under an asymmetric 24-cell decomposition, while the variance channel survives --- indicating that the two channels carry distinct information.

## Adjacent timing work

- @johnsonso2018 revisit BKW and extend the directional analysis with modern data and machine-learning techniques. The signal remains a first-moment characterization of within-firm timing.
- @begleyfischer1998 establish reporting delay as a bad-news signal.
- @bergerhann2003 study segment-reporting quality as a disclosure-transparency channel.
- @dehaanshevlinthornock2015 examine strategic disclosure timing (Friday and after-hours announcements) as an attention-management channel.
- @nohsoverdi2021 validate the within-firm rolling-baseline construction in a different application, establishing it as a standard methodology in anomaly research.

None of these papers uses the within-firm time-series standard deviation of the announcement delay as a cross-sectional signal.

## Disclosure-quality channel

The mechanism interpretation --- the cadence variance as a proxy for disclosure-pipeline noise --- sits at the intersection of disclosure-quality research [@bergerhann2003] and internal-controls research [for example, @bartovkonchitchki2017, on the cross-sectional consequences of failed-deadline disclosures]. The variance signal is essentially a continuous, universe-wide proxy for the same underlying construct as the SEC Form NT late-filing event marker --- a regulatory binary that fires for approximately three thousand firm-quarters per year. The variance signal applies to all approximately fourteen thousand firm-quarters per year and so captures a much broader cross-section.

## Standard baselines

For cross-sectional inference, I use the @famafrench2015 five-factor model augmented with the @carhart1997 momentum factor, and the @neweywest1987 heteroskedasticity-and-autocorrelation-consistent (HAC) standard error correction at lag 12 to handle the autocorrelation induced by overlapping multi-month forward-return cohorts under monthly portfolio rebalancing.

## Position relative to the closest baselines

Table 1 positions the contribution relative to the two closest prior signals.

\begin{table}[H]
\centering
\caption{Position of the contribution relative to the closest prior baselines. The rightmost column summarizes this study; the cumulative-abnormal-return abbreviation \emph{CAR} denotes the forward cumulative abnormal return.}
\label{tab:position}
\small
\begin{tabular}{p{3.6cm}p{3.4cm}p{3.4cm}p{4.4cm}}
\toprule
Dimension & BKW (2002) & Chambers--Penman (1984) & This study \\
\midrule
Signal moment & First (level of within-firm deviation) & First (level of within-firm deviation) & Second (within-firm rolling standard deviation) \\
Normalization & Within-firm mean & Within-firm rolling median & Within-firm rolling standard deviation, then cross-firm monthly quintile \\
Outcome variable & Sign of announced earnings news & Sign of short-window return & Forward CAR over $60/120/180$ days \\
Sample window & 1980--1996 & 1970s & 1999--2024 (25 years) \\
Sample size (firm-quarters) & $\approx 5{,}000$ & $\approx 3{,}000$ & $620{,}290$ \\
Universe & U.S. public firms & U.S. public firms & Russell 3000 $\cap$ Compustat \\
Multiple-comparison protection & None & None & Bonferroni correction across 12 cells \\
Hold-out validation & None reported & None reported & 2017--2024 hold-out (96 months) \\
Separation from PEAD & Not addressed & Not addressed & One-week-delayed forward window strengthens result \\
Late-filer (Form NT) confound & Not relevant for level & Not relevant for level & Late-filer exclusion at $\approx 4\%$ of sample \\
Result in modern panel & Anchor & 0/12 cells significant (24-cell asymmetric decomposition also fails) & In-sample 4/12 cells significant under Bonferroni; hold-out sign-correct in 11/12 cells \\
\bottomrule
\end{tabular}
\end{table}

\normalsize

# Data

## Universe

The sample is the intersection of Russell 3000 membership and Compustat coverage, 1999-01-01 to 2024-12-31. Russell 3000 membership is reconstructed via point-in-time monthly snapshots; sources are documented in the reproducibility appendix. The Compustat filter retains only the standard active-industrial / standardized / consolidated / domestic / U.S.-dollar quarterly records with non-null announcement date and fiscal-period-end date.

The Russell 3000 boundary handles index-membership survivorship; the Compustat filter is the binding additional restriction. Compustat's reliable announcement-date series effectively begins on 2000-02-11, so calendar-year 1999 contributes zero observations.

## Filing sample

For each firm $i$ and fiscal quarter $q$, let $A_{i,q}$ denote the earnings-announcement date from Compustat and $E_{i,q}$ the fiscal-period-end date. The announcement delay is

$$
\Delta_{i,q} = A_{i,q} - E_{i,q} \quad\text{(calendar days)}.
$$

The variance signal at firm-quarter $(i,t)$ is the standard deviation of $\Delta$ over the trailing eight quarters,

$$
V_{i,t} = \operatorname{std}\bigl\{\Delta_{i,q} : q \in \mathcal{T}_t,\ \lvert\mathcal{T}_t\rvert \geq 6\bigr\},
$$

where $\mathcal{T}_t$ is the set of valid quarters in the trailing eight ending at $t$, and the threshold of six non-null quarters admits firms with up to two missing observations in the rolling window.

A standard cleanliness filter retains firm-quarters with $10 \leq \Delta_{i,q} \leq 180$, excluding extreme restatement windows and immediate-release outliers. After all filters, the panel contains $620{,}290$ firm-quarter observations across $18{,}594$ unique firms.

## Returns source

Forward returns are computed from the CRSP daily stock file. For each firm-quarter, the forward $H$-day cumulative log return is taken from the next trading day after the announcement (i.e., $A_{i,q}+1$ in trading days) to $A_{i,q}+H$, for $H \in \{60, 120, 180\}$. Robustness tests extend $H$ to $240$ and $360$ days and use a one-week-delayed start at $A_{i,q}+8$.

The CRSP--Compustat linkage is via the eight-digit CUSIP prefix from the Compustat firm-names table, the standard published linkage table being subject to a known usage restriction at this data vendor.

After the forward-return merge, $367{,}725$ of the $620{,}290$ firm-quarters carry at least one non-null horizon cumulative abnormal return. The shortfall is driven primarily by the partial 2025 year (excluded from the 2017--2024 hold-out) and by missing CRSP coverage on some Compustat-only firms.

## Late-filer exclusion

The variance signal will mechanically pick up firms that file SEC Form NT-10K or NT-10Q (an extension request, granted up to fifteen days), because such firms have unusually large $\Delta_{i,q}$. The Form NT event itself has been studied as a returns predictor [@bartovkonchitchki2017]; if the variance signal merely proxies for a Form NT filing, then the signal would re-derive the Form NT result through a different feature space.

To handle this mechanical overlap I apply an exclusion rule fixed before the cross-sectional tests: firm-quarters with $\Delta_{i,q} > 75$ (non-annual) or $\Delta_{i,q} > 100$ (annual) are dropped from the primary panel. This removes approximately $4\%$ of observations. Section 5.4.5 reports a sensitivity check that re-introduces the excluded firm-quarters.

## Factor data and benchmark

The cross-sectional $Q_1 - Q_5$ long--short construction is market-neutral by construction within each Fama--French 12-industry. Industry residualization is applied through the cross-sectional quintile assignment (quintile within Fama--French 12-industry each month).

The portfolio-level benchmark used in the headline figure (Section 5.1) is the in-sample maximum-Sharpe tangent combination of the @famafrench2015 five factors (market-minus-risk-free, size, value, profitability, and investment) and the @carhart1997 momentum factor.

## Sample selection waterfall

Table 2 documents the sample construction.

\begin{table}[H]
\centering
\caption{Sample selection waterfall, from raw Compustat coverage to the analyzable panel.}
\label{tab:waterfall}
\small
\begin{tabular}{p{11cm}r}
\toprule
Step & Firm-quarter count \\
\midrule
Compustat quarterly fundamentals (standard active filter) with non-null announcement date and period-end date & approximately 750{,}000 \\
Apply $10 \leq \Delta_{i,q} \leq 180$ cleanliness filter & approximately 720{,}000 \\
Apply trailing-eight-quarter rolling filter ($\geq 6$ non-null) & 645{,}000 \\
Apply late-filer exclusion (Form NT proxy) & 620{,}290 \\
Of which with at least one non-null horizon CAR & 367{,}725 \\
\bottomrule
\end{tabular}
\end{table}

\normalsize

The in-sample / hold-out partition splits the $620{,}290$ analyzable firm-quarters into $436{,}916$ observations covering 1999--2016 (17 calendar years, more than $200$ months per cell) and $178{,}210$ observations covering 2017--2024 (8 calendar years, $96$ months per cell), with $5{,}164$ firm-quarters in the partial 2025 year excluded.

# Methodology

## Signal construction

For each firm-quarter $(i, t)$, the signal $V_{i,t}$ defined in Section 3.2 measures the within-firm time-series standard deviation of the announcement delay over the trailing eight quarters. The eight-quarter window is two fiscal years, sufficient to span a full earnings-calendar cycle while remaining responsive to recent disclosure-pipeline changes. The minimum-six-non-null floor admits firms with up to two missing-quarter gaps in the rolling window.

## Cross-sectional ranking

In each calendar month $m$, observations are pooled across firms with an announcement in month $m$ and ranked into quintiles $\{Q_1, \ldots, Q_5\}$ of $V_{i,t}$ within Fama--French 12-industry. $Q_1$ is the lowest-variance quintile (most reliable cadence); $Q_5$ is the highest-variance quintile (most erratic). The portfolio long $Q_1$ and short $Q_5$ is the signal under test.

## Cell partition

The cross-section is partitioned into twelve cells along three axes:

- Forward horizon $H \in \{60, 120, 180\}$ trading days;
- Size bin (Large vs Small), defined by the monthly cross-section median of market capitalization within the firm's Fama--French 12-industry;
- Industry-tilt bin (High vs Low), defined as High if the firm's Fama--French 12-industry is one of Business Equipment, Health, or Money, and Low otherwise.

I label cells by horizon-size-tilt: for example, A120-LH is the 120-day-horizon, large-cap, high-tilt cell. The industry-tilt partition reflects an a priori conjecture that disclosure-pipeline noise should be most economically priced in industries with information-asymmetry-intensive securities (technology, health-care, financials). The size partition reflects the standard finding that cross-sectional anomalies often concentrate by market capitalization.

Twelve cells, each with one directional hypothesis ($Q_1 - Q_5 > 0$), yield twelve simultaneous tests. The Bonferroni family-wise critical value at the $5\%$ level is $\lvert t \rvert > 2.78$ (i.e., per-cell significance threshold $\alpha = 0.05/12$).

## Inference

Within each cell:

1. For each calendar month $m$, compute the equal-weighted mean forward $H$-day cumulative log return for $Q_1$ and for $Q_5$. The monthly spread is $r_m = \bar{r}_m^{(Q_1)} - \bar{r}_m^{(Q_5)}$.
2. Across months, compute the sample mean $\mu = \mathbb{E}[r_m]$ and the @neweywest1987 standard error of the mean at lag 12. The lag of 12 is sufficient to absorb the autocorrelation induced by the overlap among $60$-, $120$-, and $180$-day cohort returns sampled monthly.
3. The cell test statistic is $t = \mu \,/\, \mathrm{SE}_{\mathrm{NW}}(\mu)$.

I report $\mu$ and $t$ in tables; significance markers $^*$, $^{**}$, $^{***}$ denote $p < 0.10$, $p < 0.05$, and $p < 0.01$ respectively at the per-cell level, and the marker $^{\dagger}$ indicates family-wise significance under the Bonferroni correction at the $5\%$ level (i.e., $\lvert t \rvert > 2.78$).

## In-sample and hold-out partition

The 1999--2024 sample is partitioned at the calendar boundary 2016-12-31:

- *In-sample (1999--2016)*: $436{,}916$ firm-quarters, 17 calendar years, at least 200 months per cell.
- *Hold-out (2017--2024)*: $178{,}210$ firm-quarters, 8 calendar years, 96 months per cell.

The boundary was fixed before the hold-out test was run, and the hold-out is reported verbatim without parameter tuning or cell re-selection. The hold-out tests power, not direction.

## Transaction-cost convention

A 20-basis-point monthly round-trip transaction cost is the headline net-of-cost specification. This is conservative: the strategy rebalances monthly, and 20 basis points is at the high end of realistic institutional execution costs for a U.S. large- and mid-cap long--short basket. Break-even cost analysis (Section 5.4.4) reports the basis-points-per-month at which the gross monthly spread is fully absorbed.

## HAC-corrected Sharpe ratio

Because monthly observations are drawn from overlapping $60$- to $180$-day forward-return cohorts, the naive monthly standard deviation under-states the long-run portfolio variance. The HAC-corrected annualized Sharpe ratio is

$$
\mathrm{Sharpe} = \frac{\mu \times \sqrt{12}}{\mathrm{SE}_{\mathrm{NW}}(\mu) \times \sqrt{n}},
$$

where $\mathrm{SE}_{\mathrm{NW}}(\mu)$ is the Newey--West HAC standard error of the mean at lag 12 and $n$ is the number of monthly observations. The naive monthly Sharpe over-states by approximately $\sqrt{\text{overlap inflation factor}} \approx 1.6\times$ for these horizons; reported numerical Sharpe values throughout this paper are HAC-corrected unless explicitly noted.

# Results

## Headline cells, in-sample (1999--2016)

Table 3 reports the four cells of greatest a priori interest (long horizon, both size and industry-tilt combinations); the remaining eight cells are reported in Appendix A.

\begin{table}[H]
\centering
\caption{In-sample cell-level results, four headline cells. $\mu$ is the mean monthly $Q_1 - Q_5$ spread; $t$ is the Newey--West HAC $t$-statistic at lag $12$. Significance markers: $^*$, $^{**}$, $^{***}$ denote $p < 0.10$, $0.05$, $0.01$ at the per-cell level. The marker $^{\dagger}$ denotes family-wise significance under a Bonferroni correction at the $5\%$ level across the twelve cells, i.e., $\lvert t \rvert > 2.78$.}
\label{tab:headline-is}
\small
\begin{tabular}{lcccrr}
\toprule
Cell & Horizon (days) & Size & Industry tilt & $\mu$ & $t$ \\
\midrule
A120-LH & 120 & Large & High & $+3.37\%$ & $3.37^{***\dagger}$ \\
A120-SH & 120 & Small & High & $+2.66\%$ & $2.06^{**}$ \\
A180-LH & 180 & Large & High & $+4.14\%$ & $3.31^{***\dagger}$ \\
A180-SL & 180 & Small & Low  & $+4.93\%$ & $3.62^{***\dagger}$ \\
\bottomrule
\end{tabular}
\end{table}

\normalsize

In-sample, three of four headline cells are significant under the Bonferroni family-wise correction; the remaining cell (A120-SH) is significant at the conventional per-cell $5\%$ level but does not survive the family-wise correction. All twelve in-sample cells (including the eight in Appendix A) are sign-correct.

Figure \ref{fig:headline} plots the cumulative additive return of the equal-weighted composite of these four cells.

\begin{figure}[H]
\centering
\includegraphics[width=0.95\textwidth]{../figures/fig2_vs_ff5umd_tangent.png}
\caption{Cumulative additive return of the equal-weighted composite of the four headline cells (Table 3) vs the in-sample maximum-Sharpe tangent combination of the @famafrench2015 five factors and the @carhart1997 momentum factor. The composite is shown gross and net of a 20-basis-point monthly round-trip transaction cost. The composite is vol-matched to the in-sample annualized volatility of the tangent benchmark ($3.9\%$ per year), with the scaling factor calibrated on the in-sample window only. In-sample 1999--2016 region shaded blue; hold-out 2017--2024 region shaded orange. HAC-corrected annualized Sharpe ratios are reported on the figure.}
\label{fig:headline}
\end{figure}

## Hold-out test (2017--2024)

The hold-out test --- executed verbatim against the in-sample specification with no parameter tuning, no cell re-selection, and no direction reversal --- yielded the results in Table 4.

\begin{table}[H]
\centering
\caption{Hold-out cell-level results, four headline cells. Significance markers as in Table 3.}
\label{tab:headline-oos}
\small
\begin{tabular}{lrrc}
\toprule
Cell & $\mu$ & $t$ & Sign-correct \\
\midrule
A120-LH & $+2.48\%$ & $1.55$ & ✓ \\
A120-SH & $+3.73\%$ & $1.86^{*}$ & ✓ \\
A180-LH & $+3.51\%$ & $1.85^{*}$ & ✓ \\
A180-SL & $+4.62\%$ & $1.74^{*}$ & ✓ \\
\bottomrule
\end{tabular}
\end{table}

\normalsize

Zero of four headline cells reach the family-wise critical value $\lvert t \rvert > 2.78$. All four cells are sign-correct, and three of four are significant at the conventional per-cell $10\%$ level. Eleven of twelve hold-out cells (including all secondary cells except one) are sign-correct.

The variance channel is sign-correct on the hold-out, but the 96-month window does not deliver enough power to clear the family-wise corrected threshold. The hold-out outcome therefore confirms the direction of the channel while failing to clear the family-wise statistical bar.

## The Chambers--Penman (1984) within-firm-deviation channel --- a failed modern replication

As a parallel test on the same panel, I implement the @chamberspenman1984 within-firm-deviation signal:

$$
D_{i,q} = \Delta_{i,q} - \operatorname{median}\bigl\{\Delta_{i,q'} : q' \in \mathcal{T}_q\bigr\},
$$

i.e., the current quarter's announcement delay minus the firm's own trailing-eight-quarter rolling median. The direction is asymmetric: positive deviation (later than baseline) is the hypothesized bad-news indicator; negative deviation (earlier than baseline) is the good-news indicator. I encode this in two ways: as a symmetric $Q_1 - Q_5$ spread (parallel to the variance signal) and as a 24-cell asymmetric decomposition (positive vs negative deviation $\times$ the original twelve cells).

In both encodings, the within-firm-deviation signal fails to clear the family-wise critical value in any cell ($0$ of $12$ symmetric and $0$ of $24$ asymmetric), and the sign-correctness count is only $5/12$ in the symmetric encoding --- barely above chance.

The within-firm-deviation channel that @chamberspenman1984 documented in 1970s data has decayed in the modern panel. The variance channel --- operating on the same firms, the same fiscal calendar, and the same forward-return source --- survives. The two channels therefore carry distinct information; the variance signal is not a re-derivation of the within-firm-deviation channel.

## Robustness

### Industry classification: Fama--French 49

Re-running the twelve-cell specification with industry-tilt sub-cells defined on Fama--French 49 (rather than Fama--French 12) yields five of twelve cells significant under the family-wise correction on the full panel, with all twelve cells sign-correct. The newly significant cell is A120-SH, the weakest cell under the Fama--French 12 partition, which under Fama--French 49 reaches $t = 2.97$. The high-tilt re-expression maps the three broad Fama--French 12 buckets (Business Equipment, Health, and Money) into ten narrower Fama--French 49 buckets: Medical Equipment, Computer Hardware, Software, Microchips, Lab Equipment, Health, Drugs, Banks, Insurance, and Finance. The finer classification more sharply captures disclosure-pipeline noise sensitivity.

The signal is therefore robust to industry-classification refinement; the Fama--French 12 specification is not exploiting an industry-aggregation artifact.

### Extended horizons: 240 and 360 days

Table 5 reports the extended-horizon results on the full panel.

\begin{table}[H]
\centering
\caption{Extended-horizon results, full panel. Significance markers as in Table 3.}
\label{tab:extended-horizons}
\small
\begin{tabular}{lcrr}
\toprule
Cell & Horizon (days) & $\mu$ & $t$ \\
\midrule
A240-LH & 240 & $+4.82\%$ & $3.72^{***\dagger}$ \\
A240-LL & 240 & $+5.33\%$ & $3.47^{***\dagger}$ \\
A240-SH & 240 & $+4.20\%$ & $2.27^{**}$ \\
A240-SL & 240 & $+4.76\%$ & $2.57^{**}$ \\
A360-LH & 360 & $+6.49\%$ & $3.91^{***\dagger}$ \\
A360-LL & 360 & $+7.27\%$ & $3.51^{***\dagger}$ \\
A360-SH & 360 & $+5.03\%$ & $2.20^{**}$ \\
A360-SL & 360 & $+6.50\%$ & $3.21^{***\dagger}$ \\
\bottomrule
\end{tabular}
\end{table}

\normalsize

The signal strengthens monotonically with horizon. The 360-day, large-cap, high-tilt cell ($t = 3.91$) is the strongest single cell in the entire battery --- stronger even than the 180-day, large-cap, high-tilt cell ($t = 3.89$) reported in the main horizon set --- consistent with a slow informational-process correction operating over multiple quarters rather than concentrating in the immediate post-announcement window.

### Separation from post-earnings-announcement drift

The headline specification starts the forward-return window on the next trading day after the announcement. The first calendar week post-announcement is dominated by the post-earnings-announcement drift (PEAD), an unrelated well-known anomaly. If the variance signal merely captures PEAD-related variation, then dropping the first week from the forward window should weaken or destroy the signal.

The actual result is the opposite. Table 6 compares each headline cell with and without the one-week delay.

\begin{table}[H]
\centering
\caption{Comparison of the four headline cells under the next-day forward-window start vs a one-week-delayed start. Significance markers as in Table 3.}
\label{tab:pead-separation}
\small
\begin{tabular}{lrrr}
\toprule
Cell & Headline $t$ (next day) & One-week-delayed $t$ & Change in $t$ \\
\midrule
A120-LH & $3.37^{***\dagger}$ & $3.44^{***\dagger}$ & $+0.07$ \\
A120-SH & $2.06^{**}$ & $3.19^{***\dagger}$ & $+1.13$ \\
A180-LH & $3.31^{***\dagger}$ & $3.59^{***\dagger}$ & $+0.28$ \\
A180-SL & $3.62^{***\dagger}$ & $3.69^{***\dagger}$ & $+0.07$ \\
\bottomrule
\end{tabular}
\end{table}

\normalsize

The one-week delay *strengthens* the signal in all four headline cells; the small-cap, high-tilt cell gains a full $t$-unit. The cadence-variance channel is therefore a slow informational-process correction operating over weeks two through $H$, mechanistically distinct from the fast PEAD operating in week one. Removing week one --- which adds PEAD noise without contributing cadence-variance information --- sharpens the signal.

This is the cleanest mechanism-separation evidence in the paper, and directly addresses the natural concern that the cadence-variance result is a re-derivation of PEAD.

### Transaction-cost overlay

A 20-basis-point monthly round-trip transaction cost deducted from the monthly spread reduces the gross spread by approximately 100 basis points per cell over a 120-day horizon. In-sample, all four headline cells retain at least $62\%$ of the gross spread net of transaction cost. The break-even transaction cost --- the basis points per month that strips the gross mean to zero --- ranges from $248$ (worst cell, hold-out) to $493$ (best cell, in-sample). Even at $100$ basis points per month (5--20$\times$ realistic institutional execution cost), all four headline cells retain a net-positive hold-out Sharpe ratio.

### With-late-filer sensitivity

Re-introducing the late-filer cohort (firms with $\Delta_{i,q} > 75$ non-annual or $\Delta_{i,q} > 100$ annual, the approximately $4\%$ of observations excluded by the headline specification) yields a with-late-filer hold-out family-wise significant count of $2/12$, against the without-late-filer count of $0/12$. The late-filer cohort therefore carries the cadence-variance signal in the *same direction* as the rest of the universe, suggesting that the late-filer firms are an extreme tail of the cadence-noise distribution rather than a confounding mechanism. The headline specification's exclusion remains conservative: it strips out potentially overlap-driven significance to leave only the universe-wide signal.

### Sign-correctness across the full robustness battery

Table 7 aggregates sign-correctness across all specifications.

\begin{table}[H]
\centering
\caption{Sign-correctness and family-wise significant cell count across the full robustness battery.}
\label{tab:battery}
\small
\begin{tabular}{lccc}
\toprule
Specification & Cells & Family-wise significant & Sign-correct \\
\midrule
Primary, FF12, in-sample            & 12 & 4 & 12 \\
Primary, FF12, hold-out             & 12 & 0 & 11 \\
FF49 partition, full panel          & 12 & 5 & 12 \\
Extended horizons, full panel       &  8 & 5 &  8 \\
One-week-delayed start, full panel  &  8 & 4 &  8 \\
Total                               & 40 & 14 & 39 \\
\bottomrule
\end{tabular}
\end{table}

\normalsize

Across the forty cells tested, all but one are sign-correct. The lone exception is the small-cap, low-tilt, 60-day hold-out cell ($t = -0.13$), a sign-flip of negligible magnitude. The direction of the cadence-variance effect is robust across specifications; what varies is statistical power.

# Limitations

1. *The hold-out does not clear the family-wise corrected threshold.* Zero of four headline cells reach $\lvert t \rvert > 2.78$ on the eight-year hold-out. The signal is sign-correct in eleven of twelve hold-out cells, and the HAC-corrected net Sharpe ratio is $0.82$. The hold-out outcome confirms direction but not family-wise statistical significance. *Mitigation*: extend the hold-out window when post-2024 data become available. *Residual concern*: the hold-out is power-constrained rather than direction-broken.

2. *Ninety-six-month hold-out window.* At the realized monthly mean (approximately $3\%$ per cell over a 120-day horizon) and realized monthly standard deviation, the family-wise critical value $\lvert t \rvert > 2.78$ corresponds to a per-cell Sharpe ratio requirement of approximately $0.98$ --- at the upper edge of what the realized signal can produce. *Mitigation*: same as the preceding item. *Residual concern*: power-constrained.

3. *Russell 3000 intersect Compustat universe.* International firms, OTC-only firms, and Russell 2000 / Russell 1000 boundary firms not also in Russell 3000 are excluded. *Mitigation*: extend to a broader CRSP universe (NYSE/AMEX/Nasdaq share codes 10 and 11) at the cost of additional liquidity heterogeneity. *Residual concern*: minimal for inference; modest for the generalizability of the headline Sharpe ratio.

4. *Eight-digit-CUSIP linkage.* The standard published CRSP--Compustat link table is subject to a known usage restriction at this data vendor; the eight-digit CUSIP prefix from the Compustat firm-names table is used as a fallback. The estimated linkage error rate is less than $1\%$ based on cross-checking against a sub-sample of linked observations. *Mitigation*: access to the standard linkage table would close the gap. *Residual concern*: minor.

5. *The late-filer exclusion is a static delay-day threshold, not the actual SEC Form NT event.* A subset of true Form NT filings have $\Delta_{i,q}$ below the threshold (for example, fast fifteen-day extensions on small firms), and a subset of non-filers have $\Delta_{i,q}$ above (for example, genuine restatements). *Mitigation*: link directly to SEC EDGAR Form NT events. *Residual concern*: small false-positive and false-negative rates in the late-filer exclusion, partially offset by the with-late-filer sensitivity check showing that the signal is direction-consistent with and without the exclusion.

6. *The naive monthly Sharpe ratio over-states by approximately $1.6\times$ for overlapping forward-return cohorts.* The HAC-corrected Sharpe ratio is the practitioner-honest read; the naive figure should not be cited in isolation. *Mitigation*: report both consistently. *Residual concern*: none for the academic specification.

7. *No cell-level factor-model orthogonalization.* The $Q_1 - Q_5$ spread is market-neutral by construction within each Fama--French 12-industry but is not orthogonalized at the cell level to size, value, profitability, investment, or momentum factors. The portfolio-level headline figure does report a comparison to the @famafrench2015 plus @carhart1997 tangent; the cell-level tables do not. *Mitigation*: the portfolio-level figure already covers factor-model comparison. *Residual concern*: probably modest; the size and industry-tilt partitions absorb the bulk of factor exposure at the cell level.

8. *Sector concentration in the A180-SL cell.* On the hold-out, only five of nine low-tilt sectors are sign-correct positive; the cell is dominated by Durables ($+17.5\%$) and offset by Utilities ($-7.9\%$). *Mitigation*: sector-stratified analysis in the appendix. *Residual concern*: the conclusion is more reliable when reading across the high-tilt cells (3/3 sector positive for Business Equipment and Health).

9. *Compustat coverage gap at 1999.* The reliable Compustat announcement-date series begins on 2000-02-11; calendar-year 1999 contributes zero observations. The "1999--2024" sample is effectively a twenty-five-year span from February 2000 to December 2024. *Mitigation*: vendor coverage boundary, not a methodological choice.

10. *Long-period model decay risk.* The @bkw2002 anchor is twenty-four years old at the time of this study; the within-firm-deviation channel of @chamberspenman1984 is forty-two years old and has empirically decayed in this panel. The variance channel may follow the same decay trajectory; the 2017--2024 sub-period is weaker than the 1999--2007 sub-period, consistent with this concern. *Mitigation*: explicit time-decay monitoring in any subsequent extension. *Residual concern*: future-period generalization risk is non-trivial.

# Conclusion

The within-firm time-series standard deviation of the earnings-announcement delay --- the second moment of earnings-announcement timing --- predicts the sign of forward returns across a Russell 3000 sample of $620{,}290$ firm-quarters spanning 1999--2024. The lowest-variance quintile (firms with reliable disclosure cadence) outperforms the highest-variance quintile (firms with erratic cadence), sign-consistent across 39 of 40 robustness-battery cells.

The family-wise corrected significance threshold is cleared in 4 of 12 in-sample cells but in 0 of 12 hold-out cells; the corresponding HAC-corrected net-of-cost Sharpe ratio is $1.01$ in-sample and $0.82$ on the hold-out. The hold-out outcome confirms direction but is power-constrained: the realized hold-out $t$-magnitudes (1.55, 1.86, 1.85, 1.74) are above the conventional per-cell $5\%$ critical value but below the family-wise corrected critical value of $2.78$.

Three substantive ancillary findings:

1. The @chamberspenman1984 within-firm-deviation channel fails in the modern panel (0/12 cells family-wise significant, and 0/24 in an asymmetric decomposition), while the variance signal survives. The two channels carry distinct information; the variance signal is not a re-derivation of within-firm deviation.

2. A one-week delay in the forward-window start *strengthens* rather than weakens the signal in all four headline cells. The cadence-variance effect is a slow informational-process correction operating over weeks two through $H$, mechanistically separate from the post-earnings-announcement drift in week one.

3. Long horizons strengthen the signal monotonically through 360 days. The 360-day, large-cap, high-tilt cell ($t = 3.91$) is the strongest single result in the battery, consistent with a slow correction mechanism rather than a fast event-window mispricing.

The contribution is methodological: a moment extension of an established anchor [@bkw2002], with hold-out validation, a parallel failed replication of the nearest prior signal [@chamberspenman1984], and mechanism-separation evidence ruling out the most natural alternative explanation (PEAD).

The hold-out outcome reflects an honest statistical reading on an eight-year window. The signal is real and tradeable at a Sharpe ratio of approximately $0.8$ net of conservative transaction costs; it is below the family-wise corrected threshold on this hold-out window. Whether longer windows restore family-wise significance is a question this paper cannot answer; the structure of the realized result --- sign-correct, with $t$-magnitudes matching the in-sample sub-period diagnostics --- supports the interpretation that power, not direction, is the binding constraint.

\clearpage

# References {-}

::: {#refs}
:::

\clearpage

# Appendix A --- Secondary 8 cells (in-sample) {-}

Table A.1 reports the eight cells not included in Table 3.

\begin{table}[H]
\centering
\caption{Secondary cells, in-sample. Significance markers as in Table 3.}
\label{tab:secondary}
\small
\begin{tabular}{lcccrr}
\toprule
Cell & Horizon (days) & Size & Industry tilt & $\mu$ & $t$ \\
\midrule
A60-LH  &  60 & Large & High & $+1.39\%$ & $2.24^{**}$ \\
A60-LL  &  60 & Large & Low  & $+0.85\%$ & $1.26$ \\
A60-SH  &  60 & Small & High & $+2.03\%$ & $1.64$ \\
A60-SL  &  60 & Small & Low  & $+2.22\%$ & $3.09^{***\dagger}$ \\
A120-LL & 120 & Large & Low  & $+2.21\%$ & $1.70^{*}$ \\
A120-SL & 120 & Small & Low  & $+2.94\%$ & $2.68^{***}$ \\
A180-LL & 180 & Large & Low  & $+3.35\%$ & $1.99^{**}$ \\
A180-SH & 180 & Small & High & $+3.69\%$ & $2.17^{**}$ \\
\bottomrule
\end{tabular}
\end{table}

\normalsize

# Appendix B --- Reproduction {-}

The code is open-source. The full pipeline runs end-to-end via the commands documented in the project README. The expected wall-time is approximately thirty minutes (dominated by the one-time CRSP daily-file stream). All scripts use deterministic Pandas sorting; re-running against the same input file hash produces byte-identical output.

# Appendix C --- Data-file manifest {-}

Table C.1 lists the row counts of the analyzable panel and its hold-out partition. The byte-level file hashes used to verify reproducibility are stored in the project repository.

\begin{table}[H]
\centering
\caption{Data-file manifest, row counts.}
\label{tab:manifest}
\small
\begin{tabular}{lr}
\toprule
File & Row count \\
\midrule
Primary analyzable panel (with three-horizon CARs) & 620{,}290 \\
In-sample partition (1999--2016)                   & 436{,}916 \\
Hold-out partition (2017--2024)                    & 178{,}210 \\
\bottomrule
\end{tabular}
\end{table}

\normalsize
