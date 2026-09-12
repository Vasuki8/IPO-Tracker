# IPO Tracker Data Quality

Generated: **2026-09-13T04:44:15+05:30**  
Records audited: **1,371**

## Completeness scores

| Area | Score | Records in denominator |
| --- | ---: | ---: |
| Actionable exchange terms | 72.2% | 1,364 |
| Recent exchange terms (2Y) | 67.5% | 458 |
| Offer-document intelligence | 80.4% | 17 |
| Live subscription categories | 100.0% | 7 |
| Matured lifecycle dates | 97.4% | 1,332 |
| Source/provenance trail | 100.0% | 1,371 |

## Actionable exchange fields

| Field | Present | Expected | Missing | Coverage |
| --- | ---: | ---: | ---: | ---: |
| symbol | 1,364 | 1,364 | 0 | 100.0% |
| board | 1,364 | 1,364 | 0 | 100.0% |
| exchange | 1,364 | 1,364 | 0 | 100.0% |
| openDate | 1,364 | 1,364 | 0 | 100.0% |
| closeDate | 1,364 | 1,364 | 0 | 100.0% |
| priceBand | 1,341 | 1,364 | 23 | 98.3% |
| lotSize | 11 | 1,364 | 1,353 | 0.8% |
| issueSizeCr | 21 | 1,364 | 1,343 | 1.5% |
| issueComposition | 12 | 458 | 446 | 2.6% |

## Recent exchange fields — last 2 years

| Field | Present | Expected | Missing | Coverage |
| --- | ---: | ---: | ---: | ---: |
| symbol | 458 | 458 | 0 | 100.0% |
| board | 458 | 458 | 0 | 100.0% |
| exchange | 458 | 458 | 0 | 100.0% |
| openDate | 458 | 458 | 0 | 100.0% |
| closeDate | 458 | 458 | 0 | 100.0% |
| priceBand | 448 | 458 | 10 | 97.8% |
| lotSize | 11 | 458 | 447 | 2.4% |
| issueSizeCr | 21 | 458 | 437 | 4.6% |
| issueComposition | 12 | 458 | 446 | 2.6% |

## Historical exchange fields

| Field | Present | Expected | Missing | Coverage |
| --- | ---: | ---: | ---: | ---: |
| symbol | 906 | 906 | 0 | 100.0% |
| board | 906 | 906 | 0 | 100.0% |
| exchange | 906 | 906 | 0 | 100.0% |
| openDate | 906 | 906 | 0 | 100.0% |
| closeDate | 906 | 906 | 0 | 100.0% |
| priceBand | 893 | 906 | 13 | 98.6% |
| lotSize | 0 | 906 | 906 | 0.0% |
| issueSizeCr | 0 | 906 | 906 | 0.0% |

## Offer-document fields

| Field | Present | Expected | Missing | Coverage |
| --- | ---: | ---: | ---: | ---: |
| registrar | 16 | 17 | 1 | 94.1% |
| leadManagers | 16 | 17 | 1 | 94.1% |
| promoters | 17 | 17 | 0 | 100.0% |
| objectsOfIssue | 16 | 17 | 1 | 94.1% |
| financials | 15 | 17 | 2 | 88.2% |
| promoterShareholding | 2 | 17 | 15 | 11.8% |

## Open IPO subscription fields

| Field | Present | Expected | Missing | Coverage |
| --- | ---: | ---: | ---: | ---: |
| qib | 7 | 7 | 0 | 100.0% |
| nii | 7 | 7 | 0 | 100.0% |
| retail | 7 | 7 | 0 | 100.0% |
| total | 7 | 7 | 0 | 100.0% |

## Matured lifecycle fields

| Field | Present | Expected | Missing | Coverage |
| --- | ---: | ---: | ---: | ---: |
| listingDate | 1,297 | 1,332 | 35 | 97.4% |

## Optional lifecycle observations

| Field | Present | Expected | Missing | Coverage |
| --- | ---: | ---: | ---: | ---: |
| allotmentDate | 0 | 1,332 | 1,332 | 0.0% |

## Interpretation

- **Not yet disclosed** is not treated as a data-quality failure for pre-exchange filings.
- **Collector gap** means an official field is expected and recoverable for that lifecycle/source class but remains missing.
- Fresh/OFS composition is not counted as an archival collector gap unless a qualifying offer document exists.
- Allotment dates remain visible as optional research coverage rather than inflating the actionable queue without a reliable official historical source.
- Recent exchange coverage is the best measure of whether the live collectors are working well today.
- Historical lot size and issue size are progressively repaired from the official BSE historical archive when available.
