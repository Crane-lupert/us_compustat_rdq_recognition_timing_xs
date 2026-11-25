"""s12: S1 borrow overlay. Repo charges (annual bps)/12 once per COHORT although each cohort is held H calendar days
(repo phase1_robustness_borrow_overlay.py L174). Correct cohort charge = bps/yr * H/365.
(i) paper basis with H/365 charge; (ii) calendar-time simple-return composite (s06, repo link) with monthly short-leg borrow."""
import numpy as np, pandas as pd
from common import build_cells, repo_hac_sharpe, split, nw_se, PRIMARY
P = pd.read_parquet("panel_ret.parquet"); df = build_cells(P)
sched = [(10_000, np.inf, 25), (2_000, 10_000, 50), (300, 2_000, 200), (100, 300, 800), (0, 100, 2000)]
def bps(m):
    if pd.isna(m): return 2000.0
    for lo, hi, b in sched:
        if lo <= m < hi: return float(b)
    return 2000.0
df["borrow"] = df["mcap_mil"].apply(bps)
spec = {"A120-LH": (120,"L","H"), "A120-SH": (120,"S","H"), "A180-LH": (180,"L","H"), "A180-SL": (180,"S","L")}
rep, fix, bor = {}, {}, {}
for c,(H,sz,it) in spec.items():
    sub = df[(df.size_bin==sz)&(df.ind_bin==it)].dropna(subset=[f"car_{H}","q5","mcap_mil"])
    q1 = sub[sub.q5==1].groupby("rdq_month")[f"car_{H}"].mean(); q5 = sub[sub.q5==5].groupby("rdq_month")[f"car_{H}"].mean()
    br = sub[sub.q5==5].groupby("rdq_month")["borrow"].mean()
    g = (q1-q5).dropna(); b = br.reindex(g.index).fillna(0)
    rep[c] = g - 0.002 - b/12/1e4; fix[c] = g - 0.002 - b*H/365/1e4
    bb = b.copy(); bb.index = bb.index.to_timestamp(); bor[c] = bb
for lab, dd in (("repo S1 (bps/12 per cohort)", rep), ("S1 with H/365 charge", fix)):
    comp = pd.DataFrame(dd).mean(axis=1); comp.index = comp.index.to_timestamp(); a, b = split(comp)
    print(f"paper basis {lab}: HAC Sharpe IS {repo_hac_sharpe(a):.3f} OOS {repo_hac_sharpe(b):.3f}")
M = pd.read_csv("s06_monthly_cusip.csv", parse_dates=["month"])
piv = M.pivot(index="month", columns="cell", values="ls")[PRIMARY]; c20 = M.pivot(index="month", columns="cell", values="cost20")[PRIMARY]
for per, lo, hi in (("IS", "1999", "2016-12-31"), ("OOS", "2017", "2024-12-31")):
    net = []
    for c in PRIMARY:
        bmean = bor[c].loc[lo:hi].mean(); net.append((piv[c] - c20[c] - bmean/12/1e4).loc[lo:hi])
        print(f"   {c} {per}: mean Q5 borrow {bmean:.0f} bps/yr -> {bmean/12:.0f} bp/month on the short leg")
    comp = pd.concat(net, axis=1).mean(axis=1).dropna()
    print(f"calendar-time simple composite net of 20bp/round-trip + S1 borrow, {per}: ann ret {comp.mean()*1200:.1f}%  Sharpe {comp.mean()/comp.std()*np.sqrt(12):.2f}  t {comp.mean()/nw_se(comp.values,3):.2f}")
