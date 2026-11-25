"""Phase 5 - RDQ-I: firms whose periodic report (10-Q / 10-K) is overdue relative to their own usual gap after earnings.

Definitions fixed in PHASE5_SPEC.md sections 2 and 4b before any return was computed:
  F      first periodic report filed in [rdq - 5d, rdq + 150d];  G = max(F - rdq, 0) calendar days
  G_exp  G of the same fiscal quarter one year earlier (0..60 days); F_exp = first trading day >= rdq + G_exp
  event  at the close of F_exp + L trading days (L = 5): no periodic report filed since rdq - 5d and no NT filing in
         (rdq - 30d, entry]; firm-quarters with a periodic report already filed in [rdq - 40d, rdq - 5d) are dropped
  exit   close of the trading day after the report (or an NT notice) is filed, or 30 trading days, or delisting
  test   daily equal-weighted calendar-time portfolio (>= 10 names), FF5+UMD intercept, Newey-West(5); expected sign negative
Run: python p5_02_rdq_filing_lag.py
"""
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd
import statsmodels.api as sm

from v2paths import MC_DIR, WRDS_DUMP
HERE = MC_DIR / "phase5"
MC = HERE.parent
ROOT = MC.parent
DUMP = WRDS_DUMP.rstrip("/")
SLIM = (ROOT / "RDQ_cadence" / "dsf_v2_slim.parquet").as_posix()
BIDASK = (ROOT / "RDQ_cadence" / "dsf_v2_bidask.parquet").as_posix()
PERIODIC = {"10-Q", "10-K", "10-K405", "10-KSB", "10-QSB", "10-KT", "10-QT", "10-KSB40"}
FC = ["mktrf", "smb", "hml", "rmw", "cma", "umd"]
con = duckdb.connect()
con.execute("SET memory_limit='7GB'")


def D(n):
    return np.timedelta64(n, "D")


# ---------------- filing dates ----------------
M = pd.concat([pd.read_parquet(p) for p in sorted((HERE / "cache" / "master").glob("*.parquet"))], ignore_index=True)
M["cik10"] = M.cik.astype(str).str.zfill(10)
M["date"] = pd.to_datetime(M.date)
per = M[M.form.isin(PERIODIC)].sort_values(["cik10", "date"])
nt = M[M.form.str.startswith("NT")].sort_values(["cik10", "date"])
print(f"[index] periodic filings {len(per)}, NT filings {len(nt)}, {M.date.min().date()}..{M.date.max().date()}, quarters {M.date.dt.to_period('Q').nunique()}")
per_d = {c: d.date.values.astype("datetime64[ns]") for c, d in per.groupby("cik10")}
nt_d = {c: d.date.values.astype("datetime64[ns]") for c, d in nt.groupby("cik10")}

# ---------------- announcements ----------------
fq = pd.read_parquet(MC / "r1_cache" / "fundq_rdq.parquet")
fq["datadate"] = pd.to_datetime(fq.datadate)
fq["rdq"] = pd.to_datetime(fq.rdq)
cik = fq[fq.cik.notna() & (fq.cik != "")].sort_values("datadate").drop_duplicates("gvkey", keep="last").set_index("gvkey").cik.astype(str).str.zfill(10)
V = fq[fq.rdq.notna() & fq.fyearq.notna() & fq.fqtr.notna()].copy()
V["gap"] = (V.rdq - V.datadate).dt.days
V = V[(V.gap >= 1) & (V.gap <= 120) & (V.rdq >= "2001-06-01")]
V = V.sort_values(["gvkey", "fyearq", "fqtr", "datadate"]).drop_duplicates(["gvkey", "fyearq", "fqtr"], keep="last")
V["cik10"] = V.gvkey.map(cik)
n0 = len(V)
V = V[V.cik10.notna() & V.cik10.isin(per_d.keys())].copy()
print(f"[ann] valid announcement records since 2001-06: {n0}; with a CIK that has periodic reports in the index: {len(V)}")

F, early = [], []
for c, r in zip(V.cik10.values, V.rdq.values.astype("datetime64[ns]")):
    a = per_d[c]
    k = np.searchsorted(a, r - D(5), side="left")
    F.append(a[k] if k < len(a) and a[k] <= r + D(150) else np.datetime64("NaT"))
    early.append(k > np.searchsorted(a, r - D(40), side="left"))
V["F"] = F
V["early"] = early
V["G"] = (V.F - V.rdq).dt.days.clip(lower=0)
prev = V[["gvkey", "fyearq", "fqtr", "G"]].rename(columns={"G": "G_exp"})
prev["fyearq"] = prev.fyearq + 1
V = V.merge(prev, on=["gvkey", "fyearq", "fqtr"], how="left")
S0 = V[V.G_exp.notna() & (V.G_exp >= 0) & (V.G_exp <= 60)].copy()
print(f"[slots] firm-quarters with an expected gap (0-60 days): {len(S0)}; median expected gap {S0.G_exp.median():.0f} days, share with gap 0: {np.mean(S0.G_exp == 0):.3f}; "
      f"actual gap: median {S0.G.median():.0f}, no report found in the window {S0.G.isna().mean():.4f}")

cal = con.execute(f"SELECT DISTINCT date FROM '{SLIM}' ORDER BY 1").df()
dnp = pd.DatetimeIndex(pd.to_datetime(cal["date"])).values
dcal = pd.Series(np.r_[1, np.diff(dnp).astype("timedelta64[D]").astype(int)], index=pd.DatetimeIndex(dnp))
kF0 = np.searchsorted(dnp, (S0.rdq + pd.to_timedelta(S0.G_exp, unit="D")).values.astype("datetime64[ns]"), side="left")

hdr = con.execute(f"SELECT permno, max(hdrcusip8) AS h FROM '{SLIM}' GROUP BY 1").df()
h2p = hdr.groupby("h").permno.apply(list).to_dict()
c8 = fq.dropna(subset=["cusip"]).drop_duplicates("gvkey").set_index("gvkey").cusip.str[:8]
mem = con.execute(f"""
  WITH j AS (SELECT year(date) y, max(date) d FROM '{SLIM}' WHERE month(date) = 6 GROUP BY 1),
       r AS (SELECT j.y, s.permno, row_number() OVER (PARTITION BY j.y ORDER BY s.dlycap DESC) rk
             FROM j JOIN '{SLIM}' s ON s.date = j.d
             WHERE s.sharetype='NS' AND s.securitytype='EQTY' AND s.securitysubtype='COM' AND s.usincflg='Y'
               AND s.issuertype IN ('CORP','ACOR') AND s.primaryexch IN ('N','A','Q') AND s.dlycap > 0)
  SELECT y, permno, rk FROM r WHERE rk <= 3000""").df()
ms = {(int(y), int(p)): int(rk) for y, p, rk in zip(mem.y, mem.permno, mem.rk)}

uf = HERE / "cache" / "univ_ew_2002.parquet"
if not uf.exists():
    con.register("mem_df", mem)
    con.execute(f"""COPY (SELECT s.date, avg(s.dlyret) AS ew, count(*) AS n
      FROM '{SLIM}' s JOIN mem_df m ON m.permno = s.permno AND m.y = CASE WHEN month(s.date) >= 7 THEN year(s.date) ELSE year(s.date) - 1 END
      WHERE s.dlyret IS NOT NULL AND s.date >= DATE '2002-07-01' GROUP BY 1) TO '{uf.as_posix()}' (FORMAT parquet)""")
U = pd.read_parquet(uf)
U["date"] = pd.to_datetime(U["date"])
U = U.set_index("date").ew
ff = con.execute(f"SELECT * FROM read_csv('{DUMP}/ff_all.fivefactors_daily.csv.gz', header=true)").df()
ff["date"] = pd.to_datetime(ff["date"])
ff = ff.set_index("date").astype(float)


def build(L, verbose=True):
    """events and position-day returns for entry at the close of F_exp + L trading days"""
    ok = kF0 + L < len(dnp)
    S = S0[ok].copy()
    k = kF0[ok]
    S["F_exp"] = dnp[k]
    S["t_e"] = dnp[k + L]
    S = S[(S.t_e >= "2003-01-01") & (S.t_e <= "2024-12-31")].copy()
    te = S.t_e.values.astype("datetime64[ns]")
    rd = S.rdq.values.astype("datetime64[ns]")
    filed, ntf, x_rep, x_nt = [], [], [], []
    for c, r, t in zip(S.cik10.values, rd, te):
        a = per_d[c]
        k1 = np.searchsorted(a, t, side="right")
        filed.append(k1 - np.searchsorted(a, r - D(5), side="left") > 0)
        x_rep.append(a[k1] if k1 < len(a) else np.datetime64("NaT"))
        b = nt_d.get(c)
        if b is None:
            ntf.append(False)
            x_nt.append(np.datetime64("NaT"))
        else:
            k2 = np.searchsorted(b, t, side="right")
            ntf.append(k2 - np.searchsorted(b, r - D(30), side="right") > 0)
            x_nt.append(b[k2] if k2 < len(b) else np.datetime64("NaT"))
    S["filed"], S["nt_before"], S["x_rep"], S["x_nt"] = filed, ntf, x_rep, x_nt
    Ev = S[~S.filed & ~S.nt_before & ~S.early].copy()
    if verbose:
        print(f"[overdue L={L}] slots {len(S)}; report still missing at entry {int((~S.filed).sum())} ({np.mean(~S.filed):.3f}); of these: an NT notice already filed {int((~S.filed & S.nt_before).sum())}, "
              f"a periodic report filed in [rdq-40d, rdq-5d) {int((~S.filed & ~S.nt_before & S.early).sum())}; kept {len(Ev)}")
    Ev["permno"] = [(h2p.get(c8.get(g)) or [None])[0] if len(h2p.get(c8.get(g)) or []) == 1 else None for g in Ev.gvkey]
    n_link = int(Ev.permno.notna().sum())
    Ev = Ev[Ev.permno.notna()].copy()
    Ev["permno"] = Ev.permno.astype(int)
    tt = pd.DatetimeIndex(Ev.t_e)
    Ev["rk"] = [ms.get((int(y), int(p))) for y, p in zip(np.where(tt.month >= 7, tt.year, tt.year - 1), Ev.permno)]
    n_univ = int(Ev.rk.notna().sum())
    Ev = Ev[Ev.rk.notna()].copy()
    con.register("e0", Ev[["permno", "t_e"]].drop_duplicates())
    px = con.execute(f"SELECT e.permno, e.t_e, abs(s.dlyprc) prc, s.dlycap cap, s.dlydelflg FROM e0 e JOIN '{SLIM}' s ON s.permno = e.permno AND s.date = e.t_e").df()
    con.unregister("e0")
    px["t_e"] = pd.to_datetime(px.t_e)
    Ev = Ev.merge(px, on=["permno", "t_e"])
    Ev = Ev[(Ev.prc >= 5) & (Ev.dlydelflg.fillna("N") != "Y")].copy()
    k_e = np.searchsorted(dnp, Ev.t_e.values.astype("datetime64[ns]"), side="left")

    def k_after(col):
        v = Ev[col].values.astype("datetime64[ns]")
        return np.where(np.isnat(v), 10 ** 9, np.searchsorted(dnp, v, side="right"))

    k_rep, k_nt = k_after("x_rep"), k_after("x_nt")
    k_x = np.minimum(np.minimum(np.minimum(k_rep, k_nt), k_e + 30), len(dnp) - 1)
    Ev["exit"] = dnp[k_x]
    Ev["reason"] = np.where((k_nt < k_rep) & (k_nt <= k_e + 30), "NT", np.where(k_rep <= k_e + 30, "report", "30d"))
    Ev = Ev.sort_values(["permno", "t_e", "datadate"])
    last_exit, keep = {}, []
    for p, t, x in zip(Ev.permno.values, Ev.t_e.values, Ev["exit"].values):
        good = (p not in last_exit) or (t >= last_exit[p])
        keep.append(good)
        if good:
            last_exit[p] = x
    Ev = Ev[np.array(keep)].copy()
    Ev["eid"] = np.arange(len(Ev))
    Ev["year"] = pd.DatetimeIndex(Ev.t_e).year
    Ev["no_later_report"] = Ev.x_rep.isna() | ((Ev.x_rep - Ev.t_e).dt.days > 400)
    if verbose:
        print(f"[events L={L}] linked to CRSP {n_link}, in the top-3,000 universe {n_univ}, price >= $5 and no overlap: positions {len(Ev)}; "
              f"exit by report {int((Ev.reason == 'report').sum())}, by NT notice {int((Ev.reason == 'NT').sum())}, by 30 days {int((Ev.reason == '30d').sum())}; "
              f"expected gap 0: {np.mean(Ev.G_exp == 0):.3f}; fiscal Q4 (10-K): {np.mean(Ev.fqtr == 4):.3f}; rank 1001-3000: {np.mean(Ev.rk > 1000):.3f}; "
              f"no later report within 400 days: {Ev.no_later_report.mean():.4f}; by half: {int((Ev.year <= 2013).sum())} / {int((Ev.year >= 2014).sum())}")
    con.register("ev", Ev[["eid", "permno", "t_e", "exit"]])
    R = con.execute(f"SELECT e.eid, e.permno, s.date, s.dlyret r FROM ev e JOIN '{SLIM}' s ON s.permno = e.permno AND s.date > e.t_e AND s.date <= e.exit WHERE s.dlyret IS NOT NULL").df()
    con.unregister("ev")
    R["date"] = pd.to_datetime(R["date"])
    R = R.sort_values(["eid", "date"]).reset_index(drop=True)
    g = R.groupby("eid", sort=False)
    R["first"] = g.cumcount() == 0
    R["last"] = g.cumcount(ascending=False) == 0
    R = R.merge(Ev[["eid", "t_e", "year", "rk", "reason", "G_exp", "cap", "fqtr", "no_later_report"]], on="eid")
    return Ev, R


def add_costs(Ev, R):
    """half the quoted closing spread at entry and at exit, plus a 1% per year borrow fee on calendar days"""
    last = R[R["last"]][["eid", "permno", "date"]].rename(columns={"date": "d_last"})
    e = Ev[["eid", "permno", "t_e", "year"]].merge(last, on=["eid", "permno"])
    q = pd.concat([e[["permno", "t_e"]].rename(columns={"t_e": "date"}), e[["permno", "d_last"]].rename(columns={"d_last": "date"})]).drop_duplicates()
    q["date"] = q["date"].dt.date
    con.register("qq", q)
    qs = con.execute(f"""SELECT q.permno, q.date, (b.ask - b.bid) / ((b.ask + b.bid) / 2) qs FROM qq q JOIN '{BIDASK}' b ON b.permno = q.permno AND b.date = q.date
                         WHERE b.bid > 0 AND b.ask >= b.bid AND (b.ask - b.bid) / ((b.ask + b.bid) / 2) < 1""").df()
    con.unregister("qq")
    qs["date"] = pd.to_datetime(qs["date"])
    e = e.merge(qs.rename(columns={"date": "t_e", "qs": "qs_in"}), on=["permno", "t_e"], how="left").merge(qs.rename(columns={"date": "d_last", "qs": "qs_out"}), on=["permno", "d_last"], how="left")
    miss = (float(e.qs_in.isna().mean()), float(e.qs_out.isna().mean()))
    e["qs_in"] = e.qs_in.fillna(e.qs_out)
    e["qs_out"] = e.qs_out.fillna(e.qs_in)
    for c in ("qs_in", "qs_out"):
        e[c] = e[c].fillna(e.groupby("year")[c].transform("median")).fillna(e[c].median())
    R = R.merge(e[["eid", "qs_in", "qs_out"]], on="eid", how="left")
    R["cost"] = np.where(R["first"], R.qs_in / 2, 0.0) + np.where(R["last"], R.qs_out / 2, 0.0) + 0.01 * R.date.map(dcal).values / 365.0
    print(f"   cost inputs: quoted spread missing at entry {miss[0]:.4f}, at exit {miss[1]:.4f}; mean spread at entry {e.qs_in.mean() * 1e4:.1f}bp, at exit {e.qs_out.mean() * 1e4:.1f}bp; "
          f"mean round-trip spread cost per position {(e.qs_in / 2 + e.qs_out / 2).mean() * 1e4:.1f}bp, plus borrow")
    return R


def alpha(sub, label, vw=False, net_short=False, save=None):
    n = sub.groupby("date").r.size()
    if vw:
        w = sub.assign(wr=sub.cap * sub.r).groupby("date")
        p = w.wr.sum() / w.cap.sum()
    else:
        p = sub.groupby("date").r.mean()
    p = p[n >= 10]
    if len(p) < 100:
        print(f"   {label:52s} events {sub.eid.nunique():6d}: only {len(p)} days with >= 10 names")
        return None
    d = pd.DataFrame({"y": p, "n": n[n >= 10]}).join(ff, how="inner").join(U.rename("u"), how="left")
    if net_short:
        c = sub.groupby("date").cost.mean().reindex(d.index)
        y = -(d.y - d.rf) - c
    else:
        y = d.y - d.rf
    f = sm.OLS(y, sm.add_constant(d[FC])).fit(cov_type="HAC", cov_kwds={"maxlags": 5})
    f0 = sm.OLS(y, np.ones(len(y))).fit(cov_type="HAC", cov_kwds={"maxlags": 5})
    out = (f"   {label:52s} events {sub.eid.nunique():6d} days {len(d):5d} names {d.n.mean():6.1f} | alpha {f.params['const'] * 1e4:+6.2f}bp (t {f.tvalues['const']:+.2f}) "
           f"| mean {f0.params.iloc[0] * 1e4:+6.2f}bp (t {f0.tvalues.iloc[0]:+.2f})")
    if not net_short:
        dd = d.dropna(subset=["u"])
        f2 = sm.OLS(dd.y - dd.u, np.ones(len(dd))).fit(cov_type="HAC", cov_kwds={"maxlags": 5})
        out += f" | minus universe EW {f2.params.iloc[0] * 1e4:+6.2f}bp (t {f2.tvalues.iloc[0]:+.2f})"
    print(out)
    if save is not None:
        d.assign(excess=d.y - d.rf).to_csv(save)
    return f.params["const"] * 1e4, f.tvalues["const"]


Ev, R = build(5)
Ev.to_parquet(HERE / "rdq_i_events.parquet", index=False)
hp = R.groupby("eid").size()
print(f"   holding period: mean {hp.mean():.1f} trading days, median {hp.median():.0f}; events by entry year: {Ev.year.value_counts().sort_index().to_dict()}")
print("[RDQ-I primary] daily equal-weighted portfolio of firms whose periodic report is overdue (entry F_exp + 5); expected sign negative; "
      "pass needs |t| >= 2.58, both halves negative, later half |t| >= 1.96")
alpha(R, "all entries 2003-2024", save=HERE / "rdq_i_daily.csv")
alpha(R[R.year <= 2013], "entries 2003-2013")
alpha(R[R.year >= 2014], "entries 2014-2024")
print("[RDQ-I side reports]")
alpha(R[R.reason != "NT"], "excluding positions that end in an NT notice")
alpha(R[R.G_exp == 0], "expected gap 0 (report used to come with earnings)")
alpha(R[R.G_exp > 0], "expected gap > 0")
alpha(R[R.fqtr == 4], "annual report (fiscal Q4)")
alpha(R[R.fqtr != 4], "quarterly report (fiscal Q1-Q3)")
alpha(R[R.rk > 1000], "size rank 1001-3000")
alpha(R[R.rk <= 1000], "size rank 1-1000")
alpha(R, "value-weighted (entry market cap)", vw=True)
alpha(R[~R.no_later_report], "excluding firms with no later report within 400 days")
for a, b in [(2003, 2007), (2008, 2012), (2013, 2017), (2018, 2024)]:
    alpha(R[(R.year >= a) & (R.year <= b)], f"entries {a}-{b}")
print("[RDQ-I short side net of costs] minus the excess return, minus half-spreads and a 1% borrow fee; expected sign positive")
R = add_costs(Ev, R)
alpha(R, "net short, all entries", net_short=True)
alpha(R[R.year <= 2013], "net short, entries 2003-2013", net_short=True)
alpha(R[R.year >= 2014], "net short, entries 2014-2024", net_short=True)
for L in (1, 10):
    EvL, RL = build(L)
    alpha(RL, f"entry at F_exp + {L} trading days, all entries")
    alpha(RL[RL.year <= 2013], f"entry at F_exp + {L}, 2003-2013")
    alpha(RL[RL.year >= 2014], f"entry at F_exp + {L}, 2014-2024")
