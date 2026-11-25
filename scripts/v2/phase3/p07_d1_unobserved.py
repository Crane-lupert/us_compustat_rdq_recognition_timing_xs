"""p07 (D1): cohorts never seen by the repo's Phase 0 (datadate >= 2025-01-01) whose holding window closes inside the
dump (rdq + H <= 2025-12-31, last dsf_v2 date). Counts only; no returns are computed (FROZEN_PARAMS D1).
Writes out/d1_counts.csv.
"""
import sys
sys.dont_write_bytecode = True
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from p3common import OUT, PARENT  # noqa: E402

ev = pd.read_parquet(OUT / "events.parquet")
last = pd.Timestamp("2025-12-31")
p0 = pd.read_parquet(PARENT / "panel_rebuild.parquet", columns=["rdq"])
print("Phase-0 panel rdq range:", p0.rdq.min().date(), "-", p0.rdq.max().date())
u = ev[~ev.in_phase0].copy()
print("extended-panel events with datadate >= 2025-01-01 (signal, NT filter, FF12):", len(u), " rdq range:", u.rdq.min().date(), "-", u.rdq.max().date())
rows = []
for H in (60, 120, 180):
    closed = u[u.rdq + pd.Timedelta(days=H) <= last]
    lv = {"signal": closed,
          "linked_valid_entry": closed[closed.valid_entry],
          "russell_proxy_valid_entry": closed[closed.valid_entry & closed.in_r3000]}
    p0_months = set(p0.rdq.dt.to_period("M").astype(str))
    for k, d in lv.items():
        months = sorted(d.rdq.dt.to_period("M").astype(str).unique())
        full = [m for m in months if m not in p0_months]   # months with no Phase-0 event at all
        rows.append(dict(H=H, level=k, events=len(d), cohort_months=len(months),
                         first_month=months[0] if months else "", last_month=months[-1] if months else "",
                         fully_unobserved_months=len(full), fully_unobserved_events=int(d.rdq.dt.to_period("M").astype(str).isin(full).sum())))
D = pd.DataFrame(rows)
D.to_csv(OUT / "d1_counts.csv", index=False)
print(D.to_string(index=False))
mx = int(D.cohort_months.max())
print("max closed-window unobserved cohort months:", mx, "->", "out-of-sample test NOT possible (< 12 months); counts only"
      if mx < 12 else "run main spec on the unobserved window")
