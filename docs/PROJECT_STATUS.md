# Project status and handoff

Updated **2026-09-26 (UTC)** after correcting the user-facing DRHP feature interpretation. The active backend priority remains **P1 issuer identity and universe correctness** under [DEVELOPMENT_PROCESS.md](DEVELOPMENT_PROCESS.md). The draft-offer collector remains separate from IPO-universe decisions, but its user-facing surface is now a **Pre-IPO companies** list rather than a filing-record directory. Other UI/research-depth work remains in [UI_DETAIL_NAVIGATION_HANDOFF.md](UI_DETAIL_NAVIGATION_HANDOFF.md).

## Release complete — do not replay

**PR #248 and PR #249 are merged.** AMIRCHAND and LEAP are resolved and published; the DRHP directory and its history-preserving refresh are verified on actual Pages. Do not replay approved imports from batches 1–9.

The current disposition is [nse-universe-current-review-2026-09-26.json](../data/discovery/nse-universe-current-review-2026-09-26.json): **105 approved IPOs + five debt-event exclusions + four migration exclusions + two rights-issue security exclusions + three unresolved NSE cases = 119 pinned groups**. Zero unreviewed groups remain in that original audit. This is **not full Indian IPO-universe completeness**.

**Exact next bounded backend task: GICL, VITAL and KOTYARK prior-offer/listing history review.** Use issuer-specific official notices/filings, not symbol spelling or aggregate observations. Reconcile latest main and actual Pages before action. Preserve each issuer's prior IPO history and all source conflicts; remain on hold when proof is insufficient.

## ADANIENPP1 and SILGOPP rights-security review — complete

Both previously held 2026 events are now positively classified from issuer-specific official evidence and excluded from the new-IPO queue. [The retained review](../data/discovery/nse-universe-rights-security-review-2026-09-26.json) records the decisions and literal source projections.

- **ADANIENPP1 / IN9423A01048 — Adani Enterprises Limited:** NSE circular NSE/CML/72630 calls the 10-Feb-2026 event a **further issue** and identifies the security as Re. 1 face value / Re. 0.75 paid up. The issuer separately states that this ISIN resulted from first-call conversion of partly paid shares **in relation to its Rights Issue**. The monitoring report records the rights-issue period as 25-Nov-2025 to 10-Dec-2025 and the security as partly paid equity.
- **SILGOPP / IN901II01012 — Silgo Retail Limited:** NSE circular NSE/CML/72851 explicitly describes the 19-Feb-2026 listing as **partly paid-up equity shares allotted on Rights Basis**. Silgo's Letter of Offer identifies a rights issue opening 14-Jan-2026 and closing 04-Feb-2026 at Rs. 60 per share, ratio 3 for 10.

No IPO record was added, removed or edited. The review classifies the 2026 security events only and does not erase or overwrite either issuer's earlier IPO/listing history.

One official-source conflict is preserved rather than silently resolved: NSE records SILGOPP allotment on **13-Feb-2026**, while Silgo's later first/final-call notice states **17-Feb-2026**. Both sources independently agree that the security was issued on a rights basis, so this disagreement does not affect the event classification.

Original PDF bytes were not materialized in this connector run. The review therefore retains literal official-source projections with SHA-256 hashes of those projections and explicitly leaves original-file hashes null; no projection hash is represented as an original PDF hash. No parser or adapter change was required, so no parser regression test was added.

## Pre-IPO companies — product interpretation corrected

Entry point: [Pre-IPO companies](../drhp.html), linked from the homepage on desktop and mobile. PR **#251** merged as `8fdc9bdfa8c1b03acb98ae9546ab0a9efabe0c66`. The product surface is **one company per row** for companies with retained DRHP/UDRHP evidence from SEBI. Each row shows the `DRHP filed` signal, latest retained draft date and official SEBI document. Draft-version counts remain internal/source evidence rather than the main feature. The post-merge GitHub Pages deployment workflow completed successfully.

The previous document-centric wording (`DRHP filings`, filing-record metric, filing-version emphasis) was the wrong product interpretation and has been removed from the user-facing page. Draft filings remain separate from the IPO dataset; there is no automatic IPO creation or claim of IPO approval, opening, completion or listing.

| Verified DRHP result | Value |
| --- | ---: |
| Companies | **90** |
| Unique DRHP/UDRHP filing URLs | **91** |
| Coverage year | **2026** |
| SEBI pages checked | **8** |
| Unique filings observed in latest scan | **89** |
| Earlier filings retained despite absence from latest scan | **2** |
| Source pagination consistent | **No** |
| Complete DRHP register | **No** |

History retention remains non-destructive: a missing row in a later SEBI index scan is not withdrawal evidence. The latest scan returned **91 observations**, including **two duplicates**, for **89 unique filings observed in that scan**. Two earlier retained filings remain in the union, producing **91 retained source documents across 90 companies**.

Source page totals varied between **2,212 and 2,214**. The UI exposes that inconsistency and incomplete coverage. Only explicit 2026 DRHP/UDRHP markers are included; addenda, corrigenda, unlabelled rows, other years and exchange-only filings are outside this release's coverage.

### Reliability and publication

PR #249 merged as **253b2d1b11341e240c4e1ea11742a76c1ffd8cef**. The repair preserves filing history, counts globally unique filing URLs, rejects stale/conflicting data and unsafe source URLs, detects non-advancing pages, retains original page bytes and separates collection health from the list. A failed collection leaves the last good dataset available and records the failure. The leftover temporary identity collector was removed from ordinary CI.

The existing DRHP workflow remains scheduled daily at **06:43 UTC**; execution timing is controlled by GitHub Actions. It is bounded to 16 pages and stops at the first page strictly older than the selected year. It publishes only its DRHP dataset/collection-status files and verifies actual served data and page assets afterward.

Normal DRHP refresh **36213264969 — success**. Published commit **43fbd1f519701fe8b149cf7038f76e3709a1a5dd**. Retained artifact **10895679053**, SHA-256 **bf2b71bdd21218237d8d03c90521a3b1aba023e538446fee300a1b6711ac880f**.

Collection completed **2026-09-26T02:56:59.438Z**. Actual dataset fetched **02:57:47.820Z**; verification completed **02:57:48.027Z**. Served dataset SHA-256 **a74943eca9e7bc66d0e791b25f9c59b2347ae37609d4448bfd0f3e373bf51b38**, **138,745 bytes**. All five checked files matched published bytes: `data/drhp-filings.json`, `drhp.html`, `assets/drhp.js`, `assets/styles.css`, and `index.html`. All eight original source-page hashes and byte counts were revalidated.

Collection status was checked in the repository and retained artifact. The five-file live verifier does not separately fetch `ops/drhp-collection.json`; do not describe that health file as independently byte-verified on Pages.

## AMIRCHAND and LEAP — previous identity release finalized

PR #248 merged as **a6577265048c5d7e4855feac34a3b6c06800e969**. The reusable fallback requires positive retained official identity and IPO/listing evidence and is allowed only for missing, not contradictory, endpoint metadata. The original missing metadata remains preserved.

| Issuer | IPO lookup symbol | Listed symbol | ISIN |
| --- | --- | --- | --- |
| Amir Chand Jagdish Kumar (Exports) Limited | AMIRCHAND | AMIRCHAND | INE05TO01019 |
| Leap India Limited | LEAP | **LEAPIND** | INE00GO01025 |

Batch9 retains **two issuers / 12 reviewed facts**. Market lot and minimum bid remain distinct; neither market lot nor application amount is manufactured from a minimum bid. Sources and decisions remain in [the identity review](../data/discovery/nse-universe-held-identity-review-2026-09-26.json), [batch9 manifest](../data/verified-nse-ipos/2026-09-25-batch9.json), and [rehearsal receipt](verification/nse-held-identity-drhp-rehearsal-2026-09-26.json).

### Retained actual IPO observation rechecked

The actual Pages dataset fetched **2026-09-26T02:21:48.511Z**, retained by review run **36211433801**, contains **1,323 records**. All nine reviewed batches pass **105 issuers / 627 facts**, including **2/2 identities and 12/12 batch9 facts**. Unknown/invalid statuses and records missing status evidence are both zero. Status distribution: **1,302 listed / 12 open / 7 closed / 2 upcoming**. Snapshot SHA-256 **81a133ee87dfcc1e2fb09a3881361b374902722bbd48bfa8e155d75f3f40838e**.

This is the retained **02:21 UTC IPO observation**, not a new 02:57 UTC IPO fetch. Routine historical PDF fills subsequently advanced main. PR #249 itself did not edit IPO records or the identity parser.

Against the retained 1,321-record pre-release baseline, exactly the two approved identities were added and none removed. **1,317 existing records were unchanged**. Four routine-pipeline record changes are separate: Vigor Plast India, Hyundai Motor India and R R Kabel received six previously missing offer dates; Vigor, R R Kabel and Aether Industries received eight document additions in total, with timestamps. No prior populated displayed value or status changed in that snapshot comparison. Those external routine-fill PDFs were not independently reopened here, and optional fields are not counted among the 12 batch9 facts.

## Tests and release evidence

PR #249 final-head CI passed: full data contract **36212457450**, interface **36212457353**, reviewed-BSE compatibility **36212457388**. Merged-main full contract **36213264978** also passed. Local retained-source parser, integrity, UI-contract, nine-batch IPO regression, publication-rehearsal, build and schema checks passed.

Exact fetched DRHP HTML/CSS/JavaScript and JSON were rendered offline in Chromium at **320, 375 and 1440 pixels**. Search, no-results, invalid-data rejection, error/retry, failed-refresh/last-good-list messaging and mobile navigation passed; no page overflow or JavaScript page errors. Local browser networking was unavailable; these are offline rendering checks, while actual remote byte verification was performed by the successful Actions workflow.

Durable combined receipt: [drhp-identity-release-live-2026-09-26.json](verification/drhp-identity-release-live-2026-09-26.json). Original repair evidence: run **36211433801**, artifact **10896315080**, SHA-256 **73e0a80da65cbc52ed2ce4c5d4a9635e0306f4b2ea594298ff007a1bdc68615d**. The earlier temporary materializer failed to publish workflow edits with its runner token; the authorized connector completed those edits without changing access policy. No temporary materializer remains in the merged repair.

## Remaining work and preserved history

Active NSE holds: **GICL, VITAL, KOTYARK**. These are now the exact next bounded review. **Fabino Life Sciences** remains a separate BSE listing-year hold. Keep positive debt/migration/rights-event exclusions out of the new-IPO queue while independently reviewing their issuers' original historical equity IPOs.

Broader BSE issue-summary, SEBI historical pagination and NSE-series gaps remain. **BSE parser v1.5 is 236/236 parsed; do not replay its completed cursor.** DRHP coverage expansion must address inconsistent pagination/unlabelled disclosures without treating an observed draft filing as a new approved IPO.

The old canonical review and seven-case hold files dated September 25 are preserved as historical snapshots. Use the linked **September 26 current-review state**, not their stale next-task fields, for new work.

The immediately preceding README and project-status versions are archived byte-for-byte as `docs/archive/README-before-pre-ipo-company-list-correction-2026-09-26.md` and `docs/archive/PROJECT_STATUS-before-pre-ipo-company-list-correction-2026-09-26.md`. Earlier manifests, archives, evidence and receipts remain intact. Actions artifacts expire after 14 days; the repository retains literal projections, URLs, dates, document identities, hashes and locators.

No minimum-investment expansion, billing/accounts/ads, spending or access-policy changes were introduced.
