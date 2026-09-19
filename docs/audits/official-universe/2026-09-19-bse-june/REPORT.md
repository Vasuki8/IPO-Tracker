# BSE June 2026 official-universe source review

This is an identity/lifecycle review only. It continues the released official-universe snapshot without recrawling completed NSE/SEBI/BSE archive cohorts. Canonical `data/ipos.json` is not changed by this stage.

- Base snapshot: `docs/audits/official-universe/2026-09-19`
- Baseline commit: `345e2c1e0c14b7d66475391b23c9e216362d614e`
- Candidate records: **18**
- Unambiguous identity-only admissions proposed: **18**
- Possible duplicates/collisions requiring review: **0**
- Source unavailable / not verified: **0**
- Review version: `official-universe-bse-cohort-v1`

| Official issuer | Board | BSE symbol | Decision |
|---|---|---|---|
| ATHARVA POLY-PLAST LIMITED | SME | ATHARVA | accept_identity_only |
| KRATIKAL TECH LIMITED | SME | KRATIKAL | accept_identity_only |
| Sampark India Logistics Limited | SME | SILL | accept_identity_only |
| Seemax Resources Limited | SME | SEEMAX | accept_identity_only |
| Adon Agro Commodities Limited | SME | ADON | accept_identity_only |
| Crazy Snacks Limited | SME | CRAZYSNACK | accept_identity_only |
| Twinkle Papers Limited | SME | TWINKLE | accept_identity_only |
| RIYAASAT LIFESTYLE LIMITED | SME | RIYAASAT | accept_identity_only |
| Anubhav Plast Limited | SME | ANUBHAV | accept_identity_only |
| Leapfrog Engineering Services Limited | SME | LESL | accept_identity_only |
| Horizon Reclaim (India) Limited | SME | HORIZON | accept_identity_only |
| SUSAN ELECTRICALS INDIA LIMITED | SME | SUSAN | accept_identity_only |
| UHM VACATION LIMITED | SME | UHMVL | accept_identity_only |
| Merritronix Limited | SME | MRTX | accept_identity_only |
| JIVIAL INDUSTRIES LIMITED | SME | JIVIAL | accept_identity_only |
| DIKSHA POLYMERS LIMITED | SME | DIKSHA | accept_identity_only |
| LIOTECH INDUSTRIES LIMITED | SME | LIOTECH | accept_identity_only |
| VAHH CHEMICALS LIMITED | SME | VAHH | accept_identity_only |

Every accepted proposal has an independent retained BSE detail response with exact issuer header, Equity security type, symbol and issue period matching the retained historical archive row. Listing dates and all numerical/financial/offer fields remain unknown unless separately evidenced. No fuzzy merge is performed.

The inherited Dhanwel June/August collision remains unresolved and is not included in these admissions. See `collision-review.json`. The next stage may promote only `accept_identity_only` records after reviewing this evidence; all other decisions remain non-admissions.
