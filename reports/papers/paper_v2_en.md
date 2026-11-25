---
title: "Missed Earnings Dates and Reporting Regularity: Where the Delay Effect Begins, 2004–2025"
author: "Ahn Hyun"
date: "November 2026 (draft v2 — replaces the June 2026 version)"
abstract: |
  A firm that has not announced earnings by the date implied by last year's announcement tends to have bad news. I revisit this forty-year-old result on recent US data and ask where it begins. In a test specified before returns were computed, firms still silent five trading days after their expected date earn a six-factor alpha of −8.4 basis points per day until they report (t = −4.0; 10,809 events, 2000–2024), and −12.7 basis points when the silence is verified against SEC filings (t = −4.8). One day after the expected date the average silent firm underperforms by only 0.23%. That loss is concentrated in firms whose past announcement dates were irregular: −0.57% until the day after they report (t = −7.6; 14,091 events, 2004–2024), against +0.03% for firms with regular histories. I found this split by searching 1,904 specifications on even-numbered years only. It was one of ten candidates frozen before the odd-numbered years were opened, where it was confirmed (difference −0.60 percentage points, t = −4.2), and it holds on 2025 data opened last (−1.40 points, t = −3.3). Eight of the ten candidates failed. Irregular reporters that announce on time do not underperform. The effect is weak among the 1,000 largest firms and is not statistically significant after trading costs.
jel: G12, G14, M41
ssrn-classification: "Accounting > Financial Accounting"
status: "Working paper, 2026"
geometry: margin=1in
fontsize: 11pt
linkcolor: blue
numbersections: true
bibliography: refs_v2.bib
---

# Introduction

A firm that has not announced its earnings by the date on which it announced a year earlier is, on average, sitting on bad news. The result goes back to @chambers1984 and @penman1984: late reports carry worse news, and the stocks of firms that miss their expected report date underperform until they report. Later work replaced the statistical expected date with dates that firms announce themselves [@bagnoli2002] and with revisions of scheduled dates [@johnson2018; @livnat2015].

This paper returns to the simplest version of the signal — silence past the date implied by last year's announcement, which anyone can compute a year ahead from public filings — and asks two questions on US data for 2004–2025. Does the effect still exist? And where does it begin: for which firms is a single missed day already informative?

1. **The delay effect is still there.** Firms still silent five trading days after their expected date earn a Fama–French five-factor plus momentum alpha of −8.4 basis points (bp) per day until the day after they report (*t* = −4.0; 10,809 events, 2000–2024). The sample, the portfolio rule, the statistic and the threshold were written down before returns were computed. When silence is checked against SEC filings — no 8-K reporting results of operations has been filed — the alpha is −12.7 bp (*t* = −4.8; 6,632 events, 2005–2024), and the 1,014 events in which the firm had in fact already released earnings show nothing (+1.5 bp, *t* = 0.4).
2. **One missed day is informative only for irregular reporters.** One trading day after the expected date the average silent firm underperforms by 0.23% until it reports. Splitting firms by the regularity of their own reporting history — the standard deviation of the gap between actual and expected announcement day over the previous eight quarters — concentrates the loss: irregular reporters (top third) lose 0.57% (*t* = −7.6; 14,091 events), regular reporters (bottom third) gain 0.03% (*t* = 0.4; 13,093 events).
3. **The split survives data it was not chosen on.** I found it by searching 1,904 specifications on even-numbered entry years only. Ten candidates were frozen in writing before the odd-numbered years were opened. This one was confirmed there (irregular minus regular −0.60 percentage points, *t* = −4.2) and again on 2025, opened last (−1.40 points, *t* = −3.3). One other candidate passed — post-earnings-announcement drift, included as a positive control — and eight failed.
4. **It is lateness, not the firm.** When irregular reporters announce on time they earn the same announcement return as regular reporters (difference 0.00 points, *t* = 0.03). About half of the loss of late irregular reporters accrues during the silence and half over the announcement day and the next. Their one-day misses are almost three times as likely to turn into long delays: 27% are still silent after five days, against 10% for regular reporters.

The limits are specific. The split is weak among the 1,000 largest firms (−0.18 points, *t* = −1.1). As a short position the irregular group earns +2.6 bp per day after quoted half-spreads and a 1% borrowing fee (*t* = 1.3), which is not distinguishable from zero. The calendar-time alpha of the five-day signal is close to zero in 2020–2024. The regularity split came out of a search, and an earlier pre-specified test of the opposite idea — that a delay is more informative when it comes from a regular reporter — had failed. I therefore present the result as evidence on where a known effect resides, not as a new anomaly and not as a trading strategy.

**Contribution.** The paper adds two things to the literature on late reporters. It replicates the missed-date effect of the 1980s on a recent, broad sample with point-in-time universes, delisting returns and silence verified against SEC filings. And it reports the returns of firms that have missed their expected date separately by the regularity of their reporting history, which to my knowledge has not been done.^[Descriptions of @chambers1984 and @penman1984 in this paper follow their abstracts and the summaries in @livnat2015 and @johnson2018; I did not have access to the full text of the two 1984 articles.]

**Relation to the earlier version.** This paper replaces the June 2026 version posted under the same SSRN identifier, "Earnings-Announcement Cadence Variance and the Cross-Section of Forward Returns". That version reported that the variability of a firm's announcement dates predicts its returns in a long–short portfolio held for several months. The result does not survive simple returns, calendar-time portfolios and realistic costs, and the period it called a hold-out had been examined before the design was fixed (Appendix B). The present paper keeps the variable and asks where it carries information.

# Related Literature

**Late reports and bad news.** @givoly1982 and @chambers1984 established that earnings reported later than expected tend to be worse, with the expected date in @chambers1984 taken from the same quarter of the previous year. @kross1984 study announcement-window returns of early and late announcers using a firm-specific time-series model of the reporting lag. @penman1984 turns the observation into a strategy: shorting firms that have not reported by their expected date, and closing the position after the report, earned abnormal returns before transaction costs in 1971–1976. @begley1998 confirm with analyst forecast errors that early announcements carry good news relative to late ones, and note that unexpected earnings explain little of the variation in timing.

**Announced and scheduled dates.** @bagnoli2002 use the report dates that managers announce in advance: each day of delay beyond that date goes with earnings about one cent per share below the consensus, and prices fall at the missed date and keep falling as the delay grows. @johnson2018 study firms that schedule their announcement earlier or later than a vendor's expected date, which is largely based on the same quarter of the prior year; firms that advance their date outperform firms that delay it by 2.7% over the following month. Their delaying firms have already published a new date, and they contrast their setting with earlier tests built on missed dates. @livnat2015 report similar results for changes of a tentative date. @dehaan2015, @boulland2017 and @noh2021 study when and how firms schedule announcements and what that does to investor attention.

**Regularity of reporting dates.** Two things come close to the split studied here. @byun2024 treat the variability of annual announcement dates as a firm characteristic and find that more variable firms have a weaker market reaction to earnings and weaker subsequent performance; they do not study late reporters or the period before the announcement. Commercial earnings-calendar products scale the deviation of a confirmed date by the dispersion of the firm's past dates, so that the same deviation counts for more when it comes from a consistent reporter.^[Wall Street Horizon describes its DateBreaks factor as "a modified z-score protocol" that captures how far a confirmed earnings date "deviates or breaks from historical trend (last 5 years) for the same quarter" (wallstreethorizon.com, accessed 25 November 2026).] That intuition motivated my own first test of regularity, which failed (Section 3.6). The result of this paper runs the other way at a one-day delay.

**Predictability and publication.** The positive control in Section 5 is the post-earnings-announcement drift of @bernard1989. Whether any return pattern survives its publication is an open question [@mclean2016], and the missed-date effect has been public for four decades; Section 4 shows what is left of it.

# Data and Design

## Announcement dates and expected dates

Announcement dates are the report dates of quarterly earnings in Compustat (`rdq`). For each firm-quarter the *expected date* $E$ is the announcement date of the same fiscal quarter one year earlier plus one year, moved to the next trading day when it falls on a non-trading day. The prior announcement must fall 1 to 120 days after its fiscal quarter-end. This gives 792,539 expected dates in 2002–2025, of which 524,461 belong to firms linked to CRSP by CUSIP.

## Verifying silence with SEC filings

Compustat's report date is sometimes later than the actual release. I therefore collect the item codes of 1.53 million 8-K filings by 12,576 registrants from EDGAR submission histories. A firm's announcement date is the earlier of the Compustat date and the first 8-K with Item 2.02 (results of operations and financial condition) filed between 30 days before and 150 days after $E$; an 8-K more than 45 days ahead of the Compustat date is treated as belonging to another quarter. The 8-K date is earlier than the Compustat date in 16,861 firm-quarters. A filing history that starts at least 30 days before $E$ is available for 94% of the events used below.

## Universe and events

The universe is the 3,000 largest US common stocks on NYSE, AMEX and NASDAQ by market capitalisation at the end of each June, held fixed from July to the following June. A *delay event of length $k$* occurs when a firm in the universe, with a closing price of at least \$5, has not announced by the close of the $k$-th trading day after $E$. The position is entered at that close and held until the close of the first trading day after the announcement, for at most 40 trading days. A firm has at most one open position at a time. I use $k$ = 1, 3, 5 and 10. There are 42,379 one-day events in 2004–2024, for 5,509 firms, and 2,006 in 2025.

## Reporting regularity

For each event, the *timing deviation* of a past quarter is its actual announcement day minus its expected day, in trading days. Irregularity is the sample standard deviation of the timing deviation over the firm's previous eight announced quarters, with at least six required. It is a close relative of the variable of the earlier version of this paper, the standard deviation of the reporting lag over eight quarters. Events are split at the terciles of the discovery years (Section 3.6): *irregular* reporters have a standard deviation above 3.93 trading days, *regular* reporters at most 2.20. Table 1 describes the groups. Irregular reporters are smaller, cheaper and twice as likely to have reported a loss in the previous quarter; Section 6 asks whether such differences, rather than lateness, explain the result.

**Table 1. One-day-late events by reporting history, 2004–2024.** 1,567 further events have fewer than six prior announcements and belong to no group.

| | Irregular | Middle | Regular |
|---|---:|---:|---:|
| Events | 14,091 | 13,628 | 13,093 |
| Standard deviation of the timing deviation, median (trading days) | 6.0 | 2.9 | 1.6 |
| Size rank in the universe, median | 1,595 | 1,332 | 1,130 |
| Price, median (\$) | 21.3 | 27.3 | 32.9 |
| Loss in the previous quarter, share | 0.30 | 0.21 | 0.15 |
| Days held, mean | 6.3 | 4.5 | 4.0 |
| Still silent five / ten trading days after $E$, share | 0.27 / 0.10 | 0.16 / 0.04 | 0.10 / 0.03 |

## Returns and inference

The *abnormal return* of an event is the stock's cumulative return over the holding period minus the cumulative return of the equal-weighted universe over the same days, with delisting returns included. Event-level returns are winsorized at the 1st and 99th percentiles of the discovery years. Means are tested with standard errors clustered by entry month; differences between groups add entry-year fixed effects. Because event-level tests ignore factor exposures and the overlap of positions in calendar time, I also form daily equal-weighted portfolios of all open positions, use days with at least ten names, and report the intercept of a regression of the excess return on the five factors of @fama2015 and the momentum factor [@carhart1997], with @newey1987 standard errors (five lags). Costs are half the quoted closing bid–ask spread at entry and at exit and a borrowing fee of 1% per year.

## Order of the tests and what "pre-specified" means here {#sec:order}

The tests were run in November 2026 on historical data, in the following order.

1. *A pre-specified family of three.* Before any return was computed, a document fixed three primary tests, a Bonferroni threshold of |*t*| ≥ 2.39 and the requirement of the same sign in both halves of the sample. The first, the five-day missed-date portfolio, passed (Section 4). The other two did not: a premium in the week of the expected date (*t* = 0.87) and a continuation after early versus late announcements (*t* = −0.35).
2. *Three further pre-specified tests*, none of which passed. One of them asked whether the five-day effect is stronger for *regular* reporters, on the view that a delay is a bigger surprise when it comes from a firm that is usually punctual. Regular minus irregular was +0.28 points (*t* = 0.77), the wrong sign. The others conditioned on late periodic reports (*t* = 0.41) and on insider trades before the delay (*t* = 1.18).
3. *A search with a held-out sample.* A protocol written before the search split events by entry year: even years 2004–2024 for discovery, odd years 2005–2023 for confirmation, and 2025 untouched. On the discovery years I evaluated 1,904 combinations of event type, condition, sub-universe and return window; 1,612 had at least 200 events on each side, and 75 of those had |*t*| ≥ 3.0. Ten candidates were written to a dated file. The confirmation code first had to reproduce all discovery numbers; it was then run once on the confirmation years, with the rule "same sign and |*t*| ≥ 2.58". The 2025 data were opened only for candidates that passed.
4. *Descriptive analyses of the confirmed result* (Sections 6 and 7), which select nothing.

The evidence for this ordering is file timestamps on my own machine, not a public registration. The data are historical, and I had worked with the same announcement-date panel for the earlier version of this paper. "Pre-specified" therefore means that the rule preceded the computation, not that the data did not yet exist.

# The Delay Effect, 2000–2024

The pre-specified test takes every firm that has not announced by the fifth trading day after $E$, enters at that close and holds until the day after the announcement. It predates the event table of Section 3 and was run on a separate implementation of the same definitions, with Compustat dates only. Over 2000–2024 the daily equal-weighted portfolio of these positions (10,809 events) has a six-factor intercept of −8.43 bp per day (*t* = −4.02), negative in both halves (−9.14 bp, *t* = −4.17, in 2000–2012; −8.48 bp, *t* = −2.26, in 2013–2024). An independent reconstruction from the raw files, with its own identifier link and universe, gives −8.96 bp (*t* = −4.41).

Compustat's dates overstate silence: in a random sample of 40 events, seven had an earnings 8-K on file before the entry day. Applying the SEC check to all events from 2005 leaves 6,632 verified silent events with an intercept of −12.69 bp (*t* = −4.80), against +1.45 bp (*t* = 0.42) for the 1,014 events in which earnings had already been released. The effect is where it should be. It is weaker in the recent past: −14.89 bp (*t* = −5.40) in 2005–2014 and −9.86 bp (*t* = −1.92) in 2015–2024 for the verified events, and −1.5 bp (*t* = −0.1) in 2020–2024 for the reconstruction.

Table 2 shows how the effect builds with the length of the silence, at the level of events. One day of silence costs 0.23% until the announcement; five days cost 1.07%. The loss per day held is largest for the five-day events.

**Table 2. Abnormal return of silent firms by length of silence, all firms, 2004–2024 (%).** Entry at the close of the $k$-th trading day after the expected date; exit at the close of the day after the announcement (at most 40 days). *t*-statistics clustered by entry month.

| Silent for | Events | Abnormal return | *t* | Days held | 2004–2013 (*t*) | 2014–2024 (*t*) |
|---|---:|---:|---:|---:|---:|---:|
| 1 day | 42,379 | −0.23 | −4.85 | 5.0 | −0.27 (−4.87) | −0.20 (−2.53) |
| 3 days | 21,580 | −0.51 | −7.80 | 5.5 | −0.54 (−6.99) | −0.49 (−4.44) |
| 5 days | 7,730 | −1.07 | −8.49 | 9.5 | −1.08 (−7.12) | −1.05 (−4.89) |
| 10 days | 2,524 | −1.25 | −4.66 | 18.6 | −1.20 (−3.46) | −1.34 (−3.15) |

# Where the Effect Begins

## The search and its confirmation

Table 3 lists the ten candidates frozen after the search, with their discovery and confirmation estimates. Two pass. R01 is the post-earnings-announcement drift, a known effect included to check that the confirmation procedure can detect something real. R05 is the regularity split at a one-day delay. The other eight — including conditions on size, fiscal quarter, prior losses, insider trades and late-filing notices that looked as strong as R05 in the discovery years — do not hold up.

**Table 3. The ten frozen candidates (difference between the condition and its complement, percentage points).** Discovery: even entry years 2004–2024. Confirmation: odd entry years 2005–2023, run once. Pass = same sign and |*t*| ≥ 2.58.

| | Candidate (return window) | Discovery (*t*) | Confirmation (*t*) | |
|---|---|---:|---:|---|
| R01 | After the announcement: top minus bottom third of the earnings surprise, size rank 1001–3000 (days 2–21) | +0.95 (4.90) | +1.22 (7.26) | pass |
| R02 | Silent 3 days: size rank beyond 2000 (20 days) | −1.30 (−4.29) | −0.63 (−2.02) | fail |
| R03 | Silent 1 day: fiscal fourth quarter, size rank 1001–3000 (20 days) | −1.09 (−3.96) | −0.19 (−0.68) | fail |
| R04 | Silent 3 days: loss in the previous quarter (to the announcement) | −1.01 (−3.90) | +0.11 (0.40) | fail |
| **R05** | **Silent 1 day: irregular minus regular reporters (to the announcement)** | **−0.59 (−3.85)** | **−0.60 (−4.21)** | **pass** |
| R06 | Announced 10 or more days late (days 2–21 after the announcement) | −1.50 (−3.50) | −0.44 (−1.28) | fail |
| R07 | Silent 1 day: insiders only sold in the prior 180 days, size rank 1–1000 (20 days) | −1.30 (−3.41) | +0.20 (0.43) | fail |
| R08 | Silent 1 day: an insider bought in the prior 180 days (to the announcement) | +0.77 (3.39) | +0.31 (1.43) | fail |
| R09 | Silent 1 day: late-filing notice in the prior 365 days (10 days) | −0.92 (−3.28) | −0.27 (−0.94) | fail |
| R10 | Week before the expected date: an insider bought in the prior 180 days | +0.34 (3.26) | +0.29 (1.69) | fail |

Table 4 gives R05 by sample. The discovery and confirmation estimates are almost identical, and the 2025 estimate is larger. With controls for size, price, a prior loss, momentum and the prior earnings surprise, the difference is −0.41 points (*t* = −2.70) in the discovery years and −0.59 points (*t* = −3.85) in the confirmation years.

**Table 4. Abnormal return until the day after the announcement, firms silent one day after the expected date (%).**

| Sample | Events, irregular / regular | Irregular (*t*) | Regular (*t*) | Irregular − regular (*t*) |
|---|---:|---:|---:|---:|
| Discovery: even years 2004–2024 | 7,216 / 7,341 | −0.61 (−5.38) | −0.01 (−0.05) | −0.59 (−3.85) |
| Confirmation: odd years 2005–2023 | 6,875 / 5,752 | −0.53 (−5.32) | +0.07 (0.62) | −0.60 (−4.21) |
| 2025, opened last | 503 / 805 | −1.25 (−4.18) | +0.15 (0.32) | −1.40 (−3.28) |
| 2004–2024 | 14,091 / 13,093 | −0.57 (−7.55) | +0.03 (0.35) | −0.59 (−5.65) |

![Mean cumulative abnormal return after the entry day, firms silent one trading day after their expected announcement date, 2004–2024. Fixed windows from the entry day, whether or not the firm has announced. Values in `tables/series_event_time.csv`.](figures_v2/fig1_event_time.png)

![Irregular minus regular reporters, holding-period abnormal return by entry year. Values in `tables/series_by_year.csv`.](figures_v2/fig2_by_year.png)

Figure 1 shows the path in event time: irregular reporters drift down for about three weeks, regular reporters do not. Figure 2 shows the difference year by year. It is negative in 18 of 22 years: nine of the eleven discovery years, eight of the ten confirmation years, and 2025.

## Robustness

**Table 5. Irregular minus regular reporters, one-day delay, 2004–2024.**

| | Estimate | *t* |
|---|---:|---:|
| *Event level (percentage points)* | | |
| 2004–2013 / 2014–2024 | −0.74 / −0.45 | −5.08 / −3.01 |
| Size rank 1–1000 | −0.18 | −1.12 |
| Size rank 1001–2000 | −0.69 | −3.50 |
| Size rank 2001–3000 | −0.69 | −3.28 |
| Silence verified with the 8-K history | −0.57 | −5.29 |
| Fiscal fourth quarter / other quarters | −0.66 / −0.58 | −3.27 / −4.89 |
| Firms never five or more days late in the previous eight quarters | −0.37 | −2.68 |
| Independent implementation (Appendix C), 2005–2024 | −0.46 | −4.30 |
| *Calendar time, six-factor intercept (bp per day)* | | |
| Irregular reporters | −7.10 | −3.48 |
| Regular reporters | +1.22 | 0.50 |
| Irregular minus regular, common days | −7.71 | −2.46 |
| Irregular, entries 2004–2013 / 2014–2024 | −6.53 / −7.81 | −2.87 / −2.13 |
| Irregular, size rank 1–1000 / 1001–3000 | −7.54 / −9.13 | −1.90 / −3.78 |

The difference is present in both halves of the sample and in each of four five-year blocks (−0.88, −0.56, −0.32 and −0.56 points). It is not a small-firm effect in the sense of being confined to the smallest stocks — it is the same size in ranks 1001–2000 and 2001–3000 — but it is not reliably present among the 1,000 largest firms. It does not depend on firms with a record of long delays: among firms that were never five or more days late in the previous eight quarters, whose irregularity comes from moving their date back and forth, the difference is −0.37 points (*t* = −2.68). In calendar time, the portfolio of late irregular reporters has an intercept of −7.1 bp per day; the portfolio of late regular reporters has none.

# Interpretation

## Silence or announcement?

Splitting the holding period at the close of the day before the announcement, late irregular reporters lose 0.28% during the silence (*t* = −6.28; 4.3 days on average) and 0.30% over the announcement day and the next (*t* = −4.46). Late regular reporters lose nothing in either part (−0.01% and +0.05%). The market marks irregular reporters down while they are silent and again when they report; neither part alone accounts for the result.

## Why irregular reporters?

The pre-specified test in Section 3.6 expected the opposite, and the commercial practice of scaling a deviation by the firm's past dispersion embodies the same expectation: one missed day should be more surprising for a punctual firm. The data suggest why this fails at one day. A regular reporter that is one day past its date is usually about to report: 59% have announced by the third day, and only 10% are still silent after the fifth. For such firms a one-day gap is mostly calendar noise — the date implied by last year can fall on a different weekday. An irregular reporter that is one day past its date is silent after the fifth day in 27% of cases and after the tenth in 10%. For these firms the first missed day is the beginning of a real delay more often, and long delays are where the bad news is (Table 2).

Table 6 separates the two channels. Among firms that end up equally late, irregular reporters do worse in every bin, though no single bin is significant. Reweighting regular reporters to the eventual lateness of irregular reporters closes 0.25 of the 0.58-point gap; the remaining 0.33 points arise within bins. Both the higher chance of a long delay and a worse outcome at a given delay contribute. The last rows show the same thing from the investor's side: the longer a firm has already been silent, the less its history adds, and after ten days of silence regular and irregular reporters look alike.

**Table 6. Abnormal return until the day after the announcement (%).** Upper panel: one-day-late events by the lateness finally realised, which is not known at entry. Lower panel: events defined at longer delays.

| | Irregular | Regular | Irregular − regular (*t*) |
|---|---:|---:|---:|
| *Announced on day …* | | | |
| 2 | −0.05 | +0.15 | −0.22 (−1.15) |
| 3 | −0.14 | +0.27 | −0.38 (−1.93) |
| 4–5 | −0.29 | +0.00 | −0.30 (−1.69) |
| 6–10 | −1.01 | −0.80 | −0.26 (−0.61) |
| 11 or later | −2.40 | −1.70 | −0.73 (−0.97) |
| *Silent for …* | | | |
| 1 day | −0.57 | +0.03 | −0.59 (−5.65) |
| 3 days | −0.86 | −0.23 | −0.64 (−4.05) |
| 5 days | −1.37 | −0.77 | −0.68 (−2.05) |
| 10 days | −1.37 | −1.43 | +0.02 (0.03) |

## Lateness or the firm?

Irregular reporters are smaller and less profitable (Table 1), so they might simply earn low returns around earnings announcements whether or not they are late. They do not. Among the 161,254 announcements in 2004–2024 made no later than one trading day after the expected date, irregular reporters earn +0.20% over the announcement day and the next and regular reporters +0.21% (difference 0.00 points, *t* = 0.03); over the five days before the announcement the difference is +0.03 points (*t* = 0.68). In a pooled regression of the announcement-window return on lateness, irregularity and their interaction, the interaction is −0.34 points (*t* = −3.20). Irregular reporters underperform when they are late, and only then.

One comparison goes the other way and should be read with care. In the week that ends one day after the expected date, taking all firms that have not yet announced six days before it, irregular reporters earn 0.16 points less than regular reporters (*t* = −2.34). Regular reporters by construction announce inside that week far more often, and announcements carry a positive average return in both groups, so this difference reflects who announces in the window rather than a general weakness of irregular reporters.

# Implementation

A short position in late irregular reporters earns a six-factor intercept of +7.1 bp per day before costs. After half the quoted spread at entry and exit (the quoted spread averages 25 bp at entry for this group) and a 1% borrowing fee, it earns +2.55 bp per day (*t* = 1.25); +2.36 bp (*t* = 1.04) in 2004–2013 and +2.75 bp (*t* = 0.75) in 2014–2024. Positions are short-lived, so spreads dominate. The portfolio holds at least ten names on 2,654 days, about half of all trading days, with 28 names on average. The five-day signal of Section 4 does better after costs when silence is verified (+6.32 bp per day, *t* = 2.26, with a higher assumed borrowing fee), but only for 2005–2014 (+8.55 bp, *t* = 3.15, against +3.44 bp, *t* = 0.60, in 2015–2024).

An investor cannot always know at the close whether a firm announced after the close. Adding the 11,600 firms that announced on the first day after the expected date as one-day positions leaves the result intact: irregular reporters −0.52% (*t* = −7.75), irregular minus regular −0.53 points (*t* = −5.92).

# Limitations

*The split was found by searching.* The protocol, the frozen candidate list and the single confirmation run limit the damage, and 2025 was not touched until the end, but the evidence for the order of events is private file timestamps. Eight of ten candidates failed confirmation, which is a reminder of what discovery-sample *t*-statistics of 3 to 4 are worth after 1,904 looks.

*The expected date is crude.* Last year's date plus one year ignores weekday conventions and changes in a firm's reporting calendar. If last year's announcement was unusually early, a normal report this year is labelled late. This noise is larger for irregular reporters, which should weaken the measured effect for them rather than create it, but a better expected-date model could change the picture at a one-day delay.

*It is not a new mechanism.* Late reports have been known to carry bad news since the 1980s. What this paper adds is where the effect starts.

*It is not a strategy.* The effect is absent among the largest firms and does not survive costs with statistical significance. The five-day effect has weakened since 2015.

*One year of record.* The 2025 estimate is one year, 503 irregular and 805 regular events.

# Conclusion

Forty years after it was first documented, the stock of a firm that has not reported by the date implied by last year's announcement still underperforms until it reports. For most firms a single missed day says little. For firms whose reporting dates have been irregular, the first missed day already predicts underperformance, during the silence and at the announcement, in the years used to find the pattern, in the years held back to confirm it, and in the year opened last. The same firms earn ordinary returns when they report on time.

# References

::: {#refs}
:::

# Appendix A: Definitions {-}

- *Expected date* $E$: the Compustat report date of the same fiscal quarter one year earlier, plus one year, moved to the next trading day if needed.
- *Announcement date*: the earlier of the Compustat report date and the first 8-K with Item 2.02 filed between $E$ − 30 days and $E$ + 150 days (when the firm's 8-K history starts at least 30 days before $E$).
- *Delay event of length $k$*: no announcement by the close of trading day $E + k$; entry at that close; exit at the close of the first trading day after the announcement or after 40 trading days.
- *Timing deviation*: announcement day minus expected day, in trading days. *Irregularity*: sample standard deviation of the timing deviation over the previous eight announced quarters (at least six). Irregular: above 3.93; regular: at most 2.20 (terciles of the discovery years).
- *Abnormal return*: cumulative stock return minus cumulative return of the equal-weighted universe over the same days. Winsorized at −28.5% and +27.1% for the holding period of one-day events (1st and 99th percentiles of the discovery years).
- *Universe*: 3,000 largest US common stocks (NYSE, AMEX, NASDAQ) by market capitalisation at the end of June, from July to the following June; price of at least \$5 at entry.

# Appendix B: The Earlier Version {-}

The June 2026 version sorted firms, within industries, on the standard deviation of their reporting lag (days from fiscal quarter-end to the announcement) over the previous eight quarters, and reported that a long–short portfolio on this variable earned a net Sharpe ratio of 1.01 in 2000–2016 and 0.82 in a 2017–2024 hold-out, in a Russell 3000 universe. Re-examination found the following.

- The test statistic was a difference of mean *log* returns. With simple returns, none of the twelve pre-specified cells is significant in 2000–2016 at the paper's own threshold.
- The 2017–2024 period was not a hold-out: its *t*-statistics appear in the document that fixed the design.
- Index membership was not applied; the universe was Compustat firms linked to CRSP.
- The borrowing cost was charged for one month, while positions were held for four to six months.
- With a point-in-time universe of the 3,000 largest stocks, simple returns, calendar-time portfolios, quoted spreads and borrowing fees over the holding period, one of twelve cells reaches the threshold in 2000–2016 (not one of the four primary cells) and none in 2017–2024. The composite of the four primary cells earns +0.37% per month before costs in 2000–2016 (*t* = 1.78) and +0.13% in 2017–2024, and −0.16% and −0.31% per month after costs.
- The earlier version also stated that the early-versus-late announcement effect had disappeared. With the quantiles in the right direction and a three-day announcement window, firms that announce earlier than in the previous year outperform firms that announce later by 0.56% (*t* = 4.3) in 2000–2016 and 0.73% (*t* = 3.8) in 2017–2024.

# Appendix C: Independent Recomputation {-}

The regularity split was recomputed on a different event table: one-day-late events built separately from Compustat dates only, with their own identifier link, universe and silence rule; irregularity measured in calendar days with terciles formed within each entry year; returns computed by calendar date against a separately built universe series. Over 2005–2024 (40,414 events) irregular reporters earn −0.49% (*t* = −5.58) and regular reporters −0.02% (*t* = −0.30); the difference is −0.46 points (*t* = −4.30). It is −0.55 points (*t* = −4.27) in 2005–2014 and −0.36 points (*t* = −2.07) in 2015–2024, −0.13 points (*t* = −0.78) in size ranks 1–1000 and −0.55 points (*t* = −3.84) in ranks 1001–3000. In this implementation the estimate is smaller in the even years (−0.29 points, *t* = −1.86) than in the odd years (−0.64 points, *t* = −4.27), the reverse of what selection on the even years would produce.

# Appendix D: Replication {-}

The replication package contains the specification and protocol documents, the frozen candidate list, the search log with every round, the scripts and logs of each step, and the scripts that produce the tables and figures of this paper. CRSP and Compustat data are licensed and are not included; the 8-K item codes come from public EDGAR submission histories.
