"""s07: collect out/results_r{1,2,3}.csv into out/results.csv (test_id, sample, stat, value) and the verdict table
out/summary_primary.csv (PHASE4_PROTOCOL §3 grades with |t| >= 2.39 and same-sign halves 2000-2012 / 2013-2024)."""
import sys
sys.dont_write_bytecode = True
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from p4common import OUT, verdict  # noqa: E402

R = pd.concat([pd.read_csv(OUT / f"results_r{i}.csv") for i in (1, 2, 3)], ignore_index=True)
R.to_csv(OUT / "results.csv", index=False)

EXPECTED = {"R1": -1, "R2": 1, "R3": 1}
rows = []
for tid in sorted(R.test_id.unique()):
    sub = R[R.test_id == tid]
    piv = sub.pivot_table(index="sample", columns="stat", values="value", aggfunc="first")
    if "full" not in piv.index:
        continue
    est = "alpha_bp" if "alpha_bp" in piv.columns else ("alpha_pct_month" if "alpha_pct_month" in piv.columns else None)
    if est is None or "t" not in piv.columns:
        continue
    sgn = EXPECTED[tid[:2]]
    if "short" in tid:          # short-side P&L series: profitable short = positive
        sgn = 1
    if tid.endswith("_excess"):
        sgn = np.nan
    g = lambda s, c: float(piv.loc[s, c]) if (s in piv.index and c in piv.columns) else np.nan
    a_full, t_full, a1, t1, a2, t2 = g("full", est), g("full", "t"), g("h1_2000_2012", est), g("h1_2000_2012", "t"), g("h2_2013_2024", est), g("h2_2013_2024", "t")
    n_obs = g("full", "n_days") if "n_days" in piv.columns else g("full", "n_months")
    v = verdict(t_full, sgn, a1, a2) if np.isfinite(sgn) else "(leg, no expected sign)"
    rows.append(dict(test_id=tid, primary=tid in ("R1_main", "R2_main", "R3_main"), unit=("bp/day" if est == "alpha_bp" else "%/month"),
                     expected_sign=sgn, n_events=g("full", "n_events"), n_obs=n_obs, alpha_full=a_full, t_full=t_full,
                     alpha_h1=a1, t_h1=t1, alpha_h2=a2, t_h2=t2, grade=v if tid in ("R1_main", "R2_main", "R3_main") else f"(참고 등급, 판정 아님) {v}"))
S = pd.DataFrame(rows).sort_values(["primary", "test_id"], ascending=[False, True])
S.to_csv(OUT / "summary_primary.csv", index=False)
pd.set_option("display.width", 260); pd.set_option("display.max_colwidth", 60)
print(S.round(3).to_string(index=False))
