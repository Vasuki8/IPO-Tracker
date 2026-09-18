# Retained-proposal reconciliation: read-only triage and review advice

A pending proposal is not automatically a data error, an accepted correction or an
obsolete update. This report helps the operator compare it with current accepted
data. It never edits canonical data, changes a proposal's status, clears a source
review or advances P4/P5. Existing public verification rules remain authoritative.

## Run and inspect

```sh
uv sync --frozen
mkdir -p artifacts/proposal-reconciliation
uv run --frozen python tools/reconcile_pending_updates.py > artifacts/proposal-reconciliation/report.json
uv run --frozen python tools/reconcile_pending_updates.py --check-report artifacts/proposal-reconciliation/report.json
```

The utility prints to standard output only. Redirect to an artifact directory,
never over `data/ipos.json` or `data/pending_updates.json`. Optional `--data` and
`--pending` select isolated input snapshots; neither file is written. Assessment
uses the canonical snapshot's date in India, not the current wall clock. An
explicit `--as-of YYYY-MM-DD` is also supported and recorded.

The existing **Validate IPO changes** job retains a
`proposal-reconciliation-<run>-<attempt>` artifact with the report and its actual
checkout commit. Generation and freshness checks happen before CI's temporary
correction rehearsals. That job remains read-only and uses existing dependencies;
there is no new writer, schedule, source collection or paid service. Artifacts use
the existing fourteen-day retention convention. The report adds nothing to the
public directory payload or initial page load.

`--check-report` fails if the input bytes, display holds, reporting/source-policy
code or report content changed. A passing check establishes snapshot consistency,
not recent source observation or correct financial disclosures. Regenerate after
accepted data or policy changes. A commit label alone is not a freshness check.

## Read the results without resolving them

Every original occurrence receives `inputIndex`, its retained fingerprint/status,
a hash of the entire proposal, a comparison state and a next action. Duplicates
remain separate occurrences. Original snapshots, source URLs, dates, units and
correction history remain in the input file; the report does not duplicate rejected
figures into public-facing exports. Use its input hashes and index to retrieve the
exact retained evidence. Run IDs locate collection context; they never establish
source priority or permission to reuse an old collector manifest.

Complete `documentFields` and `subscriptionSnapshot` proposals are assessed in
report schema 2. The atomic field list is imported from the existing publisher, not maintained as a second
merge policy. Matching values with different proofs or review state are a conflict.
Extra current fields cannot be ignored to manufacture an already-applied result.
Absent keys, null, zero and false remain distinct; object key order and equivalent
JSON numbers such as 100 and 100.0 do not change the semantic comparison.

| Comparison state | Meaning and next step |
| --- | --- |
| `already_applied_exact` | The entire stored group equals current accepted data. This is **not** a source-verification pass or a resolution. Check evidence/reviews before recording a decision. |
| `policy_clock_only` | Only `staticSourcePolicy.checkedAt` differs. Source observation, proof and quarantine clocks are never ignored. |
| `base_unchanged` | Current group still equals the retained base. Revalidate source lineage and policy before any retry; it is not automatically publishable. |
| `still_conflicting` | The complete proposed group differs from both current data and its base. Inspect the value, proof, scope and review differences. |
| `no_change_proposal` | The proposal equals its original base. Inspect it; this is not a source repair. |
| `legacy_group_scope` | Unknown fields prevent comparison under the current group definition. Recover its original code/context or recollect. |
| `missing_record` / `ambiguous_record` | Resolve issuer/offer identity; no name-based match is attempted. |
| `malformed_proposal` | Inspect the retained occurrence, including any fingerprint or envelope mismatch. It is not dropped. |
| `not_assessed` | Another proposal family, explicitly retained for a separate pass. |

Current/proposed `fieldStates` use the same public-quality projection as profiles,
directory, comparison and exports. They are diagnostic evaluations of copies, not
source retrieval or proof adjudication. A matching group can still be under review.
A malformed evidence shape is reported as `assessment_failed`, never verified.
Proposal identity is the retained path ID plus current record context; this report
cannot establish new issuer identity from a document it has not reviewed.

## First measured snapshot

At accepted checkpoint `800405b1`, all **441** proposals remain: **159** document
proposals are still conflicting, and **282** other-family proposals are explicitly
not assessed. Of the 159, **30** have value/field-presence differences and all have
evidence/review/scope differences; these counts overlap and are not error totals.
There are no exact already-applied groups and no duplicate fingerprints in that
snapshot. No proposal has been resolved, rejected or superseded by this report.

## Evidence-bound review advice

The retained Emmvee proposal has now been reviewed against its original collection
and the already accepted value/proof group. See the [review note](reviews/2026-09-18-emmvee-retained-proposal.md).
The decision is **do not apply as proposed**, not “already applied” or “superseded”.
Its old proof withdrawal must not overwrite the current supported allocation group.
The original status and every occurrence remain in the backlog.

`reviewDecisionAudit` preserves every event from
`docs/reviews/pending-proposal-decisions.json`; `reviewDecisions` links matching
report entries to the note. `applicable` requires the exact proposal, original run,
issuer/offer identity, accepted document-group hash, display holds and current
public verification states. Changed bindings report `proposal_mismatch`,
`identity_mismatch` or `stale_evidence`; unmatched reviews also remain visible.
An independent subscription update does not stale a document review. The only
normalized clock remains `staticSourcePolicy.checkedAt`, never the source-proof
clock. Multiple events are all shown, never selected by latest timestamp.

Add new uniquely named review events and preserve earlier notes. Evidence files
must be local, hash-matching Markdown files alongside the ledger. Invalid ledgers,
missing notes or altered evidence fail generation rather than quietly losing the
audit. `--check-report` also binds the ledger and note bytes. Neither advice nor
`applicable` is a publication permission, resolution or fresh source audit; no
publisher imports this ledger. `resolutionsApplied` remains zero.

Read-only `subscriptionSnapshot` classification is described below. P4,
Teamtech's hold and the unaccepted broad parser draft #105 remain unchanged.

## Verified review release

The Emmvee review annotation was released in #121 at `3bb08735`; its audited
accepted baseline remains `71bec048`. A concurrent ordinary filings update
`61360716` is preserved. The new main report was replayed against that updated
snapshot and the review is still applicable; no pending status was changed.
See [the release receipt](releases/2026-09-18-emmvee-proposal-review.json) for
CI, live checks, exact artifact hashes and the distinction between an operator
review and an accepted numerical publication.


## Subscription snapshots — report schema 2

The existing commands and validation-job artifact now include all retained
`subscriptionSnapshot` occurrences. The eight-field group comes from the publisher,
including category values, source label/URL, observed/collected/legacy AsOf clocks,
time basis and degraded state. A matching total with different categories, source,
clock, null or missing field is not an exact match. No subscription clock is ignored
for whole-group equality. Unknown fields/scopes and malformed proposals remain work.

`subscriptionComparison` contains base, proposed and current diagnostics, alongside
`sourceRelation`, `observationRelation` and `collectionRelation`. Source labels and
explicit HTTPS URLs use the same authority classification as the public boundary;
classification is not verified issuer identity, correct numbers or permission to
redistribute. A named exchange with no snapshot URL has unknown bound authority.
A secondary-source label stays secondary. Current attached sources/history are
intentionally not borrowed to fill a retained group's missing URL or timestamp.
This diagnostic isolation can report unknown authority where the current public
page has contextual source links; it does not change that page or those links.

Raw clocks remain in `storedClocks`. Separate instant comparisons require explicit
zones, normalize offsets only for ordering, and flag invalid/naive dates, disagreeing
collection aliases or observation after collection. `subscriptionAsOf` is a legacy
collection alias, never an observation. Collection-only or untrusted observation
bases are `not_comparable`. A newer collection of an older observation is identified
as such, not promoted. The time relation remains only a comparison even when source
bindings differ or are missing. Matching groups can still require source review.
No timestamp, closing date or `reported` state establishes final subscription.

Snapshot diagnostics include missing headline categories, missing/unsafe source
URLs, unknown authority, clock issues, retained degraded state and the shared public
subscription review state. Malformed projection data is `assessment_failed`, never
a verification pass. Current review/availability context remains attached to the
isolated assessment; original proposals and public data are not altered.

At the `09a570f5` baseline, 22 subscription groups remain conflicting. Eight have
older recorded source observations and 14 have no comparable observation time.
All 22 lack a snapshot URL: 14 are exchange-named but unbound; eight retain secondary
labels. All 441 proposal occurrences remain, including 159 unchanged document
comparisons and 260 other-family items still explicitly not assessed. No proposal
was resolved or the phase gate relaxed. `--check-report` rejects schema-1 receipts
as stale; regenerate instead of relabelling an old report.

Next, add read-only overdue-source/publication diagnostics. Source lineage recovery
and explicit audited dispositions remain separate; this tool never supplies a
publication manifest, applies a proposal or clears a source review.
