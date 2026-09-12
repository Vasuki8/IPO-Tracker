# Normalized IPO schema

Each item in `data/ipos.json` uses the same shape regardless of source.

```json
{
  "id": "stable-slug",
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
  "source": {
    "name": "NSE current",
    "url": "https://www.nseindia.com/market-data/all-upcoming-issues-ipo",
    "asOf": "2026-09-11T15:00:00+05:30"
  }
}
```

`null` is preferred to guessed or stale values.
