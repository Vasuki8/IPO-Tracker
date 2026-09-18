# IPO Tracker — prioritized development roadmap

Current execution update (18 September 2026): #108's publication source guard,
#109's Teamtech document hold and #111's document-conflict wording are released
and live-verified. #112's durable generated-presentation routing is deployed;
its actual refresh skipped source and residual collection and published no data
changes. #110's complete source-review routing is merged after successful
validation, browser and source-preview checks, and is deployed and live-verified.
Its source-preview output remains unaccepted. Main now routes all
1,618 source findings with no unmapped work, while 1,614 findings still block P4.
These increments preserve canonical values and the P4 gate. The combined #105
parser/source draft remains unaccepted: the original seven-record transport is
unavailable, and Teamtech's conflicting prospectus units block its proposed
replacement. See [PROJECT_STATUS.md](PROJECT_STATUS.md) for release evidence,
pending checks and the exact next action; the dated audit below is preserved.

Prepared 17 September 2026. Recommendation: make displayed data trustworthy, make repairs and updates dependable, complete P4, then expand historical coverage and investment-research features. Keep the current light dashboard and static GitHub Pages architecture while doing this.

**Commercial product direction — confirmed by the owner.** IPO Tracker is intended to become a public commercial product with future monetization. Treat this as a standing requirement for product, data, design and engineering decisions. Optimize for customer trust, repeat use, discoverability, accessibility, dependable operation and sustainable cost. The target paying customer, pricing and revenue model remain decisions to validate; no specific monetization model has been selected.

Commercial planning begins alongside the essential repairs. The following adjustments supplement the roadmap and take precedence where an item was previously deferred solely because this was assumed to be a personal tool:

- Assess commercial-use and redistribution permissions for each data source, document, dependency and hosting/service plan using current primary terms. Record evidence and unresolved permissions. Public accessibility and official provenance do not by themselves establish reuse rights. Resolve restrictions before monetizing the affected data or feature; research alternatives without silently changing the source policy.
- Define an initial customer segment, its recurring research problem, differentiated value, and a small set of candidate free/paid offerings. Evaluate options using user evidence and operating costs before building subscriptions or advertisements.
- Establish a crawlable public-site structure, stable URLs, useful source/methodology pages and accessible mobile journeys early. Broader SEO/content expansion follows reliable data-display rules.
- Define privacy-conscious product measures for discovery, profile use, comparison, watchlist use and return visits. Plan the measurements early; activate tracking only after its data collection and consent/privacy requirements are resolved.
- Keep source adapters, canonical data, public projections and later account/billing concerns separable. Maintain low-cost static delivery while it meets requirements. Assess current hosting and data-service suitability before paid operations; do not assume either that migration is required now or that the present plans permit every future use.
- Include incident response, backups/restore checks, user feedback/support and correction handling in readiness for public growth. Determine applicable terms, privacy, consumer and financial-information obligations from the actual product and audience, with current official sources and specialist review where needed; do not treat a disclaimer as blanket clearance.
- Before activating monetization, choose and validate the offering, establish data-use rights, test any authentication/payment/entitlement flow, and document recurring costs and support responsibilities. Obtain approval for new spending, contracts, external communications or materially changed access. Ads and sponsorships must be identifiable and must not influence source verification or factual rankings.

The commercial goal does not relax the P4 correctness gate. P5 and performance expansion remain gated. It also does not authorize immediate accounts, payments, ads, paid services or a broad rewrite. Reassess priorities using the latest repository and deployment state; retain the dated audit below as historical evidence.

This plan reviews the current repository, published data, representative live user journeys, recent workflows and pull requests, the earlier technical audit, and retrieved development decisions. The fixed code/data baseline is commit `cc30f3701996232aa0eecd1b8c4adbf710c84735`, published at 18:22 UTC on 17 September. Its Pages deployment succeeded. Live inspection followed that snapshot; date-sensitive labels can change at midnight IST. No production code, data, deployment, or PR was changed during this review.

**Execution reconciliation, 18 September 2026:** the public field-trust/freshness
omissions in the audit below are historical. #100–#103 established the public
contract and live acceptance; #106 added document-scoped public protection, #108
released source-manifest safeguards, and #109 expanded Teamtech's hold after
source review. Main `dd3a9b42` includes #110's review routing: 390 P4 plus 51
higher-priority records, 1,618 total source findings, 1,614 blocking reviews and
zero unmapped reviews. Adding five P4 rows routes 17 previously unmapped reviews;
missing-field coverage and blocking counts do not improve. Main is live-verified,
including the queue, phase status and completeness script. P4 remains incomplete
and P5 remains gated. #111 corrects the explanation of document conflicts without
accepting replacement figures; #112's generated-output classification is now
verified through an actual `presentation` refresh with source/residual collection
skipped. The latest #104 head and its public-boundary tests are preserved in the
#105 draft. Successful #104/#105 previews remain unaccepted. The #105
draft incorporates #110 at reachable code freeze `409c51c9` with 1,068 frozen
regressions passed. Current draft head `5a63a93d` adds only evidence and docs;
GitHub validation passed 1,068 regressions and browser checks passed 25 journeys
plus responsive text boundaries. Its new source preview remains running and
unaccepted. Complete-PDF execution at the code freeze passed 80 checks and its
independent replay passed 40 audit checks; neither candidate is published. Preserve each
execution's exact lineage and Teamtech's hold. [The retained source review](https://github.com/Vasuki8/IPO-Tracker/blob/5a63a93dd9f782e3bc9ec853c937fb29661108f4/docs/reviews/2026-09-18-source-review/2026-09-18-source-review-409c51c9.md)
binds the full evidence and recovery instructions to that freeze. Structural
checks do not reconcile Teamtech's conflicting units. The commercial goal and unresolved permissions/customer
validation questions remain in force. See [project status](PROJECT_STATUS.md)
and [commercial readiness](COMMERCIAL_READINESS.md).

**The main finding:** the collection and validation foundations have improved considerably, but internal source-review information does not consistently reach the public website. A page can display disputed values and a broad verification label at the same time. Fix that before adding more analytical features.

**What is already working**

| Area | Current implementation | Roadmap implication |
| --- | --- | --- |
| Website | Light indigo/slate dashboard, responsive results, search, filters, sorting, pagination and shareable filter URLs | Improve the existing design incrementally |
| Research journeys | Permanent company profiles, quick view, comparison of two or three issues, calendar, device-local watchlist and CSV export | Extend these features; do not schedule them as new builds |
| Page loading | About 570 KB of directory JSON and compact data embedded in individual profiles; quality reports load on demand | Preserve this separation from the 26.8 MB canonical dataset |
| Validation | Semantic checks, correction history, source evidence, quarantines and real-document regression fixtures | Add public-display checks and expand source coverage |
| Development checks | Committed `uv.lock`, PR validation, read-only source previews and frontend browser CI | Keep these gates; green tests alone do not prove source accuracy |
| Automation | One active data-writing workflow, serialized publication, atomic field groups and retained conflicting proposals | Finish conflict resolution and operational monitoring |
| Repair queue | All 1,351 queued records are retained | The old 300-record truncation is resolved |
| Performance | Final-price and price-history collection code exists behind the P4 gate | Enable and verify it after P4; implementation is ahead of populated coverage |

I ran the current regression suite: **930 tests passed**. Recent frontend CI and deployment checks also succeeded. I directly inspected the directory, company quick views, comparison and calendar. This was not a fresh exhaustive mobile, accessibility, security or market-source audit. [Implementation and operations][readme] [Recent browser CI][browser-ci]

**Current baseline and what the numbers mean**

| Measure | Audited value | Interpretation |
| --- | ---: | --- |
| Stored records | 1,366 | Inventory, not proof of complete or unique Indian equity IPO coverage |
| Higher-priority P0–P3 queue | 53 records | Open, upcoming, recent and filing-pipeline work |
| P4 recent-history queue | 385 records | The total pre-P5 queue is therefore 438 records |
| P5 historical queue | 913 records | Remains gated until P4 closes |
| Automated semantic errors | 0 | Does not establish that every populated value is source-verified |
| Source-review items | 1,619 across 296 records | 1,615 block P4; four belong only to P5 |
| Reviews absent from the missing-field queue | 14 items | Included in the blocking count; they need an actionable review route |
| Final Prospectus revalidation | 1,298 fields across 356 pre-P5 records | 1,187 fields in P4 plus 111 in higher priorities; overlaps other gap counts |
| Retained publication proposals | 441 across 161 issuer IDs | Pending proposals, potentially including superseded work; not 441 confirmed data errors |
| Recent exchange terms | 96.6% presence | Across 443 recent records; a presence score, not a confidence score |
| Offer-document intelligence | 68.1% presence | Across 387 eligible records |
| Use-of-proceeds coverage | 65 / 387 | 322 missing eligible records; source-table repair is a substantial task |
| Financials / promoter holding | 246 / 387; 221 / 387 | Presence only; financial source review remains significant |
| Allotment dates | 0 / 1,323 matured records | A useful lifecycle feature has no populated coverage yet |
| Listed performance | 394 final issue prices; zero price observations or benchmark comparisons | Across 1,287 listed records; a performance product is not yet populated |

These measures have different denominators and overlap. Do not sum field gaps, review items and queued records into a single issue total. The 913 P5 queued records also differ from the 912-record historical exchange completeness cohort because their inclusion rules differ. [Phase status][phase] [Completeness][quality] [Validation][validation] [Queue][queue] [Performance][performance]

**Evidence that changes the priority order**

1. **Public profiles lose important review information.** The compact profile builder carries ordinary exchange-validation status, but omits `staticSourcePolicy`, field provenance and the semantic source-review state. The display therefore cannot reliably distinguish canonical verified figures, provisional disclosures and disputed values. The comparison I inspected showed “Data validation: verified” for issues that still have issue-size review findings. [Profile builder][profiles] [Validation rules][validator]
2. **Conflicting amounts remain visible.** Shakti Polytarp's live quick view displayed ₹26.93 crore total issue size alongside ₹31.77 crore fresh issue and ₹31.77 crore OFS. Its financial table and malformed promoter fragments were also displayed without a specific source-review warning. The validator identifies displayed composition inconsistencies on 16 records. This establishes a display/consistency problem; it does not determine the correct replacement figures without checking the source documents. [Validation findings][validation]
3. **Collection time is presented as source freshness.** Kheria's stored source observation was 20:18 IST, but its quick view displayed 23:14 IST as the latest snapshot and source timestamp. The latter was collection time. The public projection omits the separate observed/collected/time-basis fields already present internally. [Profile builder][profiles] [Subscription renderer][subscriptions]
4. **Known repair work has not reached main.** PR #94 remains open for the Emmvee mixed fresh-issue/OFS seller calculation. The audited main record still contains the older ₹756.138 crore total described in that PR. Finish source acceptance and publication before counting the repair as complete; this review did not independently replay the full Emmvee PDF. [Open repair PR][pr94]
5. **Queue retention is fixed, but queue closure is unfinished.** `pending_updates.json` retains 441 proposals. The publisher appends distinct proposals and preserves accepted data; it does not itself supply a complete resolved/superseded/rejected lifecycle. Fourteen semantic review items are also absent from the missing-field queue. [Publication logic][publisher] [Phase gate][phase-code]
6. **Identity and lifecycle still need targeted attention.** An undated “Century Business Limited” record appears as open alongside a separate dated “CENTURY BUSINESS MEDIA LIMITED” record. This is a review candidate, not sufficient evidence to merge them. Allotment coverage is empty and 37 matured listing dates are missing, including five documented exclusions. [Quality report][quality] [Dataset][dataset]

**Recommended order**

The sequence below is the roadmap order. Existing P0–P5 labels continue to describe the data queue, not new project phases. Effort is relative: small = a contained change, medium = several linked changes, large = repeated source-review batches. External source availability prevents a credible fixed P4 completion date today.

| Order | Priority and result | Main deliverables | Completion check | Effort |
| --- | --- | --- | --- | --- |
| 1 | Immediate: trustworthy public figures | Field/section review states, withheld contradictions, explicit provisional values, accurate timestamp labels | Directory, profiles, comparison and export apply the same display rules | Medium |
| 2 | Immediate: dependable repairs and publication | Complete open repair acceptance, resolve retained conflicts, route all review items, record retry outcomes | Every blocker has an actionable owner/state; accepted repairs reach the live page with matching evidence | Medium |
| 3 | Necessary: complete P4 correctness and coverage | Source-family financial, composition, proceeds, intermediary, identity and term repairs; official document recovery | Existing P4 gate passes without hiding unresolved work or treating source failure as completion | Large |
| 4 | Next: complete daily IPO research | Reliable allotment/listing events, final subscriptions, minimum application terms, Today/This week and watchlist enhancements | Common research questions are answered with dated sources and clear missing states | Medium |
| 5 | After P4: useful performance analysis | Enable existing official-price collector on a recent pilot; listing-day and subsequent returns; matched benchmarks | Source prices, dates and return calculations reconcile on the pilot before expansion | Medium–large |
| 6 | After P4: expand P5 deliberately | Historical cohort reconciliation and evidence-backed backfill in bounded batches | Each cohort has published denominators, source coverage and unresolved reasons | Large |
| 7 | As usage grows: speed, discoverability and maintainability | Payload budgets, targeted frontend cleanup, richer static content, sitemap and social previews | Measured improvements with no regressions in core journeys or source meaning | Medium |
| 8 | Later: optional products | Cross-device accounts, event alerts, richer valuation tools, AI explanations and optional GMP | A demonstrated user need plus the required reliable data and operations | Large / optional |

**1. Make displayed data trustworthy**

Add a compact public quality contract to every summary and profile. Distinguish “Final Prospectus verified”, “Provisional disclosure”, “Under review”, “Awaiting disclosure” and “Source unavailable”. Use short explanations next to affected figures and a source link for details. Avoid a single score or badge implying that an entire company record has been checked.

Hide known conflicting or quarantined amounts from accepted-value tables, comparisons and CSV calculations. Preserve their original values and evidence in the audit trail. An available but unverified disclosure should not silently become a verified number simply because it is populated. For active issues, clearly label permitted RHP/exchange observations as provisional; preserve the agreed Final Prospectus authority for completed static terms.

Carry `subscriptionObservedAt`, `subscriptionCollectedAt`, source authority and time basis through public payloads. Show “Source reported at…” when known and “Checked at…; source time unavailable” otherwise. Label secondary sources visibly, including on mobile. Calculate staleness using the relevant bidding window and source cadence; a later scrape must not make an unchanged observation look newer.

Keep “one lot at cap” as its current clearly defined calculation, then introduce market lot, minimum bid quantity and minimum application amount as separate concepts when supported by issue-specific evidence. Do not infer every issue's minimum application from the displayed lot alone.

Acceptance should include real examples with internally inconsistent amounts, incomplete provenance, missing source time and market-lot/minimum-bid differences. Tests must exercise all four public surfaces: directory, company profile, comparison and CSV.

**2. Make repair work finish reliably**

Complete source review for PR #94 against the current base, then merge and publish its source-backed data correction when accepted. Check the deployed Emmvee profile; a merged parser alone is not a completed repair. Apply the same code → reviewed data → generated pages → deployed result check to later fixes.

Triage retained publication proposals into still-actionable conflicts, already-applied proposals, superseded observations, rejected proposals and retryable collections. Preserve an audit record of the resolution. Do not resolve conflicts by automatically choosing the newest writer. Start with document-field and live-subscription proposals because they affect visible research and freshness.

Unify semantic review and missing-field work so the 14 unmapped items cannot block P4 indefinitely without appearing in a repair view. Include last attempt, result, source/parser version and next eligible attempt. Source-unavailable, missing final filing, unsupported layout and contradictory source content need different actions. Prioritize currently open/upcoming issues while aging older unresolved items into service.

Add a small operational status report for last successful source observation, last accepted publication, overdue collection, oldest unresolved work and backlog changes by cause. The existing source-health and stage-outcome mechanisms are useful foundations. A successful workflow exit is not sufficient evidence that every feed is fresh. Keep monitoring focused on actual source/publication failures.

**3. Close P4 using source evidence**

Work from the real denominator: 53 higher-priority records plus 385 P4 records, with source reviews considered separately. The closeout is substantially larger than the earlier “remaining lot sizes” task.

Prioritize in this order:

1. Current and upcoming issue terms, missing subscription categories and visible amount conflicts.
2. High-reuse financial layouts: the current review report contains 1,299 financial findings, including 702 conflicting-table findings and 570 missing source-period evidence findings. These are findings, not necessarily separate incorrect cells or issuers.
3. Issue composition and seller aggregation, then use-of-proceeds tables. The latter has 322 eligible missing records and 195 explicit quarantine review items; these counts overlap.
4. Promoter, intermediary and shareholding evidence; finish unsupported layouts by shared document family rather than isolated patches where possible.
5. Document discovery/recovery and identity/lifecycle review. Revisit current evidence for Sunshine and Optivalue instead of repeating an old “blocked” classification: Sunshine now has accepted issuer-hosted evidence for several fields but still has unresolved proceeds/shareholding work.

Every accepted repair should retain document identity, URL/hash, page/row, unit, period or issue date, and parser/review version as applicable. Use complete real-document fixtures and review before/after outputs. Fail closed on conflicting issuer identities or ambiguous columns. Source failure should remain retryable or explicitly unresolved; it is not an availability exclusion by itself.

The existing completion gate requires no actionable P0–P4 rows, no semantic errors and no blocking source-review items. P5-only review work must remain separated, and unmapped reviews must be routed rather than dropped. Preserve evidence-backed exclusions. Produce the closeout report from the exact published dataset, not from a successful preview artifact. [Gate implementation][phase-code]

Keep a milestone snapshot and a separate count of new incoming issues so genuine repair progress remains visible while the rolling two-year queue changes. This reporting improvement must not relax the runtime gate.

**4. Improve the daily research experience**

Build on the existing calendar, comparison and watchlist. The most useful additions are:

- A Today/This week view for openings, closings and listings, with source-backed dates and direct company links.
- Allotment and listing milestones, clearly separating an expected date from a confirmed event. Start with recent issues; historical completeness can follow later.
- A final subscription capture/reconciliation after bidding closes, so the last intraday snapshot is not mistaken for the official final figure.
- An application amount calculator using verified lot/minimum-bid terms and disclosed prices, without implying allocation probability.
- Watchlist notes/tags, local export/import and calendar-file export before introducing account infrastructure.
- Comparison improvements for like-for-like fiscal periods, financial reporting scope, source date and verification state. Add financial ratios only when their inputs are comparable and validated.
- Clear empty states explaining whether information is undisclosed, temporarily unavailable or under review, plus a glossary for terms such as QIB, OFS and price band.

Preserve keyboard navigation, focus behavior, mobile cards and contrast. Re-run existing browser checks for changed journeys; add a new case only for a meaningful uncovered behavior. Safe navigation and presentation work can proceed alongside P4 repair once the public quality contract is in place. It must not take priority over visible incorrect figures.

**5–6. Expand performance and P5 after the gate passes**

Start performance with a bounded recent cohort. Require a confirmed final issue price, actual listing-day opening/closing observations, subsequent dated prices and a matching benchmark series. Distinguish issue-to-listing gain, return since issue and return since listing. Explain the calculation basis beside the chart. Existing code uses unadjusted price returns; splits, dividends and other corporate actions require additional data before adjusted-return claims.

Scale from listing day to one-week, one-month and longer horizons only as complete observations become available. Show missing coverage instead of filling charts with inferred prices. The existing collectors and validation code should be extended, not rewritten.

Run P5 in bounded cohorts, with the recent historical boundary first and older cohorts afterward. Reconcile the intended universe against official issue registers and review legacy non-equity rows, auxiliary events, renamed issuers and possible duplicates. Publish coverage by year, board and field with explicit denominators. Preserve nulls and evidence for every backfilled figure.

Performance and P5 can proceed as separate workstreams after P4 closes. Performance need not wait for all 913 historical queued records to finish. Neither should delay live-source maintenance.

**7–8. Improvements that can wait**

| Later improvement | Why it waits | Trigger to start |
| --- | --- | --- |
| Broader SEO | Titles, descriptions, canonical links and some social metadata already exist; sitemap and richer static page content remain opportunities | Data-display rules are reliable and public discovery is a goal |
| Further payload optimization | The normal directory already avoids the 26.8 MB master file | Measured slow-load cases, growing payloads or repeated compatibility fallback |
| Frontend module cleanup | Script layers still wrap shared renderers; this increases maintenance cost, but the current site works | Touch the affected boundary during planned features, with existing browser checks |
| More parser/adapter cleanup | There is a supported entrypoint and compatibility wrappers already | A repeated defect or expensive change justifies consolidation |
| Cross-device accounts | Watchlists already work locally; accounts add authentication, storage and privacy obligations | Real demand for syncing notes and saved issues |
| Email/push alerts | Delivery is only useful when dates, freshness and deduplication are reliable | Event collection and final subscription reconciliation have proven dependable |
| Rich valuation/sector analysis | Depends on validated financial periods, reporting scope and comparables | Financial source review has sufficient coverage |
| AI summaries or questions | They would otherwise amplify unresolved source errors | Answers can cite validated fields and documents and state missing coverage |
| Optional GMP | It is unofficial and should not contaminate official issue research | Explicit demand, reliable timestamped provenance and visually separate presentation |
| Framework/database/hosting migration | Current static delivery fits the core product | A concrete requirement such as account sync or measured scale limits |

Keep routine dependency updates, link handling, escaping and test maintenance ongoing. This review did not establish a security incident or justify a broad rewrite.

**The next ten implementation tickets, in order**

| Ticket | Concrete outcome | Dependency |
| --- | --- | --- |
| 1 | Publish compact field/section verification and review states | None |
| 2 | Withhold disputed display values consistently in profiles, comparison and exports | Ticket 1 |
| 3 | Preserve and label source observation versus collection time | Ticket 1; can accompany ticket 2 |
| 4 | Complete current-base source acceptance and deployed data correction for PR #94 | Existing source-preview gate |
| 5 | Triage the 441 retained proposals and implement auditable resolution states | Existing atomic publication rules |
| 6 | Route all 14 unmapped review items into operational work | Existing validation and queue reports |
| 7 | Repair the highest-impact current/upcoming term and subscription gaps; review Century identity | Tickets 1–3; source evidence |
| 8 | Repair the next high-reuse financial/proceeds layouts with real-document acceptance | Tickets 4–6 |
| 9 | Add progress/freshness reporting and a published P4 completion checklist | Queue and source-health evidence |
| 10 | Deliver the first lifecycle/Today/This week improvement on reliable dates | Public quality contract and validated event inputs |

Treat these as reviewable deliveries, not a promise that ten commits will close P4. Tickets 7–8 repeat in bounded evidence-backed batches until the gate passes.

Track five primary measures: visible disputed values, blocking source-review items, P0–P4 actionable records, age of unresolved publication proposals, and freshness/authority coverage for active issues. After P4, add historical cohort coverage and price/benchmark coverage. Record new incoming work separately from resolved work; a growing denominator should not hide successful repairs.

**Review limits.** Current code and dataset evidence take precedence over earlier chat completion claims. Full transcripts of every project conversation were not available. This review did not verify every original PDF, independently reconcile the complete Indian IPO universe, reproduce all frontend CI cases locally, or measure real-user performance. Source-review findings indicate work requiring investigation; they are not automatically confirmed errors. The proposed roadmap is based on the inspected snapshot and should be refreshed when the currently open source-repair work is published.

[readme]: https://github.com/Vasuki8/IPO-Tracker/blob/cc30f3701996232aa0eecd1b8c4adbf710c84735/README.md
[quality]: https://github.com/Vasuki8/IPO-Tracker/blob/cc30f3701996232aa0eecd1b8c4adbf710c84735/docs/DATA_QUALITY.md
[phase]: https://github.com/Vasuki8/IPO-Tracker/blob/cc30f3701996232aa0eecd1b8c4adbf710c84735/data/phase_status.json
[phase-code]: https://github.com/Vasuki8/IPO-Tracker/blob/cc30f3701996232aa0eecd1b8c4adbf710c84735/scripts/phase_status.py
[validation]: https://github.com/Vasuki8/IPO-Tracker/blob/cc30f3701996232aa0eecd1b8c4adbf710c84735/data/validation.json
[validator]: https://github.com/Vasuki8/IPO-Tracker/blob/cc30f3701996232aa0eecd1b8c4adbf710c84735/scripts/validate_data.py
[queue]: https://github.com/Vasuki8/IPO-Tracker/blob/cc30f3701996232aa0eecd1b8c4adbf710c84735/data/missing_queue.json
[performance]: https://github.com/Vasuki8/IPO-Tracker/blob/cc30f3701996232aa0eecd1b8c4adbf710c84735/data/performance_summary.json
[dataset]: https://github.com/Vasuki8/IPO-Tracker/blob/cc30f3701996232aa0eecd1b8c4adbf710c84735/data/ipos.json
[profiles]: https://github.com/Vasuki8/IPO-Tracker/blob/cc30f3701996232aa0eecd1b8c4adbf710c84735/scripts/build_company_pages.py
[subscriptions]: https://github.com/Vasuki8/IPO-Tracker/blob/cc30f3701996232aa0eecd1b8c4adbf710c84735/phase4.js
[publisher]: https://github.com/Vasuki8/IPO-Tracker/blob/cc30f3701996232aa0eecd1b8c4adbf710c84735/scripts/publish_transaction.py
[pr94]: https://github.com/Vasuki8/IPO-Tracker/pull/94
[browser-ci]: https://github.com/Vasuki8/IPO-Tracker/actions/runs/35257524416
