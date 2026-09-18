# IPO Tracker Data Quality

Generated: **2026-09-18T21:29:48+05:30**

Records audited: **1,370**

## Completeness scores

| Area | Score | Records in denominator |
| --- | ---: | ---: |
| Actionable exchange terms | 82.6% | 1,357 |
| Recent exchange terms (2Y) | 96.4% | 444 |
| Offer-document intelligence | 69.7% | 389 |
| Live subscription categories | 90.6% | 8 |
| Matured lifecycle dates | 97.2% | 1,323 |
| Source/provenance trail | 100.0% | 1,370 |

## Actionable exchange fields

| Field | Present | Expected | Missing | Coverage |
| --- | ---: | ---: | ---: | ---: |
| symbol | 1,352 | 1,357 | 5 | 99.6% |
| board | 1,357 | 1,357 | 0 | 100.0% |
| exchange | 1,357 | 1,357 | 0 | 100.0% |
| openDate | 1,357 | 1,357 | 0 | 100.0% |
| closeDate | 1,357 | 1,357 | 0 | 100.0% |
| priceBand | 1,336 | 1,357 | 21 | 98.5% |
| lotSize | 436 | 1,357 | 921 | 32.1% |
| issueSizeCr | 392 | 1,357 | 965 | 28.9% |
| issueComposition | 389 | 445 | 56 | 87.4% |

## Recent exchange fields — last 2 years

| Field | Present | Expected | Missing | Coverage |
| --- | ---: | ---: | ---: | ---: |
| symbol | 439 | 444 | 5 | 98.9% |
| board | 444 | 444 | 0 | 100.0% |
| exchange | 444 | 444 | 0 | 100.0% |
| openDate | 444 | 444 | 0 | 100.0% |
| closeDate | 444 | 444 | 0 | 100.0% |
| priceBand | 436 | 444 | 8 | 98.2% |
| lotSize | 429 | 444 | 15 | 96.6% |
| issueSizeCr | 385 | 444 | 59 | 86.7% |
| issueComposition | 388 | 444 | 56 | 87.4% |

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
| registrar | 361 | 389 | 28 | 92.8% |
| leadManagers | 357 | 389 | 32 | 91.8% |
| promoters | 343 | 389 | 46 | 88.2% |
| objectsOfIssue | 93 | 389 | 296 | 23.9% |
| financials | 247 | 389 | 142 | 63.5% |
| promoterShareholding | 225 | 389 | 164 | 57.8% |

## Open IPO subscription fields

| Field | Present | Expected | Missing | Coverage |
| --- | ---: | ---: | ---: | ---: |
| qib | 7 | 8 | 1 | 87.5% |
| nii | 7 | 8 | 1 | 87.5% |
| retail | 7 | 8 | 1 | 87.5% |
| total | 8 | 8 | 0 | 100.0% |

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
