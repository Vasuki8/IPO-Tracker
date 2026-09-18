# Explicit identity on value-scoped display holds

## Problem and bounded release

While reconciling PR #125 with accepted main `8cdce86a4dc05421585e042c4207f3cbc06ec22d`,
review found that its new value-scoped intermediary holds include issuer/offer
identity, but both the current public matcher and #125's proposed extracted helper
ignore that identity for value holds. The same PDF/value could therefore keep a
hold attached after the record's issuer or offer changed. Document-scoped holds
already enforce identity; value-only historical holds intentionally have no such
extra binding.

This prerequisite release makes an explicitly supplied identity mandatory for
value-scoped holds too. Record ID, company, symbol and opening date must match,
and the field proof must name that same offer date. Malformed supplied identity
fails the build rather than silently becoming an unrestricted value hold. Unknown
scope remains an error even if identity would not match. Absence of identity on an
older value-only hold preserves its original PDF/value contract. No historical
identity is invented. Mirrors, parser versions and later check times do not release
an otherwise matching hold. A changed value must still pass normal source-proof
verification before it can be displayed.

The shared projection serves profiles, directory, comparison and CSV consumers.
No renderer, canonical source, review ledger, proposal status or phase gate changes.
The existing presentation-only publisher is sufficient; no new mode, writer,
schedule, dependency, permission or paid infrastructure is introduced.

## Acceptance evidence before PR

Ten new regression tests pass through uv, plus all 26 existing public-quality tests
and eight Node public-quality tests. The new suite was also run against the exact
matcher extracted from the checksum-verified baseline archive: it detected the
ignored identities and malformed bindings (27 failing subcases). All ten tests
pass with the new matcher. Synthetic proofs in these tests verify binding behavior,
not the accuracy of a financial disclosure.

All 1,367 generated profiles rebuild without changes. The directory payload,
canonical records, all 441 retained proposals, existing holds, review ledger and
phase data remain byte-identical to the baseline. The local public artifact verifier
passes; ordinary core publication correctly returns reviewedPublication=not_requested.

The complete local attempt ran 1,108 tests with six errors because the Pages
archive omits workflows used by existing tests. Locked packages were unavailable
for offline frozen sync. Local tests used uv with available Python 3.13.5, not a
frozen/full-suite pass. Local Chromium navigation returned ERR_BLOCKED_BY_ADMINISTRATOR.
Frozen repository CI and both browser suites are required before merge; post-merge
publication and live byte acceptance must be recorded separately.

## Preserved PR #125 work and source limitations

PR #125 remains at `be7c448544381cdc0723e09b01f3734713ec8f05` during this review;
its older generated reports are not carried into main. A separate current-base
rehearsal of its shared hold/queue logic and three intermediary holds produced
11 active hold reviews, 1,607 total reviews and 1,603 P4 blockers, not its historical
15/1,614/1,610 counts. Emmvee's completed repair is not held. That rehearsal is
UNACCEPTED and is not the released gate or a completed #125 source review.

Sacheerome's official Final Prospectus physical page 3 was visually rechecked via
the web PDF renderer: the lead-manager and registrar columns are separate and the
former-name line is subordinate to the registrar name. Snehaa's 18,126,150-byte PDF
exceeded the reader's limit and direct download failed. Its earlier review remains
retained in #125; no fresh byte-hash/full-PDF verification is claimed here. This
prerequisite release activates none of the three new role holds and accepts no
replacement names or figures.

Next: port this identity rule into #125's shared helper, retain its original source
note and tests, regenerate all queue/validation/phase/profile artifacts from the
then-current accepted baseline, and complete source/browser/release acceptance.
Do not replace current accepted data with the old branch snapshot. Teamtech stays
held, #105 stays unaccepted and P5/performance expansion stays gated by P4.
Commercial source rights, audience, pricing and privacy remain unresolved; no
spending, contracts, outreach, tracking, billing or access changes are included.
