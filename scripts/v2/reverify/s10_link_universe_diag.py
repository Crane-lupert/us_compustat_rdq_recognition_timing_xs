"""s10: (i) firm-quarters dropped by the repo CUSIP link; (ii) universe composition of the repo return sample."""
import numpy as np, pandas as pd
from common import build_cells
P = pd.read_parquet("panel_ret.parquet"); df = build_cells(P); df["yr"] = df.rdq.dt.year
has_repo = df.car_180.notna(); has_perm = df.pcar_180.notna(); drop = has_perm & ~has_repo
print("permno-link only (dropped by repo link):", int(drop.sum()), " repo-linked:", int(has_repo.sum()), " both:", int((has_perm & has_repo).sum()), " repo-only:", int((has_repo & ~has_perm).sum()))
print("dropped share by period: IS", round(drop[df.yr<=2016].sum()/has_perm[df.yr<=2016].sum(),3), " OOS", round(drop[(df.yr>=2017)&(df.yr<=2024)].sum()/has_perm[(df.yr>=2017)&(df.yr<=2024)].sum(),3))
for q in (1,5):
    m = df.q5==q
    print(f"Q{q}: share dropped {drop[m].sum()/has_perm[m].sum():.3f}; mean simple 180d ret dropped {np.expm1(df.loc[drop&m,'pcar_180']).mean()*100:.2f}% vs kept {np.expm1(df.loc[has_repo&m,'car_180']).mean()*100:.2f}%;"
          f" share <=-50%: dropped {(np.expm1(df.loc[drop&m,'pcar_180'])<=-0.5).mean():.3f} vs kept {(np.expm1(df.loc[has_repo&m,'car_180'])<=-0.5).mean():.3f}")
r = df[has_repo]
print("repo return sample: common-stock flag share", round(r.common.astype(float).mean(),3))
for q in (1,5):
    rq = r[r.q5==q]
    print(f"repo sample Q{q}: entry price<$5 {(rq.prc_entry<5).mean():.3f}, <$1 {(rq.prc_entry<1).mean():.3f}; CRSP cap <$100M {(rq.cap_entry<1e5).mean():.3f}, <$300M {(rq.cap_entry<3e5).mean():.3f}; median cap $M {rq.cap_entry.median()/1e3:.0f}")
