# Project status and handoff

Updated: 2026-09-24. Backend release verified at 21:37:42 UTC / 17:37:42 America/Toronto.

## Current priority

Continue P1/P2/P3 data correctness, official-source coverage and dependable publication under [DEVELOPMENT_PROCESS.md](DEVELOPMENT_PROCESS.md). This continuation is **backend only**. The application-term requirement remains **Lot Size only**. Keep market lot, minimum bid quantity, application amount, listing date and index-admission date distinct. Do not expand downstream research/commercial infrastructure while upstream correctness is blocked.

## VERIFIED: cursor7 reviewed publication — PR #210 / #211

The 18 issuers previously source-verified in PR #207 are now reviewed, published and verified in the actually served Pages dataset. Do not repeat cursor7 discovery or publication.

PR #210 merged as `66532672a7f9c84d1fadf96cb0b17b55e87e73a8`. It added only:

- `data/verified-bse-listings/2026-09-24-batch26.json` — 15 issuers;
- `data/verified-bse-listings/2026-09-24-batch27.json` — 3 issuers.

PR #211 merged as `34b39bc9617c013c6e4d7d3955b3de5b5207a5f0`. It changes only the two default manifest selections in the existing read-only publication-verification workflow to batch26 + batch27. No parser, collector, schedule, permission or UI changes were made in this continuation.

### Evidence and safety

Source verification run `36058133127`, artifact `10833780727`, ZIP SHA-256 `553d9350d77756c3f61bac19f563aae15d3c0c7d97b6eebe47da48e7c4e2137c` were retained. All 18 original response hashes and full normalized notice texts were independently checked; strict issuer/code/notice/date/SME identity and all 54 facts were revalidated. The manifests retain literal contiguous normalized-text excerpts, offsets and full-text hashes, not reconstructed evidence prose. Original collection/publication timestamps are preserved.

Canonical listing-PDF archive probes were unavailable. The established strict issuer-specific official BSE HTML contract remains the authority for this batch. Only explicit listing date, market lot and final issue price were added; unsupported fields remain null. The already completed Arrowhead spelling and City Crops office-heading repairs were reused without further grammar changes.

The real isolated importer/publication rehearsal proved **1,091 -> 1,109**, exactly **18 additions**, **167 already-present reviewed entries**, **0 holds**, **0 identity conflicts**, all **1,091 existing records unchanged**, and a byte-idempotent second run.

### Tests and production

Passed locally: listing-verifier guards; reviewed importer, null, conflict and idempotency tests; publication-verifier failure guards; real public-projection mutation tests; real publication rehearsal; data validation and synchronized-publication checks. An independent pure audit of the downloaded live snapshot also matched the workflow receipt exactly.

PR #210 head checks passed: reviewed evidence/importer `36061743219` and full data contract `36061743083`. PR #211 head checks passed: reviewed evidence `36062528447`, data contract `36062528453`, and served-data verifier `36062528384`.

Production sync `36061861729` succeeded, publishing source-backed data commit `92d1ec4498c4ea096cd97b0b0572676e635a7352` and operator-state commit `e4b70f1183b08cba74884fa5ecdb9569f84f9a04`. Operator health was **healthy**.

A direct comparison of the served dataset with the rehearsal baseline found **18 added / 1 changed / 0 removed**. The one existing-record change is `ameya-precision-engineers-limited`: the normal source-first run added SEBI Prospectus filing/PDF document references and updated collection time. No existing IPO term value changed. This is separate from the 18 reviewed additions.

Observed recovery counts: 2020 **51**, 2021 **100**, 2022 **94**, 2023 **192**, 2024 **292**, 2025 **293**, 2026 **87**. Total **1,109**; 2023 increased from **174 to 192**. These are observed counts, not complete-universe claims.

### Actual live verification

Post-merge verifier `36062649127` passed:

| Check | Result |
| --- | ---: |
| Served records | 1,109 |
| Reviewed issuer identities | 18 / 18 unique |
| Listing-date / market-lot / issue-price fields | 54 / 54 matching |
| Failed issuers | 0 |
| Unsupported fields | 6 null fields for every issuer |
| Original document-hash field sources checked in recovery | 54 |
| Document hashes serialized in public field evidence | 0 |

The public projection intentionally omits original document hashes. They were verified in retained recovery; do not describe this as public-document-hash verification.

Snapshot fetched `2026-09-24T21:37:42.271Z`; checked `2026-09-24T21:37:42.328Z`; dataset generated `2026-09-24T21:30:22.442Z`. Snapshot SHA-256: `d52a67d7139071afd85bff4aadad69f9ced956aef385690e12f200a1d9a8d992`.

Live-verification artifact `10835146698`, ZIP SHA-256 `6d6a46359c858b93038da3970ed268d6ca918f6e6b27a323c86fd9beb19ba80a`, expires `2026-10-08T21:37:42Z`. It contains the exact served bytes, full receipt and reproducible source snapshot. Downloaded archive and snapshot hashes were checked; PR and post-merge served snapshots were byte-identical.

Pages deploy workflow `36062649299` succeeded on PR #211's merge at `2026-09-24T21:37:42Z`. The parallel native Pages run `36062648142` was cancelled; it is not reported as a successful check. Actual served-data verification above establishes release success.

Durable receipt: [verification/cursor7-live-publication-2026-09-24.json](verification/cursor7-live-publication-2026-09-24.json).

## Exact next backend task

Re-read latest main, handoff and cursor first. At this handoff the cursor is unchanged: parser **1.3.0**, **160 / 236 tracked**, **153 parsed**, **7 unparseable**, **76 untracked**; updated `2026-09-24T20:00:39.470Z`, Git blob `6ada9ade533cd1dc535799814b7a61bece067d35`.

Perform a bounded official-source/parser-family diagnosis of these retained failures:

`20240624-11`, `20240612-20`, `20240606-11`, `20240205-12`, `20240103-22`, `20231206-8`, `20230719-15`.

Re-fetch only the failed official BSE Index Services detail responses, compare fresh hashes with retained cursor hashes, and group failures by demonstrated syntax. Make only the smallest evidence-backed additive grammar repairs with fail-closed fixtures for missing/ambiguous tickers, mismatched notice/issuer counts, unrelated dates and partial clauses. Preserve already parsed cursor entries and the separate issuer-specific listing-verification requirement. Do not infer issuer identities or IPO terms from failed index notices. If automation has advanced, account for new pending segments without replaying completed work.

Cursor7 discovery batches20/21 and reviewed batches26/27 are fully closed, as are cursor6 discovery batches18/19 and reviewed batches24/25. Broader historical coverage and missing source-backed fields remain incomplete. No UI redesign, minimum-investment work, billing, accounts, ads, new spending or permission changes are part of this handoff.

## Product workstream: explicitly requested UI V2 — 2026-09-24

The new light directory and company-detail UI is **VERIFIED live**, merged in PR **#209** as `8da70a48c95e1b3c267b168fea6ebe49b68f3a76`. It adds compact responsive layouts, working search/year/board/status filters and pagination, source documents, actual timeline dates and expandable term evidence. Public IPO data and recovery/collection behavior are preserved. PR/post-merge browser, data-contract and reviewed-evidence checks passed; Pages deployment `36059729437` succeeded. Live verification at `2026-09-24T21:12:35.691Z` checked 1,091 records, working filters/detail/source documents, no browser errors and matching deployed asset hashes. See [UI_DESIGN_HANDOFF.md](UI_DESIGN_HANDOFF.md) for acceptance checks, files and release evidence.

The backend continuation priority above remains independent of this explicit UI request. That UI observation is historical; the later backend release has 1,109 records. No UI files were changed in the cursor7 publication continuation.

## Preserved history

The complete preceding status and README are archived byte-for-byte as [archive/PROJECT_STATUS-before-cursor7-publication.md](archive/PROJECT_STATUS-before-cursor7-publication.md) (original Git blob `b139f423ef171fd6c24a5747d2d213b608bd1cd0`) and [archive/README-before-cursor7-publication.md](archive/README-before-cursor7-publication.md) (blob `57a179a7ab59bc532846f6888116721f5b9bb549`). Older archives and verification receipts are unchanged. Archived next-task instructions are not current instructions.
