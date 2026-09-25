# Project status and handoff

Updated: 2026-09-24. Cursor10 publication verified on the actually served GitHub Pages dataset at 2026-09-25 02:57 UTC / 2026-09-24 22:57 America/Toronto.

## Current priority

Continue backend data correctness, official-source coverage and dependable publication under [DEVELOPMENT_PROCESS.md](DEVELOPMENT_PROCESS.md). The active application-term requirement remains **Lot Size only**. Keep market lot, minimum bid quantity, minimum application amount, listing date and index-admission date distinct. No UI or downstream commercial-feature work belongs to this continuation.

## VERIFIED: cursor10 bounded historical segment published — PR #222 / #223

The retained historical BSE SME notice cursor advanced by exactly one bounded 20-notice segment. Backfill run `36087053657` selected and parsed **20/20 notices**, with **0 fetch errors / 0 new unparseable notices**, and discovered **23 listing references**. Artifact `10844576517`, SHA-256 `10513ea7a8ba1addcd1d5944f0cb3e6010e29f276f8f6817bec1f9cdc1847233`. The semantic cursor publication commit is `c3809d9cb42a374d220d12ab7c3004f4e3a6f934`.

### Reconciliation and source review

Authoritative source-review run `36087769933`, artifact `10844392203`, SHA-256 `1d6de457ff85e0f15c9a7b8c5cb8c783d6a6e4b730372923369e88e402429f56`, source snapshot `727c069c117c52a5bff7e8c0201dc9c9286bff51`.

Against the then-current **1,171-record** 2020-2026 recovery/public universe, all **23 references were exact-missing identities**, with **0 already-present** and **0 identity/code/source conflicts**. Strict issuer-specific official BSE verification produced:

- **22 verified issuers**
- **66 explicit facts**: listing date, market lot and final issue price
- **1 rejected conflicting source**
- **0 unavailable sources**

Canonical listing-PDF archive probes returned HTTP 404, so the established strict official BSE HTML listing-notice contract remains the authority.

### Held conflict — Fabino Life Sciences Limited

**Fabino Life Sciences Limited is intentionally not published.** The index/candidate reference identifies listing date `2022-01-13`, while issuer-specific BSE Listing Notice `20220112-10`, published `2022-01-12`, contains an observed listing date of `2021-01-13`. The strict verifier therefore returns `listing_date_mismatch_or_missing`.

No date correction was inferred. The record stays held until authoritative official evidence resolves the conflicting year.

### Publication rehearsal and release

PR #222 merged as `6413c9e46542a578095c75a6ff5c8edcf5f99f49`. Its final release diff contained only five evidence/reconciliation JSON files: discovery batches33/34, cursor10 reconciliation and reviewed batches33/34. The temporary source-review workflow was removed before merge.

Exact publication rehearsal proved:

| Check | Result |
| --- | ---: |
| Baseline records | 1,171 |
| Result records | 1,193 |
| Verified additions | 22 |
| Existing records unchanged | 1,171 / 1,171 |
| Already-present reviewed entries | 247 |
| Holds/conflicts during import | 0 / 0 |
| Second run | Byte-idempotent |

Current-head reviewed-evidence run `36087912122` and data-contract run `36087912060` both passed before merge. Post-merge reviewed-evidence and data-contract checks also passed.

Production source-backed sync `36087986289` succeeded and generated data commit `384f235bdf19545f3960f2c9bcc7ed16e3f70d57`; operator-state commit `dcaf482c7b9860c1c50fb37ba565ce3fe1d8431b` reports overall **healthy**, with NSE collection, SEBI collection, rebuild, validation and repository publication all successful. The resulting Pages build `36088233705` succeeded.

### Actual served-data verification

PR #223 merged as `7e36858a7445aac975be4c32dba62ca0a718a94b` and only changes the existing read-only Pages verifier defaults to reviewed batches33/34.

Canonical post-merge verifier run `36088367208` passed against the actually served Pages dataset:

| Check | Result |
| --- | ---: |
| Actually served records | 1,193 |
| Reviewed issuers | 22 / 22 unique |
| Listing-date / market-lot / issue-price fields | 66 / 66 matching |
| Failed issuers | 0 |
| Unsupported fields | 6 null fields per issuer |
| Retained recovery document-hash fields | 66 |
| Document hashes serialized in public fields | 0 |

Served snapshot fetched `2026-09-25T02:57:25.917Z`; checked `2026-09-25T02:57:25.960Z`; dataset generated `2026-09-25T02:48:39.265Z`. Snapshot SHA-256: `e7ea980d0b158a239e3d22f155d42b90385672dfe7303e49efd10d5732f9cff8`, 6,352,711 bytes.

Post-merge artifact `10844168231`, ZIP SHA-256 `a437744898c0af70b00e46e0986b1288971f83e813ea076edbf4790f02c413b3`. Durable receipt: [verification/cursor10-live-publication-2026-09-25.json](verification/cursor10-live-publication-2026-09-25.json).

### Operational note

During temporary review-workflow cleanup, one branch push was rejected as non-fast-forward because the same review branch had advanced concurrently. Source verification and validation had already passed; no evidence was overwritten. The workflow was changed to fetch/reset the current remote branch and reapply the verified release files before pushing. The final PR diff was evidence-only and current-head CI passed.

## Cursor state and exact next backend task

Current retained BSE SME addition-notice state is parser **1.4.0**, catalog **236 eligible**, **220 tracked**, **219 parsed**, **1 retained unparseable**, **16 untracked**, updated `2026-09-25T02:38:14.470Z`, Git blob `9e73a4dfad42352af939152779c6459afdac544d`.

The next unseen notice is **`20210322-22`**.

**Next task: continue the remaining bounded historical discovery segment from `20210322-22` using the existing state-driven backfill.** Do not reset or replay prior progress. Reconcile newly discovered references against current recovery/public identities, BSE codes and listing-source identities. Independently verify only missing/unambiguous candidates in batches of at most 15, retain reviewed evidence, rehearse safe/idempotent publication, publish through the normal source-backed sync, then verify the actually served Pages result.

Keep the Fabino Life Sciences conflict separate and held. Do not guess a corrected date or include it in a later batch unless authoritative official evidence resolves the conflict.

Cursor10 discovery/reviewed batches33/34 are closed. Cursor9 batches31/32, cursor8 batches23/24 + reviewed29/30 and earlier repaired/cursor batches are also closed. Broader historical field completeness remains incomplete.

No UI, minimum-investment, billing, accounts, ads, new spending or permission changes belong to this continuation.

## Prior work and preserved history

Parser v1.4.0 remains unchanged. UI V2 remains a separate completed workstream under [UI_DESIGN_HANDOFF.md](UI_DESIGN_HANDOFF.md). Older archive files and verification receipts remain unchanged; archived next-task instructions are not current instructions.
