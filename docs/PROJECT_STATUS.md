# Project status and handoff

Updated: 2026-09-24. Backend parser repair operationally verified against the production cursor attempted at 22:06:07 UTC / 18:06:07 America/Toronto.

## Current priority

Continue P1/P2/P3 data correctness, official-source coverage and dependable publication under [DEVELOPMENT_PROCESS.md](DEVELOPMENT_PROCESS.md). This is the **backend** workstream. The application-term requirement remains **Lot Size only**. Keep market lot, minimum bid quantity, application amount, listing date and index-admission date distinct. Do not expand downstream research/commercial infrastructure while upstream correctness is blocked.

## VERIFIED: seven retained BSE parser failures repaired — PR #213

PR #213 merged as `224349d83acac08370ab30e9239ffaebab58dabc`; tested head `03fb4536d2d059bda189d7c28ae897031d3db691`. Parser **1.4.0** repairs the seven failures left by cursor6/cursor7. These failures are now closed; do not diagnose or replay them again unless new source evidence demonstrates a regression.

This release recovers **13 discovery references**, not 13 published IPOs. No issuer-specific listing verification, missing-identity reconciliation or new IPO publication was performed for these references. The public dataset and retained recovery were unchanged at **1,109 records**. No UI assets, existing schedules, workflow permissions or commercial features changed.

### Evidence and bounded grammar

A temporary PR-only read-only diagnostic fetched exactly these seven official BSE Index Services detail responses:

`20240624-11`, `20240612-20`, `20240606-11`, `20240205-12`, `20240103-22`, `20231206-8`, `20230719-15`.

Diagnostic run `36064365512` succeeded. Artifact `10834873538`, ZIP SHA-256 `91a0ee3364f198187400b93a4ed1fc6a61e5d108ab66772907a4d43369e5f2b4`, expires `2026-10-08T21:54:47Z`. All seven raw response hashes were checked, and all seven fresh Data-text hashes matched their retained cursor hashes. The old parser returned zero references from every response.

Two notices use **BSE SME Platform** after the venue. Five use ordered shared notice-ID / issuer-ticker lists ending in **respectively**. The additive repair accepts only these demonstrated forms. Shared lists still require equal notice/issuer counts and now explicitly reject duplicate notice IDs or tickers, embedded notice/ticker tokens, misplaced/repeated respectively and leftover prose. Listing statements and valid calendar dates remain mandatory; later index-admission dates are not substituted.

Successfully parsed v1.1/v1.2/v1.3 entries remain compatible. Old-parser failures are selected as an isolated `parser_changed_failure` batch rather than re-fetching successful or unseen notices. The temporary diagnostic workflow was removed before merge.

Changed files:

- `scripts/audit-bse-sme-addition-notices.mjs`
- `scripts/backfill-bse-sme-addition-notices.mjs`
- `scripts/test-audit-bse-sme-addition-notices.mjs`
- `scripts/test-backfill-bse-sme-addition-notices.mjs`
- `scripts/fixtures/bse-cursor7-parser-repair.json`

The fixture preserves literal contiguous normalized clauses, including later index dates, excerpt offsets/hashes, full normalized-text hashes, raw response/Data hashes, collection times and expected discovery references. It is regression evidence, not reviewed IPO listing authority.

### Tests

Passed locally: existing addition-notice parser tests; all seven literal source fixtures; **84 additional fail-closed source mutations**; duplicate-clause checks; cursor selection and real asynchronous migration with mocked network; semantic state merge/idempotency; data validation; synchronized-publication check.

The asynchronous test makes one catalog request and exactly seven failed-notice detail requests, recovers thirteen references, leaves its input immutable, preserves old successful entries exactly and resumes unseen selection only after the repair batch. The complete committed scripts subtree `4a432be45e09fbcf92b23351a9f7266c2ac31d94` matched the locally tested scripts.

Final PR-head CI all passed:

| Check | Run |
| --- | --- |
| Historical BSE cursor/parser | `36065319366` |
| Full IPO data contract | `36065319361` |
| Reviewed BSE evidence/importer | `36065319367` |

### Production verification

Existing merge-triggered backfill run `36065458265` completed successfully:

| Check | Result |
| --- | ---: |
| Selected retained failures | 7 / 7 |
| Selection reason | All parser_changed_failure |
| Parsed notices | 7 / 7 |
| Recovered listing references | 13 |
| Fetch errors | 0 |
| Unparseable notices | 0 |
| Previous successful entries preserved | 153 / 153 |
| Unseen notices fetched in this repair | 0 |

Attempted at `2026-09-24T22:06:07.403Z`; saved by cursor commit `ec995bfe578a0ae0fc5f9a47a236d335f9ef83e9`. Production artifact `10835704482`, ZIP SHA-256 `5adf1b4753991bb328b5969eca935a800000a035b74b8c32d9039c60eefc6ff7`, expires `2026-10-08T22:06:10Z`. Exact report SHA-256: `a2683ae7ec30b949e6316289c4e45a40528b6cff2ae016b5cc44bd276b8a6123`.

The downloaded artifact was hash-checked, all thirteen production references matched the source fixtures, and all seven source-text hashes still matched. An independently reconstructed whole cursor, changing only the seven entries and run metadata, produced Git blob **`0aba996b117374ea2ba4fbeb299144b63ca9cba2`**, exactly matching the saved GitHub cursor. This verifies all 153 prior successes and bootstrap unchanged; applying the same state proposal is idempotent.

Current cursor: parser **1.4.0**, **160 / 236 tracked**, **160 parsed**, **0 failed**, **76 untracked**. Next unseen notice: **`20230503-13`**. The pre-repair report grouped seven stale-parser failures with unseen/parser-changed work; actual untracked notices remained 76 throughout.

Pages deploy `36065458250` succeeded on the parser merge at `2026-09-24T22:06:00Z`. Operational acceptance for this release is the actual saved production cursor, not a new served-IPO-data receipt. A full repository comparison from baseline `f962aba0d70d4ec06878c98b350dea73ef7f480d` to cursor commit `ec995bfe578a0ae0fc5f9a47a236d335f9ef83e9` confirmed no public/recovery data or UI changes.

Durable receipt: [verification/bse-parser-v1.4-2026-09-24.json](verification/bse-parser-v1.4-2026-09-24.json).

## Exact next backend task

**Reconcile the thirteen recovered discovery references before skipping to newer unseen discovery.** Re-read current main, this handoff and the independent cursor first. The references are retained in the seven repaired cursor entries, the source fixture and the durable receipt; do not assume all thirteen represent missing IPOs.

Check the latest **2020-2026** recovery manifests and public dataset using normalized issuer identity, BSE scrip code and listing-source identity. Separate already-present, exact-missing and ambiguous cases. Pin only missing/unambiguous candidates in batches of at most 15, then independently verify their issuer-specific official BSE listing notices. Preserve source URLs, hashes, dates and conflicts. Only after that review should explicit listing date, market lot and final issue price enter reviewed manifests; unsupported fields remain null. Rehearse the real importer/publication, preserve existing records, require an idempotent rerun, then publish and check the actually served dataset.

Index notice parsing is not listing authority. Do not infer unsupported IPO terms or fuzzy-match issuer identities. If independent automation advances beyond this cursor, account for newer pending segments without skipping these recovered references or replaying completed releases.

The seven parser failures are closed. Cursor7 discovery batches20/21 and reviewed batches26/27 are also closed, as are cursor6 discovery batches18/19 and reviewed batches24/25. Broader historical coverage and field completeness remain incomplete. No UI, minimum-investment, billing, accounts, ads, new spending or permission changes belong to this continuation.

## Prior release and separate product workstream

The previous cursor7 reviewed publication remains verified: PR #210 / #211, **1,109 served records**, 18 unique reviewed issuers and 54 matching fields at `2026-09-24T21:37:42Z`. Its historical live evidence remains in [verification/cursor7-live-publication-2026-09-24.json](verification/cursor7-live-publication-2026-09-24.json); no new IPOs were published by the parser repair.

UI V2 was separately completed in PR #209. Its evidence and notes remain in [UI_DESIGN_HANDOFF.md](UI_DESIGN_HANDOFF.md). No UI files changed in this backend unit.

## Preserved history

The entire previous status and README are archived byte-for-byte as [archive/PROJECT_STATUS-before-cursor7-parser-repair.md](archive/PROJECT_STATUS-before-cursor7-parser-repair.md) (original Git blob `05d03ddce3bcb57d785a663111747e5266cc5088`) and [archive/README-before-cursor7-parser-repair.md](archive/README-before-cursor7-parser-repair.md) (blob `b461df24f11b88b5a12750097c8e4d103b620868`). Older archives and release receipts are unchanged. Archived next-task instructions are not current instructions.
