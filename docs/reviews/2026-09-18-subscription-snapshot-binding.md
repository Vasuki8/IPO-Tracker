# Subscription snapshot binding — 18 September 2026

## Recovered checkpoint and diagnosis

Recovery started from remote main `9210afeac2867d2ebbdfadd290706ec6a528bf4c`.
The previous handover was behind: #125 had merged as `cc41fad70e01866d0116f6dfca1a07082da10cc4`
and its derived review publication is `fe0bd1f4e807d0be52c6be16722ac2ba0b42a3b7`.
#130 strengthened live acceptance. Its actual receipt (run 35353865005, artifact
10550359119, ZIP SHA-256 `873565566e9c4d521103de45db1ed927894880fb60a1decbb3781aa6b34d0f68`)
passed 1,370 local routes and 22 complete HTTPS responses, including both held
intermediary profiles and validation/queue/phase reports. No part of #125 was
reimplemented or its older generated artifacts copied over accepted main.

The retained subscription collection from run 35350847357 was downloaded and
checksum-verified (artifact 10548793614, ZIP SHA-256
`5d6add38c8939cecc0b15baaff61cddf071131eedea697f7be1501978617cfab`). Its real
source-commit file is `1ca1112dee406327793f9b3e23c4291b8c8d13c7`. Seven of eight
attempts succeeded: five BSE and two explicitly secondary IPO Premium snapshots.
SpectraA failed: NSE returned 403, BSE had no matching issue link, and the existing
secondary feeds did not provide a usable matching row. This is recorded source
failure, not proof of a blocked publisher or authority to invent a replacement.

All seven successful proposed records omitted `subscriptionSourceUrl`, although
their new history rows retained it. The defect was already in the collected
proposal, before publication. This makes the atomic subscription group depend on
external history/source-array fallbacks and leaves retained conflicts unbound.
The writer also copied omitted categories from older observations, restamping the
mixed group with a new source and collection time. History deduplication compared
numbers alone, losing equal-value source/observation changes. These are software
provenance defects; this review does not adjudicate the underlying multiples.

## Small complete fix

The existing subscription writer now carries the supplied HTTPS URL inside the
publisher-defined atomic snapshot, with the existing independent observed/collected
clocks. A changed source, URL or observation time is a distinct history event even
when headline values are equal. Repeated collection of the same values and source
observation can still deduplicate history while advancing only the collection clock.
No observation timestamp is inferred; official feeds without one remain collection-only.

Before any write, reject empty/invalid numbers, malformed source bindings and
invalid, naive or future observation clocks. A response missing any previously
populated category is rejected as a whole: previous values, source metadata,
collection time and history all remain unchanged, and the existing runner can
try its next permitted source or record failure. This includes an explicitly
reported zero. A first partial snapshot keeps undisclosed categories null.
No category is borrowed from another observation and no final status is invented.
The prior test that expected a borrowed total is replaced with the stronger
whole-record-preservation assertion rather than removing the case.

A narrowly allowlisted leaf-collector change selects the existing `subscriptions`
mode, not a broad Final Prospectus repair. Unknown/mixed collector, policy, data,
workflow or dependency changes still use guarded repair; reviewed requests mixed
with source changes still fail. No workflow, schedule, writer, permissions or
source ordering is changed. P4/P5 gates and the source-commit guard remain mandatory.

## Verification boundary

Fifteen new regressions and all ten existing subscription tests pass locally via
uv, plus eight Node public-quality tests. Cases cover direct URL/authority binding,
source/observation switches with equal values, partial responses, zero/null/false,
invalid clocks/URLs, retained correction history, atomic publication conflicts and
narrow publication selection. All 1,370 profiles rebuild unchanged; the current
public verifier passes locally without touching canonical data or proposals.

The full local attempt ran 1,144 tests with eight errors, all missing workflow
files in the Pages artifact mirror. Locked packages were unavailable to local
`uv sync --frozen --offline`; the local tests used available Python 3.13.5 packages.
Neither attempt is represented as a full or frozen pass. Complete-repository
frozen CI and actual publication/deployment acceptance are required before release.
No new browser journey or full-PDF source audit is claimed by these local checks.

## Preserved constraints and remaining source work

This code candidate changes no accepted data or any of the 441 retained proposals.
It does not backfill older missing URLs by guessing, dispose of old conflicts,
refresh an old source clock, fix SpectraA's source availability, or promote secondary
information to official. Historical proposals still require original issuer/source
review. Source URL presence identifies the observation transport; it is not itself
proof of issuer matching or commercial-use permission. Existing source matching
and source rights remain separate review obligations.

P4's recovered gate is 1,603 blocking reviews, 387 actionable plus 55 higher-priority
records, zero unmapped; the increase from the stale handover is #125's 11 active
hold reviews, not this change. Teamtech stays held, Emmvee is not re-held, #105 remains
draft/unaccepted and P5/performance expansion remains gated. No spending, contracts,
outreach, tracking, billing, new infrastructure or access changes are introduced.
