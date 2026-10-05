# October 4 audit closeout — 2026-10-05 UTC

## Status

**ALL FIFTEEN ORIGINAL AUDIT FINDINGS ARE REPAIRED AND MERGED.**

The final defect, BUG-015 document-filter keyboard focus, merged in PR #366 as
`d3e44eb78a8b9f749ef3d21dde9b50daea308def`. Its exact PR head
`9f65259a5dd2183fda9a2be76afdc02fd788de0e` passed the full data-contract,
historical-release, reviewed-BSE and browser/interface gates before merge.

Post-merge Pages run **37352664322** succeeded. The served `data/ipos.json`
matched on the first verification attempt: **1,388 records**, SHA-256
`1741ef733cb06bc6e8d2d466ebd861ab8336996a6e7a69a0751e58dfbe1d3360`.
The DRHP page/assets and main index also matched the deployed revision. Post-merge
data-contract run **37352664476** passed. Post-merge browser/interface run
**37352664386** passed, including the real keyboard document-filter regression.
Pages health was recorded on main as `f2da5f4efc06f3114a6dcf351b6674985e7e3a69`.

## Defect-to-release map

| Audit defect | Repair | Release |
|---|---|---|
| BUG-001 | Admit only supported equity/SME live instruments; exclude retained non-equity projection without deleting recovery evidence | PR #356 / `0e0da6ce` |
| BUG-002 | Typed financial/date/share-quantity domain validation and chronology guards | PR #354 / `be8ec1e0` |
| BUG-003 | Merge evidence-bearing fields as atomic observations under concurrency | PR #354 / `be8ec1e0` |
| BUG-004 | Preserve retained null/cleared decisions, evidence and correction history | PR #354 / `be8ec1e0` |
| BUG-005 | Fail closed on contradictory or ambiguous issuer identity matches | PR #356 / `0e0da6ce` |
| BUG-006 | Retain later official live-term amendments with prior value/evidence history | PR #359 / `18d9b489` |
| BUG-007 | Make cross-year recovery moves identity-atomic across manifests | PR #360 / `0e4aad89` |
| BUG-008 | Retain per-field NSE endpoint provenance and explicit endpoint disagreements | PR #359 / `18d9b489` |
| BUG-009 | Fail closed on empty, malformed or wrong-schema IPO lifecycle data in Pre-IPO | PR #361 / `cd0e98d5` |
| BUG-010 | Prove newly observed live fields keep their new collection clock through publication | PR #363 / `f005a28b` |
| BUG-011 | Ensure published record clocks cannot predate attached evidence; six derived public clocks corrected | PR #364 / `e7394e84` |
| BUG-012 | Isolate SEBI DRHP and Axis fallback collection/health so one source failure does not suppress the other | PR #362 / `fe565c58` |
| BUG-013 | Label lead-manager timestamp-derived Pre-IPO dates visibly as proxy dates with their exact basis | PR #365 / `1e213f69` |
| BUG-014 | Replace production-dependent browser assumptions with deterministic fixtures; duplicate-route focus race fixed separately in the same browser batch | PR #357 / `ea0301aa` |
| BUG-015 | Restore keyboard focus to the selected document filter after its DOM rerender | PR #366 / `d3e44eb7` |

PR #358 is the documentation-only receipt for the preceding browser/admission
releases; it is not a separate audit defect.

## Important boundaries

- SMC Global Securities / SMCG04 remains excluded from the equity-IPO public
  directory because retained NSE series evidence is DEBT. Its recovery evidence is
  preserved.
- BUG-011 changes six **derived public** `last_collected_at` values only. Raw
  recovery records and attached evidence timestamps remain untouched.
- BUG-013 does not change any retained filing date. It exposes when a date is a
  lead-manager document timestamp proxy instead of a direct SEBI filing date.
- The latest DRHP collection can still fail because the upstream SEBI pagination
  surface is unstable. BUG-012 makes that condition fail closed, preserves the
  last good dataset, allows the independent Axis fallback attempt, and reports
  per-source health. Upstream availability itself is not claimed repaired.
- No P5/performance expansion, billing, analytics, ads, spending, contracts,
  permissions or infrastructure migration was introduced by this audit sequence.

## Next bounded work

The October audit is no longer the active blocker.

**SSEK closeout PR #352 remains separate and open.** Its branch predates the
current audit releases. Do not merge it directly from the stale head and do not
replay the old SSEK publication/source collection. First review and refresh its
closeout-only changes onto current `main`, preserve the already retained served
verification evidence, rerun current contracts, then merge only if the queue
advance and temporary-workflow retirement are still exactly bounded to the four
reviewed 2023 issuers.

Historical checkpoints below README/PROJECT_STATUS remain evidence only and must
not be interpreted as instructions to repeat completed releases.
