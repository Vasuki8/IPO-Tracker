# Reviewed active offer terms — 19 September 2026

## Problem, users and acceptance

The next P4 task at `e0094dce2649e3c5761ded4c4de32e7649da4f1f` was the
Axiom Gas Engineering, Varmora Granito and Pooja Logistics active-offer cohort.
Each had four missing exchange fields: price band, bid lot, issue amount and
composition. Investors could see the issue window but not these bidding terms.
Exchange observations are correctly prevented from becoming Final Prospectus
facts; the public projection also withheld independently reviewable active terms.

This shared NSE `issueInfo.dataList` repair targets nine of those twelve gaps:
the three price bands, bid lots and compositions below. Acceptance requires
exact issuer, symbol, board and issue dates; retained response bytes/hash and row
locators; separately reviewed evidence; explicit provisional labels and source
links; unknown observation time preserved; expiry after the IST close date;
unchanged canonical static facts, reviews, pending proposals and histories; and
bounded reviewed publication followed by live checks. Varmora's separately
disclosed minimum quantity is also supported. No subscription figure is selected.

## Source-reviewed candidate values

| Issuer / NSE symbol | Window (2026) | Price band (INR/share) | Bid lot (shares) | Explicit composition |
|---|---|---|---|---|
| Axiom Gas Engineering Limited / AXIOMGAS | 18–22 September | 51–54 | 2,000 | Fresh: up to 9,398,000 shares |
| Varmora Granito Limited / VARMORA | 22–24 September | 140–148 | 101 | Fresh: up to INR 3,200 million (320 crore); OFS: up to 26,217,634 shares |
| Pooja Logistics Limited / POOJALOGIS | 23–25 September | 109–115 | 1,200 | Fresh: 3,846,000 shares, including disclosed reservations |

Varmora's **Minimum Order Quantity** is independently labelled 101 shares.
Neither SME response states a category-neutral minimum quantity. Axiom's
advertisement distinguishes an individual bid of 4,000 shares (two lots) from
other categories, with a minimum of 6,000 and multiples of 2,000. Bid lot, market
lot, minimum quantity and minimum application money must remain distinct.
An unreported OFS leg remains null, never an inferred zero.

All values are active provisional disclosures, not completed/final IPO terms.
The frozen NSE responses expose no source observation timestamp. Retrieval
clocks are retained separately in the fixtures and accepted receipt. No derived
total issue amount is proposed. Explicit "up to" qualifications must survive
public generation and rendering.

## Independent document review and conflicts

The [machine-readable source review](2026-09-19-active-offer-source-review.json)
contains current official URLs, retrieval outcomes, document hashes, dates,
physical pages, row text, units and cross-document findings. Exact NSE response
bytes are retained in `tests/fixtures/active-offer-terms/`; their SHA256 values
were independently recomputed against collection receipts.

* **Axiom:** [issuer-hosted merged disclosure](https://axiomgas.com/uploads/investors/PB_AP_RHP_MERGED.pdf),
  SHA256 `f171f2d945a297488025dd4041f84bd1dc886599dc0757e5fbe6bfc0fc91ee05`.
  The rendered, image-only first page is a **16 September Price Band Revision cum
  Corrigendum** expressly replacing 50–53 with **51–54**. Its paragraph 1 and
  introduction establish the corrected band; section 8 also expressly discloses
  conditional floor/cap amounts. Searchable older advertisement pages retain
  50–53. A whole-document text match or automatic newest-value choice would be
  unsafe. The review accepts the explicit supersession, retaining the old evidence.
* **Varmora:** [issuer-hosted RHP](https://cdn.varmora.com/payload-media/static/Varmora%20Granito%20Limited%20-%20Red%20Herring%20Prospectus.pdf),
  dated 16 September, SHA256 `116ed0c761e9e61b09f84c76edd1fac472de6486884988b948f0722f422d05c2`.
  The cover supports fresh INR 3,200 million and Katsura OFS up to 26,217,634
  shares. The [issuer advertisement on its lead manager's register](https://www.jmfl.com/Common/getFile/6031),
  SHA256 `2287c54ae752a60cf2ed733940fa3e723bcd3a6e245641cb00f0619410417ea4`,
  physical page 1 (Financial Express, 17 September, printed page 16), independently
  confirms 140–148, minimum 101 and multiples of 101. Its floor-price column has
  **49,074,776** shares; its cap-price column has **47,839,255**. Multiplying the
  first count by the cap price produces the unsupported retained 726.31 crore.
  Explicit floor/cap monetary amounts require a separately qualified amount
  display and are outside this receipt's scalar total field.
* **Pooja:** the current official NSE detail response supports the accepted fields
  and the 23–25 September issue window. The NSE-linked RHP archive failed with a
  disconnected connection; the ratios archive timed out. Issuer investor-page
  links pointed to a sample PDF and were not accepted as an RHP. These are source
  access/recovery gaps, not absent disclosures or completed source review.

The detailed JSON also retains BSE access failures. No source failure is cleared.
No missing issuer or filing is inserted, and no financial backfill is performed.

## Publication boundary and measurement

Candidates require an explicit reviewed correction, with an immutable link to
this review, through the existing reviewed bundle/publisher. The entire
`activeOfferTerms` receipt is atomic; ordinary scheduled correction application
cannot activate it. Its source rows are not attached as `staticFieldProvenance`.
Existing holds take precedence, and a later conflicting official observation
cannot silently replace this receipt.

Baseline: **12** cohort missing exchange fields, **387 actionable / 63 higher
priority** P4 records, **1,553 blocking / 1,557 total** source reviews. These twelve
gaps are not twelve source-review findings. Publication must measure supported
missing-field reduction separately; no review-count reduction is presumed.
The three total issue amounts remain unresolved, and all completed static fields
still require Final Prospectus authority. P5/performance remain gated.

Final tests, actual counts, publication commits and live evidence belong in the
release receipt and `docs/PROJECT_STATUS.md` after the bounded publication.
