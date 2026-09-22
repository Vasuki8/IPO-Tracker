# PROJECT STATUS

Last updated: 2026-09-21

## Current state

The tracker now publishes **fourteen real 2026 IPO records** from retained official evidence.

The recovery pipeline remains source-first. Unsupported values stay null rather than being inferred, estimated, arithmetically reconstructed, or copied from aggregators.

## Completed in latest batch

The run first attempted the documented priority: directly readable official final-Prospectus recovery for ESDS Software Solution, Asset Reconstruction Company (India), and Sonaselection India.

That bounded deepening pass did not produce safe final issue prices:

- ESDS: the issuer investor page exposes a Prospectus dated September 1, 2026, but access requires an India-location confirmation that this development session cannot truthfully make.
- ARCIL: the issuer corporate-governance page exposes an "ARCIL Prospectus", but access similarly requires an India-location confirmation.
- Sonaselection: official NSE/SEBI pre-offer documents are available, but no directly readable official final Prospectus was recovered in the bounded pass.

No geographic representation was bypassed, no cap-price substitution was used, and no mirror data was promoted.

Per the development-process fallback rule, the run then completed the next small official-source batch.

### Karamtara Engineering Limited

Verified from NSE Issue Information:

- price band: ₹241–₹254
- market lot: 59 shares
- minimum bid quantity: 59 shares
- offer period: September 9–11, 2026

Retained official documents:

- NSE Issue Information — KARAMTARA
- SEBI RHP filing dated September 3, 2026
- SEBI Abridged Prospectus dated September 3, 2026

Intentionally null:

- board
- lifecycle status
- final issue price
- aggregate issue size in INR
- listing date
- minimum application amount
- sector

NSE describes a fresh-issue INR amount and a separate OFS INR amount. The tracker does not sum those components into the aggregate issue-size field without an explicit retained final-source statement.

### Pranav Constructions Limited

Verified from NSE Issue Information:

- price band: ₹118–₹124
- market lot: 120 shares
- minimum bid quantity: 120 shares
- offer period: September 7–9, 2026

Retained official documents:

- NSE Issue Information — PRANAV
- SEBI RHP filing dated September 1, 2026
- SEBI Abridged Prospectus dated September 1, 2026
- SEBI final Prospectus filing dated September 10, 2026

Intentionally null:

- board
- lifecycle status
- final issue price
- aggregate issue size in INR
- listing date
- minimum application amount
- sector

The final filing page is retained, but the final Prospectus contents were not directly extractable in this run.

### Qualiance International Limited

Verified from NSE Issue Information:

- board: SME
- price band: ₹120–₹127
- market lot: 1,000 shares
- offer period: September 4–8, 2026

Retained official documents:

- NSE Issue Information — QUALIANCE, SME series
- SEBI public-issue document page dated September 10, 2026

Intentionally null:

- lifecycle status
- final issue price
- aggregate issue size in INR
- minimum bid quantity
- listing date
- minimum application amount
- sector

Important distinction: NSE explicitly states a 1,000-share lot size, but the page does not separately state a minimum bid/order quantity. The tracker therefore does **not** copy the lot size into `minimum_bid_quantity`.

## Existing eleven records

The previously published eleven issuers and their existing evidence/freshness timestamps are unchanged by this batch.

## Data integrity rules currently enforced

- Published schema version: `1.1.0`.
- `data/ipos.json` must exactly match the retained recovery manifest.
- Verified values require retained evidence.
- Missing fields must keep `value: null`.
- Non-null board/status values require companion provenance.
- Existing evidence collection timestamps are preserved.
- `last_collected_at` is tracked per record.
- Unsupported source hosts are rejected.
- Market lot, minimum bid quantity, and minimum application amount remain separate concepts.

## Tests for latest batch

GitHub Actions passed on `recover-2026-batch-5` with:

- `node --check assets/app.js`
- `node scripts/build-published-data.mjs --check`
- `node scripts/validate-data.mjs`

Release diff review must confirm:

- published issuer count becomes 14;
- exactly 3 issuer records are added;
- the prior 11 records remain unchanged;
- Karamtara and Pranav issue-size INR fields remain null;
- Qualiance board is SME with retained NSE SME-series evidence;
- Qualiance minimum bid quantity remains null;
- all unsupported final/listing/application fields remain null;
- no unrelated product/UI feature changes.

## Earliest unfinished priority

P1 — Data correctness.

The 2026 universe remains incomplete, but the official NSE/SEBI discovery pattern now covers fourteen issuers.

## Recommended next coherent batch

Attempt one bounded final-document recovery pass for:

1. Karamtara Engineering Limited;
2. Pranav Constructions Limited;
3. Qualiance International Limited.

Recover final issue price / aggregate issue size only from directly readable official final documents.

If those paths remain inaccessible, immediately continue with the next 2–5 official-source 2026 issuers rather than repeatedly retrying the same blocked documents.

Do not bypass issuer geographic/legal disclaimers and do not use third-party mirrors to fill production fields.

The BSE dynamic listing-notice blocker remains documented.

## Publication history

- PR #1: source-backed data foundation
- PR #2: first 2026 recovery batch
- PR #3: deepen Hero Motors and Rentomojo evidence
- PR #4: recover Rentomojo final Prospectus terms
- PR #5: second official-source 2026 IPO batch
- PR #6: third official-source 2026 IPO batch
- PR #7: fourth official-source 2026 IPO batch
- Prior production head: `9b3c296a9e6e842de0e7fbe40fa6e42dfa57b4be`
- Validation and GitHub Pages deployment passed for the prior production head.

## Latest publication

- Pull request: #8 — `Add fifth official-source 2026 IPO batch`
- Squash-merged to `main`: `4b85fd7b47b8c36a5894086f8d52ee38244d604a`
- Post-merge data-contract validation: passed
- Post-merge GitHub Pages deployment: passed
- Pages artifact was generated from the merged revision.
- Published issuer count: 14
- New published issuers:
  - Karamtara Engineering Limited
  - Pranav Constructions Limited
  - Qualiance International Limited
- Qualiance publishes SME board classification with NSE SME-series provenance.
- Qualiance minimum bid quantity remains null because the official NSE page states lot size but does not separately state minimum bid/order quantity.
- Previous eleven issuer records and freshness timestamps remained unchanged.
- Unsupported final issue price, aggregate issue size, listing/status, sector, and minimum-application fields remain null.
- Direct retrieval of `https://vasuki8.github.io/IPO-Tracker/` remains unavailable from the web reader in this development session; workflow and artifact revision were verified instead.
