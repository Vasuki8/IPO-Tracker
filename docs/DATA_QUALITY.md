# IPO Tracker Data Quality

Generated: **2026-09-19T02:50:32+05:30**

Records audited: **1,371**

## Completeness scores

| Area | Score | Records in denominator |
| --- | ---: | ---: |
| Actionable exchange terms | 82.6% | 1,358 |
| Recent exchange terms (2Y) | 96.3% | 445 |
| Offer-document intelligence | 70.7% | 389 |
| Live subscription categories | 85.0% | 5 |
| Matured lifecycle dates | 97.2% | 1,323 |
| Source/provenance trail | 100.0% | 1,371 |

## Actionable exchange fields

| Field | Present | Expected | Missing | Coverage |
| --- | ---: | ---: | ---: | ---: |
| symbol | 1,353 | 1,358 | 5 | 99.6% |
| board | 1,358 | 1,358 | 0 | 100.0% |
| exchange | 1,358 | 1,358 | 0 | 100.0% |
| openDate | 1,358 | 1,358 | 0 | 100.0% |
| closeDate | 1,358 | 1,358 | 0 | 100.0% |
| priceBand | 1,336 | 1,358 | 22 | 98.4% |
| lotSize | 436 | 1,358 | 922 | 32.1% |
| issueSizeCr | 392 | 1,358 | 966 | 28.9% |
| issueComposition | 389 | 446 | 57 | 87.2% |

## Recent exchange fields — last 2 years

| Field | Present | Expected | Missing | Coverage |
| --- | ---: | ---: | ---: | ---: |
| symbol | 440 | 445 | 5 | 98.9% |
| board | 445 | 445 | 0 | 100.0% |
| exchange | 445 | 445 | 0 | 100.0% |
| openDate | 445 | 445 | 0 | 100.0% |
| closeDate | 445 | 445 | 0 | 100.0% |
| priceBand | 436 | 445 | 9 | 98.0% |
| lotSize | 429 | 445 | 16 | 96.4% |
| issueSizeCr | 385 | 445 | 60 | 86.5% |
| issueComposition | 388 | 445 | 57 | 87.2% |

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
