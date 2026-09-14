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

## Scheduling and publication

`refresh.yml` is the only active data writer. Core collection runs hourly; subscriptions run twice hourly during the configured weekday UTC window. Filing maintenance follows core collection when P0–P3 gaps exist, with a six-hour fallback. Daily maintenance runs at 13:43 UTC. GitHub schedules are best-effort; missed triggers are not evidence of fresh data.

Collectors have read-only repository permissions. They retain a baseline, proposed dataset and tested source commit in a 14-day Actions artifact. Publication runs only from `main`, serializes in one queue, tests current main, and checks that the collector's source code is still current. A three-way merge preserves unrelated updates. Document values and their evidence, and subscription values and their source/timestamps, merge as atomic groups.

Conflicting proposals are retained in `data/pending_updates.json`; accepted values are preserved. `documentFields` and `subscriptionSnapshot` in a pending path name the atomic groups defined in `publish_transaction.py`. Review source evidence, then update or recollect the affected group. There is no automatic last-writer-wins conflict resolution. Failed publications retain their original collection artifact; rerun a failed publisher only when its code is still current, otherwise recollect on current main. Publication requests a Pages rebuild explicitly after a bot commit.

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
