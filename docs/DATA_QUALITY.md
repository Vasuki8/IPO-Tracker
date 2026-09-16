# IPO Tracker Data Quality

Generated: **2026-09-16T05:55:56+05:30**

Records audited: **1,357**

## Completeness scores

| Area | Score | Records in denominator |
| --- | ---: | ---: |
| Actionable exchange terms | 82.6% | 1,350 |
| Recent exchange terms (2Y) | 96.8% | 441 |
| Offer-document intelligence | 91.5% | 90 |
| Live subscription categories | 100.0% | 8 |
| Matured lifecycle dates | 97.3% | 1,321 |
| Source/provenance trail | 99.5% | 1,357 |

## Actionable exchange fields

| Field | Present | Expected | Missing | Coverage |
| --- | ---: | ---: | ---: | ---: |
| symbol | 1,350 | 1,350 | 0 | 100.0% |
| board | 1,350 | 1,350 | 0 | 100.0% |
| exchange | 1,350 | 1,350 | 0 | 100.0% |
| openDate | 1,350 | 1,350 | 0 | 100.0% |
| closeDate | 1,350 | 1,350 | 0 | 100.0% |
| priceBand | 1,337 | 1,350 | 13 | 99.0% |
| lotSize | 329 | 1,350 | 1,021 | 24.4% |
| issueSizeCr | 439 | 1,350 | 911 | 32.5% |
| issueComposition | 435 | 441 | 6 | 98.6% |

## Recent exchange fields — last 2 years

| Field | Present | Expected | Missing | Coverage |
| --- | ---: | ---: | ---: | ---: |
| symbol | 441 | 441 | 0 | 100.0% |
| board | 441 | 441 | 0 | 100.0% |
| exchange | 441 | 441 | 0 | 100.0% |
| openDate | 441 | 441 | 0 | 100.0% |
| closeDate | 441 | 441 | 0 | 100.0% |
| priceBand | 441 | 441 | 0 | 100.0% |
| lotSize | 326 | 441 | 115 | 73.9% |
| issueSizeCr | 436 | 441 | 5 | 98.9% |
| issueComposition | 435 | 441 | 6 | 98.6% |

## Historical exchange fields

| Field | Present | Expected | Missing | Coverage |
| --- | ---: | ---: | ---: | ---: |
| symbol | 909 | 909 | 0 | 100.0% |
| board | 909 | 909 | 0 | 100.0% |
| exchange | 909 | 909 | 0 | 100.0% |
| openDate | 909 | 909 | 0 | 100.0% |
| closeDate | 909 | 909 | 0 | 100.0% |
| priceBand | 896 | 909 | 13 | 98.6% |
| lotSize | 3 | 909 | 906 | 0.3% |
| issueSizeCr | 3 | 909 | 906 | 0.3% |

## Offer-document fields

| Field | Present | Expected | Missing | Coverage |
| --- | ---: | ---: | ---: | ---: |
| registrar | 83 | 90 | 7 | 92.2% |
| leadManagers | 84 | 90 | 6 | 93.3% |
| promoters | 88 | 90 | 2 | 97.8% |
| objectsOfIssue | 86 | 90 | 4 | 95.6% |
| financials | 80 | 90 | 10 | 88.9% |
| promoterShareholding | 73 | 90 | 17 | 81.1% |

## Open IPO subscription fields

| Field | Present | Expected | Missing | Coverage |
| --- | ---: | ---: | ---: | ---: |
| qib | 8 | 8 | 0 | 100.0% |
| nii | 8 | 8 | 0 | 100.0% |
| retail | 8 | 8 | 0 | 100.0% |
| total | 8 | 8 | 0 | 100.0% |

## Matured lifecycle fields

| Field | Present | Expected | Missing | Coverage |
| --- | ---: | ---: | ---: | ---: |
| listingDate | 1,285 | 1,321 | 36 | 97.3% |

## Optional lifecycle observations

| Field | Present | Expected | Missing | Coverage |
| --- | ---: | ---: | ---: | ---: |
| allotmentDate | 0 | 1,321 | 1,321 | 0.0% |

## Interpretation

- **Not yet disclosed** is not treated as a data-quality failure for pre-exchange filings.
- **Collector gap** means an official field is expected and recoverable for that lifecycle/source class but remains missing.
- Fresh/OFS composition is not counted as an archival collector gap unless a qualifying offer document exists.
- Allotment dates remain visible as optional research coverage rather than inflating the actionable queue without a reliable official historical source.
- Recent exchange coverage is the best measure of whether the live collectors are working well today.
- Historical lot size and issue size are progressively repaired from the official BSE historical archive when available.
