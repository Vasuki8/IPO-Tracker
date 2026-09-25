# Project status and handoff

The separate IPO detail-page UI and future source-backed business/financial/risk-data requirements remain documented in [UI_DETAIL_NAVIGATION_HANDOFF.md](UI_DETAIL_NAVIGATION_HANDOFF.md). This is the active P1 data workstream handoff, not a UI release.

Updated: **2026-09-25**, after actual Pages verification `36172343065`.

## Current priority and release state

Continue **P1 issuer identity and IPO-universe coverage** under [DEVELOPMENT_PROCESS.md](DEVELOPMENT_PROCESS.md). The application-term requirement is **Lot Size only**. Keep market lot and minimum bid quantity separate; do not estimate minimum investment/application amounts.

**NSE universe batch5 is VERIFIED LIVE. Do not repeat its review or import.** The next coherent task is the pinned **15-candidate batch6 queue, MVELECTRO through CREDENT**, after reconciliation against current main and actual Pages.

## Completed batch5 — PR #242

All **15** pinned TEJA-through-JNPR candidates independently established initial public equity IPO type and consistent legal name, symbol, ISIN, board, offer dates and listing identity. **No new holds or exclusions.** Approved symbols:

**TEJA, VMOBILE, KNACK, ICELCO, KUSUMGAR, HAPPY, LASERPOWER, SBIFUNDS, CMLL, METALIC, INDOMIM, LCL, PROPSHOP, MANIPALHOS, JNPR**.

Retained **89 explicit source-backed facts**: 15 listing dates, 30 offer dates, 15 final prices, 14 price bands, 6 market lots and 9 minimum bid quantities. **TEJA is fixed price at INR 220, with market lot 600; its price band remains null rather than an invented range.** No issue size or minimum application amount was inferred.

No production parser, UI or access-policy change was needed. The final PR contained the reviewed manifest/review, regression tests, rehearsal receipt and selection of the batch5 post-publication verifier. Temporary collector/materializer files were removed before merge.

Evidence: [review](../data/discovery/nse-universe-batch5-review-2026-09-25.json), [manifest](../data/verified-nse-ipos/2026-09-25-batch5.json), [rehearsal receipt](verification/nse-universe-batch5-rehearsal-2026-09-25.json), [live receipt](verification/nse-universe-batch5-live-publication-2026-09-25.json).

### Source provenance

Read-only source run **36170193878**, artifact **10880128428**, SHA-256 `760db5e15a4ec505738f0b1a36f97026d9f210648c3e63720bb12fb575bdea49`; exact source revision `5e6a434b7fdbb1245116c78dee8f44534937fa02`. All **17 original response hashes/byte counts** passed: 15 issuer-specific NSE responses, the past-issues response, and actual Pages baseline. Original Actions artifacts expire after 14 days; durable literal projections, document identities, timestamps, response hashes and evidence locators remain in the repository.

Materialization run **36170848441**, artifact **10879669578**, SHA-256 `21960fb4bcf125696c0c281ec10986cc8d6795484be62f9ce806689a8ce6e880`; reviewed commit `abdc38eeb6a8bc5cf76c1947b9cbd64a0666d183`. Materialized manifest/review/test bytes matched the locally reviewed and tested files.

### Tests and merge

Local and Actions publication rehearsal: **1,269 -> 1,284**, exactly 15 additions, no removals, all 1,269 prior records preserved, idempotent second application. All five reviewed NSE batches passed: **66 issuers / 394 facts**.

Batch5 tests reject **14 malformed-source mutations** and **4 cross-year identity collisions**; cover fixed-price/null semantics, lot-versus-bid distinctions, corrupted post-import values, read-only inputs and both pre- and post-publication execution. The tests reconstruct a prior snapshot, preventing recurrence of batch4's stale pre-publication assertion fixed in PR #241.

PR-head `ebef9225724547091a55b9b5a98a11b711ace1a4`: full data contract **36171131310** and reviewed-BSE compatibility **36171131333**, both successful. PR #242 merged as **`091a9f324dc7deded395b5cc15bdd24334d6c3d6`**. Full data contract passed again on merged main in **36171237331**. The exact post-publication source snapshot was retested locally and passed; every source-archive file remained byte-identical after the tests.

## Actual source-backed publication and live verification

Normal source sync **36171237358**: **success**. Data commit: **`359ea237cda83fed91d7724ddd4ee658efb96ae8`**. Operator commit: **`f682dd835395620657da064d81308ca3daf30dd0`**; recorded operator health **healthy**. All measured collection/build/validation/publication stages succeeded. Optional NSE all-fields processed 89/89 candidates with 89 successful responses, no fetch errors and no budget deferrals. The source-backed pipeline, not a hand-edited public dataset, performed publication.

Actual Pages verifier **36172343065**: **success**. Artifact **10880436844**, SHA-256 `f768a8602b4b271636d58920956d93d5a1c2677d3d0ab76fda9b78f8fb29e823`; exact source revision `f682dd835395620657da064d81308ca3daf30dd0`. Dynamic Pages deployment **36172338697** for that revision succeeded by **2026-09-25T18:16:55Z**. The served bytes were independently checked against all five reviewed manifests and their retained recovery evidence.

| Verified result | Value |
| --- | ---: |
| Actual Pages records | **1,284** |
| Batch5 issuers / facts | **15 / 89**, all matching |
| All five reviewed batches | **66 issuers / 394 facts**, all matching |
| Unknown / invalid statuses | **0** |
| Missing status evidence | **0** |
| Added / removed records | **15 / 0** |
| Existing records unchanged | **1,266** |
| Existing records changed by normal sync | **3** |

Status distribution: **listed 1,263 / open 16 / closed 3 / upcoming 2**.

Actual fetch: **2026-09-25T18:16:59.688Z**. Verifier check: **2026-09-25T18:16:59.733Z**. Dataset `generated_at`: **2026-09-25T18:15:06.172Z**. Snapshot SHA-256: **`a542ba9d96d621dff867f7310c99d5c74f2864898501c46b214d94db112f1e91`**; bytes **6,944,565**. These are separate clocks; do not treat source/evidence dates as publication time.

### Exact delta and unrelated updates

Baseline: actual Pages fetched **2026-09-25T17:57:20.563Z**, **1,269 records**, hash `30bf80d968e3f13fe92a46b7d19a0f8f5260f93ecb31c5707eb4ca640fcbeff1`. This includes historical-PDF commit `31dfe3906104a9e7ec9d7a44d551a10f4766dddf` after the earlier batch4 receipt. Do not compare this release to the older batch4 hash and misattribute intervening updates to batch5.

Exactly the 15 approved batch5 identities were added; no removed or unexpected new identity. Three existing records received normal SEBI document additions plus collection metadata only: **Western Carriers (India) Limited**, **Marco Cables and Conductors Limited**, and **Yatra Online Limited**. No prior displayed IPO value or status changed. The receipt retains exact field-level changes, added document URLs, and before/after record hashes.

Three newly reviewed records received optional issue-size enrichment through the normal source sync, separate from the 89 reviewed manifest facts:
- **Kusumgar Limited**: `issue_size_inr=6500000000`, explicit NSE issuer response.
- **Juniper Green Energy Limited**: `issue_size_inr=18000000000`, explicit NSE issuer response.
- **Manipal Health Enterprises Limited**: `issue_size_inr=92752160000`, SEBI Prospectus extraction, source value `₹92,752.16 MILLION`, PDF page 3.

The two NSE amounts were independently corroborated against pinned original issuer responses. Public/recovery agreement and the source locator were checked for Manipal; the external PDF was not independently reopened in this session. Keep these ordinary-sync enrichments distinct from the manually reviewed manifest scope.

## Next P1 task — batch6

Review [the pinned queue](../data/discovery/ipo-universe-review-2026-09-25-batch6.json): **15 candidate groups, MVELECTRO through CREDENT**. Do not auto-import.

There are **44 remaining candidate issuer groups** in canonical audit **36095239145** after the first 75 groups were reviewed, **not 44 confirmed IPOs**. Group by canonical issuer; do not count repeated past-source observations as separate issuers. The original audit had 119 eligible issuer groups; ADANIENPP1's repeated observations do not create extra queue entries. Queue selection was revalidated against the hashed original audit, all prior 75 candidates and the original past-source rows.

**ANNAPURNA** and **SWARAJ** require explicit prior-offer/migration/repeat-security investigation. Their canonical rows combine **2022 offer dates with 2026 listing dates** and inconsistent historical price-range/final-price observations. These are review signals only, not completed classifications. Retain separate official identity and offering-type evidence before any proposed IPO import.

Reconcile all candidates against latest main and actual served data; establish initial equity IPO vs FPO/rights/migration/partly-paid/repeat/debt; preserve aliases, nulls and conflicts. Rehearse preservation/idempotency, run final-head CI, publish through retained recovery and verify actual Pages before completion.

## Prior holds, exclusions and wider gaps

Unresolved: **AMIRCHAND, ADANIENPP1, Fabino Life Sciences, GICL, SILGOPP, VITAL, KOTYARK**. Resolved non-IPO exclusions **10MWL29**, **QMSMEDI**, **12VPT28A** must not re-enter the new equity-IPO queue. Prior reasons/evidence remain in the archived handoffs and review manifests.

BSE issue-summary, SEBI historical pagination and unresolved NSE series still limit coverage. Do not claim complete IPO-universe coverage. **BSE parser v1.5 remains 236/236 parsed; do not replay that cursor.**

## Preserved handoff and scope

The preceding README/status are archived byte-for-byte as [README-before-nse-batch5-live-verification.md](archive/README-before-nse-batch5-live-verification.md) and [PROJECT_STATUS-before-nse-batch5-live-verification.md](archive/PROJECT_STATUS-before-nse-batch5-live-verification.md). Earlier archives/receipts are unchanged. No UI, minimum-investment expansion, billing, accounts, ads, spending or permission change belongs to this continuation.
