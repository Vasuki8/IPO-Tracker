# IPO Tracker Data Quality

Generated: **2026-09-17T03:04:53+05:30**

Records audited: **1,362**

## Completeness scores

| Area | Score | Records in denominator |
| --- | ---: | ---: |
| Actionable exchange terms | 83.5% | 1,353 |
| Recent exchange terms (2Y) | 99.2% | 441 |
| Offer-document intelligence | 76.8% | 277 |
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
| priceBand | 1,337 | 1,353 | 16 | 98.8% |
| lotSize | 437 | 1,353 | 916 | 32.3% |
| issueSizeCr | 439 | 1,353 | 914 | 32.4% |
| issueComposition | 433 | 441 | 8 | 98.2% |

## Recent exchange fields — last 2 years

| Field | Present | Expected | Missing | Coverage |
| --- | ---: | ---: | ---: | ---: |
| symbol | 438 | 441 | 3 | 99.3% |
| board | 441 | 441 | 0 | 100.0% |
| exchange | 441 | 441 | 0 | 100.0% |
| openDate | 441 | 441 | 0 | 100.0% |
| closeDate | 441 | 441 | 0 | 100.0% |
| priceBand | 438 | 441 | 3 | 99.3% |
| lotSize | 431 | 441 | 10 | 97.7% |
| issueSizeCr | 433 | 441 | 8 | 98.2% |
| issueComposition | 433 | 441 | 8 | 98.2% |

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
| registrar | 261 | 277 | 16 | 94.2% |
| leadManagers | 258 | 277 | 19 | 93.1% |
| promoters | 226 | 277 | 51 | 81.6% |
| objectsOfIssue | 214 | 277 | 63 | 77.3% |
| financials | 190 | 277 | 87 | 68.6% |
| promoterShareholding | 127 | 277 | 150 | 45.8% |

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
