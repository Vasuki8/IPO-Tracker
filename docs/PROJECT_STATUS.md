# Project status and handoff

Updated: 2026-09-24 UTC (September 23 in America/Toronto).

## Current priority

Continue P1/P2/P3 backend correctness, official-source coverage and dependable publication under `DEVELOPMENT_PROCESS.md`. Lot Size only; minimum investment, UI redesign, research-depth expansion and commercial infrastructure remain out of scope. Do not invent missing dates, issue sizes or price bands.

## Current batch: 15 independently verified BSE SME listings

PR #166: `feat/bse-verified-listing-batch-20260924`.

Base inspected: `4c1d6636839f026d4ba92906fbc25711cdac3a9d`. The preceding PR #165 discovery report contained 29 issuer references. This batch pins the newest 15, excluding both disputed scrip-code-544770 references. No additional issuer is added to the batch during retries.

### Source recovery and failed approaches

1. HTML verification run `35940961341` fetched all 15 issuer-specific URLs, but BSE returned empty ASP.NET notice templates. HTTP 200 was not accepted as listing evidence. Raw failed responses were retained.
2. Official PDF archive verification run `35941366768` downloaded all 15 real listing PDFs. The first strict verifier still rejected them because historical regulatory notice `20120216-29` was counted as header identity, and two subject columns wrap through the word `Subject` in PDF text.
3. Verifier v1.1 distinguishes header notice numbers from cited circulars and requires consistent issuer names from the subject, company table and/or explicit listing sentence. Missing source content is classified as unavailable; actual identity conflicts remain rejected. No market value was inferred to resolve these failures.
4. A new live fetch and verification run `35942438600` completed successfully: **15 verified, 0 rejected, 0 unavailable**. All 15 PDF hashes and all 45 facts match the earlier retained bytes and the reviewed evidence manifest. General data-contract CI for that verifier commit passed in run `35942438528`.

PDF pages 1 and 2 of every listing notice were also rendered and reviewed. Page 1 confirms the notice number, publication date and SME segment; page 2 explicitly states listing date, market lot and final issue price. These are independent exchange listing documents, not the index-addition PDFs.

### Reviewed source facts

| Issuer | BSE listing notice | Listing date | Market lot | Issue price (INR/share) |
| --- | --- | --- | ---: | ---: |
| ENS Enterprises | 20260820-37 | 2026-08-21 | 1,200 | 92 |
| Technocrats Plasma Systems | 20260820-35 | 2026-08-21 | 1,000 | 132 |
| LAPL Automotive | 20260812-34 | 2026-08-13 | 1,200 | 94 |
| Aegeus Technologies | 20260810-35 | 2026-08-11 | 1,200 | 105 |
| Fusion Klassroom Edutech | 20260806-43 | 2026-08-07 | 800 | 159 |
| Poojaa Precision Engg. | 20260803-22 | 2026-08-04 | 400 | 301 |
| Advance Technoforge | 20260731-25 | 2026-08-03 | 1,200 | 95 |
| Silverstorm Parks and Resorts | 20260730-40 | 2026-07-31 | 1,000 | 133 |
| Shree Balaji (Mala) Textiles | 20260728-26 | 2026-07-29 | 2,000 | 70 |
| Gulf Lloyds (India) | 20260724-6 | 2026-07-27 | 1,200 | 100 |
| Sotefin Bharat | 20260722-34 | 2026-07-23 | 600 | 187 |
| Sampark India Logistics | 20260706-28 | 2026-07-07 | 1,600 | 84 |
| Kratikal Tech | 20260706-34 | 2026-07-07 | 1,000 | 135 |
| Atharva Poly-Plast | 20260706-33 | 2026-07-07 | 2,000 | 60 |
| Seemax Resources | 20260706-30 | 2026-07-07 | 1,000 | 141 |

Exact source spelling, PDF URLs, document SHA-256, collection timestamps, publication dates and normalized page excerpts are in `data/verified-bse-listings/2026-09-24.json`. All 45 field facts cite PDF page 2. Scrip code and SME identity are independently checked before inclusion.

### Publication design

- `data/discovery/bse-listing-candidates-2026-09-24.json` retains the pinned discovery inputs and upstream report/text hashes; it is not publication authority.
- `verify-bse-listing-candidates.mjs` and `retry-bse-listing-pdf.mjs` run in an independent read-only verification workflow. They keep unavailable/rejected responses and actual PDF bytes in a 14-day artifact.
- `apply-verified-bse-listings.mjs` is a local-only importer for the reviewed committed batch. It revalidates the page excerpts, facts, identity, dates, page numbers and metadata, then uses the existing BSE record factory. It never downloads PDFs in hourly live sync.
- The importer creates missing records only. Existing identities, conflicting codes, concurrent field changes and correction histories are never overwritten. Reruns neither duplicate records nor freshen timestamps.
- The existing hourly sync applies this retained evidence, rebuilds the public dataset, validates it and uses the existing semantic publication retry path. No new write permission or paid service was added.
- Unverified price bands, open/close dates, monetary issue sizes, minimum bids and application amounts remain missing. Market lot is not copied into minimum bid quantity.

### Tests and release state

Local tests passed: all **33 test scripts**; syntax checks; all 15 actual-PDF replays; page/identity/price/lot negatives; unavailable-source and non-PDF cases; importer tampering/conflict/null-preservation tests; idempotent second import; deterministic rebuild and data validation.

The local publication rehearsal increased records from **922 to 937**, with all **922 existing published records unchanged**. Only the 2026 recovery manifest gained records; all other year manifests were byte-identical. The 2026 count would rise from 38 to 53 on this baseline. These are rehearsal counts until production data is checked.

At this checkpoint, live source verification is complete, but the final importer CI, PR merge, production bot publication and deployed-data verification remain **pending**. Do not label the 15 records live merely because their PDFs verified or a Pages build succeeded. Update this section after observing the production data revision.

### Evidence retention

Original PDF collection: run `35941366768`, artifact `10785245967`, ZIP SHA-256 `23bacb8997abc0bec91df8f3304260e5bd326c1f593162b69244f8148c2fc921`.

Successful re-verification: run `35942438600`, artifact `10784703620`, ZIP SHA-256 `64ec30157884145825c5404e47770f605b8b7a89ca8bd64612f1d7939c4df2e7`. This archive contains the 15 PDFs, failed HTML responses and complete verification report. Original collection timestamps remain in the reviewed manifest, not replaced by the later verification time. Conversation copies are retained; Actions artifacts expire after 14 days.

## Remaining blockers and next task

After production verification of this batch, continue with the **12 remaining unambiguous candidates** from the original 29-reference report. The other two candidates, MERRITRONIX LIMITED and YAASHVI JEWELLERS LIMITED, both claim code `544770`; keep them on hold until their original index PDFs and issuer-specific listing notices resolve the discrepancy.

The other **216 eligible index notices** were not covered by the original latest-20 audit. A durable versioned cursor is still needed for historical notice progress. Neither current index membership nor this 15-record batch establishes complete BSE IPO coverage for 2020-2026.

Recover missing fields only from new explicit official evidence. Do not repeat the already completed Angular-shell, empty-detail-response, plural-notice or listing-header diagnoses.

## Prior handoffs

The complete PR #165 discovery/CI repair status is preserved unchanged in `archive/PROJECT_STATUS-before-bse-listing-batch.md`. Older histories remain in `archive/PROJECT_STATUS-before-bse-notice-repair.md` and `archive/README-before-bse-notice-repair.md`. Current code, deployment evidence and this handoff supersede their stale next-task instructions.
