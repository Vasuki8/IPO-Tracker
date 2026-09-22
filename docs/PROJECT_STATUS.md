# PROJECT STATUS

Last updated: 2026-09-22

## Current state

IPO Tracker now has a working **automated official-source discovery and publication loop** plus a production-tested **SEBI document-discovery layer**.

The published 2026 dataset contains **26 real IPO issuers**.

The source-first rules remain enforced: unsupported values stay null rather than being inferred, estimated, reconstructed, or copied from aggregators.

## Automated NSE discovery — verified

PR #9 added hourly official NSE discovery and publication.

The production collector can automatically:

- discover current/upcoming IPOs;
- create new recovery records;
- retain issuer name, symbol/series and collection time;
- publish explicit NSE board/status, price-band/fixed-price, market-lot and offer-date values;
- preserve unsupported fields as null;
- rebuild and validate `data/ipos.json`;
- commit only source-backed changes;
- trigger GitHub Pages publication.

The first production run expanded the dataset from 14 to 23 issuers.

## Earlier completed batch — automated SEBI document discovery

This development run implemented and production-tested automatic SEBI offer-document discovery.

### Pull requests

- PR #10 — `Automate SEBI offer-document discovery`
  - merge: `dd6236d718b77c21f1962dc3b2e95caac8fa5d86`
- PR #11 — `Repair live SEBI filing-page parsing`
  - merge: `93ed02f01b918e3042b336b4501b7695d6a95149`
- PR #12 — `Target sparse IPOs with SEBI document search`
  - merge: `2c24f1f800bb483f2f0e66b0aedf39f90b5d80b2`
- PR #13 — `Cover recent SEBI filings from general filings feed`
  - merge: `65bdfe5bb7d9f025511963af31a34ab6561ce0f9`
- PR #14 — `Use token searches for sparse SEBI enrichment`
  - merge: `f5e7032eb560aecceaa2c67a3728a21a6a4d1251`
- PR #15 — `Add SEBI mixed Public Issues coverage`
  - merge: `86a828f2199abfc0c3f172ebf95af224f34e65fd`

### What the SEBI layer does

The hourly workflow now checks official SEBI sources for:

- RHP filing pages;
- Abridged Prospectus links;
- final Prospectus / final-offer-document filing pages.

Current official inputs include:

- dedicated RHP list;
- dedicated final-offer-document list;
- general SEBI Filings list;
- mixed Public Issues list;
- bounded issuer-specific SEBI search for sparse NSE-live records.

Issuer matching is conservative:

- normalize punctuation / whitespace / Ltd vs Limited;
- allow a controlled `(India)` alternate;
- require exactly one matching recovery record;
- skip ambiguous/unmatched entries;
- ignore DRHP/UDRHP, addendum and corrigendum entries in this initial matcher.

The SEBI layer currently attaches **document evidence only**. It does not infer market values from filenames or price-band caps.

## Production verification

### Initial live failure and repair

The first production run after PR #10:

- workflow run: `35684352679`
- NSE collection: passed
- SEBI step: failed

Reason:

- the live SEBI raw HTML used dynamic filing-link markup that differed from the original plain-`href` fixture.

PR #11 repaired the parser to support dynamic anchor attributes and raw official filing URL fallbacks.

### Verified successful network runs

After repair, production runs completed end to end:

- `35684600007`
- `35684873959`
- `35685039080`
- `35685302655`
- `35685494607`

The latest run `35685494607` passed:

- NSE parser tests;
- SEBI matcher tests;
- real NSE collection;
- real SEBI collection;
- deterministic publication;
- data-contract validation;
- publication step.

Post-merge validation and GitHub Pages deployment for head
`86a828f2199abfc0c3f172ebf95af224f34e65fd` also passed.

## Verified SEBI coverage limitation

The SEBI network/parser path is operational. After the September 22 RHP freshness/identity repairs, three formerly sparse records—Adroit Industries (India), National Stock Exchange of India, and Swastika Infra—are now enriched from current official SEBI RHP/Abridged sources. Six live-discovered records remain without retained SEBI evidence.

Latest measured result:

- 9 matched latest-list filing entries;
- 37 unmatched listing entries;
- 9/9 sparse NSE-live records searched by the bounded targeted fallback;
- 5 filing results parsed from targeted searches;
- 0 deterministic targeted issuer matches;
- 0 new documents added.

The six still-sparse live-discovered issuers are:

1. ArMee Infotech Limited
2. Axiom Gas Engineering Limited
3. Coreintegra Consulting Services Limited
4. Elevate Campuses Limited
5. Pooja Logistics Limited
6. Varmora Granito Limited

This is documented as a **source-delivery / coverage limitation**, not a reason to loosen matching.

The tracker will not:

- fuzzy-match a filing to an issuer;
- copy a third-party document mirror;
- invent a SEBI URL or filing ID;
- silently treat a search result for another issuer as evidence.

## Data integrity rules currently enforced

- Published schema version: `1.1.0`.
- `data/ipos.json` must exactly match retained recovery manifests.
- Verified values require retained evidence.
- Missing fields keep `value: null`.
- Non-null board/status values require companion provenance.
- Existing evidence collection timestamps are preserved.
- `last_collected_at` is tracked per record.
- Market lot, minimum bid quantity, and minimum application amount remain separate.
- Live-feed enrichment does not relabel richer manual evidence.
- Price-band conflicts are not silently overwritten.
- SEBI document attachment is idempotent.
- Ambiguous SEBI issuer matches are skipped.

## Tests

The current validation workflow covers:

- NSE date / price / board / status parsing;
- NSE new-record and safe-enrichment behavior;
- manual-source provenance protection;
- deterministic multi-year publication;
- SEBI filing URL parsing;
- dynamic SEBI link markup;
- RHP/final classification;
- Abridged Prospectus extraction;
- issuer normalization;
- ambiguity rejection;
- duplicate-document idempotency;
- sparse live-record candidate selection;
- bounded SEBI search token selection;
- explicit final Prospectus issue-price parsing;
- labelled cover-price syntax with unlabeled-price rejection;
- explicit final Prospectus aggregate issue-size parsing;
- unit conversion for million/lakh/crore totals;
- rejection of Fresh Issue/OFS component-only aggregate amounts.

## Latest completed batch — Abridged Prospectus issue-size extraction

PR #16 — `Extract explicit issue size from retained Abridged Prospectuses`

Squash-merged:

`c7c59252bb9e59b3767d73205ad1d682326c48b8`

The extractor:

- reads only already-retained official SEBI Abridged Prospectus PDFs;
- parses page 1 with Poppler `pdftotext -layout`;
- accepts only an explicit numeric `TOTAL OFFER SIZE` / `TOTAL ISSUE SIZE`;
- fills missing `issue_size_inr` only;
- retains source URL, document identity/type, publication date, page and collection timestamp;
- never sums Fresh Issue + OFS or derives values from shares/prices.

### Production verification

Workflow:

- `Sync live IPO data`
- run ID: `35686786294`
- conclusion: success

Measured extraction result:

- candidates: 4;
- official PDFs downloaded: 4;
- extracted: 1;
- explicit-total missing / placeholder: 3;
- PDF fetch errors: 0.

Extracted:

- Karamtara Engineering Limited
- explicit total offer size: ₹8,750.00 million
- stored INR value: ₹8,750,000,000
- evidence page: 1
- source: retained SEBI Abridged Prospectus dated September 3, 2026.

Bot data commit:

`92f0f024367b20a9f023218a0cb92ecbc2e38636`

The bot diff was reviewed and changed only:

- Karamtara `issue_size_inr`;
- Karamtara `last_collected_at`;
- manifest/dataset generation timestamps.

Unchanged as intended:

- ESDS retained its existing ₹7,200,000,000 NSE issue-size evidence;
- ARCIL remained null;
- Pranav Constructions remained null;
- Sonaselection remained null.

The three null cases did not contain an explicit numeric aggregate total in the retained Abridged Prospectus first-page table.

GitHub Pages native build/deployment for bot commit `92f0f024...` passed in run `35686851497`.

## Earliest unfinished priority

P1/P2 — **data correctness and source evidence depth**.

Live IPO discovery is automated and SEBI document matching is operational, but SEBI raw-source coverage for newly discovered sparse issuers is not sufficient to justify further endpoint-variant retries in the same workstream.

## Latest completed batch — direct SEBI Prospectus PDF resolution

PR #17 — `Resolve direct SEBI Prospectus PDF attachments`

Squash-merged:

`cd39442c03450a9189d783d554e3feb48ee57239`

The resolver:

- fetches already-retained SEBI final Prospectus filing pages;
- decodes SEBI viewer URLs carrying the direct PDF in `file=`;
- accepts only HTTPS `sebi.gov.in/sebi_data/attachdocs/*.pdf` targets;
- retains the attachment as `SEBI Prospectus PDF`;
- deduplicates viewer/direct-link forms;
- rejects non-SEBI mirrors;
- does not extract final terms in the attachment step.

### Production verification

Workflow:

- `Sync live IPO data`
- run ID: `35687483282`
- conclusion: success

Measured SEBI result:

- 9 Prospectus PDFs resolved;
- 9 records changed;
- 9 documents added;
- no market-field extraction by the resolver.

Resolved issuers:

1. Hero Motors Limited
2. Jindal Supreme (India) Limited
3. Kanohar Electricals Limited
4. LCC Projects Limited
5. Manipal Payment and Identity Solutions Limited
6. Pranav Constructions Limited
7. Rentomojo Limited
8. SS Retail Limited
9. Veegaland Developers Limited

Bot data commit:

`0c3e1c199fdb12266589c7f65eead373c49065dd`

Bot diff review confirmed the data change was limited to:

- adding `SEBI Prospectus PDF` document evidence;
- advancing `last_collected_at` for the nine enriched records;
- advancing manifest/dataset generation timestamps.

No `issue_price`, `issue_size_inr`, listing date, sector, minimum application amount, or other market field changed.

The existing Abridged Prospectus issue-size extractor subsequently saw 3 eligible candidates, downloaded all 3, extracted 0 new totals, and preserved all three as null/placeholders with zero fetch errors.

## Latest completed batch — final Prospectus issue-price extraction

PR #18 — `Extract explicit final issue price from SEBI Prospectus PDFs`

Squash-merged:

`1b41f0c115c5df993486e3d3e5f52668d73ffcfc`

The extractor:

- reads only already-retained official `SEBI Prospectus PDF` attachments under `sebi.gov.in/sebi_data/attachdocs/`;
- scans PDF pages 1–20 with Poppler `pdftotext -layout`;
- accepts only explicit `Offer Price` / `Issue Price` wording tied to a rupee amount per Equity Share;
- fills missing `issue_price` only;
- keeps existing issue-price evidence unchanged;
- retains source URL, document identity/type, publication date, PDF page and collection timestamp;
- does not consult the record's price band when extracting.

### Production verification

Workflow:

- `Sync live IPO data`
- run ID: `35688500637`
- conclusion: success

Measured extraction result:

- candidates: 7;
- official PDFs downloaded: 7;
- extracted: 4;
- explicit supported price missing: 3;
- PDF fetch errors: 0.

Extracted and published:

1. Kanohar Electricals Limited — ₹632 per Equity Share — PDF page 7
2. LCC Projects Limited — ₹146.00 per Equity Share — PDF page 7
3. Manipal Payment and Identity Solutions Limited — ₹339.00 per Equity Share — PDF page 3
4. Pranav Constructions Limited — ₹124 per Equity Share — PDF page 5

Preserved as null:

1. Jindal Supreme (India) Limited
2. SS Retail Limited
3. Veegaland Developers Limited

Hero Motors and Rentomojo were not candidates because they already had retained final issue-price evidence; the extractor did not overwrite them.

Bot data commit:

`f9b7155c42d8b44d6985d9dafb9fd242e37dc64e`

Bot diff review confirmed only:

- `data/recovery/2026/nse-issue-information.json`;
- generated `data/ipos.json`

changed. The four new issue prices carry official SEBI Prospectus PDF/page evidence. The three unsupported cases remain `value: null`.

GitHub Pages native deployment for the bot commit passed in run `35688893344`.

## Latest completed batch — final Prospectus cover-price repair

### Diagnostic

PR #20 — `Diagnose unmatched final Prospectus price phrases`

Squash-merged:

`f141c4fef5f5ce9025a9e6e809b9cc0c80a68b2f`

Production run `35689468724` used a temporary read-only 80-page diagnostic against only the three unresolved retained official Prospectuses.

It established that the 20-page production boundary was **not** the blocker. All three explicit final prices were on early pages, but the documents placed the numeric amount before the `(Offer Price)` / `(Issue Price)` label:

- Jindal Supreme (India) Limited — ₹93 — PDF page 3;
- SS Retail Limited — ₹424 — PDF page 3;
- Veegaland Developers Limited — ₹140 — PDF page 2.

The diagnostic changed no recovery or published data. Its temporary hourly workflow step was removed after investigation.

### Parser repair

PR #21 — `Parse explicit final price from Prospectus cover wording`

Squash-merged:

`454ec51a640f2f4079577d41d84dec222fe48e63`

The repair adds one strict supported syntax:

`at a price of ₹X per Equity Share ... (Offer Price/Issue Price)`

It also:

- accepts a bounded footnote marker such as SS Retail's `₹424^`;
- requires the nearby explicit `Offer Price` or `Issue Price` label;
- rejects generic unlabeled `price of ₹X per Equity Share` text;
- keeps the normal 20-page production scan;
- preserves fill-missing-only precedence;
- does not inspect or use the price-band cap to choose a value.

### Production verification

Workflow:

- `Sync live IPO data`
- run ID: `35690054143`
- conclusion: success

Measured final-Prospectus result:

- candidates: 3;
- official PDFs downloaded: 3;
- extracted: 3;
- explicit-price missing: 0;
- PDF fetch errors: 0.

Published with retained page-level official evidence:

1. Jindal Supreme (India) Limited — ₹93 per Equity Share — PDF page 3
2. SS Retail Limited — ₹424 per Equity Share — PDF page 3
3. Veegaland Developers Limited — ₹140 per Equity Share — PDF page 2

Bot data commit:

`51f806b16e4eba40efee304d07bb5753a8e0f9d9`

Bot diff review confirmed only:

- `data/recovery/2026/nse-issue-information.json`;
- generated `data/ipos.json`

changed. No unrelated code or data was modified by the bot.

Together with existing Hero Motors and Rentomojo evidence and the four values recovered by PR #18, **all 9 records currently carrying a retained official `SEBI Prospectus PDF` now have final issue-price evidence**.

## Latest completed batch — final Prospectus aggregate issue-size extraction

### Diagnostic

PR #23 — `Diagnose final Prospectus aggregate issue-size wording`

Squash-merged:

`5a0b7e225c53c737b43750db61b19309d29dabc0`

The temporary read-only diagnostic scanned pages 1–20 of the seven retained official final Prospectuses with missing `issue_size_inr`. It confirmed each document contained an explicit top-level aggregate Offer/Issue amount on PDF pages 2–3, while also containing component amounts that must not be confused with the total.

### Extractor

PR #24 — `Extract explicit aggregate issue size from final SEBI Prospectuses`

Squash-merged:

`a7d2afc5f69fe97f17564e86b72e1ebe3cd296b6`

The extractor:

- uses only retained official `SEBI Prospectus PDF` attachments;
- scans pages 1–20 with Poppler;
- accepts explicit top-level Offer/Issue aggregate amounts tied to the cover statement, an overall `(Offer)` / `(Issue)` label, or explicit `TOTAL OFFER/ISSUE SIZE`;
- supports million, lakh and crore units with direct unit conversion;
- fills missing `issue_size_inr` only;
- retains PDF page and source metadata;
- rejects Fresh Issue-only and OFS-only component amounts;
- never sums components;
- never multiplies share counts by issue price;
- removed the temporary diagnostic from the hourly workflow after the source patterns were understood.

### Production verification

Workflow:

- `Sync live IPO data`
- run ID: `35691580621`
- conclusion: success

Measured result:

- candidates: 7;
- official PDFs downloaded: 7;
- extracted: 7;
- explicit-size missing: 0;
- PDF fetch errors: 0.

Published:

1. Jindal Supreme (India) Limited — ₹1,248,804,000 — PDF page 3
2. Kanohar Electricals Limited — ₹10,557,400,000 — PDF page 3
3. LCC Projects Limited — ₹4,271,410,000 — PDF page 3
4. Manipal Payment and Identity Solutions Limited — ₹8,050,000,000 — PDF page 3
5. Pranav Constructions Limited — ₹3,510,250,000 — PDF page 2
6. SS Retail Limited — ₹5,000,000,000 — PDF page 3
7. Veegaland Developers Limited — ₹2,100,000,000 — PDF page 2

Bot data commit:

`0110d864235eccb800efa5b206fa19bf9cdb0fb4`

Bot diff review confirmed only:

- `data/recovery/2026/nse-issue-information.json`;
- generated `data/ipos.json`

changed. Existing Hero Motors and Rentomojo issue-size evidence was preserved.

GitHub Pages deployment for the bot revision passed in run `35692087146`.

All 9 records currently carrying retained official final Prospectus PDF evidence now have both final issue price and aggregate issue-size evidence.

## Latest completed batch — homepage newest-first ordering

PR #26 — `Show newest IPOs first on the homepage`

The homepage previously displayed records in dataset order. It now sorts presentation rows by source-backed IPO lifecycle dates without mutating the published dataset.

Ordering:

1. `open_date` descending;
2. `close_date` descending for equal open dates;
3. issuer name for deterministic ties;
4. missing or invalid dates last.

The same ordered rows drive:

- desktop IPO table;
- mobile IPO cards;
- search results;
- board-filtered results;
- status-filtered results.

Validation includes a dedicated behavioral test against the published dataset. At implementation time the test confirms:

- newest published open date: 2026-09-23;
- oldest published open date: 2026-08-28;
- every adjacent row is non-increasing by `open_date`.

The initial UI-only implementation left `data/ipos.json` alphabetically ordered, which meant a browser with cached pre-sort JavaScript could still display alphabetical rows.

Follow-up repair:

- deterministic publication now emits `data/ipos.json` newest-first using the same open-date/close-date/name order;
- only record order changes; field values/evidence are unchanged;
- script URLs are versioned to bypass stale browser asset cache;
- validation now asserts that the published dataset itself is already newest-first.

## Latest completed batch — SEBI RHP freshness, matching and direct-PDF recovery

### Listing freshness repair

PR #28 — `Bypass stale SEBI listing cache`

Squash-merged:

`7c7c79855628a5ef77c3ff981f201e6a98a07b90`

The collector now:

- adds a per-run cache-busting token to SEBI listing requests;
- sends `Cache-Control: no-cache` and `Pragma: no-cache`;
- logs the parsed RHP-list head for production verification.

Production run `35693581226` confirmed the GitHub Actions runner could see current entries including Adroit, Swastika Infra and National Stock Exchange of India. That run also exposed a second live markup issue.

### Malformed RHP anchor identity repair

PR #29 — `Repair issuer identity on malformed SEBI RHP anchors`

Squash-merged:

`d89ace7548358946a455b2039def30a1c9fa3f65`

SEBI's live markup can pair an official RHP filing URL with adjacent Abridged Prospectus anchor text. When title-kind and filing-URL-kind disagree, issuer identity is now derived from the official filing URL slug rather than the unsafe anchor text. Exact deterministic record matching is still required.

Production sync:

- run ID: `35693813309`
- latest-list matches: 22, up from 9 before the repair;
- unmatched current-list entries: 24;
- changed issuer records: 8;
- official documents added: 11.

The source-backed document commit was:

`ec684bc1fa558f2dafb7c7b90df6b750fc6f79ac`

Newly enriched formerly sparse issuers include:

- Adroit Industries (India) Limited;
- National Stock Exchange of India Limited;
- Swastika Infra Limited.

The same repair also attached previously missed Abridged Prospectuses to several already-enriched records.

### Direct RHP PDF resolution

PR #30 — `Resolve direct SEBI RHP PDF attachments`

Squash-merged:

`fa71baaf588930aa648e87dfade658729f44769a`

The RHP detail-page layer now resolves official `sebi.gov.in/sebi_data/attachdocs/*.pdf` viewer targets and stores them distinctly as `SEBI RHP PDF`.

Production sync:

- run ID: `35694073605`
- deterministic latest-list matches: 22;
- direct RHP PDFs resolved: 13;
- changed records: 13;
- market fields changed by this attachment stage: 0.

Bot document commit:

`3c2f3fb8a8737fe2067aab3e18e39ab86a68eeb6`

GitHub Pages deployment for that bot revision passed in run `35694143832`.

### Remaining issue-size state

Overall `issue_size_inr` coverage remains **11 present / 12 missing**.

Five missing-size records now have retained official `SEBI RHP PDF` plus Abridged Prospectus evidence:

1. Adroit Industries (India) Limited
2. Asset Reconstruction Company (India) Limited
3. National Stock Exchange of India Limited
4. Sonaselection India Limited
5. Swastika Infra Limited

The existing Abridged Prospectus page-1 extractor evaluated all five after the source repairs:

- candidates: 5;
- downloaded: 5;
- extracted: 0;
- placeholders/missing: 5;
- fetch errors: 0.

Those nulls were preserved deliberately.

## Latest completed batch — provisional publication semantics and RHP issue-size diagnostic

PR #32 — `Preserve provisional status and diagnose RHP issue size`

Squash-merged:

`ce0d10a00e830a7606e909abe047bb2ee2e983ee`

### Publication semantics

Deterministic publication now preserves a retained field's explicit status when it is:

- `verified`;
- `provisional`;
- `conflict`.

Legacy retained non-null fields without a status continue to publish as `verified`, preserving backward compatibility. Retained corrections arrays are also preserved.

This closes the semantic blocker for future official-but-not-final RHP-derived values without misrepresenting them as final evidence.

### Read-only RHP issue-size diagnostic

Production workflow:

- `Sync live IPO data`
- run ID: `35694934742`
- conclusion: success

Measured result:

- candidates: 5;
- official RHP PDFs downloaded: 5;
- parseable explicit overall INR totals: 0;
- aggregate mentions inspected: 10;
- PDF fetch errors: 0.

Per issuer:

1. **Adroit Industries (India) Limited** — no supported explicit overall INR total.
2. **Asset Reconstruction Company (India) Limited** — the RHP's `Total Offer size` is a number of Equity Shares, not an INR amount.
3. **National Stock Exchange of India Limited** — overall `Total Offer Size` is a share count; ₹700 million is explicitly only the Employee Reservation Portion.
4. **Sonaselection India Limited** — no supported explicit overall INR total.
5. **Swastika Infra Limited** — overall Offer amount remains `₹[●]`; the explicit ₹12,900 lakh amount is the Fresh Issue component only.

No `issue_size_inr` field was written. This is the intended result under the no-arithmetic/no-component-substitution rule.

The temporary production diagnostic has been removed from the hourly workflow.

## Latest completed batch — minimum bid quantity source recovery

### Abridged Prospectus diagnostic

PR #34 — `Diagnose explicit minimum bid wording in Abridged Prospectuses`

Production run `35695985070`:

- candidates: 3;
- downloads: 3;
- explicit bid-lot/minimum-bid mentions on page 1: 0;
- fetch errors: 0.

No value was written.

### RHP diagnostic

PR #35 — `Diagnose minimum bid quantity from retained RHPs`

Production run `35696444839` scanned the retained RHPs deeply:

- Adroit Industries: Bid Lot / minimum Bid Lot remains `[●]` and is explicitly deferred to the later advertisement;
- National Stock Exchange of India: RHP Bid Lot remains `[●]`;
- Swastika Infra: RHP Bid Lot remains `[●]` and is deferred to the later advertisement.

No value was written.

### Final Prospectus diagnostic

PR #36 — `Diagnose minimum bid quantity from final Prospectus`

Production run `35696964894` found one missing-bid record with a retained final Prospectus:

- National Stock Exchange of India Limited;
- final Prospectus PDF page 10: `Bid Lot 8 Equity Shares ... in multiples of 8 Equity Shares`;
- later offer-procedure tables also state `Minimum Bid 8 Equity Shares`;
- candidates: 1;
- downloads: 1;
- fetch errors: 0.

### NSE Issue Information HTML probe

PR #38 — `Probe NSE Issue Information for finalized minimum bid quantity`

Production run `35697162672` fetched Active, Forthcoming and Past page variants for Adroit, NSE and Swastika:

- candidates: 3;
- pages fetched: 9;
- pages with raw-HTML Bid Lot / Minimum Order Quantity terms: 0;
- fetch errors: 0.

The responses were approximately 297 KB application shells. The official page renders finalized bid data dynamically, so raw HTML scraping is not a viable production source. PR #37 was an earlier stale version of this probe and was closed without merge.

### Final Prospectus extractor

PR #39 — `Extract explicit minimum bid from final Prospectus`

Squash-merged:

`0c0b0668690b2f50ebe57627b74abae7a3aec4ad`

Rules:

- scans only the normal first 20 PDF pages;
- accepts explicit numeric `Bid Lot X Equity Shares` or `Minimum Bid X Equity Shares`;
- rejects rupee-denominated anchor-investor minimums;
- rejects `[●]` placeholders;
- fills missing values only;
- does not copy `market_lot`;
- retains direct final-Prospectus PDF/page evidence;
- document-derived minimum-bid evidence takes publication precedence over generic NSE term fields when present.

Production run `35697515918`:

- candidates: 1;
- downloaded: 1;
- extracted: 1;
- explicit minimum-bid missing: 0;
- fetch errors: 0.

Published:

- **National Stock Exchange of India Limited — 8 Equity Shares — verified — final Prospectus PDF page 10**.

Bot data commit:

`2f6428c2138173a4ca02dc271100ed22412da31e`

Bot diff review confirmed only:

- `data/recovery/2026/nse-issue-information.json`;
- generated `data/ipos.json`

changed.

Minimum-bid coverage is now **14 present / 9 missing**.

GitHub Pages deployment for the bot revision passed in run `35697665129`.

Adroit Industries and Swastika Infra remain null because their available RHPs still use placeholders and no final Prospectus is retained yet.

## Latest completed batch — dynamic NSE ipo-detail minimum-bid automation

### Endpoint discovery

PR #41 — `Probe official NSE ipo-detail bid fields`

Squash-merged:

`b5d7d063b092ae511d0ad44b0c27ccb9a0dff2a7`

The production probe identified and verified the official backend used by NSE Issue Information:

`/api/ipo-detail?symbol=<SYMBOL>&series=<SERIES>`

Production run `35726755503`:

- candidates: 10;
- API successes: 10;
- responses with bid-related data: 10;
- fetch errors: 0.

The probe established that static terms are not typed top-level keys. They are `issueInfo.dataList` title/value pairs. Live-demand fields under `bidDetails`, `activeCat` and demand graphs are separate and are not used for minimum-bid extraction.

The same run exposed a stale homepage-order test: it hardcoded 2026-09-23 as the latest open date, but live discovery had added IPOs opening 2026-09-25. The test was repaired to derive newest/oldest dates from the current dataset, preserving the actual ordering invariant.

PR #42, which separately added diagnostic timeouts, was closed as superseded because the production extractor includes bounded request timeouts directly.

### Production extractor

PR #43 — `Extract minimum bid from official NSE ipo-detail`

Squash-merged:

`1b4e267de543bc909616392373099a38e257281a`

Rules:

- official NSE `/api/ipo-detail` only;
- deterministic retained symbol/series;
- parse only `issueInfo.dataList`;
- prefer `Minimum Order Quantity`;
- fall back to explicit `Bid Lot`;
- require a numeric quantity followed by `Equity Shares`;
- reject placeholders/unparseable text;
- if both official values parse but disagree, publish nothing and log a conflict;
- never substitute `market_lot`;
- fill missing `minimum_bid_quantity` only;
- retain exact endpoint/source identity and collection timestamp;
- 15-second bounded request timeout with retries.

Production run `35727346835`:

- candidates: 10;
- API successes: 10;
- extracted: 5;
- missing/placeholders: 5;
- conflicts: 0;
- fetch errors: 0.

Published verified values:

1. Adroit Industries (India) Limited — 111 Equity Shares
2. ArMee Infotech Limited — 40 Equity Shares
3. Elevate Campuses Limited — 41 Equity Shares
4. Swastika Infra Limited — 81 Equity Shares
5. Varmora Granito Limited — 101 Equity Shares

Bot data commit:

`9e787f2fbb41f4e55fa05ebd097fd98fc683f7b6`

Bot diff review confirmed only:

- `data/recovery/2026/nse-issue-information.json`;
- generated `data/ipos.json`

changed.

GitHub Pages deployment for the data revision passed in run `35727496988`.

### Legacy NSE identity recovery

PR #44 — `Recover legacy NSE identity from retained official URL`

Squash-merged:

`a1829632831d453337965e671ea34d4e1a279959`

Legacy records without normalized `nse_symbol`/`nse_series` may now use deterministic parameters already retained in an official NSE Issue Information URL. Only HTTPS `nseindia.com` URLs and EQ/SME series are accepted; no fuzzy name matching is used.

Production run `35727815131` then evaluated all remaining minimum-bid gaps, including Qualiance:

- candidates: 6;
- API successes: 6;
- extracted: 0;
- missing/placeholders: 6;
- conflicts: 0;
- fetch errors: 0.

Qualiance's retained official URL deterministically resolves to `QUALIANCE / SME`, but its current endpoint payload still has no finalized supported term, so the field remains null and its normalized identity is not rewritten merely for convenience.

### Current coverage

Published dataset: **25 IPOs**.

Minimum bid quantity:

- present: **19**;
- missing: **6**.

Remaining missing:

1. Bench Mark Infotech Services Limited
2. Himalayan Solar Limited
3. Coreintegra Consulting Services Limited
4. Pooja Logistics Limited
5. Axiom Gas Engineering Limited
6. Qualiance International Limited

All six are now actively checked by the official-source pipeline where a deterministic NSE identity is available. The latest run had zero network errors.

## Latest completed batch — NSE ipo-detail listing-date automation

### Read-only source diagnostic

PR #46 — `Diagnose explicit NSE ipo-detail listing dates`

Squash-merged:

`c7b35077f1d8f71ecd0e29e936a35b62250dcc81`

Production run `35731645033`:

- candidates / API successes: 26 / 26;
- responses containing an explicit listing date: 10;
- fetch errors: 0.

The production payloads established one supported shape:

- `metaInfo.listingDate`;
- strict ISO `YYYY-MM-DD`.

No alternate/free-form listing-date shape was needed. Current/upcoming records without a published date returned no usable value.

### Production extractor

PR #47 — `Extract explicit listing dates from NSE ipo-detail`

Squash-merged:

`c6134bbea181c46e97ade256c288289c915fff16`

Rules:

- official NSE `/api/ipo-detail` only;
- deterministic symbol/series identity, including the retained-official-URL legacy path;
- accept only exact `metaInfo.listingDate`;
- require a real ISO `YYYY-MM-DD` date;
- reject free-form/invalid dates;
- never infer from issue close date, T+ schedules, lifecycle status or settlement conventions;
- fill missing `listing_date` only;
- retain exact endpoint/source identity and collection timestamp.

Production run `35732506571`:

- candidates: 26;
- API successes: 26;
- extracted: 10;
- missing: 16;
- unparseable: 0;
- fetch errors: 0.

Published:

1. Asset Reconstruction Company (India) Limited — 2026-09-17
2. ESDS Software Solution Limited — 2026-09-04
3. Kanohar Electricals Limited — 2026-09-16
4. Karamtara Engineering Limited — 2026-09-17
5. LCC Projects Limited — 2026-09-17
6. Manipal Payment and Identity Solutions Limited — 2026-09-17
7. Pranav Constructions Limited — 2026-09-15
8. Qualiance International Limited — 2026-09-11
9. Rentomojo Limited — 2026-09-17
10. Veegaland Developers Limited — 2026-09-18

Bot data commit:

`a58cdac941a4a9116672951111e63b412ec2356e`

Bot diff review confirmed only:

- `data/recovery/2026/nse-issue-information.json`;
- generated `data/ipos.json`

changed.

GitHub Pages deployment for the bot revision passed in run `35732898054`.

### Current P1 coverage snapshot

Published dataset: **26 IPOs**.

- price band: **25/26**;
- issue price: **10/26**;
- issue size INR: **12/26**;
- market lot: **18/26**;
- minimum bid quantity: **20/26**;
- minimum application amount: **0/26**;
- open date: **26/26**;
- close date: **26/26**;
- listing date: **10/26**.

The 16 missing listing dates remain source-null and will be rechecked automatically.

## Latest completed batch — NSE ipo-detail price-band completion

### Read-only diagnostic

PR #49 — `Diagnose explicit NSE price-band terms`

Squash-merged:

`7adeae9331bdc9e58829da655f72f58b76d640e8`

Production run `35737565780` evaluated the only missing price-band record:

- candidate: Axiom Gas Engineering Limited;
- identity: `AXIOMGAS / SME`;
- supported term: `Price Range`;
- source text: `Rs.51 to Rs.54 per equity share`;
- API successes: 1;
- fetch errors: 0.

### Production extractor

PR #50 — `Extract explicit price bands from NSE ipo-detail`

Squash-merged:

`5acd0a5fab5920b999501120755753a57bc1ba68`

The extractor:

- reads only exact `Price Range` / `Price Band` title-value pairs from `issueInfo.dataList`;
- requires two explicit rupee-denominated bounds per Equity Share;
- rejects fixed single prices, placeholders and reversed/invalid bounds;
- rejects conflicting supported official values;
- fills missing `price_band` only;
- retains exact NSE endpoint/source identity and collection time;
- deterministic publication prefers retained price-band evidence when present.

Production run `35738252937`:

- candidates: 1;
- API successes: 1;
- extracted: 1;
- missing/placeholders: 0;
- conflicts: 0;
- fetch errors: 0.

Published:

- **Axiom Gas Engineering Limited — ₹51 to ₹54 per Equity Share — verified**.

Bot data commit:

`134e0e7a73e736ed3748906b198a8c883fd18892`

Bot diff review confirmed only:

- `data/recovery/2026/nse-issue-information.json`;
- generated `data/ipos.json`

changed.

Price-band coverage is now **26/26**.

## Latest completed batch — final issue price from NSE public past issues

### Detailed-endpoint diagnostic

PR #52 — `Diagnose explicit NSE issue-price terms`

Production run `35741820135` checked all four already-listed records whose final issue price was missing:

- candidates / API successes: 4 / 4;
- responses containing explicit `Issue Price`, `Final Issue Price`, or `Offer Price`: 0;
- fetch errors: 0.

This closed the `/api/ipo-detail` path for final price without using price-band caps.

### Public past-issues diagnostic

PR #53 — `Diagnose final prices from NSE public past issues`

PR #54 — `Run NSE past-issues final-price diagnostic`

Production run `35742801879` used:

`https://www.nseindia.com/api/public-past-issues`

Result:

- total past rows: 1,450;
- candidates: 4;
- exact symbol matches: 4;
- rows with parseable fixed `issuePrice`: 4;
- ambiguous symbol matches: 0.

Observed official values:

1. ARCIL — ₹139 — listing date 17-SEP-2026 — EQ
2. ESDS — ₹429 — listing date 04-SEP-2026 — EQ
3. KARAMTARA — ₹254 — listing date 17-SEP-2026 — EQ
4. QUALIANCE — ₹127 — listing date 11-SEP-2026 — SME

### Production extractor

PR #55 — `Extract final issue prices from NSE public past issues`

Squash-merged:

`0dcc101be97088ec565287fa4a5a63185ec8ea6c`

The extractor:

- targets only already-listed records with missing final issue price;
- requires one unique exact symbol match;
- cross-checks NSE security type / series when present;
- cross-checks the official past-row listing date against retained listing-date evidence;
- accepts only one fixed numeric issue price;
- rejects price ranges and placeholders;
- fills missing values only;
- retains `NSE Public Past Issues` URL/identity and collection timestamp;
- never treats the price-band cap as final price.

Production run `35743854058`:

- candidates: 4;
- exact matches: 4;
- extracted: 4;
- missing/unparseable: 0;
- rejected matches: 0.

Published verified values:

1. Asset Reconstruction Company (India) Limited — ₹139
2. ESDS Software Solution Limited — ₹429
3. Karamtara Engineering Limited — ₹254
4. Qualiance International Limited — ₹127

Bot data commit:

`8746f22505f8d79920923670d3a9381699c82d17`

Bot diff review confirmed only:

- `data/recovery/2026/nse-issue-information.json`;
- generated `data/ipos.json`

changed.

### Current P1 coverage snapshot

Published dataset: **26 IPOs**.

- price band: **26/26**;
- issue price: **14/26**;
- issue size INR: **12/26**;
- market lot: **18/26**;
- minimum bid quantity: **20/26**;
- minimum application amount: **0/26**;
- open date: **26/26**;
- close date: **26/26**;
- listing date: **10/26**.

All 12 remaining issue-price nulls are not yet listed or do not yet have a published listing date. They remain null intentionally; the hourly past-issues extractor will recover them after NSE publishes a completed-issue row.

## Latest completed batch — safe NSE ipo-detail aggregate issue-size extraction

### Read-only source diagnostic

PR #57 — `Diagnose NSE ipo-detail aggregate issue size`

Squash-merged:

`c817e01ca52b2c2af58bf32a5e53c4aeb0bc0706`

Production run `35748672356`:

- candidates: 14;
- API successes: 13;
- responses with supported overall-size title: 13;
- fetch errors: 1 temporary Moneyview timeout;
- data writes: 0.

Observed source classes:

1. **Share-count only** — no INR aggregate, therefore remain null.
2. **Mixed Fresh Issue + OFS** — component prose would require arithmetic or share-price conversion, therefore remain null.
3. **Pure one-leg INR offer** — a sole Fresh Issue / OFS amount is the complete offer and can be accepted without arithmetic.

Safe live examples:

- ArMee Infotech Limited — pure Fresh Issue aggregating up to **Rs. 30,000 Lakhs**;
- Elevate Campuses Limited — pure Fresh Issue aggregating up to **Rs. 21,000 million**.

Rejected examples include:

- Axiom — Fresh Issue stated only as 93,98,000 Equity Shares;
- Swastika — INR Fresh Issue plus OFS share count;
- Varmora — INR Fresh Issue plus OFS share count;
- ARCIL — OFS share count only.

### Production extractor

PR #58 — `Extract safe aggregate issue size from NSE ipo-detail`

Squash-merged:

`09e1eb9166d73cc1d71e8994821238ce5468897c`

Rules:

- official NSE `/api/ipo-detail` only;
- exact overall `Issue Size` / `Total Issue Size` / `Offer Size` title;
- strip parenthetical carve-outs before evaluating the top-level offer;
- accept only a sole Fresh Issue or sole OFS leg when it is explicitly INR-denominated;
- support crore/million/lakh/lac unit conversion;
- never sum multiple offer legs;
- never convert share counts via issue price;
- reject share-count-only and mixed-leg prose;
- fill missing `issue_size_inr` only;
- retain exact endpoint evidence and collection timestamp.

Production run `35749978275`:

- candidates: 14;
- API successes: 14;
- extracted: 2;
- unsupported/share-count rows: 12;
- conflicts: 0;
- fetch errors: 0.

Published verified values:

1. ArMee Infotech Limited — ₹3,000,000,000
2. Elevate Campuses Limited — ₹21,000,000,000

Bot data commit:

`ccdf8f308f437257d64b2e9b3bd99eb9729eaa57`

Bot diff review confirmed only:

- `data/recovery/2026/nse-issue-information.json`;
- generated `data/ipos.json`

changed.

GitHub Pages deployment for the bot revision passed in run `35750326661`.

### Current P1 coverage snapshot

Published dataset: **26 IPOs**.

- price band: **26/26**;
- issue price: **14/26**;
- issue size INR: **14/26**;
- market lot: **18/26**;
- minimum bid quantity: **20/26**;
- minimum application amount: **0/26**;
- open date: **26/26**;
- close date: **26/26**;
- listing date: **10/26**.

The 12 remaining issue-size nulls are source-blocked under the currently supported official patterns. Existing hourly NSE/final-Prospectus automation will re-evaluate them as authoritative source data changes.

## Latest completed batch — NSE ipo-detail market-lot extraction

### Read-only diagnostic

PR #60 — `Diagnose explicit NSE market-lot terms`

Squash-merged:

`dffde0af935447556e7751c27930fb872798a1de`

Production run `35757461876` evaluated all eight missing market-lot records:

- candidates: 8;
- API successes: 8;
- explicit `Market Lot` / `Lot Size` responses: 1;
- fetch errors: 0.

Observed supported value:

- Axiom Gas Engineering Limited — `Lot Size: 2000 Equity Shares`.

No explicit Market Lot / Lot Size field was published by NSE for:

1. Moneyview Limited
2. Adroit Industries (India) Limited
3. ArMee Infotech Limited
4. Elevate Campuses Limited
5. Swastika Infra Limited
6. Varmora Granito Limited
7. National Stock Exchange of India Limited

Their existing Bid Lot / Minimum Order Quantity values were not reused as market lot.

### Production extractor

PR #61 — `Extract explicit market lot from NSE ipo-detail`

Squash-merged:

`9ed4044be6ae795bbf5373b0a7bb2530bba44960`

Rules:

- official NSE `/api/ipo-detail` only;
- exact `Market Lot` / `Lot Size` terms only;
- positive Equity Share quantity required;
- Bid Lot / Minimum Order Quantity excluded;
- placeholders rejected;
- conflicting supported values retained as null;
- fill missing `market_lot` only;
- retain exact endpoint/source identity and collection timestamp;
- retained market-lot evidence takes publication precedence over legacy feed terms when present.

Production run `35758162829`:

- candidates: 8;
- API successes: 8;
- extracted: 1;
- missing/placeholders: 7;
- conflicts: 0;
- fetch errors: 0.

Published:

- **Axiom Gas Engineering Limited — 2,000 Equity Shares — verified**.

Bot data commit:

`fbe718e911d9649e9a6007a9c2922af23b397816`

Bot diff review confirmed only:

- `data/recovery/2026/nse-issue-information.json`;
- generated `data/ipos.json`

changed.

### Current P1 coverage snapshot

Published dataset: **26 IPOs**.

- price band: **26/26**;
- issue price: **14/26**;
- issue size INR: **14/26**;
- market lot: **19/26**;
- minimum bid quantity: **20/26**;
- minimum application amount: **0/26**;
- open date: **26/26**;
- close date: **26/26**;
- listing date: **10/26**.

The seven remaining market-lot nulls are source-null under the supported NSE pattern and will be rechecked automatically.

## Latest completed batch — NSE minimum-application source survey

### Read-only diagnostic

PR #63 — `Diagnose explicit NSE minimum application amount terms`

The diagnostic scans only static `issueInfo.dataList` titles whose normalized label contains:

- `minimum`; and
- `application` or `investment`.

It does not inspect Minimum Order Quantity, Bid Lot, Market Lot, price band or arithmetic combinations.

The first all-universe run (`35759732510`) was later cancelled by workflow concurrency, but its minimum-application diagnostic step had already completed successfully: 26 candidates, 26 official NSE API successes, 0 responses with explicit minimum-application/investment terms, and 0 fetch errors.

PR #65 — `Bound minimum-application diagnostic sample`

Squash-merged:

`8ba821f8de6013dcdc56f19cbb5040e6a6e3055f`

The replacement diagnostic sampled six deterministic NSE identities covering Mainboard/SME and upcoming/open/listed states.

Production run `35760191175`:

- candidates: 6;
- API successes: 6;
- responses with explicit minimum-application/investment terms: 0;
- fetch errors: 0.

Checked:

1. Adroit Industries (India) Limited — EQ
2. Asset Reconstruction Company (India) Limited — EQ
3. Axiom Gas Engineering Limited — SME
4. Bench Mark Infotech Services Limited — SME
5. Qualiance International Limited — SME
6. Varmora Granito Limited — EQ

Every result returned an empty supported-term list.

### Decision

No `minimum_application_amount_inr` value was written.

Published coverage remains:

- present: **0/26**;
- missing: **26/26**.

The field remains distinct from market lot and minimum bid quantity. We will not calculate price × quantity or use the upper price-band bound as a substitute because the current data contract requires source-supported values.

The one-shot production diagnostic has been removed from hourly execution.

## Recommended next coherent batch

Survey retained official **SEBI Abridged Prospectus / RHP / final Prospectus PDFs** for an explicitly stated minimum application amount in INR.

Acceptance rules:

- official retained SEBI document only;
- explicit labelled INR amount only;
- page-level evidence required;
- fill missing `minimum_application_amount_inr` only;
- keep market lot / minimum bid quantity / minimum application amount distinct;
- no shares × price calculation;
- no price-band-cap inference;
- preserve null for share-count-only, placeholders or ambiguous/derived wording.

If the retained offer documents also do not state this value explicitly, record the field as source-blocked rather than synthesizing it.

## Publication history

- PR #1: source-backed data foundation
- PR #2–#8: bounded 2026 recovery/enrichment batches
- PR #9: automated NSE live discovery/publication
- PR #10: automated SEBI document discovery
- PR #11: live SEBI parser repair
- PR #12: bounded targeted SEBI fallback
- PR #13: SEBI general-filings coverage
- PR #14: token-oriented targeted search
- PR #15: mixed Public Issues coverage
- PR #16: Abridged Prospectus issue-size extraction
- Production issue-size bot commit: `92f0f024367b20a9f023218a0cb92ecbc2e38636`
- PR #17: direct SEBI Prospectus PDF resolution
- Prospectus attachment bot commit: `0c3e1c199fdb12266589c7f65eead373c49065dd`
- PR #18: explicit final issue-price extraction from SEBI Prospectus PDFs
- Initial final issue-price bot commit: `f9b7155c42d8b44d6985d9dafb9fd242e37dc64e`
- PR #20: read-only diagnostic for unresolved Prospectus price wording
- PR #21: labelled final Prospectus cover-price repair
- Completed final issue-price bot commit: `51f806b16e4eba40efee304d07bb5753a8e0f9d9`
- PR #23: read-only diagnostic for final Prospectus aggregate-size wording
- PR #24: explicit aggregate issue-size extraction from final SEBI Prospectuses
- Final Prospectus issue-size bot commit: `0110d864235eccb800efa5b206fa19bf9cdb0fb4`
- PR #28: SEBI listing cache-freshness repair
- PR #29: malformed live RHP-anchor issuer identity repair
- RHP/Abridged source-recovery bot commit: `ec684bc1fa558f2dafb7c7b90df6b750fc6f79ac`
- PR #30: direct SEBI RHP PDF resolution
- RHP PDF attachment bot commit: `3c2f3fb8a8737fe2067aab3e18e39ab86a68eeb6`
- PR #32: retained provisional-status publication + read-only RHP issue-size diagnostic
- PR #34: Abridged Prospectus minimum-bid diagnostic
- PR #35: RHP minimum-bid diagnostic
- PR #36: final Prospectus minimum-bid diagnostic
- PR #38: NSE Issue Information dynamic-page probe
- PR #39: explicit final-Prospectus minimum-bid extraction
- Minimum-bid bot commit: `2f6428c2138173a4ca02dc271100ed22412da31e`
- PR #41: official NSE ipo-detail endpoint discovery
- PR #43: NSE ipo-detail minimum-bid production extraction
- NSE ipo-detail minimum-bid bot commit: `9e787f2fbb41f4e55fa05ebd097fd98fc683f7b6`
- PR #44: deterministic legacy NSE identity recovery
- PR #46: NSE ipo-detail listing-date diagnostic
- PR #47: strict NSE ipo-detail listing-date extraction
- NSE listing-date bot commit: `a58cdac941a4a9116672951111e63b412ec2356e`
- PR #49: Axiom NSE price-band diagnostic
- PR #50: strict NSE ipo-detail price-band extraction
- Price-band completion bot commit: `134e0e7a73e736ed3748906b198a8c883fd18892`
- PR #52: listed NSE ipo-detail issue-price diagnostic
- PR #53–#54: NSE public past-issues final-price diagnostic/wiring
- PR #55: strict NSE public past-issues final-price extraction
- NSE final-price bot commit: `8746f22505f8d79920923670d3a9381699c82d17`
- PR #57: NSE ipo-detail aggregate issue-size diagnostic
- PR #58: safe one-leg NSE ipo-detail issue-size extraction
- NSE ipo-detail issue-size bot commit: `ccdf8f308f437257d64b2e9b3bd99eb9729eaa57`
- PR #60: NSE ipo-detail market-lot diagnostic
- PR #61: strict NSE ipo-detail market-lot extraction
- NSE market-lot bot commit: `fbe718e911d9649e9a6007a9c2922af23b397816`
- PR #63: NSE minimum-application source diagnostic
- PR #65: bounded NSE minimum-application diagnostic sample


## Latest completed batch — SEBI Abridged Prospectus minimum-application survey

PR #68 — `Survey Abridged Prospectus minimum application amounts` — added a read-only page-1 diagnostic over retained official SEBI Abridged Prospectuses.

Squash-merged:

`07417895888f2fc11b68e4532104cedff39577bb`

Production sync run `35761261256` completed successfully.

Results:

- retained Abridged Prospectus candidates: **16**
- PDFs downloaded successfully: **16/16**
- responses with an explicit supported INR minimum-application / minimum-investment mention on page 1: **0**
- supported mentions: **0**
- fetch errors: **0**
- data writes from the diagnostic: **0**

The survey required both a supported minimum-application / minimum-investment label and a nearby explicit INR / Rs / ₹ amount. Share-count-only wording, bid lot, minimum order quantity and maximum-application wording were not accepted.

### Decision

No `minimum_application_amount_inr` value is published from the Abridged Prospectus page-1 source family.

Coverage remains **0/26**. This is intentionally source-null rather than derived.

The one-shot diagnostic has been removed from hourly execution after measurement. Its pure parser helper remains available for future manual checks.

### Recommended next coherent batch

Survey retained official **SEBI RHP PDFs**, followed by final Prospectus PDFs where necessary, for explicit labelled INR application amounts across the full document text.

Acceptance rules:

- official retained SEBI PDF only;
- explicit labelled INR application / investment amount only;
- page-level evidence required;
- no shares × price calculation;
- no price-band-cap inference;
- do not reinterpret bid lot, minimum order quantity or share-count wording as an amount;
- fill missing values only;
- preserve null when wording is absent, derived, placeholder or ambiguous.


## Latest completed batch — full-document RHP minimum-application classification

PR #70 — `Survey RHP minimum application amounts` — introduced a strict read-only full-document survey over retained official SEBI RHP PDFs.

Squash-merged:

`d237b5f8f418ba5d4cd5de2e0d60cdd6f29f0a4d`

Production sync run `35765946080` completed successfully and scanned the complete retained RHP set before a later bounding change was added for subsequent runs.

Full-run results:

- retained RHP candidates: **14**
- PDFs downloaded: **14/14**
- pages scanned: **7,593**
- documents with at least one labelled INR minimum-application/investment mention: **14/14**
- captured labelled mentions: **28**
- fetch errors: **0**
- data writes from the diagnostic: **0**

### Classification of the matches

The RHP evidence proves that `minimum application` is not a single issuer-wide concept.

Observed source classes:

1. **Anchor / QIB Mutual Fund minimum application size**
   - commonly `₹100 million`, `₹100,000,000`, or `₹1,000 lakhs`;
   - this belongs to Anchor/QIB bidding rules and is not the ordinary retail minimum.

2. **Non-Institutional Investor (NII) minimum application size**
   - Sonaselection India Limited — **₹0.20 million = ₹200,000**, PDF page 92;
   - Swastika Infra Limited — **₹2.00 lakh = ₹200,000**, PDF pages 77 and 411.

3. **Unrelated “minimum investment” prose**
   - examples include industry-policy investment thresholds or ARC regulatory investment requirements;
   - these are not IPO application amounts.

4. **Category-specific application wording without one generic investor-independent amount**
   - several RHPs describe NII or Anchor rules but do not state one universal application amount applicable across investor classes.

### Decision

Do **not** publish an RHP-derived value into the current generic `minimum_application_amount_inr` field.

Selecting a category-specific Anchor/QIB or NII amount would collapse different investor rules into one misleading number. The existing generic field therefore remains **0/26**.

The one-shot RHP diagnostic is removed from hourly execution after this measurement. The manual diagnostic remains available and is no longer artificially bounded, so it can re-scan the full retained set when intentionally invoked.

### Recommended next coherent batch

Refine the data contract before any further application-amount extraction.

Design and test an investor-category-specific representation, for example:

- retail minimum application amount;
- NII minimum application amount;
- Anchor/QIB minimum application amount;
- related minimum bid quantity / bid-lot rule;
- source page, source status and source identity per category.

Acceptance criteria:

- preserve backward compatibility for existing published records;
- do not reinterpret the existing generic field silently;
- document category semantics explicitly;
- keep monetary amount and share quantity separate;
- retain page-level official evidence;
- no price × quantity derivation unless a future field is explicitly defined as derived and clearly labelled as such;
- only add categories that can be sourced consistently from official documents.

Until this contract exists, further minimum-application extraction should remain diagnostic-only.


## Latest completed batch — investor-category application requirements contract

PR #73 — `Add investor-category application requirements contract` — introduces an additive data model for application requirements without redefining the existing generic fields.

### Contract change

Published schema version advances from **1.1.0 to 1.2.0**.

Every IPO record now includes:

`application_requirements`

with exactly three investor categories:

- `retail`
- `non_institutional`
- `anchor_investor`

Each category contains two separate evidence-bearing fields:

- `minimum_application_amount_inr`
- `minimum_bid_quantity`

These nested fields use the same `value / status / evidence / corrections` contract as existing source-backed fields.

### Backward compatibility

The legacy top-level fields remain unchanged:

- `minimum_application_amount_inr`
- `minimum_bid_quantity`

The generic minimum-application field is **not** populated from category-specific RHP evidence and remains source-null.

The homepage/UI is intentionally unchanged in this batch. Consumers that only use existing fields continue to work, while new consumers can opt into the category-specific structure.

### Initial publication state

All new category-specific fields publish as:

- value: `null`
- status: `missing`
- evidence: `[]`
- corrections: `[]`

This creates the contract first without silently importing ambiguous values.

### Validation

The validator now requires:

- exactly the three supported investor categories;
- exactly amount + bid-quantity fields within each category;
- normal evidence-bearing field invariants for every nested field;
- verified values to retain evidence;
- missing fields to remain null.

The deterministic publisher now supports retaining future source-backed category values from recovery manifests.

Validation passed, including:

- recovery publication synchronization;
- schema 1.2.0 core invariants;
- existing NSE / SEBI parser and extraction tests.

### Recommended next coherent batch

Implement the **first strict category-specific extractor**, starting with Non-Institutional Investor minimum application amounts from retained RHP evidence.

Initial known source-backed examples from the completed RHP survey:

- Sonaselection India Limited — NII minimum application amount **₹200,000** — RHP PDF page 92;
- Swastika Infra Limited — NII minimum application amount **₹200,000** — RHP PDF pages 77 and 411.

Acceptance rules:

- write only `application_requirements.non_institutional.minimum_application_amount_inr`;
- require explicit NII / Non-Institutional context plus explicit labelled INR amount;
- retain exact PDF page and source identity;
- reject Anchor/QIB Mutual Fund minimums;
- reject unrelated investment thresholds;
- no price × quantity calculation;
- fill missing values only;
- validate across multiple retained RHPs before enabling recurring production extraction.


## Latest completed batch — production NII minimum application extraction

PR #75 — `Extract explicit RHP NII minimum application amounts` — added recurring production extraction for:

`application_requirements.non_institutional.minimum_application_amount_inr`

from retained official SEBI RHP PDFs.

Merged:

`4290dc11d5fc04c4303e0259bff39f1aa1932527`

### Production rules

The extractor:

- scans retained official SEBI RHP PDFs only;
- is bounded to the first **140 PDF pages** per candidate for recurring cost control;
- requires a direct labelled minimum-application amount;
- requires nearby `Non-Institutional` / NII category context;
- supports explicitly stated INR, million, lakh/lac and crore units;
- rejects Anchor/QIB Mutual Fund minimums;
- rejects unrelated business/regulatory minimum-investment text;
- rejects conflicting amounts;
- fills missing NII category values only;
- retains exact PDF page and source identity;
- never calculates shares × price;
- never changes the legacy top-level `minimum_application_amount_inr`.

### First production run

Sync run `35793315717` completed successfully.

Results:

- candidates: **14**
- PDFs downloaded: **14**
- extracted: **1**
- explicit NII amount missing under the first parser rule: **13**
- conflicts: **0**
- fetch errors: **0**

Published:

- **Swastika Infra Limited — ₹200,000 — verified — RHP page 77**

Source-backed data commit:

`3ca407639d5d11432816167c98f6add93892148e`

### Sonaselection parser repair

The earlier full-RHP survey had already observed:

- **Sonaselection India Limited — ₹200,000 — RHP page 92**

Its wording placed `Non-Institutional Portion` immediately **after** the labelled amount:

`minimum application size viz. ₹ 0.20 million ... Non-Institutional Portion`

The first production parser checked only backward context and therefore missed it.

PR #76 — `Fix forward NII context detection` — expanded the strict category check to a tight two-sided context window while preserving the direct-label and explicit-INR requirements.

Merged:

`c77472f26d1f93f999c64773de3bea1c4d199dfc`

Regression coverage includes the actual Sonaselection sentence shape.

Because the post-merge hourly workflow was not advancing reliably enough to complete verification in this run, the already-observed official page-92 evidence from completed diagnostic run `35765946080` was published directly in PR #77.

PR #77 — `Repair Sonaselection NII minimum application amount` — merged as:

`758c120fb1542af42415c4dbe83a06cd8f220fd1`

The repair passed:

- recovery/publication synchronization;
- schema 1.2.0 validation;
- all existing parser/extractor tests.

Current published NII minimum-application coverage:

- present: **2/26**
- missing: **24/26**

Verified values:

1. **Sonaselection India Limited — ₹200,000 — RHP page 92**
2. **Swastika Infra Limited — ₹200,000 — RHP page 77**

The generic top-level minimum-application field remains unchanged and source-null.

### Recommended next coherent batch

Continue the category-specific application contract with a **read-only source survey for explicit NII minimum bid quantity** from retained RHPs before enabling production extraction.

Acceptance rules:

- write only `application_requirements.non_institutional.minimum_bid_quantity`;
- require explicit Non-Institutional/NII context;
- require an explicit share quantity / bid requirement;
- keep amount and quantity separate;
- reject generic/retail bid-lot wording unless clearly NII-specific;
- retain page-level official evidence;
- do not infer quantity from the ₹200,000 threshold or issue price;
- validate across multiple RHPs before enabling recurring writes.

After NII quantity semantics are stable, survey explicit retail application requirements separately rather than deriving retail monetary amounts from price × lot.
