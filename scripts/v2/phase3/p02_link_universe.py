"""p02: point-in-time identifier link, Russell-3000 proxy membership, event-level attributes (no return outcomes).

Link (gvkey -> permno), frozen in FROZEN_PARAMS.json "link":
  A. Compustat names CUSIP (8) == CRSP dsenames ncusip, accepted only if that permno's ncusip record(s) overlap the
     gvkey's event span [min rdq, max rdq] (the CUSIP identified that security at some point of the firm's sample life).
  B. gvkeys without A: Compustat namesd (security-level, any iid) CUSIP == ncusip with the same overlap rule;
     several candidates -> largest overlap (days), then lowest permno.
  The permno is a permanent CRSP security id, so the link holds across later CUSIP changes (removes D8 survivorship);
  an event is usable only if the permno trades at entry (d0 rule below).
Entry d0: first CRSP trading day >= rdq+1 with non-null dlyret and dlydelflg='N'; valid iff d0 <= rdq+10 (calendar).
Skip-week entry d0_sw: same with window start rdq+8; valid iff d0_sw <= rdq+17.
Russell-3000 proxy: on the last CRSP trading day of June of year Y, securities with a dsenames record valid that day
  with shrcd in (10,11) and exchcd in (1,2,3), ranked by dsf_v2 dlycap (>0); top 3,000 = members for events with rdq in
  [Jul 1 Y, Jun 30 Y+1]. (June 2025 uses CIZ equivalents because legacy dsenames ends 2024-12-31; D1 counts only.)
CRSP common stock at the event (B1 universe): dsenames record valid on rdq with shrcd in (10,11), exchcd in (1,2,3).
Writes phase3/out/link.parquet, membership.parquet, events.parquet.
"""
import sys
sys.dont_write_bytecode = True
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from p3common import OUT, PARENT, DUMP, DSF  # noqa: E402

con = duckdb.connect()
con.execute("PRAGMA threads=8")
con.execute("SET memory_limit='10GB'")
E = pd.read_parquet(OUT / "panel_ext.parquet")
E["rid"] = np.arange(len(E))
span = E.groupby("gvkey").agg(cusip8=("cusip8", "first"), r0=("rdq", "min"), r1=("rdq", "max")).reset_index()
con.register("span", span)
con.execute(f"""CREATE TABLE nm AS SELECT permno::INT permno, namedt::DATE namedt, nameendt::DATE nameendt, ncusip,
    TRY_CAST(shrcd AS INT) shrcd, TRY_CAST(exchcd AS INT) exchcd FROM read_csv('{DUMP}crsp_a_stock.dsenames.csv.gz', header=true, all_varchar=true)""")
con.execute(f"CREATE TABLE nd AS SELECT gvkey, iid, substr(cusip,1,8) c8 FROM read_csv('{DUMP}comp_na_daily_all.namesd.csv.gz', header=true, all_varchar=true)")

# ---------- link ----------
A = con.execute("""
  SELECT s.gvkey, n.permno, min(n.namedt) nd0, max(n.nameendt) nd1, s.r0, s.r1
  FROM span s JOIN nm n ON n.ncusip = s.cusip8 GROUP BY ALL""").df()
A["ov"] = (np.minimum(A.nd1, A.r1) - np.maximum(A.nd0, A.r0)).dt.days
print("A: gvkeys with names-CUSIP match:", A.gvkey.nunique(), " with span overlap:", int((A.ov >= 0).sum()),
      " multi-permno:", int(A.groupby("gvkey").size().gt(1).sum()))
A = A[A.ov >= 0].assign(step="A")
rest = span[~span.gvkey.isin(A.gvkey)]
con.register("rest", rest)
B = con.execute("""
  SELECT s.gvkey, n.permno, min(n.namedt) nd0, max(n.nameendt) nd1, s.r0, s.r1
  FROM rest s JOIN nd d ON d.gvkey = s.gvkey JOIN nm n ON n.ncusip = d.c8 GROUP BY ALL""").df()
B["ov"] = (np.minimum(B.nd1, B.r1) - np.maximum(B.nd0, B.r0)).dt.days
B = B[B.ov >= 0].sort_values(["gvkey", "ov", "permno"], ascending=[True, False, True], kind="mergesort")
nb_multi = int(B.groupby("gvkey").size().gt(1).sum())
B = B.drop_duplicates("gvkey", keep="first").assign(step="B")
print("B: extra gvkeys via namesd security CUSIPs:", len(B), " (had >1 candidate:", nb_multi, ")")
L = pd.concat([A, B], ignore_index=True)[["gvkey", "permno", "step", "nd0", "nd1", "ov"]]
assert L.gvkey.is_unique
L.to_parquet(OUT / "link.parquet", index=False)
print("linked gvkeys:", len(L), "of", len(span), "; permnos shared by >1 gvkey:", int(L.permno.duplicated(keep=False).sum()))

# ---------- Russell-3000 proxy membership ----------
con.execute(f"CREATE TABLE jd AS SELECT year(date) y, max(date) d FROM '{DSF}' WHERE month(date)=6 GROUP BY 1")
mem = con.execute(f"""
  WITH c AS (
    SELECT j.y, s.permno, s.dlycap FROM jd j JOIN '{DSF}' s ON s.date = j.d
    JOIN nm n ON n.permno = s.permno AND j.d BETWEEN n.namedt AND n.nameendt
    WHERE j.y <= 2024 AND n.shrcd IN (10, 11) AND n.exchcd IN (1, 2, 3) AND s.dlycap > 0
    UNION ALL
    SELECT j.y, s.permno, s.dlycap FROM jd j JOIN '{DSF}' s ON s.date = j.d
    WHERE j.y = 2025 AND s.sharetype='NS' AND s.securitytype='EQTY' AND s.securitysubtype='COM' AND s.usincflg='Y'
      AND s.issuertype IN ('CORP','ACOR') AND s.primaryexch IN ('N','A','Q') AND s.dlycap > 0)
  SELECT y, permno, dlycap, rk FROM (SELECT *, row_number() OVER (PARTITION BY y ORDER BY dlycap DESC, permno) rk FROM c)
  WHERE rk <= 3000""").df()
mem.to_parquet(OUT / "membership.parquet", index=False)
cut = mem[mem.rk == 3000].set_index("y")["dlycap"] / 1000
print("R3000 proxy: years", mem.y.min(), "-", mem.y.max(), " members/yr", mem.groupby("y").size().unique().tolist(),
      " cutoff cap $M (rank 3000) 1999/2008/2016/2024:", [round(float(cut.get(y, np.nan)), 0) for y in (1999, 2008, 2016, 2024)])

# ---------- events ----------
ev = E.merge(L[["gvkey", "permno", "step"]], on="gvkey", how="left")
con.register("ev", ev[["rid", "permno", "rdq"]].dropna(subset=["permno"]).astype({"permno": "int64"}))
con.execute(f"CREATE TABLE d AS SELECT permno, date, dlycap FROM '{DSF}' WHERE dlyret IS NOT NULL AND dlydelflg='N' AND permno IN (SELECT DISTINCT permno FROM ev)")
att = con.execute("""
  WITH a AS (SELECT e.rid, x.date d0, x.dlycap cap_d0 FROM ev e ASOF JOIN d x ON x.permno = e.permno AND x.date >= e.rdq + INTERVAL 1 DAY),
       b AS (SELECT e.rid, x.date d0_sw FROM ev e ASOF JOIN d x ON x.permno = e.permno AND x.date >= e.rdq + INTERVAL 8 DAY),
       c AS (SELECT e.rid, max(CASE WHEN n.shrcd IN (10,11) AND n.exchcd IN (1,2,3) THEN 1 ELSE 0 END) common_rdq, count(n.permno) n_rec
             FROM ev e LEFT JOIN nm n ON n.permno = e.permno AND e.rdq BETWEEN n.namedt AND n.nameendt GROUP BY 1)
  SELECT e.rid, a.d0, a.cap_d0, b.d0_sw, c.common_rdq, c.n_rec FROM ev e LEFT JOIN a USING (rid) LEFT JOIN b USING (rid) LEFT JOIN c USING (rid)""").df()
ev = ev.merge(att, on="rid", how="left")
ev["d0"] = pd.to_datetime(ev["d0"]); ev["d0_sw"] = pd.to_datetime(ev["d0_sw"])
ev["valid_entry"] = ev["d0"].notna() & ((ev["d0"] - ev["rdq"]).dt.days <= 10)
ev["valid_entry_sw"] = ev["d0_sw"].notna() & ((ev["d0_sw"] - ev["rdq"]).dt.days <= 17)
ev["cap_d0_mil"] = ev["cap_d0"] / 1000.0
# 2025 events (beyond legacy dsenames): CIZ common-stock flags at d0 (D1 counts only)
late = ev["rdq"] > "2024-12-31"
if late.any():
    con.register("ev25", ev.loc[late & ev.d0.notna(), ["rid", "permno", "d0"]].astype({"permno": "int64"}))
    f25 = con.execute(f"""SELECT e.rid, max(CASE WHEN s.sharetype='NS' AND s.securitytype='EQTY' AND s.securitysubtype='COM' AND s.usincflg='Y'
            AND s.issuertype IN ('CORP','ACOR') AND s.primaryexch IN ('N','A','Q') THEN 1 ELSE 0 END) c25
            FROM ev25 e JOIN '{DSF}' s ON s.permno = e.permno AND s.date = e.d0 GROUP BY 1""").df()
    ev = ev.merge(f25, on="rid", how="left")
    ev.loc[late, "common_rdq"] = ev.loc[late, "c25"]
    ev = ev.drop(columns=["c25"])
ev["common_rdq"] = ev["common_rdq"].fillna(0).astype(bool)
ev["mem_year"] = np.where(ev["rdq"].dt.month >= 7, ev["rdq"].dt.year, ev["rdq"].dt.year - 1)
ms = set(zip(mem.y.astype(int), mem.permno.astype(int)))
ev["in_r3000"] = [(int(y), int(p)) in ms if pd.notna(p) else False for y, p in zip(ev["mem_year"], ev["permno"])]
ev.to_parquet(OUT / "events.parquet", index=False)

# ---------- diagnostics ----------
p0 = ev[ev.in_phase0 & (ev.rdq <= "2024-12-31")]
print("\nphase-0 events (rdq<=2024):", len(p0))
print("  linked:", int(p0.permno.notna().sum()), " valid entry:", int(p0.valid_entry.sum()),
      " in R3000 proxy & valid entry:", int((p0.valid_entry & p0.in_r3000).sum()),
      " CRSP common at rdq & valid entry:", int((p0.valid_entry & p0.common_rdq).sum()))
dd = (p0["d0"] - p0["rdq"]).dt.days
print("  d0 - rdq (days) quantiles among linked with d0:", dd.quantile([0.5, 0.9, 0.99, 0.999]).to_dict(),
      " share > 10:", round(float((dd > 10).mean()), 4))
u = p0[p0.valid_entry & p0.in_r3000]
print("  R3000 universe: Compustat mcap NaN share:", round(float((u.cshoq * u.prccq).isna().mean()), 5),
      " lookahead rows:", int(u.lookahead.sum()), " gvkeys:", u.gvkey.nunique())
pr = pd.read_parquet(PARENT / "panel_ret.parquet", columns=["gvkey", "datadate", "rdq", "car_180", "pcar_180", "permno"])
m = p0.merge(pr, on=["gvkey", "datadate", "rdq"], how="left", suffixes=("", "_v2"))
print("  vs repo CUSIP link (car_180 non-null):", int(m.car_180.notna().sum()), " | vs phase-1 hdrcusip permno link (pcar_180):",
      int(m.pcar_180.notna().sum()), " | phase-3 linked & valid entry:", int(m.valid_entry.sum()))
print("  repo-linked events NOT valid in phase-3 link:", int((m.car_180.notna() & ~m.valid_entry).sum()),
      " phase-3 valid but not repo-linked:", int((~m.car_180.notna() & m.valid_entry).sum()))
same = m.permno.notna() & m.permno_v2.notna()
print("  permno agreement with phase-1 hdrcusip link where both exist:", round(float((m.loc[same, 'permno'] == m.loc[same, 'permno_v2']).mean()), 5))
# Step-0 quantification: repo CUSIP-link entry day (first CUSIP-series day >= rdq+1) more than 10 days after rdq
con.register("pc", pr.assign(rid=np.arange(len(pr)))[["rid", "rdq", "car_180"]].merge(
    pd.read_parquet(PARENT / "panel_rebuild.parquet", columns=["cusip8"]).assign(rid=np.arange(len(pr))), on="rid"))
late_entry = con.execute(f"""WITH s AS (SELECT DISTINCT cusip8, date FROM '{DSF}' WHERE dlyret IS NOT NULL)
   SELECT count(*) n, sum(CASE WHEN date_diff('day', p.rdq, x.date) > 10 THEN 1 ELSE 0 END) late
   FROM pc p ASOF JOIN s x ON x.cusip8 = p.cusip8 AND x.date >= p.rdq + INTERVAL 1 DAY WHERE p.car_180 IS NOT NULL""").fetchall()
print("  [Step 0] repo/phase-1 CUSIP-link CARs whose first return-series day is > rdq+10:", late_entry)
