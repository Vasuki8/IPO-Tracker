# Project status and handoff

Updated: 2026-09-24. Backend publication verified through the normal source-backed sync at 2026-09-25 01:01 UTC / 2026-09-24 21:01 America/Toronto.

## Current priority

Continue backend data correctness, official-source coverage and dependable publication under [DEVELOPMENT_PROCESS.md](DEVELOPMENT_PROCESS.md). The application-term requirement remains **Lot Size only**. Keep market lot, minimum bid quantity, application amount, listing date and index-admission date distinct. No UI or downstream commercial-feature work belongs to this continuation.

## VERIFIED: earliest cursor8 segment published — PR #219

PR #219 merged as `7fbd972531154a19624711a10cf77f52dd12bb58`. It publishes the earliest pending cursor8 historical segment: **24 exact-missing issuer identities** from discovery batches23/24 and reviewed batches29/30. The merge adds only five JSON evidence files; no UI, parser, collector, cursor, schedule, permission or hand-edited generated-public-data changes were made.

### Evidence and reconciliation

Source-review run `36072368549`, artifact `10838128680`, ZIP SHA-256 `9dd743faf350732c00a9ec8d30776bf7c61416d5cf6b00bb69c48bc2ea04b172`. The reconciliation checked all seven 2020-2026 recovery manifests plus the then-current 1,122-record public dataset: **24 exact-missing, 0 already-present, 0 identity/code/source conflicts**. Independent issuer-specific BSE verification completed **24/24 verified, 0 rejected/unavailable**, with **72 explicit facts** revalidated.

Canonical listing-PDF probes returned HTTP 404, so the established strict issuer-specific official BSE HTML contract remains the authority. Reviewed evidence preserves original response/document hashes, collection/publication dates, full normalized-text hashes, literal contiguous excerpts and offsets. Only explicit listing date, market lot and final issue price are retained; unsupported terms remain null. The retained unparseable index notice `20221010-15` is not converted into IPO terms.

### Rehearsal and tests

The real isolated publication rehearsal proved **1,122 -> 1,146**, exactly **24 additions**, all **1,122 existing records unchanged**, **198 already-present reviewed entries**, **0 holds/conflicts**, and a byte-idempotent rerun.

PR head `d14314ec13bda745136cc8b34ba09a3d5ea30aca` passed reviewed-evidence CI `36073652069` and full data-contract CI `36073652035`. Post-merge head `7fbd972531154a19624711a10cf77f52dd12bb58` passed full data-contract run `36079891623` and reviewed-evidence run `36079891608`. The source-backed production sync `36079891576` completed successfully and committed generated data as `9cd4824aa7d1cd3c26c6dbce84c8fca1ad58a641`; operator state followed as `7d5e43eada6b7767048871f89ac3a8cb745ab7f4`. Pages deployment for the latest operator-state commit `36080148485` succeeded.

Operator snapshot generated `2026-09-25T01:01:00.530Z` reports overall **healthy**, with NSE collection, SEBI collection, rebuild, validation and repository publication all successful. The source-backed sync also performed independent NSE/SEBI enrichment; do not attribute unrelated generated-data changes to the 24 BSE additions.

## Cursor state and exact next backend task

Current retained BSE SME addition-notice state is parser **1.4.0**, catalog **236 eligible**, **200 tracked**, **199 parsed**, **1 retained unparseable**, **36 untracked**, updated `2026-09-24T23:18:20.858Z`, Git blob `fc8e1ad536246c5d1ab5d816f3fb94faa07941bc`.

The cursor advanced independently while PR #219 was under review. Its following 20-notice segment has **25 discovered references** that are separately pending review/publication. **Next task: reconcile that next pending segment against current recovery/public identities, BSE codes and listing-source identities; independently verify only missing/unambiguous candidates in batches of at most 15; retain reviewed evidence; rehearse safe/idempotent publication; publish through the normal sync; verify served output.** Do not reset or replay the cursor.

The 24 issuers in cursor8 discovery batches23/24 and reviewed batches29/30 are closed. The prior thirteen repaired references (discovery22/reviewed28), cursor7 discovery20/21 reviewed26/27, cursor6 discovery18/19 reviewed24/25 and seven parser failures are also closed. Broader historical coverage and field completeness remain incomplete.

No UI, minimum-investment, billing, accounts, ads, new spending or permission changes belong to this continuation.

## Prior work and preserved history

Parser v1.4.0 remains unchanged; its source fixtures, fail-closed mutations and operational receipt remain at [verification/bse-parser-v1.4-2026-09-24.json](verification/bse-parser-v1.4-2026-09-24.json). UI V2 was separately completed in PR #209; its evidence remains in [UI_DESIGN_HANDOFF.md](UI_DESIGN_HANDOFF.md).

The previous full status is preserved in Git history at blob `4ade0b22a0bf531d5aa1ab67e6dcd858195f148e`; older archive files and receipts remain unchanged. Archived next-task instructions are not current instructions.
