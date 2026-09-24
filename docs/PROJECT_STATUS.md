# Project status and handoff

Updated: 2026-09-24 UTC (September 24 in America/Toronto).

## Current priority

Continue P1/P2/P3 backend correctness, official-source coverage and dependable publication under `DEVELOPMENT_PROCESS.md`. The active application-term requirement is **Lot Size only**; minimum investment, UI redesign, research-depth expansion and commercial infrastructure remain out of scope.

Never infer missing IPO values. Keep listing date, index admission date, market lot, minimum bid quantity and application amount distinct.

## Latest completed batch: four held historical BSE listings resolved — PR #177

PR #177 merged as:

`e142d031eca66481c41428b65384b7cb0eb6b748`

This closes all four remaining source/identity holds from the first historical BSE SME discovery batch.

### Root causes

The four records did not share one failure mode.

**Autofurnish, Mehul Telecom and Tipco Engineering India**

Their issuer-specific official BSE listing PDFs were correctly located and downloaded, but page 2 is image-only. The PDF text layer contains the notice header on page 1 while `pdftotext` cannot recover the page-2 listing statement or terms. The earlier rejection was therefore a text-extraction limitation, not contradictory issuer evidence.

The official immutable PDFs were visually reviewed on page 2 without OCR. The reviewed facts are bound to exact BSE PDF hashes:

| Issuer | Notice | PDF SHA-256 | Listing date | Market lot | Issue price |
| --- | --- | --- | --- | ---: | ---: |
| AUTOFURNISH LIMITED | `20260527-47` | `9d19ae886d5aba5c8835ccbb656488d69b3ba8dd91a47b2411b3e7a21e97b8c3` | 2026-05-29 | 3,000 | INR 41 |
| MEHUL TELECOM LIMITED | `20260423-27` | `b620aec3111262a67e52332ba2d379dbaef32533129a8ef1c2a3215d2ac2300f` | 2026-04-24 | 1,200 | INR 98 |
| TIPCO ENGINEERING INDIA LIMITED | `20260330-44` | `ce287772d38f0efc53c4994a235331a422697f3bac2116a628fe78068a3d2bbc` | 2026-04-01 | 1,600 | INR 89 |

These three use the new reviewed evidence kind `official_listing_pdf_visual_review`.

That contract is intentionally narrow:

- exact official BSE listing-PDF URL only;
- immutable source document SHA-256;
- reviewed visual page limited to pages 1–3;
- candidate issuer, scrip code and listing date must still agree with discovery identity;
- market lot must be a positive integer and issue price a positive scalar;
- retained source strings must explicitly contain the reviewed values;
- the listing statement must contain the issuer, “Equity Shares”, “shall be listed”, and exact listing-date phrase;
- no OCR result, BSE index notice or inferred value is accepted as authority.

The visual review is preserved in:

`data/verified-bse-listings/2026-09-24-batch7.json`

Source artifact for the three PDFs:

- run: **`35956034085`**
- artifact: **`10789439895`**
- artifact ZIP SHA-256: **`d78e344277d79ccce4411e3a7f4552b3eeb87089e3d584d8a1fa8a5c746d1acb`**

**Recode Studios**

The original index-derived candidate referenced BSE notice `20260511-16`. That official notice is not the final listing-details notice: it explicitly states that the listing date and security details will be informed through a separate notice.

The original claim is preserved as correction history rather than silently replaced.

Corrected discovery:

`data/discovery/bse-listing-candidates-2026-09-24-batch7.json`

Corrected issuer-specific listing notice:

- BSE notice: **`20260511-46`**
- BSE scrip code: **544755**
- listing date: **2026-05-12**
- market lot: **800**
- final issue price: **INR 158/share**
- official PDF SHA-256: **`b04afcddd0177f067b27727405256b5bfc60d8783d825a7497367ff01f46e29a`**
- collection time: **2026-09-24T04:59:43.736Z**
- listing/lot/price evidence: **page 2**

Independent corrected-source verification:

- workflow run: **`35957926014`**
- attempted: **1**
- verified: **1**
- rejected/unavailable: **0**
- artifact: **`10791635591`**
- artifact ZIP SHA-256: **`08edc97e797cfba08fcb33cd83ba476a15217eb669f12eee6746a560d8c760dc`**

Reviewed Recode manifest:

`data/verified-bse-listings/2026-09-24-batch8.json`

### Validation

Final PR-head checks:

- reviewed BSE evidence/importer validation: **`35958072837`** — success
- full data-contract validation: **`35958072891`** — success
- BSE source verification including corrected Recode: **`35958072853`** — success

The isolated real-import publication rehearsal measured:

- **964 -> 968 records**
- exactly **4 additions**
- **42 already-present** reviewed BSE records
- **0 held existing records**
- **0 identity conflicts**
- all **964 existing records unchanged**
- second import/rebuild: **no-op / idempotent**
- total retained reviewed BSE entries: **46**

An initial PR test run failed because the synthetic visual-review fixture omitted the same “Equity Shares … shall be listed” structure required by the tightened contract. The fixture was corrected to realistic source wording; the production evidence contract was not weakened.

### Production publication

A scheduled live sync had already started immediately before the merge. The `live-ipo-sync` concurrency guard correctly cancelled that stale scheduled run when the merge-triggered run queued.

Merge-triggered production sync:

- run: **`35958207898`**
- conclusion: **success**
- reviewed BSE import: **4 added / 42 already present / 0 holds**
- semantic publication: **4 added / 35 changed / 0 removed / 0 conflicts**
- schema 1.2.0 validation: **968 records passed**
- operator health: **healthy**

The 35 changed records are concurrent official NSE/SEBI enrichment from the same source-first run; the semantic publisher separately identified exactly four additions and zero removals/conflicts.

Source-backed data commit:

`93f4e0b02141c66d547e94b2f184dccaebe39d26`

Operator-state commit:

`69aa8fb5e348a7de55b167fdd403c38c7ebb9ea1`

Production after publication:

- **968 total IPO records**
- **84 records for 2026**
- 2026 board coverage: **15 mainboard / 59 SME / 10 unknown**
- each of the four repaired issuers occurs exactly once
- each listing date, market lot and issue price agrees with reviewed evidence
- all four source document hashes are retained
- unsupported price band, offer dates, issue size, minimum bid quantity and minimum application amount remain null
- deterministic build and schema validation passed
- operator health: **healthy**

### Deployment

Native GitHub Pages build **`35958746456`** completed successfully on:

`69aa8fb5e348a7de55b167fdd403c38c7ebb9ea1`

That operator-state revision directly descends from the 968-record data commit `93f4e0b02141c66d547e94b2f184dccaebe39d26`, so the deployed Pages revision contains the four-record release.

### First historical discovery batch is closed

The first durable-cursor discovery batch contained **23 listing references**.

Its final accounting is now:

- **6** were already present when reconciled;
- **17** were genuinely missing;
- all **17** missing issuers have now been resolved and published with reviewed issuer-specific official evidence;
- no candidates from that batch remain held.

Do not revisit the completed 23-reference batch unless later authoritative evidence creates an explicit correction.

### Next task

Re-read `ops/bse-sme-addition-notices.json` before starting the next run because the cursor advances independently.

At this handoff it remains:

- **40 / 236 parsed**
- **196 unseen**
- next unseen notice: **`20260107-29`**

The next scheduled cursor run has not yet advanced this state. Once it does, reconcile only the newly completed cursor batch against the current **968-record** universe, retain exact index-notice/listing-reference evidence, and verify/materialize only genuinely missing issuers.

If the cursor is still unchanged at the next continuation after its expected schedule window, inspect the cursor workflow execution/operational state as the next P3 reliability task. Do not manually reset the cursor or repeat the now-closed first historical batch.

## Latest completed batch: remaining seven historical BSE SME listings published — PR #176

PR #176 merged as:

`9edcbb30d0a62575e12c0116a2533564ffffc4f2`

This completed the publishable subset from the first historical BSE discovery reconciliation. Combined with PR #175's six PDF-backed records, all **13 issuer-specific candidates that independently verified in PR #174 are now published**. The four candidates that failed issuer-specific verification remain held.

### Evidence-path repair

The remaining seven records had verified official BSE listing-notice HTML but no usable canonical archive listing-PDF path. PR #176 tested the notice-bound `DownloadAttach.aspx` links exposed by those pages.

Those attachment URLs were constrained to:

- `https://www.bseindia.com/markets/MarketInfo/DownloadAttach.aspx`;
- exact matching listing-notice ID;
- UUID-shaped attachment ID;
- a maximum of four notice-bound attachment probes.

The attachments were real BSE PDFs, but they were ancillary Annexure documents rather than the listing notice itself and correctly failed the listing verifier with missing listing-notice identity/content. They are **not** used as listing authority.

Instead of weakening the PDF contract, PR #176 added a separate reviewed **official-notice HTML** contract. An HTML-backed reviewed entry must retain and revalidate:

- the exact issuer-specific BSE notice URL;
- BSE notice number and publication date;
- raw HTTP-response SHA-256;
- normalized evidence-text SHA-256;
- collection timestamp;
- issuer name, SME segment, scrip code and equity-listing statement;
- listing date, market lot and final issue price;
- an offline replay through the existing `verifyListingHtml` identity/fact verifier.

HTML evidence does not invent pagination. Published fields and board/status evidence use `page: null`.

The PDF contract remains strict and separate: PDF-backed entries still require the bounded official PDF URL, document hash, page excerpts, page identity and `verifyListingPdfText` replay.

### Source verification retained

The reviewed HTML evidence came from:

- workflow run: **`35956034085`**
- artifact: **`10789439895`**
- artifact ZIP SHA-256: **`d78e344277d79ccce4411e3a7f4552b3eeb87089e3d584d8a1fa8a5c746d1acb`**

Reviewed manifests:

- `data/verified-bse-listings/2026-09-24-batch5.json` — 2 entries
- `data/verified-bse-listings/2026-09-24-batch6.json` — 5 entries

Exact published facts:

| Issuer | BSE code | Listing notice | Listing date | Market lot | Issue price |
| --- | --- | --- | --- | ---: | ---: |
| ELFIN AGRO INDIA LIMITED | 544724 | `20260311-44` | 2026-03-12 | 3,000 | INR 47 |
| PAN HR SOLUTION LIMITED | 544698 | `20260212-30` | 2026-02-13 | 1,600 | INR 78 |
| KANISHK ALUMINIUM INDIA LIMITED | 544693 | `20260203-43` | 2026-02-04 | 1,600 | INR 73 |
| ACCRETION NUTRAVEDA LIMITED | 544694 | `20260203-44` | 2026-02-04 | 1,000 | INR 129 |
| MSAFE EQUIPMENTS LIMITED | 544695 | `20260203-45` | 2026-02-04 | 1,000 | INR 123 |
| ARITAS VINYL LIMITED | 544683 | `20260122-19` | 2026-01-23 | 3,000 | INR 47 |
| YAJUR FIBRES LIMITED | 544676 | `20260113-25` | 2026-01-14 | 800 | INR 174 |

Unsupported price band, offer dates, monetary issue size, minimum bid quantity and minimum application amount remain null for all seven unless supported separately by another official source.

### Pre-merge validation

Final PR-head validation:

- reviewed BSE evidence/importer validation: **`35956420754`** — success
- full data-contract validation: **`35956420683`** — success
- issuer-specific BSE source diagnostics: **`35956420702`** — success
- protected code-544770 regression/source verification: **`35956420680`** — success

The isolated publication rehearsal used the real importer, publisher and validators:

- **957 -> 964 records**
- exactly **7 additions**
- **35 already-present** reviewed BSE records
- **0 held existing records**
- **0 identity conflicts**
- all **957 existing records unchanged**
- second import/rebuild: **no-op / idempotent**
- total retained reviewed BSE entries after this batch: **42**

### Production publication

Merge-triggered live sync:

- run: **`35956583736`**
- conclusion: **success**
- reviewed BSE import: **7 added / 35 already present / 0 holds**
- semantic publication: **7 added / 36 changed / 0 removed / 0 conflicts**
- schema 1.2.0 validation: **964 records passed**
- operator health: **healthy**

The 36 changed records are normal concurrent official NSE/SEBI enrichment from the same source-first run. The semantic publisher separately identified the seven additions and zero removals/conflicts.

Source-backed data commit:

`40c8326db90e1c8d29d98cc2c998aa88d159742c`

Operator-state commit:

`ad52c686ebfad609aab8e33db686c34e082ce256`

Production after publication:

- **964 total IPO records**
- **80 records for 2026**
- 2026 board coverage: **15 mainboard / 55 SME / 10 unknown**
- all seven new issuers occur exactly once on current `main`
- each retains its reviewed BSE notice URL and document hash
- each verified listing date, market lot and issue price agrees with the reviewed manifest
- HTML-backed field/page metadata remains `page: null`
- unsupported fields remain null
- the four rejected candidates remain absent
- deterministic build and schema validation passed
- operator health: **healthy**

### Deployment

GitHub Pages dynamic build **`35957085010`** completed successfully on:

`ad52c686ebfad609aab8e33db686c34e082ce256`

That commit is one commit ahead of and directly descends from source-backed data commit `40c8326db90e1c8d29d98cc2c998aa88d159742c`, so the deployed Pages revision contains the 964-record release.

The custom `ops/pages-publication.json` snapshot still refers to the merge-triggered deploy attempt because bot-authored data/operator commits do not necessarily re-trigger that custom persistence workflow. The native Pages build above is the authoritative descendant deployment evidence for this data commit.

### Remaining holds

The four rejected candidates from the same historical discovery batch remain excluded:

- AUTOFURNISH LIMITED — `20260527-47`
- RECODE STUDIOS LIMITED — `20260511-16`
- MEHUL TELECOM LIMITED — `20260423-27`
- TIPCO ENGINEERING INDIA LIMITED — `20260330-44`

Current recovery data confirms all four are absent. Do not infer them from SME-index discovery evidence. They require a separate issuer-identity/source repair.

### Next task

Re-read `ops/bse-sme-addition-notices.json` before starting the next run because its scheduled workflow advances independently.

At this handoff the durable cursor is still:

- **40 / 236 parsed**
- **196 unseen**
- next unseen notice: **`20260107-29`**

If the cursor has advanced by the next prompt, reconcile the newest completed cursor discovery batch against the current production universe and verify only genuinely missing/unambiguous issuers with issuer-specific official BSE evidence.

If it has not advanced, keep the cursor independent and use the next bounded P1/P2 batch to investigate the four held issuer/source mismatches. Do not reset the cursor, duplicate the 13 now-published historical records, or infer values from BSE index-addition notices.

## Latest completed batch: six historical BSE SME listings published — PR #175

PR #175 merged as:

`6059dab836760e8d9c658101a3e1e536683bd039`

It completed the safe publishable subset from the first historical discovery reconciliation without weakening the reviewed-evidence importer.

### Why only 6 of the 13 verified candidates were published

The existing reviewed importer intentionally requires an issuer-specific official BSE listing **PDF**, document hash, and page-backed excerpts.

The prior source run had 13 issuer identities that verified through official BSE listing notices, but only 6 had PDF evidence. PR #175 added an opt-in PDF-upgrade probe for already verified HTML notices and tested that behavior without changing the default retry semantics.

Source run:

- workflow: **`35954818300`**
- artifact: **`10789632860`**
- artifact ZIP SHA-256: **`3c312c2077a4e8ddfc170c50aa65ea54874ceb53fbfff813fdd882506f4db99f`**

The PDF upgrade confirmed:

- **6 PDF-backed verified candidates**
- **7 official-HTML verified candidates whose canonical archive PDF path returns HTTP 404**
- the previously identified **4 rejected candidates remain rejected**

The importer was not relaxed. HTML verification was not converted into fake page evidence.

### Reviewed batch 4

Committed manifest:

`data/verified-bse-listings/2026-09-24-batch4.json`

| Issuer | BSE code | Listing notice | Listing date | Market lot | Issue price |
| --- | --- | --- | --- | ---: | ---: |
| M.R. MANIVENI FOODS LIMITED | 544768 | `20260529-40` | 2026-06-01 | 2,000 | INR 52 |
| VEGORAMA PUNJABI ANGITHI LIMITED | 544765 | `20260526-31` | 2026-05-27 | 1,600 | INR 77 |
| GOLDLINE PHARMACEUTICAL LIMITED | 544759 | `20260518-28` | 2026-05-19 | 3,000 | INR 43 |
| SAFETY CONTROLS & DEVICES LIMITED | 544746 | `20260410-44` | 2026-04-13 | 1,600 | INR 80 |
| EMIAC TECHNOLOGIES LIMITED | 544747 | `20260410-43` | 2026-04-13 | 1,200 | INR 98 |
| NOVUS LOYALTY LIMITED | 544735 | `20260324-28` | 2026-03-25 | 1,000 | INR 146 |

Only explicit listing date, market lot and final issue price are retained from the listing PDFs. Unsupported price-band, offer-date, issue-size and application fields remain null unless supported by another official source.

### Pre-merge validation

Final PR workflows:

- reviewed BSE evidence/importer validation: **`35955058014`** — success
- full data-contract validation: **`35955057967`** — success
- BSE candidate/source diagnostics: **`35955057960`** — success
- 544770 regression/source verification: **`35955057944`** — success

The isolated real-import rehearsal measured:

- **951 -> 957 records**
- exactly **6 additions**
- **29 already-present** reviewed BSE records
- **0 held existing records**
- **0 identity conflicts**
- all **951 existing records unchanged**
- second import/rebuild: **no-op / idempotent**
- total reviewed BSE evidence entries after this batch: **35**

### Production publication

Merge-triggered live sync:

- run: **`35955112253`**
- conclusion: **success**
- reviewed BSE import: **6 added / 29 already present / 0 holds**
- semantic publication: **6 added / 37 changed / 0 removed**
- operator health: **healthy**

The 37 changed records are normal concurrent official NSE/SEBI enrichment from the same source-first run; the semantic publisher separately reported exactly 6 additions and 0 removals.

Source-backed data commit:

`fc5e0ec5e6bd9fb3c065544465066827a4005940`

Operator-state commit:

`9c07573b1ca27d48d93724236fbbde30971f11c2`

Production after publication:

- **957 total IPO records**
- **73 records for 2026**
- 2026 board coverage: **15 mainboard / 48 SME / 10 unknown**
- deterministic publication/recovery checks: passed
- schema validation: passed
- operator health: **healthy**

The exact six records are present on current `main` with their BSE scrip codes, verified listing date, market lot, issue price, document hash and batch-4 provenance.

### Deployment verification

GitHub Pages dynamic build **`35955643913`** completed successfully on:

`9c07573b1ca27d48d93724236fbbde30971f11c2`

That revision is a descendant of source-backed data commit `fc5e0ec5e6bd9fb3c065544465066827a4005940`, so the deployed Pages revision contains the six-record release.

A direct HTTP fetch of the deployed JSON could not be performed from this execution environment because external DNS resolution was unavailable. Deployment verification therefore uses the successful descendant Pages build plus exact current-main recovery records and the successful production publication log.

### Remaining seven HTML-verified candidates

These issuer-specific BSE notice pages independently verified identity and listing facts, but the official archive PDF probe returned **HTTP 404** for each:

| Issuer | Listing notice |
| --- | --- |
| ELFIN AGRO INDIA LIMITED | `20260311-44` |
| PAN HR SOLUTION LIMITED | `20260212-30` |
| KANISHK ALUMINIUM INDIA LIMITED | `20260203-43` |
| ACCRETION NUTRAVEDA LIMITED | `20260203-44` |
| MSAFE EQUIPMENTS LIMITED | `20260203-45` |
| ARITAS VINYL LIMITED | `20260122-19` |
| YAJUR FIBRES LIMITED | `20260113-25` |

They are **not published yet**. Their official HTML evidence is retained in the verification artifacts, but the current reviewed importer correctly rejects evidence without the required PDF/page contract.

### Four rejected candidates remain held

Do not publish or infer from the SME-index references:

- AUTOFURNISH LIMITED — `20260527-47`
- RECODE STUDIOS LIMITED — `20260511-16`
- MEHUL TELECOM LIMITED — `20260423-27`
- TIPCO ENGINEERING INDIA LIMITED — `20260330-44`

These remain a separate issuer-identity/source-repair problem.

### Next task

Repair the official evidence path for the **seven HTML-verified / PDF-404** notices.

Acceptance requirements:

- first inspect the exact BSE notice pages for attachment/download URLs or another official BSE document endpoint;
- preserve the already verified HTML response hashes and identities;
- if an official document exists, verify it independently and retain its hash/page evidence before publication;
- if BSE genuinely exposes only HTML, design a **separate reviewed official-HTML evidence contract** that retains URL, notice identity, publication date, response hash, collection timestamp and exact excerpts;
- do not invent page numbers or silently weaken the PDF evidence contract;
- keep the four rejected candidates out of this batch;
- after resolving this source family, return to the independent historical cursor, currently **40/236 parsed with 196 unseen** (next unseen notice remains `20260107-29`).

The historical cursor itself remains independent and must not be reset or coupled to live sync.

## Latest completed batch: first historical BSE discovery reconciliation

PR #174 reconciled the first historical cursor batch from BSE SME addition-notice run **`35952980189`**.

### Reconciliation result

The cursor's next 20 parsed notices produced **23 listing references**. Exact comparison with the current 2026 recovery universe found:

- **6 already present**
- **17 missing exact identities**
- **0 identity-review/fuzzy-match cases**

No index-only candidate was promoted. The reconciliation is retained in:

`data/discovery/bse-listing-reconciliation-2026-09-24.json`

The 17 missing candidates were split to respect the verifier's 15-record safety bound:

- `data/discovery/bse-listing-candidates-2026-09-24-batch4.json` — 15
- `data/discovery/bse-listing-candidates-2026-09-24-batch5.json` — 2

### Issuer-specific source verification

PR source run **`35954077034`** completed both candidate batches.

Final issuer-specific official BSE listing-notice result:

- attempted: **17**
- verified: **13**
- rejected: **4**
- unavailable: **0**

Artifact:

- id: **`10789631977`**
- ZIP SHA-256: **`f493f894524bc666b8652b8726283122e85f87fb00e93d96fc258a7090cc9ad6`**

Batch 5 verified **2/2**. Batch 4 verified **11/15** after the official PDF archive retry.

The four rejected candidates are intentionally held:

| Issuer | Listing notice | Rejection |
| --- | --- | --- |
| AUTOFURNISH LIMITED | `20260527-47` | scrip code missing/mismatch; listing date missing/mismatch; equity-listing statement missing |
| RECODE STUDIOS LIMITED | `20260511-16` | scrip code missing/mismatch; listing date missing/mismatch |
| MEHUL TELECOM LIMITED | `20260423-27` | scrip code missing/mismatch; listing date missing/mismatch; equity-listing statement missing |
| TIPCO ENGINEERING INDIA LIMITED | `20260330-44` | scrip code missing/mismatch; listing date missing/mismatch; equity-listing statement missing |

These are source-verification failures, not permission to infer values from the SME-index notices. Preserve them as unresolved discovery evidence until issuer identity/source repair proves the correct listing notice or bounded parser fix.

### Validation

On the final PR head:

- Validate reviewed BSE listing evidence: **success** — run `35954077035`
- Validate IPO data contract: **success** — run `35954077036`
- Verify BSE listing candidates: **success as a diagnostic collection run** — run `35954077034`; it intentionally retained the four rejected candidates instead of treating them as publishable.

No IPO records are materialized by this PR. Production remains **951 records / 67 records for 2026** until reviewed evidence for the 13 verified issuers is committed and imported.

### Next task

Convert only the **13 verified** results from artifact `10789631977` into reviewed BSE evidence manifests with document hashes/page excerpts, revalidate them offline through the existing importer, then publish those 13. Keep the four rejected candidates held for a separate source/identity repair batch. The independent historical BSE cursor must continue advancing and must not be reset.

## Latest completed batch: BSE 544770 conflict resolved and published

PR #171, **Resolve BSE 544770 identity conflict**, merged at:

`71f0f0c3824269621734e65cdd0e4abfe0c097bc`

The retained discovery conflict is now resolved by issuer-specific official BSE listing notices:

- **YAASHVI JEWELLERS LIMITED** — BSE Listing Notice `20260601-25` independently confirms **scrip code 544770**, listing date **2026-06-02**, market lot **1,600**, and final issue price **INR 83/share**.
- **MERRITRONIX LIMITED** — BSE Listing Notice `20260605-37` independently confirms **scrip code 544773**, listing date **2026-06-08**, market lot **1,000**, and final issue price **INR 149/share**.

The older BSE SME index-addition notice `20260608-14` had associated Merritronix with `544770`. That claim is preserved as **superseded discovery evidence** rather than silently deleted or selected by recency. Yaashvi's earlier index notice `20260602-17` and its listing notice both support `544770`.

### Conflict/source verification

The first conflict probe intentionally used the original index-derived identities separately:

- Merritronix candidate `544770` was **rejected only for scrip-code mismatch**, with the issuer-specific PDF observing `544773`;
- Yaashvi candidate `544770` was **verified**.

The corrected two-record batch then verified **2/2**, with 0 rejected and 0 unavailable.

Successful corrected source run:

- workflow: `35950849004`
- artifact: `10787659263`
- artifact SHA-256: `f969117ce1895c8d9d17f5b3ba2a2dfe91640f5f71367898c65f330520c04e21`
- Merritronix PDF SHA-256: `920101f48760a903cf0f41424f0df00077cd2f85987feed8fe3f91244b9bf0be`
- Yaashvi PDF SHA-256: `22e26ebf183205834b468993d4441d5eea66a14e2c775464e70c05eed2f37dfd`

Retained inputs/evidence:

- `data/discovery/bse-listing-conflict-544770-merritronix.json`
- `data/discovery/bse-listing-conflict-544770-yaashvi.json`
- `data/discovery/bse-listing-candidates-2026-09-24-batch3.json`
- `data/verified-bse-listings/2026-09-24-batch3.json`
- `.github/workflows/verify-bse-544770-conflict.yml`

Batch 3 retains Merritronix's original index claim and the issuer-specific correction in machine-readable form. Only explicit issuer-specific listing-date, market-lot and final-issue-price facts are publishable.

### Pre-merge validation

All three PR workflows passed on the reviewed batch:

- conflict/source verification: `35950980614`;
- reviewed BSE evidence/importer validation: `35950980623`;
- full data-contract validation: `35950980645`.

The isolated publication rehearsal measured:

- **949 -> 951 records**;
- exactly **2 records added**;
- **27 already-present** reviewed BSE records;
- **0 existing records changed by the BSE importer**;
- **0 held conflicts**;
- second import/rebuild: **no-op / idempotent**.

### Production publication

Merge-triggered live sync:

- run: **`35951056853`**
- conclusion: **success**
- reviewed BSE import: **2 added, 27 already present, 0 holds**
- semantic publication: **2 added, 31 changed, 0 removed**

The additional changed records are normal concurrent NSE/SEBI enrichment from the same source-first run; semantic merge reported zero conflicts.

Source-backed data commit:

`6221738a93158e5831c524d4bc8883103492cce5`

Production after publication:

- **951 total IPO records**
- **67 records for 2026**
- 2026 board coverage: **15 mainboard / 42 SME / 10 unknown**
- 2026 verified issue price: **49**
- 2026 verified market lot: **55**
- 2026 verified listing date: **49**
- deterministic recovery build: passed
- schema 1.2.0 validation: passed
- operator health: **healthy**

The production diff shows both new records retaining page-2 BSE evidence, document hashes, collection times and batch-3 provenance. Unsupported raw terms remain null: price band, offer dates, INR issue size and minimum bid quantity are not inferred.

### Deployment

The source-backed data commit was followed by operator-state commit `cf04c69179cd5935e8b04d212d56cc20360f7d40`. GitHub Pages build **`35951543912`** completed successfully on that descendant revision, so the deployed Pages artifact includes the 951-record dataset and both resolved records.

This conflict is **closed**. Do not re-open it from index evidence or change Merritronix back to `544770`.

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

### Independent live-data check and release safeguards — PR #167

The live dataset itself was fetched after publication at **2026-09-24T02:36:18.996Z**, separately from dataset generation time **2026-09-24T02:31:21.345Z**. This was not merely a check that a Pages job was green.

The retained live snapshot contains **949 records**. Each of the **27 issuers and 81 listing-date/market-lot/issue-price fields** across both reviewed batches was compared with the committed evidence: every issuer appears once, every value agrees, every field is verified and retains the corresponding official PDF URL and page 2. Both held issuers remain absent. All six unsupported fields in the 12 new records remain null/missing: price band, open date, close date, INR issue size, minimum bid quantity and minimum application amount. The actual live snapshot also passes the schema 1.2.0 core validator.

PR #167 merged at `3a89120f498f18e54fcd1b26340cf090446e22fe`. During its independent verification, PR #168 reached main with the same 12 issuers. GitHub correctly blocked the stale merge. The final reconciliation preserves #168's canonical `batch2` manifests, importer, PDF rejection classification and ligature repair unchanged. The alternative unmerged `batch-02` manifests and approval-registry implementation were dropped from the PR diff, never added to production. Do not reintroduce that superseded alternative or duplicate the 12 records.

The final #167 change is restricted to:

- `scripts/test-bse-publication-rehearsal.mjs`: an isolated run of the real importer, publisher and validators, proving existing public records are unchanged, unrelated yearly manifests are byte-identical and a second import/rebuild causes no timestamp churn;
- `.github/workflows/validate-reviewed-bse-listings.yml`: runs this end-to-end rehearsal before merge;
- `.github/workflows/verify-bse-listing-candidates.yml`: retains a tracked-source ZIP for reproducible tests and a separately timestamped deployed-data snapshot in the existing read-only artifact. No permission expansion or new PDF work inside hourly sync.

All **34 reconciled local test scripts** passed using the actual repository modules, without matcher substitutes. The publication rehearsal measured **937 -> 949**, exactly 12 added and 15 already present, with all 937 pre-existing public records unchanged and a no-op second import. Production's normal NSE/SEBI enrichments in the same sync are distinct from this isolated no-overwrite test.

All three final PR workflows passed: data-contract CI `35947529604`, reviewed-evidence CI `35947529606`, and independent source verification `35947529605`. Post-merge data-contract `35947640996` and reviewed-evidence `35947640921` also passed.

Independent source verification `35946186883` had already checked the same 12 original PDFs; all 12 document hashes and all 36 values/pages agree with the preserved canonical batch. All 24 header/fact pages were rendered and reviewed. Reconciled source run `35947529605` and its post-publication attempt 2 both verify 12/12, with 0 rejected/unavailable.

#### Reproducible evidence retention

The post-publication artifact is `bse-listing-verification-35947529605-2`, ID **10787263725**, from attempt 2. It retains the original listing PDFs, HTML attempts, verification report, tracked-source ZIP and actual deployed-data snapshot.

- ZIP SHA-256: `22dd81e6868e8907184e5efe8089aba00ce674ff7b2cd160d2ddd98ac20aabb6`
- Deployed snapshot-file SHA-256: `5c7f4df154afe0ed14db78ae2157575e93c9308f3ee00c1cfa23d44e71cd444f`
- Artifact expiry: `2026-10-08T02:36:37Z`
- A copy of this artifact and the machine-readable 27-record/81-field live-check report were retained in the conversation.

The independent pre-reconciliation source artifact remains available as ID `10787195768`, run `35946186883`, ZIP SHA-256 `8a0a777a7c29dfef19da9e6549aa1f626b070dccfae6d395333e8d6e294b9612`. Its source ZIP is an earlier revision, not the final reconciled implementation.

This release is **verified live**. Do not repeat the first 15 or remaining 12 listing imports or their completed ligature/source-delivery diagnoses.

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

## Completed: durable historical BSE notice cursor — PR #173

PR #173 merged at `2dcd60597c0fb8995a446efa00199138034b1603`.

The BSE SME addition-notice backfill is now independent, bounded and durable:

- operational state: `ops/bse-sme-addition-notices.json`;
- parser version: `1.1.0`;
- maximum batch: **20 notices**;
- schedule: every two hours, independent of the live IPO critical path;
- state is keyed by BSE notice ID, not positional offsets, so new notices do not shift historical progress;
- parser-version changes requeue earlier notices deterministically;
- unseen notices advance before retries so a failed notice cannot block the older backlog;
- failed/fetch-error/unparseable notices remain in state with attempt timestamps and are retried after cooldown;
- semantic state publication resets to latest main, merges notice-by-notice and retries pushes without rewriting IPO values.

The newest 20 successful notices were bootstrapped from retained audit run `35939161246`, artifact `10783988662`, rather than being fetched again. That bootstrap represents 29 previously reviewed discovery references and remains operational state only.

### First production historical batch

Merge-triggered workflow run:

- run: **`35952980189`**
- conclusion: **success**
- report artifact: **`10788684195`**
- artifact SHA-256: `1dde2b06eb2ce178800e6fc382895b1ad57b7458be3077e3f46098c0a248b544`
- state commit: **`6a8a21ce8c0befea1a3c67911472c3aff731c7f1`**

Observed progress:

- eligible notices: **236**
- before: **20 parsed / 216 unseen**
- selected: **20 older notices**
- parsed: **20/20**
- fetch errors: **0**
- unparseable: **0**
- new discovery references: **23**
- after: **40 parsed / 196 unseen**
- next unseen notice: **`20260107-29`**

The batch moved from the June 1, 2026 notice backward through January 13, 2026. Some older notices lacked a direct catalog PDF URL and were parsed through the existing official BSE Index Services detail endpoint; that fallback remains source-labelled in cursor state.

**Important:** these 23 references are discovery candidates only. This workflow never creates or edits IPO records. Every candidate still requires issuer-specific official BSE listing evidence before materialization.

## Next task: reconcile the first historical discovery batch

The next bounded P1/P2 task is to compare the **23 newly discovered references** from run `35952980189` against the current **951-record** production universe and retained BSE evidence.

Acceptance requirements:

- separate already-present issuers from genuinely missing candidates;
- retain exact index notice identity, listing-reference notice number, scrip code, listing date and source hash;
- never infer equivalence from fuzzy names when identity is ambiguous;
- for missing/unambiguous issuers, verify issuer-specific official BSE listing notices in a bounded batch before publication;
- preserve null unsupported fields;
- do not stop or reset the new historical cursor—the independent scheduled backfill should continue advancing the remaining **196** notices.

## Prior handoffs

- First reviewed 15-record BSE listing batch: `archive/PROJECT_STATUS-before-bse-listing-batch2.md`
- PR #165 discovery/notice-repair state: `archive/PROJECT_STATUS-before-bse-listing-batch.md`
- Older accumulated milestones remain under `docs/archive/`.

Current repository, workflow and deployment evidence supersede stale next-task instructions in archived handoffs.
