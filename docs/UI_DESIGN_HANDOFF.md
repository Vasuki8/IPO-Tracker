# IPO Tracker UI V2 handoff

Date: 2026-09-24. User request: “Design new UI for IPO Tracker.”

## Scope and design

This explicitly requested product batch redesigns the existing static interface. It uses a light off-white canvas, forest-green accents, a compact overview strip, a desktop comparison table and mobile cards. It retains the existing data fetch and lot-size/newest-first helpers.

The directory now has one search box, status tabs with counts, board and year filters, newest-first/company sorting, 20-record pagination, shareable filter URLs, clear/reset actions and honest loading/error/retry/empty states. Summary counts refer to the full published corpus; tab counts respect the other filters. Year means opening date, falling back to closing/listing date. Missing-year records have their own filter option.

The company page now works: the prior app attempted to populate an absent `#documentList`. V2 provides real document links, a source-backed three-date timeline, expandable evidence for each term, correction history when retained, explicit publication/collection dates and labelled dataset-generation time. Unimplemented placeholder navigation and sample document markup were removed. No calendar/watchlist/compare/backend or commercial service was added.

Evidence coverage groups price band/final price as alternatives and uses the existing verified lot fallback. Raw price/quantity conflicts and provisional states remain visible even when an alternate term supplies the displayed value. Complete means all six displayed term groups are verified; partial/missing remain neutral, while provisional/conflict retain distinct labels. Fractional rupee prices are no longer rounded to whole rupees. Untrusted text is escaped and source links accept only HTTP(S).

## Files

- `index.html`, `assets/styles.css`, `assets/app.js`, `assets/favicon.svg`.
- `scripts/test-ui.mjs`: browser regression suite using the current published corpus and isolated edge-case fixtures.
- `.github/workflows/validate-ui.yml`: browser checks scoped to frontend changes; test dependencies and screenshots stay in runner temporary storage.

No files under `data/` or `ops/`, source-recovery scripts, collection schedules, public field contracts or existing lot-size/order helpers were edited by this product batch. The full public JSON is still fetched; this release does not change data architecture.

## Validation

Local Chromium/Playwright checks passed at 320, 390, 820, 1024 and 1440 pixels. They cover real records, filters, counts, sorting, pagination, URL restoration, direct company links, browser back, evidence expansion, source documents, keyboard search, modal Escape/focus, long names, missing/provisional/conflict states, fractional prices, HTML escaping, unsafe link rejection and dataset error/retry/empty/malformed states. Desktop, mobile and detail screenshots were visually inspected.

Also passed: JavaScript syntax, `test-homepage-order.mjs`, `test-lot-size.mjs`, `validate-data.mjs` and `git diff --check`.

Browser setup: Playwright 1.56.1 with its Chromium build. The environment's preinstalled Playwright binary was unavailable; the isolated pinned test runtime downloaded successfully from the official fallback mirror. A tablet overflow from an absolutely positioned screen-reader label was found and fixed by containing it within the scrolling table. Mobile metrics were tightened after visual review.

Run locally with Playwright installed and Chromium available:

```bash
node scripts/test-ui.mjs
```

The `PLAYWRIGHT_MODULE` environment variable can point at an isolated Playwright installation; `UI_SCREENSHOT_DIR` optionally retains previews. Neither is needed for production.

## Release status

Implementation and local checks complete. PR CI, merge and actual Pages verification are pending; update this section with release evidence before marking the batch verified.

## Next work

For UI follow-ups, preserve the light theme and source-visible values. Do not add placeholder controls for unavailable features. For generic backend continuation, follow the current cursor7 next task in `PROJECT_STATUS.md`; this UI batch does not close or replay that work.
