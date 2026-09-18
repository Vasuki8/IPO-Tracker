# Project status and release evidence

## Standing requirements

IPO Tracker is intended to become a public commercial product. Audience, pricing
and revenue model remain undecided. Preserve trust, accessible mobile research,
privacy, stable URLs and sustainable costs. Keep the light static architecture.
No new spending, contracts, outreach, tracking, billing or material access changes
without owner approval. Sponsorship must be identifiable and cannot affect facts
or research rankings. See [COMMERCIAL_READINESS.md](COMMERCIAL_READINESS.md).

Completed static terms require matching Final Prospectus field evidence. Active
provisional disclosures and official market observations must remain labelled.
Preserve source URLs, document identity, dates, units, nulls, separate source and
collection clocks, quarantines and correction history. P5/performance expansion
remain gated by P4. See [ROADMAP.md](ROADMAP.md) and [OPERATIONS.md](OPERATIONS.md).

## Verified implementation — 18 September 2026

[PR #128](https://github.com/Vasuki8/IPO-Tracker/pull/128) is merged and live at
`543c625b9234db7a2b6ab65c6ded624894f74606`, tree
`6a5641f93a218bd434ace573b8787da2ab35dcf5`. Reviewed head was
`fd2ea8b6585a8114e84ab745f6c3f0db36b002af` on `fix-value-hold-offer-identity`.
This documentation closeout on `docs-value-hold-identity-checkpoint` records that
completed prerequisite, not acceptance of the larger #125 repair.

### Recovered state and completed safeguard

Main had not advanced from `8cdce86a4dc05421585e042c4207f3cbc06ec22d` at recovery
or immediately before merge. The update-health report and earlier reviewed Emmvee
repair are complete and were not repeated. #125 remained an older, conflicting
candidate. Its original parent is `3bdbdc5cdfb6ad44c230d2977512a2e8fa69fee4`, not
the current accepted dataset; its historical counts cannot be carried into main.

Reconciliation exposed a prerequisite: value-scoped holds could supply issuer/offer
identity, but the public matcher ignored it. The fix requires any explicitly supplied
ID/company/symbol/opening date and the proof's offer date to agree. Malformed supplied
identity fails closed. Historical value-only reviews keep their existing PDF/value
scope without invented identities. Document conflicts still bind the same PDF even
after a new extraction or mirror. A changed value still needs matching source proof.

Affected users are researchers whose profile/directory/export status could otherwise
inherit a hold from the wrong issuer or offer. Acceptance: exact matching, no identity
spillover, malformed bindings rejected, historical rules preserved, identical shared
public projections and no current accepted-data changes. All criteria for #128 pass.
[The review note](reviews/2026-09-18-value-hold-identity.md) retains the initial tests,
source limitations and separate unaccepted #125 rehearsal.

### Tests, publication and actual served output

Ten new tests pass locally through uv, along with 26 existing public-quality tests
and eight Node tests. Against the exact baseline matcher, the new tests reproduced
27 failing subcases; the fixed matcher passes all ten. The same tests pass against
the pending shared helper. Synthetic test proofs are not a new disclosure audit.

[Frozen PR validation 35317595704](https://github.com/Vasuki8/IPO-Tracker/actions/runs/35317595704)
and [post-merge validation 35318139668](https://github.com/Vasuki8/IPO-Tracker/actions/runs/35318139668)
passed. The existing publication workflow independently ran **1,108 regressions**
with Python 3.12.14 and `uv sync --frozen`; its recorded collector job is
105514284896 in run 35318139596. Full local execution attempted 1,108 tests but
had six missing-workflow-file errors in the Pages mirror; local frozen installation
lacked locked packages. Those attempts are not counted as full/frozen local passes.

[Browser CI 35317595730](https://github.com/Vasuki8/IPO-Tracker/actions/runs/35317595730)
passed **25 journeys with zero page errors**, freshness boundaries at 1440/375/320
pixels, and separate reviewed-composition checks for directory, CSV, comparison,
responsive source-linked profiles and Teamtech withholding. Downloaded artifact
10535317830 was SHA-256 verified. The 375-pixel Emmvee screenshot was inspected.
Local Chromium navigation was administratively blocked; the browser passes are CI
results, not local results. The test merge is `364ff39d8eebfde319852511ed574a0a4343aeea`.

[Presentation publisher 35318139596](https://github.com/Vasuki8/IPO-Tracker/actions/runs/35318139596)
explicitly selected `presentation`, skipped source and residual collection, passed
strict validation and eight Node tests, rebuilt **1,367 profiles with zero writes**,
and reported no accepted changes to publish. Canonical publication remains core
`d462f858fcdb18909180f8747c0e2bf0552dd6f8`; no source clocks were refreshed.

[Pages 35318200827](https://github.com/Vasuki8/IPO-Tracker/actions/runs/35318200827)
and [live acceptance 35318239203](https://github.com/Vasuki8/IPO-Tracker/actions/runs/35318239203)
succeeded. The downloaded, checksum-verified first-attempt receipt binds exactly
`543c625b`, 1,367 local profile consistency checks and **17 complete public HTTPS
responses**. All expected file hashes match the local accepted tree. The ordinary
core publication correctly returns `reviewedPublication.status=not_requested`,
not a new reviewed repair. [The release receipt](releases/2026-09-18-value-hold-identity.json)
preserves the original live receipt, tests, artifact hashes and limitations.

All 1,367 canonical records, 441 pending proposals, phase/hold/ledger bytes and public
payloads remain unchanged. Proposal report replay passes and Emmvee's advice remains
applicable; this is not a proposal resolution. P4 stays at **387 actionable plus 52
higher-priority records, 1,592 blocking source reviews, zero unmapped**. Teamtech
remains held, and P5/performance expansion remains gated.

### Preserved unfinished integration and exact next task

#125's branch `fix-actionable-public-source-holds` was fast-forwarded from
`be7c448544381cdc0723e09b01f3734713ec8f05` to
`f09d272dcd8f5c087b625d571dfa30a73b084831`, tree
`9493b7af73373e30ae61082286cfba64399362cc`. Only its shared helper and the ten
identity tests changed; the helper blob `3f8a7956a780ad36ce5c4208a248e38e4ed3719d`
matches the locally tested bytes. Original source notes, fixtures, generated
candidate reports and history are retained. **This is not a rebase, full #125
acceptance or a merge.** Its proposed new role holds are not activated on main.

A separate current-baseline rehearsal produced 11 active holds / 1,607 total reviews /
1,603 blocking reviews, not the older candidate's 15 / 1,614 / 1,610. These numbers
are UNACCEPTED rehearsal results, not the deployed gate. Emmvee correctly stays
unheld. That partial rehearsal does not replace #125's original full tests/fixtures.

Sacheerome physical page 3 was visually rechecked on the official PDF: manager and
registrar columns are separate and the former-name line is subordinate. Snehaa's
18,126,150-byte PDF exceeded the web reader limit and direct download failed.
Its earlier immutable review is preserved. No fresh byte-hash/full-PDF verification,
replacement names, numerical corrections or source rights are claimed here.

**Next:** finish current-main reconciliation of #125 using its updated helper,
original review fixtures/note and the complete accepted inventory. Regenerate
queue/validation/phase/profile artifacts instead of copying older outputs; verify
all held fields remain actionable and every original review/proposal is preserved.
Complete source-binding, frozen regression, browser and publication-scope checks
before merging, then verify the actual deployed result. Preserve #128's identity
rule through the helper extraction. Do not adopt the rehearsal counts as targets.

After that, diagnose the overdue subscription path from current run/source evidence.
The 22 retained subscription proposals still need original source-link/issuer
support before audited disposition. Broad #105 stays draft/unaccepted at
`5a63a93dd9f782e3bc9ec853c937fb29661108f4`; preserve #94/#98/#99/#104 and freeze
`409c51c9`. Commercial rights, customer segment, pricing and privacy choices remain
unresolved. No spending, contracts, outreach, tracking, billing, dependency,
permissions or architecture changes were introduced.

The working copies are separate checksum-verified Pages mirrors, not remote Git
clones; direct Git DNS failed. Original archives and the unfinished local rehearsal
are preserved. The baseline artifact is 10535895104, SHA-256
`25d74a1160f7fc74d12623cc6e78fd20f540d017de01a9420f14332e4658bf59`.
[The previous full checkpoint](https://github.com/Vasuki8/IPO-Tracker/blob/8cdce86a4dc05421585e042c4207f3cbc06ec22d/docs/PROJECT_STATUS.md)
and existing release receipts retain all prior implementation and commercial context.
