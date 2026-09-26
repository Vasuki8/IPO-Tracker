# Project status and handoff

Updated **2026-09-26 (UTC)** after completing the Abakkus/Pre-IPO source-coverage repair. The active backend priority remains **P1 issuer identity and universe correctness** under [DEVELOPMENT_PROCESS.md](DEVELOPMENT_PROCESS.md). The Pre-IPO surface is lifecycle-aware and now discovers draft issuers from the SEBI draft index plus the configured Axis Capital official BRLM fallback. Coverage is still explicitly partial. Other UI/research-depth work remains in [UI_DETAIL_NAVIGATION_HANDOFF.md](UI_DETAIL_NAVIGATION_HANDOFF.md).

## Release complete — do not replay

**PR #248 and PR #249 are merged.** AMIRCHAND and LEAP are resolved and published; the DRHP directory and its history-preserving refresh are verified on actual Pages. Do not replay approved imports from batches 1–9.

The current disposition is [nse-universe-current-review-2026-09-26.json](../data/discovery/nse-universe-current-review-2026-09-26.json): **105 approved IPOs + five debt-event exclusions + seven migration exclusions + two rights-issue security exclusions = 119 pinned groups**. **Zero unresolved and zero unreviewed groups remain in that pinned audit.** This is still **not full Indian IPO-universe completeness**.

**Exact next bounded backend task: materialize and safely import the nine now-verified historical equity IPOs** — MWL, QMSMEDI, VIVIANA, ANNAPURNA, SWARAJ, VIESL, AVPINFRA, DOLLEX and DCCL. Retain original official source bytes/SHA-256 hashes and page/locator evidence, then use a reviewed recovery importer with collision/idempotency tests. Keep all excluded 2026 debt/migration events excluded.

## Historical IPO coverage for nine excluded-event issuers — verified, import pending

The historical-equity coverage gap behind the nine earlier 2026 debt/migration exclusions is now resolved at the evidence-review layer. [The retained review](../data/discovery/excluded-event-issuer-historical-ipo-review-2026-09-26.json) verifies **9/9 historical equity IPOs** from official NSE/issuer prospectuses, listing releases, iXBRL identity filings and other official issuer/exchange disclosures.

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

**Import remains intentionally pending.** The existing reviewed-NSE importer requires retained NSE API response bytes/hashes and exact API projections. This review used official prospectuses/issuer filings/listing releases, but the original document bytes were not materialized in this connector run. Do not weaken `scripts/apply-reviewed-nse-ipos.mjs` and do not hand-edit `data/ipos.json`.

No public or recovery IPO record changed, and **zero excluded 2026 events were reintroduced**. The next task is to materialize decisive official source bytes/hashes and implement or reuse a reviewed historical-offer recovery path with identity-collision, preservation and idempotency tests.

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

PR #249 final-head CI passed: full data contract **36212457450**, interface **36212457353**, reviewed-BSE compatibility **36212457388**. Merged-main full contract **36213264978** also passed. Local retained-source parser, integrity, UI-contract, nine-batch IPO regression, publication-rehearsal, build and schema checks passed.

Exact fetched DRHP HTML/CSS/JavaScript and JSON were rendered offline in Chromium at **320, 375 and 1440 pixels**. Search, no-results, invalid-data rejection, error/retry, failed-refresh/last-good-list messaging and mobile navigation passed; no page overflow or JavaScript page errors. Local browser networking was unavailable; these are offline rendering checks, while actual remote byte verification was performed by the successful Actions workflow.

Durable combined receipt: [drhp-identity-release-live-2026-09-26.json](verification/drhp-identity-release-live-2026-09-26.json). Original repair evidence: run **36211433801**, artifact **10896315080**, SHA-256 **73e0a80da65cbc52ed2ce4c5d4a9635e0306f4b2ea594298ff007a1bdc68615d**. The earlier temporary materializer failed to publish workflow edits with its runner token; the authorized connector completed those edits without changing access policy. No temporary materializer remains in the merged repair.

## Remaining work and preserved history

Active NSE holds: **none in the pinned 119-group NSE review**. Historical IPO existence is now verified for all nine earlier debt/migration-event issuers, but import is pending durable source-byte/hash retention and a reviewed recovery path. **Fabino Life Sciences** remains a separate BSE listing-year hold. Keep all positively classified 2026 debt/migration/rights events out of the new-IPO queue.

Broader BSE issue-summary, SEBI historical pagination and NSE-series gaps remain. **BSE parser v1.5 is 236/236 parsed; do not replay its completed cursor.** DRHP coverage expansion must address inconsistent pagination/unlabelled disclosures without treating an observed draft filing as a new approved IPO.

The old canonical review and seven-case hold files dated September 25 are preserved as historical snapshots. Use the linked **September 26 current-review state**, not their stale next-task fields, for new work.

The immediately preceding README and project-status versions are archived byte-for-byte as `docs/archive/README-before-historical-ipo-coverage-nine-2026-09-26.md` and `docs/archive/PROJECT_STATUS-before-historical-ipo-coverage-nine-2026-09-26.md`. Earlier manifests, archives, evidence and receipts remain intact. Actions artifacts expire after 14 days; the repository retains literal projections, URLs, dates, document identities, hashes and locators.

No minimum-investment expansion, billing/accounts/ads, spending or access-policy changes were introduced.
