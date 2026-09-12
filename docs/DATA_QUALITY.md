# IPO Tracker Data Quality

Generated: **2026-09-12T10:14:42+05:30**  
Records audited: **1,371**

## Completeness scores

| Area | Score | Records in denominator |
| --- | ---: | ---: |
| Core exchange terms | 44.8% | 1,364 |
| Recent exchange terms (2Y) | 85.4% | 19 |
| Offer-document intelligence | 27.8% | 12 |
| Live subscription categories | 7.1% | 7 |
| Matured lifecycle dates | 100.0% | 0 |
| Source/provenance trail | 67.0% | 1,371 |

## Core exchange fields

| Field | Present | Missing | Coverage |
| --- | ---: | ---: | ---: |
| symbol | 1,364 | 0 | 100.0% |
| board | 1,364 | 0 | 100.0% |
| exchange | 1,364 | 0 | 100.0% |
| openDate | 19 | 1,345 | 1.4% |
| closeDate | 19 | 1,345 | 1.4% |
| priceBand | 1,341 | 23 | 98.3% |
| lotSize | 11 | 1,353 | 0.8% |
| issueSizeCr | 20 | 1,344 | 1.5% |
| issueComposition | 3 | 1,361 | 0.2% |

## Recent exchange fields — last 2 years

| Field | Present | Missing | Coverage |
| --- | ---: | ---: | ---: |
| symbol | 19 | 0 | 100.0% |
| board | 19 | 0 | 100.0% |
| exchange | 19 | 0 | 100.0% |
| openDate | 19 | 0 | 100.0% |
| closeDate | 19 | 0 | 100.0% |
| priceBand | 19 | 0 | 100.0% |
| lotSize | 11 | 8 | 57.9% |
| issueSizeCr | 19 | 0 | 100.0% |
| issueComposition | 2 | 17 | 10.5% |

## Offer-document fields

| Field | Present | Missing | Coverage |
| --- | ---: | ---: | ---: |
| registrar | 2 | 10 | 16.7% |
| leadManagers | 2 | 10 | 16.7% |
| promoters | 6 | 6 | 50.0% |
| objectsOfIssue | 1 | 11 | 8.3% |
| financials | 8 | 4 | 66.7% |
| promoterShareholding | 1 | 11 | 8.3% |

## Open IPO subscription fields

| Field | Present | Missing | Coverage |
| --- | ---: | ---: | ---: |
| qib | 0 | 7 | 0.0% |
| nii | 0 | 7 | 0.0% |
| retail | 0 | 7 | 0.0% |
| total | 2 | 5 | 28.6% |

## Matured lifecycle fields

| Field | Present | Missing | Coverage |
| --- | ---: | ---: | ---: |
| allotmentDate | 0 | 0 | 100.0% |
| listingDate | 0 | 0 | 100.0% |

## Interpretation

- **Not yet disclosed** is not treated as a data-quality failure for pre-exchange filings.
- **Collector gap** means a field is expected for that lifecycle stage but remains missing.
- Recent exchange coverage is the best measure of whether the live collectors are working well today.
- Historical coverage is tracked separately because older exchange/SEBI pages expose fewer structured fields.
