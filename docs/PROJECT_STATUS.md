# PROJECT STATUS

Last updated: 2026-09-22

## Current state

IPO Tracker now has a working **automated official-source discovery and publication loop** plus a production-tested **SEBI document-discovery layer**.

The published 2026 dataset contains **23 real IPO issuers**.

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

The SEBI network/parser path is operational, but the current raw responses available to GitHub Actions do **not yet enrich the nine sparse records created by the first NSE live run**.

Latest measured result:

- 9 matched latest-list filing entries;
- 37 unmatched listing entries;
- 9/9 sparse NSE-live records searched by the bounded targeted fallback;
- 5 filing results parsed from targeted searches;
- 0 deterministic targeted issuer matches;
- 0 new documents added.

The nine still-sparse live-discovered issuers are:

1. Adroit Industries (India) Limited
2. ArMee Infotech Limited
3. Axiom Gas Engineering Limited
4. Coreintegra Consulting Services Limited
5. Elevate Campuses Limited
6. National Stock Exchange of India Limited
7. Pooja Logistics Limited
8. Swastika Infra Limited
9. Varmora Granito Limited

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
- bounded SEBI search token selection.

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

## Recommended next coherent batch

Inspect the three final Prospectus PDFs that still have null issue price—Jindal Supreme, SS Retail and Veegaland—to determine whether the gap is caused by unsupported wording/layout or the current 20-page scan boundary.

Only broaden parsing when an explicit official phrase can be matched deterministically and tested across multiple documents. Do not infer the final price from the price-band cap.

After that review, the next separate field family should be explicit aggregate issue size from retained final Prospectus PDFs, with page-level evidence and no arithmetic reconstruction.

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
- Final issue-price bot commit: `f9b7155c42d8b44d6985d9dafb9fd242e37dc64e`
