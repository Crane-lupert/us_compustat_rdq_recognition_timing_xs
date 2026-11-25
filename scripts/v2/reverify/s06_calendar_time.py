"""s06: calendar-time (non-overlapping) monthly long-short returns for the 12 cells and the 4-cell composite.

Positions = firm-quarters in Q1 (long) / Q5 (short) of each size x tilt cell (repo quintile/size/tilt rules, s05 V0).
Holding window = (first trading day >= rdq+1, last trading day <= rdq+H]  (exactly the repo CAR window).
Within a cohort (cell, H, rdq_month, leg): buy-and-hold equal-weight at entry (weight = cumulative gross return).
Across cohorts: equal weight over cohorts active that day. Leg monthly return = compounded daily leg return.
LS monthly = long - short. Simple daily returns (CRSP dsf_v2 dlyret, delisting-day returns included in CIZ).

Link variants: 'cusip' = repo replica (names current CUSIP == CRSP historical cusip),
               'permno' = names CUSIP == CRSP header CUSIP -> permno.
Costs: (a) paper convention 20 bp per position round trip (long+short book), charged in calendar time as
       20bp / K per month, K = H/30.44 = holding period in months (1/K of the book turns over each month);
       (b) quoted-spread estimate: mean (ask-bid)/mid at entry of the long names + same for the short names
       entering that month (one full quoted spread = one round trip), charged / K per month. Within-cohort
       dilution trades are ignored (so both cost figures are lower bounds on turnover).
Outputs: s06_monthly_<link>.csv, s06_summary_<link>.csv
"""
import sys
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd

from common import build_cells, nw_se, repo_hac_sharpe, IS_END, OOS_START, OOS_END, PRIMARY

from v2paths import RDQ_DIR
HERE = RDQ_DIR
LINK = sys.argv[1] if len(sys.argv) > 1 else "cusip"
HS = [60, 120, 180]

P = pd.read_parquet(HERE / "panel_ret.parquet")
df = build_cells(P)
df = df[df["q5"].isin([1, 5])].copy()
df["leg"] = np.where(df["q5"] == 1, 1, -1)
df["cohort"] = df["rdq_month"].dt.to_timestamp()
df = df[df["cohort"] <= OOS_END]
if LINK == "cusip":
    df["key"] = df["cusip8"]
else:
    df = df.dropna(subset=["permno"])
    df["key"] = df["permno"].astype("int64").astype(str)
df["cellsz"] = df["size_bin"] + df["ind_bin"]
pos = df[["key", "rdq", "cellsz", "cohort", "leg"]].reset_index(drop=True)
pos["pid"] = np.arange(len(pos))

con = duckdb.connect()
con.execute("PRAGMA threads=8")
con.execute("SET memory_limit='12GB'")
con.register("pos_df", pos)
con.execute("CREATE TEMP TABLE pos AS SELECT * FROM pos_df")
keycol = "cusip8" if LINK == "cusip" else "CAST(permno AS VARCHAR)"
con.execute(f"""CREATE TEMP TABLE d AS SELECT {keycol} AS key, date, dlyret AS r
               FROM '{(HERE/'dsf_v2_slim.parquet').as_posix()}'
               WHERE dlyret IS NOT NULL AND {keycol} IN (SELECT DISTINCT key FROM pos)""")
con.execute(f"""CREATE TEMP TABLE ba AS SELECT CAST(permno AS VARCHAR) AS pk, date, bid, ask
               FROM '{(HERE/'dsf_v2_bidask.parquet').as_posix()}' WHERE bid > 0 AND ask >= bid""")
if LINK == "cusip":
    con.execute(f"CREATE TEMP TABLE kmap AS SELECT DISTINCT cusip8 AS key, CAST(permno AS VARCHAR) AS pk, date FROM '{(HERE/'dsf_v2_slim.parquet').as_posix()}' WHERE cusip8 IN (SELECT DISTINCT key FROM pos)")
# entry day d0 per position (first trading day >= rdq+1 in that key's non-null return series)
con.execute("""CREATE TEMP TABLE pos0 AS
  SELECT p.*, e.date AS d0 FROM pos p ASOF JOIN d e ON p.key = e.key AND e.date >= p.rdq + INTERVAL 1 DAY""")
# quoted spread at d0
if LINK == "cusip":
    con.execute("""CREATE TEMP TABLE sp AS SELECT p.pid, (b.ask-b.bid)/((b.ask+b.bid)/2) AS qs
      FROM pos0 p JOIN kmap k ON k.key = p.key AND k.date = p.d0 JOIN ba b ON b.pk = k.pk AND b.date = p.d0""")
else:
    con.execute("""CREATE TEMP TABLE sp AS SELECT p.pid, (b.ask-b.bid)/((b.ask+b.bid)/2) AS qs
      FROM pos0 p JOIN ba b ON b.pk = p.key AND b.date = p.d0""")

all_month = []
for H in HS:
    q = f"""
    WITH x AS (
      SELECT p.pid, p.cellsz, p.cohort, p.leg, e.date, e.r
      FROM pos0 p JOIN d e ON e.key = p.key AND e.date > p.d0 AND e.date <= p.rdq + INTERVAL {H} DAY),
    w AS (
      SELECT *, exp(coalesce(sum(ln(greatest(1+r, 1e-9))) OVER (PARTITION BY pid ORDER BY date
                 ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING), 0)) AS g
      FROM x),
    coh AS (  -- cohort-leg daily buy-and-hold return
      SELECT cellsz, cohort, leg, date, sum(g*r)/nullif(sum(g),0) AS rc FROM w GROUP BY ALL),
    legd AS (
      SELECT cellsz, leg, date, avg(rc) AS rl, count(*) AS n_active FROM coh GROUP BY ALL)
    SELECT * FROM legd
    """
    legd = con.execute(q).df()
    legd["month"] = legd["date"].values.astype("datetime64[M]")
    lm = legd.groupby(["cellsz", "leg", "month"]).agg(R=("rl", lambda s: np.prod(1 + s.values) - 1),
                                                       n_active=("n_active", "mean")).reset_index()
    # entering cohorts per (cellsz, leg, month) and their quoted spread
    ent = con.execute(f"""
      SELECT p.cellsz, p.leg, date_trunc('month', p.d0) AS month, count(DISTINCT p.cohort) AS n_enter_coh,
             avg(s.qs) AS qs_mean, count(s.qs) AS n_qs, count(*) AS n_pos
      FROM pos0 p LEFT JOIN sp s USING (pid)
      WHERE p.d0 IS NOT NULL GROUP BY ALL""").df()
    ent["month"] = pd.to_datetime(ent["month"]).values.astype("datetime64[M]")
    lm = lm.merge(ent, on=["cellsz", "leg", "month"], how="left").fillna({"n_enter_coh": 0})
    lm["w_enter"] = np.minimum(lm["n_enter_coh"] / lm["n_active"].clip(lower=1), 1.0)
    wide = lm.pivot(index="month", columns=["cellsz", "leg"], values=["R", "w_enter", "qs_mean"])
    for cz in ["LH", "LL", "SH", "SL"]:
        try:
            rl, rs = wide[("R", cz, 1)], wide[("R", cz, -1)]
        except KeyError:
            continue
        ls = (rl - rs).dropna()
        wl = wide[("w_enter", cz, 1)].reindex(ls.index).fillna(0)
        wsh = wide[("w_enter", cz, -1)].reindex(ls.index).fillna(0)
        we = (wl + wsh) / 2
        qsl = wide[("qs_mean", cz, 1)].reindex(ls.index)
        qss = wide[("qs_mean", cz, -1)].reindex(ls.index)
        # calendar-time turnover: each position is held ~H/30.44 months, so 1/K of each leg turns over per month
        K = H / 30.44
        we = pd.Series(1.0 / K, index=ls.index)
        cost20 = 0.0020 / K
        costqs = (qsl.fillna(qsl.mean()) + qss.fillna(qss.mean())) / K
        costqs = pd.Series(costqs, index=ls.index)
        cost20 = pd.Series(cost20, index=ls.index)
        all_month.append(pd.DataFrame({"cell": f"A{H}-{cz}", "month": ls.index, "ls": ls.values,
                                       "long": rl.reindex(ls.index).values, "short": rs.reindex(ls.index).values,
                                       "w_enter": we.values, "cost20": cost20.values, "costqs": costqs.values,
                                       "qs_long": qsl.values, "qs_short": qss.values}))
    print(f"H={H} done", flush=True)

M = pd.concat(all_month, ignore_index=True)
M["month"] = pd.to_datetime(M["month"])
M = M[M["month"] <= OOS_END]
M.to_csv(HERE / f"s06_monthly_{LINK}.csv", index=False)


def stats(s):
    s = s.dropna()
    n = len(s)
    mu, sd = s.mean(), s.std(ddof=1)
    return dict(n=n, mu_m=mu, ann_ret=mu * 12, ann_vol=sd * np.sqrt(12), sharpe=mu / sd * np.sqrt(12),
                t_iid=mu / (sd / np.sqrt(n)), t_nw3=mu / nw_se(s.values, 3),
                repo_hac_sharpe=repo_hac_sharpe(s, 12))


rows = []
piv = {k: M.pivot(index="month", columns="cell", values=k) for k in ["ls", "cost20", "costqs", "w_enter", "qs_long", "qs_short"]}
series = {}
for cell in sorted(M["cell"].unique()):
    series[cell] = {"gross": piv["ls"][cell], "net20": piv["ls"][cell] - piv["cost20"][cell],
                    "netqs": piv["ls"][cell] - piv["costqs"][cell],
                    "netqs50": piv["ls"][cell] - 0.5 * piv["costqs"][cell]}
comp = {k: pd.concat([series[c][k] for c in PRIMARY], axis=1).mean(axis=1, skipna=True) for k in ["gross", "net20", "netqs", "netqs50"]}
series["COMPOSITE4"] = comp
for name, dd in series.items():
    for k, s in dd.items():
        for per, ss in (("IS", s[s.index <= IS_END]), ("OOS", s[(s.index >= OOS_START) & (s.index <= OOS_END)])):
            r = stats(ss)
            r.update(cell=name, cost=k, period=per)
            rows.append(r)
S = pd.DataFrame(rows)
S.to_csv(HERE / f"s06_summary_{LINK}.csv", index=False)
pd.set_option("display.width", 220)
print(S[S.cell.isin(PRIMARY + ["COMPOSITE4"])][["cell", "cost", "period", "n", "ann_ret", "ann_vol", "sharpe", "t_iid", "t_nw3", "repo_hac_sharpe"]].round(3).to_string(index=False))
print("\nAll 12 cells gross t_nw3:")
print(S[(S.cost == "gross")].pivot(index="cell", columns="period", values="t_nw3").round(2).to_string())
w = piv["w_enter"][PRIMARY].mean(axis=1)
print("\nmean entering weight per month (primary cells):", round(float(w.mean()), 3))
print("mean quoted spread at entry, long / short legs (primary cells):",
      round(float(piv["qs_long"][PRIMARY].stack().mean()), 4), round(float(piv["qs_short"][PRIMARY].stack().mean()), 4))
