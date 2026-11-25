"""s08: Strategy B (Chambers-Penman deviation) recomputed with explicit early/late labels.
gap_dev_t = gap - rolling 8Q median; NEGATIVE = earlier than usual (early), POSITIVE = later (late).
Repo quintiles are ascending (Q1 = lowest gap_dev = EARLY, Q5 = LATE). Repo spread = Q5 - Q1 = late - early,
'sign-correct' iff > 0 -- the opposite of the Chambers-Penman prediction (early > late).
Also: announcement-window (CP-style) test, 3-day [rdq-1, rdq+1] trading-day simple return, early - late, permno link.
"""
import numpy as np, pandas as pd, duckdb
from common import quintile_within, nw_se, INDUSTRY_TILT_HIGH, OOS_END
P = pd.read_parquet("panel_ret.parquet")
df = P.dropna(subset=["gap_dev_t", "ff12"]).copy()
df["rdq_month"] = df["rdq"].dt.to_period("M")
df = quintile_within(df, "gap_dev_t", ["rdq_month", "ff12"])
chk = df.groupby("q5")["gap_dev_t"].mean()
print("mean gap_dev_t by repo quintile (Q1 lowest):", chk.round(2).to_dict())
df["mcap_mil"] = df["cshoq"] * df["prccq"]
df = df.sort_values(["rdq_month", "ff12", "mcap_mil"], kind="mergesort").reset_index(drop=True)
med = df.groupby(["rdq_month", "ff12"], sort=False)["mcap_mil"].transform("median")
df["size_bin"] = np.where(df["mcap_mil"] >= med, "L", "S"); df["ind_bin"] = np.where(df["ff12"].isin(INDUSTRY_TILT_HIGH), "H", "L")
rows = []
for H in (60, 120, 180):
    for sz in "LS":
        for it in "HL":
            sub = df[(df.size_bin == sz) & (df.ind_bin == it)].dropna(subset=[f"car_{H}"])
            m = sub[sub.q5.isin([1, 5])].groupby(["rdq_month", "q5"])[f"car_{H}"].mean().unstack().dropna()
            m.index = m.index.to_timestamp(); m = m[m.index <= OOS_END]
            sp = m[1] - m[5]   # early - late (CP-predicted > 0)
            t = sp.mean() / nw_se(sp.values, 12)
            # asymmetric legs: residual vs (month, ff12) mean over all firms with returns
            sub = sub.assign(res=sub[f"car_{H}"] - sub.groupby(["rdq_month", "ff12"])[f"car_{H}"].transform("mean"))
            leg = {}
            for q, lab in ((1, "early"), (5, "late")):
                s = sub[sub.q5 == q].groupby("rdq_month")["res"].mean(); s.index = s.index.to_timestamp(); s = s[s.index <= OOS_END]
                leg[lab] = (s.mean(), s.mean() / nw_se(s.values, 12))
            rows.append(dict(cell=f"B{H}-{sz}{it}", early_minus_late=sp.mean(), t=t, early_res=leg["early"][0], t_early=leg["early"][1],
                             late_res=leg["late"][0], t_late=leg["late"][1]))
R = pd.DataFrame(rows)
print(R.round(4).to_string(index=False))
print("symmetric: CP-sign-correct (early>late):", int((R.early_minus_late > 0).sum()), "/12;  |t|>2.78 with CP sign:", int((R.t > 2.78).sum()))
sc = int((R.early_res > 0).sum() + (R.late_res < 0).sum())
print("asymmetric: CP-sign-correct legs:", sc, "/24;  passes |t|>2.92 with CP sign:", int((R.t_early > 2.92).sum() + (R.t_late < -2.92).sum()))
R.to_csv("s08_strategy_b.csv", index=False)

# CP-style announcement window, permno link
con = duckdb.connect()
pp = df.dropna(subset=["permno"])[["permno", "rdq", "rdq_month", "q5", "size_bin", "ind_bin"]].copy(); pp["rdq_month"] = pp["rdq_month"].dt.to_timestamp()
pp["rid"] = np.arange(len(pp)); pp["permno"] = pp["permno"].astype("int64")
con.register("pp", pp)
ann = con.execute("""
WITH d AS (SELECT permno, date, dlyret, row_number() OVER (PARTITION BY permno ORDER BY date) AS k
           FROM 'dsf_v2_slim.parquet' WHERE dlyret IS NOT NULL AND permno IN (SELECT DISTINCT permno FROM pp)),
a AS (SELECT p.rid, p.permno, e.k AS k0 FROM pp p ASOF JOIN d e ON p.permno = e.permno AND e.date >= p.rdq)
SELECT a.rid, exp(sum(ln(greatest(1+d.dlyret,1e-9)))) - 1 AS r3, count(*) AS nd
FROM a JOIN d ON d.permno = a.permno AND d.k BETWEEN a.k0 - 1 AND a.k0 + 1 GROUP BY a.rid
""").df()
pp = pp.merge(ann, on="rid"); pp = pp[pp.nd == 3]
for per, lo, hi in (("IS", "2000", "2016-12-31"), ("OOS", "2017", "2024-12-31")):
    m = pp[pp.q5.isin([1, 5])].groupby(["rdq_month", "q5"])["r3"].mean().unstack().dropna()
    m = m.loc[lo:hi]
    sp = m[1] - m[5]
    print(f"CP-style 3-day [rdq-1,rdq+1] early-late (all firms, permno link) {per}: mean {sp.mean()*100:.3f}% t(NW3) {sp.mean()/nw_se(sp.values,3):.2f} n={len(sp)}")
