# Live IPO automation

## Goal

The public tracker should discover newly announced/open IPOs without requiring a manual data-recovery prompt before they appear on the website.

The automated source pipeline now has two layers:

1. official NSE public IPO feeds for discovery/basic offer terms;
2. official SEBI public-issue listings for offer-document attachment.

## Official discovery endpoints

The collector reads:

- `https://www.nseindia.com/api/all-upcoming-issues?category=ipo`
- `https://www.nseindia.com/api/ipo-current-issue`

These are public NSE website endpoints used by NSE's IPO market-data pages. They are not treated as a substitute for later offer-document recovery.

## Official SEBI document endpoints

The document-enrichment step reads SEBI's public lists for:

- RHP filings: `https://www.sebi.gov.in/sebiweb/home/HomeAction.do?doListing=yes&sid=3&smid=11&ssid=15`
- Final offer documents / Prospectus: `https://www.sebi.gov.in/sebiweb/home/HomeAction.do?doListing=yes&sid=3&smid=12&ssid=15`
- General filings view for current public-issue coverage: `https://www.sebi.gov.in/sebiweb/home/HomeAction.do?doListingAll=yes&sid=3`
- Mixed Public Issues listing: `https://www.sebi.gov.in/sebiweb/home/HomeAction.do?doListing=yes&sid=3&ssid=15`

For a matched RHP filing page, the collector also looks for an official SEBI Abridged Prospectus link under `/sebi_data/commondocs/`.

The collector reads the dedicated RHP/final lists, SEBI's current general Filings page, and the mixed Public Issues listing. The general page closes a coverage gap where very recent public-issue entries can appear there before the dedicated subtype page exposes them consistently to the raw HTML fetcher. Duplicate filing URLs are deduplicated before matching.

After that pass, it runs a bounded targeted SEBI search for the newest sparse records that:

- were originally discovered by the NSE live feed; and
- still have no retained SEBI document.

The targeted fallback uses SEBI's server-side search endpoint and is capped at 12 issuers per run. It searches with one stable issuer token rather than the full company phrase because SEBI's search endpoint is token-oriented. Generic corporate words such as `Limited`, `India`, `Industries`, `Services`, and `Engineering` are excluded when choosing the token. Search failures are logged and skipped; deterministic full-issuer matching is still required before any document is attached.

Historical backfill remains a separate recovery task.

## SEBI issuer matching

SEBI filings are attached only when issuer matching is deterministic.

Matching rules:

- normalize punctuation, whitespace and `Ltd.` / `Limited`;
- preserve meaningful issuer words;
- allow a controlled alternate for a parenthetical `(India)` suffix, e.g. `Adroit Industries (India) Limited` ↔ `Adroit Industries Limited`;
- require exactly one recovery record to match;
- skip ambiguous or unmatched entries rather than guessing.

Addenda, corrigenda, DRHP/UDRHP records are not included in this initial matcher.

## Schedule

`.github/workflows/update-ipos.yml` runs hourly at minute 17 and may also be run manually.

The workflow:

1. checks out `main`;
2. tests the feed parser;
3. fetches the NSE live feeds;
4. merges new source-backed records into the recovery manifest;
5. fetches the latest official SEBI RHP/final-offer-document lists;
6. attaches deterministic RHP / Abridged Prospectus / Prospectus evidence from the latest lists;
7. runs bounded issuer-specific SEBI search for sparse NSE-live records still missing SEBI evidence;
8. rebuilds `data/ipos.json`;
9. validates the data contract;
10. commits only if source-backed data changed;
11. the resulting push triggers the existing GitHub Pages deployment workflow.

If NSE collection or validation fails, the workflow fails before committing. The previously published website remains intact.

## Fields that may be automated from the NSE live feed

Only explicit source values are accepted:

- issuer name;
- NSE symbol / series in recovery metadata;
- board from the official NSE series:
  - `EQ` → Mainboard
  - `SME` → SME
- lifecycle status from the official feed:
  - Active → open
  - Forthcoming → upcoming
  - Closed/Past → closed
- price band when NSE explicitly provides a range;
- fixed issue price when NSE explicitly provides one value;
- market lot when NSE explicitly provides `lotSize`;
- issue open date;
- issue close date.

## Fields intentionally not derived

The collector does **not**:

- map NSE `issueSize` into `issue_size_inr` because the feed value is not an INR amount;
- copy market lot into minimum bid quantity;
- compute minimum application amount;
- infer sector;
- invent listing date;
- infer missing final issue price from the cap of a price band.

Those fields remain null/missing until supported by retained official evidence.

## Enrichment strategy

The live feed is the discovery layer, not the final research layer.

After discovery, deeper recovery can attach:

- SEBI RHP / Abridged Prospectus;
- price-band advertisements;
- final Prospectus;
- issuer / registrar disclosures;
- additional NSE/BSE official evidence.

Existing richer evidence is preserved. The live collector fills missing values and lifecycle status but does not silently overwrite a conflicting retained price band.

## Year rollover

The collector writes each issue to `data/recovery/<year>/nse-issue-information.json` based on the official issue start date.

The publication builder reads all year manifests, so a new calendar year does not require hard-coding a new published-data path.

## Fields changed by SEBI document sync

The SEBI document layer currently changes **document evidence only**.

It may attach:

- `SEBI RHP filing`;
- `SEBI Abridged Prospectus`;
- `SEBI Prospectus filing`.

It does not yet parse those documents into final issue price, issue size, minimum application amount, listing date, sector, or other market fields.

This separation is intentional: document discovery/matching is verified first, then field extraction can be added as a later bounded source-family batch with its own tests and precedence rules.

## Failure behavior

- If the SEBI listing page cannot be fetched after retries, the scheduled workflow fails before committing.
- If a SEBI listing page is fetched but contains zero parseable expected filings, the workflow fails rather than silently treating that as "no documents".
- If a matched RHP detail page cannot be fetched, the RHP filing itself may still be retained; only the optional Abridged Prospectus attachment is skipped for that run.
- Re-running the collector is idempotent: existing document URLs/identities are not duplicated.

## Production verification — 2026-09-22

The SEBI document pipeline has been exercised against the real network from GitHub Actions.

Implementation/reliability sequence:

- PR #10 introduced the SEBI layer.
- The first network run exposed dynamic-link markup not covered by the fixture parser.
- PR #11 repaired dynamic/raw filing URL parsing.
- PRs #12–#15 added bounded sparse-record search and additional official current-listing coverage.

Latest verified production run:

- workflow: `Sync live IPO data`
- run ID: `35685494607`
- head: `86a828f2199abfc0c3f172ebf95af224f34e65fd`
- conclusion: success

Latest SEBI statistics:

- 9 deterministic matches from current listing sources;
- 37 unmatched listing entries;
- 9 sparse NSE-live issuers searched;
- 5 filing results parsed from targeted searches;
- 0 exact targeted issuer matches;
- 0 new documents added in that run.

The 9 direct-list matches correspond to already-retained evidence. The sparse NSE-live records remain without SEBI documents.

This is treated as a source-coverage limitation. The matcher must not be loosened to increase the attachment count.

Future work should prefer either:

- an independently reliable official source family for those sparse records; or
- field extraction from official documents already retained.

Repeated endpoint variants are not the current recommended priority.

## Abridged Prospectus field extraction — production verified

The next enrichment layer parses **only explicit aggregate issue/offer size** from already-retained official SEBI Abridged Prospectus PDFs.

Implementation:

- script: `scripts/extract-abridged-fields.mjs`;
- PDF text engine: Poppler `pdftotext`;
- scope: page 1 only;
- source documents: retained `SEBI Abridged Prospectus` PDF URLs on `sebi.gov.in`;
- target field: `issue_size_inr`;
- precedence: fill missing values only; never overwrite an existing issue-size value.

The parser looks for the visual table column headed `TOTAL OFFER SIZE` or `TOTAL ISSUE SIZE` and accepts only an explicit numeric amount expressed in millions.

Examples covered by fixtures:

- Karamtara Engineering: explicit total offer size ₹8,750.00 million → extract;
- ESDS Software Solution: explicit total issue size ₹7,200.00 million → positive parser case;
- Pranav Constructions: total offer size contains `[●]` → preserve null;
- ARCIL: total offer size contains `[●]` → preserve null.

The extractor does **not**:

- add Fresh Issue + OFS components;
- infer total value from number of shares × price;
- use the price-band cap as final price;
- overwrite an existing retained issue size;
- treat placeholders as zero.

When a value is extracted, the recovery manifest retains:

- the INR integer value;
- the exact source amount text;
- page 1 as evidence location;
- official document URL/type/identity/publication date;
- the extraction collection timestamp.

If a PDF is inaccessible or the value is not explicit, the field remains null and the hourly workflow continues.

GitHub Actions installs `poppler-utils` explicitly before running this extractor so the PDF-text dependency is visible and reproducible.

### Production result — issue-size extraction

Production workflow run `35686786294` verified the first field-extraction family end to end.

Statistics:

- 4 missing-size records had retained SEBI Abridged Prospectus PDFs;
- all 4 PDFs downloaded successfully;
- 1 explicit total-size value was extracted;
- 3 remained null because the total-size value was a placeholder or otherwise not explicit;
- 0 PDF fetch errors.

Karamtara Engineering was enriched from page 1:

- source text: `₹8,750.00 million`;
- stored value: `8750000000`;
- source type: `SEBI Abridged Prospectus`;
- publication date: 2026-09-03;
- page: 1.

The resulting source-backed data commit is
`92f0f024367b20a9f023218a0cb92ecbc2e38636`.

This run confirms that PDF field extraction can operate conservatively in the hourly workflow without filling placeholder values or overwriting richer existing evidence.

## Final Prospectus PDF resolution

For a retained SEBI final Prospectus filing page, the document collector now also inspects the filing detail page for the official attached PDF.

SEBI often exposes the attachment through its viewer form:

```
https://www.sebi.gov.in/web/?file=<encoded official PDF URL>
```

The resolver:

- extracts the `file=` target;
- accepts only HTTPS URLs on `sebi.gov.in` / `www.sebi.gov.in`;
- requires the path to be under `/sebi_data/attachdocs/`;
- requires a PDF extension;
- stores the direct PDF as `SEBI Prospectus PDF`;
- deduplicates viewer and direct-link forms of the same attachment;
- rejects non-SEBI mirrors.

This stage attaches evidence only. It does not yet parse final issue price, aggregate issue size, listing date, or any other field from the final Prospectus PDF.

## Prospectus PDF production verification — 2026-09-22

Direct final-Prospectus attachment resolution is production-verified.

- PR: #17
- merge: `cd39442c03450a9189d783d554e3feb48ee57239`
- live sync run: `35687483282`
- result: success
- bot data commit: `0c3e1c199fdb12266589c7f65eead373c49065dd`

The run resolved 9 direct official `SEBI Prospectus PDF` attachments from already-retained final filing pages.

The resolver itself changed no market fields. Review of the bot diff confirmed only document evidence, per-record collection freshness, and generation timestamps changed.

This closes the attachment dependency needed for the next bounded extraction family. Final Prospectus field parsing must remain separate and independently tested before it is allowed to write final issue price or aggregate issue size.
