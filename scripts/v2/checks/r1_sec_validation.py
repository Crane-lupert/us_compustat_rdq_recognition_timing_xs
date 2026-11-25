"""Main-thread validation of the RDQ phase-4 result R1 with SEC filing dates.

Why: R1 shorts firms that are 'silent' five trading days after their expected earnings date, where silence is read
from Compustat's announcement date (rdq). A spot check of 40 events found 7 in which the firm had in fact filed an
earnings 8-K (Item 2.02) inside the window - Compustat's date was late. A real-time trader would not have treated
those firms as silent.

Rule fixed before computing any return of the validated subset (2026-11-21):
  - earnings release = 8-K or 8-K/A with Item 2.02 (item exists since 2004-08-23) -> entries from 2005-01-01 only
  - VERIFIED SILENT = no such filing in (E - 30 calendar days, entry date]
  - statistic: the R1 portfolio (same entry, exit, universe, price filter, >= 10 names, FF5+UMD, NW 5) on the
    verified-silent events; reported next to the events that fail verification and next to all 2005-2024 events
  - exits are left as in R1 (Compustat next rdq) so that only the entry screen changes
  - events whose firm has no CIK or no SEC filing history are reported separately (unverifiable)
Steps: python r1_sec_validation.py fetch   (resumable; SEC submissions API, generic User-Agent, <= 3 requests/s)
       python r1_sec_validation.py test
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
ROOT = HERE.parent
CACHE = HERE / "r1_cache"
DUMP = WRDS_DUMP.rstrip("/")
SLIM = (ROOT / "RDQ_cadence" / "dsf_v2_slim.parquet").as_posix()
PARTS = CACHE / "sec_parts"
PARTS.mkdir(parents=True, exist_ok=True)
DONE = CACHE / "sec_done.txt"

Ev = pd.read_parquet(CACHE / "r1_events_main_thread.parquet")
fq = pd.read_parquet(CACHE / "fundq_rdq.parquet", columns=["gvkey", "datadate", "cik"])
cik = fq[fq.cik.notna() & (fq.cik != "")].sort_values("datadate").drop_duplicates("gvkey", keep="last").set_index("gvkey").cik
Ev["cik"] = Ev.gvkey.map(cik)
Ev["cik10"] = Ev.cik.astype("string").str.zfill(10)
E05 = Ev[Ev.t_e >= "2005-01-01"].copy()


def have_from_xa():
    p = ROOT / "X_sec_letter" / "phase4" / "xa" / "cache" / "sec_filings.parquet"
    x = pd.read_parquet(p, columns=["cik10", "form", "filingDate", "items"])
    return x[x.form.isin(["8-K", "8-K/A"])]


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": os.environ["SEC_USER_AGENT"]})
    with urllib.request.urlopen(req, timeout=40) as r:
        return json.loads(r.read().decode("utf-8"))


if len(sys.argv) > 1 and sys.argv[1] == "fetch":
    xa_ciks = set(have_from_xa().cik10.unique())
    need = sorted(set(E05.cik10.dropna()) - xa_ciks)
    done = set(DONE.read_text().split()) if DONE.exists() else set()
    todo = [c for c in need if c not in done]
    print(f"events since 2005: {len(E05)}, firms with CIK {E05.cik10.nunique()}, already in the XA table {len(set(E05.cik10.dropna()) & xa_ciks)}, to fetch {len(todo)} (done {len(done)})", flush=True)
    buf, n = [], 0
    for c in todo:
        try:
            j = get(f"https://data.sec.gov/submissions/CIK{c}.json")
            time.sleep(0.35)
            blocks = [j["filings"]["recent"]]
            for f in j["filings"].get("files", []):
                blocks.append(get("https://data.sec.gov/submissions/" + f["name"]))
                time.sleep(0.35)
            for b in blocks:
                for form, fdate, items in zip(b["form"], b["filingDate"], b.get("items", [""] * len(b["form"]))):
                    if form in ("8-K", "8-K/A"):
                        buf.append((c, form, fdate, items))
            status = "ok"
        except urllib.error.HTTPError as e:
            if e.code in (403, 429):
                print(f"STOP: HTTP {e.code} at CIK {c}", flush=True)
                break
            status = f"http{e.code}"
        except Exception as e:
            status = "err"
        with open(DONE, "a") as fh:
            fh.write(c + "\n")
        n += 1
        if n % 200 == 0 or c == todo[-1]:
            pd.DataFrame(buf, columns=["cik10", "form", "filingDate", "items"]).to_parquet(PARTS / f"part_{int(time.time())}.parquet", index=False)
            buf = []
            print(f"  fetched {n}/{len(todo)}", flush=True)
    if buf:
        pd.DataFrame(buf, columns=["cik10", "form", "filingDate", "items"]).to_parquet(PARTS / f"part_{int(time.time())}_last.parquet", index=False)
    print("fetch finished", flush=True)
    sys.exit(0)

# ---------------- test ----------------
parts = [pd.read_parquet(p) for p in sorted(PARTS.glob("*.parquet"))]
F = pd.concat([have_from_xa()] + parts, ignore_index=True)
F = F[F["items"].fillna("").apply(lambda v: "2.02" in [t.strip() for t in str(v).split(",")])].copy()
F["fd"] = pd.to_datetime(F.filingDate)
any8k = set(pd.concat([have_from_xa()] + parts, ignore_index=True).cik10.unique())
d202 = F.groupby("cik10").fd.apply(lambda v: np.sort(v.values)).to_dict()
print(f"earnings 8-K (Item 2.02) filings available: {len(F)}, CIKs {F.cik10.nunique()}; CIKs with any 8-K history {len(any8k)}")


def in_window(c, lo, hi):
    a = d202.get(c)
    if a is None:
        return False
    return bool(((a > np.datetime64(lo)) & (a <= np.datetime64(hi))).any())


E05["has_hist"] = E05.cik10.isin(any8k)
E05["ann8k"] = [in_window(c, pd.Timestamp(e) - pd.Timedelta(days=30), pd.Timestamp(t)) if h else False for c, e, t, h in zip(E05.cik10, E05.E, E05.t_e, E05.has_hist)]
E05["grp"] = np.where(~E05.has_hist, "unverifiable", np.where(E05.ann8k, "not silent (8-K in window)", "verified silent"))
print("events since 2005 by verification:", E05.grp.value_counts().to_dict())
print("  share with an earnings 8-K inside the window among verifiable:", round(float(E05[E05.has_hist].ann8k.mean()), 4))
print("  by 5-year block:", E05[E05.has_hist].groupby(E05.t_e.dt.year // 5 * 5).ann8k.mean().round(3).to_dict())

con = duckdb.connect()
con.execute("SET memory_limit='6GB'")
con.register("ev", E05[["eid", "permno", "t_e", "exit"]])
R = con.execute(f"""SELECT e.eid, s.date, s.dlyret r FROM ev e JOIN '{SLIM}' s ON s.permno = e.permno AND s.date > e.t_e AND s.date <= e.exit
                    WHERE s.dlyret IS NOT NULL""").df()
R["date"] = pd.to_datetime(R["date"])
R = R.merge(E05[["eid", "t_e", "rk", "grp"]], on="eid")
ff = con.execute(f"SELECT * FROM read_csv('{DUMP}/ff_all.fivefactors_daily.csv.gz', header=true)").df()
ff["date"] = pd.to_datetime(ff["date"])
ff = ff.set_index("date").astype(float)


def alpha(sub, label):
    g = sub.groupby("date")
    p, n = g.r.mean(), g.r.size()
    p = p[n >= 10]
    if len(p) < 60:
        print(f"   {label:46s} events {sub.eid.nunique():6d}: too few days with >= 10 names ({len(p)})")
        return
    d = pd.DataFrame({"y": p}).join(ff, how="inner")
    y = d.y - d.rf
    f = sm.OLS(y, sm.add_constant(d[["mktrf", "smb", "hml", "rmw", "cma", "umd"]])).fit(cov_type="HAC", cov_kwds={"maxlags": 5})
    f0 = sm.OLS(y, np.ones(len(y))).fit(cov_type="HAC", cov_kwds={"maxlags": 5})
    print(f"   {label:46s} events {sub.eid.nunique():6d} days {len(d):5d} avg names {n[n >= 10].mean():5.1f} | alpha {f.params['const']*1e4:+6.2f}bp (t {f.tvalues['const']:+.2f}) "
          f"| mean excess {f0.params.iloc[0]*1e4:+6.2f}bp (t {f0.tvalues.iloc[0]:+.2f})")


print("[R1 with SEC verification] daily equal-weighted portfolio, FF5+UMD intercept")
alpha(R, "all events 2005-2024")
vs = R[R.grp == "verified silent"]
alpha(vs, "VERIFIED SILENT 2005-2024")
alpha(vs[vs.t_e < "2015-01-01"], "  verified silent, entries 2005-2014")
alpha(vs[vs.t_e >= "2015-01-01"], "  verified silent, entries 2015-2024")
alpha(vs[vs.t_e >= "2020-01-01"], "  verified silent, entries 2020-2024")
alpha(vs[vs.rk > 1000], "  verified silent, size rank 1001-3000")
alpha(vs[vs.rk <= 1000], "  verified silent, size rank 1-1000")
alpha(R[R.grp == "not silent (8-K in window)"], "not silent (earnings 8-K already filed)")
alpha(R[R.grp == "unverifiable"], "unverifiable (no SEC 8-K history)")
E05.to_parquet(CACHE / "r1_events_sec_verified.parquet", index=False)
