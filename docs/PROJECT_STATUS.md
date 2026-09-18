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

[PR #121](https://github.com/Vasuki8/IPO-Tracker/pull/121) is merged and live at
`3bb08735dfb114bbba08a622df50fce88274defa`, tree
`126c240dc0773b942f02f48ccff3662477ae8cb7`. Reviewed head was
`9d6ad3ae783bbd97888fd95d299d51b00f11ae40` on `feat-emmvee-proposal-review`.
This documentation-only closeout on `docs-emmvee-proposal-review-checkpoint`
records the completed milestone; no second implementation milestone is included.

### Recovered starting point

Starting main is `71bec048515b3b1fae2232b5640dac3a55ee7c3b`, tree
`7fa926362879790f54a473c02829a0612617381b`. Main had not advanced at the initial checkpoint read. #119's reconciliation tool and #120's release checkpoint are
complete. The existing Pages deployment 35307749331 and live acceptance
35307777409 succeeded. The accepted Emmvee composition repair remains the earlier `3834c732` lineage.
A subsequent routine filings publication is reconciled separately below.

### Completed: evidence-bound review of the retained Emmvee proposal

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

### Tests and source-check limitations

Eleven new regression tests pass locally through uv, including stale evidence,
identity/run/payload changes, unchanged source clocks, reordered duplicates and
preservation of all input work. Eight Node public-quality tests pass. Strict
validation reports zero errors and the same 1,596 reviews. All 1,366 profiles and
the directory rebuild without changes; the local reviewed-delivery verifier and
deterministic report replay pass. The complete local run attempted 1,062 tests;
three failed only because the Pages artifact omits `.github/workflows/` needed by
existing workflow tests. This is **not a full local suite pass**. Local frozen
sync lacked locked packages; tests used uv with available Python 3.13.5 and
requests 2.32.5 / pypdf 5.9.0. The complete-repository frozen CI subsequently passed; see below.

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

### Verified CI, release and concurrent automation

[Frozen PR validation 35309035968](https://github.com/Vasuki8/IPO-Tracker/actions/runs/35309035968)
passed the full regression suite using Python 3.12 and `uv sync --frozen`, report
replay/input-preservation checks, strict validation and generated/support checks.
Its actual test merge was `dcf43a15b171b878b2c91a1b356b35db1ac5622e`.
The downloaded report artifact 10533095128 matched ZIP SHA-256
`149d164deaed4d10da7703dc50792b71beaa7713a2ed62d733003dc71880cbcc`;
the complete report matched the local result byte for byte, SHA-256
`ed5bd99fb60e41fc9e94cdba08c00a60e2b58947e35f5d926564febd37b2b3f4`.
The reviewed tool, tests and immutable note blobs matched the tested local bytes.
The authorized merge used the exact expected head and no protection changes.

**A concurrent automatic update is preserved.** Existing filings run
`35309048100` published `61360716df53507128266eebe330cf0273038c84` shortly before
the merge. This refreshed all policy-check clocks and changed 36 records beyond
that clock, plus four generated profiles. These are not changes made by the
five-file review-only PR. No new source adjudication of those unrelated facts is
claimed. All 441 pending proposals remain byte-identical. Emmvee and Teamtech are
unchanged apart from their policy check clock; Emmvee's amounts, complete proofs,
allocations and the Teamtech hold remain intact. Current canonical SHA-256 is
`ecc71c4b53f87178c20e0b1708322a9399da66d22272c6d5e5cc62fd8335672f`.

[Post-merge frozen validation 35309364538](https://github.com/Vasuki8/IPO-Tracker/actions/runs/35309364538)
also passed on the combined tree. Its downloaded report artifact 10532925972 was
hash-verified and replayed locally against the newly deployed data. The decision
remains **applicable**, with one bound occurrence and zero resolutions. All counts
and original statuses remain unchanged; this is not an implicit source acceptance.

[Pages 35309363825](https://github.com/Vasuki8/IPO-Tracker/actions/runs/35309363825)
successfully deployed the merge, and [live acceptance 35309396845](https://github.com/Vasuki8/IPO-Tracker/actions/runs/35309396845)
passed on the first attempt. The checksum-verified deployed archive and live
receipt agree on 1,366 local profile checks and 17 complete public HTTPS responses.
The current ordinary filings publication correctly yields
`reviewedPublication.status=not_requested`, not a reviewed-repair pass; the
current Emmvee evidence binding passed separately in the operator report.
No new browser journey suite ran for this operator-only change. The previous
light presentation and all source/display rules are preserved.

[The release receipt](releases/2026-09-18-emmvee-proposal-review.json) retains exact
CI, artifact, original collection, live-response and concurrent-update evidence.
Implementation and release acceptance for #121 are complete. The operating guide
now documents advice applicability, stale/unmatched reviews and their non-resolving
boundary. Original snapshots and the immutable audit note remain untouched.

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
