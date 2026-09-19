# BSE active offer terms: source review, 19 September 2026

## Problem and bounded acceptance

Latest main at assessment was `5e8642f34447ee56f9026ad23b61838b66204162`.
The next numerical P4 cohort comprised FX Multitech, Robokidz Eduventures,
Vivekanand Cotspin, Himalaya Nutravedics India and S. K. Offset. Their 25
exchange-field gaps prevent researchers from seeing supported bidding terms.
Earlier NSE active-term, financial, universe and operational releases are complete.

Accept only the four matching index/detail pairs below, with exact source bytes,
issuer, board, offer dates, detail identifiers, currency and physical row evidence.
Keep prices, market lots and minimum quantities provisional through the IST close
date. Existing holds and same-offer conflicts win. Do not populate canonical
symbols, static values, subscription snapshots, totals or composition. Use the
existing bounded reviewed publication after support is deployed. Require regression,
browser, source-replay and deployed-byte acceptance, then record release evidence.
These are source-reviewed candidates; this source review does not assert deployment.

## Reviewed values

| Issuer | Offer window, September 2026 | Price band, INR/share | Market lot, shares | Minimum bid quantity, shares | BSE source symbol / issue / IPO number |
| --- | --- | ---: | ---: | ---: | --- |
| FX Multitech Limited | 21-23 | 110-116 | 1,200 | 2,400 | FXML / 4831 / 7980 |
| Robokidz Eduventures Limited | 21-23 | 100-106 | 1,200 | 2,400 | ROBOKIDZ / 4833 / 7982 |
| Himalaya Nutravedics India Limited | 22-24 | 100-106 | 1,200 | 2,400 | HNIL / 4834 / 7983 |
| S. K. Offset Limited | 23-25 | 119-125 | 1,000 | 2,000 | SKOFFSET / 4836 / 7984 |

The [machine receipt](2026-09-19-bse-active-offer-source-review.json) retains
every exact URL, retrieval clock, response hash, outcome and reviewed value.
Five detail responses, the current index and the rupee marker are retained as
inert gzip fixtures in `tests/fixtures/bse-active-offer-terms/`; they do not execute
the upstream page scripts. Decompressing reproduces the original bytes, including
CRLF. Details were collected at 05:33 UTC and the index at 05:35 UTC; source
observation is unknown, not either collection or source-review time.

The current index binds the exact detail link to issuer, SME board, offer window
and IPO/Forthcoming classification. In each accepted detail response, the form
action independently matches those query identifiers, the single issuer table
matches the company, and Security Type, Symbol and Issue Period agree. The detail
price agrees with that issuer's index price. Locators use zero-based HTML table
start-tag order and direct physical row order, including headers/navigation rows:
detail table 2, price row 9, market-lot row 15 and minimum-quantity row 16.

The detail page labels all prices with its rupee image. The exact BSE
`include/images/rs_b.gif` bytes were downloaded and visually inspected (SHA256
`780cc4f5c88a8c41047804b4fa764872b6648ed1df2927225996c5d1bca6a4bc`).
No bare share count is converted to money. `Market Lot` does not populate bid lot.
Canonical symbols remain absent; source symbols are evidence inside the receipt.
A later conflicting nonempty canonical symbol must invalidate the receipt.

## Independent advertisements and unresolved disclosures

Two BSE-linked advertisements were downloaded, their PDF page trees checked and
physical page 1 rendered with Poppler and visually reviewed:

- FX Multitech: Financial Express, 16 September, printed page 26; two-page PDF,
  SHA256 `17ac52d3c93a0b1a1623c1cb3f250824905b3bb531b079e82d15a9a019626509`.
  It independently corroborates the band, 2,400 minimum, 1,200 increment and dates.
  Its provisional gross offering is up to 3,900,000 shares; the detail page's
  2,797,200 shares therefore cannot stand in for the whole offer.
- Robokidz: Financial Express Mumbai, 14 September, printed page 17; three-page
  archive member, SHA256 `5621a22f0ccc91cdfb13c37cef6ca8c30fb97d7eaf04247d1fae4c421564bf9d`.
  It corroborates the band, 2,400 minimum, 1,200 increment and dates. Its gross
  issue is up to 2,932,800 shares, distinct from the detail's 2,104,800.

The text extractors returned private-use/unreadable glyphs in these advertisements;
their text output is not accepted as numeric evidence. Other newspaper editions,
later PDF pages and all financial disclosures are outside this inspection.
The two visual bid-increment statements need their own PDF evidence/replay family
before automatic receipt publication. They are not silently copied into the
DisplayIPO market-lot field or treated as general category-specific bid rules.

Himalaya and S. K. Offset's advertisement links contain Windows filesystem paths
under the official listing host; both returned HTTP 502. Preserve those failures.
Their four-way index/detail identity and labelled quantities still stand as
separate official provisional evidence. No absent advertisement is declared an
undisclosed fact or replaced by a secondary provider.

Vivekanand's detail returned HTTP 200 with an empty issue-type marker and no term
table. Its newly collected index band is 35-37, while the retained same-offer BSE
observation says 32-37. No receipt, band replacement, symbol or quantity is accepted.
The old and new observations remain in the baseline and source fixtures for review.

## Publication and remaining boundaries

The intended numerical reduction is four price-band gaps, from 25 to 21 across
the five-issuer cohort, plus eight separately labelled quantity values. No whole
record or source-review blocker reduction is promised. P4 at assessment is 408
actionable plus 67 higher-priority records, 1,553 blocking / 1,557 total reviews,
zero errors/unmapped and 1,404 canonical records. All 441 proposals remain.

Preserve the original field values, absent keys, proofs, source failures, holds,
quarantines and correction histories. Public directory, profile, quick-view,
comparison and CSV must apply the same field decisions and expiry; quantities
carry their own labels and source links. Minimum application money remains unknown.
No generic Final Prospectus parser or scheduled source collector is expanded.

P5/performance remain gated. BSE commercial collection/display/redistribution
rights, permitted hosting, customer segment, pricing and revenue model remain
unresolved under `COMMERCIAL_READINESS.md`. This source correctness review does
not grant commercial clearance. No accounts, tracking, spend, contracts, outreach,
infrastructure or permissions are introduced.

The next source task after this bounded release is Vivekanand's conflicting
index band and empty detail, followed by the independently evidenced bid-increment
family and remaining gross composition/amount disclosures. Preserve all five older
repair PRs and do not merge their broad stacks merely because tests pass.
