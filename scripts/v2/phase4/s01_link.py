"""s01: gvkey -> permno link for phase 4 (FROZEN_PARAMS "link"). No return outcome is used.
  1. phase-3 link.parquet (p02 rules A/B on the panel_ext gvkeys) is kept as is.
  2. Every other Compustat fundq gvkey with a valid announcement (rdq > datadate, rdq >= 1998-01-01) is linked with the
     same rules: A = Compustat names CUSIP[:8] == CRSP dsenames ncusip whose record(s) overlap the gvkey's announcement
     span [min rdq, max rdq]; B (if no A) = Compustat namesd security CUSIP[:8] == ncusip, same overlap rule.
     Several candidates -> largest overlap days, then lowest permno (p02 rule B tie-break, also used for A here).
  3. p03 shared-permno rule on every market trading day: a permno linked to >1 gvkey is assigned on date t to the gvkey
     whose names-CUSIP dsenames record covers t; if none covers t, to the gvkey whose record is nearest in time
     (ties -> later record start, then first gvkey). gvkeys with no names-CUSIP record on that permno never win.
Writes cache/link4.parquet (gvkey, permno, step), cache/shared_assign.parquet (permno, date, gvkey).
"""
import sys
sys.dont_write_bytecode = True
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from p4common import CACHE, P3, DUMP, con, load_calendar  # noqa: E402

c = con()
fq = pd.read_parquet(CACHE / "fundq_rdq.parquet", columns=["gvkey", "datadate", "rdq"])
fq["datadate"] = pd.to_datetime(fq["datadate"]); fq["rdq"] = pd.to_datetime(fq["rdq"])
ok = fq.rdq.notna() & fq.datadate.notna() & (fq.rdq > fq.datadate) & (fq.rdq >= "1998-01-01")
span = fq[ok].groupby("gvkey").agg(r0=("rdq", "min"), r1=("rdq", "max")).reset_index()
names = c.execute(f"SELECT gvkey, cusip FROM read_csv('{DUMP}comp_na_daily_all.names.csv.gz', header=true, all_varchar=true)").df()
names = names.sort_values("gvkey", kind="mergesort").drop_duplicates("gvkey", keep="last")
names["cusip8"] = names["cusip"].str.slice(0, 8)
span = span.merge(names[["gvkey", "cusip8"]], on="gvkey", how="left")
L3 = pd.read_parquet(P3 / "out/link.parquet")
new = span[~span.gvkey.isin(L3.gvkey)].copy()
print("gvkeys with valid rdq >= 1998:", len(span), " in phase-3 link:", int(span.gvkey.isin(L3.gvkey).sum()), " to try:", len(new))

c.execute(f"""CREATE TABLE nm AS SELECT permno::INT permno, namedt::DATE namedt, nameendt::DATE nameendt, ncusip,
    TRY_CAST(shrcd AS INT) shrcd, TRY_CAST(exchcd AS INT) exchcd FROM read_csv('{DUMP}crsp_a_stock.dsenames.csv.gz', header=true, all_varchar=true)""")
c.execute(f"CREATE TABLE nd AS SELECT gvkey, iid, substr(cusip,1,8) c8 FROM read_csv('{DUMP}comp_na_daily_all.namesd.csv.gz', header=true, all_varchar=true)")
c.register("span", new)
A = c.execute("""SELECT s.gvkey, n.permno, min(n.namedt) nd0, max(n.nameendt) nd1, s.r0, s.r1
                 FROM span s JOIN nm n ON n.ncusip = s.cusip8 GROUP BY ALL""").df()
A["ov"] = (np.minimum(pd.to_datetime(A.nd1), A.r1) - np.maximum(pd.to_datetime(A.nd0), A.r0)).dt.days
A = A[A.ov >= 0].sort_values(["gvkey", "ov", "permno"], ascending=[True, False, True], kind="mergesort")
na_multi = int(A.groupby("gvkey").size().gt(1).sum())
A = A.drop_duplicates("gvkey", keep="first").assign(step="A4")
rest = new[~new.gvkey.isin(A.gvkey)]
c.register("rest", rest)
B = c.execute("""SELECT s.gvkey, n.permno, min(n.namedt) nd0, max(n.nameendt) nd1, s.r0, s.r1
                 FROM rest s JOIN nd d ON d.gvkey = s.gvkey JOIN nm n ON n.ncusip = d.c8 GROUP BY ALL""").df()
B["ov"] = (np.minimum(pd.to_datetime(B.nd1), B.r1) - np.maximum(pd.to_datetime(B.nd0), B.r0)).dt.days
B = B[B.ov >= 0].sort_values(["gvkey", "ov", "permno"], ascending=[True, False, True], kind="mergesort")
nb_multi = int(B.groupby("gvkey").size().gt(1).sum())
B = B.drop_duplicates("gvkey", keep="first").assign(step="B4")
print(f"new links: rule A {len(A)} (gvkeys with >1 candidate {na_multi}), rule B {len(B)} (>1 candidate {nb_multi})")
L4 = pd.concat([L3[["gvkey", "permno", "step"]], A[["gvkey", "permno", "step"]], B[["gvkey", "permno", "step"]]], ignore_index=True)
L4["permno"] = L4["permno"].astype("int64")
assert L4.gvkey.is_unique
L4.to_parquet(CACHE / "link4.parquet", index=False)
dup = L4[L4.permno.duplicated(keep=False)]
print("link4 gvkeys:", len(L4), " permnos:", L4.permno.nunique(), " shared permnos:", dup.permno.nunique(), " gvkey rows on them:", len(dup),
      " (phase-3 shared permnos:", int(L3.permno.duplicated(keep=False).sum()), "rows)")

# ---- shared-permno date assignment (p03 rule, vectorised over trading days) ----
cal = load_calendar()
days = cal.date.values.astype("datetime64[D]")
nm = c.execute("SELECT permno, namedt, nameendt, ncusip FROM nm").df()
nm["namedt"] = pd.to_datetime(nm["namedt"]); nm["nameendt"] = pd.to_datetime(nm["nameendt"])
sh = dup.merge(names[["gvkey", "cusip8"]], on="gvkey", how="left")
iv = sh.merge(nm, left_on=["permno", "cusip8"], right_on=["permno", "ncusip"])[["gvkey", "permno", "namedt", "nameendt"]]
out = []
for p, g in sh.groupby("permno"):
    ivp = iv[iv.permno == p]
    best = np.full(len(days), None, dtype=object)
    bestd = np.full(len(days), np.inf)
    bests = np.full(len(days), np.datetime64("1800-01-01"), dtype="datetime64[D]")
    for gk, gi in ivp.groupby("gvkey", sort=True):
        a = gi.namedt.values.astype("datetime64[D]")[None, :]
        b = gi.nameendt.values.astype("datetime64[D]")[None, :]
        t = days[:, None]
        inside = (t >= a) & (t <= b)
        dist = np.where(inside, 0, np.minimum(np.abs((t - b).astype(int)), np.abs((a - t).astype(int)))).min(axis=1).astype(float)
        st = gi.namedt.values.astype("datetime64[D]").max()
        upd = (dist < bestd) | ((dist == bestd) & (st > bests))
        best = np.where(upd, gk, best); bestd = np.where(upd, dist, bestd); bests = np.where(upd, st, bests)
    out.append(pd.DataFrame({"permno": p, "date": cal.date.values, "gvkey": best}))
SA = pd.concat(out, ignore_index=True)
SA.to_parquet(CACHE / "shared_assign.parquet", index=False)
print("shared_assign rows:", len(SA), " permno-days with no assignable gvkey:", int(SA.gvkey.isna().sum()))

mem = pd.read_parquet(P3 / "out/membership.parquet")
lk3, lk4 = set(L3.permno.astype(int)), set(L4.permno.astype(int))
mem["l3"] = mem.permno.astype(int).isin(lk3); mem["l4"] = mem.permno.astype(int).isin(lk4)
yy = [1999, 2000, 2004, 2009, 2014, 2019, 2024]
print("R3000-proxy members linked, share by June year (phase-3 link / phase-4 link):")
print("  ", {y: (round(float(mem[mem.y == y].l3.mean()), 3), round(float(mem[mem.y == y].l4.mean()), 3)) for y in yy})
print("   overall 1999-2024:", round(float(mem[mem.y <= 2024].l3.mean()), 4), "/", round(float(mem[mem.y <= 2024].l4.mean()), 4))
