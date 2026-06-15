# Lock F — Pipeline Determinism Audit (STEP 9)

**Date**: 2026-06-16
**Step**: STEP 9 (autopilot prompt)
**Script run**: `bash D:/vscode/meta-harness/scripts/audit-pipeline-determinism.sh .`
**Exit code**: **0** (no critical Pattern A hits)
**Verdict**: **PASS** (with owner-review of 2 SUSPECTED Pattern B hits — both confirmed false positives)

## Pattern-by-pattern result

| Pattern | Description | Severity | Hits | Disposition |
|---|---|---|---|---|
| A | SQL `ANY_VALUE()` | CRITICAL | 0 | clean |
| A' | pandas `groupby.agg(...first)` on classification | HIGH | 0 | clean |
| B | `drop_duplicates()` requiring preceding sort | OWNER-REVIEW | 2 | both clean (see below) |
| C | `.agg("last"/"first")` / `.nth()` requiring preceding sort | OWNER-REVIEW | 0 | clean |

## Pattern B hit review

### Hit 1: `scripts/strategy_A_bonferroni.py:14`

```python
        no groupby.agg first/last/nth without sort; no drop_duplicates without sort.
```

**Type**: docstring text mentioning the rule. Not a real code instance.
**Disposition**: false positive.

### Hit 2: `scripts/subgate_b_crsp_uniformity.py:88`

```python
    df = df.sort_values("gvkey", kind="mergesort").drop_duplicates(
        subset=["gvkey"], keep="last"
    )
```

**Type**: canonical Lock F pattern — explicit `sort_values(..., kind="mergesort")` immediately precedes `drop_duplicates(...)`. Deterministic tie-break.
**Disposition**: false positive.

## Shared_lib Lock F compliance (auxiliary check)

`shared_lib/rdq_panel_loader/__init__.py` review:

| Function | Sort-before-groupby? | Notes |
|---|---|---|
| `load_fundq` | ✅ final `sort_values(["gvkey", "datadate"], kind="mergesort")` before return |
| `filter_gap_window` | n/a (no groupby) | preserves input order via `reset_index(drop=True)` |
| `rolling_8q_features` | ✅ `sort_values(["gvkey", "datadate"], kind="mergesort")` immediately before `groupby("gvkey")` |
| `ccm_bridge_via_names` | ✅ `sort_values("gvkey", kind="mergesort")` before `drop_duplicates(subset=["gvkey"], keep="last")` |
| `exclude_nt_filers` | n/a (no groupby; boolean mask) | order preserved via `reset_index(drop=True)` |
| `forward_returns` | ✅ `sort_values(["cusip8", "dlycaldt"], kind="mergesort")` before `groupby("cusip8")` |

All groupby/rolling/drop_duplicates operations in the shared_lib are preceded by an explicit `kind="mergesort"` sort on the relevant keys.

## Phase 0 close hand-off

Lock F audit exits with code 0. The 2 SUSPECTED Pattern B hits are owner-reviewed as false positives (one docstring text, one canonical Lock F pattern). Combined with the audits in `lock-c.md` (immutability of direction matrix + Bonferroni cell structure), Phase 0 is **Lock F + Lock C + Lock 9 (Rule 9) consistent**.

## Output

- This audit: `audits/2026-06-16-RD1-merged-RD7-lock-f-determinism.md`
- All Phase 0 sub-gates closed (a) through (e) per `audits/2026-06-16-RD1-merged-RD7-phase0-close.md`
