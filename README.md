# IPO Tracker

A source-first Indian IPO research interface.

## Current state

The public UI now consumes a dedicated source-backed dataset at `data/ipos.json`.

The first official-source 2026 recovery slice is connected and now includes final-Prospectus enrichment for both pilot issuers. Prototype IPO rows and illustrative market values are not used as production fallback data.

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

The official NSE archive copy of Rentomojo Limited's final Prospectus was recovered and added to the retained source trail.

Rentomojo now has:

- final issue price ₹404;
- total offer size ₹12,555.67 million;
- Mainboard classification;
- its earlier source-backed offer terms.

The final price and issue size come from the directly retrievable official NSE Prospectus, not a third-party mirror.

The BSE listing notices `20260916-7` and `20260916-46` were investigated again. Their canonical BSE URL pattern is known, but the dynamic BSE pages remain inaccessible to the available tooling. Listing date and listed status therefore remain null.

Recovery input remains in `data/recovery/2026/nse-issue-information.json` and is transformed deterministically into `data/ipos.json` by `scripts/build-published-data.mjs`. The publisher now also preserves `last_collected_at` per issuer, so regenerating one updated record does not falsely refresh unrelated IPOs.

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

Move to the next small 2026 official-source recovery batch using the now-proven NSE/SEBI issue-information and final-Prospectus pattern. Keep the BSE listing-notice blocker documented and revisit it when the official dynamic page or an official archive endpoint becomes directly retrievable.

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

