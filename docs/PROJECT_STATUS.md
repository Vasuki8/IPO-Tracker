# Project status and handoff

Updated: 2026-09-24. Cursor10 publication verified on the actually served GitHub Pages dataset at 2026-09-25 02:57 UTC / 2026-09-24 22:57 America/Toronto.

## Current priority

Continue backend data correctness, official-source coverage and dependable publication under [DEVELOPMENT_PROCESS.md](DEVELOPMENT_PROCESS.md). The active application-term requirement remains **Lot Size only**. Keep market lot, minimum bid quantity, minimum application amount, listing date and index-admission date distinct. No UI or downstream commercial-feature work belongs to this continuation.

## VERIFIED: cursor10 bounded segment published — PR #222 / #223

The existing state-driven backfill advanced exactly one bounded historical segment. Backfill run `36087053657` selected **20 notices**, parsed **20/20**, had **0 fetch errors / 0 new unparseable notices**, and discovered **23 listing references**. Artifact `10844576517`, ZIP SHA-256 `10513ea7a8ba1addcd1d5944f0cb3e6010e29f276f8f6817bec1f9cdc1847233`. Durable cursor commit: `c3809d9cb42a374d220d12ab7c3004f4e3a6f934`.

### Reconciliation and source review

Read-only source-review run `36087201107`, artifact `10843813845`, ZIP SHA-256 `823e540317374ada2f983c7ca1d8e03d7c41d8f6b7b78d4741423e04a01f8c52`, source snapshot `c862d6c497408991e85ea2ab368994d091d461dd`.

Against the then-current **1,171-record** recovery/public universe, all **23 references were exact-missing identities**, with **0 already-present** and **0 identity/code/source collisions**. Independent issuer-specific official BSE listing verification produced:

- **22 verified issuers**
- **1 rejected/held issuer**
- **0 unavailable**
- **66 explicit verified facts** across listing date, market lot and final issue price

Canonical listing-PDF archive probes returned HTTP 404, so the established strict issuer-specific official BSE HTML contract remains the listing authority for the 22 accepted records. Reviewed evidence preserves original response hashes, collection/publication dates, normalized text and literal contiguous excerpts.

### HELD conflict — Fabino Life Sciences Limited

**Fabino Life Sciences Limited** (BSE scrip `543444`, listing notice `20220112-10`) is deliberately **not published**.

The January 12, 2022 official BSE notice contains contradictory year information: its main listing sentence says the shares are effective **January 13, 2021**, while the same notice refers to the IPO special pre-open session on **January 13, 2022**. Discovery/index evidence points to January 13, 2022, but index discovery is not listing-term authority.

The strict verifier therefore rejected the candidate with `listing_date_mismatch_or_missing`. No date was inferred, corrected, or guessed. Keep this issuer held until an authoritative official correction or independently authoritative listing source resolves the conflict.

### Publication rehearsal and merge

The exact source-snapshot rehearsal proved **1,171 -> 1,193**, exactly **22 additions**, all **1,171 existing records unchanged**, **247 already-present reviewed entries**, **0 holds/conflicts within the publishable batch**, and a byte-idempotent rerun.

PR #222 merged as `6413c9e46542a578095c75a6ff5c8edcf5f99f49`. Net release change is only five evidence files:

- discovery batch33
- discovery batch34
- cursor10 reconciliation
- reviewed batch33
- reviewed batch34

The temporary source-review workflow was removed before merge. No UI, parser, collector, cursor, schedule, permission or hand-edited generated-public-data changes were made in the release.

Current-head reviewed-evidence CI `36087912122` and full data-contract CI `36087912060` passed before merge. Post-merge reviewed-evidence and data-contract checks also passed.

Production source-backed sync `36087986289` succeeded. Generated-data commit: `384f235bdf19545f3960f2c9bcc7ed16e3f70d57`. Operator-state commit: `dcaf482c7b9860c1c50fb37ba565ce3fe1d8431b`. Operator health is **healthy** with collection, rebuild, validation and repository publication all successful.

### Actual served-data verification

PR #223 merged as `7e36858a7445aac975be4c32dba62ca0a718a94b` and only selects reviewed batches33/34 in the existing read-only Pages verifier.

PR-head live verifier run `36088279308` passed. Canonical post-merge verifier run `36088367208` also passed against the actual served Pages dataset:

| Check | Result |
| --- | ---: |
| Actually served records | 1,193 |
| Reviewed issuers | 22 / 22 unique |
| Listing-date / market-lot / issue-price fields | 66 / 66 matching |
| Failed issuers | 0 |
| Unsupported fields | 6 null fields per issuer |
| Retained recovery document-hash fields | 66 |
| Document hashes serialized in public fields | 0 |

Served snapshot fetched `2026-09-25T02:57:25.917Z`; checked `2026-09-25T02:57:25.960Z`; dataset generated `2026-09-25T02:48:39.265Z`. Snapshot SHA-256: `e7ea980d0b158a239e3d22f155d42b90385672dfe7303e49efd10d5732f9cff8`.

Post-merge live artifact `10844168231`, ZIP SHA-256 `a437744898c0af70b00e46e0986b1288971f83e813ea076edbf4790f02c413b3`. Durable receipt: [verification/cursor10-live-publication-2026-09-25.json](verification/cursor10-live-publication-2026-09-25.json).

## Cursor state and exact next backend task

Current retained BSE SME addition-notice state is parser **1.4.0**, catalog **236 eligible**, **220 tracked**, **219 parsed**, **1 retained unparseable**, **16 untracked**, updated `2026-09-25T02:38:14.470Z`, Git blob `9e73a4dfad42352af939152779c6459afdac544d`.

The next unseen notice is **`20210322-22`**.

**Next task: process one final bounded historical discovery segment from `20210322-22` using the existing state-driven backfill.** Do not reset or replay prior progress. Reconcile discovered references against all current recovery/public identities, BSE codes and listing-source identities. Independently verify only missing/unambiguous candidates in batches of at most 15, retain reviewed evidence, rehearse safe/idempotent publication, publish through the normal source-backed sync, and verify the actually served Pages result.

Keep the Fabino conflict separate from that cursor continuation. Do not publish or silently “correct” Fabino unless an authoritative official source resolves the contradictory listing date.

Cursor10 discovery/reviewed batches33/34 are closed. Cursor9 batches31/32, cursor8 batches23/24 + reviewed29/30 and all earlier repaired/cursor batches are also closed. Broader historical field completeness remains incomplete.

No UI, minimum-investment, billing, accounts, ads, new spending or permission changes belong to this continuation.

## Prior work and preserved history

Parser v1.4.0 remains unchanged. UI V2 remains a separate completed workstream under [UI_DESIGN_HANDOFF.md](UI_DESIGN_HANDOFF.md). Older archive files and verification receipts remain unchanged; archived next-task instructions are not current instructions.
