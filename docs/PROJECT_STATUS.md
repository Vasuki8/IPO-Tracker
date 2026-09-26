# Project status and handoff

Updated **2026-09-26 (UTC)** while repairing Pre-IPO source coverage after Abakkus Asset Manager exposed a single-source discovery gap. The active backend priority remains **P1 issuer identity and universe correctness** under [DEVELOPMENT_PROCESS.md](DEVELOPMENT_PROCESS.md). The Pre-IPO surface stays lifecycle-aware; source discovery is being expanded from the SEBI draft index to configured official lead-manager offer-document sources. Other UI/research-depth work remains in [UI_DETAIL_NAVIGATION_HANDOFF.md](UI_DETAIL_NAVIGATION_HANDOFF.md).

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

Entry point: [Pre-IPO companies](../drhp.html), linked from the homepage on desktop and mobile. PR **#251** established the company-centric surface; PR **#252** (`a5b797b047abffe6406559461bc79e0ace88664c`) made it lifecycle-aware. The browser validates both `data/drhp-filings.json` and `data/ipos.json`, then removes any exact canonical legal-name match whose IPO is `upcoming`, `open`, `closed`, or `listed`, or that already carries a published IPO open/close/listing date. DRHP source history remains retained. The identity comparison mirrors the universe audit's conservative normalization (`&`/`and`, `Ltd`/`Limited`, punctuation/case); fuzzy matching is prohibited. If either lifecycle dataset is unavailable or invalid, the page fails closed.

The previous document-centric wording (`DRHP filings`, filing-record metric, filing-version emphasis) was the wrong product interpretation and has been removed from the user-facing page. Draft filings remain separate from the IPO dataset; there is no automatic IPO creation or claim of IPO approval. A company leaves the visible Pre-IPO page when the independently published IPO lifecycle proves it has progressed; the source DRHP record is never deleted by that transition.

| Verified DRHP result | Value |
| --- | ---: |
| Draft-backed companies retained | **90** |
| Visible true pre-IPO companies | **82** |
| Progressed issuers hidden dynamically | **8** |
| Unique DRHP/UDRHP filing URLs | **91** |
| Coverage year | **2026** |
| SEBI pages checked | **8** |
| Unique filings observed in latest scan | **90** |
| Earlier filing retained despite absence from latest scan | **1** |
| Source pagination consistent | **No** |
| Complete DRHP register | **No** |

History retention remains non-destructive: a missing row in a later SEBI index scan is not withdrawal evidence. The latest scan returned **92 observations**, including **two duplicates**, for **90 unique filings observed in that scan**. One earlier retained filing remains in the union, producing **91 retained source documents across 90 companies**. Current lifecycle reconciliation hides **8** progressed issuers and leaves **82** visible as true pre-IPO companies.

Source page totals varied between **2,212 and 2,214**. The UI exposes that inconsistency and incomplete coverage. **Abakkus Asset Manager Limited was not present in the current SEBI draft-offer index despite being published as a DRHP by official book-running lead-manager sources.** The collector is therefore adding an Axis Capital official offer-document fallback. Coverage remains partial: addenda, corrigenda, unlabelled SEBI rows, other years and unconfigured lead-manager sources remain outside the claimed universe.

### Reliability and publication

PR #249 merged as **253b2d1b11341e240c4e1ea11742a76c1ffd8cef**. The repair preserves filing history, counts globally unique filing URLs, rejects stale/conflicting data and unsafe source URLs, detects non-advancing pages, retains original page bytes and separates collection health from the list. A failed collection leaves the last good dataset available and records the failure. The leftover temporary identity collector was removed from ordinary CI.

The draft-source workflow is being changed to run **every two hours at minute 17 UTC**, subject to GitHub Actions scheduling. The SEBI collector remains bounded to 16 pages and stops at the first page strictly older than the selected year; configured official lead-manager source pages are checked in the same run. It publishes only its draft-evidence dataset/collection-status files and verifies actual served data and page assets afterward.

Post-PR #252 DRHP refresh **36218461502 — success**. Collection completed **2026-09-26T04:39:23.635Z**. The verifier initially observed the prior served dataset while Pages was propagating, retried, and finished **verified** at **2026-09-26T04:40:12.294Z**. Final served bytes matched all six checked files: `data/drhp-filings.json`, `drhp.html`, `assets/pre-ipo-filter.js`, `assets/drhp.js`, `assets/styles.css`, and `index.html`. Served DRHP dataset SHA-256 **fbc56ba56a7db53686c725843e4b8e121cbb3017fb979020b2045ba9228d941c**. The lifecycle helper itself matched SHA-256 **10b2656b301f3505df45e1dc7b3f3b6a86a9c89a5e4e8ce9943ed7183069c4e3**.

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
