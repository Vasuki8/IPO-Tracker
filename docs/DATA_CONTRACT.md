# IPO published-data contract

This is the boundary between source recovery and the public UI.

## Purpose

The public site reads `data/ipos.json`. That file must contain only source-supported IPO records. The UI must not fall back to demo market values when production data is unavailable.

The machine-readable contract is `data/ipo-schema.json`. The current published schema version is `1.1.0`.

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

## Scalar metadata provenance

`board` and `status` remain scalar values for UI compatibility, but schema version 1.1.0 requires companion arrays:

- `board_evidence`
- `status_evidence`

If either scalar is non-null, its companion evidence array must contain retained official evidence. This prevents provenance from being lost while avoiding a breaking UI migration.

## Collection-time preservation

Regeneration must not rewrite the collection timestamp of older evidence. Recovery manifests retain source/document collection timestamps individually. `last_collected_at` may advance when a record is checked again while the timestamps on previously retained evidence remain unchanged.

## Application terms

These remain separate fields:

- `market_lot`;
- `minimum_bid_quantity`;
- `minimum_application_amount_inr`.

Do not derive one from another unless a future documented transformation explicitly retains the derivation and its inputs.

## Corrections and conflicts

Do not overwrite history silently. If a later authoritative source changes a value, append a correction entry with the old value, new value, timestamp, and reason.

If official sources conflict and precedence does not resolve the disagreement, preserve both pieces of evidence and publish the field with `status: "conflict"`.

## Recovery publication

Retained recovery input is organized by issue year:

```
data/recovery/
  2026/
    nse-issue-information.json
  2027/
    nse-issue-information.json
  ...
```

Publication is deterministic:

```
node scripts/build-published-data.mjs
```

The publisher reads every year manifest and builds the single public dataset at `data/ipos.json`.

CI runs the publisher with `--check` and fails if `data/ipos.json` does not exactly match the retained recovery inputs.

## Automated discovery

`scripts/sync-nse-live.mjs` is the first automated discovery layer. It reads official NSE public IPO feeds and adds or enriches only explicitly supported values.

It intentionally does not convert NSE's `issueSize` field into `issue_size_inr`, derive minimum bid quantity from market lot, compute minimum application amounts, or infer other unsupported values.

See `docs/AUTOMATION.md` for the source and scheduling rules.

## Source hosts

The recovery publisher currently accepts a restricted set of official source hosts. This is deliberate validation, not a claim that only those organizations can ever provide authoritative evidence. New official source families must be added explicitly and tested.
