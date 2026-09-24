# Project status and handoff

Updated: 2026-09-24 UTC (September 23 in America/Toronto).

## Current priority

Continue P1/P2/P3 backend correctness, official-source coverage and dependable publication under `DEVELOPMENT_PROCESS.md`. The active application-term requirement is **Lot Size only**; minimum investment, UI redesign, research-depth expansion and commercial infrastructure remain out of scope.

Never infer missing IPO values. Keep listing date, index admission date, market lot, minimum bid quantity and application amount distinct.

## Latest completed batch: remaining 12 verified BSE SME listings

PR #168, **Verify and recover remaining 12 BSE SME listings**, merged at:

`39ead2287b9352953d43b24ec9a006ab21f0d72a`

This batch completed the remaining unambiguous issuer references from the original 29-reference BSE SME addition-notice report. Together with PR #166's first 15 records, **27 independently reviewed BSE listing records from that report are now retained and published**.

The two disputed code-`544770` references remain excluded:

- MERRITRONIX LIMITED — referenced listing notice `20260605-37`
- YAASHVI JEWELLERS LIMITED — referenced listing notice `20260601-25`

Do not choose one by recency, name similarity or last-wins logic.

### Batch-2 source verification

Pinned input:

`data/discovery/bse-listing-candidates-2026-09-24-batch2.json`

Successful issuer-specific source verification:

- workflow run: `35946970931`
- attempted: **12**
- verified: **12**
- rejected: **0**
- unavailable: **0**
- artifact: `10787446306`
- artifact SHA-256: `4d93a865acc52cebd8b57e6d00668b722b6182c79aa8d2b874b9864dc57e1863`

The artifact contains all 12 official BSE listing PDFs plus the verification report. Exact reviewed evidence is retained in:

`data/verified-bse-listings/2026-09-24-batch2.json`

Only explicit issuer-specific PDF facts are retained:

- listing date;
- market lot;
- final issue price.

No price band, offer dates, monetary issue size, minimum bid quantity or application amount is inferred.

### Reliability repairs in PR #168

The batch also repaired two reusable verifier issues:

1. **PDF rejection classification**
   - a successfully downloaded official PDF that fails identity verification is now classified as `rejected`, not left as `unavailable`;
   - HTML-attempt metadata is preserved separately.

2. **BSE PDF ligature text**
   - Leapfrog Engineering Services' official PDF extracts `effective` as `e ective`;
   - the listing-date grammar now accepts only that bounded PDF-text form in addition to normal `effective from`;
   - `Effective at the open ...` remains rejected so index-admission dates cannot become listing dates.

The first post-fix run demonstrated the distinction: an earlier run produced 11 verified + 1 rejected; after the bounded ligature repair the same source family produced 12/12 verified.

### Multi-batch reviewed importer

`scripts/apply-verified-bse-listings.mjs` now loads multiple approved manifests under `data/verified-bse-listings/`.

For every batch it still:

- revalidates committed page excerpts and PDF facts;
- requires the matching approved discovery batch;
- uses no network in the live import step;
- creates missing records only;
- never overwrites an existing or conflicting identity;
- preserves field/source hashes, page evidence and collection timestamps;
- remains idempotent on rerun.

PR validation passed for both the reviewed-evidence importer and the full data contract.

## Production publication verification

Merge-triggered live sync:

- workflow run: **`35947297162`**
- conclusion: **success**
- reviewed BSE import step: **success**
- semantic publication: **success**

The live workflow measured:

- `added_records: 12`
- `changed_records: 27`
- `removed_records: 0`

The additional changed records came from the normal concurrent NSE/SEBI historical/live enrichment in the same source-first run; the semantic merge preserved those concurrent changes.

Source-backed data commit:

`1d7ffff145b99cf045b6954028d595105a1522fb`

Production build after semantic merge:

- **949 total published IPO records**
- **65 records for 2026**
- schema/core validation: passed
- deterministic recovery build check: passed
- operator health at completion: healthy

The prior production state had 53 records for 2026, so this batch accounts for exactly the expected **+12**.

The 2026 recovery diff retains batch-2 provenance through:

`data/verified-bse-listings/2026-09-24-batch2.json`

and shows unsupported raw terms such as price band, open/close dates and minimum bid quantity remaining null for these new BSE-only records.

### Deployment

GitHub Pages build `35947797703` completed successfully on commit:

`1d92710098fcf9b492a572eb6424e2c434153e93`

That commit is a descendant of the source-backed data revision `1d7ffff145b99cf045b6954028d595105a1522fb`, so the deployed Pages build includes the 12 newly published BSE records.

## Reviewed batch-2 facts

| Issuer | BSE listing notice | Listing date | Market lot | Issue price (INR/share) |
| --- | --- | --- | ---: | ---: |
| Crazy Snacks | 20260702-44 | 2026-07-03 | 3,000 | 42 |
| Liotech Industries | 20260623-33 | 2026-06-24 | 400 | 321 |
| Leapfrog Engineering Services | 20260623-30 | 2026-06-24 | 6,000 | 23 |
| Diksha Polymers | 20260623-31 | 2026-06-24 | 1,200 | 112 |
| Horizon Reclaim (India) | 20260618-28 | 2026-06-19 | 1,200 | 103 |
| Susan Electricals India | 20260617-35 | 2026-06-18 | 1,000 | 127 |
| Vahh Chemicals | 20260610-34 | 2026-06-11 | 2,000 | 60 |
| UHM Vacation | 20260610-44 | 2026-06-11 | 800 | 166 |
| SMR Jewels | 20260605-45 | 2026-06-08 | 1,000 | 128 |
| Aureate Tradde | 20260604-33 | 2026-06-05 | 2,000 | 70 |
| Rajnandini Fashion India | 20260602-37 | 2026-06-03 | 2,000 | 63 |
| Harikanta Overseas | 20260601-23 | 2026-06-02 | 1,200 | 91 |

## Release reliability follow-up: Pages publication-state race

During final handoff publication, GitHub Pages deployment for README commit `ad62e44ad85c60a0910a6df1e9212349f559c0bc` itself succeeded, but workflow run `35948066974` ended red because its final `ops/pages-publication.json` commit conflicted while rebasing over another Pages-health update.

PR #169 repaired only that operational-state race:

- merge commit: `180087143d3fb986d0413c62c2fdb5a2da69909f`;
- the workflow now resets to the latest `origin/main`, recomputes Pages state against the newest committed state, validates the operational schema, and retries the push up to three times;
- CI forbids returning to the old "modify JSON then rebase" pattern.

Production deployment run `35948287263` completed **successfully**, including the formerly failing status-persistence step. Durable Pages state was committed as `45b2f22a4f5d3a7b8416133a0b7eeab6fc580b5a` and records:

- deployment status: success;
- deployed commit: `180087143d3fb986d0413c62c2fdb5a2da69909f`;
- completion: `2026-09-24T02:41:40Z`;
- page URL: `https://vasuki8.github.io/IPO-Tracker/`.

This was an operational metadata repair only; no IPO value or recovery evidence was changed.

## Remaining BSE blockers and next task

### 1. Resolve the code-544770 identity collision

The next bounded P1/P2 task should independently inspect both original index-addition PDFs and both issuer-specific BSE listing notices for:

- MERRITRONIX LIMITED
- YAASHVI JEWELLERS LIMITED

Both currently claim BSE scrip code `544770` in retained discovery evidence. Preserve both pieces of evidence until an authoritative issuer/listing source resolves the discrepancy. Do not materialize either candidate from index evidence alone.

### 2. Add durable historical BSE notice progress

The original BSE catalog contained **236 eligible SME addition notices**. The completed discovery audit processed only the latest 20; **216 older notices remain outside that audit batch**.

After the 544770 conflict is addressed, build a durable parser-versioned cursor so historical BSE notice recovery progresses through older notices without rescanning the newest 20 each run.

Current BSE index membership is still only a discovery aid; it is not proof of complete historical IPO coverage.

## Prior handoffs

- First reviewed 15-record BSE listing batch: `archive/PROJECT_STATUS-before-bse-listing-batch2.md`
- PR #165 discovery/notice-repair state: `archive/PROJECT_STATUS-before-bse-listing-batch.md`
- Older accumulated milestones remain under `docs/archive/`.

Current repository, workflow and deployment evidence supersede stale next-task instructions in archived handoffs.
