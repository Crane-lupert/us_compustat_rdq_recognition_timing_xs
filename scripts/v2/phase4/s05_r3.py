"""s05 (R3): post-announcement returns, EARLY (>= 5 trading days before E) minus LATE (>= 5 after) (FROZEN_PARAMS "R3").
Inputs: out/r3_events_base.parquet (s02), dsf_v2 / bidask, FF5+UMD daily (dump), IBES surpsum / id (dump), CRSP dsenames (dump).
Writes out/r3_event_table.parquet/.csv, out/daily_r3.parquet, out/results_r3.csv; log on stdout.
"""
import sys
sys.dont_write_bytecode = True
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from p4common import OUT, DUMP, HALF_SPLIT, con, load_ff_daily, verdict  # noqa: E402
from p4port import pos_days, attach_costs, alpha_rows  # noqa: E402

c = con()
ff = load_ff_daily()
RF = ff.set_index("date")["rf"]
B = pd.read_parquet(OUT / "r3_events_base.parquet")
for col in ("datadate", "rdq", "E", "d0", "x20", "x60", "d_delist", "rdq_prev", "dd_prev"):
    B[col] = pd.to_datetime(B[col]).astype("datetime64[ns]")
rows = []
cnt = dict(universe_announcements=len(B), noE=int((B.group == "noE").sum()), share_noE=float((B.group == "noE").mean()),
           MID=int((B.group == "MID").sum()), EARLY_before_overlap=int((B.group == "EARLY").sum()), LATE_before_overlap=int((B.group == "LATE").sum()))

# ---------------- IBES surprise sign (auxiliary split only)
ib = c.execute(f"""
  WITH idm AS (SELECT DISTINCT ticker, cusip FROM read_csv('{DUMP}tr_ibes.id.csv.gz', header=true, all_varchar=true) WHERE cusip IS NOT NULL AND length(cusip) = 8),
       nm AS (SELECT DISTINCT permno::BIGINT permno, ncusip FROM read_csv('{DUMP}crsp_a_stock.dsenames.csv.gz', header=true, all_varchar=true) WHERE ncusip IS NOT NULL),
       tp AS (SELECT DISTINCT i.ticker, n.permno FROM idm i JOIN nm n ON n.ncusip = i.cusip),
       su AS (SELECT ticker, TRY_CAST(pyear AS INT) pyear, TRY_CAST(pmon AS INT) pmon, TRY_CAST(anndats AS DATE) anndats,
                     TRY_CAST(actual AS DOUBLE) actual, TRY_CAST(surpmean AS DOUBLE) surpmean
              FROM read_csv('{DUMP}tr_ibes.surpsum.csv.gz', header=true, all_varchar=true) WHERE measure = 'EPS' AND fiscalp = 'QTR')
  SELECT tp.permno, su.* FROM su JOIN tp USING (ticker) WHERE su.actual IS NOT NULL AND su.surpmean IS NOT NULL""").df()
ib["anndats"] = pd.to_datetime(ib["anndats"]).astype("datetime64[ns]")
E0 = B[B.group.isin(["EARLY", "LATE"])][["permno", "datadate", "rdq"]].drop_duplicates()
E0["pyear"], E0["pmon"] = E0.datadate.dt.year, E0.datadate.dt.month
mt = E0.merge(ib, on=["permno", "pyear", "pmon"], how="inner")
mt["dd"] = (mt.anndats - mt.rdq).dt.days.abs()
mt = mt[mt.dd <= 3].sort_values(["permno", "rdq", "dd"], kind="mergesort").drop_duplicates(["permno", "rdq"], keep="first")
mt["surp"] = np.sign(mt.actual - mt.surpmean)
B = B.merge(mt[["permno", "rdq", "surp"]], on=["permno", "rdq"], how="left")
cnt["ibes_matched_EARLY_LATE"] = int(B[B.group.isin(["EARLY", "LATE"])].surp.notna().sum())
cnt["ibes_match_share_EARLY_LATE"] = float(B[B.group.isin(["EARLY", "LATE"])].surp.notna().mean())

daily_out, tables = [], []
for H in (20, 60):
    ev = B[B.group.isin(["EARLY", "LATE"])].copy()
    ev["exit"] = ev[f"x{H}"]
    ev = ev.sort_values(["permno", "d0", "datadate"], kind="mergesort").reset_index(drop=True)
    keep = np.zeros(len(ev), dtype=bool)
    last_exit = {}
    for i, (p, d0, ex) in enumerate(zip(ev.permno.values, ev.d0.values, ev.exit.values)):
        le = last_exit.get(p)
        if le is None or d0 >= le:
            keep[i] = True
            last_exit[p] = ex
    cnt[f"H{H}_overlap_dropped"] = int((~keep).sum())
    ev = ev[keep].copy()
    ev["pid"] = np.arange(len(ev), dtype=np.int64)
    ev["entry"] = ev["d0"]
    cnt[f"H{H}_EARLY"], cnt[f"H{H}_LATE"] = int((ev.group == "EARLY").sum()), int((ev.group == "LATE").sum())
    pdays = pos_days(c, ev[["pid", "permno", "entry", "exit"]])
    pdays, ecost, info = attach_costs(c, ev[["pid", "permno", "entry", "cap_entry", "group"]], pdays, leg_col="group",
                                      short_mask=lambda e: (e["group"] == "LATE").values)
    for k2, v in info.items():
        cnt[f"H{H}_{k2}"] = v
    pdays = pdays.merge(ev[["pid", "group", "entry", "surp"]], on="pid", how="left")
    pdays["h1"] = pdays.entry < HALF_SPLIT
    print(f"[R3 H={H}] events EARLY {cnt[f'H{H}_EARLY']:,} LATE {cnt[f'H{H}_LATE']:,}; position-days {len(pdays):,}; "
          f"dup (pid,date) {int(pdays.duplicated(['pid', 'date']).sum())}", flush=True)
    dup_pd = int(pdays.merge(ev[["pid", "permno"]], on="pid").duplicated(["permno", "date"]).sum())
    cnt[f"H{H}_duplicate_permno_days"] = dup_pd

    def legs(mask):
        d = pdays if mask is None else pdays[mask]
        out = {}
        for gname in ("EARLY", "LATE"):
            x = d[d.group == gname]
            g = x.groupby("date")
            w = x[x.cap_lag.notna() & (x.cap_lag > 0)]
            gw = w.assign(wr=w.cap_lag * w.r).groupby("date")
            out[gname] = pd.DataFrame({"n": g.size(), "r": g.r.mean(), "cost": g.cost.mean(),
                                       "vw": gw.wr.sum() / gw.cap_lag.sum(), "nv": gw.size()})
        J = out["EARLY"].join(out["LATE"], how="outer", lsuffix="_E", rsuffix="_L")
        for col in ("n_E", "n_L", "nv_E", "nv_L"):
            J[col] = J[col].fillna(0)
        return J

    tag = "R3_main" if H == 20 else "R3_main__hold_60d"
    for sname, m in (("full", None), ("h1_2000_2012", pdays.h1.values), ("h2_2013_2024", ~pdays.h1.values)):
        J = legs(m)
        ok = (J.n_E >= 10) & (J.n_L >= 10)
        ls = (J.r_E - J.r_L)[ok]
        rows += alpha_rows(tag, sname, ls, ff, excess=False,
                           extra=dict(n_events=int(len(ev) if m is None else ev[(ev.entry < HALF_SPLIT) == sname.startswith("h1")].shape[0]),
                                      mean_n_EARLY_days_used=float(J.n_E[ok].mean()), mean_n_LATE_days_used=float(J.n_L[ok].mean())))
        if H == 20:
            rows += alpha_rows("R3_main__leg_EARLY_excess", sname, J.r_E[ok], ff, excess=True)
            rows += alpha_rows("R3_main__leg_LATE_excess", sname, J.r_L[ok], ff, excess=True)
            okv = (J.nv_E >= 10) & (J.nv_L >= 10)
            rows += alpha_rows("R3_main__value_weighted", sname, (J.vw_E - J.vw_L)[okv], ff, excess=False)
            net = (J.r_E - J.cost_E - J.r_L - J.cost_L)[ok]
            rows += alpha_rows("R3_main__net_of_costs", sname, net, ff, excess=False,
                               extra=dict(mean_cost_EARLY_bp_day=float(J.cost_E[ok].mean() * 1e4), mean_cost_LATE_bp_day=float(J.cost_L[ok].mean() * 1e4)))
            for sv, sl in ((1.0, "positive"), (-1.0, "negative")):
                ms = (pdays.surp == sv).values
                Js = legs(ms if m is None else (ms & m))
                oks = (Js.n_E >= 10) & (Js.n_L >= 10)
                rows += alpha_rows(f"R3_main__ibes_surprise_{sl}", sname, (Js.r_E - Js.r_L)[oks], ff, excess=False,
                                   extra=dict(n_EARLY_events=int(ev[(ev.surp == sv) & (ev.group == "EARLY") & ((ev.entry < HALF_SPLIT) == sname.startswith("h1") if m is not None else True)].shape[0]),
                                              n_LATE_events=int(ev[(ev.surp == sv) & (ev.group == "LATE") & ((ev.entry < HALF_SPLIT) == sname.startswith("h1") if m is not None else True)].shape[0])))
        J = J.reset_index().assign(test_id=tag, sample=sname)
        daily_out.append(J)
    # event table (holding returns)
    lg = np.log1p(pdays.r.clip(lower=-0.999999))
    evr = pd.DataFrame({"pid": pdays.pid, "lg": lg, "cost": pdays.cost}).groupby("pid").agg(lg=("lg", "sum"), cost=("cost", "sum"), n_ret_days=("lg", "size"))
    evr["ret_hold"] = np.expm1(evr.lg)
    ev = ev.merge(evr[["ret_hold", "cost", "n_ret_days"]], left_on="pid", right_index=True, how="left")
    ev = ev.merge(ecost[["pid", "qs_in", "qs_out", "bps"]], on="pid", how="left")
    ev["H"] = H
    tables.append(ev[["H", "permno", "gvkey", "datadate", "fqtr", "rdq", "rdq_prev", "E", "dev_td", "group", "entry", "exit", "d_delist",
                      "surp", "rk", "cap_entry", "n_ret_days", "ret_hold", "qs_in", "qs_out", "bps", "cost"]])

for k2, v in cnt.items():
    rows.append(dict(test_id="R3_main__counts", sample="full", stat=k2, value=v))
T = pd.concat(tables, ignore_index=True)
T.to_parquet(OUT / "r3_event_table.parquet", index=False)
T[T.H == 20].to_csv(OUT / "r3_event_table_h20.csv", index=False)
pd.concat(daily_out, ignore_index=True).to_parquet(OUT / "daily_r3.parquet", index=False)
R = pd.DataFrame(rows)
R.to_csv(OUT / "results_r3.csv", index=False)
pd.set_option("display.width", 250)
key = R[R.stat.isin(["alpha_bp", "t", "n_days", "mean_bp", "t_mean"])].pivot_table(index=["test_id", "sample"], columns="stat", values="value", aggfunc="first")
print("\n" + key[["alpha_bp", "t", "mean_bp", "t_mean", "n_days"]].round(3).to_string())
print("\n" + R[R.test_id == "R3_main__counts"].to_string(index=False))
m = R[(R.test_id == "R3_main") & (R.stat == "alpha_bp")].set_index("sample").value
tt = R[(R.test_id == "R3_main") & (R.stat == "t") & (R["sample"] == "full")].value.iloc[0]
print("\nR3 verdict (expected sign +):", verdict(tt, 1, m["h1_2000_2012"], m["h2_2013_2024"]))
