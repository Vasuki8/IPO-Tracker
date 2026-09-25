# Project status and handoff

Updated: 2026-09-25 UTC / 2026-09-24 America/Toronto. Parser v1.5 repair and all 10 recovered publishable BSE references are verified on the actually served Pages dataset.

## Current priority

Continue **P1 data correctness / IPO-universe coverage**, then P2 source evidence and P3 freshness under [DEVELOPMENT_PROCESS.md](DEVELOPMENT_PROCESS.md). The active application-term requirement remains **Lot Size only**. Keep market lot, minimum bid quantity, minimum application amount, listing date and index-admission date distinct. No UI or downstream commercial-feature work belongs to this continuation.

## VERIFIED: all retained BSE cursor parser failures repaired — PR #226

PR #226 merged as `b489d4d0ba9b01f3f6b2ecf88c56b17b877dcfda` and releases parser **v1.5.0**.

Read-only diagnosis run `36091504365`, artifact `10846116502`, ZIP SHA-256 `aafb6f74855133ca07573163b6b06326d1384361652c80a390ebdecd43784d83`, proved two exact legacy source families:

- `20200813-12` and `20200713-20`: listing dates contain whitespace before the comma, e.g. `August 13 , 2020`.
- `20221010-15`: one repeated notice prefix with compact numeric suffixes, followed by an explicit ordered BSE SME IPO ticker/name table.

The v1.5 repair is bounded and fail-closed. The compact mapping requires unique expanded notice IDs, unique six-digit tickers, exact row-count equality, the demonstrated table header, a single matching admission-date cell, and the prose listing date. It never substitutes the later index-admission date. Exact official source fixtures and negative mutations are retained.

Parser v1.4 parsed successes are explicitly compatible with v1.5, so the migration does **not** replay successful history. Final PR-head reviewed-evidence run `36092040925`, data-contract run `36092040928`, and bounded-backfill test run `36092040923` all passed.

### Production parser migration

Post-merge backfill run `36092149729`, artifact `10845847537`, ZIP SHA-256 `93a4e238e50ee030020b21275f30211ded1b7454577cf6c21828154d7a6c03bc`, selected exactly the **3 failed v1.4 notices** as `parser_changed_failure`.

Result: **3 selected, 3 parsed, 10 references recovered, 0 fetch errors, 0 unparseable**. Cursor commit `74f8f7d963af16ce18d29b5c3179f55d7db0c404`; cursor blob `1ed18c7221833aba026da5c28791c54e590805b7`.

Current cursor is parser **1.5.0**, **236/236 tracked, 236 parsed, 0 failed, 0 unseen, complete:true**.

## VERIFIED: 10 v1.5-recovered issuers published — PR #227 / #228

Independent review run `36092275068`, artifact `10846242339`, ZIP SHA-256 `ed0a6042e12dcb199ac4b8dea5c5434eab7918b8ecfbff7f6c9d1591844fc5d5`, reconciled the 10 recovered references against the then-current 1,208-record recovery/public universe:

- **10 exact-missing identities**
- **0 already present**
- **0 identity/code/source collisions**
- **10/10 issuer-specific BSE listing notices verified**
- **30/30 explicit facts**: listing date, market lot, final issue price
- **0 rejected / 0 unavailable**

All 10 canonical listing-PDF archive probes returned HTTP 404, so the established strict official BSE listing-notice HTML contract remains the authority. Unsupported fields remain null.

Exact publication rehearsal proved **1,208 -> 1,218**, exactly 10 additions, all 1,208 existing records unchanged, 284 already-present reviewed entries, 0 holds/conflicts and a byte-idempotent rerun. PR #227 merged as `e581d1e7a47f59fc62a3488849e815f5ae689b15`. Production source-backed sync `36092732738` succeeded; generated-data commit `61b173feb789fba15eb207c0bacaaa476704cbbb`; operator-state commit `602fd2cdb2d2da6c47e85048bf61c3aa1839566d` is **healthy**.

### Actual served-data verification

PR #228 merged as `9abfd1f72e9277dc22158be9249fe419fd667fd7` and only selects reviewed batch36 in the existing read-only verifier.

Canonical post-merge run `36093076719` passed:

| Check | Result |
| --- | ---: |
| Actually served records | 1,218 |
| Recovered issuers, present exactly once | 10 / 10 |
| Listing date / market lot / issue price | 30 / 30 matching |
| Failed issuers | 0 |
| Unsupported fields | 6 null fields per issuer |
| Cursor | parser 1.5.0; 236 / 236 parsed |

Snapshot fetched `2026-09-25T04:06:40.989Z`; checked `2026-09-25T04:06:41.046Z`; dataset generated `2026-09-25T03:54:56.693Z`. SHA-256 `9a5ced8e0831bf07961c4fb3593f24d99008688f6874b2b86649c1d449841945`, 6,480,099 bytes. Post-merge artifact `10846531544`, ZIP SHA-256 `a035bfefa772678329c32d10a7dae1a0c846911d67318a742d9b30f8ae9c6db7`. Reviewed-evidence run `36093076748`, data-contract run `36093076711`, and Pages deployment `36093076768` passed.

Compared with the prior verified 1,208-record Pages snapshot, the served result is **exactly +10 records, 0 removals, and 0 changes to any existing record**.

Durable receipt: [verification/bse-parser-v1.5-repair-and-live-publication-2026-09-25.json](verification/bse-parser-v1.5-repair-and-live-publication-2026-09-25.json).

## Remaining held conflict

**Fabino Life Sciences Limited** remains deliberately absent. BSE scrip `543444`, issuer listing notice `20220112-10`: candidate/index date `2022-01-13` conflicts with the issuer-specific official notice's observed date `2021-01-13`. Do not infer or silently correct the year. Publish only if authoritative official evidence resolves the conflict.

## Observed baseline and exact next backend task

The current served tracker contains **1,218 records**. Observed counts are: 2020 **65**, 2021 **120**, 2022 **136**, 2023 **216**, 2024 **301**, 2025 **293**, 2026 **87**. These are tracker counts, **not** a claim of complete official-universe coverage.

The bounded BSE SME addition-notice cursor is now fully parsed, so repeating or extending that cursor is no longer the next P1 task.

**Next task: run a fresh machine-readable official IPO-universe completeness audit across current NSE, BSE and SEBI sources.** Define and retain inclusion/status rules for Mainboard and SME, draft/RHP/final-prospectus stages, open/upcoming/completed/withdrawn outcomes as applicable; reconcile issuer identity, BSE/NSE identifiers and source identity against the current 1,218-record universe; report exact missing/ambiguous/already-present counts; and only materialize unambiguous exact-missing issuers with official evidence. Do not treat the 236 BSE index notices as the full IPO universe.

After identity coverage is reconciled, continue P1 field completeness, with Lot Size still the active application-term requirement.

No UI, minimum-investment expansion, billing, accounts, ads, new spending or permission changes belong to this continuation.

## Preserved history

The preceding status/README are archived byte-for-byte in [archive/PROJECT_STATUS-before-v15-parser-repair.md](archive/PROJECT_STATUS-before-v15-parser-repair.md) and [archive/README-before-v15-parser-repair.md](archive/README-before-v15-parser-repair.md). Older archives and receipts remain unchanged. UI V2 remains a separate completed workstream under [UI_DESIGN_HANDOFF.md](UI_DESIGN_HANDOFF.md).
