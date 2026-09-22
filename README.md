# IPO Tracker

A source-first Indian IPO research interface.

## Current state

The public UI now consumes a dedicated source-backed dataset at `data/ipos.json`.

The dataset is intentionally empty until authoritative IPO recovery is reconnected. Prototype IPO rows and illustrative market values are no longer used as production fallback data.

### Data foundation now includes

- Evidence-bearing IPO field contract
- Null preservation
- Verified / provisional / conflict / missing source states
- Separate market lot, minimum bid quantity, and minimum application amount
- Publication, observation, collection, and dataset-generation time concepts
- Correction history
- Machine-checkable validation
- GitHub Actions validation

See `docs/DATA_CONTRACT.md` and `data/ipo-schema.json`.

## Local preview

Open `index.html` in a browser or serve the repository with any static HTTP server.

## Architecture

```
index.html
assets/
  styles.css
  app.js
```

The UI is static-hosting friendly and can be published via GitHub Pages.

---

## Handoff for the next prompt

Use this section as the starting context when continuing work in a new chat.

### Repository

- Repository: `Vasuki8/IPO-Tracker`
- Default branch: `main`
- Hosting target: GitHub Pages
- Deployment workflow: `.github/workflows/deploy-pages.yml`

### What happened in the latest run

The source-backed production data boundary was established.

The UI no longer embeds demo IPO records. It loads `data/ipos.json`, which currently contains zero records because the historical authoritative recovery pipeline is not present in this repository.

New files:

```
data/
  ipos.json
  ipo-schema.json
docs/
  DATA_CONTRACT.md
scripts/
  validate-data.mjs
.github/workflows/
  validate-data.yml
```

Updated:

- `assets/app.js` — loads published source-backed records and renders null/source states safely.
- `index.html` — removes hard-coded sample IPO, financial, timeline, and document values.
- `docs/PROJECT_STATUS.md` — records the new data foundation and next blocker.

Validation now runs:

```
node --check assets/app.js
node scripts/validate-data.mjs
```

### Critical data warning

Do not populate `data/ipos.json` with guessed, estimated, unsupported, or aggregator-derived substitute values.

The next batch should reconnect official-source IPO discovery/recovery for a bounded 2026 batch and publish only records that satisfy the contract.

### Main blocker

The authoritative historical IPO discovery/recovery pipeline is still absent from this repository.

### Next priority

Rebuild/reconnect official-source IPO recovery and publish the first real 2026 IPO records into `data/ipos.json`.

Preserve:

1. nulls;
2. source URL/document identity;
3. publication date;
4. page/evidence location when available;
5. collection timestamps;
6. conflicts and correction history;
7. separate market lot, minimum bid quantity, and minimum application amount.

### Product direction

The product is intended to become a public commercial IPO research/tracking product.

Current priority order remains:

1. Trustworthy displayed data
2. Accurate freshness and source labels
3. Reliable recovery / repair handling
4. Complete source coverage
5. Better IPO research workflows
6. Performance / expansion only after correctness is stable
7. Discoverability and maintainability
8. Commercial features only when explicitly justified

Do not add billing, accounts, ads, analytics, paid infrastructure, or other commercial systems without explicit approval.

## Development operating model

Future development runs must follow `docs/DEVELOPMENT_PROCESS.md`.

For a fresh chat, the preferred continuation instruction is:

> Continue IPO Tracker development. Read README.md, docs/PROJECT_STATUS.md, and docs/DEVELOPMENT_PROCESS.md first. Follow the repository development process, select the earliest unfinished priority, and complete one coherent batch end to end.

After that, the user may simply say **"continue"** for subsequent batches. The development process and handoff files are the source of truth; the user should not need to resend a large master prompt.

