# PROJECT STATUS

Last updated: 2026-09-21

## Current state

The repository now has a source-first public data contract **and the first real 2026 recovery slice**.

Two IPO records are published from retained official-source evidence:

- Hero Motors Limited
- Rentomojo Limited

The batch is intentionally incomplete at the field level. Unsupported values remain null instead of being derived, estimated, or copied from aggregators.

## Completed in latest batch

- Added `data/recovery/2026/nse-issue-information.json` as the retained recovery manifest for the first source family.
- Added `scripts/build-published-data.mjs` to deterministically transform retained recovery evidence into `data/ipos.json`.
- Restricted the recovery publisher to official NSE and SEBI hosts.
- Published Hero Motors Limited with source-backed:
  - price band
  - market lot
  - minimum bid quantity
  - offer open date
  - offer close date
  - total issue size
- Published Rentomojo Limited with source-backed:
  - price band
  - market lot
  - minimum bid quantity
  - offer open date
  - offer close date
- Retained official NSE issue-information URLs and SEBI offer-document trails.
- Preserved unsupported fields as null/missing, including issue price, minimum application amount, listing date, board, sector, and status where this batch did not establish them.
- Added a CI synchronization check so `data/ipos.json` must exactly match the recovery manifest transformation.
- Fixed validation workflow scope so every pushed recovery branch is tested rather than only the previous feature branch.

## Source verification

The batch was cross-checked against official sources before publication:

- NSE issue information for Hero Motors Limited
- NSE issue information for Rentomojo Limited
- SEBI RHP / Abridged Prospectus / Prospectus trails for both issuers
- Rentomojo RHP addendum retained in its document trail
- Hero Motors total offer size is supported by its SEBI Abridged Prospectus

No aggregator value was used to fill a missing production field.

## Tests

GitHub Actions passed on `recover-2026-nse-batch-1` with:

- `node --check assets/app.js`
- `node scripts/build-published-data.mjs --check`
- `node scripts/validate-data.mjs`

The diff review verified:

- the branch is based on current `main`;
- exactly two IPO records are added;
- null fields remain null;
- verified values retain official evidence;
- no correction history is deleted;
- no unrelated UI or infrastructure files are changed;
- the generated public dataset is synchronized with the retained recovery manifest.

## Current limitation

This is the first recovery adapter, not yet an automated web collector.

The retained manifest was built from manually verified official NSE/SEBI evidence and is reproducibly published into the UI dataset. Automatic new-IPO discovery, document downloading, source-change detection, and scheduled refresh remain future P3 work.

The historical 2026 universe is also far from complete.

## Earliest unfinished priority

P1 — Data correctness.

Before broad universe expansion, deepen the first recovered records so core terms are as complete as official sources permit, especially:

- final issue price;
- listing date;
- board;
- IPO lifecycle status;
- minimum application amount only if directly supported or via a separately documented derivation rule.

## Recommended next coherent batch

Recover the remaining core P1 fields for Hero Motors Limited and Rentomojo Limited from official final prospectus / exchange listing evidence.

Acceptance criteria:

1. official sources only;
2. preserve nulls where evidence remains unavailable;
3. do not silently calculate minimum application amount;
4. retain source URL, identity, publication date, page/evidence location, and collection time;
5. preserve any conflicts rather than overwriting them;
6. pass recovery synchronization and data-contract validation;
7. verify the enriched records render correctly after deployment.

## Prior publication

- Pull request: #1 — `Establish source-backed IPO data foundation`
- Foundation merge: `4ae4fb43b63fc9aebd5380bab33cd3cc838f48ec`
- Deployment bookkeeping commit: `a3e1214e43e3ab19ea60a2c88baf975392775b5a`
- Validation and GitHub Pages deployment passed.

## Latest publication

- Pull request: #2 — `Recover first source-backed 2026 IPO batch`
- Squash-merged to `main`: `30d73b04677fda0f5d6c17a688f16fa50809840b`
- Post-merge validation workflow: passed
- Post-merge GitHub Pages deployment workflow: passed
- Pages artifact `github-pages` was generated from the merged revision.
- Direct retrieval of `https://vasuki8.github.io/IPO-Tracker/` was unavailable from the web tool in this development session, so visual live-page verification was not independently performed.
- Repository/deployment verification confirms the published artifact contains the two-record source-backed dataset.
