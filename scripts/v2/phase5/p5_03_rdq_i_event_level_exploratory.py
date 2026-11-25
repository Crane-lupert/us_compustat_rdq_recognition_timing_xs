"""EXPLORATORY (not pre-specified, not used for the verdict): event-level view of RDQ-I.
The pre-specified estimator keeps only days with >= 10 open positions (851 of about 5,500 days). This script averages the
holding-period abnormal return (stock minus equal-weighted universe over the same days) over all events instead,
clustered by entry month, to see whether the null is produced by that day filter.
Run: python p5_03_rdq_i_event_level_exploratory.py
"""
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd
import statsmodels.api as sm

from v2paths import MC_DIR
HERE = MC_DIR / "phase5"
SLIM = (HERE.parent.parent / "RDQ_cadence" / "dsf_v2_slim.parquet").as_posix()
con = duckdb.connect()
Ev = pd.read_parquet(HERE / "rdq_i_events.parquet")
U = pd.read_parquet(HERE / "cache" / "univ_ew_2002.parquet")
U["date"] = pd.to_datetime(U["date"])
U = U.sort_values("date").set_index("date")
clog = np.log1p(U.ew).cumsum()
con.register("ev", Ev[["eid", "permno", "t_e", "exit"]])
R = con.execute(f"""SELECT e.eid, exp(sum(ln(greatest(1 + s.dlyret, 1e-9)))) - 1 AS r, count(*) AS nd
                    FROM ev e JOIN '{SLIM}' s ON s.permno = e.permno AND s.date > e.t_e AND s.date <= e.exit
                    WHERE s.dlyret IS NOT NULL GROUP BY 1""").df()
E = Ev.merge(R, on="eid")
E["bench"] = np.expm1(clog.reindex(pd.to_datetime(E["exit"])).values - clog.reindex(pd.to_datetime(E.t_e)).values)
E = E.dropna(subset=["bench"])
E["ar"] = (E.r - E.bench) * 100
E["ym"] = pd.to_datetime(E.t_e).dt.year * 100 + pd.to_datetime(E.t_e).dt.month


def run(d, label):
    f = sm.OLS(d.ar.values, np.ones(len(d))).fit(cov_type="cluster", cov_kwds={"groups": d.ym.values})
    print(f"   {label:40s} events {len(d):5d} | mean holding-period abnormal return {f.params[0]:+.3f}% (t {f.tvalues[0]:+.2f}), median {d.ar.median():+.3f}%, mean days held {d.nd.mean():.1f}")


print("[EXPLORATORY] RDQ-I, event-level abnormal return over the holding period (stock minus universe EW)")
run(E, "all entries 2003-2024")
run(E[E.year <= 2013], "entries 2003-2013")
run(E[E.year >= 2014], "entries 2014-2024")
run(E[E.rk <= 1000], "size rank 1-1000")
run(E[E.rk > 1000], "size rank 1001-3000")
run(E[E.fqtr == 4], "annual report")
run(E[E.fqtr != 4], "quarterly report")
run(E[E.reason == "NT"], "positions that ended in an NT notice")
run(E[E.reason == "30d"], "positions that ran 30 days")
