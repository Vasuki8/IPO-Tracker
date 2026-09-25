# Project status and handoff

Updated: 2026-09-25 UTC / 2026-09-24 America/Toronto. Cursor11 publishable records verified on the actually served Pages dataset at 03:28:25 UTC / 23:28:25 Toronto.

## Current priority

Continue backend data correctness, official-source coverage and dependable publication under [DEVELOPMENT_PROCESS.md](DEVELOPMENT_PROCESS.md). The application-term requirement remains **Lot Size only**. Keep market lot, minimum bid quantity, minimum application amount, listing date and index-admission date distinct. No UI or downstream commercial-feature work belongs to this continuation.

## VERIFIED: cursor11 publishable batch — PR #224 / #225

The final previously unseen segment of the retained historical BSE SME notice catalog has been attempted. Its 15 independently verified issuer references are now published and verified live. **Catalog traversal is not complete IPO-universe coverage:** three parser failures, the separate Fabino conflict and broader field/coverage gaps remain unresolved.

### Bounded discovery and reconciliation

Backfill run `36089320357` selected the final **16 unseen notices**, starting at `20210322-22`: **14 parsed, 2 new unparseable, 0 fetch errors, 15 issuer references**. All **220 previously retained notice objects stayed unchanged**. The existing state-driven backfill was triggered through its documented workflow-comment change; no schedule, parser or permission changes were made.

Cursor publication commit: `4a0aa8ee844931fe881b22c9f50bbb0cd77740f9`. Artifact `10844814145`, ZIP SHA-256 `2ccc611617b66f5cfba3a472fa8c38f48371a209f3ef935d78eb934f5996f347`. Downloaded bytes and every retained file hash were checked.

Source-review run `36089473609`, artifact `10845122407`, ZIP SHA-256 `9c7b9e4de903147465b9ee8db6cb93ad13c8b44c6fbe6f62c1a468ac58124e5b`. Exact source snapshot: `f29380424a20ae6de8f6c8efe3be24439e65576b`. All seven 2020-2026 recovery manifests and the 1,193-record public dataset were reconciled: **15 exact-missing identities, 0 already-present, 0 identity/code/source collisions**.

Independent issuer-specific official BSE listing verification passed **15/15 issuers and 45 explicit facts**, with **0 rejected / 0 unavailable**. All nine input file SHA-256/Git-blob pairs and all fifteen original HTML response hashes, normalized texts, identities and facts were independently revalidated locally. Literal contiguous excerpts, offsets, full-text hashes and original publication/collection dates are retained. Unsupported fields remain null.

All 15 canonical listing-PDF archive probes returned HTTP 404. The established strict official HTML listing-notice contract remains the authority; no parser relaxation or inferred terms were used. Local runtime network access was unavailable, so exact Actions source archives supplied the reproducible local checkout and source bytes.

### Release and tests

PR #224 merged as `9b83b943e9d5ef89c1136769825d2053b84bd54c`. Its net diff adds only:

- `data/discovery/bse-listing-candidates-2026-09-25-batch35.json`
- `data/discovery/bse-listing-reconciliation-2026-09-25-cursor11.json`
- `data/verified-bse-listings/2026-09-25-batch35.json`

The temporary read-only review workflow was removed before merge. The exact committed release tree `aedc1ca5b2f3b15553788fedec778ed2569034f3` matches the locally tested tree.

The real isolated publication rehearsal proved **1,193 -> 1,208**, exactly **15 additions**, all **1,193 existing records unchanged**, **269 already-present reviewed entries**, **0 holds/conflicts**, and a byte-idempotent second run. Cursor selection/state/semantic merge, parser fixtures, listing identity/source guards, importer/null/conflict/idempotency, live-verifier mutations, real public projection, synchronized publication and data validation passed locally. A retained-catalog cooldown check selected zero immediate retries and only the three failed notices after cooldown, never parsed notices.

PR #224 head checks passed: reviewed evidence `36090073888`, data contract `36090073895`. Production source-backed sync `36090144644` succeeded, including publication validation. Generated-data commit: `85841109957bf71f7c35e7e7d922bc5f73fbef96`. Operator-state commit: `b5160842d83a11a1f42773d4f2e4ba65cd345617`; snapshot at `2026-09-25T03:26:46.463Z` reports **healthy**, with all collection/rebuild/validation/repository-publication stages successful.

### Actual served-data verification

PR #225 merged as `79d6adcf144a6855d3bb8ca10d75d6cc87d65bce`. It only selects reviewed batch35 in the two existing read-only verifier defaults. PR live run `36090412495`, reviewed-evidence run `36090412512` and data-contract run `36090412491` passed. Canonical post-merge live run **`36090479336`** passed; Pages deployment `36090479309` succeeded.

| Check | Result |
| --- | ---: |
| Actually served records | 1,208 |
| Reviewed issuers, present exactly once | 15 / 15 |
| Listing date / market lot / issue price | 45 / 45 matching |
| Failed issuers | 0 |
| Unsupported fields | 6 null fields per issuer |
| Original document-hash fields checked in recovery | 45 |
| Document hashes serialized in public fields | 0 |

Snapshot fetched `2026-09-25T03:28:25.758Z`; checked `2026-09-25T03:28:25.820Z`; dataset generated `2026-09-25T03:23:30.290Z`. SHA-256: `8139aab00bef2066d00377eca641f1e09f6dec6a6fe1a61d1c7e1ead788c9329`, **6,429,683 bytes**. Post-merge artifact `10845696503`, ZIP SHA-256 `b32706ab6b1142fc64b6db02d677a67f17b30f453f7edb89f5083b5e608f8410`, expires `2026-10-09T03:28:26Z`.

Both downloaded archives and actual served bytes were independently checked. A fresh pure audit reproduced every issuer result, and PR/post-merge served snapshots were byte-identical. Do not call retained-hash verification public-document-hash verification.

The actual served comparison with the rehearsal baseline found **15 added / 2 changed / 0 removed**. KRN Heat Exchanger and Refrigeration and Suyog Gurbaxani Funicular Ropeways only gained SEBI filing/PDF references and collection timestamps. No prior documents were removed and no existing IPO term value changed. This normal source-backed enrichment is separate from the 15 additions.

Observed annual counts: **2020: 63; 2021: 120; 2022: 128; 2023: 216; 2024: 301; 2025: 293; 2026: 87**. This batch adds 12 to 2020 and 3 to 2021. These are observed tracker counts, not full-universe claims.

Durable receipt: [verification/cursor11-live-publication-2026-09-25.json](verification/cursor11-live-publication-2026-09-25.json).

## Remaining blockers and exact next backend task

Current cursor: parser **1.4.0**, **236/236 tracked**, **233 parsed**, **3 retained unparseable**, **0 unseen**, `complete: false`; updated `2026-09-25T03:11:40.548Z`, Git blob `d7b2188e53474edca110ee8272dc56b5b070863b`.

The retained failures are **`20221010-15`**, **`20200813-12`** and **`20200713-20`**, each with `no_parseable_listing_reference`. The latter two are new in cursor11. Their identities, source URLs, text hashes and attempt timestamps remain in cursor state, reconciliation and the receipt.

**Next task: inspect and repair these three retained parser failures as one bounded source-family repair, starting from their original official source text.** Re-read current main and cursor first. Retain source fixtures and add fail-closed regression tests; only change a reusable parser rule when the source supports it. Do not clear or replay successfully parsed history. Reconcile any recovered references against the current multi-year universe; independently verify issuer-specific listing evidence before reviewed import and actual served-data verification.

**Fabino Life Sciences Limited remains separately held and absent from the served snapshot.** BSE code `543444`, notice `20220112-10`: candidate/index date `2022-01-13` conflicts with issuer-notice text `2021-01-13`. Do not infer a correction; publish only after authoritative official evidence resolves it.

Cursor11 discovery/reviewed batch35 is closed. Cursor10 batches33/34, cursor9 batches31/32 and earlier cursor/repaired batches are also closed. Broader historical field completeness and IPO-universe coverage remain incomplete. No UI, minimum-investment, billing, accounts, ads, spending or permissions work belongs here.

## Preserved history

Previous status and README are archived byte-for-byte in [archive/PROJECT_STATUS-before-cursor11-publication.md](archive/PROJECT_STATUS-before-cursor11-publication.md) and [archive/README-before-cursor11-publication.md](archive/README-before-cursor11-publication.md). Earlier receipts and archives remain unchanged; archived next-task instructions are not current instructions. UI V2 stays separate under [UI_DESIGN_HANDOFF.md](UI_DESIGN_HANDOFF.md).
