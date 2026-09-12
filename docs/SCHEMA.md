# Normalized IPO schema — v2

`data/ipos.json` is a source-aware normalized database. Missing values remain `null`; values are never guessed simply to complete a row.

```json
{
  "id": "EXAMPLE-or-stable-slug",
  "matchKey": "EXAMPLE",
  "symbol": "EXAMPLE",
  "company": "Example Limited",
  "board": "Mainboard",
  "exchange": "NSE",
  "status": "open",
  "openDate": "2026-09-10",
  "closeDate": "2026-09-14",
  "allotmentDate": null,
  "listingDate": null,
  "priceBand": { "min": 100, "max": 110 },
  "lotSize": 125,
  "issueSizeCr": 500,
  "freshIssueCr": 300,
  "ofsCr": 200,
  "sharesOffered": 10000000,
  "sharesBid": 32000000,
  "subscription": { "qib": 3.1, "nii": 2.4, "retail": 1.9, "total": 2.6 },
  "listing": { "issuePrice": 110, "listPrice": 132, "gainPct": 20.0 },
  "lifecycle": {
    "stage": "exchange",
    "stageDate": "2026-09-10",
    "candidate": false
  },
  "documents": [
    {
      "type": "RHP",
      "title": "Example Limited - RHP",
      "url": "https://www.sebi.gov.in/...",
      "filedDate": "2026-09-05",
      "source": "SEBI"
    }
  ],
  "sources": [
    {
      "name": "NSE current",
      "kind": "exchange",
      "url": "https://www.nseindia.com/market-data/all-upcoming-issues-ipo",
      "asOf": "2026-09-11T15:00:00+05:30"
    },
    {
      "name": "SEBI public issues",
      "kind": "regulator",
      "url": "https://www.sebi.gov.in/filings/public-issues/...",
      "asOf": "2026-09-05"
    }
  ],
  "observations": {
    "NSE": { "openDate": "2026-09-10", "closeDate": "2026-09-14", "lotSize": 125 },
    "BSE": { "openDate": "2026-09-10", "closeDate": "2026-09-14", "lotSize": 125 },
    "SEBI": { "stage": "rhp", "filedDate": "2026-09-05", "documentCount": 2 }
  },
  "validation": {
    "status": "verified",
    "checkedAt": "2026-09-11T15:00:00+05:30",
    "independentSources": ["BSE", "NSE", "SEBI"],
    "checks": [
      { "field": "openDate", "nse": "2026-09-10", "bse": "2026-09-10", "match": true }
    ]
  }
}
```

## Lifecycle stages

- `drhp` — draft red herring prospectus / draft offer document at SEBI.
- `udrhp` — updated draft red herring prospectus.
- `rhp` — red herring prospectus filed with ROC and surfaced by SEBI.
- `prospectus` — final offer document/prospectus.
- `exchange` — issue is present in exchange data.

A SEBI-only record may have `lifecycle.candidate: true`. That means it is an official public-issue filing discovered before enough exchange information exists to fully classify or schedule the IPO.

## Validation states

- `verified` — at least two independent official sources support the record and no comparable field is currently in conflict.
- `single-source` — only one independent source currently supports comparable fields.
- `conflict` — NSE and BSE disagree on at least one comparable populated field.

Comparable fields currently include open date, close date, price band, lot size and issue size. A lower-priority source never overwrites a populated NSE value; both observations are preserved instead.

## Compatibility

`source` is retained as the primary/legacy source object for the frontend, while `sources` is the v2 multi-source trail.
