# IPO Tracker Data Quality

Generated: **2026-09-15T10:36:25+05:30**

Records audited: **1,354**

## Completeness scores

| Area | Score | Records in denominator |
| --- | ---: | ---: |
| Actionable exchange terms | 82.6% | 1,347 |
| Recent exchange terms (2Y) | 96.8% | 438 |
| Offer-document intelligence | 91.5% | 90 |
| Live subscription categories | 77.8% | 9 |
| Matured lifecycle dates | 97.2% | 1,318 |
| Source/provenance trail | 99.5% | 1,354 |

## Actionable exchange fields

| Field | Present | Expected | Missing | Coverage |
| --- | ---: | ---: | ---: | ---: |
| symbol | 1,347 | 1,347 | 0 | 100.0% |
| board | 1,347 | 1,347 | 0 | 100.0% |
| exchange | 1,347 | 1,347 | 0 | 100.0% |
| openDate | 1,347 | 1,347 | 0 | 100.0% |
| closeDate | 1,347 | 1,347 | 0 | 100.0% |
| priceBand | 1,334 | 1,347 | 13 | 99.0% |
| lotSize | 324 | 1,347 | 1,023 | 24.1% |
| issueSizeCr | 436 | 1,347 | 911 | 32.4% |
| issueComposition | 433 | 438 | 5 | 98.9% |

## Recent exchange fields — last 2 years

| Field | Present | Expected | Missing | Coverage |
| --- | ---: | ---: | ---: | ---: |
| symbol | 438 | 438 | 0 | 100.0% |
| board | 438 | 438 | 0 | 100.0% |
| exchange | 438 | 438 | 0 | 100.0% |
| openDate | 438 | 438 | 0 | 100.0% |
| closeDate | 438 | 438 | 0 | 100.0% |
| priceBand | 438 | 438 | 0 | 100.0% |
| lotSize | 321 | 438 | 117 | 73.3% |
| issueSizeCr | 433 | 438 | 5 | 98.9% |
| issueComposition | 433 | 438 | 5 | 98.9% |

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
| registrar | 83 | 90 | 7 | 92.2% |
| leadManagers | 84 | 90 | 6 | 93.3% |
| promoters | 88 | 90 | 2 | 97.8% |
| objectsOfIssue | 86 | 90 | 4 | 95.6% |
| financials | 80 | 90 | 10 | 88.9% |
| promoterShareholding | 73 | 90 | 17 | 81.1% |

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
| listingDate | 1,281 | 1,318 | 37 | 97.2% |

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
