"""Phase 7 shared helpers: trading calendar, universe, abnormal returns over windows, and the two screening statistics.

Stage discipline (PHASE7_SEARCH_PROTOCOL.md section 1): every event carries `stage` = "disc" (even entry year <= 2024),
"conf" (odd entry year <= 2023) or "rec" (2025). `ar_windows` refuses to compute returns for stages that the caller has
not explicitly asked for, so a search script cannot touch the confirmation or record years by accident.
"""
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd

from v2paths import MC_DIR, WRDS_DUMP
HERE = MC_DIR / "phase7"
MC = HERE.parent
ROOT = MC.parent
CACHE = HERE / "cache"
OUT = HERE / "out"
CACHE.mkdir(exist_ok=True)
OUT.mkdir(exist_ok=True)
DUMP = WRDS_DUMP.rstrip("/")
SLIM = (ROOT / "RDQ_cadence" / "dsf_v2_slim.parquet").as_posix()
BIDASK = (ROOT / "RDQ_cadence" / "dsf_v2_bidask.parquet").as_posix()


def con():
    c = duckdb.connect()
    c.execute("SET memory_limit='7GB'")
    c.execute("SET preserve_insertion_order=false")
    return c


def stage_of(dates):
    y = pd.DatetimeIndex(dates).year
    return np.where(y >= 2025, "rec", np.where(y % 2 == 0, "disc", "conf"))


def calendar():
    f = CACHE / "calendar.parquet"
    if not f.exists():
        con().execute(f"COPY (SELECT date, row_number() OVER (ORDER BY date) - 1 AS k FROM (SELECT DISTINCT date FROM '{SLIM}')) TO '{f.as_posix()}' (FORMAT parquet)")
    c = pd.read_parquet(f).sort_values("k")
    c["date"] = pd.to_datetime(c["date"])
    return c.reset_index(drop=True)


def members():
    """June market-cap rank (top 3,000 common stocks) by membership year y: valid from July of y to June of y+1"""
    f = CACHE / "members.parquet"
    if not f.exists():
        con().execute(f"""COPY (
          WITH j AS (SELECT year(date) y, max(date) d FROM '{SLIM}' WHERE month(date) = 6 GROUP BY 1),
               r AS (SELECT j.y, s.permno, row_number() OVER (PARTITION BY j.y ORDER BY s.dlycap DESC) rk
                     FROM j JOIN '{SLIM}' s ON s.date = j.d
                     WHERE s.sharetype='NS' AND s.securitytype='EQTY' AND s.securitysubtype='COM' AND s.usincflg='Y'
                       AND s.issuertype IN ('CORP','ACOR') AND s.primaryexch IN ('N','A','Q') AND s.dlycap > 0)
          SELECT y, permno, rk FROM r WHERE rk <= 3000) TO '{f.as_posix()}' (FORMAT parquet)""")
    return pd.read_parquet(f)


def ret_k():
    """log returns of every stock that was ever a universe member, keyed by the calendar index k (parquet path)"""
    f = CACHE / "ret_k.parquet"
    if not f.exists():
        calendar()
        members()
        con().execute(f"""COPY (SELECT s.permno, c.k, ln(greatest(1 + s.dlyret, 1e-9)) AS lr
                               FROM '{SLIM}' s JOIN '{(CACHE / 'calendar.parquet').as_posix()}' c ON c.date = s.date
                               WHERE s.dlyret IS NOT NULL AND s.date >= DATE '2002-06-01'
                                 AND s.permno IN (SELECT DISTINCT permno FROM '{(CACHE / 'members.parquet').as_posix()}'))
                        TO '{f.as_posix()}' (FORMAT parquet, COMPRESSION zstd)""")
    return f.as_posix()


def bench_clog():
    """cumulative log return of the equal-weighted universe by calendar index k (array aligned with calendar())"""
    f = CACHE / "bench.parquet"
    cal = calendar()
    if not f.exists():
        members()
        con().execute(f"""COPY (SELECT s.date, avg(s.dlyret) AS ew, count(*) AS n
              FROM '{SLIM}' s JOIN '{(CACHE / 'members.parquet').as_posix()}' m
                ON m.permno = s.permno AND m.y = CASE WHEN month(s.date) >= 7 THEN year(s.date) ELSE year(s.date) - 1 END
              WHERE s.dlyret IS NOT NULL AND s.date >= DATE '2002-07-01' GROUP BY 1) TO '{f.as_posix()}' (FORMAT parquet)""")
    b = pd.read_parquet(f)
    b["date"] = pd.to_datetime(b["date"])
    ew = cal.merge(b[["date", "ew"]], on="date", how="left").ew.fillna(0.0).values
    return np.concatenate([[0.0], np.cumsum(np.log1p(ew))])[1:]          # clog[k] = cumulative through day k


def ar_windows(ev, windows, allow=("disc",), exit_col=None):
    """abnormal return (stock minus equal-weighted universe over the same days) for each window.

    ev: eid, permno, k0 (calendar index of the entry day; returns start the next day), stage [, exit_col = last index held]
    windows: list of (name, a, b): days k0+a+1 .. k0+b.  With exit_col an extra window "hold" = k0+1 .. exit is added.
    """
    bad = set(ev.stage.unique()) - set(allow)
    if bad:
        raise RuntimeError(f"stage discipline: events of stage {sorted(bad)} passed to ar_windows with allow={allow}")
    c = con()
    wmax = max(b for _, _, b in windows) if windows else 0
    cols = ["eid", "permno", "k0"] + ([exit_col] if exit_col else [])
    e = ev[cols].copy()
    if exit_col:
        e = e.rename(columns={exit_col: "kx"})
        wmax = max(wmax, int((e.kx - e.k0).max()))
    c.register("ev", e)
    sel = []
    for name, a, b in windows:
        cond = f"r.k > e.k0 + {a} AND r.k <= e.k0 + {b}"
        sel.append(f"sum(r.lr) FILTER (WHERE {cond}) AS s_{name}, max(r.k) FILTER (WHERE {cond}) AS k_{name}, count(*) FILTER (WHERE {cond}) AS n_{name}")
    if exit_col:
        sel.append("sum(r.lr) FILTER (WHERE r.k <= e.kx) AS s_hold, max(r.k) FILTER (WHERE r.k <= e.kx) AS k_hold, count(*) FILTER (WHERE r.k <= e.kx) AS n_hold")
    q = c.execute(f"""SELECT e.eid, {', '.join(sel)} FROM ev e JOIN '{ret_k()}' r
                      ON r.permno = e.permno AND r.k > e.k0 AND r.k <= e.k0 + {wmax} GROUP BY e.eid""").df()
    B = bench_clog()
    out = ev[["eid", "k0"]].merge(q, on="eid", how="left")
    res = pd.DataFrame({"eid": out.eid.values})
    names = [(n, a) for n, a, _ in windows] + ([("hold", 0)] if exit_col else [])
    for name, a in names:
        s, kl = out[f"s_{name}"].values.astype(float), out[f"k_{name}"].values
        ok = ~np.isnan(s)
        ar = np.full(len(out), np.nan)
        k_end = np.where(ok, np.nan_to_num(kl.astype(float), nan=0), 0).astype(int)
        k_beg = (out.k0.values + a).astype(int)
        ar[ok] = (np.expm1(s[ok]) - np.expm1(B[k_end[ok]] - B[k_beg[ok]])) * 100
        res["ar_" + name] = ar
        res["n_" + name] = out[f"n_{name}"].fillna(0).astype(int).values
    return res


def past_returns(ev, windows):
    """raw cumulative returns (percent) over PAST windows only, e.g. ("mom", -252, -21) = days k0-251 .. k0-21.
    These are conditioning variables, not outcomes, so there is no stage restriction; b must be <= 0."""
    assert all(b <= 0 for _, _, b in windows), "past_returns is for windows that end on or before the entry day"
    c = con()
    c.register("ev", ev[["eid", "permno", "k0"]])
    amin = min(a for _, a, _ in windows)
    sel = ", ".join(f"sum(r.lr) FILTER (WHERE r.k > e.k0 + {a} AND r.k <= e.k0 + {b}) AS {n}, count(*) FILTER (WHERE r.k > e.k0 + {a} AND r.k <= e.k0 + {b}) AS n_{n}" for n, a, b in windows)
    q = c.execute(f"""SELECT e.eid, {sel} FROM ev e JOIN '{ret_k()}' r ON r.permno = e.permno AND r.k > e.k0 + {amin} AND r.k <= e.k0 GROUP BY e.eid""").df()
    for n, a, b in windows:
        q[n] = np.where(q["n_" + n] >= 0.6 * (b - a), np.expm1(q[n]) * 100, np.nan)
    return q[["eid"] + [n for n, _, _ in windows]]


def _cluster_var(score, g, G):
    s = np.bincount(g, weights=score, minlength=G)
    return (G / (G - 1)) * np.sum(s * s)


def diff_test(y, x, fe, g):
    """slope of y on a 0/1 flag x with fixed effects fe (integer codes), clustered by g (integer codes).
    Returns (difference, t, n1, n0). NaN in y must be removed by the caller."""
    n1 = int(x.sum())
    n0 = len(x) - n1
    if n1 < 2 or n0 < 2:
        return np.nan, np.nan, n1, n0
    nf = fe.max() + 1
    cnt = np.bincount(fe, minlength=nf)
    yt = y - (np.bincount(fe, weights=y, minlength=nf) / cnt)[fe]
    xt = x - (np.bincount(fe, weights=x, minlength=nf) / cnt)[fe]
    sxx = np.sum(xt * xt)
    if sxx <= 0:
        return np.nan, np.nan, n1, n0
    b = np.sum(xt * yt) / sxx
    u = yt - b * xt
    G = g.max() + 1
    se = np.sqrt(_cluster_var(xt * u, g, G)) / sxx
    return b, (b / se if se > 0 else np.nan), n1, n0


def level_test(y, g):
    """mean of y with cluster-robust t (clusters g)."""
    n = len(y)
    if n < 2:
        return np.nan, np.nan, n
    m = y.mean()
    G = g.max() + 1
    se = np.sqrt(_cluster_var(y - m, g, G)) / n
    return m, (m / se if se > 0 else np.nan), n


def codes(a):
    return pd.factorize(a)[0]


def diff_test_ctrl(y, x, Z, fe, g):
    """as diff_test, with control variables Z (n x p array): y and x are residualized on Z and the fixed effects."""
    n1 = int(x.sum())
    n0 = len(x) - n1
    if n1 < 2 or n0 < 2:
        return np.nan, np.nan, n1, n0
    nf = fe.max() + 1
    cnt = np.bincount(fe, minlength=nf)

    def dm(v):
        return v - (np.bincount(fe, weights=v, minlength=nf) / cnt)[fe]

    Zt = np.column_stack([dm(Z[:, j]) for j in range(Z.shape[1])])
    yt, xt = dm(y), dm(x)
    yt = yt - Zt @ np.linalg.lstsq(Zt, yt, rcond=None)[0]
    xt = xt - Zt @ np.linalg.lstsq(Zt, xt, rcond=None)[0]
    sxx = np.sum(xt * xt)
    if sxx <= 0:
        return np.nan, np.nan, n1, n0
    b = np.sum(xt * yt) / sxx
    u = yt - b * xt
    G = g.max() + 1
    se = np.sqrt(_cluster_var(xt * u, g, G)) / sxx
    return b, (b / se if se > 0 else np.nan), n1, n0
