# IPO Tracker Data Quality

Generated: **2026-09-13T16:30:34+05:30**  
Records audited: **1,365**

## Completeness scores

| Area | Score | Records in denominator |
| --- | ---: | ---: |
| Actionable exchange terms | 79.3% | 1,358 |
| Recent exchange terms (2Y) | 87.2% | 452 |
| Offer-document intelligence | 62.8% | 73 |
| Live subscription categories | 100.0% | 7 |
| Matured lifecycle dates | 97.5% | 1,326 |
| Source/provenance trail | 100.0% | 1,365 |

## Actionable exchange fields

| Field | Present | Expected | Missing | Coverage |
| --- | ---: | ---: | ---: | ---: |
| symbol | 1,358 | 1,358 | 0 | 100.0% |
| board | 1,358 | 1,358 | 0 | 100.0% |
| exchange | 1,358 | 1,358 | 0 | 100.0% |
| openDate | 1,358 | 1,358 | 0 | 100.0% |
| closeDate | 1,358 | 1,358 | 0 | 100.0% |
| priceBand | 1,336 | 1,358 | 22 | 98.4% |
| lotSize | 49 | 1,358 | 1,309 | 3.6% |
| issueSizeCr | 397 | 1,358 | 961 | 29.2% |
| issueComposition | 397 | 452 | 55 | 87.8% |

## Recent exchange fields — last 2 years

| Field | Present | Expected | Missing | Coverage |
| --- | ---: | ---: | ---: | ---: |
| symbol | 452 | 452 | 0 | 100.0% |
| board | 452 | 452 | 0 | 100.0% |
| exchange | 452 | 452 | 0 | 100.0% |
| openDate | 452 | 452 | 0 | 100.0% |
| closeDate | 452 | 452 | 0 | 100.0% |
| priceBand | 443 | 452 | 9 | 98.0% |
| lotSize | 49 | 452 | 403 | 10.8% |
| issueSizeCr | 397 | 452 | 55 | 87.8% |
| issueComposition | 397 | 452 | 55 | 87.8% |

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
| listingDate | 1,293 | 1,326 | 33 | 97.5% |

## Optional lifecycle observations

| Field | Present | Expected | Missing | Coverage |
| --- | ---: | ---: | ---: | ---: |
| allotmentDate | 0 | 1,326 | 1,326 | 0.0% |

## Interpretation

- **Not yet disclosed** is not treated as a data-quality failure for pre-exchange filings.
- **Collector gap** means an official field is expected and recoverable for that lifecycle/source class but remains missing.
- Fresh/OFS composition is not counted as an archival collector gap unless a qualifying offer document exists.
- Allotment dates remain visible as optional research coverage rather than inflating the actionable queue without a reliable official historical source.
- Recent exchange coverage is the best measure of whether the live collectors are working well today.
- Historical lot size and issue size are progressively repaired from the official BSE historical archive when available.
