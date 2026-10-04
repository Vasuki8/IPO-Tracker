# IPO integrity safeguard repair — 2026-10-04

Status: **READY_FOR_REVIEW**. Not merged or live-verified.

## Scope

This batch addresses audit BUG-003, BUG-004 and BUG-002. It changes publication
safeguards, not IPO facts. The other twelve audited defects and separate historical
release, draft-source and scheduling workstreams are not closed by this batch.

### BUG-003 — atomic retained-field merging

A value-bearing object is now one indivisible observation. When concurrent edits
conflict, the entire current field is held unchanged, including value, status,
source and correction history, and the existing conflict counter increments.
Independent record changes can still merge. Non-concurrent updates apply as
complete objects; repeated application is idempotent. Nested application
requirements and price-band endpoints receive the same protection.

This prevents combining a current value with an incoming source supporting a
different value. It does not automatically adjudicate an official-source dispute
or introduce a new approval/publication bypass. Proposal conflict-reporting policy
remains unchanged; detailed proposal retention and source-conflict resolution are
separate work, not claimed as completed here.

### BUG-004 — preserve deliberately cleared values

An existing retained field takes precedence over legacy `terms` even when its
value is null. Its sources, correction history and explicit missing/provisional/
conflict status survive serialization. Legacy fallback is used only when the
retained field is absent. Malformed retained field envelopes or correction arrays
fail instead of being silently dropped. This includes nested application fields.

### BUG-002 — field-specific value validation

Typed schema references constrain positive INR numbers, positive safe-integer
share quantities, valid calendar dates and exact price-band shape. Semantic guards
reject inverted bands and unlabelled opening/closing/listing date reversals.
Explicitly labelled date conflicts, nulls, fractional INR, and invalid original
values inside correction history remain retainable. No date, quantity or price is
inferred. Existing final-price-versus-band conflict display is unchanged.

The dependency-free validator enforces the `$ref` siblings and numeric assertions
used by these definitions. No runtime dependency was added. Published shape and
schema payload version remain 1.2.0.

## Verification and provenance

Baseline: source revision `034f60576f9367d1c55cfac9d36a3ad63dc40f97`, from Pages
workflow 37235771863 / artifact 11315213742. ZIP SHA-256:
`99928a58987a4f5f5264cdda2e8e534d119b0fea025bb03f180f63ec59f8cd13`.
Branch base: `9900fa9bc00c375ebb80e92e7c54a9ae9ef163a3`, the following Pages-health
commit. Production files and tests were checked by Git blob hash before upload.

The added tests ran against the original code and failed on the audited defects,
then passed with the fixes. They invoke the real merger, builder and validator,
not test-only reimplementations.

- `test-live-sync-semantic-publication.mjs`: complete-object conflict handling,
  concurrent source-only edits, price bands, cleared fields, nested application
  requirements, input preservation and idempotent replay.
- `test-bse-public-projection.mjs`: original real-release checks plus a 34-record
  null/fallback fixture with exact source/history and deterministic output checks.
- `test-validate-data.mjs`: 66 invalid domain cases and 17 existing malformed
  datasets rejected; five legitimate fractional/null/conflict/history edge cases
  retained; the full current corpus accepted.
- Builder `--check`, published validation, changed JavaScript syntax and
  `git diff --check` passed. An independent Python Draft202012Validator checked
  schema validity and all current public records successfully.

**Local full-suite result: 100 of 103 script entrypoints passed.** All non-browser
entrypoints passed. The three browser scripts cannot start because Playwright is
unavailable locally: `test-ui.mjs`, `test-product-logic-ui.mjs` and
`test-drhp-freshness.mjs`. This is not a green claim for the complete browser suite.
Local Node is v22.16.0; existing GitHub CI uses Node 20. GitHub branch checks remain
required before merge. BUG-014's moving-production-fixture problem is not masked
or changed in this batch.

The Pages archive omitted `.github`. Its files were restored from retained source
artifact 11112041606, then independently verified: the full Git tree matches main's
`04afce9e42b11324ccfb6e4b6d436f18cfc77960`. All nine initially blocked workflow tests
then passed. No workflow was modified.

## Data preservation and handoff

All seven recovery manifests and `data/ipos.json` remain byte-for-byte unchanged.
The public file contains 1,389 records, generated at 2026-10-04T20:35:00.071Z,
SHA-256 `2343c0ae10a83fb56453f34afefcbe7d5568a1f295c62467fd532b1c1f60c53b`.
No source collector was run against external services. No UI, operational state,
workflow, permission, licensing decision or commercial feature was changed.

Review and run repository checks before merge. After merge, verify the operational
sync/publication result without replaying historical imports. Next address equity
instrument eligibility and issuer matching (BUG-001 and BUG-005), then amended-term
retention and endpoint provenance. SSEK PR #352, source health, schedule gaps and
main protection/licensing remain separate. Do not expand P5/performance.
