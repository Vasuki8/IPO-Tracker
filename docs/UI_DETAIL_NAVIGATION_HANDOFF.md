# IPO detail navigation and source organization

Date: 2026-09-25. Product batch requested by the user with UI/UX design freedom.

## Change

The company page has a compact, sticky guide to key dates, terms and evidence, and source documents. The hero's document action and guide buttons scroll within the page without changing the `#ipo/{id}` route.

Retained documents are grouped by their existing type label into offer filings, exchange records and other sources. When more than one group exists, a count-labelled filter lets readers focus on one group or return to all. The original source URL, identity, publication date and collection time remain on each item. The groups describe document provenance, not an inferred offer stage. Records with one group or no retained documents do not show unnecessary filters.

No IPO facts, source evidence, collection schedule or data contract changed. Deeper sections such as company financials and risks should wait for source-backed structured data; the existing official filing links already provide a route to those documents.

## Verification

Playwright/Chromium checks pass with real data and isolated edge fixtures, including source grouping and counts, filter switching, hash-route stability, direct links, browser back, 320–1440 px layout, no-documents state, unsafe URLs and HTML escaping. Desktop and mobile detail screenshots were inspected. `test-homepage-order.mjs`, `test-lot-size.mjs`, `validate-data.mjs`, `build-published-data.mjs --check`, JavaScript syntax and `git diff --check` passed locally against 1,243 records at the checked-out revision. That count is a local build check, not a fresh live-publication claim.

## Release verification

**Verified live.** [PR #237](https://github.com/Vasuki8/IPO-Tracker/pull/237) merged as `8dea7696883f0418e90d02ce7981c5a85a7ffb9d`. PR checks passed: interface `36163555130`, data contract `36163555071`, reviewed BSE evidence `36163555072`.

At `2026-09-25T16:56:18Z`, the ordinary Pages URL served HTML, CSS and JavaScript whose SHA-256 values exactly matched the release files. A deployed mobile Chromium session loaded the current dataset, opened Shah Investor's Home Limited through its direct IPO route, rendered all five retained documents, filtered to two exchange records, preserved the route, found no horizontal overflow, and produced no page errors. The actual Pages dataset had 1,256 records, generated at `2026-09-25T16:08:35.285Z`; this is a separate publication observation, not a source recency claim. The backend batch3 release is tracked in the P1 handoff independently.

Durable receipt: [verification/ui-detail-navigation-live-2026-09-25.json](verification/ui-detail-navigation-live-2026-09-25.json). The browser's isolated proxy connection required `ignoreHTTPSErrors`; independent normal-TLS downloads confirmed the exact served release bytes and dataset hash. Production security settings were not changed.
