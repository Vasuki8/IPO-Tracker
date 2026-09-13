# IPO Tracker Data Quality

Generated: **2026-09-14T04:22:21+05:30**  
Records audited: **1,354**

## Completeness scores

| Area | Score | Records in denominator |
| --- | ---: | ---: |
| Actionable exchange terms | 82.4% | 1,347 |
| Recent exchange terms (2Y) | 96.2% | 438 |
| Offer-document intelligence | 100.0% | 73 |
| Live subscription categories | 100.0% | 7 |
| Matured lifecycle dates | 97.5% | 1,316 |
| Source/provenance trail | 100.0% | 1,354 |

## Actionable exchange fields

| Field | Present | Expected | Missing | Coverage |
| --- | ---: | ---: | ---: | ---: |
| symbol | 1,347 | 1,347 | 0 | 100.0% |
| board | 1,347 | 1,347 | 0 | 100.0% |
| exchange | 1,347 | 1,347 | 0 | 100.0% |
| openDate | 1,347 | 1,347 | 0 | 100.0% |
| closeDate | 1,347 | 1,347 | 0 | 100.0% |
| priceBand | 1,334 | 1,347 | 13 | 99.0% |
| lotSize | 318 | 1,347 | 1,029 | 23.6% |
| issueSizeCr | 432 | 1,347 | 915 | 32.1% |
| issueComposition | 422 | 438 | 16 | 96.3% |

## Recent exchange fields — last 2 years

| Field | Present | Expected | Missing | Coverage |
| --- | ---: | ---: | ---: | ---: |
| symbol | 438 | 438 | 0 | 100.0% |
| board | 438 | 438 | 0 | 100.0% |
| exchange | 438 | 438 | 0 | 100.0% |
| openDate | 438 | 438 | 0 | 100.0% |
| closeDate | 438 | 438 | 0 | 100.0% |
| priceBand | 438 | 438 | 0 | 100.0% |
| lotSize | 315 | 438 | 123 | 71.9% |
| issueSizeCr | 429 | 438 | 9 | 97.9% |
| issueComposition | 422 | 438 | 16 | 96.3% |

## Historical exchange fields

| Field | Present | Expected | Missing | Coverage |
| --- | ---: | ---: | ---: | ---: |
| symbol | 909 | 909 | 0 | 100.0% |
| board | 909 | 909 | 0 | 100.0% |
| exchange | 909 | 909 | 0 | 100.0% |
| openDate | 909 | 909 | 0 | 100.0% |
| closeDate | 909 | 909 | 0 | 100.0% |
| priceBand | 896 | 909 | 13 | 98.6% |
| lotSize | 3 | 909 | 906 | 0.3% |
| issueSizeCr | 3 | 909 | 906 | 0.3% |

## Offer-document fields

| Field | Present | Expected | Missing | Coverage |
| --- | ---: | ---: | ---: | ---: |
| registrar | 73 | 73 | 0 | 100.0% |
| leadManagers | 73 | 73 | 0 | 100.0% |
| promoters | 73 | 73 | 0 | 100.0% |
| objectsOfIssue | 73 | 73 | 0 | 100.0% |
| financials | 73 | 73 | 0 | 100.0% |
| promoterShareholding | 73 | 73 | 0 | 100.0% |

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
| listingDate | 1,283 | 1,316 | 33 | 97.5% |

## Optional lifecycle observations

| Field | Present | Expected | Missing | Coverage |
| --- | ---: | ---: | ---: | ---: |
| allotmentDate | 0 | 1,316 | 1,316 | 0.0% |

## Interpretation

- **Not yet disclosed** is not treated as a data-quality failure for pre-exchange filings.
- **Collector gap** means an official field is expected and recoverable for that lifecycle/source class but remains missing.
- Fresh/OFS composition is not counted as an archival collector gap unless a qualifying offer document exists.
- Allotment dates remain visible as optional research coverage rather than inflating the actionable queue without a reliable official historical source.
- Recent exchange coverage is the best measure of whether the live collectors are working well today.
- Historical lot size and issue size are progressively repaired from the official BSE historical archive when available.
