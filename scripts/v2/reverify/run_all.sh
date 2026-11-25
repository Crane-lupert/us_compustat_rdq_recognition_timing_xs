#!/usr/bin/env bash
# RD1 (SSRN 6965838) re-verification -- full pipeline. Run from this folder in Git Bash: bash run_all.sh
# Reads only: $WRDS_DUMP_DIR/{crsp_a_stock.dsf_v2, comp_na_daily_all.fundq, comp_na_daily_all.names}.csv.gz
#             and (comparison only) <repo>/artifacts/*.parquet|json
# Writes only to this folder. Wall time ~30-40 min (s06 x2 dominate).
set -e
CODE="$(cd "$(dirname "$0")" && pwd)"
cd "$RDQ_V2_WORK/RDQ_cadence"
python "$CODE/s01_extract_dsf_v2.py"          > s01_extract_dsf_v2.log 2>&1
python "$CODE/s01b_extract_dsf_v2_bidask.py"  > s01b.log 2>&1
python "$CODE/s03_rebuild_panel.py"           > s03_rebuild_panel.log 2>&1     # 620,290 rows, exact match to repo panel
python "$CODE/s04_forward_returns.py"         > s04_forward_returns.log 2>&1   # CARs match repo to 4.6e-7; permno link
python "$CODE/s05_cell_stats.py"              > s05_cell_stats.log 2>&1        # 12-cell t: V0 replica + variants V1-V5
python "$CODE/s05b_jensen.py"                 > s05b_jensen.log 2>&1
python "$CODE/s05c_full_panel_2025.py"        > s05c_full_panel_2025.log 2>&1
python "$CODE/s06_calendar_time.py" cusip     > s06_calendar_time_cusip.log 2>&1   # calendar-time Sharpe, repo link
python "$CODE/s06_calendar_time.py" permno    > s06_calendar_time_permno.log 2>&1  # calendar-time Sharpe, permno link
python "$CODE/s07_sharpe_decomposition.py"    > s07_sharpe_decomposition.log 2>&1  # reproduces 1.06/0.87, 1.01/0.82
python "$CODE/s08_strategy_b.py"              > s08_strategy_b.log 2>&1
python "$CODE/s08b_strategy_b_repo_order.py"  > s08b_strategy_b_repo_order.log 2>&1
python "$CODE/s09_skipweek_pit.py"            > s09_skipweek_pit.log 2>&1
python "$CODE/s10_link_universe_diag.py"      > s10_link_universe_diag.log 2>&1
python "$CODE/s11_universe_only_and_fig.py"   > s11_universe_only_and_fig.log 2>&1
python "$CODE/s12_borrow_fix.py"              > s12_borrow_fix.log 2>&1
echo done
