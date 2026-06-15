---
date: 2026-06-16
phase: 1
step: 1 (Day 1)
repo: us_compustat_rdq_recognition_timing_xs
project_id: RD1-merged-RD7
script: scripts/phase1_is_oos_split.py
artifacts:
  - artifacts/panel_is.parquet
  - artifacts/panel_oos.parquet
  - artifacts/phase1_is_oos_split.json
---

# Phase 1 Day-1 — IS/OOS Split + OOS Lock SHA Pin

## §1 Purpose

Materialize the IS / OOS partition of `panel_with_returns.parquet` per [Lock D §3](2026-06-16-RD1-merged-RD7-phase1-prereg-lock-d.md) and SHA-pin both subsets. The OOS subset is **SEALED** — no Strategy A analysis touches `panel_oos.parquet` until Day 4 (STEP 4).

Per autopilot prompt PROHIBITION: "NO OOS PARTITION ACCESS before Day 4 (IS-tuning must complete on Day 1-3 first)." This script computes only row-count and SHA metadata over OOS rows (no Bonferroni-12 statistics, no quintile assignment, no t-stat). The seal is operational, not cryptographic — enforced by execution discipline through Day 3.

## §2 Partition definitions (Lock D §3)

| Partition | rdq range | rows | n_with_returns (≥1 horizon CAR) |
|---|---|---|---|
| **IS** (in-sample) | 1999-01-01 .. 2016-12-31 | **436,916** | 245,198 |
| **OOS** (hold-out, SEALED) | 2017-01-01 .. 2024-12-31 | **178,210** | 122,527 |
| Excluded (pre-1999) | — | 0 | — |
| Excluded (post-2024, partial year) | 2025 partial | 5,164 | — |
| **Source total** | 2000-02-11 .. 2025-04-10 | **620,290** | — |

Row balance: 436,916 + 178,210 + 0 + 5,164 = **620,290** ✓ (Lock F-compliant: deterministic split via inclusive date masks; sort by `(gvkey, rdq)` with `kind="mergesort"`.)

## §3 SHA-256 pins

| Artifact | sha256 |
|---|---|
| `panel_with_returns.parquet` (Phase 0 source, frozen) | `4e83a37590699baa6286c4712e99b5c2b4d4cf46009f287f530480e5fa649c31` |
| `panel_is.parquet` (Phase 1 IS subset) | `c2929544d0a1f818be0b6e5193636cd3c3edac178a846fcbf75283473e84924e` |
| `panel_oos.parquet` (Phase 1 OOS subset, **SEALED**) | `b5d039bc0892a9cd4fc91481de6f3ffd1a397840fab6029c1756c6c05cdb76e6` |

Re-running `python scripts/phase1_is_oos_split.py` against the same source SHA must reproduce identical IS and OOS SHAs (Lock F determinism). Source SHA mismatch triggers HALT + Lock C/D deviation protocol (Lock D §9).

## §4 IS partition year distribution

```
2000:13,522  2001:32,171  2002:32,047  2003:30,449  2004:29,135  2005:28,231
2006:27,300  2007:26,518  2008:25,968  2009:25,170  2010:24,371  2011:23,871
2012:23,573  2013:23,492  2014:23,749  2015:23,991  2016:23,358
```

17 calendar years (1999 has 0 rows because Compustat fundq earliest rdq is 2000-02-11). NW-12 t-stat power: ≥200 months available, well above 200-month floor for Bonferroni-12.

## §5 OOS partition year distribution

```
2017:22,601  2018:22,059  2019:21,797  2020:21,184  2021:21,694
2022:22,872  2023:23,405  2024:22,598
```

8 calendar years, 96 months, 178,210 firm-Q rows (122,527 with ≥1 horizon CAR). Power-constrained per Phase 1 entry §4 / Lock D §4 — sub-period 2017-2024 already known to yield ~1.5-1.9 t-stat per primary cell in Phase 0 regime-stability analysis (not a Phase 1 result; published in Phase 0 close).

## §6 Sealing protocol enforcement

OOS partition is sealed until Day 4. Operational checks:

- Days 2-3 scripts (`phase1_strategy_A_is.py`, `phase1_robustness_is.py`) hard-code `PANEL_PATH = artifacts/panel_is.parquet`.
- Day 4 script (`phase1_strategy_A_oos.py`) is the **only** authorized OOS reader.
- Day 5 sector + WITH-NT analysis reads OOS but only after Day 4 verdict is closed.
- If any Day 2-3 robustness extension would require OOS data (e.g., 240d/360d horizon on full panel), defer to Day 4+.

No `panel_with_returns.parquet` reads on Day 2-3 either — IS-only analysis means `panel_is.parquet` only.

## §7 Lock F compliance

- All sort calls use `kind="mergesort"` (`scripts/phase1_is_oos_split.py:65-70`).
- Inclusive boundary masks on `rdq` column (datetime64[ns]).
- Parquet written via `engine="pyarrow"` for byte-stable output across runs.
- SHA-256 computed in 1 MB chunks (`scripts/phase1_is_oos_split.py:31-35`).

## §8 Hand-off to Day 2

STEP 2 cleared to begin:

- Input: `artifacts/panel_is.parquet` (sha256 `c2929...4924e`)
- Script: `scripts/phase1_strategy_A_is.py` (re-uses `strategy_A_bonferroni.py` core; reads IS subset only)
- Output: `artifacts/strategy_A_bonferroni12_is.csv` + `.json`
- HALT condition: <3/4 primary cells |t| > 2.78 on IS → STEP 2 audit triggers diagnostics, do not advance to STEP 3.

## §9 Commit pin

| Commit | Description |
|---|---|
| `fd2828f` | Phase 1 STEP 0: Day-0 anti-bias self-check audit |
| TBD | Phase 1 STEP 1: Day-1 IS/OOS split + SHA pin |
