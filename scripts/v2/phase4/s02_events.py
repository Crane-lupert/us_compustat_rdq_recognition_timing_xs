"""s02: announcement history, expected dates and the R1 / R2 / R3 event sets (FROZEN_PARAMS "announcements", "R1", "R2",
"R3"). NO return outcome is computed here (only dates, flags, entry-day price / cap / membership conditions).

Inputs: cache/fundq_rdq.parquet (s00), cache/link4.parquet + cache/shared_assign.parquet (s01), cache/calendar.parquet,
phase3/out/membership.parquet, dsf_v2_slim (entry-day rows, delisting-row dates).
Writes cache/ann_valid.parquet, cache/slots.parquet, cache/e_any.parquet, cache/r1_slots_o{1,5,10}.parquet (all slots with
flags), out/r1_events_o{1,5,10}.parquet (traded events, no returns yet), out/r3_events_base.parquet, log on stdout.
"""
import sys
sys.dont_write_bytecode = True
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from p4common import CACHE, OUT, P3, DSF, LAST_DAY, FIRST_ENTRY, con, load_calendar  # noqa: E402

c = con()
cal = load_calendar()
CD = cal.date.values.astype("datetime64[ns]")
NCAL = len(CD)


def k_ge(x):
    """index of the first market trading day >= x (NCAL if beyond)."""
    return np.searchsorted(CD, np.asarray(x, dtype="datetime64[ns]"), side="left")


def k_gt(x):
    return np.searchsorted(CD, np.asarray(x, dtype="datetime64[ns]"), side="right")


def day(k):
    k = np.asarray(k)
    out = np.full(k.shape, np.datetime64("NaT"), dtype="datetime64[ns]")
    ok = (k >= 0) & (k < NCAL)
    out[ok] = CD[k[ok]]
    return out


# ------------------------------------------------------------------ announcements
fq = pd.read_parquet(CACHE / "fundq_rdq.parquet")
fq["datadate"] = pd.to_datetime(fq["datadate"]).astype("datetime64[ns]"); fq["rdq"] = pd.to_datetime(fq["rdq"]).astype("datetime64[ns]")
allrows = fq.dropna(subset=["datadate"]).copy()
n_err = int((allrows.rdq.notna() & (allrows.rdq <= allrows.datadate)).sum())
V = allrows[allrows.rdq.notna() & (allrows.rdq > allrows.datadate)].copy()      # valid announcement records
V["gap"] = (V.rdq - V.datadate).dt.days
print(f"fundq rows {len(allrows):,}; valid announcement records (rdq > datadate) {len(V):,}; erroneous rdq <= datadate treated as missing: {n_err}")
V[["gvkey", "datadate", "rdq", "fyearq", "fqtr", "fyr", "gap"]].to_parquet(CACHE / "ann_valid.parquet", index=False)

# prior-year source records P: one per (gvkey, fyearq, fqtr), latest datadate (as phase-3 p01 Chambers-Penman)
P = V.dropna(subset=["fyearq", "fqtr"]).sort_values(["gvkey", "fyearq", "fqtr", "datadate"], kind="mergesort")
P = P.drop_duplicates(["gvkey", "fyearq", "fqtr"], keep="last").copy()
P["E_raw"] = P["rdq"] + pd.DateOffset(years=1)
P["kE"] = k_ge(P["E_raw"].values)
P["E"] = day(P["kE"].values)
P["D_exp"] = P["datadate"] + pd.DateOffset(months=12)
P["elig"] = P["gap"].between(1, 120)
P = P[P["E_raw"] >= pd.Timestamp(CD[0])].copy()          # expected dates inside the CRSP calendar only
# schedule check at tau = E - 45 calendar days: latest valid record announced on/before tau
Vs = V.sort_values(["rdq", "datadate"], kind="mergesort")[["gvkey", "rdq", "datadate", "fyr"]].rename(
    columns={"rdq": "L_rdq", "datadate": "L_datadate", "fyr": "L_fyr"})
P["tau"] = P["E"] - pd.Timedelta(days=45)
P = P.dropna(subset=["tau"]).sort_values("tau", kind="mergesort")
P = pd.merge_asof(P, Vs, left_on="tau", right_on="L_rdq", by="gvkey", direction="backward", allow_exact_matches=True)
mdiff = (P.L_datadate.dt.year * 12 + P.L_datadate.dt.month) - (P.datadate.dt.year * 12 + P.datadate.dt.month)
P["sched_ok"] = (P.L_fyr == P.fyr) & (mdiff % 3 == 0)
print(f"prior-year source records P: {len(P):,}; eligible gap 1-120: {int(P.elig.sum()):,}; "
      f"schedule check fails among eligible: {int((P.elig & ~P.sched_ok).sum()):,} (fyr change {int((P.elig & (P.L_fyr != P.fyr)).sum()):,})")
S = P[P.elig].sort_values(["gvkey", "kE", "datadate"], kind="mergesort")
nd = int(S.duplicated(["gvkey", "kE"], keep=False).sum())
S = S.drop_duplicates(["gvkey", "kE"], keep="last").copy()
S["Y"] = S["fyearq"] + 1
print(f"eligible slots after (gvkey, E) de-duplication: {len(S):,} ({nd:,} rows were in duplicated groups)")
S[["gvkey", "fyearq", "fqtr", "datadate", "rdq", "gap", "fyr", "E_raw", "E", "kE", "D_exp", "sched_ok", "L_rdq", "L_datadate", "L_fyr", "Y"]].to_parquet(
    CACHE / "slots.parquet", index=False)

# any expected date (N exclusion / coverage in R2): every valid record's rdq + 1 year, de-duplicated per gvkey
EA = V[["gvkey", "rdq"]].copy()
EA["E_raw"] = EA["rdq"] + pd.DateOffset(years=1)
EA = EA[EA["E_raw"] >= pd.Timestamp(CD[0])].copy()
EA["kE"] = k_ge(EA["E_raw"].values)
EA = EA.drop_duplicates(["gvkey", "kE"])[["gvkey", "kE"]]
EA.to_parquet(CACHE / "e_any.parquet", index=False)
print(f"any-E (gvkey, E) pairs: {len(EA):,}")

# ------------------------------------------------------------------ link / universe helpers
L4 = pd.read_parquet(CACHE / "link4.parquet")
SA = pd.read_parquet(CACHE / "shared_assign.parquet")
SA["date"] = pd.to_datetime(SA["date"]).astype("datetime64[ns]")
shared = set(SA.permno.unique())
mem = pd.read_parquet(P3 / "out/membership.parquet")[["y", "permno", "rk", "dlycap"]].rename(columns={"dlycap": "cap_june"})
mem["permno"] = mem["permno"].astype("int64")


def attach_link(df, date_col):
    """permno via link4; for shared permnos keep the row only if the date is assigned to this gvkey (p03 rule)."""
    df = df.merge(L4[["gvkey", "permno", "step"]], on="gvkey", how="inner")
    df["permno"] = df["permno"].astype("int64")
    m = df.merge(SA.rename(columns={"gvkey": "g_assigned", "date": date_col}), on=["permno", date_col], how="left")
    keep = (~m.permno.isin(shared)) | (m.g_assigned == m.gvkey)
    return m[keep].drop(columns=["g_assigned"]), int((~keep).sum())


def attach_universe(df, date_col):
    df = df.copy()
    d = pd.to_datetime(df[date_col])
    df["mem_y"] = np.where(d.dt.month >= 7, d.dt.year, d.dt.year - 1)
    return df.merge(mem.rename(columns={"y": "mem_y"}), on=["mem_y", "permno"], how="inner")


def entry_rows(df, date_col):
    """normal (non-delisting) CRSP row of the permno on the entry date: price, cap."""
    q = df[["permno", date_col]].drop_duplicates().rename(columns={date_col: "d"})
    c.register("q", q)
    r = c.execute(f"""SELECT q.permno, q.d, s.dlyprc prc_entry, s.dlycap cap_entry
                      FROM q JOIN '{DSF}' s ON s.permno = q.permno AND s.date = q.d WHERE s.dlydelflg = 'N'""").df()
    c.unregister("q")
    r["d"] = pd.to_datetime(r["d"]).astype("datetime64[ns]")
    return df.merge(r.rename(columns={"d": date_col}), on=["permno", date_col], how="left")


delist = c.execute(f"SELECT permno::BIGINT permno, date AS d_delist FROM '{DSF}' WHERE dlydelflg = 'Y'").df()
delist["d_delist"] = pd.to_datetime(delist["d_delist"]).astype("datetime64[ns]")

# current-year row existence (any fundq row incl. null rdq) keyed by (gvkey, fyearq, fqtr)
cur = allrows.dropna(subset=["fyearq", "fqtr"]).copy()
cur["rdq_ok"] = cur.rdq.notna() & (cur.rdq > cur.datadate)
cur = cur.sort_values(["gvkey", "fyearq", "fqtr", "rdq_ok", "datadate"], kind="mergesort").drop_duplicates(["gvkey", "fyearq", "fqtr"], keep="last")
cur = cur[["gvkey", "fyearq", "fqtr", "rdq", "rdq_ok"]].rename(columns={"fyearq": "Y", "fqtr": "fqtr", "rdq": "rdq_cur", "rdq_ok": "has_rdq"})
cur["has_row"] = True

# slot-quarter already announced (any record with datadate >= D_exp - 15 days announced on/before t): suffix-min of rdq
Vd = V.sort_values(["gvkey", "datadate"], kind="mergesort")[["gvkey", "datadate", "rdq"]].copy()
Vd["rdq_sufmin"] = Vd.iloc[::-1].groupby("gvkey", sort=False)["rdq"].cummin().iloc[::-1].values
Vd = Vd.rename(columns={"datadate": "dd_v"})[["gvkey", "dd_v", "rdq_sufmin"]].sort_values("dd_v", kind="mergesort")
Vr = V.sort_values(["rdq"], kind="mergesort")[["gvkey", "rdq"]]

# ------------------------------------------------------------------ R1
for o, var in ((1, "main"), (5, "main"), (10, "main"), (5, "literal")):   # 'literal' = EXPLORATORY (FROZEN R1.not_announced)
    sfx = f"o{o}" + ("" if var == "main" else "_literal")
    R = S.copy()
    R["k_e"] = R["kE"] + o
    R["t_e"] = day(R["k_e"].values)
    R = R[(R.t_e >= FIRST_ENTRY) & (R.t_e <= LAST_DAY)].copy()
    n0 = len(R)
    R = R.sort_values("t_e", kind="mergesort")
    R = pd.merge_asof(R, Vr.rename(columns={"rdq": "r_last"}), left_on="t_e", right_on="r_last", by="gvkey",
                      direction="backward", allow_exact_matches=True)
    R["ann_window"] = R.r_last.notna() & (R.r_last > R.E - pd.Timedelta(days=30))
    R["thr"] = R["D_exp"] - pd.Timedelta(days=15)
    R = R.sort_values("thr", kind="mergesort")
    R = pd.merge_asof(R, Vd, left_on="thr", right_on="dd_v", by="gvkey", direction="forward", allow_exact_matches=True)
    R["ann_slot"] = R.rdq_sufmin.notna() & (R.rdq_sufmin <= R.t_e)
    R["not_ann"] = ~R.ann_window & ~R.ann_slot
    R = R.merge(cur, on=["gvkey", "Y", "fqtr"], how="left")
    R["has_row"] = R["has_row"].astype("boolean").fillna(False).astype(bool); R["has_rdq"] = R["has_rdq"].astype("boolean").fillna(False).astype(bool)
    # exit candidates (dates only): next valid announcement strictly after t_e
    R = R.sort_values("t_e", kind="mergesort")
    R = pd.merge_asof(R, Vr.rename(columns={"rdq": "rdq_next"}), left_on="t_e", right_on="rdq_next", by="gvkey",
                      direction="forward", allow_exact_matches=False)
    cand = R[(R.not_ann if var == "main" else ~R.ann_window) & R.sched_ok].copy()
    cnt = dict(slots=n0, announced_window=int(R.ann_window.sum()), announced_slot_early_only=int((R.ann_slot & ~R.ann_window).sum()),
               not_announced=int(R.not_ann.sum()), not_ann_sched_fail=int((R.not_ann & ~R.sched_ok).sum()))
    cand, n_sh = attach_link(cand, "t_e")
    cnt["linked"] = len(cand); cnt["shared_permno_dropped"] = n_sh
    cand = attach_universe(cand, "t_e"); cnt["in_universe"] = len(cand)
    cand = entry_rows(cand, "t_e")
    cand["prc_ok"] = cand.prc_entry.abs() >= 5
    cnt["trading_on_entry"] = int(cand.prc_entry.notna().sum()); cnt["price_ge_5"] = int(cand.prc_ok.sum())
    cand = cand[cand.prc_ok].copy()
    cand = cand.merge(delist, on="permno", how="left")
    cand.loc[cand.d_delist <= cand.t_e, "d_delist"] = pd.NaT       # (cannot happen: entry row is a normal row)
    x_ann = day(k_gt(cand["rdq_next"].values))
    x_40 = day(cand["k_e"].values + 40)
    cand["x_ann"], cand["x_40"] = x_ann, x_40
    X = np.stack([cand.x_ann.values.astype("datetime64[ns]").astype("int64"),
                  cand.x_40.values.astype("datetime64[ns]").astype("int64"),
                  cand.d_delist.values.astype("datetime64[ns]").astype("int64")], axis=1).astype(float)
    X[X < -1e18] = np.inf                                            # NaT -> never
    j = np.argmin(X, axis=1)
    cand["exit"] = pd.to_datetime(X[np.arange(len(X)), j].astype("int64"))
    cand["exit_reason"] = np.array(["announce", "40d", "delist"])[j]
    # ties: announcement-exit day equal to the 40-day exit -> 'announce'; delisting on the same day -> 'delist'
    cand.loc[(cand.x_ann == cand.exit), "exit_reason"] = "announce"
    cand.loc[(cand.d_delist == cand.exit), "exit_reason"] = "delist"
    # one position per permno at a time (earlier entry kept; a later event entering before the kept exit is dropped)
    cand = cand.sort_values(["permno", "t_e", "datadate"], kind="mergesort").reset_index(drop=True)
    keep = np.zeros(len(cand), dtype=bool)
    last_exit = {}
    for i, (p, te, ex) in enumerate(zip(cand.permno.values, cand.t_e.values, cand.exit.values)):
        le = last_exit.get(p)
        if le is None or te >= le:
            keep[i] = True
            last_exit[p] = ex
    cnt["overlap_dropped"] = int((~keep).sum())
    ev = cand[keep].copy()
    cnt["events"] = len(ev)
    ev["eid"] = np.arange(len(ev), dtype=np.int64)
    ev["never_announced_after"] = ev.rdq_next.isna()
    cols = ["eid", "permno", "gvkey", "step", "fyearq", "fqtr", "datadate", "rdq", "gap", "E", "kE", "t_e", "k_e", "exit", "exit_reason",
            "rdq_next", "x_ann", "x_40", "d_delist", "has_row", "has_rdq", "rdq_cur", "never_announced_after", "prc_entry", "cap_entry",
            "rk", "mem_y"]
    ev = ev[cols].rename(columns={"datadate": "datadate_prev", "rdq": "rdq_prev", "gap": "gap_prev", "fyearq": "fyearq_prev",
                                  "t_e": "entry"})
    ev.to_parquet(OUT / f"r1_events_{sfx}.parquet", index=False)
    R[["gvkey", "fyearq", "fqtr", "E", "t_e", "ann_window", "ann_slot", "not_ann", "sched_ok", "has_row", "has_rdq"]].to_parquet(
        CACHE / f"r1_slots_{sfx}.parquet", index=False)
    print(f"\n[R1 entry E+{o} {var}] " + ", ".join(f"{k} {v:,}" for k, v in cnt.items()))
    print(f"   events by current-year Compustat row: has row {int(ev.has_row.sum()):,} (with valid rdq {int(ev.has_rdq.sum()):,}), "
          f"no row {int((~ev.has_row).sum()):,}; exit reasons {ev.exit_reason.value_counts().to_dict()}; "
          f"never announced afterwards {int(ev.never_announced_after.sum()):,}")
    print(f"   entry years: {ev.entry.dt.year.value_counts().sort_index().to_dict()}")

# ------------------------------------------------------------------ R3 base events (announcements)
C = V.dropna(subset=["fyearq", "fqtr"]).sort_values(["gvkey", "fyearq", "fqtr", "datadate"], kind="mergesort")
C = C.drop_duplicates(["gvkey", "fyearq", "fqtr"], keep="last")
C = C[C.gap.between(1, 180)].copy()
n_c = len(C)
C = C.sort_values(["gvkey", "rdq", "datadate"], kind="mergesort")
n_same = int(C.duplicated(["gvkey", "rdq"], keep=False).sum())
C = C.drop_duplicates(["gvkey", "rdq"], keep="last").copy()
Pp = P[["gvkey", "fyearq", "fqtr", "datadate", "rdq", "gap", "fyr", "elig", "E", "kE"]].rename(
    columns={"datadate": "dd_prev", "rdq": "rdq_prev", "gap": "gap_prev", "fyr": "fyr_prev", "E": "E", "kE": "kE"})
Pp["fyearq"] = Pp["fyearq"] + 1
C = C.merge(Pp, on=["gvkey", "fyearq", "fqtr"], how="left")
md = (C.datadate.dt.year * 12 + C.datadate.dt.month) - (C.dd_prev.dt.year * 12 + C.dd_prev.dt.month)
C["has_E"] = C.rdq_prev.notna() & C.elig.astype("boolean").fillna(False).astype(bool) & (C.fyr == C.fyr_prev) & (md == 12)
C["k_rdq"] = k_ge(C["rdq"].values)
C["dev_td"] = np.where(C.has_E, C.k_rdq - C.kE, np.nan)
C["group"] = np.where(~C.has_E, "noE", np.where(C.dev_td <= -5, "EARLY", np.where(C.dev_td >= 5, "LATE", "MID")))
C["k0"] = k_gt(C["rdq"].values)
C["d0"] = day(C["k0"].values)
C = C[(C.d0 >= FIRST_ENTRY) & (C.d0 <= LAST_DAY)].copy()
cnt3 = dict(current_records_gap_1_180=n_c, same_day_dups=n_same, announcements_entry_2000_2024=len(C))
C, n_sh = attach_link(C, "d0"); cnt3["linked"] = len(C); cnt3["shared_permno_dropped"] = n_sh
C = attach_universe(C, "d0"); cnt3["in_universe"] = len(C)
C = entry_rows(C, "d0"); C = C[C.prc_entry.notna()].copy(); cnt3["trading_on_entry"] = len(C)
C = C.merge(delist, on="permno", how="left")
C.loc[C.d_delist <= C.d0, "d_delist"] = pd.NaT
for H in (20, 60):
    xh = day(C["k0"].values + H)
    C[f"x{H}"] = pd.to_datetime(np.where(C.d_delist.notna() & (C.d_delist.values < xh), C.d_delist.values, xh))
print("\n[R3 base] " + ", ".join(f"{k} {v:,}" for k, v in cnt3.items()))
print("   groups (before per-permno overlap rule):", C.group.value_counts().to_dict())
print("   dev_td quantiles (has_E):", C.loc[C.has_E, "dev_td"].quantile([0.01, 0.05, 0.1, 0.25, 0.5, 0.75, 0.9, 0.95, 0.99]).to_dict())
cols3 = ["permno", "gvkey", "step", "fyearq", "fqtr", "datadate", "rdq", "gap", "fyr", "dd_prev", "rdq_prev", "gap_prev", "E", "kE",
         "has_E", "k_rdq", "dev_td", "group", "d0", "k0", "x20", "x60", "d_delist", "prc_entry", "cap_entry", "rk", "mem_y"]
C[cols3].to_parquet(OUT / "r3_events_base.parquet", index=False)
print("wrote r1_events_o{1,5,10}.parquet, r1_events_o5_literal.parquet (EXPLORATORY), r3_events_base.parquet")
