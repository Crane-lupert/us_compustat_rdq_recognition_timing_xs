# v2 reference implementation

Code behind `reports/papers/paper_v2_en.md` ("Missed Earnings Dates and Reporting Regularity: Where the Delay Effect Begins, 2004–2025").

The scripts were run in November 2026 in a separate verification workspace and copied here with their absolute paths replaced by environment variables (`v2paths.py`, one copy per folder). After the move, the following were run from this location against the workspace tables:

| Run from this location | Result |
|---|---|
| `reports/papers/v2/make_tables.py` | log and all four tables identical to the stored ones |
| `phase4/s03_r1.py` (the pre-specified five-day test) | log identical; hashes of the output files unchanged |
| `checks/r1_sec_validation.py` (analysis step, cached filings) | −12.69 bp, *t* = −4.80; output table unchanged |
| `phase5/p5_10_rdq_regularity.py`, `phase6/p6_01_rdq_insider.py` | output tables unchanged; logs in `docs/v2/logs/phase5/rdq_r_run.log.txt`, `phase6/` |
| `phase7/p7_43_r05_by_delay_length.py`, `phase7/p7_45_r05_placebo.py` | logs identical |
| `reports/papers/v2/check_numbers.py` | all 392 decimal numbers of the paper are found in the logs and tables of this repository |

## Folders

| Folder | Paper | What it does |
|---|---|---|
| `reverify/` | Appendix B | The June 2026 version re-examined: CRSP daily extracts (`s01`, `s01b`), rebuild of the published panel and returns (`s03`, `s04`), the published statistic and its variants with simple returns (`s05`, `s05b`, `s05c`), calendar-time portfolios (`s06`), decomposition of the published Sharpe ratio (`s07`), early versus late announcers (`s08`, `s08b`), skip-week, link and universe checks (`s09`–`s11`), borrowing cost (`s12`) |
| `phase3/` | Appendix B | Corrected re-run of the June design with the choices frozen in `FROZEN_PARAMS.json`: panel (`p01`), point-in-time link and universe (`p02`), cells (`p03`), calendar-time portfolios and statistics (`p04`, `p05`), cohort check, unobserved quarters, announcement-window effect, delisting returns (`p06`–`p09`), tables (`p10`) |
| `phase4/` | Sections 3.6 and 4 | The pre-specified family of three: link and events without returns (`s01`, `s02`), the five-day missed-date portfolio R1 (`s03`), the expected-date-week premium R2 (`s04`), early versus late announcers R3 (`s05`), look-ahead and double-count checks (`s06`), result tables (`s07`). Frozen choices in `FROZEN_PARAMS.json` |
| `checks/` | Sections 4 and 7 | Independent reconstruction of R1 from the raw files (`r1_phase4_check.py`); silence verified against 8-K Item 2.02 (`r1_sec_validation.py`); the verified events net of costs (`r1_verified_net_of_costs.py`, written on 2026-11-25); filing histories for the round-2 test (`rdq2_fetch_filings.py`) |
| `phase5/`, `phase6/` | Section 3.6, item 2 | Three further pre-specified tests, none of which passed: late periodic reports (`p5_01`, `p5_02`; `p5_03` is exploratory), regular versus irregular reporters at a five-day delay (`p5_10`), insider trades before the delay (`p6_01`) |
| `phase7/` | Sections 3, 5, 6, 7 and Appendix C | The search with a held-out sample: 8-K item panel (`p7_01`), Compustat quarterly extract (`p7_02`), event tables (`p7_20`), search on even years (`p7_22`), the same with controls (`p7_23`), the single confirmation run on odd years (`p7_30`), follow-up of the confirmed candidate — calendar-time intercepts, costs, the 2025 record (`p7_40`), same-day announcers (`p7_41`), independent recomputation (`p7_42`), delay length (`p7_43`), silence versus announcement (`p7_44`), on-time announcers (`p7_45`). Shared helpers in `p7lib.py`, which refuses to compute returns for a stage the caller has not asked for |
| `../../reports/papers/v2/` | all tables and figures | `make_tables.py`, `make_figures.py`, `check_numbers.py` |
| `../../docs/v2/` | Section 3.6 | The specification and protocol documents written before the corresponding results (`PHASE3_SPEC.md` to `PHASE7_SEARCH_PROTOCOL.md`, in Korean), the frozen candidate list (`CANDIDATES.md`), the search log (`SEARCH_LOG.md`) and the execution logs (`logs/`) |

## Configuration

```bash
export RDQ_V2_WORK=/path/to/workdir                # intermediate tables (layout below)
export WRDS_DUMP_DIR=/path/to/wrds/extracts        # <schema>.<table>.csv.gz files
export EDGAR_ARCHIVE_ZIP=/path/to/submissions.zip  # only phase7/p7_01: EDGAR submissions JSON files
export SEC_USER_AGENT="name and contact"           # only the steps that request sec.gov (in checks/ and phase5/p5_01)
```

The scripts keep the layout of the workspace they were run in:

```
$RDQ_V2_WORK/RDQ_cadence/              dsf_v2_slim.parquet, dsf_v2_bidask.parquet (reverify/s01, s01b); outputs of reverify/
$RDQ_V2_WORK/RDQ_cadence/phase3/       out/, logs/
$RDQ_V2_WORK/RDQ_cadence/phase4/       out/, logs/, cache/
$RDQ_V2_WORK/_main_checks/             r1_cache/, rdq2_cache/, phase5/, phase6/
$RDQ_V2_WORK/_main_checks/phase7/      cache/, out/
```

`reverify/s05b`–`s12` use file names relative to the working directory and are run from `$RDQ_V2_WORK/RDQ_cadence` (`run_all.sh` does this). The panels of the June version are read from `artifacts/` of this repository (built by the June scripts; not tracked).

## Order

`reverify/run_all.sh` → `phase3/run_phase3.sh` → `phase4/run_phase4.sh` → `checks/r1_phase4_check.py` → `checks/r1_sec_validation.py fetch`, then `checks/r1_sec_validation.py` → `checks/r1_verified_net_of_costs.py` → `phase5/p5_01` → `p5_02` → `p5_10` → `phase6/p6_01` → `phase7/p7_01` → `p7_02` → `p7_20` → `p7_22` → `p7_23` → `p7_30_confirm.py disc` (self-check on the discovery years) → `p7_30_confirm.py conf` (once) → `p7_40_r05_followup.py`, `p7_40_r05_followup.py rec` → `p7_41`–`p7_45` → `reports/papers/v2/make_tables.py` → `make_figures.py`.

## Inputs that these scripts do not build

Some phase-7 inputs were built in the same workspace for a different project and are not part of this package. All derive from public EDGAR data.

| Table (relative to `$RDQ_V2_WORK`) | Content | Used by |
|---|---|---|
| `X_sec_letter/phase4/xa/cache/sec_filings.parquet` | Filing histories (form, date, 8-K items) of a set of registrants | `phase7/p7_01` and `checks/r1_sec_validation.py`, as one of three sources of 8-K item codes |
| `X_sec_letter/phase4/common/conversations.parquet` | Dates of SEC comment-letter releases by registrant | `phase7/p7_20`, for one search condition |
| `_main_checks/x2a_cache/od_sales.parquet`, `issuer_presence.parquet` | Open-market purchases and sales by officers and directors, parsed from Form 4 filings (2015 on) | `phase7/p7_20` (the insider conditions of candidates R07, R08 and R10) and `phase6/p6_01` |

Without the last two, the corresponding search conditions drop out; the delay events, the regularity measure and the returns do not use them. `phase7/p7_30_confirm.py` also contains a block for one frozen candidate of that other project, run under the same protocol; it reads that project's event table, and its output is omitted from the logs in `docs/v2/logs/phase7/`.

## Data

Public: SEC EDGAR submission histories and quarterly indexes; Kenneth French's factor library (read from the WRDS copy). Licensed, **not in this repository**: CRSP daily stock file, names and delistings; Compustat North America quarterly fundamentals, company names and short interest; I/B/E/S surprise summary (one auxiliary split in phase 4). Event-level tables contain CRSP returns and are not published; the aggregate series behind the tables and figures are in `reports/papers/v2/tables/`.

Two copies in `docs/v2/` and here differ from the workspace originals: local path prefixes in the logs are replaced by placeholders (`$RDQ_V2_WORK`, `$WRDS_DUMP_DIR`, `<site-packages>`), and one local path in `phase3/FROZEN_PARAMS.json` is made relative to this repository, so the hash of that file differs from the one recorded when it was frozen.
