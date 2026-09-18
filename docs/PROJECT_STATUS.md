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

## Active core subscription boundary repair — 18 September 2026

Starting checkpoint: `b3a108785c8f4436cd83a14c2ea408ed1f9e9683` (#134).
#125–#134 are already merged; the latest Pages run 35373656691 and live check
35373705280 passed at that exact commit. The actual live log binds 1,371 routes
and 22 complete HTTPS responses. The full earlier checkpoint is preserved
[at the starting commit](https://github.com/Vasuki8/IPO-Tracker/blob/b3a108785c8f4436cd83a14c2ea408ed1f9e9683/docs/PROJECT_STATUS.md).

### Problem, users and acceptance

Researchers could see a newly collected NSE summary total attached to older BSE
or secondary categories, source URLs and clocks. The publisher's atomic group
cannot identify a mixed snapshot already assembled by the core collector.

[PR #135](https://github.com/Vasuki8/IPO-Tracker/pull/135), branch
`fix-core-subscription-boundary`, adds a reproduction through the real
`run_update_final_policy.py` entrypoint. Test-only commit
`5d39041f7ba50e283cedbbc64d67067b96b93156` preserves the before-fix checkpoint.

The fix makes generic issue-feed multiples independent observations and preserves
the complete accepted subscription family and its history across core refreshes.
Observations retain feed endpoint identity, issuer/offer dates, raw reported
fields, multiples and collection time. Observation time remains unknown and
the bid denominator explicitly unverified. Missing accepted values stay missing;
the dedicated detail collector retains its existing source-bound acceptance rules.

Acceptance: reproduce the old failure; pass frozen regression and browser checks;
preserve unrelated lifecycle updates and concurrent accepted detail snapshots;
review the complete diff; merge through normal protections; verify Pages output.
Do not restore historical numbers from the diagnostic or automatically resolve
proposals. This implementation is prevention, not source-value adjudication.

### Validation and release state

The local execution environment is disconnected (`409 environment_offline`).
Edits use GitHub's repository tools; all new execution evidence must come from
actual GitHub CI. No local pass is claimed. CI and release results will be recorded
before closing this increment. The existing source/repair publisher and its
permissions, schedules and validation remain unchanged.

The network-free regression reconstructs eight incoming summary rows from the
retained `nextRepairDiagnostic` in the BSE release receipt. Those rows and their
issuer shells are synthetic reproductions of recorded deltas, not original HTTP
responses. They prove the producer/merge behavior, not which source total is correct.
See [the boundary review](reviews/2026-09-18-core-subscription-boundary.md).

### Gate, blockers and next action

Starting accepted inventory: 1,371 records; P4 remains incomplete with 387 actionable
plus 56 higher-priority records, 1,607 reviews / 1,603 blocking / four P5-only and
zero unmapped. All 441 retained proposals, including 22 subscription proposals,
remain untouched. Teamtech stays held and accepted Emmvee evidence stays intact.
#105 is still draft at `5a63a93dd9f782e3bc9ec853c937fb29661108f4`; preserve
#94/#98/#99/#104 and the `409c51c9` freeze.

After this prevention passes, review the eight historical diagnostic snapshots
against current exact issuer/offer and denominator evidence. Do not assume either
old or new total is correct. If source reconciliation is blocked, use an explicit,
evidence-bound public review hold rather than an estimated replacement. SpectraA's
missing matching source and the 22 original subscription proposals remain open.
P5 and performance expansion stay gated. Commercial rights, audience, pricing,
privacy and applicable professional-review questions remain unresolved.
