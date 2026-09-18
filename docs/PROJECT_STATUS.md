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

## Current milestone — reviewed Emmvee proposal, 18 September 2026

Starting main is `71bec048515b3b1fae2232b5640dac3a55ee7c3b`, tree
`7fa926362879790f54a473c02829a0612617381b`. Main has not advanced since the
last checkpoint. #119's reconciliation tool and #120's release checkpoint are
complete. The existing Pages deployment 35307749331 and live acceptance
35307777409 succeeded. Canonical publication remains `3834c732`.

### Implemented on `feat-emmvee-proposal-review`

The next unfinished item was the retained Emmvee document proposal, fingerprint
`15558bebf1ac545501558352946b9104ebf2ce62d499024ae295e783f725c15c`, original run
`35204652736` (baseline index 133). Recovered that run's exact collection artifact
10489143505 and verified ZIP SHA-256
`ca493aca0d1ae0b2b40797902378803b732c84b063c15a1a74ec4574b8193923`.
Its original source commit is `e2ab245533ed790c50bfd40a14cfb93c6fda2fd3`.
Every retained base/proposed document field equals its original artifact field;
issuer, symbol and offer identity also agree. No old manifest was relabelled.

[The evidence review](reviews/2026-09-18-emmvee-retained-proposal.md) records
**do not apply as proposed**. The original proposal carries the rejected
composition and withdraws the legacy allocation list for missing source proof.
The current accepted group has the separately reviewed composition and a two-row,
source-table-bound allocation proof. The old quarantine was a valid historical
safeguard, not an allocation correction to reapply over supported current evidence.
This decision does not declare the entire proposal applied or superseded.

The operator report now attaches the review only to the exact fingerprint, full
proposal hash, original run, issuer/offer identity, accepted document group and
display-hold bytes. Current public verification must still support the reviewed
fields. Changed proofs, values, source clocks, holds or identities require review
again. Only the policy-enforcement check clock is normalized; unrelated subscription
updates survive. Reordered/duplicate occurrences and unmatched historical reviews
remain visible; no latest-review-wins rule is introduced.

Review events live in `docs/reviews/pending-proposal-decisions.json`; the referenced
note is hash-bound. Missing or altered notes and malformed ledgers fail closed.
The report's freshness check includes ledger/evidence bytes. This is operator
advice, not publication authority: **all 441 proposals retain their original
pending status**, the 159 conflicting document groups and 282 unassessed items
remain counted, and no canonical, proposal, source-review or gate data changes.

### Tests and remaining release acceptance

Eleven new regression tests pass locally through uv, including stale evidence,
identity/run/payload changes, unchanged source clocks, reordered duplicates and
preservation of all input work. Eight Node public-quality tests pass. Strict
validation reports zero errors and the same 1,596 reviews. All 1,366 profiles and
the directory rebuild without changes; the local reviewed-delivery verifier and
deterministic report replay pass. The complete local run attempted 1,062 tests;
three failed only because the Pages artifact omits `.github/workflows/` needed by
existing workflow tests. This is **not a full local suite pass**. Local frozen
sync lacked locked packages; tests used uv with available Python 3.13.5 and
requests 2.32.5 / pypdf 5.9.0. Require frozen full-repository CI before merging.

Fresh NSE PDF retrieval was unavailable: the web reader rejected its 11,360,516-byte
length and direct download failed. This is a review of the original collection
and immutable accepted field evidence, **not a new full-PDF audit**. No new PDF,
secondary-source substitute, numerical correction or parser rollout is included.
The prior source-review timestamp, URL, PDF hash, source rows/units and correction
history remain unchanged. The detailed note records the exact evidence bindings.

The working copy is a separate, locally labelled mirror of checksum-verified
Pages artifact 10531947746, not remote Git history. Original archives were preserved;
no prior working tree survived. Direct Git access failed DNS. Authenticated GitHub
read/write/release actions are used only with their actual returned evidence.

Remaining for this branch: review the complete diff, pass frozen GitHub validation,
inspect and compare its retained reconciliation report, merge with the exact head,
verify Pages/live acceptance and record final commit/run IDs. No release is claimed
by this pre-merge status.

### Gate, blockers and next task

P4 remains incomplete: 387 actionable and 51 higher-priority records; 1,596 total
source reviews, 1,592 blocking, four P5-only and zero unmapped. P5/performance
expansion remains gated. Teamtech remains held. Draft #105 remains unaccepted at
`5a63a93dd9f782e3bc9ec853c937fb29661108f4` (source code freeze `409c51c9`), with
#94/#98/#99/#104 preserved. No broad preview or historical candidate is promoted.
Commercial source rights, audience, pricing and privacy decisions remain unresolved;
no spending, contracts, outreach, tracking, billing, permissions or infrastructure
changes were introduced. No rights are inferred from retained official evidence.

**Next concrete task after this release:** extend the read-only reconciliation tool
to `subscriptionSnapshot` proposals, comparing complete source-bound snapshots,
official/secondary authority and observation versus collection clocks. Preserve all
proposals and avoid newest-writer-wins resolution; do not publish or expand P5.
Overdue-source/publication detection follows that bounded classification work.

[Previous verified status and receipts](https://github.com/Vasuki8/IPO-Tracker/blob/71bec048515b3b1fae2232b5640dac3a55ee7c3b/docs/PROJECT_STATUS.md)
remain immutable. See [operator guidance](PROPOSAL_RECONCILIATION.md).
