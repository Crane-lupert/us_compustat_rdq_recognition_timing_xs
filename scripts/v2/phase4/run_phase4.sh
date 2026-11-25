#!/usr/bin/env bash
# RDQ (SSRN 6965838) phase 4 -- R1 / R2 / R3 pre-specified pilot tests. From Git Bash: bash phase4/run_phase4.sh  (~4 min)
# Reads only: $WRDS_DUMP_DIR/{comp_na_daily_all.fundq,names,namesd; crsp_a_stock.dsenames;
#             ff_all.fivefactors_daily,fivefactors_monthly; tr_ibes.surpsum,id}.csv.gz, ../dsf_v2_slim.parquet,
#             ../dsf_v2_bidask.parquet, ../phase3/out/{link,membership,panel_ext}.parquet. Writes only inside phase4/.
# No external request. Caches in phase4/cache are rebuilt only if missing (delete them to rebuild from the dump).
set -e
CODE="$(cd "$(dirname "$0")" && pwd)"
cd "$RDQ_V2_WORK/RDQ_cadence/phase4"
export PYTHONDONTWRITEBYTECODE=1
mkdir -p out logs cache tmp
python "$CODE/s00_data_checks.py" > logs/s00_data_checks.log 2>&1   # Step 0: inputs, ranges, factor file, fundq extract
python "$CODE/s01_link.py"        > logs/s01_link.log 2>&1          # gvkey-permno link (phase-3 rules, all fundq gvkeys)
python "$CODE/s02_events.py"      > logs/s02_events.log 2>&1        # expected dates, R1 / R3 event sets (no returns)
python "$CODE/s03_r1.py"          > logs/s03_r1.log 2>&1            # R1 + its 'with report' items
python "$CODE/s04_r2.py"          > logs/s04_r2.log 2>&1            # R2 + its 'with report' items
python "$CODE/s05_r3.py"          > logs/s05_r3.log 2>&1            # R3 + its 'with report' items (incl. IBES split)
python "$CODE/s06_qa.py"          > logs/s06_qa.log 2>&1            # look-ahead / double-count checks, independent SQL recomputation
python "$CODE/s07_results.py"     > logs/s07_results.log 2>&1       # out/results.csv, out/summary_primary.csv
echo "phase 4 done"
