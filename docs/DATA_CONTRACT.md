# IPO published-data contract

This is the boundary between source recovery and the public UI.

## Purpose

The public site reads `data/ipos.json`. That file must contain only source-supported IPO records. The UI must not fall back to demo market values when production data is unavailable.

The machine-readable contract is `data/ipo-schema.json`.

## Field rules

Every important market field is represented as an evidence-bearing object:

```json
{
  "value": null,
  "status": "missing",
  "evidence": [],
  "corrections": []
}
```

Allowed status values are:

- `verified` — supported by retained official evidence.
- `provisional` — official but not yet final or superseding evidence may still arrive.
- `conflict` — retained official sources disagree and the conflict is unresolved.
- `missing` — no verified value is currently published.

A missing value remains `null`. It must never become zero, an estimate, or an aggregator-derived substitute merely to make the UI look complete.

## Required evidence metadata

Evidence supports the value rather than merely naming a source. Retain, when available:

- official URL;
- document type;
- document identity;
- publication date;
- page / evidence location;
- collection timestamp.

## Time semantics

Keep these concepts distinct:

- `publication_date`: when the source document was published;
- `first_observed_at`: when this IPO was first observed by the tracker;
- `last_collected_at`: when the tracker most recently collected or checked the record;
- `generated_at`: when the published dataset was generated.

## Application terms

These remain separate fields:

- `market_lot`;
- `minimum_bid_quantity`;
- `minimum_application_amount_inr`.

Do not derive one from another unless a future documented transformation explicitly retains the derivation and its inputs.

## Corrections and conflicts

Do not overwrite history silently. If a later authoritative source changes a value, append a correction entry with the old value, new value, timestamp, and reason.

If official sources conflict and precedence does not resolve the disagreement, preserve both pieces of evidence and publish the field with `status: "conflict"`.

## Current state

The initial `data/ipos.json` intentionally contains zero records because the authoritative historical recovery pipeline is not present in this repository. This is safer than publishing prototype values as real IPO data.
