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

## Current verified implementation — 18 September 2026

[PR #119](https://github.com/Vasuki8/IPO-Tracker/pull/119) is merged and live at
`cbc55e78e8806ae4641ef14fac39927677dcba01`, tree
`e2f49a1cfd24aa13f646b08278d6f8ea31e940e3`. Reviewed head was
`2f3a25d5381e9c68e8bfc69083497c276daed464` on
`feat-read-only-proposal-reconciliation`. This documentation-only closeout on
`docs-proposal-reconciliation-checkpoint` records the completed release, not a
second implementation milestone. Canonical publication remains `3834c732`.

### Reconciled starting point

Verified starting main is `800405b1c19c1c61367eb17b62bf5367267a0f70`, tree
`0ac00aa42b1db678a266e7bbe99dd182d522dc75`. The #117/#118 release and the Emmvee
publication `3834c732` are complete and are not repeated. No newer open work was
found beyond preserved #94/#98/#99/#104/#105. The starting checkpoint's successful Pages and reviewed
live acceptance were runs 35305866028 and 35305891983.

### Completed milestone: read-only retained document-proposal reconciliation

Branch `feat-read-only-proposal-reconciliation` adds an operator report and sixteen
regressions. Previously, 441 retained proposals had no current comparison or actionable
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

### Verified tests, report and release

Local uv execution passed **1,051 regressions** (16 new), **eight Node checks**,
whole-backlog byte preservation, deterministic report replay and stale-input/report
rejection. All **1,366 profiles** rebuild with zero changes; the existing reviewed
public-delivery verifier passes locally against the accepted snapshot. Local Python
3.13.5 used available requests 2.32.5 / pypdf 5.9.0; frozen offline sync failed because
locked packages were absent. This is not a local frozen-environment pass.

[PR validation 35307190366](https://github.com/Vasuki8/IPO-Tracker/actions/runs/35307190366)
succeeded using Python 3.12 and `uv sync --frozen`, including the full regression
suite, report generation/replay, input-preservation check, generated public
payloads, strict validation and compact support artifacts. Its actual test merge
was `d80797a40804c556e0ae511866a85f0f3802b2bc`. Downloaded report artifact
10532396046 verified ZIP SHA-256
`295f5ed7be0f17c574516ae45c6e6c8aca5d62a1fea46c5f4ca3fbe744f440cd`.
The complete report is byte-for-byte identical to the local result, SHA-256
`0cfd41d4526f5911b5d70d51eb4309e9adc392ca35203fecea5ee62d7bc6934e`.
All 441 occurrences, exact original snapshots and P4 state remain unchanged.

The five-file diff was reviewed with no outstanding review requests; main had not
advanced. The authorized merge used the exact expected head. [Post-merge validation
35307317850](https://github.com/Vasuki8/IPO-Tracker/actions/runs/35307317850) also passed.
[Pages 35307316718](https://github.com/Vasuki8/IPO-Tracker/actions/runs/35307316718)
successfully deployed the merge. [Live acceptance 35307372609](https://github.com/Vasuki8/IPO-Tracker/actions/runs/35307372609)
passed on its first attempt: 1,366 local profiles consistent, 17 complete public
HTTPS responses matching the immutable commit and `reviewedPublication.status=passed`
for the retained Emmvee repair. The downloaded live artifact 10531752580 verified
SHA-256 `4e08004b12d4bfa7cbb723f97ea7f9e89b291f30b5ede2d1c97574bdc4f495cc`;
all expected public hashes also match the unchanged local public files.

The [release receipt](releases/2026-09-18-proposal-reconciliation.json) retains the
original live receipt, report hashes, CI and artifact bindings and exact limitations.
This reporting-only change did not trigger a new browser journey suite or source
collector; no new browser/PDF source-audit pass is claimed. No public rendering or
dataset bytes changed. All acceptance criteria for this report milestone are
complete. Classification is not an audited proposal resolution; that remains work.

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
proposal (baseline input index 133, original run `35204652736`) against the released
composition proofs and its original source context. Select it by retained fingerprint
`15558bebf1ac545501558352946b9104ebf2ce62d499024ae295e783f725c15c`, not by a
mutable array position alone. Its allocation differences exceed the composition
repair, so the complete proposal must not be declared superseded on that repair
alone. Record an evidence-backed decision separately; do not delete the proposal
or reopen Teamtech/P5. Subscription triage and overdue-update monitoring follow.

Earlier verified release receipts and detailed recovery evidence remain in
`docs/releases/` and [the immutable prior status](https://github.com/Vasuki8/IPO-Tracker/blob/800405b1c19c1c61367eb17b62bf5367267a0f70/docs/PROJECT_STATUS.md).
