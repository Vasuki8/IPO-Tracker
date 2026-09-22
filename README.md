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

SEBI RHP source recovery is now production-repaired and significantly deeper.

PR #28 bypassed stale SEBI listing cache responses. PR #29 repaired a live malformed-anchor pattern where an RHP filing URL was paired with adjacent Abridged Prospectus text. Production sync `35693813309` then increased deterministic SEBI latest-list matches from 9 to 22, changed 8 issuer records, and attached 11 official documents.

PR #30 added direct official RHP PDF resolution from retained SEBI RHP filing pages. Production sync `35694073605` resolved **13 `SEBI RHP PDF` attachments** and retained them without publishing any RHP-derived market term.

Explicit aggregate issue-size extraction from retained official SEBI final Prospectus PDFs is also production-verified.

PR #23 used a temporary read-only diagnostic to inspect the seven retained final Prospectuses that still lacked `issue_size_inr`. PR #24 then added a bounded extractor for explicit top-level Offer/Issue aggregate amounts and removed the temporary diagnostic from the hourly workflow.

Final issue-price recovery from the currently retained official SEBI Prospectus PDFs is also complete.

PR #20 added a temporary read-only diagnostic scan for the three remaining null cases and proved the 20-page boundary was not the problem. Their final prices were stated on PDF pages 2–3 using the reverse-labelled cover form `at a price of ₹X per Equity Share ... (Offer/Issue Price)`.

PR #21 added only that explicit syntax to the production parser, tested the three real wording patterns plus a negative unlabeled-price case, and removed the expensive diagnostic step from the hourly workflow. The production sync then filled all three remaining prices from official SEBI Prospectus evidence.

Earlier, official SEBI document discovery was integrated into the hourly NSE sync.

PRs #10–#15 implemented and hardened:

- deterministic RHP / Abridged Prospectus / Prospectus matching;
- dynamic SEBI filing-link parsing;
- general Filings and mixed Public Issues coverage;
- bounded issuer-specific searches for sparse NSE-live records;
- strict ambiguity rejection and idempotent document attachment.

The production network path is verified end to end. The latest real run passed NSE collection, SEBI collection, rebuild, deterministic publication and data-contract validation.

**Important current limitation:** current SEBI recovery now covers 17 of the 23 published issuer records. Six live-discovered issuers still have no retained SEBI document: ArMee Infotech, Axiom Gas Engineering, Coreintegra Consulting Services, Elevate Campuses, Pooja Logistics, and Varmora Granito. Matching remains strict rather than attaching uncertain evidence.

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
- final issue price for issuers that do not yet have a retained authoritative final-price source;
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

PR #18 merged at `1b41f0c115c5df993486e3d3e5f52668d73ffcfc` and initially recovered four missing final prices.

PR #20 merged at `f141c4fef5f5ce9025a9e6e809b9cc0c80a68b2f` as a one-run diagnostic. Production run `35689468724` scanned the three unresolved official PDFs and found explicit cover statements on early pages:

- Jindal Supreme (India) Limited — `₹93 per Equity Share ... (Offer Price)`, PDF page 3;
- SS Retail Limited — `₹424^ per Equity Share ... (Offer Price)`, PDF page 3;
- Veegaland Developers Limited — `₹140 per Equity Share ... (Issue Price)`, PDF page 2.

PR #21 merged at `454ec51a640f2f4079577d41d84dec222fe48e63` and added only that labelled cover syntax. Production run `35690054143` then completed successfully:

- candidates: 3;
- official PDFs downloaded: 3;
- extracted: 3;
- explicit-price missing: 0;
- PDF fetch errors: 0.

The source-backed bot commit is `51f806b16e4eba40efee304d07bb5753a8e0f9d9`. All nine records that currently retain an official `SEBI Prospectus PDF` now have a retained final issue price; existing Hero Motors and Rentomojo evidence was not overwritten.

### Latest final-Prospectus issue-size result

PR #23 merged at `5a0b7e225c53c737b43750db61b19309d29dabc0` as a temporary read-only diagnostic. It confirmed that all seven missing-size final Prospectuses contain an explicit top-level aggregate Offer/Issue amount on PDF pages 2–3, while the same pages also contain smaller Fresh Issue and/or OFS component amounts.

PR #24 merged at `a7d2afc5f69fe97f17564e86b72e1ebe3cd296b6`. The extractor accepts only explicit overall Offer/Issue amounts, supports million/lakh/crore units, fills missing values only, and rejects Fresh Issue-only, OFS-only and unlabeled aggregate amounts.

Production sync run `35691580621` completed successfully:

- candidates: 7;
- official PDFs downloaded: 7;
- extracted: 7;
- explicit-size missing: 0;
- PDF fetch errors: 0.

Published with official SEBI Prospectus PDF/page evidence:

- Jindal Supreme (India) Limited — ₹1,248,804,000 — PDF page 3;
- Kanohar Electricals Limited — ₹10,557,400,000 — PDF page 3;
- LCC Projects Limited — ₹4,271,410,000 — PDF page 3;
- Manipal Payment and Identity Solutions Limited — ₹8,050,000,000 — PDF page 3;
- Pranav Constructions Limited — ₹3,510,250,000 — PDF page 2;
- SS Retail Limited — ₹5,000,000,000 — PDF page 3;
- Veegaland Developers Limited — ₹2,100,000,000 — PDF page 2.

Source-backed bot commit: `0110d864235eccb800efa5b206fa19bf9cdb0fb4`.

GitHub Pages deployment for that data revision passed in run `35692087146`.

All 9 records currently carrying retained `SEBI Prospectus PDF` evidence now have both final issue price and aggregate issue-size evidence.

### Latest homepage ordering result

The homepage IPO market list is explicitly ordered **newest to oldest** by source-backed IPO open date.

A follow-up repair also changed deterministic publication order in `data/ipos.json` from issuer-name alphabetical to newest-first and versioned the ordering scripts. This makes the visible order resilient even when a browser has cached the previous UI JavaScript.

Implementation rules:

- primary sort: `open_date` descending;
- tie-breaker: `close_date` descending;
- final deterministic tie-breaker: issuer name;
- missing/invalid dates sort last;
- sorting is applied after search/board/status filters, so filtered desktop and mobile views remain newest-first;
- the underlying `data/ipos.json` order and all source evidence remain unchanged.

PR #26 adds the shared ordering helper plus a behavioral test against the current published dataset.

### Latest RHP recovery result

The repaired RHP source family now retains direct official RHP PDFs. Five records still missing `issue_size_inr` now have both an Abridged Prospectus and an RHP PDF:

- Adroit Industries (India) Limited;
- Asset Reconstruction Company (India) Limited;
- National Stock Exchange of India Limited;
- Sonaselection India Limited;
- Swastika Infra Limited.

The existing page-1 Abridged Prospectus extractor checked all five and extracted **0** because the aggregate-size cells remain placeholders. That null preservation is intentional.

Source-backed document bot commits:

- `ec684bc1fa558f2dafb7c7b90df6b750fc6f79ac` — repaired current-list RHP/Abridged attachments;
- `3c2f3fb8a8737fe2067aab3e18e39ab86a68eeb6` — 13 direct RHP PDF attachments.

GitHub Pages deployment for `3c2f3fb...` passed in run `35694143832`.

### Recommended next coherent batch

Add a bounded **RHP aggregate issue-size extraction family for the five RHP-backed missing-size records**, but publish any RHP-derived value as **provisional**, not verified/final.

First extend retained-field publication so a recovery field can preserve `status: "provisional"`. Then inspect only explicit top-level Offer/Issue aggregate amounts from retained `SEBI RHP PDF` files, retain page-level evidence, fill missing values only, and never sum Fresh Issue + OFS components or calculate shares × price.

The other remaining missing-size records should stay null until an authoritative official source family becomes available.

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
