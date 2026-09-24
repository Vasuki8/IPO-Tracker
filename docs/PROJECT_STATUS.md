# Project status and handoff

Updated: 2026-09-24. Latest source verification completed 21:00 UTC / 17:00 America/Toronto.

## Current priority

Continue P1/P2/P3 data correctness, official-source coverage and dependable publication under `DEVELOPMENT_PROCESS.md`. The application-term requirement remains **Lot Size only**. Keep market lot, minimum bid quantity, application amount, listing date and index-admission date distinct. UI redesign and downstream research/commercial infrastructure are out of scope.

## Completed: cursor7 reconciliation and source verification — PR #207

PR #207 merged as `17fe924e81fdf735ffd7addd1ed9982dfe49a3d8`. The independent historical BSE SME cursor had advanced beyond the prior handoff, so this unit preserved sequencing and reconciled the new 20-notice segment rather than replaying cursor6 parser work.

### Cursor7 discovery and reconciliation

The segment first attempted at `2026-09-24T20:00:39.470Z` contains:

- **20 notices**;
- **18 parsed listing references**;
- **2 new unparseable notices**: `20231206-8` and `20230719-15`.

All 18 parsed references were checked against the current 2020-2026 retained recovery universe (**1,091 records**) using normalized issuer identity, BSE scrip code and listing-source identity. Result: **18 exact-missing / 0 already-present / 0 code or source collisions**. No fuzzy identity equivalence was accepted.

Retained discovery inputs:

- `data/discovery/bse-listing-reconciliation-2026-09-24-cursor7.json`;
- `data/discovery/bse-listing-candidates-2026-09-24-batch20.json` — 15 issuers;
- `data/discovery/bse-listing-candidates-2026-09-24-batch21.json` — 3 issuers.

Index-addition evidence remains discovery-only and was not used as listing-term authority.

### Evidence-backed verifier repairs

The first source-verification run exposed two identity-only rejects:

- Arrowhead: the BSE Index Services discovery text used **“Arrowhead Separation Engineering Limited”**, while issuer-specific BSE listing notice `20231124-50` uses the legal-name spelling **“Arrowhead Seperation Engineering Limited”**. The candidate now preserves both spellings and uses the issuer-specific listing notice as listing authority.
- City Crops: the listing verifier incorrectly captured `Registered & Corporate Office` as part of the issuer name. The parser boundary now accepts that demonstrated BSE office heading, with a regression fixture. No broader fuzzy matching was added.

The final PR-head source verification run `36058133127` completed:

- batch20: **15 / 15 verified**;
- batch21: **3 / 3 verified**;
- **0 rejected**;
- **0 unavailable**.

Evidence artifact:

- artifact: `10833780727`;
- digest: `sha256:553d9350d77756c3f61bac19f563aae15d3c0c7d97b6eebe47da48e7c4e2137c`;
- expiry: `2026-10-08T21:00:14Z`.

Other final PR-head checks also passed:

- reviewed BSE listing evidence: `36058133257`;
- BSE 544770 identity-conflict guard: `36058133386`;
- full IPO data contract: `36058133413`.

This PR is discovery/source verification only. It does **not** materialize the 18 issuers into retained recovery or the public dataset.

### Current cursor and exact next task

Re-read after merge:

- parser **1.3.0**;
- **160 / 236 tracked**;
- **153 parsed**;
- **7 unparseable**;
- **76 untracked**;
- cursor state blob: `6ada9ade533cd1dc535799814b7a61bece067d35`;
- updated at `2026-09-24T20:00:39.470Z`.

The seven retained failures remain separate and must not be used to infer issuers:

- `20240624-11`
- `20240612-20`
- `20240606-11`
- `20240205-12`
- `20240103-22`
- `20231206-8`
- `20230719-15`

**Next task:** freeze the 18 source-verified cursor7 results from artifact `10833780727` into reviewed BSE evidence manifests, at most 15 issuers per manifest (the next available reviewed manifest numbers are currently batch26/batch27). Preserve exact official BSE source URL, response hash, collection/publication date, page/evidence metadata and only explicit listing date, market lot and final issue price; unsupported terms remain null. Rehearse the real importer/publication against latest main, require existing records to remain unchanged and a second run to be idempotent, then publish through the existing source-backed workflow and verify the actually served Pages dataset. Re-read main immediately before materialization because automation may change coverage. Only after this cursor7 parsed segment is closed should the seven unparseable notices be handled as a separate bounded parser/source-family repair.

Do not replay cursor7 discovery batches20/21, cursor6 batches18/19, or reviewed batches24/25.

## Completed: cursor6 reviewed publication and live verification — PR #204 / #205

PR #204 merged as `30127408c952dd98da6524ff13ee2d6d5537503f`. It converted the 19 already source-verified cursor6 candidates into reviewed evidence without changing parser/cursor behavior:

- `data/verified-bse-listings/2026-09-24-batch24.json` — 15;
- `data/verified-bse-listings/2026-09-24-batch25.json` — 4.

Both manifests retain source verification run `36041395122`, artifact `10826304295`, artifact ZIP SHA-256 `1a54f73efd2784202fb64f1ddadb5cbd825b448aea4056a3d2d2ff2ebe35f441`, exact issuer-specific official BSE notice URLs/response hashes/collection and publication dates, and only explicit listing date, market lot and final issue price. Canonical listing-PDF archive probes were unavailable; unsupported terms remain null.

### Publication safety and production

Immediately before review, all 19 identities were still absent from the current 1,072-record public dataset and 273-record 2024 recovery set.

The real offline importer/publication rehearsal measured:

- **1,072 -> 1,091** records;
- exactly **19 additions**;
- **148 already-present** reviewed BSE entries;
- **0 held existing**;
- **0 identity conflicts**;
- all **1,072 existing records unchanged**;
- second import/rebuild: no-op / idempotent.

PR #204's reviewed-evidence/importer CI and full data-contract CI both passed before merge.

Merge-triggered production sync `36044490807` completed successfully:

- reviewed BSE import: **19 added / 148 already present / 0 held / 0 identity conflicts**;
- semantic publication: **19 added / 7 changed / 0 removed / 0 conflicts**;
- source-backed data commit: `3e6b106e0daa50bb381159e9f5578b205ee54611`;
- operator-state commit: `d189a486120e2ee31c83a834770af22adf298f84`;
- published/validated: **1,091 records**;
- current 2024 recovery: **292 records**;
- operator health: **healthy**.

The seven changed records are normal concurrent official-source enrichment from the same source-first run and are distinct from the 19 reviewed additions.

### Actually served data verification

PR #205 merged as `e920fb28cd4647c2ecbd17529b23a13607851910`. It changes only the existing read-only BSE publication verifier default to batch24 + batch25 and retains a durable verification summary; it does not import or mutate IPO values.

Canonical post-merge live verifier run `36045625232` completed successfully:

| Check | Result |
| --- | ---: |
| Live records | **1,091** |
| Reviewed issuer identities | **19 / 19 unique** |
| Listing date / lot / issue-price fields | **57 / 57 matching** |
| Failed issuers | **0** |
| Unsupported fields | **6 null fields for every issuer** |
| Original document-hash field sources checked in recovery | **57** |
| Document hashes serialized in public field evidence | **0** |

The public projection intentionally omits document SHA-256 values; raw hashes remain mandatory and verified in retained recovery. Do not describe this release as public-hash verification.

Post-merge observation:

- snapshot fetched: `2026-09-24T19:04:35.469Z`;
- checked: `2026-09-24T19:04:35.534Z`;
- dataset generated: `2026-09-24T18:54:41.274Z`;
- snapshot SHA-256: `b707398c57676e6758f113ef31d6c1a717cc012a27f266b7a6f6f9b439f7fa5f`;
- artifact: `10828372193`;
- artifact ZIP SHA-256: `f6bceadb52852e54ad1ee21bb7b2131a9c7461f53e677dc48fa4e4065dfe5f1b`;
- artifact expiry: `2026-10-08T19:04:35Z`.

Durable receipt:

`docs/verification/cursor6-live-publication-2026-09-24.json`

Post-merge workflows all passed:

- read-only live publication verifier: `36045625232`;
- full data contract: `36045625276`;
- reviewed BSE evidence/importer: `36045625287`;
- deploy workflow: `36045625354`;
- native Pages build: `36045671486` — success on final Pages-health revision `187493575f425ecf694f307b9567ddd05cecd16b`.

### Cursor and next task

Cursor6 publication is fully closed. At handoff the independent cursor remains:

- parser **1.3.0**;
- **140 / 236 tracked**;
- **135 parsed**;
- **5 unparseable**;
- **96 untracked**.

The five unfinished notices are:

- `20240624-11`
- `20240612-20`
- `20240606-11`
- `20240205-12`
- `20240103-22`

**Next task:** perform a bounded parser/source-family diagnosis of only those failures. Re-fetch official BSE Index Services details, compare response hashes with retained cursor hashes, group by demonstrated source syntax, and make only evidence-backed additive grammar changes with fail-closed regression fixtures. Do not infer issuer identities from failed index notices. Re-read the cursor first in case independent automation has advanced; do not replay cursor6 discovery batches18/19 or reviewed batches24/25.

## Prior completed: cursor6 reconciliation and source verification — PR #201

PR #201 merged as `9cc541d3b9e1bc317ed3e9bb3545ea51ce47f327`.

The 20-notice segment first attempted at `2026-09-24T18:12:33.727Z` produced **15 parsed notices / 19 listing references / 5 unparseable notices**. The parsed references were reconciled against current production (**1,072 records**) and 2024 recovery (**273 records**): **19 exact-missing / 0 already-present / 0 ambiguous or BSE-code collisions**.

Retained reconciliation and candidate batches:

- `data/discovery/bse-listing-reconciliation-2026-09-24-cursor6.json`;
- `data/discovery/bse-listing-candidates-2026-09-24-batch18.json` — 15;
- `data/discovery/bse-listing-candidates-2026-09-24-batch19.json` — 4.

Source verification run `36041395122` completed **15/15 + 4/4 verified**, 0 rejected/unavailable. Artifact `10826304295`, ZIP SHA-256 `1a54f73efd2784202fb64f1ddadb5cbd825b448aea4056a3d2d2ff2ebe35f441`.

PIOTEX INDUSTRIES LIMITED demonstrated an older official-notice variant where the lot is present only as `minimum market lot (i.e.1200 equity shares)`. The verifier now accepts that bounded clause while retaining all identity/date/SME/price guards; regression coverage is merged.

Current cursor after this batch: parser **1.3.0**, **140/236 tracked**, **135 parsed**, **5 unparseable**, **96 unseen**.

The five failures remain separate: `20240624-11`, `20240612-20`, `20240606-11`, `20240205-12`, `20240103-22`.

### Concurrent repaired-cursor5 closure

The prior handoff's four batch17 issuers were independently completed by concurrent reviewed **batch22** before this continuation reached publication. PR #199 records production sync `36036317281` (4 additions) and live verification `36037026089` (**4/4 issuers, 12/12 fields, 0 failures**) at **1,072 total records**. Duplicate PR #202 was closed unmerged after its rehearsal correctly held all four existing records. Do not repeat batch17/batch22.

### Next task

Freeze cursor6's 19 already-verified source results from artifact `10826304295` into reviewed evidence manifests, preserving exact official HTML text/hash and only explicit listing date, market lot and final issue price. Rehearse against latest main before publication because automation may have changed identity coverage. If still missing/unambiguous, publish through the existing importer and verify the served dataset. Only after cursor6 batches18/19 are closed should the five unparseable notices receive a separate demonstrated parser/source-family repair.

## Prior completed: cursor5 parser/source-family repair — PR #193

PR #193 merged as `61453efd680289a57ecc889a0070aa894624df77`.

This batch closed the three parser failures left after PR #191's cursor5 publication. It did **not** infer IPO terms from BSE index notices and did not materialize new IPO records.

### Bounded diagnosis

The retained failures were:

| Index notice | Retained text SHA-256 |
| --- | --- |
| `20241211-15` | `f9f8af6c8d5ff4bb90988651e6ceb9b7814cc18bc2f7f82716d87c1786c258e9` |
| `20241202-11` | `31308fbc6b6f43f758f5310d2fdf7ec73f30c2c99e82f063a7ee86823c53f8e1` |
| `20240722-21` | `2c82a1a53467bce1c4d60d0dda60c7b8c49081b3f5da994ed9fb5f9cb19dad18` |

A temporary read-only diagnostic re-fetched exactly these three BSE Index Services detail responses. All three fresh response hashes matched the retained cursor hashes.

Two notices use whitespace after the opening parenthesis before the ticker label. The July 2024 notice uses a single `Notice No:` label followed by two listing-notice IDs and then two issuer/ticker pairs in the same order.

### Parser v1.3.0

The additive repair:

- accepts whitespace inside `( Exchange ticker ... )`;
- accepts the demonstrated shared notice-ID list only when notice-ID count exactly equals issuer/ticker-pair count;
- preserves order for that one-to-one mapping;
- rejects partial clauses, leftover notice IDs and issuer captures containing raw notice-number tokens;
- keeps all existing listing-statement/date/ticker safety checks;
- treats successful parser v1.1 and v1.2 cursor entries as compatible;
- requeues failed v1.2 entries immediately as `parser_changed_failure`.

The temporary diagnostic script and workflow hook were removed before merge.

CI exposed and fixed three test/control-flow issues during development: the migration fixture initially mislabeled the incoming parser version; the standard parser initially aborted before the shared-ID fallback; and an incomplete shared clause could initially leak a raw second notice ID into the first issuer capture. The final regressions explicitly fail closed on all three cases.

Final PR-head validation:

- data contract `36028430818` — success;
- reviewed evidence `36028430692` — success;
- dedicated historical BSE cursor/parser `36028431156` — success.

### Production repair

Merge-triggered backfill run `36028598993`:

- selected: **3 / 3**, each `parser_changed_failure`;
- parsed: **3 / 3**;
- fetch errors: **0**;
- unparseable: **0**;
- recovered references: **4**;
- artifact: **10820393192**;
- artifact ZIP SHA-256: `01f9895ba1fcc97abda170c5f4a1690e227fc6401f3e2dde314ee4cd99b95f3c`;
- cursor-state commit: `fd06045ac437636bc5d0c8dba087397ad4897c28`.

Cursor after repair:

- parser **1.3.0**;
- **120 tracked / 236 eligible**;
- **120 parsed**;
- **0 failed / unparseable**;
- **116 unseen**;
- next unseen: **`20240624-11`**.

Post-merge data-contract, reviewed-evidence, BSE-universe and backfill workflows all passed. The Pages deploy workflow for the parser merge also succeeded.

### Repaired-reference reconciliation

Current reconciliation snapshots:

- `data/recovery/2024/nse-issue-information.json`: blob `304a11c1ddaa76a58f8c649cbf2b83fd91e2eab3`, **269 records**;
- `data/ipos.json`: blob `9d3724dd445ef0e0e12a6bb7fa43c4fc40d42345`, **1,068 records**.

Result: **4 exact-missing identities / 0 already present / 0 ambiguous or BSE-code/source collisions**.

| Issuer | BSE code | Listing notice | Listing date |
| --- | ---: | --- | --- |
| NISUS FINANCE SERVICES CO LIMITED | 544296 | `20241210-61` | 2024-12-11 |
| Rajesh Power Services Limited. | 544291 | `20241129-72` | 2024-12-02 |
| Aelea Commodities Limited | 544213 | `20240719-44` | 2024-07-22 |
| Three M Paper Boards Ltd | 544214 | `20240719-38` | 2024-07-22 |

Retained files:

- `data/discovery/bse-listing-reconciliation-2026-09-24-cursor5-repaired.json`;
- `data/discovery/bse-listing-candidates-2026-09-24-batch17.json`.

These four references are discovery-only until issuer-specific BSE listing notices independently verify them.

### Next task

Always re-read current `main` and cursor state first. Even if the independent cursor advances, close **batch17** before skipping to newer discovery.

Acceptance criteria:

1. independently verify the four pinned issuer-specific official BSE listing notices;
2. require exact issuer identity, listing notice, six-digit BSE code, listing date and SME listing statement;
3. retain market lot and final issue price only when explicit in issuer-specific official evidence;
4. preserve unsupported fields as null;
5. publish only reviewed evidence through the existing importer and verify the served dataset;
6. after batch17 is closed, continue the historical cursor from `20240624-11`.

## Prior completed: cursor5 reconciliation, publication and live verification — PR #191 / #192

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
