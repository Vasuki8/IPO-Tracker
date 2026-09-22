# IPO Tracker

A source-first Indian IPO research interface.

## Current state

This repository was initialized on 2026-09-21 as a fresh UI/UX foundation. The repository was empty when work began, so the current implementation intentionally focuses on presentation architecture rather than recreating an unverified historical backend.

### UI V1 includes

- Responsive light-theme homepage
- IPO master table on desktop
- IPO cards on mobile
- Search and board/status filters
- IPO detail view
- Source status: verified, provisional, missing
- Separate lot size, minimum bid quantity, and minimum application amount
- Offer-document trail
- IPO timeline
- Financial summary layout
- Mobile bottom navigation

## Important

The IPO rows currently shown in the UI are **demo data only**. They are intentionally labeled as such and must not be treated as production market data.

The next engineering step is to connect the interface to the authoritative IPO dataset / recovery pipeline while preserving source provenance and null/conflict handling.

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

When GitHub access was restored on 2026-09-21, the accessible `IPO-Tracker` repository was confirmed to be a fresh/empty repository with no historical commits or branches.

The repository was therefore initialized with **UI/UX V1** rather than attempting to recreate an unseen backend or invent production data.

### Files added

```
index.html
assets/
  styles.css
  app.js
docs/
  PROJECT_STATUS.md
.github/
  workflows/
    deploy-pages.yml
README.md
```

### UI/UX V1 completed

- Responsive light theme
- Desktop IPO master table
- Mobile IPO cards
- Search
- Mainboard / SME filter
- Open / Upcoming / Closed / Listed filters
- IPO detail view
- Source status badges:
  - Verified
  - Provisional
  - Source Missing
- Separate fields for:
  - market lot
  - minimum bid quantity
  - minimum application amount
- IPO timeline
- Offer-document trail
- Financial-summary layout
- Mobile bottom navigation
- GitHub Pages deployment workflow

### Critical data warning

The IPO rows currently inside `assets/app.js` are **demo data only**.

Do not treat them as real IPO records and do not build additional production logic around those values.

The demo rows should be removed or replaced once the real dataset is connected.

### Main blocker

The historical IPO data pipeline / recovered IPO dataset referenced in earlier work is **not present in this repository**.

Do not silently rebuild historical data from guesses.

The next run should first determine where the authoritative current IPO dataset or recovery pipeline exists, or rebuild it explicitly from official sources if it genuinely needs to be recreated.

### Next priority

Connect the UI V1 to the **real source-supported IPO dataset**.

Preserve the following rules while doing so:

1. Never invent or estimate missing values.
2. Preserve nulls and source conflicts.
3. Retain source URL / document identity where available.
4. Keep observation date, collection date, and publication date distinct.
5. Keep market lot, minimum bid quantity, and minimum application amount as separate concepts.
6. Do not require a Final Prospectus before an IPO can appear in the tracker.
7. Use the best available official document for each field, including DRHP, RHP, price-band advertisements, exchange notices, prospectus/final prospectus, registrar or issuer disclosures as appropriate.
8. Clearly label provisional values.
9. Keep the current light-theme UI direction unless a later product decision explicitly changes it.
10. Update `docs/PROJECT_STATUS.md` and this handoff after each substantial run.

### Suggested first actions in the next prompt

1. Fetch latest `main`.
2. Read `README.md` and `docs/PROJECT_STATUS.md`.
3. Inspect the repository before changing anything.
4. Verify GitHub Pages deployment health.
5. Locate or define the authoritative IPO data source/pipeline.
6. Replace demo data incrementally with real source-backed IPO records.
7. Test desktop and mobile rendering after data integration.
8. Commit the coherent change set and update the handoff.

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

