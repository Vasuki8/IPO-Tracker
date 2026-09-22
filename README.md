# IPO Tracker

A source-first Indian IPO research interface.

## Current state

The public UI now consumes a dedicated source-backed dataset at `data/ipos.json`.

The first official-source 2026 recovery slice is connected and now includes final-term enrichment. Prototype IPO rows and illustrative market values are not used as production fallback data.

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

The two-record 2026 pilot was deepened:

- Hero Motors Limited now has final issue price ₹84 from the issuer-hosted final Prospectus.
- Rentomojo Limited now has Mainboard classification from an NSE-hosted Public Announcement.

Schema version `1.1.0` adds retained provenance for board/status metadata and the recovery publisher now preserves each source's original collection timestamp across regeneration.

Recovery input remains in `data/recovery/2026/nse-issue-information.json` and is transformed deterministically into `data/ipos.json` by `scripts/build-published-data.mjs`.

Unsupported fields remain null. In particular, Rentomojo's issue price/listing date were not populated from third-party mirrors when the official dynamic BSE source could not be directly retrieved.

Validation now runs:

```
node --check assets/app.js
node scripts/build-published-data.mjs --check
node scripts/validate-data.mjs
```

### Critical data warning

Do not edit `data/ipos.json` as a substitute for source recovery. Update retained recovery evidence and regenerate the public dataset.

Do not fill nulls with guessed, estimated, unsupported, or aggregator-derived substitute values.

### Main limitation

The first recovery adapter is deterministic but not yet an automated web collector, and the 2026 IPO universe remains incomplete.

### Next priority

Resolve the official BSE/NSE listing-notice source family for remaining final issue price, listing date and listed-status evidence. If direct official retrieval remains blocked, keep those fields null and proceed to the next official-source 2026 recovery family rather than using mirrors.

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

