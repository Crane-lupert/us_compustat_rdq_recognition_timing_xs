"""Phase 4 shared helpers (RDQ, SSRN 6965838; PHASE4_SPEC.md R1/R2/R3). Self-contained; phase 1-3 outputs are read only.
All implementation choices are frozen in phase4/FROZEN_PARAMS.json.
"""
import sys
sys.dont_write_bytecode = True

import json
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats

from v2paths import RDQ_DIR, WRDS_DUMP
P4 = RDQ_DIR / "phase4"
RDQ = P4.parent
P3 = RDQ / "phase3"
OUT, LOGS, CACHE, TMP = P4 / "out", P4 / "logs", P4 / "cache", P4 / "tmp"
DUMP = WRDS_DUMP
DSF = (RDQ / "dsf_v2_slim.parquet").as_posix()
BIDASK = (RDQ / "dsf_v2_bidask.parquet").as_posix()
FUNDQ = DUMP + "comp_na_daily_all.fundq.csv.gz"
LAST_DAY = pd.Timestamp("2024-12-31")          # CRSP used through 2024-12
FIRST_ENTRY = pd.Timestamp("2000-01-01")
HALF_SPLIT = pd.Timestamp("2013-01-01")        # first half: entry < 2013-01-01
FC = ["mktrf", "smb", "hml", "rmw", "cma", "umd"]
BORROW_SCHEDULE = [(10_000.0, np.inf, 25.0), (2_000.0, 10_000.0, 50.0), (300.0, 2_000.0, 200.0),
                   (100.0, 300.0, 800.0), (0.0, 100.0, 2000.0)]   # = phase3 p3common (repo borrow overlay table)
CRIT = 2.39                                     # Bonferroni 3 tests, two-sided 5%


def frozen():
    f = Path(__file__).resolve().parent / "FROZEN_PARAMS.json"
    return json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}


def con(mem="8GB", threads=8):
    c = duckdb.connect()
    c.execute(f"PRAGMA threads={threads}")
    c.execute(f"SET memory_limit='{mem}'")
    c.execute(f"SET temp_directory='{TMP.as_posix()}'")
    c.execute("SET preserve_insertion_order=false")
    return c


def borrow_bps_vec(cap_mil):
    cap = np.asarray(cap_mil, dtype=float)
    out = np.full(cap.shape, 2000.0)
    for lo, hi, b in BORROW_SCHEDULE:
        out = np.where((cap >= lo) & (cap < hi), b, out)
    return out


def load_calendar():
    """market trading calendar = distinct dsf_v2 dates (cached), with integer index k."""
    f = CACHE / "calendar.parquet"
    if f.exists():
        cal = pd.read_parquet(f)
        cal["date"] = pd.to_datetime(cal["date"]).astype("datetime64[ns]")
        return cal
    c = con()
    cal = c.execute(f"SELECT DISTINCT date FROM '{DSF}' ORDER BY date").df()
    cal["date"] = pd.to_datetime(cal["date"])
    cal["k"] = np.arange(len(cal), dtype=np.int64)
    cal.to_parquet(f, index=False)
    return cal


def load_ff_daily():
    f = CACHE / "ff5umd_daily.parquet"
    if f.exists():
        ff = pd.read_parquet(f)
        ff["date"] = pd.to_datetime(ff["date"]).astype("datetime64[ns]")
        return ff
    c = con()
    ff = c.execute(f"""SELECT TRY_CAST(date AS DATE) date, TRY_CAST(mktrf AS DOUBLE) mktrf, TRY_CAST(smb AS DOUBLE) smb,
        TRY_CAST(hml AS DOUBLE) hml, TRY_CAST(rmw AS DOUBLE) rmw, TRY_CAST(cma AS DOUBLE) cma, TRY_CAST(rf AS DOUBLE) rf,
        TRY_CAST(umd AS DOUBLE) umd FROM read_csv('{DUMP}ff_all.fivefactors_daily.csv.gz', header=true, all_varchar=true)""").df()
    ff["date"] = pd.to_datetime(ff["date"])
    ff.to_parquet(f, index=False)
    return ff


def load_ff_monthly():
    f = CACHE / "ff5umd_monthly.parquet"
    if f.exists():
        return pd.read_parquet(f)
    c = con()
    ff = c.execute(f"SELECT * FROM read_csv('{DUMP}ff_all.fivefactors_monthly.csv.gz', header=true, all_varchar=true)").df()
    ff.to_parquet(f, index=False)
    return ff


def nw_alpha(y, X=None, lags=5):
    """OLS y = a + X b, Newey-West (Bartlett, maxlags=lags) SE; statsmodels HAC without small-sample correction.
    Returns dict(alpha, t, n, betas...)."""
    y = np.asarray(y, dtype=float)
    if X is None:
        Z = np.ones((len(y), 1))
    else:
        Z = sm.add_constant(np.asarray(X, dtype=float), has_constant="add")
    ok = np.isfinite(y) & np.isfinite(Z).all(axis=1)
    y, Z = y[ok], Z[ok]
    if len(y) < 30:
        return dict(alpha=np.nan, t=np.nan, n=int(len(y)), p=np.nan, mean=np.nan, t_mean=np.nan)
    o = sm.OLS(y, Z).fit(cov_type="HAC", cov_kwds={"maxlags": lags, "use_correction": False})
    m = sm.OLS(y, np.ones((len(y), 1))).fit(cov_type="HAC", cov_kwds={"maxlags": lags, "use_correction": False})
    return dict(alpha=float(o.params[0]), t=float(o.tvalues[0]), n=int(len(y)), p=float(2 * stats.norm.sf(abs(o.tvalues[0]))),
                mean=float(m.params[0]), t_mean=float(m.tvalues[0]), r2=float(o.rsquared),
                **({f"b_{FC[i]}": float(o.params[i + 1]) for i in range(Z.shape[1] - 1)} if X is not None else {}))


def ff_regress(series, ff, excess=False, lags=5):
    """series: pd.Series indexed by date (daily portfolio return). excess=True subtracts rf (long-only portfolio);
    zero-investment spreads use excess=False. Regressed on FF5+UMD (dump ff_all.fivefactors_daily)."""
    s = series.dropna()
    F = ff.set_index("date").reindex(s.index)
    y = s.values - (F["rf"].values if excess else 0.0)
    return nw_alpha(y, F[FC].values, lags)


def verdict(t_full, sign_expected, a_first, a_second):
    """PHASE4_PROTOCOL §3 grades. sign_expected = +1 / -1."""
    if not np.isfinite(t_full):
        return "성립 안 함"
    right = np.sign(t_full) == sign_expected
    halves_same = (np.sign(a_first) == sign_expected) and (np.sign(a_second) == sign_expected)
    if right and abs(t_full) >= CRIT and halves_same:
        return "성립"
    if right and (abs(t_full) >= CRIT or abs(t_full) >= 1.96):
        return "약함"
    if (not right) and abs(t_full) >= CRIT:
        return "성립 안 함 (반대 부호 유의)"
    return "성립 안 함"


def log(msg, fh=None):
    print(msg, flush=True)
    if fh is not None:
        fh.write(msg + "\n")
        fh.flush()
