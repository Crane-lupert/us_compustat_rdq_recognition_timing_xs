"""s06: implementation self-checks (look-ahead, survivorship, double counting, delisting returns) and an independent
recomputation of the three primary daily series with a separate code path (plain SQL from the saved event tables).
Writes out/qa_checks.csv; log on stdout.
"""
import sys
sys.dont_write_bytecode = True
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from p4common import OUT, CACHE, P3, DSF, LAST_DAY, con, load_ff_daily, ff_regress, load_calendar  # noqa: E402

c = con()
cal = load_calendar()
CD = cal.date.values.astype("datetime64[ns]")
ff = load_ff_daily()
chk = []


def add(name, value, ok=None, note=""):
    chk.append(dict(check=name, value=value, pass_=ok, note=note))
    print(f"{name}: {value} {'' if ok is None else ('PASS' if ok else 'FAIL')} {note}", flush=True)


# ---------------- R1: entry decision uses no rdq after entry; slots from prior-year records
ev = pd.read_parquet(OUT / "r1_event_table.parquet")
for col in ("E", "entry", "exit", "rdq_prev", "rdq_next", "datadate_prev"):
    ev[col] = pd.to_datetime(ev[col]).astype("datetime64[ns]")
V = pd.read_parquet(CACHE / "ann_valid.parquet")
V["rdq"] = pd.to_datetime(V["rdq"]).astype("datetime64[ns]"); V["datadate"] = pd.to_datetime(V["datadate"]).astype("datetime64[ns]")
m = ev[["permno", "gvkey", "E", "entry", "datadate_prev", "rdq_next"]].reset_index().merge(V[["gvkey", "rdq", "datadate"]], on="gvkey", how="left")
win = m[(m.rdq > m.E - pd.Timedelta(days=30)) & (m.rdq <= m.entry)]
add("R1 events with a valid rdq in (E-30, entry]", int(win["index"].nunique()), int(win["index"].nunique()) == 0)
slotq = m[(m.datadate >= m.datadate_prev + pd.DateOffset(months=12) - pd.Timedelta(days=15)) & (m.rdq <= m.entry)]
add("R1 events whose slot quarter was announced on/before entry", int(slotq["index"].nunique()), int(slotq["index"].nunique()) == 0)
nxt = m[m.rdq > m.entry].groupby("index").rdq.min()
same = (ev.rdq_next.reindex(nxt.index) == nxt).mean() if len(nxt) else np.nan
add("R1 rdq_next = first valid rdq after entry (share)", float(same), bool(same == 1.0))
k_e = np.searchsorted(CD, ev.entry.values.astype("datetime64[ns]")); kE = np.searchsorted(CD, ev.E.values.astype("datetime64[ns]"))
add("R1 entry = E + 5 trading days (share)", float(np.mean(k_e - kE == 5)), bool(np.all(k_e - kE == 5)))
Eraw = ev.rdq_prev + pd.DateOffset(years=1)
kk = np.searchsorted(CD, Eraw.values.astype("datetime64[ns]"), side="left")
add("R1 E = first trading day >= prior-year rdq + 1 year (share)", float(np.mean(CD[kk] == ev.E.values)), bool(np.all(CD[kk] == ev.E.values)))
add("R1 events without a current-year Compustat row (survivorship check: slots need no current row)", int((~ev.has_row).sum()), True)
gap = (ev.rdq_prev - ev.datadate_prev).dt.days
add("R1 prior-year gap within 1..120 days (share)", float(gap.between(1, 120).mean()), bool(gap.between(1, 120).all()))

# universe: June ranking day precedes entry
mem_day = pd.to_datetime(dict(year=ev.entry.dt.year.where(ev.entry.dt.month >= 7, ev.entry.dt.year - 1), month=6, day=30))
add("R1 membership ranking date (<= Jun 30 of membership year) before entry (share)", float((mem_day < ev.entry).mean()), bool((mem_day < ev.entry).all()))

# ---------------- independent recomputation of the R1 main daily EW series (plain SQL)
c.register("e1", ev[["permno", "entry", "exit"]].assign(entry=ev.entry.dt.date, exit=ev.exit.clip(upper=LAST_DAY).dt.date))
r1 = c.execute(f"""SELECT s.date, count(*) n, avg(s.dlyret) r, count(DISTINCT s.permno) np, sum((s.dlydelflg = 'Y')::INT) ndel
                   FROM e1 e JOIN '{DSF}' s ON s.permno = e.permno AND s.date > e.entry AND s.date <= e.exit
                   WHERE s.dlyret IS NOT NULL GROUP BY 1 ORDER BY 1""").df()
r1["date"] = pd.to_datetime(r1["date"]).astype("datetime64[ns]")
add("R1 duplicate permno-days in the portfolio", int((r1.n != r1.np).sum()), bool((r1.n == r1.np).all()))
add("R1 delisting-return rows inside holdings", int(r1.ndel.sum()), True)
d1 = pd.read_parquet(OUT / "daily_r1.parquet")
d1 = d1[(d1.test_id == "R1_main") & (d1["sample"] == "full")].set_index("date")
j = r1.set_index("date").join(d1[["n", "r"]], rsuffix="_eng")
add("R1 daily EW: max |SQL - engine|", float((j.r - j.r_eng).abs().max()), bool((j.r - j.r_eng).abs().max() < 1e-12 and (j.n == j.n_eng).all()))
s = r1.set_index("date")
s = s[s.n >= 10].r
a = ff_regress(s, ff, excess=True)
add("R1 main alpha recomputed (bp/day, t)", f"{a['alpha']*1e4:.3f}, {a['t']:.3f}", None)

# ---------------- R2: windows depend only on prior-year dates
A = pd.read_parquet(OUT / "r2_events.parquet")
A["E"] = pd.to_datetime(A["E"]).astype("datetime64[ns]")
S = pd.read_parquet(CACHE / "slots.parquet")
S["E"] = pd.to_datetime(S["E"]).astype("datetime64[ns]")
S = S[S.sched_ok]
mm = A.merge(S[["gvkey", "E", "rdq"]], on=["gvkey", "E"], how="left")
add("R2 A events whose E is an eligible prior-year slot (share)", float(mm.rdq.notna().mean()), bool(mm.rdq.notna().all()))
lead = (mm.E - mm.rdq).dt.days
add("R2 E - prior-year rdq (days) min / max", f"{lead.min()} / {lead.max()}", bool(lead.min() >= 365))
D = pd.read_parquet(OUT / "daily_r2.parquet")
ew = D.s_A2 / D.n_A2 - D.s_N / D.n_N
s = ew[D.n_A2 >= 10]
a = ff_regress(s, ff, excess=False)
add("R2 main alpha recomputed from daily aggregates (bp/day, t)", f"{a['alpha']*1e4:.3f}, {a['t']:.3f}", None)

# ---------------- R3: independent recomputation (plain SQL) of the 20-day LS series
T = pd.read_parquet(OUT / "r3_event_table.parquet")
T = T[T.H == 20].copy()
for col in ("entry", "exit", "rdq", "E"):
    T[col] = pd.to_datetime(T[col]).astype("datetime64[ns]")
kr = np.searchsorted(CD, T.rdq.values.astype("datetime64[ns]"), side="left")
kE3 = np.searchsorted(CD, T.E.values.astype("datetime64[ns]"), side="left")
add("R3 dev_td recomputed equals table (share)", float(np.mean((kr - kE3) == T.dev_td.values)), bool(np.all((kr - kE3) == T.dev_td.values)))
k0 = np.searchsorted(CD, T.entry.values.astype("datetime64[ns]"), side="left")
add("R3 entry = first trading day after rdq (share)", float(np.mean(CD[np.searchsorted(CD, T.rdq.values.astype('datetime64[ns]'), side='right')] == T.entry.values)), None)
c.register("e3", T[["permno", "entry", "exit", "group"]].assign(entry=T.entry.dt.date, exit=T.exit.clip(upper=LAST_DAY).dt.date))
r3 = c.execute(f"""SELECT s.date, e.group grp, count(*) n, avg(s.dlyret) r, count(DISTINCT s.permno) np
                   FROM e3 e JOIN '{DSF}' s ON s.permno = e.permno AND s.date > e.entry AND s.date <= e.exit
                   WHERE s.dlyret IS NOT NULL GROUP BY 1, 2""").df()
r3["date"] = pd.to_datetime(r3["date"]).astype("datetime64[ns]")
add("R3 duplicate permno-days within a leg", int((r3.n != r3.np).sum()), bool((r3.n == r3.np).all()))
P = r3.pivot(index="date", columns="grp", values=["n", "r"])
ok = (P[("n", "EARLY")] >= 10) & (P[("n", "LATE")] >= 10)
ls = (P[("r", "EARLY")] - P[("r", "LATE")])[ok]
a = ff_regress(ls, ff, excess=False)
add("R3 main alpha recomputed (bp/day, t)", f"{a['alpha']*1e4:.3f}, {a['t']:.3f}", None)
both = c.execute(f"""SELECT count(*) FROM (SELECT s.permno, s.date FROM e3 e JOIN '{DSF}' s ON s.permno = e.permno AND s.date > e.entry
                     AND s.date <= e.exit WHERE s.dlyret IS NOT NULL GROUP BY 1, 2 HAVING count(DISTINCT e.group) > 1)""").fetchone()[0]
add("R3 permno-days held in both legs", int(both), int(both) == 0)

pd.DataFrame(chk).to_csv(OUT / "qa_checks.csv", index=False)
