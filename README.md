# us_compustat_rdq_recognition_timing_xs

**Missed Earnings Dates and Reporting Regularity: Where the Delay Effect Begins, 2004–2025** — working paper, v2 (November 2026).

Manuscript: [reports/papers/paper_v2_en.md](reports/papers/paper_v2_en.md) ([PDF](reports/papers/paper_v2_en.pdf)) · Korean version: [reports/papers/paper_v2_kr.md](reports/papers/paper_v2_kr.md) · Korean summary: [readme_kr.md](readme_kr.md)

> **Status.** v2 replaces the June 2026 manuscript posted as SSRN 6965838 ("Earnings-Announcement Cadence Variance and the Cross-Section of Forward Returns"). The long–short results of that version do not survive simple returns, calendar-time portfolios and realistic costs, and the period it called a hold-out had been examined before the design was fixed (paper, Appendix B). The SSRN entry is being revised to v2; until that revision is posted, the PDF on SSRN is the earlier version. The earlier README, paper and outline are kept in [reports/papers/archive_v1/](reports/papers/archive_v1/).

## Question

A firm that has not announced earnings by the date implied by last year's announcement tends to have bad news (Chambers and Penman 1984; Penman 1984). The expected date needs nothing but last year's report date, so anyone can compute it a year ahead. Two questions on US data for 2004–2025: does the effect still exist, and where does it begin — for which firms is a single missed day already informative?

## Results

| Test | Sample | Estimate | *t* |
|---|---|---:|---:|
| Specified before returns were computed: firms still silent five trading days after the expected date, held until the day after they report; daily equal-weighted portfolio, Fama–French five factors plus momentum | 2000–2024, 10,809 events | −8.4 bp per day | −4.0 |
| Same, silence verified against SEC 8-K filings (Item 2.02) | 2005–2024, 6,632 events | −12.7 bp per day | −4.8 |
| Firms silent **one** day, irregular reporting history (top third): abnormal return until the day after they report | 2004–2024, 14,091 events | −0.57% | −7.6 |
| Same, regular reporting history (bottom third) | 2004–2024, 13,093 events | +0.03% | 0.4 |
| Irregular minus regular — even years, where the split was found | 2004–2024 | −0.59 pp | −3.9 |
| Irregular minus regular — odd years, held back and run once | 2005–2023 | −0.60 pp | −4.2 |
| Irregular minus regular — 2025, opened last | 2025 | −1.40 pp | −3.3 |
| Late irregular reporters in calendar time, six-factor intercept | 2004–2024 | −7.1 bp per day | −3.5 |
| Irregular minus regular when the firm announces **on time**, announcement day and the next | 161,254 announcements | 0.00 pp | 0.03 |

Reporting regularity is the standard deviation, over a firm's previous eight quarters, of the gap between its actual and expected announcement day. Irregular reporters lose about half of the 0.57% while they are silent and half when they report; 27% of their one-day misses are still silent after five days, against 10% for regular reporters.

## What is not claimed

- **Not a new anomaly.** Late reports have been known to carry bad news since the 1980s. The first two rows replicate that result on a recent sample; the regularity split shows where the effect starts.
- **Not a trading strategy.** A short position in late irregular reporters earns +2.6 bp per day after quoted half-spreads and a 1% borrowing fee (*t* = 1.3). The split is weak among the 1,000 largest firms (−0.18 pp, *t* = −1.1), and the five-day effect has weakened since 2015.
- **The split was found by searching.** 1,904 specifications were evaluated on even years only; ten candidates were frozen before the odd years were opened; eight of them failed there (paper, Table 3). The order of these steps is documented by the author's files, not by a public registry (paper, Section 3.6).
- **Five other tests specified in advance did not pass**, including the opposite hypothesis that a delay is more informative when it comes from a regular reporter (*t* = 0.77, wrong sign).
- The descriptions of the two 1984 articles follow their abstracts and later summaries; the full texts were not consulted.

## Repository layout

| Path | Content |
|---|---|
| `reports/papers/paper_v2_en.md`, `paper_v2_kr.md`, `refs_v2.bib`, `figures_v2/` | Manuscript (pandoc Markdown), Korean version, references, figures |
| `reports/papers/v2/` | `make_tables.py`, `make_figures.py`, `check_numbers.py`, and the aggregate series behind the tables and figures (`tables/`) |
| `scripts/v2/` | Reference implementation by round: `reverify/` and `phase3/` (the June version re-examined), `phase4/` and `checks/` (the pre-specified five-day test and its verification), `phase5/`, `phase6/` (further pre-specified tests), `phase7/` (search, confirmation, follow-up). See [scripts/v2/README.md](scripts/v2/README.md) |
| `docs/v2/` | Specification and protocol documents written before the corresponding results (in Korean), the frozen candidate list, the search log, execution logs |
| `reports/papers/archive_v1/`, `scripts/*.py`, `shared_lib/`, `audits/`, `artifacts/`, `SPEC.md` | The June 2026 analysis, kept as a record |

## Reproduction

```bash
pip install pandas pyarrow numpy duckdb statsmodels scipy matplotlib
export RDQ_V2_WORK=/path/to/workdir          # intermediate tables
export WRDS_DUMP_DIR=/path/to/wrds/extracts  # licensed data, not in this repository
# pipeline order and the remaining settings: scripts/v2/README.md
python reports/papers/v2/make_tables.py
python reports/papers/v2/make_figures.py
python reports/papers/v2/check_numbers.py    # every decimal number of the paper against the logs and tables
cd reports/papers
pandoc paper_v2_en.md --citeproc --standalone --mathml --number-sections -c v2/print.css -o paper_v2_en.html
# print paper_v2_en.html to PDF with a browser (the committed PDF was made with headless Chrome)
```

## Data and licences

Public: SEC EDGAR submission histories and quarterly indexes (8-K item codes, filing dates), Kenneth French's data library. Licensed and not redistributed: CRSP daily stock file, Compustat North America (quarterly fundamentals, names, short interest), I/B/E/S (one auxiliary split).

Source code is released under the [MIT License](LICENSE). The working-paper text and figures are (c) 2026 Hyun Ahn, all rights reserved. See [NOTICE](NOTICE).

## Main references

- Chambers, A. E. and S. H. Penman (1984). Timeliness of reporting and the stock price reaction to earnings announcements. *Journal of Accounting Research* 22(1), 21–47.
- Penman, S. H. (1984). Abnormal returns to investment strategies based on the timing of earnings reports. *Journal of Accounting and Economics* 6(3), 165–183.
- Bagnoli, M., W. Kross and S. G. Watts (2002). The information in management's expected earnings report date: a day late, a penny short. *Journal of Accounting Research* 40(5), 1275–1296.
- Johnson, T. L. and E. C. So (2018). Time will tell: information in the timing of scheduled earnings news. *Journal of Financial and Quantitative Analysis* 53(6), 2431–2464.
- Byun, S., K. C. Roland and D. Kang (2024). The determinants and information effects of earnings announcement date variability. *Journal of Risk and Financial Management* 17(10), 462.
