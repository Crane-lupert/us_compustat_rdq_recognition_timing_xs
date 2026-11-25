"""s11: (i) universe-only effect on the paper basis (log CAR, repo CUSIP link): Russell-3000 proxy / CRSP common stock;
(ii) calendar-time net composite vol-matched to 3.9% like Figure 1."""
import numpy as np, pandas as pd, duckdb
from common import build_cells, monthly_spread, cell_stat, split, IS_END, PRIMARY
P = pd.read_parquet("panel_ret.parquet")
con = duckdb.connect()
mem = con.execute("""
WITH m AS (SELECT year(date) y, max(date) d FROM 'dsf_v2_slim.parquet' WHERE month(date)=5 GROUP BY 1),
c AS (SELECT m.y, s.permno, s.dlycap FROM 'dsf_v2_slim.parquet' s JOIN m ON s.date=m.d
      WHERE s.sharetype='NS' AND s.securitytype='EQTY' AND s.securitysubtype='COM' AND s.usincflg='Y'
        AND s.issuertype IN ('CORP','ACOR') AND s.primaryexch IN ('N','A','Q') AND s.dlycap>0)
SELECT y, permno FROM (SELECT *, row_number() OVER (PARTITION BY y ORDER BY dlycap DESC) rk FROM c) WHERE rk<=3000""").df()
ms = set(zip(mem.y, mem.permno))
P["mem_y"] = np.where(P.rdq.dt.month >= 7, P.rdq.dt.year, P.rdq.dt.year - 1)
P["r3000"] = [((y, int(p)) in ms) if pd.notna(p) else False for y, p in zip(P.mem_y, P.permno)]
for lab, sub in (("R3000-proxy, log, repo link", P[P.r3000 & P.car_180.notna()]),
                 ("common-stock, log, repo link", P[P.common.fillna(False).astype(bool) & P.car_180.notna()])):
    df = build_cells(sub.copy()); out = []; npass = 0
    for H in (60,120,180):
        for sz in "LS":
            for it in "HL":
                s = monthly_spread(df, f"car_{H}", sz, it); a, b = split(s)
                npass += int(cell_stat(a)[1] > 2.78)
                c = f"A{H}-{sz}{it}"
                if c in ["A120-LH","A120-SH","A180-LH","A180-SL","A60-SL","A180-LL"]:
                    out.append(f"{c} IS {cell_stat(a)[1]:.2f} OOS {cell_stat(b)[1]:.2f}")
    print(lab, f"(n firm-q {len(sub):,}); IS passes {npass}/12:", " | ".join(out))
M = pd.read_csv("s06_monthly_cusip.csv", parse_dates=["month"])
net = M.assign(n=M.ls - M.cost20).pivot(index="month", columns="cell", values="n")[PRIMARY].mean(axis=1)
scale = 0.0388 / (net[net.index <= IS_END].std() * np.sqrt(12)); cum = (net * scale).cumsum() * 100
print(f"calendar-time net20 composite vol-matched to 3.9%: cumulative by 2016-12 {cum[cum.index<=IS_END].iloc[-1]:.1f}%, by 2024-12 {cum.iloc[-1]:.1f}%")
