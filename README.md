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
