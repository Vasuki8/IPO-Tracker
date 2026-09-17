# IPO Tracker Data Quality

Generated: **2026-09-17T10:40:01+05:30**

Records audited: **1,362**

## Completeness scores

| Area | Score | Records in denominator |
| --- | ---: | ---: |
| Actionable exchange terms | 82.5% | 1,353 |
| Recent exchange terms (2Y) | 96.2% | 441 |
| Offer-document intelligence | 66.0% | 381 |
| Live subscription categories | 77.8% | 9 |
| Matured lifecycle dates | 97.2% | 1,323 |
| Source/provenance trail | 100.0% | 1,362 |

## Actionable exchange fields

| Field | Present | Expected | Missing | Coverage |
| --- | ---: | ---: | ---: | ---: |
| symbol | 1,350 | 1,353 | 3 | 99.8% |
| board | 1,353 | 1,353 | 0 | 100.0% |
| exchange | 1,353 | 1,353 | 0 | 100.0% |
| openDate | 1,353 | 1,353 | 0 | 100.0% |
| closeDate | 1,353 | 1,353 | 0 | 100.0% |
| priceBand | 1,336 | 1,353 | 17 | 98.7% |
| lotSize | 436 | 1,353 | 917 | 32.2% |
| issueSizeCr | 380 | 1,353 | 973 | 28.1% |
| issueComposition | 376 | 441 | 65 | 85.3% |

## Recent exchange fields — last 2 years

| Field | Present | Expected | Missing | Coverage |
| --- | ---: | ---: | ---: | ---: |
| symbol | 438 | 441 | 3 | 99.3% |
| board | 441 | 441 | 0 | 100.0% |
| exchange | 441 | 441 | 0 | 100.0% |
| openDate | 441 | 441 | 0 | 100.0% |
| closeDate | 441 | 441 | 0 | 100.0% |
| priceBand | 437 | 441 | 4 | 99.1% |
| lotSize | 430 | 441 | 11 | 97.5% |
| issueSizeCr | 374 | 441 | 67 | 84.8% |
| issueComposition | 376 | 441 | 65 | 85.3% |

## Historical exchange fields

| Field | Present | Expected | Missing | Coverage |
| --- | ---: | ---: | ---: | ---: |
| symbol | 912 | 912 | 0 | 100.0% |
| board | 912 | 912 | 0 | 100.0% |
| exchange | 912 | 912 | 0 | 100.0% |
| openDate | 912 | 912 | 0 | 100.0% |
| closeDate | 912 | 912 | 0 | 100.0% |
| priceBand | 899 | 912 | 13 | 98.6% |
| lotSize | 6 | 912 | 906 | 0.7% |
| issueSizeCr | 6 | 912 | 906 | 0.7% |

## Offer-document fields

| Field | Present | Expected | Missing | Coverage |
| --- | ---: | ---: | ---: | ---: |
| registrar | 345 | 381 | 36 | 90.6% |
| leadManagers | 341 | 381 | 40 | 89.5% |
| promoters | 295 | 381 | 86 | 77.4% |
| objectsOfIssue | 69 | 381 | 312 | 18.1% |
| financials | 242 | 381 | 139 | 63.5% |
| promoterShareholding | 216 | 381 | 165 | 56.7% |

## Open IPO subscription fields

| Field | Present | Expected | Missing | Coverage |
| --- | ---: | ---: | ---: | ---: |
| qib | 7 | 9 | 2 | 77.8% |
| nii | 7 | 9 | 2 | 77.8% |
| retail | 7 | 9 | 2 | 77.8% |
| total | 7 | 9 | 2 | 77.8% |

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
