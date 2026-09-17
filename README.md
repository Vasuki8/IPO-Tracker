# India IPO Tracker

## Standing product direction and current work

IPO Tracker is intended to become a public commercial product. The paying audience,
pricing and revenue model are not selected. Trustworthy source-linked facts,
repeat research, accessibility, stable public URLs and sustainable operation take
precedence over adding paid features. No new spend, contracts, external outreach
or material access changes without owner approval.

Follow [the owner roadmap](docs/ROADMAP.md), [current engineering status](docs/PROJECT_STATUS.md)
and [commercial readiness register](docs/COMMERCIAL_READINESS.md). The dated audit
is historical evidence; current source/data/release receipts take precedence.
Keep the light static architecture while it meets requirements. P5 and performance
expansion remain blocked until the existing P4 correctness gate passes.

**Public display authority:** record-level exchange agreement is not whole-IPO
verification. Completed static terms require matching Final Prospectus field
proofs; permitted active bidding observations are explicitly provisional. Disputed
figures are withheld from accepted-value views and exports while original values,
source proofs and review history remain intact. Observation time, collection time,
market lot and minimum bid quantity are distinct. Earlier implementation notes
below do not override these rules. See [public methodology](methodology.html).

A static, source-aware website for tracking Indian IPOs from **SEBI filing through exchange listing**. The frontend is plain HTML/CSS/JavaScript, currently delivered by GitHub Pages; commercial hosting suitability remains unresolved. Python updaters build and enrich the normalized `data/ipos.json` database.

## Research workspace

- **Explore IPOs:** status, company, board and year filters; seven sorting options; 25/50-row pagination; and CSV export of all matching records. The default Open first sort starts with open offers ordered by closing date, followed by upcoming issues and then recent closing/listing activity. Individual filter chips can be removed without resetting the rest. Search and filter state is kept in the URL and restored when returning from a company profile.
- **IPO calendar:** opening, closing and listing events grouped by date, with month navigation. Issues without an opening date are available under **Dates pending** in the directory.
- **Watchlist:** bookmark issues from the directory, quick view or permanent company profile in the current browser. This is device-local storage, with no account or cross-device sync.
- **Compare:** select two or three IPOs to compare the available issue terms, lot size and one-lot value at the price-band cap, dates, timestamped subscription and listing return.
- **Company profiles:** permanent URLs and an explicit quick-view action; responsive issue terms, lifecycle, subscription charts and snapshots, offer information, financials, documents and source validation.
- **Data & sources:** source diagnostics and coverage/repair details are available in a dedicated view. Coverage payloads load only when that view is opened.

The compact light interface uses a mobile card layout for IPO results, six visible status filters, a persistent navigation/search bar, keyboard-accessible actions and reduced-motion support. The directory shows one-lot value at the upper price band for current offers, and listing return when exploring listed issues. Subscription figures distinguish source observation from collection time; exports include lot terms and subscription provenance. A dash means the value is unavailable. Display changes do not alter canonical source records or collection policy.

### Browser checks

The **Frontend browser checks** workflow runs the actual site through Chromium and retains screenshots and failure traces. It installs its test runtime in the runner's temporary directory; the published site has no new runtime dependencies. To run locally with an installed Playwright/Chromium test runtime, serve the repository over HTTP and run `node tests/frontend_smoke.cjs`, followed by `node tests/frontend_quality_layout.cjs`. `BASE_URL` and `SMOKE_ARTIFACT_DIR` configure both suites. The main smoke suite also supports `PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH` and `PLAYWRIGHT_CHROMIUM_ARGS` for local test environments. The quality-layout check verifies text boundaries as well as page overflow, so a clipped source label cannot pass merely because the page fits the screen.

## Data architecture

The sources deliberately have different roles:

- **SEBI** — earliest official discovery layer. Scans Public Issues filings for DRHP/UDRHP/RHP/final prospectus records and retains official document links.
- **NSE** — primary exchange spine for current issues, upcoming issues, issue details and historical IPO records.
- **Exchange subscription detail** — Phase 4 live-demand layer. NSE `/api/ipo-detail` is preferred for QIB, NII/HNI, Retail/Individual and Total multiples. If NSE's web firewall blocks the GitHub Actions runner, the collector uses BSE's official Cumulative Demand Schedule for the same live issue. Changed observations are retained as timestamped history rather than overwritten.
- **BSE** — independent exchange validation layer. It fills missing values but cannot silently overwrite populated NSE values, and it provides the official subscription fallback described above.
- **Final Prospectus documents** — canonical authority for completed static terms. Supported, source-bound fields include issue composition, lead managers, registrar, promoters, use of proceeds, promoter holding and restated financials. Draft/RHP links remain historical disclosures, not substitutes for completed-term verification.

When NSE and BSE disagree on comparable fields, the record is marked `conflict`. Both original observations remain in labelled diagnostics; disputed accepted-value fields are withheld.

Official source pages:

- SEBI Public Issues: https://www.sebi.gov.in/filings/public-issues.html
- NSE IPO data: https://www.nseindia.com/market-data/all-upcoming-issues-ipo
- NSE issue/bid detail: https://www.nseindia.com/market-data/issue-information
- BSE Public Issues: https://www.bseindia.com/markets/PublicIssues/IPOIssues_new.aspx?id=1&Type=p

## Run locally

```powershell
# from the project folder
uv sync --frozen
uv run --frozen python scripts/build_company_pages.py
uv run python -m http.server 8000
```

Open `http://localhost:8000`.

> Do not open `index.html` with `file://`; the browser cannot reliably fetch the public summary and profile routes that way.

## Refresh all official sources

```powershell
uv run --frozen python scripts/run_pipeline.py --mode core
uv run --frozen python scripts/run_pipeline.py --mode subscriptions
uv run --frozen python scripts/run_pipeline.py --mode maintenance
```

The routine refresh performs:

1. NSE current + upcoming + historical refresh.
2. Recent SEBI filing scan and offer-document collection.
3. BSE current IPO-only validation.
4. Live QIB/NII/Retail/Total subscription capture for open issues, preferring NSE and falling back to BSE's official cumulative-demand schedule when needed.
5. Cross-source validation and conflict flagging.
6. Incremental Final Prospectus extraction within the active priority gate.

### Historical NSE backfill — after the P4 gate passes

```powershell
uv run python scripts/run_update.py --bootstrap-history --history-from 2000-01-01
```

### Deeper SEBI filing scan

```powershell
uv run python scripts/run_update.py --sebi-pages 20
```

### Extract all eligible offer documents

```powershell
uv run --frozen python scripts/run_offer_documents.py --limit 0
```

The offer-document extractor is incremental and respects the current priority gate. Completed-term verification requires a Final Prospectus; legacy abridged/RHP extraction does not satisfy that authority. Parser or source changes and unresolved revalidation can make an existing document eligible again.

### Capture/debug one IPO's subscription data

```powershell
uv run python scripts/track_subscriptions.py --company "Company Name" --force-snapshot
```

Routine subscription runs only inspect IPOs whose exchange bidding window is open. A new history row is stored when QIB/NII/Retail/Total values change; `subscriptionAsOf` records the latest successful collection check even when the multiples are unchanged.

### Debug one source at a time

```powershell
uv run python scripts/run_update.py --skip-sebi --skip-bse
uv run python scripts/run_update.py --skip-bse
uv run python scripts/run_update.py --skip-sebi
uv run --frozen python scripts/run_offer_documents.py --company "Company Name" --force
```

## GitHub Pages deployment

The current repository deploys branch `main` from `/ (root)`. Use the already-authorized workflow permissions; do not broaden repository or organization permissions to work around a failed check. Commercial hosting suitability must be resolved before monetizing affected features.

One workflow, **Collect and publish IPO data**, collects sources and publishes through a serialized, validated merge. It preserves concurrent edits and pending conflicts, and explicitly requests a Pages rebuild. Manual runs select a scoped collection mode; `presentation` only rebuilds public projections from current accepted main without collecting, correcting or resolving data. Pure presentation pushes select that path; mixed or unknown source changes remain repair runs. See [the operations guide](docs/OPERATIONS.md) for schedules, repair semantics and phase gates and [project status](docs/PROJECT_STATUS.md) for current release evidence.

For a presentation release, require the frozen Python suite, Node quality tests, rebuilt public projections, canonical byte preservation and both browser suites. After merge, require the actual publication commit and successful Pages deployment; inspect affected deployed profiles before marking the release complete. A parser merge, green preview or local generated HTML alone is not publication.

## NSE website endpoints used

- `/api/ipo-current-issue`
- `/api/all-upcoming-issues?category=ipo`
- `/api/ipo-detail?symbol=...&series=EQ|SME`
- `/api/public-past-issues?from_date=DD-MM-YYYY&to_date=DD-MM-YYYY`

These are public website data endpoints rather than a guaranteed commercial API. The updater uses cookie priming, retries and conservative failure handling. Phase 4 can fall back to BSE's official cumulative-demand page when NSE blocks a cloud runner. Accessibility does not establish commercial-use or redistribution rights.

## Phase 3 structured fields

When supported by matching Final Prospectus field evidence, records can include:

- `issueComposition.freshShares`, `ofsShares`, and source-supported final fresh/OFS amounts; a price-band cap is not a final issue price
- `leadManagers`
- `registrar`
- `promoters`
- `objectsOfIssue[]` with amounts normalized to ₹ crore
- `financials.periods[]` for revenue, EBITDA, PAT, net worth, RONW/ROE and EPS when disclosed
- `shareholding.promoterPreIssuePct`
- `offerDocumentExtraction` with source PDF, parser version, SHA-256, pages parsed and extraction timestamp

Accepted Final Prospectus repairs can correct legacy static values with before/after audit history and matching source evidence. Unsupported layouts remain flagged for review. Merely populated fields or a successful parse do not establish verification.

## Phase 4 subscription fields

For live/open issues, records can include:

- `subscription.qib`
- `subscription.nii`
- `subscription.retail` — also accepts NSE's newer SME `Individual Investor` terminology
- `subscription.total`
- `subscriptionAsOf` — timestamp of the latest successful collection check
- `subscriptionObservedAt` / `subscriptionCollectedAt` / `subscriptionTimeBasis` — source time, collection time and their distinction
- `subscriptionSource` / `subscriptionSourceUrl` — the labelled source used for the accepted snapshot
- `subscriptionHistory[]` — changed snapshots with `capturedAt`, available `observedAt`, multiples and source provenance

The public projection also exposes `subscriptionAuthority`. A later history row cannot replace the accepted current snapshot or its source clock. Collection-history charts are labelled as such. Latest recorded post-close demand is not automatically an official final subscription.

## Data quality rules

- Dates use ISO `YYYY-MM-DD`; timestamps retain their timezone and are displayed in IST.
- Missing values stay `null`; compact public payloads may omit them but never turn them into zero.
- Every record can keep multiple `sources` plus a `documents` timeline.
- NSE remains primary for exchange market observations; completed static terms use the Final Prospectus policy.
- BSE can fill missing exchange observations, but conflicts are recorded instead of overwritten.
- SEBI-only public-issue filings are marked as pre-exchange candidates until exchange data confirms them.
- Offer-document extraction retains provenance per PDF and matching evidence per accepted field.
- Subscription collectors prefer NSE and BSE Cumulative Demand; fallback providers are explicitly labelled secondary/degraded. NII amount sub-buckets are not substituted for the aggregate NII row.
- If a document or one live subscription detail request cannot be parsed, the error remains explicit rather than being treated as completion.
- If all core live sources fail, the updater preserves the existing healthy dataset.
- `meta.sourceHealth` exposes source-level success/failure in the website; a successful workflow is not proof every observation is fresh.

## Next priorities

Follow [the owner roadmap](docs/ROADMAP.md) and [verified project status](docs/PROJECT_STATUS.md): public trust/freshness, dependable repairs and proposal/review routing, then P4 source-evidence closeout. Daily research improvements build on those foundations. Performance and historical P5 are separate later workstreams, both blocked while P4 remains incomplete. Customer validation, data-use rights and service suitability proceed alongside repairs; billing, accounts and tracking require their prerequisites and approval.

Semantic validation and phase gates are independent of presence-based completeness. See [schema v5](docs/SCHEMA.md) and [operations](docs/OPERATIONS.md).
