# Live IPO automation

## Goal

The public tracker should discover newly announced/open IPOs without requiring a manual data-recovery prompt before they appear on the website.

The automated source pipeline now has four bounded layers:

1. official NSE public IPO feeds for discovery/basic offer terms;
2. official SEBI public-issue listings for offer-document attachment;
3. explicit aggregate issue-size extraction from retained SEBI Abridged Prospectus PDFs;
4. explicit final issue-price extraction from retained SEBI Prospectus PDFs;
5. explicit aggregate issue-size extraction from retained SEBI Prospectus PDFs.

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
8. tests and runs bounded PDF field extractors against already-retained official documents;
9. rebuilds `data/ipos.json`;
10. validates the data contract;
11. commits only if source-backed data changed;
12. the resulting push triggers GitHub Pages publication.

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

## Fields changed by SEBI document sync and extractors

The SEBI **document attachment** step still changes document evidence only. It may attach:

- `SEBI RHP filing`;
- `SEBI Abridged Prospectus`;
- `SEBI Prospectus filing`;
- `SEBI Prospectus PDF`.

Field extraction remains a separate stage with separate tests and precedence rules.

Currently automated document-derived fields are limited to:

- explicit aggregate `issue_size_inr` from supported Abridged Prospectus first-page total-size cells;
- explicit final `issue_price` from supported wording in retained final Prospectus PDFs;
- explicit aggregate `issue_size_inr` from supported top-level Offer/Issue wording in retained final Prospectus PDFs.

Minimum application amount, listing date, sector and other unsupported document-derived fields remain null until a separately tested source family is added.

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

This closes the attachment dependency for bounded final-document field extraction.

## Final Prospectus issue-price extraction — production verified

PR #18 added a separate extractor for **explicit final issue price** from retained official SEBI Prospectus PDFs.

Implementation:

- script: `scripts/extract-prospectus-fields.mjs`;
- PDF text engine: Poppler `pdftotext`;
- scope: PDF pages 1–20;
- source documents: retained `SEBI Prospectus PDF` URLs under `sebi.gov.in/sebi_data/attachdocs/`;
- target field: `issue_price`;
- precedence: fill missing values only; never overwrite retained issue-price evidence.

The parser accepts only explicit `Offer Price` / `Issue Price` wording with a rupee amount per Equity Share. It does not inspect the price-band cap to choose a final price.

Production workflow run `35688500637` completed successfully.

Statistics:

- candidates: 7;
- PDFs downloaded: 7;
- extracted: 4;
- no supported explicit price found: 3;
- fetch errors: 0.

Extracted:

- Kanohar Electricals Limited — ₹632 — PDF page 7;
- LCC Projects Limited — ₹146 — PDF page 7;
- Manipal Payment and Identity Solutions Limited — ₹339 — PDF page 3;
- Pranav Constructions Limited — ₹124 — PDF page 5.

Preserved as null:

- Jindal Supreme (India) Limited;
- SS Retail Limited;
- Veegaland Developers Limited.

Existing Hero Motors and Rentomojo issue-price evidence was not overwritten.

The resulting source-backed data commit is `f9b7155c42d8b44d6985d9dafb9fd242e37dc64e`. GitHub Pages deployment for that revision passed in run `35688893344`.

### Cover-price wording repair

A one-run read-only diagnostic (PR #20, production run `35689468724`) showed that the remaining three null values were not outside the 20-page boundary. Their official Prospectus covers used a reverse-labelled form where the amount comes first and the field label follows:

`at a price of ₹X per Equity Share ... (Offer Price/Issue Price)`

PR #21 added only this explicit form, including a bounded footnote marker after the amount, while requiring the nearby Offer/Issue Price label. An unlabeled generic `price of ₹X per Equity Share` remains rejected.

Production run `35690054143` recovered all three remaining values with zero fetch errors:

- Jindal Supreme (India) Limited — ₹93 — PDF page 3;
- SS Retail Limited — ₹424 — PDF page 3;
- Veegaland Developers Limited — ₹140 — PDF page 2.

The source-backed bot commit is `51f806b16e4eba40efee304d07bb5753a8e0f9d9`.

The temporary deep diagnostic step was removed from the hourly workflow. The production extractor remains bounded to pages 1–20 and fill-missing-only behavior.

All 9 records currently carrying retained `SEBI Prospectus PDF` evidence now have final issue-price evidence.

## Final Prospectus aggregate issue-size extraction — production verified

PR #23 used a temporary read-only diagnostic to inspect the seven retained final Prospectuses with missing `issue_size_inr`. The source documents showed explicit top-level totals on pages 2–3 alongside smaller Fresh Issue/OFS component amounts.

PR #24 added a separate aggregate-size extractor with these rules:

- source: retained official `SEBI Prospectus PDF` only;
- scope: PDF pages 1–20;
- accept only explicit overall Offer/Issue totals;
- support million, lakh and crore units;
- fill missing `issue_size_inr` only;
- reject Fresh Issue-only and OFS-only amounts;
- never add components;
- never derive amount from shares × price.

Production run `35691580621` succeeded:

- candidates: 7;
- downloaded: 7;
- extracted: 7;
- explicit-size missing: 0;
- fetch errors: 0.

The resulting source-backed data commit is `0110d864235eccb800efa5b206fa19bf9cdb0fb4`, and GitHub Pages deployment run `35692087146` passed.

All 9 retained final-Prospectus records now have both final issue price and aggregate issue-size evidence.

Across the full 23-record dataset, `issue_size_inr` coverage is now 11 present / 12 missing. The next P1 work should continue issue-size recovery from a different reusable official source family for those remaining 12 records; the completed final-Prospectus extractor should not be broadened to infer missing values.

## SEBI RHP freshness and direct-PDF recovery — production verified

The current SEBI source layer now includes explicit freshness hardening for listing pages:

- per-run cache-busting query token;
- `Cache-Control: no-cache`;
- `Pragma: no-cache`.

This was required because GitHub Actions had continued receiving an older RHP listing while newer filings were already visible publicly.

The live SEBI RHP markup also exposed a malformed-anchor case: an RHP filing URL could be paired with adjacent Abridged Prospectus text. The parser now trusts the official filing URL slug for issuer identity only when the visible title does not classify as the same document kind. Deterministic issuer matching itself is unchanged.

Production verification:

- PR #28: listing freshness repair;
- PR #29: RHP issuer-identity repair;
- run `35693813309`: 22 deterministic latest-list matches, 8 changed records, 11 documents added;
- bot commit `ec684bc1fa558f2dafb7c7b90df6b750fc6f79ac`.

For matched RHP filing pages, the collector now also resolves official direct attachments under `/sebi_data/attachdocs/` and stores them as `SEBI RHP PDF`.

- PR #30: direct RHP PDF resolution;
- run `35694073605`: 13 RHP PDFs resolved;
- bot commit `3c2f3fb8a8737fe2067aab3e18e39ab86a68eeb6`;
- no market value was extracted by the attachment step.

After these repairs, five missing-size issuers have both retained RHP PDFs and Abridged Prospectuses. Their Abridged Prospectus total-size cells remain placeholders, so the existing extractor intentionally published no value.

The next safe field-extraction layer should use the retained RHP PDFs only with **provisional field status**. The publication builder must first preserve a retained field's provisional status instead of automatically converting every non-null retained value to verified.

## RHP aggregate issue-size diagnostic — no safe total available

PR #32 added two safety capabilities:

1. retained recovery fields may preserve `provisional` or `conflict` status through deterministic publication;
2. a read-only diagnostic can inspect retained `SEBI RHP PDF` files for explicit top-level aggregate Offer/Issue amounts.

Production run `35694934742` evaluated five missing-size RHP-backed records:

- candidates: 5;
- downloads: 5;
- parseable overall INR totals: 0;
- fetch errors: 0.

The RHPs do not provide a safe overall INR issue-size value at this stage. Some disclose share-count totals or explicit component amounts, but the overall amount remains price-dependent or placeholder-based. Examples include NSE's ₹700 million Employee Reservation Portion and Swastika Infra's ₹12,900 lakh Fresh Issue; neither is the overall Offer size.

Accordingly, no provisional `issue_size_inr` was written. The temporary diagnostic step was removed from hourly execution.

The final-document automation remains the correct upgrade path: once an official final Prospectus is retained, the existing final-Prospectus extractor can publish an explicit final aggregate amount.

The next source-depth family should focus on explicit minimum bid quantity from retained RHP/Abridged documents, without equating it to market lot absent source text.

## Minimum bid quantity recovery — production verified

Minimum bid quantity remains distinct from market lot.

Three official source stages were tested:

1. **Abridged Prospectus** — page-1 diagnostic found no explicit bid-lot wording for Adroit, NSE or Swastika.
2. **RHP** — the three documents contain `[●]` placeholders and explicitly defer the Bid Lot / minimum Bid Lot to a later price-band disclosure.
3. **Final Prospectus** — NSE's final document contains a finalized numeric Bid Lot.

The final-Prospectus extractor accepts only:

- `Bid Lot <integer> Equity Shares`;
- `Minimum Bid <integer> Equity Shares`.

It rejects:

- anchor-investor rupee minimums;
- placeholder values;
- inferred equality with market lot.

Production run `35697515918` extracted:

- National Stock Exchange of India Limited — 8 Equity Shares — PDF page 10.

The recovery record stores `minimum_bid_quantity` independently with verified SEBI final-Prospectus evidence. Deterministic publication prefers this retained document-derived field when present and otherwise keeps using explicit NSE term evidence.

Bot data commit: `2f6428c2138173a4ca02dc271100ed22412da31e`.

Published minimum-bid coverage is now 14/23.

### NSE Issue Information limitation

The rendered NSE Issue Information page is a promising official source for the remaining bid quantities, but a direct HTML fetch returns only the client application shell. Production probe `35697162672` fetched 9 page variants across Adroit, NSE and Swastika with zero network errors and zero raw-HTML bid terms.

Future automation should identify the official dynamic NSE backend endpoint used by that page rather than scrape rendered HTML.

## NSE ipo-detail minimum-bid automation — production verified

The rendered NSE Issue Information page is backed by the official JSON endpoint:

`https://www.nseindia.com/api/ipo-detail?symbol=<SYMBOL>&series=<SERIES>`

Production discovery run `35726755503` verified 10/10 live requests with zero fetch errors and established the response model:

- `issueInfo.dataList` contains static issue terms as title/value pairs;
- `bidDetails`, `activeCat`, `demandGraph` and related sections contain subscription/demand data and are not term evidence.

The minimum-bid extractor reads only `issueInfo.dataList`. Supported titles:

1. `Minimum Order Quantity` — preferred;
2. `Bid Lot` — explicit fallback.

A value is accepted only when it starts with a positive integer quantity followed by `Equity Shares`. Placeholder text is rejected. If both supported titles are present and parse to different quantities, no value is published.

The extractor:

- fills missing values only;
- never equates market lot with minimum bid;
- stores verified evidence against the exact official endpoint URL;
- uses retained NSE symbol/series identity;
- applies bounded request timeouts/retries.

Production run `35727346835` extracted five verified values:

- Adroit Industries (India) Limited — 111;
- ArMee Infotech Limited — 40;
- Elevate Campuses Limited — 41;
- Swastika Infra Limited — 81;
- Varmora Granito Limited — 101.

Bot data commit: `9e787f2fbb41f4e55fa05ebd097fd98fc683f7b6`.

Legacy records may also recover deterministic symbol/series parameters from an already-retained official NSE Issue Information URL. PR #44 enabled this path. Production run `35727815131` reached all six remaining gaps with 6/6 successful API calls and no conflicts or fetch errors, but NSE currently publishes no supported finalized minimum-bid value for those six. They remain null and will be retried automatically.

Current minimum-bid coverage: **19/25**.

The same `ipo-detail` payload exposes `metaInfo`, making explicit listing-date recovery the next high-value P1 field family. Listing dates must be sourced directly from the payload; do not infer them from close dates.

## NSE ipo-detail listing-date automation — production verified

The official NSE `/api/ipo-detail` payload exposes listing dates under `metaInfo.listingDate`.

A read-only production diagnostic (PR #46, run `35731645033`) checked all 26 deterministic NSE identities:

- 26 API successes;
- 10 explicit listing dates;
- 0 fetch errors.

Every usable value followed the exact ISO `YYYY-MM-DD` shape. No listing date was inferred from issue timing.

PR #47 added production extraction with strict rules:

- source: official NSE `/api/ipo-detail`;
- field: exact `metaInfo.listingDate`;
- parser: valid ISO `YYYY-MM-DD` only;
- target: missing `listing_date` only;
- evidence: exact endpoint URL/identity and collection timestamp;
- absent or invalid source values remain null.

Production run `35732506571` extracted 10 verified listing dates from 26 successful API calls with zero unparseable values and zero fetch errors.

Bot data commit: `a58cdac941a4a9116672951111e63b412ec2356e`.

Listing-date coverage is now **10/26**. Remaining records are automatically rechecked on hourly sync as NSE populates `metaInfo.listingDate`.

The earliest remaining P1 gap is now price band: **25/26** records have one, with Axiom Gas Engineering Limited as the sole missing record. The next source-family batch should inspect explicit `Price Range` / `Price Band` title/value pairs in the same NSE endpoint.

## NSE ipo-detail price-band automation — production verified

The official NSE `/api/ipo-detail` source now closes the only remaining price-band gap.

PR #49 production diagnostic found for Axiom Gas Engineering Limited:

- identity: `AXIOMGAS / SME`;
- title: `Price Range`;
- value: `Rs.51 to Rs.54 per equity share`.

PR #50 added a strict extractor for exact `Price Range` / `Price Band` terms. It requires two rupee-denominated bounds per Equity Share, rejects fixed single prices/placeholders/conflicts, fills missing values only, and stores direct NSE API evidence.

Production run `35738252937` extracted Axiom's verified ₹51–₹54 band with 1/1 API success and zero conflicts/errors.

Bot data commit: `134e0e7a73e736ed3748906b198a8c883fd18892`.

Published price-band coverage is now **26/26**.

The next price-related P1 family is final issue price. Keep it distinct from price band and never use the band cap as the final price.

## NSE public past-issues final-price automation — production verified

NSE `/api/ipo-detail` was tested first for already-listed missing-price records and returned no explicit final-price term. Production run `35741820135` completed 4/4 requests with zero fetch errors and zero supported issue-price candidates.

The authoritative completed-issue source is:

`https://www.nseindia.com/api/public-past-issues`

Read-only production diagnostic `35742801879` found four exact symbol matches and four fixed issue prices with no ambiguity:

- ARCIL — ₹139;
- ESDS — ₹429;
- KARAMTARA — ₹254;
- QUALIANCE — ₹127.

The production extractor (PR #55) requires:

- retained deterministic NSE identity;
- already-published listing date;
- one unique exact symbol row;
- matching series/security type when provided;
- matching official listing date when provided;
- a fixed numeric `issuePrice`.

It explicitly rejects range strings and placeholders, fills missing values only, and never substitutes a price-band cap.

Production run `35743854058` extracted all four candidates with zero rejects or parse failures.

Bot data commit: `8746f22505f8d79920923670d3a9381699c82d17`.

Issue-price coverage is now **14/26**. The remaining 12 records are not yet completed/listed; they stay null until NSE publishes a past-issues row and will then be retried automatically.

The next P1 field family is aggregate issue-size INR. NSE `ipo-detail` `Issue Size` text may contain share counts, total INR amounts, or component prose, so any extractor must accept only an explicit overall rupee aggregate and must not reconstruct it arithmetically.

## NSE ipo-detail aggregate issue-size automation — production verified

The official NSE `/api/ipo-detail` `Issue Size` row is free-form prose and cannot be treated as an INR amount generically.

Production diagnostic PR #57 / run `35748672356` established three source shapes:

- share-count-only offers;
- mixed Fresh Issue + OFS disclosures;
- pure one-leg Fresh Issue/OFS disclosures with one explicit INR aggregate.

Only the third shape is safe for direct publication without arithmetic.

PR #58 added the production extractor with these rules:

- read only overall Issue Size / Total Issue Size / Offer Size terms;
- strip parenthetical carve-outs;
- accept only a sole Fresh Issue or sole OFS leg with an explicit INR amount;
- convert crore/million/lakh/lac units directly;
- reject share-count-only rows;
- reject mixed Fresh+OFS rows even when one component is INR-denominated;
- never sum components;
- never calculate shares × issue price;
- fill missing issue size only.

Production run `35749978275` completed 14/14 official API requests and extracted:

- ArMee Infotech Limited — ₹3,000,000,000;
- Elevate Campuses Limited — ₹21,000,000,000.

Twelve rows remained null by design. Bot data commit: `ccdf8f308f437257d64b2e9b3bd99eb9729eaa57`.

Published issue-size coverage is now **14/26**.

The next P1 source family is explicit market lot. Do not reuse Bid Lot / Minimum Order Quantity as market lot merely because values may coincide; inspect explicit Market Lot / Lot Size source terms separately.

## NSE ipo-detail market-lot automation — production verified

Market lot remains a separate application term from minimum bid quantity.

Read-only production diagnostic PR #60 / run `35757461876` checked the eight missing market-lot records using official NSE `/api/ipo-detail`:

- 8 API successes;
- 1 response with explicit Market Lot / Lot Size;
- 0 fetch errors.

The sole supported source term was:

- Axiom Gas Engineering Limited — `Lot Size: 2000 Equity Shares`.

The other seven records expose no explicit Market Lot / Lot Size field. Bid Lot and Minimum Order Quantity are intentionally ignored for market-lot purposes.

PR #61 added the production extractor:

- accepted titles: exact Market Lot / Lot Size;
- positive Equity Share quantity required;
- placeholders/conflicts rejected;
- missing fields only;
- exact NSE endpoint evidence retained;
- retained market-lot evidence supported by deterministic publication.

Production run `35758162829` extracted Axiom's verified 2,000-share market lot from 8/8 successful API calls, with 7 source-null records and zero conflicts/fetch errors.

Bot data commit: `fbe718e911d9649e9a6007a9c2922af23b397816`.

Published market-lot coverage is now **19/26**.

The next P1 field family is minimum application amount INR. Start with explicit official source text; do not compute it from price and quantity in the first extraction family.

