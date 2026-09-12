# IPO Tracker Data Quality

Generated: **2026-09-12T10:08:58+05:30**  
Records audited: **1,371**

## Completeness scores

| Area | Score | Records in denominator |
| --- | ---: | ---: |
| Core exchange terms | 44.6% | 1,364 |
| Recent exchange terms (2Y) | 70.8% | 19 |
| Offer-document intelligence | 25.0% | 12 |
| Live subscription categories | 7.1% | 7 |
| Matured lifecycle dates | 100.0% | 0 |
| Source/provenance trail | 67.0% | 1,371 |

## Core exchange fields

| Field | Present | Missing | Coverage |
| --- | ---: | ---: | ---: |
| symbol | 1,357 | 7 | 99.5% |
| board | 1,364 | 0 | 100.0% |
| exchange | 1,364 | 0 | 100.0% |
| openDate | 19 | 1,345 | 1.4% |
| closeDate | 19 | 1,345 | 1.4% |
| priceBand | 1,341 | 23 | 98.3% |
| lotSize | 0 | 1,364 | 0.0% |
| issueSizeCr | 13 | 1,351 | 1.0% |
| issueComposition | 3 | 1,361 | 0.2% |

## Recent exchange fields — last 2 years

| Field | Present | Missing | Coverage |
| --- | ---: | ---: | ---: |
| symbol | 12 | 7 | 63.2% |
| board | 19 | 0 | 100.0% |
| exchange | 19 | 0 | 100.0% |
| openDate | 19 | 0 | 100.0% |
| closeDate | 19 | 0 | 100.0% |
| priceBand | 19 | 0 | 100.0% |
| lotSize | 0 | 19 | 0.0% |
| issueSizeCr | 12 | 7 | 63.2% |
| issueComposition | 2 | 17 | 10.5% |

## Offer-document fields

| Field | Present | Missing | Coverage |
| --- | ---: | ---: | ---: |
| registrar | 1 | 11 | 8.3% |
| leadManagers | 1 | 11 | 8.3% |
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
