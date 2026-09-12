# IPO Tracker Data Quality

Generated: **2026-09-13T02:03:58+05:30**  
Records audited: **1,371**

## Completeness scores

| Area | Score | Records in denominator |
| --- | ---: | ---: |
| Core exchange terms | 66.8% | 1,364 |
| Recent exchange terms (2Y) | 67.3% | 458 |
| Offer-document intelligence | 76.4% | 12 |
| Live subscription categories | 28.6% | 7 |
| Matured lifecycle dates | 48.7% | 1,332 |
| Source/provenance trail | 67.0% | 1,371 |

## Core exchange fields

| Field | Present | Missing | Coverage |
| --- | ---: | ---: | ---: |
| symbol | 1,364 | 0 | 100.0% |
| board | 1,364 | 0 | 100.0% |
| exchange | 1,364 | 0 | 100.0% |
| openDate | 1,364 | 0 | 100.0% |
| closeDate | 1,364 | 0 | 100.0% |
| priceBand | 1,341 | 23 | 98.3% |
| lotSize | 11 | 1,353 | 0.8% |
| issueSizeCr | 20 | 1,344 | 1.5% |
| issueComposition | 6 | 1,358 | 0.4% |

## Recent exchange fields — last 2 years

| Field | Present | Missing | Coverage |
| --- | ---: | ---: | ---: |
| symbol | 458 | 0 | 100.0% |
| board | 458 | 0 | 100.0% |
| exchange | 458 | 0 | 100.0% |
| openDate | 458 | 0 | 100.0% |
| closeDate | 458 | 0 | 100.0% |
| priceBand | 448 | 10 | 97.8% |
| lotSize | 11 | 447 | 2.4% |
| issueSizeCr | 20 | 438 | 4.4% |
| issueComposition | 6 | 452 | 1.3% |

## Offer-document fields

| Field | Present | Missing | Coverage |
| --- | ---: | ---: | ---: |
| registrar | 11 | 1 | 91.7% |
| leadManagers | 11 | 1 | 91.7% |
| promoters | 12 | 0 | 100.0% |
| objectsOfIssue | 11 | 1 | 91.7% |
| financials | 9 | 3 | 75.0% |
| promoterShareholding | 1 | 11 | 8.3% |

## Open IPO subscription fields

| Field | Present | Missing | Coverage |
| --- | ---: | ---: | ---: |
| qib | 2 | 5 | 28.6% |
| nii | 2 | 5 | 28.6% |
| retail | 2 | 5 | 28.6% |
| total | 2 | 5 | 28.6% |

## Matured lifecycle fields

| Field | Present | Missing | Coverage |
| --- | ---: | ---: | ---: |
| allotmentDate | 0 | 1,332 | 0.0% |
| listingDate | 1,297 | 35 | 97.4% |

## Interpretation

- **Not yet disclosed** is not treated as a data-quality failure for pre-exchange filings.
- **Collector gap** means a field is expected for that lifecycle stage but remains missing.
- Recent exchange coverage is the best measure of whether the live collectors are working well today.
- Historical coverage is tracked separately because older exchange/SEBI pages expose fewer structured fields.
