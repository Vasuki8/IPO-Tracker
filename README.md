# India IPO Tracker

A static, source-aware website for tracking Indian IPOs across **upcoming, open, closed and listed** stages. The frontend is plain HTML/CSS/JavaScript so it can be hosted free on GitHub Pages. A Python updater pulls NSE data and writes a normalized `data/ipos.json` file.

## Why this is the first build

The first priority is the **data spine**, not cosmetic pages. NSE exposes the current issue list, upcoming issues, issue details and historical issues through its website data endpoints. Once normalized into one schema, SEBI DRHP/RHP filings and BSE cross-checks can be added later without changing the UI.

## Run locally

```powershell
# from the project folder
uv sync
uv run python -m http.server 8000
```

Open `http://localhost:8000`.

> Do not open `index.html` with `file://`; the browser cannot reliably fetch `data/ipos.json` that way.

## Refresh live NSE data

```powershell
uv run python scripts/update_data.py
```

The scheduled updater refreshes the latest year of historical data plus current/upcoming issues.

### First-time full history backfill

```powershell
uv run python scripts/update_data.py --bootstrap-history --history-from 2000-01-01
```

This intentionally makes many small date-range requests rather than one giant request. It is slower but safer for the NSE endpoint.

## GitHub Pages deployment

1. Create a public GitHub repository and upload this project.
2. In **Settings → Pages**, deploy from branch `main` and `/ (root)`.
3. In **Settings → Actions → General → Workflow permissions**, allow **Read and write permissions**.
4. Open **Actions → Update IPO data → Run workflow**.
5. For the first run, optionally enable **Backfill full IPO history from 2000**.

After that, the workflow runs hourly and commits `data/ipos.json` only when it changes.

## NSE endpoints used

- `/api/ipo-current-issue` — current/live issues
- `/api/all-upcoming-issues?category=ipo` — upcoming issues
- `/api/ipo-detail?symbol=...&series=EQ|SME` — issue detail/category data
- `/api/public-past-issues?from_date=DD-MM-YYYY&to_date=DD-MM-YYYY` — historical issues

These are public website endpoints, but they are not presented as a formal commercial API. NSE can block cloud/datacenter traffic. The updater therefore uses a cookie handshake, retries, and refuses to overwrite a healthy dataset with an empty response.

## Data quality rules

- Dates are stored as ISO `YYYY-MM-DD`.
- Times are stored in `Asia/Kolkata`.
- Missing values stay `null`; the updater does not fabricate values.
- Each record stores `source.name`, `source.url` and `source.asOf`.
- Existing non-null values are retained if a later source response omits them.
- IPO status is re-derived from dates every run.

## Next implementation priorities

1. Add **SEBI DRHP/RHP/prospectus collector** so companies appear earlier than the NSE bidding calendar.
2. Add **BSE fallback and category subscription cross-checks**.
3. Add **listing-price/current-price performance** from exchange market data.
4. Add per-IPO detail pages and downloadable historical CSV.
5. Add optional GMP only as a separately labeled unofficial source.
