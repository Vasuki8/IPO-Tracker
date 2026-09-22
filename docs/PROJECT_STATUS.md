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

## Latest completed batch — automated SEBI document discovery

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

## Earliest unfinished priority

P1/P2 — **data correctness and source evidence depth**.

Live IPO discovery is automated and SEBI document matching is operational, but SEBI raw-source coverage for newly discovered sparse issuers is not sufficient to justify further endpoint-variant retries in the same workstream.

## Recommended next coherent batch

Move to a source family where evidence is already retained and make it produce additional trusted fields.

Recommended first target:

**automate one bounded field-extraction family from retained official Abridged Prospectus / final Prospectus documents.**

Acceptance criteria:

1. start only with documents whose official URL is already retained;
2. extract a very small field set, e.g. explicit aggregate issue size and/or final issue price;
3. retain page/evidence location and source document identity;
4. never substitute price-band cap for final issue price;
5. preserve null when a PDF is inaccessible or the value is not explicit;
6. add source-family fixtures/tests before production use;
7. keep SEBI sparse-discovery coverage as a documented blocker rather than loosening issuer matching.

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
