# IPO Tracker Data Quality

Generated: **2026-09-18T07:57:52+05:30**

Records audited: **1,366**

## Completeness scores

| Area | Score | Records in denominator |
| --- | ---: | ---: |
| Actionable exchange terms | 82.6% | 1,355 |
| Recent exchange terms (2Y) | 96.6% | 442 |
| Offer-document intelligence | 70.0% | 387 |
| Live subscription categories | 78.1% | 8 |
| Matured lifecycle dates | 97.2% | 1,323 |
| Source/provenance trail | 100.0% | 1,366 |

## Actionable exchange fields

| Field | Present | Expected | Missing | Coverage |
| --- | ---: | ---: | ---: | ---: |
| symbol | 1,351 | 1,355 | 4 | 99.7% |
| board | 1,355 | 1,355 | 0 | 100.0% |
| exchange | 1,355 | 1,355 | 0 | 100.0% |
| openDate | 1,355 | 1,355 | 0 | 100.0% |
| closeDate | 1,355 | 1,355 | 0 | 100.0% |
| priceBand | 1,336 | 1,355 | 19 | 98.6% |
| lotSize | 436 | 1,355 | 919 | 32.2% |
| issueSizeCr | 392 | 1,355 | 963 | 28.9% |
| issueComposition | 389 | 443 | 54 | 87.8% |

## Recent exchange fields — last 2 years

| Field | Present | Expected | Missing | Coverage |
| --- | ---: | ---: | ---: | ---: |
| symbol | 438 | 442 | 4 | 99.1% |
| board | 442 | 442 | 0 | 100.0% |
| exchange | 442 | 442 | 0 | 100.0% |
| openDate | 442 | 442 | 0 | 100.0% |
| closeDate | 442 | 442 | 0 | 100.0% |
| priceBand | 436 | 442 | 6 | 98.6% |
| lotSize | 429 | 442 | 13 | 97.1% |
| issueSizeCr | 385 | 442 | 57 | 87.1% |
| issueComposition | 388 | 442 | 54 | 87.8% |

## Historical exchange fields

| Field | Present | Expected | Missing | Coverage |
| --- | ---: | ---: | ---: | ---: |
| symbol | 913 | 913 | 0 | 100.0% |
| board | 913 | 913 | 0 | 100.0% |
| exchange | 913 | 913 | 0 | 100.0% |
| openDate | 913 | 913 | 0 | 100.0% |
| closeDate | 913 | 913 | 0 | 100.0% |
| priceBand | 900 | 913 | 13 | 98.6% |
| lotSize | 7 | 913 | 906 | 0.8% |
| issueSizeCr | 7 | 913 | 906 | 0.8% |
| issueComposition | 1 | 1 | 0 | 100.0% |

## Offer-document fields

| Field | Present | Expected | Missing | Coverage |
| --- | ---: | ---: | ---: | ---: |
| registrar | 361 | 387 | 26 | 93.3% |
| leadManagers | 357 | 387 | 30 | 92.2% |
| promoters | 343 | 387 | 44 | 88.6% |
| objectsOfIssue | 93 | 387 | 294 | 24.0% |
| financials | 247 | 387 | 140 | 63.8% |
| promoterShareholding | 225 | 387 | 162 | 58.1% |

## Open IPO subscription fields

| Field | Present | Expected | Missing | Coverage |
| --- | ---: | ---: | ---: | ---: |
| qib | 6 | 8 | 2 | 75.0% |
| nii | 6 | 8 | 2 | 75.0% |
| retail | 6 | 8 | 2 | 75.0% |
| total | 7 | 8 | 1 | 87.5% |

## Matured lifecycle fields

| Field | Present | Expected | Missing | Coverage |
| --- | ---: | ---: | ---: | ---: |
| listingDate | 1,286 | 1,323 | 37 | 97.2% |

## Optional lifecycle observations

| Field | Present | Expected | Missing | Coverage |
| --- | ---: | ---: | ---: | ---: |
| allotmentDate | 0 | 1,323 | 1,323 | 0.0% |

## Interpretation

- **Not yet disclosed** is not treated as a data-quality failure for pre-exchange filings.
- **Collector gap** means an official field is expected and recoverable for that lifecycle/source class but remains missing.
- Fresh/OFS composition is not counted as an archival collector gap unless a qualifying offer document exists.
- Allotment dates remain visible as optional research coverage rather than inflating the actionable queue without a reliable official historical source.
- Recent exchange coverage is the best measure of whether the live collectors are working well today.
- Historical lot size and issue size are progressively repaired from the official BSE historical archive when available.
