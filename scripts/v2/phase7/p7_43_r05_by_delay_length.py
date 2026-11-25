"""Phase 7 - step 43: R05 follow-up (interpretation). Irregular vs regular reporters at delays of 1, 3, 5 and 10 trading days,
full period 2004-2024. Descriptive: the frozen test was the one-day delay; this shows how the picture changes with the length.
Run: python p7_43_r05_by_delay_length.py
"""
import json
import warnings

import numpy as np
import pandas as pd

import p7lib as L

warnings.simplefilter("ignore")
cuts = json.load(open(L.OUT / "rdq_search_cuts.json"))
q1, q2 = cuts["delay1:terc:sd_dev8"]
ev = pd.read_parquet(L.CACHE / "rdq_events_delay.parquet")
ev = ev[(ev.year >= 2004) & ev.stage.isin(["disc", "conf"])].copy()
ev["grp"] = np.where(ev.sd_dev8 > q2, "IRR", np.where(ev.sd_dev8 <= q1, "REG", np.where(ev.sd_dev8.notna(), "MID", "NA")))
for kd in (1, 3, 5, 10):
    D = ev[ev.kd == kd].copy()
    D["eid"] = np.arange(len(D))
    D = D.merge(L.ar_windows(D, [], allow=("disc", "conf"), exit_col="kx"), on="eid")
    lo, hi = cuts[f"delay{kd}:hold"]
    D["y"] = D.ar_hold.clip(lo, hi)
    out = f"   delay of {kd:2d} day(s): events {len(D):6d}"
    for gname in ("IRR", "MID", "REG"):
        x = D[(D.grp == gname) & D.y.notna()]
        m, t, n = L.level_test(x.y.values, L.codes(x.ym.values))
        out += f" | {gname} {m:+.3f}% (t {t:+5.2f}, n {n}, {x.n_hold.mean():.1f} days)"
    z = D[D.grp.isin(["IRR", "REG"]) & D.y.notna()]
    b, t, n1, n0 = L.diff_test(z.y.values, (z.grp == "IRR").astype(float).values, L.codes(z.year.values), L.codes(z.ym.values))
    print(out + f" | IRR - REG {b:+.3f} (t {t:+5.2f})")
    for gname in ("IRR", "REG"):
        x = D[(D.grp == gname) & D.y.notna()]
        print(f"      {gname}: {x.y.sum() / x.n_hold.sum() * 100:+.1f} bp per position-day; share of all events {len(x) / len(D):.2f}")
