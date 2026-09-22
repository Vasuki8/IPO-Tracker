# PROJECT STATUS

Last updated: 2026-09-21

## Current state

The tracker publishes two real 2026 IPO records from retained official evidence:

- Hero Motors Limited
- Rentomojo Limited

The two-record pilot now demonstrates both pre-offer term recovery and final-Prospectus enrichment while preserving unsupported fields as null.

## Completed in latest batch

### Rentomojo Limited — official final Prospectus recovery

A directly retrievable official NSE archive copy of Rentomojo Limited's Prospectus was recovered:

- document: `Rentomojo Limited - Prospectus dated September 11, 2026`
- official source: `https://nsearchives.nseindia.com/corporate/FP_INE08T701025_15SEP2026.pdf`

The Prospectus explicitly establishes:

- final issue price: ₹404 per Equity Share
- total offer size: ₹12,555.67 million
- equivalent stored INR value: ₹12,555,670,000

Both fields are now published as verified and retain the Prospectus URL, identity, document date, evidence location, and collection timestamp.

The original NSE issue-information evidence and earlier collection timestamps were preserved.

### What remains intentionally null for Rentomojo

- listing date
- lifecycle status
- minimum application amount
- sector

The listing date and listed status were not promoted from third-party mirrors.

The minimum application amount was not silently derived from `37 × ₹404`; the project still requires either direct official evidence or a separately documented derivation rule before publishing that field.

## Official exchange listing-source investigation

The listing-source family was investigated again.

### BSE

Two BSE listing notices are discoverable for Rentomojo:

- `20260916-7` — preliminary listing notice
- `20260916-46` — effective listing notice reported as September 17, 2026

The canonical BSE notice URL pattern is known:

`https://www.bseindia.com/markets/MarketInfo/DispNewNoticesCirculars.aspx?page=<NOTICE_NO>`

Older BSE notices at this pattern are directly retrievable by the available tooling, confirming that the URL structure is legitimate. However, the 2026 Rentomojo dynamic notice pages still return an inaccessible/internal-error response in this development session.

Search indexes and third-party mirrors expose the notice contents, but those mirrors were not accepted as production evidence.

### NSE

A directly retrievable NSE final Prospectus was found and used for final issue price and total offer size.

A directly retrievable NSE listing circular establishing the actual listing date/status was not found in this run.

## PDF verification note

The Rentomojo NSE Prospectus was opened as a PDF and its text layer was available. The required screenshot renderer was also invoked for the relevant pages, but returned a cache-miss error. Page-level evidence therefore uses the official PDF text location while documenting that visual screenshot rendering was unavailable.

## Current published data

### Hero Motors Limited

Verified:

- price band: ₹79–₹84
- final issue price: ₹84
- issue size: ₹10,000 million
- market lot: 178 shares
- minimum bid quantity: 178 shares
- offer period: September 16–18, 2026

Still null:

- board
- lifecycle status
- listing date
- minimum application amount
- sector

### Rentomojo Limited

Verified:

- board: Mainboard
- price band: ₹384–₹404
- final issue price: ₹404
- issue size: ₹12,555.67 million
- market lot: 37 shares
- minimum bid quantity: 37 shares
- offer period: September 9–11, 2026

Still null:

- lifecycle status
- listing date
- minimum application amount
- sector

## Data integrity rules currently enforced

- Published schema version: `1.1.0`.
- `data/ipos.json` must be exactly synchronized with the retained recovery manifest.
- Verified values require retained evidence.
- Missing fields must keep `value: null`.
- Non-null board/status values require companion provenance.
- Existing evidence collection timestamps must not be rewritten when a record is re-collected.
- `last_collected_at` is tracked per record rather than copied from the dataset-generation timestamp; untouched issuers do not become falsely "fresh".
- Unsupported source hosts are rejected by the recovery publisher.

## Tests required for this batch

GitHub Actions must pass:

- `node --check assets/app.js`
- `node scripts/build-published-data.mjs --check`
- `node scripts/validate-data.mjs`

Diff review must confirm:

- no new issuer is introduced;
- Rentomojo issue price is ₹404 from the official NSE Prospectus;
- Rentomojo issue size is ₹12,555,670,000 from the same Prospectus;
- listing date/status remain null;
- minimum application amount remains null;
- prior evidence timestamps remain unchanged;
- Hero Motors keeps its prior `last_collected_at` because it was not re-collected in this batch;
- Rentomojo advances to the new collection timestamp;
- no unrelated UI/product feature is changed.

## Earliest unfinished priority

P1 — Data correctness.

The direct BSE listing-notice endpoint remains blocked in this environment, while the official NSE final-Prospectus family is now proven usable.

## Recommended next coherent batch

Do not spend another full batch retrying the same inaccessible BSE notice endpoint.

Proceed to the next small 2026 official-source recovery batch using the proven pattern:

1. discover 2–5 additional 2026 IPO issuers from official NSE/SEBI sources;
2. retain issuer identity and offer-document trail;
3. recover core P1 terms from official issue-information / Prospectus sources;
4. preserve unavailable listing fields as null;
5. return to the BSE listing-notice family when a directly retrievable official endpoint or archive path is available.

The exchange-listing blocker should remain documented, not bypassed with mirrors.

## Publication history

- PR #1: source-backed data foundation
- Foundation merge: `4ae4fb43b63fc9aebd5380bab33cd3cc838f48ec`
- PR #2: first 2026 recovery batch
- First recovery merge: `30d73b04677fda0f5d6c17a688f16fa50809840b`
- PR #3: deepen Hero Motors and Rentomojo evidence
- Final-term enrichment merge: `5ecbcc4615c523d4bdafc56632b17ee6d4762722`
- Prior production bookkeeping head: `880c53a5f2f8c6ffb6f5561a761b6f0037aec598`
- Validation and GitHub Pages deployment passed for the prior production head.

## Latest publication

- Pull request: #4 — `Recover Rentomojo final Prospectus terms`
- Squash-merged to `main`: `9895698d87513a2e037f95cf5cf4f2886590df9a`
- Post-merge data-contract validation: passed
- Post-merge GitHub Pages deployment: passed
- Pages artifact was generated from the merged revision.
- Rentomojo final issue price ₹404 and total offer size ₹12,555.67 million are published from the official NSE archived Prospectus.
- Hero Motors' `last_collected_at` remained unchanged because Hero was not re-collected in this batch.
- Rentomojo listing date/status and minimum application amount remain null.
- Direct retrieval of `https://vasuki8.github.io/IPO-Tracker/` remains unavailable from the web reader in this development session; deployment workflow and artifact revision were verified instead.
