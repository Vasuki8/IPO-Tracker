# Historical subscription snapshot holds — 18 September 2026

## Evidence and decision

Reviewed accepted baseline `3979db542a16cd81cb46ba762f6a905a09ee3daf` after
#135's collector prevention and #136's checkpoint were already deployed. The
older handoff patch is superseded by that release and has not been applied.

The original before/after canonical bytes were recovered from retained Pages
artifacts and checked against the hashes in
[the immutable diagnostic](https://github.com/Vasuki8/IPO-Tracker/blob/3979db542a16cd81cb46ba762f6a905a09ee3daf/docs/releases/2026-09-18-bse-source-authority.json).
Before: `70a5133f11bce99f9e432c1ae56b52c29b012593`, SHA-256
`1b600dc26dbf5ec24908464ba3da3ce3c0798fa3804278b5c85c32fcb0d352eb`.
After: `eec88efb37a238ee862a7d21a8bfa84f940fcaae`, SHA-256
`60097606443c2460f1672a81e74144c39504ef13527b3de1bd1400b1806b2d6f`.
All eight total changes and unchanged issuer/offer identities match the retained
diagnostic. The current snapshots retain those totals and metadata. This is an
exact dataset comparison, not a claim that either set of multiples is correct.

The [earlier source/boundary review](https://github.com/Vasuki8/IPO-Tracker/blob/3979db542a16cd81cb46ba762f6a905a09ee3daf/docs/reviews/2026-09-18-core-subscription-boundary.md)
and #135's failing-then-passing replay establish the producer defect: the generic
NSE summary could replace a total while preserving another observation's category
values and attribution. The newly deployed prevention does not retrospectively
repair the historical snapshots.

A fresh read of https://www.nseindia.com/api/ipo-current-issue on 18 September
returned the eight matching issuer/symbol/date rows and headline multiples, with
`noOfSharesOffered` and `noOfsharesBid`. It supplies summary inputs, not a comparable
BSE/secondary category denominator or a source observation timestamp. SONA/EQ and
SPECTRAA/SME NSE detail URLs and BSE beta demand ID 7973 were inaccessible through
the read tool. This does not establish an exchange outage or missing disclosure.
No full response hash, full PDF review, final subscription figure or numerical
replacement was verified in this increment.

**Decision: withhold the exact historical subscription snapshots for sona,
ssretail, jsipl, heromotors, nse, kheriaauto, spectraa and axiomgas pending source
reconciliation.** SpectraA's snapshot has no source link; do not invent one from
its generic issue-feed record. No old total is restored. Other fields are outside
this decision. The original canonical values, categories, clocks, history and all
441 pending proposals remain untouched.

## Binding, public treatment and release criteria

The existing hold registry gains a separate `subscription_snapshot` scope rather
than fabricating a static-field PDF proof. Each binding retains the exact issue
identity including both offer dates and the complete present subscription fields,
plus a digest of that snapshot. Missing keys and explicit nulls remain distinct.
The only non-resolving comparison exception is collection-clock refresh
(`subscriptionAsOf`, `subscriptionCollectedAt`): rechecking mixed facts cannot
release the hold. Actual source observation times, names, URLs, categories and
values remain part of the binding. Historical rows do not override current facts.
A different snapshot is outside this exact hold, not an automatic declaration
that a retained proposal is resolved or the new figure is final.

Public profiles, quick views, directory, comparisons and CSV withhold the affected
multiples; profile history/chart fallback is disabled while held. The field-evidence
panel explicitly identifies the subscription review. Metadata remains available
without manufacturing freshness. A manual-source-review task retains each binding,
original source context and next action; it adds no automatic Final Prospectus gap.
Review counts may increase: this is visibility of unresolved work, not P4 progress.

Release uses the existing serialized `review` path, rebuilding only derived
validation, queue, phase and public artifacts from then-current main. Require
frozen regressions, browser cross-surface checks, unchanged canonical/proposal
bytes and live held-profile/queue verification. No collector/writer/schedule,
dependency, tracking, billing, architecture or permission expansion is introduced.
Source-host authority is not commercial redistribution permission; those rights
and customer/pricing/privacy decisions remain unresolved.

Next obtain issuer-specific detail and denominator evidence for one held snapshot,
then use the existing source-bound collector/accepted publication path. Do not
clear a hold by changing its timestamp, deleting its review, or restoring an old
number from history. SpectraA source matching and the 22 original subscription
proposals remain separate evidence work. P5/performance remains gated by P4.
