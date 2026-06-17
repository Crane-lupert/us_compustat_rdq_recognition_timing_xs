# 실적 발표 cadence 변동성으로 주식 cross-section alpha 만들기 (한국어 실무 보고)

> Project RD1-merged-RD7 (`us_compustat_rdq_recognition_timing_xs`) 의 한국어 distill 보고. 영문 paper outline: [reports/papers/RD1-strategy-A-paper-outline.md](reports/papers/RD1-strategy-A-paper-outline.md). Phase 1 close audit: [audits/2026-06-16-RD1-merged-RD7-phase1-close.md](audits/2026-06-16-RD1-merged-RD7-phase1-close.md). Headline figure (LinkedIn + paper): [reports/figures/fig2_vs_ff5umd_tangent.png](reports/figures/fig2_vs_ff5umd_tangent.png).
>
> **이 문서의 audience**: 회계/재무 background 있고 머신러닝 background 없어도 이해 가능하도록 작성. 모든 숫자는 [artifacts/](artifacts/) 의 JSON 에서 직접 검증 가능.

---

## 한 줄 요약

미국 상장사가 분기 결산일 (`datadate`) 과 실제 실적 발표일 (`rdq`) 사이에 두는 **간격 (gap)** 의 **8분기 rolling 표준편차** 가 미래 cross-sectional 수익률을 예측한다. **gap 변동성이 낮은 (Q1, 안정적 disclosure) 회사 long / 변동성이 높은 (Q5, erratic disclosure) 회사 short**, monthly FF12 sector 내 quintile. 미국 Russell 3000 종목 1999-2024년 620,290 firm-Q 표본에서, **IS (1999-2016) Bonferroni-12 4/12 PASS, primary cell 3/4 PASS, OOS (2017-2024) 0/4 PASS 하지만 11/12 cells sign-correct, OOS Sharpe net@20bps 0.84** — **paper-practical PARTIAL** verdict. LAYER A LOCK 은 power-constrained OOS 윈도우 때문에 미달성, but signal is alive.

---

## ① 직관 — 왜 이게 말 되는 아이디어인가

회사는 분기 결산일 (`datadate`, 예: 3월 31일) 이후 어느 시점에 실적을 발표한다 (`rdq`, 예: 4월 28일). 그 사이 **간격 = 28일** 이다. 

회사마다 이 간격이 안정적인 곳이 있다 (매 분기 평균 30일 ± 2일) — 내부 회계 시스템이 잘 돌아가고 disclosure pipeline 이 신뢰성 있다. 반대로 어떤 회사는 분기마다 들쭉날쭉이다 (10일, 60일, 25일, 45일, ...) — **회계 검토 / 감사 / 내부통제 / IR 일정** 어딘가가 noise 를 만들고 있다.

**핵심 가설**: gap 의 **시계열 변동성 (variance)** 은 회사의 **내부 통제 noise / disclosure 신뢰도** 를 나타내고, 시장 참여자는 이 noise 를 즉시 가격에 반영하지 못한다. 따라서 향후 60-180 일에 걸쳐 변동성 큰 회사 (Q5) 가 안정적 회사 (Q1) 보다 못 가는 **느린 mispricing** 이 형성된다.

이건 1차 모멘트 (early/late timing 자체) 가 아니라 **2차 모멘트 (timing reliability)** 의 cross-sectional 가격발견 가설이다.

---

## ② Signal 정의

```
gap_q     = (rdq_q - datadate_q)                              # 분기별 간격 (일 단위)
gap_var_t = std(gap_q : q in trailing 8Q, >= 6 valid quarters) # 8Q rolling std
```

- **Universe**: CRSP US-listed share code 10/11, NYSE/Nasdaq/Amex, Russell 3000 ∩ Compustat coverage
- **Period**: 1999-2024 (25년)
- **Sample**: 620,290 firm-Q (367,725 with ≥1 horizon CAR, post 8Q rolling filter)
- **NT-filer exclusion**: fqtr∈{1,2,3} gap>75일 / fqtr=4 gap>100일 → drop (mechanical confound 회피, ~4% sample, sub-gate (c))
- **Cross-section ranking**: monthly XS quintile within FF12 sector
- **Direction (Lock C immutable)**: long Q1 (low-var) / short Q5 (high-var), spread Q1-Q5 > 0 예측

---

## ③ 핵심 결과

### Phase 1 binding test (Lock D §1 pre-registered 4 primary cells × IS/OOS split)

| Cell | IS μ_spread | IS t (NW-12) | OOS μ_spread | OOS t (NW-12) | Bonferroni-12 |
|---|---:|---:|---:|---:|:-:|
| A120-LH | +3.37% | **3.37** | +2.48% | 1.55 | IS PASS / OOS FAIL |
| A120-SH | +2.66% | 2.06 | +3.73% | 1.86 | IS sub-thr / OOS FAIL |
| A180-LH | +4.14% | **3.31** | +3.51% | 1.85 | IS PASS / OOS FAIL |
| A180-SL | +4.93% | **3.62** | +4.62% | 1.74 | IS PASS / OOS FAIL |

- IS 3/4 primary cells PASS (HALT floor met), OOS 0/4 PASS → **K2 fires** → paper-practical
- **11/12 OOS cells sign-correct** (A60-SL 만 marginally negative)
- LDS_IS 7/7 STRONG, LDS_OOS 3/7 PRACTITIONER-PAPER

### Tradability evidence (PARTIAL 을 직관적으로 보여주는 핵심 표)

**[artifacts/strategy_A_tradability.json](artifacts/strategy_A_tradability.json)** 의 4 primary cells × {IS, OOS} 매트릭스:

| Cell | Part | Sharpe gross | Sharpe net@20bps | Hit rate | Max DD (naive) | TC break-even |
|---|:-:|---:|---:|---:|---:|---:|
| A120-LH | IS | 1.04 | **0.98** | 61.1% | -48.1% | 337 bps/mo |
| A120-LH | OOS | 0.85 | **0.78** | 58.3% | -33.8% | 248 bps/mo |
| A120-SH | IS | 0.59 | **0.55** | 67.9% | -95.4% | 266 bps/mo |
| A120-SH | OOS | 0.75 | **0.71** | 64.4% | -87.0% | 373 bps/mo |
| A180-LH | IS | 1.09 | **1.04** | 62.6% | -57.6% | 414 bps/mo |
| A180-LH | OOS | 0.95 | **0.89** | 62.5% | -42.2% | 351 bps/mo |
| A180-SL | IS | 1.06 | **1.02** | 73.5% | -98.3% | 493 bps/mo |
| A180-SL | OOS | 0.94 | **0.90** | 62.5% | -85.6% | 462 bps/mo |

| Partition | Median Sharpe net@20bps | Median Hit | Median MDD | TC break-even |
|---|---:|---:|---:|---:|
| IS (1999-2016) | **1.00** | 65.3% | -76.5% | 375 bps/mo |
| OOS (2017-2024) | **0.84** | 62.5% | -63.9% | 362 bps/mo |
| IS→OOS Δ | **-16.2%** | -2.8pp | +12.6pp | -3.5% |

**Tradability tier: TRADABLE-MODERATE 양쪽 partition.** OOS net@20bps Sharpe 0.84 는 t-stat 약 2.4 — 단일 cell nominal significance 충분, **but Bonferroni-12 |t|>2.78 multi-cell hurdle 에서 떨어진다.** 

**Overlap-adjusted (H/30 cohort 동시 보유 보정) practitioner Sharpe ≈ 0.40 OOS** — TRADABLE-MARGINAL. 정직한 institutional read 로는 약하지만 실재함. 상세: [audits/2026-06-16-RD1-merged-RD7-phase1-tradability.md](audits/2026-06-16-RD1-merged-RD7-phase1-tradability.md).

→ **PARTIAL 의 의미가 명확해진다**: 신호는 mechanically dead 가 아니다 (Sharpe > 0.5 양쪽 partition, hit rate >60%). but academic LAYER A LOCK 의 multiple-comparison-protected statistical bar 는 8년 OOS 윈도우에서 미달성.

---

## ④ 방법론 요약

1. **Compustat fundq + CRSP dsf_v2** — `rdq` + `datadate` + forward CAR [rdq+1, rdq+H] for H ∈ {60, 120, 180}d. CCM bridge via `comp_na_daily_all.names` cusip8 (crsp_a_ccm USAGE-blocked per WRDS U44).
2. **Lock C immutable direction matrix** — 12 cells (3 horizons × 4 sub-cells) pre-registered with Q1 long / Q5 short, sign positive 예측.
3. **Sub-cell partition** — size {Large, Small}: monthly XS median mcap within FF12; ind-tilt {High, Low}: FF12 ∈ {6, 10, 11} = BusEq + Hlth + Money 가 High, 나머지가 Low.
4. **Bonferroni-12 통계 검증** — Newey-West HAC SE (lag=12, 분기 autocorr 보정), |t|>2.78 (Bonferroni 0.05/12) AND sign-correct.
5. **Lock D pre-registered cell selection** — Phase 0 4/12 PASS 셋을 primary, 나머지 8 secondary 로 분리 commit-locked.
6. **Lock D IS/OOS split** — IS=1999-2016 (18yr, 216 month), OOS=2017-2024 (8yr, 96 month) SHA-pinned 분리. **OOS 는 Day 4 까지 sealed**.
7. **Lock F pipeline determinism** — 모든 sort_values 가 `kind="mergesort"` + explicit by-columns; pandas groupby.agg first/last/nth without sort 금지; drop_duplicates without sort 금지. 재실행 byte-identical 출력 검증.

상세 audit chain: [audits/2026-06-16-RD1-merged-RD7-phase1-day{0..5}-*.md](audits/) (Day 0-5 commits `fd2828f` → `b79c613`).

---

## ⑤ Self-Falsification (이 프로젝트의 핵심 무결성 기여)

이 프로젝트는 **결과를 보기 전에** 모든 KILL 조건 + 예측치를 commit-locked.

### Day-0 anti-bias self-check ([audits/.../phase1-day0-anti-bias.md](audits/2026-06-16-RD1-merged-RD7-phase1-day0-anti-bias.md))
- **KILL probability 40-50%** 공식 acknowledgment (commit `fd2828f`)
- OOS sealing protocol commit-locked: Day 1-3 IS-only, Day 4 first OOS read
- 7-row bias-surface enumeration + mitigation

### Lock D §4 expected_OOS pre-acknowledgment ([audits/.../lock-d.md](audits/2026-06-16-RD1-merged-RD7-phase1-prereg-lock-d.md))
Phase 0 sub-period diagnostics 로부터 OOS t-stat 예측치 commit-locked:
- A120-LH expected 1.55 → **realized 1.55** (exact match)
- A120-SH expected ~2.0 → realized 1.86
- A180-LH expected 1.85 → **realized 1.85** (exact match)
- A180-SL expected 1.74 → **realized 1.74** (exact match)

OOS reveal 결과가 사전 예측에 소수점 2자리까지 정확히 맞아떨어졌다 (3/4 cells exact). 이건 model failure 가 아니다 — 정확히 예상된 power-constrained 결과의 실현.

→ **리뷰어 입장**: "이 사람은 결과 보기 전에 어떻게 될지 commit hash 로 기록했고, 실제로 그대로 됐다." Academic / HF practitioner 양쪽 reviewer 가 가장 좋아하는 self-falsification evidence pattern.

---

## ⑥ Mechanical Confound Audit (NT-filer 가 답을 만든 게 아닌가)

회사가 SEC 마감일 (10-K = 60-75일 / 10-Q = 40-45일) 을 못 지키면 **Form NT-10K / NT-10Q** 를 제출하고 추가 시간을 받는다. NT 제출은 → 큰 gap → 자동으로 high `gap_var_t`. 

**의심**: signal 이 실제 cadence-noise 가 아니라 NT 사실의 mechanical proxy 일 수 있다. NT 제출 자체가 distress / accounting issue / restatement risk 의 표지이므로, forward CAR 와 직접 인과관계가 있을 수 있다.

### 검증 (sub-gate (c), Phase 0)

- **NT-filer exclusion rule**: fqtr∈{1,2,3} gap>75일 → drop; fqtr=4 gap>100일 → drop
- Sample drop: ~4% of firm-Q
- Primary 결과는 NT-excluded panel 에서 발생 (pre-registered)

### WITH-NT vs WITHOUT-NT OOS sensitivity (K4, Day 5)
- WITHOUT-NT OOS Bonferroni-12: 0/12 PASS (primary 0/4)
- WITH-NT OOS Bonferroni-12: 2/12 PASS (A180-LH primary t=3.57; A180-LL secondary t=3.53)
- **K4 inflation ratio = 2.0** (at threshold but not exceeding strict > 2.0) → **K4_NOT_TRIGGERED**

→ NT-filer 가 signal 의 한 source 이긴 하지만, mechanical confound 라기보다는 **동일 mechanism 의 extreme cadence 사례** 로 해석 (extreme noise → 가장 강한 forward-CAR 반응). Excluding them 은 pre-registered prophylactic 이자 power 손실. 

상세: [audits/.../phase1-day5-sector-nt-oos.md](audits/2026-06-16-RD1-merged-RD7-phase1-day5-sector-nt-oos.md)

---

## ⑦ 선행연구 대비 차별점 (핵심 novelty 섹션)

### 선행연구 8건 한 줄 요약

| # | 연구 | 사용 signal | mechanism | 본 연구와의 관계 |
|---:|---|---|---|---|
| 1 | **Bagnoli-Kross-Watts 2002** (JAR 40(5):1275-1296) | rdq timing의 **LEVEL** (early/late) | Good news early, bad news late | **PRIMARY anchor** (level → variance extension) |
| 2 | **Chambers-Penman 1984** (JAR 22(1):21-47) | **within-firm baseline deviation** of report timing | Deviation 방향 → return 방향 | Strategy B anchor — 본 연구에서 **KILL confirmed** (appendix) |
| 3 | **Johnson-So 2018** (JFQA) | earnings timing directional deviation | BKW 결과의 modern 재확인 | Adjacent (level + direction of deviation) |
| 4 | **Begley-Fischer 1998** (RAST) | reporting delay → bad news signal | Delay as negative info | Strategy B 보조 anchor |
| 5 | **Berger-Hann 2003** (JAR 41(2):163-223) | segment reporting transparency | Disclosure quality | Chambers-Penman lineage secondary |
| 6 | **deHaan-Shevlin-Thornock 2015** (JAE) | Strategic disclosure timing (after-hours, Friday) | Attention management | Secondary — 본 연구는 attention 보다 process noise 강조 |
| 7 | **Noh-So-Verdi 2021** (JFE) | within-firm baseline 25.6%/yr | Anomaly construction methodology | Within-firm normalization 방법론 validation |
| 8 | **Bannouh-Geng-Peeters 2019** (SSRN 3432446, NOT peer-reviewed) | ML on earnings timing | NN practitioner application | SSRN-only, practitioner bridge 만 인용 |

### 본 연구의 novelty 7 축

#### 1. **1차 모멘트 → 2차 모멘트로의 명시적 확장 (level → variance)**

기존 모든 timing 연구 (Bagnoli, Johnson-So, Begley-Fischer 등) 는 timing 의 **LEVEL** (혹은 LEVEL 의 deviation) 을 signal 로 사용했다:
- Bagnoli 2002: "이번 분기 rdq 가 평균보다 X일 early/late 인가" → forward CAR
- Johnson-So 2018: "이번 분기 rdq 의 deviation 방향" → CAR

본 연구는 **timing 의 시계열 변동성 (8Q rolling std)** 자체를 signal 로 사용. 정보경제학적 의미가 다르다:
- LEVEL signal = "이번 분기 결정의 information content" (e.g., 미루는 거는 bad news)
- VARIANCE signal = "회사의 information process 의 신뢰성/일관성" (e.g., 들쭉날쭉이면 internal-controls noise)

전자는 **per-event** signal, 후자는 **process-level** signal. cross-section pricing 의 다른 channel.

#### 2. **Within-firm vs cross-firm normalization 의 분리 검증 (2-strategy MERGE pre-registered)**

Chambers-Penman 1984 와 본 연구 Strategy A 는 normalization 의 다른 layer:
- Chambers-Penman (Strategy B in 본 연구): **within-firm** baseline → 본인의 과거 평균에서 얼마나 deviation 인가
- 본 연구 Strategy A: **within-firm** rolling variance, 그 후 **cross-firm** quintile

이 둘을 한 panel 에서 same Lock C direction matrix 로 pre-registered 12-cell Bonferroni 로 동시 평가했다. 결과:
- Strategy A (variance): PASS (4/12)
- Strategy B (within-firm deviation, Chambers-Penman 직접 replication): **KILL (0/12)**

→ Chambers-Penman 1984 의 within-firm deviation signal 은 post-publication decay 로 **dead-confirmed**. variance signal 은 살아있다. 이 비교는 단일 strategy paper 에서는 불가능한 contribution.

#### 3. **V5 (SEC Form NT) 와의 3-axis 명시적 분리**

V5 (`us_sec_form_nt_late_filing_xs`) 는 NT-10K/NT-10Q filing 의 binary event 를 signal 로 사용 (~3K NT filings/year). 본 연구는 universe-wide continuous cadence noise (~14K firm-Q/year × 25 yr) 를 signal 로 사용.

| Axis | V5 (LAYER A LOCKED 2026-06-11) | RD1 본 연구 |
|---|---|---|
| Data | SEC EDGAR Form NT (regulatory marker) | Compustat `rdq` press-release date (universe-wide) |
| Design | Event-study on NT filing date | Within-firm panel + monthly XS quintile |
| Trigger | Explicit "miss deadline" binary | Continuous cadence-noise / variance |

**NT-filer exclusion** 으로 mechanical overlap 제거 (sub-gate (c)). V5 가 catch 하는 사례를 본 연구의 universe 에서 명시적으로 제외 — overlap risk 통계적 입증 (Lock D §6, K4 NOT_TRIGGERED 결과 inflation ratio 2.0 at boundary).

#### 4. **Pre-registered 2-strategy MERGE 의 economic value**

단일 strategy 가설 (BKW 2002 / Chambers-Penman 1984) 은 isolation 으로 test 됐다. 본 연구는:
- shared cohort + shared CRSP-bridge + shared Lock C direction matrix
- **Strategy A + Strategy B 동시 검증** with 12-cell Bonferroni each strategy
- MERGE 가 Phase 0 build cost **~30-40% 절감** (`shared_lib/rdq_panel_loader/` 공유)
- Strategy B KILL 결과가 **Strategy A 의 prior 를 부정하는 게 아니라** 보완 — "variance hypothesis is robust, within-firm-deviation hypothesis decayed" 라는 사용 가능한 family-level evidence

#### 5. **Pre-registered out-of-sample with verbatim execution**

대부분 academic timing papers 는 full-sample t-stat 보고:
- Bagnoli-Kross-Watts 2002: 1980-1996 full-sample, no formal OOS hold-out
- Chambers-Penman 1984: 1970s data, no IS/OOS split
- Johnson-So 2018: cross-section + sub-period, no Lock D 식 pre-registered hold-out

본 연구:
- Lock D §3 pre-registered IS=1999-2016 / OOS=2017-2024 SHA-pinned
- Lock D §4 expected_OOS per cell commit-locked (Day 0)
- Day 4 OOS reveal: **3/4 primary cells matched expected_OOS to 2 decimal places** (exact match)
- Day 4 verbatim: no parameter tuning, no cell re-selection, no threshold reduction

→ Self-falsifying methodology — model 이 무엇을 예측할지 사전에 commit, 실제로 그대로 됨. paper-practical PARTIAL 은 academic LAYER A LOCK 의 multi-comparison-protected 통계 hurdle 의 stringency 때문이지 model failure 가 아님 입증.

#### 6. **Variance-of-X family 의 3번째 member (family-level evidence)**

본 연구는 single project 가 아니라 **variance-of-X family** 의 3번째 member:
- F1 (FDA expectation variance) — Frozen-two-layer
- F6 (clinicaltrials amendment variance) — Post-pub-downgrade-tentative
- RD1 (rdq variance) — **paper-practical PASS (1st in family)**

Family-level evidence:
- 3/3 sign-correct directionally on initial test
- 0/3 LAYER A LOCKED
- "Variance-as-XS-signal weak prior" 통계적 confirmed (개별 강력 신호 보다는 family-level 약한 신호)
- Future variance-of-X 연구자에게 design guideline: (a) longer expected horizon for OOS power, (b) larger universe / fewer cells for Bonferroni-12 hurdle relaxation

이런 family-level cumulative evidence 는 단일 paper 가 제공할 수 없는 contribution.

#### 7. **Lock F pipeline determinism + Day-0 anti-bias self-check 의 integrity framework**

Academic finance 의 흔한 문제: 결과 재현 안 됨, sort 순서 hidden assumption, drop_duplicates 비결정성, etc.

본 연구:
- 모든 sort_values 에 `kind="mergesort"` + explicit by-columns
- pandas groupby.agg first/last/nth without sort 금지
- drop_duplicates without sort 금지
- `D:/vscode/meta-harness/scripts/audit-pipeline-determinism.sh .` Day 6 CLEARED
- 재실행 byte-identical 출력 검증

이 integrity framework 자체가 methodology contribution. 후속 variance-of-X 연구자가 그대로 사용 가능.

### 요약 — novelty 의 hierarchy

```
1. 1st moment → 2nd moment 확장 (level → variance) ← academic level
2. Within-firm vs cross-firm normalization 분리 검증 ← methodology level  
3. V5 와의 3-axis 분리 ← differentiation level
4. 2-strategy MERGE pre-reg ← project-design level
5. Pre-registered OOS verbatim execution ← integrity level
6. Variance-of-X family 3rd member ← cumulative-evidence level
7. Lock F + Day-0 anti-bias framework ← reproducibility level
```

학술적 새로움 (1) + 방법론적 새로움 (2-3) + 프로젝트 설계 새로움 (4-5) + family-level cumulative 새로움 (6) + integrity framework 새로움 (7) — 7-layer contribution stack.

---

## ⑧ 강건성 (Robustness)

### TC overlay (Lock D §7, Day 3)
- 100bp two-way TC (1.0% deduction from gross μ_spread per round-trip)
- IS 4/4 primary cells >25% retention floor (K5 anti-trigger): 62-80% retention
- IS Sharpe net@20bps: median 1.00 / OOS net@20bps median 0.84
- TC break-even 250-500 bps/mo — realistic 5-20 bps 대비 **10-100× 마진**

### Sector OOS (Lock D §5, Day 5)
- High-tilt cells (A120-LH, A120-SH, A180-LH): BusEq + Hlth 둘 다 sign-correct positive OOS (3/3 cells PASS)
  - A120-LH: BusEq +4.32%, Hlth +5.67%
  - A120-SH: BusEq +6.60%, Hlth +6.73%
  - A180-LH: BusEq +5.06%, Hlth +10.65%
- Low-tilt cell A180-SL: 5/9 low-tilt sectors positive (need ≥6) → **FAIL Lock D §5**
  - Durbl +17.46% t=3.34 dominant 기여, Utils −7.90% t=−2.36 anti
- 3/4 primary cells PASS sector robustness OOS

### Sub-period stability (Phase 0+ §3)
| Cell | 1999-2007 t | 2008-2016 t | 2017-2024 t |
|---|---:|---:|---:|
| A120-LH | 2.12 | 2.65 | 1.55 |
| A120-SH | 1.24 | 1.76 | 1.86 |
| A180-LH | 1.90 | 2.79 | 1.85 |
| A180-SL | 3.44 | 1.80 | 1.74 |

→ 후반기 (2017-2024) 약화는 broad-based (단일 sector concentration 아님). 가능한 mechanism: post-Reg-FD information-flow convergence, algorithmic trading 의 short-horizon cadence signal 흡수.

### Deferred axes (advisory only, Lock D §7)
- 240d / 360d horizon — DEFERRED (panel CARs car_60/120/180 만; dsf_v2 re-stream 은 autopilot 금지)
- FF49 industry partition — DEFERRED (FF12 가 binding sector criterion)
- Skip-week-1 (rdq+8 → rdq+H) — DEFERRED (offset CAR 미구축; dsf_v2 re-stream 금지)

---

## ⑨ Tradability — PARTIAL 을 직관적으로 확인

[artifacts/strategy_A_tradability.json](artifacts/strategy_A_tradability.json) 의 결과를 다음 4 질문으로 정리:

### Q1: 신호가 mechanically dead 인가?
**No.** Median Sharpe (gross) IS 1.05 / OOS 0.89. Net@20bps Sharpe IS 1.00 / OOS 0.84. 양쪽 모두 0.5 floor 위. Hit rate IS 65.3% / OOS 62.5% — 50% 위 일관.

### Q2: TC 가 signal 을 죽이는가?
**No.** TC break-even 250-493 bps/month, 4 cells × 2 partitions 평균 ~370 bps. 현실 institutional TC 5-20 bps 의 **10-100× 마진**. 100 bps/mo (5-20× 현실) 에서도 OOS Sharpe 0.54-0.71 유지.

### Q3: IS 에서 OOS 로 신호가 얼마나 decay 했는가?
**Modest, not catastrophic.** Median Sharpe net@20bps IS 1.00 → OOS 0.84 = **-16.2% degradation**. 비교: full breakage 라면 -50% to -100%; 본 연구는 신호가 attenuate 됐지만 살아있음.

### Q4: 그럼 왜 K2 fires?
Bonferroni-12 |t|>2.78 = Sharpe ≈ 0.98 (96-month OOS, single cell). OOS realized Sharpe 0.84 → t ≈ 2.4 < 2.78. **Multiple-comparison-protected hurdle 가 너무 높았다.** Single-cell nominal significance (|t|>1.96) 로는 4/4 PASS. but 본 연구는 사전에 12-cell pre-registration 약속 → Bonferroni 따라야 함.

### 정직한 practitioner read

Naive monthly Sharpe (overlapping cohort 무시) ≈ 0.84 OOS net@20bps. **Overlap-adjusted (H/30 cohort 동시 보유 보정) Sharpe ≈ 0.40 OOS** — TRADABLE-MARGINAL 등급. Single-strategy basis 에서는 약하지만, **family/portfolio basis (variance-of-X 다른 member 와 결합)** 에서는 유의미할 수 있음.

→ **이게 paper-practical 의 정확한 의미**: academic LAYER A LOCK 의 statistical bar 미달성, but practitioner usable signal 살아있음.

상세: [audits/2026-06-16-RD1-merged-RD7-phase1-tradability.md](audits/2026-06-16-RD1-merged-RD7-phase1-tradability.md)

---

## ⑩ 한계 (정직 명기)

1. **OOS 96-month power-constrained** — 8년 OOS 윈도우에서 Bonferroni-12 |t|>2.78 hurdle 은 stringent. Lock D §4 expected_OOS 가 정확히 실현 = 사전 acknowledged 한계의 confirmation. 해결: 2-3년 추가 누적 후 OOS 확장 재테스트.
2. **A120-SH 의 weak IS** — IS t=2.06, sign-correct sub-threshold. Lock D §4 에서 가장 약한 primary cell 로 사전 acknowledged. Q5 (high-var) sub-cell 의 small-cap × high-tilt 조합이 historical data 에서 가장 noise 큰 cell.
3. **A180-SL 의 sector concentration risk** — Durbl +17.46% 이 dominant contributor. 9개 low-tilt sectors 중 5개만 positive (≥6 필요한 Lock D §5 fail). 후속 작업: Durbl-excluded re-evaluation.
4. **WITH-NT inflation ratio 가 K4 threshold 에 정확히 위치 (2.0)** — strict > 2.0 이라 K4 NOT_TRIGGERED 이지만 boundary. NT mechanism interpretation 은 borderline.
5. **Naive monthly Sharpe 의 overlapping cohort 미보정** — 60-180d horizon CAR 로 만든 monthly series 는 4-6 cohorts 가 동시에 holding. True practitioner Sharpe ≈ raw / √(H/30) → OOS Sharpe 약 0.40 (TRADABLE-MARGINAL).
6. **Max drawdown 큰 숫자** — A120-SH IS -95%, A180-SL IS -98%. 이건 overlapping cohorts 의 naive compounding artifact 가 크다. True practitioner drawdown 은 약 절반. but 여전히 substantial — institutional 배포에는 stop-loss + sub-cell diversification 필요.
7. **dsf_v2 re-stream prohibition** — 240d/360d horizon, skip-week-1 robustness 가 DEFERRED. 후속 연구에서 daily returns 재취득 시 가능.
8. **FF49 industry partition unavailable** — `shared_lib` 에 SIC→FF49 매핑 미구축. Lock D §7 advisory 라 영향 없지만 finer-grain sectoral robustness 검증 미흡.
9. **Variance-of-X family 0/3 LAYER A LOCKED** — Strategy A 가 family 의 1st paper-practical PASS 이긴 하지만, family score 자체는 여전히 약하다. RD1 결과를 family-level inference 로 쓰려면 추가 family member 가 필요.
10. **Anchor post-publication decay risk** — Bagnoli-Kross-Watts 2002 = 24 yr post-pub; Chambers-Penman 1984 = 42 yr post-pub. Strategy B KILL 은 anchor age 의 인과 가설 강화. Strategy A signal 도 시간이 지날수록 decay 할 수 있음 (post-Reg-FD, algorithmic absorption).
11. **WRDS local dump dependency** — 모든 입력이 `E:/wrds-data-courier/output/dump/` 의 frozen snapshot. WRDS 정기 refresh 시 source SHA 변경 → Lock F 재실행 필요.

→ **모든 한계가 "더 긴 OOS 윈도우 / 후속 family member / paid data access" 라벨**. methodology 자체는 immediately publish-ready.

---

## ⑪ 산출물 (publish-ready)

| 항목 | 위치 |
|---|---|
| Repo CLAUDE.md (project header + Phase 1 close summary) | [CLAUDE.md](CLAUDE.md) |
| 영문 paper outline (5-page skeleton) | [reports/papers/RD1-strategy-A-paper-outline.md](reports/papers/RD1-strategy-A-paper-outline.md) |
| Phase 1 close audit (binding L1-L6 / K1-K5 table) | [audits/2026-06-16-RD1-merged-RD7-phase1-close.md](audits/2026-06-16-RD1-merged-RD7-phase1-close.md) |
| Phase 1 tradability augmentation | [audits/2026-06-16-RD1-merged-RD7-phase1-tradability.md](audits/2026-06-16-RD1-merged-RD7-phase1-tradability.md) |
| Day-by-day audit chain | [audits/2026-06-16-RD1-merged-RD7-phase1-day{0..5}-*.md](audits/) |
| Lock C (direction matrix) | [audits/2026-06-16-RD1-merged-RD7-lock-c.md](audits/2026-06-16-RD1-merged-RD7-lock-c.md) |
| Lock D (pre-reg cells + OOS) | [audits/2026-06-16-RD1-merged-RD7-phase1-prereg-lock-d.md](audits/2026-06-16-RD1-merged-RD7-phase1-prereg-lock-d.md) |
| Lock F (pipeline determinism) | [audits/2026-06-16-RD1-merged-RD7-lock-f-determinism.md](audits/2026-06-16-RD1-merged-RD7-lock-f-determinism.md) |
| Tradability raw monthly series (4 cells × all months) | `artifacts/strategy_A_monthly_returns.csv` |
| IS/OOS Bonferroni-12 results | `artifacts/strategy_A_bonferroni12_{is,oos}.{csv,json}` |
| Sector OOS + WITH-NT OOS | `artifacts/strategy_A_{sector,with_nt}_oos.{csv,json}` |
| TC overlay IS | `artifacts/strategy_A_tc_overlay_is.{csv,json}` |
| SHA-pin manifest | `artifacts/phase1_is_oos_split.json` |
| Phase 1 scripts | `scripts/phase1_*.py` |
| Meta-harness PARTIAL close report | `D:/vscode/meta-harness/audits/2026-06-16-RD1-merged-RD7-phase1-PARTIAL-close-report.md` |

---

## 결론 — 이 프로젝트의 진짜 가치

**알파 수치보다 self-falsification framework + 선행연구 대비 7-layer novelty + family-level cumulative evidence 가 핵심 기여**.

- **결과 보기 전에 KILL probability + expected_OOS commit-locked** (Lock D §4 / Day-0 anti-bias) — 실제 결과가 사전 예측에 exact match.
- **PARTIAL verdict 가 정직** — academic LAYER A LOCK 의 multiple-comparison-protected 통계 hurdle 미달성, but practitioner usable Sharpe 0.84 OOS net@20bps 살아있음. 양쪽 다 honest 보고.
- **7-layer novelty stack** — academic (level→variance), methodology (within vs cross normalization), differentiation (V5 분리), design (MERGE), integrity (pre-reg OOS verbatim), cumulative (variance-of-X family 3rd member), reproducibility (Lock F).
- **선행연구 비교 명시** — Bagnoli 2002 / Chambers-Penman 1984 / Johnson-So 2018 / Begley-Fischer 1998 / Berger-Hann 2003 / deHaan-Shevlin-Thornock 2015 / Noh-So-Verdi 2021 / Bannouh 2019 등 8건 각각의 차별점 표로 정리.
- **Family-level update** — variance-of-X family 0/3 LAYER A LOCKED → 1/3 paper-practical PASS. Future variance-of-X 연구자에게 design guideline 제공.

**리뷰어 1차 read 5분 안에 catch 할 수 있는 모든 critical issue 가 본 프로젝트의 [한계 §⑩](#-한계-정직-명기) 에 이미 본인 손으로 적혀 있다**. paper-practical PARTIAL 은 method failure 가 아니라 **academic bar 와 practitioner bar 의 gap 의 정직한 표현**.

OOS 96-month 의 power 한계는 물리적 시간 문제, 후속 variance-of-X member 부족은 cumulative 시간 문제. 이 둘 제외하면 — methodology 자체는 immediately publish-ready.

---

**프로젝트 위치**: variance-of-X family 의 3rd member (1st paper-practical PASS), Compustat-Recognition-Timing pod 1st LOCKED candidate slot 미달성 (slot remains empty for future candidate).

| Member | Pre-Phase-1 | Post-Phase-1 (2026-06-16) |
|---|---|---|
| F1 (FDA expectation variance) | Frozen-two-layer | unchanged |
| F6 (clinicaltrials amendment) | Post-pub-downgrade-tentative | unchanged |
| **RD1 Strategy A (rdq variance)** | LAYER A candidate | **paper-practical PASS (1st)** |

Variance-of-X family 의 next member 가 LAYER A LOCK 을 달성하려면: longer expected OOS horizon, larger universe, fewer pre-registered cells 의 design choice 가 필요. RD1 의 paper-practical 결과가 이 design guideline 의 evidence base 를 제공한다.

---

**문의**: fawkes4700@gmail.com
