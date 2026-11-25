"""p06: cohort-level (published-statistic) tests.
B2: main universe + PIT link, simple buy-and-hold return over the repo window (from p04 ct_bh_main.parquet),
    per (cell, rdq month) mean(Q1) - mean(Q5), NW(12) t, periods by cohort month.
B3: published construction as-is (log CAR, repo current-CUSIP link, full Compustat sorting universe) from the
    phase-1 panel_ret.parquet (car_* equal to the repo's to 4.6e-7), NW(12).
Writes out/cohort_stats.csv; prints tables.
"""
import sys
sys.dont_write_bytecode = True
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats as st

sys.path.insert(0, str(Path(__file__).resolve().parent))
from p3common import OUT, PARENT, PRIMARY, assign_cells, nw_se, bonf_crit  # noqa: E402

PER = {"IS": ("2000-02-01", "2016-12-01"), "LATE": ("2017-01-01", "2024-12-01")}
rows = []


def cohort_tests(df, ret_tpl, variant, horizons=(60, 120, 180)):
    for H in horizons:
        col = ret_tpl.format(H=H)
        for sz in "LS":
            for it in "HL":
                sub = df[(df.size_bin == sz) & (df.ind_bin == it) & df.q5.isin([1, 5])].dropna(subset=[col])
                m = sub.groupby(["rdq_month", "q5"], observed=True)[col].mean().unstack("q5")
                if 1 not in m or 5 not in m:
                    continue
                s = (m[1] - m[5]).dropna().sort_index()
                s.index = s.index.to_timestamp()
                for per, (a, b) in PER.items():
                    ss = s.loc[a:b]
                    n = len(ss)
                    mu = float(ss.mean())
                    t = mu / nw_se(ss.values, 12)
                    rows.append(dict(variant=variant, cell=f"A{H}-{sz}{it}", period=per, n_months=n, mu=mu, t_nw12=t,
                                     p_two=float(2 * st.t.sf(abs(t), n - 1)), crit_bonf2=bonf_crit(n - 1),
                                     pass_bonf2=bool(mu > 0 and t > bonf_crit(n - 1)), pass_278=bool(mu > 0 and t > 2.78),
                                     sign_ok=bool(mu > 0)))


# ---- B2 ----
cm = pd.read_parquet(OUT / "cells_main.parquet")
bh = pd.read_parquet(OUT / "ct_bh_main.parquet")
w = bh.pivot_table(index="rid", columns="H", values="bh", aggfunc="first")
w.columns = [f"bh_{c}" for c in w.columns]
cm = cm.merge(w, left_on="rid", right_index=True, how="left")
cm.loc[~cm.valid_entry, ["bh_60", "bh_120", "bh_180"]] = np.nan
cohort_tests(cm, "bh_{H}", "B2_simple_cohort_main")

# ---- B3 ----
pr = pd.read_parquet(PARENT / "panel_ret.parquet")
b3 = assign_cells(pr, "gap_var_t")
cohort_tests(b3, "car_{H}", "B3_published_log_cusip_full")

R = pd.DataFrame(rows)
R.to_csv(OUT / "cohort_stats.csv", index=False)
pd.set_option("display.width", 220)
for v in R.variant.unique():
    t = R[R.variant == v]
    print(f"\n===== {v}: cohort spread mean (%), NW12 t =====")
    piv = t.pivot_table(index="cell", columns="period", values=["mu", "t_nw12"], aggfunc="first")
    piv[("mu", "IS")] *= 100; piv[("mu", "LATE")] *= 100
    print(piv.round(2).to_string())
    for per in PER:
        tt = t[t.period == per]
        print(f"   {per}: Bonferroni-12 exact passes {int(tt.pass_bonf2.sum())}/12 (crit ~{tt.crit_bonf2.mean():.3f}); |t|>2.78 {int(tt.pass_278.sum())}; "
              f"sign-correct {int(tt.sign_ok.sum())}/12; primary t: " +
              ", ".join(f"{c} {tt.set_index('cell').t_nw12.get(c, np.nan):.2f}" for c in PRIMARY))
