# Project status and release evidence

## Standing product and data requirements

IPO Tracker is intended to become a public commercial product. Customer segment,
pricing and revenue model remain undecided. Preserve trust, accessible mobile
research, stable URLs, privacy and sustainable operating costs. Keep the light
static architecture. No new spending, contracts, outreach, tracking, billing or
material access changes without owner approval. Sponsorship must be identifiable
and cannot influence factual verification or research rankings. See
[COMMERCIAL_READINESS.md](COMMERCIAL_READINESS.md).

Completed static terms require matching Final Prospectus field evidence. Active
provisional disclosures and official market observations must remain labelled.
Preserve source URLs, document identity, dates, units, nulls, separate source and
collection clocks, quarantines and correction history. P4 remains incomplete;
P5 and performance coverage expansion remain gated. See [ROADMAP.md](ROADMAP.md),
[OPERATIONS.md](OPERATIONS.md) and [REVIEWED_PUBLICATION.md](REVIEWED_PUBLICATION.md).

## Verified checkpoint — 18 September 2026, 03:24 UTC

**The bounded Emmvee value/proof repair is merged, published and live-verified.**
Latest verified data release: `3834c7323fc7ae794526942f649d128c209a4997`, tree
`fa76fd3ab807addbc1dbe42188e8d003a887cffe`. This checkpoint documentation follows
that release; it does not publish additional IPO facts or change the collector.

| Increment | Actual evidence |
| --- | --- |
| Code [#115](https://github.com/Vasuki8/IPO-Tracker/pull/115) | Branch `fix-reviewed-composition-evidence`, reviewed head `9ada81b07158ea72e597d18731fe9fde694c8304`, merge `8a2ab9d266c7f7e9a4bcc606e9fccf2397b423d4` |
| Request [#116](https://github.com/Vasuki8/IPO-Tracker/pull/116) | Branch `release-emmvee-reviewed-proof`, head `bacff4f2670fa327791a440c88f48e3c4abef5f5`, merge `20d542fcde8b085a49b5443051a7647c624b5680`; changes exactly one request file selecting Emmvee |
| Publisher | [35302828628](https://github.com/Vasuki8/IPO-Tracker/actions/runs/35302828628), both jobs successful; actual `mode=reviewed`, `reviewedIds=[emmvee]`, 441 pending proposals |
| Data output | `3834c7323fc7ae794526942f649d128c209a4997`, parent `20d542fcde8b085a49b5443051a7647c624b5680`; ten generated/data/report files changed, one canonical issuer changed |
| Pages | [35302925923](https://github.com/Vasuki8/IPO-Tracker/actions/runs/35302925923) successfully deployed the data commit |
| Actual public acceptance | [35302956384](https://github.com/Vasuki8/IPO-Tracker/actions/runs/35302956384), status passed; 1,366 local profiles consistent and 17 complete HTTPS responses matched the immutable deployment |

The actual bundle, final Pages artifact and live receipt were downloaded and
SHA-256 verified. [The retained release receipt](releases/2026-09-18-reviewed-emmvee.json)
records their IDs/hashes, complete live inventory, snapshot hashes, source commit,
exact publication scope, proposal preservation and unchanged P4 gate.

### What changed and why

The earlier #114 registry repair accepted Emmvee's numbers, but the subsequent
normal refresh retained the rejected legacy field proofs. The public projection
correctly withheld the mismatch. The previous chat handover's completed one-record
release and historical documentation #115 were not established: #115 did not exist
at this session's beginning. **This milestone created the actual code #115 and
completed the missing evidence/publication work.**

All four composition fields now have matching Final Prospectus evidence and public
`final_verified` states. The published values are ₹2,143.862 crore fresh issue plus
₹756.138 crore OFS = ₹2,900 crore total; 98,795,483 fresh shares and 34,845,069 OFS
shares. The compact profile intentionally stores amounts in their separate aliases
rather than duplicating them inside its share-composition object.

Compared with the accepted release baseline, only Emmvee's `staticFieldProvenance`,
`staticSourcePolicy` and one appended proof-history event changed. Amounts were
already corrected before this publication. The complete published IPO record list
matches the approved proposal. All **1,365 other records** remain equal, including
Teamtech. Existing Emmvee allocations, their full document proof, unrelated source
proofs and prior correction history are unchanged. All **441 pending proposals**
remain byte-for-byte unchanged; pending-file SHA-256 is
`ed4b1ae67dfc0b9a9a92090749e24c631933a884a92e6fe9576a6af1f8ba68a3`.
The generator rewrote one profile and the compact directory, not 1,366 profiles.

### Dependable publication path

The four-field composition and proof group is bound to exact issuer/offer identity,
accepted correction values, old-proof hashes and the immutable reviewed proof file.
Divergent current values or evidence reject the whole group. Original proofs remain
in an append-only audit. Reapplication does not duplicate the proof event.

The existing single serialized publisher now supports explicit offline `reviewed`
mode. Before any writes it checks original source-commit policy, snapshot hashes,
before-value/proof preconditions, the exact permitted transition, strict validation
and all four public verification decisions. Rehashing an arbitrary proposal does
not authorize it. Concurrent document changes fail closed; independent subscription
updates survive. Reviewed publication never rewrites pending-proposal bytes.

The current connector cannot dispatch workflows. The verified alternative is a PR
changing **only** `data/reviewed_publication_request.json`. #116 used that route;
it selected reviewed mode, skipped source collection and residual extraction, and
retained the actual request and source commit in its bundle. A mixed request/code/
data/docs push fails closed rather than starting broad collection. No new writer,
permissions, token or service was introduced. Commands and recovery are in
[REVIEWED_PUBLICATION.md](REVIEWED_PUBLICATION.md).

The code-merge ordinary repair run [35302740755](https://github.com/Vasuki8/IPO-Tracker/actions/runs/35302740755)
was cancelled during source collection. Its residual, snapshot and artifact steps
were skipped; its publisher has no executed steps. No output from it was accepted.
This cancellation coincided with the later request push and existing concurrency;
the causal cancellation annotation was not independently inspected. The successful
reviewed run above, not that ordinary run, produced this release.

### Tests and source checks

- [Final frozen validation 35302397273](https://github.com/Vasuki8/IPO-Tracker/actions/runs/35302397273): **1,027 Python regressions** through uv/Python 3.12, including 20 new evidence/publication/request tests; strict validation and compact/generated checks passed. [Request validation 35302779252](https://github.com/Vasuki8/IPO-Tracker/actions/runs/35302779252) also passed before its merge.
- [Final browser checks 35302397121](https://github.com/Vasuki8/IPO-Tracker/actions/runs/35302397121): **25 existing journeys**, **eight Node checks**, freshness text bounds at **1440/375/320px**, 1,366-profile consistency and 17 loopback files passed. A separately served real candidate also passed directory, CSV, comparison, responsive profile and Teamtech-hold acceptance, with no page errors or large canonical-dataset fetches. Its final downloaded artifact hash is retained; an initial candidate mobile screenshot was visually inspected.
- Publication replay and adversarial tests cover stale/missing/changed source proofs, mismatched issuer/offer, tampered or incomplete groups, unsafe proof paths, duplicate/unreviewed IDs, missing source manifests, concurrent document changes, rehashed arbitrary snapshots, fabricated audit events, history loss, idempotence and preserved independent subscriptions.
- Actual published records were compared with the retained base and proposal. All 17 deployed receipt hashes match the downloaded Pages artifact. The actual profile and compact directory expose the accepted Emmvee values; Teamtech's actual published profile remains `under_review` with allocations withheld.

This is **reuse of exact previously reviewed source evidence**, not a fresh full-PDF
review or parser rollout. The proof file from #105 at
`5a63a93dd9f782e3bc9ec853c937fb29661108f4` has Git blob
`5ca3afdf6207c86fbea6f3e5ab236dde6c2fec45`, SHA-256
`1f8b7ae600da76ea9f62a9771377925d17be3c5d98ebc8080e36b63a9a5795cf`.
Its original check time `2026-09-18T00:37:05.669681+00:00`, parser-33 lineage,
physical page-3 million-denominated clauses, normalized units, document date and
PDF hash `85eb9319dc01027821813c71d3702164911442a14547ad72cc04270ea6612eda`
are retained unchanged. [Original review](https://github.com/Vasuki8/IPO-Tracker/blob/5a63a93dd9f782e3bc9ec853c937fb29661108f4/docs/reviews/2026-09-18-source-review/2026-09-18-source-review-409c51c9.md).
The prospectus Basis of Allotment qualification is not a claim of a later outcome.

Local frozen dependency installation failed DNS, and local Chromium navigation was
administratively blocked. Local uv/Python 3.13 tests are not represented as a local
frozen or browser pass; actual frozen/browser acceptance came from GitHub CI.
Complete served-byte matching is not an all-profile live-browser audit, a feed-
freshness guarantee or proof that every unresolved source value is correct.

## Current gates and remaining work

At the published data commit, P4 remains incomplete: **387 actionable records and
51 higher-priority records**, zero semantic errors, **1,596 reviews / 1,592 blocking
P4 / four P5-only / zero unmapped**. Final-document revalidation is 321 records /
1,173 fields, plus 29 higher-priority records / 107 fields. Five evidence-backed
resolved-unavailable records remain. These cohorts overlap. P5 remains
`waiting_for_p4` with 914 actionable records. This evidence repair did not lower
source-review counts or remove unresolved work. No performance coverage expanded.

[#105](https://github.com/Vasuki8/IPO-Tracker/pull/105), branch
`fix-p4-reviewed-integration`, was rechecked and remains draft at
`5a63a93dd9f782e3bc9ec853c937fb29661108f4`; source freeze
`409c51c939bd839940594278d324016766cb84c6`. The completed separate Emmvee release
is recorded on its conversation. Its broad parser and diagnostic datasets remain
UNACCEPTED. Preserve #94/#98/#99/#104 original branches and diagnostic recovery;
do not merge them solely on green tests. Teamtech still has contradictory units
(page 89 crores versus lakhs elsewhere); no assumed typo or estimated reconciliation
is accepted. Other unresolved document holds are unchanged.

Commercial collection/redistribution/display rights, hosting suitability, customer
validation, pricing, privacy measurements and professional jurisdiction review
remain unresolved. No spending, contracts, external source outreach, new providers,
accounts, tracking, payments or access expansion were activated by this work.

## Exact next task and continuity

Start a **read-only reconciliation report for all 441 retained proposals** against
the current accepted records and matching evidence. Preserve every original
fingerprint, proposal payload, run/source lineage and unresolved status. Separate
already-applied, still-conflicting, stale-source-policy and missing-identity cases;
route each remaining case to explicit repair/review work. Do not auto-promote or
delete proposals. Follow with evidence-backed reconciliation actions, overdue-
update detection and the next bounded P4 source batch. Keep P5/performance gated.

No Emmvee release acceptance remains outstanding at this data checkpoint. Final
checkpoint documentation is maintained on `docs-reviewed-emmvee-release` and must
pass its own normal PR/deployment workflow. #115 and #116 branches are preserved;
#105 remains the active blocked source integration. Re-read actual main and
publication status before starting another batch.

The roadmap's dated audit and earlier headline counts are historical; current
numbers and acceptance above take precedence. The preceding full checkpoint is
preserved at [3c948d3b](https://github.com/Vasuki8/IPO-Tracker/blob/3c948d3b2eeea0c7b446693a4fa6a418d23caa50/docs/PROJECT_STATUS.md),
and earlier release receipts remain under `docs/releases/`. Do not repeat released
trust/freshness, document-hold, review-routing or Emmvee-publication work.
