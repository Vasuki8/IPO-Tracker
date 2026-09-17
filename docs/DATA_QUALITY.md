# IPO Tracker Data Quality

Generated: **2026-09-17T23:52:33+05:30**

Records audited: **1,366**

## Completeness scores

| Area | Score | Records in denominator |
| --- | ---: | ---: |
| Actionable exchange terms | 82.6% | 1,355 |
| Recent exchange terms (2Y) | 96.6% | 443 |
| Offer-document intelligence | 68.1% | 387 |
| Live subscription categories | 91.7% | 9 |
| Matured lifecycle dates | 97.2% | 1,323 |
| Source/provenance trail | 100.0% | 1,366 |

## Actionable exchange fields

| Field | Present | Expected | Missing | Coverage |
| --- | ---: | ---: | ---: | ---: |
| symbol | 1,351 | 1,355 | 4 | 99.7% |
| board | 1,355 | 1,355 | 0 | 100.0% |
| exchange | 1,355 | 1,355 | 0 | 100.0% |
| openDate | 1,355 | 1,355 | 0 | 100.0% |
| closeDate | 1,355 | 1,355 | 0 | 100.0% |
| priceBand | 1,336 | 1,355 | 19 | 98.6% |
| lotSize | 436 | 1,355 | 919 | 32.2% |
| issueSizeCr | 392 | 1,355 | 963 | 28.9% |
| issueComposition | 389 | 443 | 54 | 87.8% |

## Recent exchange fields — last 2 years

| Field | Present | Expected | Missing | Coverage |
| --- | ---: | ---: | ---: | ---: |
| symbol | 439 | 443 | 4 | 99.1% |
| board | 443 | 443 | 0 | 100.0% |
| exchange | 443 | 443 | 0 | 100.0% |
| openDate | 443 | 443 | 0 | 100.0% |
| closeDate | 443 | 443 | 0 | 100.0% |
| priceBand | 437 | 443 | 6 | 98.6% |
| lotSize | 430 | 443 | 13 | 97.1% |
| issueSizeCr | 386 | 443 | 57 | 87.1% |
| issueComposition | 389 | 443 | 54 | 87.8% |

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
| registrar | 356 | 387 | 31 | 92.0% |
| leadManagers | 350 | 387 | 37 | 90.4% |
| promoters | 343 | 387 | 44 | 88.6% |
| objectsOfIssue | 65 | 387 | 322 | 16.8% |
| financials | 246 | 387 | 141 | 63.6% |
| promoterShareholding | 221 | 387 | 166 | 57.1% |

## Open IPO subscription fields

| Field | Present | Expected | Missing | Coverage |
| --- | ---: | ---: | ---: | ---: |
| qib | 8 | 9 | 1 | 88.9% |
| nii | 8 | 9 | 1 | 88.9% |
| retail | 8 | 9 | 1 | 88.9% |
| total | 9 | 9 | 0 | 100.0% |

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
