"""s07: reproduce the headline composite Sharpe (1.06/0.87 gross, 1.01/0.82 net, S0 1.02/0.84, S1 0.80/0.68,
Table 7 annual returns) from the rebuilt panel, then decompose the gap to the calendar-time figure.

Steps
  R1  V0 cohort series, repo composite & repo HAC-Sharpe formula  (should hit 1.06/0.87, 1.01/0.82)
  R2  same series: naive mean/sd*sqrt(12) (repo tradability convention) and Table-7-style ann return = mu*12
  R3  same series, per-cell 'correct' non-overlapping Sharpe: mean/sd of the K-month cohort return * sqrt(12/K)
      and a strictly non-overlapping subsample (every K-th cohort month, all K offsets averaged)
  R4  V1 (simple buy-and-hold returns) cohort series with the repo HAC formula
  R5  NW lag sensitivity for the repo HAC formula (lag 12 vs 24 vs HH lag K-1)
  R6  S1 borrow overlay recomputed (repo rules) on V0 -> 0.7956 / 0.683 check
Input: panel_ret.parquet. Output: stdout log.
"""
from pathlib import Path

import numpy as np
import pandas as pd

from common import build_cells, monthly_spread, nw_se, hh_se, repo_hac_sharpe, split, PRIMARY, IS_END, OOS_START, OOS_END

from v2paths import RDQ_DIR
HERE = RDQ_DIR
P = pd.read_parquet(HERE / "panel_ret.parquet")
for H in (120, 180):
    P[f"scar_{H}"] = np.expm1(P[f"car_{H}"])
df = build_cells(P)
spec = {"A120-LH": (120, "L", "H"), "A120-SH": (120, "S", "H"), "A180-LH": (180, "L", "H"), "A180-SL": (180, "S", "L")}


def cells(colfmt):
    out = {}
    for c, (H, sz, it) in spec.items():
        s = monthly_spread(df, colfmt.format(H=H), sz, it)
        out[c] = s[s.index <= pd.Timestamp("2025-12-31")]
    return pd.DataFrame(out)


def naive(s):
    s = s.dropna()
    return s.mean() / s.std(ddof=1) * np.sqrt(12)


C0 = cells("car_{H}")
# repo fig2: composite over months in tradability csv (<= OOS_END), intersected with FF months (FF ends?)
comp0 = C0[C0.index <= OOS_END].mean(axis=1, skipna=True).dropna()
print("R1 repo-formula composite Sharpe (V0, log cohort returns):")
for lab, s in (("gross", comp0), ("net20", comp0 - 0.002)):
    a, b = split(s)
    print(f"   {lab}: IS {repo_hac_sharpe(a):.3f}  OOS {repo_hac_sharpe(b):.3f}   (paper fig2: gross 1.06/0.87, net 1.01/0.82)")
a, b = split(comp0 - 0.002)
print(f"R2 naive mean/sd*sqrt12 net20: IS {naive(a):.3f} OOS {naive(b):.3f};  'ann return' mu*12: IS {a.mean()*1200:.1f}% OOS {b.mean()*1200:.1f}% (Table 7 S0: 45.5/42.6)")
print("   ratio naive/HAC (paper claims ~1.6x):", round(naive(a) / repo_hac_sharpe(a), 2), round(naive(b) / repo_hac_sharpe(b), 2))

print("R3 per-cell Sharpe on V0 log cohort series:")
for c, (H, sz, it) in spec.items():
    K = H / 30.44
    Kint = int(round(K))
    for per, s in zip(("IS", "OOS"), split(C0[c].dropna())):
        s = s - 0.002
        sh_hac = repo_hac_sharpe(s)
        sh_kmonth = s.mean() / s.std(ddof=1) * np.sqrt(12 / K)
        # strict non-overlap: every Kint-th month, average over offsets
        subs = [s.iloc[o::Kint] for o in range(Kint)]
        sh_sub = np.mean([x.mean() / x.std(ddof=1) * np.sqrt(12 / Kint) for x in subs if len(x) > 5])
        ann_ret_correct = s.mean() * 12 / K
        print(f"   {c} {per}: repoHAC {sh_hac:.2f} | mu/sd*sqrt(12/K) {sh_kmonth:.2f} | non-overlap subsample {sh_sub:.2f}"
              f" | ann.ret repo(mu*12) {s.mean()*1200:.1f}% vs mu*12/K {ann_ret_correct*100:.1f}%")

C1 = cells("scar_{H}")
comp1 = C1[C1.index <= OOS_END].mean(axis=1, skipna=True).dropna()
print("R4 repo-formula composite Sharpe on V1 (simple buy-and-hold) cohort series:")
for lab, s in (("gross", comp1), ("net20", comp1 - 0.002)):
    a, b = split(s)
    print(f"   {lab}: IS {repo_hac_sharpe(a):.3f}  OOS {repo_hac_sharpe(b):.3f};  mu*12: IS {a.mean()*1200:.1f}% OOS {b.mean()*1200:.1f}%")

print("R5 lag sensitivity of the repo HAC Sharpe (V0 net20 composite):")
for lag in (12, 24, 36):
    a, b = split(comp0 - 0.002)
    print(f"   NW lag {lag}: IS {repo_hac_sharpe(a, lag):.3f} OOS {repo_hac_sharpe(b, lag):.3f}")
for c, (H, sz, it) in spec.items():
    K = int(round(H / 30.44))
    a, b = split(C0[c].dropna())
    print(f"   {c} t: NW12 IS {a.mean()/nw_se(a.values,12):.2f} OOS {b.mean()/nw_se(b.values,12):.2f} | "
          f"HH(K-1={K-1}) IS {a.mean()/hh_se(a.values,K-1):.2f} OOS {b.mean()/hh_se(b.values,K-1):.2f} | "
          f"HH(2K) IS {a.mean()/hh_se(a.values,2*K):.2f} OOS {b.mean()/hh_se(b.values,2*K):.2f}")

# R6 S1 borrow overlay on V0 (repo rules: Compustat mcap tiers, flat 20bp, borrow bps/yr /12 per cohort)
sched = [(10_000, np.inf, 25), (2_000, 10_000, 50), (300, 2_000, 200), (100, 300, 800), (0, 100, 2000)]
def bps(m):
    if pd.isna(m):
        return 2000.0
    for lo, hi, b in sched:
        if lo <= m < hi:
            return float(b)
    return 2000.0
df["borrow"] = df["mcap_mil"].apply(bps)
S1 = {}
S0 = {}
for c, (H, sz, it) in spec.items():
    sub = df[(df.size_bin == sz) & (df.ind_bin == it)].dropna(subset=[f"car_{H}", "q5", "mcap_mil"])
    q1 = sub[sub.q5 == 1].groupby("rdq_month")[f"car_{H}"].mean()
    q5 = sub[sub.q5 == 5].groupby("rdq_month")[f"car_{H}"].mean()
    br = sub[sub.q5 == 5].groupby("rdq_month")["borrow"].mean()
    g = (q1 - q5).dropna()
    S0[c] = g - 0.002
    S1[c] = g - 0.002 - br.reindex(g.index).fillna(0) / 12 / 10_000
for lab, dd in (("S0", S0), ("S1", S1)):
    comp = pd.DataFrame(dd).mean(axis=1, skipna=True)
    comp.index = comp.index.to_timestamp()
    a, b = split(comp)
    print(f"R6 {lab}: IS {repo_hac_sharpe(a):.4f} OOS {repo_hac_sharpe(b):.4f}  ann mu*12 IS {a.mean()*1200:.1f}% OOS {b.mean()*1200:.1f}%")
mq5 = df[(df.q5 == 5)].copy()
for c, (H, sz, it) in spec.items():
    sub = mq5[(mq5.size_bin == sz) & (mq5.ind_bin == it)].dropna(subset=[f"car_{H}"])
    print(f"   {c} Q5 short basket (with returns): share mcap<$100M {np.mean(sub.mcap_mil < 100):.2f}, "
          f"<$300M {np.mean(sub.mcap_mil < 300):.2f}, price<$5 {np.mean(sub.prccq < 5):.2f}, price<$1 {np.mean(sub.prccq < 1):.2f}; "
          f"mean borrow bps/yr {sub.borrow.mean():.0f} -> per-cohort charge {sub.borrow.mean()/12:.0f} bp vs holding {H/30.44:.1f} months")
