"""s03 (R1): short firms that passed E + 5 trading days without announcing (FROZEN_PARAMS "R1").
Inputs: out/r1_events_o{5,1,10}.parquet, out/r1_events_o5_literal.parquet (EXPLORATORY), dsf_v2 / bidask, FF5+UMD daily (dump).
Writes out/r1_event_table.parquet/.csv (main events with holding returns), out/daily_r1.parquet, out/results_r1.csv,
cache/universe_ew.parquet; log on stdout.
"""
import sys
sys.dont_write_bytecode = True
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

sys.path.insert(0, str(Path(__file__).resolve().parent))
from p4common import OUT, CACHE, P3, DSF, HALF_SPLIT, con, load_ff_daily, load_calendar, verdict  # noqa: E402
from p4port import pos_days, attach_costs, daily, alpha_rows  # noqa: E402

c = con()
ff = load_ff_daily()
RF = ff.set_index("date")["rf"]
cal = load_calendar()
CD = cal.date.values.astype("datetime64[ns]")


def cluster_t(y, g):
    y = np.asarray(y, float); ok = np.isfinite(y); y = y[ok]; g = np.asarray(g)[ok]
    n = len(y)
    if n < 3:
        return dict(n=n, mean=np.nan, t=np.nan, G=0)
    m = y.mean(); e = y - m
    s = pd.Series(e).groupby(g).sum().values; G = len(s)
    v = (s ** 2).sum() / n ** 2 * G / (G - 1)
    return dict(n=n, mean=float(m), t=float(m / np.sqrt(v)), G=int(G))


# ---------------- universe equal-weight benchmark (all members with a return row that day)
fu = CACHE / "universe_ew.parquet"
if not fu.exists():
    c.execute(f"CREATE OR REPLACE TABLE mem AS SELECT y::INT y, permno::BIGINT permno FROM '{(P3 / 'out/membership.parquet').as_posix()}' WHERE y <= 2024")
    U = c.execute(f"""SELECT s.date, count(*) n_u, avg(s.dlyret) univ FROM '{DSF}' s JOIN mem m ON m.permno = s.permno
                      AND s.date >= make_date(m.y, 7, 1) AND s.date <= make_date(m.y + 1, 6, 30)
                      WHERE s.date BETWEEN DATE '2000-01-01' AND DATE '2024-12-31' AND s.dlyret IS NOT NULL GROUP BY 1""").df()
    U["date"] = pd.to_datetime(U["date"]).astype("datetime64[ns]")
    U.sort_values("date").to_parquet(fu, index=False)
U = pd.read_parquet(fu)
U["date"] = pd.to_datetime(U["date"]).astype("datetime64[ns]")
UNIV = U.set_index("date")["univ"]

rows, daily_out = [], []
VARIANTS = [("R1_main", "o5"), ("R1_entry_E+1", "o1"), ("R1_entry_E+10", "o10"), ("R1_literal_rule_EXPLORATORY", "o5_literal")]
for test_id, sfx in VARIANTS:
    ev = pd.read_parquet(OUT / f"r1_events_{sfx}.parquet")
    for col in ("E", "entry", "exit", "rdq_next", "rdq_prev"):
        ev[col] = pd.to_datetime(ev[col]).astype("datetime64[ns]")
    ev["pid"] = ev["eid"]
    ev["d_ann"] = pd.NaT
    k = np.searchsorted(CD, ev["rdq_next"].values.astype("datetime64[ns]"), side="left")
    okk = ev.rdq_next.notna().values & (k < len(CD))
    ev.loc[okk, "d_ann"] = CD[k[okk]]
    ev["d_ann"] = pd.to_datetime(ev["d_ann"]).astype("datetime64[ns]")
    pdays = pos_days(c, ev[["pid", "permno", "entry", "exit"]])
    pdays, ecost, info = attach_costs(c, ev[["pid", "permno", "entry", "cap_entry"]], pdays, short_mask=lambda e: np.ones(len(e), dtype=bool))
    pdays = pdays.merge(ev[["pid", "d_ann", "exit_reason", "rk", "entry"]], on="pid", how="left")
    pdays["state"] = np.where(pdays.d_ann.notna() & (pdays.date >= pdays.d_ann), "ann", "wait")
    pdays["rf"] = RF.reindex(pdays.date).values
    pdays["rx"] = pdays.r - pdays.rf
    pdays["rx_wait"] = np.where(pdays.state == "wait", pdays.rx, 0.0)
    pdays["rx_ann"] = np.where(pdays.state == "ann", pdays.rx, 0.0)
    pdays["rx_notann"] = np.where(pdays.exit_reason.isin(["40d", "delist"]), pdays.rx, 0.0)
    pdays["rx_annexit"] = np.where(pdays.exit_reason == "announce", pdays.rx, 0.0)
    pdays["h1"] = pdays.entry < HALF_SPLIT
    print(f"\n[{test_id}] events {len(ev):,}; with >= 1 return day {pdays.pid.nunique():,}; position-days {len(pdays):,}; "
          f"cost inputs {', '.join(f'{k} {v:.4f}' for k, v in info.items())}", flush=True)

    # event-level holding returns (descriptive)
    lg = np.log1p(pdays.r.clip(lower=-0.999999))
    evr = pd.DataFrame({"pid": pdays.pid, "lg": lg, "w": np.where(pdays.state == "wait", lg, 0.0), "a": np.where(pdays.state == "ann", lg, 0.0),
                        "c": pdays.cost}).groupby("pid").agg(lg=("lg", "sum"), w=("w", "sum"), a=("a", "sum"), cost=("c", "sum"), n_ret_days=("lg", "size"))
    evr["ret_hold"], evr["ret_wait"], evr["ret_ann"] = np.expm1(evr.lg), np.expm1(evr.w), np.expm1(evr.a)
    ev = ev.merge(evr[["ret_hold", "ret_wait", "ret_ann", "cost", "n_ret_days"]], left_on="pid", right_index=True, how="left")
    ev = ev.merge(ecost[["pid", "qs_in", "qs_out", "qs_in2", "qs_out2", "bps"]], on="pid", how="left")

    samples = {"full": None, "h1_2000_2012": pdays.h1.values, "h2_2013_2024": ~pdays.h1.values}
    for sname, m in samples.items():
        P = daily(pdays, m, cols=("r", "cost", "rx_wait", "rx_ann", "rx_notann", "rx_annexit"))
        P["rf"] = RF.reindex(P.index).values
        P["univ"] = UNIV.reindex(P.index).values
        rows += alpha_rows(test_id, sname, P.r, ff, excess=True, n=P.n,
                           extra=dict(n_events=int(len(ev) if m is None else ev[(ev.entry < HALF_SPLIT) == (sname.startswith("h1"))].shape[0])))
        if test_id in ("R1_main", "R1_literal_rule_EXPLORATORY"):
            used = P.n >= 10
            short_net = -(P.r - P.rf) - P.cost
            rows += alpha_rows(test_id + "__short_net_of_costs", sname, short_net[used], ff, excess=False,
                               extra=dict(mean_cost_bp_per_day=float(P.cost[used].mean() * 1e4)))
            rows += alpha_rows(test_id + "__short_gross", sname, -(P.r - P.rf)[used], ff, excess=False)
        if test_id == "R1_main":
            used = P.n >= 10
            rows += alpha_rows("R1_main__minus_universe_EW", sname, (P.r - P.univ)[used], ff, excess=False)
            for comp in ("rx_wait", "rx_ann", "rx_notann", "rx_annexit"):
                rows += alpha_rows(f"R1_main__contrib_{comp}", sname, P[comp][used], ff, excess=False)
            rows += alpha_rows("R1_main__value_weighted", sname, P.vw, ff, excess=True, n=P.n_vw)
            for lo, hi in ((1, 500), (501, 1000), (1001, 3000)):
                mb = pdays.rk.between(lo, hi).values
                mm = mb if m is None else (mb & m)
                Pb = daily(pdays, mm, cols=("r",))
                rows += alpha_rows(f"R1_main__size_rank_{lo}_{hi}", sname, Pb.r, ff, excess=True, n=Pb.n,
                                   extra=dict(n_events=int(pdays[mm].pid.nunique())))
        P = P.reset_index().assign(test_id=test_id, sample=sname)
        daily_out.append(P)

    if test_id == "R1_main":
        # counts and composition (FROZEN R1.with_report.counts / never_announced / decomposition)
        cnt = dict(n_events=len(ev), has_row=int(ev.has_row.sum()), has_row_valid_rdq=int(ev.has_rdq.sum()),
                   no_row=int((~ev.has_row).sum()), exit_announce=int((ev.exit_reason == "announce").sum()),
                   exit_40d=int((ev.exit_reason == "40d").sum()), exit_delist=int((ev.exit_reason == "delist").sum()),
                   never_announced_after=int(ev.never_announced_after.sum()),
                   share_not_announced_within_hold=float(ev.exit_reason.isin(["40d", "delist"]).mean()),
                   share_never_announced=float(ev.never_announced_after.mean()),
                   share_position_days_wait=float((pdays.state == "wait").mean()),
                   share_position_days_notann_events=float(pdays.exit_reason.isin(["40d", "delist"]).mean()),
                   median_hold_ret_days=float(ev.n_ret_days.median()), mean_hold_ret_days=float(ev.n_ret_days.mean()),
                   mean_qs_in=float(ev.qs_in2.mean()), mean_qs_out=float(ev.qs_out2.mean()), mean_borrow_bps=float(ev.bps.mean()),
                   mean_total_cost_per_event=float(ev.cost.mean()))
        for k2, v in cnt.items():
            rows.append(dict(test_id="R1_main__counts", sample="full", stat=k2, value=v))
        for grp_name, gm in (("all", np.ones(len(ev), bool)), ("has_row", ev.has_row.values), ("no_row", ~ev.has_row.values),
                             ("exit_announce", (ev.exit_reason == "announce").values), ("exit_not_announced", ev.exit_reason.isin(["40d", "delist"]).values)):
            e2 = ev[gm]
            for col in ("ret_hold", "ret_wait", "ret_ann"):
                ct = cluster_t(e2[col].values, e2.entry.dt.strftime("%Y-%m-%d").values)
                rows += [dict(test_id=f"R1_main__event_mean_{col}", sample=grp_name, stat="n", value=ct["n"]),
                         dict(test_id=f"R1_main__event_mean_{col}", sample=grp_name, stat="mean_pct", value=ct["mean"] * 100),
                         dict(test_id=f"R1_main__event_mean_{col}", sample=grp_name, stat="t_entry_date_cluster", value=ct["t"])]
        tab = ev[["permno", "gvkey", "rdq_prev", "datadate_prev", "fqtr", "E", "entry", "exit", "exit_reason", "rdq_next", "has_row", "has_rdq",
                  "rdq_cur", "never_announced_after", "prc_entry", "cap_entry", "rk", "n_ret_days", "ret_hold", "ret_wait", "ret_ann",
                  "qs_in", "qs_out", "bps", "cost"]]
        tab.to_parquet(OUT / "r1_event_table.parquet", index=False)
        tab.to_csv(OUT / "r1_event_table.csv", index=False)

R = pd.DataFrame(rows)
R.to_csv(OUT / "results_r1.csv", index=False)
pd.concat(daily_out, ignore_index=True).to_parquet(OUT / "daily_r1.parquet", index=False)

pd.set_option("display.width", 250)
key = R[R.stat.isin(["alpha_bp", "t", "n_days", "mean_n_stocks_days_used", "n_events"])].pivot_table(
    index=["test_id", "sample"], columns="stat", values="value", aggfunc="first")
print("\n" + key.round(3).to_string())
m = R[(R.test_id == "R1_main") & (R.stat == "alpha_bp")].set_index("sample").value
tt = R[(R.test_id == "R1_main") & (R.stat == "t") & (R["sample"] == "full")].value.iloc[0]
print("\nR1 verdict (expected sign -):", verdict(tt, -1, m["h1_2000_2012"], m["h2_2013_2024"]))
print("\n" + R[R.test_id.str.startswith("R1_main__counts") | R.test_id.str.startswith("R1_main__event_mean")].to_string(index=False))
