# Project status and handoff

Updated **2026-09-27 (UTC)** after the EKI Energy / Gretex release was **VERIFIED on actual Pages**. Active priority remains **P1 issuer identity and universe correctness** under [DEVELOPMENT_PROCESS.md](DEVELOPMENT_PROCESS.md).

## Exact next bounded task

Review **Getalong Enterprise Limited (543372)** and **Shri Venkatesh Refineries Limited (543373)** from the remaining nine original BSE 2021 unmatched rows. First reconcile against latest recovery to avoid duplicates. Obtain issuer-specific official listing/offer evidence and original response bytes, validate identity and issue type, then publish only supported facts through the existing reviewed-BSE path. The historical issue-summary rows are discovery evidence, never import authorization.

The machine-readable [2021 disposition](../data/discovery/bse-2021-unmatched-disposition-2026-09-27.json) accounts for all **16 original unmatched rows: seven reviewed/published and nine awaiting review**. Original source totals remain **91 official rows / 75 exact matches / 16 unmatched**; this is a follow-up disposition, not a new complete-universe audit.

| Still awaiting issuer-specific review | Discovery BSE code |
| --- | --- |
| Getalong Enterprise Limited | 543372 |
| Sigachi Industries Limited | 543389 |
| Adeshwar Meditex Limited | 543309 |
| HP Adhesives Limited | 543433 |
| Jetmall Spices and Masala Limited | 543286 |
| Nuvoco Vistas Corporation Limited | 543334 |
| Brandbucket Media & Technology Limited | 543439 |
| Shri Venkatesh Refineries Limited | 543373 |
| FSN E-Commerce Ventures Limited | 543384 |

Do not reuse the earlier exploratory Sigachi/Latteys URLs as positive issuer evidence. They did not establish a clean source path. Later corporate names, migrations, splits, bonus issues and current trading lots must not overwrite original IPO facts.

## Latest release — EKI Energy and Gretex complete

PR **#293** merged as **4114e0aae95a3b36444e4f910da7f3904dfab923**. Publication commit **8b0621a82d6a8f4d700b5145757a2df338618fd4** added exactly two 2021 recovery records and rebuilt `data/ipos.json`. **Do not replay this completed batch.**

| Issuer | Original board | Original listing | Issue price | Historical market lot |
| --- | --- | --- | ---: | ---: |
| EKI Energy Services Limited | SME | 07-Apr-2021 | INR 102 | 1,200 shares |
| Gretex Corporate Services Limited | SME | 09-Aug-2021 | INR 170 | 800 shares |

The values come from original BSE notices **20210406-21** and **20210806-21**, not an aggregator or a current-price/lot feed. The batch keeps price bands, offer dates, issue sizes, minimum bid quantities and minimum application amounts **null**. Market lot is not relabelled as application quantity. The notices' symbols and ISINs remain in retained evidence; this release did not expand the established import contract to publish extra identity fields.

### Original evidence and implementation

- [Approved standard manifest](../data/verified-bse-listings/2026-09-27.json), [discovery candidates](../data/discovery/bse-listing-candidates-2026-09-27.json), and [source receipt](../data/evidence/bse-2021-sme-pair-source-receipt-2026-09-27.json).
- Collection run **36287056000**: **2 original HTML responses / 192,432 bytes**, artifact **10919754960**, SHA-256 **fbfdc3d3cffca645dadf3717488e81277036ef7c9a89a378b2ea12a4d3e9689a**. Both notices passed the first strict collection attempt.
- Reused `verify-bse-listing-candidates.mjs`, `apply-verified-bse-listings.mjs`, and `verify-bse-publication.mjs`; no parser relaxation or parallel importer. Added `release-bse-2021-sme-pair.mjs`, `test-bse-2021-sme-pair.mjs`, and `publish-bse-2021-sme-pair.yml`. The release wrapper binds the exact manifest bytes to the receipt and fails closed on held/conflicting records.
- Publication recomputes on latest main, rejects intervening code/evidence changes, validates before and after applying, and never rebases generated JSON. Temporary collection workflow removed before merge. No UI changes.

### Tests and actual live verification

All final-head PR checks passed: data contract **36287458543**, reviewed-BSE validation **36287458606**, and full publication rehearsal **36287458628**. Merged-main data contract **36287598576** passed. Existing source-verifier/import/publication tests and the new pair regression passed locally and in the release workflow, including **16 negative cases**, dry-run non-mutation, fresh application, idempotency, cross-year identity collisions, altered evidence, null preservation and live-comparison fixtures.

Publication/verification run **36287598558** passed: **2/2 issuers, 6/6 reviewed fields, zero failed issuers**. The first two HTTP fetches still returned the earlier 1,343-record dataset; the third succeeded. The retained [live receipt](verification/bse-2021-sme-pair-live-2026-09-27.json) records:

- Served dataset: **1,345 records**, fetched **2026-09-27T02:08:52.115Z**.
- Dataset SHA-256: **c3bc50254cf0a6cc5215e853a7301b98c0ac6eb30b8ad5b4d3200842d32c6f06**.
- Dataset generation: **2026-09-27T01:57:02.271Z**; this is distinct from collection, fetch and publication time.
- Live artifact **10921320961**, SHA-256 **34f6d2068028ff0ac8f0d35a007335561ebcf17040854815a5f4f1e1978988a7**, including failed and successful response bytes/reports.
- Independent comparison with the 1,343-record pre-release Pages snapshot found exactly two additions, **zero deletions and zero changes to existing records**.

Original source hashes were checked in retained recovery; the public schema does not serialize them. Do not represent this as verification of hashes exposed by the website. Original and live-response artifacts have **14-day retention**; durable manifest excerpts, receipt hashes and URLs stay in the repository. There is no new browser/UI test claim for this data-only release.

## Completed work — do not restart

The original 2021 unmatched records already repaired are **IRFC, Anupam Rasayan India, Exxaro Tiles, Nureca, Paras Defence, EKI Energy and Gretex**. Their manifests and source receipts remain retained. Missing fields on earlier repairs remain missing; this batch did not fill or reinterpret them.

Also complete: the four BSE 2020 repairs; five high-priority BSE historical reconciliations; Fabino's evidence-backed 2022 listing correction; nine excluded-event issuers' historical equity IPOs; the pinned NSE review (**105 approved IPOs + 14 non-IPO exclusions = 119 groups, no unresolved holds**). Keep excluded debt, migration and rights-security events out of the new-IPO queue. BSE parser v1.5's **236/236** completed cursor must not be replayed.

## Remaining boundaries and parallel workstreams

Overall Indian IPO-universe coverage is still incomplete. After the remaining 2021 rows, continue bounded year/source-family reconciliation. SEBI historical pagination, NSE-series coverage and wider Pre-IPO lead-manager discovery remain separate gaps. Maintain observation/collection/generation/publication distinctions and preserve source conflicts/corrections.

The Pre-IPO view and collector remain lifecycle-aware and history-preserving; this batch did not refresh or re-audit their coverage. UI/company-research requirements stay in [UI_DETAIL_NAVIGATION_HANDOFF.md](UI_DETAIL_NAVIGATION_HANDOFF.md); do not expand downstream research/performance while upstream correctness is materially blocked. Keep the static/light-theme architecture and the active Lot Size-only requirement. No new spending, licensing commitments, billing, accounts, analytics, ads or access-policy changes were introduced.

## Preserved historical handoff

The previous canonical status is archived **byte-for-byte** as [PROJECT_STATUS_ARCHIVE_THROUGH_PARAS_2026-09-27.md](PROJECT_STATUS_ARCHIVE_THROUGH_PARAS_2026-09-27.md), original Git blob **5dc0fd15d0572b3bafb5ad6661fc8fb76ec424f6**. It contains historical run IDs, source decisions, failed approaches and earlier release receipts. Its obsolete next-task and blocked-publication paragraphs are historical, not current instructions. All earlier archives remain intact. Use this file and the pinned disposition for the next continuation.
