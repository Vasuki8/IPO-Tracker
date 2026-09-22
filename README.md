# IPO Tracker

A source-first Indian IPO research interface with automated official-source discovery and GitHub Pages publication.

## Current state

The public UI consumes the source-backed dataset at `data/ipos.json`.

As of the first production live-sync run on 2026-09-22, the published 2026 dataset contains **23 real IPO issuers**. The tracker does not use prototype/demo market rows as production fallback data.

### Data foundation

- Evidence-bearing IPO field contract
- Null preservation
- Verified / provisional / conflict / missing source states
- Separate market lot, minimum bid quantity, and minimum application amount
- Publication, observation, collection, and dataset-generation timestamps
- Correction/conflict history
- Deterministic publication from retained recovery manifests
- Machine-checkable validation
- GitHub Actions validation

See `docs/DATA_CONTRACT.md` and `data/ipo-schema.json`.

## Live automation

The tracker now has an automated discovery/publishing loop.

`.github/workflows/update-ipos.yml` runs **hourly** and:

1. retrieves current/upcoming IPOs from official NSE website feeds;
2. merges explicitly supported source values into the retained recovery manifest;
3. leaves unsupported values null;
4. rebuilds `data/ipos.json`;
5. validates the data contract;
6. commits only source-backed changes;
7. lets GitHub Pages publish the new revision.

The first real production run succeeded and automatically increased the dataset from 14 to 23 issuers.

See `docs/AUTOMATION.md` for the exact source and field rules.

### Automation is intentionally conservative

The NSE discovery feed does **not** automatically cause the tracker to:

- interpret NSE `issueSize` as an INR issue-size amount;
- copy market lot into minimum bid quantity;
- calculate minimum application amount;
- infer sector or listing date;
- treat the cap of a price band as the final issue price.

Those values remain missing until supported by retained official evidence.

## Architecture

```
index.html
assets/
  styles.css
  app.js
data/
  ipo-schema.json
  ipos.json
  recovery/
    <year>/
      nse-issue-information.json
scripts/
  sync-nse-live.mjs
  build-published-data.mjs
  validate-data.mjs
.github/
  workflows/
    update-ipos.yml
    validate-data.yml
    deploy-pages.yml
docs/
  DEVELOPMENT_PROCESS.md
  DATA_CONTRACT.md
  AUTOMATION.md
  PROJECT_STATUS.md
```

## Local preview

Open `index.html` in a browser or serve the repository with any static HTTP server.

---

## Handoff for the next prompt

Use this section as the starting context when continuing work in a new chat.

### Repository

- Repository: `Vasuki8/IPO-Tracker`
- Default branch: `main`
- Website: `https://vasuki8.github.io/IPO-Tracker/`
- Hosting: GitHub Pages
- Live-data workflow: `.github/workflows/update-ipos.yml`
- Deployment workflow: `.github/workflows/deploy-pages.yml`

### Latest completed batch

PR #9, **Automate live IPO discovery and publication**, was squash-merged to `main` at:

`8a6895d34bd64c2600c6e82bec29418e399fa366`

The first real GitHub Actions live sync then:

- successfully reached the official NSE feeds;
- passed parser, deterministic-build, and data-contract validation;
- created bot commit `87c52215fcdbaa079b937597fe902a13309e22d2`;
- expanded the public dataset from **14 to 23 issuers**;
- added 9 new source-backed NSE-discovered issuers;
- enriched Sonaselection India Limited's board/lifecycle status;
- preserved unsupported fields as null;
- triggered a successful GitHub Pages publication for the bot-generated revision.

Newly discovered records in that first live run:

- Adroit Industries (India) Limited
- ArMee Infotech Limited
- Axiom Gas Engineering Limited
- Coreintegra Consulting Services Limited
- Elevate Campuses Limited
- National Stock Exchange of India Limited
- Pooja Logistics Limited
- Swastika Infra Limited
- Varmora Granito Limited

### Critical data rule

Do not edit `data/ipos.json` as a substitute for source recovery.

Update retained recovery evidence and regenerate the public dataset.

Never fill nulls with guesses, estimates, unsupported arithmetic, or aggregator-derived substitutes.

### What automation does now

Hourly NSE discovery can automatically publish:

- issuer name;
- board when explicit from NSE series;
- lifecycle status represented by the feed;
- explicit price band;
- explicit fixed issue price when present;
- explicit market lot when present;
- issue open date;
- issue close date.

### Main remaining limitation

The discovery/publish loop is live, but **deep offer-document enrichment is not fully automated yet**.

Newly discovered IPOs can therefore appear quickly while still showing missing fields such as:

- aggregate issue size in INR;
- minimum bid quantity where not separately stated;
- minimum application amount;
- final issue price;
- listing date;
- sector;
- richer DRHP/RHP/Prospectus evidence.

The next source-automation layer should attach official SEBI / exchange / issuer offer-document evidence to newly discovered IPOs rather than relying on manual recovery prompts.

### Recommended next coherent batch

Automate official filing/document discovery and enrichment for newly detected IPOs, starting with SEBI RHP / Abridged Prospectus / Prospectus matching.

Acceptance criteria should include:

1. deterministic issuer matching;
2. retained official document identity/URL/publication date;
3. no guessing when a match is ambiguous;
4. no weakening of null/conflict rules;
5. source-level tests across several issuers;
6. successful scheduled-run integration without breaking the current live discovery loop.

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

For a fresh chat:

> Continue IPO Tracker development. Read README.md, docs/PROJECT_STATUS.md, and docs/DEVELOPMENT_PROCESS.md first. Follow the repository development process, select the earliest unfinished priority, and complete one coherent batch end to end.

After that, the user may simply say **"continue"**. The repository process/handoff files are the source of truth; the user should not need to resend a large master prompt.
