# Live IPO automation

## Goal

The public tracker should discover newly announced/open IPOs without requiring a manual data-recovery prompt before they appear on the website.

The first automated source family is the official NSE public IPO feed.

## Official discovery endpoints

The collector reads:

- `https://www.nseindia.com/api/all-upcoming-issues?category=ipo`
- `https://www.nseindia.com/api/ipo-current-issue`

These are public NSE website endpoints used by NSE's IPO market-data pages. They are not treated as a substitute for later offer-document recovery.

## Schedule

`.github/workflows/update-ipos.yml` runs hourly at minute 17 and may also be run manually.

The workflow:

1. checks out `main`;
2. tests the feed parser;
3. fetches the NSE live feeds;
4. merges new source-backed records into the recovery manifest;
5. rebuilds `data/ipos.json`;
6. validates the data contract;
7. commits only if source-backed data changed;
8. the resulting push triggers the existing GitHub Pages deployment workflow.

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
