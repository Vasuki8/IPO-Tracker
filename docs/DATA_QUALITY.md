# IPO Tracker Data Quality

Generated: **2026-09-13T04:15:26+05:30**  
Records audited: **1,371**

## Completeness scores

| Area | Score | Records in denominator |
| --- | ---: | ---: |
| Core exchange terms | 66.8% | 1,364 |
| Recent exchange terms (2Y) | 67.5% | 458 |
| Offer-document intelligence | 72.5% | 17 |
| Live subscription categories | 100.0% | 7 |
| Matured lifecycle dates | 48.7% | 1,332 |
| Source/provenance trail | 67.1% | 1,371 |

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
| issueSizeCr | 21 | 1,343 | 1.5% |
| issueComposition | 12 | 1,352 | 0.9% |

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
| issueSizeCr | 21 | 437 | 4.6% |
| issueComposition | 12 | 446 | 2.6% |

## Offer-document fields

| Field | Present | Missing | Coverage |
| --- | ---: | ---: | ---: |
| registrar | 16 | 1 | 94.1% |
| leadManagers | 16 | 1 | 94.1% |
| promoters | 16 | 1 | 94.1% |
| objectsOfIssue | 16 | 1 | 94.1% |
| financials | 9 | 8 | 52.9% |
| promoterShareholding | 1 | 16 | 5.9% |

## Open IPO subscription fields

| Field | Present | Missing | Coverage |
| --- | ---: | ---: | ---: |
| qib | 7 | 0 | 100.0% |
| nii | 7 | 0 | 100.0% |
| retail | 7 | 0 | 100.0% |
| total | 7 | 0 | 100.0% |

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
