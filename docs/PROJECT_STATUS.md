# Project status and release evidence

## Standing product direction

IPO Tracker is intended to become a public commercial product. The paying audience,
pricing and revenue model are not selected. Customer trust, repeat research,
accessibility, discoverability, dependable operations and sustainable costs apply
to every milestone. No new spending, contracts, external outreach, accounts,
payments, analytics tracking or materially changed access without required owner
approval. Sponsorship must be identifiable and separate from factual verification
and ranking. See `COMMERCIAL_READINESS.md` for evidence and unresolved decisions.

Keep the existing light/static architecture while it meets requirements. Final
Prospectus authority for completed static terms, explicit provisional disclosures,
source observation versus collection time, missing-value semantics and the existing
P4 correctness gate are unchanged. P5/performance expansion remain gated.

## Recovery of the interrupted session — 17 September 2026

The failed chat response did **not** discard the previous implementation:

- [PR #100](https://github.com/Vasuki8/IPO-Tracker/pull/100) merged as
  `bb2227c727597b7c75ff55c6dc88268860026c41` at 21:30:10 UTC. Its head was
  `aa6922129d0217e3f0c3c00b99a1c7a329090e3a`. Public field decisions/withholding,
  separate observation/check clocks, secondary labels, methodology, commercial
  readiness and presentation-only publication are implemented. Do not rebuild
  these as new roadmap tickets.
- The presentation publisher created `2ec1b07edd54ecb16efad9c1364bdbd0790703b4`.
  [Pages run 35277098551](https://github.com/Vasuki8/IPO-Tracker/actions/runs/35277098551)
  succeeded. Downloaded artifact `10521465600` has verified archive SHA-256
  `e90c5076826605b9856a39d89686f90e574cd6f038c25883c31de05ce5f369bf`.
  The recovered code, generated data and all 1,366 profiles were inspected from
  that artifact. This is deployed-artifact evidence, not a claim of direct public
  HTTP access from the local environment.
- No prior Git working tree or unfinished patch survived in the accessible
  workspace. The roadmap, two earlier source-preview ZIPs and three screenshots
  did survive and were preserved. Recovery used a new artifact-derived workspace,
  not a reset/overwrite of an existing checkout. Direct Git/network access failed;
  GitHub connector reads/writes and workflow artifacts remain available.
- Current `main` later advanced through the independent scheduled publisher to
  `e3ee0fe1d43efee3785743388523e1d408ce6008` (filings output). This recovery work is
  based on that newer main tree and must preserve its data. It does not claim the
  older presentation artifact is the latest canonical snapshot.

The detailed pre-release implementation note is preserved in the history of this
file at `2ec1b07edd54ecb16efad9c1364bdbd0790703b4`. The owner roadmap remains a dated
audit in `ROADMAP.md`; it has not been rewritten to imply source repairs occurred.

## One bounded milestone: complete public-release acceptance

**Problem / affected users:** a green build and an interrupted release handoff do
not prove directory researchers, profile readers and CSV/comparison users receive
the same trust-aware snapshot. The previous status still said pre-release after
#100 had actually merged and deployed.

**Acceptance:** verify all local generated profiles against the summary contract;
compare bounded real HTTP samples with the exact deployment checkout; reject
stale/mixed content and changed source clocks; retain pass/failure receipts; no
canonical/proposal/gate writes; full frozen and browser checks before merge.

Implementation branch: `chore-public-release-verification` (new PR/release receipts
must be recorded after they actually exist). `tests/verify_public_release.py`
checks all profiles locally and full bytes for a bounded served sample. The new
`Verify public release` workflow has read-only permissions and follows successful
main-branch Pages runs using their immutable commit. Existing frontend CI also
runs the HTTP acceptance check after its browser journeys. No new source writer,
paid service, tracking or production dependency is introduced.

Verified locally on the recovered presentation artifact: **957 Python regressions**
(949 existing plus eight release-check tests), **seven Node quality/renderer tests**,
all **1,366 profile/summary consistency checks**, and **17 complete HTTP responses**
from a loopback server. Negative cases cover stale profiles, changed source clocks
and authority, reintroduced held amounts, remapped/mismatched source references,
duplicate/unsafe inventories, malformed payloads, HTTP failure and wrong bytes.
Tests assert no file mutation and no public master/proposal/gate requests.

The original workflows missing from the Pages archive were recovered with their
exact Git blob hashes before running the full local suite. Local tests used
`uv run --no-project --python /opt/pyvenv/bin/python` with available Python 3.13;
locked dependency installation failed because local networking/cache is unavailable.
Do not call that a frozen pass. Frozen GitHub validation, fresh browser results,
authorized merge and post-deployment HTTP acceptance are pending until observed.
See `PUBLIC_RELEASE_ACCEPTANCE.md` for scope, commands, cost bounds and recovery.

## Preserved unfinished source repairs

- [#94](https://github.com/Vasuki8/IPO-Tracker/pull/94), `fix-p4-mixed-ofs-sellers`,
  head `4707df1e82337e3a7b8bac0838bbaa30c3d200be`: not merged; GitHub currently
  reports a merge conflict against main. The broad preview did not contain the
  intended Emmvee/Teamtech repairs. It is not an accepted seven-record publication.
- [#98](https://github.com/Vasuki8/IPO-Tracker/pull/98),
  `fix-reviewed-correction-publication-guard`, last inspected head
  `d5e5d0580360a87dffc35b69e674886848b55005`: source-policy/manifest safeguards
  stacked on #94, not integrated by this milestone.
- [#99](https://github.com/Vasuki8/IPO-Tracker/pull/99),
  `fix-kaytex-speb-document-holds`, head `a503531ded368c4eb53ba09cf5c2aafef3391c38`:
  additional Kaytex/SPEB source holds and final-preview review ordering, stacked
  on #94. Its source findings, preserved proposal and manifest handoff must be
  carried forward. This recovery does not re-review the PDFs or promote its preview.

No branch above is overwritten, retargeted or merged by this milestone. Existing
canonical defects, review history and temporary public holds remain distinct.
The recovered presentation report had P4 incomplete with 385 P4 plus 53 higher
priority rows, 1,615 blocking reviews, 14 unmapped reviews and P5 waiting. Those
are the older artifact's dated counts, not a replacement for the next accepted
canonical publication's recalculated reports.

## Exact next task after release acceptance

Reconcile #94 with current main while preserving #100's public trust boundary;
integrate #98 and #99 on that repair branch, then freeze the combined code for the
explicit seven-record acceptance. Reproduce Emmvee composition and Teamtech
allocations with matching Final Prospectus proofs; preserve the five continuing
holds, Kaytex/SPEB safeguards, unaffected records and proposal history. Recollect
under the combined source policy rather than relabelling an old collector manifest.
Only after source acceptance, reviewed publication and deployed-page verification
may that repair be called complete. Do not enable P5/performance while P4 is blocked.

Proposal triage, routing all semantic reviews, overdue-update detection, lifecycle
work and the remaining P4 evidence batches remain unfinished. Data-use/hosting
permissions, customer validation, exact dependency/asset notices, professional
jurisdiction review, telemetry decisions and a restore rehearsal remain unresolved.
No monetization activation or external communication was performed.
