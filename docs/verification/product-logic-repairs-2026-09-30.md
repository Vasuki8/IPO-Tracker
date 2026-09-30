# Website logic repairs — 30 September 2026

This repair batch addresses all seven findings from the website behavior review. It builds on the earlier code-review repairs without discarding them. It is prepared on a repair branch for review; merge and deployment remain pending.

## Behavior changes

| Finding | Result |
| --- | --- |
| Expired offers counted as Open now | Verified closing dates before the Indian market day produce a Bidding closed display. The 30 September review snapshot has six actionable Open rows instead of twelve. Retained reported status and sources remain available. |
| Unexplained verified pricing disagreement | A final issue price outside the retained band shows Price conflict in desktop/mobile results and detail. Both evidence summaries and overall coverage show Conflict. Energy-Mission retains ₹131–₹138 and ₹60 with an explanation that the basis is unresolved. |
| Mixed meanings under Lot size | The headline explicitly labels Trading lot or Minimum IPO bid, preserving market-lot-first precedence. Detail evidence exposes both quantities separately, including RBZ's 1-share trading lot and 150-share minimum IPO bid. |
| Recent listing-only records buried by Newest first | The first valid opening, closing, or listing date is compared across all records. Invalid dates fall back, undated records sort last, and ties remain deterministic. ENS moves from global position 305 to 56. The builder uses the same comparator as the website. |
| Advertised sector search without classifications | Search is labelled and implemented as company-name search until sector classifications exist. |
| Draft freshness hidden behind a newer lifecycle timestamp | The page separately shows loaded draft-source collection, IPO lifecycle dataset generation, and reported refresh attempt/status. Failed/unavailable refreshes preserve data and source timestamps. A mismatched successful health report cannot redate the loaded evidence. |
| Unclassified boards missing from board browsing | Board unavailable is a selectable filter, survives URL reload, and exposes all 41 unclassified records without assigning a board. |

The independent review also found that an already-open tab could retain yesterday's bidding status across Indian midnight. A market-day timer and focus/visibility refresh now update counts, filters and detail bidding state without reloading or resetting expanded term evidence.

## Evidence preservation

- All 1,387 records, source fields, evidence, corrections and top-level metadata are unchanged by this batch after ignoring record order. Deep equality was checked against the pre-batch snapshot `/tmp/ipo-product-order-before.json`.
- The public dataset's generation timestamp remains `2026-09-30T14:37:04Z`. Reordering does not imply a fresh source collection.
- Date projection changes the website's bidding display; it does not overwrite reported lifecycle status or infer actual listing/trading.
- Pricing reconciliation remains unresolved in the retained sources. The repair makes that uncertainty explicit rather than selecting an unsupported correct value.
- No sector or board classification was invented. Minimum investment calculations remain out of scope.

## Verification

Failing regressions were observed before the changes for the original website contradictions, cross-date-kind sorting, impossible calendar-date fallback, draft freshness, and open-tab midnight behavior.

The final full regression run passed all 103 `scripts/test-*.mjs` entry points, including the existing website browser suite and the two new browser suites. All 209 JavaScript syntax checks, YAML parsing, 230 workflow shell syntax checks, builder synchronization, schema validation and `git diff --check` passed. The independent reviewer found no remaining important issues after the midnight repair, and separately verified focus/visibility refresh and preservation of expanded evidence, document category and filter URL.

Focused verification commands:

```sh
node scripts/test-homepage-order.mjs
node scripts/build-published-data.mjs --check
node scripts/validate-data.mjs
PLAYWRIGHT_MODULE=/path/to/node_modules/playwright node scripts/test-ui.mjs
PLAYWRIGHT_MODULE=/path/to/node_modules/playwright node scripts/test-product-logic-ui.mjs
PLAYWRIGHT_MODULE=/path/to/node_modules/playwright node scripts/test-drhp-freshness.mjs
```

Product browser checks cover real dataset examples, future opening dates, closing-day inclusion, Indian date rollover, no inferred listing, compatible and missing final prices, explicit lot labels on mobile and desktop, searchable companies, board-filter persistence, and widths from 320 to 1440 pixels. Freshness checks cover eight success/failure/unavailable/mismatched timestamp scenarios.

The UI workflow now runs all three browser entry points and is triggered by relevant source/data/health changes. Two historical non-browser workflow loops explicitly exclude the browser suites, which require the separate Playwright installation.

Final results and screenshots are retained under `/workspace/ipo-tools/product-review/` in this cloud workspace. Production behavior and fresh exchange data were not verified or changed by this batch.

## Integration preparation

The repair branch subsequently incorporated main through `6a14056704b0993052630303718e0a0c21604159`, including its latest automated source collection. The recovery generation timestamp uses that newer source update, and the public array was regenerated with the shared builder to resolve its ordering conflict. Comparison against that main snapshot confirms all 1,387 stable IDs, every term/source value and its generation timestamp are preserved. Only the five intended status/evidence repairs from the earlier code-review batch differ; prior status sources remain retained. These incoming source changes are distinct from the original offline repair and website review.
