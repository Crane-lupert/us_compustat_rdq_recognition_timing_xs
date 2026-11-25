"""Phase 7 - step 20: family R event tables with every condition (no outcome data).

Three event sets (PHASE7_SEARCH_PROTOCOL.md section 2.2):
  delay   silent k trading days past the expected announcement date (k = 1, 3, 5, 10); held until the day after the announcement (max 40 days)
  ann     actual announcements, with the timing deviation from the expected date
  exp     entry 6 trading days before the expected date (not yet announced), exit the day after the expected date
Expected date E = prior-year same-quarter announcement date + 1 year. The announcement date is the earlier of Compustat rdq and the
first 8-K Item 2.02 in [E - 30d, E + 150d] (when the firm's 8-K history is available).
Run: python p7_20_rdq_build.py
"""
import numpy as np
import pandas as pd

import p7lib as L

cal = L.calendar()
dnp = cal.date.values
NK = len(dnp)
D1 = np.timedelta64(1, "D")


def kidx(d, side="left"):
    return np.searchsorted(dnp, np.asarray(d, dtype="datetime64[ns]"), side=side)


# ---------------- announcements and slots ----------------
fq = pd.read_parquet(L.CACHE / "fundq_ext.parquet")
fq["datadate"] = pd.to_datetime(fq.datadate)
fq["rdq"] = pd.to_datetime(fq.rdq)
fq = fq[fq.fyearq.notna() & fq.fqtr.notna()].sort_values(["gvkey", "fyearq", "fqtr", "datadate"]).drop_duplicates(["gvkey", "fyearq", "fqtr"], keep="last")
p = fq[["gvkey", "fyearq", "fqtr", "epspxq"]].rename(columns={"epspxq": "eps_l4"})
p["fyearq"] = p.fyearq + 1
fq = fq.merge(p, on=["gvkey", "fyearq", "fqtr"], how="left")
fq["sue"] = (fq.epspxq - fq.eps_l4) / fq.prccq.where(fq.prccq > 1)
fq["loss"] = (fq.ibq < 0).where(fq.ibq.notna())
cikmap = fq[fq.cik.notna() & (fq.cik != "")].sort_values("datadate").drop_duplicates("gvkey", keep="last").set_index("gvkey").cik.astype(str).str.zfill(10)
V = fq[fq.rdq.notna()].copy()
V["gap"] = (V.rdq - V.datadate).dt.days
act = V[V.gap >= 1][["gvkey", "fyearq", "fqtr", "rdq", "sue", "loss"]].rename(columns={"rdq": "rdq_act", "sue": "sue_act", "loss": "loss_act"})
S = V[(V.gap >= 1) & (V.gap <= 120)][["gvkey", "fyearq", "fqtr", "rdq", "cusip"]].rename(columns={"rdq": "rdq_prev"})
S["fyearq"] = S.fyearq + 1
S = S.merge(act, on=["gvkey", "fyearq", "fqtr"], how="left")
S["E_raw"] = S.rdq_prev + pd.DateOffset(years=1)
S = S[(S.E_raw >= "2002-01-01") & (S.E_raw <= "2025-12-31")].copy()
S["kE"] = kidx(S.E_raw.values)
S = S[S.kE < NK - 1].copy()
S["cik10"] = S.gvkey.map(cikmap)
c = L.con()
hdr = c.execute(f"SELECT permno, max(hdrcusip8) AS h FROM '{L.SLIM}' GROUP BY 1").df()
h2p = hdr.groupby("h").permno.apply(list).to_dict()
c8 = fq.dropna(subset=["cusip"]).drop_duplicates("gvkey").set_index("gvkey").cusip.str[:8]
g2p = {g_: (h2p.get(c_)[0] if c_ in h2p and len(h2p[c_]) == 1 else None) for g_, c_ in c8.items()}
S["permno"] = S.gvkey.map(g2p)
print(f"[slots] expected-date slots 2002-2025: {len(S)}; with a CRSP link: {int(S.permno.notna().sum())}; with a CIK: {int(S.cik10.notna().sum())}")

# ---------------- 8-K Item 2.02 ----------------
K = pd.read_parquet(L.CACHE / "k8_all.parquet")
K["d"] = pd.to_datetime(K.date, errors="coerce")
K = K.dropna(subset=["d"]).sort_values(["cik10", "d"])
by202 = {k: v.d.values.astype("datetime64[ns]") for k, v in K[K.i202].groupby("cik10")}
COV = pd.read_parquet(L.CACHE / "k8_coverage.parquet")
covd = dict(zip(COV.cik10, pd.to_datetime(COV.cov_start).values.astype("datetime64[ns]")))
a8, cov8 = [], []
for ck, e in zip(S.cik10.values, S.E_raw.values.astype("datetime64[ns]")):
    lo = e - 30 * D1
    cs = covd.get(ck)
    cov8.append(cs is not None and cs <= lo)
    v = by202.get(ck)
    if v is None:
        a8.append(np.datetime64("NaT"))
        continue
    i = np.searchsorted(v, lo, side="left")
    a8.append(v[i] if i < len(v) and v[i] <= e + 150 * D1 else np.datetime64("NaT"))
S["ann8k"] = a8
S["k8cov"] = cov8
early8 = S.ann8k.notna() & S.rdq_act.notna() & ((S.rdq_act - S.ann8k).dt.days > 45)      # an 8-K far ahead of rdq: not this quarter's release
S.loc[early8, "ann8k"] = pd.NaT
S["ann"] = S[["rdq_act", "ann8k"]].min(axis=1)
S["k_ann"] = np.where(S.ann.notna(), kidx(S.ann.fillna(pd.Timestamp("2099-01-01")).values), 10 ** 8)
S["dev_td"] = np.where(S.ann.notna(), S.k_ann - S.kE, np.nan)
S["dev_cd"] = (S.ann - S.E_raw).dt.days
S["slot_id"] = np.arange(len(S))
print(f"[ann] slots with an announcement date: {int(S.ann.notna().sum())}; 8-K history available: {int(S.k8cov.sum())}; 8-K date earlier than rdq: {int((S.ann8k < S.rdq_act).sum())}; "
      f"rdq missing but 8-K found: {int((S.rdq_act.isna() & S.ann8k.notna()).sum())}")

mem = L.members()
ms = {(int(y), int(pn)): int(rk) for y, pn, rk in zip(mem.y, mem.permno, mem.rk)}
days = pd.DatetimeIndex(dnp)
my_of_k = np.where(days.month >= 7, days.year, days.year - 1)


def finish(ev, kcol):
    """universe rank and price at the entry day; drops events outside the universe or below $5"""
    ev = ev[ev.permno.notna()].copy()
    ev["permno"] = ev.permno.astype(int)
    ev["k0"] = ev[kcol].astype(int)
    ev = ev[(ev.k0 >= 0) & (ev.k0 < NK - 1)].copy()
    ev["rk"] = [ms.get((int(my_of_k[k]), int(pn))) for k, pn in zip(ev.k0.values, ev.permno.values)]
    ev = ev[ev.rk.notna()].copy()
    ev["date"] = dnp[ev.k0.values]
    cc = L.con()
    cc.register("e0", ev[["permno", "date"]].drop_duplicates())
    px = cc.execute(f"SELECT e.permno, e.date, abs(s.dlyprc) prc, s.dlycap cap, s.dlydelflg FROM e0 e JOIN '{L.SLIM}' s ON s.permno = e.permno AND s.date = e.date").df()
    px["date"] = pd.to_datetime(px["date"])
    ev = ev.merge(px, on=["permno", "date"])
    ev = ev[(ev.prc >= 5) & (ev.dlydelflg.fillna("N") != "Y")].copy()
    ev["stage"] = L.stage_of(ev.date)
    ev["year"] = pd.DatetimeIndex(ev.date).year
    ev["ym"] = ev.year * 100 + pd.DatetimeIndex(ev.date).month
    return ev


# ---------------- event sets ----------------
parts = []
for kd in (1, 3, 5, 10):
    e = S[(S.kE + kd < NK - 1) & (S.k_ann > S.kE + kd)].copy()
    e["kd"] = kd
    e["k_entry"] = e.kE + kd
    e = finish(e, "k_entry")
    e["kx"] = np.minimum(np.minimum(e.k_ann + 1, e.k0 + 40), NK - 1).astype(int)
    e = e.sort_values(["permno", "k0"])
    last, keep = {}, []
    for pn, k0, kx in zip(e.permno.values, e.k0.values, e.kx.values):
        ok = (pn not in last) or (k0 >= last[pn])
        keep.append(ok)
        if ok:
            last[pn] = kx
    e = e[np.array(keep)].copy()
    parts.append(e)
    print(f"[delay k={kd}] events {len(e)} (2005-2024: {int(((e.year >= 2005) & (e.year <= 2024)).sum())}); 8-K history available {e.k8cov.mean():.3f}; by stage {e.stage.value_counts().to_dict()}")
DEL = pd.concat(parts, ignore_index=True)
ANN = finish(S[S.ann.notna() & (S.k_ann < NK - 1) & (S.dev_td.abs() <= 60)].copy(), "k_ann")
EXP = S[(S.kE - 6 >= 0) & (S.k_ann > S.kE - 6)].copy()
EXP["k_entry"] = EXP.kE - 6
EXP = finish(EXP, "k_entry")
EXP["kx"] = (EXP.kE + 1).astype(int)
print(f"[ann] announcement events {len(ANN)}; [exp] expected-window events {len(EXP)}")

# ---------------- conditions ----------------
V2 = V[V.gap >= 1].sort_values(["gvkey", "rdq"])
fund = {g_: (v.rdq.values.astype("datetime64[ns]"), v.sue.values.astype(float), v.loss.astype(float).values, v.cshoq.values.astype(float)) for g_, v in V2.groupby("gvkey")}
H = S[S.ann.notna()].sort_values(["gvkey", "ann"])
hist = {g_: (v.ann.values.astype("datetime64[ns]"), v.dev_td.values.astype(float)) for g_, v in H.groupby("gvkey")}
M = pd.concat([pd.read_parquet(f) for f in sorted((L.MC / "phase5" / "cache" / "master").glob("*.parquet"))], ignore_index=True)
M = M[M.form.str.startswith("NT")]
M["cik10"] = M.cik.astype(str).str.zfill(10)
M["d"] = pd.to_datetime(M.date)
ntd = {k: v.d.values.astype("datetime64[ns]") for k, v in M.sort_values("d").groupby("cik10")}
items = {it: {k: v.d.values.astype("datetime64[ns]") for k, v in K[K[it]].groupby("cik10")} for it in ("i401", "i402", "i502")}
K["i2056"] = K.i205 | K.i206
items["i2056"] = {k: v.d.values.astype("datetime64[ns]") for k, v in K[K.i2056].groupby("cik10")}
INS = pd.read_parquet(L.MC / "x2a_cache" / "od_sales.parquet")
INS["d"] = pd.to_datetime(INS.dt.astype(str), format="%Y%m%d", errors="coerce")
INS = INS.dropna(subset=["d"]).sort_values("d")
insS = {k: v.d.values.astype("datetime64[ns]") for k, v in INS[INS.code == "S"].groupby("cik")}
insP = {k: v.d.values.astype("datetime64[ns]") for k, v in INS[INS.code == "P"].groupby("cik")}
PR = pd.read_parquet(L.MC / "x2a_cache" / "issuer_presence.parquet")
pres = set(zip(PR.cik, PR.year))
CV = pd.read_parquet(L.ROOT / "X_sec_letter" / "phase4" / "common" / "conversations.parquet")[["cik10", "dissem_date", "n_upload"]]
letd = {k: v.dissem_date.values.astype("datetime64[ns]") for k, v in CV.sort_values("dissem_date").groupby("cik10")}
letd3 = {k: v.dissem_date.values.astype("datetime64[ns]") for k, v in CV[CV.n_upload >= 3].sort_values("dissem_date").groupby("cik10")}
SI = pd.read_parquet(L.CACHE / "shortint.parquet")
SI["d"] = pd.to_datetime(SI.datadate, errors="coerce")
SI["si"] = pd.to_numeric(SI.shortintadj, errors="coerce").fillna(pd.to_numeric(SI.shortint, errors="coerce"))
SI = SI.dropna(subset=["d", "si"]).sort_values(["gvkey", "d", "si"]).drop_duplicates(["gvkey", "d"], keep="last")
sid = {g_: (v.d.values.astype("datetime64[ns]"), v.si.values.astype(float)) for g_, v in SI.groupby("gvkey")}
CO = pd.read_parquet(L.CACHE / "company.parquet").drop_duplicates("gvkey").set_index("gvkey")


def cnt(dct, key, lo, hi):
    v = dct.get(key)
    if v is None:
        return 0
    return int(np.searchsorted(v, hi, side="left") - np.searchsorted(v, lo, side="left"))


def conditions(ev, label):
    out = {k: [] for k in ("sue_prev", "loss_prev", "n_late8", "sd_dev8", "n_hist8", "nt365", "k401", "k402", "k502", "k2056", "k8hist", "ins_s", "ins_p", "ins_cov",
                           "let365", "let3_365", "si_ratio", "si_chg")}
    for g_, ck, d in zip(ev.gvkey.values, ev.cik10.values, ev.date.values.astype("datetime64[ns]")):
        f = fund.get(g_)
        sp = lp = sh = np.nan
        if f is not None:
            i = np.searchsorted(f[0], d, side="left") - 1
            if i >= 0 and (d - f[0][i]) <= 200 * D1:
                sp, lp, sh = f[1][i], f[2][i], f[3][i]
        out["sue_prev"].append(sp)
        out["loss_prev"].append(lp)
        h = hist.get(g_)
        if h is None:
            out["n_late8"].append(np.nan); out["sd_dev8"].append(np.nan); out["n_hist8"].append(0)
        else:
            i = np.searchsorted(h[0], d, side="left")
            x = h[1][max(0, i - 8):i]
            out["n_hist8"].append(len(x))
            out["n_late8"].append(float((x >= 5).sum()) if len(x) >= 4 else np.nan)
            out["sd_dev8"].append(float(np.std(x, ddof=1)) if len(x) >= 6 else np.nan)
        out["nt365"].append(cnt(ntd, ck, d - 365 * D1, d))
        cs = covd.get(ck)
        out["k8hist"].append(cs is not None and cs <= d - 180 * D1)
        for nm, it in (("k401", "i401"), ("k402", "i402"), ("k502", "i502"), ("k2056", "i2056")):
            out[nm].append(cnt(items[it], ck, d - 180 * D1, d))
        y = pd.Timestamp(d).year
        out["ins_cov"].append(((ck, y) in pres) or ((ck, y - 1) in pres))
        out["ins_s"].append(cnt(insS, ck, d - 180 * D1, d))
        out["ins_p"].append(cnt(insP, ck, d - 180 * D1, d))
        out["let365"].append(cnt(letd, ck, d - 365 * D1, d))
        out["let3_365"].append(cnt(letd3, ck, d - 365 * D1, d))
        s = sid.get(g_)
        r = ch = np.nan
        if s is not None and sh == sh and sh > 0:
            i = np.searchsorted(s[0], d, side="left") - 1
            if i >= 0 and (d - s[0][i]) <= 45 * D1:
                r = s[1][i] / (sh * 1e6)
                j = np.searchsorted(s[0], d - 90 * D1, side="left") - 1
                if j >= 0 and (d - s[0][j]) <= 150 * D1:
                    ch = r - s[1][j] / (sh * 1e6)
        out["si_ratio"].append(r)
        out["si_chg"].append(ch)
    for k, v in out.items():
        ev[k] = v
    ev["eid"] = np.arange(len(ev))
    pr = L.past_returns(ev, [("mom", -252, -21), ("r1m", -21, 0)])
    ev = ev.merge(pr, on="eid", how="left")
    ev["fq4"] = ev.fqtr == 4
    ev["sic1"] = ev.gvkey.map(CO.sic).astype(str).str[:1]
    print(f"[cond {label}] events {len(ev)}; non-missing: prior SUE {ev.sue_prev.notna().mean():.2f}, delay history {ev.n_late8.notna().mean():.2f}, 8-K history {np.mean(ev.k8hist):.2f}, "
          f"insider data {np.mean(ev.ins_cov):.2f}, short interest {ev.si_ratio.notna().mean():.2f}, momentum {ev.mom.notna().mean():.2f}")
    return ev


DEL = conditions(DEL, "delay")
DEL.to_parquet(L.CACHE / "rdq_events_delay.parquet", index=False)
ANN = conditions(ANN, "ann")
ANN.to_parquet(L.CACHE / "rdq_events_ann.parquet", index=False)
EXP = conditions(EXP, "exp")
EXP.to_parquet(L.CACHE / "rdq_events_exp.parquet", index=False)
print("done")
