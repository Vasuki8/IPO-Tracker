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

**Latest completed unit: cursor5 reconciled, verified, published and checked live — PR #191 + PR #192.**

PR #191 merged as `3e415a4f88d4582d7d0d905d0ec72b89eb5ee20e`. It closed the parsed portion of the 20-notice historical cursor segment first attempted at `2026-09-24T15:09:03.207Z`:

- **17 parsed notices / 18 listing references**;
- multi-year reconciliation against current 2020–2026 recovery + public data: **18 exact-missing identities / 0 already present / 0 ambiguous or code/source collisions**;
- discovery batches: `batch15` (15) + `batch16` (3);
- three index notices remain unparseable and are isolated: `20241211-15`, `20241202-11`, `20240722-21`.

Initial verification found one bounded source-format issue: BSE appends `(Formerly Known as Neopolitan Pizza Limited)` to the **current** issuer name for Neopolitan Pizza and Foods Ltd. The verifier now strips only that trailing parenthetical for listing-identity comparison. A candidate using only the former name still rejects; notice number, BSE code, listing date, SME status, market lot and issue price remain strict.

Fresh source verification:

- run `36025166795`: **15/15 + 3/3 verified**, 0 rejected/unavailable;
- artifact `10819732464`, ZIP SHA-256 `c0a2c88937c66dce95869335642fb6254d234828d7f4c220cd8e0a9379916b89`;
- reviewed manifests: `data/verified-bse-listings/2026-09-24-batch20.json` and `batch21.json`;
- final PR-head source re-verification `36026096850`: again **18/18**, artifact `10819618949`, SHA-256 `b05dbbd501a557dc4c2c13581e88bbbf2123a2d242323a23048a3c99cdead901`.

The source-verification workflow timeout was raised from 10 to 20 minutes only because its retained historical regression suite now exceeds ten minutes. Candidate bounds, source rules, permissions and publication behavior did not change.

Real importer rehearsal proved **1,050 → 1,068**, exactly **18 additions**, all 1,050 existing records unchanged, **0 holds/conflicts**, and an idempotent rerun.

Production sync `36026575507` succeeded:

- reviewed BSE import: **18 added / 126 already present / 0 holds / 0 identity conflicts**;
- semantic publication: **18 added / 19 changed / 0 removed / 0 conflicts**;
- source-backed data commit: `eb023d3e60c1d66ed3a1e38f4f78d66cc6de6839`;
- operator-state commit: `138115a9a0544dcff175c967c1419d8ee26c38ed`;
- schema 1.2.0: **1,068 records passed**;
- operator health: **healthy**;
- retained recovery: **2024 = 269**, **2025 = 293**.

The 19 changed records are normal concurrent official-source enrichment and are separate from the 18 additions.

Pages build `36027207308` succeeded on the final operator revision. The first live-verifier attempt ran before Pages caught up and correctly failed against the old **1,050-record** snapshot; it was not treated as success. After deployment completed, attempt 2 of run `36027489827` verified the actual site:

- snapshot fetched `2026-09-24T16:30:56.256Z`;
- checked `2026-09-24T16:30:56.295Z`;
- dataset generated `2026-09-24T16:21:47.053Z`;
- **1,068 served records**;
- **18/18 unique reviewed issuers**;
- **54/54 listing-date / market-lot / issue-price checks**;
- **0 failed issuers**;
- all six unsupported fields remain null for all 18;
- retained recovery verifies **54 original document-hash field sources**; the public projection still serializes **0** document hashes and is not described as live hash verification;
- live snapshot SHA-256: `3c26f8dbea5e18dbfb498b2a609d3f9be6e431b359734b881a77539b9d603dab`;
- successful artifact: `10821006183`, ZIP SHA-256 `b8dcb40ed94b09daf16501b2b2fd8f97769174d10ed20d963129786e4f1f5cfa`.

Durable receipt: [docs/verification/cursor5-live-publication-2026-09-24.json](docs/verification/cursor5-live-publication-2026-09-24.json).

### Current historical cursor

Re-read immediately before this handoff:

- parser **1.2.0**;
- **120 tracked / 236 eligible**;
- **117 parsed / 3 unparseable**;
- **116 not yet tracked**;
- cursor has **not advanced** since `2026-09-24T15:09:03.207Z`.

**Next:** re-read `main` and the cursor first. If no newer cursor segment has advanced, the earliest unfinished work is a **bounded parser/source-family repair for the three retained unparseable notices**: `20241211-15`, `20241202-11`, and `20240722-21`. Diagnose only demonstrated official-source shapes; do not infer issuers from failed index notices. If the independent cursor has advanced and created an unprocessed segment, reconcile that segment before skipping ahead. Do not replay discovery batches15/16, reviewed batches20/21, or the completed Neopolitan repair.

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
