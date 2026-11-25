"""R1 with SEC verification, net of costs (the figures quoted in Section 7 of the v2 paper).

Verified-silent events (r1_cache/r1_events_sec_verified.parquet, grp == 'verified silent'; written by
r1_sec_validation.py) are matched to the phase-4 event table on (permno, entry date). The matched positions go through
the phase-4 portfolio and cost machinery unchanged (p4port: half the quoted spread at entry and at exit, borrowing fee
from the size schedule; both frozen in phase 4).
Statistic: daily equal-weighted short return net of costs on days with at least 10 names, FF5+UMD intercept, NW(5).

Written 2026-11-25 to put on file figures that were first computed interactively on 2026-11-21. No outcome data are
used that the phase-4 and verification runs had not already used. Run: python r1_verified_net_of_costs.py
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from v2paths import MC_DIR
HERE = MC_DIR
P4CODE = Path(__file__).resolve().parents[1] / "phase4"
sys.path.insert(0, str(P4CODE))
from p4common import OUT, con, ff_regress, load_ff_daily  # noqa: E402
from p4port import attach_costs, daily, pos_days  # noqa: E402

V = pd.read_parquet(HERE / "r1_cache" / "r1_events_sec_verified.parquet")
V = V[V.grp == "verified silent"][["permno", "t_e"]].rename(columns={"t_e": "entry"}).drop_duplicates()
V["permno"] = V.permno.astype("int64")
V["entry"] = pd.to_datetime(V["entry"]).astype("datetime64[ns]")
ev = pd.read_parquet(OUT / "r1_events_o5.parquet")
for col in ("entry", "exit"):
    ev[col] = pd.to_datetime(ev[col]).astype("datetime64[ns]")
ev["permno"] = ev.permno.astype("int64")
ev["pid"] = ev["eid"]
m = ev.merge(V, on=["permno", "entry"], how="inner").sort_values("pid", kind="mergesort").reset_index(drop=True)
print(f"verified-silent events {len(V)}; matched to the phase-4 event table {len(m)}")

c = con()
ff = load_ff_daily()
RF = ff.set_index("date")["rf"]
pdays = pos_days(c, m[["pid", "permno", "entry", "exit"]])
pdays, ecost, info = attach_costs(c, m[["pid", "permno", "entry", "cap_entry"]], pdays, short_mask=lambda e: np.ones(len(e), dtype=bool))
pdays = pdays.merge(m[["pid", "entry", "rk"]].rename(columns={"entry": "entry_d"}), on="pid", how="left")
print("cost inputs: " + ", ".join(f"{k} {v:.4f}" for k, v in info.items()))
print("[R1, verified silent] daily equal-weighted short portfolio, FF5+UMD intercept, days with >= 10 names")


def run(label, mask):
    P = daily(pdays, mask, cols=("r", "cost"))
    P["rf"] = RF.reindex(P.index).values
    used = P.n >= 10
    gross = (-(P.r - P.rf))[used].dropna()
    net = (-(P.r - P.rf) - P.cost)[used].dropna()
    g = ff_regress(gross, ff, excess=False, lags=5)
    a = ff_regress(net, ff, excess=False, lags=5)
    n_ev = pdays.pid.nunique() if mask is None else pdays[mask].pid.nunique()
    print(f"   {label:<30} events {n_ev:5d} days {int(a['n']):5d} avg names {P.n[used].mean():5.1f} | gross {g['alpha'] * 1e4:+6.2f}bp (t {g['t']:+.2f})"
          f" | net of costs {a['alpha'] * 1e4:+6.2f}bp (t {a['t']:+.2f}) | mean cost {P.cost[used].mean() * 1e4:.2f}bp/day")


yr = pdays.entry_d.dt.year
run("2005-2024", None)
run("entries 2005-2014", (yr <= 2014).values)
run("entries 2015-2024", (yr >= 2015).values)
run("size rank 1001-3000", (pdays.rk > 1000).values)
run("size rank 1-1000", (pdays.rk <= 1000).values)
