# Project status and handoff

The active backend workstream remains **P1 issuer identity and IPO-universe coverage** under [DEVELOPMENT_PROCESS.md](DEVELOPMENT_PROCESS.md). UI and future source-backed research requirements remain in [UI_DETAIL_NAVIGATION_HANDOFF.md](UI_DETAIL_NAVIGATION_HANDOFF.md). The application-term requirement is **Lot Size only**; preserve the distinction between market lot and minimum bid quantity. No estimated application amount.

Updated: **2026-09-25**, after actual batch6 publication verification.

## Current release and next task

**Batch6 is VERIFIED LIVE; do not repeat its review/import.** Continue with the pinned **15-candidate batch7 queue, SKYTECH through 12AIL28**, after reconciling against latest main and actual Pages. There are **29 remaining candidate issuer groups**, not 29 confirmed IPOs.

## Completed batch6 — PR #243

Reviewed all 15 MVELECTRO-through-CREDENT candidates. **12 initial-equity IPOs approved, two migrations excluded, one identity hold.** Published symbols:

**MVELECTRO, ANAWIL, ARDEE, OPTIMYSTIX, TECHNOCRAF, DHOOTTRANS, MOLBIO, MILKYMIST, BLEL, PRAMODINI, SHIPROCKET, CREDENT**.

The reviewed manifest retains **72 explicit facts**: 12 listing dates, 24 offer dates, 12 final issue prices, 12 price bands, 4 market lots and 8 minimum bid quantities. No issue size or application amount was inferred. Ordinary sync enrichment, if any, is separate from this reviewed fact count.

### Exclusions and hold

**ANNAPURNA — excluded migration, not a new IPO.** The official issuer disclosure encloses NSE/CML/75660 dated August 10, 2026, referring to its 2022 SME listing and moving the shares to the main board effective August 12, 2026. PDF pages 1–3 were visually reviewed; the annexure establishes symbol/ISIN INE0MGM01017. The main-board trading lot of 1 is not an IPO application lot.

**SWARAJ — excluded migration, not a new IPO.** The official issuer disclosure encloses NSE/LIST/307 dated August 11, 2026, explicitly moving the shares from Emerge to the main board effective August 13, 2026. PDF pages 1–2 were visually reviewed; symbol/ISIN INE0GMR01016 are retained. Do not mix its 2022 offer terms with the 2026 migration date.

**LEAP — held, missing issuer identity.** The response contains offer terms but `companyName` is only the symbol and the selected `metaInfo` identity/security fields are null. Do not synthesize legal name, ISIN, board, listing date or security classification from the aggregate row. It remains outside the approved manifest.

### Reusable source repair

The official ARDEE terms explicitly say `Rs. 50/- per equity share to Rs. 53/- equity share` and `Minimum 281 Equity Shares`. The price-band parser now accepts this fully anchored repeated-unit form only with INR markers/share units on both bounds. The minimum-bid parser accepts a bounded Minimum qualifier and preserves literal evidence. Market-lot parsing and issuer/offering gates remain unchanged; 281 must not be relabelled as market lot.

### Source evidence, tests and merge

Source review **36174755920**, artifact **10881946171**, SHA-256 `432491018daa0a376559937a81dde8726623ccb4e110761d7340091a9b240e63`; exact source merge-ref **c82637ae5bc82ce59831dcfa1d10ff2438b1ad4b**. All **24 response hashes/byte counts** checked: **23 HTTP successes, one retained 404**. The failed guessed standalone circular path was not used as positive evidence; the successfully fetched official disclosure encloses the authoritative circular.

Materialization **36175903734**, artifact **10882192517**, SHA-256 `6b4a596f1928c5d6d9a59f0023c1065764b07204de44a158de8a7379e4bf5092`; reviewed commit **d4473f86206a8e416d338752897359025d44cfe5**. All five produced parser/evidence/test files match locally tested bytes.

Rehearsal **1,284 -> 1,296**, 12 additions, zero removals, all 1,284 prior records unchanged, idempotent rerun. All six reviewed NSE batches: **78 issuers / 466 facts**. Batch6 rejects **18 source mutations and four cross-year identity collisions**; covers pre/post-publication inputs, corrupted existing data, null preservation, exclusions and read-only behavior.

Final PR-head CI: full data contract **36176126457**, reviewed-BSE **36176126455**, both successful. PR #243 merged as **4a9d3a259685d67d41dff054d48d8bf0e98130d9**. All temporary collectors/materializers/patch scripts were removed before merge. Only reviewed evidence, parser/test support, rehearsal receipt and verifier selection remain.

## Actual source-backed publication

Normal source-backed sync **36176259835** completed successfully. Data commit **b6c169c3481612cc2bf55ed10e72445d3687e89c**; operator/source snapshot **fafe8b0163a7967666e39083f58f1253a150162a**; operator health **healthy**. Collection, rebuild, validation and repository publication stages all succeeded. The public dataset was generated through retained recovery, not edited by hand.

Actual Pages verifier **36177365928** succeeded, with artifact **10882885861**, SHA-256 `e7655b62e9fc116a31906ae2905c5eef4492c4e21df2ed5171d7b9fb6cc9ef12`. Dynamic Pages deployment **36177356849** for the source revision succeeded by **2026-09-25T19:04:57Z**. The first two verifier attempts saw the preceding dataset; the third passed after Pages propagation. This was not a failed import.

| Actual served result | Verified value |
| --- | ---: |
| Live records | **1,296** |
| Batch6 issuers / facts | **12 / 72**, all matching |
| All six reviewed batches | **78 issuers / 466 facts**, all matching |
| Added / removed records | **12 / 0** |
| Prior records unchanged | **1,272 / 1,284** |
| Prior records changed by ordinary pipelines | **12** |
| Unknown / invalid statuses | **0** |
| Records missing status evidence | **0** |

Status distribution: **listed 1,275 / open 12 / closed 7 / upcoming 2**.

Actual fetch **2026-09-25T19:05:14.509Z**; verifier check **2026-09-25T19:05:14.575Z**; dataset generated **2026-09-25T18:55:21.251Z**. Snapshot SHA-256 **`0fe577e052a06eef0e477eff7a0530a289b5715d25da42e372fc5071f4e9b1e0`**, **7,031,468 bytes**. Served bytes equal the exact post-publication source snapshot. These observation, generation and publication clocks remain distinct.

The post-publication snapshot passed parser tests, all reviewed-import tests, all-six-batch publication rehearsal, reviewed-manifest validation, synchronized-build check and public schema validation. All **300 source-archive files** remained byte-identical after testing.

### Exact delta and routine changes — do not conflate with the reviewed import

Baseline: actual Pages fetched **2026-09-25T18:40:26.337Z**, **1,284 records**, SHA-256 `a542ba9d96d621dff867f7310c99d5c74f2864898501c46b214d94db112f1e91`. The isolated batch6 rehearsal preserved all 1,284. Between that baseline and final live output, normal pipelines also changed 12 older records; the durable receipt separates their field changes, collection timestamps, document URLs and before/after record hashes.

**Intervening sync 36175082009**, before the batch6 merge, produced data commit **0355b6c6a1da724269355bc6fa9c5aff9bfa6bb2** and operator commit **024bdf47b717f958517fc0faec6b5f12adbdfaf9**. Its changes account for eight older records: four **open -> closed** transitions for Adroit Industries (India), ArMee Infotech, Elevate Campuses and Swastika Infra with NSE feed evidence; source-backed fills of two previously missing Propshop Events and Exhibitions fields plus document attachment; and document additions for INDO-MIM, AIRFLOA Rail Technology and Kesar India.

**Release sync 36176259835** added documents to four older records: Shringar House of Mangalsutra, Urban Company, P N Gadgil Jewellers and Signatureglobal (India). Across both runs, eight older records gained 21 document entries. No record was removed, and every prior reviewed manifest fact still matches. Do not claim that all old statuses/values were unchanged: the four status transitions and the two previously missing Propshop fields are explicit routine changes.

Propshop's routine fields are `issue_size_inr=285660000` (SEBI Prospectus PDF page 2) and `minimum_bid_quantity=4000` (page 9). Public/recovery consistency and retained source locators were checked; an attempted independent PDF reopen was unavailable in this session. These fields are not included in batch6's manually reviewed 72 facts.

One newly approved record gained ordinary optional enrichment: **MV Electrosystems** `issue_size_inr=2900000000`, an explicit NSE response amount of Rs. 2900 million. It was independently corroborated against the pinned original issuer response, without multiplying price by shares, and remains separate from the reviewed 72 facts.


## Exact next task — batch7

[Batch7 queue](../data/discovery/ipo-universe-review-2026-09-25-batch7.json): **SKYTECH through 12AIL28**, 15 issuer groups. It is a review queue, not import authorization. Its selection was revalidated against hashed canonical audit **36095239145**, the original past-source rows and all 90 prior candidate groups. The canonical audit contains 119 eligible groups, with duplicate source observations counted only once.

**1150VIES30** and **12AIL28** require explicit debt/repeat-security review: their aggregate rows combine 2024 offer dates with 2026 listing dates and incompatible final-price/range observations. Do not pre-classify them from the symbol. **FASCINATE** has an August 11–19 offer window; verify any revised/extended wording rather than inferring dates.

Reconcile every candidate against all recovery years and actual served data. Independently establish initial equity IPO vs FPO/rights/debt/migration/repeat security, preserve aliases/nulls/conflicts, test preservation/idempotency, publish from retained recovery and verify actual Pages before completion.

## Remaining holds, gaps and preserved history

Unresolved: **LEAP, AMIRCHAND, ADANIENPP1, Fabino Life Sciences, GICL, SILGOPP, VITAL, KOTYARK**. Resolved non-IPO exclusions **ANNAPURNA, SWARAJ, 10MWL29, QMSMEDI, 12VPT28A** must not re-enter the new equity-IPO queue. A migration exclusion is not evidence that the issuer never had an IPO.

BSE issue-summary, SEBI historical pagination and unresolved NSE series still limit universe completeness. **BSE parser v1.5 is 236/236 parsed; do not replay its cursor.** No full-universe completeness claim.

Evidence: [review](../data/discovery/nse-universe-batch6-review-2026-09-25.json), [manifest](../data/verified-nse-ipos/2026-09-25-batch6.json), [rehearsal receipt](verification/nse-universe-batch6-rehearsal-2026-09-25.json), [live receipt](verification/nse-universe-batch6-live-publication-2026-09-25.json).

Previous handoffs are preserved byte-for-byte in [README-before-nse-batch6-live-verification.md](archive/README-before-nse-batch6-live-verification.md) and [PROJECT_STATUS-before-nse-batch6-live-verification.md](archive/PROJECT_STATUS-before-nse-batch6-live-verification.md). Earlier archives/evidence remain unchanged. Actions raw artifacts expire after 14 days; durable projections, URLs, document identity, dates, hashes and evidence locators remain in the repo.

No UI, minimum-investment expansion, billing/accounts/ads, spending or access changes belong to this continuation.
