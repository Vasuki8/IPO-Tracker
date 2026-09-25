# Project status and handoff

The active backend workstream is **P1 issuer identity and IPO-universe coverage** under [DEVELOPMENT_PROCESS.md](DEVELOPMENT_PROCESS.md). UI and future research-data requirements stay in [UI_DETAIL_NAVIGATION_HANDOFF.md](UI_DETAIL_NAVIGATION_HANDOFF.md). The application-term requirement remains **Lot Size only**. Preserve market lot and minimum bid quantity as distinct fields; do not estimate application amounts.

Updated: **2026-09-25**, after actual batch7 Pages verification.

## Current release and next task

**Batch7 is VERIFIED LIVE. Do not repeat its review/import.** The exact next task is [batch8](../data/discovery/ipo-universe-review-2026-09-25-batch8.json): **14 candidate issuer groups from SUMAX through SPECTRAA**. These are the final 14 groups in the pinned canonical audit, **not 14 confirmed IPOs** and not proof of full-universe completeness.

## Completed batch7 — PR #244

Reviewed 15 SKYTECH-through-12AIL28 groups: **13 approved initial-equity IPOs, two excluded debt securities, no new holds**.

Approved symbols: **SKYTECH, FASCINATE, HORIZONIND, LALITHAA, SHANKESH, SUNSHINE, GAJA, TEMPSENS, AUGMONT, ABH, MADHURKNIT, SKYWAYS, SYMBIOTEC**.

The reviewed manifest retains **78 explicit facts**: 13 listing dates, 26 offer dates, 13 final prices, 13 price bands, four market lots and nine minimum bid quantities. No issue size or application amount was inferred. Optional source-sync enrichments remain separate from this count.

### Debt exclusions and source dates

**1150VIES30** is a debt security of Vision Infra Equipment Solutions. NSE's issuer response flags debt and reports ISIN **INE0TR007022**, matching **NSE/CML/76063**, dated August 31, 2026, security VIESL30 / VIESL 11.50% 2030 Sr I. Separate official equity filings identify **VIESL / INE0TR001017**. The debt-market circular is effective August 31; the issuer endpoint reports September 1 in the capital-market segment. Neither date is a new equity IPO. Do not combine its 2024 equity offer terms with the 2026 debt listing.

**12AIL28** is debt of AVP Infracon, ISIN **INE0R9407016**, matching **NSE/CML/76110**, dated September 1, 2026, effective September 2. Separate equity identity is **AVPINFRA / INE0R9401019**. Its secondary-market lot of one is not an IPO application lot. The aggregate source mixes a 2024 equity offer with a 2026 debt listing.

Both decisions retain original issuer responses, official PDF identities/pages/hashes, and distinct equity filings. Relevant circular pages were text-extracted and visually inspected. Excluding these debt events does not imply that the issuers never had equity IPOs.

### Reusable parser repair

FASCINATE's literal Issue Period is `11-Aug-2026 to 19-Aug-2026 (The Issue is further extended to 19-Aug-2026)`. The importer now recognizes only this anchored optional suffix, requires its endpoint to repeat the stated closing date, and still requires independent past-source date agreement. Conflicting dates, conditional wording and appended text fail closed. No issuer allowlist or date inference.

FASCINATE retains final price **151**, band **142–151**, market lot **800**, and minimum bid quantity **null**. The literal lot description does not authorize inventing a minimum bid.

### Source, rehearsal and merge evidence

Read-only source run **36180291566**, artifact **10884545129**, SHA-256 `4196efe544c31deee32ebd6d642e11d5f904266aee97a10b43c96f392dd27da6`; exact merge-ref source **d451a6166aea8437d976228014c563fc70885981**. All **21 original response hashes/byte counts** passed; all HTTP 200.

Materialization run **36181249657**, artifact **10883833361**, SHA-256 `8c3e7e5d9ad8f49502f78ec0c57e1594bd7512a8b8c8aa6569d6f71b5ffa22cd`; reviewed commit **2ee7c4287ffa4079c790882e730d60594e6999fc**. All five evidence/parser/test files match locally tested bytes.

Isolated rehearsal **1,296 -> 1,309**, exactly 13 additions, no removals, all 1,296 existing records unchanged, idempotent rerun. All seven reviewed batches pass **91 issuers / 544 facts**. Batch7 regressions reject **20 source mutations and four cross-year identity collisions** and cover before/after publication, corrupted existing values, exclusions, nulls and read-only behavior.

Final-head data-contract **36181495143** and reviewed-BSE **36181495050** passed. PR #244 merged as **72605cb38f76a6541fc84abba889693322d1a6ab**. Merged-main data-contract **36181601737** also passed. The temporary collector, materializer and builder were removed; the final seven-file change contains only reviewed evidence, the minimal importer repair, tests, rehearsal receipt and verifier selection.

## Actual publication and served-data verification

Normal source-backed sync **36181601722** completed successfully. Data commit **23dc175bced8bc54a8063f43efa140b2eb979104**; operator/source revision **8022888e030eb38112469307db0bb6e9437cf875**. Operator health: **healthy**. The public data came through retained recovery and semantic publication, not hand edits.

Actual Pages verifier **36182904949** succeeded. Artifact **10885275368**, SHA-256 `8e10e132c8c2b3a5c6400fb25bb2255bb7a76579a22010bc217b2fbb86381673`. Pages deployment **36182898721** succeeded for the verified source revision. The first verifier attempt still saw the preceding 1,296-record dataset; the second passed after Pages propagation. This was not a failed import.

| Actual served result | Verified value |
| --- | ---: |
| Live records | **1,309** |
| Batch7 issuers / facts | **13 / 78**, all matching |
| All seven reviewed batches | **91 issuers / 544 facts**, all matching |
| Added / removed records | **13 / 0** |
| Existing baseline records unchanged | **1,291 / 1,296** |
| Existing records changed by routine pipelines | **5** |
| Unknown / invalid statuses | **0** |
| Missing status evidence | **0** |

Status distribution: **listed 1,288 / open 12 / closed 7 / upcoming 2**.

Actual fetch **2026-09-25T19:59:16.697Z**; verifier check **2026-09-25T19:59:16.782Z**; dataset generation **2026-09-25T19:55:28.706Z**. Snapshot SHA-256 **`f1b0d662e1dc8a61cd4a821451143e85ea5a6e53425f158431a26953ca8b3df0`**, **7,122,490 bytes**. Served bytes equal the retained source snapshot. Keep collection, source observation, dataset generation and Pages publication times distinct.

The exact post-publication snapshot passed parser/import/rehearsal/manifest/build/schema checks. All **308 archived source files** remained byte-identical after testing.

### Exact delta and optional routine enrichment

Baseline: actual Pages fetched **2026-09-25T19:33:27.352Z**, **1,296 records**, SHA-256 `0fe577e052a06eef0e477eff7a0530a289b5715d25da42e372fc5071f4e9b1e0`. Exactly the 13 approved identities were added; no removals or unexpected new issuer. All earlier reviewed facts still match.

Historical recovery filled **seven previously missing offer dates across four prior records**. Their collection timestamp, **2026-09-25T19:34:17.340Z**, predates the batch7 merge. The intervening historical offer-date backfill commit is **9c05b75d64d4a35e959ebb535e5ef0d87cb077dd**, published at **19:45:10Z**, before the batch7 merge at **19:45:15Z**.

- **Saatvik Green Energy Limited** — closing date **2025-09-23**.
- **AIRFLOA Rail Technology Limited** — offer dates **2025-09-11 to 2025-09-15**.
- **Deepak Builders & Engineers India Limited** — offer dates **2024-10-21 to 2024-10-23**.
- **Kesar India Limited** — offer dates **2022-06-30 to 2022-07-04**.

The release sync also added **four source-document entries to Chavda Infra Limited**, plus its collection timestamp. No prior non-null displayed value or status was replaced. The exact delta, source metadata and before/after record hashes are retained in the live receipt.

Three new batch7 records received optional issue-size enrichment, separate from the manually reviewed 78 facts:
- **Horizon Industrial Parks Limited**: `issue_size_inr=26000000000`, independently corroborated against the pinned original NSE response.
- **Gaja Alternative Asset Management Limited**: `issue_size_inr=5500000000`, retained SEBI Prospectus source, **PDF page 3**.
- **Skyways Air Services Limited**: `issue_size_inr=5827960000`, retained SEBI Prospectus source, **PDF page 2**.

Gaja and Skyways were checked for public/recovery value agreement and retained source locators; their external PDFs were not independently reopened in this run. The receipt labels these checks `public_recovery_consistency_only`. Do not count them among the 78 manually reviewed facts or attribute routine historical/date/document updates to the reviewed import.

## Exact next task — batch8

[Batch8 queue](../data/discovery/ipo-universe-review-2026-09-25-batch8.json): **14 groups, SUMAX through SPECTRAA**. Selection was revalidated against the hashed original audit **36095239145**, original past-source rows and all **105 prior candidate groups**. The canonical audit contains 119 eligible issuer groups; repeated observations count once.

**DOLLEX** combines December 2022 offer dates with a September 2026 listing date and a price mismatch; investigate prior IPO/migration/repeat history. **13DCCL28** combines May 2025 offer dates, a September 2026 listing and incompatible prices; establish debt/equity type and identifiers independently. **VINOD** has a single-price source observation; verify fixed-price status and preserve a null band unless an actual band is disclosed.

Reconcile every candidate against all recovery years and actual Pages. Establish offering type and identity from issuer-specific official evidence, not the aggregate row. Preserve aliases/nulls/conflicts, test before and after publication, publish via retained recovery and verify actual served output. Finishing this queue will not resolve the separate holds or wider source-coverage gaps.

## Prior holds, gaps and preserved handoff

Unresolved: **LEAP, AMIRCHAND, ADANIENPP1, Fabino Life Sciences, GICL, SILGOPP, VITAL, KOTYARK**. Resolved debt/migration exclusions now also include **1150VIES30 and 12AIL28**, alongside ANNAPURNA, SWARAJ, 10MWL29, QMSMEDI and 12VPT28A. Do not recycle excluded events into the new equity-IPO queue.

BSE issue-summary, SEBI historical pagination and unresolved NSE series still limit coverage. **BSE parser v1.5 is 236/236 parsed; do not replay its cursor.** Do not claim full IPO-universe completeness.

Evidence: [review](../data/discovery/nse-universe-batch7-review-2026-09-25.json), [manifest](../data/verified-nse-ipos/2026-09-25-batch7.json), [rehearsal](verification/nse-universe-batch7-rehearsal-2026-09-25.json), [live receipt](verification/nse-universe-batch7-live-publication-2026-09-25.json).

Previous handoffs are archived byte-for-byte as [README-before-nse-batch7-live-verification.md](archive/README-before-nse-batch7-live-verification.md) and [PROJECT_STATUS-before-nse-batch7-live-verification.md](archive/PROJECT_STATUS-before-nse-batch7-live-verification.md). Earlier evidence is unchanged. Raw Actions artifacts expire after 14 days; durable literal projections, URLs, document identity, dates, hashes and evidence locators remain in the repository.

No UI, minimum-investment expansion, billing/accounts/ads, spending or access-policy changes belong to this continuation.
