# Project status and handoff

Updated: 2026-09-24. Cursor9 publication verified on the actually served GitHub Pages dataset at 2026-09-25 02:28 UTC / 2026-09-24 22:28 America/Toronto.

## Current priority

Continue backend data correctness, official-source coverage and dependable publication under [DEVELOPMENT_PROCESS.md](DEVELOPMENT_PROCESS.md). The active application-term requirement remains **Lot Size only**. Keep market lot, minimum bid quantity, minimum application amount, listing date and index-admission date distinct. No UI or downstream commercial-feature work belongs to this continuation.

## VERIFIED: second retained cursor segment published — PR #220 / #221

PR #220 merged as `3f8bc9086d8ca36f3b7d402c9f614b8e1f0a694d`. It publishes the second retained historical cursor segment: **25 exact-missing BSE SME issuer identities** from discovery batches31/32 and reviewed batches31/32. The release adds only reviewed evidence/reconciliation JSON; no UI, parser, collector, cursor, schedule, permission or hand-edited generated-public-data changes were made.

### Source review and reconciliation

Read-only source-review run `36080905638`, artifact `10841898100`, ZIP SHA-256 `f1303d5adc7cf14dba75e04464a565f9631bef3b9b0b44ae27aa64bb123f6eb0`, source snapshot `027c1bd2382403636110a55929af61da6bb0d307`.

Against the then-current 2020-2026 recovery/public universe (**1,146 records**), reconciliation found **25 exact-missing identities, 0 already-present, 0 identity/code/source conflicts**. Independent issuer-specific official BSE verification completed **25/25 verified, 0 rejected/unavailable**, with **75 explicit facts**: listing date, market lot and final issue price for every issuer.

Canonical listing-PDF archive probes returned HTTP 404. The established strict issuer-specific official BSE HTML contract remains the listing authority. Reviewed evidence preserves original response hashes, collection/publication dates, normalized text and literal contiguous excerpts. Unsupported fields remain null.

### Rehearsal and tests

Exact source-snapshot publication rehearsal proved **1,146 -> 1,171**, exactly **25 additions**, all **1,146 existing records unchanged**, **222 already-present reviewed entries**, **0 holds/conflicts**, and a byte-idempotent rerun.

Relevant importer/evidence tests, reviewed-evidence validation, publication rehearsal, synchronized publication and data-contract checks passed. PR #220 head checks passed before merge. Post-merge source-backed syncs `36081911163` and `36082722423` succeeded; generated-data commits include `a84d4700a1222691a46ba15d46b3f9391a72404d` and `6013bee0e7e44d5b926845638df61b177187de3f`. Latest retained operator state `5333d0029cf2ceb4b6a6358c3118ff5a75750935` reports the collection/rebuild/validation/publication pipeline healthy.

### Actual served-data verification

PR #221 merged as `bd549cc8b1951f6741fe6f6fd5ba11bdc5eacd48` and only changes the existing read-only publication verifier defaults to reviewed batches31/32.

PR-head live verifier run `36086275472` passed. Canonical post-merge live verifier run `36086364954` also passed against the actual Pages dataset:

| Check | Result |
| --- | ---: |
| Actually served records | 1,171 |
| Reviewed issuers | 25 / 25 unique |
| Listing-date / market-lot / issue-price fields | 75 / 75 matching |
| Failed issuers | 0 |
| Unsupported fields | 6 null fields per issuer |
| Retained recovery document-hash fields | 75 |
| Document hashes serialized in public fields | 0 |

Served snapshot fetched `2026-09-25T02:28:12.990Z`; checked `2026-09-25T02:28:13.033Z`; dataset generated `2026-09-25T01:25:57.917Z`. Snapshot SHA-256: `d8549169d7f15e297e6df535d3ce520abb32ab8c50c1b647a9c43839aa4a9f1c`.

Post-merge verification artifact `10844520599`, ZIP SHA-256 `ee80a2b787d46e561f6efe13f76c89784131cf0b4ce199c65f9e97f8fa961df3`. Durable receipt: [verification/cursor9-live-publication-2026-09-25.json](verification/cursor9-live-publication-2026-09-25.json).

## Cursor state and exact next backend task

Current retained BSE SME addition-notice state remains parser **1.4.0**, catalog **236 eligible**, **200 tracked**, **199 parsed**, **1 retained unparseable**, **36 untracked**, updated `2026-09-24T23:18:20.858Z`, Git blob `fc8e1ad536246c5d1ab5d816f3fb94faa07941bc`.

**Next task: continue one bounded historical discovery segment from the first unseen notice after the current retained state.** Use the existing state-driven backfill; do not reset or replay prior progress. Reconcile new references against all current recovery/public identities, BSE codes and listing-source identities. Independently verify only missing/unambiguous candidates in batches of at most 15, retain reviewed evidence, rehearse safe/idempotent publication, publish through the normal source-backed sync, then verify the actually served Pages result.

Cursor9 discovery/reviewed batches31/32 are closed. Cursor8 batches23/24 + reviewed29/30 are closed. Earlier repaired/cursor batches and prior parser repairs are also closed; do not repeat them. Broader historical coverage and field completeness remain incomplete.

No UI, minimum-investment, billing, accounts, ads, new spending or permission changes belong to this continuation.

## Prior work and preserved history

Parser v1.4.0 remains unchanged. UI V2 remains a separate completed workstream under [UI_DESIGN_HANDOFF.md](UI_DESIGN_HANDOFF.md). Older archive files and verification receipts remain unchanged; archived next-task instructions are not current instructions.
