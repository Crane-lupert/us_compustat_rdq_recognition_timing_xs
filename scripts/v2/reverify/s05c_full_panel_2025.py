"""s05c: Phase-0 full-panel Strategy A cells with vs without the partial-2025 cohorts (repo full panel incl. rdq to 2025-04-10)."""
import pandas as pd
from common import build_cells, monthly_spread, cell_stat
P = pd.read_parquet("panel_ret.parquet"); df = build_cells(P)
for H in (60,120,180):
    for sz in "LS":
        for it in "HL":
            s = monthly_spread(df, f"car_{H}", sz, it)
            a = cell_stat(s); b = cell_stat(s[s.index <= "2024-12-31"])
            print(f"A{H}-{sz}{it}: with 2025 months t={a[1]:.2f} (n={a[2]})  | <=2024-12 t={b[1]:.2f} (n={b[2]})  2025 months: {[round(x,3) for x in s[s.index>'2024-12-31'].values]}")
