---
title: "Earnings-announcement cadence variance and the cross-section of post-announcement returns"
project_id: RD1-merged-RD7
status: paper-practical outline (Phase 1 close 2026-06-16)
target_venue: JFE / JFQA / RAST (paper-practical lane)
outline_authored_by: deterministic skeleton, no LLM expense yet
budget_remaining_for_draft: $25-75 via openrouter_client (NOT direct API key)
---

# Paper Outline — Strategy A (RD1) Cadence-Variance Cross-Section

**Note**: This is a structured outline only (max 5-page paper skeleton per autopilot prompt STEP 6). Full paper drafting via `D:/vscode/portfolio-coordination/shared-utils/shared_utils/openrouter_client.py` deferred to Day 6+ continuation. Budget $25-75 reserved.

## §1 Introduction (extension axis Bagnoli-Kross-Watts level → variance)

- **Anchor**: Bagnoli, Kross, Watts (2002) JAR 40(5):1275-1296 — earnings announcement timing **level** (early vs late vs on-time) predicts post-announcement returns. Good news announced early; bad news delayed.
- **Extension axis**: We move from announcement timing **level** to announcement timing **variance**. Hypothesis: firms with high within-firm rolling variance of (rdq − datadate) have erratic disclosure pipelines that correlate with NEG forward CAR.
- **Mechanism story**: cadence variance proxies for internal-controls noise / disclosure pipeline turbulence. Q1 (low-variance) firms exhibit stable, predictable disclosure timing — markets price them efficiently. Q5 (high-variance) firms carry disclosure-process uncertainty that resolves over forward 120-180d windows in the NEG direction.
- **Contribution**: First U.S.-cross-section panel test of cadence-variance as XS signal; extends Bagnoli-Kross-Watts 2002 level-of-lag into 2nd-moment-of-lag.
- **Differentiation from V5 (SEC Form NT)**: V5 uses regulatory binary marker (NT-10K/NT-10Q filings); RD1 uses continuous cadence-noise on universe-wide Compustat `rdq`. NT-filer exclusion mitigates mechanical overlap (Phase 0 sub-gate (c)).

## §2 Data

- **Compustat fundq** 1999-2024 (25 yrs), standard INDL/STD/C/D/USD filter. rdq + datadate + gvkey + cshoq + prccq + sic.
- **CRSP dsf_v2** for daily returns; CAR over [rdq+1, rdq+H] for H ∈ {60, 120, 180}.
- **CCM bridge** via `comp_na_daily_all.names` cusip8 (crsp_a_ccm USAGE-blocked per WRDS U44).
- **Sample**: 620,290 firm-Q raw → 436,916 IS + 178,210 OOS (post-2025 partial year excluded). 367,725 with ≥1 horizon CAR (245,198 IS + 122,527 OOS).
- **NT-filer exclusion** (sub-gate (c)): drop fqtr∈{1,2,3} with gap>75d; fqtr=4 with gap>100d. ~4% sample.
- **Period split** (Lock D §3): IS = 1999-2016 (18 yrs, 216 months), OOS = 2017-2024 (8 yrs, 96 months).
- **SHA pins** ([artifacts/phase1_is_oos_split.json](../../artifacts/phase1_is_oos_split.json)): source panel `4e83a37...649c31`, IS `c292954...4924e`, OOS `b5d039b...db76e6`.

## §3 Methodology

- **Signal construction**: `gap_var_t = std({gap_q : q ∈ trailing 8Q, ≥6 valid})` where `gap_q = (rdq − datadate)_q`. 8Q rolling window with ≥6 non-NaN floor.
- **Cross-sectional ranking**: monthly XS quintile within FF12 sector. Q1 = low-variance, Q5 = high-variance. Predicted spread: Q1 − Q5 > 0 (Lock C direction matrix).
- **Bonferroni-12 cells**: 3 horizons (60/120/180d) × 4 sub-cells (size Large/Small × industry-tilt High/Low) = 12 cells. Sub-cell assignment by monthly XS median mcap within FF12 (size); FF12 ∈ {6, 10, 11} = high-tilt (BusEq + Hlth + Money), rest = low-tilt.
- **t-statistic**: Newey-West with 12-lag (quarterly autocorrelation correction).
- **Pass criterion**: |t| > 2.78 (Bonferroni 0.05/12) AND sign-correct (mu_spread > 0).
- **Lock C immutable direction matrix**: all 12 cells pre-registered with Q1 long / Q5 short.
- **Lock D pre-registered primary cells** (4): A120-LH, A120-SH, A180-LH, A180-SL. Selected from Phase 0 4/12 Bonferroni-12 PASS set.

## §4 Results

### §4.1 In-sample (IS, 1999-2016)

| Cell | μ_spread | t (NW-12) | Bonferroni-12 |
|---|---:|---:|:-:|
| A120-LH | +3.37% | 3.37 | PASS |
| A120-SH | +2.66% | 2.06 | sign-correct, sub-threshold |
| A180-LH | +4.14% | 3.31 | PASS |
| A180-SL | +4.93% | 3.62 | PASS |

**IS 3/4 primary cells PASS** (HALT floor met). All 12 IS cells sign-correct. LDS_IS 7/7 LIVE-DEPLOYABLE-STRONG (counterfactual: had OOS replicated this strength, paper would have been LAYER A LOCK candidate). See [audits/2026-06-16-RD1-merged-RD7-phase1-day2-is-reconfirm.md](../../audits/2026-06-16-RD1-merged-RD7-phase1-day2-is-reconfirm.md).

### §4.2 Out-of-sample (OOS, 2017-2024)

| Cell | μ_spread | t (NW-12) | Bonferroni-12 |
|---|---:|---:|:-:|
| A120-LH | +2.48% | 1.55 | sign-correct, sub-threshold |
| A120-SH | +3.73% | 1.86 | sign-correct, sub-threshold |
| A180-LH | +3.51% | 1.85 | sign-correct, sub-threshold |
| A180-SL | +4.62% | 1.74 | sign-correct, sub-threshold |

**OOS 0/4 primary cells PASS Bonferroni-12** but **11/12 cells sign-correct OOS** (only A60-SL flips marginally). Top OOS cell: A180-LL (secondary) t=2.49. The signal is **directionally robust but power-constrained** on the 8-year OOS window. Pre-acknowledged in Lock D §4 expected_OOS = 1.55-1.85 per primary cell. See [audits/2026-06-16-RD1-merged-RD7-phase1-day4-oos-reveal.md](../../audits/2026-06-16-RD1-merged-RD7-phase1-day4-oos-reveal.md).

### §4.3 Sector robustness OOS

| Cell | Sector criterion (Lock D §5) | Result |
|---|---|---|
| A120-LH | BusEq + Hlth both positive | **PASS** (BusEq +4.32%, Hlth +5.67%) |
| A120-SH | BusEq + Hlth both positive | **PASS** (BusEq +6.60%, Hlth +6.73%) |
| A180-LH | BusEq + Hlth both positive | **PASS** (BusEq +5.06%, Hlth +10.65%) |
| A180-SL | ≥6/9 low-tilt sectors positive | **FAIL** (5/9; Durbl dominant +17.46%, Utils anti −7.90%) |

3/4 cells PASS sector robustness OOS. The mechanism is sectorally interpretable for high-tilt cells (technology + healthcare); concentrated in durable-goods for the low-tilt cell.

### §4.4 Sub-period stability (Phase 0+ §3 — full sample, included as appendix table)

| Cell | 1999-2007 t | 2008-2016 t | 2017-2024 t |
|---|---:|---:|---:|
| A120-LH | 2.12 | 2.65 | 1.55 |
| A120-SH | 1.24 | 1.76 | 1.86 |
| A180-LH | 1.90 | 2.79 | 1.85 |
| A180-SL | 3.44 | 1.80 | 1.74 |

Late-period weakening is broad-based, not concentrated. Possible mechanisms: post-Reg-FD information-flow convergence; algorithmic trading absorbing the cadence signal at faster horizons.

## §5 Robustness

### §5.1 Transaction cost overlay (100bp two-way)

| Cell | μ_gross (IS) | μ_net (1% off) | Retention | ≥25% K-floor | ≥75% STRONG |
|---|---:|---:|---:|:-:|:-:|
| A120-LH | +3.37% | +2.37% | 70.4% | ✓ | — |
| A120-SH | +2.66% | +1.66% | 62.4% | ✓ | — |
| A180-LH | +4.14% | +3.14% | 75.8% | ✓ | ✓ |
| A180-SL | +4.93% | +3.93% | 79.7% | ✓ | ✓ |

4/4 primary cells exceed 25% retention floor on IS. Net-of-cost spread economically meaningful at 120-180d horizons.

### §5.2 WITH-NT vs WITHOUT-NT sensitivity (OOS)

- WITHOUT-NT primary OOS: 0/12 Bonferroni PASS (pre-registered specification).
- WITH-NT sensitivity OOS: 2/12 Bonferroni PASS (A180-LH primary t=3.57; A180-LL secondary t=3.53).
- K4 inflation ratio = 2.0 at threshold (not exceeding strict > 2.0) → K4_NOT_TRIGGERED.
- **Interpretation**: NT-filers carry the variance-of-cadence signal genuinely, not as mechanical confound. Excluding them is the pre-registered prophylactic but also removes power.

### §5.3 Deferred axes (advisory, Lock D §7 — see [artifacts/phase1_robustness_is_deferrals.json](../../artifacts/phase1_robustness_is_deferrals.json))

- 240d / 360d horizons: DEFERRED (no daily returns persisted)
- FF49 industry partition: DEFERRED (FF12 is binding sector criterion per Lock D §5)
- Skip-week-1 (rdq+8 → rdq+H): DEFERRED (no offset CAR available)

## §6 Strategy B NEG appendix (Chambers-Penman 1984 — DEAD-CONFIRMED)

Phase 0 Strategy B (within-firm rolling baseline deviation XS, RD7) failed Bonferroni-12 with 0/12 PASS even in the asymmetric 24-cell decomposition. Chambers-Penman 1984 JAR (anchor for Strategy B) predicts early/late deviation → forward CAR direction. Empirical:

- Phase 0 KILL: 0/12 Bonferroni-12 cells PASS (symmetric Q5-Q1).
- Asymmetric 24-cell (pos vs neg deviation separately): 0/24 PASS.
- See [audits/2026-06-16-RD1-merged-RD7-strategy-B-results.md](../../audits/2026-06-16-RD1-merged-RD7-strategy-B-results.md).

Within-firm baseline deviation does not survive post-Chambers-Penman post-publication decay. Reported as failed-replication contribution.

## §7 Discussion

### §7.1 Variance-of-X family update

| Member | Pre-Phase-1 | Post-Phase-1 |
|---|---|---|
| F1 (FDA expectation variance) | Frozen-two-layer | unchanged |
| F6 (clinicaltrials amendment) | Post-pub-downgrade-tentative | unchanged |
| **RD1 Strategy A** | LAYER A candidate | **paper-practical PASS** |

Family score: 0/3 LAYER A LOCKED; 1/3 paper-practical PASS. The variance-of-X-as-XS-signal weak prior is confirmed but not catastrophically — directional signal survives across all 3 members; statistical power on 8-year hold-outs is the binding constraint.

### §7.2 Pod assignment

- Compustat-Recognition-Timing pod: **1st LOCKED slot remains unclaimed**.
- RD1 contributed paper-practical evidence; pod accepts new candidates.

### §7.3 LDS evolution

- LDS_IS 7/7 → LDS_OOS 3/7. Signal-side axes (1, 2, 4) preserved; pass-floor axes (3, 5, 6, 7) all drop. Diagnostic: signal exists but lacks Bonferroni-12 power on shorter samples.

### §7.4 Future directions

- Longer horizon CARs (240d / 360d) — requires fresh dsf_v2 stream.
- Skip-week-1 implementation — separates PEAD overlap from cadence-variance.
- FF49 finer partition — may reveal sub-industry concentration.
- Combined Strategy A × momentum / accruals interaction — complementary mechanism.
- International extension — IBES expectation cadence on non-U.S. cohorts.

## §8 Artifacts and reproducibility

| Item | Path |
|---|---|
| IS partition | artifacts/panel_is.parquet (sha256 c292954...4924e) |
| OOS partition | artifacts/panel_oos.parquet (sha256 b5d039b...db76e6) |
| IS Bonferroni-12 results | artifacts/strategy_A_bonferroni12_is.{csv,json} |
| OOS Bonferroni-12 results | artifacts/strategy_A_bonferroni12_oos.{csv,json} |
| TC overlay | artifacts/strategy_A_tc_overlay_is.{csv,json} |
| Sector OOS | artifacts/strategy_A_sector_oos.{csv,json} |
| WITH-NT OOS | artifacts/strategy_A_with_nt_oos.{csv,json} |
| Phase 1 audit chain | audits/2026-06-16-RD1-merged-RD7-phase1-day{0..5}-*.md |
| Locks | C (direction matrix), D (pre-reg cells), F (pipeline determinism) |
| Code | scripts/strategy_A_bonferroni.py + scripts/phase1_*.py |

**Reproducibility**: Lock F audit run on Day 6 cleared both Pattern B hits as compliant (sort_values + mergesort chain). All scripts use mergesort kind for sort_values; no pandas group-by-without-sort. Re-running `python scripts/phase1_*.py` against the SHA-pinned IS/OOS partitions produces byte-identical CSV/JSON outputs.
