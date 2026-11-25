"""p04: calendar-time portfolios (FROZEN_PARAMS calendar_time / costs / entry_exit).

For each config (universe, H, start) and cell labelling, computes per (cell, leg, month):
  R        leg monthly simple return (cohort-EW, buy-and-hold within cohort, compounded daily)
  borrow   daily-accrued borrow fee of the leg (used for the short leg only)
  c_qs     quoted-spread trading cost (half spread at entry + half spread at exit, by trade weight)
  c_20     auxiliary 20 bp per round trip (10 + 10 bp) by trade weight
Also writes per-position buy-and-hold simple returns (for B2) for the main universe, next-day start.
Outputs: phase3/out/ct_monthly.csv.gz, phase3/out/ct_bh_main.parquet, log on stdout.
"""
import sys
sys.dont_write_bytecode = True
import time
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from p3common import OUT, P3, DSF, BIDASK  # noqa: E402

TMP = P3 / "tmp_duck"
TMP.mkdir(exist_ok=True)
con = duckdb.connect()
con.execute("PRAGMA threads=8")
con.execute("SET memory_limit='10GB'")
con.execute(f"SET temp_directory='{TMP.as_posix()}'")
con.execute("SET preserve_insertion_order=false")

cells = {u: pd.read_parquet(OUT / f"cells_{u}.parquet") for u in ("main", "b1")}
CONFIGS = [  # (universe, H, start, labellings)
    ("main", 60, "nd", ["c12", "c49"]), ("main", 120, "nd", ["c12", "c49"]), ("main", 180, "nd", ["c12", "c49"]),
    ("main", 240, "nd", ["c12"]), ("main", 360, "nd", ["c12"]),
    ("main", 120, "sw", ["c12"]), ("main", 180, "sw", ["c12"]),
    ("b1", 60, "nd", ["c12"]), ("b1", 120, "nd", ["c12"]), ("b1", 180, "nd", ["c12"]),
]
permnos = sorted(set(np.concatenate([c.loc[c.q5.isin([1, 5]), "permno"].unique() for c in cells.values()])))
con.register("plist", pd.DataFrame({"permno": np.array(permnos, dtype="int64")}))
t0 = time.time()
con.execute(f"""CREATE TEMP TABLE cal AS SELECT date, date_diff('day', lag(date) OVER (ORDER BY date), date) AS dcal
                FROM (SELECT DISTINCT date FROM '{DSF}')""")
con.execute(f"""CREATE TEMP TABLE dd AS SELECT s.permno::BIGINT permno, s.date, s.dlyret r, coalesce(c.dcal, 1) dcal
                FROM '{DSF}' s JOIN cal c USING (date) WHERE s.dlyret IS NOT NULL AND s.permno IN (SELECT permno FROM plist)""")
con.execute(f"""CREATE TEMP TABLE qs AS SELECT permno::BIGINT permno, date, (ask-bid)/((ask+bid)/2) qs FROM '{BIDASK}'
                WHERE bid > 0 AND ask >= bid AND (ask-bid)/((ask+bid)/2) < 1 AND permno IN (SELECT permno FROM plist)""")
print(f"daily rows {con.execute('SELECT count(*) FROM dd').fetchone()[0]:,}, qs rows {con.execute('SELECT count(*) FROM qs').fetchone()[0]:,}"
      f" ({time.time()-t0:.0f}s)", flush=True)

monthly, bh_out = [], []
for uni, H, start, labs in CONFIGS:
    t1 = time.time()
    c = cells[uni]
    ok = "valid_entry" if start == "nd" else "valid_entry_sw"
    dcol = "d0" if start == "nd" else "d0_sw"
    p = c[c.q5.isin([1, 5]) & c[ok]].copy()
    pos = pd.DataFrame({
        "pid": np.arange(len(p), dtype="int64"), "permno": p["permno"].astype("int64").values,
        "d0": pd.to_datetime(p[dcol]).values, "wend": (p["rdq"] + pd.Timedelta(days=H)).values,
        "cohort": p["rdq"].dt.to_period("M").dt.to_timestamp().values, "leg": np.where(p["q5"] == 1, 1, -1).astype("int8"),
        "c12": (p["size_bin"] + p["ind_bin"]).values, "c49": (p["size_bin"] + p["ind_bin49"]).values,
        "bps": p["borrow_bps"].astype(float).values})
    con.register("pos_df", pos)
    con.execute("CREATE OR REPLACE TEMP TABLE pos AS SELECT * FROM pos_df")
    con.execute("""CREATE OR REPLACE TEMP TABLE w AS
      WITH x AS (SELECT p.pid, p.leg, p.cohort, p.c12, p.c49, p.bps, d.date, d.r, d.dcal
                 FROM pos p JOIN dd d ON d.permno = p.permno AND d.date > p.d0 AND d.date <= p.wend)
      SELECT *, exp(coalesce(sum(ln(greatest(1+r, 1e-9))) OVER (PARTITION BY pid ORDER BY date
                 ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING), 0)) AS g,
             row_number() OVER (PARTITION BY pid ORDER BY date) rnf,
             row_number() OVER (PARTITION BY pid ORDER BY date DESC) rnl
      FROM x""")
    nw = con.execute("SELECT count(*), count(DISTINCT pid) FROM w").fetchone()
    if uni == "main" and start == "nd":
        bh = con.execute("SELECT pid, g*(1+r) - 1 AS bh, date AS d_exit FROM w WHERE rnl = 1").df()
        bh = bh.merge(pos[["pid"]].assign(rid=p["rid"].values), on="pid")[["rid", "bh", "d_exit"]]
        bh["H"] = H
        bh_out.append(bh)
    for lab in labs:
        con.execute(f"""CREATE OR REPLACE TEMP TABLE coh AS
          SELECT {lab} AS cell, cohort, leg, date, sum(g*r)/sum(g) rc, sum(g) G, sum(g*bps)/sum(g) bc, max(dcal) dcal
          FROM w GROUP BY ALL""")
        con.execute("""CREATE OR REPLACE TEMP TABLE legd AS
          SELECT cell, leg, date, avg(rc) rl, count(*) N, avg(bc) fee, max(dcal) dcal FROM coh GROUP BY ALL""")
        legd = con.execute("SELECT * FROM legd").df()
        tw = con.execute(f"""
          SELECT w.pid, w.rnf, w.rnl, w.date, w.r, w.g / c.G / l.N AS wt, l.rl
          FROM w JOIN coh c ON c.cell = w.{lab} AND c.cohort = w.cohort AND c.leg = w.leg AND c.date = w.date
                 JOIN legd l ON l.cell = w.{lab} AND l.leg = w.leg AND l.date = w.date
          WHERE w.rnf = 1 OR w.rnl = 1""").df()
        ent = tw[tw.rnf == 1][["pid", "wt"]].rename(columns={"wt": "w_in"})
        ex = tw[tw.rnl == 1].copy()
        ex["w_out"] = ex["wt"] * (1 + ex["r"]) / (1 + ex["rl"])
        ex = ex[["pid", "date", "w_out"]].rename(columns={"date": "d_exit"})
        tr = pos.merge(ent, on="pid").merge(ex, on="pid")
        con.register("tr_df", tr[["pid", "permno", "d0", "d_exit"]])
        q = con.execute("""SELECT t.pid, a.qs qs_in, b.qs qs_out FROM tr_df t
                           LEFT JOIN qs a ON a.permno = t.permno AND a.date = t.d0
                           LEFT JOIN qs b ON b.permno = t.permno AND b.date = t.d_exit""").df()
        tr = tr.merge(q, on="pid", how="left")
        tr["cell"] = tr[lab]
        miss_in, miss_out = float(tr.qs_in.isna().mean()), float(tr.qs_out.isna().mean())
        tr["qs_in2"] = tr["qs_in"].fillna(tr["qs_out"])
        tr["qs_out2"] = tr["qs_out"].fillna(tr["qs_in"])
        for col in ("qs_in2", "qs_out2"):
            tr[col] = tr[col].fillna(tr.groupby(["cell", "leg", "cohort"])[col].transform("median"))
            tr[col] = tr[col].fillna(tr.groupby(["cell", "leg"])[col].transform("median"))
        tr["m_in"] = pd.to_datetime(tr["d0"]).values.astype("datetime64[M]")
        tr["m_out"] = pd.to_datetime(tr["d_exit"]).values.astype("datetime64[M]")
        # DEV1 slot weights: 1 / (n positions in the cell-leg-cohort x mean active cohorts in the trade month)
        legd["month"] = pd.to_datetime(legd["date"]).values.astype("datetime64[M]")
        ncm = legd.groupby(["cell", "leg", "month"])["N"].mean()
        tr["n_coh"] = tr.groupby(["cell", "leg", "cohort"])["pid"].transform("size")
        nin = ncm.reindex(pd.MultiIndex.from_arrays([tr.cell, tr.leg, tr.m_in])).values
        nout = ncm.reindex(pd.MultiIndex.from_arrays([tr.cell, tr.leg, tr.m_out])).values
        nmed = float(np.nanmedian(ncm.values))
        tr["ws_in"] = 1.0 / (tr["n_coh"] * np.where(np.isnan(nin), nmed, nin))
        tr["ws_out"] = 1.0 / (tr["n_coh"] * np.where(np.isnan(nout), nmed, nout))
        cin = tr.assign(c_qs=tr.w_in * tr.qs_in2 / 2, c_20=tr.w_in * 0.0010,
                        c_qs_s=tr.ws_in * tr.qs_in2 / 2, c_20_s=tr.ws_in * 0.0010
                        ).groupby(["cell", "leg", "m_in"])[["c_qs", "c_20", "c_qs_s", "c_20_s"]].sum()
        cout = tr.assign(c_qs=tr.w_out * tr.qs_out2 / 2, c_20=tr.w_out * 0.0010,
                         c_qs_s=tr.ws_out * tr.qs_out2 / 2, c_20_s=tr.ws_out * 0.0010
                         ).groupby(["cell", "leg", "m_out"])[["c_qs", "c_20", "c_qs_s", "c_20_s"]].sum()
        cin.index.names = cout.index.names = ["cell", "leg", "month"]
        cost = cin.add(cout, fill_value=0.0)
        nent = tr.groupby(["cell", "leg", "m_in"]).size().rename("n_enter")
        nent.index.names = ["cell", "leg", "month"]
        legd["fee_day"] = legd["fee"] / 1e4 * legd["dcal"] / 365.0
        lm = legd.groupby(["cell", "leg", "month"]).agg(R=("rl", lambda s: float(np.prod(1 + s.values) - 1)),
                                                         borrow=("fee_day", "sum"), ncoh=("N", "mean"), ndays=("rl", "size"))
        lm = lm.join(cost, how="outer").join(nent, how="left").fillna(
            {"R": 0.0, "borrow": 0.0, "c_qs": 0.0, "c_20": 0.0, "c_qs_s": 0.0, "c_20_s": 0.0, "n_enter": 0})
        lm = lm.reset_index()
        lm.insert(0, "label", lab); lm.insert(0, "start", start); lm.insert(0, "H", H); lm.insert(0, "universe", uni)
        monthly.append(lm)
        print(f"[{uni} H={H} {start} {lab}] pos {len(pos):,} with return days {nw[1]:,}; position-days {nw[0]:,}; "
              f"qs missing in/out {miss_in:.3f}/{miss_out:.3f}; mean qs in L/S "
              f"{tr.loc[tr.leg==1,'qs_in2'].mean():.4f}/{tr.loc[tr.leg==-1,'qs_in2'].mean():.4f}; "
              f"mean cohorts/day {legd.N.mean():.2f}; turnover/leg-month frozen {lm.c_20.mean()/0.001:.3f} vs DEV1 slot "
              f"{lm.c_20_s.mean()/0.001:.3f} ({time.time()-t1:.0f}s)", flush=True)
    con.execute("DROP TABLE IF EXISTS w")

M = pd.concat(monthly, ignore_index=True)
M.to_csv(OUT / "ct_monthly.csv.gz", index=False)
pd.concat(bh_out, ignore_index=True).to_parquet(OUT / "ct_bh_main.parquet", index=False)
print(f"wrote ct_monthly.csv.gz ({len(M):,} rows) and ct_bh_main.parquet; total {time.time()-t0:.0f}s")
con.close()
import shutil
shutil.rmtree(TMP, ignore_errors=True)
