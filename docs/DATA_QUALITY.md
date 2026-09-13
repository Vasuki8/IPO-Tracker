# IPO Tracker Data Quality

Generated: **2026-09-13T08:02:44+05:30**  
Records audited: **1,371**

## Completeness scores

| Area | Score | Records in denominator |
| --- | ---: | ---: |
| Actionable exchange terms | 75.4% | 1,364 |
| Recent exchange terms (2Y) | 76.4% | 458 |
| Offer-document intelligence | 91.7% | 20 |
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
| issueSizeCr | 204 | 1,364 | 1,160 | 15.0% |
| issueComposition | 198 | 458 | 260 | 43.2% |

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
| issueSizeCr | 204 | 458 | 254 | 44.5% |
| issueComposition | 198 | 458 | 260 | 43.2% |

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
| registrar | 20 | 20 | 0 | 100.0% |
| leadManagers | 19 | 20 | 1 | 95.0% |
| promoters | 20 | 20 | 0 | 100.0% |
| objectsOfIssue | 20 | 20 | 0 | 100.0% |
| financials | 20 | 20 | 0 | 100.0% |
| promoterShareholding | 11 | 20 | 9 | 55.0% |

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
