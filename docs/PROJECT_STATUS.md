# Project status and release evidence

## Standing requirements

IPO Tracker is intended to become a public commercial product. Audience, pricing
and revenue model remain undecided. Preserve trust, accessible mobile research,
privacy, stable URLs and sustainable costs. Keep the light static architecture.
No new spending, contracts, outreach, tracking, billing or material access changes
without owner approval. Sponsorship must be identifiable and cannot affect facts
or research rankings. See [COMMERCIAL_READINESS.md](COMMERCIAL_READINESS.md).

Completed static terms require matching Final Prospectus field evidence. Active
provisional disclosures and official market observations must remain labelled.
Preserve source URLs, document identity, dates, units, nulls, separate source and
collection clocks, quarantines and correction history. P5/performance expansion
remain gated by P4. See [ROADMAP.md](ROADMAP.md) and [OPERATIONS.md](OPERATIONS.md).

## Current checkpoint — qualified offer amounts published and verified, 19 September 2026

Accepted data release: **`40a24ca1cc2e5310825aad36769ee3cad75fe9ae`**.
Support [PR #171](https://github.com/Vasuki8/IPO-Tracker/pull/171), head
`6bdcb9b72fbd0249a19ac68d9ddf865edb96c29a`, merged as
`4a8ff79a19df59faf49677931516312b366fa4ee`. Review-only publication was
`ec31caea26de73fb0a7e373247b22b5535524022`. The separate single-file request
[PR #172](https://github.com/Vasuki8/IPO-Tracker/pull/172), head
`1cbb313b8d1ded2e82859eecefb5a18cec36073a`, merged as
`90ce951c8d9a6e176f07d5d647e0e7057d4b9967`. Documentation closeout branch:
`docs-qualified-amount-recovery-closeout`; its PR/commit is identified by the
Git history containing this checkpoint.

Recovery freshly verified main `0a393cd4`, completed BSE #168–170, subsequent
scheduled core `20068a87`/filings `0a393cd4`, their successful deployment and
18 direct live files. Source commits `70a47cb0` and `6e2df0a4` were already pushed;
the amount implementation was initially uncommitted with no PR. It was preserved,
reviewed and tested. A subsequent pre-PR fetch found #171/#172 already completed
with exactly the same implementation, including the three recovered fixes below.
No duplicate implementation PR or publication request was created. The frozen
local checkpoint `4af01723` remains on `recover-qualified-offer-amounts`.
Repository and deployment evidence superseded the stale awaiting-release status.

Problem/users: IPO researchers need the issuer's conditional whole-offer amounts
without treating a price-band cap as a final price or proceeds. The three-issuer
source family is complete at **two supported pairs and one unresolved amount**:

| Issuer | At floor price, INR crore | At cap price, INR crore | Required qualification / validity |
| --- | --- | --- | --- |
| Axiom Gas | 47.9298 at INR 51/share | 50.7492 at INR 54/share | Up to 9,398,000 shares; subject to finalisation of Basis of Allotment; through 22 September IST |
| Varmora | Up to 687.047 at INR 140/share | Up to 708.021 at INR 148/share | Up to each disclosed monetary amount; final terms unknown; through 24 September IST |
| Pooja Logistics | Unknown | Unknown | Current inspected RHP/advertisement retains placeholders; amount gap remains |

The [immutable source review](reviews/2026-09-19-qualified-offer-amount-source-review.md)
is bound to `6e2df0a4d4c8b736d0c07d526b3b844eaecd0b49`. Original document/member
hashes were recomputed; the amount/qualification pages and Varmora signature/date
were visually checked. Bounded visual transcriptions are identified as manual.
Axiom's explicit price-band supersession and Varmora's separate signature
16 September/publication 17 September dates survive. Pooja's recovered archives
and earlier failures remain distinct. Only explicit issuer amounts and unit
conversion are accepted; no multiplication-derived total is supplied.

`issueAmountScenarios` remains separate from unknown canonical `issueSizeCr`.
Issuer document URLs, identity/hash, dates, physical page/row, units and review
are separate from original NSE evidence. Observation times remain unknown;
collection/review clocks do not refresh a source observation. Directory, profile,
quick view, comparison and CSV keep both amounts and qualifications. Holds,
conflicts, invalidity and IST expiry withhold the pair and restore missing-field
work. No minimum quantity, application amount, canonical symbol or composition
expansion is included. Earlier BSE/Vivekanand gaps and all held evidence remain.

The final recovery fixes also propagate ordinary canonical price/total review
states to dependent amounts; keep health attribution accurate for surviving NSE
terms when a supplement is invalid; and reject identical wrong scalar promotion
on directory and profile. Each has a focused regression and independent code review.

The accepted diff changes exactly **Axiom/Varmora `activeOfferTerms` and appended
`dataCorrections`**. Original receipts remain in correction history. All **1,404
unselected records**, **441 proposals**, all holds and all **1,557 validation and
expanded-queue source reviews** are preserved exactly. Source-health clocks and
performance values are unchanged. No availability resolution was added or removed.
See the [measured release receipt](releases/2026-09-19-qualified-offer-recovery.json).
The cohort's active amount gaps fell **3 to 1**; higher-priority P4 records fell
**69 to 67**, solely through provisional coverage, not final-amount verification.

Current P4: **408 actionable + 67 higher priority; 1,553 blocking / 1,557 total
reviews; zero errors / zero unmapped; 1,406 canonical records**. Final Prospectus
revalidation is unchanged at **321 records / 1,174 fields**. P5 remains
`waiting_for_p4` with **914 records**; performance expansion remains disabled.

Validation: **1,392 Python tests**, **43 standard-library release tests**,
**39 Node tests**, including **19 amount and 8 receipt-health tests**, pass.
Strict validation, bounded preparation/accepted scope checks and all **1,406
profile contracts** pass. Support PR validation 35448476902, source preview
35448476877, hold evidence 35448476880, release candidate 35448476898 and browser
35448476884 passed all six jobs. Main validation 35448752007/browser 35448752008
and request validation 35448832878 passed. CI browser acceptance covers 25 smoke
checks, existing families and both amount issuers at 1440/375/320px, CSV,
comparison and expiry. Desktop/320px screenshots were visually inspected;
[the browser receipt](releases/2026-09-19-qualified-offer-recovery-browser.json)
records actual CI evidence after local Chromium installation failed.

Reviewed publisher **35448941571** succeeded, with collector **105912618954** and
publisher **105912760095**. Accepted Pages **35449044417** and public verifier
**35449087717** passed. [Twenty direct verifier files](releases/2026-09-19-qualified-offer-recovery-live.json)
and [eleven additional exact-byte checks](releases/2026-09-19-qualified-offer-recovery-direct-live.json)
match `40a24ca1`, including both amounts, proofs, P4 reports and preserved Pooja/BSE
profiles. Scheduled run 35448787952 was correctly rejected by the stale-source
policy guard after policy changed; no protection was bypassed or old artifact
forced through. The separate reviewed publication completed successfully.

No implementation, review or data-release acceptance remains for this bounded
family. Commercial source/redistribution rights, permitted hosting, operator and
jurisdictions, audience, pricing and revenue model remain unresolved. No spending,
outreach, contracts, tracking, accounts, billing, access or infrastructure changes.
Open #94/#98/#99 and drafts #104/#105 remain preserved.

**Exact next task:** diagnose the promoter/subtotal/page-locator family against
multiple matching Final Prospectuses, starting with held Vinod Texworld. Establish
promoters versus promoter-group scope and actual source-row pages before proposing
any parser or value replacement. Retain Vinod's 93.11 and its hold/history; do not
automatically replace it with 93.10. Keep Pooja's amount and other unsupported
fields unresolved. Do not start P5 or performance expansion.

## Previous checkpoint — reviewed BSE active terms released, 19 September 2026

Verified data-release main: **`599798ff18e92e8ad9fc0da0f99a98f6fb5ce1ad`**.
Support [PR #168](https://github.com/Vasuki8/IPO-Tracker/pull/168) merged as
`1e2e08e4e0f1f144f2220d17526fbe7fb0351e6d`; implementation commit
`b16661c8aa7c57600e49d3dd8a6c22a4fd6b954e`. Review-only publication was
`4d2d558b318d7982d17e116dc92341f774d8b4d9`. The separate single-file request,
[PR #169](https://github.com/Vasuki8/IPO-Tracker/pull/169), merged as
`974f2d3b4cd872495dfb8d229366c2fa44997981` from `a6bb21315238121d5df97aed08db932ffaa55480`.
Documentation closeout branch: `docs-bse-active-offer-closeout`,
[PR #170](https://github.com/Vasuki8/IPO-Tracker/pull/170). Its commit and check
evidence are identified by the linked PR and Git history containing this checkpoint.

Recovery began at `5e8642f3` (#167). After the connection interruption, a fresh
fetch found independently scheduled core publication
`2d07c3b63a631a3560f75996180fe0fb7979f665`, verified by Pages 35425762822 and
verifier 35425782777. Its two added issuers, Elevate Campuses and Unitec Fibres,
were preserved: inventory rose from 1,404 to **1,406**, and higher-priority P4
records from 67 to **69**. The interrupted source commit existed on GitHub;
the implementation tree/branch/PR did not. Upload resumed through the connected
GitHub API, verifying every blob and the complete tree against local content.
Local preupload commits remain on `local-bse-preupload-20260919`. No earlier
commercial, operational, universe or NSE receipt work was repeated.

Problem/users: IPO researchers needed evidence for the five newly admitted BSE
upcoming SME offers. The bounded current-index/detail family now supplies:

| Issuer | Provisional band, INR/share | Market lot, shares | Minimum bid quantity, shares | Valid through close date, IST |
|---|---:|---:|---:|---|
| FX Multitech | 110–116 | 1,200 | 2,400 | 23 September 2026 |
| Robokidz Eduventures | 100–106 | 1,200 | 2,400 | 23 September 2026 |
| Himalaya Nutravedics India | 100–106 | 1,200 | 2,400 | 24 September 2026 |
| S. K. Offset | 119–125 | 1,000 | 2,000 | 25 September 2026 |

The [source review](reviews/2026-09-19-bse-active-offer-source-review.md) is bound
to immutable `f16287080613b57b000a227fca9d90eab1b72b25`. It retains five exact
detail responses, the index, source URLs/hashes, identity, table/row locators,
units and the currency asset. The FX and Robokidz official advertisement pages
were rendered and inspected independently. Collection, review and unknown source
observation clocks remain distinct. Source identity symbols do not fill canonical
symbols. Receipt replay, existing holds, same-offer conflicts and IST expiry
control the same projected values across directory, profiles, quick views,
comparisons and CSV. Expired or invalid receipts restore the unresolved gaps.

Vivekanand's detail table remains empty. Its latest retained index observation is
35–37; the earlier 32–37 observation remains in committed historical evidence.
No receipt was approved for it. BSE detail share counts do not establish whole
issue totals. **Bid lots, canonical symbols, total amounts, composition and
minimum application amounts remain unknown** in this batch; none was inferred.
The Himalaya/S. K. advertisement-link failures remain documented.

The accepted transaction changed exactly four records, limited to
`activeOfferTerms`, source/correction history and validation metadata. All **1,402
unselected records**, all **441 pending proposals**, all holds and all **1,557
validation/expanded-queue source reviews** are preserved exactly. No review was
removed. Performance values are unchanged; its regenerated summary changed only
its generation timestamp. The existing core source checks were not refreshed by
this reviewed publication. See the [release receipt](releases/2026-09-19-bse-active-offer-terms.json).

The five-offer core gaps fell **25 → 21**, with eight additional separately
labelled quantity values. P4 remains **408 actionable + 69 higher priority;
1,553 blocking / 1,557 total reviews; zero errors / zero unmapped**. Final
Prospectus revalidation remains **321 records / 1,174 fields**. P5's 914 records
remain `waiting_for_p4`; neither P5 nor performance expansion was enabled.

Validation: **1,373 Python tests pass** under uv/Python 3.12, including **18 BSE
family tests**; **43 release tests also pass with only the standard library**;
**38 Node tests pass**. Strict validation and all **1,406 directory/profile pairs**
pass. All five support PR checks passed: validation 35427787091, source preview
35427787077, release candidate 35427787098 and browser 35427787080. Main validation
35428021138/browser 35428021140 and request validation 35428200100 also passed.
Browser coverage includes 25 existing smoke checks, prior reviewed families and
all four BSE issuers at 1440/375/320px, exports, comparisons, unknown clocks,
separate quantities, the rejected fifth issuer and expiry. Desktop/320px
screenshots were visually inspected. The local Chromium download failed; the
[successful CI browser receipt](releases/2026-09-19-bse-active-offer-browser.json)
records actual browser acceptance.

Reviewed publisher **35428300106** succeeded (collector 105858053604, publisher
105858167409), skipping source collection and residual repair. Accepted Pages
**35428372558** and deployed verifier **35428395090** passed. The
[22-file live verification](releases/2026-09-19-bse-active-offer-live.json) and
[nine additional exact-byte checks](releases/2026-09-19-bse-active-offer-direct-live.json)
match `599798ff`, including all four accepted profiles, the unresolved Vivekanand
profile, shared scripts, summary and P4 gate. Initial support verifier 35428037274
caught the old Varmora summary before regeneration; review publication `4d2d558b`
resolved it before the request merge. The support-output requirement is documented
in [OPERATIONS.md](OPERATIONS.md).

The [07:07Z operational checkpoint](releases/2026-09-19-bse-active-offer-health.json)
has **zero overdue source checks/stages**, **6 failed + 1 partial + 26 successful
sources**, seven sources/four stages needing investigation, and seven provisional
offer receipts with unknown observations. The scheduled core run fixed the old
attempt-age gap; BSE primary/SME failures, SEBI register timeout and other source
failures remain. See the [bounded diagnosis](reviews/2026-09-19-core-schedule-diagnosis.md).

No implementation, source-review or data-release acceptance criteria remain for
this bounded batch. This is not P4 completion or commercial clearance. Commercial
source/redistribution permissions, operator/jurisdictions, permitted hosting,
audience, pricing and revenue model remain unresolved. No spending, outreach,
tracking, accounts, billing, access changes or infrastructure migration occurred.
Preserved open work: #94, #98, #99 and drafts #104/#105.

**Exact next task:** review the separate qualified NSE floor/cap total-amount
family for Axiom Gas, Varmora and Pooja Logistics. Preserve qualifications and
unsupported values; retain the BSE gaps, Vivekanand evidence and every hold.
Do not start P5 or performance expansion.

## Previous checkpoint — commercial publication-scope review released, 19 September 2026

Verified research-release main: **`3481d89a21e77ac1f302bdc9171dd8eb5b67ee4a`**,
merged in [PR #166](https://github.com/Vasuki8/IPO-Tracker/pull/166); research commit
`de09c162cae491ce2f0dae16f21349d9a14091aa`. Assessment main was
`1e86840856525db2ee2b436ed64f2b6e60374ee0` (scheduled filings update incorporated
from initial `4c5f1af5`), including completed operational #164–165 and universe
#162–163. Documentation closeout branch: `docs-commercial-publication-scope-closeout`;
[PR #167](https://github.com/Vasuki8/IPO-Tracker/pull/167) records the closeout;
its commit is identified by Git history containing this checkpoint.
Previous commercial #152–153 research was reused with original
check dates. The exact next publication-mapping task is implemented in the
[commercial audit](audits/commercial/2026-09-19-publication-scope/REPORT.md),
[field/surface map](audits/commercial/2026-09-19-publication-scope/exposure.json),
[current inventory](audits/commercial/2026-09-19-publication-scope/inventory.json)
and updated [commercial decision register](COMMERCIAL_READINESS.md).

The 13-issuer map covers nine canonical secondary subscription records (six IPO
Premium, three IPO Dhamaka), **56 public profile history rows**, **21 issuer-hosted
static proofs / 20 corresponding profile values**, and **34 of 441 unresolved
proposals**. Seven missing top-level subscription source URLs remain unknown.
Orkla/Sunshine proofs, held Sunshine financials, Injecto registrar references,
Lumino/Steamhouse secondary links, raw JSON/history and CSV scope are distinguished.
No source link is treated as field provenance or permission. Inventory is now
**61 hosts**, up from 58 through links inside retained NSE responses; eleven Python
package versions and notice hashes are unchanged.

New primary checks cover IPO Watch, IPO Central, Economic Times, Moneycontrol,
Business Standard and Mint. BSE's public Legal page exposes no documents;
disclaimer and product rights remain unresolved. Completed collector logs bind
Poppler/libpoppler134 24.02.0-1ubuntu9.9 and poppler-data 0.4.12-1 to matching Ubuntu
copyright notices; six action/tool top-level licenses were inspected. Chromium,
bundled/transitive notices and SVG provenance remain open. Existing NSE/SEBI,
issuer, core-secondary and hosting evidence was carried without claiming refresh.

Four customer hypotheses, proposed privacy-conscious measurements/retention, cost
categories and support/correction process are retained. **Commercial launch is
not cleared.** Owner must identify operator/jurisdictions and review owner; direct
professional assessment of interim collection/publication boundaries and permitted
hosting; and later validate audience/pricing. No contacts, spend, contracts,
accounts, tracking, ads or infrastructure changes. No public behavior change.

P4 is unchanged: **408 actionable + 67 higher priority; 1,553 blocking / 1,557 total
reviews; 0 errors / 0 unmapped; 1,404 canonical records**. P5/performance remain
gated. Canonical values, pending proposals and review state are outside this diff.
Seven focused audit tests and 38 Node public-quality/source-health tests pass.
Both audit JSON artifacts replay exactly; prior register bytes and protected
paths are unchanged; local Markdown links resolve. Strict validation passes
with 1,404 records, zero errors and 1,557 reviews. **All 1,354 Python tests pass**
in PR validation **35423499597**; main validation **35423605159** also passed,
including proposal reconciliation and generated public artifacts. Pages
**35423604707** and public verification **35423628525** passed.
[27 direct live checks](audits/commercial/2026-09-19-publication-scope/live-delivery.json)
matched the immutable research merge exactly, including the register/audit,
raw canonical/proposal/summary data and all 13 mapped profiles. The
[release receipt](audits/commercial/2026-09-19-publication-scope/release.json)
records the evidence before documentation closeout. No release acceptance
criteria remain for this bounded research milestone; no commercial clearance
or P4 blocker reduction is claimed.
Preserved open work: #94, #98, #99 and drafts #104/#105.

**Exact next commercial task:** owner-directed professional review of the completed
13-issuer packet and interim publication policy. Independent next research cohort:
map broker/lead-manager/small-news retained material, starting with
`www.ipoplatform.com`, `www.equentis.com`, `www.idbidirect.in`, `www.plindia.com` and
`ipobarta.ai`, then inspect applicable public terms. BSE agreement recovery remains
blocked on accessible applicable terms or separately authorized outreach. Do not
repeat the completed packet unless its bound inputs change.

## Previous checkpoint — operational receipt visibility released, 19 September 2026

Verified release main: **`aa4d5b4709a5b62bb4be8fa5ba95800984df8be9`**, merged in
[PR #164](https://github.com/Vasuki8/IPO-Tracker/pull/164); implementation
`2b5f5d3c41fcec97f5a19d14663d3918a719fdbe`. Baseline was `5531a7cf`.
Documentation closeout branch: `docs-operational-offer-receipts-closeout`; its
commit is identified by Git history containing this checkpoint. The existing operational/source-clock
releases and universe #162–163 are complete; no earlier repair was repeated.
See the [operational audit](audits/operational-health/2026-09-19-offer-receipts/REPORT.md),
[bound report](audits/operational-health/2026-09-19-offer-receipts/report.json) and
[human view](audits/operational-health/2026-09-19-offer-receipts/operator-view.md).
The [release receipt](audits/operational-health/2026-09-19-offer-receipts/release.json)
records exact validation and deployment evidence.

The read-only operator report now includes the three retained reviewed provisional
offer receipts (Axiom Gas, Varmora, Pooja Logistics). Source-response replay and
public projection are reused, including holds, conflicting fields, invalid receipts,
future clocks and expiry at midnight in India. Observation, collection and review
remain separate; exact receipt acceptance/publication time stays unknown. No new
writer, source request, workflow, alert or public behavior was introduced.

Frozen at **04:30:00Z**: **5 failed sources, 1 partial failure, 27 recorded successes;
3 overdue source checks, 1 overdue core stage; 8 sources and 4 stages needing
investigation; 441 unresolved proposals**. Three subscription observations are
unknown and two are older than tolerance outside the Saturday monitoring window.
All three reviewed offer receipts are provisional with unknown source observations.
All proposal origin windows remain available, with exact proposal creation ages
unknown. Older successful bounded releases did not refresh the general core checks.

The accepted publisher metadata still points to **35417782070**, with job window
03:11:03–03:11:33Z. This predates later universe admission; it is not the latest
canonical edit or exact acceptance time. Later successful run **35418300903** had
no matching accepted run ID and skipped general source collection; no publication
failure or source freshness is inferred. Prior Pages **35420840497** and public
verification **35420860238** passed on baseline main.

Preservation checks confirm byte-identical canonical records, proposals, phase,
queue, holds and correction/review registries. P4 is unchanged: **408 actionable +
67 higher priority; 1,553 blocking / 1,557 total reviews; 0 errors / 0 unmapped**.
P5/performance remain gated. Commercial source permissions, permitted hosting,
customer segment, pricing and revenue model remain unresolved.

Tests: **40 focused health tests**, **38 Node tests**, strict validation pass.
**All 1,347 Python tests pass on Linux**, including the two local Windows
filesystem limitations. PR validation **35421655528** and main validation
**35421730603** passed, including report replay and generated public artifacts.
Pages **35421729869** and deployed verification **35421750703** passed. The
[live verifier](audits/operational-health/2026-09-19-offer-receipts/live-verification.json)
checked 21 public files; [eight additional exact-byte checks](audits/operational-health/2026-09-19-offer-receipts/live-report.json)
include the new report/operator view, summary, phase, source-health script and all
three receipt profiles. Public behavior remains unchanged. No implementation or
release acceptance criteria remain for this bounded milestone. No new source
correctness or blocker reduction is claimed.

Preserved open work: #94, #98, #99 and drafts #104/#105. No other branch was
modified. **Exact next operational task:** investigate the three overdue core
source checks using fresh run/job evidence; distinguish missing scheduled attempts,
collection failure and publication delay before any guarded retry. Retain BSE's
parse/timeout failures, source blocks and proposals. Do not start P5.

## Previous checkpoint — official-universe continuation released, 19 September 2026

Current verified data-release main: **`46e4bbaffa8df49480f352a2b9346c9661cd2864`**. Assessment baseline was
`be97b7966e647601141116447421af5c2d72634e`; implementation/data commit
`cf21055c02319bc49a2c87df7f4714b1866e9e82`, [PR #162](https://github.com/Vasuki8/IPO-Tracker/pull/162).
Documentation closeout branch: `docs-universe-continuation-closeout`; its commit
is identified by Git history containing this checkpoint. The [audit report](audits/official-universe/2026-09-19/REPORT.md),
[release receipt](audits/official-universe/2026-09-19/release.json),
[source/period/board/stage denominators](audits/official-universe/2026-09-19/audit.json)
and [live delivery receipt](audits/official-universe/2026-09-19/live-delivery.json)
are durable. Previous universe #145–148, operations/commercial releases and
active-term #158–161 work was recognized and preserved.

**Coverage remains incomplete.** These denominators are distinct observed
equity-public-issue candidates, not unique IPO companies or an all-India total:

| Source | Matched / observed candidates | Rate | Missing-name rows | Identity review / unverified |
|---|---:|---:|---:|---:|
| NSE | 173 / 174 | 99.43% | 1 | 0 / 0 |
| BSE | 588 / 1,848 | 31.82% | 1,250 | 10 / 0 |
| SEBI | 2,618 / 5,858 | 44.69% | 3,090 | 47 / 103 |

There are **2,148 unmatched normalized candidate names**, **227 tracker-only
records** and five retained approved alias bindings. Missing names still require
identity/initial-offering review; tracker-only does not mean invalid. Distinct
filing stages, addenda, repeated offers, board disagreements and source failures
remain visible. Draft filing alone never establishes an upcoming IPO.

**Completed historical work:** reused the original BSE archive (1,282 book-built,
558 fixed-price rows, plus eight current observations) and verified SEBI RHP/final/
Other Documents traversals without refetching them. Recovered the draft register
through **22 annual windows (2004–2025) + nine monthly windows (2026 through
19 September)**: **2,210 rows / 2,210 unique primary URLs**, including **45 newly
captured filing URLs**. The unfiltered 2,208/2,210 inconsistency and incomplete
2026 annual window remain retained, alongside the successful bounded windows.
The 2024 timeout recovered on one retry. Snapshot continuation binds the original
manifest hash and preserves original response bytes and collection dates.

**Admissions:** all 25 July/August BSE SME candidates were source-reviewed against
archive names/boards and exact detail-page Equity security, symbol and issue
period. They are admitted as **closed; listing unknown**, with every numerical
term/financial/subscription field null. Detail collection time uses the actual
detail receipt; observation remains unknown. Inventory **1,379 → 1,404**, stable
routes **1,404**. Existing 1,379 records/profiles, 1,557 reviews and 441 byte-identical
proposals remain unchanged. BSE matches rise 563 → 588. One additional missing-name
row becomes an explicit review, not an accepted match: June 23 Dhanwel Hybird Seeds
and August 19–21 Dhanwel Hybrid Seeds share DHANWEL but differ in offer dates.
No alias, cancellation, second issuer or offer merge was inferred.

**Tests:** Linux CI **35420466941** passed **1,339 Python tests** and strict validation,
with zero errors; 30 existing identity tests and seven new continuation/real-cohort
tests cover normalization, aliases, collisions, stages, boards, dates and source
hashes. All 38 Node tests passed. Five machine audit outputs reproduce byte-for-byte.
The 25 admitted profiles and directory searches passed **75 viewport checks** at
1440/375/320px, with no page errors, overflow or master-data fetch. Local full Python
had only the two known Windows filename/symlink limitations; Linux passes them.

**Published/live:** Pages **35420562278** and deployed verification **35420613423** succeeded.
The bounded delivery script checked every admitted profile's identity, null terms,
unknown observation clock and source link against exact deployed bytes, plus the
existing public/review artifacts. Live browser checks confirm the new issuer pages.
No remaining release acceptance criteria for this bounded continuation.

**Remaining gaps:** new NSE historical requests for 2025 Q2, 2024 Q4, 2020 Q1 and
2015 Q1 timed out; prior annual failures remain. NSE's Adani partly-paid/call-money
event classification remains unresolved. BSE has no independent archive total;
current fixed-price/main-host gaps remain. Pre-2004 draft, separate SME and
exhaustive cancellation coverage are not claimed. No unsupported exclusions,
financial backfill or silent resolution of prior source holds occurred.

**P4 remains blocked:** **408 actionable + 67 higher priority** (previously 387 +
63), **1,553 blocking / 1,557 total reviews**, four P5-only, zero errors/unmapped.
The increase exposes newly admitted incomplete records; it is not a blocker
reduction. P5 remains waiting (914). All existing numerical holds, including
SpectraA and Vinod, remain. Old PRs #94/#98/#99/#104/#105 and the unrelated
`fix-nse-detail-denominators` worktree are untouched. No active development PR from
this milestone remains after documentation closeout. Customer/pricing/revenue,
redistribution rights, hosting suitability and professional/privacy review remain
owner decisions; no spending, tracking, contracts or material permissions changed.

**Exact next universe task:** review the **18 BSE June 2026 unmatched candidates**
in [next-cohort.json](audits/official-universe/2026-09-19/next-cohort.json), preserving
the separate Dhanwel June/August lifecycle conflict. Retry only the recorded NSE
quarters after endpoint access changes; reuse the completed SEBI windows.
The separate numerical P4 task remains the five BSE current/upcoming detail-layout
family recorded in ROADMAP; it was not replaced by a financial backfill.


## Previous checkpoint — reviewed active offer terms released, 19 September 2026

Current verified release main: **`689eb4124c253d1fe59f20f9834e8fddaee2bd51`**.
Accepted three-issuer data: **`f0419d59cabc39a047c2fb2d69b3fb216c45c693`**;
assessment base: `e0094dce2649e3c5761ded4c4de32e7649da4f1f`. Documentation
closeout branch is `docs-active-offer-release-20260919`, [PR #161](https://github.com/Vasuki8/IPO-Tracker/pull/161);
its commit is identified by Git history containing this checkpoint. See the [release receipt](releases/2026-09-19-active-offer-terms.json),
[exact-byte live verification](releases/2026-09-19-active-offer-live.json) and
[source review](reviews/2026-09-19-active-offer-source-review.md). Completed
financial #143/#144, universe #145–148, operations #149–151/#154–157 and commercial
#152/#153 work was recognized and preserved. The previous exact next task is now
complete for the supported NSE labelled-table family.

**Problem and affected users:** current/upcoming IPO researchers could see the
offer windows but not independently reviewable active bidding terms. The shared
NSE `issueInfo.dataList` parser now retains exact response bytes/hash, issuer,
symbol, board, dates, row/table, unit, review version and correction history.
Accepted provisional receipts remain separate from completed static facts.
Source observation stays unknown; collection/review clocks are distinct.

**Source-reviewed and live:** Axiom Gas shows INR 51–54, bid lot 2,000 and fresh
up to 9,398,000 shares; Varmora shows INR 140–148, bid lot 101, separately labelled
minimum quantity 101, fresh up to INR 320 crore and OFS up to 26,217,634 shares;
Pooja Logistics shows INR 109–115, bid lot 1,200 and fresh 3,846,000 shares.
Every accepted field carries provisional authority, a source link and IST expiry.
Market lot, unknown minimum quantities and all three total issue amounts stay
unknown. No total is calculated from shares times cap price. Existing subscription
observations are unchanged; SpectraA remains held.

Rendered document review confirmed Axiom's 16 September revision explicitly
supersedes its older 50–53 advertisement. Varmora's RHP and issuer advertisement
confirm the fresh/OFS and floor/cap distinction; its retained floor share count
cannot be multiplied by the cap price to establish a total. Pooja's NSE detail
supports the accepted terms, but the RHP connection failed and ratios archive
timed out; placeholder issuer PDF links were rejected. These access gaps remain
open. Immutable source review commit: `1fb4c7d12e1a5eb616a4db16b304a0aeda32103f`.

**Measured result:** the three issuers' exchange gaps fell **12 → 3**: nine actual
missing fields filled, with only total issue amounts remaining. Global price-band
gaps **30 → 27**, bid-lot gaps **925 → 922**, composition gaps **60 → 57**;
amount gaps remain **969**. This is not a source-review-count reduction. All
**1,557 validation issues and expanded queue reviews** are identical to baseline;
all **441 proposals are byte-identical**, inventory remains **1,379**, queue **1,364**.
Only these three canonical records changed, within reviewed receipt/source/history/
validation scope. Static values, Final Prospectus proofs, holds and policy remain.

- [PR #158](https://github.com/Vasuki8/IPO-Tracker/pull/158): shared parser, reviewed transport and public eligibility; implementation `e158ee56`, isolated active clock metadata `4b245d41`, merge `a310209e`.
- [PR #159](https://github.com/Vasuki8/IPO-Tracker/pull/159): bounded request `5bbc3809`, merge `9c404bea`; existing publisher **35417782070** accepted exactly three IDs at `f0419d59`.
- [PR #160](https://github.com/Vasuki8/IPO-Tracker/pull/160): read-only delivery verifier `18ada890`, merge `9fd5ef2b`; retained source-proof Git identity and active receipt/value/qualification/clock/expiry checks.

**Tests:** final PR validation **35418119511** passed **1,332 Python tests**, strict
validation (zero errors), proposal checks and public generation. Browser
**35418119472** passed the existing regressions, **38 Node tests**, and the new
three-real-document cohort at 1440/375/320px across profiles, directory, quick view,
comparison and CSV, including provisional expiry. Focused parser tests cover both
composition layouts, reservations, units, ambiguous columns/labels, identity,
contradictions and separate quantities. Four new delivery tests independently
passed. Local Windows retains only the two known filename/symlink limitations;
the complete Linux suite passes them unchanged. Source correctness was separately
reviewed against the official response bytes and documents, not inferred from CI.

**Deployment:** support publisher **35417569744**, bounded publisher **35417782070**
and final review-only publisher **35418300903** succeeded. Final publication only
refreshed three generated report clocks; accepted data/proofs stayed unchanged.
Pages **35417847172** deployed accepted data; Pages **35418352442** deployed the
final release. Live verification **35418374265** passed. The earlier accepted-data
verification **35417869059** failed because its verifier did not recognize the new
receipt kind; #160 fixed that delivery-contract gap without changing accepted values.
Independent HTTPS verification matches all selected public artifact bytes and
checks the 1,379-route manifest; actual live browser checks confirm all three
profiles' values, null totals, provisional labels and unknown source clocks.

**Current P4 remains incomplete:** **387 actionable + 63 higher-priority records;
1,553 blocking / 1,557 total reviews**, four P5-only, zero semantic errors and
zero unmapped reviews. Final Prospectus revalidation remains 321 P4 records /
1,174 fields and 28 higher-priority records / 104 fields. P5 remains waiting (914).
No remaining acceptance criteria for this bounded source family. Qualified total
amount layouts, Pooja source recovery, Vinod shareholding subtotal/page locators,
SpectraA and other holds remain unresolved. Historical Snehaa/Sacheerome NSE PDF
access failure is still open; no old cached evidence is represented as a new pass.

Old PRs #94/#98/#99/#104/#105 and the unrelated `fix-nse-detail-denominators`
worktree remain untouched. No active development PR remains from this milestone
after documentation closeout. Audience, pricing/revenue, redistribution rights,
hosting suitability, legal operator/privacy and professional review remain owner
decisions. No new spending, contracts, tracking, permissions, P5 or performance.

**Exact next task:** inspect the shared BSE current/upcoming detail and identity
layout for **FX Multitech, Robokidz Eduventures, Vivekanand Cotspin, Himalaya
Nutravedics India and S. K. Offset**. These five SME records have 25 retained
exchange gaps (symbol, price, lot, total and composition); this is a candidate
batch size, not a promised reduction. Bind official identities/windows and review
multiple real documents before proposing fields. Keep the three NSE total amounts
for a separate qualified floor/cap amount family and retain all existing holds.


## Previous checkpoint — core clocks released and source hold verified, 19 September 2026

Current verified data-release main: **`118a5dd33913c5a2f76d15ad5939574eb5e85af3`**.
Core publication is `5ea15921c2a2e742b282acefad6df366dab0c58f`; assessment base
was `ac51bebeb75a1afd41150a061288d4078e0e89c9`. Documentation closeout branch is
`docs-core-release-closeout`, [PR #157](https://github.com/Vasuki8/IPO-Tracker/pull/157);
its commit is identified by Git history containing this checkpoint. The [release receipt](audits/operational-health/2026-09-19-core-clocks/release.json)
binds commits, source evidence, checks and live artifacts. Completed financial
#143/#144, universe #145–148, operational #149–151 and commercial #152/#153 work
was recognized and preserved. Hy-Tech/Onemi was not repeated.

**Completed:** core sources now record actual endpoint/page/range attempt clocks,
partial failures and explicit deferred states. Unknown source observation stays
unknown; concurrent publication keeps an outcome and its clock together. Seven
reviewed BSE-only identities survive an independent NSE success/BSE failure;
their exact retained official HTML receipts replayed. All **1,379 IDs**, all eight
admission receipts and **441 byte-identical proposals** survive publication.

- [PR #154](https://github.com/Vasuki8/IPO-Tracker/pull/154): `089a9464` / `7c9de7f8`, merged `9878e0f6`.
- [PR #155](https://github.com/Vasuki8/IPO-Tracker/pull/155): `ac6a318f` / `5927d9de` / `383d9a30`, merged `432c9fa1`.
- [PR #156](https://github.com/Vasuki8/IPO-Tracker/pull/156): `6d073ab5` / `c392c02b`, merged `06bd9f77`.

Release inspection cancelled first collector **35412526647** before publication
when legacy cleanup threatened seven accepted admissions; no accepted data was
lost. Superseded preview **35412888497** was cancelled while core preview was
restricted to its existing retained-data path. Final preview **35413034734** passed
both jobs; mixed parser changes retain their original full source preview.

**Source-review follow-up:** existing bounded filing maintenance populated Vinod's
financials, objects and shareholding. Independent SEBI PDF/hash/visual review passed
all **nine financial and five allocation amounts**. Its derived 93.11% promoter
percentage and wrong page locator failed review. An exact issuer/offer/PDF/value
hold now withholds shareholding and adds one manual review, retaining the canonical
value, empty parsed names, proof and three correction events. No 93.10 replacement
is accepted. See [physical pages, units and findings](reviews/2026-09-19-vinod-publication-source-review.md).
This is an added visible defect, not a claimed P4 reduction. The value binding covers
the whole object; a future names/value change requires review, not automatic acceptance.

**Tests:** final Linux validation **35414579930** passed **1,314 Python tests**,
strict validation with zero errors, retained-proposal checks and public generation.
All **36 Node tests** and browser **35414579922** passed, including Vinod profile
and quick view at 1440/390/320px, CSV, prior holds and financial/intermediary
regressions. Local Windows has only the two known filename/symlink limitations,
which pass on Linux. Historical before/after reports and the final report reproduce;
the Git comparison is deterministic across hash seeds. Diff review confirmed all
1,556 prior review issues and queue tasks remain, with exactly one new manual hold.

**Published and live:** core refresh **35413219212**, Pages **35413782301** and
deployed verification **35413803388** succeeded at `5ea15921`. Review-only refresh
**35414832256** published `118a5dd3`; Pages **35414893422** and live verification
**35414917011** succeeded. Nine additional exact-byte live checks confirm canonical,
proposals, phase/validation/queue/hold registry, summary, Vinod profile and source
health code. Live browser shows Shareholding **Under review**, promoter pre-issue
as a dash, and matched financial/objects values retained. Earlier 13 exact-byte and
18 public-route checks verified core/admitted profiles and source diagnostics.

NSE live has 12 rows and two successful attempts; history has a successful empty
dated range. SEBI has 13 unique filings across four requests, not a full-history
coverage claim. BSE retains eight rows plus two failures out of three attempts.
The final operational report at **02:12:42Z** records **5 failed sources, 1 partial
failure, 27 successful entries; 0 known overdue source checks/stages; 3 stages and
6 sources needing investigation; 441 unresolved proposals**. Two subscription
observations exceed tolerance outside monitoring hours, not a missed intraday SLA.

**External evidence check remains failed:** **35414579942**, both attempts, could
not retrieve unchanged Snehaa/Sacheerome PDFs. Independent requests received HTTP
200 HTML declaring regional unavailability (18,590 bytes), not matching PDFs.
Original hashes/holds and the fail-closed checker remain unchanged; cached old PDFs
do not count as a current pass. This does not affect Vinod's retrieved SEBI evidence.
The protective hold was merged through the normal authorized workflow with that
unrelated access gap explicitly unresolved; no checks or protections were changed.
See [the access receipt](audits/operational-health/2026-09-19-core-clocks/nse-access-gap.json).

**Current P4:** **387 actionable + 63 higher-priority; 1,553 blocking / 1,557 total
reviews**, four P5-only, zero semantic errors/unmapped reviews. Before this hold:
1,552 / 1,556. P5 remains waiting (914 records); 321 P4 records need Final Prospectus
revalidation. No remaining implementation/release acceptance criteria for this
bounded milestone; numerical shareholding repair and source-access recovery remain
separate open work. BSE primary-page parsing/SME timeout, SpectraA, other source
holds and proposal backlog remain unresolved.

Old PRs #94/#98/#99/#104/#105 remain separate and unmerged; no active development
PR from this milestone remains after documentation closeout. The unrelated
`fix-nse-detail-denominators` worktree is preserved. Audience, pricing/revenue,
redistribution rights, hosting suitability, legal operator/privacy and professional
review remain owner decisions. No spending, tracking, contracts, material access
changes, P5 or performance expansion.

**Exact next task:** source-review the current/upcoming offer-term cohort Axiom Gas,
Varmora and Pooja Logistics against matching official lifecycle/document evidence,
cluster common layouts, and repair only supported fields. Keep SpectraA held.
Also retain the newly exposed shareholding subtotal/page-locator family for bounded
multi-document diagnosis; PNGS Reva's adjusted EBITDA/partnership EPS remains
conditional. Retry the unchanged NSE historical evidence check once access returns;
no unattended retry or monitoring was configured.

## Previous checkpoint — commercial evidence review, 19 September 2026

Current verified research-release main: **`c39c823c715599d9a169ed2b7a773a4c3cd98482`**.
Assessment base was `11a62c47f64506fb3fbccdec8ba7f88e43d8c468`; the final
documentation closeout commit is identified by Git history containing this checkpoint.
Fetched current main and recognized completed PRs #149–151 before research.
This sequential milestone updates [COMMERCIAL_READINESS.md](COMMERCIAL_READINESS.md)
and retains a [dated research receipt](audits/commercial/2026-09-19/REPORT.md),
reproducible inventory and verbatim prior register.
[PR #152](https://github.com/Vasuki8/IPO-Tracker/pull/152) merged research commits
`e766387e` and `4eb0fb50` as `c39c823c`. Research branch
`docs-commercial-rights-20260919` is merged. Documentation closeout branch:
`docs-commercial-release-20260919`.

Local checks passed: exact offline inventory reproduction, byte-identical prior
register, local document links, protected-data/public-output diff, and strict
validation (zero errors, 1,556 retained reviews). All **34 Node public-quality and
source-health tests** passed; initial sandbox process-spawn denial was resolved
by running the same tests with approved execution permissions. All **1,293 Python tests** passed on Linux in
[validation 35410043930](https://github.com/Vasuki8/IPO-Tracker/actions/runs/35410043930),
along with public generation, retained-proposal checks and strict validation.

New primary restrictions recorded for IPO Premium, Groww, IPO Dhamaka, Orkla,
Sunshine and Integrated Registry. Six configured issuer/registrar hosts plus four
additional issuer hosts reviewed; missing permission remains unknown. Recent
17 September NSE/SEBI/Pages evidence carried with its original check date. BSE
website terms remain inaccessible (403); data portal supplies no readable agreement.
The bounded inventory has **58 hostnames**, eleven locked package notice inventories,
and **nine canonical secondary subscription labels** (six IPO Premium, three IPO
Dhamaka). Historical references are not represented as accepted facts or permissions.

Live canonical, proposal and summary JSON routes returned HTTP 200. Rights review
therefore includes raw/public history and exports, even when interface holds hide a
value. No source/data permission obtained and no access/publication policy changed.
GitHub Actions service/billing/privacy reviewed; Cloudflare Pages remains an
unselected static candidate with explicit file/build limits, not a migration approval.
Windows tzdata and transitive notices narrow prior software gaps; exact CI binary,
asset provenance and project license questions remain.

Four unvalidated customer hypotheses: active retail researchers, long-term investors,
small advisor/research teams and finance editors. Candidate free/paid workflows,
a disabled aggregate-first measurement plan, retention/consent questions, seven
cost categories and correction/incident responsibilities are documented. Pricing,
legal operator/jurisdictions, source rights, permitted hosting, outreach, review
budget, code licensing, support capacity and privacy decisions remain with owner.
Qualified review is required for the actual data uses and regulatory/privacy scope.
No contracts, contacts, purchases, tracking, billing or accounts were introduced.

P4 unchanged: **387 actionable + 63 higher-priority**, **1,552 blocking reviews**,
1,556 total reviews (four P5-only). Canonical inventory **1,379**, proposals **441**;
P5 remains waiting with 914 records. No numerical correction or blocker reduction.
Older open PRs #105/#104 (draft), #99, #98 and #94 remain untouched.

Research release [Pages 35410171795](https://github.com/Vasuki8/IPO-Tracker/actions/runs/35410171795)
and [live verification 35410194991](https://github.com/Vasuki8/IPO-Tracker/actions/runs/35410194991)
passed for `c39c823c`. At **2026-09-19T00:42Z**, direct live SHA-256 comparisons
matched COMMERCIAL_READINESS, the research report/inventory, index.html and
source-health.js to the immutable merge. See [release.json](audits/commercial/2026-09-19/release.json).
Research documentation only; no public product behavior or protected-data changes.

**Exact next commercial task:** map the nine secondary subscription records plus
Orkla/Sunshine/Integrated Registry evidence to published fields/excerpts, raw
JSON/proposals/history and exports, then use the packet for owner-directed
professional review of interim collection/publication policy. Recover readable BSE
terms through permitted access; continue unreviewed hosts without treating gaps as
permission. Spending/outreach/contracts and material access changes require owner
approval. P4 engineering priority and existing operational/universe next tasks remain.

## Previous checkpoint — operational health release, 18–19 September 2026

Recovery started at **`4f0e5599be8d9230bdd9b929aec6382e8c600be5`** after
the completed official-universe release. The existing read-only report from
PR #126 was extended; source repairs, inventory admissions and operational
writers were not duplicated. Current accepted main before documentation closeout:
**b6d82f7824758d0cb3ae767e2e5673f8a1f6b208**.

[PR #149](https://github.com/Vasuki8/IPO-Tracker/pull/149) joins the existing
source-health, stage, proposal reconciliation, review-decision, queue and phase
evidence in `tools/report_update_health.py` (`7f97991e`, `7b5549ce`; merge `04e795e8`).
It adds JSON/Markdown views, explicit source roles, independent check/observation
clocks, latest retained stage success, failure/deferral reasons, publication
execution windows, and all retained proposal identities/ages/next actions.
No alerts, network collection or competing state store were added.

[PR #150](https://github.com/Vasuki8/IPO-Tracker/pull/150) corrects public clock
and authority labels (`e30aa734`, `e08eed05`, `0f6ed615`, `dd344fd5`; merge `b6d82f78`).
Unknown source checks no longer borrow the dataset generation time. Deferred,
failed, degraded and unavailable outcomes remain distinct. Mixed subscription
diagnostics expose their retained failures and secondary-source counts; source
roles do not establish field authority. The snapshot tooltip identifies generation
time separately from source observation and accepted publication. The existing
presentation route was verified before release to avoid repair collection.

The [frozen operational assessment](audits/operational-health/2026-09-18/REPORT.md)
at **2026-09-18T23:38:00Z** retains 33 source entries and 14 stage entries:
**5 failed source entries**, **3 blocked stages**, **0 overdue monitored source
checks/stages**, and one unknown subscription-stage outcome. These are retained
outcomes, including historical entries, not five newly failing sources in one run.
Five active-by-recorded-date subscriptions include **2 observations older than
the 90-minute tolerance** and **3 unknown observation times**. Subscription
monitoring deadlines were inactive at that instant; absence of an overdue signal
does not establish freshness. Eight source entries need investigation.

All **441 pending proposals** remain unresolved: 181 still conflicting, 260 not
assessed. Exact creation ages are unknown for all 441; four bound origin workflow
windows are retained separately. The existing Emmvee decision remains visible
with its stale-evidence/revalidation flag. No equality/age signal resolves a review.
All **1,556 source reviews**, including **1,552 blocking** and four P5-only, remain.
The accepted collector metadata names run `35402275281`: publisher execution
22:45:54–22:46:28Z, collection completion to publisher completion **37 seconds**.
Exact accepted-commit and per-source acceptance timestamps remain unknown; later
identity edits are not misrepresented as that earlier publisher execution.

Tests: **29 focused operational tests**, **34 Node/public-quality tests**, all
**1,293 Python tests on Linux**, strict validation with **zero semantic errors**,
exact offline report reproduction and protected-data byte checks. Windows retains
the two known filesystem-only test errors. Browser CI checks diagnostic clocks,
text bounds and existing public behavior at **320, 375 and 1,440 pixels**.
Final PR validation: [35407785625](https://github.com/Vasuki8/IPO-Tracker/actions/runs/35407785625) and [35407821461](https://github.com/Vasuki8/IPO-Tracker/actions/runs/35407821461). Browser [35407821463](https://github.com/Vasuki8/IPO-Tracker/actions/runs/35407821463) and candidate-release [35407821459](https://github.com/Vasuki8/IPO-Tracker/actions/runs/35407821459) passed. Clock fixtures were separated from document fixtures without weakening assertions or source-review rules.
Combined main validation `35408036734` and browser checks `35408036728` also passed.
Publication [35408036765](https://github.com/Vasuki8/IPO-Tracker/actions/runs/35408036765) confirmed presentation mode, 1,379 unchanged company pages, no data rewrite and no summary rewrite. [Pages 35408105745](https://github.com/Vasuki8/IPO-Tracker/actions/runs/35408105745) and [live verification 35408140207](https://github.com/Vasuki8/IPO-Tracker/actions/runs/35408140207) passed. All 24 checked live files matched the immutable release, including `source-health.js`; direct live browser checks confirmed unknown check times, retained SpectraA errors and mixed-source labels. See the [release receipt](audits/operational-health/2026-09-18/release.json).

Canonical inventory remains **1,379**; this work changed no canonical values,
proposals, source-review dispositions or source proofs. P4 remains **387 actionable
+ 63 higher priority**, **1,552 blocking reviews**. P5 remains waiting with 914
records. No P4 blocker reduction is claimed.

Unresolved operational gaps: core source check times are missing; source-level
observation times and historical last-success clocks are not recorded; exact
proposal creation and accepted-publication clocks are absent. SpectraA subscription
collection is blocked by unavailable matching feeds. Legacy BSE-history metadata
still describes the old collector failure even though the separate universe audit
recovered an archive. These remain visible; no source failure was treated as completion.

Older open work remains untouched: #105/#104 drafts, #99, #98 and #94. Customer
segment, pricing/revenue model, source redistribution rights and hosting fit remain
unresolved; no spending, outreach, contracts or permission changes were made.

**Exact next operational task:** add evidence-bound check timestamps for future
NSE/BSE/SEBI attempts inside the existing core collector, with failed/deferred
attempt tests. Keep observations unknown when sources supply no timestamp; never
retrofill check times from build/stage clocks. Separately, the next universe cohort
remains the 12 retained August BSE SME candidates; P4 source repairs retain priority.

Operational counts were recomputed unchanged at **2026-09-19T00:07:30.687014+00:00**. The receipt retains the report digest and input hashes. The snapshot is not an always-on monitor. Documentation closeout branch: `docs-operational-health-release-20260918`.

## Historical checkpoint — official-universe release verified, 18 September 2026

Accepted data/main commit observed before documentation closeout:
**`794a8f6012047a0d817f4363a9374439c9892eb3`** (PR #147).
Recovery began at `6992dd44`; the intervening scheduled data publication was
incorporated without changing any of its 1,371 existing records.
The prior HTEL/Onemi financial release is preserved below and was not repeated.
[PR #146](https://github.com/Vasuki8/IPO-Tracker/pull/146) added the audit and eight
reviewed identities (`780f3b85`, `2b16d34c`; merge `b23fc366`). Live review caught
collection time labelled as source-record time on their source links.
[PR #147](https://github.com/Vasuki8/IPO-Tracker/pull/147) corrected that boundary
(`8836f864`; merge `794a8f60`), retaining null observation times, collection clocks
and correction history. Documentation closeout branch:
`docs-official-universe-release-20260918`.

Both PRs passed all **1,283 Python tests on Linux** (runs
[35403902766](https://github.com/Vasuki8/IPO-Tracker/actions/runs/35403902766) and
[35404373836](https://github.com/Vasuki8/IPO-Tracker/actions/runs/35404373836)).
Final data release: [Pages 35404502951](https://github.com/Vasuki8/IPO-Tracker/actions/runs/35404502951),
[live verification 35404532544](https://github.com/Vasuki8/IPO-Tracker/actions/runs/35404532544)
and main validation `35404503868` all succeeded. Complete HTTP bytes matched for
31 public files including all eight new profiles. Live browser checks verified
their names, official links, unknown terms and unknown source clocks; directory
search finds Vinod with its reported listing date. The previously visited Vinod
page required a fresh browser load after deployment; its plain-URL HTTP bytes
also matched. See the retained [release receipt](audits/official-universe/2026-09-18/release.json).

The [official-universe report](audits/official-universe/2026-09-18/REPORT.md) and
[reproducible audit](audits/official-universe/2026-09-18/audit.json) establish that
coverage is incomplete. Distinct observed candidate denominators after eight
reviewed admissions: NSE **173/174 (99.43%)**, BSE **563/1,848 (30.47%)**, SEBI
**2,602/5,813 (44.76%)**. These are source-record/name match rates, not whole-market
IPO coverage. Exact source/year/board/lifecycle breakdowns are in the audit.

SEBI: all 236 page positions traversed; RHP 1,270, final-offer 1,560 and Other
Documents 818 rows reconcile. Draft pages disagree between 2,208 and 2,210 rows,
with 43 repeated URLs; completion is not claimed. BSE's recovered official beta
archive has 1,282 book-building rows back to 2002 and 558 fixed-price rows back to
2010. NSE current/upcoming, 2025 Q1 and 2026 year-to-date responded; annual
2000–2025 queries timed out. The SEBI date-filter probe returned HTTP 530.
All gaps and original responses remain retained.

Five evidence-bound aliases were accepted for audit matching; other conflicts
remain open. The report retains 2,160 unmatched normalized candidate names and
227 tracker-only/unreconciled records. These are not automatic new-IPO admissions.
Eight reviewed September issuers were added: Amtech Esters, Quanto Agroworld,
Panchatv Bharat, Infrax Renewable, Apana Logistics, Farm Peace, Fly Hi Maritime
Travels and Vinod Texworld. Seven BSE issues are closed with unknown listing dates;
NSE explicitly lists Vinod on 17 September. Numerical/static terms remain null.

All 1,371 existing records and 441 proposals are unchanged; correction history,
proofs, holds and all 1,556 source reviews are preserved. Inventory is 1,379.
P4: **387 actionable + 63 higher priority; 1,552 blocking reviews; zero semantic
errors**. P5 remains waiting with 914 records. No P4 reduction is claimed.

Tests: 30 focused universe/evidence tests, 20 affected operational regressions,
nine Node quality tests and strict validation pass. Direct browser checks cover
all eight profiles, directory search and mobile layout. Full Linux CI passed;
the full Windows run retains the two known filesystem limitations. The metadata
count mismatch found during that run was fixed without weakening validation.

The earlier open PRs #105/#104 (drafts), #99/#98/#94 remain untouched. Commercial
segment, pricing, revenue model, source redistribution rights and hosting fit
remain unresolved. No paid services, outreach or permissions changed.

**Exact next task:** review the [12 BSE August 2026 missing SME-name candidates](audits/official-universe/2026-09-18/next-cohort.json)
from the retained archive. Check issuer/symbol/issue-period details and possible
tracker aliases before accepting any new identities; leave unknown terms null.
Recover stable SEBI
draft pagination and the failed NSE historical ranges separately; do not repeat
verified RHP/final/Other/BSE cohorts or begin numerical backfill.

## Historical checkpoint — reviewed financial release, 18 September 2026

Current accepted data/main commit observed before documentation closeout:
**`ea5f0f2631051feffb470c2cbd1b596f5767cf06`**. Sequential recovery started at
`07527e52d2a3b590be2851fcb0d578ed3f580136`; the earlier intermediary/NSE work was
already complete. Documentation closeout branch: `docs-p4-financial-release-20260918`.
This section supersedes the historical checkpoint below.

### Completed, merged and verified live

[PR #143](https://github.com/Vasuki8/IPO-Tracker/pull/143) merged as
`df5196139d8747a3c4422313a9f5355451204eeb` (code/evidence commits `9229780b`,
`e0193a2a`, `79648113`). The shared offline financial-grid helper repairs annotated
annual consolidated tables, explicit revenue and net-worth rows, wrapped EPS
labels and separate interim columns. It rejects ambiguous dates/columns/units,
conflicting scope/values, percentage/currency contamination and incomplete rows.
Global collectors/parser versions were not expanded.

Reviewed issuers: **Hy-Tech Engineers / HTEL** and **Onemi Technology Solutions /
KISSHT**. All 36 existing annual metric cells now have matching Final Prospectus
evidence. The correction fixes switched years, share-count/date tokens stored as
EPS, total income stored as revenue, interim values stored as annual values, and
percentages stored as net worth. It preserves all six existing metrics and three
annual years per issuer; no review was moved into an exclusion or silently dropped.

Both official PDFs were hash-checked and fully extracted with production
`pdftotext -layout -fixed 3` flags (416/416 and 464/464 pages). Physical ratio,
revenue and net-worth tables were visually/source reviewed and replayed from
retained native text spans. Cover dates, filing dates, collection/review clocks,
reporting periods, units and correction history remain distinct. The source review
also reconciles Onemi's FY2024 revenue restatement and distinguishes its closing
net-worth RoNW denominator from HTEL's average-equity denominator. See
[source review](reviews/2026-09-18-reviewed-financial-grids.md) and
[machine receipt](reviews/2026-09-18-reviewed-financial-grids.json).

Source-free support publisher [35395932313](https://github.com/Vasuki8/IPO-Tracker/actions/runs/35395932313)
produced `88cf2fb6`, changing only derived reports. Request-only
[PR #144](https://github.com/Vasuki8/IPO-Tracker/pull/144) merged as
`4ad09484f1663a873653482408a94b4a06effbf4`. The existing guarded
[publisher 35396161543](https://github.com/Vasuki8/IPO-Tracker/actions/runs/35396161543)
selected `reviewed`, skipped source collection and published `ea5f0f26`.
Only `htel` and `kissht` canonical records changed. **1,369 other records, all 441
pending proposals, all 459 earlier registry corrections, unrelated proofs and
append-only source/correction history were preserved.**

[Validation 35395566118](https://github.com/Vasuki8/IPO-Tracker/actions/runs/35395566118)
passed **1,253 frozen Python regressions** on Linux. Focused checks include 13 new
financial parser/publication tests, 20 public-release verifier tests, five request
tests, strict validation and nine Node public-quality tests. The local full run
retained the two documented Windows filesystem limitations; Linux tests passed
without weakening them. [Source preview 35395566141](https://github.com/Vasuki8/IPO-Tracker/actions/runs/35395566141)
and public consistency 35395566231 passed. [Browser 35395566217](https://github.com/Vasuki8/IPO-Tracker/actions/runs/35395566217)
passed existing directory/CSV/comparison/hold journeys and both reviewed financial
profiles/quick views at 1440/375/320 pixels. Its artifact checksum matched and both
mobile profiles were visually reviewed. An initial delivery-test assumption about
the compact profile's omitted unit field was fixed; canonical units and all public
cells are now explicitly checked against the existing table-caption contract.

[Pages 35396284700](https://github.com/Vasuki8/IPO-Tracker/actions/runs/35396284700)
and [live acceptance 35396326142](https://github.com/Vasuki8/IPO-Tracker/actions/runs/35396326142)
passed on the accepted data commit. A separate local release verifier checked all
1,371 routes and compared complete live HTTPS bytes, including both repaired
profiles and their exact reviewed values/proofs. Direct browser inspection confirmed
the annual rows and Final Prospectus page-282/page-335 links. PNGS's financial table
remains withheld. See [release receipt](releases/2026-09-18-reviewed-financial-grids.json).

### Current P4 gate and remaining work

P4 is **incomplete: 387 actionable + 55 higher-priority records**. Source reviews:
**1,556 total / 1,552 blocking / four P5-only / zero unmapped / zero semantic errors**.
Before this batch: 388 actionable + 55 higher priority; 1,598 total / 1,594 blocking.
The verified reduction is **42 blocking source reviews and one actionable P4 record**.
P4 Final Prospectus revalidation is 321 records / 1,174 fields; higher priority is
28 records / 104 fields. P5 remains `waiting_for_p4` with 914 actionable records;
performance expansion remains gated.

PNGS Reva's official PDF was recovered, hash-matched and fully extracted (477/477
pages). Physical page 331/printed327 reports **Adjusted EBITDA**, partnership-era
FY2024/FY2023 and explicitly unavailable historical EPS. This is a distinct,
unsupported representation/layout, not source unavailability. **All 18 PNGS
reviews remain open.** No adjusted EBITDA was relabelled and no EPS was estimated.
Other source holds, including SpectraA and Teamtech, remain active. An older
scheduled artifact from `07527e52` was correctly rejected by source-policy guard
in run 35395047328; it must be recollected with current policy, never forced through.

Active earlier PRs remain untouched: draft **#105** `fix-p4-reviewed-integration`
(`5a63a93d`), draft **#104** `integrate-p4-reviewed-repairs` (`4d94951b`), **#99**
`fix-kaytex-speb-document-holds` (`a503531d`), **#98**
`fix-reviewed-correction-publication-guard` (`d5e5d058`), and **#94**
`fix-p4-mixed-ofs-sellers` (`4707df1e`). Their broad/obsolete stacks are not release
evidence; do not merge them wholesale or repeat already accepted work.

Commercial decisions remain unresolved: paying segment, pricing/revenue model,
source storage/display/redistribution permissions, hosting fit/cost and applicable
professional review. No spending, outreach, contracts, permissions, accounts,
billing, analytics or infrastructure changes were made.

**Exact next task:** inspect PNGS Reva's Final Prospectus annual PAT/net-worth rows
and definitions alongside page 331. Cluster other documents with explicitly labelled
Adjusted EBITDA and partnership-era unavailable EPS; implement a separate reviewed
representation that preserves those distinctions and nulls, then complete the same
source-reviewed bounded publication chain. Its PDF hash and source excerpt are in
the machine receipt. Do not reuse the current consolidated grid scope blindly, and
do not re-review HTEL/KISSHT unless repository evidence changes. This selected
two-issuer consolidated-table milestone is released and complete; P4 is not.

## Historical integration checkpoint — 18 September 2026

Accepted data release/current main observed before documentation closeout:
**`de69f6ce92b94ce0acfbe6709c38a1b170c313a8`**. Recovery started from the supplied
`64697fe1d837e422a6678c51959e647fb7ad6e0b`; scheduled core publication
`268946862820bfead2b3b5e0c14c7a1f637d7dd5` arrived during review and was incorporated.
Earlier completed #108, #114–#117 and #135–#138 were recognized, not reapplied.
Documentation closeout branch: `docs-p4-integration-20260918`.

### Completed and verified

[PR #139](https://github.com/Vasuki8/IPO-Tracker/pull/139), merged as
`5039a33853a810b9beafea52a97e8e4e05f38ce1`, adds a reusable paired-column review
helper and evidence-bound intermediary publication. It requires exact issuer/offer
identity, role/name spans from one physical table, document hash/date, Final
Prospectus authority and separate collection/review clocks. Explicit-reviewed
correction groups remain inert in ordinary registry application. Generic
re-extraction of the same PDF cannot undo accepted reviewed role evidence;
different authoritative documents remain eligible. Existing holds/history survive.
The source-free support publisher produced `08b35e42` with unchanged canonical
and pending-proposal bytes.

[PR #141](https://github.com/Vasuki8/IPO-Tracker/pull/141), merged as
`3ef3e3e665eb10752eca7d35d7c273d4e0bd25df`, changes only the reviewed request.
[Publisher 35390088056](https://github.com/Vasuki8/IPO-Tracker/actions/runs/35390088056)
selected `reviewed`, skipped source/residual collection, generated a fresh source
manifest and published `cf4dae81`. Only Snehaa and Sacheerome's intermediary groups
were accepted; 1,369 other issuer records and all 441 pending proposals survived.
Snehaa now has Fast Track Finsec / Skyline; Sacheerome has GYR Capital Advisors /
MUFG Intime India. Complete legal names and matching proofs are retained.

Exact official Final Prospectuses were downloaded and hash/page-tree checked:
Snehaa (467 pages, physical role table 1, corroborating 83) and Sacheerome
(293 pages, role table 3, corroborating 52). The source review distinguishes
Sacheerome's current MUFG legal name from its former Link Intime name. Source
bytes, role rows and rendered pages were reviewed; this is not a claim to have
audited every disclosure in both documents. See the immutable linked source
review and [release receipt](releases/2026-09-18-reviewed-intermediaries.json).

Final PR-head validation 35388997223 passed **1,217 frozen Python 3.12 regressions**;
source-free preview 35388996960 and release rehearsal 35388997191 passed.
[Browser 35388996780](https://github.com/Vasuki8/IPO-Tracker/actions/runs/35388996780)
passed 25 existing journeys, nine Node tests, existing hold/BSE/Emmvee checks and
both new intermediary profile/quick-view journeys at 1440/375/320 pixels. The
downloaded artifact checksum matched; both 375-pixel profiles were visually
inspected. Request validation 35389898010 and five local request tests passed.
Local Windows full-suite limitations (control-character filenames and symlink
privilege) were not used to weaken Linux tests; Linux remains the release authority.

[Pages 35390194114](https://github.com/Vasuki8/IPO-Tracker/actions/runs/35390194114)
and [live acceptance 35390243353](https://github.com/Vasuki8/IPO-Tracker/actions/runs/35390243353)
passed on `cf4dae81`, including exact reviewed values/proofs and served profile
bytes. Direct live browser checks also confirmed Snehaa's page-1 role links and
Sacheerome's page-3 role links in its profile/quick view, with unrelated fields
still under review. Candidate artifacts were never substituted for deployment.

### Current blockers and next work

P4 is **incomplete: 388 actionable + 55 higher-priority records; 1,598 total
source reviews, 1,594 blocking, four P5-only, zero unmapped and zero semantic
errors**. This release removed **three actual blocking reviews** (1,597 → 1,594),
not three whole-record blockers. Final Prospectus revalidation remains 322 records /
1,175 fields (higher priority 28 / 105). Inventory remains 1,371. P5 remains
`waiting_for_p4` with 914 actionable records; performance expansion is gated.

SpectraA's exact NSE SME response now has a retained source/denominator review.
Its counts-only categories, zero-denominator EQ placeholder and graph total do
not establish a safe replacement snapshot. The hold remains active.
[PR #140](https://github.com/Vasuki8/IPO-Tracker/pull/140) merged as
`a0e7e0214bd161b227e822bbe0c41287f8e23429` after combined validation 35390771579
passed **1,239 frozen regressions**, including 22 real-response/guard tests.
The six-file change requires exact issue identity, correct API series and matching
reported multiples/bid denominators; contradictory duplicate counts fail even
when a row lacks a multiple. The response fixture stays outside the unrelated
Final Prospectus preview glob; no workflow or protection was changed. Earlier
broad previews on obsolete heads remain diagnostic and unaccepted.

[Publisher 35390899139](https://github.com/Vasuki8/IPO-Tracker/actions/runs/35390899139)
used `subscriptions` mode and published `de69f6ce`. The source stage reports
`source_blocked`: five attempts, four updated records, zero added history snapshots,
one failure (SpectraA), zero NSE successes, two BSE and two explicitly labelled
secondary fallbacks. NSE returned HTTP 403 in the runner. This is a deployed guard,
not acceptance of a replacement SpectraA number or proof of fresh official NSE
data. All historical source bindings, 441 proposals and Teamtech's hold remain.
The four successful refreshes changed collection/check clocks, not subscription
values or history. Ordinary policy-check clocks were regenerated across the
inventory; they do not represent a new PDF source review. Snehaa, Sacheerome,
Teamtech and SpectraA's generated profile bytes match `cf4dae81` exactly.

[Pages 35391159527](https://github.com/Vasuki8/IPO-Tracker/actions/runs/35391159527)
and [live acceptance 35391206824](https://github.com/Vasuki8/IPO-Tracker/actions/runs/35391206824)
passed on `de69f6ce`. The [NSE guard release receipt](releases/2026-09-18-nse-detail-guard.json)
records the exact source outcomes, canonical/proof preservation and served-output
checks. No additional P4 blocker was removed by this guard release.

Legacy #94/#98/#99 and draft #104 remain preserved. Broad draft #105 stays
unaccepted at `5a63a93dd9f782e3bc9ec853c937fb29661108f4`; its preview passing does
not establish source acceptance, and it conflicts with current main. Do not merge
it wholesale or drop its review evidence. The 22 subscription proposals still
need original issuer/source evidence; stale operator advice needs revalidation.

**Exact next action:** reproduce the Hy-Tech and Onemi table failures with
production `pdftotext`, then implement and source-review the shared bounded
`OTHER FINANCIAL INFORMATION` repair in
[the source diagnosis](reviews/2026-09-18-financial-seed-inspection.md).
Both complete PDFs match retained hashes; targeted rendered tables were inspected
and 102 diagnostic receipt/replay assertions passed. Local pypdf layout is not
established as production extraction parity; comprehensive competing-table review
and financial-specific reviewed transport validation remain to do.
Their 42 financial reviews are exposure, not a promised reduction. Preserve annual
versus interim periods, units, scope, EPS basis, conflicts and nulls; accept only
matching Final Prospectus cells through a bounded publication. Add PNGS only if
its source proves the same layout family.

Commercial rights remain unresolved for collection, excerpts, storage, public
JSON/CSV and paid reuse. Paying audience, pricing/revenue model, suitable commercial
hosting, privacy/telemetry and regulatory review remain owner decisions in
[COMMERCIAL_READINESS.md](COMMERCIAL_READINESS.md). No spending, contracts,
outreach, billing, infrastructure or material permission changes were made.

## Historical recovery milestone — 18 September 2026

[PR #137](https://github.com/Vasuki8/IPO-Tracker/pull/137) is merged as
`8dd2a51305a21b5ddb9aebf6c7861128a985ebd0`, tree
`97db9fa055262310c546c867841109892022bae2`. Reviewed head was
`eebd4ff8ba897b91526ac0eaf3986bdffc1795e8` on
`fix-historical-subscription-review-holds`. The existing review-only publisher
produced **`f6db111ac3275a180562e2251c95818b23f4a95f`**, tree
`fa05493d9e58ef4dd35df0a451a6ffbb9ce52eb0`. This output is live-verified.
Documentation closeout branch: `docs-subscription-hold-recovery-checkpoint`.
No second implementation milestone is included in this recovery.

### What survived the interruption

The older portable core-collector patch was recovered and checksum-checked, not
reapplied: #135 and #136 had already completed. Current main was the independent
repair publication `4688128d226c86fd1194f519a09688fed91297cd`, with successful
Pages/live runs 35378534547/35378579959. Its 1,371 records and 441 proposals were
preserved. Original repair/source branches and the handoff archives remain intact.

Open #137 already contained the next historical-snapshot hold implementation at
`482eae8a69f452b8e418acbd4303c36edbff248c`, with source-note parent
`0b27f66c244074e971a0c7e08591f0b842b3cacf`. Its tests/browser checks passed but
release run 35380352028 correctly rejected `spectraa: held subscription leaked`:
it inspected old generated outputs before the review publisher had rebuilt them.
The failed receipt was downloaded and checksum-verified, not disregarded as a pass.

### Completed problem and acceptance criteria

Unreconciled historical subscription figures must not appear as ordinary reported
multiples or escape through chart/history fallback. The existing hold registry now
retains eight exact issuer/offer/snapshot bindings, separate from static PDF holds.
Only SpectraA still matches the current held snapshot: the independent repair had
already replaced the other seven through the existing collector. Those newer
snapshots were neither overwritten nor declared audited resolutions by this work.

A collection-clock refresh or a later history row cannot release mixed facts.
Actual source identity, observation time, category values, missing keys and nulls
remain part of the evidence boundary. Active holds withhold subscription multiples
and history in shared public projections and expose an accurate Field evidence
explanation. Every active hold reaches an actionable manual source-review task,
without inventing a Final Prospectus repair gap or accepting a replacement number.
The [retained review](reviews/2026-09-18-subscription-snapshot-holds.md) preserves
the original dataset/source limitations and eight bindings. The original before/
after hashes and all eight diagnostic changes were independently replayed here.

Recovery follow-up `fddf7cf9` adds a PR-only isolated Git-export rehearsal using
only the four existing derived-output builders. It rejects dirty/mismatched
checkouts, unsafe destinations, missing inputs, symlinks, failed builders and any
protected-file mutation after each stage. Candidate receipts are explicitly not
deployments. Actual deployed verification remains read-only and never rebuilds.
Follow-up `eebd4ff8` narrowly includes the known read-only release workflow in
review-mode routing; any mixed collector, dependency or canonical change still
requires repair. No new publisher, schedule, permission or dependency was added.

### Tests and actual publication

Final-head frozen validation **35383110930**, candidate release **35383110680**,
source-hold evidence **35383110671** and BSE-host evidence **35383110585** passed.
[Browser 35383110570](https://github.com/Vasuki8/IPO-Tracker/actions/runs/35383110570)
passed 25 existing journeys plus active subscription-hold profile/quick-view,
directory, comparison and CSV checks at 1440/375/320 pixels. Static holds, BSE
labels, freshness layout and the reviewed Emmvee rehearsal also passed. Downloaded
browser results matched their artifact checksum; the 375-pixel SpectraA screenshot
was inspected. No page errors or master-dataset requests were reported.

[Publisher 35383599928](https://github.com/Vasuki8/IPO-Tracker/actions/runs/35383599928)
explicitly selected **review** mode and skipped source collection and P4 residual
extraction. Its Python 3.12.14 / `uv sync --frozen` run passed **1,182 regressions**
(21 added across the recovered hold and recovery changes). Post-merge validation
35383599887 and browser 35383599949 passed. Local uv tests passed 12 hold tests,
eight isolated-rehearsal tests and one routing test; nine Node tests passed.
Local Python 3.13 with available packages is not the frozen CI environment.
The Pages mirror lacks some workflow files and direct Git failed DNS; no full
local frozen suite or local browser run is claimed. Remote writes used the actual
connector and original ancestry, not reconstructed local Git history.

[Pages 35383703226](https://github.com/Vasuki8/IPO-Tracker/actions/runs/35383703226)
and [live acceptance 35383754007](https://github.com/Vasuki8/IPO-Tracker/actions/runs/35383754007)
succeeded. The checksum-verified first-attempt receipt checks all **1,371** local
profiles and **23 complete live HTTPS responses**, including SpectraA and its
validation/queue. The deployed workflow skipped the PR builder. Its ordinary
`reviewedPublication=not_requested` is not a new reviewed numerical repair.

Downloaded baseline/published trees and local read-only verifier replay confirm
all canonical/proposal bytes, values, clocks, proofs and correction histories are
unchanged. Teamtech and Emmvee public bytes are identical. SpectraA's displayed
subscription is withheld; heromotors, jsipl and ssretail additionally lose expired
provisional price bands under existing India-date rules. Four profiles changed,
1,367 did not; this is not four source-data corrections. No new numerical source
or full-PDF audit is claimed. The [release receipt](releases/2026-09-18-subscription-hold-recovery.json)
retains exact hashes, lineage, checks, publication scope and the unaltered live
receipt. All acceptance criteria for this hold-delivery milestone are complete.

### Remaining blockers and exact next task

Current P4: **388 actionable + 55 higher-priority records**, **1,601 total source
reviews**, **1,597 blocking**, four P5-only and zero unmapped. The extra blocking
review is SpectraA; it is unresolved work becoming visible, not completion.
Priority changes also reflect the India-date rollover. All **441 proposals** remain
pending. Teamtech stays held; #105 remains draft/unaccepted at
`5a63a93dd9f782e3bc9ec853c937fb29661108f4` with code freeze `409c51c9`.
Preserve #94/#98/#99/#104. P5 and performance expansion remain gated.

**Next:** obtain exact SpectraA issuer/offer/source-detail and bid-denominator
evidence before a bounded subscription correction. Do not replace its number from
headline feeds/history or clear the hold by changing collection clocks. The other
seven historical bindings are retained, not marked resolved; the 22 retained
subscription proposals still need original source/issuer evidence. Revalidate the
stale Emmvee operator advice rather than renewing it automatically. Source rights,
customer segment, pricing and privacy remain unresolved; no spending, outreach,
tracking, billing, infrastructure or access changes were introduced.

Earlier detailed status remains [immutable at the recovered baseline](https://github.com/Vasuki8/IPO-Tracker/blob/4688128d226c86fd1194f519a09688fed91297cd/docs/PROJECT_STATUS.md).
Existing source reviews, correction histories and the dated roadmap audit are preserved.
