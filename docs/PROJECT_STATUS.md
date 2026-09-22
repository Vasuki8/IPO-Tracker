# PROJECT STATUS

Last updated: 2026-09-21

## Current state

The tracker now publishes **eight real 2026 IPO records** from retained official evidence:

- Hero Motors Limited
- Rentomojo Limited
- Jindal Supreme (India) Limited
- Manipal Payment and Identity Solutions Limited
- SS Retail Limited
- Kanohar Electricals Limited
- LCC Projects Limited
- Veegaland Developers Limited

The recovery pipeline remains source-first. Unsupported values stay null instead of being inferred, estimated, arithmetically reconstructed, or copied from aggregators.

## Completed in latest batch

The run first attempted the documented priority: deepen Jindal Supreme, Manipal Payment, and SS Retail from directly retrievable official final Prospectus copies.

That path remained blocked:

- Jindal Supreme: SEBI final Prospectus filing is verified, but the attached final PDF is not directly readable through the available tooling and the issuer site does not currently expose a usable final Prospectus copy.
- Manipal Payment: an official NSE archive final-Prospectus URL can be identified, but the available web reader cannot retrieve its contents reliably enough to extract production values.
- SS Retail: SEBI final Prospectus filing is verified, but the final document remains behind an inaccessible/dynamic document path.

No cap-price substitution or mirror data was used.

Per the development-process fallback rule, the run then completed the next small official-source discovery batch.

### Kanohar Electricals Limited

Verified from NSE Issue Information:

- price band: ₹601–₹632
- market lot: 23 shares
- minimum bid quantity: 23 shares
- offer period: September 8–10, 2026

Retained documents:

- NSE Issue Information — KANOHAR
- SEBI RHP filing dated September 3, 2026
- SEBI final Prospectus filing dated September 15, 2026

Intentionally null:

- board
- lifecycle status
- final issue price
- aggregate issue size in INR
- listing date
- minimum application amount
- sector

### LCC Projects Limited

Verified from NSE Issue Information:

- price band: ₹139–₹146
- market lot: 102 shares
- minimum bid quantity: 102 shares
- offer period: September 9–11, 2026

Retained documents:

- NSE Issue Information — LCCPROJECT
- SEBI RHP filing dated September 4, 2026
- SEBI final Prospectus filing dated September 17, 2026

Intentionally null:

- board
- lifecycle status
- final issue price
- aggregate issue size in INR
- listing date
- minimum application amount
- sector

The NSE issue description contains a fresh-issue amount plus an OFS share count. The tracker did **not** manufacture a single INR issue-size value from those heterogeneous components.

### Veegaland Developers Limited

Verified from NSE Issue Information:

- price band: ₹130–₹140
- market lot: 107 shares
- minimum bid quantity: 107 shares
- offer period: September 10–15, 2026

Retained documents:

- NSE Issue Information — VEEGALAND
- SEBI RHP filing dated August 31, 2026
- SEBI final Prospectus filing dated September 16, 2026

Intentionally null:

- board
- lifecycle status
- final issue price
- aggregate issue size in INR
- listing date
- minimum application amount
- sector

Although NSE describes the fresh issue as aggregating up to ₹21,000 lakhs, the production aggregate issue-size field remains null until final-document evidence establishes the value under the project's final-term rules.

## Existing five records

Existing Hero Motors, Rentomojo, Jindal Supreme, Manipal Payment, and SS Retail values and freshness timestamps were not modified by this batch.

## Data integrity rules currently enforced

- Published schema version: `1.1.0`.
- `data/ipos.json` must exactly match the retained recovery manifest.
- Verified values require retained evidence.
- Missing fields must keep `value: null`.
- Non-null board/status values require companion provenance.
- Existing evidence collection timestamps are preserved.
- `last_collected_at` is tracked per record.
- Unsupported source hosts are rejected.
- Market lot, minimum bid quantity, and minimum application amount remain separate.

## Tests for latest batch

GitHub Actions passed on `recover-2026-batch-3`:

- `node --check assets/app.js`
- `node scripts/build-published-data.mjs --check`
- `node scripts/validate-data.mjs`

Release diff review must confirm:

- published issuer count becomes 8;
- exactly 3 issuer records are added;
- the previous 5 records are unchanged;
- all unsupported final/listing/application fields remain null;
- no issue-size arithmetic is introduced;
- no unrelated UI/product feature is changed.

## Earliest unfinished priority

P1 — Data correctness.

The 2026 universe is still incomplete. The NSE/SEBI discovery path is now proven across eight issuers, while final-document retrieval remains uneven across issuer/source families.

## Recommended next coherent batch

Try one bounded final-document recovery pass for:

- Kanohar Electricals Limited
- LCC Projects Limited
- Veegaland Developers Limited

Look specifically for directly retrievable official NSE archive or issuer-hosted final Prospectus copies and recover final issue price / aggregate issue size only when explicitly stated.

If those final documents remain inaccessible, do not keep retrying the same blocked paths. Continue with another 2–5 issuer 2026 official-source batch and leave final fields null.

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
- PR #5: second official-source 2026 IPO batch
- Second batch merge: `8206b58574610103e18d86bd719b7169b145610f`
- Prior production bookkeeping head: `0515407dc7d38ce7a08790f61fdb69ef01eefa26`
- Validation and GitHub Pages deployment passed for the prior production head.

## Latest publication

- Pull request: #6 — `Add third official-source 2026 IPO batch`
- Squash-merged to `main`: `ad7d82fc87b88f3c48c131965c27ee928331cefc`
- Post-merge data-contract validation: passed
- Post-merge GitHub Pages deployment: passed
- Pages artifact was generated from the merged revision.
- Published issuer count: 8
- New published issuers:
  - Kanohar Electricals Limited
  - LCC Projects Limited
  - Veegaland Developers Limited
- Previous five issuer records and freshness timestamps remained unchanged.
- Unsupported final issue price, aggregate issue size, listing/status, board, sector, and minimum-application fields remain null.
- Direct retrieval of `https://vasuki8.github.io/IPO-Tracker/` remains unavailable from the web reader in this development session; workflow and artifact revision were verified instead.
