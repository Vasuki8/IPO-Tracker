# India IPO Tracker

A static, source-aware website for tracking Indian IPOs from **SEBI filing through exchange listing**. The frontend is plain HTML/CSS/JavaScript for free GitHub Pages hosting; a Python updater builds the normalized `data/ipos.json` database.

## Phase 2 data architecture

The sources deliberately have different roles:

- **SEBI** — earliest official discovery layer. Scans Public Issues filings for DRHP/UDRHP/RHP/final prospectus records and retains official document links.
- **NSE** — primary exchange spine for current issues, upcoming issues, issue details and historical IPO records.
- **BSE** — independent exchange validation layer. It fills missing values but cannot silently overwrite populated NSE values.

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
uv run python scripts/update_data.py
```

The default refresh performs:

1. NSE current + upcoming + detail enrichment.
2. Recent NSE history refresh.
3. Recent SEBI filing scan and offer-document collection.
4. BSE current/public issue validation.
5. Cross-source validation and conflict flagging.

### First-time full NSE history backfill

```powershell
uv run python scripts/update_data.py --bootstrap-history --history-from 2000-01-01
```

### Deeper first-time SEBI scan

```powershell
uv run python scripts/update_data.py --sebi-pages 20
```

After a filing is discovered it remains in the local database, so routine hourly refreshes only need a few recent SEBI pages.

### Debug one source at a time

```powershell
uv run python scripts/update_data.py --skip-sebi --skip-bse
uv run python scripts/update_data.py --skip-bse
uv run python scripts/update_data.py --skip-sebi
```

## GitHub Pages deployment

1. Create a public GitHub repository and upload this project.
2. In **Settings → Pages**, deploy from branch `main` and `/ (root)`.
3. In **Settings → Actions → General → Workflow permissions**, allow **Read and write permissions**.
4. Open **Actions → Update IPO data → Run workflow**.
5. On the first run, enable **Backfill full NSE IPO history** and/or **Deep scan SEBI filings** if desired.

The workflow then runs hourly and commits `data/ipos.json` only when the normalized database changes.

## NSE website endpoints used

- `/api/ipo-current-issue`
- `/api/all-upcoming-issues?category=ipo`
- `/api/ipo-detail?symbol=...&series=EQ|SME`
- `/api/public-past-issues?from_date=DD-MM-YYYY&to_date=DD-MM-YYYY`

These are public website data endpoints rather than a guaranteed commercial API. The updater uses cookie priming, retries and conservative failure handling.

## Data quality rules

- Dates use ISO `YYYY-MM-DD`; timestamps use `Asia/Kolkata`.
- Missing values stay `null`.
- Every record can keep multiple `sources` plus a `documents` timeline.
- NSE remains primary for populated exchange fields.
- BSE can fill missing fields, but conflicts are recorded instead of overwritten.
- SEBI-only public-issue filings are marked as pre-exchange candidates until exchange data confirms them.
- If all live sources fail, the updater preserves the existing healthy dataset.
- `meta.sourceHealth` exposes source-level success/failure in the website.

## Next priorities

1. Extract issue size, fresh issue/OFS split, lead managers and financials directly from RHP/Prospectus documents.
2. Add category-level QIB/NII/Retail subscription snapshots with timestamps.
3. Add listing-day and post-listing market performance.
4. Add per-IPO historical timeline and downloadable CSV.
5. Add optional GMP only as a visually separate **unofficial/unregulated** source.
