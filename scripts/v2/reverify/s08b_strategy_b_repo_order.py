"""s08b: Strategy B on the REPO panel row order (repo sign: late - early), a shuffled tie order, and my rebuild order."""
import numpy as np, pandas as pd
from common import quintile_within, nw_se, INDUSTRY_TILT_HIGH
from v2paths import V1_ARTIFACTS
rp = pd.read_parquet(V1_ARTIFACTS + "panel_with_returns.parquet")
def run(panel, label):
    df = panel.dropna(subset=["gap_dev_t","ff12"]).copy(); df["rdq_month"]=df["rdq"].dt.to_period("M")
    df = quintile_within(df, "gap_dev_t", ["rdq_month","ff12"])
    df["mcap_mil"]=df["cshoq"]*df["prccq"]
    df = df.sort_values(["rdq_month","ff12","mcap_mil"], kind="mergesort").reset_index(drop=True)
    med = df.groupby(["rdq_month","ff12"], sort=False)["mcap_mil"].transform("median")
    df["size_bin"]=np.where(df["mcap_mil"]>=med,"L","S"); df["ind_bin"]=np.where(df["ff12"].isin(INDUSTRY_TILT_HIGH),"H","L")
    out=[]
    for H in (60,120,180):
        for sz in "LS":
            for it in "HL":
                sub=df[(df.size_bin==sz)&(df.ind_bin==it)].dropna(subset=[f"car_{H}","q5"])
                m=sub[sub.q5.isin([1,5])].groupby(["rdq_month","q5"])[f"car_{H}"].mean().unstack().dropna()
                sp=m[5]-m[1]
                out.append((f"B{H}-{sz}{it}", round(float(sp.mean()),4), round(float(sp.mean()/nw_se(sp.values,12)),2)))
    print(label, out)
run(rp, "repo order (late-early, repo sign):")
run(rp.sample(frac=1.0, random_state=7).reset_index(drop=True), "shuffled tie order seed 7 (late-early):")
run(pd.read_parquet("panel_ret.parquet"), "my rebuild order (late-early):")
