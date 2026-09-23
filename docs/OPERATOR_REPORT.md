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
