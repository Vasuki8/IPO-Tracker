# IPO Tracker

A source-first Indian IPO research interface with automated official-source discovery and GitHub Pages publication.

## Current state

The public UI consumes the source-backed dataset at `data/ipos.json`.

As of the latest production sync on 2026-09-22, the published 2026 dataset contains **26 real IPO issuers**. The tracker does not use prototype/demo market rows as production fallback data.

### Data foundation

- Evidence-bearing IPO field contract
- Null preservation
- Verified / provisional / conflict / missing source states
- Separate market lot, minimum bid quantity, and minimum application amount
- Publication, observation, collection, and dataset-generation timestamps
- Correction/conflict history
- Deterministic publication from retained recovery manifests
- Machine-checkable validation
- GitHub Actions validation

See `docs/DATA_CONTRACT.md` and `data/ipo-schema.json`.

## Live automation

The tracker now has an automated discovery, official-document enrichment, and publishing loop.

`.github/workflows/update-ipos.yml` runs **hourly** and:

1. retrieves current/upcoming IPOs from official NSE website feeds;
2. merges explicitly supported source values into the retained recovery manifest;
3. leaves unsupported values null;
4. rebuilds `data/ipos.json`;
5. validates the data contract;
6. commits only source-backed changes;
7. lets GitHub Pages publish the new revision.

The first real production run succeeded and automatically increased the dataset from 14 to 23 issuers.

See `docs/AUTOMATION.md` for the exact source and field rules.

### Automation is intentionally conservative

The NSE discovery feed does **not** automatically cause the tracker to:

- interpret NSE `issueSize` as an INR issue-size amount;
- copy market lot into minimum bid quantity;
- calculate minimum application amount;
- infer sector or listing date;
- treat the cap of a price band as the final issue price.

Those values remain missing until supported by retained official evidence.

## Architecture

```
index.html
assets/
  styles.css
  app.js
data/
  ipo-schema.json
  ipos.json
  recovery/
    <year>/
      nse-issue-information.json
scripts/
  sync-nse-live.mjs
  build-published-data.mjs
  validate-data.mjs
.github/
  workflows/
    update-ipos.yml
    validate-data.yml
    deploy-pages.yml
docs/
  DEVELOPMENT_PROCESS.md
  DATA_CONTRACT.md
  AUTOMATION.md
  PROJECT_STATUS.md
```

## Local preview

Open `index.html` in a browser or serve the repository with any static HTTP server.

---

## Handoff for the next prompt

Use this section as the starting context when continuing work in a new chat.

### Repository

- Repository: `Vasuki8/IPO-Tracker`
- Default branch: `main`
- Website: `https://vasuki8.github.io/IPO-Tracker/`
- Hosting: GitHub Pages
- Live-data workflow: `.github/workflows/update-ipos.yml`
- Deployment workflow: `.github/workflows/deploy-pages.yml`

### Latest completed batch

SEBI RHP source recovery is now production-repaired and significantly deeper.

PR #28 bypassed stale SEBI listing cache responses. PR #29 repaired a live malformed-anchor pattern where an RHP filing URL was paired with adjacent Abridged Prospectus text. Production sync `35693813309` then increased deterministic SEBI latest-list matches from 9 to 22, changed 8 issuer records, and attached 11 official documents.

PR #30 added direct official RHP PDF resolution from retained SEBI RHP filing pages. Production sync `35694073605` resolved **13 `SEBI RHP PDF` attachments** and retained them without publishing any RHP-derived market term.

Explicit aggregate issue-size extraction from retained official SEBI final Prospectus PDFs is also production-verified.

PR #23 used a temporary read-only diagnostic to inspect the seven retained final Prospectuses that still lacked `issue_size_inr`. PR #24 then added a bounded extractor for explicit top-level Offer/Issue aggregate amounts and removed the temporary diagnostic from the hourly workflow.

Final issue-price recovery from the currently retained official SEBI Prospectus PDFs is also complete.

PR #20 added a temporary read-only diagnostic scan for the three remaining null cases and proved the 20-page boundary was not the problem. Their final prices were stated on PDF pages 2–3 using the reverse-labelled cover form `at a price of ₹X per Equity Share ... (Offer/Issue Price)`.

PR #21 added only that explicit syntax to the production parser, tested the three real wording patterns plus a negative unlabeled-price case, and removed the expensive diagnostic step from the hourly workflow. The production sync then filled all three remaining prices from official SEBI Prospectus evidence.

Earlier, official SEBI document discovery was integrated into the hourly NSE sync.

PRs #10–#15 implemented and hardened:

- deterministic RHP / Abridged Prospectus / Prospectus matching;
- dynamic SEBI filing-link parsing;
- general Filings and mixed Public Issues coverage;
- bounded issuer-specific searches for sparse NSE-live records;
- strict ambiguity rejection and idempotent document attachment.

The production network path is verified end to end. The latest real run passed NSE collection, SEBI collection, rebuild, deterministic publication and data-contract validation.

**Important current limitation:** current SEBI recovery now covers 17 of the 23 published issuer records. Six live-discovered issuers still have no retained SEBI document: ArMee Infotech, Axiom Gas Engineering, Coreintegra Consulting Services, Elevate Campuses, Pooja Logistics, and Varmora Granito. Matching remains strict rather than attaching uncertain evidence.

### Critical data rule

Do not edit `data/ipos.json` as a substitute for source recovery.

Update retained recovery evidence and regenerate the public dataset.

Never fill nulls with guesses, estimates, unsupported arithmetic, or aggregator-derived substitutes.

### What automation does now

Hourly NSE discovery can automatically publish:

- issuer name;
- board when explicit from NSE series;
- lifecycle status represented by the feed;
- explicit price band;
- explicit fixed issue price when present;
- explicit market lot when present;
- issue open date;
- issue close date.

### Main remaining limitation

The discovery/publish loop and SEBI matcher are live, but two evidence-depth gaps remain:

1. SEBI's raw pages do not currently expose attachable documents for every sparse NSE-live issuer in GitHub Actions;
2. field extraction is currently bounded to explicit Abridged Prospectus aggregate size and explicit final-Prospectus issue price; most remaining fields are not automated yet.

IPOs can therefore still show missing fields such as:

- aggregate issue size in INR;
- minimum bid quantity where not separately stated;
- minimum application amount;
- final issue price for issuers that do not yet have a retained authoritative final-price source;
- listing date;
- sector;
- richer DRHP/RHP/Prospectus evidence.

The next source-automation layer should parse a bounded set of fields from retained official offer documents, with explicit source precedence and page-level evidence, rather than inferring values from filenames or price-band caps.

### Latest field-extraction result

The Abridged Prospectus issue-size extractor is now production-verified.

PR #16 merged at `c7c59252bb9e59b3767d73205ad1d682326c48b8`.

Real hourly run `35686786294` downloaded all 4 eligible retained SEBI Abridged Prospectus PDFs with zero fetch errors and:

- extracted Karamtara Engineering's explicit total offer size of ₹8,750.00 million;
- preserved ARCIL, Pranav Constructions and Sonaselection as null because their first-page total-size cells were placeholders/non-explicit;
- left ESDS unchanged because it already had verified issue-size evidence.

The source-backed bot commit is `92f0f024367b20a9f023218a0cb92ecbc2e38636`.

### Latest final-document result

Direct official final-Prospectus PDF resolution is now production-verified.

PR #17 merged at `cd39442c03450a9189d783d554e3feb48ee57239`.

Real sync run `35687483282` resolved and attached **9 official SEBI Prospectus PDFs** to deterministic issuer records. Bot commit `0c3e1c199fdb12266589c7f65eead373c49065dd` changed document evidence/freshness only; no market field was inferred or overwritten.

### Latest final-Prospectus price result

PR #18 merged at `1b41f0c115c5df993486e3d3e5f52668d73ffcfc` and initially recovered four missing final prices.

PR #20 merged at `f141c4fef5f5ce9025a9e6e809b9cc0c80a68b2f` as a one-run diagnostic. Production run `35689468724` scanned the three unresolved official PDFs and found explicit cover statements on early pages:

- Jindal Supreme (India) Limited — `₹93 per Equity Share ... (Offer Price)`, PDF page 3;
- SS Retail Limited — `₹424^ per Equity Share ... (Offer Price)`, PDF page 3;
- Veegaland Developers Limited — `₹140 per Equity Share ... (Issue Price)`, PDF page 2.

PR #21 merged at `454ec51a640f2f4079577d41d84dec222fe48e63` and added only that labelled cover syntax. Production run `35690054143` then completed successfully:

- candidates: 3;
- official PDFs downloaded: 3;
- extracted: 3;
- explicit-price missing: 0;
- PDF fetch errors: 0.

The source-backed bot commit is `51f806b16e4eba40efee304d07bb5753a8e0f9d9`. All nine records that currently retain an official `SEBI Prospectus PDF` now have a retained final issue price; existing Hero Motors and Rentomojo evidence was not overwritten.

### Latest final-Prospectus issue-size result

PR #23 merged at `5a0b7e225c53c737b43750db61b19309d29dabc0` as a temporary read-only diagnostic. It confirmed that all seven missing-size final Prospectuses contain an explicit top-level aggregate Offer/Issue amount on PDF pages 2–3, while the same pages also contain smaller Fresh Issue and/or OFS component amounts.

PR #24 merged at `a7d2afc5f69fe97f17564e86b72e1ebe3cd296b6`. The extractor accepts only explicit overall Offer/Issue amounts, supports million/lakh/crore units, fills missing values only, and rejects Fresh Issue-only, OFS-only and unlabeled aggregate amounts.

Production sync run `35691580621` completed successfully:

- candidates: 7;
- official PDFs downloaded: 7;
- extracted: 7;
- explicit-size missing: 0;
- PDF fetch errors: 0.

Published with official SEBI Prospectus PDF/page evidence:

- Jindal Supreme (India) Limited — ₹1,248,804,000 — PDF page 3;
- Kanohar Electricals Limited — ₹10,557,400,000 — PDF page 3;
- LCC Projects Limited — ₹4,271,410,000 — PDF page 3;
- Manipal Payment and Identity Solutions Limited — ₹8,050,000,000 — PDF page 3;
- Pranav Constructions Limited — ₹3,510,250,000 — PDF page 2;
- SS Retail Limited — ₹5,000,000,000 — PDF page 3;
- Veegaland Developers Limited — ₹2,100,000,000 — PDF page 2.

Source-backed bot commit: `0110d864235eccb800efa5b206fa19bf9cdb0fb4`.

GitHub Pages deployment for that data revision passed in run `35692087146`.

All 9 records currently carrying retained `SEBI Prospectus PDF` evidence now have both final issue price and aggregate issue-size evidence.

### Latest homepage ordering result

The homepage IPO market list is explicitly ordered **newest to oldest** by source-backed IPO open date.

A follow-up repair also changed deterministic publication order in `data/ipos.json` from issuer-name alphabetical to newest-first and versioned the ordering scripts. This makes the visible order resilient even when a browser has cached the previous UI JavaScript.

Implementation rules:

- primary sort: `open_date` descending;
- tie-breaker: `close_date` descending;
- final deterministic tie-breaker: issuer name;
- missing/invalid dates sort last;
- sorting is applied after search/board/status filters, so filtered desktop and mobile views remain newest-first;
- the underlying `data/ipos.json` order and all source evidence remain unchanged.

PR #26 adds the shared ordering helper plus a behavioral test against the current published dataset.

### Latest RHP recovery result

The repaired RHP source family now retains direct official RHP PDFs. Five records still missing `issue_size_inr` now have both an Abridged Prospectus and an RHP PDF:

- Adroit Industries (India) Limited;
- Asset Reconstruction Company (India) Limited;
- National Stock Exchange of India Limited;
- Sonaselection India Limited;
- Swastika Infra Limited.

The existing page-1 Abridged Prospectus extractor checked all five and extracted **0** because the aggregate-size cells remain placeholders. That null preservation is intentional.

Source-backed document bot commits:

- `ec684bc1fa558f2dafb7c7b90df6b750fc6f79ac` — repaired current-list RHP/Abridged attachments;
- `3c2f3fb8a8737fe2067aab3e18e39ab86a68eeb6` — 13 direct RHP PDF attachments.

GitHub Pages deployment for `3c2f3fb...` passed in run `35694143832`.

### Latest RHP issue-size diagnostic result

PR #32 merged at `ce0d10a00e830a7606e909abe047bb2ee2e983ee`.

The deterministic publisher now preserves retained `verified`, `provisional`, and `conflict` status instead of automatically upgrading every retained non-null field to verified.

Production sync run `35694934742` then evaluated the five missing-size records with retained official `SEBI RHP PDF` evidence:

- candidates: 5;
- PDFs downloaded: 5;
- parseable explicit overall totals: **0**;
- PDF fetch errors: 0.

The result is source-driven rather than a parser failure:

- Adroit Industries — no explicit INR overall total in the bounded scan;
- ARCIL — `Total Offer size` is stated as an equity-share count, not an INR total;
- NSE — `Total Offer Size` is a share count; ₹700 million refers only to the Employee Reservation Portion;
- Sonaselection — no explicit INR overall total in the bounded scan;
- Swastika Infra — overall Offer amount remains `₹[●]`; ₹12,900 lakh is explicitly the Fresh Issue component, not the total Offer.

Therefore **no RHP-derived `issue_size_inr` value was published**, provisional or otherwise. The temporary diagnostic was removed from hourly execution after this measurement.

### Latest minimum-bid recovery result

The minimum-bid source family has now been tested across the available document stages rather than equating it with market lot.

- PR #34 — Abridged Prospectus diagnostic: Adroit, NSE, and Swastika all downloaded successfully, but page 1 contained **0 explicit minimum-bid mentions**.
- PR #35 — RHP diagnostic: all three RHPs explicitly deferred the Bid Lot / Minimum Bid Lot to the later price-band advertisement and retained `[●]` placeholders.
- PR #36 — final-Prospectus diagnostic: one eligible final Prospectus existed, for National Stock Exchange of India Limited. It explicitly states **Bid Lot 8 Equity Shares** on PDF page 10 and repeats **Minimum Bid 8 Equity Shares** later in the offer-procedure tables.
- PR #38 — NSE Issue Information HTML probe: all 9 Active/Forthcoming/Past page requests succeeded, but GitHub Actions received only the client-side shell; the rendered Bid Lot / Minimum Order Quantity values are supplied dynamically rather than in raw HTML.
- PR #39 — strict final-Prospectus extractor, merged at `0c0b0668690b2f50ebe57627b74abae7a3aec4ad`.

Production sync run `35697515918` succeeded:

- candidates: 1;
- official final Prospectus PDFs downloaded: 1;
- extracted: 1;
- explicit minimum-bid missing: 0;
- fetch errors: 0.

Published:

- **National Stock Exchange of India Limited — minimum bid quantity 8 Equity Shares — final Prospectus PDF page 10**.

Source-backed bot commit:

`2f6428c2138173a4ca02dc271100ed22412da31e`

Only the recovery manifest and generated `data/ipos.json` changed. The published field is `verified` and retains the direct official SEBI Prospectus PDF/page evidence.

Minimum-bid coverage improved from **13/23 to 14/23**; 9 records remain missing.

GitHub Pages deployment for the bot revision passed in run `35697665129`.

### Latest NSE ipo-detail result

The official dynamic source behind NSE Issue Information is now integrated:

`https://www.nseindia.com/api/ipo-detail?symbol=<SYMBOL>&series=<SERIES>`

PR #41 verified the endpoint against the live missing-bid set. Production run `35726755503` returned HTTP-successful JSON for **10/10** tested symbols with zero fetch errors and confirmed the response structure:

- `issueInfo.dataList` contains static issue terms as `{title, value}` pairs;
- `bidDetails` / `activeCat` are subscription-demand data and are not used as minimum-bid terms.

PR #43 merged at `1b4e267de543bc909616392373099a38e257281a` and added a strict production extractor. It:

- reads only `issueInfo.dataList`;
- prefers explicit `Minimum Order Quantity`;
- accepts explicit `Bid Lot` as the official fallback;
- parses only numeric Equity Share quantities;
- rejects placeholders;
- refuses publication if the two official values disagree;
- keeps `market_lot` separate;
- fills missing values only;
- retains the exact NSE endpoint/identity and collection timestamp.

Production run `35727346835`:

- candidates: 10;
- API successes: 10;
- extracted: **5**;
- missing/placeholders: 5;
- conflicts: 0;
- fetch errors: 0.

Published:

- Adroit Industries (India) Limited — **111** Equity Shares;
- ArMee Infotech Limited — **40** Equity Shares;
- Elevate Campuses Limited — **41** Equity Shares;
- Swastika Infra Limited — **81** Equity Shares;
- Varmora Granito Limited — **101** Equity Shares.

Source-backed bot commit:

`9e787f2fbb41f4e55fa05ebd097fd98fc683f7b6`

The bot diff changed only the recovery manifest and generated `data/ipos.json`. GitHub Pages deployment for that data revision passed in run `35727496988`.

PR #44 then added deterministic legacy identity recovery from already-retained official NSE Issue Information URLs. Production run `35727815131` successfully queried **all 6 remaining gaps**, including Qualiance:

- candidates: 6;
- API successes: 6;
- extracted: 0;
- missing/placeholders: 6;
- conflicts: 0;
- fetch errors: 0.

This confirms the remaining nulls are currently **source-null**, not collection failures. The hourly extractor will keep checking them automatically as NSE publishes finalized terms.

Minimum-bid coverage is now **19/25 present, 6/25 missing**.

### Latest listing-date recovery result

PR #46 — `Diagnose explicit NSE ipo-detail listing dates` — production-verified the field shape before writes.

Production run `35731645033` queried **26/26** deterministic NSE identities successfully:

- API successes: 26;
- responses with explicit listing date: 10;
- fetch errors: 0.

The live source shape was consistent:

- field: `metaInfo.listingDate`;
- format: strict ISO `YYYY-MM-DD`;
- current/upcoming issues without a published listing date returned no usable field.

Observed explicit dates included ARCIL `2026-09-17`, ESDS `2026-09-04`, Qualiance `2026-09-11`, Pranav `2026-09-15`, and Veegaland `2026-09-18`.

PR #47 merged at `c6134bbea181c46e97ade256c288289c915fff16` and promoted only that observed shape into production extraction.

Extractor rules:

- official NSE `/api/ipo-detail` only;
- exact `metaInfo.listingDate` only;
- strict valid ISO `YYYY-MM-DD` parsing;
- no inference from close date, T+ schedules, status or settlement conventions;
- fill missing `listing_date` only;
- retain exact endpoint identity and collection timestamp;
- preserve null for absent or unparseable values.

Production run `35732506571`:

- candidates: 26;
- API successes: 26;
- extracted: **10**;
- missing: 16;
- unparseable: 0;
- fetch errors: 0.

Published verified listing dates:

- Asset Reconstruction Company (India) Limited — **2026-09-17**;
- ESDS Software Solution Limited — **2026-09-04**;
- Kanohar Electricals Limited — **2026-09-16**;
- Karamtara Engineering Limited — **2026-09-17**;
- LCC Projects Limited — **2026-09-17**;
- Manipal Payment and Identity Solutions Limited — **2026-09-17**;
- Pranav Constructions Limited — **2026-09-15**;
- Qualiance International Limited — **2026-09-11**;
- Rentomojo Limited — **2026-09-17**;
- Veegaland Developers Limited — **2026-09-18**.

Source-backed bot commit:

`a58cdac941a4a9116672951111e63b412ec2356e`

The bot diff changed only recovery data and generated `data/ipos.json`. GitHub Pages deployment for the data revision passed in run `35732898054`.

Current listing-date coverage is **10/26 present, 16/26 missing**. The remaining nulls are automatically rechecked as NSE publishes `metaInfo.listingDate`.

### Latest price-band completion result

PR #49 — `Diagnose explicit NSE price-band terms` — verified Axiom's official NSE `ipo-detail` source before any write.

Production run `35737565780` found exactly one missing-band candidate and returned:

- issuer: Axiom Gas Engineering Limited;
- symbol / series: `AXIOMGAS / SME`;
- official term: `Price Range`;
- source value: `Rs.51 to Rs.54 per equity share`;
- API successes: 1;
- responses with supported price-band terms: 1;
- fetch errors: 0.

PR #50 merged at `5acd0a5fab5920b999501120755753a57bc1ba68` and added strict production extraction.

Rules:

- accept only exact `Price Range` / `Price Band` title-value pairs;
- require two explicit rupee-denominated bounds per Equity Share;
- reject single fixed prices, placeholders, reversed/invalid ranges and unrelated fields;
- refuse publication if multiple supported official terms disagree;
- fill missing price bands only;
- retain exact NSE endpoint evidence and collection timestamp.

Production run `35738252937`:

- candidates: 1;
- API successes: 1;
- extracted: 1;
- missing/placeholders: 0;
- conflicts: 0;
- fetch errors: 0.

Published:

- **Axiom Gas Engineering Limited — ₹51 to ₹54 per Equity Share — verified**.

Source-backed bot commit:

`134e0e7a73e736ed3748906b198a8c883fd18892`

Only recovery data and generated `data/ipos.json` changed.

Price-band coverage is now **26/26**.

### Latest final issue-price recovery result

The listed missing-price gap is now covered by an official NSE completed-issue source.

PR #52 first tested `/api/ipo-detail` on the four already-listed records whose final issue price was still null. Production run `35741820135` returned **4/4 successful responses but 0 explicit `Issue Price` / `Final Issue Price` / `Offer Price` terms**, confirming that the detailed endpoint was not the correct final-price source. No band cap was used.

PRs #53–#54 then moved the diagnostic to official NSE:

`https://www.nseindia.com/api/public-past-issues`

Production run `35742801879` returned:

- past rows: 1,450;
- candidates: 4;
- exact symbol matches: 4;
- parseable fixed issue prices: 4;
- ambiguous symbol matches: 0.

Verified official values:

- Asset Reconstruction Company (India) Limited — **₹139**;
- ESDS Software Solution Limited — **₹429**;
- Karamtara Engineering Limited — **₹254**;
- Qualiance International Limited — **₹127**.

PR #55 merged at `0dcc101be97088ec565287fa4a5a63185ec8ea6c` and promoted that source into production extraction.

Safety rules:

- only already-listed records with missing issue price are candidates;
- exact NSE symbol match is required;
- security type / series must agree when supplied;
- retained official listing date is cross-checked against the past-issues row;
- only a fixed numeric `issuePrice` is accepted;
- ranges and placeholders are rejected;
- existing issue-price evidence is never overwritten;
- price-band caps are never substituted.

Production run `35743854058` succeeded:

- candidates: 4;
- exact matches: 4;
- extracted: **4**;
- missing/unparseable: 0;
- rejected matches: 0.

Source-backed bot commit:

`8746f22505f8d79920923670d3a9381699c82d17`

The bot diff changed only recovery data and generated `data/ipos.json`.

Issue-price coverage improved from **10/26 to 14/26**. The remaining 12 nulls are not yet listed (or do not yet have a published NSE listing date), so the hourly past-issues extractor will fill them automatically when NSE publishes completed-issue rows.

### Latest NSE issue-size recovery result

PR #57 — `Diagnose NSE ipo-detail aggregate issue size` — inspected the exact official `Issue Size` text before any write.

Production run `35748672356`:

- candidates: 14;
- API successes: 13;
- responses with overall-size terms: 13;
- fetch errors: 1 temporary Moneyview timeout;
- values written: 0.

The source text fell into three important classes:

- share-count-only offers, such as Axiom, Qualiance, Pooja, Sonaselection, ARCIL and several SME issues;
- mixed Fresh Issue + OFS disclosures where one or both legs are not a single overall INR total, such as Swastika and Varmora;
- pure one-leg Fresh Issue disclosures with one explicit INR aggregate, observed for ArMee and Elevate.

PR #58 merged at `09e1eb9166d73cc1d71e8994821238ce5468897c` and promoted only the safe third class into production extraction.

The extractor:

- reads only overall `Issue Size` / `Total Issue Size` / `Offer Size` rows;
- strips parenthetical anchor / market-maker carve-outs before evaluating the top-level offer;
- accepts only a sole Fresh Issue or sole OFS leg when that entire offer is explicitly INR-denominated;
- supports crore, million, lakh and lac unit conversion;
- rejects share-count-only rows;
- rejects every mixed Fresh Issue + OFS row rather than summing or converting components;
- never multiplies shares by issue/final price;
- fills missing values only and retains exact NSE API evidence.

Production run `35749978275` succeeded:

- candidates: 14;
- API successes: 14;
- extracted: **2**;
- unsupported/share-count rows: 12;
- conflicts: 0;
- fetch errors: 0.

Published verified values:

- **ArMee Infotech Limited — ₹3,000,000,000**;
- **Elevate Campuses Limited — ₹21,000,000,000**.

Source-backed bot commit:

`ccdf8f308f437257d64b2e9b3bd99eb9729eaa57`

The bot diff changed only recovery data and generated `data/ipos.json`. GitHub Pages deployment for the bot revision passed in run `35750326661`.

Aggregate issue-size coverage improved from **12/26 to 14/26**. The remaining 12 records are deliberately source-null under this NSE rule and will continue to be checked by the existing final-Prospectus and NSE automation.

### Latest market-lot recovery result

PR #60 — `Diagnose explicit NSE market-lot terms` — inspected the eight missing records read-only.

Production run `35757461876`:

- candidates: 8;
- API successes: 8;
- responses with explicit `Market Lot` / `Lot Size`: **1**;
- fetch errors: 0.

The sole supported term was:

- **Axiom Gas Engineering Limited — `Lot Size: 2000 Equity Shares`**.

Adroit, ArMee, Elevate, Moneyview, NSE, Swastika, and Varmora returned no explicit `Market Lot` / `Lot Size` field. Their `Bid Lot` / `Minimum Order Quantity` values were deliberately ignored.

PR #61 merged at `9ed4044be6ae795bbf5373b0a7bb2530bba44960` and promoted only explicit market-lot terms into production extraction.

Rules:

- official NSE `/api/ipo-detail` only;
- exact `Market Lot` / `Lot Size` title-value pairs only;
- positive Equity Share quantity required;
- `Bid Lot` and `Minimum Order Quantity` are not accepted as market lot;
- placeholders and conflicting official values are rejected;
- fill missing `market_lot` only;
- retain exact endpoint/source identity and collection timestamp;
- deterministic publication preserves retained market-lot evidence.

Production run `35758162829`:

- candidates: 8;
- API successes: 8;
- extracted: **1**;
- missing/placeholders: 7;
- conflicts: 0;
- fetch errors: 0.

Published:

- **Axiom Gas Engineering Limited — market lot 2,000 Equity Shares — verified**.

Source-backed bot commit:

`fbe718e911d9649e9a6007a9c2922af23b397816`

The bot diff changed only recovery data and generated `data/ipos.json`.

Market-lot coverage improved from **18/26 to 19/26**. The remaining seven records are source-null for explicit market lot and will continue to be checked automatically.

### Latest minimum-application source result

PR #63 — `Diagnose explicit NSE minimum application amount terms` — added a read-only NSE `/api/ipo-detail` survey.

The initial all-universe run was intentionally cancelled after the diagnostic proved too expensive for an hourly non-writing step. PR #65 bounded the survey to six representative deterministic issues spanning:

- Mainboard and SME;
- upcoming, open and already-listed issues.

Production run `35760191175` completed successfully:

- candidates: 6;
- official NSE API successes: 6;
- responses with explicit minimum-application/investment terms: **0**;
- fetch errors: 0.

Checked issuers:

- Adroit Industries (India) Limited;
- Asset Reconstruction Company (India) Limited;
- Axiom Gas Engineering Limited;
- Bench Mark Infotech Services Limited;
- Qualiance International Limited;
- Varmora Granito Limited.

For all six, `issueInfo.dataList` contained **no explicit `Minimum Application Amount` / `Minimum Investment Amount` term**. Therefore no extractor was enabled and coverage remains **0/26**.

This is a source limitation, not a calculation gap. The tracker will not manufacture the field from minimum bid quantity × issue price or the price-band cap.

The one-shot diagnostic has been removed from hourly execution after this measurement. Its parser helper remains available for future manual source checks.

### Recommended next coherent batch

Continue minimum-application recovery with the next official source family: **retained SEBI offer documents**.

Start with a read-only survey of retained Abridged Prospectus / RHP / final Prospectus PDFs for explicit INR wording such as:

- `Minimum Application Amount`;
- `Minimum Amount`;
- `Minimum Investment`;
- another clearly equivalent labelled INR amount.

Acceptance rules:

- official retained SEBI document only;
- require an explicitly stated INR amount;
- retain PDF page evidence;
- keep minimum application amount distinct from market lot and minimum bid quantity;
- no price × quantity calculation;
- no price-band-cap inference;
- fill missing values only;
- preserve null for share-count-only, placeholder, derived or ambiguous wording.

### Product direction

The product is intended to become a public commercial IPO research/tracking product.

Current priority order remains:

1. Trustworthy displayed data
2. Accurate freshness and source labels
3. Reliable recovery / repair handling
4. Complete source coverage
5. Better IPO research workflows
6. Performance / expansion only after correctness is stable
7. Discoverability and maintainability
8. Commercial features only when explicitly justified

Do not add billing, accounts, ads, analytics, paid infrastructure, or other commercial systems without explicit approval.

## Development operating model

Future development runs must follow `docs/DEVELOPMENT_PROCESS.md`.

For a fresh chat:

> Continue IPO Tracker development. Read README.md, docs/PROJECT_STATUS.md, and docs/DEVELOPMENT_PROCESS.md first. Follow the repository development process, select the earliest unfinished priority, and complete one coherent batch end to end.

After that, the user may simply say **"continue"**. The repository process/handoff files are the source of truth; the user should not need to resend a large master prompt.


### Abridged Prospectus minimum-application survey

PR #68 tested the next official source family after NSE `ipo-detail`: retained SEBI Abridged Prospectuses.

Production run `35761261256` downloaded **16/16** retained Abridged Prospectus PDFs and found **0 explicit supported INR minimum-application/minimum-investment mentions on page 1**, with **0 fetch errors**. No values were written and coverage remains **0/26**.

The tracker continues to reject derived `price × quantity` values and does not reinterpret bid lot / minimum order quantity as an INR application amount.

Next: survey retained official SEBI RHP PDFs (and then final Prospectus PDFs if needed) across full document text, retaining page-level evidence for any explicit INR amount.


### Full RHP minimum-application classification

The retained RHP source family has now been fully measured.

Production run `35765946080` scanned **14/14** official SEBI RHP PDFs across **7,593 pages**, capturing **28 labelled INR minimum-application/investment mentions** with **0 fetch errors**.

The result exposed a schema problem rather than a missing parser: the values are investor-category-specific. Most are Anchor/QIB Mutual Fund minimums around ₹100 million; Sonaselection and Swastika explicitly state NII minimum application sizes of ₹200,000; some other matches are unrelated business/regulatory “minimum investment” text.

Therefore the generic `minimum_application_amount_inr` remains **0/26** rather than publishing a misleading category-specific value.

Next recommended batch: refine the data contract to model investor-category-specific application requirements before adding production extraction.


### Investor-category application requirements contract

Schema **1.2.0** adds a backward-compatible `application_requirements` object to every published IPO record.

Supported categories are:

- `retail`
- `non_institutional`
- `anchor_investor`

Each category separately tracks an evidence-bearing `minimum_application_amount_inr` and `minimum_bid_quantity`.

The legacy top-level application/bid fields remain unchanged, and the homepage is unchanged. All new category fields initially publish as `missing`; no RHP amount is imported automatically by the contract migration.

This resolves the ambiguity discovered in the full RHP survey without losing backward compatibility.

Next: add a strict source-backed NII minimum-application extractor, beginning with the explicit ₹200,000 RHP disclosures already observed for Sonaselection and Swastika.


### Production NII minimum application extraction

The category-specific application contract is now populated from official RHP evidence for the first supported category.

PR #75 added recurring strict extraction for `application_requirements.non_institutional.minimum_application_amount_inr`. Production run `35793315717` published **Swastika Infra Limited — ₹200,000 — RHP page 77**.

PR #76 repaired forward category-context detection for RHP wording where the Non-Institutional cue follows the amount. PR #77 then published the already-observed official evidence for **Sonaselection India Limited — ₹200,000 — RHP page 92**.

Current verified NII minimum-application coverage is **2/26**:

- Sonaselection India Limited — ₹200,000 — page 92;
- Swastika Infra Limited — ₹200,000 — page 77.

The legacy generic minimum-application amount remains null and no price × quantity derivation is used.

Next: survey retained RHPs for explicit **NII minimum bid quantity** wording before enabling the next category-specific production extractor.


### NII minimum bid quantity source survey

The retained RHP source family has now been measured for explicit Non-Institutional minimum share quantities.

PR #79 / sync run `35801899974` scanned **14/14 official SEBI RHP PDFs across 7,588 pages** and found:

- **0 documents** with an explicit NII minimum share quantity;
- **0 qualifying mentions**;
- **0 fetch errors**.

Accordingly, `application_requirements.non_institutional.minimum_bid_quantity` remains **0/26**. The tracker does not derive a share quantity from the ₹200,000 NII threshold, issue price, generic bid lot, or lot rounding.

PR #80 removed the completed one-shot survey from hourly execution.

Next: survey retained official offer documents for explicit **retail minimum application amounts** before enabling any retail category extraction.


### Retail minimum application amount source survey

The tracker has now completed a strict official-source survey for `application_requirements.retail.minimum_application_amount_inr`.

Existing full-RHP evidence showed retail rules expressed as **minimum Bid Lot**, not a direct retail INR minimum application amount.

PR #82 then surveyed retained final Prospectus PDFs. Production run `35804488536` scanned 9/10 successfully across **4,786 pages** with **0 explicit retail minimum-INR mentions**. The one unresolved Kanohar Prospectus was retried separately in PR #83 with a bounded 650-page scan; it scanned **511 pages** and again found **0 qualifying retail INR mentions**.

Accordingly, retail minimum application amount remains **0/26** by design. The tracker does not calculate price × lot or reuse NII/generic amounts.

PR #84 removed the completed one-shot survey from hourly execution.

Next: survey retained official documents for explicit **retail minimum bid quantity / minimum Bid Lot** wording before enabling retail category production extraction.


### Current application-term scope: Lot Size only

The active product requirement is now **Lot Size only**. Minimum investment / minimum application amount is out of scope unless explicitly re-enabled later.

The website displays one Lot Size value using verified source evidence:

- prefer `market_lot`;
- if that raw field is missing, fall back to verified `minimum_bid_quantity`;
- never calculate price × quantity.

Current 2026 user-facing Lot Size coverage is **26/26**: 19 direct market-lot values plus 7 verified official minimum-bid-quantity fallbacks.

Minimum-investment/application-amount values are no longer displayed on the homepage or IPO detail page, and the recurring minimum-application extraction step has been removed from the hourly workflow.


### Lot Size verification guardrail

The Lot Size display now accepts **verified fields only**.

Resolution order is:

1. verified `market_lot`;
2. verified `minimum_bid_quantity`;
3. otherwise show missing.

Provisional/conflict numeric values are never surfaced as Lot Size. Current 2026 coverage remains **26/26 verified Lot Size** with no data rewrite.

**Handoff:** minimum investment/application amount remains out of scope. The next development batch should re-audit the **12 missing issue-size records** against newly available official evidence before moving to freshness/operations work.


### Issue-size re-audit handoff

The 12 missing 2026 issue sizes have now been re-audited against current official evidence.

Latest supported-source checks found **no new publishable aggregate INR totals**, so issue-size coverage remains **14/26 verified**.

New evidence handled in this batch:

- **Qualiance International Limited** — the collector now resolves the attached PDF from its official SEBI `Other Documents` filing while preserving the neutral document type. Its Total Issue Size remains `[●]`.
- **Moneyview Limited** — a robust bounded PDF-transfer fallback allowed its official SEBI RHP to be inspected. The overall Offer remains `₹ [●] million`; only the Fresh Issue component is explicit at ₹7,500 million, so no total issue size is published.

Reusable source improvements remain enabled:

- SEBI Other Document PDF resolution;
- bounded `curl` fallback when normal official-PDF transfer terminates.

The one-shot Moneyview/Qualiance diagnostic has been removed from hourly execution.

**Handoff:** do not repeat issue-size recovery until new official evidence appears. Lot Size remains **26/26 verified**, and minimum investment remains out of scope. The next development batch should move to **operational freshness/source-health visibility**, starting with a read-only operator report that distinguishes source observation, collection success/failure and publication freshness.


### Operator freshness/source-health report

A read-only operator report is now available through:

```bash
node scripts/operator-report.mjs
node scripts/operator-report.mjs --json
```

The hourly sync also writes the report to the GitHub Actions **Job Summary**, including on failed runs.

It separates:

- source/record observation and collection timestamps;
- dataset generation time;
- NSE/SEBI collection success vs failure;
- build/validation/repository-publication outcomes;
- field coverage and verified Lot Size coverage.

It deliberately does not infer source-null from a null value and does not invent a GitHub Pages publication timestamp.

**Handoff:** Lot Size remains **26/26 verified** and minimum-investment work remains out of scope. The next batch should add durable **GitHub Pages publication-health visibility** while keeping deployment time separate from dataset generation time.


### Durable GitHub Pages publication health

GitHub Pages deployment health is now retained separately from IPO data in `ops/pages-publication.json`.

The record distinguishes the **latest deployment attempt** from the **last successful publication**, so a failed deployment remains visible without losing the last known-good publication time/commit. The operator freshness report reads this state directly.

The Pages workflow ignores status-only commits, preventing recursive deployments. IPO values and `data/ipos.json.generated_at` are not used as deployment timestamps.

**Handoff:** the next backend operations batch should add read-only **staleness thresholds / actionable health classification** on top of the separated collection, dataset-generation, and Pages-publication timestamps.


### Operator staleness and health classification

The backend operator report now classifies freshness as `healthy`, `stale`, `failure`, or `unknown` using explicit thresholds. Dataset generation, record collection, retained evidence collection and Pages publication remain separate signals.

No IPO value or field status is changed by this classification, and source-null is never inferred from age.

**Handoff:** next add read-only **recovery guidance** that maps each unhealthy reason to a safe diagnostic/action, without automatically rerunning workflows or modifying data.


### Read-only operator recovery guidance

The operator report now maps each unhealthy/unknown health reason to a priority, diagnostic step, and safe recovery recommendation. Guidance is informational only: it does not rerun workflows, rewrite data, or send notifications.

**Handoff:** next persist a machine-readable **latest operator snapshot** containing sync health, reasons, guidance, and run identity, separate from IPO data and without creating workflow loops.


### Durable latest operator snapshot

The hourly backend sync now persists its latest machine-readable operational state to `ops/operator-snapshot.json`: run identity, health/reasons, recovery guidance, stage outcomes, freshness timestamps, and Pages publication state. IPO records are deliberately excluded.

**Handoff:** next add bounded **operator health-transition history** so repeated failures/staleness can be distinguished from one-off events without accumulating unlimited workflow history.


### Bounded operator health history

The backend now retains up to **48 health transitions** in `ops/operator-health-history.json`. Consecutive identical states are compressed with an observation count, so repeated hourly healthy runs do not create unlimited history.

**Handoff:** next surface recurrence context from this bounded history in the read-only operator report; keep alerts and automatic recovery out of scope.


### Operator recurrence context

The operator report now shows the current retained state, consecutive observation count, and up to five recent health transitions from the bounded history. It explicitly handles the period before history is first recorded.

**Handoff:** next make rebuild, validation, and repository-publication failures first-class operator health reasons with reason-specific recovery guidance.


### First-class pipeline failure classification

The operator layer now distinguishes source collection, dataset rebuild, data validation, repository publication, and Pages deployment failures. Each has targeted diagnostic/recovery guidance; downstream failures are not mislabeled as source failures.

**Handoff:** next refine skipped/unmeasured stage semantics so expected downstream skips after an upstream failure are distinguished from unexpectedly unmeasured stages.


### Pipeline stage measurement semantics

The operator layer now distinguishes expected downstream skips after an upstream failure from unexplained skipped/unmeasured stages. Expected skips do not create redundant failures; unexplained stages become explicit `*_unmeasured` reasons with overall `unknown`.

**Handoff:** next add independent schema validation for operator snapshot/history JSON so malformed operational state is detected explicitly without affecting IPO data.
