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

## Current execution — retained-proposal report, 18 September 2026

Verified starting main is `800405b1c19c1c61367eb17b62bf5367267a0f70`, tree
`0ac00aa42b1db678a266e7bbe99dd182d522dc75`. The #117/#118 release and the Emmvee
publication `3834c732` are complete and are not repeated. No newer open work was
found beyond preserved #94/#98/#99/#104/#105. Main's successful Pages and reviewed
live acceptance remain runs 35305866028 and 35305891983.

### Implemented milestone: read-only retained document-proposal reconciliation

Branch `feat-read-only-proposal-reconciliation` adds an operator report and sixteen
regressions. Problem: 441 retained proposals have no current comparison or actionable
triage; a newer timestamp or matching amount cannot safely resolve a whole source
update. Acceptance requires one traceable report entry per occurrence, complete
atomic-group comparison, shared public evidence states, explicit malformed/unknown
work and zero writes to canonical/proposal/review/phase data.

The report imports the publisher's document group and existing public-quality rules.
It distinguishes exact whole-group matches, policy-check-clock-only differences,
unchanged base, conflicting groups and unsupported/malformed identities/scopes.
Equal values with different proofs remain conflicts. Source/proof clocks, review
state, missing keys, nulls and zero are preserved. It prints to stdout only and has
an exact-input/policy freshness check; no proposal is automatically resolved.
Other proposal families remain explicit `not_assessed` work with next actions.

The existing read-only validation job generates and retains the report before any
transient correction rehearsals. There is no new writer, schedule, dependency,
source request, public payload or paid service. `tools/` intentionally keeps this
operator utility outside collector-triggering `scripts/` changes; the collector
workflow and source guard are unchanged. See [the operating guide](PROPOSAL_RECONCILIATION.md).

Current measured result: **441 retained occurrences**, **159 document proposals**,
all 159 still conflicting, **282 explicitly not assessed**. Thirty document groups
have value/field-presence differences; all 159 differ in evidence/review/scope.
These are overlapping comparisons, not 159 newly confirmed source errors.
The original pending status, fingerprints, full snapshots and histories are unchanged.

### Verification and release boundary

Local uv execution passed **1,051 regressions** (16 new), **eight Node checks**,
whole-backlog byte preservation, deterministic report replay and stale-input/report
rejection. All **1,366 profiles** rebuild with zero changes; the existing reviewed
public-delivery verifier passes locally against the accepted snapshot. Local Python
3.13.5 used available requests 2.32.5 / pypdf 5.9.0; frozen offline sync failed because
locked packages were absent. This is not a local frozen-environment pass. Frozen
Python 3.12 CI, reviewed diff, authorized merge and post-merge deployment/HTTPS
acceptance remain required before declaring this branch released.

The runtime had retained ZIPs/screenshots but no working checkout. A separate
artifact mirror was recovered from Pages artifact 10530808507, SHA-256
`9b9432c2c3344340e86ce63fede2d0b6ee4740cdd9743fa5516323482bf027b7`.
Relevant workflow files were read via the connector and their Git blob hashes
matched. Direct Git access failed DNS; the local mirror is not remote Git history.
All pre-existing archives and the original source branches remain untouched.

### Gate, blockers and exact next task

P4 is still incomplete: **387 actionable + 51 higher-priority records**, **1,596**
total source reviews, **1,592** blocking, **four** P5-only and **zero** unmapped.
No exclusions or counts were changed to claim progress. Teamtech remains held;
P5/performance expansion remains gated. Broad parser draft #105 remains unaccepted
at `5a63a93dd9f782e3bc9ec853c937fb29661108f4`, code freeze `409c51c9`.
The original #94/#98/#99/#104 work remains preserved. Commercial source rights,
customer segment, pricing and privacy choices remain unresolved; this milestone
introduces no spending, outreach, tracking, billing or access changes.

**Next concrete task:** use the report to review the single retained Emmvee document
proposal (baseline input index 133) against the released composition proofs and
its original source context. Its allocation differences exceed the composition
repair, so the complete proposal must not be declared superseded on that repair
alone. Record an evidence-backed decision separately; do not delete the proposal
or reopen Teamtech/P5. Subscription triage and overdue-update monitoring follow.

Earlier verified release receipts and detailed recovery evidence remain in
`docs/releases/` and [the immutable prior status](https://github.com/Vasuki8/IPO-Tracker/blob/800405b1c19c1c61367eb17b62bf5367267a0f70/docs/PROJECT_STATUS.md).
