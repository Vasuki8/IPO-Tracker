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

## Reconciled checkpoint — 18 September 2026

Actual published main at this implementation baseline is
`3c948d3b2eeea0c7b446693a4fa6a418d23caa50`, tree
`afb2c1854485dc669ab09b1b26942b187132a72c`.
PR #114 merged as `e59b9735305425f99a9b87f5ea0bf0a12c09c3c1` and changed only
`data/verified_corrections.json`. Its normal refresh [35298017157](https://github.com/Vasuki8/IPO-Tracker/actions/runs/35298017157)
subsequently published the bot commit above. [Pages 35299431541](https://github.com/Vasuki8/IPO-Tracker/actions/runs/35299431541)
and [live acceptance 35299463384](https://github.com/Vasuki8/IPO-Tracker/actions/runs/35299463384)
succeeded. The downloaded Pages artifact 10528823983 matched SHA-256
`1ba53184f3ce6907c5a7e0ebb9ded03e34dad619bc85c38fa9af670d29e14903`;
release artifact 10529153179 matched
`50924b236e434feba2c4bad6fdc22f5aabc938c207890a68c57b7a73d9cbcd1d`.
The latter checks 1,366 local routes and 17 full live HTTPS responses, not source accuracy.

**Previous handover correction:** #114 did not itself publish canonical data or
matching field proofs. PR #115 did not exist when checked at this session's start;
no preceding #115 documentation merge is established. The normal refresh changed
77 files, including unrelated routine updates, so it was not an Emmvee-only release.
Those updates are retained as the new baseline. Emmvee's amounts are now correct,
but its field proofs still contain the rejected legacy composition. Public views
correctly withhold this mismatch. Finishing the value/proof repair is the earliest
unmet milestone, before claiming an accepted public numerical repair.

The trust/freshness contract, display holds, source-commit guard, presentation
routing and complete source-review routing (#100–#113) are already released.
Their detailed history remains in [the immutable prior status](https://github.com/Vasuki8/IPO-Tracker/blob/3c948d3b2eeea0c7b446693a4fa6a418d23caa50/docs/PROJECT_STATUS.md)
and `docs/releases/`; old receipts are not rewritten.

Current baseline: 1,366 records; P4 incomplete with 387 actionable records and
51 higher-priority records; zero strict errors; 1,596 reviews, 1,592 blocking P4,
four P5-only, zero unmapped. There are 321 P4 final-document revalidation records /
1,173 fields and 29 higher-priority records / 107 fields. Five resolved-unavailable
records remain. All 441 pending proposals remain retained. These cohorts overlap.
P5 remains `waiting_for_p4` with 914 actionable records.

## Active milestone: bounded reviewed composition evidence

Branch `fix-reviewed-composition-evidence` is based on the baseline above. It does
not merge #105's broad parser changes or alter any canonical data in its code PR.

The correction applier pairs the complete four-field composition with its exact
retained proofs. Exact issuer/offer, before-value and before-proof checks reject
concurrent changes as a complete group. Previous proofs are appended to correction
history, not discarded. Already-correct amounts can receive matching proofs;
reapplication does not duplicate the audit. Other proofs and allocations stay intact.

The existing single serialized publisher gains explicit `reviewed` mode and
`reviewed_ids`. Preparation is offline, selected-record-only, and uses existing
correction and Final Prospectus policy checks. Publication rechecks snapshot
hashes, before-value/proof preconditions, the permitted transition, strict errors
and all four public verification states. A rehashed arbitrary proposal cannot
bypass the accepted transition. Document conflicts fail before any writes;
independent subscription updates survive. Reviewed mode never rewrites pending
proposal bytes or invokes source/residual collection. Regular modes remain intact.
The proof index and directory are protected source-policy dependencies.

### Evidence

The retained full-document review supports Emmvee's 98,795,483 fresh shares /
₹2,143.862 crore, 34,845,069 OFS shares / ₹756.138 crore, and ₹2,900 crore total.
Page-3 million-denominated clauses, units, exact rows and ₹217 offer price remain
in the proofs; the original Basis of Allotment qualification is not a later outcome.
The exact proof file from draft #105 at `5a63a93dd9f782e3bc9ec853c937fb29661108f4`
has Git blob `5ca3afdf6207c86fbea6f3e5ab236dde6c2fec45` and SHA-256
`1f8b7ae600da76ea9f62a9771377925d17be3c5d98ebc8080e36b63a9a5795cf`.
Its original check time `2026-09-18T00:37:05.669681+00:00`, parser-33 lineage,
PDF hash `85eb9319dc01027821813c71d3702164911442a14547ad72cc04270ea6612eda`
and document date are unchanged. [Original source review](https://github.com/Vasuki8/IPO-Tracker/blob/5a63a93dd9f782e3bc9ec853c937fb29661108f4/docs/reviews/2026-09-18-source-review/2026-09-18-source-review-409c51c9.md).
This is exact evidence reuse, not a fresh full-PDF review, new source download,
parser-33 rollout or acceptance of the broad diagnostic dataset.

Teamtech remains held: its prospectus says crores on page 89 where other pages say
lakhs. No assumed typo or estimated reconciliation is accepted. Its record and
all other unselected records/proposals are outside this correction scope.

### Verification and remaining acceptance

Before the final write-boundary hardening, 1,021 Python regressions passed through
uv using available Python 3.13.5; eight Node quality tests passed. Local frozen
installation failed DNS access to the locked packages, and Chromium navigation
returned `ERR_BLOCKED_BY_ADMINISTRATOR`. Neither a local frozen pass nor local
browser pass is claimed. Candidate generation rewrote one of 1,366 profiles and
its compact directory, preserving canonical input and the other 1,365 records.

The final branch adds publisher replay of the accepted transition and one further
adversarial test. Frozen Python 3.12 CI, actual browser checks and final diff review
remain required. Browser CI includes a separate candidate site for directory,
profile, comparison, CSV, three widths, and Teamtech's continuing hold, without
modifying committed canonical/pending data. No branch code is yet merged or deployed
at this pre-release checkpoint.

Remaining: complete CI and authorized merge; dispatch the existing refresh with
`mode=reviewed`, `reviewed_ids=emmvee`; inspect its retained bundle and actual
publication diff; verify unchanged pending proposals, Pages and live public output.
Record exact PR/head/merge/data commit and workflow IDs before declaring completion.

## Preserved work, blockers and next task

#105 (`fix-p4-reviewed-integration`) stays draft at
`5a63a93dd9f782e3bc9ec853c937fb29661108f4`, source code freeze
`409c51c939bd839940594278d324016766cb84c6`. Original #94/#98/#99/#104 branches
and diagnostic recovery evidence are preserved; no broad parser acceptance is
implied by green tests. Its old preview 35292625507 completion is not reverified
in this bounded milestone. P4 remains the gate.

After bounded Emmvee publication/live acceptance, finish retained-proposal
lifecycle/reconciliation and overdue-update detection alongside source-backed P4
batches. Keep unresolved items; never improve completion numbers by dropping them.
Commercial source/redistribution/hosting permissions, customer validation, pricing,
privacy measurements and professional jurisdiction review remain unresolved.
No new services, tracking, accounts, billing, spending, contracts or access changes.
