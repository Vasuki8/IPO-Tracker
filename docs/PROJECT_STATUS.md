# PROJECT STATUS

Last updated: 2026-09-22

## Current state

IPO Tracker now has a working **automated official-source discovery and publication loop**.

The published 2026 dataset contains **23 real IPO issuers** after the first production live-sync run.

The source-first rules remain enforced: unsupported values stay null rather than being inferred, estimated, reconstructed, or copied from aggregators.

## Latest completed batch — live IPO automation

### Pull request

PR #9 — `Automate live IPO discovery and publication`

Squash-merged to `main`:

`8a6895d34bd64c2600c6e82bec29418e399fa366`

### Automation added

`.github/workflows/update-ipos.yml` now runs hourly at minute 17 and can also run manually.

The workflow:

1. tests the live-feed parser;
2. collects official NSE current/upcoming IPO data;
3. merges explicitly supported values into retained recovery manifests;
4. rebuilds `data/ipos.json`;
5. verifies deterministic publication;
6. validates the IPO data contract;
7. commits only when source-backed data changed.

The resulting data commit is then published by GitHub Pages.

### First production run

The first live run succeeded from GitHub Actions.

Collector run:

- workflow: `Sync live IPO data`
- run ID: `35683653409`
- conclusion: success

The run successfully completed:

- live-feed parser tests;
- real NSE collection;
- published-data rebuild;
- deterministic publication check;
- data-contract validation;
- source-backed data commit.

Bot-generated commit:

`87c52215fcdbaa079b937597fe902a13309e22d2`

Commit message:

`chore(data): sync live NSE IPO feed`

### Dataset result

Before live sync: **14 issuers**

After live sync: **23 issuers**

Newly added:

1. Adroit Industries (India) Limited
2. ArMee Infotech Limited
3. Axiom Gas Engineering Limited
4. Coreintegra Consulting Services Limited
5. Elevate Campuses Limited
6. National Stock Exchange of India Limited
7. Pooja Logistics Limited
8. Swastika Infra Limited
9. Varmora Granito Limited

Existing-record enrichment:

- Sonaselection India Limited received official NSE board/status evidence and lifecycle status was updated to closed.

### Data-safety audit

The bot-generated diff was reviewed after the real collection.

For newly discovered records:

- `issue_size_inr` remained null;
- `minimum_bid_quantity` remained null unless retained elsewhere;
- `minimum_application_amount_inr` remained null;
- final issue price remained null unless explicitly supplied as a fixed price;
- no sector/listing date was guessed;
- explicit NSE price bands and dates were retained with source evidence;
- explicit SME market lots were retained where the feed supplied them.

The collector does not treat NSE's `issueSize` field as an INR issue-size value.

### Publication verification

GitHub Pages successfully published the bot-generated data revision:

- Pages run ID: `35683671138`
- deployed head: `87c52215fcdbaa079b937597fe902a13309e22d2`
- conclusion: success

Direct retrieval of the Pages URL remains unavailable from the development web reader, so workflow revision/deployment evidence is used for verification.

## Automation source

Current automated discovery source family:

- official NSE upcoming IPO website feed;
- official NSE current IPO website feed.

See `docs/AUTOMATION.md`.

This source is the **discovery / basic-terms layer**, not the final document-research layer.

## Data integrity rules currently enforced

- Published schema version: `1.1.0`.
- `data/ipos.json` must exactly match retained recovery manifests.
- Verified values require retained evidence.
- Missing fields keep `value: null`.
- Non-null board/status values require companion provenance.
- Existing evidence collection timestamps are preserved.
- `last_collected_at` is tracked per record.
- Unsupported source hosts are rejected by the publisher.
- Market lot, minimum bid quantity, and minimum application amount remain separate concepts.
- Live-feed enrichment may not relabel older manual term evidence as live-feed evidence.
- Price-band conflicts are not silently overwritten.

## Tests

The automation batch added tests for:

- NSE date parsing;
- price-band parsing;
- fixed-price parsing;
- Mainboard/SME mapping;
- lifecycle status mapping;
- merging upcoming/current feed data;
- new-record construction;
- preservation of unsupported null fields;
- manual-source provenance protection;
- safe enrichment of records originally discovered by the live feed;
- deterministic multi-year publication.

PR/branch validation passed before merge, and the real production network run passed after merge.

## Earliest unfinished priority

P1/P2 — data correctness and source evidence depth.

New IPO discovery is now automated, but newly discovered IPOs may have sparse detail until richer official documents are attached.

## Recommended next coherent batch

Automate official offer-document discovery/enrichment for newly discovered IPOs.

Start with a bounded SEBI source family capable of matching new NSE-discovered issuers to:

- RHP;
- Abridged Prospectus;
- Prospectus / other relevant final filing.

Requirements:

- deterministic or explicitly reviewed matching;
- retain document identity, URL and publication date;
- preserve ambiguous matches rather than guessing;
- extract only fields supported by directly retained official evidence;
- test across multiple issuers;
- integrate safely with the hourly collector.

## Publication history

- PR #1: source-backed data foundation
- PR #2: first 2026 recovery batch
- PR #3: deepen Hero Motors and Rentomojo evidence
- PR #4: recover Rentomojo final Prospectus terms
- PR #5: second official-source 2026 IPO batch
- PR #6: third official-source 2026 IPO batch
- PR #7: fourth official-source 2026 IPO batch
- PR #8: fifth official-source 2026 IPO batch
- PR #9: automated live IPO discovery and publication
