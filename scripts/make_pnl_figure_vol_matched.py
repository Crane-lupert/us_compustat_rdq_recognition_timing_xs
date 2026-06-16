"""Vol-matched-to-benchmark PnL figure (fig2).

Builds a publication + LinkedIn-quality figure that compares the cadence-
variance long-short strategy (vol-matched) to a long-only universe benchmark
on the same vol footing. Distinct from fig1 (which vol-scaled to a fixed
10pct target, no external benchmark).

Inputs:
  artifacts/panel_with_returns_ext.parquet   -- monthly universe basket (long-only)
  artifacts/strategy_A_pit_clean_monthly.csv -- PIT-clean monthly Q1-Q5 spreads

Output:
  reports/figures/fig2_vs_universe_benchmark.png

The benchmark is "buy the universe basket at each calendar month, hold H days":
the equal-weighted mean forward H-day cumulative log return across all firms
whose rdq falls in that month. This is the natural practitioner benchmark for
an event-anchored strategy because:
  (a) Same cadence (monthly) as the long-short basket.
  (b) Same forward horizon (H days).
  (c) Same opportunity set (universe of firms with announcement in that month).
  (d) Same data source -- avoids data-vendor / index-methodology heterogeneity.

The strategy series is the PIT-clean composite (equal-weighted across the 4
mirror-of-primary cells: A120-SW1-LH, A120-SW1-SH, A180-SW1-LH, A180-SW1-SL).
Vol-matching is at the IN-SAMPLE realized vol of the benchmark, applied to the
full strategy series. This avoids look-ahead in the vol-scaling.

Per checklist §7.6, this figure does NOT overwrite fig1 -- the primary
specification's pre-registered headline remains fig1. fig2 is the
post-hoc PIT-clean live-implementable specification.
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
FIG_DIR = REPO / "reports" / "figures"
FIG_DIR.mkdir(parents=True, exist_ok=True)

IS_END = pd.Timestamp("2016-12-31")
OOS_START = pd.Timestamp("2017-01-01")
OOS_END = pd.Timestamp("2024-12-31")
TC_PER_MONTH = 20 / 10_000  # 20 bps round-trip
PRIMARY_MIRROR = ["A120-SW1-LH", "A120-SW1-SH", "A180-SW1-LH", "A180-SW1-SL"]

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


def vol_match(monthly: pd.Series, target_vol_ann: float, vol_calib_window) -> pd.Series:
    """Scale monthly series to target annualized vol; calibration uses the
    in-sample window only to avoid look-ahead."""
    calib = monthly.loc[vol_calib_window].dropna()
    realized_vol_ann = calib.std(ddof=1) * np.sqrt(12)
    if realized_vol_ann <= 0 or np.isnan(realized_vol_ann):
        return monthly
    scale = target_vol_ann / realized_vol_ann
    return monthly * scale


def cumulative_growth(monthly: pd.Series) -> pd.Series:
    """Additive cumulative return (in percentage points). Same convention as
    V5 make_fig1 -- the per-month observation is an H-day cumulative log
    return, so multiplicative compounding overstates dramatically. Additive
    cumsum is the convention for overlapping-cohort visualizations."""
    return 100.0 * monthly.fillna(0).cumsum()


def main() -> int:
    # ---- 1. Strategy series (PIT-clean composite) ----
    strat_monthly = pd.read_csv(ART / "strategy_A_pit_clean_monthly.csv",
                                index_col="month", parse_dates=True)
    strat_monthly = strat_monthly[strat_monthly.index <= OOS_END]
    composite = strat_monthly[PRIMARY_MIRROR].mean(axis=1, skipna=True)
    composite_net = composite - TC_PER_MONTH

    # ---- 2. Benchmark: universe-basket forward return ----
    # Per rdq_month, equal-weighted mean of car_180_sw1 across all firms in panel.
    # This is "buy each announcing firm at rdq+8, hold for 180d" as a long-only basket.
    panel = pd.read_parquet(ART / "panel_with_returns_ext.parquet")
    panel = panel.dropna(subset=["rdq", "car_180_sw1"])
    panel["rdq_month"] = panel["rdq"].dt.to_period("M")
    universe_monthly = panel.groupby("rdq_month")["car_180_sw1"].mean()
    universe_monthly.index = universe_monthly.index.to_timestamp()
    universe_monthly = universe_monthly[universe_monthly.index <= OOS_END]

    # Align benchmark to strategy index (months that have both)
    common = composite.index.intersection(universe_monthly.index)
    composite = composite.reindex(common)
    composite_net = composite_net.reindex(common)
    universe_monthly = universe_monthly.reindex(common)

    # ---- 3. Vol-match strategy to benchmark IN-SAMPLE vol ----
    is_window = common <= IS_END
    bench_is_vol_ann = float(universe_monthly[is_window].std(ddof=1) * np.sqrt(12))

    composite_vm = vol_match(composite, bench_is_vol_ann, is_window)
    composite_net_vm = vol_match(composite_net, bench_is_vol_ann, is_window)

    # ---- 4. Cumulative growth ----
    cg_strat_vm = cumulative_growth(composite_vm)
    cg_strat_net_vm = cumulative_growth(composite_net_vm)
    cg_bench = cumulative_growth(universe_monthly)

    # ---- 5. Stats ----
    bench_is = universe_monthly[is_window]
    bench_oos = universe_monthly[~is_window]
    strat_vm_is = composite_vm[is_window]
    strat_vm_oos = composite_vm[~is_window]
    strat_net_vm_is = composite_net_vm[is_window]
    strat_net_vm_oos = composite_net_vm[~is_window]

    stats = {
        "bench_is_vol_ann_pct": round(bench_is_vol_ann * 100, 2),
        "bench_is_sharpe_naive": round(annualized_sharpe(bench_is), 3),
        "bench_oos_sharpe_naive": round(annualized_sharpe(bench_oos), 3),
        "bench_is_sharpe_hac": round(annualized_sharpe_hac(bench_is), 3),
        "bench_oos_sharpe_hac": round(annualized_sharpe_hac(bench_oos), 3),
        "strat_vm_is_sharpe_naive": round(annualized_sharpe(strat_vm_is), 3),
        "strat_vm_oos_sharpe_naive": round(annualized_sharpe(strat_vm_oos), 3),
        "strat_vm_is_sharpe_hac": round(annualized_sharpe_hac(strat_vm_is), 3),
        "strat_vm_oos_sharpe_hac": round(annualized_sharpe_hac(strat_vm_oos), 3),
        "strat_net_vm_is_sharpe_hac": round(annualized_sharpe_hac(strat_net_vm_is), 3),
        "strat_net_vm_oos_sharpe_hac": round(annualized_sharpe_hac(strat_net_vm_oos), 3),
        "terminal_strat_vm": round(float(cg_strat_vm.iloc[-1]), 2),
        "terminal_strat_net_vm": round(float(cg_strat_net_vm.iloc[-1]), 2),
        "terminal_bench": round(float(cg_bench.iloc[-1]), 2),
    }

    # ---- 6. Figure ----
    fig = plt.figure(figsize=(9.0, 7.0))
    gs = fig.add_gridspec(2, 1, height_ratios=[2.8, 1.0], hspace=0.45)
    ax = fig.add_subplot(gs[0])
    ax_stats = fig.add_subplot(gs[1])
    ax_stats.axis("off")

    ax.axvspan(common.min(), IS_END, alpha=0.08, color="C0", label="_nolegend_")
    ax.axvspan(OOS_START, OOS_END, alpha=0.12, color="C1", label="_nolegend_")
    ax.axvline(IS_END, color="black", linewidth=0.7, alpha=0.55, linestyle="--")

    ymax = float(max(cg_strat_vm.max(), cg_strat_net_vm.max(), cg_bench.max()))
    ax.text(pd.Timestamp("2005-06-01"), ymax * 0.40,
            "In-sample\n(1999-2016)",
            ha="center", va="top", fontsize=10, color="C0", alpha=0.75,
            fontweight="bold")
    ax.text(pd.Timestamp("2020-06-01"), ymax * 0.93,
            "Out-of-sample\n(2017-2024)",
            ha="center", va="top", fontsize=10, color="C1", alpha=0.90,
            fontweight="bold")

    ax.plot(cg_strat_vm.index, cg_strat_vm.values, color="C0", linewidth=1.9,
            label="PIT-clean long-short, vol-matched to benchmark, gross")
    ax.plot(cg_strat_net_vm.index, cg_strat_net_vm.values, color="C0",
            linewidth=1.4, linestyle=":",
            label="PIT-clean long-short, vol-matched, net of 20 bps/month")
    ax.plot(cg_bench.index, cg_bench.values, color="C3", linewidth=1.6,
            linestyle="--",
            label="Universe long-only basket (180d horizon, buy at rdq+8)")
    ax.axhline(0.0, color="black", linewidth=0.6, alpha=0.4)

    ax.set_ylabel(f"Cumulative additive return (%)\n"
                  f"strategy vol-matched to benchmark "
                  f"({stats['bench_is_vol_ann_pct']:.1f}% ann. in-sample vol)")
    ax.set_title(
        "Cadence-variance long-short (PIT-clean, live-implementable) vs\n"
        "long-only universe benchmark, vol-matched"
    )
    ax.legend(loc="upper left", framealpha=0.93, fontsize=9)
    ax.grid(True, alpha=0.25)
    ax.set_xlabel("Year")

    # ---- 7. Stats panel ----
    stats_table = (
        f"Annualized Sharpe (HAC-corrected, Newey-West lag 12)\n"
        f"                              IS         OOS\n"
        f"Long-only benchmark:      {stats['bench_is_sharpe_hac']:>6.2f}    {stats['bench_oos_sharpe_hac']:>6.2f}\n"
        f"Strategy vol-matched:     {stats['strat_vm_is_sharpe_hac']:>6.2f}    {stats['strat_vm_oos_sharpe_hac']:>6.2f}\n"
        f"Strategy net 20 bp / mo:  {stats['strat_net_vm_is_sharpe_hac']:>6.2f}    {stats['strat_net_vm_oos_sharpe_hac']:>6.2f}\n"
        f"\n"
        f"Vol-match target: in-sample benchmark vol = {stats['bench_is_vol_ann_pct']:.1f}%/yr\n"
        f"(both series on 180d cumulative return scale, monthly cadence,\n"
        f"vol annualized by sqrt(12) -- inflated for overlapping cohorts)\n"
        f"\n"
        f"Terminal cumulative return (additive, vol-matched):\n"
        f"  Strategy gross:   +{stats['terminal_strat_vm']:.0f}%\n"
        f"  Strategy net:     +{stats['terminal_strat_net_vm']:.0f}%\n"
        f"  Benchmark:        +{stats['terminal_bench']:.0f}%\n"
    )
    ax_stats.text(0.00, 1.00, stats_table, transform=ax_stats.transAxes,
                  fontsize=8.4, verticalalignment="top", horizontalalignment="left",
                  family="monospace")

    narrative = (
        "Strategy is the PIT-clean, live-implementable variant:\n"
        " - Quintile rank uses TRAILING 30-day FF12 cohort with strict-less-\n"
        "   than rdq filter (eliminates within-month look-ahead in the\n"
        "   primary backtest specification).\n"
        " - Forward window starts at rdq+8 (absorbs Compustat refresh delay\n"
        "   plus the post-earnings-announcement-drift week).\n"
        " - Composite is equal-weighted across 4 mirror-of-primary cells.\n"
        "Benchmark is the universe long-only basket: buy each announcing\n"
        "firm at rdq+8, hold 180d, equal-weighted across announcers.\n"
        "Both series share the same cadence, horizon, and opportunity set.\n"
        "Vol-matching uses in-sample benchmark vol only (no look-ahead).\n"
        "\n"
        "Note: this PIT-clean specification was not pre-registered. The\n"
        "pre-registered headline (calendar-month grouping, rdq+1 forward\n"
        "window) failed Bonferroni-12 out-of-sample; this variant clears it\n"
        "in 3 of 4 mirror cells -- treated as a post-hoc finding."
    )
    ax_stats.text(0.55, 1.00, narrative, transform=ax_stats.transAxes,
                  fontsize=8.0, verticalalignment="top", horizontalalignment="left")

    fig.subplots_adjust(left=0.08, right=0.97, top=0.93, bottom=0.05)
    out = FIG_DIR / "fig2_vs_universe_benchmark.png"
    fig.savefig(out, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out}")

    out_json = ART / "fig2_vs_universe_benchmark_summary.json"
    out_json.write_text(json.dumps(stats, indent=2, default=str))
    print(f"wrote {out_json}")
    return 0


if __name__ == "__main__":
    main()
