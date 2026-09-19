# IPO Tracker Data Quality

Generated: **2026-09-19T20:53:35+05:30**

Records audited: **1,436**

## Completeness scores

| Area | Score | Records in denominator |
| --- | ---: | ---: |
| Actionable exchange terms | 81.3% | 1,423 |
| Recent exchange terms (2Y) | 91.3% | 510 |
| Offer-document intelligence | 70.6% | 390 |
| Live subscription categories | 85.0% | 5 |
| Matured lifecycle dates | 93.2% | 1,380 |
| Source/provenance trail | 99.1% | 1,436 |

## Actionable exchange fields

| Field | Present | Expected | Missing | Coverage |
| --- | ---: | ---: | ---: | ---: |
| symbol | 1,416 | 1,423 | 7 | 99.5% |
| board | 1,423 | 1,423 | 0 | 100.0% |
| exchange | 1,423 | 1,423 | 0 | 100.0% |
| openDate | 1,423 | 1,423 | 0 | 100.0% |
| closeDate | 1,423 | 1,423 | 0 | 100.0% |
| priceBand | 1,339 | 1,423 | 84 | 94.1% |
| lotSize | 439 | 1,423 | 984 | 30.9% |
| issueSizeCr | 394 | 1,423 | 1,029 | 27.7% |
| issueComposition | 392 | 511 | 119 | 76.7% |

## Recent exchange fields — last 2 years

| Field | Present | Expected | Missing | Coverage |
| --- | ---: | ---: | ---: | ---: |
| symbol | 503 | 510 | 7 | 98.6% |
| board | 510 | 510 | 0 | 100.0% |
| exchange | 510 | 510 | 0 | 100.0% |
| openDate | 510 | 510 | 0 | 100.0% |
| closeDate | 510 | 510 | 0 | 100.0% |
| priceBand | 439 | 510 | 71 | 86.1% |
| lotSize | 432 | 510 | 78 | 84.7% |
| issueSizeCr | 387 | 510 | 123 | 75.9% |
| issueComposition | 391 | 510 | 119 | 76.7% |

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
| registrar | 368 | 390 | 22 | 94.4% |
| leadManagers | 365 | 390 | 25 | 93.6% |
| promoters | 343 | 390 | 47 | 87.9% |
| objectsOfIssue | 94 | 390 | 296 | 24.1% |
| financials | 248 | 390 | 142 | 63.6% |
| promoterShareholding | 235 | 390 | 155 | 60.3% |

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
| listingDate | 1,286 | 1,380 | 94 | 93.2% |

## Optional lifecycle observations

| Field | Present | Expected | Missing | Coverage |
| --- | ---: | ---: | ---: | ---: |
| allotmentDate | 0 | 1,380 | 1,380 | 0.0% |

## Interpretation

- **Not yet disclosed** is not treated as a data-quality failure for pre-exchange filings.
- **Collector gap** means an official field is expected and recoverable for that lifecycle/source class but remains missing.
- Fresh/OFS composition is not counted as an archival collector gap unless a qualifying offer document exists.
- Allotment dates remain visible as optional research coverage rather than inflating the actionable queue without a reliable official historical source.
- Recent exchange coverage is the best measure of whether the live collectors are working well today.
- Historical lot size and issue size are progressively repaired from the official BSE historical archive when available.
