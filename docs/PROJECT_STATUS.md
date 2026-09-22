# PROJECT STATUS

Last updated: 2026-09-21

## Current state

The repository now has a source-first production data boundary between IPO recovery and the public UI.

The earlier UI V1 used clearly labeled demo IPO rows because the historical recovery pipeline was not present in the repository. This batch removed those demo market values from the production rendering path rather than allowing prototype values to become accidental production data.

## Completed in latest batch

- Added `data/ipos.json` as the only published IPO dataset consumed by the UI.
- Added `data/ipo-schema.json` with evidence-bearing field definitions.
- Added `docs/DATA_CONTRACT.md` documenting null, provenance, timestamp, conflict, and correction rules.
- Added `scripts/validate-data.mjs` to enforce core invariants.
- Added GitHub Actions validation for JavaScript syntax and IPO data invariants.
- Reworked `assets/app.js` to load the published dataset instead of embedded demo IPOs.
- Preserved separate market lot, minimum bid quantity, and minimum application amount fields.
- Added null-safe rendering and source states: verified, provisional, conflict, missing.
- Removed hard-coded sample IPO, financial, timeline, and document values from the production UI path.
- Added a clear empty state when no source-backed records are published.

## Tests

GitHub Actions validation passed on the feature branch after the final cleanup:

- `node --check assets/app.js`
- `node scripts/validate-data.mjs`

Diff review also verified:

- branch is based on current `main`;
- no production IPO records were invented;
- `data/ipos.json` intentionally contains zero records;
- evidence, corrections, publication date, first-observed time, last-collected time, and generated time remain represented in the contract;
- known demo issuer names and illustrative market values were removed from the production rendering path.

## Current blocker

The authoritative historical IPO discovery/recovery pipeline is still not present in this repository.

Therefore the published dataset currently contains zero IPO records by design. Re-populating the tracker must be done from official source evidence rather than copying the former demo values or guessing missing fields.

## Earliest unfinished priority

P1 — Data correctness: rebuild/reconnect authoritative IPO universe recovery and begin publishing real source-supported IPO records into `data/ipos.json`.

## Recommended next coherent batch

Implement the first official-source discovery/recovery adapter for a bounded 2026 IPO batch, producing records that satisfy the published-data contract.

Acceptance criteria for that batch:

1. use official sources only for published values;
2. preserve nulls rather than estimating;
3. retain document URL/identity/publication date/page when available;
4. retain collection timestamps;
5. publish no more than a small coherent batch;
6. pass `scripts/validate-data.mjs`;
7. verify the records render correctly on desktop/mobile.

## Publication

- Pull request: #1 — `Establish source-backed IPO data foundation`
- Merged to `main`: `4ae4fb43b63fc9aebd5380bab33cd3cc838f48ec`
- Post-merge validation workflow: passed
- GitHub Pages deployment workflow: passed
- Pages artifact was generated from the merged `main` revision.
- Direct browser retrieval of the public Pages URL was unavailable from the development session, so visual live-page verification was not independently performed; deployment health and artifact revision were verified through GitHub Actions.
