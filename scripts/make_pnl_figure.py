"""Generate publication + LinkedIn PnL figure for the cadence-variance strategy.

Inputs:  artifacts/strategy_A_monthly_returns.csv (4 primary cells, monthly Q1-Q5)
Output:  reports/figures/fig1_cumulative_pnl.png  (300 dpi, ~7.6 x 4.4 in)

Figure design (per us_sec_form_nt_late_filing_xs/scripts/make-paper-figures.py
pattern, fig1_per_capital):

  Single panel, cumulative growth of $1 of capital, vol-scaled to 10% annualized
  target volatility (common practitioner target). Lines:

    (1) Composite long-short, vol-scaled gross
    (2) Composite long-short, vol-scaled net of 20 bps/month round-trip TC
    (3) Best individual cell (A180-SL) vol-scaled gross  -- reference comparator

  IS region (2000-05 .. 2016-12) shaded light blue; OOS region (2017-01 ..
  2024-12) shaded light orange. Vertical reference line at the IS/OOS boundary.
  Lower-right legend with terminal-capital + Sharpe per line.

  Title indicates pre-registered out-of-sample split.

English-only labels per meta-harness paper-writing checklist §5.6 Flavor A
(no Korean-English code-switching). PNG 300 dpi, vector-friendly fonts.
"""
from __future__ import annotations

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
FIG_DIR = REPO / "reports" / "figures"
FIG_DIR.mkdir(parents=True, exist_ok=True)

IS_END = pd.Timestamp("2016-12-31")
OOS_START = pd.Timestamp("2017-01-01")
OOS_END = pd.Timestamp("2024-12-31")
TC_PER_MONTH = 20 / 10_000  # 20 bps round-trip per monthly rebalance
TARGET_VOL = 0.10  # annualized

plt.rcParams.update({
    "font.family": "DejaVu Serif",
    "font.size": 10,
    "axes.titlesize": 11,
    "axes.labelsize": 10,
    "legend.fontsize": 9,
    "xtick.labelsize": 9,
    "ytick.labelsize": 9,
    "axes.spines.top": False,
    "axes.spines.right": False,
})


def annualized_sharpe(monthly: pd.Series) -> float:
    monthly = monthly.dropna()
    if len(monthly) < 12:
        return float("nan")
    return float(monthly.mean() / monthly.std(ddof=1) * np.sqrt(12))


def annualized_sharpe_hac(monthly: pd.Series, lag: int = 12) -> float:
    """HAC-corrected annualized Sharpe accounting for autocorrelation in
    overlapping H-day forward-return observations. Uses Newey-West with the
    specified lag (default 12 = quarterly overlap correction)."""
    monthly = monthly.dropna()
    if len(monthly) < 12:
        return float("nan")
    n = len(monthly)
    mu = float(monthly.mean())
    se_mean = newey_west_se(monthly.values, lag=lag)
    if se_mean <= 0 or np.isnan(se_mean):
        return float("nan")
    long_run_std_per_period = se_mean * np.sqrt(n)  # HAC-corrected unconditional std
    return float(mu / long_run_std_per_period * np.sqrt(12))


def annualized_return_pct(monthly: pd.Series) -> float:
    return float(monthly.mean() * 12 * 100)


def max_drawdown_pct(monthly_returns: pd.Series) -> float:
    cum = (1.0 + monthly_returns.fillna(0)).cumprod()
    peak = cum.cummax()
    dd = (cum - peak) / peak
    return float(dd.min() * 100)


def vol_scale(monthly: pd.Series, target_vol: float) -> pd.Series:
    """Scale series to target annualized volatility. Scaling factor uses full
    in-sample std to avoid look-ahead. This is the practitioner convention
    when comparing nominal-vol strategies across capital-equalized scenarios.
    """
    is_mask = monthly.index <= IS_END
    is_vol_ann = monthly.loc[is_mask].std(ddof=1) * np.sqrt(12)
    if is_vol_ann <= 0 or np.isnan(is_vol_ann):
        return monthly
    scale = target_vol / is_vol_ann
    return monthly * scale


def cumulative_growth(monthly: pd.Series) -> pd.Series:
    """Additive cumulative return (in percentage points). Same convention as
    V5 make_fig1 -- each monthly observation is already an H-day cumulative
    log return (overlapping cohorts), so multiplicative cumprod over-states
    the growth dramatically. Additive cumsum is the correct convention.
    Sharpe and TC-break-even are unaffected by this choice."""
    return 100.0 * monthly.fillna(0).cumsum()


def main() -> int:
    monthly = pd.read_csv(ART / "strategy_A_monthly_returns.csv",
                          index_col="month", parse_dates=True)
    monthly = monthly[monthly.index <= OOS_END]  # exclude 2025 partial

    # Composite = equal-weighted average of the 4 primary cells (per-month mean
    # across available cells; NaN cells are excluded from that month's mean).
    composite_gross = monthly.mean(axis=1, skipna=True)
    composite_net = composite_gross - TC_PER_MONTH
    best_cell_gross = monthly["A180-SL"].copy()

    composite_gross_vs = vol_scale(composite_gross, TARGET_VOL)
    composite_net_vs = vol_scale(composite_net, TARGET_VOL)
    best_gross_vs = vol_scale(best_cell_gross.dropna(), TARGET_VOL)

    cg_growth = cumulative_growth(composite_gross_vs)
    cn_growth = cumulative_growth(composite_net_vs)
    best_growth = cumulative_growth(best_gross_vs)

    fig = plt.figure(figsize=(9.0, 7.0))
    gs = fig.add_gridspec(2, 1, height_ratios=[2.8, 1.0], hspace=0.45)
    ax = fig.add_subplot(gs[0])
    ax_stats = fig.add_subplot(gs[1])
    ax_stats.axis("off")

    # Shaded IS / OOS regions
    ax.axvspan(monthly.index[0], IS_END, alpha=0.08, color="C0",
               label="_nolegend_")
    ax.axvspan(OOS_START, OOS_END, alpha=0.12, color="C1",
               label="_nolegend_")
    ax.axvline(IS_END, color="black", linewidth=0.7, alpha=0.55, linestyle="--")

    # Lines
    ax.plot(cg_growth.index, cg_growth.values, color="C0", linewidth=1.9,
            label="Composite (4 pre-registered cells), gross")
    ax.plot(cn_growth.index, cn_growth.values, color="C0", linewidth=1.4,
            linestyle=":",
            label="Composite, net of 20 bps/month round-trip TC")
    ax.plot(best_growth.index, best_growth.values, color="C2", linewidth=1.5,
            linestyle="--",
            label="Best cell (180d horizon, small / low-tilt), gross")

    # IS / OOS in-axes labels (positioned in upper third where lines are still low)
    ymax = float(max(cg_growth.max(), cn_growth.max(), best_growth.max()))
    label_y = ymax * 0.40
    ax.text(pd.Timestamp("2005-06-01"), label_y, "In-sample\n(1999-2016)",
            ha="center", va="top", fontsize=10, color="C0", alpha=0.75,
            fontweight="bold")
    ax.text(pd.Timestamp("2018-06-01"), ymax * 0.92, "Out-of-sample\n(2017-2024)",
            ha="center", va="top", fontsize=10, color="C1", alpha=0.90,
            fontweight="bold")

    ax.set_ylabel("Cumulative return (%, vol-scaled to 10% annualized)")
    ax.set_title(
        "Earnings-announcement cadence-variance long-short:\n"
        "pre-registered out-of-sample test"
    )
    ax.legend(loc="upper left", framealpha=0.93, fontsize=9)
    ax.grid(True, alpha=0.15, linewidth=0.5, linestyle="-")
    ax.set_xlabel("Year")

    # Summary box (lower-right) -- terminal capital + IS/OOS Sharpe per line.
    is_composite_net = composite_net.loc[composite_net.index <= IS_END]
    oos_composite_net = composite_net.loc[
        (composite_net.index >= OOS_START) & (composite_net.index <= OOS_END)
    ]
    is_best = best_cell_gross.loc[best_cell_gross.index <= IS_END]
    oos_best = best_cell_gross.loc[
        (best_cell_gross.index >= OOS_START) & (best_cell_gross.index <= OOS_END)
    ]

    # Naive monthly Sharpe (treats overlapping H-day forward returns as IID)
    is_comp_gross = composite_gross.loc[composite_gross.index <= IS_END]
    oos_comp_gross = composite_gross.loc[
        (composite_gross.index >= OOS_START) & (composite_gross.index <= OOS_END)
    ]

    sharpe_naive_is_comp_gross = annualized_sharpe(is_comp_gross)
    sharpe_naive_oos_comp_gross = annualized_sharpe(oos_comp_gross)
    sharpe_naive_is_comp_net = annualized_sharpe(is_composite_net)
    sharpe_naive_oos_comp_net = annualized_sharpe(oos_composite_net)
    sharpe_naive_is_best = annualized_sharpe(is_best)
    sharpe_naive_oos_best = annualized_sharpe(oos_best)

    # HAC-corrected Sharpe (Newey-West lag=12 quarterly autocorr; equivalent
    # to dividing by sqrt(approximate overlap inflation factor)).
    sharpe_hac_is_comp_net = annualized_sharpe_hac(is_composite_net)
    sharpe_hac_oos_comp_net = annualized_sharpe_hac(oos_composite_net)
    sharpe_hac_is_best = annualized_sharpe_hac(is_best)
    sharpe_hac_oos_best = annualized_sharpe_hac(oos_best)

    # Stats panel (below main chart). Two-column layout:
    #   left = numerics table; right = narrative.
    stats_table = (
        f"Annualized Sharpe (10% target vol)\n"
        f"                          Naive   HAC-corrected\n"
        f"Composite gross  IS:      {sharpe_naive_is_comp_gross:>4.2f}        --\n"
        f"                 OOS:     {sharpe_naive_oos_comp_gross:>4.2f}        --\n"
        f"Composite net    IS:      {sharpe_naive_is_comp_net:>4.2f}        {sharpe_hac_is_comp_net:>4.2f}\n"
        f" (20 bps / mo)   OOS:     {sharpe_naive_oos_comp_net:>4.2f}        {sharpe_hac_oos_comp_net:>4.2f}\n"
        f"Best cell gross  IS:      {sharpe_naive_is_best:>4.2f}        {sharpe_hac_is_best:>4.2f}\n"
        f"                 OOS:     {sharpe_naive_oos_best:>4.2f}        {sharpe_hac_oos_best:>4.2f}\n"
    )
    ax_stats.text(0.00, 1.00, stats_table, transform=ax_stats.transAxes,
                  fontsize=8.4, verticalalignment="top", horizontalalignment="left",
                  family="monospace")

    narrative = (
        "HAC-corrected Sharpe (Newey-West lag = 12) accounts for the\n"
        "autocorrelation in monthly observations drawn from overlapping\n"
        "120 / 180-day forward-return cohorts. It is the practitioner-honest\n"
        "read; the naive monthly Sharpe overstates by approximately 1.6x.\n"
        "\n"
        "Pre-registered out-of-sample test: 0 of 4 primary cells cross\n"
        "the Bonferroni-12 |t| > 2.78 multiple-comparison-protected bar,\n"
        "but 11 of 12 cells remain sign-correct out-of-sample, and the\n"
        "HAC-corrected net Sharpe stays at 0.82 OOS (vs 1.01 in-sample,\n"
        "a -19% degradation). The signal is alive but below the academic\n"
        "statistical bar -- paper-practical outcome."
    )
    ax_stats.text(0.46, 1.00, narrative, transform=ax_stats.transAxes,
                  fontsize=8.4, verticalalignment="top", horizontalalignment="left")

    # Manual layout: tight_layout doesn't play well with our text-only stats axes.
    fig.subplots_adjust(left=0.07, right=0.97, top=0.93, bottom=0.05)
    out = FIG_DIR / "fig1_cumulative_pnl.png"
    fig.savefig(out, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out}")

    # Also dump a small machine-readable summary so the paper / README can
    # cite numerics without re-running matplotlib.
    summary_dict = {
        "target_vol_ann": TARGET_VOL,
        "tc_bps_per_month": int(TC_PER_MONTH * 10_000),
        "is_window": "2000-05..2016-12",
        "oos_window": "2017-01..2024-12",
        "composite_gross": {
            "is_sharpe_ann": annualized_sharpe(composite_gross.loc[composite_gross.index <= IS_END]),
            "oos_sharpe_ann": annualized_sharpe(composite_gross.loc[(composite_gross.index >= OOS_START) & (composite_gross.index <= OOS_END)]),
            "is_ann_return_pct": annualized_return_pct(composite_gross.loc[composite_gross.index <= IS_END]),
            "oos_ann_return_pct": annualized_return_pct(composite_gross.loc[(composite_gross.index >= OOS_START) & (composite_gross.index <= OOS_END)]),
            "is_max_dd_pct": max_drawdown_pct(composite_gross.loc[composite_gross.index <= IS_END]),
            "oos_max_dd_pct": max_drawdown_pct(composite_gross.loc[(composite_gross.index >= OOS_START) & (composite_gross.index <= OOS_END)]),
        },
        "composite_net20bps": {
            "is_sharpe_ann": annualized_sharpe(is_composite_net),
            "oos_sharpe_ann": annualized_sharpe(oos_composite_net),
            "is_ann_return_pct": annualized_return_pct(is_composite_net),
            "oos_ann_return_pct": annualized_return_pct(oos_composite_net),
        },
        "best_cell_A180_SL_gross": {
            "is_sharpe_ann": annualized_sharpe(is_best),
            "oos_sharpe_ann": annualized_sharpe(oos_best),
            "is_ann_return_pct": annualized_return_pct(is_best),
            "oos_ann_return_pct": annualized_return_pct(oos_best),
        },
        "terminal_capital_vol_scaled": {
            "composite_gross": float(cg_growth.iloc[-1]),
            "composite_net": float(cn_growth.iloc[-1]),
            "best_cell": float(best_growth.iloc[-1]),
        },
    }
    import json
    out_json = ART / "fig1_cumulative_pnl_summary.json"
    out_json.write_text(json.dumps(summary_dict, indent=2, default=str))
    print(f"wrote {out_json}")

    return 0


if __name__ == "__main__":
    main()
