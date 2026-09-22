# PROJECT STATUS

Last updated: 2026-09-21

## Current state

The tracker publishes two real 2026 IPO records from retained official evidence:

- Hero Motors Limited
- Rentomojo Limited

This batch deepened those records without filling unsupported gaps.

## Completed in latest batch

### Hero Motors Limited

Added the final issue price:

- issue price: ₹84 per Equity Share
- source: issuer-hosted final Prospectus dated September 18, 2026
- evidence page: 10
- source collection timestamp retained separately from earlier NSE/SEBI evidence

The Prospectus explicitly defines the Offer Price as ₹84 per Equity Share.

### Rentomojo Limited

Added the board classification:

- board: Mainboard
- source: NSE-hosted Public Announcement dated March 28, 2026
- evidence page: 1

The announcement explicitly describes the proposed IPO as an initial public offering on the Main Board of BSE and NSE.

### Data-contract improvements

- Bumped published schema from `1.0.0` to `1.1.0`.
- Added `board_evidence` and `status_evidence` arrays so scalar lifecycle metadata cannot lose provenance.
- Validation now rejects a non-null board or status without retained evidence.
- Added official issuer-host support for Hero Motors evidence.
- Added official NSE archive host support.
- Fixed recovery publication so regenerating the dataset no longer overwrites older evidence collection timestamps.
- Preserved the original `first_observed_at` timestamp for both records.
- New evidence receives the new collection time while existing evidence keeps its original collection time.

## Fields intentionally still null

### Hero Motors Limited

- board
- lifecycle status
- listing date
- minimum application amount

### Rentomojo Limited

- final issue price
- lifecycle status
- listing date
- minimum application amount
- issue size

These values were not promoted because the retained official evidence available to this run did not meet the project's source-verification standard.

## Source-recovery attempts that did not become production data

- BSE notice `20260916-46` is discoverable through search/mirror indexing and describes Rentomojo's ₹404 issue price and September 17 listing, but the official dynamic BSE notice endpoint could not be independently retrieved in this development session. Mirror data was therefore not used as production evidence.
- The SEBI Rentomojo final Prospectus filing was verified and exposes the official attached PDF URL, but direct retrieval of that PDF timed out in the available web tooling. No unverified values were extracted from secondary copies.
- Hero Motors' official final Prospectus PDF was readable through the issuer site; the web screenshot renderer returned a cache-miss error, but the PDF text layer provided page-level evidence for the ₹84 Offer Price.
- Rentomojo's NSE Public Announcement PDF is official and indexed with the explicit Main Board statement; the screenshot renderer could not render that search result, so the indexed official PDF text was used.

## Tests required for this batch

GitHub Actions must pass:

- `node --check assets/app.js`
- `node scripts/build-published-data.mjs --check`
- `node scripts/validate-data.mjs`

Diff review must confirm:

- exactly two existing records are enriched; no new issuer is introduced;
- Hero issue price is ₹84 with official issuer evidence;
- Rentomojo board is Mainboard with official NSE evidence;
- previous evidence collection timestamps remain unchanged;
- unsupported fields remain null;
- no correction history is lost;
- no unrelated product feature is changed.

## Earliest unfinished priority

P1 — Data correctness.

The two-record pilot is now strong enough to demonstrate final-term enrichment. Remaining P1 work is split by source availability:

1. Resolve official listing/final-price evidence for Rentomojo from a directly retrievable BSE/NSE/SEBI source.
2. Recover Hero Motors board/status/listing only when explicit official evidence is available.
3. Then expand the same recovery pattern to the next small 2026 issuer batch.

## Recommended next coherent batch

Resolve the official exchange listing-source family.

Target:

- official BSE/NSE listing notices;
- final issue price;
- listing date;
- listed lifecycle status;
- board classification where explicitly stated.

Do not use third-party notice mirrors as production sources. If official dynamic exchange pages remain inaccessible, retain the gaps and move to another official source family rather than guessing.

## Publication history

- PR #1: source-backed data foundation
- Foundation merge: `4ae4fb43b63fc9aebd5380bab33cd3cc838f48ec`
- PR #2: first 2026 recovery batch
- First recovery merge: `30d73b04677fda0f5d6c17a688f16fa50809840b`
- First recovery deployment bookkeeping: `fc2c995b3e59e75eaacd3bdfec474a7cdf07aa6a`
- Validation and GitHub Pages deployment passed for the prior production head.
