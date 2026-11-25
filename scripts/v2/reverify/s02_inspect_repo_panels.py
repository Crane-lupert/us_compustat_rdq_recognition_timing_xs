"""s02: inspect the repo's cached panels (read-only)."""
import pandas as pd
from v2paths import V1_ARTIFACTS
ART = V1_ARTIFACTS
for f in ["panel_post_nt_excl", "panel_with_returns", "panel_with_returns_full", "panel_with_returns_ext", "panel_is", "panel_oos"]:
    p = pd.read_parquet(ART + f + ".parquet")
    cars = [c for c in p.columns if c.startswith("car_")]
    print(f, len(p), list(p.columns))
    if cars:
        print("   any car non-null:", int(p[cars].notna().any(axis=1).sum()), {c: int(p[c].notna().sum()) for c in cars})
    print("   cusip8 null:", int(p["cusip8"].isna().sum()) if "cusip8" in p else "n/a",
          " rdq range:", p["rdq"].min(), p["rdq"].max(), " datadate range:", p["datadate"].min(), p["datadate"].max())
p = pd.read_parquet(ART + "panel_with_returns.parquet")
p["yr"] = p["rdq"].dt.year
g = p.groupby("yr").agg(n=("gvkey", "size"), with_ret=("car_120", lambda s: s.notna().sum()))
g["frac"] = (g["with_ret"] / g["n"]).round(3)
print(g.to_string())
