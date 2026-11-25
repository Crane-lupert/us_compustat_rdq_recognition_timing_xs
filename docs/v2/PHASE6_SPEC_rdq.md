# 6차 — RDQ·SEC Letter 추가 가설 (라운드 3, 마지막), 사전 고정 사양

> 공개 사본 (2026-11-25). 원문에서 (i) 같은 규칙으로 진행한 다른 프로젝트의 가설·결과, (ii) 작업 지시 인용과 로컬 폴더 이름을 뺐다. 뺀 자리는 **[생략]** 으로 표시했다. 그 밖의 문장은 원문 그대로다. 문서 안의 경로 (`_main_checks/…`, `RDQ_cadence/…`) 는 작업 폴더 (`RDQ_V2_WORK`) 기준이다.

고정일 2026-11-21. 결과 변수 (수익률·NT 제출 여부) 를 보기 전에 썼다. 공통 규칙은 `PHASE4_PROTOCOL.md`, 라운드 규칙은 `PHASE5_SPEC.md` §0 그대로다. 메인 스레드가 직접 수행하고, 산출물은 `_main_checks/phase6/` 에 둔다. SEC 에는 더 요청하지 않는다 (라운드 2 에서 SEC 가 신원을 밝히지 않은 자동 요청을 거절함). 이 랩탑에 있는 자료만 쓴다.

## 0. 이 라운드를 여는 근거와 끝내는 규칙

라운드 2 결과 (모두 통과 못 함): RDQ-R t +0.77, RDQ-I t +0.41 (예상과 반대 부호), **[생략]**. `PHASE5_SPEC.md` §0 의 중지 규칙은 "선행연구 대조를 통과하는 새 후보가 남아 있을 때만 한 라운드를 더 한다. 그 뒤에는 멈춘다" 이다. 아래 §1 의 대조에서 두 후보가 남았으므로 한 라운드를 더 한다. **이 라운드가 마지막이다.** 통과하면 선행연구 정밀 대조 (Stage B) 로 넘기고, 통과하지 못하면 "이 환경에서는 나오지 않는다" 로 보고하고 멈춘다.

누적 다중검정: RDQ 는 주 검정 5개 뒤의 6번째 → |t| ≥ 2.64. SEC Letter 는 6개 뒤의 7번째 → |t| ≥ 2.69. 전·후반 부호가 같아야 하고 후반 단독으로 |t| ≥ 1.96.

## 1. 후보와 선행연구 사전 대조 (2026-11-21 검색)

| 후보 | 가장 가까운 선행연구 | 판단 |
|---|---|---|
| RDQ-F 발표 예정일을 넘기기 전의 내부자 거래 방향이 지연 뒤 수익률을 가르는가 | 검색 1회에서 직접 연구를 못 찾음. 가까운 것은 다른 사건 앞의 내부자 매도 (레터 공개 전 — Dechow–Lawrence–Ryans 2016, 사이버 침해 공시 전) | **진행** |
| 지연 신호 자체 (기한 넘긴 기업 공매도) | Chambers–Penman (1984), Bagnoli–Kross–Watts (2002), Duarte-Silva 외 (2013), 상용 신호 (Wall Street Horizon, RavenPack) | 제외 (4차 R1 과 같음, 이미 연구·상용화) |
| 지연의 신용시장 반응 (CDS·회사채) | 검색 1회에서 직접 연구를 못 찾음 | 제외 (검정력: 4차 R1 의 효과는 시가총액 1001–3000위에만 있음 — 1–500위 −9.36bp t −0.87, 501–1000위 −2.96bp t −0.45. CDS·회사채가 있는 기업은 대형주) |
| 지연을 미리 예측해 그 전에 매도 | RavenPack 백서가 앞당김·지연 분류와 예측 포트폴리오를 냄 | 제외 (상용화됨) |
| 지연 뒤 다음 분기의 수익률 (지연의 지속) | 4차 R3 (발표 뒤 이른 기업 − 늦은 기업) 가 0 | 제외 (근거 없음) |

P8 대조 기록 (인용한 선행연구):

- Anchor cite: Chambers & Penman (1984), "Timeliness of Reporting and the Stock Price Reaction to Earnings Announcements", *Journal of Accounting Research* 22(1): 21–47 / P8 verify: VERIFIED (서지; 결과는 2차 인용으로 확인 — 이른 발표는 좋은 소식, 늦은 발표는 나쁜 소식) / Evidence: https://ideas.repec.org/a/bla/joares/v22y1984i1p21-47.html
- Anchor cite: Bagnoli, Kross & Watts (2002), *Journal of Accounting Research* 40(5): 1275–1296 / P8 verify: VERIFIED (블록리스트 C.10·C.126 의 정정 반영 — 경영진이 미리 알린 예정일을 쓰며, 예정일을 넘기면 주가가 내리고 지연이 길어질수록 더 내린다고 보고) / Evidence: https://ideas.repec.org/a/bla/joares/v40y2002i5p1275-1296.html
- Anchor cite: Duarte-Silva, Fu, Noe & Ramesh (2013), "How Do Investors Interpret Announcements of Earnings Delays?", *Journal of Applied Corporate Finance* 25(1): 64–71 / P8 verify: VERIFIED (처음에 넷째 저자를 Rao 로 기억했으나 Ramesh 가 맞음 — 검색으로 정정) / Evidence: https://econpapers.repec.org/RePEc:bla:jacrfn:v:25:y:2013:i:1:p:64-71
- Anchor cite: Ryans (2021), "Textual classification of SEC comment letters", *Review of Accounting Studies* 26(1): 37–80, DOI 10.1007/s11142-020-09565-6 / P8 verify: VERIFIED (블록리스트 C.123 의 정정 반영 — 분류기는 다음 해 재작성·손상으로 학습하며, 레터 공개의 평균 주가 효과는 유의하지 않다고 보고) / Evidence: https://ideas.repec.org/a/spr/reaccs/v26y2021i1d10.1007_s11142-020-09565-6.html
- Anchor cite: Bartov & Konchitchki (2017), "SEC Filings, Regulatory Deadlines, and Capital Market Consequences", *Accounting Horizons* 31(4): 109–131 / P8 verify: VERIFIED (블록리스트 C.102 의 정정 반영 — 학술지는 Accounting Horizons) / Evidence: https://faculty.haas.berkeley.edu/yaniv/files/Papers_Publications/SEC-Filings-Regulatory-Deadlines-Capital-Market-Consequences_Bartov-Konchitchki_AH.pdf
- Anchor cite: RavenPack earnings date white paper (업계 백서, 심사 없음) / P8 verify: VERIFIED (존재만; 수치는 미검증) / Evidence: https://cdn-static.bizzabo.com/bizzabo.users.files/145245/251725/6341843/RavenPack%20Earnings%20Date%20Paper.pdf

동기와 novelty 를 나눠 적는다 (L1). RDQ-F 의 novelty 문장: "예정일을 넘긴 기업 가운데 그 전 180일의 내부자 순매수·순매도 방향이 지연 기간 수익률을 가른다는 것은 선행연구에 없다." **[생략]** 검색 1회 기준이므로 통과하면 Stage B 에서 다시 대조한다.

## 2. RDQ-F — 지연 전 내부자 거래 방향 (주 검정)

- 가설: 발표 예정일을 넘기고 침묵하는 기업 가운데, 그 전에 내부자가 판 기업은 더 내리고 내부자가 산 기업은 덜 내린다.
- 표본: 4차 R1 의 SEC 검증 미발표 사건 (`_main_checks/r1_cache/r1_events_sec_verified.parquet` 의 `verified silent`) 중 예정일 `E` 가 2015-07-01 이후이고, 그 기업의 Form 4 기록이 진입 연도나 그 전 해에 있는 사건. 결과를 보기 전에 센 수: 2,363건 (2015–2019 1,179 / 2020–2024 1,184).
- 내부자 거래: 임원·이사의 공개시장 매도 (S)·매수 (P), 거래일 기준, `[E − 180일, E)`. 자료는 4차 X2a 에서 메인 스레드가 직접 파싱한 표 (`_main_checks/x2a_cache/od_sales.parquet`).
- 방향 점수 `D`: 매수가 한 번이라도 있으면 +1, 매도만 있으면 −1, 둘 다 없으면 0. 결과를 보기 전에 센 수: +1 640건, −1 966건, 0 757건.
- 결과 변수: 보유 기간 (R1 과 같은 진입·청산) 의 종목 수익률 − 같은 기간 유니버스 동일가중 수익률 (라운드 2 RDQ-R 과 같음), %.
- 통계량: `결과 ~ D + log(진입일 시가총액) + 진입 연도 고정효과`, 진입 월 군집. `D` 의 계수. **예상 부호 양.** 전·후반 2015–2019 / 2020–2024.
- 시가총액을 통제하는 이유: 내부자 매도는 큰 기업에서 더 흔하고 (1,000위 안 55%, 밖 34%), R1 의 효과는 작은 기업에 있다. 통제하지 않으면 가설과 반대 방향으로 섞인다.
- 함께 보고: 세 집단의 평균, 매수 집단 대 나머지, 매도 집단 대 나머지, 시가총액 통제 없는 판.
- 검정력 (결과 전 계산): 보유 기간 초과수익의 표준편차를 11% 로 보면 `D` 계수의 표준오차는 약 0.28%p 이다. |t| ≥ 2.64 가 되려면 계수가 0.74%p 이상, 즉 매수 집단과 매도 집단의 차이가 1.5%p 이상이어야 한다 (R1 의 평균 효과는 약 −1.3%). 통과 가능성은 낮다고 본다.

## 3. **[생략]** (다른 프로젝트의 주 검정)

## 4. 판정

`PHASE5_SPEC.md` §5 와 같다. 통과한 검정만 Stage B 로 넘긴다.
