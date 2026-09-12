# India IPO Tracker

A static, source-aware website for tracking Indian IPOs from **SEBI filing through exchange listing**. The frontend is plain HTML/CSS/JavaScript for free GitHub Pages hosting; Python updaters build and enrich the normalized `data/ipos.json` database.

## Data architecture

The sources deliberately have different roles:

- **SEBI** — earliest official discovery layer. Scans Public Issues filings for DRHP/UDRHP/RHP/final prospectus records and retains official document links.
- **NSE** — primary exchange spine for current issues, upcoming issues, issue details and historical IPO records.
- **BSE** — independent exchange validation layer. It fills missing values but cannot silently overwrite populated NSE values.
- **SEBI offer documents** — Phase 3 structured extraction layer. Abridged DRHP/RHP/Prospectus PDFs are parsed for issue composition, lead managers, registrar, promoters, objects of the issue, promoter pre-issue holding and restated financials.

When NSE and BSE disagree on comparable fields, the record is marked `conflict` and both values remain visible in the IPO detail dialog.

Official source pages:

- SEBI Public Issues: https://www.sebi.gov.in/filings/public-issues.html
- NSE IPO data: https://www.nseindia.com/market-data/all-upcoming-issues-ipo
- BSE Public Issues: https://www.bseindia.com/markets/PublicIssues/IPOIssues_new.aspx?id=1&Type=p

## Run locally

```powershell
# from the project folder
uv sync
uv run python -m http.server 8000
```

Open `http://localhost:8000`.

> Do not open `index.html` with `file://`; the browser cannot reliably fetch `data/ipos.json` that way.

## Refresh all official sources

```powershell
uv run python scripts/run_update.py
uv run python scripts/enrich_offer_docs.py --limit 8
```

The routine refresh performs:

1. NSE current + upcoming + historical refresh.
2. Recent SEBI filing scan and offer-document collection.
3. BSE current IPO-only validation.
4. Cross-source validation and conflict flagging.
5. Incremental extraction from recent SEBI Abridged Prospectus PDFs.

### First-time full NSE history backfill

```powershell
uv run python scripts/run_update.py --bootstrap-history --history-from 2000-01-01
```

### Deeper SEBI filing scan

```powershell
uv run python scripts/run_update.py --sebi-pages 20
```

### Extract all eligible offer documents

```powershell
uv run python scripts/enrich_offer_docs.py --limit 0
```

The offer-document extractor is incremental. Once a PDF has been successfully parsed with the current parser version, routine hourly runs skip it unless a newer document becomes available. It intentionally prioritizes short official **Abridged Prospectus** PDFs rather than repeatedly downloading very large full RHP/DRHP files.

### Debug one source at a time

```powershell
uv run python scripts/run_update.py --skip-sebi --skip-bse
uv run python scripts/run_update.py --skip-bse
uv run python scripts/run_update.py --skip-sebi
uv run python scripts/enrich_offer_docs.py --company "Company Name" --force
```

## GitHub Pages deployment

1. Create a public GitHub repository and upload this project.
2. In **Settings → Pages**, deploy from branch `main` and `/ (root)`.
3. In **Settings → Actions → General → Workflow permissions**, allow **Read and write permissions**.
4. Open **Actions → Update IPO data → Run workflow**.
5. Optional manual inputs can backfill NSE history, deepen the SEBI filing scan, or process all currently eligible offer documents.

The workflow runs hourly and commits `data/ipos.json` only when the normalized database changes.

## NSE website endpoints used

- `/api/ipo-current-issue`
- `/api/all-upcoming-issues?category=ipo`
- `/api/ipo-detail?symbol=...&series=EQ|SME`
- `/api/public-past-issues?from_date=DD-MM-YYYY&to_date=DD-MM-YYYY`

These are public website data endpoints rather than a guaranteed commercial API. The updater uses cookie priming, retries and conservative failure handling.

## Phase 3 structured fields

When available in the official SEBI Abridged Prospectus, records can include:

- `issueComposition.freshShares`, `ofsShares`, fresh/OFS value at the exchange cap price
- `leadManagers`
- `registrar`
- `promoters`
- `objectsOfIssue[]` with amounts normalized to ₹ crore
- `financials.periods[]` for revenue, EBITDA, PAT, net worth, RONW/ROE and EPS when disclosed
- `shareholding.promoterPreIssuePct`
- `offerDocumentExtraction` with source PDF, parser version, SHA-256, pages parsed and extraction timestamp

Document-derived values fill missing fields but do not silently overwrite populated exchange values.

## Data quality rules

- Dates use ISO `YYYY-MM-DD`; timestamps use `Asia/Kolkata`.
- Missing values stay `null`.
- Every record can keep multiple `sources` plus a `documents` timeline.
- NSE remains primary for populated exchange fields.
- BSE can fill missing fields, but conflicts are recorded instead of overwritten.
- SEBI-only public-issue filings are marked as pre-exchange candidates until exchange data confirms them.
- Offer-document extraction is official-source-only and provenance is retained per PDF.
- If a document cannot be parsed, the error is recorded without blocking the core NSE/SEBI/BSE refresh.
- If all live sources fail, the updater preserves the existing healthy dataset.
- `meta.sourceHealth` exposes source-level success/failure in the website.

## Next priorities

1. Complete backfill of eligible SEBI offer documents and improve parser coverage for alternate prospectus layouts.
2. Add category-level QIB/NII/Retail subscription snapshots with timestamps.
3. Add listing-day and post-listing market performance.
4. Add per-IPO historical timeline and downloadable CSV.
5. Add optional GMP only as a visually separate **unofficial/unregulated** source.
