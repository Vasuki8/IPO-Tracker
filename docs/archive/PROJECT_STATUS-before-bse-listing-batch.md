# Project status and handoff

Updated: 2026-09-24 UTC (September 23 in America/Toronto).

## Current priority

Continue P1/P2/P3 backend data correctness, source coverage and dependable publication under `DEVELOPMENT_PROCESS.md`. The active application-term requirement is Lot Size only; minimum investment remains out of scope. Preserve the static architecture and official-source evidence rules.

The existing NSE/SEBI collection and historical backfill pipelines are already implemented. The BSE SME constituent JSON endpoint is connected. The remaining BSE work is turning correctly parsed discovery candidates into independently verified issuer/listing evidence, without claiming current index membership is the entire historical IPO universe.

## Current batch: BSE notice discovery and CI repair — VERIFIED

Verification applies to the parser, read-only discovery audit and deployment, not to candidate materialization or complete historical coverage.

### Recovered state

Base inspected: `545518553efb419362f2cd84e4306ef43d362e72`.

The preceding parser change was `8bee31cd7c9f81ddaf6dab77f2260fd9b10a8873`. Production audit run `35937699843` failed its BSE addition-notice test; the notice collection step was skipped. General validation CI did not invoke that test.

The failure was reproduced locally against byte-identical copies of the committed parser and test: the plural notice used `Notice No:`, but the parser's initial clause delimiter accepted only the period/no-punctuation forms. Its later entry parser already accepted a colon.

### Changes

- Align clause and entry punctuation handling for singular and plural official listing references.
- Preserve the distinction between the explicit BSE listing date and the later index-addition date.
- Reject calendar rollover, unrelated prose between references and listing statements, missing tickers, and conflicting duplicate issuer/date evidence within the parsed notice.
- Enforce the existing bounded scan on every clause, including clauses followed by another reference.
- Validate notice batch sizes before network work; retain the current maximum of 20 notices.
- Run the addition-notice test in pull-request/push CI, not just the production source workflow.
- Classify source audits as `complete`, `partial`, `failed`, or `no_eligible_notices`; partial/failed collection exits nonzero instead of appearing successful with no candidates.
- Support `--output` JSON with parser version, run/commit identity, generation time, candidates and failures. Candidate evidence includes the actual source kind/URL, collection time and an **extracted-text** SHA-256 (not a PDF-file hash).
- Retain the JSON as a 14-day Actions artifact even when the notice audit fails. The BSE workflow remains independent and retains `contents: read` permission.

### Files

`scripts/audit-bse-sme-addition-notices.mjs`, its test, `.github/workflows/validate-data.yml`, `.github/workflows/audit-bse-sme-universe.yml`, README and this handoff. Earlier README/status histories are preserved unchanged under `docs/archive/`.

### Tests and release verification

Local checks passed: JavaScript syntax; existing singular/plural cases; 25 punctuation/dash combinations; duplicate/conflict, invalid-date/leap-year, wrong-date, missing-ticker, unrelated-text, URL, batch-boundary and audit-health checks; real CLI failure-output test with a simulated source outage; workflow YAML parsing.

The local parser suite substitutes the unrelated matcher import only and does not exercise network collection or issuer matching. That substitute was not committed. Both GitHub validation runs used the actual repository modules and passed the full existing suite, including the new notice test and deterministic publication/data-contract checks.

| Check | Observed result |
| --- | --- |
| Pull request | #165 merged |
| Merge commit | `7eedd8f9668cd7fce51d373427d7a2d7eafd7a8c` |
| PR validation run | `35939095504` — completed success |
| Post-merge validation run | `35939161216` — completed success |
| Production BSE audit | `35939161246`, job `107442985818` — completed success |
| Pages deployment | `35939161184` — success for the merge commit; completed `2026-09-24T00:36:33Z` |
| Audit artifact upload | Success; artifact `10783988662` |

### Measured production result

Report generated at `2026-09-24T00:36:54.982Z`, parser version `1.1.0`:

- 1,649 catalog rows; 236 eligible SME addition notices.
- 20 notices attempted; 20 fetched as official PDFs; no HTML detail fallback used.
- 29 issuer/listing references parsed; 29 unmatched to the inspected recovery universe.
- 0 fetch errors; 0 parse failures; report status `complete`.
- No IPO record or market field was added by this read-only audit.

`complete` means this selected notice batch was collected and parsed. It does not certify issuer identities, resolve cross-notice inconsistencies, or imply historical-universe completeness.

### Retained report and integrity

Actions artifact: `bse-sme-addition-notices-35939161246-1`, ID `10783988662`, from run `35939161246`. The downloaded ZIP is 3,581 bytes and contains `bse-sme-addition-notices.json`.

ZIP SHA-256 checked against GitHub's artifact digest:

`d041a66e67d715aa0b62341d6e92ff2bc463a6dedd8f4529a530b0e9b5db7b56`

The Actions artifact expires on `2026-10-08T00:36:55Z`; copies of the original ZIP and extracted JSON were also supplied in the conversation. Report checks confirmed its commit/run identity, counters, PDF source kinds, text-hash presence and unique `(listing_notice_no, bse_scrip_code)` pairs.

### Unresolved cross-notice identity collision

The report contains two different issuer references with scrip code `544770`:

| Extracted issuer | Referenced listing notice | Extracted listing date | Index notice PDF |
| --- | --- | --- | --- |
| MERRITRONIX LIMITED | `20260605-37` | `2026-06-08` | `20260608-14.pdf` |
| YAASHVI JEWELLERS LIMITED | `20260601-25` | `2026-06-02` | `20260602-17.pdf` |

These are **unresolved extracted candidate facts**, not independently verified exchange identities or publication-ready IPO records. Both references remain in the read-only report. The parser's within-notice conflict checks do not resolve this cross-notice collision. Do not choose one by name length, newest date, or last-wins. Recheck both original PDFs and their issuer-specific official BSE listing notices before accepting either mapping.

## Data and safety review

This batch did not edit recovery manifests, `data/ipos.json`, `data/bse-ipo-sources.json`, field values, evidence histories or UI assets. It did not relax issuer-specific BSE listing-evidence requirements or reinsert BSE auditing into hourly live sync. No spending or permission expansion was introduced. The hourly NSE/SEBI sync was not rerun as part of this repair's verification; its code was unchanged.

## Remaining blockers and next task

1. Verify up to 15 candidate issuers against their issuer-specific official BSE listing notices, prioritizing unambiguous identities from the retained report. Keep the two `544770` references on hold until reconciled. Only then update retained source evidence and rebuild the public dataset.
2. Keep index admission dates separate from listing dates. Do not promote unmatched index candidates solely because parsing succeeded.
3. The audit still selects the latest 20 eligible notices; older-notice progress needs a separate durable, versioned cursor. The other 216 eligible notices were not processed in this batch. Do not repeatedly rescan the same latest notices and call it historical completion.
4. Full 2020–2026 BSE coverage and many historical fields remain incomplete. Generate coverage from current recovery files, rather than using old README counts.

## Prior history

The previous full project-status log is preserved byte-for-byte in [archive/PROJECT_STATUS-before-bse-notice-repair.md](archive/PROJECT_STATUS-before-bse-notice-repair.md). The previous README handoff is in [archive/README-before-bse-notice-repair.md](archive/README-before-bse-notice-repair.md). These are historical milestones; this document and current code/run evidence supersede their stale next-task instructions.
