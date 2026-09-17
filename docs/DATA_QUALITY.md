# IPO Tracker Data Quality

Generated: **2026-09-17T11:55:16+05:30**

Records audited: **1,362**

## Completeness scores

| Area | Score | Records in denominator |
| --- | ---: | ---: |
| Actionable exchange terms | 82.7% | 1,353 |
| Recent exchange terms (2Y) | 96.7% | 441 |
| Offer-document intelligence | 66.4% | 387 |
| Live subscription categories | 88.9% | 9 |
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
| issueSizeCr | 390 | 1,353 | 963 | 28.8% |
| issueComposition | 387 | 441 | 54 | 87.8% |

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
| issueSizeCr | 384 | 441 | 57 | 87.1% |
| issueComposition | 387 | 441 | 54 | 87.8% |

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
| registrar | 350 | 387 | 37 | 90.4% |
| leadManagers | 346 | 387 | 41 | 89.4% |
| promoters | 312 | 387 | 75 | 80.6% |
| objectsOfIssue | 67 | 387 | 320 | 17.3% |
| financials | 246 | 387 | 141 | 63.6% |
| promoterShareholding | 220 | 387 | 167 | 56.8% |

## Open IPO subscription fields

| Field | Present | Expected | Missing | Coverage |
| --- | ---: | ---: | ---: | ---: |
| qib | 8 | 9 | 1 | 88.9% |
| nii | 8 | 9 | 1 | 88.9% |
| retail | 8 | 9 | 1 | 88.9% |
| total | 8 | 9 | 1 | 88.9% |

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
