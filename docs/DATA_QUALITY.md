# IPO Tracker Data Quality

Generated: **2026-09-17T00:49:32+05:30**

Records audited: **1,361**

## Completeness scores

| Area | Score | Records in denominator |
| --- | ---: | ---: |
| Actionable exchange terms | 83.5% | 1,352 |
| Recent exchange terms (2Y) | 99.2% | 440 |
| Offer-document intelligence | 77.5% | 232 |
| Live subscription categories | 77.8% | 9 |
| Matured lifecycle dates | 97.2% | 1,323 |
| Source/provenance trail | 100.0% | 1,361 |

## Actionable exchange fields

| Field | Present | Expected | Missing | Coverage |
| --- | ---: | ---: | ---: | ---: |
| symbol | 1,350 | 1,352 | 2 | 99.9% |
| board | 1,352 | 1,352 | 0 | 100.0% |
| exchange | 1,352 | 1,352 | 0 | 100.0% |
| openDate | 1,352 | 1,352 | 0 | 100.0% |
| closeDate | 1,352 | 1,352 | 0 | 100.0% |
| priceBand | 1,337 | 1,352 | 15 | 98.9% |
| lotSize | 431 | 1,352 | 921 | 31.9% |
| issueSizeCr | 439 | 1,352 | 913 | 32.5% |
| issueComposition | 433 | 440 | 7 | 98.4% |

## Recent exchange fields — last 2 years

| Field | Present | Expected | Missing | Coverage |
| --- | ---: | ---: | ---: | ---: |
| symbol | 438 | 440 | 2 | 99.5% |
| board | 440 | 440 | 0 | 100.0% |
| exchange | 440 | 440 | 0 | 100.0% |
| openDate | 440 | 440 | 0 | 100.0% |
| closeDate | 440 | 440 | 0 | 100.0% |
| priceBand | 438 | 440 | 2 | 99.5% |
| lotSize | 425 | 440 | 15 | 96.6% |
| issueSizeCr | 433 | 440 | 7 | 98.4% |
| issueComposition | 433 | 440 | 7 | 98.4% |

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
| registrar | 223 | 232 | 9 | 96.1% |
| leadManagers | 224 | 232 | 8 | 96.6% |
| promoters | 200 | 232 | 32 | 86.2% |
| objectsOfIssue | 194 | 232 | 38 | 83.6% |
| financials | 152 | 232 | 80 | 65.5% |
| promoterShareholding | 86 | 232 | 146 | 37.1% |

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
