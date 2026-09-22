# PROJECT STATUS

Last updated: 2026-09-21

## Current state

The tracker now publishes **eleven real 2026 IPO records** from retained official evidence:

- Asset Reconstruction Company (India) Limited
- ESDS Software Solution Limited
- Hero Motors Limited
- Jindal Supreme (India) Limited
- Kanohar Electricals Limited
- LCC Projects Limited
- Manipal Payment and Identity Solutions Limited
- Rentomojo Limited
- Sonaselection India Limited
- SS Retail Limited
- Veegaland Developers Limited

The recovery pipeline remains source-first. Unsupported values stay null rather than being inferred, estimated, arithmetically reconstructed, or copied from aggregators.

## Completed in latest batch

The run first attempted the documented priority: recover directly readable final Prospectus copies for Kanohar Electricals, LCC Projects and Veegaland Developers.

That bounded deepening pass did not produce safe new final-term values:

- Kanohar: no directly readable official final Prospectus copy was located through the available NSE/issuer source paths.
- LCC Projects: the issuer investor page exposes a Prospectus entry, but the underlying final PDF URL/content is not directly exposed by the available web parser.
- Veegaland Developers: the issuer IPO page exposes a Prospectus dated September 15, 2026, but the downloadable document is behind a disclaimer/JavaScript flow and could not be directly extracted.
- No final issue price was inferred from the cap price.
- No aggregate issue size was reconstructed from partial issue components.

Per the fallback rule in `docs/DEVELOPMENT_PROCESS.md`, the run then added the next small official-source batch.

### Asset Reconstruction Company (India) Limited

Verified from NSE Issue Information:

- price band: ₹132–₹139
- market lot: 107 shares
- minimum bid quantity: 107 shares
- offer period: September 9–11, 2026

Retained official documents:

- NSE Issue Information — ARCIL
- SEBI RHP filing dated September 2, 2026
- SEBI Abridged Prospectus dated September 2, 2026

Intentionally null:

- board
- lifecycle status
- final issue price
- aggregate issue size in INR
- listing date
- minimum application amount
- sector

NSE describes the offer size in shares rather than a single INR value, so `issue_size_inr` remains null.

### ESDS Software Solution Limited

Verified from NSE Issue Information:

- price band: ₹408–₹429
- market lot: 34 shares
- minimum bid quantity: 34 shares
- offer period: August 28–September 1, 2026
- issue size: ₹7,200 million

Stored INR issue size:

- ₹7,200,000,000

The NSE source explicitly describes the IPO as a fresh issue aggregating up to ₹7,200 million, so this is retained as a verified INR issue-size field without arithmetic reconstruction.

Retained official documents:

- NSE Issue Information — ESDS
- SEBI RHP filing dated August 25, 2026
- SEBI Abridged Prospectus dated August 25, 2026

Intentionally null:

- board
- lifecycle status
- final issue price
- listing date
- minimum application amount
- sector

### Sonaselection India Limited

Verified from NSE Issue Information:

- price band: ₹94–₹99
- market lot: 150 shares
- minimum bid quantity: 150 shares
- offer period: September 17–21, 2026

Retained official documents:

- NSE Issue Information — SONA
- SEBI RHP filing dated September 9, 2026
- SEBI Abridged Prospectus dated September 9, 2026

Intentionally null:

- board
- lifecycle status
- final issue price
- aggregate issue size in INR
- listing date
- minimum application amount
- sector

NSE states the fresh issue size in equity-share count, not a final INR aggregate, so `issue_size_inr` remains null.

## Existing eight records

The previously published eight issuers and their existing evidence/freshness timestamps are unchanged by this batch.

## Data integrity rules currently enforced

- Published schema version: `1.1.0`.
- `data/ipos.json` must exactly match the retained recovery manifest.
- Verified values require retained evidence.
- Missing fields must keep `value: null`.
- Non-null board/status values require companion provenance.
- Existing evidence collection timestamps are preserved.
- `last_collected_at` is tracked per record.
- Unsupported source hosts are rejected.
- Market lot, minimum bid quantity and minimum application amount remain separate concepts.

## Tests for latest batch

Required GitHub Actions checks:

- `node --check assets/app.js`
- `node scripts/build-published-data.mjs --check`
- `node scripts/validate-data.mjs`

Release diff review must confirm:

- published issuer count becomes 11;
- exactly 3 issuer records are added;
- the prior 8 records remain unchanged;
- ARCIL/Sonaselection issue-size INR fields remain null;
- ESDS issue size is ₹7,200,000,000 with retained NSE evidence;
- final issue prices, listing/status and minimum application fields remain null where unsupported;
- no unrelated product/UI feature changes.

## Earliest unfinished priority

P1 — Data correctness.

The 2026 universe remains incomplete, but the official NSE/SEBI discovery pattern now covers eleven issuers.

## Recommended next coherent batch

Attempt one bounded final-document recovery pass for the newest three issuers only where a directly readable official final Prospectus exists.

Priority:

1. ESDS final Prospectus / final issue price;
2. ARCIL final Prospectus / final issue price;
3. Sonaselection final Prospectus / final issue price.

If those final documents are not directly readable, move immediately to the next 2–5 issuer 2026 official-source batch.

Do not repeatedly retry inaccessible issuer/SEBI document paths, and do not use third-party mirrors to fill production fields.

The BSE dynamic listing-notice blocker remains documented.

## Publication history

- PR #1: source-backed data foundation
- PR #2: first 2026 recovery batch
- PR #3: deepen Hero Motors and Rentomojo evidence
- PR #4: recover Rentomojo final Prospectus terms
- PR #5: second official-source 2026 IPO batch
- PR #6: third official-source 2026 IPO batch
- Prior production head: `b7fef58ea9ad7d164512e57366818b054a1ab06d`
- Validation and GitHub Pages deployment passed for the prior production head.

## Latest publication

- Pull request: #7 — `Add fourth official-source 2026 IPO batch`
- Squash-merged to `main`: `90f7b4389e14f5847d95090f023a11a9d7317022`
- Post-merge data-contract validation: passed
- Post-merge GitHub Pages deployment: passed
- Pages artifact was generated from the merged revision.
- Published issuer count: 11
- New published issuers:
  - Asset Reconstruction Company (India) Limited
  - ESDS Software Solution Limited
  - Sonaselection India Limited
- ESDS publishes a verified ₹7,200 million issue size from NSE issue information.
- Previous eight issuer records and freshness timestamps remained unchanged.
- Unsupported final issue price, listing/status, board, sector, and minimum-application fields remain null.
- Direct retrieval of `https://vasuki8.github.io/IPO-Tracker/` remains unavailable from the web reader in this development session; workflow and artifact revision were verified instead.
