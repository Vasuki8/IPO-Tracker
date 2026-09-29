# Project status and handoff

Updated **2026-09-28 (UTC)** after completing the retained four-issuer prospectus field review. Active priority remains **P1 issuer identity and data correctness**. This task adds a source-bound review and read-only validation, not an IPO import. It approves **zero new public fields** and changes **zero public IPO records**.

## Stale PR retirement review — 2026-09-28

**PR #196 and PR #246 are closed unmerged.** The [seven-file semantic review](verification/stale-pr-review-2026-09-28.md) and [comparison receipt](verification/stale-pr-review-2026-09-28.json) are pinned to main `9a544996475e84788a7cc08fc6e49d9acd8b52bb`. #196 is superseded by #198/#199: its four issuer facts already exist, while main retains later batch22 evidence. The current importer recognizes main's four entries and holds all four old-hash entries without overwriting anything. #246 is obsolete temporary DRHP collection/materialization scaffolding; #248–#256 already delivered the feature, identity resolution, history retention, lifecycle filtering and source corrections. No validated production delta needed porting, and no stale workflow or import was run. Branch history remains retained.

Targeted BSE/DRHP regression tests, the real isolated BSE publication rehearsal, current progress guards and build/schema checks passed. All **1,375** IPO records stayed unchanged; the full BSE rehearsal added zero records and was idempotent. This documentation-only retirement does not constitute a new public-data release or a fresh live-site/source verification. The next P1 task and PR #334's source-review boundaries below remain unchanged; do not replay either retired PR.

## Exact next bounded task

Obtain and retain approved original **actual-listing evidence** for **Indian Renewable Energy Development Agency Limited (544026)**, **Motisons Jewellers Limited (544053)**, **RBZ Jewellers Limited (544060)** and **SHELTER PHARMA LIMITED (543963)**. Their prospectus terms are now reviewed in the [field review](../data/discovery/bse-2023-irms-field-review-2026-09-28.json); do not redo source discovery or overwrite the original collection receipts. The unresolved dependency is an original exchange listing notice or equivalent authoritative actual-listing disclosure, including issuer identity, document date and original bytes. Prospectus proposals, discovery dates and third-party reports do not establish actual listing for publication.

Then reconcile existing names, aliases and exchange identities across all latest recovery years, prepare a separate reviewed bounded import, verify exact served public projections and only then close the queue rows. Do not make final-prospectus completeness a condition of inclusion, infer minimum application amounts, or promote provisional amounts to realised proceeds. No current identity check is a permanent collision clearance.

The [2023 progress ledger](../data/discovery/bse-2023-review-progress-2026-09-28.json) stays **8 reviewed/published + 22 awaiting review**, from the immutable 30-candidate queue. No candidate is closed by this field review. The original queue SHA-256 remains `975d244fc1a6166aebbb9a4c4da64b60fe3a85e1b3c1d84b9eca3ab4b2812cb4`, with source clock **2026-09-26T16:40:34.440Z**. The original 2022 queue remains **14 reviewed/published + 2 existing-recovery alias + 0 awaiting review**; 2021 is also complete. These are bounded queue counts, not Indian IPO-universe completeness.

## Completed: historical prospectus field review

The review records **32 field dispositions**: **24 verified stated terms, 3 provisional amounts, 1 not-applicable fixed-price band and 4 missing actual listing dates**. “Verified stated term” is an internal review label, not a new public schema enum, proof of an actual event or permission to publish. Sixteen primary physical PDF pages were visually checked from retained original bytes, with text extraction and no OCR. The review binds each field to its PDF response hash, physical page, locator, original unit, reporting period and qualification.

| Candidate | Stated band / issue price (INR) | Stated 2023 trading lot | Retail minimum bid | Stated public offer schedule | Total stated issue/offer amount |
| --- | --- | ---: | ---: | --- | --- |
| IREDA | 30–32 / 32 | 1 | 460 | 21–23 Nov-2023 | INR 21,502.12 million; provisional |
| Motisons Jewellers | 52–55 / 55 | 1 | 250 | 18–20 Dec-2023 | INR 15,109.05 lakh; provisional |
| RBZ Jewellers | 95–100 / 100 | 1 | 150 | 19–21 Dec-2023 | INR 10,000 lakh; provisional |
| Shelter Pharma | Fixed price / 42 | 3,000 | 3,000 | 10–14 Aug-2023 | INR 1,602.72 lakh; exact stated fixed-price total |

All four actual listing dates and unsupported exchange identifiers/board values remain null in this review. Trading lots describe the 2023 offer documents, not a new current-market observation. Offer dates are the stated public schedule, not independently observed events. Anchor dates are separately retained and never substituted for public opening. Shelter has no book-building price band; that internal not-applicable disposition is not converted to a made-up range or public schema change.

### Amount and evidence qualifications

IREDA's cover total includes fresh issue and OFS and is subject to finalisation of Basis of Allotment. It is neither solely issuer proceeds nor verified realised proceeds. Motisons' front matter describes an up-to public issue after the pre-IPO placement reduction; the separate INR 3,300 lakh placement must not be added to the public-issue amount or confused with net proceeds. RBZ's physical page 11 explicitly qualifies the amount as subject to finalisation of Basis of Allotment even though the cover omits that footnote. All three remain provisional.

Shelter's cover explicitly states the total in lakh. A front-matter repetition omits the unit, so it is not used alone for normalization. The total includes the INR 80.64 lakh market-maker reservation; the INR 1,522.08 lakh net public issue is a different scope. The exact stated total is not proof of realised proceeds. No share-count-times-price arithmetic is used to create amounts.

Motisons' attachment path says `may-2024`, but the retained cover date is **20-Dec-2023**. Keep document dates, landing-page dates, unknown PDF publication dates, collection times and review time separate. The original source plan's unreviewed document-date nulls and source receipt's incomplete-release flags are not rewritten by this later review.

## Retained sources and verification

This task reuses PR #334's [source-set receipt](../data/evidence/bse-2023-irms-source-receipt-2026-09-28.json): eight unique responses / **39,977,695 bytes** across source run **36431201278**, attempts 1 and 2. Artifacts **10973861758** and **10974237168** remain separately retained, including both partial failures. Motisons PDF is selected from attempt 2; the other seven responses from attempt 1. Both ZIP hashes and original response hashes/lengths were rechecked, and both original single-attempt validators still correctly report **7/8, partial**. This is not a fresh source collection or a relabeling of either failed source job.

Raw archives expire **12-Oct-2026 UTC**. Hashes and selection receipts are durable; original bytes are not permanently archived. Reuse the retained originals before expiry, or record a genuine new collection and compare hashes afterward.

`scripts/check-bse-2023-irms-field-review.mjs` validates source/queue/plan bindings, original attempt provenance, document clocks, units, scope, status, page bounds, missing listing evidence and the exact reviewed projection. The projection pin is an explicit human-review integrity boundary, **not an automatic semantic PDF parser**. A new substantive review must explicitly update it. The checker has no apply mode and cannot publish or close a queue row.

The new test entry point has **45 cases**, including mutation rejection, all four issuers' field-evidence binding, cross-year identity matches and refusal of `--apply`. The validator and offline workflow guards were observed failing before implementation and passing afterward. Current identity checks inspect exact ids, canonical legal names and BSE codes across all recovery years; matching records warn without authorizing an import. The local baseline inspected 1,375 records across 2020–2026 and found no such matches, not a full alias clearance.

Baseline verification passed **89 existing non-browser test entry points**. Final full-suite results, PR/merge status and any deployment checks are recorded in the [release closeout](verification/bse-2023-irms-field-release-2026-09-28.json). Local verification used the hash-checked deployed PR #334 snapshot plus exact fetched workflow blobs; it is not falsely described as a Git clone of latest main. Final PR CI must check the actual merge tree against current main. Browser `test-ui.mjs` is not part of this backend review; no browser or new live-field verification is claimed merely from unit tests.

Run `node scripts/test-bse-2023-irms-field-review.mjs`, `node scripts/check-bse-2023-irms-field-review.mjs`, `node scripts/test-bse-2023-irms-evidence.mjs`, `node scripts/test-bse-2023-irms-handoff.mjs`, `node scripts/check-bse-2023-progress.mjs`, `node scripts/check-bse-2022-disposition.mjs`, `node scripts/check-retained-bse-snapshot.mjs`, `node scripts/build-published-data.mjs --check`, `node scripts/validate-data.mjs` and all non-browser test entry points before a release. Original attempts can be revalidated with the existing collector's `--validate-dir=/absolute/path/to/one-attempt`; never merge original attempt directories.

## History and preserved boundaries

The previous canonical handoff is archived **byte-for-byte** in [the source-preparation archive](PROJECT_STATUS_ARCHIVE_THROUGH_IRMS_SOURCES_2026-09-28.md), original Git blob **68ab0beb4e498d919f0b39467e43b1fe7a41d353**. Its older next-task wording is historical. PR #334 merge **9e8e9341f159dddbca2b668a5848a2561654c14e** and closeout **4459d099812cce4a5eedd093deb8f92ab499513e** remain the original source-collection release, not this field review's publication authority.

The last public-data release remains PR #332. Preserve Valiant's conflicting amount and missing minimum bid, the other PR #332 provisional amounts, Hariom/FiveStar conflicts, Rainbow/FiveStar aliases, CAMS/Protean cross-year guards and all original source/correction history. Do not replay completed 2020–2022 releases, prior 2023 releases, reviewed NSE batches or parser-v1.5's completed 236/236 cursor. The 920-row audit and old 215-candidate snapshot total are unchanged.

No public data, recovery, queue/progress snapshot, UI, public schema, collection schedule or publication source allowlist is modified by this field review. Preserve the light-theme [UI handoff](UI_DESIGN_HANDOFF.md), [detail-navigation handoff](UI_DETAIL_NAVIGATION_HANDOFF.md), lifecycle-aware Pre-IPO history and partial-coverage labels. The active application term remains **Lot Size only**, with verified market lot first and verified minimum bid as fallback, while retaining separate raw fields.

Overall universe and field coverage remain incomplete. Continue P1/source repairs and **do not expand P5/performance while P4 is blocked**. Preserve static hosting and commercial data-rights constraints; no new spending, contracts, accounts, billing, analytics, ads, infrastructure or material access changes without approval. Follow [DEVELOPMENT_PROCESS.md](DEVELOPMENT_PROCESS.md).
