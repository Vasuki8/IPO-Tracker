# IPO Tracker Data Quality

Generated: **2026-09-19T16:58:00+05:30**

Records audited: **1,406**

## Completeness scores

| Area | Score | Records in denominator |
| --- | ---: | ---: |
| Actionable exchange terms | 81.9% | 1,393 |
| Recent exchange terms (2Y) | 93.5% | 480 |
| Offer-document intelligence | 70.6% | 390 |
| Live subscription categories | 85.0% | 5 |
| Matured lifecycle dates | 95.3% | 1,350 |
| Source/provenance trail | 100.0% | 1,406 |

## Actionable exchange fields

| Field | Present | Expected | Missing | Coverage |
| --- | ---: | ---: | ---: | ---: |
| symbol | 1,386 | 1,393 | 7 | 99.5% |
| board | 1,393 | 1,393 | 0 | 100.0% |
| exchange | 1,393 | 1,393 | 0 | 100.0% |
| openDate | 1,393 | 1,393 | 0 | 100.0% |
| closeDate | 1,393 | 1,393 | 0 | 100.0% |
| priceBand | 1,339 | 1,393 | 54 | 96.1% |
| lotSize | 439 | 1,393 | 954 | 31.5% |
| issueSizeCr | 392 | 1,393 | 1,001 | 28.1% |
| issueComposition | 392 | 481 | 89 | 81.5% |

## Recent exchange fields — last 2 years

| Field | Present | Expected | Missing | Coverage |
| --- | ---: | ---: | ---: | ---: |
| symbol | 473 | 480 | 7 | 98.5% |
| board | 480 | 480 | 0 | 100.0% |
| exchange | 480 | 480 | 0 | 100.0% |
| openDate | 480 | 480 | 0 | 100.0% |
| closeDate | 480 | 480 | 0 | 100.0% |
| priceBand | 439 | 480 | 41 | 91.5% |
| lotSize | 432 | 480 | 48 | 90.0% |
| issueSizeCr | 385 | 480 | 95 | 80.2% |
| issueComposition | 391 | 480 | 89 | 81.5% |

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
