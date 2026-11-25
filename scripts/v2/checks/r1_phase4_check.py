"""Main-thread independent rebuild of the RDQ phase-4 test R1 (short firms that are overdue on their earnings date).

Own code from raw inputs: Compustat fundq (dump) for announcement dates, the CRSP daily extract for returns,
own identifier link (Compustat header CUSIP = CRSP header CUSIP), own June top-3,000 universe (CIZ share flags),
own event construction. Nothing is read from the agent's phase-4 folder except, at the end, its event table
(to compare counts and overlap).

Rule (PHASE4_SPEC R1 + the agent's pre-result clarification (b)):
  E = first trading day >= (prior-year same-quarter announcement date + 1 year); entry = close of E + 5 trading days if
  (a) no announcement of the firm in (E - 30 calendar days, entry] and (b) the slot's own quarter (or a later one) has not
  been announced by entry; price >= $5 and in the universe at entry; exit = close of the trading day after the next
  announcement, or 40 trading days, or delisting. Daily equal-weighted portfolio, days with < 10 stocks dropped,
  FF5+UMD intercept with Newey-West(5).
Run: python r1_phase4_check.py [--sec]
"""
import json
import sys
import time
import urllib.request
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd
import statsmodels.api as sm

import os
from v2paths import MC_DIR, WRDS_DUMP
HERE = MC_DIR
RDQ = HERE.parent / "RDQ_cadence"
DUMP = WRDS_DUMP.rstrip("/")
SLIM = (RDQ / "dsf_v2_slim.parquet").as_posix()
CACHE = HERE / "r1_cache"
CACHE.mkdir(exist_ok=True)
con = duckdb.connect()
con.execute("SET memory_limit='7GB'")

# ---------------- announcements ----------------
fq = CACHE / "fundq_rdq.parquet"
if not fq.exists():
    con.execute(f"""COPY (SELECT gvkey, CAST(datadate AS DATE) datadate, TRY_CAST(fyearq AS INT) fyearq, TRY_CAST(fqtr AS INT) fqtr,
                           TRY_CAST(fyr AS INT) fyr, cusip, TRY_CAST(rdq AS DATE) rdq, cik
                    FROM read_csv('{DUMP}/comp_na_daily_all.fundq.csv.gz', all_varchar=true, header=true, ignore_errors=true)
                    WHERE indfmt='INDL' AND datafmt='STD' AND consol='C' AND popsrc='D' AND datadate >= '1997-01-01')
                   TO '{fq.as_posix()}' (FORMAT parquet)""")
A = pd.read_parquet(fq)
A["datadate"] = pd.to_datetime(A.datadate)
A["rdq"] = pd.to_datetime(A.rdq)
V = A[A.rdq.notna() & (A.rdq > A.datadate)].copy()
V = V.sort_values(["gvkey", "fyearq", "fqtr", "datadate"]).drop_duplicates(["gvkey", "fyearq", "fqtr"], keep="last")
print(f"[ann] fundq rows {len(A)}, valid announcement records {len(V)}, gvkeys {V.gvkey.nunique()}")

# ---------------- calendar ----------------
cal = con.execute(f"SELECT DISTINCT date FROM '{SLIM}' ORDER BY 1").df()
days = pd.DatetimeIndex(pd.to_datetime(cal["date"]))
dnp = days.values


def k_on_or_after(d):
    return np.searchsorted(dnp, np.asarray(d, dtype="datetime64[ns]"), side="left")


# ---------------- slots from prior-year records ----------------
P = V[V.fyearq.notna() & V.fqtr.notna()].copy()
P["gap"] = (P.rdq - P.datadate).dt.days
P = P[(P.gap >= 1) & (P.gap <= 120)]
P["E_raw"] = P.rdq + pd.DateOffset(years=1)
P["kE"] = k_on_or_after(P.E_raw.values)
P = P[P.kE + 5 < len(days)]
P["E"] = dnp[P.kE.values]
P["t_e"] = dnp[P.kE.values + 5]
P["D_exp"] = P.datadate + pd.DateOffset(months=12)
P = P.sort_values(["gvkey", "E", "datadate"]).drop_duplicates(["gvkey", "E"], keep="last")
P = P[(P.t_e >= "2000-01-01") & (P.t_e <= "2024-12-31")]
print(f"[slots] expected-date slots {len(P)}")

# (a) and (b) with per-firm arrays
by = {g: (d.rdq.values.astype("datetime64[ns]"), d.datadate.values.astype("datetime64[ns]")) for g, d in V.sort_values(["gvkey", "rdq"]).groupby("gvkey")}
keep, nxt = [], []
for g, d in P.groupby("gvkey", sort=False):
    rd, dd = by[g]
    rds = np.sort(rd)
    o = np.argsort(dd)
    dd_s, rd_by_dd = dd[o], rd[o]
    sufmin = np.minimum.accumulate(rd_by_dd[::-1])[::-1]
    te = d.t_e.values.astype("datetime64[ns]")
    lo = d.E.values.astype("datetime64[ns]") - np.timedelta64(30, "D")
    a_cnt = np.searchsorted(rds, te, side="right") - np.searchsorted(rds, lo, side="right")
    j = np.searchsorted(dd_s, d.D_exp.values.astype("datetime64[ns]") - np.timedelta64(15, "D"), side="left")
    b_min = np.where(j < len(sufmin), sufmin[np.minimum(j, len(sufmin) - 1)], np.datetime64("NaT"))
    b_ann = ~np.isnat(b_min) & (b_min <= te)
    keep.append((a_cnt == 0) & ~b_ann)
    jn = np.searchsorted(rds, te, side="right")
    nxt.append(np.where(jn < len(rds), rds[np.minimum(jn, len(rds) - 1)], np.datetime64("NaT")))
P["overdue"] = np.concatenate(keep)
P["overdue_literal"] = None
P["rdq_next"] = np.concatenate(nxt)
Ev = P[P.overdue].copy()
print(f"[overdue] slots still silent at E+5 (rules a and b): {len(Ev)}")

# ---------------- own link and universe ----------------
hdr = con.execute(f"SELECT permno, max(hdrcusip8) AS h FROM '{SLIM}' GROUP BY 1").df()
h2p = hdr.groupby("h").permno.apply(list).to_dict()
c8 = A.dropna(subset=["cusip"]).drop_duplicates("gvkey").set_index("gvkey").cusip.str[:8]
Ev["permno"] = [(h2p.get(c8.get(g)) or [None])[0] if len(h2p.get(c8.get(g)) or []) == 1 else None for g in Ev.gvkey]
print(f"[link] overdue slots linked by header CUSIP: {int(Ev.permno.notna().sum())}")
Ev = Ev[Ev.permno.notna()].copy()
Ev["permno"] = Ev.permno.astype(int)
mem = con.execute(f"""
  WITH j AS (SELECT year(date) y, max(date) d FROM '{SLIM}' WHERE month(date) = 6 GROUP BY 1),
       r AS (SELECT j.y, s.permno, row_number() OVER (PARTITION BY j.y ORDER BY s.dlycap DESC) rk
             FROM j JOIN '{SLIM}' s ON s.date = j.d
             WHERE s.sharetype='NS' AND s.securitytype='EQTY' AND s.securitysubtype='COM' AND s.usincflg='Y'
               AND s.issuertype IN ('CORP','ACOR') AND s.primaryexch IN ('N','A','Q') AND s.dlycap > 0)
  SELECT y, permno, rk FROM r WHERE rk <= 3000""").df()
ms = {(int(y), int(p)): int(rk) for y, p, rk in zip(mem.y, mem.permno, mem.rk)}
te = pd.DatetimeIndex(Ev.t_e)
Ev["mem_y"] = np.where(te.month >= 7, te.year, te.year - 1)
Ev["rk"] = [ms.get((int(y), int(p))) for y, p in zip(Ev.mem_y, Ev.permno)]
Ev = Ev[Ev.rk.notna()].copy()
# price at entry
con.register("e0", Ev[["permno", "t_e"]].drop_duplicates())
px = con.execute(f"""SELECT e.permno, e.t_e, abs(s.dlyprc) prc, s.dlydelflg FROM e0 e JOIN '{SLIM}' s ON s.permno = e.permno AND s.date = e.t_e""").df()
px["t_e"] = pd.to_datetime(px.t_e)
Ev = Ev.merge(px, on=["permno", "t_e"], how="inner")
Ev = Ev[(Ev.prc >= 5) & (Ev.dlydelflg.fillna("N") != "Y")].copy()
k_e = k_on_or_after(Ev.t_e.values)
k_ann = np.where(Ev.rdq_next.isna().values, 10 ** 9, np.searchsorted(dnp, Ev.rdq_next.values.astype("datetime64[ns]"), side="right"))
k_x = np.minimum(np.minimum(k_ann, k_e + 40), len(days) - 1)
Ev["exit"] = dnp[k_x]
Ev["reason"] = np.where(k_ann <= k_e + 40, "announce", "40d")
Ev = Ev.sort_values(["permno", "t_e", "datadate"])
last_exit, flag = {}, []
for p, t, x in zip(Ev.permno.values, Ev.t_e.values, Ev["exit"].values):
    ok = (p not in last_exit) or (t >= last_exit[p])
    flag.append(ok)
    if ok:
        last_exit[p] = x
Ev = Ev[np.array(flag)].copy()
Ev["eid"] = np.arange(len(Ev))
Ev["no_current_row"] = Ev.rdq_next.isna()
print(f"[events] entered positions: {len(Ev)} (first half {int((Ev.t_e < '2013-01-01').sum())}, second half {int((Ev.t_e >= '2013-01-01').sum())}); "
      f"exit by announcement {int((Ev.reason == 'announce').sum())}, by 40 days {int((Ev.reason == '40d').sum())}; rank 1001-3000 share {np.mean(Ev.rk > 1000):.3f}")

# ---------------- returns ----------------
con.register("ev", Ev[["eid", "permno", "t_e", "exit"]])
R = con.execute(f"""SELECT e.eid, s.date, s.dlyret r FROM ev e JOIN '{SLIM}' s ON s.permno = e.permno AND s.date > e.t_e AND s.date <= e.exit
                    WHERE s.dlyret IS NOT NULL""").df()
R["date"] = pd.to_datetime(R["date"])
R = R.merge(Ev[["eid", "t_e", "rk"]], on="eid")
ff = con.execute(f"SELECT * FROM read_csv('{DUMP}/ff_all.fivefactors_daily.csv.gz', header=true)").df()
ff["date"] = pd.to_datetime(ff["date"])
ff = ff.set_index("date").astype(float)


def alpha(sub, label, vw=False):
    g = sub.groupby("date")
    p = g.r.mean()
    n = g.r.size()
    p = p[n >= 10]
    d = pd.DataFrame({"y": p}).join(ff, how="inner")
    y = d.y - d.rf
    f = sm.OLS(y, sm.add_constant(d[["mktrf", "smb", "hml", "rmw", "cma", "umd"]])).fit(cov_type="HAC", cov_kwds={"maxlags": 5})
    f0 = sm.OLS(y, np.ones(len(y))).fit(cov_type="HAC", cov_kwds={"maxlags": 5})
    print(f"   {label:38s} events {sub.eid.nunique():6d} days {len(d):5d} avg names {n[n >= 10].mean():5.1f} | alpha {f.params['const']*1e4:+6.2f}bp (t {f.tvalues['const']:+.2f}) "
          f"| mean excess {f0.params[0]*1e4:+6.2f}bp (t {f0.tvalues[0]:+.2f})")
    return f.params["const"] * 1e4, f.tvalues["const"]


print("[R1] daily equal-weighted portfolio of overdue firms, FF5+UMD intercept (expected sign negative)")
alpha(R, "all entries 2000-2024")
alpha(R[R.t_e < "2013-01-01"], "entries 2000-2012")
alpha(R[R.t_e >= "2013-01-01"], "entries 2013-2024")
alpha(R[R.rk > 1000], "size rank 1001-3000")
alpha(R[R.rk <= 1000], "size rank 1-1000")
for a, b in [(2000, 2004), (2005, 2009), (2010, 2014), (2015, 2019), (2020, 2024)]:
    alpha(R[(R.t_e.dt.year >= a) & (R.t_e.dt.year <= b)], f"entries {a}-{b}")

# ---------------- comparison with the agent's event table ----------------
try:
    ag = pd.read_parquet(RDQ / "phase4" / "out" / "r1_event_table.parquet")
    cols = {c.lower(): c for c in ag.columns}
    pc = cols.get("permno")
    ec = [c for c in ag.columns if c.lower() in ("t_e", "entry", "entry_date", "entry_dt")][0]
    a_keys = set(zip(ag[pc].astype(int), pd.to_datetime(ag[ec]).dt.strftime("%Y%m%d")))
    m_keys = set(zip(Ev.permno.astype(int), pd.to_datetime(Ev.t_e).dt.strftime("%Y%m%d")))
    print(f"[cmp] agent events {len(a_keys)}, main-thread events {len(m_keys)}, common {len(a_keys & m_keys)} "
          f"({len(a_keys & m_keys) / len(a_keys):.3f} of the agent's)")
except Exception as e:
    print("[cmp] agent event table not compared:", repr(e)[:200])
Ev.to_parquet(CACHE / "r1_events_main_thread.parquet", index=False)

# ---------------- SEC spot check: were these firms really silent? ----------------
if "--sec" in sys.argv:
    cik = A.dropna(subset=["cik"]).drop_duplicates("gvkey").set_index("gvkey").cik
    S = Ev[(Ev.t_e >= "2006-01-01")].copy()
    S["cik"] = S.gvkey.map(cik)
    S = S[S.cik.notna() & (S.cik != "")].sample(40, random_state=20261121)

    def get(url):
        req = urllib.request.Request(url, headers={"User-Agent": os.environ["SEC_USER_AGENT"]})
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read().decode("utf-8"))

    silent = early = fail = 0
    for row in S.itertuples(index=False):
        c = str(row.cik).zfill(10)
        try:
            j = get(f"https://data.sec.gov/submissions/CIK{c}.json")
            time.sleep(0.4)
            blocks = [j["filings"]["recent"]]
            for f in j["filings"].get("files", []):
                blocks.append(get("https://data.sec.gov/submissions/" + f["name"]))
                time.sleep(0.4)
            d202 = []
            for b in blocks:
                for form, fdate, items in zip(b["form"], b["filingDate"], b.get("items", [""] * len(b["form"]))):
                    if form in ("8-K", "8-K/A") and "2.02" in [t.strip() for t in str(items).split(",")]:
                        d202.append(pd.Timestamp(fdate))
            lo, hi = pd.Timestamp(row.E) - pd.Timedelta(days=30), pd.Timestamp(row.t_e)
            inwin = [d for d in d202 if lo < d <= hi]
            if inwin:
                early += 1
                print(f"    8-K Item 2.02 inside the window: cik {c}, E {pd.Timestamp(row.E).date()}, entry {hi.date()}, 2.02 on {[str(d.date()) for d in inwin]}, Compustat next rdq {pd.Timestamp(row.rdq_next).date() if pd.notna(row.rdq_next) else None}")
            else:
                silent += 1
        except Exception as e:
            fail += 1
            if "403" in repr(e) or "429" in repr(e):
                print("    stopping (403/429)")
                break
    print(f"[sec] sample of {len(S)} events since 2006: no earnings 8-K (Item 2.02) in (E-30d, entry] in {silent}; an earnings 8-K was filed in the window in {early}; request failed {fail}")
