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

## Current execution — subscription proposal triage, 18 September 2026

Starting main is `09a570f52d99d6eb5752c112e7ea34722c341917`, tree
`143342838d03956144ddef32eea74532602868a4`. The initial current-main read and
open-PR delta query found no advance since #122. Its Pages deployment
35309924949 and live acceptance 35309960677 succeeded. #121's evidence-bound
Emmvee advice is complete and remains applicable; its correction is not repeated.

### Implemented: complete subscription-snapshot reconciliation

Branch `feat-subscription-proposal-triage` extends the existing read-only report.
Problem: subscription conflicts were unassessed, and a newer collection timestamp
or an exchange-sounding label cannot establish a newer, authoritative observation.
Affected users are repair operators and, indirectly, researchers relying on
consistent public subscription figures and freshness labels.

Acceptance: compare the publisher's complete `subscriptionSnapshot` group, preserve
every occurrence and all input bytes, separate observed and collected times,
identify missing/invalid source bindings, and never apply or resolve by recency.
The shared public projection supplies numeric/review states and authority
classification on isolated copies. Today's attached sources/history are not spliced
into older proposals. Raw clock strings remain retained; separate comparisons use
explicit timezone-aware instants. Collection-only and legacy AsOf clocks never
become source observations. Final subscription is not inferred from a closing date.

Report schema 2 adds snapshot diagnostics and separate subscription counts. The
existing exact-input/policy replay rejects old or changed reports. Document
classification, the immutable Emmvee note/ledger and all prior review decisions
are preserved. Unknown proposal families remain visible, not excluded. See
[operator guidance](PROPOSAL_RECONCILIATION.md).

Measured against this accepted snapshot: **441 retained proposals**, **159 document
groups still conflicting**, **22 subscription groups still conflicting**, and
**260 other-family proposals explicitly not assessed**. All 22 subscription
proposals lack a snapshot-bound URL; 14 name BSE but cannot establish authority
from their stored group alone. Eight carry secondary-source labels and older
observation timestamps; the other 14 have no comparable source observation.
None is automatically superseded. These are triage findings, not new confirmed
source errors, resolutions or improvements in P4 completeness.

### Verification and release boundary

**16 new subscription tests** and **11 existing advice tests** pass locally through
uv, covering complete categories, zero/null/false, source changes, spoofed hosts,
missing URLs, two independent clocks, offset normalization, invalid/naive times,
legacy aliases, duplicate proposals, retained reviews and non-final intraday data.
Eight Node public-quality tests pass. All 1,366 profiles rebuild with zero changes;
strict validation has zero errors and 1,596 reviews. The report is deterministic,
and all 159 document entries plus Emmvee's advice match the prior CI report exactly.
All 441 proposal identities/statuses/hashes and canonical/phase data are preserved.

Local frozen sync lacked locked packages. Local uv tests use Python 3.13.5 with
available dependencies, not a frozen pass. The full local attempt before the final
category regression ran 1,077 tests with three errors because the Pages mirror
omits existing workflow files; it is not claimed as a full-suite pass. Require
complete-repository frozen CI, retained-report inspection, exact-head merge,
Pages and live-byte acceptance before declaring this branch released.

No original working tree survived; existing ZIPs were left untouched. The separate
local mirror comes from Pages artifact 10532438782, verified SHA-256
`111bd5e6e3c719982d3cfc5fadf83a36d0a53e1f0630061fec6201f6db9ab406`.
Direct Git access failed DNS. Authenticated GitHub actions remain the remote
read/write/release path. The mirror's local Git history is explicitly not remote
history. This increment adds no source collection, dependency, workflow writer,
public payload, browser journey change, tracking, account or paid service.

### Gate, blockers and next task

P4 remains incomplete: **387 actionable + 51 higher-priority records**, **1,596**
total reviews, **1,592** blocking, **four** P5-only and **zero** unmapped. P5 and
performance expansion remain gated. Teamtech remains held. Broad parser draft
#105 remains unaccepted at `5a63a93dd9f782e3bc9ec853c937fb29661108f4`, with
#94/#98/#99/#104 and code freeze `409c51c9` preserved. No data/source decision was
made for those branches. Commercial rights, audience, pricing and privacy remain
unresolved; no spending, contracts, outreach or material access changes occurred.

**Next task after this release:** add a read-only overdue-source/publication report,
using actual stage outcomes, last accepted publication and per-source observation
versus collection clocks. Missing observation times must remain unknown, not fresh.
Keep stale/failed/deferred collection distinct from publication delay; do not add
alerts or another writer. Retained subscription proposals need original collection
URL/issuer evidence before any audited disposition; their comparison alone is not
resolution authority.

[Previous verified status](https://github.com/Vasuki8/IPO-Tracker/blob/09a570f52d99d6eb5752c112e7ea34722c341917/docs/PROJECT_STATUS.md)
and `docs/releases/2026-09-18-emmvee-proposal-review.json` preserve the earlier
release and concurrent filings update `61360716`. Immutable source reviews,
correction history, retained proposals and the commercial register are unchanged.
