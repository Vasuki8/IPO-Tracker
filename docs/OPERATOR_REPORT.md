# Operator freshness and source-health report

The first operator report is intentionally **read-only**. It does not mutate IPO values or invent timestamps.

## Run locally

```bash
node scripts/operator-report.mjs
node scripts/operator-report.mjs --json
```

The hourly GitHub Actions sync also appends the report to the workflow **Job Summary** after the pipeline, including when an earlier collection/build step fails.

## Timestamp semantics

- **first observed** — when an IPO first entered retained recovery data;
- **record collected** — latest retained `last_collected_at` for a record;
- **evidence collected** — latest `collected_at` on retained field/document evidence;
- **dataset generated** — `data/ipos.json.generated_at`, when the published JSON snapshot was rebuilt;
- **report generated** — when the operator report itself ran.

These are not interchangeable.

## Pipeline health semantics

The sync workflow passes real step outcomes into the report for:

- NSE collection;
- SEBI collection;
- dataset rebuild;
- data validation;
- repository publication step.

If NSE or SEBI fails/cancels, the report says `collection_failure`.

If collection succeeds but a field is null, the report does **not** call that a collection failure. A null can be a legitimate source gap. Field-specific source-null conclusions remain in `docs/PROJECT_STATUS.md`.

## Known limitation

GitHub Pages publication time/status is produced by a separate workflow and is **not persisted in the dataset or sync workflow**. The operator report therefore says that Pages publication is not recorded instead of fabricating a timestamp.

A later operations batch can persist or query Pages deployment health if the project needs a single durable operator surface.


## Staleness and actionable health

The report classifies operational health without changing IPO data.

Default thresholds:

- dataset generation: stale after **3 hours**;
- latest retained record collection: stale after **3 hours**;
- latest retained evidence collection: stale after **24 hours**;
- last successful GitHub Pages publication: stale after **3 hours**.

The longer evidence threshold is deliberate: an hourly collector can succeed without discovering new document/field evidence.

Overall states:

- `healthy` — measured operational signals are within their thresholds and collection is successful;
- `stale` — one or more measured freshness signals exceeded its explicit threshold;
- `failure` — current collection failed/cancelled or the latest Pages deployment failed/cancelled;
- `unknown` — required timestamps are unavailable or collection health was not measured.

Failure takes precedence over stale, and stale takes precedence over unknown.

These classifications are operator signals only. They do **not** mark individual IPO fields as stale, missing, source-null, verified, or conflicting, and they never mutate `data/ipos.json`.


## Recovery guidance

Every unhealthy/unknown health reason now maps to a read-only operator recommendation with:

- priority;
- diagnostic step;
- recovery step.

Guidance is intentionally conservative. Examples:

- collection failure → inspect the failed NSE/SEBI workflow step before changing a parser;
- Pages deployment failure → inspect the deployment workflow, then rerun only after the cause is understood;
- stale dataset → distinguish collection health from rebuild/validation/publication health;
- stale evidence → first determine whether newer official evidence actually exists; do **not** rerun solely because evidence is old;
- missing timestamps → repair retention of real operational timestamps; never synthesize historical times.

The operator report does not execute these actions. It does not rerun workflows, modify recovery manifests, change IPO values, or send notifications.


## Durable operator snapshot

The hourly sync persists its latest operational state to `ops/operator-snapshot.json` after producing the Job Summary.

The snapshot contains only operational metadata:

- sync workflow run ID / attempt / commit;
- overall health, reasons, thresholds and measured ages;
- recovery guidance;
- collection/build/validation/publication step outcomes;
- dataset/collection/evidence freshness timestamps;
- latest retained GitHub Pages publication state.

It deliberately excludes IPO records and field coverage. `data/ipos.json` remains the only published IPO dataset.

The snapshot is written in an `if: always()` workflow step so a failed collector can still leave durable diagnostic state. Its bot commit changes only `ops/operator-snapshot.json`, which is outside the sync workflow's push-path trigger, preventing a recursive sync loop.
