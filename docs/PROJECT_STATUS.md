# Project status and handoff

Updated: 2026-09-24. Live observation: 16:30:56 UTC / 12:30:56 America/Toronto.

## Current priority

Continue P1/P2/P3 data correctness, official-source coverage and dependable publication under `DEVELOPMENT_PROCESS.md`. The application-term requirement remains **Lot Size only**. Keep market lot, minimum bid quantity, application amount, listing date and index-admission date distinct. UI redesign and downstream research/commercial infrastructure are out of scope.

## Completed: cursor5 reconciliation, publication and live verification — PR #191 / #192

PR #191 merged as `3e415a4f88d4582d7d0d905d0ec72b89eb5ee20e`.

### Reconciliation

The 20-notice cursor segment first attempted at `2026-09-24T15:09:03.207Z` contained:

- **17 parsed notices**;
- **18 listing references**;
- **3 unparseable notices**.

A multi-year reconciliation searched current 2020–2026 retained recovery plus the then-current 1,050-record public dataset, using normalized issuer identity, BSE scrip code and listing-source identity. Result:

- **18 exact-missing identities**;
- **0 already-present matches**;
- **0 ambiguous/name-code/source collisions**.

Retained discovery:

- `data/discovery/bse-listing-reconciliation-2026-09-24-cursor5.json`;
- `data/discovery/bse-listing-candidates-2026-09-24-batch15.json` — 15 candidates;
- `data/discovery/bse-listing-candidates-2026-09-24-batch16.json` — 3 candidates.

The three failed index notices remain outside the candidate batches:

- `20241211-15`;
- `20241202-11`;
- `20240722-21`.

No issuer was inferred from them.

### Bounded source-identity repair

Initial source verification verified 17/18. Neopolitan Pizza and Foods Ltd was the only rejection because its official BSE listing notice uses the current legal issuer followed by:

`(Formerly Known as Neopolitan Pizza Limited)`

The verifier now removes only a **trailing parenthetical former-name clause** when comparing the observed listing issuer with the candidate current name. The historical/former name cannot substitute for the current issuer; an exact regression proves that candidate still rejects. Notice number, six-digit BSE code, listing date, SME segment, equity-listing statement, market lot and final issue price remain strict.

The retained historical regression suite had grown beyond the old 10-minute Actions limit, so the source-verification job timeout was changed to **20 minutes**. This was operational only: no batch size, permission, schedule, source rule or publication behavior changed.

### Source verification and reviewed evidence

Fresh source verification run `36025166795`:

- batch15: **15/15 verified**;
- batch16: **3/3 verified**;
- rejected: **0**;
- unavailable: **0**;
- artifact: `10819732464`;
- artifact ZIP SHA-256: `c0a2c88937c66dce95869335642fb6254d234828d7f4c220cd8e0a9379916b89`.

Canonical listing-PDF archive paths were unavailable. Reviewed evidence therefore retains the established strict official-listing-notice HTML contract.

Reviewed manifests:

- `data/verified-bse-listings/2026-09-24-batch20.json` — 15;
- `data/verified-bse-listings/2026-09-24-batch21.json` — 3.

Final PR-head source verification `36026096850` again reached **15/15 + 3/3**, 0 rejected/unavailable. Artifact `10819618949`, ZIP SHA-256 `b05dbbd501a557dc4c2c13581e88bbbf2123a2d242323a23048a3c99cdead901`.

Final PR checks passed:

- full data contract: `36026096822`;
- reviewed evidence/importer: `36026096937`;
- protected BSE identity regression: `36026097009`;
- source verification: `36026096850`.

### Publication rehearsal and production

The real offline importer/publication rehearsal measured:

- **1,050 → 1,068 records**;
- exactly **18 additions**;
- **126 already-present** reviewed BSE entries;
- **0 held existing**;
- **0 identity conflicts**;
- all **1,050 existing records unchanged**;
- second import/rebuild: no-op / idempotent.

Production sync `36026575507` completed successfully:

- reviewed BSE import: **18 added / 126 already present / 0 holds / 0 identity conflicts**;
- semantic publication: **18 added / 19 changed / 0 removed / 0 conflicts**;
- source-backed commit: `eb023d3e60c1d66ed3a1e38f4f78d66cc6de6839`;
- operator-state commit: `138115a9a0544dcff175c967c1419d8ee26c38ed`;
- published/validated: **1,068 records**;
- operator health: **healthy**;
- post-publication retained counts include **2024 = 269** and **2025 = 293**.

The 19 changed records are normal concurrent official NSE/SEBI enrichment from the same source-first sync, distinct from the 18 additions.

### Deployed-data verification

Native Pages build `36027207308` succeeded on operator revision `138115a9a0544dcff175c967c1419d8ee26c38ed`.

PR #192 updates the existing read-only live verifier default from completed cursor4 manifests batch18/19 to batch20/21. The first run attempt `36027489827` correctly failed because it fetched the previous **1,050-record** Pages snapshot generated at `2026-09-24T15:41:54.375Z`; all 18 new identities were absent. This was a deployment-lag observation, not accepted as release success.

After Pages completed, only the failed verifier job was rerun. Attempt 2 succeeded:

- snapshot fetched: `2026-09-24T16:30:56.256Z`;
- checked: `2026-09-24T16:30:56.295Z`;
- dataset generated: `2026-09-24T16:21:47.053Z`;
- live total: **1,068 records**;
- unique reviewed issuers: **18 / 18**;
- matching listing-date / market-lot / issue-price fields: **54 / 54**;
- failed issuers: **0**;
- all six unsupported fields null for each reviewed issuer;
- retained original document-hash sources checked: **54**;
- document hashes serialized in public field evidence: **0**.

Live snapshot SHA-256:

`3c26f8dbea5e18dbfb498b2a609d3f9be6e431b359734b881a77539b9d603dab`

Successful artifact:

- run: `36027489827`, attempt 2;
- artifact: `10821006183`;
- ZIP SHA-256: `b8dcb40ed94b09daf16501b2b2fd8f97769174d10ed20d963129786e4f1f5cfa`;
- expiry: `2026-10-08T16:30:56Z`.

Durable summary:

`docs/verification/cursor5-live-publication-2026-09-24.json`

### Current cursor and next task

Re-read immediately before handoff:

- parser **1.2.0**;
- **120 tracked / 236 eligible**;
- **117 parsed / 3 unparseable**;
- **116 not yet tracked**;
- updated at `2026-09-24T15:09:03.207Z`.

The parsed portion of this segment is fully reconciled, reviewed, published and verified live.

If the cursor is unchanged on the next run, the earliest unfinished batch is the **three retained unparseable notices** (`20241211-15`, `20241202-11`, `20240722-21`). Treat them as a bounded parser/source-family repair, group only by demonstrated official-source shape, and do not infer issuers from index evidence. If automation has advanced the cursor and produced an unprocessed segment, re-read that state first and do not skip an earlier unprocessed segment. Do not repeat batches15/16, batches20/21, or the Neopolitan identity repair.

## Prior completed: cursor4 live verification and handoff recovery — PR #189

The release-verification work is complete for the 23 cursor4 issuers already merged in PR #187. This continuation adds no IPOs and does not alter their values or reset any cursor.

### Recovered repository state

- PR #187 merged at `e30423c2319c95a6bf3560d5bc40775930430577`: 23 reviewed issuers, discovery batches 13/14, evidence batches 18/19.
- PR #188 merged at `29d90752d45822a6a7e10f145ee4afb0d1135407`: fixes the child-process buffer used to read large recovery baselines. The original default-buffer failure was incorrectly treated as a missing baseline, dropping additions during semantic publication. Do not repeat this completed repair.
- The subsequent source-backed sync included the reviewed records. This run verifies the actual site rather than assuming that merge or a green Pages job proves publication.
- Both README and PROJECT_STATUS still described PR #184. Their entire prior contents are archived unchanged, replacing stale instructions with this handoff.

### Canonical implementation

- `scripts/verify-bse-publication.mjs`
- `scripts/test-verify-bse-publication.mjs`
- `scripts/test-bse-public-projection.mjs`
- `.github/workflows/verify-bse-publication.yml`
- `docs/verification/cursor4-live-publication-2026-09-24.json`

The verifier compares selected reviewed manifests with current retained recovery identities/provenance and a freshly fetched Pages dataset. It checks exact issuer uniqueness, board/status evidence, listing date, market lot, issue price, source URL/type/identity, publication/collection date, page and correction history. It preserves the downloaded bytes and their SHA-256, independently records fetch/check/generation clocks, and emits a failed receipt for HTTP, size, JSON or integrity failures. It never imports IPOs or modifies recovery/cursor state.

This is a manually runnable or implementation-change-triggered verifier, not a new scheduled collector. Existing sync, discovery, deployment schedules and permissions are unchanged. Each reviewed input manifest retains the existing 15-issuer validation bound.

### Diagnosed verification failure and repair

Initial PR #189 run `36017592030` failed all 23 issuers even though their identities and 69 values were present in its 1,050-record live snapshot. It incorrectly required `document_sha256` inside public evidence. The current publisher intentionally projects a smaller evidence object and does not serialize that property.

The repair keeps original hashes mandatory in retained recovery. Public comparisons check the metadata actually serialized; an explicitly present public hash must match and a present null/wrong hash is rejected. The receipt reports **retained hash checks separately from serialized live hashes**. This run did not change the publisher projection or claim raw-only hashes were present in public JSON.

A new integration test runs the real importer and publisher in an isolated copy and verifies that exact output. Eight additional mutation cases cover missing/wrong retained hashes, wrong/null explicitly published hashes, wrong document type, altered source text, lost correction history and invalid provisional nulls. Original mutation/identity/clock/network tests remain intact. The audit leaves public data and cursor bytes unchanged.

An alternative implementation was briefly opened as PR #190 before the existing PR #189 was identified. PR #190 is closed, unmerged, and retained only for traceability. Only the canonical PR #189 implementation should land.

### Validation and live evidence

Code head: `3f2e29e1aa3be1e101c0bbe65f1339eb19302c25`.

All three PR-head workflows completed successfully:

| Check | Run |
| --- | --- |
| Reviewed BSE evidence/importer CI | `36020477691` |
| Full IPO data contract CI | `36020477787` |
| Fresh served-data verification | `36020477749` |

The downloaded artifact was hash-checked and its source files byte-compared with the locally tested implementation. The full live snapshot was parsed and its SHA-256 checked against the receipt.

| Observation | Result |
| --- | --- |
| Snapshot fetched | `2026-09-24T15:28:55.837Z` |
| Verification checked | `2026-09-24T15:28:55.890Z` |
| Dataset generated | `2026-09-24T15:17:42.466Z` |
| Live total | **1,050 records** |
| Unique reviewed issuers | **23 / 23** |
| Matching listing-date/lot/price fields | **69 / 69** |
| Failed issuers | **0** |
| Unsupported fields | **6 null fields for each of the 23 issuers** |
| Original document hashes checked in recovery | **69 field sources** |
| Document hashes serialized in live field evidence | **0** |

Live response SHA-256: `696bec3c8072af424d39868b51377930b58724a81ddc5a2070ef36d4b8ba65d3`.

Artifact: **10817060050**, run **36020477749**, ZIP SHA-256 `f32b91690da499944a55e17c2dbff695f6f8a2d2594e7f55cc541c1ed5d99197`. Expiry: `2026-10-08T15:28:56Z`. It contains `publication-report.json`, exact `deployed-data.json` and `source-snapshot.zip`. The durable repository summary is `docs/verification/cursor4-live-publication-2026-09-24.json`.

Retained recovery counts in that verification revision: 2020 **51**, 2021 **100**, 2022 **94**, 2023 **174**, 2024 **252**, 2025 **292**, 2026 **87**. These sum to 1,050; they are observed counts, not a claim of complete universe coverage. The two records beyond the isolated 1,048-record cursor4 rehearsal are outside this 23-issuer release scope.

## Next task: reconcile the newly completed historical segment

Always re-read the cursor and latest recovery/public data first. The cursor observed at `2026-09-24T15:09:03.207Z` has:

- parser **1.2.0**;
- **120 tracked / 236 eligible**;
- **117 parsed / 3 unparseable**;
- **116 not yet tracked**.

The 20 new notices beyond the previously completed 100-notice cursor were first attempted at `2026-09-24T15:09:03.207Z`. They run from `20250103-24` through `20240627-14`, include **17 parsed notices / 18 listing references**, and have not been reconciled into new verifier batches.

Next acceptance criteria:

1. Reconcile all 18 references against the **multi-year** current recovery and public data, including normalized issuer identity, BSE code and listing-source identity. Some references concern 2024; do not restrict the search to 2025.
2. Separate already-present, genuinely missing and ambiguous identities. Discovery references are not automatically missing IPOs and are not listing-term authority.
3. Pin and independently verify only missing/unambiguous issuers, at most 15 per verification batch. Preserve source URLs/hashes/dates and null unsupported terms.
4. Keep failed notices **`20241211-15`, `20241202-11`, `20240722-21`** separate for a bounded demonstrated parser/source-family repair; do not infer their issuers.
5. Do not skip this unprocessed segment if the independent cursor advances again. Do not replay cursor4 batches 13/14 or reviewed batches 18/19.

The receipt records the exact 20 notice IDs for resumption. Broader historical coverage and source-field completeness remain incomplete.

## Historical evidence

The entire previous status is preserved as `docs/archive/PROJECT_STATUS-before-cursor4-live-verification.md` (original Git blob `3e7dae21d092270622b8af2dee784de6c4e5ca26`). The previous README is preserved as `docs/archive/README-before-cursor4-live-verification.md` (blob `9ab4237c5550794b55aeebf259b8557b0463f63a`). Older archives remain unchanged. Current repository/receipt evidence supersedes archived next-task instructions.
