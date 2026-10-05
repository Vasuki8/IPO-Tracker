# Browser-gate and IPO admission release — 2026-10-05 UTC

## Verified release state

The separate browser stabilization PR #357 merged as
`ea0301aa5f4a02c2f5beaa3fa846a21d92fe6e4c` at 2026-10-05T00:05:28Z.
PR #356 was then refreshed onto that change, checked, and merged as
`0e0da6ceacba40db808f90df7653d95732ab3160` at 2026-10-05T00:35:22Z.
That is October 4 at 20:35 EDT in America/Toronto. Its Pages deployment and
served output are verified. No browser gate was bypassed.

## Root cause and separate repair

A single fragment navigation could deliver both popstate and hashchange. A late
second render focused the detail heading after the user had skipped to main and
replaced expanded evidence. The retained original-focus.log from runner
37245740299 failed with actual `detailName`, expected `main`. PR #357 deduplicates
already-rendered URLs and invalidates the key on a new data load. Real Back/Forward,
query-only navigation, data reload and evidence expansion remain tested.

Synthetic UI-only fixture factories replace changing production counts, named
issuer lifecycle and refresh-status assumptions (BUG-014). The general directory
suite retains a real-corpus smoke check. Four browser scripts run three times;
ANY failure fails the gate. Repetition is not retry-until-green. No assertions
were disabled, and no new runtime dependency or production schedule was added.
This fixes the skip-link routing race, not BUG-015's document-filter focus issue.

## Tests and review

Reviewed candidate head: `24986b8d7b4bb515af175ee8f7b9549588871d1f`.
The downloaded PR source archive matched test merge `c9cf3ef5` and full Git tree
`762602c96ec1aba66102b9f1780703dbff3076b5`; the actual release has that same tree.
All seven refreshed PR workflows passed, including data contract 37246512814 and
browser 37246512748. Its downloaded result contains 12/12 passing executions.

Fresh local Node 22.16.0 sweep: 102/102 non-browser test entrypoints passed.
The command time limit interrupted reporting after 92 completed scripts; the
remaining ten were run and all 102 unique results retained. Builder --check,
typed full-corpus validation, unchanged worktree and exact data preservation passed.
Full HTTP browser tests ran on GitHub's Node 20 / pinned Playwright 1.56.1, not in
the network-restricted local runtime. No independent-review approval is implied;
review was performed by the current agent.

Post-merge data-contract run 37248108188 passed. Post-merge browser run
37248108152 passed all 12 executions again. Each three-run focus suite covers
27 delayed-event journeys at 320/390/1440 widths, plus navigation/reload checks.

## Served output and preservation

Pages run 37248108151 succeeded. Its actual IPO response returned HTTP 200 at
2026-10-05T00:35:44.953Z and matched on attempt 1:
`941e85283cf468a67ec4ad556755ed930afdd1dcef5c30fe0cf8ff86eba8307b`.
The dataset contains 1,388 records and retains generation time
2026-10-04T23:42:42.380Z. The six DRHP/page responses also matched.
Downloaded response bytes independently matched the tested public JSON. Uploaded
app.js, admission policy, collector, builder and all seven recovery files also
matched the tested bytes. This is runner-retained served-byte verification plus
CI browser interaction testing, not a claimed direct live browser visit here.

Compared with current pre-release data (SHA-256
`08b17c6e4810e46425c99ca1018119774a93436bb3418b61a79305a7b64d3ef4`),
only `smc-global-securities-limited` / SMCG04 is absent from the public projection.
Its complete DEBT recovery record remains. All other 1,388 objects, metadata and
seven recovery manifests are unchanged. PR #357 itself changed no IPO facts.
The older counts/hashes in the admission implementation note are historical
snapshots; refreshed source data was preserved, not rolled back.

## Retained artifact identities

| Evidence | Artifact | ZIP SHA-256 |
|---|---:|---|
| Original focus failure and repaired runs | 11319136455 | 2f8d450d509b445552ceb86e3e7f48e86af0d4aaad72d1ecfc71274771b0237d |
| Refreshed PR source | 11319197525 | 14eca44e4648d9ad976e7d07007dffa1b93dfa5c9c81a6a39edb1090d67801b8 |
| Refreshed PR browser runs | 11319556435 | b7a099f3c43a8d9e084d45d638018fefac11f286f48638b98b840f563a16b8be |
| Post-merge browser runs | 11319434269 | 7f0f3d4df76f11c516315b7d4f1ea2616f1004d79bd63330c1e5442589ce40ea |
| Served responses | 11319294506 | 3a3ba414abf8ba6883bc2c1a1ff5eae4ce586aa9d5439554c2c0700fe1c165eb |
| Uploaded site | 11319254730 | 5e83ee82fa8a0d89c1167106d32bc81b0650b20ebc40c8493f1f7154cfcf51eb |

All downloaded ZIP hashes were verified. Browser artifacts expire October 12;
the served-response artifact expires October 19 and the site artifact October 6
(UTC). Conversation evidence retains logs/receipts independently of those expiries.

## Remaining scope and next task

PR #354's earlier cycle 37241174980 and downstream 37242214201 were verified in
the preceding admission batch; do not reopen that completed checkpoint. This
receipt verifies the new release, not a new complete external-source collection
cycle under the new collector or all current operational health.

Original audit fixes now deployed: BUG-001, BUG-002, BUG-003, BUG-004, BUG-005,
and BUG-014. Nine original findings remain open: BUG-006, BUG-007, BUG-008,
BUG-009, BUG-010, BUG-011, BUG-012, BUG-013 and BUG-015. The separately reproduced
skip-link race is also repaired; no other finding is silently closed.

Next bounded code work: retain amended official terms/conflicts (BUG-006) and
correct endpoint provenance (BUG-008), preserving evidence, nulls and corrections.
Check current source health before changes. SSEK closeout #352 and administrative,
licensing and schedule issues remain separate. Do not replay historical imports,
expand P5/performance, or add spending, permissions or monetization without approval.
