"""QA: independent pandas recomputation of (1) per-position buy-and-hold returns for 300 random main-universe
positions (H=120) and (2) one leg-month of the calendar-time engine (cell SH, short leg, H=120, 2008-10 and 2019-03),
compared with p04 outputs. Seeded. Prints max differences.
"""
import sys
sys.dont_write_bytecode = True
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from p3common import OUT, DSF  # noqa: E402

cm = pd.read_parquet(OUT / "cells_main.parquet")
bh = pd.read_parquet(OUT / "ct_bh_main.parquet")
con = duckdb.connect()
# (1) BH returns
pos = cm[cm.q5.isin([1, 5]) & cm.valid_entry].sample(300, random_state=7)
con.register("p", pos[["rid", "permno", "d0", "rdq"]].astype({"permno": "int64"}))
r = con.execute(f"""SELECT p.rid, exp(sum(ln(1 + s.dlyret))) - 1 AS bh_chk
                    FROM p JOIN '{DSF}' s ON s.permno = p.permno AND s.date > p.d0 AND s.date <= p.rdq + INTERVAL 120 DAY
                    WHERE s.dlyret IS NOT NULL GROUP BY p.rid""").df()
m = r.merge(bh[bh.H == 120], on="rid")
print("(1) BH check: n", len(m), " max |diff|", float((m.bh - m.bh_chk).abs().max()))

# (2) one leg-month
M = pd.read_csv(OUT / "ct_monthly.csv.gz", parse_dates=["month"])
for month in ("2008-10-01", "2019-03-01"):
    mo = pd.Timestamp(month)
    me = mo + pd.offsets.MonthEnd(0)
    leg = cm[(cm.q5 == 5) & cm.valid_entry & (cm.size_bin == "S") & (cm.ind_bin == "H")].copy()
    leg["wend"] = leg["rdq"] + pd.Timedelta(days=120)
    leg = leg[(leg.d0 < me) & (leg.wend >= mo)]
    leg["cohort"] = leg["rdq"].dt.to_period("M")
    con.register("q", leg[["rid", "permno", "d0", "wend"]].astype({"permno": "int64"}))
    d = con.execute(f"""SELECT q.rid, s.date, s.dlyret r FROM q JOIN '{DSF}' s ON s.permno = q.permno
                        AND s.date > q.d0 AND s.date <= q.wend WHERE s.dlyret IS NOT NULL ORDER BY q.rid, s.date""").df()
    d = d.merge(leg[["rid", "cohort"]], on="rid")
    d["g"] = d.groupby("rid")["r"].transform(lambda x: np.concatenate([[1.0], np.cumprod(1 + x.values)[:-1]]))
    d = d[(d.date >= mo) & (d.date <= me)]
    coh = d.groupby(["date", "cohort"]).apply(lambda x: (x.g * x.r).sum() / x.g.sum(), include_groups=False).rename("rc").reset_index()
    legd = coh.groupby("date").rc.mean()
    R_chk = float(np.prod(1 + legd.values) - 1)
    R_eng = float(M[(M.universe == "main") & (M.H == 120) & (M.start == "nd") & (M.label == "c12") & (M.cell == "SH") &
                    (M.leg == -1) & (M.month == mo)].R.iloc[0])
    print(f"(2) leg-month {month} SH short H=120: engine {R_eng:.6f} vs pandas {R_chk:.6f} (diff {R_eng - R_chk:.2e}); active positions {leg.shape[0]}")
