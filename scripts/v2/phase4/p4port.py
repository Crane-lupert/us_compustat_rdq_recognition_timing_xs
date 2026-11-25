"""Phase 4 portfolio machinery shared by R1 and R3 (FROZEN_PARAMS "returns", "costs_common", "inference")."""
import sys
sys.dont_write_bytecode = True

import numpy as np
import pandas as pd

from p4common import DSF, BIDASK, LAST_DAY, FC, borrow_bps_vec, ff_regress, load_calendar

CAL = load_calendar()
DCAL = CAL.assign(dcal=CAL.date.diff().dt.days.fillna(1).astype(int))[["date", "dcal"]]


def pos_days(c, pos):
    """pos: pid, permno, entry, exit (dates). Returns pid, date, r, cap_lag for entry < date <= min(exit, LAST_DAY)
    with a non-null return (delisting row included). cap_lag = dlycap of the permno's previous dsf row."""
    p = pos[["pid", "permno", "entry", "exit"]].copy()
    p["exit"] = p["exit"].where(p["exit"] <= LAST_DAY, LAST_DAY)
    c.register("pos_df", p)
    c.execute("CREATE OR REPLACE TEMP TABLE pos AS SELECT pid::BIGINT pid, permno::BIGINT permno, entry::DATE entry, exit::DATE exit FROM pos_df")
    c.unregister("pos_df")
    c.execute(f"""CREATE OR REPLACE TEMP TABLE px AS
        SELECT permno::BIGINT permno, date, dlyret r, lag(dlycap) OVER (PARTITION BY permno ORDER BY date) cap_lag
        FROM '{DSF}' WHERE permno IN (SELECT DISTINCT permno FROM pos) AND date >= DATE '1999-06-01' AND date <= DATE '2024-12-31'""")
    d = c.execute("""SELECT p.pid, x.date, x.r, x.cap_lag FROM pos p JOIN px x
                     ON x.permno = p.permno AND x.date > p.entry AND x.date <= p.exit WHERE x.r IS NOT NULL""").df()
    c.execute("DROP TABLE px")
    d["date"] = pd.to_datetime(d["date"]).astype("datetime64[ns]")
    d = d.sort_values(["pid", "date"], kind="mergesort").reset_index(drop=True)
    g = d.groupby("pid", sort=False)
    d["first"] = g.cumcount() == 0
    d["last"] = g.cumcount(ascending=False) == 0
    return d.merge(DCAL, on="date", how="left")


def quoted_spreads(c, pairs):
    """pairs: permno, date -> qs (NaN if no valid closing quote)."""
    q = pairs[["permno", "date"]].drop_duplicates().copy()
    q["date"] = pd.to_datetime(q["date"]).dt.date
    c.register("qq", q)
    r = c.execute(f"""SELECT q.permno::BIGINT permno, q.date, (b.ask - b.bid) / ((b.ask + b.bid) / 2) qs
                      FROM qq q JOIN '{BIDASK}' b ON b.permno = q.permno AND b.date = q.date
                      WHERE b.bid > 0 AND b.ask >= b.bid AND (b.ask - b.bid) / ((b.ask + b.bid) / 2) < 1""").df()
    c.unregister("qq")
    r["date"] = pd.to_datetime(r["date"]).astype("datetime64[ns]")
    return r


def attach_costs(c, ev, pdays, leg_col=None, short_mask=None):
    """Per-position cost inputs (FROZEN costs_common). ev: pid, permno, entry, cap_entry (+ leg_col). pdays from pos_days.
    Adds to pdays: cost = half qs at entry on the first day + half qs at exit on the last day (+ borrow for short positions)."""
    last = pdays[pdays["last"]][["pid", "date"]].rename(columns={"date": "d_last"})
    e = ev.merge(last, on="pid", how="inner").copy()
    qin = quoted_spreads(c, e.rename(columns={"entry": "date"})[["permno", "date"]]).rename(columns={"date": "entry", "qs": "qs_in"})
    qout = quoted_spreads(c, e.rename(columns={"d_last": "date"})[["permno", "date"]]).rename(columns={"date": "d_last", "qs": "qs_out"})
    e = e.merge(qin, on=["permno", "entry"], how="left").merge(qout, on=["permno", "d_last"], how="left")
    miss_in, miss_out = float(e.qs_in.isna().mean()), float(e.qs_out.isna().mean())
    e["qs_in2"] = e["qs_in"].fillna(e["qs_out"])
    e["qs_out2"] = e["qs_out"].fillna(e["qs_in"])
    grp = [leg_col] if leg_col else []
    e["yr"] = pd.to_datetime(e["entry"]).dt.year
    for col in ("qs_in2", "qs_out2"):
        e[col] = e[col].fillna(e.groupby(grp + ["yr"])[col].transform("median") if grp else e.groupby("yr")[col].transform("median"))
        e[col] = e[col].fillna(e.groupby(grp)[col].transform("median") if grp else e[col].median())
    e["bps"] = borrow_bps_vec(e["cap_entry"].values / 1000.0)
    is_short = np.zeros(len(e), dtype=bool) if short_mask is None else short_mask(e)
    e["is_short"] = is_short
    pdays = pdays.merge(e[["pid", "qs_in2", "qs_out2", "bps", "is_short"]], on="pid", how="inner")
    pdays["c_spread"] = np.where(pdays["first"], pdays.qs_in2 / 2, 0.0) + np.where(pdays["last"], pdays.qs_out2 / 2, 0.0)
    pdays["c_borrow"] = np.where(pdays.is_short, pdays.bps / 1e4 * pdays.dcal / 365.0, 0.0)
    pdays["cost"] = pdays.c_spread + pdays.c_borrow
    info = dict(qs_missing_in=miss_in, qs_missing_out=miss_out, qs_in_mean=float(e.qs_in2.mean()), qs_out_mean=float(e.qs_out2.mean()),
                bps_mean=float(e.bps.mean()))
    return pdays, e, info


def daily(pdays, mask=None, cols=("r",)):
    """EW daily portfolio over the selected position-days: n (stocks with a return), mean of each col; VW of r with cap_lag."""
    d = pdays if mask is None else pdays[mask]
    g = d.groupby("date")
    out = pd.DataFrame({"n": g.size()})
    for col in cols:
        out[col] = g[col].mean()
    w = d[d.cap_lag.notna() & (d.cap_lag > 0)]
    gw = w.assign(wr=w.cap_lag * w.r).groupby("date")
    out["vw"] = gw.wr.sum() / gw.cap_lag.sum()
    out["n_vw"] = gw.size()
    return out


def alpha_rows(test_id, sample, series, ff, excess, n=None, min_n=10, extra=None):
    """regress the daily series (days with n >= min_n) on FF5+UMD; returns list of result rows."""
    s = series if n is None else series[n >= min_n]
    s = s.dropna()
    r = ff_regress(s, ff, excess=excess, lags=5)
    rows = [dict(test_id=test_id, sample=sample, stat=k, value=v) for k, v in
            dict(alpha_bp=r["alpha"] * 1e4, t=r["t"], n_days=r["n"], mean_bp=r["mean"] * 1e4, t_mean=r["t_mean"],
                 alpha_ann_pct=r["alpha"] * 252 * 100, r2=r.get("r2", np.nan),
                 **{f"b_{f}": r.get(f"b_{f}", np.nan) for f in FC}).items()]
    if n is not None:
        nn = n[n >= min_n]
        rows += [dict(test_id=test_id, sample=sample, stat="mean_n_stocks_days_used", value=float(nn.mean()) if len(nn) else np.nan),
                 dict(test_id=test_id, sample=sample, stat="mean_n_stocks_all_days", value=float(n.mean()) if len(n) else np.nan),
                 dict(test_id=test_id, sample=sample, stat="n_days_any_position", value=int(len(n)))]
    for k, v in (extra or {}).items():
        rows.append(dict(test_id=test_id, sample=sample, stat=k, value=v))
    return rows
