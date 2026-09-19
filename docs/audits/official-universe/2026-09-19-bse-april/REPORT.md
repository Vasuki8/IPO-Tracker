# BSE official-universe bounded-cohort source review

This is an identity/lifecycle review only. It continues the released official-universe snapshot without recrawling completed NSE/SEBI/BSE archive cohorts. Canonical `data/ipos.json` is not changed by this stage.

- Base snapshot: `docs/audits/official-universe/2026-09-19-bse-may`
- Baseline commit: `1461e6987c0d81d16666ede762650059deb162e2`
- Candidate records: **2**
- Unambiguous identity-only admissions proposed: **2**
- Possible duplicates/collisions requiring review: **0**
- Source unavailable / not verified: **0**
- Review version: `official-universe-bse-cohort-v1`

| Official issuer | Board | BSE symbol | Decision |
|---|---|---|---|
| Mehul Telecom Limited | SME | MTL | accept_identity_only |
| Safety controls & Devices Limited | SME | SCDL | accept_identity_only |

Every accepted proposal has an independent retained BSE detail response with exact issuer header, Equity security type, symbol and issue period matching the retained historical archive row. Listing dates and all numerical/financial/offer fields remain unknown unless separately evidenced. No fuzzy merge is performed.

The inherited Dhanwel June/August collision remains unresolved and is not included in these admissions. See `collision-review.json`. The next stage may promote only `accept_identity_only` records after reviewing this evidence; all other decisions remain non-admissions.
