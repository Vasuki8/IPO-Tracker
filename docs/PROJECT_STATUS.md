# PROJECT STATUS

Last updated: 2026-09-21

## Current state

The tracker now publishes **five real 2026 IPO records** from retained official evidence:

- Hero Motors Limited
- Rentomojo Limited
- Jindal Supreme (India) Limited
- Manipal Payment and Identity Solutions Limited
- SS Retail Limited

The recovery pipeline remains deliberately source-first: unsupported fields stay null rather than being estimated, inferred, or copied from aggregators.

## Completed in latest batch

Added three additional 2026 IPO issuers using the proven official NSE/SEBI source pattern.

### Jindal Supreme (India) Limited

Verified from NSE Issue Information:

- price band: ₹88–₹93
- market lot: 161 shares
- minimum bid quantity: 161 shares
- offer period: September 16–18, 2026

Retained documents:

- NSE Issue Information — JSIPL
- SEBI RHP filing dated September 8, 2026
- SEBI Prospectus filing dated September 21, 2026

Intentionally null:

- board
- lifecycle status
- final issue price
- issue size in INR
- listing date
- minimum application amount
- sector

### Manipal Payment and Identity Solutions Limited

Verified from NSE Issue Information:

- price band: ₹322–₹339
- market lot: 44 shares
- minimum bid quantity: 44 shares
- offer period: September 9–11, 2026

Verified from an NSE-hosted Public Announcement:

- board: Mainboard

Retained documents:

- NSE Public Announcement dated June 28, 2025
- NSE Issue Information — MPIMANIPAL
- SEBI RHP filing dated September 4, 2026
- SEBI Prospectus filing dated September 21, 2026

Intentionally null:

- lifecycle status
- final issue price
- issue size in INR
- listing date
- minimum application amount
- sector

### SS Retail Limited

Verified from NSE Issue Information:

- price band: ₹403–₹424
- market lot: 35 shares
- minimum bid quantity: 35 shares
- offer period: September 16–18, 2026

Retained documents:

- NSE Issue Information — SSRETAIL
- SEBI RHP filing dated September 9, 2026
- SEBI Prospectus filing dated September 21, 2026

Intentionally null:

- board
- lifecycle status
- final issue price
- issue size in INR
- listing date
- minimum application amount
- sector

## Why final issue price / issue size were not added

The SEBI final Prospectus filing pages were directly verified for all three new issuers.

However, the attached final Prospectus PDFs were not reliably readable by the available web tooling in this run:

- Jindal Supreme's SEBI attachment opened only through the SEBI PDF viewer shell; the direct PDF URL was not retrievable.
- Manipal Payment's SEBI attachment returned a cache-miss error.
- SS Retail's SEBI attachment opened only through the SEBI PDF viewer shell; the direct PDF URL was not retrievable.

No final issue price was inferred from the upper end of the price band.

No issue size was arithmetically reconstructed from separate fresh-issue and OFS components.

## Existing pilot records

### Hero Motors Limited

Verified:

- price band: ₹79–₹84
- final issue price: ₹84
- issue size: ₹10,000 million
- market lot: 178 shares
- minimum bid quantity: 178 shares
- offer period: September 16–18, 2026

### Rentomojo Limited

Verified:

- board: Mainboard
- price band: ₹384–₹404
- final issue price: ₹404
- issue size: ₹12,555.67 million
- market lot: 37 shares
- minimum bid quantity: 37 shares
- offer period: September 9–11, 2026

## Data integrity rules currently enforced

- Published schema version: `1.1.0`.
- `data/ipos.json` must be exactly synchronized with the retained recovery manifest.
- Verified values require retained evidence.
- Missing fields must keep `value: null`.
- Non-null board/status values require companion provenance.
- Existing evidence collection timestamps are preserved.
- `last_collected_at` is tracked per record.
- Unsupported source hosts are rejected by the recovery publisher.
- Market lot, minimum bid quantity, and minimum application amount remain separate concepts.

## Tests for latest batch

GitHub Actions passed on `recover-2026-batch-2` with:

- `node --check assets/app.js`
- `node scripts/build-published-data.mjs --check`
- `node scripts/validate-data.mjs`

Diff review must confirm before publication:

- exactly three new issuer records are added;
- existing Hero/Rentomojo values are unchanged;
- new final issue prices remain null;
- new issue-size fields remain null;
- Manipal board is Mainboard with retained NSE evidence;
- no listing date/status is guessed;
- no minimum application amount is derived;
- no unrelated UI or product feature is changed.

## Earliest unfinished priority

P1 — Data correctness.

The 2026 universe remains incomplete, but the source family now works across five issuers.

## Recommended next coherent batch

Deepen the three newly added issuers **only where directly retrievable official final documents permit it**.

Priority:

1. locate official NSE archive or issuer-hosted final Prospectus copies for Jindal Supreme, Manipal Payment, and SS Retail;
2. recover final issue price and aggregate issue size only when explicitly stated;
3. retain page/evidence location and collection time;
4. preserve listing/status fields as null unless official listing evidence is directly accessible;
5. if final-document extraction remains blocked, add the next small 2026 issuer batch rather than using mirrors or guesses.

The BSE dynamic listing-notice blocker remains documented and should not be bypassed with third-party mirrors.

## Publication history

- PR #1: source-backed data foundation
- Foundation merge: `4ae4fb43b63fc9aebd5380bab33cd3cc838f48ec`
- PR #2: first 2026 recovery batch
- First recovery merge: `30d73b04677fda0f5d6c17a688f16fa50809840b`
- PR #3: deepen Hero Motors and Rentomojo evidence
- Final-term enrichment merge: `5ecbcc4615c523d4bdafc56632b17ee6d4762722`
- PR #4: recover Rentomojo final Prospectus terms
- Rentomojo final-terms merge: `9895698d87513a2e037f95cf5cf4f2886590df9a`
- Prior production bookkeeping head: `b17f9586ae3131bd1fda312f598d4b79d9a404a2`
- Validation and GitHub Pages deployment passed for the prior production head.

## Latest publication

- Pull request: #5 — `Add second official-source 2026 IPO batch`
- Squash-merged to `main`: `8206b58574610103e18d86bd719b7169b145610f`
- Post-merge data-contract validation: passed
- Post-merge GitHub Pages deployment: passed
- Pages artifact was generated from the merged revision.
- Published issuer count: 5
- New published issuers:
  - Jindal Supreme (India) Limited
  - Manipal Payment and Identity Solutions Limited
  - SS Retail Limited
- Hero Motors and Rentomojo published values/freshness remained unchanged.
- Final issue price, issue size, listing date/status, and minimum application fields that lacked direct official evidence remain null.
- Direct retrieval of `https://vasuki8.github.io/IPO-Tracker/` remains unavailable from the web reader in this development session; workflow and artifact revision were verified instead.
