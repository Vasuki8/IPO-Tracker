# Project status and handoff

Updated **2026-09-26 (UTC)** after completing the official BSE 2020–2026 historical coverage audit and publishing/verifying its five high-priority reconciliation actions. The active backend priority remains **P1 issuer identity and universe correctness** under [DEVELOPMENT_PROCESS.md](DEVELOPMENT_PROCESS.md). The pinned NSE review, nine historical excluded-event IPO repairs, Fabino, and the first BSE reconciliation batch are closed through reviewed evidence-backed paths. The next bounded task is the four unmatched BSE 2020 issuers. The Pre-IPO source-coverage repair remains live and separate. Other UI/research-depth work remains in [UI_DETAIL_NAVIGATION_HANDOFF.md](UI_DETAIL_NAVIGATION_HANDOFF.md).

## Release complete — do not replay

**PR #248 and PR #249 are merged.** AMIRCHAND and LEAP are resolved and published; the DRHP directory and its history-preserving refresh are verified on actual Pages. Do not replay approved imports from batches 1–9.

The current disposition is [nse-universe-current-review-2026-09-26.json](../data/discovery/nse-universe-current-review-2026-09-26.json): **105 approved IPOs + five debt-event exclusions + seven migration exclusions + two rights-issue security exclusions = 119 pinned groups**. **Zero unresolved and zero unreviewed groups remain in that pinned audit.** This is still **not full Indian IPO-universe completeness**.

**Exact next bounded backend task: review the four unmatched BSE 2020 issuers — Likhitha Infrastructure Limited (543240), Secmark Consultancy Limited (543234), SM Auto Stamping Limited (543065), and Shine Fashions (India) Limited (543244).** Treat the BSE historical rows as discovery evidence only. Verify each issuer's legal identity, IPO/issue type, board, offer facts and listing from issuer-specific official BSE/SEBI/issuer sources; materialize original bytes/hashes; import only independently supported records through a reviewed collision/idempotency-safe path.

## BSE historical coverage audit and high-priority reconciliation — published and verified live

[The retained read-only audit](../data/discovery/bse-issue-summary-coverage-audit-2026-09-26.json) now characterizes the official BSE historical source for the project window. BSE exposes **2017–2026**; the audit fully collected **2020–2026**, reconciled every official per-year row total, retained raw response hashes/fetch timestamps, and made **zero automatic imports**.

Audit snapshot before reconciliation:
- **920 historical rows + 32 current-issue rows**
- **666 exact / 3 prefix / 0 ambiguous / 251 unmatched**
- **3 listing-date conflicts**
- official project-window totals reconciled for every year
- audit run **36256389220**, artifact **10910408234**
- not a complete Indian IPO-universe claim

The five high-priority findings were then reviewed from issuer-specific official evidence. [The review](../data/discovery/bse-issue-summary-high-priority-reconciliation-2026-09-26.json) is bound to [a durable 10-document source receipt](../data/evidence/bse-high-priority-reconciliation-source-receipt-2026-09-26.json): **43,318,707 original response bytes**, artifact **10912597972**, digest **sha256:5728fd05047d366a11585224b49fe2bc9472ac50ad0ba43aca6102d6124d547a**.

Published actions:
- **CAMS:** moved from recovery 2021 to 2020; listing **01-Oct-2020**, issue price **₹1,230**, offer **21–23 Sep 2020**; prior wrong 2021/₹1,240 observations retained in correction history.
- **Protean eGov:** moved from recovery 2025 to original IPO year 2023; listing **13-Nov-2023**, price **₹792**, offer **06–08 Nov 2023**; later **06-Feb-2025 NSE listing** retained separately.
- **Fabtech Technologies Limited:** added as a distinct 2025 Mainboard IPO; **Fabtech Technologies Cleanrooms Limited** remained unchanged.
- **Happy Forgings Limited:** legal name corrected, stable ID/listing facts preserved.
- **Kronox Lab Sciences Limited:** legal-name spacing corrected, stable ID/listing facts preserved.

PR **#269** merged as **c24dbe0311426649f65b41a8ddb03c7df76a1fc7**; PR **#270** made the regression test valid both before and after application; publication commit **b8ee98c5a8c74b56d0ea580ab9ceac793ea5e341** applied the changes.

Actual Pages verification run **36266960117** passed **5/5 actions / 0 failures** after one normal cache retry. The verified served snapshot contains **1,334 records**, fetched **2026-09-26T19:42:51.919Z**, SHA-256 **9752d227d037e1ffd8994d10cc52f9f8a373da751266934970a07a0cd10ab764**, retained in artifact **10914368318**.

## Fabino Life Sciences listing-year correction — published and verified live

The separate Fabino BSE hold is resolved. [The retained review](../data/discovery/bse-fabino-listing-year-review-2026-09-26.json) preserves the source conflict: BSE Notice **20220112-10** is dated 12-Jan-2022 but one listing sentence says **"January 13, 2021"**. The same notice schedules the Special Pre-open Session for **13-Jan-2022**, and independent BSE SME IPO Index evidence explicitly confirms the company was listed effective **13-Jan-2022**.

Published historical record:
- **Issuer:** Fabino Life Sciences Limited
- **BSE scrip / symbol:** 543444 / FABINO
- **ISIN:** INE0DRT01018
- **Board:** SME
- **Offer:** 31-Dec-2021 to 05-Jan-2022
- **Issue price:** ₹36
- **Market lot:** 3,000
- **Listing date:** **13-Jan-2022**

Evidence materialization run **36248932290** retained **4 official BSE/SEBI documents / 12,642,908 response bytes** in artifact **10908566869**, digest **sha256:b1dce44e5806fa6998cc25a4895159c4b2f2d32d1e7d65afc11a03606e26a841**. PR **#264** merged as **5391027eaac6c18724f482c2ef1c5111a33f0f7d**; publication commit **6d7fad63f478d17d8238a0976efb1f4a247866ef** added one 2022 recovery record.

Actual Pages verification run **36254088389** passed **5 reviewed fields / 0 errors**. The fetched dataset contains **1,333 records**; snapshot fetched **2026-09-26T16:04:08.456Z**, SHA-256 **64a6ddbfb04e556f9f1deca2f54038561e1bed4444702a6a94b06af5eb8269ad**, retained in artifact **10909383646**.

The erroneous 2021 notice text remains in the listing-date correction history. The generic BSE listing parser was **not** relaxed.

## Historical IPO coverage for nine excluded-event issuers — published and verified live

The historical-equity coverage gap behind the nine earlier 2026 debt/migration exclusions is now closed through the reviewed recovery/publication path. [The retained review](../data/discovery/excluded-event-issuer-historical-ipo-review-2026-09-26.json) verifies **9/9 historical equity IPOs**, [the durable source receipt](../data/evidence/historical-ipo-nine-source-receipt-2026-09-26.json) binds the review to **25 original official documents / 146,148,394 response bytes**, and [the approved import manifest](../data/verified-historical-ipos/2026-09-26-nine.json) maps only explicit fields to those retained sources.

| Excluded 2026 event | Historical equity symbol | Historical listing |
| --- | --- | --- |
| 10MWL29 | MWL | 11-Jul-2022 |
| QMSMEDI migration | QMSMEDI | 11-Oct-2022 |
| 12VPT28A | VIVIANA | 16-Sep-2022 |
| ANNAPURNA migration | ANNAPURNA | 27-Sep-2022 |
| SWARAJ migration | SWARAJ | 28-Mar-2022 |
| 1150VIES30 | VIESL | 13-Sep-2024 |
| 12AIL28 | AVPINFRA | 20-Mar-2024 |
| DOLLEX migration | DOLLEX | 28-Dec-2022 |
| 13DCCL28 | DCCL | 28-May-2025 |

Evidence materialization run **36244158677** retained source artifact **10906719463** with digest **sha256:6f0a6ad7fbe3ece39e2b010d66bb9a306ffe4d2590b67c02e4980c3b42c90c52**. PR **#261** merged as **85e6e96239089ec7237c34cca17df912af029ce0**; the race-safe publication workflow created commit **e956549413205d2cfe6c7e7aa563f91804929ff1**.

Actual Pages verification run **36248129988** passed **9/9 issuers / 33 reviewed fields / 0 failures**. The fetched public dataset contains **1,332 records**; snapshot fetched **2026-09-26T14:20:28.176Z**, SHA-256 **d6a7ada5aeb2f20b0445efa2c04d0a2033f3e0df809e4be46756492d0ebb9004**, retained in verification artifact **10908262582**.

**Zero excluded 2026 events were reintroduced.** Source-policy boundaries remain conservative: VIESL offer dates and SWARAJ offer terms remain missing because this release did not expand the accepted publication-host allowlist to their reviewed source hosts. Missing fields stay missing rather than being copied from weaker evidence.

## GICL, VITAL and KOTYARK migration review — complete

The final three NSE holds are positively classified as **migration events, not new 2026 IPOs**. [The retained review](../data/discovery/nse-universe-final-migration-review-2026-09-26.json) records the issuer-specific official evidence and preserved conflicts.

- **GICL / Globe International Carriers Limited / INE947T01022:** NSE listing approval states that the equity shares were admitted to the Main Board effective **18-Feb-2026 pursuant to migration from SME Emerge**. A 2025 official filing also explains the ISIN change from INE947T01014 to INE947T01022 after a face-value split; that security maintenance is not a new IPO.
- **VITAL / Vital Chemtech Limited / INE0L4K01016:** an official issuer filing to NSE states that the company was earlier on NSE EMERGE and its equity shares were listed on the Main Board effective **11-Mar-2026 upon migration**. The 2022 IPO history remains separate; NSE Market Pulse identifies the 14-Nov-2022 listing as an SME-IPO.
- **KOTYARK / Kotyark Industries Limited / INE0J0B01017:** NSE Circular **NSE/CML/73219** explicitly states migration from SME EMERGE to the Main Board effective **12-Mar-2026** and references the original 2021 SME listing circular. Issuer financial statements separately retain the 2021 IPO details (21–25 Oct 2021, Rs.51, listed 2-Nov-2021).

No public IPO record was added, removed or edited. Price/source conflicts are retained rather than used to reinterpret the 2026 migration events. Original PDF bytes were not materialized in this connector review; retained projection hashes are hashes of the literal review projections only.

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
| Draft-backed companies retained | **95** |
| Visible true pre-IPO companies | **84** |
| Progressed issuers hidden dynamically | **11** |
| Unique DRHP/UDRHP filing URLs | **97** |
| Coverage year | **2026** |
| SEBI pages checked | **8** |
| Earlier filings retained despite absence from latest scan | **3** |
| Corrected invalid supplemental rows | **3** |
| Source pagination consistent | **No** |
| Complete DRHP register | **No** |

History retention remains non-destructive, but proven adapter mistakes are correction-aware rather than retained forever. The final v2.2 union contains **95 draft-backed companies / 97 filings**; current lifecycle reconciliation hides **11** progressed issuers and leaves **84** visible as true Pre-IPO companies. Abakkus Asset Manager Limited remains visible with DRHP date **22-Sep-2026**.

Source page totals continue to vary between **2,212 and 2,214**, so SEBI pagination is not treated as a complete register. **Abakkus Asset Manager Limited was missing from the SEBI draft index but present on Axis Capital's official offer-document page; it is now discovered automatically from that fallback.** The first live fallback also exposed mirror/re-upload timing issues. PRs **#254–#256** corrected those projections and removed three invalid legacy supplemental rows with retained correction history. Coverage remains partial: unconfigured lead-manager sources, unlabelled SEBI rows, other years, addenda and corrigenda remain outside the claimed universe.

### Reliability and publication

PR #249 merged as **253b2d1b11341e240c4e1ea11742a76c1ffd8cef**. The repair preserves filing history, counts globally unique filing URLs, rejects stale/conflicting data and unsafe source URLs, detects non-advancing pages, retains original page bytes and separates collection health from the list. A failed collection leaves the last good dataset available and records the failure. The leftover temporary identity collector was removed from ordinary CI.

The draft-source workflow now runs **every two hours at minute 17 UTC**, subject to GitHub Actions scheduling. The SEBI collector remains bounded to 16 pages and stops at the first page strictly older than the selected year; configured official lead-manager source pages are checked in the same run. It publishes only its draft-evidence dataset/collection-status files and verifies actual served data and page assets afterward.

Final cleanup PR **#256** merged as **399e272c2c5731873fbc602539e68e2e0a84b7bb**. Post-merge source refresh **36238943188 — success** produced publication commit **51d13484a28c7f61eeab828175c8cf05fbe7db45**. Live verification completed **2026-09-26T11:29:55.995Z** and all six checked files matched published bytes: `data/drhp-filings.json`, `drhp.html`, `assets/pre-ipo-filter.js`, `assets/drhp.js`, `assets/styles.css`, and `index.html`. Served DRHP dataset SHA-256 **4a5b5fb545eb99e653a019b2628f9e19ddbb4a0d9bda2fa823b65f85bb2fa8c5**.

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

BSE historical audit/reconciliation: PR **#266** added the read-only BSE coverage audit; PR **#267** created the five-action evidence batch; PR **#268** added Protean's original BSE listing proof; PR **#269** added the reviewed importer/verifier; PR **#270** fixed post-apply test semantics. Evidence materialization run **36262801644** passed. PR #269 final-head data contract **36266680368** and reviewed-BSE compatibility **36266680426** passed after the manifest contrast fix; publication run **36266941993** passed; live verification **36266960117** passed and retained artifact **10914368318**.

Fabino release: PR **#263** materialized the four official sources; PR **#264** added the reviewed correction importer and verifier. PR #264 final-head full data contract **36253989366** and reviewed-BSE compatibility **36253989374** passed. Publication workflow **36254067566** passed. Actual Pages verification **36254088389** passed and retained artifact **10909383646**.

Historical IPO release: PR **#259** added source materialization; PR **#260** fixed durable receipt publication; PR **#261** added the reviewed historical importer and verifier. PR #261 final-head full data contract **36248058518** and reviewed-BSE compatibility **36248058467** passed. Publication workflow **36248110656** passed. Actual Pages verification **36248129988** passed and retained artifact **10908262582**.

PR #249 final-head CI passed: full data contract **36212457450**, interface **36212457353**, reviewed-BSE compatibility **36212457388**. Merged-main full contract **36213264978** also passed. Local retained-source parser, integrity, UI-contract, nine-batch IPO regression, publication-rehearsal, build and schema checks passed.

Exact fetched DRHP HTML/CSS/JavaScript and JSON were rendered offline in Chromium at **320, 375 and 1440 pixels**. Search, no-results, invalid-data rejection, error/retry, failed-refresh/last-good-list messaging and mobile navigation passed; no page overflow or JavaScript page errors. Local browser networking was unavailable; these are offline rendering checks, while actual remote byte verification was performed by the successful Actions workflow.

Durable combined receipt: [drhp-identity-release-live-2026-09-26.json](verification/drhp-identity-release-live-2026-09-26.json). Original repair evidence: run **36211433801**, artifact **10896315080**, SHA-256 **73e0a80da65cbc52ed2ce4c5d4a9635e0306f4b2ea594298ff007a1bdc68615d**. The earlier temporary materializer failed to publish workflow edits with its runner token; the authorized connector completed those edits without changing access policy. No temporary materializer remains in the merged repair.

## Remaining work and preserved history

Active NSE holds: **none in the pinned 119-group NSE review**. The nine historical IPOs behind the earlier excluded debt/migration events and **Fabino Life Sciences** are published and verified live. Keep all positively classified 2026 debt/migration/rights events out of the new-IPO queue.

The BSE historical coverage source is now characterized. The exact next P1 batch is the **four unmatched 2020 BSE issuers**: Likhitha Infrastructure Limited (543240), Secmark Consultancy Limited (543234), SM Auto Stamping Limited (543065), and Shine Fashions (India) Limited (543244). Review them issuer-by-issuer with official evidence; do not bulk-import the remaining unmatched rows. **BSE parser v1.5 is 236/236 parsed; do not replay its completed cursor.** After 2020, continue unmatched BSE coverage in bounded year/source-family batches. SEBI historical pagination, NSE-series coverage and broader DRHP source completeness remain separate gaps.

The old canonical review and seven-case hold files dated September 25 are preserved as historical snapshots. Use the linked **September 26 current-review state**, not their stale next-task fields, for new work.

The immediately preceding README and project-status versions are archived byte-for-byte as `docs/archive/README-before-bse-audit-reconciliation-2026-09-26.md` and `docs/archive/PROJECT_STATUS-before-bse-audit-reconciliation-2026-09-26.md`. Earlier manifests, archives, evidence and receipts remain intact. Actions artifacts expire after 14 days; durable receipts retain source hashes, URLs, dates, document identities and locators.

No minimum-investment expansion, billing/accounts/ads, spending or access-policy changes were introduced.
