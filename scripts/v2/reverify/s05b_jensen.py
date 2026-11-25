"""s05b: decompose the log-vs-simple gap by leg (V0 repo sample), plus cross-sectional sd and median descriptives."""
import numpy as np, pandas as pd
from common import build_cells, nw_se, OOS_END
P = pd.read_parquet("panel_ret.parquet")
df = build_cells(P)
rows=[]
for H in (120,180):
    df[f"s_{H}"] = np.expm1(df[f"car_{H}"])
    for sz in "LS":
        for it in "HL":
            sub = df[(df.size_bin==sz)&(df.ind_bin==it)&df.q5.isin([1,5])].dropna(subset=[f"car_{H}"])
            g = sub.groupby(["rdq_month","q5"])
            m_log = g[f"car_{H}"].mean().unstack(); m_s = g[f"s_{H}"].mean().unstack()
            sd_log = g[f"car_{H}"].std().unstack(); med = g[f"car_{H}"].median().unstack()
            for name, frame in (("log",m_log),("simple",m_s),("xs_sd_log",sd_log),("median_log",med)):
                frame = frame.copy(); frame.index = frame.index.to_timestamp(); frame = frame[frame.index<=OOS_END]
                for per,(lo,hi) in {"IS":("1999","2016-12-31"),"OOS":("2017","2024-12-31")}.items():
                    f = frame.loc[lo:hi].dropna(); sp = f[1]-f[5]
                    rows.append(dict(cell=f"A{H}-{sz}{it}",per=per,stat=name,Q1=f[1].mean()*100,Q5=f[5].mean()*100,spread=sp.mean()*100,t_nw12=sp.mean()/nw_se(sp.values,12)))
R = pd.DataFrame(rows); pd.set_option("display.width",200)
print(R[R.cell.isin(["A120-LH","A120-SH","A180-LH","A180-SL"])].round(2).to_string(index=False))
R.to_csv("s05b_jensen.csv",index=False)
