# Project status and handoff

Updated: 2026-09-24. Live observation: 15:28:55 UTC / 11:28:55 America/Toronto.

## Current priority

Continue P1/P2/P3 data correctness, official-source coverage and dependable publication under `DEVELOPMENT_PROCESS.md`. The application-term requirement remains **Lot Size only**. Keep market lot, minimum bid quantity, application amount, listing date and index-admission date distinct. UI redesign and downstream research/commercial infrastructure are out of scope.

## Completed: cursor5 parsed-reference reconciliation closure

The next historical segment after cursor4 was first attempted at `2026-09-24T15:09:03.207Z`.

Cursor segment:

- selected notices: **20**
- parsed notices: **17**
- unparseable notices: **3**
- parsed listing references: **18**
- cursor after segment: **120 / 236 tracked**
- parser: **1.2.0**
- statuses: **117 parsed / 3 unparseable**

### Historical vs current reconciliation

An earlier machine-readable reconciliation already existed:

`data/discovery/bse-listing-reconciliation-2026-09-24-cursor5.json`

At its observation time, the 18 parsed references were correctly classified as missing against the then-current 1,050-record public / retained-recovery snapshot.

Do not rewrite that evidence. Later scheduled official-source collection changed the production state.

This continuation re-ran reconciliation against the latest multi-year recovery universe and public dataset and retained the result separately as:

`data/discovery/bse-listing-reconciliation-2026-09-24-cursor5-final.json`

Current snapshots:

| Scope | Records |
| --- | ---: |
| Public dataset | **1,068** |
| 2020 recovery | 51 |
| 2021 recovery | 100 |
| 2022 recovery | 94 |
| 2023 recovery | 174 |
| 2024 recovery | **269** |
| 2025 recovery | **293** |
| 2026 recovery | 87 |

Public dataset generation time: `2026-09-24T16:21:47.053Z`.

The final reconciliation checks every recovery year plus the public dataset. Identity acceptance requires:

- exact normalized issuer identity;
- no conflicting six-digit BSE scrip code;
- exact issuer-specific BSE listing-source URL;
- exactly one recovery identity and one public identity;
- no fuzzy equivalence.

Result:

- **18 / 18 already-present exact identities**
- **0 missing exact identities**
- **0 identity-review cases**
- **0 code conflicts**
- **18 / 18 public listing-date / market-lot / issue-price triples match retained recovery**
- all three displayed fields remain **verified**
- each listing-date public source URL matches the recovered issuer-specific BSE listing notice

No new candidate verification batch was created and no IPO was re-imported. This is intentional: historical index discovery must not duplicate records that later source-first automation has already populated.

### Three held parser failures

The same 20-notice segment contains three notices that remain unparseable and were not used to infer any issuer:

| Notice | Date | Error |
| --- | --- | --- |
| `20241211-15` | 2024-12-11 | `no_parseable_listing_reference` |
| `20241202-11` | 2024-12-02 | `no_parseable_listing_reference` |
| `20240722-21` | 2024-07-22 | `no_parseable_listing_reference` |

Their retained source URLs and extracted-text SHA-256 values remain in cursor state and in the reconciliation receipts.

## Next task: bounded cursor5 parser/source-family repair

Always re-read current `main` and the durable cursor before starting.

For exactly the three held notices above:

1. Re-fetch the official BSE Index Services notice-detail payload.
2. Confirm the current response/text hash matches retained cursor evidence before changing grammar.
3. Inspect the demonstrated wording/HTML shapes and group failures by source family.
4. Add only grammar variants supported by those sources, with exact regression fixtures.
5. Preserve already-parsed cursor entries and avoid replaying successful notices.
6. Re-run the bounded cursor repair and retain newly discovered references as discovery-only.
7. Reconcile any recovered references against current production before issuer-specific verification.

Do not infer an issuer from an unparseable index notice. Do not repeat cursor4 batches 13/14, reviewed batches 18/19, or the 18 already-present cursor5 references.

## Prior completed unit: cursor4 live verification and handoff recovery — PR #189

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
