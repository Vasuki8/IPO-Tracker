# IPO integrity safeguard release receipt — 2026-10-04

## Release state

PR #354 is **merged and deployed**. The served snapshot is verified. Completion
of the first new live-source sync is still unverified; this is not a claim that
all operational health or all fifteen audit defects are resolved.

- Reviewed head: `ab77c770816217542dcc4483a080061fd7036078`.
- Latest pre-merge main checked: `4ec18c13d17c453686f725a69e43f5f031f509d4`.
- Merge: `be8ec1e0c1683a6e9fa41ddd78fd34e4aa1dd804`, 2026-10-04T22:44:42Z.
- Post-merge data-contract run: 37241175018, success on Node 20.
- Deployment run: 37241175061, job 111550036921, success.

## Review and fresh tests

Reviewed complete production changes and associated tests for atomic observation
merging, explicit cleared-field precedence, source/history preservation, typed
schema references and qualified date chronology. No new merge-blocking regression
was identified within that scope. This was a review by the current agent, not an
independent reviewer approval. Other audit issues remain separately tracked.

The review source was artifact 11316817258 from PR run 37239816206. Archive
SHA-256: `a65b8de01aa515e14e6594d414614a803acd00805bf33fd98d476e3cf18c7c5b`.
Its extracted full Git tree matched the reviewed head:
`913400f974446e5709460d0f0be9dcda45a87984`.
Main had advanced only operational logs since the branch base; no code/data
rebase conflict was present. Merge used an expected-head SHA guard.

All 103 local test scripts were attempted: 100 non-browser entrypoints passed;
`test-ui.mjs`, `test-product-logic-ui.mjs`, and `test-drhp-freshness.mjs` could not
start because `playwright` was unavailable. They are not reported as passes and
no expectations were weakened. The first local test batch reached the execution
time limit after 86 scripts; remaining scripts were then run to completion with
per-script results retained. Node version was 22.16.0.

The 66 invalid domain cases, 17 malformed datasets and five legitimate edge cases
passed their rejection/acceptance assertions. Additional review exercised 48
atomic-observation combinations for concurrent holds, whole updates, replay and
input preservation. Builder `--check`, the complete published-data validator and
Python Draft202012Validator with date format checks passed. The local worktree
was clean after tests; public data and all recovery manifests were unchanged.

All seven previously triggered PR checks were rechecked as successful. The
post-merge data-contract job subsequently passed every step, including the real
merged-tree builder, typed validator and semantic publication regressions.

## Actual served response and deployed artifact

Pages fetched `data/ipos.json` at **2026-10-04T22:45:08.650Z**. HTTP status was 200,
verification attempt was 1, and expected and served SHA-256 matched:
`2343c0ae10a83fb56453f34afefcbe7d5568a1f295c62467fd532b1c1f60c53b`.
The response contains 1,389 records, generated at 2026-10-04T20:35:00.071Z.
It was downloaded from the workflow artifact and independently compared
byte-for-byte with the locally tested data; the comparison passed.

Served-response artifact **11316733416**, 303,736 bytes, ZIP SHA-256
`846213470f408730ab1ccf39fb40ccd61eccf067c5098b22256050b093cd5fe7`.
Expires 2026-10-18T22:45:09Z. Its IPO and DRHP verification reports are retained
in the accompanying conversation evidence package.

The six DRHP/page files returned HTTP 200 with matching hashes; the last was
checked at 2026-10-04T22:45:09.408Z. These were `data/drhp-filings.json`,
`drhp.html`, `assets/pre-ipo-filter.js`, `assets/drhp.js`, `assets/styles.css`,
and `index.html`. This is served-byte verification, not a browser interaction test.

Uploaded site artifact **11316743305**, 2,018,437 bytes, ZIP SHA-256
`0ce5b1caf73292161eb061a5fd4838c5d1700bc83b10ff2f179ff9265bd62713`.
Expires 2026-10-05T22:45:00Z. The patched three production scripts and schema,
public JSON and all seven recovery files matched the tested bytes in this archive.
Direct external network access from the local runtime and web viewer was
unavailable, so actual response verification relies on the fetched-and-retained
GitHub runner responses, not a claimed direct browser visit from this chat.

## Remaining operational verification and next work

The merge automatically started live-sync **37241174980**. Its NSE collection,
historical materialization, reviewed-source and SEBI document-attachment steps
passed; at the last check it was extracting NSE issue fields. Later extraction,
rebuild, semantic apply,
repository publication and downstream served verification were not yet observed
complete. The temporary `reviewed_ssek` job was skipped. No separate manual
historical release or production replay was dispatched.

The next run must inspect that exact sync and any downstream deployment before
calling the full source-to-publication cycle verified. If it succeeded, advance
to BUG-001/BUG-005. BUG-014 browser fixture brittleness, the other audited defects,
SSEK closeout #352, schedule health, source rights and branch protection remain
outside this release. Do not weaken conflict checks, infer data or expand P5.

The served DRHP snapshot reports a separate successful source collection at
2026-10-04T21:21:28.121Z with 102 companies, 104 filings and consistent pagination.
That collection predates this merge; it is not an effect of these repairs.

This release changed no IPO facts, source clocks, recovery evidence, frontend
behavior, schedules, permissions, licenses, infrastructure or commercial features.
The follow-up handoff commit is documentation-only and preserves preceding notes.
