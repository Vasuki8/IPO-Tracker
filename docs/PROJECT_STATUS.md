# Project status and handoff

The active workstream remains **P1 issuer identity and IPO-universe coverage** under [DEVELOPMENT_PROCESS.md](DEVELOPMENT_PROCESS.md). UI and future research-data requirements remain separate in [UI_DETAIL_NAVIGATION_HANDOFF.md](UI_DETAIL_NAVIGATION_HANDOFF.md). **Lot Size only** remains the application-term requirement; market lot and minimum bid quantity are distinct, and no application amount is estimated.

Updated **2026-09-25**, after actual batch8 Pages verification.

## Release state and exact next task

**Batch8 is VERIFIED LIVE. Do not replay the approved imports from batches 1–8.** The pinned 119-group canonical review queue is exhausted, but **seven NSE cases remain held** and wider coverage is incomplete. The exact next bounded task is **AMIRCHAND and LEAP missing-identity review**, from [the retained hold queue](../data/discovery/ipo-universe-held-review-2026-09-25.json).

## Completed batch8 — PR #245

Reviewed all 14 SUMAX-through-SPECTRAA groups: **12 approved initial-equity IPOs, one migration exclusion, one debt exclusion, zero new holds**.

Published symbols: **SUMAX, LUMINO, ASHUTOSH, PERNIASPOP, SHANTIINOR, DEEPA, GLASSWALL, PRASOLCHEM, STEAMHOUSE, VINOD, KHERIAAUTO, SPECTRAA**.

The manifest retains **71 explicit source-backed facts**: 12 listing dates, 24 offer dates, 12 final prices, 11 price bands, six market lots and six minimum bid quantities. **No production parser change was required.** No issue size or application amount was inferred.

**VINOD** explicitly discloses Fixed Price and Rs.94 per equity share. Its price band stays **null**, market lot is **1,200**, and minimum bid stays **null**. Do not manufacture a 94–94 band or copy market lot into minimum bid.

### Positive event exclusions and retained conflicts

**DOLLEX — excluded 2026 migration, not a new IPO.** The official issuer disclosure encloses **NSE/LIST/314**, dated September 9, 2026, approving SME Emerge-to-main-board migration effective September 11. Symbol and ISIN **INE0JHH01011** match. Pages 1–2 of the retained original PDF were visually inspected. Preserve the December 2022 original-offer terms separately; secondary-market lot 1 is not an IPO application lot.

**13DCCL28 — excluded debt event.** NSE's debt flag and ISIN **INE04Q907231** match **NSE/CML/76341**, dated September 15, 2026, effective September 16: a privately placed **DCCL 13% 2028** security, series N0. Pages 1 and 3 of the retained original circular were visually inspected. Do not combine the aggregate row's May 2025 equity-offer terms with this September 2026 debt listing.

The supplementary **DCCL** endpoint reports ISIN **INE04Q901010** and old IPO terms but also `isDebtSec=true`. That inconsistency is retained as `retained_mixed_metadata_not_equity_approval`, not silently cleared or used to approve an equity record. The debt exclusion rests on the matching 13DCCL28 circular identity.

### Original evidence, regression tests and merge

Read-only source run **36187113307**, artifact **10886636012**, SHA-256 `7169cbd2c166521850ac2fac44c4f4be808440df1ffc0acd45951cd84b2df1bb`; exact merge-ref source **a678c760130f082327ee591f5e38c154c68150d5**. All **19 response hashes and byte counts** passed, all HTTP 200. Canonical past-response hash and actual baseline bytes matched their pinned evidence.

Materialization **36187979805**, artifact **10887157480**, SHA-256 `ba00acef89e7f0239810237e365da10f45fa7c5e4633a5a6393b886df152d2c6`; reviewed commit **ab5d0275c70168116714fbaf9c6414a63a2ee986**. Generated evidence and test files match locally tested bytes. No failed materialization attempts.

Isolated rehearsal **1,309 -> 1,321**, exactly 12 additions, no removals, all 1,309 prior records unchanged, idempotent rerun. All eight reviewed batches pass **103 issuers / 615 facts**. Batch8 rejects **21 source mutations and four cross-year identity collisions**, with before/after-publication execution, corrupted existing values, fixed-price/null-band handling, positive exclusion evidence and read-only inputs tested.

Final-head CI: data contract **36188166811**, reviewed-BSE **36188166727**, both successful. PR #245 merged as **b265dfca446d7e2119eee1636f34a2bb1bf7e930**; merged-main data contract **36188313978** passed. Both temporary workflows and the materializer were removed before merge. The six-file final diff contains only reviewed evidence, tests, rehearsal receipt and verifier selection.

## Actual source-backed publication and Pages

Normal source sync **36188314026** succeeded. Data commit **519c0fd8efb5db650f245aa17e5a368ca57b995b**; operator/source snapshot **5c9983045a5df174ba6f6b850b33e907bb1822f7**; operator health **healthy**. Data was generated through retained recovery and semantic publication, not hand-edited.

Actual Pages verifier **36189922895** succeeded, artifact **10887797144**, SHA-256 `fa2b1b385a7b2b8d7b2831f902847573cd9fc2bb12764bde7292cb723322f2d7`. Pages deployment **36189916786** succeeded. The first 11 bounded verifier attempts saw the preceding 1,309-record dataset (SHA-256 e442d4d4e0b5c4efccee521242104f537265b5faeea503737dafaf97d6a27f8a). Attempt 12 passed after Pages publication. Earlier Pages run 36189912843 was cancelled; run 36189916786 succeeded for the following operator revision containing the same published IPO data. The reviewed import did not fail.

| Actual served check | Verified result |
| --- | ---: |
| Live records | **1,321** |
| Batch8 issuers / facts | **12 / 71**, all matching |
| All eight reviewed batches | **103 issuers / 615 facts**, all matching |
| Added / removed | **12 / 0** |
| Prior records unchanged | **1,305 / 1,309** |
| Prior records changed by routine pipelines | **4** |
| Unknown / invalid statuses | **0** |
| Missing status evidence | **0** |

Status distribution: **listed 1,300 / open 12 / closed 7 / upcoming 2**.

Actual fetch **2026-09-25T21:14:56.192Z**; verifier check **2026-09-25T21:14:56.279Z**; dataset generation **2026-09-25T21:02:27.569Z**. Snapshot SHA-256 **`704b89e1ff652353af29acf2790d1aee93a3b12fad083c6b4bca052622f37000`**, **7,207,506 bytes**. Actual served bytes equal the retained post-publication source snapshot. Keep source observations, collection, generation and publication times distinct.

The exact post-publication snapshot passed importer/parser/publication-rehearsal/manifest/build/schema tests. All **316 source files** remained byte-identical after testing.

### Exact baseline delta and routine enrichment

Baseline actual Pages fetched **2026-09-25T20:41:24.792Z**, **1,309 records**, SHA-256 `f1b0d662e1dc8a61cd4a821451143e85ea5a6e53425f158431a26953ca8b3df0`. Exactly the 12 reviewed identities were added; none removed. All earlier reviewed facts still match. The live receipt separately retains every prior-record change, source metadata, added document URL and before/after record hash.

The separate historical PDF backfill collected at **2026-09-25T20:49:10.224Z** and published commit **baf459109b4103d82d38c4513f2684306b82e79b** at **20:54:21Z**, during the release run. It filled two previously missing issue sizes: **Chemcon Speciality Chemicals — 3,180,000,000 INR** (Prospectus page 1) and **Marco Cables and Conductors — 187,272,000 INR** (Prospectus page 3), with their collection timestamps. Public/recovery consistency and retained source locators were checked; those external PDFs were not independently reopened.

The release sync added **four document entries to SAMHI Hotels** and **two to Taurian MPS**, plus collection timestamps. No document was removed. **No previously populated displayed value or status was replaced.** These four routine record changes are separate from the 12 reviewed additions.

Optional issue-size enrichment on the newly approved records is separate from the manually reviewed 71 facts:

| Issuer | Retained INR amount | Source/check |
| --- | ---: | --- |
| Lumino Industries | 7,000,000,000 | SEBI Prospectus page 2; public/recovery consistency only |
| Purple Style Labs | 6,800,000,000 | Independently corroborated in the pinned original NSE response: explicit sole fresh issue of Rs. 6800 million |
| Deepa Jewellers | 4,597,160,000 | SEBI Prospectus page 3; public/recovery consistency only |
| Glass Wall Systems (India) | 4,278,900,000 | SEBI Prospectus page 3; public/recovery consistency only |
| Steamhouse India | 4,140,000,000 | SEBI Prospectus page 3; public/recovery consistency only |
| Vinod Texworld | 428,302,000 | SEBI Prospectus page 3; public/recovery consistency only |

`public_recovery_consistency_only` confirms value/source agreement in retained and served data, not an independent re-read of the external PDF. Those five new-record PDFs were not independently reopened in this run. The live receipt retains URLs, document identity, dates, pages and literal source amounts; Purple Style Labs also has pinned original-response corroboration. Do not count these optional fields or the historical backfills among the 71 manually reviewed facts.

## Pinned audit accounting — not full-universe completeness

[Canonical review summary](../data/discovery/nse-universe-canonical-review-2026-09-25.json) revalidates all **119 candidate groups** against the original hashed audit **36095239145**, original past-source rows and all eight sets of retained queue, review and manifest files. There are 121 observations because ADANIENPP1 occurs three times; it counts as one group.

Final accounting: **103 approved equity IPOs + five excluded debt events + four excluded migrations + seven unresolved groups = 119**. **Zero unreviewed groups remain in this pinned queue.** All 103 approved issuers and 615 reviewed facts are verified in actual Pages. This is not a claim that the full Indian IPO universe is complete.

The seven unresolved NSE cases are **AMIRCHAND, LEAP, ADANIENPP1, GICL, SILGOPP, VITAL and KOTYARK**. Their original candidates, decisions, reasons, review hashes and source-run references remain in the [hold queue](../data/discovery/ipo-universe-held-review-2026-09-25.json).

**Next bounded task: AMIRCHAND and LEAP.** Establish missing legal-name, symbol, ISIN, board, listing and offering identity through independent issuer-specific official filings/notices. Extend a reusable evidence-backed path only with tests; do not synthesize identity from the aggregate row. Reconcile latest main/Pages first; preserve nulls/conflicts and leave on hold when proof is insufficient. Then resolve the five older-offer/security-history cases separately.

### Separate original-IPO coverage follow-up

The nine resolved exclusions concern **2026 events**, not the issuers' entire history. Exact normalized-name checks across retained recovery and actual Pages found no matches for these nine issuer names. This is a **diagnostic for independent historical-offer review**, not automatic missing-IPO proof or import authorization. Review original offer identity/year before adding any historical record; never recycle the excluded migration/debt event as a new IPO.

BSE **Fabino Life Sciences** remains a separate listing-year hold. BSE issue-summary, SEBI historical pagination and unresolved NSE-series coverage gaps remain. **BSE parser v1.5 is 236/236 parsed; do not replay its cursor.**

## Evidence and preserved handoff

[Review](../data/discovery/nse-universe-batch8-review-2026-09-25.json), [manifest](../data/verified-nse-ipos/2026-09-25-batch8.json), [rehearsal receipt](verification/nse-universe-batch8-rehearsal-2026-09-25.json), [live receipt](verification/nse-universe-batch8-live-publication-2026-09-25.json).

Previous handoffs are archived byte-for-byte in [README-before-nse-batch8-live-verification.md](archive/README-before-nse-batch8-live-verification.md) and [PROJECT_STATUS-before-nse-batch8-live-verification.md](archive/PROJECT_STATUS-before-nse-batch8-live-verification.md). Earlier evidence remains intact. Raw Actions artifacts expire after 14 days; durable literal projections, URLs, document identities, dates, hashes and evidence locators remain in the repository.

No UI, minimum-investment, billing/accounts/ads, spending or access-policy expansion belongs to this continuation.
