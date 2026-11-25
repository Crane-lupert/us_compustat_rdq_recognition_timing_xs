"""Phase 7 - step 41: implementability check for R05 (follow-up, full period 2004-2024).
A trader at the close of E+1 cannot know that a firm will announce after that close. Compustat dates do not tell the time of day,
so the conservative version adds EVERY firm that announced on E+1 as an entered position held for one day (the day after).
This is a lower bound on the size of the effect: half of those firms had in fact already announced before the close.
Run: python p7_41_r05_sameday.py
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
DEL = pd.read_parquet(L.CACHE / "rdq_events_delay.parquet")
DEL = DEL[(DEL.kd == 1) & (DEL.year >= 2004) & DEL.stage.isin(["disc", "conf"])].copy()
DEL["eid"] = np.arange(len(DEL))
DEL = DEL.merge(L.ar_windows(DEL, [], allow=("disc", "conf"), exit_col="kx"), on="eid")
DEL["y"] = DEL.ar_hold.clip(lo, hi)
ANN = pd.read_parquet(L.CACHE / "rdq_events_ann.parquet")
SD = ANN[(ANN.dev_td == 1) & (ANN.year >= 2004) & ANN.stage.isin(["disc", "conf"])].copy()
SD["eid"] = np.arange(len(SD))
SD = SD.merge(L.ar_windows(SD, [("w1", 0, 1)], allow=("disc", "conf")), on="eid")
SD["y"] = SD.ar_w1.clip(lo, hi)
print(f"delay events (silent through E+1): {len(DEL)}; firms that announced on E+1: {len(SD)}")
P = pd.concat([DEL[["y", "sd_dev8", "year", "ym", "rk"]].assign(src="delay"), SD[["y", "sd_dev8", "year", "ym", "rk"]].assign(src="sameday")], ignore_index=True)
P["grp"] = np.where(P.sd_dev8 > q2, "IRR", np.where(P.sd_dev8 <= q1, "REG", np.where(P.sd_dev8.notna(), "MID", "NA")))


def show(d, label):
    out = f"   {label:44s}"
    for gname in ("IRR", "REG"):
        x = d[(d.grp == gname) & d.y.notna()]
        m, t, n = L.level_test(x.y.values, L.codes(x.ym.values))
        out += f" | {gname} {m:+.3f}% (t {t:+5.2f}, n {n})"
    z = d[d.grp.isin(["IRR", "REG"]) & d.y.notna()]
    b, t, n1, n0 = L.diff_test(z.y.values, (z.grp == "IRR").astype(float).values, L.codes(z.year.values), L.codes(z.ym.values))
    print(out + f" | IRR - REG {b:+.3f} (t {t:+5.2f})")


show(P[P.src == "delay"], "as tested (silent through E+1)")
show(P[P.src == "sameday"], "firms that announced on E+1 (one day held)")
show(P, "conservative: both together")
show(P[P.year <= 2013], "conservative, 2004-2013")
show(P[P.year >= 2014], "conservative, 2014-2024")
