"""Vol-matched-to-LS-benchmark PnL figure (fig2).

Same strategy as fig1 (composite of the 4 pre-registered primary cells in the
primary specification: calendar-month FF12 cross-section, rdq+1 forward window).
The only differences from fig1 are:
  (1) the vol target -- here, the in-sample annualized vol of the FF5+UMD
      tangent benchmark, rather than fig1's 10% fixed target;
  (2) the comparator -- here, the FF5+UMD tangent (a long-short factor-model
      benchmark on the same vol footing), rather than fig1's strategy-only view.

Both strategy and benchmark are long-short by construction.

Inputs:
  artifacts/strategy_A_monthly_returns.csv  -- monthly Q1-Q5 spread per primary cell
  data/ff5_umd_monthly.jsonl                -- FF5 + UMD monthly returns (% per month)

Output:
  reports/figures/fig2_vs_ff5umd_tangent.png
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

REPO = Path("d:/vscode/us_compustat_rdq_recognition_timing_xs")
sys.path.insert(0, str(REPO / "scripts"))
from strategy_A_bonferroni import newey_west_se  # type: ignore  # noqa: E402

ART = REPO / "artifacts"
DATA = REPO / "data"
FIG_DIR = REPO / "reports" / "figures"
FIG_DIR.mkdir(parents=True, exist_ok=True)

IS_END = pd.Timestamp("2016-12-31")
OOS_START = pd.Timestamp("2017-01-01")
OOS_END = pd.Timestamp("2024-12-31")
TC_PER_MONTH = 20 / 10_000  # 20 bps round-trip
PRIMARY_CELLS = ["A120-LH", "A120-SH", "A180-LH", "A180-SL"]
FACTORS = ["Mkt-RF", "SMB", "HML", "RMW", "CMA", "MOM"]

plt.rcParams.update({
    "font.family": "DejaVu Serif",
    "font.size": 10,
    "axes.titlesize": 12,
    "axes.labelsize": 10,
    "legend.fontsize": 9,
    "xtick.labelsize": 9,
    "ytick.labelsize": 9,
    "axes.spines.top": False,
    "axes.spines.right": False,
})


def annualized_sharpe_hac(monthly: pd.Series, lag: int = 12) -> float:
    monthly = monthly.dropna()
    if len(monthly) < 12:
        return float("nan")
    n = len(monthly)
    mu = float(monthly.mean())
    se_mean = newey_west_se(monthly.values, lag=lag)
    if se_mean <= 0 or np.isnan(se_mean):
        return float("nan")
    long_run_std_per_period = se_mean * np.sqrt(n)
    return float(mu / long_run_std_per_period * np.sqrt(12))


def load_ff5umd_monthly() -> pd.DataFrame:
    rows = [json.loads(l) for l in (DATA / "ff5_umd_monthly.jsonl").open(encoding="utf-8")]
    df = pd.DataFrame(rows)
    # FF returns are in percentage points; convert to fractional
    for c in FACTORS + ["RF"]:
        df[c] = df[c].astype(float) / 100.0
    df["month"] = pd.to_datetime(df["year_month"] + "-01")
    df = df.set_index("month").sort_index()
    return df


def tangent_weights(returns: pd.DataFrame) -> np.ndarray:
    """In-sample max-Sharpe tangent weights for the FF5+UMD basket. Standard
    closed form: w proportional to Sigma^{-1} mu. Normalized to sum to one
    (unitary leverage)."""
    mu = returns.mean().values
    sigma = returns.cov().values
    raw = np.linalg.solve(sigma, mu)
    w = raw / raw.sum()
    return w


def main() -> int:
    # ---- 1. Strategy: primary specification composite (same as fig1) ----
    strat_monthly = pd.read_csv(ART / "strategy_A_monthly_returns.csv",
                                index_col="month", parse_dates=True)
    strat_monthly = strat_monthly[strat_monthly.index <= OOS_END]
    # Drop any trailing all-NaN rows so cumsum does not extend with flat fills.
    strat_monthly = strat_monthly.dropna(how="all")
    composite = strat_monthly[PRIMARY_CELLS].mean(axis=1, skipna=True).dropna()
    composite_net = composite - TC_PER_MONTH

    # ---- 2. FF5+UMD factors and IS-optimal tangent ----
    ff = load_ff5umd_monthly()
    common = composite.index.intersection(ff.index)
    composite = composite.reindex(common)
    composite_net = composite_net.reindex(common)
    ff_aligned = ff.loc[common, FACTORS]

    is_mask = common <= IS_END
    oos_mask = (common >= OOS_START) & (common <= OOS_END)

    w_tan = tangent_weights(ff_aligned.loc[is_mask])
    tangent = pd.Series(ff_aligned.values @ w_tan, index=common, name="Tangent")

    # ---- 3. Vol-match strategy to in-sample tangent vol ----
    tan_is_vol_ann = float(tangent[is_mask].std(ddof=1) * np.sqrt(12))
    strat_is_vol_ann = float(composite[is_mask].std(ddof=1) * np.sqrt(12))
    scale = tan_is_vol_ann / strat_is_vol_ann

    strat_vm = composite * scale
    strat_net_vm = composite_net * scale

    # ---- 3a. Residual alpha vs FF5+UMD: strategy - betahat * factors ----
    # Regress vol-matched strategy (net) on FF5+UMD factors with intercept;
    # the residual series alpha_t = strategy_t - betahat * factors_t is the
    # part of the strategy return that the factor model does not explain.
    # This is V5 make_fig1's "residual alpha trail" convention.
    y_net = strat_net_vm.loc[is_mask].dropna().values
    X_is = np.column_stack([np.ones(int(is_mask.sum())), ff_aligned.loc[is_mask].values])
    # Lstsq on IS to get betas; apply to FULL series for OOS residual trail.
    beta = np.linalg.lstsq(X_is, strat_net_vm.loc[is_mask].values, rcond=None)[0]
    intercept = beta[0]
    factor_betas = beta[1:]
    # Factor-spanned monthly return (excluding intercept):
    factor_spanned = pd.Series(ff_aligned.values @ factor_betas, index=common)
    residual_alpha = strat_net_vm - factor_spanned  # = intercept + residual_t in IS

    # ---- 4. Cumulative additive return ----
    cg_strat_vm = 100.0 * strat_vm.fillna(0).cumsum()
    cg_strat_net_vm = 100.0 * strat_net_vm.fillna(0).cumsum()
    cg_tan = 100.0 * tangent.fillna(0).cumsum()
    cg_alpha = 100.0 * residual_alpha.fillna(0).cumsum()

    # ---- 5. Sharpes ----
    stats = {
        "tan_is_vol_ann_pct": round(tan_is_vol_ann * 100, 2),
        "tan_is_sharpe": round(annualized_sharpe_hac(tangent[is_mask]), 2),
        "tan_oos_sharpe": round(annualized_sharpe_hac(tangent[oos_mask]), 2),
        "strat_vm_is_sharpe": round(annualized_sharpe_hac(strat_vm[is_mask]), 2),
        "strat_vm_oos_sharpe": round(annualized_sharpe_hac(strat_vm[oos_mask]), 2),
        "strat_net_vm_is_sharpe": round(annualized_sharpe_hac(strat_net_vm[is_mask]), 2),
        "strat_net_vm_oos_sharpe": round(annualized_sharpe_hac(strat_net_vm[oos_mask]), 2),
        "residual_alpha_is_sharpe": round(annualized_sharpe_hac(residual_alpha[is_mask]), 2),
        "residual_alpha_oos_sharpe": round(annualized_sharpe_hac(residual_alpha[oos_mask]), 2),
        "ff5umd_intercept_monthly_pct": round(float(intercept) * 100, 3),
        "ff5umd_intercept_annualized_pct": round(float(intercept) * 12 * 100, 2),
        "ff5umd_betas": {f: round(float(b), 3) for f, b in zip(FACTORS, factor_betas)},
        "terminal_strat_vm": round(float(cg_strat_vm.iloc[-1])),
        "terminal_strat_net_vm": round(float(cg_strat_net_vm.iloc[-1])),
        "terminal_tan": round(float(cg_tan.iloc[-1])),
        "terminal_residual_alpha": round(float(cg_alpha.iloc[-1])),
        "tangent_weights": {f: round(float(w), 3) for f, w in zip(FACTORS, w_tan)},
    }

    # ---- 6. Figure: single panel, minimal legend ----
    fig, ax = plt.subplots(figsize=(8.4, 4.8))
    ax.axvspan(common.min(), IS_END, alpha=0.07, color="C0")
    ax.axvspan(OOS_START, OOS_END, alpha=0.11, color="C1")
    ax.axvline(IS_END, color="black", linewidth=0.7, alpha=0.55, linestyle="--")

    ax.plot(cg_strat_vm.index, cg_strat_vm.values, color="C0", linewidth=1.9,
            label="Strategy")
    ax.plot(cg_strat_net_vm.index, cg_strat_net_vm.values, color="C0",
            linewidth=1.3, linestyle=":",
            label="Strategy, net of 20 bps/month")
    ax.plot(cg_tan.index, cg_tan.values, color="C3", linewidth=1.5,
            linestyle="--",
            label="FF5+UMD tangent (in-sample max-Sharpe)")
    ax.plot(cg_alpha.index, cg_alpha.values, color="C2", linewidth=1.5,
            linestyle="-.",
            label=r"Residual $\alpha$ (strategy net minus FF5+UMD factor span)")

    ymax = float(max(cg_strat_vm.max(), cg_tan.max(), cg_alpha.max()))
    ymin = float(min(cg_strat_vm.min(), cg_tan.min(), cg_alpha.min(), 0))
    pad = (ymax - ymin) * 0.10
    ax.set_ylim(ymin - pad, ymax + pad)

    # IS / OOS labels (placed in low-density chart area)
    ax.text(pd.Timestamp("2007-06-01"), ymax * 0.05, "In-sample",
            ha="center", va="bottom", fontsize=10, color="C0", alpha=0.75,
            fontweight="bold")
    ax.text(pd.Timestamp("2020-06-01"), ymax * 0.05, "Out-of-sample",
            ha="center", va="bottom", fontsize=10, color="C1", alpha=0.90,
            fontweight="bold")

    # Inline compact Sharpe annotation (3 lines, near top-left under legend)
    sharpe_text = (
        f"HAC-corrected Sharpe (IS / OOS):\n"
        f"   Strategy:                  {stats['strat_vm_is_sharpe']:.2f} / {stats['strat_vm_oos_sharpe']:.2f}\n"
        f"   Strategy, net:             {stats['strat_net_vm_is_sharpe']:.2f} / {stats['strat_net_vm_oos_sharpe']:.2f}\n"
        f"   FF5+UMD tangent:           {stats['tan_is_sharpe']:.2f} / {stats['tan_oos_sharpe']:.2f}\n"
        f"   Residual alpha:            {stats['residual_alpha_is_sharpe']:.2f} / {stats['residual_alpha_oos_sharpe']:.2f}\n"
        f"FF5+UMD intercept (IS net): {stats['ff5umd_intercept_annualized_pct']:.1f} % / yr"
    )
    ax.text(0.022, 0.62, sharpe_text, transform=ax.transAxes,
            fontsize=8.6, verticalalignment="top", horizontalalignment="left",
            family="monospace",
            bbox=dict(boxstyle="round,pad=0.35", facecolor="white",
                      edgecolor="lightgray", alpha=0.92))

    ax.set_xlabel("Year")
    ax.set_ylabel(
        f"Cumulative return (%, vol-matched to {stats['tan_is_vol_ann_pct']:.1f}% in-sample)"
    )
    ax.set_title("Cadence-variance long-short vs FF5+UMD tangent")
    ax.legend(loc="upper left", framealpha=0.92, fontsize=9)
    ax.grid(True, alpha=0.15, linewidth=0.5, linestyle="-")

    fig.tight_layout()
    out = FIG_DIR / "fig2_vs_ff5umd_tangent.png"
    fig.savefig(out, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out}")

    out_json = ART / "fig2_vs_ff5umd_tangent_summary.json"
    out_json.write_text(json.dumps(stats, indent=2, default=str))
    print(f"wrote {out_json}")
    return 0


if __name__ == "__main__":
    main()
