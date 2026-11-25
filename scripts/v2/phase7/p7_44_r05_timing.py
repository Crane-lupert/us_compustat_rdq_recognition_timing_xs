"""Phase 7 - step 44: R05 follow-up (interpretation, written after the confirmation and the 2025 record; descriptive only).

Where in the holding period does the return of the one-day-late firms arise, and how much of the irregular-minus-regular
difference is the eventual length of the delay?

  [1] silence vs announcement: the holding period (entry = close of the first trading day after the expected date, exit =
      close of the day after the announcement, at most 40 days) is split at the close of the day before the announcement.
  [2] how long the silence lasts, by group (no returns).
  [3] holding-period return by eventual lateness (known only afterwards) and group.
Full period 2004-2024 (discovery + confirmation years). Nothing here selects a specification.
Run: python p7_44_r05_timing.py
"""
import json
import warnings

import numpy as np
import pandas as pd

import p7lib as L

warnings.simplefilter("ignore")
cuts = json.load(open(L.OUT / "rdq_search_cuts.json"))
q1, q2 = cuts["delay1:terc:sd_dev8"]
lo, hi = cuts["delay1:hold"]
ev = pd.read_parquet(L.CACHE / "rdq_events_delay.parquet")
D = ev[(ev.kd == 1) & (ev.year >= 2004) & ev.stage.isin(["disc", "conf"])].copy()
D["grp"] = np.where(D.sd_dev8 > q2, "IRR", np.where(D.sd_dev8 <= q1, "REG", np.where(D.sd_dev8.notna(), "MID", "NA")))
D["eid"] = np.arange(len(D))
D = D.merge(L.ar_windows(D, [], allow=("disc", "conf"), exit_col="kx"), on="eid")
D["y"] = D.ar_hold.clip(lo, hi)
D["capped"] = D.kx < D.k_ann + 1                                   # no announcement within 40 days (or the data end)
D["ks"] = np.minimum(np.maximum(D.k_ann - 1, D.k0), D.kx).astype(int)   # last silent day held

# silent part: k0+1 .. ks
S = D[D.ks > D.k0].copy()
a = L.ar_windows(S, [], allow=("disc", "conf"), exit_col="ks").rename(columns={"ar_hold": "ar_sil", "n_hold": "n_sil"})
D = D.merge(a, on="eid", how="left")
D["ar_sil"] = np.where(D.ks > D.k0, D.ar_sil, 0.0)
D["n_sil"] = D.n_sil.fillna(0)
# announcement part: ks+1 .. kx (the announcement day and the next day), only when the announcement is inside the window
A = D[(~D.capped) & (D.kx > D.ks)].copy()
A2 = A[["eid", "permno", "stage", "kx"]].copy()
A2["k0"] = A.ks.values
b = L.ar_windows(A2, [], allow=("disc", "conf"), exit_col="kx").rename(columns={"ar_hold": "ar_ann", "n_hold": "n_ann"})
D = D.merge(b, on="eid", how="left")

print(f"=== R05 timing, 2004-2024: one-day-late events {len(D)}; groups {D.grp.value_counts().to_dict()}; no announcement inside 40 days: {int(D.capped.sum())}")
print("[1] silence vs announcement (percent; each part winsorized at the holding-period cut-offs of the discovery years)")
for part, col, ncol in (("whole holding period", "y", "n_hold"), ("silent days only", "ar_sil", "n_sil"), ("announcement day + next day", "ar_ann", "n_ann")):
    out = f"   {part:28s}"
    for g in ("IRR", "MID", "REG"):
        x = D[(D.grp == g) & D[col].notna()]
        v = x[col].clip(lo, hi).values
        m, t, n = L.level_test(v, L.codes(x.ym.values))
        out += f" | {g} {m:+.3f} (t {t:+5.2f}, n {n}, {x[ncol].mean():.1f} d)"
    z = D[D.grp.isin(["IRR", "REG"]) & D[col].notna()]
    bb, t, n1, n0 = L.diff_test(z[col].clip(lo, hi).values, (z.grp == "IRR").astype(float).values, L.codes(z.year.values), L.codes(z.ym.values))
    print(out + f" | IRR - REG {bb:+.3f} (t {t:+5.2f})")
for g in ("IRR", "REG"):
    x = D[D.grp == g]
    print(f"      {g}: silent days {x.ar_sil.clip(lo, hi).sum() / max(x.n_sil.sum(), 1) * 100:+.1f} bp per position-day over {int(x.n_sil.sum())} days;"
          f" announcement window {x.ar_ann.clip(lo, hi).sum() / max(x.n_ann.sum(), 1) * 100:+.1f} bp per day over {int(x.n_ann.fillna(0).sum())} days")

print("[2] how long the silence lasts after the first missed day (trading days after the expected date; no returns)")
D["late"] = np.where(D.k_ann < 10 ** 7, D.k_ann - D.kE, np.nan)
for g in ("IRR", "MID", "REG"):
    x = D[D.grp == g]
    print(f"   {g}: n {len(x)} | announced by day 2: {np.mean(x.late <= 2):.3f} | by day 3: {np.mean(x.late <= 3):.3f} | still silent after day 3: {np.mean(x.late > 3):.3f}"
          f" | after day 5: {np.mean(x.late > 5):.3f} | after day 10: {np.mean(x.late > 10):.3f} | after day 20: {np.mean(x.late > 20):.3f} | median {x.late.median():.0f}")

print("[3] holding-period return by eventual lateness (percent; lateness is known only afterwards)")
bins = [(2, 2, "2 days"), (3, 3, "3 days"), (4, 5, "4-5 days"), (6, 10, "6-10 days"), (11, 10 ** 6, "11+ days")]
for a_, b_, name in bins:
    out = f"   announced {name:10s}"
    Z = D[(D.late >= a_) & (D.late <= b_) & D.y.notna()]
    for g in ("IRR", "REG"):
        x = Z[Z.grp == g]
        m, t, n = L.level_test(x.y.values, L.codes(x.ym.values))
        out += f" | {g} {m:+.3f} (t {t:+5.2f}, n {n})"
    z = Z[Z.grp.isin(["IRR", "REG"])]
    bb, t, n1, n0 = L.diff_test(z.y.values, (z.grp == "IRR").astype(float).values, L.codes(z.year.values), L.codes(z.ym.values))
    print(out + f" | IRR - REG {bb:+.3f} (t {t:+5.2f})")
# reweighting: the regular group's return if it had the irregular group's distribution of eventual lateness
w = {}
for a_, b_, name in bins:
    xi = D[(D.grp == "IRR") & (D.late >= a_) & (D.late <= b_) & D.y.notna()]
    xr = D[(D.grp == "REG") & (D.late >= a_) & (D.late <= b_) & D.y.notna()]
    w[name] = (len(xi), xi.y.mean(), len(xr), xr.y.mean())
ni = sum(v[0] for v in w.values())
nr = sum(v[2] for v in w.values())
irr = sum(v[0] * v[1] for v in w.values()) / ni
reg = sum(v[2] * v[3] for v in w.values()) / nr
reg_rw = sum(v[0] * v[3] for v in w.values()) / ni
print(f"   IRR mean {irr:+.3f}, REG mean {reg:+.3f}, REG reweighted to the IRR lateness mix {reg_rw:+.3f}"
      f" -> of the difference {irr - reg:+.3f}, lateness mix {reg_rw - reg:+.3f}, within-bin {irr - reg_rw:+.3f}")
