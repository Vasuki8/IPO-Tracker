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


## Latest completed batch — NII minimum bid quantity source survey

PR #79 — `Survey RHP NII minimum bid quantities` — added a strict read-only survey for:

`application_requirements.non_institutional.minimum_bid_quantity`

across retained official SEBI RHP PDFs.

Merged:

`df130bfdc4dc0940e4f9a47c61cd156615bbcdd4`

The survey required:

- an explicit share count;
- nearby `Non-Institutional` / NII category context;
- direct minimum-bid / minimum-application-size share wording;
- no amount-to-quantity calculation;
- no generic bid-lot reinterpretation.

### Production measurement

Sync run `35801899974` completed the NII quantity diagnostic successfully before the later one-shot cleanup cancelled the unrelated downstream NII-amount step.

Results:

- retained RHP candidates: **14**
- PDFs downloaded: **14/14**
- pages scanned: **7,588**
- documents with an explicit NII share quantity: **0**
- explicit NII share-quantity mentions: **0**
- fetch errors: **0**
- data writes from the diagnostic: **0**

Every retained RHP in the current 2026 universe therefore failed the strict explicit-share-quantity test.

### Decision

Do **not** populate `application_requirements.non_institutional.minimum_bid_quantity` from the current RHP source family.

NII rules in these documents are expressed through monetary thresholds / category rules rather than a direct category-specific minimum share count.

The tracker will not derive the quantity from:

- the ₹200,000 NII application threshold;
- issue price or price-band cap;
- generic Bid Lot;
- top-level minimum bid quantity;
- arithmetic rounding to lot multiples.

Current NII minimum-bid-quantity coverage remains:

- present: **0/26**
- missing: **26/26**

This is a deliberate source-null result, not a parser failure.

PR #80 — `Remove completed NII bid-quantity survey` — removed the one-shot diagnostic from hourly execution while retaining the manual diagnostic helpers.

Merged:

`a1c2cc1798ccec2058dde274cf557997d16521ef`

### Recommended next coherent batch

Survey official retained offer documents for **explicit retail application requirements**, beginning with:

`application_requirements.retail.minimum_application_amount_inr`

Acceptance rules:

- require explicit Retail Individual Bidder / Retail Individual Investor context;
- require an explicit INR minimum application amount;
- retain exact PDF page and source identity;
- do not derive amount from price × lot;
- keep amount and share quantity separate;
- reject generic application amounts without clear retail context;
- reject maximum application limits;
- fill missing values only;
- survey first, then enable production extraction only if wording is consistent across multiple documents.

If retail monetary amounts are also source-null, separately survey explicit retail minimum bid quantities rather than deriving them.


## Latest completed batch — retail minimum application amount source survey

The retail application-amount source family has now been measured across retained official offer documents without using any derived arithmetic.

### Existing RHP evidence reuse

The earlier full-RHP minimum-application diagnostic had already scanned **14/14 retained official SEBI RHP PDFs across 7,593 pages**.

Reviewing its captured minimum-application contexts for explicit Retail Individual Bidder / Retail Individual Investor wording found no source-backed retail INR minimum amount.

Where retail wording was present, the RHPs stated a **minimum Bid Lot** rule. Explicit monetary minimums such as **₹200,000** belonged to the Non-Institutional category.

### Final Prospectus survey

PR #82 — `Survey final Prospectus retail minimum application amounts` — added a strict read-only full-document survey for:

`application_requirements.retail.minimum_application_amount_inr`

Merged:

`cbbe247e0107ec7f95649204c4c0b57ddfb30335`

Production sync run `35804488536` scanned 9/10 retained final Prospectus PDFs successfully:

- downloaded: **9/10**
- pages scanned: **4,786**
- documents with an explicit Retail Individual minimum INR amount: **0**
- qualifying mentions: **0**
- one unresolved PDF: Kanohar Electricals Limited, where unbounded text extraction was terminated

The survey required:

- explicit Retail Individual Bidder / Retail Individual Investor context;
- an explicitly labelled minimum application amount;
- an explicit INR / Rs / ₹ amount;
- no maximum-application wording;
- no NII amount reuse;
- no generic amount without retail context;
- no price × lot derivation.

### Kanohar targeted retry

PR #83 — `Retry Kanohar retail minimum application survey` — retried only Kanohar with a bounded **650-page** scan.

Merged:

`be115a1f4bba4f5f4efe818ed626f12c8b6769db`

Production retry result:

- candidates: **1**
- downloaded: **1**
- pages scanned: **511**
- explicit retail minimum-INR mentions: **0**
- fetch errors: **0**

This closes the one unresolved final Prospectus.

### Decision

Do **not** populate `application_requirements.retail.minimum_application_amount_inr` from the current retained RHP/final-Prospectus source family.

Current retail minimum-application coverage remains:

- present: **0/26**
- missing: **26/26**

This is a deliberate **source-null** result.

The tracker will not derive retail minimum application amount from:

- issue price × bid lot;
- price-band cap × bid lot;
- top-level market lot;
- generic minimum bid quantity;
- any assumed retail lot multiple.

PR #84 — `Remove completed retail minimum application survey` — removed the one-shot retail diagnostic from hourly execution and restored the full-universe/full-document diagnostic as a manual tool.

Merged:

`f8382dca5fff476424976527142693fafa428cd4`

### Recommended next coherent batch

Survey retained official offer documents for explicit:

`application_requirements.retail.minimum_bid_quantity`

Acceptance rules:

- require explicit Retail Individual Bidder / Retail Individual Investor context;
- require an explicit share quantity / minimum Bid Lot rule;
- retain exact PDF page and source identity;
- keep quantity separate from monetary application amount;
- reject NII/Anchor quantity rules;
- reject generic Bid Lot wording unless the retail applicability is explicit;
- do not infer quantity from ₹ thresholds or issue price;
- survey first, then enable recurring extraction only if wording is consistent across multiple documents.

If retail minimum bid quantity proves consistently source-backed, it can become the primary retail application requirement shown to users while retail monetary amount remains null.


## Latest scope decision — lot size only

The user has explicitly narrowed the application-term scope:

> Find just **Lot Size**. Minimum investment / minimum application amount is not needed.

This instruction overrides the earlier application-amount recovery roadmap.

### Product behavior

The website now exposes a single user-facing **Lot Size** value.

Display rule:

1. use verified `market_lot` when present;
2. otherwise use verified `minimum_bid_quantity` as the official share-quantity fallback;
3. never calculate a monetary minimum;
4. never calculate shares from price;
5. preserve the underlying raw evidence fields internally for provenance/backward compatibility.

This is a display rule only. It does **not** overwrite a null `market_lot` with a different raw field.

### Current 2026 lot-size coverage

Published IPOs: **26**

User-facing Lot Size present: **26/26**

- direct `market_lot`: **19/26**
- verified `minimum_bid_quantity` fallback: **7/26**
- missing user-facing Lot Size: **0/26**

The seven fallback records are:

1. Moneyview Limited — 441 shares
2. Adroit Industries (India) Limited — 111 shares
3. ArMee Infotech Limited — 40 shares
4. Elevate Campuses Limited — 41 shares
5. Swastika Infra Limited — 81 shares
6. Varmora Granito Limited — 101 shares
7. National Stock Exchange of India Limited — 8 shares

Every fallback value is already retained as verified official-source share-quantity evidence.

### UI cleanup

Minimum investment / minimum application amount is removed from:

- homepage desktop IPO table;
- mobile IPO cards;
- detail-page KPI strip;
- IPO details list.

The desktop column is now simply **Lot size**.

### Automation cleanup

The recurring RHP NII minimum-application extractor is removed from the hourly live-data workflow.

Historical application-amount fields and manual parsers remain in the data contract/codebase for backward compatibility, but future development must not spend time recovering minimum-investment/application amounts unless the user explicitly re-enables that scope.

### Next priority

Continue improving trustworthy IPO data while treating **Lot Size as complete at the user-facing layer (26/26)**.

Do not start further minimum-investment/application-amount recovery.


## Latest completed batch — verified-only Lot Size display

The lot-size-only UI introduced in PR #86 has been hardened so the canonical displayed Lot Size accepts **verified source-backed fields only**.

### Rule

User-facing Lot Size now resolves as:

1. verified `market_lot`;
2. otherwise verified `minimum_bid_quantity`;
3. otherwise null.

A non-null value with status `provisional`, `conflict`, or any non-verified state is no longer eligible for display.

This prevents a future live-source change from surfacing an unverified Lot Size merely because the raw numeric value is non-null.

### Current production state

The current 26-record 2026 dataset remains unchanged:

- user-facing Lot Size: **26/26**
- all 26 selected values are verified;
- 19 use verified `market_lot`;
- 7 use verified `minimum_bid_quantity` fallback;
- no data values were rewritten.

### Tests

Dedicated lot-size tests now cover:

- verified market-lot precedence;
- verified minimum-bid fallback;
- provisional market-lot rejection with verified fallback;
- conflict rejection;
- provisional fallback rejection;
- fully missing case.

### Handoff / next task

Application amount / minimum-investment work remains explicitly out of scope.

The next data-quality batch should move to the remaining homepage data gaps rather than application terms. Current major gaps are:

- issue price: **14/26 present**;
- issue size: **14/26 present**;
- listing date: **13/26 present**.

Most missing issue prices/listing dates belong to open or upcoming IPOs and should remain null until the official source publishes them.

Recommended next coherent batch: **re-audit the 12 missing issue-size records against the latest retained official SEBI/NSE documents**, but do not repeat already-proven source families unless new documents or source observations have appeared. If no new authoritative evidence exists, record the remaining issue-size nulls as current source-blockers and move to freshness/operations work.


## Latest completed batch — 12-record issue-size re-audit

The post-Lot-Size P1 issue-size re-audit is complete. The published 2026 universe still has **14/26 verified issue sizes** and **12/26 source-null issue sizes**.

This batch intentionally did **not** repeat source families that had already been exhaustively measured unless the official evidence set had changed.

### Baseline recheck

The latest successful hourly source run re-tested all 12 missing issue-size records against the currently supported NSE and Abridged Prospectus paths:

- NSE `/api/ipo-detail` issue-size candidates: **12**
- NSE API successes: **12/12**
- new supported INR totals: **0**
- unsupported/share-count responses: **12**
- conflicts: **0**
- fetch errors: **0**

Abridged Prospectus recheck:

- candidates: **5**
- PDFs downloaded: **5/5**
- new numeric total Offer/Issue sizes: **0**
- placeholders / missing supported totals: **5**
- fetch errors: **0**

There were no missing issue-size records with a newly retained final Prospectus eligible for the existing production extractor.

### New official evidence identified

Only two missing records had genuinely new official evidence relative to the earlier issue-size surveys:

1. **Moneyview Limited** — newly retained official SEBI RHP PDF.
2. **Qualiance International Limited** — retained SEBI filing classified as `Other Documents`, whose attached official PDF had not previously been resolved.

PR #88 — `Audit newly available issue-size evidence` — merged as:

`8955cc5985ec342eec43902baa2c286b4ca64f35`

It added a reusable SEBI source repair:

- existing `SEBI Other Document` filing pages can now resolve attached official `/sebi_data/attachdocs/...pdf` files;
- the PDF remains typed **SEBI Other Document PDF**;
- it is **not** relabelled as a final Prospectus;
- source identity, publication date and collection time are retained.

Production run `35816379147` resolved:

- Other Document PDF candidates: **1**
- resolved PDFs: **1**
- resolution errors: **0**

Resolved:

- **Qualiance International Limited**
- official SEBI PDF: `1789025406710_1349.pdf`

The source-evidence attachment was published by bot commit:

`0afface6b29a2e5d60d7cc575b2e0f358bdb44ac`

No issue-size value was written.

### Qualiance result

The resolved official PDF was scanned through the same strict aggregate issue-size parser.

Page 1 explicitly showed a `Total Issue Size` column, but the amount remained **`[●]`**. The Fresh Issue aggregate was also **`₹ [●] lakhs`**.

Result:

- pages scanned: **20**
- supported overall INR total: **none**
- issue size remains null.

### Moneyview transfer repair and result

The first Moneyview RHP attempt reached the official source but the Node PDF body transfer terminated before parsing.

PR #89 — `Retry terminated SEBI PDF transfers` — merged as:

`702292315dc3ba510d46235c010d798f6e95d66f`

The PDF loader now:

- keeps the normal bounded Node fetch/retry path first;
- falls back to bounded `curl` only after those attempts fail;
- uses the same validated official SEBI URL;
- requires a `%PDF-` file signature;
- uses bounded connect/overall timeouts and retries;
- does not change extraction semantics.

Production run `35816892862` then completed the diagnostic successfully:

- candidates: **2**
- downloaded: **2/2**
- fetch errors: **0**
- parseable overall totals: **0**

Moneyview RHP evidence:

- page 3: overall Offer aggregate remains **`₹ [●] million`**;
- Fresh Issue is explicitly stated as **up to ₹7,500 million**;
- the Offer also contains an OFS whose INR aggregate remains `[●]`.

The tracker does **not** publish ₹7,500 million as the total issue size because it is only one component of the overall Offer. It also does not derive the missing OFS/overall amount from shares or price.

### Decision

No new `issue_size_inr` values are published from this re-audit.

Current issue-size coverage remains:

- verified: **14/26**
- missing/source-null: **12/26**

The remaining nulls are now blocked by current official-source content rather than an untested source family:

- current NSE issue-size terms are share-count/unsupported for all 12;
- current eligible Abridged Prospectuses do not expose numeric aggregate totals;
- previously retained RHP/final-Prospectus families have already been measured;
- Moneyview overall Offer remains a placeholder despite an explicit Fresh Issue component;
- Qualiance total issue size remains a placeholder in its newly resolved official PDF;
- several live SME records still have no deterministic SEBI offer-document match.

The one-shot Moneyview/Qualiance diagnostic and its hard-coded candidate list are removed from recurring execution after this measurement.

Reusable improvements retained:

- neutral SEBI Other Document PDF resolution;
- robust bounded SEBI PDF transfer fallback.

### Handoff / next coherent batch

**Do not repeat issue-size source recovery until new authoritative source evidence appears.**

Lot Size remains **26/26 verified** and minimum-investment/application-amount work remains out of scope.

The next coherent priority is **operational freshness / source-health visibility**. Start by auditing the current operator-facing freshness state and make it easy to distinguish, per source/field where practical:

- source observation time;
- collection-attempt time;
- successful collection time;
- publication time;
- current source-null vs collection failure;
- last successful GitHub Pages publication.

Prefer a read-only/operator report first. Do not change data values or invent freshness timestamps.


## Latest completed batch — read-only operator freshness/source-health report

The first operations/freshness visibility layer is implemented without changing IPO data values.

### New operator report

Added:

- `scripts/operator-report.mjs`
- `scripts/test-operator-report.mjs`
- `docs/OPERATOR_REPORT.md`

The report can run locally:

```bash
node scripts/operator-report.mjs
node scripts/operator-report.mjs --json
```

It summarizes:

- current published record count;
- verified/missing/non-verified coverage for key fields;
- verified Lot Size coverage;
- dataset `generated_at`;
- recovery `collection_started_at`;
- latest retained record collection time;
- latest retained evidence collection time;
- latest first-observed IPO time.

### Collection failure vs source gap

The hourly sync now gives stable IDs to the key operational stages and passes their **actual GitHub Actions outcomes** into an always-run operator summary:

- NSE collection;
- SEBI collection;
- dataset rebuild;
- data validation;
- repository publication step.

The report classifies the run as:

- `collection_success` when both NSE and SEBI collection succeeded;
- `collection_failure` when either collection stage failed/cancelled;
- `not_measured` when the outcomes are unavailable.

This avoids treating a null field as proof of a collection failure.

A missing field after a successful collection is reported only as a missing data value. Field-specific source-null decisions continue to come from the source-recovery evidence documented in this status file.

### Timestamp semantics

The report deliberately distinguishes:

- first observation;
- retained record collection;
- retained evidence collection;
- published JSON generation;
- operator report generation.

It does **not** relabel one timestamp as another.

### Known limitation

GitHub Pages deployment runs in a separate workflow. The sync job does not currently persist its success time/status, so the operator report explicitly says:

`GitHub Pages publication: not persisted by this sync workflow`

rather than inventing a publication timestamp.

### Workflow behavior

The operator summary step uses `if: always()`, so it still appears in the GitHub Actions Job Summary when an earlier collection/build/validation step fails.

The report is read-only and does not commit operational state.

### Handoff / next coherent batch

Keep Lot Size at **26/26 verified** and minimum-investment/application-amount work out of scope.

Next operations batch: add **durable publication-health visibility** so the operator surface can include the latest successful GitHub Pages publication timestamp/status without confusing it with dataset generation time.

Prefer one of:

1. a small explicitly generated deployment-status artifact updated by the Pages workflow; or
2. a safe GitHub API lookup in an operator-only report.

Do not rewrite IPO data values or overload `generated_at` with deployment semantics.


## Latest completed batch — durable GitHub Pages publication health

The operations/freshness layer now persists GitHub Pages deployment health separately from IPO data.

### Operational state

Added `ops/pages-publication.json` with two explicit concepts:

- `latest_attempt` — the most recent Pages deployment attempt, including success/failure/cancelled status, completion time, commit SHA and workflow run;
- `last_successful` — the last known successful Pages publication, preserved when a later attempt fails.

The initial record is seeded from verified successful Pages workflow run `35818066215`, which completed at `2026-09-23T04:22:42Z` for commit `d50c266e2f9ba4018b18364d1b5f4a4b6ca2d160`.

### Workflow behavior

`.github/workflows/deploy-pages.yml` now records deployment health in an `if: always()` step after the Pages deployment attempt.

The health-record commit is operational metadata only. The Pages workflow ignores pushes that change only `ops/pages-publication.json`, preventing a recursive deploy/status-commit loop.

The operator report reads this record and now shows both:

- latest Pages attempt status/time;
- last successful Pages publication time/commit.

Dataset `generated_at` remains unchanged in meaning and is not reused as deployment time.

### Tests / safety

Added focused tests for:

- successful publication recording;
- failed publication preserving the prior last-successful record;
- unknown outcome normalization;
- operator-report rendering of latest attempt vs last successful publication.

No IPO data value or source evidence is changed by this batch.

### Handoff / next coherent batch

Operational collection health and Pages publication health are now visible separately.

Next operations batch: add **staleness thresholds / actionable operator health classification** using the now-separated timestamps. Keep the first version read-only and explicit: classify stale dataset/source observations only from documented thresholds, and do not mutate IPO values or infer source-null from age alone.


## Latest completed batch — operator staleness / actionable health classification

The read-only operator surface now converts the separated operational timestamps into explicit health states without changing IPO data.

### Default thresholds

- dataset generation: **3 hours**;
- latest retained record collection: **3 hours**;
- latest retained evidence collection: **24 hours**;
- last successful GitHub Pages publication: **3 hours**.

The evidence threshold is intentionally longer because a successful hourly collection does not imply that a new offer document or field observation must appear every hour.

### Health states

- `healthy` — measured signals are inside their thresholds and collection is successful;
- `stale` — one or more measured freshness signals exceed the documented threshold;
- `failure` — NSE/SEBI collection failed/cancelled or the latest Pages deployment failed/cancelled;
- `unknown` — required operational timestamps are unavailable or collection health is not measured.

Precedence is failure > stale > unknown > healthy.

The report includes the measured ages, thresholds and machine-readable reasons such as `stale_dataset`, `stale_record_collection`, `stale_evidence_collection`, `stale_pages_publication`, `collection_failure` and `pages_deployment_failure`.

### Safety

This classification is operational only:

- it does not mutate `data/ipos.json`;
- it does not change field verification/source status;
- it does not infer source-null from age;
- it does not treat a lack of new evidence as a collection failure.

### Handoff / next coherent batch

The operator surface can now distinguish current failures, stale operational state and unknown/unmeasured state.

Next backend operations batch: make **recovery actions explicit for unhealthy states**. Start read-only: map each health reason to the safest diagnostic/recovery step and surface it in the operator report. Do not automatically rerun workflows, rewrite data, or notify external systems yet.


## Latest completed batch — read-only operator recovery guidance

The operator report now maps every current unhealthy/unknown health reason to a specific diagnostic and recovery recommendation.

### Guidance model

Each recommendation contains:

- the health reason;
- priority (`high`, `medium`, or `low`);
- a diagnostic step;
- a recovery step.

Current mappings cover:

- collection failure;
- Pages deployment failure;
- stale dataset generation;
- stale retained-record collection;
- stale retained evidence;
- stale Pages publication;
- missing dataset/record/Pages timestamps;
- invalid report time.

A healthy report returns no recovery action.

### Guardrails

The guidance layer is read-only:

- it does not rerun GitHub Actions;
- it does not mutate IPO data or recovery manifests;
- it does not send alerts/notifications;
- it does not recommend parser changes before inspecting a collection failure;
- stale evidence explicitly does not justify a rerun by itself because the official source may simply have no newer evidence.

### Handoff / next coherent batch

The operations surface now has measurement, health classification and reason-specific recovery guidance.

Next backend operations batch: add a **machine-readable operator snapshot artifact** for the latest sync result (health + guidance + relevant run identity) so operational state survives beyond an individual GitHub Actions Job Summary. Keep it separate from IPO data and avoid recursive workflow triggers.


## Latest completed batch — durable machine-readable operator snapshot

The hourly sync now persists its latest operator state to `ops/operator-snapshot.json` in addition to the GitHub Actions Job Summary.

### Snapshot contract

Schema `1.0.0` contains operational metadata only:

- sync run ID, attempt, workflow name and commit SHA;
- overall health, reasons, thresholds and measured ages;
- reason-specific recovery guidance;
- collection/build/validation/repository-publication stage outcomes;
- dataset generation, collection-start, latest record-collection and latest evidence-collection timestamps;
- retained GitHub Pages publication health.

It deliberately excludes IPO records and field coverage so the snapshot cannot become a competing IPO dataset.

### Workflow behavior

The snapshot step uses `if: always()`, allowing failed collection/build runs to leave durable diagnostic state.

The bot commit stages only `ops/operator-snapshot.json`. That path is outside the sync workflow's push-path trigger, so the snapshot commit does not recursively start another sync.

### Tests / safety

The snapshot contract test verifies run identity, health, pipeline/freshness state and confirms IPO records/field coverage are absent.

No IPO data values, evidence or field statuses are changed.

### Handoff / next coherent batch

The operations layer now has durable Pages state plus a durable latest sync snapshot.

Next backend operations batch: add a **small history/retention strategy for operator health transitions** so recurring failures/staleness can be distinguished from a one-off event without storing unbounded workflow history. Keep it operational-only and bounded; do not add external monitoring services or notifications yet.


## Latest repair batch — sync publication race and first snapshot persistence

Production verification after the operator-snapshot batch exposed two coupled workflow defects.

### Observed failure

Sync run `35872142330` successfully collected NSE/SEBI sources, rebuilt the dataset and passed validation, including a newly recovered official NSE issue size. Its data publication push then failed with a non-fast-forward rejection because another operational bot commit had advanced `main` during the long-running sync.

The snapshot step ran afterward, but the first `ops/operator-snapshot.json` was an untracked file. `git diff --quiet -- <path>` does not report untracked files, so the workflow incorrectly printed `Operator snapshot is unchanged` and did not persist it.

### Repair

The sync workflow now:

- commits source-backed data locally, fetches current `origin/main`, rebases the data commit, then pushes without force;
- explicitly checks whether `ops/operator-snapshot.json` is already tracked before using `git diff --quiet`;
- treats an untracked first snapshot as publishable;
- rebases the snapshot commit onto current `origin/main` before pushing, preserving concurrent data/Pages operational commits.

CI includes workflow-semantic guards for the rebase and untracked-snapshot checks.

### Handoff

Do not add operator transition history until a production sync confirms both source-backed data publication and first snapshot persistence under the repaired workflow.

After that verification, resume the planned bounded operator health-transition history batch.


## Latest completed batch — bounded operator health-transition history

Production sync `35874760161` verified the repaired publication path before this batch: collection, rebuild, validation and repository publication succeeded, and the first durable operator snapshot was committed to `main`.

The operator persistence layer now additionally maintains `ops/operator-health-history.json`.

### Retention semantics

- retain at most **48 health transitions**;
- consecutive runs with identical overall health + reasons are compressed;
- compressed entries retain first/last observation, first/last run and an observation count;
- a changed health state or reason set creates a new transition.

This avoids unbounded hourly history while still showing whether a failure/stale condition is recurring or a one-off transition.

### Safety

History is operational-only. It does not contain IPO records/field values and does not change source evidence or verification status.

### Handoff / next coherent batch

Operational freshness now has current state, recovery guidance, durable snapshot and bounded transition history.

Next backend batch: expose **recurrence context in the operator report** (for example, current state observation count and recent transitions) from the bounded history. Keep this read-only; do not add alerts or automatic recovery yet.


## Latest completed batch — operator recurrence context

The read-only operator report now consumes the bounded health-transition history when available.

It surfaces:

- current retained state and consecutive observation count;
- retained transition count;
- up to five recent transitions with reasons and first/last observation timestamps;
- an explicit `not recorded yet` state before the first history artifact exists.

Recurrence remains informational only: repeated failures/staleness do not automatically alter severity, rerun workflows, mutate data or send notifications.

### Handoff / next coherent batch

The operator layer now provides current health, recovery guidance, durable snapshot, bounded transition history and recurrence context.

Next backend operations batch: improve **pipeline-stage failure classification** beyond collection only. Distinguish rebuild, validation and repository-publication failures as first-class health reasons with safe recovery guidance, while preserving collection/source-null semantics.


## Latest completed batch — first-class downstream pipeline failures

Operator health now distinguishes downstream failures from source collection failures.

New first-class reasons:

- `rebuild_failure`;
- `validation_failure`;
- `repository_publication_failure`.

All are classified as operator `failure` and have reason-specific high-priority diagnostic/recovery guidance.

This preserves source semantics: successful NSE/SEBI collection followed by a rebuild, validation or Git publication failure is not reported as `collection_failure`, and no IPO field/source-null status is changed.

### Handoff / next coherent batch

The operator model now covers collection, rebuild, validation, repository publication and Pages deployment failures separately.

Next backend operations batch: improve **unmeasured/skipped stage semantics** so an expected skip after an upstream failure is distinguished from a stage that was never measured unexpectedly. Keep failure causality clear and avoid multiplying redundant failure reasons.


## Latest completed batch — skipped/unmeasured stage causality

Pipeline measurement now distinguishes expected downstream skips from unexplained missing execution.

### Semantics

- expected skip after a known upstream failure → no extra health reason;
- unexplained skip → `<stage>_unmeasured`;
- unknown/unrecorded outcome → `<stage>_unmeasured`;
- explicit failure/cancelled → existing first-class `<stage>_failure`.

Unexpectedly unmeasured rebuild/validation/repository-publication stages produce overall `unknown`, not `failure`, because the system lacks a measured outcome.

This prevents a single collection/rebuild failure from producing redundant downstream failure reasons while also preventing a skipped stage from being silently treated as successful.

### Handoff / next coherent batch

Pipeline causality is now explicit across collection, rebuild, validation and repository publication.

Next backend operations batch: add **snapshot/history schema validation** so malformed operational JSON is detected explicitly rather than silently consumed. Keep validation independent from IPO data validation and do not make operational metadata failures mutate IPO data.


## Consolidated backend repair pass — operational state integrity and publication reliability

Per owner request, this run consolidates the remaining coherent P3 operational repairs instead of stopping after one small handoff item.

### Repairs completed

1. **Independent operational-state validation**
   - Added `scripts/validate-operator-state.mjs`.
   - Validates `ops/operator-snapshot.json`, `ops/operator-health-history.json`, and `ops/pages-publication.json` independently from IPO data validation.
   - Enforces schema version, required object/array shapes, health-state values, bounded history retention, positive observation counts, and core run/timestamp fields.

2. **Validate before persistence**
   - Snapshot/history generation validates newly built state before history is written.
   - Malformed operational state causes the operator persistence step to fail explicitly rather than committing corrupt JSON.
   - This failure path does not mutate IPO data.

3. **Committed-state CI validation**
   - CI tests valid/invalid operational-state fixtures.
   - CI validates the currently committed snapshot/history/Pages state on every normal validation run.

4. **Pages-health publication race repair**
   - The Pages workflow now fetches/rebases onto current `origin/main` before pushing its operational health commit.
   - This matches the previously repaired data/snapshot publication path and prevents a concurrent data/operator-state commit from causing a non-fast-forward Pages-health failure.
   - No force push is used.

5. **Workflow trigger coverage**
   - Changes to the new validator/tests trigger the live-sync validation path.
   - CI guards the race-safe rebase semantics for both sync and Pages operational publication.

### Safety

Operational validation remains separate from `data/ipos.json` validation. A malformed operator artifact is an operations problem; it never causes IPO values, source evidence, null semantics or correction history to be rewritten.

### Handoff

After this consolidated repair pass is verified in CI and production, resume backend development from repository evidence rather than the older one-batch handoffs above. The next task should be chosen from any remaining real P1/P2/P3 correctness gaps, not from already-completed operator plumbing.


## Latest data-recovery batch — NSE past-issues listing date + final price

Coverage audit after the consolidated operational repairs showed the largest homepage gaps were listing date (19/32 missing) and issue price (18/32 missing).

The existing official NSE `public-past-issues` extractor had a circular constraint: it only considered records that already had a listing date, even though the official past-issues row itself contains the listing date.

This batch removes that dependency:

- exact NSE symbol/series matching remains required;
- if a retained listing date already exists, a conflicting NSE row is still rejected;
- when listing date is missing, the exact official row can now verify and retain it;
- after listing-date recovery, the same official row can verify final issue price;
- unparseable dates remain null;
- evidence/document identity and collection timestamps are retained.

This is a reusable source-family repair, not a manual issuer patch.

### Handoff

Measure production coverage improvement from the next sync. Then continue with the highest remaining verified P1/P2 gap, likely issue size or residual listing-date/issue-price records not present in NSE past issues.


## Latest data-source expansion — official BSE IPO diagnostic

The tracker previously had no BSE source integration. This is a material coverage gap for BSE/SME-only issues and historical recovery.

Added a read-only official BSE issue-summary diagnostic that:

- fetches BSE's official Public Issues summary;
- discovers official `DisplayIPO.aspx` detail links;
- normalizes issuer names conservatively;
- requires a unique issuer match before considering a BSE issue page;
- reports matched / missing / ambiguous coverage for IPO records that still have homepage field gaps;
- does not write IPO values yet.

This diagnostic-first step is intentional. BSE page/identifier behavior must be measured against multiple real issuers before a writer is allowed to retain issue price, listing date, issue size, market lot or minimum bid values.

The same BSE issue-summary/detail family is intended to support both current 2026 gaps and historical IPO recovery (2025 → 2020).

### Handoff

Run the BSE diagnostic in production, inspect matched official detail pages and field layouts, then implement field-specific BSE extraction only for terms that are explicit and consistently identifiable. Preserve NSE/SEBI evidence and conflicts rather than overwriting them.


## BSE expansion — verified page parsers and historical source manifest

Production BSE diagnostic run `35884250076` proved that `Issuesummary.aspx` is a JavaScript shell on the Actions runner: HTTP retrieval succeeded but returned zero server-rendered `DisplayIPO` links. Therefore the summary HTML is not a valid discovery feed.

The free official BSE pages themselves remain useful once their URLs are known. Added tested parsers for:

- BSE equity `DisplayIPO.aspx` pages: symbol, issue period, number of shares, price band, market lot, minimum bid quantity;
- BSE listing notices: company, effective listing/trading date, market lot, final public issue price.

Non-equity issue pages are explicitly rejected by the equity parser.

Added `data/bse-ipo-sources.json` as a retained official-source manifest. This separates **discovery** from **extraction**: once an official BSE issue/listing URL is discovered and matched, it can be retained and re-parsed automatically without rediscovering identifiers on every run.

This manifest is intentionally empty initially; no BSE URL is guessed. It is suitable for current 2026 recovery and year-by-year historical backfill through 2020.

### Important constraint

BSE's server-rendered issue summary cannot currently enumerate issues for us, and BSE's formal structured market-data API is a registered/licensed product. Do not invent undocumented endpoints or scrape around access controls. Populate the manifest only from explicit official BSE URLs/evidence.

### Next data task

Populate BSE source-manifest entries for verified 2026 residual gaps and historical years from official BSE pages/notices, then add conflict-safe recovery writes from the tested parsers.


## Substantial BSE + historical retrieval batch — recovery writer and year audit

This batch moves BSE from read-only parsing to conflict-safe recovery application.

### BSE recovery writes

For a retained, verified BSE source URL with exactly one matching recovery record:

- BSE equity issue detail can fill missing price band, market lot, minimum bid quantity, open date and close date;
- BSE listing notice can fill missing listing date, final issue price and market lot;
- existing non-null values are never overwritten;
- disagreements are reported as conflicts rather than silently resolved;
- every applied value retains BSE URL, document type/identity, publication date and collection time;
- source documents are attached once to the recovery record.

BSE issue share count is parsed and retained in diagnostics but is **not multiplied by price to manufacture INR issue size**. Issue size remains null unless an official source explicitly states the monetary total.

### Verified historical BSE source seeds

The BSE source manifest now contains real official 2025 examples for:

- Kenrik Industries Limited — BSE public issue detail;
- 3B Films Limited — BSE listing notice;
- Billionbrains Garage Ventures Limited (Groww) — BSE public issue detail.

These are source evidence, not a claim that the 2025 universe is complete.

### Historical universe audit

Added a machine-readable runtime audit for 2026 → 2020. Current repository truth is explicit:

- 2026 recovery universe is materialized;
- 2025 → 2020 recovery universes are not yet materialized;
- verified BSE source counts are reported independently by year.

This prevents a few discovered historical issuers from being mistaken for complete year coverage.

### Next substantial retrieval task

Materialize the historical IPO universe year-by-year from official exchange/SEBI evidence, beginning with 2025, and then apply the now-reusable NSE/BSE/SEBI field recovery stack. Do not infer completeness from search-engine discovery alone.


## Historical publication compatibility — BSE evidence + listing-date ordering

Audit of the published-data builder confirmed that it already merges every `data/recovery/YYYY/nse-issue-information.json` manifest, so newly materialized 2020-2025 records will flow into `data/ipos.json` automatically.

Two historical-publication fixes were required:

- add official BSE hosts to the publisher's source allowlist so verified BSE evidence can be retained without validation failure;
- when historical records lack offer open/close dates, sort them by verified listing date before issuer name, preserving newest-to-oldest behavior for completed IPOs.

This does not invent historical offer dates. Listing date is used only as the ordering fallback when open/close dates are absent.


## Historical SEBI enrichment — bounded targeted search with durable cursor

Audit after historical universe materialization showed SEBI's targeted issuer search was restricted to live-feed records. Historical NSE records therefore received SEBI documents only when they happened to appear on SEBI's current listing pages.

This batch adds a bounded historical search path:

- up to **12 historical issuers per sync** are searched through the official SEBI filings search;
- live current-IPO targeted searches remain capped separately at 12;
- historical candidates must have a verified listing date and no retained SEBI document;
- search state is persisted in `ops/sebi-historical-search.json`, so each hourly run advances to previously unsearched issuers rather than repeating the same misses;
- successful matches are not searched again;
- no-match results retry after 30 days;
- transient search errors retry after 24 hours;
- search state is operational metadata and is ignored by GitHub Pages when it is the only changed file.

This turns SEBI historical enrichment into an incremental automatic backfill instead of a current-IPO-only process.

### Safety

A search attempt never creates IPO field evidence by itself. Only an actual matched official SEBI filing/document is attached to the recovery record. Unmatched searches remain operational cursor state only.


## SEBI historical search latency guard

Historical SEBI targeted searches now use explicit request timeouts and a smaller bounded batch:

- historical targeted searches are capped at **12 issuers per sync**;
- targeted search requests use two attempts with a 10-second timeout per attempt;
- general SEBI listing/detail requests also have a 15-second timeout;
- a slow/unresponsive SEBI request is recorded as an error and retried by the existing 24-hour cooldown rather than blocking publication indefinitely.

This prioritizes steady hourly progress over attempting too many historical issuers in one run.


## First successful 2020–2026 historical publication

Production sync `35909605857` successfully rebuilt, validated and published **915 IPO records across 7 year manifests**.

### Published universe counts

- 2020: **51**
- 2021: **100**
- 2022: **94**
- 2023: **174**
- 2024: **252**
- 2025: **212**
- 2026: **32**
- total: **915**

Historical 2020–2025 records currently have very strong NSE historical coverage for:

- listing date: **883/883**;
- final issue price: **881/883**.

The major remaining historical field gaps are price band, offer open/close dates, issue size, market lot and minimum bid quantity.

### BSE ordering repair

The live workflow previously ran the retained BSE writer before historical NSE materialization. On a first-year materialization run, verified historical BSE sources therefore had no recovery record to attach to.

The workflow now:

1. collects current NSE data;
2. materializes 2020–2025 historical NSE records;
3. applies retained BSE sources;
4. runs the detailed historical coverage audit;
5. continues with SEBI enrichment.

This allows retained BSE evidence to apply during the same run that creates historical recovery records.

### Detailed coverage audit

`scripts/audit-historical-coverage.mjs` now reports, per year:

- total records;
- Mainboard / SME / unknown-board counts;
- retained verified BSE source count;
- records with BSE evidence;
- records with SEBI evidence;
- coverage counts for price band, final issue price, issue size, market lot, minimum bid, offer dates and listing date.

This makes subsequent historical retrieval improvements measurable instead of relying on directory presence alone.


## Historical NSE detail backfill — bounded field recovery

The first historical publication contains **883 records from 2020-2025**. NSE Public Past Issues provides excellent listing-date/final-price coverage, but historical price band, market lot, minimum bid and monetary issue-size coverage is still effectively zero.

Added a dedicated historical NSE `ipo-detail` backfill that is separate from the live/current IPO detail sweep.

### Behavior

- processes at most **24 historical IPOs per sync**;
- only considers pre-current-year records with retained NSE symbol/series and one of the target fields still missing;
- fetches each historical `ipo-detail` payload once;
- reuses the existing conservative parsers for:
  - price band;
  - market lot;
  - minimum bid quantity;
  - explicit monetary issue size;
- never overwrites an existing non-null value;
- does not infer issue size from shares × price;
- records a durable per-issuer cursor in `ops/nse-historical-detail.json`;
- successful/no-field responses are not repeatedly probed with the same parser version;
- transient fetch errors retry after 24 hours;
- changing the parser version makes records eligible for reprocessing after future parser improvements.

The cursor is operational metadata and cursor-only commits are ignored by GitHub Pages.

### Scope note

Open/close date recovery is intentionally not included in this batch because the existing `ipo-detail` contract has not yet been verified for a stable historical offer-date field. Historical offer dates remain null until an explicit official field/source is validated.

### Expected effect

At 24 records per hourly sync, the 883-record historical backlog can be sampled progressively without blocking current IPO publication. The detailed historical coverage audit runs after this backfill step, making field gains measurable on every run.


## BSE retrieval repair — session handshake + BSE-only materialization

Production logs showed why the retained BSE sources had produced zero attached records:

- official BSE issue-detail URLs returned HTML to GitHub Actions, but the body did not parse as an equity issue page;
- BSE listing notices parsed correctly, but BSE-only issuers such as 3B Films had no NSE historical recovery record to attach to;
- official BSE search results confirm that the retained issue-detail URLs contain the expected equity issue terms when served normally.

This batch addresses both failure modes.

### BSE session handling

The BSE collector now primes a session against `https://www.bseindia.com/`, retains returned cookies, and sends them with issue/listing page requests. When a page still does not parse, diagnostics now retain response byte count and a short page-head sample so anti-bot/challenge responses can be distinguished from parser defects.

### Fixed-price BSE issue support

The BSE issue-detail parser now also accepts explicit fixed `Issue Price` values in addition to price bands. This is required for fixed-price SME issues such as Kenrik Industries.

### BSE-only issuer materialization

A retained BSE manifest source may now explicitly set `materialize_if_missing: true`.

When a verified BSE source has no matching recovery record:

- the source must contain an explicit year;
- a BSE listing notice must name the same normalized issuer before materialization;
- a new recovery record is created with BSE provenance;
- no NSE identity is invented;
- fields are populated only from the parsed official BSE page/notice;
- `listed` status is retained only when an actual BSE listing notice is the source.

The three currently verified 2025 BSE sources are opted in.

### Publication repair

Retained `open_date` / `close_date` fields are now preferred by the publisher before NSE term fallbacks, so BSE-derived offer dates retain their own evidence instead of being dropped.

This provides a controlled path for BSE-only historical IPOs while keeping universe expansion evidence-driven rather than inferred from search-engine results.


## BSE universe safety tightening — listing notices only

Production evidence from the retained BSE sources established that official BSE listing notices are reliably parseable on the Actions runner, while desktop `DisplayIPO.aspx` issue-detail pages may return non-parseable/challenge HTML even after session priming.

Universe materialization is therefore tightened:

- **only an official BSE listing notice may create an unmatched BSE-only IPO record**;
- the manifest must explicitly set `materialize_if_missing: true`;
- the notice issuer must match the retained issuer identity;
- the notice must contain a parseable effective listing date;
- board is retained only when the notice explicitly states `Segment SME` or `Segment Equity`;
- issue-detail pages may enrich an already-known issuer when they parse, but can no longer create a new issuer on their own.

The current manifest keeps BSE-only materialization enabled for the 3B Films listing notice and disables it for the Kenrik/Groww issue-detail seeds.

This makes exchange-universe inclusion depend on direct listing evidence rather than an offer/detail page that may represent an issue before listing or may be inconsistently served.


## Historical NSE detail batch acceleration

Two production backfill runs established that the bounded historical NSE detail path is stable:

- first run: 24/24 API calls succeeded, 24 records enriched, 48 fields recovered;
- second run: 24/24 API calls succeeded, 22 records enriched, 45 fields recovered, 0 fetch errors.

The bounded batch is therefore increased from **24 to 48 issuers per sync**. Cursor/version gating, request timeouts, no-overwrite semantics and error retries remain unchanged.


## Historical offer-date backfill — explicit SEBI RHP/Prospectus dates

Historical 2020-2025 open/close date coverage remained at zero after NSE historical universe materialization. The existing NSE historical source does not expose a verified offer-period field, so this batch recovers dates only from explicit official SEBI document text.

### Behavior

- process at most **12 historical IPOs per sync**;
- candidate records must be pre-current-year, still missing open/close dates, and already retain an official SEBI Prospectus PDF or RHP PDF;
- Prospectus PDF is preferred over RHP PDF when both are available;
- only explicit labels such as `Bid/Issue Opening Date`, `Issue Opening Date`, `Bid/Issue Closing Date`, and equivalent `opens on` / `closes on` wording are accepted;
- month-name dates are parsed with strict calendar validation;
- conflicting official dates are rejected;
- opening date after closing date is rejected;
- closing date after a retained listing date is rejected;
- existing non-null dates are never overwritten;
- each recovered date retains source PDF URL, document identity/type, publication date, PDF page and collection timestamp.

### Bounded cursor

`ops/sebi-historical-offer-dates.json` records parser version, last attempt, extraction result and source URL. Successful/no-field/conflict results are not repeatedly scanned with the same parser version; transient PDF failures retry after 24 hours.

This queue is separate from the heavy general historical PDF passes so offer-date recovery can progress without blocking live publication.
