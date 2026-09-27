# Project status and handoff

Updated **2026-09-27 (UTC)** after publishing Jetmall Spices / Brandbucket Media. Active priority remains **P1 issuer identity and universe correctness**.

## Exact next bounded task

The original **16 unmatched BSE 2021 rows are fully resolved**: **15 reviewed IPOs published + 1 existing-recovery alias (FSN/NYKAA)**. Do not replay the 2021 unmatched queue.

Start the next bounded P1 source-family review with two **2022 Mainboard** unmatched rows from the retained BSE audit: **Veranda Learning Solutions Limited (543514)** and **Uma Exports Limited (543513)**. Reconcile against latest recovery first, then obtain issuer-specific official BSE/SEBI evidence and original bytes. The 2022 audit has **90 official rows / 74 exact matches / 16 unmatched**; this is not a complete Indian IPO-universe claim.

## Latest release — final 2021 pair complete

PR **#305** merged as **5bb6a53fcd6feacfce1bb6ba3cb574c9476f8453**. Publication commit **f18c05a5a6677f37e1b1c1f21b404a162574a245** added **Sigachi Industries Limited** and **Adeshwar Meditex Limited** to 2021 recovery. **Do not replay this batch.**

| Issuer | Board | Listing | Issue price | Issue size | Market lot | Minimum bid | Offer dates |
| --- | --- | --- | ---: | ---: | ---: | ---: | --- |
| Sigachi Industries Limited | missing | 15-Nov-2021 | INR 163 | INR 1,254,285,000 | 1 | 90 | 01–03 Nov-2021 |
| Adeshwar Meditex Limited | SME | 28-Jun-2021 | INR 25 | INR 97,500,000 | 6,000 | 6,000 | 15–18 Jun-2021 |

Four original official PDFs were retained in successful collection run **36294152639**: **31,154,774 response bytes**, artifact **10923273210**, SHA-256 **5a21b43d148fd8dc1179e21b1455978de3daa485819682abdc69ad363ae42e8f**. Sigachi is bound to its SEBI final Prospectus and a SEBI-hosted BRLM past-issues table; Adeshwar is bound to its BSE-hosted Prospectus and a SEBI-hosted lead-manager past-issues table.

The release deliberately keeps BSE scrip codes as discovery metadata and leaves unsupported price-band / ISIN / NSE identity fields null. Sigachi's one-share trading lot and 90-share minimum bid quantity remain distinct fields; they must not be collapsed. PR-head publication rehearsal **36313752438**, reviewed-BSE validation **36313752391**, and full data-contract run **36313752361** passed. Merged-main publication run **36313829030** validated and published successfully. **Actual Pages verification run 36314083474 passed on attempt 1:** served `data/ipos.json` contains **1,353 records**, dataset generation timestamp **2026-09-27T10:50:59.911Z**, SHA-256 **a9058c8ed9a207cf9448c9074e0c2bfedab1fc21abba198140b6ab649bc9d200**. The original BSE 2021 unmatched queue is therefore **fully resolved and live-verified**.

## Latest release — Jetmall Spices and Brandbucket Media

PR **#302** merged as **f39725b46085dabddd33b1441d8f23b950930ebc**. Publication commit **f36dad255d2fcc491f93c9d6f29e29dd28db4cc6** added exactly two 2021 recovery records and rebuilt `data/ipos.json`. **Do not replay this batch.**

| Issuer | Board | Listing | Issue price | Issue size | Market lot | Minimum bid quantity | Offer dates |
| --- | --- | --- | ---: | ---: | ---: | ---: | --- |
| Jetmall Spices and Masala Limited | SME | 19-Apr-2021 | INR 20 | INR 49.8m | 6,000 | 6,000 | 31-Mar–07-Apr-2021 |
| Brandbucket Media & Technology Limited | SME | 31-Dec-2021 | INR 55 | INR 82.5m | 2,000 | 2,000 | 20–23 Dec-2021 |

Five original BSE/SEBI PDFs were retained in collection run **36292730634**: **21,126,205 response bytes**, artifact **10922279333**, SHA-256 **5e8bd0331c0a13ab112ea175040a4459ebae109e6927e36c193acb4f7dca86aa**. Jetmall is bound to its SEBI final Prospectus for original terms and a SEBI-hosted lead-manager track record for listing date; Brandbucket is bound to its BSE-hosted Prospectus plus a SEBI-hosted lead-manager track record. The Jetmall BSE draft is retained as corroborating original evidence.

Market lot and minimum bid quantity are stored separately because the prospectuses state both separately; equality is not inferred. **BSE scrip codes remain discovery metadata only**, and price bands, ISIN/NSE identities and unsupported values remain null.

PR-head dedicated publication rehearsal **36293015660**, reviewed-BSE validation **36293015649**, and full data-contract run **36293015652** passed. Merged-main publication run **36293086864** validated and published successfully; merged-main data contract **36293086793** passed. A clean documentation merge follows this note to trigger a post-publication Pages served-byte verification before the batch is marked fully live-verified.

## Latest release — HP Adhesives and Nuvoco Vistas

PR **#299** merged as **93c5bb0a880991b6bd7a767f0a4647803af18451**. Publication commit **2af9da4046d61c3d91438fd498cfd4745df943e6** added exactly two 2021 recovery records and rebuilt `data/ipos.json`. **Do not replay this batch.**

| Issuer | Listing | Issue price | Issue size | Offer dates |
| --- | --- | ---: | ---: | --- |
| HP Adhesives Limited | 27-Dec-2021 | INR 274 | INR 1,259,633,000 | 15–17 Dec 2021 |
| Nuvoco Vistas Corporation Limited | 23-Aug-2021 | INR 570 | INR 50,000,000,000 | missing |

Three original SEBI PDFs were retained in collection run **36291613284**: **9,016,934 response bytes**, artifact **10922282542**, SHA-256 **7c6dbe124e583c0a95753c8641186b84b17e4e6ee135503a51c9d817679de318**. HP is bound to the final Prospectus for IPO identity, ₹274 price, ₹12,596.33 lakh aggregate offer and 15–17 Dec offer dates, plus a SEBI-hosted BRLM track-record document for the 27-Dec listing date. Nuvoco is bound to the September 2021 SEBI Bulletin for IPO identity, 23-Aug listing, ₹570 issue price and ₹5,000 crore issue size.

Only directly supported fields were published. **Board, BSE scrip code, market lot, minimum bid quantity, price band, ISIN/NSE identity and unsupported values remain null in this batch.** The BSE codes 543433 and 543334 remain discovery metadata only. HP/Nuvoco PR-head publication rehearsal **36291857793**, reviewed-BSE validation **36291857728**, and full data-contract run **36291857749** passed; merged-main publication run **36291915717** and data-contract run **36291915690** also passed.

**Actual Pages verification run 36292097474 passed on attempt 1:** served `data/ipos.json` contained **1,349 records**, generation timestamp **2026-09-27T03:37:14.445Z**, SHA-256 **68a5a3dbb6cdb78e71688dcb3d8545b139da1e31ba7fe55af4260661d3b09d34**. HP Adhesives and Nuvoco are therefore **published and live-verified**.

## Latest bounded review — Sigachi / Adeshwar held, no publication

Both issuers remain absent from recovery. Fresh official-source probing run **36290437470** successfully retained only the two BSE HTML responses for the tested notice URLs; the SEBI URLs returned 404. A second probe replaced those with guessed BSE prospectus URLs, which also returned 404. Strict issuer-specific listing verification then showed the tested notice numbers were unrelated: **20211112-34** was a BSE membership notice, and **20210614-39** was an ESOP/further-securities notice. Both were rejected for issuer/code/date/SME/equity-listing mismatch. No importer, manifest, recovery record or public-data change was created.

This is a useful negative result: do not weaken the verifier, do not infer IPO terms from the historical issue-summary row, and do not reuse the failed exploratory URLs. Sigachi and Adeshwar remain in the seven-row pending queue for a later source-family approach.

## Latest release — Getalong Enterprise and Shri Venkatesh Refineries

PR **#295** merged as **a8157cbc2b54441568de67a904d9ef0fbcd0f5f8**. Publication commit **a408b27b84e8187b78721a969474088e9a8c3ded** added exactly two 2021 recovery records and rebuilt the public dataset. **Do not replay this batch.**

| Issuer | Board | Listing | Issue price | Gross issue | Historical lot | Minimum bid | Offer dates |
| --- | --- | --- | ---: | ---: | ---: | ---: | --- |
| Getalong Enterprise Limited | SME | 08-Oct-2021 | INR 69 | INR 51.75m | 2,000 | missing | missing |
| Shri Venkatesh Refineries Limited | SME | 11-Oct-2021 | INR 40 | INR 117.12m | 3,000 | 3,000 | 29-Sep–01-Oct-2021 |

Four issuer-specific BSE PDFs were retained in collection run **36288334517**: **10,811,327 original response bytes**, artifact **10920948015**, SHA-256 **59b253317b595943d71100faf3dd61873e17053f42ee1c0412ba83c7dc3ee2ff**. Getalong is bound to its BSE-hosted draft prospectus plus issuer annual-report filing; SVRL is bound to its BSE-hosted final prospectus plus BSE listing/index release. Unsupported price bands, ISIN/NSE identity and Getalong offer/minimum-bid fields remain missing. Market lot and minimum bid quantity remain distinct.

PR-head publication rehearsal **36288408467**, reviewed-BSE validation **36288408451**, and full data-contract run **36288408461** passed. Merged-main publication run **36288465950** validated and published successfully. **Actual Pages verification run 36288580617 passed on attempt 1:** served `data/ipos.json` contains **1,347 records**, generation timestamp **2026-09-27T02:25:51.579Z**, SHA-256 **a4bd158642fb2f62709d564c9f7dffe8edafe4abe75e4271f4f70185bdfdf364**. Getalong and SVRL are therefore **published and live-verified**.

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
