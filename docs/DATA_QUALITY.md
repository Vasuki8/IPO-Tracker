# IPO Tracker Data Quality

Generated: **2026-09-19T09:18:23+05:30**

Records audited: **1,404**

## Completeness scores

| Area | Score | Records in denominator |
| --- | ---: | ---: |
| Actionable exchange terms | 82.0% | 1,391 |
| Recent exchange terms (2Y) | 93.7% | 478 |
| Offer-document intelligence | 70.6% | 390 |
| Live subscription categories | 85.0% | 5 |
| Matured lifecycle dates | 95.3% | 1,350 |
| Source/provenance trail | 99.2% | 1,404 |

## Actionable exchange fields

| Field | Present | Expected | Missing | Coverage |
| --- | ---: | ---: | ---: | ---: |
| symbol | 1,386 | 1,391 | 5 | 99.6% |
| board | 1,391 | 1,391 | 0 | 100.0% |
| exchange | 1,391 | 1,391 | 0 | 100.0% |
| openDate | 1,391 | 1,391 | 0 | 100.0% |
| closeDate | 1,391 | 1,391 | 0 | 100.0% |
| priceBand | 1,339 | 1,391 | 52 | 96.3% |
| lotSize | 439 | 1,391 | 952 | 31.6% |
| issueSizeCr | 392 | 1,391 | 999 | 28.2% |
| issueComposition | 392 | 479 | 87 | 81.8% |

## Recent exchange fields — last 2 years

| Field | Present | Expected | Missing | Coverage |
| --- | ---: | ---: | ---: | ---: |
| symbol | 473 | 478 | 5 | 99.0% |
| board | 478 | 478 | 0 | 100.0% |
| exchange | 478 | 478 | 0 | 100.0% |
| openDate | 478 | 478 | 0 | 100.0% |
| closeDate | 478 | 478 | 0 | 100.0% |
| priceBand | 439 | 478 | 39 | 91.8% |
| lotSize | 432 | 478 | 46 | 90.4% |
| issueSizeCr | 385 | 478 | 93 | 80.5% |
| issueComposition | 391 | 478 | 87 | 81.8% |

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
| listingDate | 1,286 | 1,350 | 64 | 95.3% |

## Optional lifecycle observations

| Field | Present | Expected | Missing | Coverage |
| --- | ---: | ---: | ---: | ---: |
| allotmentDate | 0 | 1,350 | 1,350 | 0.0% |

## Interpretation

- **Not yet disclosed** is not treated as a data-quality failure for pre-exchange filings.
- **Collector gap** means an official field is expected and recoverable for that lifecycle/source class but remains missing.
- Fresh/OFS composition is not counted as an archival collector gap unless a qualifying offer document exists.
- Allotment dates remain visible as optional research coverage rather than inflating the actionable queue without a reliable official historical source.
- Recent exchange coverage is the best measure of whether the live collectors are working well today.
- Historical lot size and issue size are progressively repaired from the official BSE historical archive when available.
