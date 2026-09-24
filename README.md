# IPO Tracker

A source-first Indian IPO research website with automated official-source collection and GitHub Pages publication.

- Repository: `Vasuki8/IPO-Tracker`; default branch: `main`.
- Website: https://vasuki8.github.io/IPO-Tracker/
- Public dataset: `data/ipos.json`, generated from retained evidence under `data/recovery/`.
- Development contract: [docs/DEVELOPMENT_PROCESS.md](docs/DEVELOPMENT_PROCESS.md).
- Current handoff: [docs/PROJECT_STATUS.md](docs/PROJECT_STATUS.md).

## Product and data rules

Coverage spans 2020-2026 but is incomplete. Run `node scripts/audit-historical-coverage.mjs` for current counts; old milestones are not current totals.

The active application-term requirement is **Lot Size only**. Display verified market lot first, then verified minimum bid quantity when market lot is missing. Keep the raw fields distinct. Minimum investment/application amount remains out of scope.

Never invent missing values or use price-times-quantity arithmetic to fill them. Preserve official sources, document identity, dates, hashes when retained, nulls, conflicts and correction history. A final Prospectus is not required for inclusion. Repair retained recovery evidence rather than hand-editing `data/ipos.json`.

## Automation

The existing hourly `update-ipos.yml` collects NSE/SEBI data and imports reviewed BSE evidence. Historical PDF recovery and the bounded BSE notice cursor run independently. `deploy-pages.yml` publishes the site. Workflow files define actual schedules and execution.

`verify-bse-publication.yml` is a **read-only post-publication check** for selected reviewed BSE manifests. It fetches the actual Pages dataset, retains its original bytes/hash and separate observation time, and checks issuer identity, values, source metadata and retained provenance. It runs manually or when its implementation changes; it does not alter the collection schedule or import IPOs.

Collection time, dataset generation and Pages publication are distinct signals. `node scripts/operator-report.mjs` reports operational health without rewriting IPO values.

## Handoff for the next prompt

**Latest completed unit: cursor6 reviewed evidence published and verified live — PR #204 / #205.**

PR #204 merged as `30127408c952dd98da6524ff13ee2d6d5537503f`. It froze the 19 already source-verified cursor6 issuers into:

- `data/verified-bse-listings/2026-09-24-batch24.json` — 15 issuers;
- `data/verified-bse-listings/2026-09-24-batch25.json` — 4 issuers.

The source verification remains run `36041395122` / artifact `10826304295`, ZIP SHA-256 `1a54f73efd2784202fb64f1ddadb5cbd825b448aea4056a3d2d2ff2ebe35f441`. Canonical listing-PDF archive probes were unavailable, so the reviewed manifests retain the strict issuer-specific official BSE HTML evidence already verified in PR #201. Unsupported fields remain null.

The real importer rehearsal proved **1,072 -> 1,091**, exactly **19 additions**, all 1,072 existing records unchanged, **148 already-present reviewed entries**, **0 holds/conflicts**, and an idempotent rerun.

Production sync `36044490807` succeeded:

- reviewed BSE import: **19 added / 148 already present / 0 held / 0 identity conflicts**;
- semantic publication: **19 added / 7 changed / 0 removed / 0 conflicts**;
- source-backed data commit: `3e6b106e0daa50bb381159e9f5578b205ee54611`;
- operator-state commit: `d189a486120e2ee31c83a834770af22adf298f84`;
- published/validated: **1,091 records**;
- 2024 recovery: **292 records**;
- operator health: **healthy**.

The 7 changed records are normal concurrent official-source enrichment and are separate from the 19 cursor6 additions.

PR #205 merged as `e920fb28cd4647c2ecbd17529b23a13607851910` and points the existing read-only publication verifier at batch24 + batch25. The canonical post-merge live verification run `36045625232` succeeded against the actually served Pages JSON:

- **1,091 live records**;
- **19 / 19** reviewed issuers occur exactly once;
- **57 / 57** listing-date, market-lot and issue-price fields match reviewed evidence;
- **0 failed issuers**;
- all six unsupported fields remain null for every reviewed issuer;
- retained recovery document hashes checked: **57 field sources**;
- document hashes serialized in public field evidence: **0** (the public projection intentionally omits them).

Post-merge snapshot:

- fetched: `2026-09-24T19:04:35.469Z`;
- checked: `2026-09-24T19:04:35.534Z`;
- dataset generated: `2026-09-24T18:54:41.274Z`;
- snapshot SHA-256: `b707398c57676e6758f113ef31d6c1a717cc012a27f266b7a6f6f9b439f7fa5f`;
- artifact: `10828372193`;
- artifact ZIP SHA-256: `f6bceadb52852e54ad1ee21bb7b2131a9c7461f53e677dc48fa4e4065dfe5f1b`.

Durable summary: `docs/verification/cursor6-live-publication-2026-09-24.json`.

Post-merge reviewed-evidence, full data-contract, read-only live-verification and deploy workflows all passed. Native Pages build `36045671486` succeeded on final Pages-health revision `187493575f425ecf694f307b9567ddd05cecd16b`.

### Current historical cursor

Re-read the cursor before new work. At this handoff it remains:

- parser **1.3.0**;
- **140 tracked / 236 eligible**;
- **135 parsed**;
- **5 unparseable**;
- **96 not yet tracked**.

Cursor6 batches18/19 and reviewed batches24/25 are now fully closed. Do not replay them.

### Next task

Handle the five retained cursor6 parser failures as a **separate bounded parser/source-family repair**:

- `20240624-11`
- `20240612-20`
- `20240606-11`
- `20240205-12`
- `20240103-22`

Re-fetch only the failed official BSE Index Services responses, confirm fresh hashes against retained cursor hashes, group failures only by demonstrated source shape, and make the smallest additive parser repair with regression fixtures. Do **not** infer issuers from failed index notices. If the independent cursor has advanced with a newer unprocessed segment before work starts, re-read the handoff/cursor and preserve sequencing rather than replaying completed cursor6 publication.

No UI redesign, minimum-investment work, billing, accounts, ads, spending or permission changes are part of this handoff.
## Local checks

```bash
node scripts/test-verify-bse-publication.mjs
node scripts/test-bse-public-projection.mjs
node scripts/test-bse-publication-rehearsal.mjs
node scripts/apply-verified-bse-listings.mjs --check
node scripts/build-published-data.mjs --check
node scripts/validate-data.mjs
node scripts/audit-historical-coverage.mjs
```

For a live receipt, run `scripts/verify-bse-publication.mjs` with `--manifests=<comma-separated reviewed paths>` and `--output-dir=<artifact directory>`. It reports failure on unavailable/malformed snapshots or mismatches and never imports IPO records.

## Historical handoffs

The complete previous README and status are preserved unchanged in [docs/archive/README-before-cursor4-live-verification.md](docs/archive/README-before-cursor4-live-verification.md) and [docs/archive/PROJECT_STATUS-before-cursor4-live-verification.md](docs/archive/PROJECT_STATUS-before-cursor4-live-verification.md). Older archives remain unchanged. Archived next-task instructions are not current instructions.
