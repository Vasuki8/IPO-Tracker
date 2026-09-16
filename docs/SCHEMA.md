# Normalized IPO schema — v5

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


## Version 5 additions

The record-level `validation` object above describes exchange comparison only. It is separate from the dataset's semantic validation report.

| Field or file | Meaning |
| --- | --- |
| `meta.schemaVersion` | 5 after a reviewed migration or publication |
| `dataCorrections[]` | Before/after field values, reason, parser version and source URL/hash when available |
| `documentFieldProvenance` | Source URL/hash, document date/type, parser version and field evidence |
| `documentFieldProvenance.evidence.financials` | `FYyyyy.metric` → source page, row, header, original unit and normalized value |
| `lotSizeEvidence`, `listingDateEvidence` | Issue-specific source URL/hash, issuer and issue dates, source field and accepted value |
| `nseOfferFilings` | Last register fingerprint, collection outcome, changed fields, document count and retry timestamp |
| `documentRepair` | Attempt time, status and `financialStatus` (`validated` or `needs_review`) |
| `subscriptionCollectedAt` | Collector timestamp; compatibility `subscriptionAsOf` has this same meaning |
| `subscriptionObservedAt` | Actual source observation time, or null when unavailable |
| `subscriptionTimeBasis` | `source-observation` or `collection-only` |
| `performance.latest` | Price, observation time, collection time and official source URL |
| `performance.observations[]` | Deduplicated dated price observations |
| `performance.returnSinceIssuePct` | Unadjusted price return from a confirmed final issue price, otherwise null |
| `performance.benchmarkExcessReturnPct` | Return from listing versus a matching dated benchmark, otherwise null |
| `meta.pipelineStages` | Stage status, exit code, duration, check time and bounded diagnostics |
| `meta.publication` | Collector commit, publication run and pending-conflict count |
| `data/validation.json` | Semantic errors and unresolved source-review items |
| `data/missing_queue.json` | Complete priority queue, including every P5 row and explicit availability exclusions |
| `data/phase_status.json` | Evidence gate for P4 completion and P5 activation |
| `data/pending_updates.json` | Unaccepted concurrent proposals retained for source review |

Financial currency values use ₹ crore; RONW/ROE use percentages and EPS uses rupees per share. Fiscal labels must come from table columns. Original source units remain in field evidence. Timestamps retain an explicit UTC offset; operational timestamps may use UTC or Asia/Kolkata.

Financial rows distinguish `revenueCr` from `totalIncomeCr`, and basic `eps` from `dilutedEps`. Financial evidence records zero-based `sourceColumns` and the reporting `scope` where disclosed.

Final-listing XBRL supplies `lotSize` and `marketLot` from the disclosed `MarketLot`. It does not infer `minimumBidQuantity`. Earlier records may separately retain a disclosed minimum application quantity; the fill-only collector preserves those values for source review. Lot evidence, when present, must match the accepted value and issue date.

`meta.pipelineStages` may report `deferred` with a null exit code when the overall collection budget leaves insufficient time to start a stage.
