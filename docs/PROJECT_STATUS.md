# Project status and handoff

Updated: 2026-09-24 UTC. Current batch: PR #167, remaining 12 BSE listing candidates.

## Priority and scope

Continue P1/P2/P3 backend correctness, official-source coverage and dependable publication under `DEVELOPMENT_PROCESS.md`. Lot Size only; minimum investment, UI redesign, research-depth expansion and commercial infrastructure remain out of scope. Never derive prices, dates or INR issue sizes from index membership or arithmetic.

Base inspected: `421df24f0393cde3238df560f6f1bbf5f847ddd8`. PR #166 was already merged at `2eb53e62747fe2d873c3a658fd3e7ca0b0a971c2`. Its former pending-publication handoff was stale: a fresh deployed-data snapshot fetched at `2026-09-24T02:11:34.796Z` contains **937 records and all previous 15 listings/45 reviewed facts**. Those records are not repeated in the new batch.

## New bounded source verification

Exactly the 12 remaining unambiguous references from original discovery report `35939161246` were pinned in `data/discovery/bse-listing-candidates-2026-09-24-batch-02.json`. The two disputed code-544770 references remain excluded. No candidate was added during retries.

Initial source run `35945780782` downloaded all 12 genuine listing PDFs and verified 11. Leapfrog's PDF renders “effective” but pdftotext drops the ff ligature, producing `e ective from`. This was a text-extraction defect, not a disagreement about its June 24 listing date. Verifier 1.2.0 accepts only the observed label variant and preserves its original text verbatim in field evidence; candidate identity/date, range and conflict guards remain enforced.

Successful live verification `35946186883` completed: **12 verified, 0 rejected, 0 unavailable**. All 12 PDF hashes exactly match the first downloads. Both header and fact pages of all 12 documents were rendered and reviewed; all 36 facts cite PDF page 2. Local replay of the actual PDF bytes and retained excerpts agrees with the source report.

| Issuer | BSE listing notice | Listing date | Market lot | Issue price (INR/share) |
| --- | --- | --- | ---: | ---: |
| CRAZY SNACKS LIMITED | 20260702-44 | 2026-07-03 | 3,000 | 42 |
| LIOTECH INDUSTRIES LIMITED | 20260623-33 | 2026-06-24 | 400 | 321 |
| Leapfrog Engineering Services Limited | 20260623-30 | 2026-06-24 | 6,000 | 23 |
| Diksha Polymers Limited | 20260623-31 | 2026-06-24 | 1,200 | 112 |
| HORIZON RECLAIM (INDIA) LIMITED | 20260618-28 | 2026-06-19 | 1,200 | 103 |
| Susan Electricals India Limited | 20260617-35 | 2026-06-18 | 1,000 | 127 |
| Vahh Chemicals Limited | 20260610-34 | 2026-06-11 | 2,000 | 60 |
| UHM Vacation Limited | 20260610-44 | 2026-06-11 | 800 | 166 |
| SMR Jewels Limited | 20260605-45 | 2026-06-08 | 1,000 | 128 |
| Aureate Tradde Limited | 20260604-33 | 2026-06-05 | 2,000 | 70 |
| Rajnandini Fashion India Limited | 20260602-37 | 2026-06-03 | 2,000 | 63 |
| Harikanta Overseas Limited | 20260601-23 | 2026-06-02 | 1,200 | 91 |

## Publication implementation

- `data/verified-bse-listings/2026-09-24-batch-02.json` retains independently reviewed source URLs, PDF hashes, actual collection/publication times, identity pages, original normalized excerpts and explicit facts.
- `approved-batches.json` explicitly registers both reviewed batches. There is no automatic directory scan or promotion of unreviewed discovery reports.
- The existing offline importer validates all registered batches before writing, rejects cross-batch identity collisions and unsafe/mismatched paths, and records each record's actual batch path.
- Historical verifier-1.1.0 evidence remains versioned 1.1.0 and is revalidated by the current parser; it is not relabeled or retimestamped. Unknown versions are rejected.
- Existing/concurrent records, field corrections and unsupported nulls are never overwritten. The hourly sync still uses the existing semantic publication path; no extra PDF network work is added to it.
- The independent verification artifact now retains a tracked-source snapshot for reproducible local tests and a separately timestamped deployed-data snapshot. Both are read-only; permissions remain unchanged.

## Tests and diff review

All **36 local test scripts** passed using the actual archived repository modules, without matcher substitutes. This includes the existing suites, the observed text-regression tests, pinned 12-candidate/disjointness checks, approved-registry path binding, cross-batch conflict rejection, full-batch validation before mutation, provenance and idempotency.

The real importer/publisher/validators were rehearsed in an isolated copy: **937 -> 949 records**, with all **937 existing public records byte-equivalent as JSON values**, no changes to any other year manifest, and an identical second import/rebuild. The 2026 count rises from 53 to 65 on this inspected baseline. Remote CI runs the same rehearsal before merge.

No hand-edit to `data/ipos.json`, recovery manifests, original reviewed batch, BSE source manifest or UI assets is included in this development commit. Handoff history is preserved in `docs/archive/PROJECT_STATUS-before-bse-remaining-batch.md`.

## Release checkpoint

Source verification and local tests are complete. Final PR CI, merge, production bot publication and deployed verification are **pending** at this checkpoint. Do not label the 12 records live until the source-backed data revision and actual deployed data are checked. Replace this paragraph with observed run IDs/results after release.

## Evidence retention

Initial collection: run `35945780782`, artifact `10786259323`, ZIP SHA-256 `3ce203c0513289a09614fb3d6d9d927e4868036a3ef297bc92a55e8ee7792c10`.

Successful verification: run `35946186883`, artifact `10787195768`, ZIP SHA-256 `8a0a777a7c29dfef19da9e6549aa1f626b070dccfae6d395333e8d6e294b9612`. This includes all 12 original PDFs, failed HTML responses, report, source snapshot and deployed baseline. It expires on `2026-10-08T02:11:52Z`; conversation copies are retained. No PDF is replaced by an index notice or third-party mirror.

## Remaining blockers and next task

After verified publication, 27 of the original 29 discovery references will have independently verified listings. The remaining two, **MERRITRONIX LIMITED** and **YAASHVI JEWELLERS LIMITED**, both claim code `544770` in index references. Reconcile their original index PDFs and issuer-specific listing notices before accepting either mapping; never use last-wins or a name-length heuristic.

Then add a durable, parser-versioned cursor for the other **216 eligible older index notices**. The latest-20 audit is not a historical completion claim. Full 2020-2026 BSE universe coverage and many historical fields remain incomplete.

Do not repeat the completed Angular-shell, empty-detail, plural-clause, listing-header or missing-ff diagnoses. Recover unsupported price bands, offer dates and INR issue sizes only from new explicit official evidence.

## Prior handoffs

PR #166's full source-review history is preserved in `archive/PROJECT_STATUS-before-bse-remaining-batch.md`. Earlier handoffs remain unchanged under `docs/archive/`. Current code, deployment data and this handoff supersede stale checkpoints in those archives.
