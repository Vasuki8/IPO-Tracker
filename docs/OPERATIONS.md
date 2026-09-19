# IPO data operations

## Supported entrypoints

Use Python 3.12 and the committed `uv.lock`: `uv sync --frozen`. Linux production runners install `poppler-utils` for bounded, fixed-pitch PDF table extraction. Install Poppler locally before running PDF collection; unsupported extraction environments fail explicitly instead of changing table layout.

Run `uv run --frozen python scripts/run_pipeline.py --mode MODE` with one of:

| Mode | Work |
| --- | --- |
| `core` | Current exchange data, recent SEBI discovery, then repair high-priority filing gaps |
| `subscriptions` | Open-issue demand snapshots with source labels |
| `filings` | P0–P3 document discovery and offer-term maintenance |
| `repair` | Apply the correction registry and revalidate document-derived fields |
| `p4` | Recent SEBI Other Documents, NSE bid lots, and BSE recent-history backfill |
| `p5` | Bounded historical expansion, enabled only after P4's correctness gate passes |
| `performance` | Official price observations, enabled only after P4's gate passes |
| `maintenance` | Document maintenance, P4 closeout, then gated P5 and performance |

Every mode rebuilds completeness, the complete missing-field queue, semantic validation, and phase status. A zero exit from a source wrapper does not by itself establish source success: inspect `meta.pipelineStages`, record attempt outcomes, and `data/validation.json`.

The pipeline has a 60-minute total collection budget (`--budget-minutes`, capped at 65). Each stage receives at most the remaining budget. Later stages become `deferred` when time runs out; completed atomic collector checkpoints remain available for validation and publication within the 75-minute workflow limit. Deferral leaves missing fields on the queue.

## Scheduling and publication

Use the offline [recorded update-health report](UPDATE_HEALTH.md) to join existing
source checks, stage outcomes, publication metadata, proposal reconciliation and
review queues at an explicit assessment time. It prints JSON or Markdown and
never writes accepted data. Unknown source observations, failed/deferred attempts,
unavailable sources, unresolved proposals and publication delay are separate
signals. The [18 September snapshot](audits/operational-health/2026-09-18/REPORT.md)
retains the real evidence and its limitations; regenerate before acting on it.

`refresh.yml` is the only active data writer. Core collection runs hourly; subscriptions run twice hourly during the configured weekday UTC window. Filing maintenance follows core collection when P0–P3 gaps exist, with a six-hour fallback. Daily maintenance runs at 13:43 UTC. GitHub schedules are best-effort; missed triggers are not evidence of fresh data.

Core NSE live/history, SEBI and BSE health now records future completed collection
attempts in `meta.sourceHealth`: endpoint/page/date-range receipts, `checkedAt`,
row counts and failure reasons. The aggregate check clock is the last actual
attempt, not the dataset build, publication or source observation. No older check
or observation time is reconstructed. A successful empty NSE response means
checked with zero rows; an unsupported response or unparsed SEBI/BSE page remains
a failure, not proof that a disclosure is absent. Partial success retains failed
siblings. An explicit skip has `status: deferred`, no new check clock and the
previous real outcome under `lastAttempt`; repeating a skip does not nest history.

When no rows arrive, the existing collector retains new diagnostics alongside the
unchanged accepted rows and metadata. It returns failure if attempted collection
failed, and success for valid empty checks. Attachment failures discard that
source's incomplete changes. Reviewed universe identity source/observation URLs
bound to `universeAdmission.identitySource` survive core cleanup even when BSE's
current-page request fails or the issuer no longer appears there. Stage time-budget
deferrals do not run the collector
and cannot mint source checks. Source clocks still cannot establish field accuracy.
Each source-health or stage entry merges as a whole: concurrent attempts cannot combine
one outcome with another attempt's clock or receipts. The existing metadata
conflict policy retains the accepted entry; other sources merge independently.
Narrow core collector/transport pushes select the existing `core` workflow, including
its conditional bounded filing maintenance; mixed parser/policy/dependency changes
retain the ordinary repair route. Inspect the resulting canonical/proposal diff.
The source-preview workflow maps a core-only PR to its existing retained-data
validation path. Core requests run at release; a metadata/identity change must not
fall through the old non-review branch into unrelated financial or market-history
collection. Mixed parser changes keep their full source preview.

Collectors have read-only repository permissions. They retain a baseline, proposed dataset and tested source commit in a 14-day Actions artifact. Publication runs only from `main`, serializes in one queue, tests current main, and checks that the collector's scripts, locked dependencies and reviewed-correction registry are still current. A supplied collector manifest must contain a valid ancestor commit; missing, empty or malformed manifests fail before any data writes. See `PUBLICATION_SOURCE_GUARD.md` for recovery. A three-way merge preserves unrelated updates. Document values and their evidence, and subscription values and their source/timestamps, merge as atomic groups.

The core NSE current/upcoming/history feed does not own accepted subscription
snapshots. Its multiples and raw share inputs stay in
`observations.NSE.subscriptionSummary`, with endpoint/issuer/offer identity,
collection time, unknown observation time and an unverified denominator. Core
merging preserves the complete accepted subscription family and history, including
absence. The dedicated detail collector's existing complete-response rules govern
accepted updates. Historical mixed snapshots require source reconciliation or an
explicit review hold; this boundary does not backfill them. See
[the core subscription review](reviews/2026-09-18-core-subscription-boundary.md).

NSE detail collection requires the board-compatible API route (`SME` for SME,
`EQ` for mainboard), exact issuer/symbol/offer dates, a reported category multiple,
positive offered shares and matching bid arithmetic. Conflicting duplicate
headline counts reject the response even when one row lacks a multiple. Counts-only
tables, graph headlines and zero-denominator placeholders cannot supply missing
subscription values. Rejection preserves the accepted snapshot and its hold;
another source still needs the existing complete-response checks. API routing is
distinct from a security's trading-series label. The
[SpectraA evidence review](reviews/2026-09-18-spectraa-nse-detail-evidence.md)
records why its official response does not yet resolve its historical hold.

Conflicting proposals are retained in `data/pending_updates.json`; accepted values are preserved. `documentFields` and `subscriptionSnapshot` in a pending path name the atomic groups defined in `publish_transaction.py`. Review source evidence, then update or recollect the affected group. There is no automatic last-writer-wins conflict resolution. Failed publications retain their original collection artifact; rerun a failed publisher only when its code is still current, otherwise recollect on current main. Publication requests a Pages rebuild explicitly after a bot commit.

`priceSnapshot` keeps listing prices, final-price evidence, observations and calculated returns together. If another collection changed any of those fields, the competing snapshot stays pending rather than mixing one baseline with another return.

Listing dates and their evidence also belong to `priceSnapshot`. `lotTerms` keeps the bid lot, market lot, minimum application quantity, and retained lot evidence together so conflicting collectors cannot attach one filing's evidence to another value.

Exchange-comparison `validation` is regenerated from accepted observations and source records when those inputs change. Concurrent validation timestamps do not create pending source conflicts; competing underlying observations still do.

Previous ad-hoc writing workflows are retained under `.github/retired-workflows` for reference. They do not execute. Legacy parser entrypoints remain for regression compatibility; scheduled document extraction uses `run_offer_documents.py` and the isolated `offer_parser.py` API.

## Correctness and repairs

`data/verified_corrections.json` records exact prior-value hashes and replacement fields. Corrections apply atomically per issuer only while all preconditions still match, so a later concurrent correction is preserved. The initial batch uses source-linked PDFs and the current parser's table/role rules. `dataCorrections` retains before/after values and reasons; `documentFieldProvenance` retains the document hash, URL, page, original row/header, unit, and normalized numeric value.

Unsupported financial and intermediary layouts retain prior disclosures and create source-review items. Objects of issue follow the stricter source-table evidence gate below. Mixed interim/annual columns are not silently relabelled as fiscal years. Conflicting numeric disclosures are excluded from the accepted extraction. A PDF fetch failure preserves existing data and records its cause. Both primary and issuer document runners write atomic checkpoints after completed attempts, including matching source proofs, extraction metadata and current health, so a later timeout retains completed work. A checkpoint failure stops the stage instead of being mislabeled as a source error.

Final Prospectus downloads validate the PDF container and page tree before caching or reusing bytes. An unreadable cached document is discarded and fetched again within the existing retry, time and size limits. Cache files become visible only after a complete, validated download is written and atomically renamed. Non-strict PDF recovery remains allowed; this check does not verify every content stream or source value. `--cached-only` never downloads: missing or unreadable cached PDFs are reported without a network request.

Verified issuer-hosted Final Prospectus replacements are recorded in `issuer_offer_registry.py` with an exact host, filing date and source page. The issuer runner checks the record identity and opening-page company name before applying canonical field policy. A changed registry URL is eligible even when the previous URL failed or an older document was already extracted. Source previews also run when this registry changes and inspect up to 30 issuer fallbacks, matching the production cap, so previously failed sources remain within the preview batch.

Source preview saves its final queue and complete validation report before printing optional PDF excerpts. Those diagnostics convert only the first 45 pages and stop after the three excerpts that appear in the log; canonical extraction retains its 520-page cap. The review job allows 50 minutes for the 30-document, 30-issuer, 100-document review and 30-document residual stages, including reporting and artifact upload. Strict validation remains required.

Objects-of-issue validation rejects recognizable bid-lot and trading-lot definitions whose share counts were mistaken for monetary allocations. Enforcement withdraws such existing rows and their canonical proof, preserves the original value and evidence in the audit snapshot, and returns the field to Final Prospectus revalidation. A valid allocation table can resolve the quarantine; the lot-size field is preserved.

An explicit issuer heading beside a cover identity or registered-office label must match the target record. A conflicting cover issuer blocks primary and residual extraction even when an official filing's metadata or an incidental body mention matches the target. When no clear cover identity is readable, the existing text and official-metadata checks still apply. Reviewed identity corrections use exact issuer, offer and prior-value preconditions to clear contaminated fields and matching evidence while retaining their audit history. Source previews apply the correction registry before collection, matching production.

Final Prospectus promoter names come from bounded, explicitly headed lists in the opening pages. Accepted lists retain their page, original rows and complete legal names; selling-shareholder definitions cannot supply the promoter group. Conflicting accepted lists remain unresolved, and residual repairs preserve the final parser's accepted or unresolved decision. Parser 29 schedules source re-extraction for this change.

The final parser recognizes bidding ranges in definitions that place the minimum and maximum prices before parenthetic Floor Price and Cap Price labels, including an optional `i.e.,` prefix. Both labelled values must belong to the same definition, and conflicting explicit ranges remain unresolved. This allows an evidenced bidding range to replace an older one-point band while keeping the final issue price separate.

The reviewed Priority Jewels correction quarantines its unverified financial table after confirming that 19 of 21 cells contradict its matching Final Prospectus. The record retains the old values and source review in `dataCorrections`; `offer.financials` remains queued. Restoration requires annual columns, correct units, the per-year standalone or consolidated scope, and the disclosed EPS basis. The correction replaces an obsolete registry group without overwriting newer intermediary or document evidence, and refuses to overwrite a financial value changed since the review.

Final Prospectus issue composition is extracted from bounded offer clauses with page and row evidence. The parser checks fresh issue plus offer for sale against the total, and share counts against an explicitly stated final issue price when uniform valuation is supported. An individual selling shareholder's quantity cannot stand in for the entire offer for sale, and neither a price-band cap nor a historical transaction price can value the final issue. Discounted offers retain explicitly disclosed amounts; missing amounts are not inferred at the headline price. Contradictory clauses require review.

Parser 30 also recognizes an initial offer whose quoted aggregate is immediately followed by an explicit definition of the entire offer as an offer for sale. The whole-offer alias may precede `THROUGH AN OFFER FOR SALE` or immediately follow it. The attached seller quantities must corroborate the initial total, which supplies the canonical OFS shares and quoted amount. Disclosed seller aggregates must remain consistent with that total, allowing the existing rounding tolerance. Mixed fresh-issue language remains unresolved; explicit nil or not-applicable clauses remain compatible. Reservation and subscription clauses do not supply seller quantities, and the parser retains the quoted aggregate at its disclosed precision without inferring employee allotments or discount-adjusted proceeds.

Previously verified issue amounts that contradict their own counts or totals are quarantined during policy enforcement. Their original values and source evidence remain in `dataCorrections` and the `issueCompositionReview` snapshot; the affected amounts become null until a valid source repair supplies them. Quarantined fields remain in the Final Prospectus queue even while null. Partial repairs resolve only the fields actually recovered. Legacy mixed-source disagreements remain visible as review items. Publication keeps issue amounts, document evidence and quarantine state in one atomic group.

Objects of issue require an observed allocation table in a Final Prospectus. Parser 31 and residual adapter 4 retain the actual heading, PDF pages, explicit monetary unit, physical column headers and exact purpose/amount spans, including wrapped purposes. The supported family has one purpose column and one allocation-amount column, optionally followed by an explicitly labelled percentage column. Aligned purpose fragments such as `purposes*` remain part of their row. An isolated footnote marker or a repeated column header does not prove that the preceding table is complete; those ambiguous prefixes remain unresolved. Totals and subsequent deployment, financing and narrative sections close the table; conflicting candidates, missing units and unexplained columns remain unresolved. Each canonical amount must equal its source token converted to crore.

Enforcement rechecks old objects against this source-table contract. Missing legacy raw evidence is labelled `source-evidence-required`, separately from structurally invalid rows; both are withheld while the original values, source proof, document metadata and extraction envelopes are preserved in `dataCorrections` and `objectsOfIssueReview`. Old verification labels cannot restore them. Complete document-level evidence may migrate only when its source URL and SHA match the field's source. Repeated enforcement keeps the same audit snapshot, and a supported replacement resolves the review without deleting that history. Values, evidence and review state publish together; withheld objects remain actionable in P4.

`completeness.json` measures field presence. `validation.json` separately reports invalid values and disclosures needing source review. A populated field is not automatically correct. `phase_status.json` keeps P4 incomplete and P5 gated while actionable P0–P4 gaps, semantic errors or unresolved source-review items remain. Documented availability exclusions remain visible as raw missing fields; source failure alone must not be converted into a completed task.

## Subscription and performance semantics

NSE and BSE remain the preferred subscription sources. Existing Groww and IPO Dhamaka fallback collectors retain explicit secondary-source/degraded labels. `subscriptionAsOf` is a compatibility collection timestamp, not necessarily the exchange's observation time. `subscriptionObservedAt` is null unless the collector supplies the actual source time.

Performance observations require an exact NSE symbol, a positive price and an official observation timestamp. Final issue prices come from `listing.issuePrice`; a price-band cap is not assumed to be the final price. Later opening prices cannot become listing-day prices. Returns are explicitly unadjusted price returns excluding dividends and corporate-action adjustments. Benchmark excess returns remain null until source-linked baselines and observations have matching dates. Historical price coverage is incomplete until an official historical source has been collected.

## Verification

Run `uv run --frozen python -m unittest discover -s tests -q`, then use `uv run --frozen python` to run `scripts/apply_corrections.py`, `scripts/enforce_final_prospectus_policy.py` and `scripts/validate_data.py --strict` in that order. Policy enforcement first migrates unsupported legacy objects into an auditable review state. Regression tests cover source year alignment, footnotes, negative/missing cells, unsupported/interim layouts, intermediary contacts and former names, concurrent publication, complete queues, migration preconditions and performance-date/identity rules.

## Final issue prices and historical observations

`collect_final_issue_prices.py` reads the explicit Issue_Price field in official NSE monthly workbooks. It requires the same canonical issuer, exact issue opening date, compatible symbol and closing date, and a price consistent with any established band. It persists the final value with the report URL, document hash and matched issuer/date. Already reviewed NSE listing-circular observations can supply the same baseline. Conflicting dates or prices remain unresolved.

Repair mode processes up to 100 documents per run and collects recent final-price baselines. P5 also uses the NSE monthly archive after the P4 gate passes, supplementing the BSE historical source. All source stages retain bounded budgets.

`collect_price_history.py` reads official dated NSE daily equity and index CSV reports, collecting the listing-day open and close plus subsequent daily closes. Date-only reports retain date precision. NIFTY 50 excess returns compare listing-day close with a matching later close; a later daily open cannot become the listing price. This collector runs in the existing performance phase after P4 passes. Unadjusted returns do not account for splits, dividends or other corporate actions.

Historical rows remain in the observation history even when a newer observation arrived first. An official daily close supersedes an intraday quote for the same date; collecting either again does not duplicate it. Later quotes clear close-based benchmark comparisons until a matching equity close is available. Final issue prices arriving after observations refresh the existing returns immediately.

Missing index baselines are retried even when the listing-day equity close is already present. Empty or wrong-date responses are not retained as valid cached reports. Conflicting listing-day prices preserve the accepted value and its source, retain the proposed report in `listing.priceConflicts`, and keep a review item visible. Semantic validation checks observations and return calculations before publication.

`source-review.yml` is a read-only preview for parser changes. It runs the full test suite, applies source repairs to an ephemeral dataset, and retains proposed values and validation findings as an artifact. It watches the primary parser, residual layouts and shared objects checks. The final review processes up to 100 primary documents and 30 residual documents, deriving residual order from the updated queue and reusing the PDF cache. It saves the final repair queue and complete report after both stages and final policy enforcement, before bounded optional diagnostics. It cannot publish data. Review the source results before merging parser changes.

## Source-review work in the queue

The missing-data queue now also retains semantic source reviews, including otherwise complete financial tables with individual conflicting metrics. Use `source_review_queue.expand_review_items(row, queue["sourceReviewDefinitions"])` to inspect exact fields, reasons, source pointers and next actions. Source-review counts are distinct from missing-field coverage and remain actionable even when an unrelated missing field has an availability resolution. Queue rows in Data & sources show both counts.

The strict Final Prospectus runners consume `source_review_queue.actionable_gaps` so supported review tasks can enter their existing source paths. Parser-version, source-identity and retry bounds are unchanged: an unchanged document already attempted by the current parser stays available for manual source review, rather than being downloaded on every run. Listing/date conflicts require issue-specific official exchange evidence; unknown fields require operator triage. Legacy RHP/DRHP fallback scripts receive no new review routes. Routing a review does not resolve it, change canonical values, or open P5 while P4 remains blocked.

## NSE issuer filing register

`collect_nse_offer_filings.py` reads the official SME and equity offer registers and their linked final-listing XBRL documents. Matching requires the canonical issuer, exact opening date, compatible closing date, and independently matching symbol or ISIN. The collector rejects inconsistent identities, conflicting filings, wrong XML units, undated/future listings, and non-official links. It fills missing issue lots and listing dates and reads the explicit `FinalIssuePrice`; existing conflicting values are preserved. Each accepted value retains the document hash, source field, issuer, and issue dates.

Repair, maintenance, and P4 collect up to 150 candidate records and discover at most five issuers' RHP/final PDF documents per run. Completed records checkpoint independently while other downloads continue. The register fingerprint and a seven-day retry interval avoid repeating unchanged source attempts. Newly discovered documents still undergo the parser's opening-page issuer check. P5 uses the same register for older issues only after the correctness gate passes.

Parser 22 supports selected-financial-information headings, staggered annual dates, explicit lakh and `₹ Mn` units, and standalone/consolidated scope changes inside shared or continued tables. Financial fixtures retain original PDF spacing and actual disclosed numeric rows.

## Reviewed active offer terms

`activeOfferTerms` holds separately reviewed provisional disclosures for the exact
issuer, board and offer window. `active_offer_terms.py` replays retained NSE
`issueInfo.dataList` bytes, SHA256 and row locators. It accepts explicit price
bands, bid lots, separately labelled minimum quantities and supported fresh/OFS
composition; it never calculates a total issue amount from shares and a cap price.
Composition keeps explicit `up_to` qualifications and undisclosed legs stay null.
The response has no observation timestamp, so `observedAt` stays null while
collection and review clocks remain distinct.

New receipts use `kind: active-offer-terms` in the existing reviewed evidence
registry and an `explicit-reviewed` correction. Deploy support/evidence first,
then submit only `data/reviewed_publication_request.json` on a separate PR. Ordinary
scheduled apply is inert. Preparation verifies source-byte replay, before-value
preconditions, exact public values and source review. The existing publisher
merges the entire receipt atomically and appends source/correction history;
canonical static fields, Final Prospectus proofs and static policy are untouched.

Public projection and active completeness use the same reviewed eligibility
rules. Existing holds win. Conflicting same-offer NSE/BSE evidence stays a manual
review with pointers to the receipt and observations. Disclosures expire after
the close date in IST, including cached browser output; closed/withdrawn/cancelled
or mismatched offers do not qualify. Expiry restores missing-field work rather
than promoting provisional terms to final facts. Source recovery and conditional
floor/cap amount layouts remain separate work, not availability exclusions.

For a reproducible historical browser rehearsal, use
`uv run --frozen python tests/prepare_active_offer_site.py --output <new-directory>`
and serve that isolated directory for `tests/frontend_active_offer_terms.cjs`.
The test fixes its issue-date clock; production and reviewed publication always
use the real clock. See the [three-issuer source review](reviews/2026-09-19-active-offer-source-review.md).

The read-only public release verifier replays the accepted receipt against its
retained proof and Git blob identity, then checks exact provisional values,
qualifications, source clocks and expiry in public files. After expiry it accepts
properly withheld regenerated fields; it never promotes active terms to Final facts.
