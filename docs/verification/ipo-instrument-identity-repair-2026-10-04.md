# IPO instrument admission and issuer-identity repair — 2026-10-04

## Scope and release boundary

Repairs BUG-001 and BUG-005 only. This is the tested implementation record;
branch CI, merge and post-repair served verification are recorded in the PR
release receipt. The other audit findings and SSEK closeout #352 are not closed.
No financial terms are inferred or amended. No UI, commercial, licensing,
permission or production-schedule change is included.

## Prior release: the previously pending cycle completed

Live-sync **37241174980** completed successfully, including extraction, rebuild,
validation, semantic proposal application, repository publication and operator
state persistence. Its updated operator snapshot was generated at
2026-10-04T23:01:23.909Z. The downstream Pages run **37242214201** succeeded.

The runner's actual served IPO response returned HTTP 200 on attempt 1 at
2026-10-04T23:01:50.193Z. It had 1,389 records and SHA-256
`4bf3e7b30cf9c80ac31356c872ebadc94852890151432e416775dfd51c9b9806`.
The verification artifact is 11317907814, ZIP SHA-256
`9d67ecfbe14b61e6335f17b0c7cbf2ae9650ff1d07813ec7f0886c3c406ef6b4`.
Downloaded response bytes exactly matched the deployed site artifact
11317529358 (ZIP SHA-256
`b4f19d5700fcc77d8147127a0dc88c4161a0333dd92941a88ba2a2c29af8452d`).
This completes the outstanding PR354 cycle check; it does not certify every
source's substantive facts or resolve the other operational findings.

## BUG-001: admission and public projection

The live adapter accepts only the EQ and SME families already used by the
historical NSE collector. Missing/unrecognised series and positive or unresolved
non-equity flags are rejected. Excluded input observations, endpoint, reason and
collection clock remain in the run's structured summary. Direct record creation
and enrichment have the same guard, so callers cannot bypass feed filtering.

The shared public-projection policy excludes retained explicit unsupported
series, including an explicit series in an NSE source URL. Unknown-board records
with independently retained equity IPO evidence and no series classification
remain eligible; a null board is not a debt classifier. Unknown series are
unapproved, not automatically described as debt.

The only current public removal is `smc-global-securities-limited` / `SMCG04`,
whose retained source explicitly says `nse_series: DEBT`. All seven recovery files
are unchanged, including the full SMC record, original clocks and source history.
The other 1,388 public objects and dataset metadata are exactly unchanged.
The rebuilt JSON SHA-256 is
`7d0fb465758c477e52a8b27ae3c2c896cb1c85af6db228519a9432cdbc0119fa`.
See `data/discovery/ipo-instrument-exclusion-2026-10-04.json` for the receipt.

## BUG-005: identity consistency before mutation

Preflight checks the entire eligible incoming batch against all recovery years
and against other incoming identities before writing any manifest. Matching name
and symbol must select one compatible record. Retained explicit symbols, NSE
source-URL identifiers, recognised NSE identity labels and known series/board
must agree. A matching symbol cannot override a conflicting legal name, and a
matching name cannot replace a different known symbol. Ambiguous matches are not
resolved by map insertion order.

Contradictions fail the collection before file mutation and include the incoming
observation and retained identity in the error diagnostic. No uncertain
observation is attached to an arbitrary issuer. Legitimate cosmetic case,
spacing, punctuation and ampersand normalization is retained; no fuzzy matching,
new alias approval or automatic corporate rename resolution is introduced.
A genuinely absent symbol may still be filled for an exact compatible name.

Cross-year identities are held for explicit review. This prevents an unsafe
insertion but does not implement a full offer-year correction/migration workflow;
BUG-007 is not claimed resolved. Amendment retention (BUG-006), endpoint field
provenance (BUG-008), clock repair and browser fixture brittleness remain separate.

## Tests and provenance

The source snapshot is `da9a583409983a0d9aba073b74f25de382a63d23`. The entire
reconstructed Git tree matched `2c7173e3f96920c066eb92a4a31b784a1a5b15c5`, including
`.github` files restored from the earlier full source artifact. Work was isolated
from the actual repository and no external source collector was run locally.

Eighteen initial regression cases were run against the original code: sixteen
failed on unsafe behavior and two legitimate controls passed. All eighteen passed
after repair. A nineteenth source-URL-series case then failed and passed after
closing that additional admission path. The existing collector CI entrypoint
imports these tests, so they are not merely an unexecuted test file.

The non-browser suite passed 101/101 entrypoints. Builder consistency, full public
schema validation, deterministic output and all seven recovery-file preservation
checks passed. A dry run using 26 retained live-feed identity fixtures admitted
25 eligible observations, excluded SMC DEBT, created no duplicate records and
left recovery files unchanged. It is a retained-fixture test, not a live fetch.

Three original browser entrypoints remain unverified. The default Node environment
lacks its `playwright` package; using the available bundled driver and system
Chromium allowed launch but localhost navigation was blocked by administrator
policy. No browser test was weakened and no full browser certification is claimed.
No UI behavior changed in this patch. Review is by the current agent, not an
independent reviewer's approval.

A temporary, exact-branch-only preparation workflow may apply this reviewed patch
and rebuild the large derived JSON. It must verify exact before/after data hashes,
allow only the SMC public removal, preserve every recovery file, and remove itself
and its patch payload before the PR is opened. It never writes main or modifies
permissions/schedules there. Final CI checks the resulting complete branch.
