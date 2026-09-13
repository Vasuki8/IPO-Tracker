# IPO Tracker Data Quality

Generated: **2026-09-13T22:23:56+05:30**  
Records audited: **1,357**

## Completeness scores

| Area | Score | Records in denominator |
| --- | ---: | ---: |
| Actionable exchange terms | 81.9% | 1,350 |
| Recent exchange terms (2Y) | 94.7% | 444 |
| Offer-document intelligence | 62.8% | 73 |
| Live subscription categories | 100.0% | 7 |
| Matured lifecycle dates | 97.5% | 1,318 |
| Source/provenance trail | 100.0% | 1,357 |

## Actionable exchange fields

| Field | Present | Expected | Missing | Coverage |
| --- | ---: | ---: | ---: | ---: |
| symbol | 1,350 | 1,350 | 0 | 100.0% |
| board | 1,350 | 1,350 | 0 | 100.0% |
| exchange | 1,350 | 1,350 | 0 | 100.0% |
| openDate | 1,350 | 1,350 | 0 | 100.0% |
| closeDate | 1,350 | 1,350 | 0 | 100.0% |
| priceBand | 1,335 | 1,350 | 15 | 98.9% |
| lotSize | 316 | 1,350 | 1,034 | 23.4% |
| issueSizeCr | 403 | 1,350 | 947 | 29.9% |
| issueComposition | 403 | 444 | 41 | 90.8% |

## Recent exchange fields — last 2 years

| Field | Present | Expected | Missing | Coverage |
| --- | ---: | ---: | ---: | ---: |
| symbol | 444 | 444 | 0 | 100.0% |
| board | 444 | 444 | 0 | 100.0% |
| exchange | 444 | 444 | 0 | 100.0% |
| openDate | 444 | 444 | 0 | 100.0% |
| closeDate | 444 | 444 | 0 | 100.0% |
| priceBand | 442 | 444 | 2 | 99.5% |
| lotSize | 316 | 444 | 128 | 71.2% |
| issueSizeCr | 403 | 444 | 41 | 90.8% |
| issueComposition | 403 | 444 | 41 | 90.8% |

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
| registrar | 46 | 73 | 27 | 63.0% |
| leadManagers | 46 | 73 | 27 | 63.0% |
| promoters | 46 | 73 | 27 | 63.0% |
| objectsOfIssue | 46 | 73 | 27 | 63.0% |
| financials | 46 | 73 | 27 | 63.0% |
| promoterShareholding | 45 | 73 | 28 | 61.6% |

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
| listingDate | 1,285 | 1,318 | 33 | 97.5% |

## Optional lifecycle observations

| Field | Present | Expected | Missing | Coverage |
| --- | ---: | ---: | ---: | ---: |
| allotmentDate | 0 | 1,318 | 1,318 | 0.0% |

## Interpretation

- **Not yet disclosed** is not treated as a data-quality failure for pre-exchange filings.
- **Collector gap** means an official field is expected and recoverable for that lifecycle/source class but remains missing.
- Fresh/OFS composition is not counted as an archival collector gap unless a qualifying offer document exists.
- Allotment dates remain visible as optional research coverage rather than inflating the actionable queue without a reliable official historical source.
- Recent exchange coverage is the best measure of whether the live collectors are working well today.
- Historical lot size and issue size are progressively repaired from the official BSE historical archive when available.
