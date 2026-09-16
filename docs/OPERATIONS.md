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

`refresh.yml` is the only active data writer. Core collection runs hourly; subscriptions run twice hourly during the configured weekday UTC window. Filing maintenance follows core collection when P0–P3 gaps exist, with a six-hour fallback. Daily maintenance runs at 13:43 UTC. GitHub schedules are best-effort; missed triggers are not evidence of fresh data.

Collectors have read-only repository permissions. They retain a baseline, proposed dataset and tested source commit in a 14-day Actions artifact. Publication runs only from `main`, serializes in one queue, tests current main, and checks that the collector's source code is still current. A three-way merge preserves unrelated updates. Document values and their evidence, and subscription values and their source/timestamps, merge as atomic groups.

Conflicting proposals are retained in `data/pending_updates.json`; accepted values are preserved. `documentFields` and `subscriptionSnapshot` in a pending path name the atomic groups defined in `publish_transaction.py`. Review source evidence, then update or recollect the affected group. There is no automatic last-writer-wins conflict resolution. Failed publications retain their original collection artifact; rerun a failed publisher only when its code is still current, otherwise recollect on current main. Publication requests a Pages rebuild explicitly after a bot commit.

`priceSnapshot` keeps listing prices, final-price evidence, observations and calculated returns together. If another collection changed any of those fields, the competing snapshot stays pending rather than mixing one baseline with another return.

Listing dates and their evidence also belong to `priceSnapshot`. `lotTerms` keeps the bid lot, market lot, minimum application quantity, and retained lot evidence together so conflicting collectors cannot attach one filing's evidence to another value.

Exchange-comparison `validation` is regenerated from accepted observations and source records when those inputs change. Concurrent validation timestamps do not create pending source conflicts; competing underlying observations still do.

Previous ad-hoc writing workflows are retained under `.github/retired-workflows` for reference. They do not execute. Legacy parser entrypoints remain for regression compatibility; scheduled document extraction uses `run_offer_documents.py` and the isolated `offer_parser.py` API.

## Correctness and repairs

`data/verified_corrections.json` records exact prior-value hashes and replacement fields. Corrections apply atomically per issuer only while all preconditions still match, so a later concurrent correction is preserved. The initial batch uses source-linked PDFs and the current parser's table/role rules. `dataCorrections` retains before/after values and reasons; `documentFieldProvenance` retains the document hash, URL, page, original row/header, unit, and normalized numeric value.

Unsupported layouts retain prior disclosures and create source-review items. Mixed interim/annual columns are not silently relabelled as fiscal years. Conflicting numeric disclosures are excluded from the accepted extraction. A PDF fetch failure preserves existing data and records its cause. The extractor writes an atomic checkpoint after each document; a timeout can therefore retain completed work.

`completeness.json` measures field presence. `validation.json` separately reports invalid values and disclosures needing source review. A populated field is not automatically correct. `phase_status.json` keeps P4 incomplete and P5 gated while actionable P0–P4 gaps, semantic errors or unresolved source-review items remain. Documented availability exclusions remain visible as raw missing fields; source failure alone must not be converted into a completed task.

## Subscription and performance semantics

NSE and BSE remain the preferred subscription sources. Existing Groww and IPO Dhamaka fallback collectors retain explicit secondary-source/degraded labels. `subscriptionAsOf` is a compatibility collection timestamp, not necessarily the exchange's observation time. `subscriptionObservedAt` is null unless the collector supplies the actual source time.

Performance observations require an exact NSE symbol, a positive price and an official observation timestamp. Final issue prices come from `listing.issuePrice`; a price-band cap is not assumed to be the final price. Later opening prices cannot become listing-day prices. Returns are explicitly unadjusted price returns excluding dividends and corporate-action adjustments. Benchmark excess returns remain null until source-linked baselines and observations have matching dates. Historical price coverage is incomplete until an official historical source has been collected.

## Verification

Run `uv run --frozen python -m unittest discover -s tests -q`, then apply the correction registry and run `scripts/validate_data.py --strict`. Regression tests cover source year alignment, footnotes, negative/missing cells, unsupported/interim layouts, intermediary contacts and former names, concurrent publication, complete queues, migration preconditions and performance-date/identity rules.

## Final issue prices and historical observations

`collect_final_issue_prices.py` reads the explicit Issue_Price field in official NSE monthly workbooks. It requires the same canonical issuer, exact issue opening date, compatible symbol and closing date, and a price consistent with any established band. It persists the final value with the report URL, document hash and matched issuer/date. Already reviewed NSE listing-circular observations can supply the same baseline. Conflicting dates or prices remain unresolved.

Repair mode processes up to 100 documents per run and collects recent final-price baselines. P5 also uses the NSE monthly archive after the P4 gate passes, supplementing the BSE historical source. All source stages retain bounded budgets.

`collect_price_history.py` reads official dated NSE daily equity and index CSV reports, collecting the listing-day open and close plus subsequent daily closes. Date-only reports retain date precision. NIFTY 50 excess returns compare listing-day close with a matching later close; a later daily open cannot become the listing price. This collector runs in the existing performance phase after P4 passes. Unadjusted returns do not account for splits, dividends or other corporate actions.

Historical rows remain in the observation history even when a newer observation arrived first. An official daily close supersedes an intraday quote for the same date; collecting either again does not duplicate it. Later quotes clear close-based benchmark comparisons until a matching equity close is available. Final issue prices arriving after observations refresh the existing returns immediately.

Missing index baselines are retried even when the listing-day equity close is already present. Empty or wrong-date responses are not retained as valid cached reports. Conflicting listing-day prices preserve the accepted value and its source, retain the proposed report in `listing.priceConflicts`, and keep a review item visible. Semantic validation checks observations and return calculations before publication.

`source-review.yml` is a read-only preview for parser changes. It runs the full test suite, applies source repairs to an ephemeral dataset, and retains proposed values and validation findings as an artifact. It cannot publish data. Review the source results before merging parser changes.

## NSE issuer filing register

`collect_nse_offer_filings.py` reads the official SME and equity offer registers and their linked final-listing XBRL documents. Matching requires the canonical issuer, exact opening date, compatible closing date, and independently matching symbol or ISIN. The collector rejects inconsistent identities, conflicting filings, wrong XML units, undated/future listings, and non-official links. It fills missing issue lots and listing dates and reads the explicit `FinalIssuePrice`; existing conflicting values are preserved. Each accepted value retains the document hash, source field, issuer, and issue dates.

Repair, maintenance, and P4 collect up to 150 candidate records and discover at most five issuers' RHP/final PDF documents per run. Completed records checkpoint independently while other downloads continue. The register fingerprint and a seven-day retry interval avoid repeating unchanged source attempts. Newly discovered documents still undergo the parser's opening-page issuer check. P5 uses the same register for older issues only after the correctness gate passes.

Parser 22 supports selected-financial-information headings, staggered annual dates, explicit lakh and `₹ Mn` units, and standalone/consolidated scope changes inside shared or continued tables. Financial fixtures retain original PDF spacing and actual disclosed numeric rows.
