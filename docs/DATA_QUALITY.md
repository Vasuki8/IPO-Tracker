# IPO Tracker Data Quality

Generated: **2026-09-19T04:26:58+05:30**

Records audited: **1,379**

## Completeness scores

| Area | Score | Records in denominator |
| --- | ---: | ---: |
| Actionable exchange terms | 82.4% | 1,366 |
| Recent exchange terms (2Y) | 95.6% | 453 |
| Offer-document intelligence | 70.7% | 389 |
| Live subscription categories | 85.0% | 5 |
| Matured lifecycle dates | 97.1% | 1,325 |
| Source/provenance trail | 99.7% | 1,379 |

## Actionable exchange fields

| Field | Present | Expected | Missing | Coverage |
| --- | ---: | ---: | ---: | ---: |
| symbol | 1,361 | 1,366 | 5 | 99.6% |
| board | 1,366 | 1,366 | 0 | 100.0% |
| exchange | 1,366 | 1,366 | 0 | 100.0% |
| openDate | 1,366 | 1,366 | 0 | 100.0% |
| closeDate | 1,366 | 1,366 | 0 | 100.0% |
| priceBand | 1,336 | 1,366 | 30 | 97.8% |
| lotSize | 436 | 1,366 | 930 | 31.9% |
| issueSizeCr | 392 | 1,366 | 974 | 28.7% |
| issueComposition | 389 | 454 | 65 | 85.7% |

## Recent exchange fields — last 2 years

| Field | Present | Expected | Missing | Coverage |
| --- | ---: | ---: | ---: | ---: |
| symbol | 448 | 453 | 5 | 98.9% |
| board | 453 | 453 | 0 | 100.0% |
| exchange | 453 | 453 | 0 | 100.0% |
| openDate | 453 | 453 | 0 | 100.0% |
| closeDate | 453 | 453 | 0 | 100.0% |
| priceBand | 436 | 453 | 17 | 96.2% |
| lotSize | 429 | 453 | 24 | 94.7% |
| issueSizeCr | 385 | 453 | 68 | 85.0% |
| issueComposition | 388 | 453 | 65 | 85.7% |

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
| registrar | 368 | 389 | 21 | 94.6% |
| leadManagers | 365 | 389 | 24 | 93.8% |
| promoters | 343 | 389 | 46 | 88.2% |
| objectsOfIssue | 93 | 389 | 296 | 23.9% |
| financials | 247 | 389 | 142 | 63.5% |
| promoterShareholding | 234 | 389 | 155 | 60.2% |

## Open IPO subscription fields

| Field | Present | Expected | Missing | Coverage |
| --- | ---: | ---: | ---: | ---: |
| qib | 4 | 5 | 1 | 80.0% |
| nii | 4 | 5 | 1 | 80.0% |
| retail | 4 | 5 | 1 | 80.0% |
| total | 5 | 5 | 0 | 100.0% |

## Matured lifecycle fields

| Field | Present | Expected | Missing | Coverage |
| --- | ---: | ---: | ---: | ---: |
| listingDate | 1,286 | 1,325 | 39 | 97.1% |

## Optional lifecycle observations

| Field | Present | Expected | Missing | Coverage |
| --- | ---: | ---: | ---: | ---: |
| allotmentDate | 0 | 1,325 | 1,325 | 0.0% |

## Interpretation

- **Not yet disclosed** is not treated as a data-quality failure for pre-exchange filings.
- **Collector gap** means an official field is expected and recoverable for that lifecycle/source class but remains missing.
- Fresh/OFS composition is not counted as an archival collector gap unless a qualifying offer document exists.
- Allotment dates remain visible as optional research coverage rather than inflating the actionable queue without a reliable official historical source.
- Recent exchange coverage is the best measure of whether the live collectors are working well today.
- Historical lot size and issue size are progressively repaired from the official BSE historical archive when available.
