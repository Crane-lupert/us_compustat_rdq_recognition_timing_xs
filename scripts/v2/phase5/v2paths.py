"""Paths for the v2 scripts. Set the environment variables to point at your own copies.

RDQ_V2_WORK        working directory for intermediate tables (not in the repository). The scripts keep the layout of the
                   workspace they were run in: RDQ_cadence/ (CRSP extracts, rounds 1-4) and _main_checks/ (independent
                   checks, rounds 5-7)
WRDS_DUMP_DIR      directory with the WRDS extracts as <schema>.<table>.csv.gz (licensed data; not in the repository)
EDGAR_ARCHIVE_ZIP  zip archive of SEC EDGAR submissions JSON files (sec-data/submissions/CIK##########.json), read by
                   phase7/p7_01_8k_panel.py
SEC_USER_AGENT     User-Agent for the scripts that request data.sec.gov / www.sec.gov (SEC asks automated clients to
                   identify themselves); only the fetch steps read it
"""
import os
from pathlib import Path

_REPO = Path(__file__).resolve().parents[3]
WORK = Path(os.environ.get("RDQ_V2_WORK", str(_REPO / "data" / "v2_work")))
RDQ_DIR = WORK / "RDQ_cadence"
MC_DIR = WORK / "_main_checks"
WRDS_DUMP = os.environ.get("WRDS_DUMP_DIR", str(_REPO / "data" / "wrds_dump")).replace("\\", "/").rstrip("/") + "/"
V1_ARTIFACTS = str(_REPO / "artifacts").replace("\\", "/") + "/"
EDGAR_ARCHIVE = os.environ.get("EDGAR_ARCHIVE_ZIP", str(_REPO / "data" / "edgar_submissions.zip")).replace("\\", "/")
