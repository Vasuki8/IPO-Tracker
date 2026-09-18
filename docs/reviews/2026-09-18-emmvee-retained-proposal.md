# Emmvee retained document proposal: do not apply as proposed

Review time: `2026-09-18T04:49:59.562981+00:00`. Decision scope: one exact retained proposal,
not a canonical data correction, new PDF audit, or resolution of P4 source work.
Reviewed accepted baseline: `71bec048515b3b1fae2232b5640dac3a55ee7c3b`;
canonical value/proof publication: `3834c7323fc7ae794526942f649d128c209a4997`.

## Decision

**Do not apply this atomic proposal as proposed.** It carries forward the rejected
composition and withdraws an allocation group whose source-proof gap has since
been repaired. This is not a decision that the entire proposal was applied or
superseded, and it is not a rejection of the historical safety quarantine.
The original occurrence stays `pending_conflict_review`, with its complete base,
proposed snapshot, fingerprint and audit history intact. No numerical value,
source-review item, availability decision or phase gate is changed by this note.

The operator report may display this advice only while the exact proposal, issuer,
accepted document group and display holds still match. A changed proof, source
clock, review state or identity makes the note require revalidation. The ordinary
policy enforcement check clock is the only normalized clock. An independent
subscription update does not change the reviewed document group. The note is not
read by the publisher and cannot authorize or prevent publication by itself.

## Original collection recovered and checked

Original run: [35204652736](https://github.com/Vasuki8/IPO-Tracker/actions/runs/35204652736).
Artifact `10489143505`, `ipo-collection-35204652736`, downloaded and verified:

- ZIP SHA-256: `ca493aca0d1ae0b2b40797902378803b732c84b063c15a1a74ec4574b8193923`.
- Actual `source-commit.txt`: `e2ab245533ed790c50bfd40a14cfb93c6fda2fd3`.
- Base file SHA-256: `a46163a9bde56d02dde0261f95f025b6a4c2c93cff1c89c64f548e2837778f01`.
- Proposed file SHA-256: `42d0a0249bac0b847c2da1e341ef3bd2eda13fc4cc470449652fa26936d31b5c`.

Every field of both retained document snapshots equals the corresponding field in
the original artifact; the original issuer, symbol and 2025-11-11 offer date agree.
The preserved proposal fingerprint is `15558bebf1ac545501558352946b9104ebf2ce62d499024ae295e783f725c15c`; its full occurrence SHA-256 is
`e55de865b3cbd32a0759ae3ed87e081c3100a8f35e0b218d5a89000cf499cddb`. Index 133 is only a baseline locator, never an identity key.
Its base/proposed group hashes are `98fa8abeb9ef23507ff176e803bb51e7b765ee5f70a274e9872486c82ded8eea` and
`6e179489211246164c158da55b883eed1f5a0c303805d7cf98d92a46793c6f33`. No original collector manifest was relabelled.

## Findings against retained, already accepted evidence

**Composition.** The proposal carries the same rejected composition as its base:
34,845,069 fresh shares, 17,422,535 OFS shares, and INR 378.069 crore for each
component. Current accepted evidence instead supports 98,795,483 fresh shares /
INR 2,143.862 crore, 34,845,069 OFS shares / INR 756.138 crore, and INR 2,900 crore
total. All four values equal their complete retained proofs. The source's offer
clauses and Basis of Allotment qualification remain unchanged; no new final
allotment outcome is asserted.

The accepted composition artifact is
`data/reviewed_correction_evidence/emmvee.json`, SHA-256
`1f8b7ae600da76ea9f62a9771377925d17be3c5d98ebc8080e36b63a9a5795cf`, Git blob
`5ca3afdf6207c86fbea6f3e5ab236dde6c2fec45`. The
[original complete-source execution record](https://github.com/Vasuki8/IPO-Tracker/blob/5a63a93dd9f782e3bc9ec853c937fb29661108f4/docs/reviews/2026-09-18-source-review/2026-09-18-source-review-409c51c9.md)
and [actual released delivery receipt](../releases/2026-09-18-reviewed-release-acceptance.json)
remain separate evidence. Their original times are not replaced by this review time.

**Objects of the issue.** The original base has a four-row legacy extraction,
including two truncated narrative fragments. The proposal sets `objectsOfIssue`
to null, removes its old field proof and records a source-evidence-required
quarantine. That was a safety withdrawal, not a proposal to publish a new set of
allocations. The current record contains two source-bound rows: debt/interest
repayment for the issuer and EEPL, and general corporate purposes. Its retained
physical-page-21 table proof locates INR 16,212.94 million and INR 4,387.11 million,
with net proceeds of INR 20,600.05 million. The normalized amounts sum to the
quoted net total: 1,621.294 + 438.711 = 2,060.005 crore. Exact source lines, spans,
unit, page and table total remain in the accepted proof, not copied into a new
unverified extraction. That complete proof's semantic SHA-256 is `f766e7e8cd3cb2be891d1132a6958631920443527e0628489e4af6a013691503`.

The retained objects proof is parser 31, checked at `2026-09-17T14:28:13+05:30`;
the reviewed composition proof is parser 33, checked at
`2026-09-18T00:37:05.669681+00:00`. Both bind the same 2025-11-14 Final Prospectus,
NSE source URL and PDF SHA-256
`85eb9319dc01027821813c71d3702164911442a14547ad72cc04270ea6612eda`.
Existing evidence validators and public projections were reused; all five reviewed
fields are currently `final_verified`. This note neither upgrades their authority
nor establishes that every disclosure in that PDF is correct.

**Other document fields.** Lead-manager/registrar values are unchanged; extraction,
proof and review envelopes differ. No new acceptance of those envelopes, unresolved
financial information, or other issuers is made. The atomic proposal cannot be
partially replayed by discarding its conflicting composition or audit fields.

## Reproducibility and limitations

Accepted group hash including every clock: `68af587565a9193c22db4b26ddbee130efbb5102248d2726d37d838b126ea047`.
Accepted group hash excluding only `staticSourcePolicy.checkedAt`: `e599bf3b0ed16f6a19446ae06f3e954a9ad2ddc8427d277afb8e9e13c235b1b9`.
The decision ledger binds the latter, the full proposal, exact issuer/offer and
display-hold bytes, as well as this note's exact bytes. The original occurrence
also remains available at the pinned baseline's `data/pending_updates.json` after
the temporary Actions artifact expires.

A fresh NSE PDF fetch in this session failed: the web reader rejected its
11,360,516-byte length and direct download failed. No fresh PDF rendering,
new full-document review, or substitute secondary-source confirmation is claimed.
The decision reuses immutable accepted evidence and checks the original collection
history; it cannot establish newly disclosed figures. No PDF copy is added to the
repository. Existing data/document redistribution permissions remain unresolved.

To reproduce the read-only binding check, run `uv sync --frozen`, then
`uv run --frozen python tools/reconcile_pending_updates.py` and inspect the review
with ID `emmvee-retained-document-2026-09-18`. Its action is advice only;
`resolutionChanged` and `resolutionsApplied` remain false/zero. Keep the note when
it becomes stale and append a newly reviewed event instead of silently revising it.

Next independent repair work: classify retained subscription snapshots using
source authority and separate observation/collection clocks, preserving every
proposal. P4, Teamtech's hold and draft #105 remain unchanged.
