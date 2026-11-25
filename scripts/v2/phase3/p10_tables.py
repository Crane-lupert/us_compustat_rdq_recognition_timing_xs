"""p10 (Step 4): published -> corrected (main spec) correspondence for every table / figure / abstract number of
reports/papers/paper_v1_en.md (repo HEAD a2860f4). Writes phase3/out/corrected_tables.csv
(columns: table_id, item, published, corrected, spec, note).
Spec codes: M = main spec (Russell-3000 proxy + PIT link + simple returns + calendar-time monthly LS, NW auto-lag t,
exact Bonferroni-12); costs: 'spread' / 'spread+borrow' use DEV1 slot turnover (frozen-rule value in note);
B2 = cohort statistic (published statistic, simple returns, main universe); D2/D3/D4 = confirmation tests.
"""
import sys
sys.dont_write_bytecode = True
import json
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from p3common import OUT, PRIMARY  # noqa: E402

S = pd.read_csv(OUT / "ct_stats.csv")
C = pd.read_csv(OUT / "cohort_stats.csv")
D2 = pd.read_csv(OUT / "d2_cp.csv")
T6 = pd.read_csv(OUT / "d4_table6.csv")
T8 = pd.read_csv(OUT / "d4_table8.csv")
D3 = pd.read_csv(OUT / "d3_lpm.csv")
CR = json.loads((OUT / "criteria.json").read_text(encoding="utf-8"))
ser = pd.read_pickle(OUT / "ct_series.pkl")


def g(cell, per, cost="gross", uni="main", f="t_nw"):
    r = S[(S.universe == uni) & (S.cell == cell) & (S.period == per) & (S.cost == cost)]
    return float(r[f].iloc[0])


def mt(cell, per, cost="gross"):
    return f"{100*g(cell, per, cost, f='mu_m'):+.3f}%/mo (t {g(cell, per, cost):.2f})"


def b2(cell, per):
    r = C[(C.variant == "B2_simple_cohort_main") & (C.cell == cell) & (C.period == per)].iloc[0]
    return f"B2 cohort {100*r.mu:+.2f}% (t {r.t_nw12:.2f})"


def cnt(per, cost="gross", key="pass_bonf2", uni="main"):
    t = S[(S.universe == uni) & S.cell.isin([f"A{H}-{a}{b}" for H in (60, 120, 180) for a in "LS" for b in "HL"]) & (S.period == per) & (S.cost == cost)]
    return int(t[key].sum())


def comp(per, cost):
    return g("COMPOSITE4", per, cost, f="sharpe")


rows = []
A = rows.append
d2 = {(r.outcome, r.period): r for r in D2.itertuples()}
# ---------------- abstract ----------------
A(["abstract", "universe / sample", "Russell 3000 panel of 620,290 firm-quarters (CRSP+Compustat) 1999-2024",
   "Compustat signal panel 620,290 firm-quarters (exact); tested universe = Russell-3000 proxy (June top-3,000 CRSP common): 259,453 events / 7,903 firms, 105,236 Q1/Q5 positions, 2000-02..2024-12",
   "M", "Russell 3000 was never implemented in the repo (phase-1 D5)"])
A(["abstract", "in-sample sign-correct cells", "12/12", f"{cnt('IS', key='sign_ok')}/12", "M gross", ""])
A(["abstract", "hold-out sign-correct cells", "11/12 (2017-2024 hold-out)", f"{cnt('LATE', key='sign_ok')}/12 (2017-2024 later subperiod, not a hold-out)", "M gross", "2017-2024 t were in Lock D before the 'reveal' (phase-1 D4)"])
A(["abstract", "in-sample Bonferroni passes", "4/12", f"{cnt('IS')}/12 (A180-SH t {g('A180-SH','IS'):.2f} vs exact crit 2.898; NW12 t {g('A180-SH','IS',f='t_nw12'):.2f})", "M gross", f"B2 cohort statistic: {int(C[(C.variant=='B2_simple_cohort_main')&(C.period=='IS')].pass_bonf2.sum())}/12 (A120-SL)"])
A(["abstract", "hold-out Bonferroni passes", "0/12", f"{cnt('LATE')}/12", "M gross", ""])
A(["abstract", "composite net Sharpe (HAC, 20 bp) IS / hold-out", "1.01 / 0.82",
   f"gross {comp('IS','gross'):.2f} / {comp('LATE','gross'):.2f}; net of spread {comp('IS','net_qs_s'):.2f} / {comp('LATE','net_qs_s'):.2f}; net of spread+borrow {comp('IS','net_all_s'):.2f} / {comp('LATE','net_all_s'):.2f}",
   "M composite, calendar-time Sharpe", f"frozen-rule costs: spread {comp('IS','net_qs'):.2f}/{comp('LATE','net_qs'):.2f}, spread+borrow {comp('IS','net_all'):.2f}/{comp('LATE','net_all'):.2f}; aux 20bp/round trip {comp('IS','net_20_s'):.2f}/{comp('LATE','net_20_s'):.2f}"])
A(["abstract", "tangent benchmark Sharpe", "1.05 / 1.01", "N/A (benchmark not part of the phase-3 spec)", "-", "benchmark comparison relied on the overlapping-cohort HAC Sharpe; not part of the phase-3 spec"])
A(["abstract", "one-week delay strengthens all 4 primary cells", "yes (4/4)",
   "no: change in t IS " + ", ".join(f"{r.change_t:+.2f}" for r in T6[T6.period=='IS'].itertuples()) + "; later " + ", ".join(f"{r.change_t:+.2f}" for r in T6[T6.period=='LATE'].itertuples()),
   "D4 Table 6 (M, like-for-like)", "order A120-LH, A120-SH, A180-LH, A180-SL"])
A(["abstract", "Chambers-Penman channel decayed / fails", "0/12 symmetric, 0/24 asymmetric; decayed",
   f"early-late 3-day market-adjusted {100*d2[('ar3','IS')].early_minus_late:+.2f}% (t {d2[('ar3','IS')].t_nw:.2f}) 2000-2016; {100*d2[('ar3','LATE')].early_minus_late:+.2f}% (t {d2[('ar3','LATE')].t_nw:.2f}) 2017-2024",
   "D2", "original CP expected date (prior-year same quarter), direction corrected; published test used 60-180d post-windows and inverted quintile labels"])
# ---------------- Table 1 ----------------
A(["T1", "universe (this study)", "Russell 3000 ∩ Compustat", "Russell-3000 proxy (June top-3,000 CRSP shrcd 10/11, exchcd 1/2/3) ∩ Compustat via PIT CUSIP->permno", "M", ""])
A(["T1", "hold-out validation", "2017-2024 hold-out (96 months)", "2017-2024 later subperiod (96 months), not a hold-out", "M", ""])
A(["T1", "separation from PEAD", "one-week-delayed window strengthens result", "mixed (see D4 Table 6)", "D4", ""])
A(["T1", "late-filer exclusion share", "≈4% of sample", "3.02% (19,314 firm-quarters)", "panel", "phase-1 s03 log"])
A(["T1", "CP result in modern panel", "0/12 significant (24-cell asymmetric also fails)", f"3-day early-late +{100*d2[('ar3','IS')].early_minus_late:.2f}% (t {d2[('ar3','IS')].t_nw:.1f}) / +{100*d2[('ar3','LATE')].early_minus_late:.2f}% (t {d2[('ar3','LATE')].t_nw:.1f})", "D2", ""])
A(["T1", "this study result", "IS 4/12 Bonferroni; hold-out sign-correct 11/12", f"IS {cnt('IS')}/12; later {cnt('LATE')}/12; sign {cnt('IS',key='sign_ok')}/12, {cnt('LATE',key='sign_ok')}/12", "M gross", ""])
# ---------------- Table 2 / text counts ----------------
for it, pub, cor in [("Compustat rows with rdq & datadate (1999-2024)", "≈750,000", "753,594"), ("after 10<=gap<=180", "≈720,000", "740,523"),
                     ("after trailing-8Q >=6 filter", "645,000", "639,604"), ("after late-filer exclusion", "620,290", "620,290"),
                     ("with >=1 horizon CAR", "367,725", "371,847 (repo CUSIP link, incl. partial-2025 rdq); PIT link with valid entry rdq<=2024: 443,692; Russell proxy sorting universe 259,453")]:
    A(["T2", it, pub, cor, "panel", "phase-1 s03/s04 logs; phase-3 p02/p03 logs"])
A(["S3.2/S4.5", "IS / hold-out / 2025 partition rows", "436,916 / 178,210 / 5,164", "436,916 / 178,210 / 5,164 (panel partition by rdq; later part is not a hold-out)", "panel", ""])
# ---------------- Tables 3/4 + Appendix A ----------------
pub_is = {"A120-LH": ("+3.37%", "3.37"), "A120-SH": ("+2.66%", "2.06"), "A180-LH": ("+4.14%", "3.31"), "A180-SL": ("+4.93%", "3.62"),
          "A60-LH": ("+1.39%", "2.24"), "A60-LL": ("+0.85%", "1.26"), "A60-SH": ("+2.03%", "1.64"), "A60-SL": ("+2.22%", "3.09"),
          "A120-LL": ("+2.21%", "1.70"), "A120-SL": ("+2.94%", "2.68"), "A180-LL": ("+3.35%", "1.99"), "A180-SH": ("+3.69%", "2.17")}
pub_oos = {"A120-LH": ("+2.48%", "1.55"), "A120-SH": ("+3.73%", "1.86"), "A180-LH": ("+3.51%", "1.85"), "A180-SL": ("+4.62%", "1.74")}
for c, (mu, t) in pub_is.items():
    tid = "T3" if c in PRIMARY else "A.1"
    A([tid, f"{c} in-sample mu, t", f"{mu}, {t}", mt(c, "IS"), "M gross", f"{b2(c,'IS')}; units differ: published mu = mean H-day cohort log spread"])
for c, (mu, t) in pub_oos.items():
    A(["T4", f"{c} hold-out mu, t", f"{mu}, {t}", mt(c, "LATE"), "M gross (later subperiod)", b2(c, "LATE")])
A(["T4/S5.2", "hold-out sign-correct cells", "11/12", f"{cnt('LATE',key='sign_ok')}/12", "M gross", ""])
# ---------------- Figure 1 ----------------
cs = ser[("main", "COMPOSITE4")]
cum = lambda s: float((1 + s).prod() - 1)
A(["Fig1", "composite cumulative return & HAC Sharpe", "vol-matched cumsum of overlapping cohort returns; HAC Sharpe 1.06/0.87 gross, 1.01/0.82 net",
   f"calendar-time compounded composite: gross {100*cum(cs.loc['2000-02':'2016-12','gross']):+.1f}% (2000-02..2016-12), {100*cum(cs.loc['2017-01':'2024-12','gross']):+.1f}% (2017-2024); net of spread+borrow {100*cum(cs.loc['2000-02':'2016-12','net_all_s']):+.1f}% / {100*cum(cs.loc['2017-01':'2024-12','net_all_s']):+.1f}%",
   "M composite", "cumsum of overlapping cohort returns is not a portfolio path (phase-1 D2)"])
# ---------------- Section 5.3 CP ----------------
A(["S5.3", "CP symmetric/asymmetric family-wise passes; sign-correct", "0/12, 0/24; 5/12 sign-correct",
   f"early-late 3-day: IS +{100*d2[('ar3','IS')].early_minus_late:.3f}% t {d2[('ar3','IS')].t_nw:.2f} (T={d2[('ar3','IS')].T}); later +{100*d2[('ar3','LATE')].early_minus_late:.3f}% t {d2[('ar3','LATE')].t_nw:.2f} (T={d2[('ar3','LATE')].T}); raw: +{100*d2[('raw3','IS')].early_minus_late:.3f}% (t {d2[('raw3','IS')].t_nw:.2f}) / +{100*d2[('raw3','LATE')].early_minus_late:.3f}% (t {d2[('raw3','LATE')].t_nw:.2f})",
   "D2", "Strategy B's own 60-180d cells were not re-run under M (not in the phase-3 spec)"])
# ---------------- FF49 ----------------
ff = T8[(T8.block == "FF49 tilt 12 cells")]
A(["S5.4.1", "FF49 partition: family-wise significant (full panel); A120-SH t", "5/12 (full panel, incl. 2025); A120-SH t 2.97",
   f"IS {int(ff[ff.period=='IS'].bonf12_exact.iloc[0])}/12, later {int(ff[ff.period=='LATE'].bonf12_exact.iloc[0])}/12; A120-SH-FF49 t {g('A120-SH-FF49','IS'):.2f} (IS) / {g('A120-SH-FF49','LATE'):.2f}",
   "D4 (M, FF49 tilt)", "passing cell: A180-SH-FF49"])
# ---------------- Table 5 ----------------
pub5 = {"A240-LH": ("+4.82%", "3.72"), "A240-LL": ("+5.33%", "3.47"), "A240-SH": ("+4.20%", "2.27"), "A240-SL": ("+4.76%", "2.57"),
        "A360-LH": ("+6.49%", "3.91"), "A360-LL": ("+7.27%", "3.51"), "A360-SH": ("+5.03%", "2.20"), "A360-SL": ("+6.50%", "3.21")}
for c, (mu, t) in pub5.items():
    A(["T5", f"{c} mu, t (full panel)", f"{mu}, {t}", f"IS {mt(c,'IS')}; later {mt(c,'LATE')}", "D4 (M, extended H)", ""])
A(["S5.4.2", "signal strengthens monotonically with horizon; A360-LH strongest (t 3.91)", "yes",
   f"no: IS t A60/120/180/240/360-LH = {g('A60-LH','IS'):.2f}/{g('A120-LH','IS'):.2f}/{g('A180-LH','IS'):.2f}/{g('A240-LH','IS'):.2f}/{g('A360-LH','IS'):.2f}; strongest IS cell A180-SH",
   "D4 (M)", ""])
# ---------------- Table 6 ----------------
pub6 = {"A120-LH": ("3.37", "3.44", "+0.07"), "A120-SH": ("2.06", "3.19", "+1.13"), "A180-LH": ("3.31", "3.59", "+0.28"), "A180-SL": ("3.62", "3.69", "+0.07")}
for c, (a, b, d) in pub6.items():
    r_is = T6[(T6.cell == c) & (T6.period == "IS")].iloc[0]
    r_la = T6[(T6.cell == c) & (T6.period == "LATE")].iloc[0]
    A(["T6", f"{c} next-day t / delayed t / change", f"{a} / {b} / {d} (IS vs full panel incl. 2025)",
       f"IS {r_is.t_nextday:.2f} / {r_is.t_skipweek:.2f} / {r_is.change_t:+.2f}; later {r_la.t_nextday:.2f} / {r_la.t_skipweek:.2f} / {r_la.change_t:+.2f}",
       "D4 (M, like-for-like)", ""])
# ---------------- TC overlay text ----------------
A(["S5.4.4", "IS retention of gross spread net of TC", ">=62% for 4/4 primary cells",
   "net of spread+borrow / gross (IS): " + ", ".join(f"{c} {CR['L5_K5_net_all_over_gross']['net_all_s_IS'][c]}" for c in PRIMARY),
   "M (DEV1)", "negative ratios = net mean below zero; A120-LH gross ~0"])
A(["S5.4.4", "break-even TC", "248-493 bp per month", f"composite gross {100*g('COMPOSITE4','IS',f='mu_m'):.3f}%/mo IS, {100*g('COMPOSITE4','LATE',f='mu_m'):.3f}%/mo later = break-even monthly cost; realised IS spread cost {100*cs.loc['2000-02':'2016-12','cost_qs_s'].mean():.3f} (DEV1; frozen {100*cs.loc['2000-02':'2016-12','cost_qs'].mean():.3f}) and borrow {100*cs.loc['2000-02':'2016-12','borrow'].mean():.3f} %/mo",
   "M composite", "published figure was per cohort round trip, not per month"])
A(["S4.6", "20 bp is conservative", "20 bp monthly round trip", "main-universe quoted spread at entry: long 0.26%, short 0.57% (per round trip = full spread); B1 universe 0.55% / 2.04%", "M / B1", "p04 log"])
# ---------------- Table 7 ----------------
for sc, pub, cor, note in [
    ("S0 (20 bp)", "+1.02 / +0.84; ann +45.5% / +42.6%", f"aux 20bp/round trip: Sharpe {comp('IS','net_20_s'):.2f} / {comp('LATE','net_20_s'):.2f}; ann {100*g('COMPOSITE4','IS','net_20_s',f='ann_ret'):+.1f}% / {100*g('COMPOSITE4','LATE','net_20_s',f='ann_ret'):+.1f}%", "M composite"),
    ("gross", "(1.06 / 0.87 gross, Fig 1)", f"Sharpe {comp('IS','gross'):.2f} / {comp('LATE','gross'):.2f}; ann {100*g('COMPOSITE4','IS',f='ann_ret'):+.1f}% / {100*g('COMPOSITE4','LATE',f='ann_ret'):+.1f}%", "M composite"),
    ("S1 (size borrow)", "+0.80 / +0.68; ann +34.9% / +34.8%", f"spread+borrow (borrow accrued over holding period): Sharpe {comp('IS','net_all_s'):.2f} / {comp('LATE','net_all_s'):.2f}; ann {100*g('COMPOSITE4','IS','net_all_s',f='ann_ret'):+.1f}% / {100*g('COMPOSITE4','LATE','net_all_s',f='ann_ret'):+.1f}%", "M composite (DEV1)"),
    ("S2-S4 (short-universe filters)", "+0.13/+0.42, +0.21/+0.67, +0.59/+0.30", "N/A (short-basket filters not in the phase-3 spec)", "not in the phase-3 spec (short-basket filters not re-run)")]:
    A(["T7", sc, pub, cor, "-" if cor.startswith("N/A") else "M composite", note if note != "M composite" else "costs by DEV1 slot turnover"])
# ---------------- with-late-filer ----------------
A(["S5.4.6", "with-late-filer hold-out passes", "2/12 vs 0/12", "N/A (WITH-NT not in the phase-3 spec)", "-", "WITH-NT not in the phase-3 spec; moot after K1/K2"])
# ---------------- Table 8 ----------------
for r in T8.itertuples():
    A(["T8", f"{r.block} [{r.period}]", "", f"family-wise (exact Bonferroni-12) {r.bonf12_exact}/{r.cells}; |t|>2.78 {r.abs_t_278}; nominal 5% {r.nominal5} (chance {r.chance}); sign-correct {r.sign_correct}/{r.cells}", "D4 (M gross)", ""])
A(["T8", "published total", "40 cells, 14 family-wise significant, 39 sign-correct (mixed samples)",
   f"IS {int(T8[(T8.block=='Total')&(T8.period=='IS')].bonf12_exact.iloc[0])}/40 significant, {int(T8[(T8.block=='Total')&(T8.period=='IS')].sign_correct.iloc[0])}/40 sign; later {int(T8[(T8.block=='Total')&(T8.period=='LATE')].bonf12_exact.iloc[0])}/40, {int(T8[(T8.block=='Total')&(T8.period=='LATE')].sign_correct.iloc[0])}/40 sign",
   "D4 (M gross)", "same sample per row; blocks overlap (same positions)"])
# ---------------- limitations / conclusion ----------------
A(["S6.1/S7", "hold-out net Sharpe; realised hold-out t", "0.82; (1.55, 1.86, 1.85, 1.74)",
   f"composite later net of spread+borrow {comp('LATE','net_all_s'):.2f}; later t (M gross) " + ", ".join(f"{g(c,'LATE'):.2f}" for c in PRIMARY), "M", ""])
A(["S6.2", "per-cell Sharpe requirement ~0.98", "~0.98", "N/A (derived from the overlapping-cohort statistic)", "-", "derived from the overlapping-cohort statistic"])
A(["S6.4", "linkage error < 1% (cross-check)", "<1%", "no cross-check existed; PIT ncusip link agrees with phase-1 header-CUSIP permno link on 99.8% of jointly linked events; 7,394/371,847 repo CARs start >10 days after rdq", "link", "p02 log"])
A(["S6.9", "rdq series begins 2000-02-11 (vendor boundary)", "vendor boundary", "rdq non-null from 1985 (50-89% of rows 1985-2000); first panel rdq 2000-02-11 follows from datadate>=1999 + 6-quarter warm-up", "panel", "phase-1 s03 log"])
A(["S7", "sign-consistent 39/40", "39/40", f"IS 39/40, later {int(T8[(T8.block=='Total')&(T8.period=='LATE')].sign_correct.iloc[0])}/40", "D4", ""])
A(["S7", "tradeable at Sharpe ≈0.8 net", "≈0.8", f"composite net of spread+borrow {comp('IS','net_all_s'):.2f} (IS) / {comp('LATE','net_all_s'):.2f} (later)", "M composite (DEV1)", ""])
A(["App.C", "row counts 620,290 / 436,916 / 178,210", "same", "same", "panel", "data counts confirmed"])
# ---------------- extra: D3 ----------------
q5 = D3[(D3['var'] == 'Q_5')]
for r in q5.itertuples():
    A(["(new) D3", f"Q5 vs Q1 12-month performance-delisting LPM [{r.period}]", "not in paper",
       f"{100*r.coef:+.3f} pp (t {r.t:.2f}, N {r.N:,}, {r.clusters:,} firms); raw rate Q1 {100*r.base_rate_Q1:.2f}% vs Q5 {100*r.rate_Q5:.2f}%",
       "D3 exploratory", "controls log cap, trailing vol, year FE; gvkey clusters"])
T = pd.DataFrame(rows, columns=["table_id", "item", "published", "corrected", "spec", "note"])
T.to_csv(OUT / "corrected_tables.csv", index=False)
print(f"wrote corrected_tables.csv ({len(T)} rows)")
pd.set_option("display.width", 250, "display.max_colwidth", 140)
print(T[["table_id", "item", "published", "corrected"]].to_string(index=False))
