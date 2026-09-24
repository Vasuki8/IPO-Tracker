# IPO Tracker

A source-first Indian IPO research website with automated official-source collection and GitHub Pages publication.

- Repository: `Vasuki8/IPO-Tracker`; default branch: `main`.
- Website: https://vasuki8.github.io/IPO-Tracker/
- Public dataset: `data/ipos.json`, generated from retained evidence under `data/recovery/`.
- Development contract: [docs/DEVELOPMENT_PROCESS.md](docs/DEVELOPMENT_PROCESS.md).
- Current handoff and verification: [docs/PROJECT_STATUS.md](docs/PROJECT_STATUS.md).

## Product and data rules

Coverage includes records across 2020–2026, but the historical universe and field coverage remain incomplete. Run `node scripts/audit-historical-coverage.mjs` for current per-year counts; do not reuse old milestone counts as current totals.

The active application-term requirement is **Lot Size only**. Display verified market lot first, then verified minimum bid quantity when market lot is missing. Keep the raw fields distinct. Minimum investment/application amount remains out of scope.

Never fill missing data with guesses or price × quantity arithmetic. Preserve source URLs, document identity, reporting dates, collection timestamps, nulls, conflicts and correction history. A final Prospectus is not required for inclusion; use the best available official evidence for each field. Do not edit `data/ipos.json` instead of repairing retained recovery evidence.

## Automation

| Workflow | Purpose |
| --- | --- |
| `update-ipos.yml` | Hourly NSE live collection, historical detail recovery, SEBI discovery and source-backed publication |
| `backfill-historical-offer-dates.yml` | Independent historical PDF offer-date recovery |
| `backfill-historical-pdf-fields.yml` | Independent historical PDF field recovery |
| `audit-bse-sme-universe.yml` | Independent, read-only BSE SME constituent and addition-notice audits |
| `validate-data.yml` | Pull-request/push tests and data-contract checks |
| `deploy-pages.yml` | Website deployment and publication-health recording |

See [docs/AUTOMATION.md](docs/AUTOMATION.md) for background; the workflow files are authoritative for actual execution. Collection time, dataset generation and Pages publication are separate signals. `node scripts/operator-report.mjs` reports operational health without rewriting IPO values.

## Handoff for the next prompt

**Verified batch: BSE SME notice parser and validation repair — 2026-09-24 UTC (September 23 in Toronto).**

PR #165 merged at `7eedd8f9668cd7fce51d373427d7a2d7eafd7a8c`. Full PR/main validation, production BSE audit and Pages deployment passed. Production audit `35939161246` fetched **20 official notice PDFs and parsed 29 issuer/listing references**, with zero fetch or parse failures. The report is retained as Actions artifact `10783988662`, with a conversation copy; integrity and expiry details are in [PROJECT_STATUS.md](docs/PROJECT_STATUS.md).

The constituent JSON source is already connected. Addition notices can link directly to official PDFs; their HTML detail response may be empty. Do not repeat the completed Angular-shell or empty-HTML diagnosis.

The repaired regression was a mismatch between the parser's initial clause delimiter and its later entry parser: `Notice No:` was accepted by one but rejected by the other. The existing plural-notice test failed in production, while general CI had omitted that test. The repair fixes both, strengthens date/identity guards, and retains a machine-readable notice audit report even on source failure.

**No IPO was added by this read-only batch.** The 29 references are discovery candidates, not independently verified IPO records. Two references share scrip code `544770` but name different issuers: MERRITRONIX LIMITED and YAASHVI JEWELLERS LIMITED. Keep both on hold until their original PDFs and issuer-specific BSE listing notices resolve the identity discrepancy.

**Next:** verify up to 15 candidate issuers using official BSE listing notices, retaining source evidence before any materialization. Keep index admission dates separate from listing dates. The latest-20-notices audit is not a complete historical backfill; older-notice progress still needs a durable cursor.

No UI redesign, research-depth expansion, minimum-investment work, billing, accounts, ads, paid services or access changes are part of this batch.

## Local checks

Serve the repository with any static HTTP server for preview. For backend work:

```bash
node scripts/test-audit-bse-sme-addition-notices.mjs
node scripts/build-published-data.mjs --check
node scripts/validate-data.mjs
node scripts/audit-historical-coverage.mjs
```

The live BSE notice audit requires `pdftotext` and network access:

```bash
node scripts/audit-bse-sme-addition-notices.mjs --batch=20 --output=/tmp/bse-notices.json
```

The audit is read-only. Supported notice batch sizes are integers from 1 to 20. Failed or partial collection returns a nonzero exit code and retains available results when `--output` is supplied.

## Earlier handoffs

The previous accumulated README is preserved unchanged in [docs/archive/README-before-bse-notice-repair.md](docs/archive/README-before-bse-notice-repair.md). It records earlier milestones, not current coverage or next-task instructions.
