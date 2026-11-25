"""s09: (a) Table 6 (PEAD separation) like-for-like; (b) PIT-clean variant replicate + simple-return version.

Input: repo artifacts/panel_with_returns_ext.parquet (read-only; carries car_120/180 and car_120_sw1/180_sw1 log CARs;
       its car_120/180 equal panel_ret.parquet's, checked below). PIT quintile logic copied from repo scripts/phase1_pit_clean.py.
"""
import numpy as np
import pandas as pd

from common import build_cells, monthly_spread, cell_stat, INDUSTRY_TILT_HIGH, IS_END, OOS_START, OOS_END

from v2paths import V1_ARTIFACTS
E = pd.read_parquet(V1_ARTIFACTS + "panel_with_returns_ext.parquet")
for c in ["car_120", "car_180", "car_120_sw1", "car_180_sw1"]:
    E["s" + c] = np.expm1(E[c])
spec = {"LH120": ("A120-LH", 120, "L", "H"), "SH120": ("A120-SH", 120, "S", "H"),
        "LH180": ("A180-LH", 180, "L", "H"), "SL180": ("A180-SL", 180, "S", "L")}


def per(s, p):
    if p == "IS":
        return s[s.index <= IS_END]
    if p == "OOS":
        return s[(s.index >= OOS_START) & (s.index <= OOS_END)]
    if p == "FULL<=2024":
        return s[s.index <= OOS_END]
    return s  # FULL incl. partial 2025 (repo full-panel convention)


df = build_cells(E)
print("(a) Table 6 like-for-like: t(NW12) next-day window vs one-week-delayed window")
for k, (cell, H, sz, it) in spec.items():
    for basis, pre in (("log", ""), ("simple", "s")):
        line = []
        for p in ("IS", "OOS", "FULL<=2024", "FULL+2025"):
            a = cell_stat(per(monthly_spread(df, f"{pre}car_{H}", sz, it), p))[1]
            b = cell_stat(per(monthly_spread(df, f"{pre}car_{H}_sw1", sz, it), p))[1]
            line.append(f"{p}: {a:.2f}->{b:.2f}")
        print(f"   {cell} [{basis}] " + " | ".join(line))


def assign_pit_quintile(df, signal_col, cohort_days=30):
    df = df.dropna(subset=[signal_col, "ff12", "rdq"]).copy()
    df = df.sort_values(["ff12", "rdq", signal_col], kind="mergesort").reset_index(drop=True)
    q5 = np.full(len(df), np.nan)
    rd = df["rdq"].values.astype("int64")
    ff = df["ff12"].values
    sg = df[signal_col].values
    win = cohort_days * 24 * 3600 * 1_000_000_000
    n = len(df)
    i = 0
    while i < n:
        j = i
        while j < n and ff[j] == ff[i]:
            j += 1
        br, bs = rd[i:j], sg[i:j]
        for k in range(j - i):
            d = br[k]
            left = np.searchsorted(br[:k], d - win, side="left")
            right = np.searchsorted(br[:k], d, side="left")
            co = bs[left:right]
            co = co[~np.isnan(co)]
            if len(co) < 5 or np.isnan(bs[k]):
                continue
            pct = ((co < bs[k]).sum() + 0.5 * (co == bs[k]).sum()) / len(co)
            q5[i + k] = min(5, max(1, int(pct * 5) + 1))
        i = j
    df["q5"] = q5
    return df


pit = assign_pit_quintile(E, "gap_var_t")
pit["mcap_mil"] = pit["cshoq"] * pit["prccq"]
pit["rdq_month"] = pit["rdq"].dt.to_period("M")
pit = pit.sort_values(["rdq_month", "ff12", "mcap_mil"], kind="mergesort").reset_index(drop=True)
med = pit.groupby(["rdq_month", "ff12"], sort=False)["mcap_mil"].transform("median")
pit["size_bin"] = np.where(pit["mcap_mil"] >= med, "L", "S")
pit["ind_bin"] = np.where(pit["ff12"].isin(INDUSTRY_TILT_HIGH), "H", "L")
print("\n(b) PIT-clean variant (trailing-30d FF12 cohort, rdq+8 start): t(NW12)  [repo strategy_A_pit_clean.json is_oos_per_cell for log]")
for k, (cell, H, sz, it) in spec.items():
    out = []
    for basis, pre in (("log", ""), ("simple", "s")):
        s = monthly_spread(pit, f"{pre}car_{H}_sw1", sz, it)
        out.append(f"{basis}: IS {cell_stat(per(s,'IS'))[1]:.2f} OOS {cell_stat(per(s,'OOS'))[1]:.2f} FULL+2025 {cell_stat(s)[1]:.2f}")
    print(f"   {cell}-SW1  " + " | ".join(out))
