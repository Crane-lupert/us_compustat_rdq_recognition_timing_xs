"""Shared helpers for the RD1 re-verification (work folder only)."""
import numpy as np
import pandas as pd

INDUSTRY_TILT_HIGH = {6, 10, 11}
PRIMARY = ["A120-LH", "A120-SH", "A180-LH", "A180-SL"]
IS_END = pd.Timestamp("2016-12-31")
OOS_START = pd.Timestamp("2017-01-01")
OOS_END = pd.Timestamp("2024-12-31")


def ff12_from_sic(sic) -> int:
    """Same mapping as repo shared_lib/rdq_panel_loader.ff12_from_sic (copied verbatim in logic)."""
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


def nw_se(x, lag=12):
    """Newey-West (Bartlett) SE of the mean; identical formula to repo strategy_A_bonferroni.newey_west_se."""
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


def hh_se(x, lag):
    """Hansen-Hodrick (uniform weights, truncated at `lag`) SE of the mean; falls back to NW if LRV<0."""
    x = np.asarray(x, dtype=float)
    n = len(x)
    xd = x - x.mean()
    lrv = xd @ xd / n
    for k in range(1, lag + 1):
        lrv += 2.0 * (xd[k:] @ xd[:-k]) / n
    if lrv <= 0:
        return nw_se(x, lag)
    return float(np.sqrt(lrv / n))


def quintile_within(df, signal_col, group_cols):
    """Repo convention: rank(method='first') then qcut into 5 within group (groups < 5 rows -> NaN)."""
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


def build_cells(panel, signal_col="gap_var_t"):
    """Replicates repo build_monthly_xs_panel + assign_subcells."""
    df = panel.dropna(subset=[signal_col, "ff12"]).copy()
    df["rdq_month"] = df["rdq"].dt.to_period("M")
    df = quintile_within(df, signal_col, ["rdq_month", "ff12"])
    df["mcap_mil"] = df["cshoq"] * df["prccq"]
    df = df.sort_values(["rdq_month", "ff12", "mcap_mil"], kind="mergesort").reset_index(drop=True)
    med = df.groupby(["rdq_month", "ff12"], sort=False, observed=True)["mcap_mil"].transform("median")
    df["size_bin"] = np.where(df["mcap_mil"] >= med, "L", "S")
    df["ind_bin"] = np.where(df["ff12"].isin(INDUSTRY_TILT_HIGH), "H", "L")
    return df


def monthly_spread(df, ret_col, sz, it, q_long=1, q_short=5):
    sub = df[(df["size_bin"] == sz) & (df["ind_bin"] == it)].dropna(subset=[ret_col, "q5"])
    sub = sub[sub["q5"].isin([q_long, q_short])]
    m = sub.groupby(["rdq_month", "q5"], observed=True)[ret_col].mean().unstack("q5")
    if q_long not in m.columns or q_short not in m.columns:
        return pd.Series(dtype=float)
    s = (m[q_long] - m[q_short]).dropna().sort_index()
    s.index = s.index.to_timestamp()
    return s


def cell_stat(s, lag=12):
    s = s.dropna()
    if len(s) < 12:
        return float("nan"), float("nan"), len(s)
    mu = float(s.mean())
    se = nw_se(s.values, lag)
    return mu, mu / se, len(s)


def repo_hac_sharpe(s, lag=12):
    """Repo annualized_sharpe_hac: mu / (NW_SE*sqrt(n)) * sqrt(12)."""
    s = s.dropna()
    n = len(s)
    se = nw_se(s.values, lag)
    return float(s.mean() / (se * np.sqrt(n)) * np.sqrt(12))


def split(s):
    return s[s.index <= IS_END], s[(s.index >= OOS_START) & (s.index <= OOS_END)]
