# IPO detail navigation and source organization

Date: 2026-09-25. Product batch requested by the user with UI/UX design freedom.

## Change

The company page has a compact, sticky guide to key dates, terms and evidence, and source documents. The hero's document action and guide buttons scroll within the page without changing the `#ipo/{id}` route.

Retained documents are grouped by their existing type label into offer filings, exchange records and other sources. When more than one group exists, a count-labelled filter lets readers focus on one group or return to all. The original source URL, identity, publication date and collection time remain on each item. The groups describe document provenance, not an inferred offer stage. Records with one group or no retained documents do not show unnecessary filters.

No IPO facts, source evidence, collection schedule or data contract changed. Deeper sections such as company financials and risks should wait for source-backed structured data; the existing official filing links already provide a route to those documents.

## Verification

Playwright/Chromium checks pass with real data and isolated edge fixtures, including source grouping and counts, filter switching, hash-route stability, direct links, browser back, 320–1440 px layout, no-documents state, unsafe URLs and HTML escaping. Desktop and mobile detail screenshots were inspected. `test-homepage-order.mjs`, `test-lot-size.mjs`, `validate-data.mjs`, `build-published-data.mjs --check`, JavaScript syntax and `git diff --check` passed locally against 1,243 records at the checked-out revision. That count is a local build check, not a fresh live-publication claim.

Release status and actual Pages verification are recorded in the later release update below.
