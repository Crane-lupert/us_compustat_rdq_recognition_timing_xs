"""s04 (R2): expected-announcement-week premium (FROZEN_PARAMS "R2").
A = covered universe stock-days within [E-2, E+2] trading days of an eligible schedule-checked E (variants +-1, +-5);
N = covered stock-days with no E_any within +-10 trading days. Daily EW(A) - EW(N) on FF5+UMD, NW(5).
Writes out/daily_r2.parquet (per-day aggregates), out/r2_events.parquet (A events with window and actual-in-window flags),
out/r2_monthly.parquet, out/r2_expected_dates.parquet, out/results_r2.csv; log on stdout.
"""
import sys
sys.dont_write_bytecode = True
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from p4common import OUT, CACHE, P3, DSF, BIDASK, FC, con, load_ff_daily, load_ff_monthly, load_calendar, nw_alpha, verdict  # noqa: E402
from p4port import alpha_rows  # noqa: E402

t0 = time.time()
c = con(mem="8GB")
cal = load_calendar()
ff = load_ff_daily()
c.register("cal_df", cal[["date", "k"]].assign(date=cal.date.dt.date))
c.execute("CREATE TABLE cal AS SELECT date::DATE date, k::BIGINT k FROM cal_df")
c.execute(f"CREATE TABLE mem AS SELECT y::INT y, permno::BIGINT permno, rk::INT rk FROM '{(P3 / 'out/membership.parquet').as_posix()}' WHERE y <= 2024")
c.execute(f"CREATE TABLE l4 AS SELECT gvkey, permno::BIGINT permno FROM '{(CACHE / 'link4.parquet').as_posix()}'")
c.execute("CREATE TABLE l4u AS SELECT gvkey, permno FROM l4 WHERE permno IN (SELECT permno FROM l4 GROUP BY 1 HAVING count(*) = 1)")
c.execute(f"CREATE TABLE sa AS SELECT permno::BIGINT permno, date::DATE date, gvkey FROM '{(CACHE / 'shared_assign.parquet').as_posix()}'")
c.execute(f"CREATE TABLE ea AS SELECT DISTINCT gvkey, kE::BIGINT kE FROM '{(CACHE / 'slots.parquet').as_posix()}' WHERE sched_ok")
c.execute(f"CREATE TABLE ey AS SELECT DISTINCT gvkey, kE::BIGINT kE FROM '{(CACHE / 'e_any.parquet').as_posix()}'")
c.execute(f"""CREATE TABLE pan AS SELECT gvkey, rdq::DATE rdq, gap_var_t FROM '{(P3 / 'out/panel_ext.parquet').as_posix()}'
              WHERE NOT lookahead AND gap_var_t IS NOT NULL""")

# ---- universe stock-days with return, lagged cap, June rank, calendar index, assigned gvkey
c.execute(f"""CREATE TABLE ud AS
  WITH px AS (SELECT permno::BIGINT permno, date, dlyret r, lag(dlycap) OVER (PARTITION BY permno ORDER BY date) cap_lag
              FROM '{DSF}' WHERE permno IN (SELECT DISTINCT permno FROM mem) AND date >= DATE '1999-06-01' AND date <= DATE '2024-12-31')
  SELECT px.permno, px.date, px.r, px.cap_lag, m.rk FROM px JOIN mem m ON m.permno = px.permno
         AND px.date >= make_date(m.y, 7, 1) AND px.date <= make_date(m.y + 1, 6, 30)
  WHERE px.date >= DATE '2000-01-01' AND px.r IS NOT NULL""")
c.execute("""CREATE TABLE ud2 AS SELECT u.*, cl.k, coalesce(s.gvkey, l.gvkey) gvkey
             FROM ud u JOIN cal cl ON cl.date = u.date
             LEFT JOIN sa s ON s.permno = u.permno AND s.date = u.date
             LEFT JOIN l4u l ON l.permno = u.permno""")
c.execute("DROP TABLE ud")
n_all, n_link = c.execute("SELECT count(*), count(gvkey) FROM ud2").fetchone()
print(f"universe stock-days 2000-2024 with return: {n_all:,}; linked (gvkey assigned): {n_link:,} ({time.time()-t0:.0f}s)", flush=True)
c.execute("DELETE FROM ud2 WHERE gvkey IS NULL")

# ---- nearest expected dates (trading-day distance) via ASOF joins
c.execute("""CREATE TABLE ud3 AS
  SELECT u.*, a1.kE kA_prev, a2.kE kA_next, y1.kE kY_prev, y2.kE kY_next
  FROM ud2 u
  ASOF LEFT JOIN ea a1 ON u.gvkey = a1.gvkey AND u.k >= a1.kE
  ASOF LEFT JOIN ea a2 ON u.gvkey = a2.gvkey AND u.k <= a2.kE
  ASOF LEFT JOIN ey y1 ON u.gvkey = y1.gvkey AND u.k >= y1.kE
  ASOF LEFT JOIN ey y2 ON u.gvkey = y2.gvkey AND u.k <= y2.kE""")
c.execute("DROP TABLE ud2")
c.execute("""CREATE TABLE ud4 AS SELECT permno, date, r, cap_lag, rk, k, gvkey,
    least(coalesce(k - kA_prev, 99999), coalesce(kA_next - k, 99999)) distA,
    least(coalesce(k - kY_prev, 99999), coalesce(kY_next - k, 99999)) distY,
    CASE WHEN coalesce(k - kA_prev, 99999) <= coalesce(kA_next - k, 99999) THEN kA_prev ELSE kA_next END kA_near,
    date_trunc('month', date)::DATE mstart
  FROM ud3""")
c.execute("DROP TABLE ud3")
c.execute("""CREATE TABLE ud5 AS SELECT u.*, (distY <= 63) covered, (distA <= 2) A2, (distA <= 1) A1, (distA <= 5) A5,
             (distY <= 63 AND distY > 10) N FROM ud4 u""")
c.execute("DROP TABLE ud4")
print("flags:", c.execute("SELECT count(*), sum(covered::INT), sum(A2::INT), sum(A1::INT), sum(A5::INT), sum(N::INT) FROM ud5").fetchone(),
      f"({time.time()-t0:.0f}s)", flush=True)
c.execute("DELETE FROM ud5 WHERE NOT covered")

# ---- gap_var_t terciles per month (signal known at the month start)
c.execute("""CREATE TABLE sm AS SELECT permno, mstart, first(gvkey ORDER BY date) gvkey FROM ud5 GROUP BY 1, 2""")
c.execute("""CREATE TABLE sm2 AS SELECT s.permno, s.mstart, p.gap_var_t sig FROM sm s
             ASOF LEFT JOIN pan p ON s.gvkey = p.gvkey AND s.mstart > p.rdq""")
c.execute("""CREATE TABLE terc AS SELECT permno, mstart, ntile(3) OVER (PARTITION BY mstart ORDER BY sig, permno) terc
             FROM sm2 WHERE sig IS NOT NULL""")
print("stock-months with signal:", c.execute("SELECT count(*) FROM terc").fetchone()[0], " of", c.execute("SELECT count(*) FROM sm").fetchone()[0], flush=True)

# ---- quoted-spread costs per run (A2 runs: spec cost; N runs: EXPLORATORY)
c.execute(f"""CREATE TABLE qs AS SELECT permno::BIGINT permno, date, (ask - bid) / ((ask + bid) / 2) qs FROM '{BIDASK}'
              WHERE bid > 0 AND ask >= bid AND (ask - bid) / ((ask + bid) / 2) < 1 AND date >= DATE '1999-12-01' AND date <= DATE '2024-12-31'
              AND permno IN (SELECT DISTINCT permno FROM mem)""")


def run_costs(flag):
    c.execute(f"""CREATE OR REPLACE TABLE rr AS
      WITH a AS (SELECT permno, date, k, lag(k) OVER w pk, lead(k) OVER w nk FROM ud5 WHERE {flag} WINDOW w AS (PARTITION BY permno ORDER BY k)),
           b AS (SELECT *, (pk IS NULL OR k - pk > 1) is_start, (nk IS NULL OR nk - k > 1) is_end FROM a),
           c AS (SELECT *, sum(is_start::INT) OVER (PARTITION BY permno ORDER BY k ROWS UNBOUNDED PRECEDING) run_id FROM b)
      SELECT c.*, ce.date d_entry FROM c LEFT JOIN cal ce ON ce.k = c.k - 1""")
    c.execute(f"""CREATE OR REPLACE TABLE runs AS
      SELECT r.permno, r.run_id, max(CASE WHEN r.is_start THEN r.d_entry END) d_in, max(CASE WHEN r.is_end THEN r.date END) d_out
      FROM rr r GROUP BY 1, 2""")
    c.execute("""CREATE OR REPLACE TABLE runs2 AS
      SELECT u.*, qi.qs qs_in, qo.qs qs_out, year(u.d_in) yr FROM runs u
      LEFT JOIN qs qi ON qi.permno = u.permno AND qi.date = u.d_in LEFT JOIN qs qo ON qo.permno = u.permno AND qo.date = u.d_out""")
    miss = c.execute("SELECT count(*), avg((qs_in IS NULL)::INT), avg((qs_out IS NULL)::INT) FROM runs2").fetchone()
    c.execute("""CREATE OR REPLACE TABLE runs3 AS
      WITH a AS (SELECT *, coalesce(qs_in, qs_out) qi2, coalesce(qs_out, qs_in) qo2 FROM runs2),
           b AS (SELECT *, median(qi2) OVER (PARTITION BY yr) mi_y, median(qo2) OVER (PARTITION BY yr) mo_y,
                           median(qi2) OVER () mi_all, median(qo2) OVER () mo_all FROM a)
      SELECT permno, run_id, coalesce(qi2, mi_y, mi_all) qi, coalesce(qo2, mo_y, mo_all) qo FROM b""")
    c.execute(f"""CREATE OR REPLACE TABLE cost_{flag} AS
      SELECT r.permno, r.date, (CASE WHEN r.is_start THEN q.qi / 2 ELSE 0 END) + (CASE WHEN r.is_end THEN q.qo / 2 ELSE 0 END) cst
      FROM rr r JOIN runs3 q USING (permno, run_id)""")
    mq = c.execute("SELECT avg(qi), avg(qo) FROM runs3").fetchone()
    print(f"cost runs {flag}: runs {miss[0]:,}, qs missing in/out {miss[1]:.4f}/{miss[2]:.4f}, mean qs in/out {mq[0]:.5f}/{mq[1]:.5f}", flush=True)
    return dict(runs=miss[0], qs_missing_in=miss[1], qs_missing_out=miss[2], mean_qs_in=mq[0], mean_qs_out=mq[1])


cinfoA = run_costs("A2")
cinfoN = run_costs("N")
c.execute("""CREATE TABLE ud6 AS SELECT u.*, t.terc, ca.cst cA, cn.cst cN FROM ud5 u
             LEFT JOIN terc t ON t.permno = u.permno AND t.mstart = u.mstart
             LEFT JOIN cost_A2 ca ON ca.permno = u.permno AND ca.date = u.date
             LEFT JOIN cost_N cn ON cn.permno = u.permno AND cn.date = u.date""")
dups = c.execute("SELECT count(*) FROM (SELECT permno, date FROM ud6 GROUP BY 1, 2 HAVING count(*) > 1)").fetchone()[0]
print("duplicate (permno, date) stock-days:", dups, f"({time.time()-t0:.0f}s)", flush=True)


def agg(flag, cond=None):
    f = flag if cond is None else f"{flag} AND {cond}"
    return (f"count(*) FILTER (WHERE {f}) n_{{n}}, sum(r) FILTER (WHERE {f}) s_{{n}}, "
            f"sum(r * cap_lag) FILTER (WHERE {f} AND cap_lag > 0) vn_{{n}}, sum(cap_lag) FILTER (WHERE {f} AND cap_lag > 0) vd_{{n}}, "
            f"count(*) FILTER (WHERE {f} AND cap_lag > 0) nv_{{n}}")


parts = []
for name, flag, cond in [("A2", "A2", None), ("A1", "A1", None), ("A5", "A5", None), ("N", "N", None),
                         ("A2_b1", "A2", "rk <= 500"), ("A2_b2", "A2", "rk BETWEEN 501 AND 1000"), ("A2_b3", "A2", "rk > 1000"),
                         ("N_b1", "N", "rk <= 500"), ("N_b2", "N", "rk BETWEEN 501 AND 1000"), ("N_b3", "N", "rk > 1000"),
                         ("A2_t1", "A2", "terc = 1"), ("A2_t2", "A2", "terc = 2"), ("A2_t3", "A2", "terc = 3"),
                         ("N_t1", "N", "terc = 1"), ("N_t2", "N", "terc = 2"), ("N_t3", "N", "terc = 3")]:
    parts.append(agg(flag, cond).format(n=name))
parts.append("sum(cA) FILTER (WHERE A2) cA2, sum(cN) FILTER (WHERE N) cN")
D = c.execute(f"SELECT date, {', '.join(parts)} FROM ud6 GROUP BY date ORDER BY date").df()
D["date"] = pd.to_datetime(D["date"]).astype("datetime64[ns]")
D = D.set_index("date")
D.to_parquet(OUT / "daily_r2.parquet")
print(f"daily aggregates: {len(D):,} days ({time.time()-t0:.0f}s)", flush=True)

# ---- A events and actual-announcement-in-window share
c.execute(f"""CREATE TABLE rd AS SELECT DISTINCT a.gvkey, cl.k k_rdq FROM '{(CACHE / 'ann_valid.parquet').as_posix()}' a
              ASOF JOIN cal cl ON a.rdq::DATE <= cl.date""")
ev_rows = []
for w, flag in ((2, "A2"), (1, "A1"), (5, "A5")):
    c.execute(f"""CREATE OR REPLACE TABLE aev AS SELECT permno, gvkey, kA_near kE, min(date) first_day, max(date) last_day, count(*) n_days
                  FROM ud6 WHERE {flag} GROUP BY 1, 2, 3""")
    c.execute(f"""CREATE OR REPLACE TABLE aev2 AS SELECT e.*, r.k_rdq k_first_after FROM (SELECT *, kE - {w} kmin FROM aev) e
                  ASOF LEFT JOIN rd r ON e.gvkey = r.gvkey AND e.kmin <= r.k_rdq""")
    st = c.execute(f"SELECT count(*), avg((k_first_after IS NOT NULL AND k_first_after <= kE + {w})::INT) FROM aev2").fetchone()
    ev_rows.append(dict(window=w, n_events=st[0], share_actual_in_window=st[1]))
    if w == 2:
        A = c.execute(f"""SELECT a.permno, a.gvkey, ce.date E, cs.date win_start, cx.date win_end, a.first_day, a.last_day, a.n_days,
                          (a.k_first_after IS NOT NULL AND a.k_first_after <= a.kE + {w}) actual_in_window
                          FROM aev2 a JOIN cal ce ON ce.k = a.kE JOIN cal cs ON cs.k = a.kE - {w} JOIN cal cx ON cx.k = a.kE + {w}""").df()
        A.to_parquet(OUT / "r2_events.parquet", index=False)
print("actual announcement in window:", ev_rows, flush=True)
E1 = c.execute("SELECT e.gvkey, cl.date E, 'eligible_sched_ok' kind FROM ea e JOIN cal cl ON cl.k = e.kE").df()
E2 = c.execute("SELECT e.gvkey, cl.date E, 'any' kind FROM ey e JOIN cal cl ON cl.k = e.kE").df()
pd.concat([E1, E2], ignore_index=True).to_parquet(OUT / "r2_expected_dates.parquet", index=False)

# ---- monthly version
c.execute("CREATE TABLE eam AS SELECT DISTINCT e.gvkey, date_trunc('month', cl.date)::DATE m FROM ea e JOIN cal cl ON cl.k = e.kE")
c.execute("CREATE TABLE eym AS SELECT DISTINCT e.gvkey, date_trunc('month', cl.date)::DATE m FROM ey e JOIN cal cl ON cl.k = e.kE")
c.execute(f"""CREATE TABLE smr AS
  WITH px AS (SELECT permno::BIGINT permno, date, dlyret r FROM '{DSF}' WHERE permno IN (SELECT DISTINCT permno FROM mem)
              AND date >= DATE '2000-01-01' AND date <= DATE '2024-12-31' AND dlyret IS NOT NULL),
       u AS (SELECT px.permno, date_trunc('month', px.date)::DATE m, px.r, px.date FROM px JOIN mem mm ON mm.permno = px.permno
             AND px.date >= make_date(mm.y, 7, 1) AND px.date <= make_date(mm.y + 1, 6, 30)),
       g AS (SELECT u.*, coalesce(s.gvkey, l.gvkey) gvkey FROM u LEFT JOIN sa s ON s.permno = u.permno AND s.date = u.date
             LEFT JOIN l4u l ON l.permno = u.permno)
  SELECT permno, m, first(gvkey ORDER BY date) gvkey, exp(sum(ln(greatest(1 + r, 1e-9)))) - 1 ret_m FROM g WHERE gvkey IS NOT NULL GROUP BY 1, 2""")
c.execute("""CREATE TABLE eymc AS SELECT DISTINCT gvkey, (m + to_months(d::INTEGER))::DATE m FROM eym, range(-2, 3) t(d)""")
c.execute("""CREATE TABLE smr2 AS SELECT s.*, (a.gvkey IS NOT NULL) Am, (b.gvkey IS NOT NULL) Ym, (cc.gvkey IS NOT NULL) covm
  FROM smr s LEFT JOIN eam a ON a.gvkey = s.gvkey AND a.m = s.m LEFT JOIN eym b ON b.gvkey = s.gvkey AND b.m = s.m
  LEFT JOIN eymc cc ON cc.gvkey = s.gvkey AND cc.m = s.m""")
M = c.execute("""SELECT m, count(*) FILTER (WHERE covm AND Am) nA, avg(ret_m) FILTER (WHERE covm AND Am) rA,
                 count(*) FILTER (WHERE covm AND NOT Ym) nN, avg(ret_m) FILTER (WHERE covm AND NOT Ym) rN
                 FROM smr2 GROUP BY 1 ORDER BY 1""").df()
M["m"] = pd.to_datetime(M["m"]).astype("datetime64[ns]")
M.to_parquet(OUT / "r2_monthly.parquet", index=False)
print(f"monthly: {len(M)} months, mean nA {M.nA.mean():.0f}, mean nN {M.nN.mean():.0f} ({time.time()-t0:.0f}s)", flush=True)

# ---------------------------------------------------------------- statistics
rows = []
h1 = pd.Series(D.index, index=D.index).shift(1) <= pd.Timestamp("2012-12-31")
h1.iloc[0] = True
SAMPLES = {"full": np.ones(len(D), bool), "h1_2000_2012": h1.values, "h2_2013_2024": ~h1.values}


def ew(x):
    return D[f"s_{x}"] / D[f"n_{x}"]


def vw(x):
    return D[f"vn_{x}"] / D[f"vd_{x}"]


specs = {
    "R2_main": (ew("A2") - ew("N"), D.n_A2),
    "R2_main__value_weighted": (vw("A2") - vw("N"), D.nv_A2),
    "R2_main__window_E-1_E+1": (ew("A1") - ew("N"), D.n_A1),
    "R2_main__window_E-5_E+5": (ew("A5") - ew("N"), D.n_A5),
    "R2_main__size_rank_1_500": (ew("A2_b1") - ew("N_b1"), D.n_A2_b1),
    "R2_main__size_rank_501_1000": (ew("A2_b2") - ew("N_b2"), D.n_A2_b2),
    "R2_main__size_rank_1001_3000": (ew("A2_b3") - ew("N_b3"), D.n_A2_b3),
    "R2_main__gap_var_tercile_low_regular": (ew("A2_t1") - ew("N_t1"), D.n_A2_t1),
    "R2_main__gap_var_tercile_mid": (ew("A2_t2") - ew("N_t2"), D.n_A2_t2),
    "R2_main__gap_var_tercile_high_irregular": (ew("A2_t3") - ew("N_t3"), D.n_A2_t3),
    "R2_main__net_of_A_spread_costs": ((D.s_A2 - D.cA2) / D.n_A2 - ew("N"), D.n_A2),
    "R2_main__net_incl_N_leg_cost_EXPLORATORY": ((D.s_A2 - D.cA2) / D.n_A2 - (D.s_N + D.cN) / D.n_N, D.n_A2),
    "R2_main__A_leg_excess": (ew("A2"), D.n_A2),
    "R2_main__N_leg_excess": (ew("N"), D.n_A2),
}
for tid, (s, n) in specs.items():
    for sname, m in SAMPLES.items():
        excess = tid.endswith("_excess")
        rows += alpha_rows(tid, sname, s[m], ff, excess=excess, n=n[m])
for k2, v in {**{f"A_cost_{k}": v for k, v in cinfoA.items()}, **{f"N_cost_{k}": v for k, v in cinfoN.items()}}.items():
    rows.append(dict(test_id="R2_main__counts", sample="full", stat=k2, value=v))
for e in ev_rows:
    rows += [dict(test_id=f"R2_window_{e['window']}", sample="full", stat="n_A_events", value=e["n_events"]),
             dict(test_id=f"R2_window_{e['window']}", sample="full", stat="share_actual_announcement_in_window", value=e["share_actual_in_window"])]
rows += [dict(test_id="R2_main__counts", sample="full", stat=k, value=v) for k, v in
         dict(mean_A_stocks_per_day=float(D.n_A2.mean()), mean_N_stocks_per_day=float(D.n_N.mean()),
              days_A_ge_10=int((D.n_A2 >= 10).sum()), days_total=len(D),
              mean_cost_A_bp_per_A_stock_day=float((D.cA2.sum() / D.n_A2.sum()) * 1e4)).items()]

# monthly
fm = load_ff_monthly()
fm = fm.assign(m=pd.to_datetime(fm["date"]).astype("datetime64[ns]"))
for col in FC + ["rf"]:
    fm[col] = pd.to_numeric(fm[col])
Mm = M.merge(fm[["m"] + FC], on="m", how="left").set_index("m")
Mm["diff"] = Mm.rA - Mm.rN
for sname, mm in (("full", np.ones(len(Mm), bool)), ("h1_2000_2012", (Mm.index <= "2012-12-01")), ("h2_2013_2024", (Mm.index >= "2013-01-01"))):
    X = Mm[mm & (Mm.nA >= 10)]
    T = len(X)
    L = int(np.floor(4 * (T / 100.0) ** (2.0 / 9.0)))
    r = nw_alpha(X["diff"].values, X[FC].values, lags=L)
    rows += [dict(test_id="R2_monthly", sample=sname, stat=k, value=v) for k, v in
             dict(alpha_pct_month=r["alpha"] * 100, t=r["t"], n_months=r["n"], nw_lag=L, mean_pct_month=r["mean"] * 100, t_mean=r["t_mean"],
                  mean_nA=float(X.nA.mean()), mean_nN=float(X.nN.mean())).items()]

R = pd.DataFrame(rows)
R.to_csv(OUT / "results_r2.csv", index=False)
pd.set_option("display.width", 250)
key = R[R.stat.isin(["alpha_bp", "t", "n_days", "mean_n_stocks_days_used"])].pivot_table(index=["test_id", "sample"], columns="stat",
                                                                                          values="value", aggfunc="first")
print("\n" + key[["alpha_bp", "t", "n_days", "mean_n_stocks_days_used"]].round(3).to_string())
print("\n" + R[R.test_id.isin(["R2_monthly", "R2_main__counts", "R2_window_1", "R2_window_2", "R2_window_5"])].to_string(index=False))
m = R[(R.test_id == "R2_main") & (R.stat == "alpha_bp")].set_index("sample").value
tt = R[(R.test_id == "R2_main") & (R.stat == "t") & (R["sample"] == "full")].value.iloc[0]
print("\nR2 verdict (expected sign +):", verdict(tt, 1, m["h1_2000_2012"], m["h2_2013_2024"]), f"(total {time.time()-t0:.0f}s)")
