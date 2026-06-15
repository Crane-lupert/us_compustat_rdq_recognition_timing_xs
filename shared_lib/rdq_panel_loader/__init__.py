"""shared_lib/rdq_panel_loader — shared cohort + features for Strategy A and B.

This module saves ~30-40% Phase 0 build cost by providing:
- load_fundq() — reads E:/wrds-data-courier/output/dump/comp_na_daily_all.fundq.csv.gz
- filter_gap_window(df, min_days=10, max_days=180) — drops restated/special-period rows
- rolling_8q_features(df, min_valid=6) — emits gap_var_t (Strategy A) and gap_dev_t (Strategy B)
- ccm_bridge_via_names() — GVKEY↔PERMNO via comp_na_daily_all.names (USAGE-blocked crsp_a_ccm fallback, U44 precedent)
- forward_returns(panel, dsf_v2_path, horizons=(60, 120, 180)) — joins crsp_a_stock.dsf_v2
- exclude_nt_filers(panel, nt_filings_csv) — V5 SEC Form NT mechanical confound mitigation

Skeleton only — implementation in Phase 0 Day-2 per launch SPEC §6.
"""

__version__ = "0.0.1-skeleton"


def load_fundq(path: str = "E:/wrds-data-courier/output/dump/comp_na_daily_all.fundq.csv.gz"):
    """Read Compustat fundamentals quarterly from WRDS local dump.

    Returns:
        pandas DataFrame with columns: gvkey, datadate, rdq, conm, fyearq, fqtr.

    Notes:
        - WRDS dump file 675 MB REAL (snapshot 2026-05-31 §B row 38).
        - No wrds.Connection() — local dump path only per Rule 6.
    """
    raise NotImplementedError("Phase 0 Day-2 implementation")


def filter_gap_window(df, min_days: int = 10, max_days: int = 180):
    """Filter rows by rdq-datadate gap window. Drop restated/special-period rows."""
    raise NotImplementedError("Phase 0 Day-2 implementation")


def rolling_8q_features(df, min_valid: int = 6):
    """Emit gap_var_t (Strategy A) and gap_dev_t (Strategy B) per firm-Q.

    gap_var_t = std({gap_q : q in trailing 8Q, ≥min_valid valid})
    gap_dev_t = gap_t − median({gap_q : q in trailing 8Q, ≥min_valid valid})
    """
    raise NotImplementedError("Phase 0 Day-2 implementation")


def ccm_bridge_via_names(gvkey_list):
    """GVKEY↔PERMNO via comp_na_daily_all.names (USAGE-blocked crsp_a_ccm fallback per U44)."""
    raise NotImplementedError("Phase 0 Day-2 implementation")


def forward_returns(panel, dsf_v2_path: str, horizons=(60, 120, 180)):
    """Join crsp_a_stock.dsf_v2 forward returns for horizons."""
    raise NotImplementedError("Phase 0 Day-2 implementation")


def exclude_nt_filers(panel, nt_filings_csv: str):
    """Drop NT-10K/NT-10Q firm-quarters (V5 confound mitigation)."""
    raise NotImplementedError("Phase 0 Day-2 implementation")
