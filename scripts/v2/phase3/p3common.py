"""Phase 3 shared helpers (RD1, SSRN 6965838). Self-contained: no import from the phase 1-2 folder.

All parameter values used here are frozen in phase3/FROZEN_PARAMS.json (Step 1).
"""
import sys
sys.dont_write_bytecode = True

import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats as st

from v2paths import RDQ_DIR, WRDS_DUMP
P3 = RDQ_DIR / "phase3"
PARENT = P3.parent
OUT = P3 / "out"
LOGS = P3 / "logs"
DUMP = WRDS_DUMP
DSF = (PARENT / "dsf_v2_slim.parquet").as_posix()
BIDASK = (PARENT / "dsf_v2_bidask.parquet").as_posix()

FROZEN = json.loads((Path(__file__).resolve().parent / "FROZEN_PARAMS.json").read_text(encoding="utf-8")) if (Path(__file__).resolve().parent / "FROZEN_PARAMS.json").exists() else {}

INDUSTRY_TILT_HIGH = {6, 10, 11}                      # Lock C / repo strategy_A_bonferroni.py L34
FF49_HIGH_TILT = {12, 35, 36, 37, 38, 11, 13, 45, 46, 48}  # repo phase1_robustness_ff49.py L42
PRIMARY = ["A120-LH", "A120-SH", "A180-LH", "A180-SL"]  # Lock D §1
IS_FIRST, IS_LAST = pd.Timestamp("2000-02-01"), pd.Timestamp("2016-12-01")    # return months (month start)
LATE_FIRST, LATE_LAST = pd.Timestamp("2017-01-01"), pd.Timestamp("2024-12-01")
BORROW_SCHEDULE = [(10_000.0, np.inf, 25.0), (2_000.0, 10_000.0, 50.0), (300.0, 2_000.0, 200.0),
                   (100.0, 300.0, 800.0), (0.0, 100.0, 2000.0)]   # repo phase1_robustness_borrow_overlay.py L88-94


def ff12_from_sic(sic) -> int:
    """Copy of repo shared_lib/rdq_panel_loader.ff12_from_sic (same logic as phase 1-2 common.py)."""
    if pd.isna(sic):
        return 12
    s = int(sic)
    if (100 <= s <= 999 or 2000 <= s <= 2399 or 2700 <= s <= 2749
            or 2770 <= s <= 2799 or 3100 <= s <= 3199 or 3940 <= s <= 3989):
        return 1
    if (2500 <= s <= 2519 or 2590 <= s <= 2599 or 3630 <= s <= 3659
            or 3710 <= s <= 3711 or s == 3714 or s == 3716
            or 3750 <= s <= 3751 or s == 3792 or 3900 <= s <= 3939 or 3990 <= s <= 3999):
        return 2
    if (2520 <= s <= 2589 or 2600 <= s <= 2699 or 2750 <= s <= 2769
            or 3000 <= s <= 3099 or 3200 <= s <= 3569 or 3580 <= s <= 3629
            or 3700 <= s <= 3709 or 3712 <= s <= 3713 or s == 3715
            or 3717 <= s <= 3749 or 3752 <= s <= 3791 or 3793 <= s <= 3799
            or 3830 <= s <= 3839 or 3860 <= s <= 3899):
        return 3
    if 1200 <= s <= 1399 or 2900 <= s <= 2999:
        return 4
    if 2800 <= s <= 2829 or 2840 <= s <= 2899:
        return 5
    if (3570 <= s <= 3579 or 3660 <= s <= 3692 or 3694 <= s <= 3699
            or 3810 <= s <= 3829 or 7370 <= s <= 7379):
        return 6
    if 4800 <= s <= 4899:
        return 7
    if 4900 <= s <= 4949:
        return 8
    if 5000 <= s <= 5999 or 7200 <= s <= 7299 or 7600 <= s <= 7699:
        return 9
    if 2830 <= s <= 2839 or s == 3693 or 3840 <= s <= 3859 or 8000 <= s <= 8099:
        return 10
    if 6000 <= s <= 6999:
        return 11
    return 12


def borrow_bps(mcap_mil) -> float:
    if pd.isna(mcap_mil):
        return 2000.0
    for lo, hi, b in BORROW_SCHEDULE:
        if lo <= mcap_mil < hi:
            return b
    return 2000.0


def nw_lag_auto(T: int) -> int:
    """Newey-West (1994) plug-in rule floor(4 (T/100)^(2/9))."""
    return int(np.floor(4.0 * (T / 100.0) ** (2.0 / 9.0)))


def nw_se(x, lag):
    """Newey-West (Bartlett) SE of the mean (same formula as repo strategy_A_bonferroni.newey_west_se)."""
    x = np.asarray(x, dtype=float)
    n = len(x)
    if n <= 1:
        return float("nan")
    xd = x - x.mean()
    lrv = xd @ xd / n
    for k in range(1, lag + 1):
        w = 1.0 - k / (lag + 1)
        lrv += 2.0 * w * (xd[k:] @ xd[:-k]) / n
    if lrv < 0:
        lrv = xd @ xd / n
    return float(np.sqrt(lrv / n))


def bonf_crit(df: int, m: int = 12, alpha: float = 0.05, two_sided: bool = True) -> float:
    a = alpha / m
    return float(st.t.ppf(1 - (a / 2 if two_sided else a), df))


def series_stats(s: pd.Series, lag=None, m=12):
    """Calendar-time monthly series stats. s must already contain every month of the period (0 where flat)."""
    s = s.astype(float)
    T = len(s)
    mu = float(s.mean())
    sd = float(s.std(ddof=1))
    L = nw_lag_auto(T) if lag is None else lag
    se = nw_se(s.values, L)
    t = mu / se if se > 0 else float("nan")
    df = T - 1
    p2 = float(2 * st.t.sf(abs(t), df))
    crit2 = bonf_crit(df, m, two_sided=True)
    crit1 = bonf_crit(df, m, two_sided=False)
    return dict(T=T, mu_m=mu, sd_m=sd, ann_ret=mu * 12, ann_vol=sd * np.sqrt(12),
                sharpe=mu / sd * np.sqrt(12) if sd > 0 else float("nan"),
                nw_lag=L, t_nw=t, t_nw12=mu / nw_se(s.values, 12), p_two=p2,
                crit_bonf2=crit2, crit_bonf1=crit1,
                pass_bonf2=bool(mu > 0 and t > crit2), pass_bonf1=bool(mu > 0 and t > crit1),
                pass_278=bool(mu > 0 and t > 2.78), pass_nom5=bool(mu > 0 and p2 < 0.05), sign_ok=bool(mu > 0))


def month_index(first, last):
    return pd.date_range(first, last, freq="MS")


def quintile_within(df, signal_col, group_cols):
    """Repo convention (strategy_A_bonferroni.build_monthly_xs_panel): sort by group+signal (mergesort),
    rank(method='first') then qcut into 5 within group; groups with < 5 rows -> NaN."""
    def _q(s):
        s = s.dropna()
        if len(s) < 5:
            return pd.Series([np.nan] * len(s), index=s.index)
        try:
            return pd.qcut(s.rank(method="first"), 5, labels=[1, 2, 3, 4, 5]).astype(float)
        except (ValueError, IndexError):
            return pd.Series([np.nan] * len(s), index=s.index)
    df = df.sort_values(group_cols + [signal_col], kind="mergesort").reset_index(drop=True)
    df["q5"] = df.groupby(group_cols, sort=False, observed=True)[signal_col].transform(_q)
    return df


def assign_cells(df, signal_col="gap_var_t"):
    """Lock C cells inside the given universe (repo build_monthly_xs_panel + assign_subcells):
    quintile of signal within (rdq_month, FF12); size = Compustat cshoq*prccq vs (rdq_month, FF12) median
    (NaN mcap -> 'S', repo behaviour); tilt H if FF12 in {6,10,11}; FF49 tilt carried as ind_bin49."""
    df = df.dropna(subset=[signal_col, "ff12"]).copy()
    df["rdq_month"] = df["rdq"].dt.to_period("M")
    df = quintile_within(df, signal_col, ["rdq_month", "ff12"])
    df["mcap_mil"] = df["cshoq"] * df["prccq"]
    df = df.sort_values(["rdq_month", "ff12", "mcap_mil"], kind="mergesort").reset_index(drop=True)
    med = df.groupby(["rdq_month", "ff12"], sort=False, observed=True)["mcap_mil"].transform("median")
    df["size_bin"] = np.where(df["mcap_mil"] >= med, "L", "S")
    df["ind_bin"] = np.where(df["ff12"].isin(INDUSTRY_TILT_HIGH), "H", "L")
    if "ff49" in df.columns:
        df["ind_bin49"] = np.where(df["ff49"].isin(FF49_HIGH_TILT), "H", "L")
    return df


def log(msg, fh=None):
    print(msg, flush=True)
    if fh is not None:
        fh.write(msg + "\n")
        fh.flush()
