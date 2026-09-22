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

The tracker now has an automated discovery, official-document enrichment, and publishing loop.

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

Explicit final issue-price extraction from retained official SEBI Prospectus PDFs is now production-verified.

PR #18 added a conservative extractor that scans only retained official `SEBI Prospectus PDF` attachments, fills missing `issue_price` only, preserves page-level evidence, and does not infer the final price from a price band or cap.

Earlier, official SEBI document discovery was integrated into the hourly NSE sync.

PRs #10–#15 implemented and hardened:

- deterministic RHP / Abridged Prospectus / Prospectus matching;
- dynamic SEBI filing-link parsing;
- general Filings and mixed Public Issues coverage;
- bounded issuer-specific searches for sparse NSE-live records;
- strict ambiguity rejection and idempotent document attachment.

The production network path is verified end to end. The latest real run passed NSE collection, SEBI collection, rebuild, deterministic publication and data-contract validation.

**Important current limitation:** the raw SEBI responses available to GitHub Actions still did not add documents to the 9 sparse issuers created by the first NSE live run. The latest measurement searched all 9 sparse records, parsed 5 targeted filing results, but produced 0 exact issuer matches. Matching will remain strict rather than attaching uncertain evidence.

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

The discovery/publish loop and SEBI matcher are live, but two evidence-depth gaps remain:

1. SEBI's raw pages do not currently expose attachable documents for every sparse NSE-live issuer in GitHub Actions;
2. field extraction is currently bounded to explicit Abridged Prospectus aggregate size and explicit final-Prospectus issue price; most remaining fields are not automated yet.

IPOs can therefore still show missing fields such as:

- aggregate issue size in INR;
- minimum bid quantity where not separately stated;
- minimum application amount;
- final issue price where the retained official Prospectus does not contain supported explicit wording in the bounded scan;
- listing date;
- sector;
- richer DRHP/RHP/Prospectus evidence.

The next source-automation layer should parse a bounded set of fields from retained official offer documents, with explicit source precedence and page-level evidence, rather than inferring values from filenames or price-band caps.

### Latest field-extraction result

The Abridged Prospectus issue-size extractor is now production-verified.

PR #16 merged at `c7c59252bb9e59b3767d73205ad1d682326c48b8`.

Real hourly run `35686786294` downloaded all 4 eligible retained SEBI Abridged Prospectus PDFs with zero fetch errors and:

- extracted Karamtara Engineering's explicit total offer size of ₹8,750.00 million;
- preserved ARCIL, Pranav Constructions and Sonaselection as null because their first-page total-size cells were placeholders/non-explicit;
- left ESDS unchanged because it already had verified issue-size evidence.

The source-backed bot commit is `92f0f024367b20a9f023218a0cb92ecbc2e38636`.

### Latest final-document result

Direct official final-Prospectus PDF resolution is now production-verified.

PR #17 merged at `cd39442c03450a9189d783d554e3feb48ee57239`.

Real sync run `35687483282` resolved and attached **9 official SEBI Prospectus PDFs** to deterministic issuer records. Bot commit `0c3e1c199fdb12266589c7f65eead373c49065dd` changed document evidence/freshness only; no market field was inferred or overwritten.

### Latest final-Prospectus price result

PR #18 merged at `1b41f0c115c5df993486e3d3e5f52668d73ffcfc`.

Production sync run `35688500637` evaluated 7 missing-price records with retained official SEBI Prospectus PDFs:

- 7 PDFs downloaded successfully;
- 4 explicit final issue prices extracted;
- 3 remained null because no supported explicit final-price phrase was found in the bounded scan;
- 0 PDF fetch errors.

Verified prices published with PDF-page evidence:

- Kanohar Electricals Limited — ₹632, PDF page 7;
- LCC Projects Limited — ₹146, PDF page 7;
- Manipal Payment and Identity Solutions Limited — ₹339, PDF page 3;
- Pranav Constructions Limited — ₹124, PDF page 5.

Preserved as null:

- Jindal Supreme (India) Limited;
- SS Retail Limited;
- Veegaland Developers Limited.

Source-backed bot commit: `f9b7155c42d8b44d6985d9dafb9fd242e37dc64e`.

GitHub Pages deployment for that bot commit passed in run `35688893344`.

### Recommended next coherent batch

Inspect the three retained final Prospectuses that still have null issue price to determine whether the missing value is due to wording/layout/page-scope coverage before broadening the parser. Keep strict explicit-value rules. After that, add a separately tested bounded extractor for explicit aggregate issue size from final Prospectus PDFs.

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
