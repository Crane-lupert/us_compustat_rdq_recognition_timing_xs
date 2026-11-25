#!/usr/bin/env bash
# RD1 (SSRN 6965838) phase 3 -- full re-run. From Git Bash: bash phase3/run_phase3.sh   (~8 min)
# Reads only: $WRDS_DUMP_DIR/{comp_na_daily_all.fundq,names,namesd; crsp_a_stock.dsenames,stkdelists;
#             crsp_a_indexes.dsix}.csv.gz, the phase-1/2 caches ../dsf_v2_slim.parquet, ../dsf_v2_bidask.parquet,
#             ../panel_rebuild.parquet, ../panel_ret.parquet (not rebuilt). Writes only inside phase3/.
set -e
CODE="$(cd "$(dirname "$0")" && pwd)"
cd "$RDQ_V2_WORK/RDQ_cadence/phase3"
export PYTHONDONTWRITEBYTECODE=1
mkdir -p out logs step0
# Step 0: phase-1/2 scripts re-run from redirected copies (outputs must equal the phase-1/2 logs)
( cd step0 && python s05_rerun.py > s05_rerun.log 2>&1 && python s08_rerun.py > s08_rerun.log 2>&1 \
  && python s06_rerun.py cusip > s06_rerun_cusip.log 2>&1 )
diff <(grep -v "Warning\|common_mask" ../s05_cell_stats.log) <(grep -v "Warning\|common_mask" step0/s05_rerun.log) > /dev/null && echo "step0 s05 identical"
diff ../s06_calendar_time_cusip.log step0/s06_rerun_cusip.log > /dev/null && echo "step0 s06 identical"
diff ../s08_strategy_b.log step0/s08_rerun.log > /dev/null && echo "step0 s08 identical"
# Phase 3 (parameters: FROZEN_PARAMS.json, deviation DEV1 included)
python "$CODE/p01_panel_ext.py"        > logs/p01_panel_ext.log 2>&1        # signal panel incl. 2025 rows, look-ahead flag, CP deviation
python "$CODE/p02_link_universe.py"    > logs/p02_link_universe.log 2>&1    # PIT CUSIP->permno link, Russell-3000 proxy, entry dates
python "$CODE/p03_cells.py"            > logs/p03_cells.log 2>&1            # duplicate rules + Lock C cells per universe
python "$CODE/p04_calendar_time.py"    > logs/p04_calendar_time.log 2>&1    # calendar-time engine, spread/borrow costs, BH returns
python "$CODE/p05_stats.py"            > logs/p05_stats.log 2>&1            # main 12 cells, B1, B4 composite, D4, pre-registered criteria
python "$CODE/p06_cohort.py"           > logs/p06_cohort.log 2>&1           # B2 (cohort statistic, simple) + B3 (published replica)
python "$CODE/p07_d1_unobserved.py"    > logs/p07_d1_unobserved.log 2>&1    # D1 counts
python "$CODE/p08_d2_cp.py"            > logs/p08_d2_cp.log 2>&1            # D2 Chambers-Penman 3-day
python "$CODE/p09_d3_delist.py"        > logs/p09_d3_delist.log 2>&1        # D3 exploratory delisting LPM
python "$CODE/p10_tables.py"           > logs/p10_tables.log 2>&1           # Step 4 corrected_tables.csv
python "$CODE/qa_engine_check.py"      > logs/qa_engine_check.log 2>&1      # independent recomputation of engine outputs
echo "phase 3 done"
