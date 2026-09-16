# IPO Tracker Data Quality

Generated: **2026-09-16T22:34:02+05:30**

Records audited: **1,361**

## Completeness scores

| Area | Score | Records in denominator |
| --- | ---: | ---: |
| Actionable exchange terms | 83.5% | 1,352 |
| Recent exchange terms (2Y) | 99.0% | 443 |
| Offer-document intelligence | 81.3% | 179 |
| Live subscription categories | 100.0% | 8 |
| Matured lifecycle dates | 97.3% | 1,321 |
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
| lotSize | 426 | 1,352 | 926 | 31.5% |
| issueSizeCr | 439 | 1,352 | 913 | 32.5% |
| issueComposition | 436 | 443 | 7 | 98.4% |

## Recent exchange fields — last 2 years

| Field | Present | Expected | Missing | Coverage |
| --- | ---: | ---: | ---: | ---: |
| symbol | 441 | 443 | 2 | 99.5% |
| board | 443 | 443 | 0 | 100.0% |
| exchange | 443 | 443 | 0 | 100.0% |
| openDate | 443 | 443 | 0 | 100.0% |
| closeDate | 443 | 443 | 0 | 100.0% |
| priceBand | 441 | 443 | 2 | 99.5% |
| lotSize | 423 | 443 | 20 | 95.5% |
| issueSizeCr | 436 | 443 | 7 | 98.4% |
| issueComposition | 436 | 443 | 7 | 98.4% |

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
| registrar | 177 | 179 | 2 | 98.9% |
| leadManagers | 175 | 179 | 4 | 97.8% |
| promoters | 159 | 179 | 20 | 88.8% |
| objectsOfIssue | 159 | 179 | 20 | 88.8% |
| financials | 119 | 179 | 60 | 66.5% |
| promoterShareholding | 84 | 179 | 95 | 46.9% |

## Open IPO subscription fields

| Field | Present | Expected | Missing | Coverage |
| --- | ---: | ---: | ---: | ---: |
| qib | 8 | 8 | 0 | 100.0% |
| nii | 8 | 8 | 0 | 100.0% |
| retail | 8 | 8 | 0 | 100.0% |
| total | 8 | 8 | 0 | 100.0% |

## Matured lifecycle fields

| Field | Present | Expected | Missing | Coverage |
| --- | ---: | ---: | ---: | ---: |
| listingDate | 1,285 | 1,321 | 36 | 97.3% |

## Optional lifecycle observations

| Field | Present | Expected | Missing | Coverage |
| --- | ---: | ---: | ---: | ---: |
| allotmentDate | 0 | 1,321 | 1,321 | 0.0% |

## Interpretation

- **Not yet disclosed** is not treated as a data-quality failure for pre-exchange filings.
- **Collector gap** means an official field is expected and recoverable for that lifecycle/source class but remains missing.
- Fresh/OFS composition is not counted as an archival collector gap unless a qualifying offer document exists.
- Allotment dates remain visible as optional research coverage rather than inflating the actionable queue without a reliable official historical source.
- Recent exchange coverage is the best measure of whether the live collectors are working well today.
- Historical lot size and issue size are progressively repaired from the official BSE historical archive when available.
