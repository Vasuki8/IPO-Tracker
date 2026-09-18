# Core subscription hand-off — 18 September 2026

## Evidence and scope

The accepted [BSE authority release receipt](../releases/2026-09-18-bse-source-authority.json)
retains a comparison between canonical commits `70a5133f11bce99f9e432c1ae56b52c29b012593`
and `eec88efb37a238ee862a7d21a8bfa84f940fcaae`, including both complete-file SHA-256
digests and eight changed totals. Seven retain their category values, source
name/URL and source/collection clocks; SpectraA has no bound snapshot source.
No total is accepted or rejected numerically by this comparison.

At starting main `b3a108785c8f4436cd83a14c2ea408ed1f9e9683`,
`update_data.normalize_nse_record` put issue-feed multiples into canonical
`subscription`. The active wrapper `run_update.merge_non_null_preserving_nested`
merged that dictionary field by field, retaining previously collected categories.
The incoming record did not carry replacement subscription attribution. The
publisher then correctly treated the already mixed candidate as an atomic group;
there was no concurrent group conflict to detect in the ordinary case.

## Acceptance boundary

The generic current/upcoming/history collector now retains its latest numbers in
`observations.NSE.subscriptionSummary`. The observation records its own feed
kind, endpoint identity, source page, issuer name/symbol/open and close dates,
collection timestamp, raw subscription/share fields and parsed multiples.
`observedAt` remains null; `timeBasis` is collection-only. The denominator is
unverified. For the historical endpoint, the normalizer does not have the request
window and does not invent query dates. Raw field names retain their original
meaning; no share/currency conversion is performed in this observation.

Core merging preserves existing subscription fields and history, including their
absence. It cannot create a new canonical number, source clock or finality marker.
The dedicated detail collector still owns accepted snapshot updates and retains
its complete-response/source/observation checks. Other core lifecycle updates
continue normally. Competing summary observations merge as whole evidence objects;
unaccepted candidates remain in the existing pending-proposal review flow. No canonical backfill, correction-history rewrite, proposal
reconciliation or source expansion is included.

## Regression interpretation

The network-free test replays the real Final Prospectus core entrypoint with
temporary files and fake NSE responses. Eight ratios reproduce the retained
diagnostic deltas; the issuer shells and API rows are constructed fixtures,
not original HTTP responses. A new issue exercises zero versus missing values,
and unknown input remains in raw evidence. A concurrent accepted detail update
tests the real three-way publisher. Public projection assertions verify that
core collection does not re-label the retained snapshot.

The old regression explicitly expected a mixed total; it is updated to require
preservation of the whole prior snapshot. Existing detail-collector acceptance
tests remain unchanged. Browser CI watches changes to the two core files so that
future changes at this boundary also run existing public research journeys.

The test-only parent reproduced all eight mixed totals in frozen CI run
35375027327 (1,160 tests attempted; all reported failures were in the six new
boundary tests). The local workspace is disconnected; CI is the execution authority. This note
does not claim any fresh NSE response or universal correctness of source data.
Record exact CI, merge and deployment evidence in PROJECT_STATUS.md.

## Remaining source work

The historical diagnostic remains unresolved. Reconcile original source, exact
issuer/offer and bid denominator before numerical replacement, or apply an
evidence-bound review hold while the discrepancy is unresolved. Preserve the
original 441 proposals and all 22 subscription proposals. SpectraA's source-link
failure cannot be solved by relaxing issuer matching. No commercial rights,
final-subscription status or source-observation time follows from this code fix.

The broad core collectors remain subject to ordinary repair publication mode.
No writer, schedule, paid service, dependency, tracking or access change is added.
