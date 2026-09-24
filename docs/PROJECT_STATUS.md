# Project status and handoff

Updated: 2026-09-24 UTC (September 23 in America/Toronto).

## Current priority

Continue P1/P2/P3 backend data correctness, source coverage and dependable publication under `DEVELOPMENT_PROCESS.md`. The active application-term requirement is Lot Size only; minimum investment remains out of scope. Preserve the static architecture and official-source evidence rules.

The existing NSE/SEBI collection and historical backfill pipelines are already implemented. The BSE SME constituent JSON endpoint is connected. The remaining BSE work is turning correctly parsed discovery candidates into independently verified issuer/listing evidence, without claiming current index membership is the entire historical IPO universe.

## Current batch: repair BSE notice discovery and its CI gate

### Recovered state

Base inspected: `545518553efb419362f2cd84e4306ef43d362e72`.

The preceding parser change was `8bee31cd7c9f81ddaf6dab77f2260fd9b10a8873`. Production audit run `35937699843` failed its BSE addition-notice test; the notice collection step was skipped. General validation CI did not invoke that test.

The failure was reproduced locally against byte-identical copies of the committed parser and test: the plural notice used `Notice No:`, but the parser's initial clause delimiter accepted only the period/no-punctuation forms. Its later entry parser already accepted a colon.

### Changes

- Align clause and entry punctuation handling for singular and plural official listing references.
- Preserve the distinction between the explicit BSE listing date and the later index-addition date.
- Reject calendar rollover, unrelated prose between references and listing statements, missing tickers, and conflicting duplicate issuer/date evidence.
- Enforce the existing bounded scan on every clause, including clauses followed by another reference.
- Validate notice batch sizes before network work; retain the current maximum of 20 notices.
- Run the addition-notice test in pull-request/push CI, not just the production source workflow.
- Classify source audits as `complete`, `partial`, `failed`, or `no_eligible_notices`; partial/failed collection exits nonzero instead of appearing successful with no candidates.
- Support `--output` JSON with parser version, run/commit identity, generation time, candidates and failures. Candidate evidence includes the actual source kind/URL, collection time and an **extracted-text** SHA-256 (not a PDF-file hash).
- Retain the JSON as a 14-day Actions artifact even when the notice audit fails. The BSE workflow remains independent and retains `contents: read` permission.

### Files

`scripts/audit-bse-sme-addition-notices.mjs`, its test, `.github/workflows/validate-data.yml`, `.github/workflows/audit-bse-sme-universe.yml`, README and this handoff. Earlier README/status histories are preserved unchanged under `docs/archive/`.

### Validation state before merge

Local checks passed: JavaScript syntax; existing singular/plural cases; 25 punctuation/dash combinations; duplicate/conflict, invalid-date/leap-year, wrong-date, missing-ticker, unrelated-text, URL, batch-boundary and audit-health checks; real CLI failure-output test with a simulated source outage; workflow YAML parsing.

The local parser suite does not exercise network collection or issuer matching. Its unrelated matcher import is substituted locally and is not included in the commit; GitHub CI uses the actual repository module and runs the full existing validation suite.

CI, merge, live-source audit and deployment verification are **pending** at this pre-merge checkpoint. Update this section with observed run IDs/results after execution. Do not call this batch production-verified based solely on unit tests.

## Data and safety review

This batch does not edit recovery manifests, `data/ipos.json`, `data/bse-ipo-sources.json`, field values, evidence histories or UI assets. It does not relax issuer-specific BSE listing-evidence requirements or reinsert BSE auditing into hourly live sync. No spending, external communication or permission expansion is introduced.

## Remaining blockers and next task

1. Verify the repaired source audit on real official PDFs and record successes/failures. A catalog HTTP 200 or an empty HTML `Data` string is not successful notice extraction.
2. From a successful report, verify a bounded set of issuer-specific BSE listing notices before updating the retained source manifest or materializing records. Do not use an index effective date as a listing date.
3. The audit still selects the latest 20 eligible notices; older-notice progress needs a separate durable, versioned cursor. Do not repeatedly rescan the same latest notices and call it historical completion.
4. Full 2020–2026 BSE coverage and many historical fields remain incomplete. Generate coverage from current recovery files, rather than using old README counts.

## Prior history

The previous full project-status log is preserved byte-for-byte in [archive/PROJECT_STATUS-before-bse-notice-repair.md](archive/PROJECT_STATUS-before-bse-notice-repair.md). The previous README handoff is in [archive/README-before-bse-notice-repair.md](archive/README-before-bse-notice-repair.md). These are historical milestones; this document and current code/run evidence supersede their stale next-task instructions.
