# Project status and handoff

Updated: 2026-09-24. Backend publication verified at 22:57:35 UTC / 18:57:35 America/Toronto.

## Current priority

Continue backend data correctness, official-source coverage and dependable publication under [DEVELOPMENT_PROCESS.md](DEVELOPMENT_PROCESS.md). The application-term requirement remains **Lot Size only**. Keep market lot, minimum bid quantity, application amount, listing date and index-admission date distinct. No UI or downstream commercial-feature work belongs to this continuation.

## VERIFIED: thirteen repaired cursor7 references published — PR #215 / #216

The thirteen references recovered by parser v1.4.0 are now reconciled, independently source-verified, reviewed, published and verified in the actually served Pages dataset. This segment is closed; do not repeat it.

PR #215 merged as `45eab356842ecd49895642133fc2e3eab1d0c427`. It added only three evidence files:

- `data/discovery/bse-listing-candidates-2026-09-24-batch22.json`
- `data/discovery/bse-listing-reconciliation-2026-09-24-cursor7-repaired.json`
- `data/verified-bse-listings/2026-09-24-batch28.json`

PR #216 merged as `f41557347c204fda3f8f297e4ed23f1267b39d49`. It changes only the two default manifest selections in the existing read-only publication verifier to batch28. No parser, UI, collector, cursor, schedule or permission changes were made in this unit. Generated IPO data was published by the existing source-backed sync, not hand-edited.

### Evidence and reconciliation

Source review run `36068697382` checked all seven 2020-2026 recovery manifests and the committed public dataset at baseline `e7781f054568732ef489fd419f27d379ebfdef5f`: **1,109 records; 13 exact-missing identities; 0 already-present; 0 ambiguous/code/source collisions**. Issuer-specific BSE verification completed **13/13 verified, 0 rejected/unavailable**. No fuzzy identity matching or parser relaxation was needed.

Artifact `10837695329`, ZIP SHA-256 `b6d7f8ab62eadf63352dfaf2e1b82271864756dce3625864f71a717d429e6d1d`, expires `2026-10-08T22:40:51Z`. The downloaded archive, all ten snapshot hashes, all thirteen original HTTP response hashes and all 39 extracted facts were independently checked. Reviewed evidence uses literal contiguous normalized-text excerpts with offsets and full-text hashes. Collection/publication dates were preserved rather than replaced with release time.

Canonical listing-PDF archive probes returned HTTP 404. The established strict issuer-specific official BSE HTML contract remains the authority. Only explicit listing date, market lot and final issue price were retained; six unsupported terms per issuer remain null. The temporary PR-only read-only source-review workflow was removed before merge.

### Rehearsal and tests

The real isolated importer/publication rehearsal proved **1,109 -> 1,122**, exactly **13 additions**, **185 already-present reviewed entries**, **0 holds/conflicts**, all **1,109 existing records unchanged**, and a byte-idempotent second run. A pure audit of the real publisher output also checked all thirteen identities, all 39 facts, nulls and retained hashes.

Passed locally: listing-verifier guards; reviewed importer/null/conflict/idempotency tests; real publication rehearsal; live-verifier mutation and real publisher-projection tests; parser/cursor/state regressions; synchronized publication and data validation. The entire tested repository tree `d37ddc479f61cdea51966128b14e133ca00d95b0` exactly matched the committed tree.

PR #215 head checks passed: reviewed evidence/importer `36069399500`, full data contract `36069399553`. PR #216 head checks passed: reviewed evidence `36070151143`, full data contract `36070151155`, served-data verifier `36070151228`.

### Production and actual served-data verification

Production sync `36069541844` succeeded. Source-backed data commit: `0a6e2bae1e0ce35e20975de479a17696395ddfc6`. Operator-state commit: `ca5d59edee121b8d7ce2026e01cc5ffc0fb299b2`. Operator health was **healthy** at `2026-09-24T22:53:13.986Z`.

A direct comparison of the served snapshot with the rehearsal baseline found **13 added / 3 changed / 0 removed**. The three existing-record changes were additional SEBI Prospectus/RHP filing/PDF references and collection timestamps for Rubicon Research, WeWork India Management and Garuda Construction and Engineering. No documents were removed and no existing IPO term value changed. These normal source-first enrichments are separate from the thirteen reviewed additions.

Observed recovery counts: 2020 **51**, 2021 **100**, 2022 **94**, 2023 **196**, 2024 **301**, 2025 **293**, 2026 **87**. Total **1,122**; this batch adds **4 to 2023** and **9 to 2024**. These are observed counts, not complete-universe claims.

Canonical post-merge verifier `36070243437` passed:

| Check | Result |
| --- | ---: |
| Actually served records | 1,122 |
| Reviewed issuers | 13 / 13 unique |
| Listing-date / market-lot / issue-price fields | 39 / 39 matching |
| Failed issuers | 0 |
| Unsupported fields | 6 null fields per issuer |
| Original document-hash field sources checked in recovery | 39 |
| Document hashes serialized in public evidence | 0 |

Original hashes were checked in retained recovery. The public projection intentionally omits document hashes; do not describe this as public-document-hash verification.

Snapshot fetched `2026-09-24T22:57:35.734Z`; checked `2026-09-24T22:57:35.772Z`; dataset generated `2026-09-24T22:49:44.462Z`. Snapshot SHA-256: `bd2e2eace8417c760d85f14609c432da0c7fef0cbea3ddf89054d4cd65cc66a3`.

Post-merge artifact `10838520133`, ZIP SHA-256 `9177f167c564f4c9269c15d4d9bd7ec377dc2320246999284369e0ba080ae8d0`, expires `2026-10-08T22:57:36Z`. Exact downloaded bytes and archive hashes were checked; a fresh pure audit from the retained source snapshot matched every issuer result. PR and post-merge served snapshots were byte-identical. Pages deploy `36070243523` succeeded on PR #216's merge. The earlier merge deploy alone was not accepted as proof of data publication.

Durable receipt: [verification/repaired-cursor7-live-publication-2026-09-24.json](verification/repaired-cursor7-live-publication-2026-09-24.json). Later independent historical-field automation may enrich unrelated records; this receipt identifies the exact verified snapshot.

## Exact next backend task

Re-read current main, this handoff and `ops/bse-sme-addition-notices.json` first. Latest checked cursor remains parser **1.4.0**, **160/236 tracked**, **160 parsed**, **0 failed**, **76 untracked**, updated `2026-09-24T22:06:07.403Z`, Git blob `0aba996b117374ea2ba4fbeb299144b63ca9cba2`.

**Continue one bounded historical discovery segment from the first unseen notice, currently `20230503-13`.** Use the existing state-driven backfill; do not reset or replay prior progress. If independent automation has already advanced, reconcile its earliest pending segment instead of fetching it again. Compare references against all current 2020-2026 recovery and public identities, BSE codes and listing-source identities; separate already-present, missing and ambiguous cases. Independently verify issuer-specific official listing notices only for missing/unambiguous candidates in batches of at most 15. Retain reviewed evidence, rehearse safe/idempotent publication, then verify the actually served result.

The thirteen repaired references are fully closed as **discovery batch22 / reviewed batch28**. The seven parser failures are also closed. Do not repeat cursor7 discovery20/21 or reviewed26/27, nor cursor6 discovery18/19 or reviewed24/25. Broader historical coverage and field completeness remain incomplete. No UI, minimum-investment, billing, accounts, ads, new spending or permission changes belong to this continuation.

## Prior work and preserved history

Parser v1.4.0 remains unchanged; its source fixtures, 84 fail-closed mutations and operational receipt remain at [verification/bse-parser-v1.4-2026-09-24.json](verification/bse-parser-v1.4-2026-09-24.json). UI V2 was separately completed in PR #209; its evidence remains in [UI_DESIGN_HANDOFF.md](UI_DESIGN_HANDOFF.md). No UI files changed in this backend unit.

The complete prior status and README are archived byte-for-byte in [archive/PROJECT_STATUS-before-repaired-cursor7-publication.md](archive/PROJECT_STATUS-before-repaired-cursor7-publication.md) (original Git blob `3d48b15db6b82b117302a2d7edcb2922eaa33861`) and [archive/README-before-repaired-cursor7-publication.md](archive/README-before-repaired-cursor7-publication.md) (blob `2ef2c7391b8473496c0829699e73689eaced5cdf`). Older archives and receipts remain unchanged. Archived next-task instructions are not current instructions.
